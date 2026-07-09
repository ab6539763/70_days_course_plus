"""
文档批量读取工具 — NexusAgent tools 层首个生产模块

使用 pathlib 遍历目录、读取文本文件，可选调用 utils.text_utils 清洗管道。
为 Day 28 RAG 文档加载流水线提供文件层能力。

需求：ZL-NA-REQ-011

运行示例：
    python3 -c "
    from tools.doc_reader import read_documents
    from core.paths import get_path
    docs = read_documents(get_path('sample_docs'))
    print(len(docs), 'files')
    "

作者：NexusAgent 项目组
创建日期：2026-07-16
版本：0.1.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from core.exceptions import StorageError
from utils.text_utils import clean_text

# 默认尝试的编码顺序（企业文档常见 UTF-8 / GBK）
DEFAULT_ENCODINGS = ("utf-8", "gbk", "gb2312", "latin-1")

# 手机号脱敏正则（Day 2 样本级简单规则，Day 11 正式启用）
_PHONE_PATTERN = re.compile(r"1\d{10}")


@dataclass
class DocumentRecord:
    """单份文档的读取结果"""

    path: Path
    content: str
    encoding: str
    size_bytes: int
    cleaned: str | None = None
    stats: dict = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.path.name


def read_text_file(path: Path, *, encodings: tuple[str, ...] = DEFAULT_ENCODINGS) -> tuple[str, str]:
    """
    读取单个文本文件，按编码列表依次尝试。

    Args:
        path: 文件路径
        encodings: 编码尝试顺序

    Returns:
        (文本内容, 实际使用的编码)

    Raises:
        StorageError: 文件不存在或全部编码解码失败
    """
    if not path.exists():
        raise StorageError(f"文件不存在: {path.name}", path=str(path))
    if not path.is_file():
        raise StorageError(f"路径不是文件: {path.name}", path=str(path))

    raw_bytes = _read_bytes(path)
    last_error: Exception | None = None

    for encoding in encodings:
        try:
            return raw_bytes.decode(encoding), encoding
        except UnicodeDecodeError as exc:
            last_error = exc
            continue

    raise StorageError(
        f"无法用 {encodings} 解码文件",
        path=str(path),
    ) from last_error


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise StorageError(f"读取失败: {exc}", path=str(path)) from exc


def iter_text_files(
    directory: Path,
    pattern: str = "*.txt",
    *,
    recursive: bool = False,
) -> Iterator[Path]:
    """
    遍历目录中的文本文件。

    Args:
        directory: 目标目录
        pattern: glob 模式，默认 *.txt
        recursive: 是否递归子目录（** 模式）

    Yields:
        匹配的文件路径（已排序）

    Raises:
        StorageError: 目录不存在
    """
    if not directory.exists():
        raise StorageError(f"目录不存在: {directory}", path=str(directory))
    if not directory.is_dir():
        raise StorageError(f"路径不是目录: {directory}", path=str(directory))

    glob_pattern = f"**/{pattern}" if recursive else pattern
    yield from sorted(directory.glob(glob_pattern))


def mask_phone_numbers(text: str) -> tuple[str, int]:
    """使用正则脱敏中国大陆 11 位手机号"""

    count = 0

    def _repl(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return "***PHONE***"

    masked = _PHONE_PATTERN.sub(_repl, text)
    return masked, count


def read_document(
    path: Path,
    *,
    clean: bool = False,
    to_lower: bool = False,
    mask_phone: bool = False,
    encodings: tuple[str, ...] = DEFAULT_ENCODINGS,
) -> DocumentRecord:
    """
    读取单份文档，可选清洗。

    Args:
        path: 文件路径
        clean: 是否执行 text_utils 清洗管道
        to_lower: 清洗时转小写
        mask_phone: 清洗后脱敏手机号
        encodings: 编码尝试顺序
    """
    content, encoding = read_text_file(path, encodings=encodings)
    record = DocumentRecord(
        path=path,
        content=content,
        encoding=encoding,
        size_bytes=path.stat().st_size,
    )

    if clean:
        cleaned, stats = clean_text(content, to_lower=to_lower)
        if mask_phone:
            cleaned, phone_count = mask_phone_numbers(cleaned)
            stats["phone_masked"] = phone_count
        record.cleaned = cleaned
        record.stats = stats

    return record


def read_documents(
    directory: Path,
    pattern: str = "*.txt",
    *,
    recursive: bool = False,
    clean: bool = False,
    to_lower: bool = False,
    mask_phone: bool = False,
) -> list[DocumentRecord]:
    """
    批量读取目录下匹配的文本文件。

    Returns:
        DocumentRecord 列表（按文件名排序）
    """
    records: list[DocumentRecord] = []
    for file_path in iter_text_files(directory, pattern, recursive=recursive):
        records.append(
            read_document(
                file_path,
                clean=clean,
                to_lower=to_lower,
                mask_phone=mask_phone,
            )
        )
    return records


def write_cleaned_documents(
    records: list[DocumentRecord],
    output_dir: Path,
    *,
    prefix: str = "cleaned_",
) -> list[Path]:
    """
    将清洗后的文档写入输出目录。

    Raises:
        StorageError: 记录未清洗或写入失败
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for record in records:
        if record.cleaned is None:
            raise StorageError(
                f"文档未清洗，无法写入: {record.name}",
                path=str(record.path),
            )
        out_path = output_dir / f"{prefix}{record.name}"
        try:
            out_path.write_text(record.cleaned, encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"写入失败: {exc}", path=str(out_path)) from exc
        written.append(out_path)

    return written


def batch_clean_directory(
    input_dir: Path,
    output_dir: Path,
    *,
    pattern: str = "*.txt",
    to_lower: bool = False,
    mask_phone: bool = True,
) -> list[DocumentRecord]:
    """
    批量读取、清洗并写出文档（Day 3 platform_cli 批处理的生产层替代）。

    Returns:
        已清洗的 DocumentRecord 列表
    """
    records = read_documents(
        input_dir,
        pattern,
        clean=True,
        to_lower=to_lower,
        mask_phone=mask_phone,
    )
    write_cleaned_documents(records, output_dir)
    return records
