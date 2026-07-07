# Day 24 实操 Lab 手册

**需求**：ZL-NA-REQ-024  
**时长**：90 分钟  
**环境**：nexus-agent-platform + frontend

---

## Lab 0：环境准备（10 min）

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
export PYTHONPATH=src
export NEXUS_LLM_MOCK=1
python3 -m pytest tests/day24/test_integration.py -v
```

**通过标准**：12 passed

---

## Lab 1：launch 门禁（10 min）

```bash
python3 src/day24/sprint3_launch.py
```

**通过标准**：exit 0，含 pytest 与 E2E ✅

---

## Lab 2：启动服务（10 min）

```bash
python3 src/day24/sprint3_launch.py --serve
```

浏览器访问 `http://127.0.0.1:8000/`

**通过标准**：页面可聊，session-label 可见

---

## Lab 3：三问句（15 min）

输入 DEMO_QUERIES 三句，记录 kind。

**通过标准**：faq + route 至少各出现一次

---

## Lab 4：新对话（10 min）

聊两句后点新对话，观察 session-label 与消息清空。

**通过标准**：标签变化，欢迎语出现

---

## Lab 5：e2e_smoke 对照（10 min）

```bash
python3 src/day24/e2e_smoke.py
```

对比终端输出与 Lab 3 结果。

**通过标准**：exit 0

---

## Lab 6：localStorage（10 min）

DevTools → Application → Local Storage → 记录 key 与值，刷新验证。

**通过标准**：刷新前后值相同

---

## Lab 7：errors 注入（15 min）

停止 uvicorn，仅访问静态页（无 mock），发消息观察错误文案。

**通过标准**：非原始 Failed to fetch（若引 errors.js）

---

## 验收表

| Lab | 交付物 |
|-----|--------|
| 0 | pytest 截图 |
| 3 | kind 记录表 |
| 4 | 新对话截图 |
| 5 | smoke 终端输出 |

## 故障排除

见 [17_启动脚本速查手册.md](17_启动脚本速查手册.md)。

Lab 手册完。

---

## Lab 评分扩展

| Lab | 分值 |
|-----|------|
| 0-2 | 各 10 |
| 3-5 | 各 15 |
| 6-7 | 各 10 |

## 选修 Lab 8：sprint3_review

```bash
python3 src/day24/sprint3_review.py
```

打印 Day 15-24 里程碑，写 50 字感想。

Lab 扩展完。

---

## 故障排除百科

### E1：Address already in use

`lsof -i :8000` 查占用，`kill` 后重试。勿用 8080 冒充整合验收。

### E2：pytest collection error

确认 cwd 在 nexus-agent-platform，PYTHONPATH=src。

### E3：smoke index 失败

检查 frontend 是否在仓库根且 app mount 路径四级 parent 正确。

### E4：kind 单一

三问句至少两种 kind；若全 llm，查 Matcher 与 MOCK。

### E5：session-label 空白

session.js 未加载或 JS 报错，Console 查看。

百科完。
