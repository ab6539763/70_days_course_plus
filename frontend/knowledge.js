/**
 * NexusAgent Day 25 — 知识库侧栏（上传与状态）
 *
 * 需求：ZL-NA-REQ-025
 */
(function (global) {
  "use strict";

  async function fetchStatus() {
    const base = (global.NexusConfig && global.NexusConfig.apiBase) || "";
    const res = await fetch(`${base}/api/knowledge/status`);
    if (!res.ok) {
      throw new Error(`status ${res.status}`);
    }
    return res.json();
  }

  async function uploadFile(file) {
    const base = (global.NexusConfig && global.NexusConfig.apiBase) || "";
    const form = new FormData();
    form.append("file", file, file.name);
    const res = await fetch(`${base}/api/knowledge/upload`, {
      method: "POST",
      body: form,
    });
    const payload = await (global.NexusErrors
      ? NexusErrors.parseErrorResponse(res)
      : res.json().catch(() => ({})));
    if (!res.ok) {
      const msg = global.NexusErrors
        ? NexusErrors.mapApiError(res.status, payload)
        : `上传失败（${res.status}）`;
      throw new Error(msg);
    }
    return payload;
  }

  function renderStatus(el, data) {
    if (!el || !data) return;
    const docs = (data.documents || [])
      .map((d) => d.name)
      .slice(-5)
      .join("、");
    el.textContent = `${data.document_count} 篇 / ${data.chunk_count} 块${
      data.validation_config && data.validation_config.enabled
        ? " · validate"
        : data.route_config && data.route_config.enabled
        ? " · route"
        : data.expansion_config && data.expansion_config.enabled
        ? " · expand"
        : data.citation_config && data.citation_config.enabled
        ? " · cite"
        : data.rewrite_config && data.rewrite_config.enabled === false
          ? " · no-rewrite"
          : data.rewrite_config && data.rewrite_config.enabled
            ? " · rewrite"
            : data.rerank_config && data.rerank_config.enabled === false
              ? " · recall-only"
              : data.rerank_config && data.rerank_config.enabled
                ? " · rerank"
                : data.retrieval_config && data.retrieval_config.mode
                  ? " · " + data.retrieval_config.mode
                  : data.index_mode
                    ? " · " + data.index_mode
                    : ""
    }${docs ? " · " + docs : ""}`;
  }

  async function runEvaluate() {
    const base = (global.NexusConfig && global.NexusConfig.apiBase) || "";
    const res = await fetch(`${base}/api/knowledge/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ use_presets: true }),
    });
    if (!res.ok) {
      throw new Error(`evaluate ${res.status}`);
    }
    return res.json();
  }

  async function runRebuild(applyBest) {
    const base = (global.NexusConfig && global.NexusConfig.apiBase) || "";
    const res = await fetch(`${base}/api/knowledge/rebuild`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        include_sample_docs: true,
        apply_best_config: !!applyBest,
      }),
    });
    if (!res.ok) {
      throw new Error(`rebuild ${res.status}`);
    }
    return res.json();
  }

  function bindPanel() {
    const panel = document.getElementById("kb-panel");
    const toggle = document.getElementById("kb-toggle");
    const statusEl = document.getElementById("kb-status");
    const fileInput = document.getElementById("kb-file");
    const uploadBtn = document.getElementById("kb-upload-btn");
    const evalBtn = document.getElementById("kb-eval-btn");
    const rebuildBtn = document.getElementById("kb-rebuild-btn");
    const msgEl = document.getElementById("kb-message");

    if (!panel) return;

    if (global.NexusConfig && global.NexusConfig.useMock) {
      if (statusEl) statusEl.textContent = "Mock 模式不可用";
      return;
    }

    async function refresh() {
      try {
        const data = await fetchStatus();
        renderStatus(statusEl, data);
      } catch (_e) {
        if (statusEl) statusEl.textContent = "知识库离线";
      }
    }

    if (toggle) {
      toggle.addEventListener("click", () => {
        panel.classList.toggle("kb-panel--open");
      });
    }

    if (uploadBtn && fileInput) {
      uploadBtn.addEventListener("click", async () => {
        const file = fileInput.files && fileInput.files[0];
        if (!file) {
          if (msgEl) msgEl.textContent = "请选择 .txt / .md / .pdf 文件";
          return;
        }
        if (msgEl) msgEl.textContent = "上传中…";
        try {
          const result = await uploadFile(file);
          if (msgEl) {
            msgEl.textContent = `${result.message}（+${result.chunk_count} 块）`;
          }
          fileInput.value = "";
          await refresh();
        } catch (err) {
          if (msgEl) msgEl.textContent = err.message || "上传失败";
        }
      });
    }

    if (evalBtn) {
      evalBtn.addEventListener("click", async () => {
        if (msgEl) msgEl.textContent = "评估中…";
        try {
          const result = await runEvaluate();
          const best = result.best_config || {};
          if (msgEl) {
            msgEl.textContent = `推荐: ${best.name || "—"} size=${best.chunk_size} hit@1 实验完成`;
          }
        } catch (err) {
          if (msgEl) msgEl.textContent = err.message || "评估失败";
        }
      });
    }

    if (rebuildBtn) {
      rebuildBtn.addEventListener("click", async () => {
        if (msgEl) msgEl.textContent = "重建中…";
        try {
          const result = await runRebuild(false);
          if (msgEl) {
            msgEl.textContent = `${result.message}（${result.chunks_before}→${result.chunks_after} 块）`;
          }
          await refresh();
        } catch (err) {
          if (msgEl) msgEl.textContent = err.message || "重建失败";
        }
      });
    }

    refresh();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindPanel);
  } else {
    bindPanel();
  }

  global.NexusKnowledge = {
    fetchStatus,
    uploadFile,
    runEvaluate,
    runRebuild,
    renderStatus,
  };
})(window);
