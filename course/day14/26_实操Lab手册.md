# Day 14 实操 Lab 手册

**实验名称**：构建与验收 CLI 多轮对话助手  
**实验学时**：3 小时（课堂 2h + 课后 1h）  
**环境**：`nexus-agent-platform`，Python 3.10+

---

## Lab 0：环境检查（10 min）

```bash
cd /path/to/nexus-agent-platform
export PYTHONPATH=src
export NEXUS_LLM_MOCK=1
python3 --version
python3 -c "from chat import ChatAssistant; print('OK')"
```

**通过标准**：打印 `OK`。

---

## Lab 1：组件冒烟（15 min）

### 步骤

1. 运行 `python3 src/day14/assistant_demos.py`  
2. 记录 `历史消息数`、`客户端类型`、默认 system 前 40 字  
3. 对照源码 `ChatAssistant.__init__`  

### 验收

| 检查项 | 预期 |
|--------|------|
| 历史消息数 | ≥1（含 system） |
| 客户端类型 | ResilientLLMClient |
| /help 输出 | 含 /exit |

---

## Lab 2：脚本验收演示（20 min）

```bash
python3 src/day14/cli_assistant_demo.py
```

### 观察清单

- [ ] 脚本 5 行输入均有 `>>>` 打印  
- [ ] 首问回复含助手内容  
- [ ] `/history` 枚举消息  
- [ ] `/save` 打印路径  
- [ ] `/exit` 告别  

### 实验报告

用表格记录每行输入与首行输出关键词。

---

## Lab 3：交互式七命令（30 min）

```bash
python3 src/chat/cli_assistant.py
```

按 [07_晚自习.md](07_晚自习.md) 任务二顺序操作。

**额外挑战**：对话 5 轮后执行 `/save`，用 `cat` 查看 JSON 结构。

---

## Lab 4：断点调试 chat_turn（25 min）

### 目标

单步理解 `add_user → complete → add_assistant`。

### 步骤

1. 在 `chat_turn` 三行设断点（或 print 调试）  
2. 运行 `pytest tests/day14/test_chat_turn_mock.py -v`（或单测函数名）  
3. 观察 `len(messages)` 在调用前后变化  

### 思考题

第二次 `complete` 时 messages 比第一次多几条？

**答案**：多 2 条（上一轮 user + assistant）。

---

## Lab 5：编写 run_scripted 测试（30 min）

创建 `tests/day14/test_lab_scripted.py`：

```python
def test_lab_three_turns_and_history():
    a = ChatAssistant(client=make_mock_client([SAMPLE_RESPONSE, FOLLOWUP_RESPONSE]))
    outs = a.run_scripted(["第一问", "第二问", "/history"])
    assert len(outs) >= 2
    assert any("对话历史" in o for o in outs)
```

运行：

```bash
python3 -m pytest tests/day14/test_lab_scripted.py -v
```

---

## Lab 6：模拟 API 失败（20 min）

阅读 `test_api_error_handled_in_scripted`，手写最小复现：

```python
def fail_transport(*_):
    raise APIError("503", status_code=503)
```

断言 `run_scripted(["你好"])` 输出含「失败」且进程不崩。

---

## Lab 7：Sprint 1 里程碑仪式（10 min）

```bash
python3 src/day14/sprint1_review.py
```

全组齐读输出，合影（可选）。

---

## Lab 8：阶段评审彩排（20 min）

对照 [24_阶段项目评审标准.md](24_阶段项目评审标准.md)：

1. 自评 F01–F07  
2. 同伴互评 A01–A03  
3. 记录 1 条改进项  

---

## Lab 9：Day 15 预习（10 min）

在 Python REPL 或调试中打印 Mock `complete` 返回的 `usage` 字段（参考 Day 12 测试数据）。

写一句话：**为何多轮对话第 N 轮的 prompt_tokens 通常大于第一轮？**

---

## Lab 故障排除

| 问题 | 处理 |
|------|------|
| 导入失败 | `export PYTHONPATH=src` |
| pytest 收集不到 | 文件名 `test_*.py` |
| 交互无响应 | 确认非空行、非未知命令 |

详见 [10_常见问题与排错指南.md](10_常见问题与排错指南.md)。

---

## Lab 提交物

```
lab/day14/
├── lab_report.md      # Lab 1-3 观察表
├── test_lab_scripted.py
├── api_fail_notes.md  # Lab 6 笔记
└── sprint1_self_review.md  # Lab 8 自评
```

---

## 实验总结

本 Lab 贯穿 Sprint 1 收官全流程：**冒烟 → 脚本验收 → 交互 → 测试 → 评审 → 预习**。

完成全部 Lab 即达到 Day 14 熟练度，并为 Day 15 Token 计数做好准备。

---

## 🎉 Sprint 1 实验收官

> 十四天前你还在配置 Python 环境；今天你在 Lab 里验收多轮 AI 助手。  
> 这不是结束，是你作为 **AI 应用工程师** 的正式开幕。  
> **干得漂亮！我们 Sprint 2 见。**
