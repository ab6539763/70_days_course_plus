# Day 23 实操 Lab 手册

**需求**：ZL-NA-REQ-023  
**时长**：90 分钟  
**环境**：nexus-agent-platform + frontend

---

## Lab 0：环境准备（10 min）

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
export PYTHONPATH=src
export NEXUS_LLM_MOCK=1
python3 -m pytest tests/day23/test_api_chat.py -v
```

**通过标准**：12 passed

---

## Lab 1：健康检查（10 min）

```bash
python3 src/day23/api_health_demo.py
curl -s http://127.0.0.1:8000/api/health | jq
```

记录 `version` 与 `mock_llm`。

---

## Lab 2：启动服务（10 min）

```bash
python3 src/day23/run_server.py
```

浏览器访问：

- `http://127.0.0.1:8000/`  
- `http://127.0.0.1:8000/docs`  

---

## Lab 3：Swagger 调试（15 min）

1. 打开 `/docs`  
2. 展开 `POST /api/chat`  
3. Try it out，body：`{"message":"投资有风险吗"}`  
4. 确认 `kind=faq`  

再试 `{"message":""}`，确认 422。

---

## Lab 4：浏览器 Network（15 min）

1. F12 → Network  
2. 发送「帮我总结要点」  
3. 截图 Response JSON  
4. 对比气泡标签与 `kind`  

---

## Lab 5：api_chat_demo（10 min）

```bash
python3 src/day23/api_chat_demo.py
```

将终端输出粘贴到 `lab5_output.txt`。

---

## Lab 6：session_id 实验（10 min）

```bash
curl -s -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"你好","session_id":"lab-user-1"}' | jq .session_id

curl -s -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"再见","session_id":"lab-user-1"}' | jq .session_id
```

两次应均为 `lab-user-1`。

---

## Lab 7：Mock 回退（10 min）

1. 停 uvicorn  
2. `cd frontend && python3 -m http.server 8080`  
3. 访问 `http://127.0.0.1:8080/?mock=1`  
4. 确认走 Mock；访问无参数时 fetch 失败（预期）  

理解 config.js 意义。

---

## Lab 8：classify_reply 单测（10 min）

```bash
python3 -c "
from api.response_parser import classify_reply
cases = [
    '[FAQ 直答·70%] x',
    '[路由: rag_qa] y',
    'plain',
]
for c in cases:
    print(c, '->', classify_reply(c))
"
```

---

## 验收

| Lab | 交付物 |
|-----|--------|
| 0 | pytest 截图 |
| 4 | Network 截图 |
| 5 | lab5_output.txt |
| 6 | 两条 curl 输出 |

---

## 故障排除

见 [17_FastAPI速查手册.md](17_FastAPI速查手册.md)。

Lab 手册完。

---

## Lab 9：Swagger 与 curl 对照（选修，15 min）

同一 body `{"message":"投资有风险吗"}` 分别在 Swagger 与 curl 执行，diff 两份 JSON 的 key 顺序（应一致）与 kind（应一致）。理解「工具不同，契约相同」。林晓记录：Swagger 自动加 Content-Type，curl 须手写，遗漏则 422 或 415。

## Lab 10：故障注入（选修，10 min）

临时设 `NEXUS_LLM_MOCK=0` 且无真实 Key，观察 500 响应形状（若触发 ConfigError）。**实验后恢复 MOCK=1**。体会错误 JSON 对前端 catch 的影响。赵岩要求：故障实验仅限本地，禁止对共享演示机操作。

## 智链科技 Lab 评分手册

| Lab | 分值 | 要点 |
|-----|------|------|
| 0 | 15 | 12 passed 截图 |
| 4 | 20 | Network JSON |
| 6 | 15 | session_id 一致 |
| 其余 | 通过/不通过 | 助教勾选 |

Lab 扩展完。培训部 2026-07-28。

---

## Lab 11 至 13 选修

Lab 11：对比 8080 静态与 8000 API 同一问句 reply 差异，写三百字报告。Lab 12：阅读 factory.py 全文，画出依赖箭头图。Lab 13：在 Swagger 试 session_id 字段，验证两次回传一致。选修不计分，推荐林晓型学员完成。
