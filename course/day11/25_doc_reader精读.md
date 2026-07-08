# Day 11 doc_reader 精读

**文件**：`nexus-agent-platform/src/tools/doc_reader.py`  
**方法**：慢读 + 提问 + 自答  
**需求**：ZL-NA-REQ-011

---

## 精读说明

本文按源码顺序「逐段咀嚼」，适合打印后在代码旁批注。行号以仓库当前版本为准（约 258 行）。

---

## 模块文档字符串（L1-L20）

```python
"""
文档批量读取工具 — NexusAgent tools 层首个生产模块
...
需求：ZL-NA-REQ-011
"""
```

**自问**：为何强调「首个生产模块」？  
**自答**：Day 10 创建 tools 空包；今日证明 tools 层可承载可测试、可被 RAG 复用的能力，而非堆在 dayXX。

运行示例使用 `get_path('sample_docs')`——与文档字符串一致，复制即可跑。

---

## 导入段（L22-L30）

```python
from core.exceptions import StorageError
from utils.text_utils import clean_text
```

**依赖审计**：

- ✓ core, utils  
- ✗ 无 models, services, dayXX  

`re` 仅用于手机脱敏，不引入 `regex` 第三方库。

---

## DEFAULT_ENCODINGS（L32-L33）

元组不可变，防止运行时被篡改。若需租户级配置，Day 28 改为参数或配置文件，而非 mutate 全局。

---

## _PHONE_PATTERN（L35-L36）

编译一次，多次 `sub` 复用。`r"1\d{10}"` 原始字符串避免 `\d` 转义错误。

---

## DocumentRecord（L39-L52）

### L43-L48 字段顺序

`path` → `content` → `encoding` → `size_bytes` 是「读取即可得」；`cleaned` / `stats` 是衍生数据。

### L50-L52 name 属性

```python
@property
def name(self) -> str:
    return self.path.name
```

避免模板层接触 `Path` 细节；若未来改为 S3 URI，`name` 可改为末段逻辑而不动调用方。

---

## read_text_file 精读

### L69-L72 前置条件

先 `exists` 再 `is_file`：若路径是目录，`exists` 真但 `is_file` 假——第二条 StorageError 更准确。

### L74-L75 读字节

**关键设计**：不假设编码，整文件进内存。MVP 文件小，简化逻辑。

### L77-L82 解码循环

```python
for encoding in encodings:
    try:
        return raw_bytes.decode(encoding), encoding
    except UnicodeDecodeError as exc:
        last_error = exc
        continue
```

**只捕 UnicodeDecodeError**：`LookupError`（非法编码名）应直接失败，暴露配置错误。

### L84-L87 终极失败

`from last_error` — pytest 可断言 `__cause__` 链。

---

## _read_bytes（L90-L94）

单一职责：字节 IO 与 StorageError 转换。未来加重试（NFS 瞬断）可只改此处。

---

## iter_text_files（L97-L123）

### L117-L120 目录校验

与 `read_text_file` 文件校验对称。

### L122-L123 glob

```python
glob_pattern = f"**/{pattern}" if recursive else pattern
yield from sorted(directory.glob(glob_pattern))
```

`yield from` 保持生成器惰性；调用方 `list()` 才执行磁盘遍历。

**性能注记**：大目录 `sorted` 有 O(n log n) 成本；当前样本目录 n 小。

---

## mask_phone_numbers（L126-L137）

`nonlocal count` 是 Python 闭包经典模式。若改用 `re.subn`，可简化但当前实现教学价值更高。

---

## read_document（L140-L174）

### L158-L164 构造记录

`size_bytes` 在清洗前取自磁盘，反映**原始文件**大小，非清洗后字符串长度。

### L166-L172 清洗分支

```python
if clean:
    cleaned, stats = clean_text(content, to_lower=to_lower)
    if mask_phone:
        cleaned, phone_count = mask_phone_numbers(cleaned)
        stats["phone_masked"] = phone_count
```

**顺序不可颠倒**：先敏感词清洗再手机脱敏。`mask_phone` 嵌套在 `if clean` 内——`clean=False` 时 `mask_phone=True` 无效（API 文档需说明）。

---

## read_documents（L177-L202）

纯编排，无新逻辑。列表追加顺序 = `iter_text_files` 排序顺序。

---

## write_cleaned_documents（L205-L233）

### L217 mkdir

`exist_ok=True` 避免并发创建竞态报错。

### L221-L225 业务校验

比文件系统层更早失败，错误信息含 `record.name` 人类可读。

### L228 UTF-8

清洗后内部已是 `str`，写出编码与源文件 `encoding` 字段无关——**归一化**策略。

---

## batch_clean_directory（L236-L258）

```python
mask_phone: bool = True,
```

企业默认脱敏；若科研样本需保留号码，显式传 `False` 并走审批。

三行组合体现 **composition over inheritance**——无类层次，仅函数组合。

---

## 精读习题

1. 在 `read_document` 中加 `max_size_bytes` 参数应插在哪一行之前？  
2. 如何用 5 行代码只统计目录行数而不清洗？  
3. `stats["replace_count"]` 来自哪个函数？  

<details>
<summary>参考答案</summary>

1. 在 `read_text_file` 之后、`read_bytes` 之后检查 `len(raw_bytes)` 或 `stat.st_size`  
2. `sum(len(read_document(p, clean=False).content.splitlines()) for p in iter_text_files(d))`  
3. `utils.text_utils.clean_text` 内 `mask_sensitive_words` 累加  

</details>

---

## 与测试用例逐条对应

阅读 `tests/day11/test_doc_reader.py` 时，在每条 assert 旁标注对应函数行号——建议作为晚自习作业。

---

*速查：[17_doc_reader速查手册.md](17_doc_reader速查手册.md) · 走查：[20_完整代码走查.md](20_完整代码走查.md)*
