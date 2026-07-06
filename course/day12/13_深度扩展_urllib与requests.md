# Day 12 深度扩展：urllib 与 requests

**篇幅**：进阶阅读 · 约 2500 字

---

## 一、为何课程选择 urllib

NexusAgent Day 12 明确使用标准库 `urllib.request`，原因：

1. **零依赖**：`pip install` 前即可发 HTTP  
2. **教学透明**：暴露 bytes、encode、Request 构造，理解底层  
3. **企业合规**：部分金融客户 PyPI 包需安全审计  
4. **足够 MVP**：单次 Chat Completion 无需连接池

---

## 二、urllib 常用模式对照

### GET

```python
# urllib
with urllib.request.urlopen(url, timeout=10) as resp:
    data = resp.read()

# requests（对比，今日不引入）
# r = requests.get(url, timeout=10)
# data = r.content
```

### POST JSON

```python
# urllib（本项目）
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, headers=headers, method="POST")
with urllib.request.urlopen(req, timeout=60) as resp:
    ...

# requests
# r = requests.post(url, json=payload, headers=headers, timeout=60)
```

`requests` 的 `json=` 参数自动序列化；urllib 需手动 `dumps`+`encode`。

---

## 三、功能对比表

| 能力 | urllib | requests |
|------|--------|----------|
| 安装 | 内置 | PyPI |
| API 友好度 | ★★☆ | ★★★★ |
| 超时 | urlopen(timeout) | timeout= |
| Session/连接池 | 无 | requests.Session() |
| 文件上传 | 繁琐 | files= |
| 异常类型 | HTTPError/URLError | HTTPError/ConnectionError |

---

## 四、错误处理差异

urllib：`HTTPError` 是 `URLError` 子类，**带 status code**，需 `read()` body。

requests：`response.raise_for_status()`，或检查 `response.status_code`。

本项目统一为 `APIError`，屏蔽库差异——若未来换 `httpx`，仅改 `default_transport`。

---

## 五、测试策略

| 方案 | urllib 项目 | requests 项目 |
|------|-------------|---------------|
| 注入 transport | ✅ 本项目 | 可 mock Session |
| responses 库 | 不适用 | 常用 |
| httpbin 集成测 | 可选（http_demos） | 同 |

**本项目最佳实践**：`TransportFunc` 注入，测试永不触网。

---

## 六、何时迁移到 requests/httpx

陈默建议的演进路径：

```
Day 12  urllib（学习）
Day 30+ httpx（异步、HTTP/2、生产）
```

触发条件：

- 需要 async `await client.post`  
- 高并发连接池  
- 统一 sync/async 客户端

---

## 七、手写 requests 等价 POST（阅读材料）

```python
# 仅供对比，勿加入 nexus-agent-platform 依赖
import requests

def requests_transport(url, headers, payload):
    r = requests.post(url, json=payload, headers=headers, timeout=60)
    if r.status_code >= 400:
        raise APIError("HTTP 失败", status_code=r.status_code, response_body=r.text)
    return r.json()
```

与 `default_transport` **签名相同**，可无缝替换注入。

---

## 八、urllib 代理与 SSL

- 环境变量 `HTTP_PROXY` / `HTTPS_PROXY` 被 urllib 识别  
- 企业 MITM 证书需导入系统 trust store  
- 课程环境一般直连公网 API

---

*REST 深入：[22_HTTP与REST深度讲义.md](22_HTTP与REST深度讲义.md)*
