/**
 * NexusAgent Day 22 — 静态聊天页交互逻辑
 *
 * 需求：ZL-NA-REQ-022 / ZL-NA-REQ-024
 */

(function () {
  "use strict";

  const messagesEl = document.getElementById("messages");
  const formEl = document.getElementById("chat-form");
  const inputEl = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");
  const loadingEl = document.getElementById("loading");
  const badgeEl = document.getElementById("status-badge");
  const newChatBtn = document.getElementById("new-chat-btn");
  const sessionLabel = document.getElementById("session-label");

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function setLoading(on) {
    loadingEl.classList.toggle("hidden", !on);
    loadingEl.setAttribute("aria-hidden", on ? "false" : "true");
    sendBtn.disabled = on;
    inputEl.disabled = on;
  }

  function parseReply(reply) {
    if (reply.startsWith("[FAQ 直答")) {
      return { kind: "faq", text: reply };
    }
    const routeMatch = reply.match(/^\[路由:\s*([^\]]+)\]\s*(.*)$/s);
    if (routeMatch) {
      return {
        kind: "route",
        template: routeMatch[1].trim(),
        text: routeMatch[2].trim() || reply,
      };
    }
    return { kind: "bot", text: reply };
  }

  function appendMessage(role, content, meta) {
    const wrap = document.createElement("div");
    wrap.className = `msg msg--${role}`;

    const avatar = document.createElement("div");
    avatar.className = "msg__avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = role === "user" ? "我" : "AI";

    const bubble = document.createElement("div");
    bubble.className = "msg__bubble";

    if (role === "bot" && content.kind === "faq") {
      const tag = document.createElement("span");
      tag.className = "msg__tag msg__tag--faq";
      tag.textContent = "FAQ 直答";
      bubble.appendChild(tag);
    }

    if (role === "bot" && content.kind === "route") {
      const tag = document.createElement("span");
      tag.className = "msg__tag msg__tag--route";
      tag.textContent = `路由 · ${content.template}`;
      bubble.appendChild(tag);
    }

    const p = document.createElement("p");
    p.textContent = typeof content === "string" ? content : content.text;
    bubble.appendChild(p);

    if (meta) {
      const metaEl = document.createElement("span");
      metaEl.className = "msg__meta";
      metaEl.textContent = meta;
      bubble.appendChild(metaEl);
    }

    wrap.appendChild(avatar);
    wrap.appendChild(bubble);
    messagesEl.appendChild(wrap);
    scrollToBottom();
  }

  async function dispatchMessage(text) {
    const mock = window.NexusMock;
    if (!mock) {
      throw new Error("mock.js 未加载");
    }
    if (mock.useMock) {
      return mock.sendMessage(text);
    }
    return mock.sendMessageApi(text);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const text = inputEl.value.trim();
    if (!text) return;

    appendMessage("user", text);
    inputEl.value = "";
    setLoading(true);

    try {
      const result = await dispatchMessage(text);
      let parsed;
      if (result.kind && result.kind !== "api" && result.kind !== "mock") {
        parsed =
          result.kind === "faq"
            ? { kind: "faq", text: result.reply }
            : result.kind === "route"
              ? parseReply(result.reply)
              : { kind: "bot", text: result.reply };
      } else {
        parsed = parseReply(result.reply);
      }
      appendMessage("bot", parsed, result.meta);
    } catch (err) {
      appendMessage("bot", `错误：${err.message}`, "请求失败");
    } finally {
      setLoading(false);
      inputEl.focus();
    }
  }

  formEl.addEventListener("submit", handleSubmit);

  function updateSessionLabel() {
    if (!sessionLabel || !window.NexusSession) return;
    sessionLabel.textContent = NexusSession.shortId(NexusSession.getSessionId());
  }

  async function checkHealth() {
    if (!badgeEl || (window.NexusConfig && window.NexusConfig.useMock)) return;
    try {
      const base = (window.NexusConfig && window.NexusConfig.apiBase) || "";
      const res = await fetch(`${base}/api/health`);
      if (res.ok) {
        badgeEl.textContent = "API 在线";
        badgeEl.style.background = "#d1fae5";
        badgeEl.style.color = "#065f46";
      } else {
        badgeEl.textContent = "API 异常";
        badgeEl.style.background = "#fee2e2";
        badgeEl.style.color = "#991b1b";
      }
    } catch (_e) {
      badgeEl.textContent = "API 离线";
      badgeEl.style.background = "#fee2e2";
      badgeEl.style.color = "#991b1b";
    }
  }

  if (newChatBtn) {
    newChatBtn.addEventListener("click", async () => {
      if (window.NexusSession) {
        const oldSid = NexusSession.getSessionId();
        const base = (window.NexusConfig && window.NexusConfig.apiBase) || "";
        if (!(window.NexusConfig && window.NexusConfig.useMock)) {
          try {
            await fetch(`${base}/api/session/reset`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ session_id: oldSid }),
            });
          } catch (_e) {
            /* 服务端重置失败不阻塞 UI */
          }
        }
        NexusSession.resetSession();
        updateSessionLabel();
      }
      messagesEl.innerHTML = "";
      appendMessage(
        "bot",
        "已开始新对话。可继续提问。",
        "系统"
      );
    });
  }

  const badge = badgeEl;
  if (badge && window.NexusConfig && !window.NexusConfig.useMock) {
    badge.textContent = "API 模式";
    badge.style.background = "#d1fae5";
    badge.style.color = "#065f46";
    checkHealth();
  }

  updateSessionLabel();

  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      formEl.requestSubmit();
    }
  });

  inputEl.focus();
})();
