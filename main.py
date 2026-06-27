#!/usr/bin/env python3
"""Code Eval Platform — FastAPI 应用入口。"""

import json
import os
import time
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI(title="Code Eval Platform")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ---- 内存数据存储 ----
challenges = [
    {
        "id": 1,
        "name": "两数之和",
        "difficulty": "easy",
        "description": "给定整数数组和目标值，返回和为目标值的两个下标",
        "signature": "def two_sum(nums: list[int], target: int) -> list[int]:",
        "test_cases": [
            {"input": {"nums": [2,7,11,15], "target": 9}, "expected": [0,1]},
            {"input": {"nums": [3,2,4], "target": 6}, "expected": [1,2]},
            {"input": {"nums": [3,3], "target": 6}, "expected": [0,1]},
        ],
    },
    {
        "id": 2,
        "name": "有效括号",
        "difficulty": "medium",
        "description": "判断括号字符串是否有效",
        "signature": "def is_valid(s: str) -> bool:",
        "test_cases": [
            {"input": {"s": "()"}, "expected": True},
            {"input": {"s": "()[]{}"}, "expected": True},
            {"input": {"s": "(]"}, "expected": False},
        ],
    },
    {
        "id": 3,
        "name": "LRU 缓存",
        "difficulty": "hard",
        "description": "设计 LRU 缓存数据结构",
        "signature": "class LRUCache:\n    def get(self, key: int) -> int: ...\n    def put(self, key: int, value: int) -> None: ...",
        "test_cases": [
            {"input": {"ops": ["put","put","get","put","get","put","get","get","get"], "args": [[1,1],[2,2],[1],[3,3],[2],[4,4],[1],[3],[4]], "capacity": 2}, "expected": [1,-1,-1,3,4]},
        ],
    },
]

evaluations = []
leaderboard = []


class EvalRequest(BaseModel):
    model_name: str
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    challenge_ids: list[int] = []


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页 — 排行榜 + 最近评测。"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "leaderboard": leaderboard,
        "evaluations": evaluations[-10:],
        "challenges": challenges,
    })


@app.get("/api/challenges")
async def get_challenges():
    """获取所有题目。"""
    return challenges


@app.post("/api/evaluate")
async def run_evaluation(req: EvalRequest):
    """运行评测。"""
    from evaluator import evaluate_model

    target_challenges = challenges
    if req.challenge_ids:
        target_challenges = [c for c in challenges if c["id"] in req.challenge_ids]

    result = evaluate_model(
        model_name=req.model_name,
        api_key=req.api_key,
        base_url=req.base_url,
        challenges=target_challenges,
    )

    eval_record = {
        "id": len(evaluations) + 1,
        "model_name": req.model_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": result,
        "avg_score": round(sum(r["score"] for r in result) / len(result), 1) if result else 0,
    }
    evaluations.append(eval_record)

    # 更新排行榜
    _update_leaderboard(req.model_name, eval_record["avg_score"])

    return eval_record


@app.get("/api/leaderboard")
async def get_leaderboard():
    """获取排行榜。"""
    return sorted(leaderboard, key=lambda x: x["best_score"], reverse=True)


@app.get("/api/evaluations")
async def get_evaluations():
    """获取评测历史。"""
    return evaluations


def _update_leaderboard(model_name: str, score: float):
    """更新排行榜。"""
    for entry in leaderboard:
        if entry["model_name"] == model_name:
            entry["best_score"] = max(entry["best_score"], score)
            entry["last_eval"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry["eval_count"] += 1
            return
    leaderboard.append({
        "model_name": model_name,
        "best_score": score,
        "last_eval": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "eval_count": 1,
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
