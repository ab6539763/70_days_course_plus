# Phase 3 第二日总结

Day 25 可写 txt → Day 26 多格式解析 + 章节分块。  
明日 Day 27：chunk_size/overlap 调参与 hit@1 评估。

```mermaid
graph LR
    D25[txt store] --> D26["md/pdf parse"]
    D26 --> D27[evaluate]
```

总结完。

---

## Phase3 两日时间线详表

| 时间 | Day25 | Day26 |
|------|-------|-------|
| 上午 | KnowledgeStore | markdown_parser |
| 下午 | upload API | pdf + compare |
| 晚自习 | store.json | chunk_strategies |
| 验收 | txt chat | md/pdf chat |

## 投资人 Q&A 预案

问：为何不全 OCR？答：成本与教学边界。问：格式更多？答：docx 在 backlog。问：命中率？答：Day27 evaluate。

## 团队士气

林晓日记：「两天把知识管线走通，比刷题踏实。」

总结长文完。


---

## 附录

两日合览：txt→md/pdf；fixed→auto。

---

## 话术

三格式、章节分块、PDF 入库。

---

## 五步专节（24_Phase3第二日总结.md）

1. upload multipart
2. parse_bytes
3. chunk_from_parsed
4. ingest_parsed
5. clear_all

<!-- vol4-26-steps -->

### 索引 26 专属注记

本节与 ZL-NA-REQ-026 第 9 条 FR 呼应。 实验记录编号 EXP-D26-26。 讲师批注：复现 `pytest tests/day26/` 第 10 条相关测试。


---

## 合并

Day25 写 + Day26 格式


---

## 叙事专节

赵岩：「Day25 知识从哪来，Day26 知识长什么样。」

<!-- narrative-24_Phase3第二日总结.md -->
