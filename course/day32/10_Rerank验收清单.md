# Day 32 Rerank 验收清单

- [ ] `MockCrossEncoderReranker` + `score_pair`  
- [ ] `RerankingRetriever` 两阶段 search  
- [ ] `RerankConfig.validate`  
- [ ] `store.json` 持久化 rerank_config  
- [ ] GET/PUT `/api/knowledge/rerank-config`  
- [ ] `_build_rag_service` 装配 RerankingRetriever  
- [ ] `tests/day32/` 18 项全绿  
- [ ] `rerank_demo.py` ✅  
- [ ] `rerank_api_demo.py` ✅  
- [ ] status 含 rerank_config  

**签字**：___________

---

## 功能验收（逐项）

| ID | 项 | 命令/方法 | 预期 |
|----|-----|-----------|------|
| AC-01 | 默认 enabled | GET rerank-config | true |
| AC-02 | 关 rerank | PUT enabled=false | 200 |
| AC-03 | 翻牌 | pytest test_mock_rerank_reorders | pass |
| AC-04 | 号码 | pytest test_phone_query_rerank | pass |
| AC-05 | chat | POST /api/chat | 200 |
| AC-06 | 版本 | GET /api/health | 0.32.0 |
| AC-07 | 持久化 | save/load store | pool 保留 |
| AC-08 | demo | rerank_demo.py | ✅ |
| AC-09 | inner | test_inner_hybrid | HybridRetriever |
| AC-10 | 422 | pool=0 | 422 |

---

## 非功能验收

- [ ] 全量 pytest ≥420 passed  
- [ ] 课件 regenerate ≥100k chars  
- [ ] CI Day32 job 绿  

---

## 回归范围

day23–day32 API version 断言；day31 hybrid 测试在 RerankingRetriever 外包下仍绿。

---

## 现场验收脚本

```bash
set -e
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day32/ -q
python3 src/day32/rerank_demo.py | grep -q "✅"
python3 src/day32/rerank_api_demo.py | grep -q "✅"
echo DAY32_OK
```

---

## hit@1 专项验收

- [ ] query 年化收益率可达 开启精排 top-1 含 8% 或年化  
- [ ] query 13900001111 top-1 含号码  
- [ ] PUT enabled=false 后 GET 一致  

---

## 学员能力达成

A：能配置 rerank-config  
B：能解释 score_pair  
C：能跑通 Lab 4 开关对比  
D：能教他人读 rerank_demo 双列
