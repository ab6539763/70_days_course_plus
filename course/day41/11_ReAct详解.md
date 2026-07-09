# StateGraph 详解（Day 41 专题）

## 1. 状态图

```
planner → tool_runner → answer
         ↑___________|
```

## 2. 节点

- `planner`：选择工具或 Final Answer
- `tool_runner`：StateGraph node
- `answer`：汇总 reply

## 3. 可观测

`graph_trace[]` 每步含 `node`；`node_path[]` 记录遍历路径。
