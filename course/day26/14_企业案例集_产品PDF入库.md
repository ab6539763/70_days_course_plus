# 企业案例：产品 PDF 入库

合规部提交 `product_notice.pdf`。林晓上传后问「起购门槛」，RAG 命中抽取文本「1000 元」。

## 步骤

1. 侧栏选 PDF  
2. 确认 format=pdf  
3. chat 验收  

## 失败

扫描件 PDF → PDF_EMPTY → 走 OCR 议题。

案例完。

---

## 合规部周报摘录

「product_notice.pdf 已入库，chat 可答起购与风险条款。扫描件合同仍走人工。」周航注：PDF_EMPTY 不是 bug，是边界教育。

## 操作录屏时间码

00:00 选择 pdf；00:05 上传；00:12 status 更新；00:20 chat 提问；00:45 展示命中句。

## 失败转工单

扫描件 → 工单 OCR-2026-0711 → 不在 Day26 范围。

案例长文完。


---

## 附录

合规 PDF 须可编辑；扫描件走人工 OCR 工单。

---

## 量化

5 分钟上传替代 3 天发版。

---

## 五步专节（14_企业案例集_产品PDF入库.md）

1. upload multipart
2. parse_bytes
3. chunk_from_parsed
4. ingest_parsed
5. clear_all

<!-- vol4-16-steps -->

### 索引 16 专属注记

本节与 ZL-NA-REQ-026 第 8 条 FR 呼应。 实验记录编号 EXP-D26-16。 讲师批注：复现 `pytest tests/day26/` 第 17 条相关测试。


---

## 工单

PDF_EMPTY → OCR 工单


---

## 叙事专节

合规周报写：可编辑 pdf 入库 OK，扫描件走 OCR 工单。

<!-- narrative-14_企业案例集_产品PDF入库.md -->
