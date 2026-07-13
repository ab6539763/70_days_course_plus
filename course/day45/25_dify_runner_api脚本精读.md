# dify_runner API 脚本精读

## dify_api_demo.py 全文

```python
"""
Dify API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day45/dify_api_demo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from fastapi.testclient import TestClient

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


def main() -> int:
    set_knowledge_store(KnowledgeStore.bootstrap_from_sample_docs())
    client = TestClient(create_app())

    print("=== Day 45 Dify API Demo ===\n")
    cfg = client.get("/api/agent/dify-config").json()
    print(f"  workflow_name={cfg.get('workflow_name')} enabled={cfg.get('enabled')}")

    exported = client.post("/api/agent/dify-export", json={})
    print(f"  dify-export: {exported.status_code}")
    export_body = exported.json()
    node_ids = [n.get("id") for n in export_body.get("workflow", {}).get("graph", {}).get("nodes", [])]
    print(f"  nodes={node_ids}")

    preview = client.post(
        "/api/agent/dify-preview",
        json={"query": "年化收益怎么样"},
    )
    print(f"  dify-preview: {preview.status_code}")
    body = preview.json()
    print(f"  tools_used={body.get('tools_used')} dify_trace 节点数={len(body.get('dify_trace', []))}")

    chat = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "dify_mode": True},
    )
    print(f"  chat dify_mode: {chat.status_code}")
    chat_body = chat.json()
    print(f"  kind={chat_body.get('kind')} dify_trace 节点数={len(chat_body.get('dify_trace') or [])}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

## 逐段讲解

| 行段 | 说明 |
|------|------|
| 开头 | 注入 `src` 与 `NEXUS_LLM_MOCK` |
| TestClient | 创建 app 与测试客户端 |
| bootstrap | 保证语料/知识库已初始化 |
| GET dify-config | 读默认配置 |
| POST dify-export | 导出工作流 DSL — **核心演示** |
| POST dify-preview | 预览一次调用的 dify_trace |
| chat + health | 端到端 + 版本号 v0.45.0 |

---

## dify_demo.py 全文

```python
"""
Dify 工作流对接演示

运行：PYTHONPATH=src python3 src/day45/dify_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.dify_config import DifyConfig
from agent.dify_runner import DifyRunner
from api.factory import create_orchestrator
from day45.constants import DIFY_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 45 Dify 工作流对接演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    runner = DifyRunner.from_executor(
        orchestrator.tool_executor,
        config=DifyConfig(enabled=True),
    )

    workflow = runner.export_workflow()
    node_ids = [n.id for n in workflow.nodes]
    print(f"\n  导出 Dify 工作流「{workflow.name}」节点: {node_ids}")

    for item in DIFY_CASES:
        outcome = runner.invoke(item["query"])
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if tool == item["expect_tool"] else "⚠️"
        print(f"\n  Q: {item['query']}")
        print(f"    tools_used={list(outcome.tools_used)} {flag}")
        print(f"    dify_trace 节点数={len(outcome.dify_trace)}")
        print(f"    reply: {outcome.reply[:70]}...")

    print("\n  ✅ Dify 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


`export_workflow()` 与 `invoke()` 分别对应"导出"与"运行"两条路径。

---

## constants.py

```python
DIFY_CASES = [
    {"query": "客服电话多少", "expect_tool": "faq_lookup"},
    {"query": "年化收益怎么样", "expect_tool": "rag_search"},
    {"query": "帮我总结一下理财产品", "expect_tool": "intent_classify"},
]

QUIZ_PASS_SCORE = 60
```

---

## phase4_quiz.py 骨架

```python
"""
Phase 4 周测 — Day 39-44 知识点自测

共 10 题，每题 10 分。覆盖 ReAct、AgentExecutor、StateGraph、Approval、
Supervisor、MCP。

运行：python3 src/day45/phase4_quiz.py
CI：python3 src/day45/phase4_quiz.py --scripted
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day45.constants import QUIZ_PASS_SCORE

QUESTIONS: list[dict] = [
    {
        "q": "手写 ReAct Agent（Day 39）的核心循环是？",
        "options": ["Plan-Execute", "Thought-Action-Observation", "Map-Reduce", "Fork-Join"],
        "answer": 1,
        "explain": "ReAct = Reasoning + Acting，循环为 Thought → Action → Observation。",
    },
    {
        "q": "AgentExecutor（Day 40）用什么装饰器把函数注册为工具？",
        "options": ["@retry", "@tool", "@cache", "@route"],
        "answer": 1,
        "explain": "@tool 装饰器 + StructuredTool 自动从函数签名推导 OpenAI function-calling schema。",
    },
    {
        "q": "StateGraph（Day 41）里 node_path 记录的是？",
        "options": ["每个节点的耗时", "本次调用实际经过的节点序列", "所有可能的节点", "配置项列表"],
        "answer": 1,
        "explain": "node_path 是调用期间真正走过的节点名称序列，用于审计与调试。",
    },
    {
        "q": "人工审批工作流（Day 42）中断后，靠什么恢复执行？",
        "options": ["session_id", "checkpoint_id + approval-resume", "重新发起 chat", "轮询超时"],
        "answer": 1,
        "explain": "中断时返回 checkpoint_id，人工调用 approval-resume 携带 approved/comment 后续跑。",
    },
    {
        "q": "Supervisor 多 Agent（Day 43）委派的三个子 Agent 是？",
        "options": [
            "faq_worker / rag_worker / intent_worker",
            "planner / executor / critic",
            "reader / writer / judge",
            "router / merger / ranker",
        ],
        "answer": 0,
        "explain": "supervisor_route 按问题类型委派给 faq_worker、rag_worker 或 intent_worker。",
    },
    {
        "q": "MCP 协议（Day 44）的两个核心方法是？",
        "options": ["get/post", "tools/list 与 tools/call", "read/write", "push/pull"],
        "answer": 1,
        "explain": "tools/list 发现工具 schema；tools/call 按名调用，均为 JSON-RPC 风格。",
    },
    {
        "q": "McpRunner.invoke 的四阶段顺序是？",
        "options": [
            "call → route → discover → answer",
            "discover → route → call → answer",
            "route → discover → answer → call",
            "answer → call → route → discover",
        ],
        "answer": 1,
        "explain": "先发现工具（discover），再路由选工具（route），调用（call），最后汇总（answer）。",
    },
    {
        "q": "Day 39-44 的 chat 接口共享的可观测性设计是？",
        "options": [
            "每种模式都返回专属 trace 字段（agent_trace/executor_trace/.../mcp_trace）",
            "只有 kind 字段没有 trace",
            "trace 统一放在 citations 里",
            "trace 只在 CI 环境返回",
        ],
        "answer": 0,
        "explain": "每个 Phase 4 模式都新增自己的 trace 字段，教学上强调「可观测性优先」。",
    },
    {
        "q": "Supervisor 与 MCP 最大的设计差异是？",
        "options": [
            "Supervisor 无需工具",
            "Supervisor 委派进程内子 Agent；MCP 面向协议化、可跨进程/跨语言的外部工具",
            "MCP 不能持久化配置",
            "两者完全一样",
        ],
        "answer": 1,
        "explain": "Day43 让 Agent 可协作（进程内）；Day44 让工具链可扩展（协议边界，面向外部生态）。",
    },
    {
        "q": "关闭 Day 39-44 任一新增模式最快的方式是？",
        "options": [
            "改代码重新部署",
            "PUT 对应 /api/agent/*-config 把 enabled 设为 false",
            "删除 store.json",
            "重启整个平台",
        ],
        "answer": 1,
        "explain": "所有 Phase 4 模式默认可通过 enabled=false 一键回退，无需改代码。",
    },
]


def run_quiz_scripted(answers: list[int] | None = None) -> int:
    """非交互评分（供 CI 与单元测试）"""
    if answers is None:
        answers = [q["answer"] for q in QUESTIONS]
    score = 0
    for item, ans in zip(QUESTIONS, answers):
        if ans == item["answer"]:
            score += 10
    return score


def run_quiz() -> int:
    print("=" * 48)
    print("  NexusAgent Phase 4 周测（Day 39-44）")
    print("=" * 48)
    score = 0
    for i, item in enumerate(QUESTIONS, 1):
        print(f"\n第 {i} 题：{item['q']}")
        for j, opt in enumerate(item["options"]):
            print(f"  {j}. {opt}")
        raw = input("你的答案（数字）：").strip()
        if raw.isdigit() and int(raw) == item["answer"]:
            print("  ✅ 正确")
            score += 10
        else:
            correct = item["options"][item["answer"]]
            print(f"  ❌ 正确答案：{item['answer']}. {correct}")
            print(f"     解析：{item['explain']}")
    print("\n" + "=" * 48)
    print(f"  得分：{score} / 100")
    if score >= QUIZ_PASS_SCORE:
        print("  🎉 及格！Phase 4 前半程验收通过。")
    else:
        print("  📚 建议复习 Day 39-44 课件后再测。")
    print("=" * 48)
    return score


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--scripted" in argv:
        score = run_quiz_scripted()
        print(f"Phase4 quiz scripted score: {score}/100")
        return 0 if score >= QUIZ_PASS_SCORE else 1
    run_quiz()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

## phase4_review.py 全文

```python
"""
Phase 4 知识回顾 — Day 39-45 能力串联

运行：python3 src/day45/phase4_review.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

MILESTONES = [
    ("Day 39", "手写 ReAct Agent — Thought/Action/Observation"),
    ("Day 40", "AgentExecutor 框架工具链 — StructuredTool + intermediate_steps"),
    ("Day 41", "StateGraph 状态图编排 — planner → tool_runner → answer"),
    ("Day 42", "人工审批工作流 — human_approval + checkpoint 中断恢复"),
    ("Day 43", "Supervisor 多 Agent 委派 — faq/rag/intent 三专职子 Agent"),
    ("Day 44", "MCP 协议与工具生态 — 自研 MCP Server tools/list + tools/call"),
    ("Day 45", "Dify 工作流对接 + Phase 4 周测 ← 今日"),
]


def main() -> int:
    print("=== Phase 4 能力里程碑（Day 39-45）===\n")
    for phase, desc in MILESTONES:
        print(f"  ✅ {phase}: {desc}")
    print("\n  周测交付：ReAct + Executor + Graph + Approval + Supervisor + MCP 整合自测")
    print("  Dify 交付：ToolRegistry → Dify 工作流 DSL 导出 + 运行 trace 映射")
    print("  下一阶段：Day 46+ Agent 工程化（可观测性与容错）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day45/dify_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day45/dify_api_demo.py
PYTHONPATH=src python3 src/day45/phase4_review.py
PYTHONPATH=src python3 src/day45/phase4_quiz.py --scripted
pytest tests/day45/ -v
```
