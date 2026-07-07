# Day 29 Chroma 验收清单

**版本**：v0.29.0 | **教师勾选**

## 代码交付

- [ ] `rag/chroma_store.py` 存在且 `VECTOR_BACKEND == "chroma"`  
- [ ] `rag/chroma_retriever.py` 实现 `search()`  
- [ ] `knowledge_store._rebuild_index` 调用 `chroma.reset` + upsert  
- [ ] `knowledge_store._sync_chroma_from_json` 实现冷启动  
- [ ] `requirements-api.txt` 含 chromadb  

## 测试

- [ ] `pytest tests/day29/test_chroma_index.py` 全绿（10 项）  
- [ ] `pytest tests/day29/test_chroma_api.py` 全绿（5 项）  
- [ ] `test_chroma_matches_in_memory_retriever_top1` 通过  

## API

- [ ] `GET /api/knowledge/status` 含 `vector_backend`, `chroma_path`, `chroma_count`  
- [ ] `POST /api/knowledge/rebuild` 后 `chroma_count == chunks_after`  
- [ ] `POST /api/chat` 检索正常  

## 演示脚本

- [ ] `python3 src/day29/chroma_demo.py` 打印 ✅  
- [ ] `python3 src/day29/chroma_api_demo.py` 打印 ✅  

## 课件

- [ ] 30 篇课件齐全  
- [ ] `22_chroma_store精读.md` 含完整源码  
- [ ] 学员 Lab 报告 ≥ 1 份归档  

**验收签字**：___________  **日期**：___________

---

## 验收场景脚本（教师现场）

```bash
set -e
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day29/ -q
python3 src/day29/chroma_demo.py | grep -q "✅"
python3 src/day29/chroma_api_demo.py | grep -q "✅"
echo "DAY29_ACCEPTANCE_OK"
```

---

## 常见验收失败与处置

| 失败项 | 处置 |
|--------|------|
| chroma_count 偏差 | rebuild + 查 JSON chunks |
| import chromadb | pip install -r requirements-api.txt |
| chat 空回复 | 查 embedding_state 是否空 |
| version 不匹配 | 查 PLATFORM_VERSION 常量 |

---

## 学员签字确认

本人已完成 Lab 六步并理解双存储备份要求：___________ 日期 _______
