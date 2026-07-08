/**
 * NexusAgent Day 22 — 本地 Mock 对话桥
 *
 * 模拟 ChatOrchestrator.handle_message 的返回格式，与 Day 21 后端契约对齐。
 * Day 23 将替换为 fetch('/api/chat', ...)。
 *
 * 需求：ZL-NA-REQ-022
 */

(function (global) {
  "use strict";

  const DELAY_MS = 350;

  const FAQ_RULES = [
    {
      test: (t) => /风险|有风险/.test(t),
      reply: "[FAQ 直答·72%] 投资有风险，入市需谨慎。请阅读风险揭示书。",
      meta: "FAQ 直答",
    },
    {
      test: (t) => /回报率|年化|收益/.test(t),
      reply:
        "[FAQ 直答·74%] 请参考产品说明书，收益率以公告为准。投资有风险，入市需谨慎。",
      meta: "FAQ 直答",
    },
    {
      test: (t) => /客服|电话|联系/.test(t),
      reply: "[FAQ 直答·67%] 客服热线 400-888-9999，工作日 9:00-18:00。",
      meta: "FAQ 直答",
    },
  ];

  const ROUTE_RULES = [
    {
      test: (t) => /总结|要点|摘要/.test(t),
      template: "doc_summary",
      body: "已根据您的要求整理 3 个要点：① 产品定位稳健型；② 年化收益以公告为准；③ 须阅读风险揭示书。",
    },
    {
      test: (t) => /合规|审阅|宣传/.test(t),
      template: "compliance_review",
      body: "【风险等级：高】存在夸大收益表述，建议删除「稳赚」类用语并补充风险提示。",
    },
    {
      test: (t) => /文档|资料|根据/.test(t),
      template: "rag_qa",
      body: "根据检索资料，该理财产品年化收益率约为 3.5%-4.2%，具体以实际公告为准。",
    },
    {
      test: (t) => /理财|产品/.test(t),
      template: "product_faq",
      body: "稳健增值系列产品适合稳健型投资者，投资有风险，入市需谨慎。",
    },
  ];

  function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Mock 发送消息 — 对齐 Day 21 编排器输出格式
   * @param {string} text 用户输入
   * @returns {Promise<{reply: string, meta?: string, kind?: string}>}
   */
  async function sendMessage(text) {
    const trimmed = (text || "").trim();
    if (!trimmed) {
      return { reply: "请输入有效内容。", meta: "系统提示", kind: "system" };
    }

    await delay(DELAY_MS);

    for (const rule of FAQ_RULES) {
      if (rule.test(trimmed)) {
        return { reply: rule.reply, meta: rule.meta, kind: "faq" };
      }
    }

    for (const rule of ROUTE_RULES) {
      if (rule.test(trimmed)) {
        return {
          reply: `[路由: ${rule.template}] ${rule.body}`,
          meta: `路由 · ${rule.template}`,
          kind: "route",
        };
      }
    }

    return {
      reply: `（Mock）助手收到：${trimmed}`,
      meta: "Mock 默认",
      kind: "mock",
    };
  }

  /**
   * Day 23 API 占位 — 保持 app.js 切换点单一
   */
  async function sendMessageApi(text) {
    const base = (global.NexusConfig && global.NexusConfig.apiBase) || "";
    const sessionId =
      global.NexusSession && global.NexusSession.getSessionId
        ? global.NexusSession.getSessionId()
        : undefined;

    const res = await fetch(`${base}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });

    if (!res.ok) {
      const payload =
        global.NexusErrors && global.NexusErrors.parseErrorResponse
          ? await global.NexusErrors.parseErrorResponse(res)
          : {};
      const msg =
        global.NexusErrors && global.NexusErrors.mapApiError
          ? global.NexusErrors.mapApiError(res.status, payload)
          : `API 错误: ${res.status}`;
      throw new Error(msg);
    }

    const data = await res.json();
    return {
      reply: data.reply || "",
      meta: data.meta || "API",
      kind: data.kind || "api",
      session_id: data.session_id,
      citations: data.citations || [],
      rewrite: data.rewrite || null,
      expansion: data.expansion || null,
    };
  }

  global.NexusMock = {
    sendMessage,
    sendMessageApi,
    useMock: !(global.NexusConfig && global.NexusConfig.useMock === false),
  };
})(window);
