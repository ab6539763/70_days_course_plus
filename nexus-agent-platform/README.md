# NexusAgent 灵犀智能体平台

> 企业级多租户 Agent 编排与 RAG 知识库平台 — 70 天实战建设

## 项目状态

| 版本 | 日期 | 里程碑 | 状态 |
|------|------|--------|------|
| v0.1.0 | Day 1 | 项目启动、CLI 成员信息采集 | 🟢 进行中 |

## 快速开始

```bash
# 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖（Day 1 无第三方依赖）
pip install -r requirements-day01.txt

# 运行 Day 1 程序
python src/day01/personal_info_card.py
```

## 目录结构

```
nexus-agent-platform/
├── src/
│   └── day01/              # Day 1 交付物
│       ├── constants.py
│       ├── personal_info_card.py
│       ├── hello.py
│       └── exercises/      # 课后练习
├── tests/
│   └── day01/
└── docs/
    └── ARCHITECTURE.md
```

## 开发规范

- Python 3.11
- 代码风格：PEP 8
- 提交规范：见 `team/GIT_CONVENTION.md`
- 每个 Day 的代码在 `src/dayXX/` 目录

## 许可证

MIT License
