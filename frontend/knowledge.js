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
      docs ? " · " + docs : ""
    }`;
  }

  function bindPanel() {
    const panel = document.getElementById("kb-panel");
    const toggle = document.getElementById("kb-toggle");
    const statusEl = document.getElementById("kb-status");
    const fileInput = document.getElementById("kb-file");
    const uploadBtn = document.getElementById("kb-upload-btn");
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

    refresh();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindPanel);
  } else {
    bindPanel();
  }

  global.NexusKnowledge = { fetchStatus, uploadFile, renderStatus };
})(window);
