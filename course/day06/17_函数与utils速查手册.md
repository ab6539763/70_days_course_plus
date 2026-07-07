# Day 6 函数与 utils 速查手册

## 一、函数定义模板

```python
def function_name(arg1: str, arg2: int = 0, *args, **kwargs) -> dict:
    """
    一句话说明

    Args:
        arg1: 说明
        arg2: 说明，默认 0

    Returns:
        说明返回值
    """
    ...
```

## 二、参数速查

| 语法 | 含义 | 示例 |
|------|------|------|
| `a, b` | 位置参数 | `add(1, 2)` |
| `c=0` | 默认参数 | `connect(host, port=5432)` |
| `*args` | 多余位置参数 → tuple | `log("m", 1, 2)` |
| `**kwargs` | 多余关键字 → dict | `f(x=1, y=2)` |
| `*, x` | x 必须关键字传递 | `save(p, d, indent=2)` |

## 三、返回值模式

| 模式 | 示例 | 用途 |
|------|------|------|
| 单值 | `return 42` | 计算结果 |
| 多值 tuple | `return a, b` | 统计多项 |
| 错误消息 | `return None` / `return "错误"` | validators |
| 提前退出 | `return` 在 if 内 | 卫语句 |

## 四、作用域关键字

| 关键字 | 作用 |
|--------|------|
| `global x` | 函数内修改模块级变量 |
| `nonlocal x` | 内层函数修改外层闭包变量 |

## 五、lambda 常用场景

```python
sorted(items, key=lambda x: x["priority"])
sorted(items, key=lambda x: (x["done"], -x["priority"]))
map(lambda s: s.strip(), lines)
filter(lambda x: x > 0, nums)
```

## 六、utils 模块 API 一览

### text_utils

| 函数 | 返回 |
|------|------|
| `collapse_whitespace(text)` | str |
| `collapse_duplicate_punctuation(text)` | str |
| `mask_sensitive_words(text, words=None)` | `(str, int)` |
| `clean_text(raw, *, to_lower=False, sensitive_words=None)` | `(str, dict)` |

### json_utils

| 函数 | 返回 |
|------|------|
| `load_json(path, default=None)` | Any |
| `save_json(path, data, *, indent=2)` | None |
| `ensure_dict_keys(data, defaults)` | dict |

### validators

| 函数 | 返回 |
|------|------|
| `require_non_empty(value, field_name="字段")` | `str \| None` |
| `parse_priority(value, default=2)` | int 1/2/3 |
| `parse_positive_int(value)` | `int \| None` |
| `validate_email(email)` | `str \| None` |

### formatters

| 函数 | 返回 |
|------|------|
| `format_box_report(title, lines, width=42)` | str |
| `format_todo_line(todo)` | str |

## 七、优先级与显示

| 存储值 | 标签 |
|--------|------|
| 1 | 高 |
| 2 | 中 |
| 3 | 低 |

`format_todo_line` 输出示例：`[ ] #3 [中] 完成 utils 测试`

## 八、运行与测试命令

```bash
cd nexus-agent-platform
python3 src/day06/function_demos.py
PYTHONPATH=src python3 src/day06/todo_manager_v3.py
python3 -m pytest tests/test_utils.py tests/day06/ -v
python3 -m pytest tests/ -v
```

## 九、与前后 Day 衔接

| Day | 产出 | Day 6 关系 |
|-----|------|------------|
| Day 2 | text_cleaner | → text_utils |
| Day 5 | todo_storage, v2 | → json_utils, v3 |
| Day 7 | 通讯录 | 复用 validators |
| Day 8 | 类与模块 | utils 变 package |

## 十、反模式清单

1. 在 utils 里 `print` — 应返回字符串或抛异常
2. 默认参数用 `[]` / `{}` — 用 None 代替
3. 业务逻辑塞进 utils — 留在 todo_manager
4. 循环 import — utils 不 import dayXX
5. 上帝函数超过 80 行 — 拆成多个小函数

---

*打印本页贴显示器旁，编码时快速查阅。*
