# Day 11 实操 Lab 手册（Step-by-Step）

按步骤完成全天实验，约 3000 字。  
**环境**：`cd nexus-agent-platform` · `export PYTHONPATH=src`

---

## Lab 0：环境自检（5 分钟）

```bash
cd nexus-agent-platform
export PYTHONPATH=src
python3 -c "from tools.doc_reader import read_documents; from core.paths import get_path; print(len(read_documents(get_path('sample_docs'))))"
```

预期：打印 `3` 或更多（sample_docs 内 txt 数量）。

若失败：检查是否在项目根、PYTHONPATH 是否含 `src`。

---

## Lab 1：pathlib 基础（15 分钟）

```bash
python3 src/day11/file_demos.py
```

### 记录表

| 输出段 | 你观察到的值 |
|--------|--------------|
| 目录 exists | |
| parent.name | |
| 读写内容 repr | |
| st_size | |

### 追问

在 REPL 中执行：

```python
from core.paths import get_path
p = get_path("sample_docs")
list(p.glob("*.txt"))
```

与 `iter_text_files` 结果顺序是否一致？为何 demo 用后者？

<details><summary>提示</summary>iter_text_files 内含 sorted 与 StorageError 目录校验</details>

---

## Lab 2：glob 遍历（15 分钟）

```bash
python3 src/day11/glob_demos.py
```

手填：

- 文件数量：____  
- 最大文件名字：____  
- 其 stat().st_size：____  

### 扩展

修改本地副本（勿提交），加 `recursive=True` 测子目录（需自建 `sub/test.txt`）。

---

## Lab 3：编码回退（20 分钟）

```bash
python3 src/day11/encoding_demos.py
```

观察 `utf8.txt` 与 `gbk.txt` 的 `encoding=` 字段。

### 实验 A：破坏 UTF-8

```python
from pathlib import Path
from tools.doc_reader import read_text_file

p = Path("src/day11/sample_encoding/gbk.txt")
content, enc = read_text_file(p)
assert enc == "gbk"
```

### 实验 B：全失败

```bash
python3 -c "
from pathlib import Path
from tools.doc_reader import read_text_file
from core.exceptions import StorageError
p = Path('/tmp/day11_bad.bin')
p.write_bytes(bytes([0xff, 0xfe, 0x00, 0x01]))
try:
    read_text_file(p)
except StorageError as e:
    print('code:', e.code, 'path:', e.path)
"
```

---

## Lab 4：单文档清洗（20 分钟）

在 REPL：

```python
from core.paths import get_path
from tools.doc_reader import read_document

sample = list(get_path("sample_docs").glob("*.txt"))[0]
r = read_document(sample, clean=True, mask_phone=True)
print("encoding:", r.encoding)
print("replace_count:", r.stats.get("replace_count"))
print("phone_masked:", r.stats.get("phone_masked", 0))
print("cleaned preview:", (r.cleaned or "")[:80])
```

**检查**：`r.cleaned is not None`；敏感词应出现 `***`。

---

## Lab 5：批量清洗主流程（25 分钟）

```bash
python3 src/day11/doc_reader_demo.py
echo $?
```

### 验证输出目录

```bash
ls -la src/day11/output/
head -n 5 src/day11/output/cleaned_*.txt | head -20
```

### 对比 Day 3（可选）

若本地有 `src/day03/output/`，执行：

```bash
diff -r src/day03/output src/day11/output 2>/dev/null || echo "目录不同或不存在，跳过"
```

记录差异条数：____

---

## Lab 6：write_cleaned 边界（15 分钟）

```python
from pathlib import Path
from tools.doc_reader import read_document, write_cleaned_documents
from core.exceptions import StorageError
import tempfile

with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "t.txt"
    p.write_text("test", encoding="utf-8")
    rec = read_document(p, clean=False)
    try:
        write_cleaned_documents([rec], Path(td) / "out")
    except StorageError as e:
        print("预期错误:", e.message)
```

---

## Lab 7：pytest 全量（20 分钟）

```bash
python3 -m pytest tests/day11/ -v --tb=short
```

| 测试名 | 通过？ | 测什么（一句话） |
|--------|--------|------------------|
| test_read_text_file_utf8 | | |
| test_read_text_file_gbk_fallback | | |
| test_mask_phone_numbers | | |
| test_batch_clean_directory | | |
| ... | | |

目标：**12 passed**。

---

## Lab 8：batch_clean 源码跟踪（20 分钟）

1. 在 `batch_clean_directory` 第一行设断点  
2. 以调试模式运行 `doc_reader_demo.py`  
3. 单步进入 `read_documents` → `read_document` → `clean_text`  

画简图（纸笔）：调用栈深度与数据类型变化。

---

## Lab 9：路径注册（10 分钟）

打开 `src/core/paths.py`，找到：

```python
"sample_docs": SRC_ROOT / "day02" / "sample_docs",
"doc_output": SRC_ROOT / "day11" / "output",
```

在 REPL 验证：

```python
from core.paths import get_path
assert get_path("sample_docs").exists()
```

---

## Lab 10：晚自习脚本（30 分钟）

按 [07_晚自习.md](07_晚自习.md) 完成 `evening_glob.py` 骨架：

- 遍历 sample_docs  
- 打印 文件名 | 字节 | 编码  
- 统计总字节  

---

## Lab 完成检查清单

- [ ] file_demos / glob_demos / encoding_demos / doc_reader_demo 均退出码 0  
- [ ] `src/day11/output/cleaned_*.txt` 存在  
- [ ] pytest day11 全绿  
- [ ] 能口头解释 `read_text_file` 与 `path.read_text` 区别  
- [ ] 能说明 `StorageError.path` 用途  

---

## 故障转移

| 现象 | 文档 |
|------|------|
| 编码错误 | [10_常见问题与排错指南.md](10_常见问题与排错指南.md) Q1 |
| 目录不存在 | Q2 |
| 未清洗写出 | Q3 |

---

*课堂笔记：[05_课堂笔记_上午.md](05_课堂笔记_上午.md)、[06_课堂笔记_下午.md](06_课堂笔记_下午.md)*
