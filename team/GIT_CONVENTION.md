# Git 提交规范

## 分支命名

```
main                          # 生产分支（保护分支）
develop                       # 开发集成分支
feature/dayXX-<简短描述>      # 功能分支（培训期间按天）
fix/<issue-id>-<描述>         # 修复分支
```

培训期间，每天创建功能分支：

```bash
git checkout -b feature/day01-dev-env-setup
```

## Commit Message 格式

```
<type>(<scope>): <subject>

<body>
```

### Type 类型

| type | 说明 |
|------|------|
| feat | 新功能 |
| fix | 修复 bug |
| docs | 文档变更 |
| style | 代码格式（不影响逻辑） |
| refactor | 重构 |
| test | 测试 |
| chore | 构建/工具变更 |

### 示例

```
feat(day01): 实现个人信息卡片 CLI 程序

- 支持姓名、年龄、职位输入
- 格式化输出员工卡片
- 为后续 NexusAgent 用户注册模块打基础

Refs: ZL-NA-001
```

## PR 规范

1. 标题：`[DayXX] 功能描述`
2. 描述：关联需求文档编号、测试说明、截图（如有 UI）
3. 至少 1 位 Reviewer Approve 后合并
