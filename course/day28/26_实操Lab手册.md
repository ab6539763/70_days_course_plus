# Day 28 实操 Lab 手册

**分值**：100 分

## Step 0 环境（5 分）

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day28/ -q
```

## Step 1 观察重建前（10 分）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
print(s.chunk_count, s.chunk_config.name)
"
```

## Step 2 设置 wide 并 rebuild（25 分）

```bash
python3 src/day28/rebuild_demo.py | tee lab28_rebuild.txt
```

记录 chunks 变化：______ → ______

## Step 3 API rebuild（25 分）

```bash
python3 src/day28/rebuild_api_demo.py
```

截图含 `last_rebuilt_at`。

## Step 4 apply_best_config（20 分）

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \
  -H 'Content-Type: application/json' \
  -d '{"apply_best_config":true}' | jq '.chunk_config.name, .chunks_after'
```

## Step 5 chat 抽测（10 分）

```bash
curl -s -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"赎回多久到账","session_id":"lab28"}' | jq .
```

## Step 6 反思（5 分）

100 字：rebuild 与 Day 27 evaluate 分工。

## 教师勾选

- [ ] lab28_rebuild.txt 已交  
- [ ] chat 回答含 T+1 或赎回关键词  

## Lab 专属辅导

**Step 2**：若 chunks 前后不变，检查是否忘记 `set_chunk_config(wide)`。  
**Step 4**：`apply_best_config` 响应中 `chunk_config.name` 应与 Day 27 evaluate 一致。  
**Step 5**：chat 失败先查 session 是否需新 `session_id`。  
**常见扣分**：未提交 `lab28_rebuild.txt`；反思未对比 evaluate vs rebuild 写库差异。
