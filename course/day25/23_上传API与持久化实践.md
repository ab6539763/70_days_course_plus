# 上传 API 与持久化实践

**需求**：ZL-NA-REQ-025 | **动手**

## 实验 1：观察 store.json 增长

```bash
cd nexus-agent-platform
export PYTHONPATH=src
wc -c data/knowledge/store.json
python3 -c "
from rag.knowledge_store import get_knowledge_store
from day25.constants import SAMPLE_UPLOAD_TEXT
kb = get_knowledge_store()
kb.ingest_text(SAMPLE_UPLOAD_TEXT, filename='lab.txt')
kb.save()
"
wc -c data/knowledge/store.json
```

## 实验 2：upload 响应字段

使用 Swagger Try it out 上传，记录：

- `chunk_count` vs `total_chunks`  
- `sessions_cleared`  

## 实验 3：损坏 JSON 恢复

```bash
cp data/knowledge/store.json /tmp/backup.json
echo '{invalid' > data/knowledge/store.json
# 重启服务观察 bootstrap 行为（勿在生产做）
```

## 实验 4：路径安全

尝试上传文件名 `../../etc/passwd`——`Path(filename).name` 应剥离为 `passwd`。

## CI 对照

`test_store_json_has_version` 断言 `version` 与 `platform_version` 字段存在。

实践完。

---

## 附录：完整 knowledge.py 路由节选（实践 vol2）

```python
"""
知识库 REST API — 文档上传、分块调参与检索评估

需求：ZL-NA-REQ-025 / ZL-NA-REQ-026 / ZL-NA-REQ-027 / ZL-NA-REQ-028 / ZL-NA-REQ-029 / ZL-NA-REQ-030
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas import (
    ChunkConfigRequest,
    ChunkConfigResponse,
    EvaluateRequest,
    EvaluateResponse,
    KnowledgeStatusResponse,
    KnowledgeUploadResponse,
    RebuildRequest,
    RebuildResponse,
)
from api.sessions import session_manager
from core.exceptions import NexusError, StorageError
from rag.chunk_config import PRESET_CONFIGS, ChunkConfig
from rag.ingestion import ingest_upload
from rag.knowledge_rebuild import rebuild_store, rebuild_with_best_config
from rag.knowledge_store import get_knowledge_store
from rag.retrieval_eval import EvalQuery, pick_best_config, run_ab_experiment
from tools.doc_parser import parse_bytes

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

MAX_UPLOAD_BYTES = 512_000  # 500 KB 教学上限
_EVAL_SAMPLE = (
    Path(__file__).resolve().parent.parent / "day26" / "sample_docs" / "product_notice.md"
)


@router.get("/chunk-config", response_model=ChunkConfigResponse)
def get_chunk_config() -> ChunkConfigResponse:
    """返回当前知识库默认分块参数"""
    cfg = get_knowledge_store().get_chunk_config()
    return ChunkConfigResponse(**cfg.to_dict())


@router.put("/chunk-config", response_model=ChunkConfigResponse)
def update_chunk_config(body: ChunkConfigRequest) -> ChunkConfigResponse:
    """更新默认分块参数（影响后续上传）"""
    store = get_knowledge_store()
    try:
        cfg = ChunkConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_chunk_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ChunkConfigResponse(**cfg.to_dict())


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate_chunk_configs(body: EvaluateRequest | None = None) -> EvaluateResponse:
    """
    对内置样例文档运行 A/B 分块评估，返回 hit@1 与推荐配置。

    默认使用 PRESET_CONFIGS 四套预设与 day27 评估问句集。
    """
    body = body or EvaluateRequest()
    if not _EVAL_SAMPLE.is_file():
        raise HTTPException(status_code=500, detail="评估样例文档缺失")

    doc = parse_bytes(_EVAL_SAMPLE.read_bytes(), _EVAL_SAMPLE.name)
    from day27.constants import EVAL_QUERIES

    queries = [EvalQuery.from_dict(q) for q in EVAL_QUERIES]

    if body.use_presets and not body.configs:
        configs = list(PRESET_CONFIGS)
    else:
        configs = [ChunkConfig.from_dict(c.model_dump()) for c in body.configs]
        for c in configs:
            c.validate()

    results = run_ab_experiment(doc, configs, queries)
    best = pick_best_config(results)
    if not best:
        raise HTTPException(status_code=500, detail="评估未产生结果")

    return EvaluateResponse(
        best_config=best.to_dict()["config"],
        results=[r.to_dict() for r in results],
        eval_query_count=len(queries),
    )


@router.post("/rebuild", response_model=RebuildResponse)
def rebuild_knowledge_base(body: RebuildRequest | None = None) -> RebuildResponse:
    """
    按当前 chunk_config（或 evaluate 最优配置）全量重建知识库。

    重扫 sample_docs + knowledge_uploads，清空后重新分块与索引。
    """
    body = body or RebuildRequest()
    store = get_knowledge_store()

    if body.apply_best_config:
        if not _EVAL_SAMPLE.is_file():
            raise HTTPException(status_code=500, detail="评估样例文档缺失")
        report = rebuild_with_best_config(
            store,
            eval_sample_path=_EVAL_SAMPLE,
            include_sample_docs=body.include_sample_docs,
        )
    else:
        report = rebuild_store(store, include_sample_docs=body.include_sample_docs)

    cleared = session_manager.clear_all()
    data = report.to_dict()
    data["sessions_cleared"] = cleared
    return RebuildResponse(**data)


@router.get("/status", response_model=KnowledgeStatusResponse)
def knowledge_status() -> KnowledgeStatusResponse:
    """返回知识库文档数、分块数、支持格式与文档列表"""
    store = get_knowledge_store()
    data = store.status_dict()
    return KnowledgeStatusResponse(**data)


@router.post("/upload", response_model=KnowledgeUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="企业文档 (.txt / .md / .pdf)"),
) -> KnowledgeUploadResponse:
    """
    上传企业文档到知识库：解析 → 落盘 → 分块 → Chroma 向量索引 → 持久化。

    Day 26 起支持 Markdown 与 PDF。上传成功后清除服务端会话。
    """
    if not file.filename:
        raise HTTPException(status_code=422, detail="缺少文件名")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=422, detail="文件内容为空")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="文件超过 500KB 上限")

    try:
        meta = ingest_upload(data, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except NexusError as exc:
        status = 400 if exc.code in (
            "PDF_PARSE_ERROR", "PDF_EMPTY", "UNSUPPORTED_FORMAT", "EMPTY_FILE"
        ) else 500
        raise HTTPException(status_code=status, detail=exc.message) from exc
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=exc.message) from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="文本文件须为 UTF-8 编码") from exc

    cleared = session_manager.clear_all()
    store = get_knowledge_store()

    return KnowledgeUploadResponse(
        filename=meta.name,
        format=meta.format,
        chunk_count=meta.chunk_count,
        document_count=store.document_count,
        total_chunks=store.chunk_count,
        sessions_cleared=cleared,
        index_mode=store.index_mode,
        message=f"文档已入库（{meta.format}），增量索引已更新",
    )
```


---

## 附录：multipart 与 FastAPI UploadFile

`UploadFile` 异步 `read()` 返回 bytes；`filename` 来自 Content-Disposition。字段名必须 `file` 与参数名一致。Swagger 自动生成 boundary；curl 用 `-F`。

---

## 附录：持久化恢复演练脚本

```bash
#!/bin/bash
# backup_day25.sh
cp data/knowledge/store.json "/tmp/store-$(date +%Y%m%d).json"
tar czf "/tmp/uploads-$(date +%Y%m%d).tgz" data/knowledge/uploads/
echo backup ok
```



---

## 附录：knowledge.py upload 完整路由（实践专节）

```python
def knowledge_status() -> KnowledgeStatusResponse:
    """返回知识库文档数、分块数、支持格式与文档列表"""
    store = get_knowledge_store()
    data = store.status_dict()
    return KnowledgeStatusResponse(**data)


@router.post("/upload", response_model=KnowledgeUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="企业文档 (.txt / .md / .pdf)"),
) -> KnowledgeUploadResponse:
    """
    上传企业文档到知识库：解析 → 落盘 → 分块 → Chroma 向量索引 → 持久化。

    Day 26 起支持 Markdown 与 PDF。上传成功后清除服务端会话。
    """
    if not file.filename:
        raise HTTPException(status_code=422, detail="缺少文件名")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=422, detail="文件内容为空")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="文件超过 500KB 上限")

    try:
        meta = ingest_upload(data, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except NexusError as exc:
        status = 400 if exc.code in (
            "PDF_PARSE_ERROR", "PDF_EMPTY", "UNSUPPORTED_FORMAT", "EMPTY_FILE"
        ) else 500
        raise HTTPException(status_code=status, detail=exc.message) from exc
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=exc.message) from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="文本文件须为 UTF-8 编码") from exc

    cleared = session_manager.clear_all()
    store = get_knowledge_store()

    return KnowledgeUploadResponse(
        filename=meta.name,
        format=meta.format,
        chunk_count=meta.chunk_count,
        document_count=store.document_count,
        total_chunks=store.chunk_count,
        sessions_cleared=cleared,
        index_mode=store.index_mode,
        message=f"文档已入库（{meta.format}），增量索引已更新",
    )
```


注意异常映射顺序：`ValueError`→422，`NexusError` 按 code 分 400/500。

实践附录完。

---

## 附录：multipart 抓包读法（实践 vol2）

Wireshark 或浏览器 Raw 中找 `Content-Disposition: form-data; name="file"`。字段名必须 `file` 与 FastAPI `File(...)` 参数名一致。改名导致 422 Unprocessable。

实践 vol2 完。

---

## 磁盘清理

实验后执行：`rm -f data/knowledge/uploads/lab*.txt`。勿删 store 除非有意重置。清理完。
