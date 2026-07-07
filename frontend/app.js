/**
 * NexusAgent Day 22 — 静态聊天页交互逻辑
 *
 * 需求：ZL-NA-REQ-022
 */

(function () {
  "use strict";

  const messagesEl = document.getElementById("messages");
  const formEl = document.getElementById("chat-form");
  const inputEl = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");
  const loadingEl = document.getElementById("loading");

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
      const parsed = parseReply(result.reply);
      appendMessage("bot", parsed, result.meta);
    } catch (err) {
      appendMessage("bot", `错误：${err.message}`, "请求失败");
    } finally {
      setLoading(false);
      inputEl.focus();
    }
  }

  formEl.addEventListener("submit", handleSubmit);

  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      formEl.requestSubmit();
    }
  });

  inputEl.focus();
})();
