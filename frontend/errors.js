/**
 * NexusAgent Day 24 — API 错误文案映射
 */
(function (global) {
  "use strict";

  function mapApiError(status, payload) {
    const detail =
      (payload && (payload.detail || payload.message)) ||
      (typeof payload === "string" ? payload : "");

    if (status === 422) {
      return "输入无效，请检查消息后重试。";
    }
    if (status === 502) {
      return "大模型服务繁忙，请稍后重试。";
    }
    if (status === 500) {
      return detail ? `服务异常：${detail}` : "服务配置异常，请联系管理员。";
    }
    if (status === 404) {
      return "接口不存在，请确认 API 服务已启动。";
    }
    return detail ? `请求失败（${status}）：${detail}` : `请求失败（${status}）`;
  }

  async function parseErrorResponse(res) {
    try {
      return await res.json();
    } catch (_e) {
      return { detail: res.statusText };
    }
  }

  global.NexusErrors = {
    mapApiError,
    parseErrorResponse,
  };
})(window);
