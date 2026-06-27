"""评测引擎 — 代码正确性和质量评估。"""

import ast
import json
from openai import OpenAI



def _check_code_safety(code: str) -> tuple[bool, str]:
    """检查代码是否包含危险操作。"""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"语法错误: {e}"

    dangerous_modules = {"os", "sys", "subprocess", "shutil", "socket", "http", "ftplib",
                         "ctypes", "importlib", "pathlib", "signal", "multiprocessing"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in dangerous_modules:
                    return False, f"禁止导入模块: {alias.name}"
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in dangerous_modules:
                return False, f"禁止导入模块: {node.module}"

    return True, ""

def evaluate_model(model_name: str, api_key: str, base_url: str, challenges: list[dict]) -> list[dict]:
    """评测单个模型在多道题目上的表现。"""
    client = OpenAI(api_key=api_key, base_url=base_url)
    results = []

    for challenge in challenges:
        result = _evaluate_challenge(client, model_name, challenge)
        results.append(result)

    return results


def _evaluate_challenge(client: OpenAI, model_name: str, challenge: dict) -> dict:
    """评测单道题目。"""
    prompt = f"""请完成以下编程题目，只返回 Python 代码。

题目: {challenge['description']}
函数签名: {challenge['signature']}

示例: {json.dumps(challenge['test_cases'][:2], ensure_ascii=False)}

只返回代码，不要解释。"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是 Python 程序员，只返回代码。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=1024,
        )
        code = response.choices[0].message.content or ""
    except Exception as e:
        return {
            "challenge_name": challenge["name"],
            "score": 0,
            "passed": 0,
            "total": len(challenge["test_cases"]),
            "code": "",
            "error": str(e),
        }

    # 提取代码
    code = code.strip()
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    code = code.strip()

    # 运行测试
    passed = _run_tests(code, challenge)

    # 代码质量
    quality = _evaluate_quality(code)

    total = len(challenge["test_cases"])
    correctness = passed / total * 100 if total > 0 else 0
    score = correctness * 0.6 + quality * 0.4

    return {
        "challenge_name": challenge["name"],
        "score": round(score, 1),
        "passed": passed,
        "total": total,
        "correctness": round(correctness, 1),
        "quality": round(quality, 1),
        "code": code[:500],
    }


def _run_tests(code: str, challenge: dict) -> int:
    """运行测试用例，返回通过数。"""
    namespace = {}
    safe, msg = _check_code_safety(code)
    if not safe:
        return 0
    try:
        exec(code, namespace)
    except Exception:
        return 0

    # 获取函数
    func = None
    for name, obj in namespace.items():
        if callable(obj) and not name.startswith("_"):
            func = obj
            break

    if not func:
        return 0

    passed = 0
    for tc in challenge["test_cases"]:
        try:
            result = func(**tc["input"])
            if result == tc["expected"]:
                passed += 1
        except Exception:
            continue

    return passed


def _evaluate_quality(code: str) -> float:
    """评估代码质量 (0-100)。"""
    score = 100.0
    lines = [l for l in code.strip().split("\n") if l.strip()]

    if len(lines) > 30:
        score -= min(20, (len(lines) - 30) * 2)
    if "import *" in code:
        score -= 10
    if any(l.strip().startswith("#") for l in lines):
        score = min(100, score + 5)

    return max(0, min(100, score))
