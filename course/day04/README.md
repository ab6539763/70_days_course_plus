# Day 4 课件索引

**日期**：2026-07-09（星期四）  
**主题**：核心数据结构（上）— list、tuple、set  
**Sprint**：Sprint 1 — CLI 工具链（第 4 天）

## 学习路径

| 序号 | 文件 | 内容 |
|------|------|------|
| 1-4 | 旁白/企业/需求/架构 | 项目上下文 |
| 5-6 | 上午/下午课堂笔记 | list、tuple、set |
| 7-11 | 晚自习/作业/FAQ | 巩固 |
| 12 | [12_课堂练习册.md](12_课堂练习册.md) | 随堂练习 A-J |
| 13 | [13_知识点深度扩展.md](13_知识点深度扩展.md) | 深度扩展+自测 |

## 配套代码

```bash
python src/day04/todo_manager.py
python src/day04/list_demos.py
```

## 今日交付物

- [x] `todo_manager.py` 待办事项管理器（纯命令行）
- [x] 列表增删改查、排序、列表推导式实战

## 上下文链

```
Day 3  platform_cli（菜单循环）
Day 4  todo_manager（list 存储待办）→ Day 5 JSON 持久化
Day 7  通讯录（同类 CRUD）
Day 14 messages list（多轮对话）
```

## 核心代码导读

### todo 数据格式

```python
# [id, title, description, priority, done]
[1, "完成清洗", "Day2", 1, False]
```

### 必会操作

```python
todos.append(item)              # 增
todos[i] = new_value            # 改
todos.pop(index)                # 删
for t in todos: ...             # 查
sorted(todos, key=lambda t: t[3])  # 排序
[t for t in todos if not t[4]]  # 推导式过滤
```

### 运行与测试

```bash
python src/day04/todo_manager.py
python src/day04/list_demos.py
pytest tests/day04/ -v
```

## 学习时长建议

| 时段 | 内容 | 时长 |
|------|------|------|
| 上午 | list 笔记 + 练习册 A-E | 3h |
| 下午 | tuple/set + todo 实操 | 3.5h |
| 晚自习 | 作业 + 案例集阅读 | 2h |

---