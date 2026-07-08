# Day 11 课件索引

**日期**：2026-07-16（星期四）  
**主题**：文件与标准库 — 文档批量读取  
**Sprint**：Sprint 2 第 4 天

## 配套代码

```bash
cd nexus-agent-platform
python3 src/day11/file_demos.py
python3 src/day11/glob_demos.py
python3 src/day11/encoding_demos.py
python3 src/day11/doc_reader_demo.py
python3 -m pytest tests/day11/ -v
```

## 今日交付物

- [x] `tools/doc_reader.py` — 批量读文档 + 可选清洗
- [x] `DocumentRecord` 数据类
- [x] `core/paths.py` 注册 sample_docs / doc_output
- [x] Day 11 演示脚本与 12 项单元测试

## 上下文链

```
Day 10 包重组 → Day 11 doc_reader  ← 今日
Day 12 llm/client → Day 14 cli_assistant
```
