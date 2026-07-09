# 深度扩展：自适应路由方法论

## 1. 工业界标准漏斗

```
Stage0: Query processing（Day36 rewrite）
Stage1: Recall — sparse + dense（Day33 hybrid）
Stage2: Rewrite — cross-encoder（Day36）
Stage3: Fusion / filter
Stage4: LLM generation
```

## 2. 为何三阶段足够（教学栈）

- 全库 cross 不可扩展  
- 单阶段 bi-encoder 口语命中 不足  
- 增加第三阶段 LTR 收益递减  

## 3. Recall@K 与 Precision@1

| 指标 | 阶段 | 优化手段 |
|------|------|----------|
| Recall@20 | hybrid | fusion / pool |
| MRR@1 | rewrite | cross-encoder |
| Latency | 全局 | pool、开关、batch |

## 4. Cascade 与 Parallel

本实现是 **serial cascade**：必须等 hybrid 返回才能 rewrite。并行多路召回是 Day33 已做；rewrite 是串行改写。

## 5. 延迟预算分解（示例）

| 段 | ms |
|----|-----|
| embed query | 15 |
| hybrid | 45 |
| rewrite 20 对 | 10 |
| LLM | 800 |

rewrite 占检索段 ~18%，可接受。

## 6. Negative sampling 与训练（展望）

真 cross-encoder 用 (q, pos) vs (q, neg) 训练；mock 用启发式负样本：hybrid 高分但 token 弱相关。

## 7. 与 RRF 关系

RRF 在 **路间** 融合；rewrite 在 **路后** 重排。顺序：keyword+vector → RRF/weighted → top-20 → cross。

## 8. 案例：微软 Bing / Google 双塔 + rewrite

公开资料普遍采用多阶段；本课是缩小版教学实现。

## 9. 失败模式

| 现象 | 诊断 |
|------|------|
| rewrite 无提升 | pool 太小或 mock 与业务不匹配 |
| 延迟飙升 | pool 或真模型未 batch |
| 关 rewrite 更好 | mock 启发式伤害业务 — 换模型 |

## 10. 推荐阅读

- Reimers & Gurevych: Sentence-BERT  
- Nogueira: Document Ranking with BERT  

## 11. 数学：为何 length_penalty

长文档偶然命中更多 query token → coverage 虚高；惩罚 `len/2500` 压低噪声政策文。

## 12. 实验设计模板

固定 hybrid 配置，扫 pool ∈ {10,20,30,40}，画 口语命中-latency 曲线。
