# Day 10 课件索引

**日期**：2026-07-15（星期三）  
**主题**：模块与异常 — 包结构重组  
**Sprint**：Sprint 2 第 3 天

## 配套代码

```bash
cd nexus-agent-platform
python3 src/day10/module_demos.py
python3 src/day10/exception_demos.py
python3 src/day10/structure_audit.py
python3 -m pytest tests/day10/ -v
```

## 今日交付物

- [x] `core/` — 异常体系、paths、bootstrap
- [x] `services/` — MessageHistoryService
- [x] `llm/`、`chat/`、`tools/` 骨架包
- [x] `PACKAGE_STRUCTURE.md` 包结构文档

## 上下文链

```
Day 9 BaseModel → Day 10 包重组 + 异常  ← 今日
Day 11 doc_reader → Day 12 llm/client
```
