# Day 27 实操 Lab 手册

**时长**：120 分钟 | **分值**：100 分（计入平时成绩）

## 环境准备（5 分）

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

检查：`python3 -c "from day27.constants import EVAL_QUERIES; print(len(EVAL_QUERIES))"` 输出 4。

## 步骤 1：CLI A/B（15 分）

```bash
python3 src/day27/ab_experiment_demo.py | tee lab27_ab.txt
```

**交付**：`lab27_ab.txt` 含四套 PRESET 输出。  
**评分**：文件存在且含 hit_rate 行。

## 步骤 2：找出 best_config（15 分）

从输出填写：

- 推荐配置名：________  
- 其 hit_rate：________  
- 其 chunk_count：________  

## 步骤 3：API evaluate（20 分）

终端 1：

```bash
uvicorn api.app:create_app --factory --port 8000
```

终端 2：

```bash
python3 src/day27/chunk_tune_api_demo.py
```

**评分**：截图含 PUT 与 POST evaluate 成功。

## 步骤 4：持久化验证（20 分）

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/chunk-config \
  -H 'Content-Type: application/json' \
  -d '{"chunk_size":350,"overlap":50,"strategy":"auto","name":"lab_wide"}'

curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.chunk_config'
```

重启服务后再次 GET，确认 chunk_size 仍为 350。

## 步骤 5：pytest（15 分）

```bash
pytest tests/day27/ -q --tb=no
```

要求：全部 passed。

## 步骤 6：反思报告（10 分）

200 字：为何 evaluate 后 chunk_count 不变？若要让全库用 lab_wide，明天该调用什么 API？

## 教师验收勾选

- [ ] 步骤 1–6 齐全  
- [ ] 无抄袭 lab 文件  
- [ ] 反思提到 rebuild  

## Lab 专属辅导（不与作业重复）

**步骤 2 常见错误**：把 ab 输出中 `avg_top_score` 最高误认为最优 —— 排序第一键是 hit_rate。  
**步骤 4 常见错误**：未重启 uvicorn 就断言持久化失败。  
**步骤 6 优秀反思范例**：evaluate 只改内存 retriever；PUT 只改默认配置字段；全库块变化需 Day 28 `POST /rebuild`。
