# Day 5 OpenAI 兼容 API 字段速查手册

> 适用于 DeepSeek、通义千问、OpenAI 等兼容格式 API。Day 12 真实调用时对照使用。

---

## 一、请求体（Request Body）

```json
{
  "model": "deepseek-chat",
  "messages": [
    {"role": "system", "content": "你是一个有帮助的助手。"},
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": false
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model | string | 是 | 模型 ID |
| messages | array | 是 | 对话历史，list of dict |
| temperature | float | 否 | 0-2，越高越随机 |
| max_tokens | int | 否 | 最大生成 token |
| stream | bool | 否 | 是否流式 |
| top_p | float | 否 | 核采样 |
| frequency_penalty | float | 否 | 频率惩罚 |

### Python 构造请求

```python
import json

body = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "你好"}],
    "temperature": 0.7,
}
body_str = json.dumps(body, ensure_ascii=False)
# requests.post(url, data=body_str, headers={...})
# 或 requests.post(url, json=body)  # 推荐
```

---

## 二、成功响应（Chat Completion）

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1720600000,
  "model": "deepseek-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！有什么可以帮助你的？"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 12,
    "total_tokens": 22
  }
}
```

### 提取代码模板

```python
def extract_answer(response: dict) -> str:
    choices = response.get("choices", [])
    if not choices:
        return ""
    return choices[0].get("message", {}).get("content", "")

def extract_usage(response: dict) -> dict:
    return response.get("usage", {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    })
```

---

## 三、流式响应（Stream Chunk）

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion.chunk",
  "choices": [
    {
      "index": 0,
      "delta": {"content": "你"},
      "finish_reason": null
    }
  ]
}
```

### 拼接流式内容（Day 16）

```python
full_content = ""
for chunk in stream:
    delta = chunk.get("choices", [{}])[0].get("delta", {})
    piece = delta.get("content", "")
    if piece:
        full_content += piece
```

---

## 四、错误响应

```json
{
  "error": {
    "message": "Incorrect API key provided",
    "type": "invalid_request_error",
    "code": "invalid_api_key"
  }
}
```

### 处理模板

```python
def check_error(response: dict) -> None:
    if "error" in response:
        err = response["error"]
        raise RuntimeError(f"[{err.get('code')}] {err.get('message')}")
```

---

## 五、finish_reason 取值

| 值 | 含义 |
|----|------|
| stop | 正常结束 |
| length | 达到 max_tokens 截断 |
| tool_calls | 需要执行工具（Day 19） |
| content_filter | 内容过滤 |

---

## 六、role 取值

| role | 说明 |
|------|------|
| system | 系统指令 |
| user | 用户输入 |
| assistant | 模型回复 |
| tool | 工具返回（Day 19） |

---

## 七、计费估算（Day 15 预习）

```python
def estimate_cost(usage: dict, price_per_million: float = 1.0) -> float:
    """price_per_million: 每百万 token 价格（元）"""
    tokens = usage.get("total_tokens", 0)
    return tokens / 1_000_000 * price_per_million
```

---

## 八、调试清单

- [ ] 请求体是合法 JSON 吗？
- [ ] messages 是数组且每项有 role/content 吗？
- [ ] 响应先判断 error 再取 choices 吗？
- [ ] usage 字段记录到日志了吗？
- [ ] ensure_ascii=False 保存中文日志了吗？

---

*本手册随 Day 12 真实 API 调用持续更新。*
