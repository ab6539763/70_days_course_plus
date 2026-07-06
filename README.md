# NexusAgent 企业级智能体平台 — 70天实战培训课程

> **从零基础到高级 AI 应用开发工程师**：以真实企业业务需求驱动，在 70 天内亲手将一个 Agent 企业级平台从 0 到 1 完整落地。

## 课程定位

本仓库不是传统的「知识点堆砌型」教程，而是一份**可执行的工程剧本**：

- 你将以**智链科技（Zhilian Tech）**新入职工程师的身份，加入 **NexusAgent（灵犀智能体平台）** 项目组
- 每一天都有明确的**企业需求、Sprint 任务、代码交付物、评审标准**
- 70 天后，你将拥有一个可写入简历的**企业级 Agent 平台**，累计代码量约 **20 万行**

## 仓库结构

```
70_days_course_plus/
├── course/                    # 每日课件（Day 1 ~ Day 70）
│   ├── README.md              # 课程总览
│   ├── ROADMAP.md             # 70天路线图与里程碑
│   └── day01/ ~ day70/        # 每日独立课件目录
├── nexus-agent-platform/      # 企业级平台主工程（逐日迭代）
├── team/                      # 团队协作文档（章程、Sprint、会议纪要）
└── scripts/                   # 工具脚本
```

## 企业项目背景

| 项目 | 说明 |
|------|------|
| **公司** | 智链科技有限公司（Zhilian Tech） |
| **产品** | NexusAgent 灵犀智能体平台 |
| **定位** | 面向中大型企业的多租户 Agent 编排、RAG 知识库、工具市场一体化平台 |
| **客户场景** | 智能客服、企业知识问答、办公自动化、数据分析 Agent |
| **技术栈** | Python 3.11、FastAPI、LangChain/LangGraph、PostgreSQL、Redis、Milvus、Docker/K8s |

## 学习路径

| 阶段 | 天数 | 核心能力 | 企业交付物 |
|------|------|----------|------------|
| Python 基础 | Day 1-14 | 编程基本功 | 平台 CLI 工具链 + 多轮对话助手 |
| 大模型与 Prompt | Day 15-24 | API 调用与 Web 服务 | 网页版 Chat API |
| RAG 开发 | Day 25-38 | 知识库问答 | 企业知识库问答系统 |
| Agent 开发 | Day 39-50 | 多 Agent 编排 | 多 Agent 智能办公助手 |
| 微调与部署 | Day 51-60 | 模型微调与容器化 | 生产环境部署 |
| 毕业设计 | Day 61-70 | 综合实战 | 完整平台上线 |

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/ab6539763/70_days_course_plus.git
cd 70_days_course_plus

# 2. 进入 Day 1 课件
cd course/day01

# 3. 阅读旁白解读，了解今日任务
cat 00_旁白解读.md

# 4. 配置开发环境后运行第一个程序
cd ../../nexus-agent-platform
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-day01.txt
python src/day01/personal_info_card.py
```

## 今日学习（Day 1）

👉 请直接进入 [`course/day01/`](course/day01/) 开始第一天的学习。

## 许可证

本课程资料仅供学习使用。NexusAgent 平台代码采用 MIT 许可证。
