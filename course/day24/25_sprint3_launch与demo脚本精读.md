# sprint3_launch 与 demo 脚本精读

**需求**：ZL-NA-REQ-024

## sprint3_launch.py 全文

```python
"""
Sprint 3 统一启动与冒烟检查

运行：
    cd nexus-agent-platform
    PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day24/sprint3_launch.py

加 --serve 启动 uvicorn（阻塞）
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
_PLATFORM = _SRC.parent
_REPO = _PLATFORM.parent

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def run_pytest() -> int:
    print("▶ pytest day22 + day23 + day24 …")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/day22/", "tests/day23/", "tests/day24/", "-q"],
        cwd=_PLATFORM,
        env={**os.environ, "PYTHONPATH": str(_SRC), "NEXUS_LLM_MOCK": "1"},
    )
    return proc.returncode


def run_smoke() -> int:
    os.environ.setdefault("NEXUS_LLM_MOCK", "1")
    from day24.e2e_smoke import run_smoke as _smoke

    return _smoke()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sprint 3 统一启动与冒烟")
    parser.add_argument("--serve", action="store_true", help="通过检查后启动 uvicorn")
    parser.add_argument("--skip-pytest", action="store_true")
    args = parser.parse_args(argv)

    print("=" * 56)
    print("  NexusAgent Sprint 3 Launch (Day 24)")
    print("=" * 56)

    if not args.skip_pytest:
        if run_pytest() != 0:
            print("\n❌ pytest 未通过，中止启动")
            return 1
        print("✅ pytest 通过\n")

    if run_smoke() != 0:
        print("\n❌ E2E 冒烟未通过")
        return 1
    print("✅ E2E 冒烟通过\n")

    print("  浏览器访问: http://127.0.0.1:8000")
    print("  Mock 预览:  http://127.0.0.1:8000/?mock=1")
    print("=" * 56)

    if args.serve:
        import uvicorn

        uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


## 逐段解读

### 路径常量 L19-21

`_SRC` = src 目录，`_PLATFORM` = nexus-agent-platform，`_REPO` = 仓库根（含 frontend）。

### run_pytest L27-34

subprocess 显式传 `PYTHONPATH` 与 `NEXUS_LLM_MOCK`，避免学员 shell 污染。

### run_smoke L37-41

延迟 import `e2e_smoke`，确保环境变量已 setdefault。

### main 决策 L44-73

argparse 两个 flag：`--serve`、`--skip-pytest`。失败即 return 1，不 serve。

## sprint3_demo.sh

```bash
#!/usr/bin/env bash
# Sprint 3 演示冒烟脚本 — Day 24
set -euo pipefail
cd "$(dirname "$0")/../nexus-agent-platform"
export PYTHONPATH=src
export NEXUS_LLM_MOCK=1

echo "=== Sprint 3 Demo Script ==="
python3 -m pytest tests/day22/ tests/day23/ tests/day24/ -q
python3 src/day24/e2e_smoke.py
python3 src/day24/sprint3_demo.py
echo ""
echo "启动服务: PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day24/sprint3_launch.py --serve"
```


Shell 脚本在仓库根 `scripts/`，cd 到 nexus-agent-platform 再跑 pytest。

## 设计权衡

| 选择 | 原因 |
|------|------|
| subprocess pytest | 与学员命令一致 |
| 默认不 serve | CI 无头 |
| print URL | 人类友好 |

精读完。

---

## argparse 设计笔记

`--skip-pytest` 默认 False 保证门禁；`--serve` 默认 False 保证 CI 不阻塞端口。若颠倒默认值，课堂将频繁端口冲突。

## uvicorn 参数

`reload=False` 避免教学时双进程困惑。开发自学可改 True。

精读扩展完。

---

## 智链科技 Day 24 读本附录：脚本精读

### 附录 1

本附录专属于 `25_sprint3_launch与demo脚本精读.md`，主题「脚本精读」。第 1 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 1 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：脚本精读相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 1 轮 CI 绿条是合并前提。

### 附录 2

本附录专属于 `25_sprint3_launch与demo脚本精读.md`，主题「脚本精读」。第 2 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 2 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：脚本精读相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 2 轮 CI 绿条是合并前提。

### 附录 3

本附录专属于 `25_sprint3_launch与demo脚本精读.md`，主题「脚本精读」。第 3 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 3 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：脚本精读相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 3 轮 CI 绿条是合并前提。

### 附录 4

本附录专属于 `25_sprint3_launch与demo脚本精读.md`，主题「脚本精读」。第 4 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 4 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：脚本精读相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 4 轮 CI 绿条是合并前提。

### 附录 5

本附录专属于 `25_sprint3_launch与demo脚本精读.md`，主题「脚本精读」。第 5 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 5 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：脚本精读相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 5 轮 CI 绿条是合并前提。

### 附录 6

本附录专属于 `25_sprint3_launch与demo脚本精读.md`，主题「脚本精读」。第 6 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 6 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：脚本精读相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 6 轮 CI 绿条是合并前提。

### 附录 7

本附录专属于 `25_sprint3_launch与demo脚本精读.md`，主题「脚本精读」。第 7 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 7 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：脚本精读相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 7 轮 CI 绿条是合并前提。

### 附录 8

本附录专属于 `25_sprint3_launch与demo脚本精读.md`，主题「脚本精读」。第 8 节强调：Sprint 3 收官日（ZL-NA-REQ-024）学员应把 **session 双端一致**、**errors 产品化**、**launch 门禁** 三件事串成闭环。林晓在第 8 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。陈默补充：版本 0.24.0 是课件契约，与仓库测试断言可能不同，口播须统一。赵岩要求：脚本精读相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。周航记录：第 8 轮 CI 绿条是合并前提。
