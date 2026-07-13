# Phase 3 第四日总结（Day 25–28）

| 日 | 关键词 |
|----|--------|
| 25 | 知识库 REST |
| 26 | md/pdf 解析 |
| 27 | chunk A/B evaluate |
| 28 | rebuild 发布 |

## 发布闭环

```
evaluate (实验) → chunk-config (配置) → rebuild (发布) → chat (验证)
```

## 字段演进

store.json：

- Day 25: documents, chunks  
- Day 27: + chunk_config  
- Day 28: + last_rebuilt_at  

## 测试累计

day25 + day26 + day27 + day28 pytest 作为 Phase 3 回归套件。

## 明日

Day 29：向量从 JSON 迁至 Chroma，**rebuild 流程不变**，变的是 `_rebuild_index` 内部实现。

---

## Day 25–28 能力栈（详细）

### 知识入库

- Day 25：`ingest_upload` / `ingest_text`  
- Day 26：`parse_bytes` 支持 md/pdf  
- Day 27：默认分块可配置、可评估  
- Day 28：全库按配置重扫发布  

### 状态字段演进

```json
{
  "chunk_config": {"name": "wide", "chunk_size": 400},
  "last_rebuilt_at": "2026-08-04T12:00:00Z",
  "index_mode": "full"
}
```

### API 端点累积

| Day | 新端点 |
|-----|--------|
| 25 | POST upload, GET status |
| 27 | GET/PUT chunk-config, POST evaluate |
| 28 | POST rebuild |

### 团队能力验收

- 林晓：能独立跑通 evaluate → rebuild  
- 周航：能备份恢复 store.json  
- 赵岩：能评审 PRESET 选型报告  
- 小吴：能执行 chat 抽测并填表  

### 常见面试题

1. 为何 evaluate 不 rebuild？  
2. uploads 优先的业务含义？  
3. last_rebuilt_at 与 last_incremental_at 区别？（Day 30）  

### 下一阶段

Day 29 Chroma：rebuild 后检查 `chroma_count == chunk_count`。

## 学员自测 10 问（Day 28）

1. rebuild 是否删除 uploads？  
2. apply_best_config 依赖哪份评估样例？  
3. sessions_cleared 何时大于 0？  
4. include_sample_docs=false 的典型场景？  
5. RebuildReport 哪个字段用于审计？  
6. 与 evaluate 相比谁写入 chunks？  
7. collect_source_files 返回顺序？  
8. 重建失败如何回滚？  
9. Day 30 incremental 与 rebuild 区别？  
10. 投资人演示前三步 API 是什么？  

参考答案见 `21_课堂知识竞赛.md` 与 `09_作业答案.md`。
