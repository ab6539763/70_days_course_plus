/**
 * NexusAgent Day 24 — 浏览器会话 ID 持久化
 *
 * 使用 localStorage 保存 session_id，供 POST /api/chat 携带，避免刷新后串话。
 *
 * 需求：ZL-NA-REQ-024
 */
(function (global) {
  "use strict";

  const STORAGE_KEY = "nexus_session_id";

  function generateId() {
    if (global.crypto && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return "sess-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
  }

  function getSessionId() {
    let id = localStorage.getItem(STORAGE_KEY);
    if (!id) {
      id = generateId();
      localStorage.setItem(STORAGE_KEY, id);
    }
    return id;
  }

  function resetSession() {
    const id = generateId();
    localStorage.setItem(STORAGE_KEY, id);
    return id;
  }

  function shortId(id) {
    if (!id || id.length <= 12) return id || "";
    return id.slice(0, 8) + "…";
  }

  global.NexusSession = {
    getSessionId,
    resetSession,
    shortId,
    STORAGE_KEY,
  };
})(window);
