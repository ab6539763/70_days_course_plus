# Day 12 API 密钥与环境变量实践

**动手实验手册** · 约 2000 字

---

## 一、.env 工作流

### 1.1 初始化

```bash
cd nexus-agent-platform
cp .env.example .env
```

`.env.example` 内容（节选）：

```bash
# DEEPSEEK_API_KEY=your_api_key_here
# DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
# NEXUS_LLM_MOCK=1
```

取消注释并填入真实值（课堂可用 Mock）。

### 1.2 验证加载

```python
from llm.env import load_llm_env

cfg = load_llm_env()
print(cfg.mock, bool(cfg.api_key), cfg.base_url)
```

---

## 二、三种运行模式

| 模式 | 配置 | 用途 |
|------|------|------|
| Mock | `NEXUS_LLM_MOCK=1` | 开发、CI、课堂 |
| Live | Key 有效，Mock=0 | 联调、验收 |
| 故障 | 无 Key 非 Mock | 应 ConfigError |

### 实验 A：Mock

```bash
export NEXUS_LLM_MOCK=1
unset DEEPSEEK_API_KEY
python3 src/day12/llm_client_demo.py
```

预期：`模式: Mock`，正常输出。

### 实验 B：ConfigError

```bash
unset NEXUS_LLM_MOCK DEEPSEEK_API_KEY
python3 -c "from llm.env import load_llm_env; load_llm_env()"
```

预期：`ConfigError: 缺少 DEEPSEEK_API_KEY...`

### 实验 C：Live（可选）

`.env`：

```
DEEPSEEK_API_KEY=sk-你的密钥
NEXUS_LLM_MOCK=0
```

```bash
python3 src/day12/llm_client_demo.py
```

预期：`模式: Live`，content 与问题相关。

---

## 三、优先级实验

### 步骤

1. `.env` 写 `DEEPSEEK_API_KEY=from-file`  
2. `export DEEPSEEK_API_KEY=from-env`  
3. `load_llm_env().api_key`

预期：`from-env` 胜出。

---

## 四、parse_env_file 边界

创建 `/tmp/test.env`：

```bash
# comment
DEEPSEEK_API_KEY="quoted-key"
EMPTY=

BAD_LINE
KEY=value=extra
```

```python
from pathlib import Path
from llm.env import parse_env_file
print(parse_env_file(Path("/tmp/test.env")))
```

观察：引号剥离、`BAD_LINE` 跳过、`value=extra` 的 partition 行为。

---

## 五、安全实践

### 5.1 禁止事项

- ❌ commit `.env`  
- ❌ 在截图/日志中暴露完整 Key  
- ❌ 在 GitHub Issue 粘贴 Key  

### 5.2 推荐事项

- ✅ 使用 `.env.example` 模板  
- ✅ CI 仅 `NEXUS_LLM_MOCK=1`  
- ✅ 生产用 K8s Secret / Vault 注入 `DEEPSEEK_API_KEY`  
- ✅ Key 轮转后旧 Key 立即作废  

### 5.3 泄露应急

1. 厂商控制台吊销 Key  
2. 生成新 Key  
3. 更新 Secret  
4. 审计 Git 历史（`git log -p` 搜 sk-）

---

## 六、Mock 环境变量真值表

| 值 | mock |
|----|------|
| 1 | ✅ |
| true | ✅ |
| yes | ✅ |
| on | ✅ |
| 0 | ❌ |
| false | ❌ |
| （空） | ❌ |

---

## 七、与 Day 13 衔接

重试装饰器**不应**在缺 Key 时反复重试。环境配置错误应在第一次 `load_llm_env` 或 `_headers` 时失败。

---

## 八、自检清单

- [ ] `.gitignore` 含 `.env`  
- [ ] 能在 Mock 下跑通 pytest  
- [ ] 能解释 environ 与 .env 优先级  
- [ ] 知道 ConfigError 与 APIError 区别  

---

*企业案例：[14_企业案例集_API集成.md](14_企业案例集_API集成.md)*
