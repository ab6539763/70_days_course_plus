# Day 37 Expansion 验收清单

- [ ] `Citation` + `RuleBasedQueryRouter.route`  
- [ ] `RoutingRetriever.search` + rewrite 元数据  
- [ ] `RouteConfig.validate`  
- [ ] `store.json` 持久化 citation_config  
- [ ] GET/PUT `/api/knowledge/route-config`  
- [ ] POST `/api/knowledge/citation-preview`  
- [ ] `api/chat` 返回 expansion.queries + merged citations + rewrite  
- [ ] `tests/day37/` 20 项全绿  
- [ ] `route_demo.py` ✅  
- [ ] `route_api_demo.py` ✅  
- [ ] 前端 `msg__route` 展示  

**签字**：___________

---

## 功能验收（逐项）

| ID | 项 | 命令/方法 | 预期 |
|----|-----|-----------|------|
| AC-01 | 默认 enabled | GET route-config | true |
| AC-02 | 关 citations | PUT enabled=false | 200 |
| AC-03 | 构建引用 | pytest test_RuleBasedQueryRouter.route_from_results | pass |
| AC-04 | rewrite 元数据 | pytest test_RoutingRetriever.search_rewrite_meta | pass |
| AC-05 | chat | POST /api/chat | citations 非空 |
| AC-06 | 版本 | GET /api/health | 0.37.0 |
| AC-07 | 持久化 | save/load store | max_citations 保留 |
| AC-08 | demo | route_demo.py | ✅ |
| AC-09 | preview | citation-preview | ≥1 source |
| AC-10 | 422 | max_citations=0 | 422 |

---

## 非功能验收

- [ ] 全量 pytest ≥490 passed  
- [ ] 课件 regenerate ≥100k chars  
- [ ] CI Day38 job 绿  

---

## 回归范围

day23–day37 API version 断言；day33 rewrite 测试在完整检索栈下仍绿。

---

## 现场验收脚本

```bash
set -e
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day37/ -q
python3 src/day37/route_demo.py | grep -q "✅"
python3 src/day37/route_api_demo.py | grep -q "✅"
echo DAY36_OK
```

---

## 自适应路由专项验收

- [ ] query 年化收益率 citations[0] 含 source 与 preview  
- [ ] include_route_meta=true 时含 rewrite 字段  
- [ ] PUT enabled=false 后 chat citations=[]  

---

## 学员能力达成

A：能配置 route-config  
B：能解释 citations 字段  
C：能跑通 Lab 4 citation-preview  
D：能教他人读 route_demo 输出
