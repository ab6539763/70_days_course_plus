# NexusAgent 前端 — Day 22 静态聊天页

智链科技灵犀智能体平台的浏览器入口（Mock 模式）。

## 快速开始

```bash
# 在仓库根目录
cd frontend
python3 -m http.server 8080
# 浏览器打开 http://localhost:8080
```

无需 Node.js / npm。

## 文件说明

| 文件 | 说明 |
|------|------|
| `index.html` | 页面骨架：消息区、输入框、发送按钮 |
| `style.css` | 聊天气泡、FAQ/路由标签样式 |
| `app.js` | 发送、渲染、加载态 |
| `mock.js` | 本地 Mock，对齐 `ChatOrchestrator.handle_message` 返回格式 |

## 与后端契约

Day 22 Mock 返回格式示例：

- FAQ 直答：`[FAQ 直答·72%] 投资有风险…`
- 意图路由：`[路由: rag_qa] 根据检索资料…`

Day 23 将 `mock.js` 中 `useMock` 设为 `false`，对接 `POST /api/chat`。

## 需求

ZL-NA-REQ-022
