# Day 10 实操 Lab 手册（Step-by-Step）

按步骤完成下午实验，约 3000 字。

---

## Lab 1：验证 PYTHONPATH（10 分钟）

```bash
cd nexus-agent-platform
unset PYTHONPATH
python3 -c "import models" 2>&1 || echo "预期失败"
export PYTHONPATH=src
python3 -c "from models import ChatMessage; print('OK')"
```

**结论**：生产脚本必须保证 `src` 在 path 上。

---

## Lab 2：运行 module_demos（15 分钟）

```bash
python3 src/day10/module_demos.py
```

记录输出四段：__name__、import 风格、bootstrap、包目录。  
**问题**：`llm` 包状态应为 OK。

---

## Lab 3：异常演示（20 分钟）

```bash
python3 src/day10/exception_demos.py
```

分别观察：

1. ModelValidationError 的 code  
2. NexusError 基类捕获三种子类  
3. ValueError 兼容捕获  
4. `__cause__` 链  

**练习**：修改 `exception_demos.py` 触发 `ConfigError`，观察 `[CONFIG_ERROR]` 前缀。

---

## Lab 4：structure_audit（10 分钟）

```bash
python3 src/day10/structure_audit.py
echo "退出码: $?"
```

若失败，根据 ❌ 提示补 `__init__.py`。

---

## Lab 5：services 加载消息（20 分钟）

```python
from core.bootstrap import setup_python_path
setup_python_path()
from core.paths import get_path
from services import MessageHistory

h = MessageHistory.load_json(get_path("messages"))
print(len(h), "条消息")
for m in h.messages:
    print(m.format_line())
```

---

## Lab 6：pytest 回归（15 分钟）

```bash
python3 -m pytest tests/day10/ -v
python3 -m pytest tests/day08/test_chat_message.py -v
```

确认迁移未破坏 Day 8。

---

## Lab 7：阅读 PACKAGE_STRUCTURE（15 分钟）

打开 `PACKAGE_STRUCTURE.md`，完成 [25_PACKAGE_STRUCTURE精读.md](25_PACKAGE_STRUCTURE精读.md) 作业。

---

## 验收标准

- [ ] 六个 Lab 全部执行  
- [ ] structure_audit 退出码 0  
- [ ] day10 + day08 测试全绿  
- [ ] 能口头解释 core vs services  

---

*实验总计约 105 分钟，含休息。*
