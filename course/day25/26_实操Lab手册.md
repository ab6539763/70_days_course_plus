# Day 25 实操 Lab 手册

**需求**：ZL-NA-REQ-025 | **时长**：90 分钟

---

## Lab 0：环境（10 min）

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 -m pytest tests/day25/ -v
```

**通过**：17 passed

---

## Lab 1：ingestion_demo（10 min）

```bash
python3 src/day25/ingestion_demo.py
```

记录 ingest 前后 `chunk_count`。

---

## Lab 2：knowledge_api_demo（10 min）

```bash
python3 src/day25/knowledge_api_demo.py
```

观察 TestClient upload 响应 JSON。

---

## Lab 3：启动服务（10 min）

```bash
python3 src/day24/sprint3_launch.py --serve --skip-pytest
```

访问 `/` 与 `/docs`。

---

## Lab 4：Swagger 上传（15 min）

1. `POST /api/knowledge/upload` Try it out  
2. 选 `custom_faq.txt`  
3. 确认 200 与 `sessions_cleared`  

<details><summary>期望字段</summary>filename, chunk_count, total_chunks, sessions_cleared, message</details>

---

## Lab 5：浏览器侧栏（15 min）

1. 打开知识库面板  
2. 上传文件  
3. 状态行更新  
4. 聊天提问「最低起购金额」  

---

## Lab 6：store.json 审计（10 min）

```bash
python3 -c "import json; d=json.load(open('data/knowledge/store.json')); print(len(d['chunks']), d.get('version'))"
```

---

## Lab 7：故障注入（10 min）

上传空 txt → 期望 422  

<details><summary>排错提示</summary>查 API 返回 detail 字段文案</details>

---

## 提交物

- `lab_log.md` 含 7 步截图或输出  
- pytest 全绿截图  

Lab 完。

---

## Lab 8：factory 注入验证（加分 10 min）

```python
# homework/day25/factory_check.py
from api.factory import create_orchestrator
from rag.knowledge_store import get_knowledge_store
o = create_orchestrator()
ctx = get_knowledge_store().as_rag_service().retrieve_context("起购")
print("ok", len(ctx) > 0)
```

---

## Lab 9：损坏 UTF-8 实验（加分）

写入 Latin-1 字节上传，观察 400 响应 detail。

---

## Lab 评分 Rubric 详表

| 项 | 优秀 | 良好 | 及格 |
|----|------|------|------|
| pytest | 17 绿 | 15+ | 12+ |
| upload | 含 sessions_cleared | 200 无 chat | TestClient 过 |
| chat 命中 | 两问句 | 一问句 | 无 |



---

## 附录：Lab 评分（Lab 专节）

| Lab | 分值 |
|-----|------|
| 0–3 | 各 10 |
| 4–5 | 各 15 |
| 6–7 | 各 10 |

迟交 Lab 日志扣 20%。

Lab 附录完。

---

## 附录：Lab 互评表（Lab vol2）

两人互换 `lab_log.md`，按检查点评分。互评占 Lab 成绩 20%。重点看 Lab 5 是否证明 chat 命中上传内容。

Lab vol2 完。

---

## Lab 助教配置

每台助教机预装 venv、导入 sample faq、预跑 pytest 节省课堂时间。

---

## 互评表

Lab 互评三项：pytest 绿、upload 截图、chat 命中。每项 pass/fail。互评完。
