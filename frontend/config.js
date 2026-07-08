/**
 * NexusAgent Day 23 — 前端 API 配置
 *
 * 由 FastAPI 同源托管时默认 useMock: false。
 * 纯静态预览可加 ?mock=1 查询参数。
 */
(function (global) {
  "use strict";

  const params = new URLSearchParams(global.location.search);

  global.NexusConfig = {
    useMock: params.get("mock") === "1",
    apiBase: "",
  };
})(window);
