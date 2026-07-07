# Day 11 pathlib 深度讲义

**课时**：约 90 分钟扩展讲座  
**目标**：系统掌握 `pathlib.Path` 在 NexusAgent 中的用法

---

## 第一章 Path 对象模型

### 1.1 类层次

```
PurePath（纯计算，无 IO）
  ├── PurePosixPath
  └── PureWindowsPath

Path（含 IO）
  ├── PosixPath   ← Linux/macOS
  └── WindowsPath
```

`Path("a/b")` 在 Linux 上构造 `PosixPath`。

### 1.2 不可变语义

`Path` 操作返回**新**对象：

```python
p = Path("/tmp/a.txt")
q = p.with_suffix(".md")  # p 不变
```

---

## 第二章 路径拼接与解析

### 2.1 `/` 运算符

```python
root = Path("/data")
docs = root / "docs" / "2026" / "report.txt"
```

右侧可为 `str` 或 `Path`；**左侧必须是 Path**。

### 2.2 常用变换

| 方法 | 示例结果 |
|------|----------|
| `.parent` | 父目录 |
| `.name` | `report.txt` |
| `.stem` | `report` |
| `.suffix` | `.txt` |
| `.with_name("x.txt")` | 换文件名 |
| `.with_suffix(".json")` | 换后缀 |
| `.resolve()` | 绝对路径 |
| `.relative_to(root)` | 相对路径 |

### 2.3 `core/paths.py` 实例

```python
SRC_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SRC_ROOT.parent
DATA_ROOT = SRC_ROOT / "data"
```

`__file__` 锚定源码树，避免 cwd 依赖。

---

## 第三章 存在性与类型判断

```python
p.exists()    # 路径存在（文件或目录）
p.is_file()
p.is_dir()
p.is_symlink()
```

**竞态**：`exists()` 与 `open()` 之间文件可能被删——企业代码仍须 try/except `StorageError`。

---

## 第四章 目录操作

```python
p.mkdir(parents=False, exist_ok=False)  # 单层
p.mkdir(parents=True, exist_ok=True)   # 递归，doc_reader 写出

# 删除（谨慎）
p.unlink()          # 文件
p.rmdir()           # 空目录
# shutil.rmtree     # 非 pathlib，删树
```

`iterdir()` 列举直接子项；`glob` / `rglob` 模式匹配。

---

## 第五章 glob 与 rglob

```python
list(Path("sample_docs").glob("*.txt"))       # 当前层
list(Path("sample_docs").glob("**/*.txt"))    # 递归
list(Path("sample_docs").rglob("*.txt"))       # 等价 **/
```

`doc_reader.iter_text_files` 封装了 recursive 开关与 sorted。

### 5.1 模式语法速查

| 模式 | 含义 |
|------|------|
| `*` | 任意非分隔符 |
| `**` | 任意层级（需 recursive / rglob） |
| `?` | 单字符 |
| `[abc]` | 字符集 |

---

## 第六章 文本与二进制 IO

```python
# 文本
text = path.read_text(encoding="utf-8")
path.write_text(text, encoding="utf-8")

# 二进制
data = path.read_bytes()
path.write_bytes(data)
```

### 6.1 encoding 参数

Python 3.10+ `open` 默认 `encoding="utf-8"`（locale 仍可能干扰）；**企业代码显式写 utf-8**。

### 6.2 与 doc_reader 分工

| 层 | 职责 |
|----|------|
| Path.read_bytes | 原始字节 |
| read_text_file | 编码回退 |
| Path.write_text | 已知 UTF-8 写出 |

---

## 第七章 stat 与元数据

```python
st = path.stat()
st.st_size      # 字节
st.st_mtime     # 修改时间
st.st_ctime     # 平台相关
```

`DocumentRecord.size_bytes` 在读取时快照，后续文件变更不会自动更新。

---

## 第八章 PathLike 协议

任何实现 `__fspath__()` 的对象可传给 `open()`：

```python
os.fspath(Path("a"))  # 'a'
```

---

## 第九章 反模式清单

| 反模式 | 后果 |
|--------|------|
| `str` 拼 `"/" + name` | Windows 失败 |
| 不 resolve 就比较路径 | 相对/绝对混淆 |
| glob 后不 sorted | 测试 flaky |
| read_text 读 GBK | UnicodeDecodeError |

---

## 第十章 综合练习

实现函数：

```python
def find_largest_txt(directory: Path) -> Path | None:
    """返回目录下最大的 .txt 文件 Path，无则 None"""
```

提示：`iter_text_files` + `stat().st_size` + `max(..., key=)`。

---

## 第十一章 与 os 模块桥接

```python
import os
os.listdir(path)           # path 可为 Path
os.rename(old, new)        # Path 均可
subprocess.run(["cat", path])  # 需 str(path)
```

---

*实操：[26_实操Lab手册.md](26_实操Lab手册.md) · 上午笔记：[05_课堂笔记_上午.md](05_课堂笔记_上午.md)*
