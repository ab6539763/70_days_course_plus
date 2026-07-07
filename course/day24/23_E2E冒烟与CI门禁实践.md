# E2E 冒烟与 CI 门禁实践

**需求**：ZL-NA-REQ-024

## 1. 冒烟脚本全文

```python
"""
Sprint 3 E2E 冒烟 — TestClient 模拟投资人三问句

运行：NEXUS_LLM_MOCK=1 python3 src/day24/e2e_smoke.py
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
from day24.constants import DEMO_QUERIES


def run_smoke() -> int:
    client = TestClient(create_app())
    print("=== Sprint 3 E2E 冒烟 ===\n")

    health = client.get("/api/health")
    if health.status_code != 200:
        print(f"  ❌ health {health.status_code}")
        return 1
    print(f"  ✅ health {health.json()}")

    index = client.get("/")
    if "NexusAgent" not in index.text:
        print("  ❌ 首页未加载")
        return 1
    print("  ✅ frontend index")

    for script in ("session.js", "errors.js", "config.js"):
        r = client.get(f"/{script}")
        if r.status_code != 200:
            print(f"  ❌ {script} 缺失")
            return 1
    print("  ✅ session.js / errors.js / config.js")

    sid = "e2e-demo-session"
    kinds = set()
    for q in DEMO_QUERIES:
        resp = client.post("/api/chat", json={"message": q, "session_id": sid})
        if resp.status_code != 200:
            print(f"  ❌ chat failed: {q} -> {resp.status_code}")
            return 1
        data = resp.json()
        kinds.add(data.get("kind"))
        print(f"  ✅ Q: {q[:20]}… kind={data.get('kind')}")

    reset = client.post("/api/session/reset", json={"session_id": sid})
    if reset.status_code != 200:
        print("  ❌ session reset failed")
        return 1
    print("  ✅ session reset")

    print(f"\n  命中 kind 集合: {sorted(kinds)}")
    print("  E2E 冒烟完成")
    return 0


def main() -> int:
    return run_smoke()


if __name__ == "__main__":
    raise SystemExit(main())
```


## 2. 检查项矩阵

| 步骤 | 验证 | 失败含义 |
|------|------|----------|
| GET /api/health | 200 | API 未挂载 |
| GET / | 含 NexusAgent | 静态托管失败 |
| GET session.js 等 | 200 | 整合脚本缺失 |
| POST chat ×3 | 200 | 编排器或路由坏 |
| POST reset | 200 | reset 未实现 |

## 3. CI 集成建议

```yaml
- name: Sprint 3 gate
  run: |
    cd nexus-agent-platform
    export PYTHONPATH=src NEXUS_LLM_MOCK=1
    python3 src/day24/sprint3_launch.py
```

## 4. 与浏览器 E2E 边界

TestClient 不执行 JS，不测 localStorage。互补测试：

- 冒烟：HTTP + 静态内容  
- test_index_has_new_chat_button：读 HTML 文件  
- 人工 Lab：浏览器行为  

## 5. 故障排查

| 输出 | 对策 |
|------|------|
| health 非 200 | 检查 create_app |
| index 无 NexusAgent | frontend 路径 |
| chat failed | NEXUS_LLM_MOCK、编排器 |
| reset failed | chat.py 路由 |

CI 实践完。

---

## 6. 冒烟输出范例（注解）

```
=== Sprint 3 E2E 冒烟 ===
  ✅ health {'status':'ok','version':'...','mock_llm':True}
  ✅ frontend index
  ✅ session.js / errors.js / config.js
  ✅ Q: 投资有风险吗… kind=faq
  ...
  命中 kind 集合: ['faq', 'route']
```

kind 集合至少 2 种说明路由多样性达标。

## 7. flake 处理

偶发 FAQ 未命中时查 NEXUS_LLM_MOCK 与 Matcher，非 smoke 脚本 bug。

CI 文档完。

---

## 智链科技 Day 24 读本附录：CI 实践

### 附录 1

本附录专属于 `23_E2E冒烟与CI门禁实践.md`，主题「CI 实践」。第 1 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 1 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：CI 实践相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 1 轮 CI 绿条是合并前提。

### 附录 2

本附录专属于 `23_E2E冒烟与CI门禁实践.md`，主题「CI 实践」。第 2 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 2 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：CI 实践相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 2 轮 CI 绿条是合并前提。

### 附录 3

本附录专属于 `23_E2E冒烟与CI门禁实践.md`，主题「CI 实践」。第 3 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 3 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：CI 实践相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 3 轮 CI 绿条是合并前提。

### 附录 4

本附录专属于 `23_E2E冒烟与CI门禁实践.md`，主题「CI 实践」。第 4 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 4 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：CI 实践相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 4 轮 CI 绿条是合并前提。

### 附录 5

本附录专属于 `23_E2E冒烟与CI门禁实践.md`，主题「CI 实践」。第 5 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 5 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：CI 实践相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 5 轮 CI 绿条是合并前提。

### 附录 6

本附录专属于 `23_E2E冒烟与CI门禁实践.md`，主题「CI 实践」。第 6 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 6 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：CI 实践相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 6 轮 CI 绿条是合并前提。

### 附录 7

本附录专属于 `23_E2E冒烟与CI门禁实践.md`，主题「CI 实践」。第 7 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 7 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：CI 实践相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 7 轮 CI 绿条是合并前提。

### 附录 8

本附录专属于 `23_E2E冒烟与CI门禁实践.md`，主题「CI 实践」。第 8 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 8 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：CI 实践相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 8 轮 CI 绿条是合并前提。
