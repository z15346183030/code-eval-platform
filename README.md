# 📊 Code Eval Platform

一个完整的 AI 模型代码能力评估平台。支持上传代码题目、多模型自动评测、排行榜展示和评测报告导出。

## ✨ 特性

- **Web 管理界面** — 可视化管理题目、模型、评测任务
- **多模型对比** — 同时测试多个 AI 模型的编程能力
- **自动评分** — 代码正确性 + 代码质量双维度评估
- **排行榜** — 实时更新的模型能力排名
- **评测报告** — 导出 Markdown 格式的详细报告

## 🚀 快速开始

```bash
pip install fastapi uvicorn openai jinja2

# 启动服务
python main.py

# 访问 http://localhost:8000
```

## 📸 界面

- **首页** — 模型排行榜 + 最近评测
- **题目管理** — 查看/添加编程题目
- **评测任务** — 创建评测、查看结果
- **模型配置** — 管理 API Key 和模型

## 🏗️ 项目结构

```
code-eval-platform/
├── main.py              # FastAPI 应用入口
├── evaluator.py         # 评测引擎
├── models.py            # 数据模型
├── templates/
│   └── index.html       # 前端页面
├── static/
│   └── style.css        # 样式
└── requirements.txt
```

## License

MIT
