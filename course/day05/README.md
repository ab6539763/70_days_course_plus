# Day 5 课件索引

**日期**：2026-07-10（星期五）  
**主题**：字典 dict 与 JSON — API 交互的基石  
**Sprint**：Sprint 1 第 5 天

## 学习路径

| 序号 | 文件 | 内容 |
|------|------|------|
| 1-4 | 旁白/企业/需求/架构 | 项目上下文 |
| 5-6 | 上午/下午课堂笔记 | dict、JSON |
| 7-11 | 晚自习/作业/FAQ | 巩固 |
| 12-13 | 练习册/深度扩展 | 选修 |

## 配套代码

```bash
python src/day05/todo_manager_v2.py
python src/day05/api_response_parser.py --input src/day05/sample_data/chat_completion.json
python src/day05/dict_demos.py
```

## 今日交付物

- [x] `todo_manager_v2.py` — dict + JSON 持久化待办
- [x] `api_response_parser.py` — 模拟 API JSON 字段提取
- [x] `todo_storage.py` — 读写 todos.json

## 上下文链

```
Day 4  list 待办（内存）
Day 5  dict + JSON 持久化 + API 解析  ← 今日
---

## 代码地图

```
src/day05/
├── todo_storage.py         # load/save JSON
├── todo_manager_v2.py      # ★ 待办 v2
├── api_response_parser.py  # ★ API 解析
├── dict_demos.py
├── data/todos.json
└── sample_data/*.json
```

## 核心技能

```python
# dict
d["key"], d.get("key", default)
for k, v in d.items():

# json
json.loads(s)   # 字符串 → Python
json.dumps(d)   # Python → 字符串
json.load(f)    # 文件 → Python
json.dump(d, f) # Python → 文件
```

---