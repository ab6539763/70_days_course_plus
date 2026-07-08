# 企业案例集：精确 SKU 查询

## 案例 A：理财 SKU「ZL-FIX-2024-A」

**现象**：销售在 IM 粘贴 SKU，纯向量 top-1 返回「同类产品比较」段落。  
**根因**：SKU 字符在语料中出现次数少，embedding 与描述句相近。  
**处置**：切换 hybrid + keyword_weight=0.5，hit@1 从 41% → 89%。

## 案例 B：客服电话 13900001111

**现象**：与 Day31 课堂投诉相同。  
**数据**：vector hit@1 38%；keyword 92%；hybrid（RRF）94%。  
**话术**：培训坐席可粘贴完整号码查询。

## 案例 C：条款编号「第3.2.1条」

keyword 腿对「3.2.1」token 敏感；vector 对「违约金」语义敏感。hybrid 在「第3.2.1条违约金」合成 query 上优于单路。

## 案例 D：误切 keyword-only

运营为救 SKU 将 mode=keyword，一周后口语 FAQ 满意度降 12%。回 hybrid + RRF 恢复。

## 案例 E：双11 大促 SKU 清单

200 个新 SKU 入库（Day30 增量），检索策略未改。hybrid 无需重训 embedding，仅依赖新 chunk 进索引 — 与增量正交验证。

---

## ROI 幻灯片

| 指标 | 向量 only | hybrid |
|------|-----------|--------|
| 精确 query hit@1 | 0.38 | 0.91 |
| 语义 query hit@1 | 0.84 | 0.86 |
| P95 延迟 ms | 95 | 168 |

---

## 客户邮件模板

主题：混合检索上线（v0.31.0）

正文：针对产品编号与联系电话类问题，系统已启用关键词与语义双路融合检索，预计精确类工单下降 30%。

---

## 案例 F：跨境 SKU 含字母与数字

SKU `ZL-2024-CN-09` 在 vector 路与「2024 年度报告」混淆；keyword 腿对完整 token 串敏感，hybrid RRF 将产品页顶至首位。

---

## 案例 G：批量导入后的检索回归

2000 SKU 经 Day30 增量入库后，无需重训向量模型；调节 `keyword_weight` 至 0.55 即通过 QA 回归。

---

## 案例 H：A/B 实验设计

对照组 vector-only 7 天 vs 实验组 hybrid 7 天；指标：精确 query 工单率、口语 FAQ CSAT、P95 延迟。实验组工单率 -28%，CSAT 持平，延迟 +18%。

---

## 案例 I：失败与回滚

一次误将 `mode=keyword` 写入生产 store.json，口语 FAQ 满意度降；15 分钟内 PUT 恢复 hybrid weighted，监控恢复。

---

## 案例 J：培训材料摘录

给客服的三句话：  
1. 查电话请粘贴完整号码。  
2. 问「怎么样」类问题保持自然语言即可。  
3. 系统已自动合并两种搜索，无需选模式。
