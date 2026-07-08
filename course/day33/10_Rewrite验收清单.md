# Day 33 Rewrite 验收清单

- [ ] `RuleBasedQueryRewriter` + `rewrite`  
- [ ] `RewritingRetriever` 三阶段 search  
- [ ] `RewriteConfig.validate`  
- [ ] `store.json` 持久化 rewrite_config  
- [ ] GET/PUT `/api/knowledge/rewrite-config`  
- [ ] `_build_rag_service` 装配 RewritingRetriever  
- [ ] `tests/day33/` 20 项全绿  
- [ ] `rewrite_demo.py` ✅  
- [ ] `rewrite_api_demo.py` ✅  
- [ ] status 含 rewrite_config  

**签字**：___________

---

## 功能验收（逐项）

| ID | 项 | 命令/方法 | 预期 |
|----|-----|-----------|------|
| AC-01 | 默认 enabled | GET rewrite-config | true |
| AC-02 | 关 rewrite | PUT enabled=false | 200 |
| AC-03 | 翻牌 | pytest test_mock_rewrite_reorders | pass |
| AC-04 | 号码 | pytest test_phone_query_rewrite | pass |
| AC-05 | chat | POST /api/chat | 200 |
| AC-06 | 版本 | GET /api/health | 0.32.0 |
| AC-07 | 持久化 | save/load store | pool 保留 |
| AC-08 | demo | rewrite_demo.py | ✅ |
| AC-09 | inner | test_inner_hybrid | HybridRetriever |
| AC-10 | 422 | pool=0 | 422 |

---

## 非功能验收

- [ ] 全量 pytest ≥420 passed  
- [ ] 课件 regenerate ≥100k chars  
- [ ] CI Day34 job 绿  

---

## 回归范围

day23–day34 API version 断言；day32 hybrid 测试在 RewritingRetriever 外包下仍绿。

---

## 现场验收脚本

```bash
set -e
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day33/ -q
python3 src/day33/rewrite_demo.py | grep -q "✅"
python3 src/day33/rewrite_api_demo.py | grep -q "✅"
echo DAY32_OK
```

---

## 口语命中 专项验收

- [ ] query 年化收益率可达 开启改写 top-1 含 8% 或年化  
- [ ] query 13900001111 top-1 含号码  
- [ ] PUT enabled=false 后 GET 一致  

---

## 学员能力达成

A：能配置 rewrite-config  
B：能解释 rewrite  
C：能跑通 Lab 4 开关对比  
D：能教他人读 rewrite_demo 双列
