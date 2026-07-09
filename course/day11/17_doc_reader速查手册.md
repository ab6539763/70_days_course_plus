# doc_reader 速查手册

**模块**：`nexus-agent-platform/src/tools/doc_reader.py`  
**需求**：ZL-NA-REQ-011

---

## 快速开始

```python
from core.paths import get_path
from tools.doc_reader import batch_clean_directory

records = batch_clean_directory(
    get_path("sample_docs"),
    get_path("doc_output"),
    mask_phone=True,
)
print(len(records))
```

---

## 常量

| 名称 | 值 | 说明 |
|------|-----|------|
| `DEFAULT_ENCODINGS` | `("utf-8", "gbk", "gb2312", "latin-1")` | 解码尝试顺序 |
| `_PHONE_PATTERN` | `1\d{10}` | 手机脱敏（模块内私有） |

---

## DocumentRecord

```python
@dataclass
class DocumentRecord:
    path: Path
    content: str
    encoding: str
    size_bytes: int
    cleaned: str | None = None
    stats: dict = field(default_factory=dict)

    @property
    def name(self) -> str  # path.name
```

---

## API 一览

### read_text_file

```python
content, encoding = read_text_file(
    path: Path,
    *,
    encodings: tuple[str, ...] = DEFAULT_ENCODINGS,
) -> tuple[str, str]
```

**Raises**: `StorageError` — 不存在 / 非文件 / 解码全失败

---

### iter_text_files

```python
for p in iter_text_files(
    directory: Path,
    pattern: str = "*.txt",
    *,
    recursive: bool = False,
) -> Iterator[Path]:
    ...
```

**Raises**: `StorageError` — 目录不存在或非目录

---

### mask_phone_numbers

```python
masked, count = mask_phone_numbers(text: str) -> tuple[str, int]
```

---

### read_document

```python
record = read_document(
    path: Path,
    *,
    clean: bool = False,
    to_lower: bool = False,
    mask_phone: bool = False,
    encodings: tuple[str, ...] = DEFAULT_ENCODINGS,
) -> DocumentRecord
```

| 参数 | 默认 | 说明 |
|------|------|------|
| clean | False | 调用 clean_text |
| to_lower | False | 清洗时转小写 |
| mask_phone | False | 清洗后脱敏手机 |

---

### read_documents

```python
records = read_documents(
    directory: Path,
    pattern: str = "*.txt",
    *,
    recursive: bool = False,
    clean: bool = False,
    to_lower: bool = False,
    mask_phone: bool = False,
) -> list[DocumentRecord]
```

---

### write_cleaned_documents

```python
paths = write_cleaned_documents(
    records: list[DocumentRecord],
    output_dir: Path,
    *,
    prefix: str = "cleaned_",
) -> list[Path]
```

**Raises**: `StorageError` — `cleaned is None` 或写入 OSError

---

### batch_clean_directory

```python
records = batch_clean_directory(
    input_dir: Path,
    output_dir: Path,
    *,
    pattern: str = "*.txt",
    to_lower: bool = False,
    mask_phone: bool = True,
) -> list[DocumentRecord]
```

---

## stats 字典键（clean=True）

| 键 | 含义 |
|----|------|
| raw_len | 原文长度 |
| clean_len | 清洗后长度 |
| replace_count | 敏感词替换次数 |
| empty_dropped | 丢弃空行数 |
| raw_lines | 原文行数 |
| clean_lines | 清洗后行数 |
| phone_masked | 手机脱敏次数（mask_phone=True） |

---

## 路径键（core/paths.py）

| key | 指向 |
|-----|------|
| sample_docs | src/day02/sample_docs |
| doc_output | src/day11/output |

---

## 异常

```python
from core.exceptions import StorageError

except StorageError as e:
    e.code   # "STORAGE_ERROR"
    e.path   # str | None
    e.message
```

---

## 命令行

```bash
cd nexus-agent-platform
python3 src/day11/doc_reader_demo.py
python3 -m pytest tests/day11/ -v
```

---

*深度：[11_文件IO与doc_reader详解.md](11_文件IO与doc_reader详解.md) · 精读：[25_doc_reader精读.md](25_doc_reader精读.md)*
