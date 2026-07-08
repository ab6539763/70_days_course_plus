# Day 23 API 安全与 CORS 企业实践

**智链科技内控要点**  
**需求**：ZL-NA-REQ-023

---

## 1. CORS 教学配置 vs 生产

### Day 23 开发配置

```python
allow_origins=["*"]
```

**用途**：分离部署调试、Swagger 跨源。  
**风险**：任意网站可读 API（若无鉴权）。

### 生产建议

```python
allow_origins=[
    "https://agent.zhilian-tech.com",
    "https://admin.zhilian-tech.com",
]
allow_credentials=True  # 若用 Cookie
```

---

## 2. 同源托管的安全收益

- 浏览器不触发跨域读响应限制  
- Cookie SameSite 策略简单  
- CSP 可统一配置  

Day 23 `app.mount("/", StaticFiles)` 是**安全架构推荐路径**的简化版。

---

## 3. 输入校验纵深

| 层 | 机制 |
|----|------|
| 前端 | maxlength=2000 |
| API | Pydantic max_length=2000 |
| 编排器 | 业务拒绝超长（可选） |

防止 DoS 大 payload 耗尽内存。

---

## 4. 鉴权空白（Day 23）

当前 `POST /api/chat` **无认证**。风险：

- 内网演示可接受  
- 公网暴露会被刷量  

Sprint 4 计划：API Key header `X-Nexus-Key`。

---

## 5. 错误信息泄露

`detail` 含 `exc.message` 可能暴露内部路径。生产应：

- 对外通用文案  
- 对内 `request_id` 查日志  

赵岩合规：502 不对用户显示上游 URL。

---

## 6. HTTPS

教学 HTTP 仅限实训室。生产强制 TLS 1.2+。

---

## 7. 审计日志

建议中间件记录：

- timestamp  
- session_id（哈希）  
- message 长度（非明文，合规场景）  
- kind  

金融场景存明文须审批。

---

## 8. 林晓 checklist

- [ ] 不在公网暴露 8000  
- [ ] 演示结束关闭 uvicorn  
- [ ] 作业 curl 日志不含真实 API Key  

企业实践文档完。

---

## 9. 智链科技安全培训合规条款摘录

### 9.1 数据分级

用户聊天内容默认「内部敏感」。API 日志不得写入未加密个人笔记本。演示截图须打码 session_id 若含真实工号。

### 9.2 渗透测试预告

信息安全部将于 Sprint 4 对 `POST /api/chat` 做匿名 fuzz。预期发现：无 rate limit、无 auth。修复计划已排期，学员勿惊。

### 9.3 供应链

requirements-api.txt 须从智链镜像安装，防 typosquatting。周航已在 CI 校验 hash pin（试点）。

### 9.4 学员承诺句

「我不得在公网暴露教学 API。」——开课前朗读，林晓队率先签署电子版。

安全扩展完。

---

## 10. 智链科技红蓝对抗演练（选修叙述）

蓝队：学员尝试在未授权情况刷 POST /api/chat。红队：周航监控日志。结论：无 rate limit 时蓝队可刷；教学环境断开外网仅内网 VLAN。演练目的：建立安全意识，非打击学员。选修叙述，不实际操作攻击工具。红蓝对抗叙述完。

**安全课后作业（口头）**：列举三条 Day 23 教学环境不可用于生产的原因。参考答案：无 HTTPS、无鉴权、CORS 全开。
