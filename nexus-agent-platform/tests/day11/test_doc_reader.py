"""Day 11 doc_reader 与文件 IO 测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.exceptions import StorageError
from core.paths import get_path
from tools.doc_reader import (
    DocumentRecord,
    batch_clean_directory,
    iter_text_files,
    mask_phone_numbers,
    read_document,
    read_documents,
    read_text_file,
    write_cleaned_documents,
)


def test_read_text_file_utf8(tmp_path):
    path = tmp_path / "hello.txt"
    path.write_text("你好 NexusAgent", encoding="utf-8")
    content, enc = read_text_file(path)
    assert content == "你好 NexusAgent"
    assert enc == "utf-8"


def test_read_text_file_gbk_fallback(tmp_path):
    path = tmp_path / "gbk.txt"
    path.write_bytes("中文".encode("gbk"))
    content, enc = read_text_file(path)
    assert "中文" in content
    assert enc == "gbk"


def test_read_text_file_not_found(tmp_path):
    with pytest.raises(StorageError) as exc:
        read_text_file(tmp_path / "missing.txt")
    assert exc.value.code == "STORAGE_ERROR"


def test_iter_text_files_sorted(tmp_path):
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    names = [p.name for p in iter_text_files(tmp_path)]
    assert names == ["a.txt", "b.txt"]


def test_iter_text_files_missing_dir(tmp_path):
    with pytest.raises(StorageError):
        list(iter_text_files(tmp_path / "nope"))


def test_mask_phone_numbers():
    text = "联系 13812345678 或 13900001111"
    masked, count = mask_phone_numbers(text)
    assert count == 2
    assert "13812345678" not in masked
    assert "***PHONE***" in masked


def test_read_document_with_clean(tmp_path):
    path = tmp_path / "doc.txt"
    path.write_text("  内部资料！！！  \n\n", encoding="utf-8")
    record = read_document(path, clean=True, mask_phone=False)
    assert record.cleaned is not None
    assert "***" in record.cleaned
    assert record.stats["replace_count"] >= 1


def test_read_documents_sample_docs():
    docs = read_documents(get_path("sample_docs"))
    assert len(docs) >= 3
    assert all(isinstance(d, DocumentRecord) for d in docs)


def test_write_cleaned_documents(tmp_path):
    src = tmp_path / "in.txt"
    src.write_text("内部资料 test", encoding="utf-8")
    record = read_document(src, clean=True)
    out_dir = tmp_path / "out"
    paths = write_cleaned_documents([record], out_dir)
    assert len(paths) == 1
    assert paths[0].read_text(encoding="utf-8")


def test_write_cleaned_without_clean_raises(tmp_path):
    path = tmp_path / "raw.txt"
    path.write_text("x", encoding="utf-8")
    record = read_document(path, clean=False)
    with pytest.raises(StorageError):
        write_cleaned_documents([record], tmp_path / "out")


def test_batch_clean_directory(tmp_path):
    (tmp_path / "a.txt").write_text("内部资料 13812345678", encoding="utf-8")
    out = tmp_path / "output"
    records = batch_clean_directory(tmp_path, out)
    assert len(records) == 1
    assert (out / "cleaned_a.txt").exists()


def test_get_path_sample_docs():
    p = get_path("sample_docs")
    assert p.name == "sample_docs"
    assert p.exists()
