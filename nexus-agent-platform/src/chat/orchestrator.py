"""
对话编排器 — FAQ 直答 + 工具 + 意图路由 + LLM

Sprint 3 周测整合交付：将 Day 15–20 能力串成一条用户消息处理链。

需求：ZL-NA-REQ-021
"""

from __future__ import annotations

from dataclasses import dataclass

from chat.cli_assistant import ChatAssistant
from rag.context import RAGContextService
from prompts.intent import IntentRouter
from services.faq_matcher import SimilarQuestionMatcher
from tools.executor import ToolExecutor
from tools.tool_registry import ToolRegistry, build_nexus_tools


@dataclass
class OrchestratorConfig:
    """编排策略配置"""

    faq_direct_threshold: float = 0.65
    enable_faq_direct: bool = True
    enable_auto_route: bool = True


class ChatOrchestrator:
    """
    多能力编排入口

    处理顺序：
    1. FAQ 高置信直答（跳过 LLM）
    2. ChatAssistant.auto_route + RAG context + LLM 多轮对话
    3. 显式工具调用由 /tool 命令触发
    """

    def __init__(
        self,
        assistant: ChatAssistant,
        *,
        faq_matcher: SimilarQuestionMatcher | None = None,
        rag_service: RAGContextService | None = None,
        intent_router: IntentRouter | None = None,
        tool_registry: ToolRegistry | None = None,
        config: OrchestratorConfig | None = None,
    ) -> None:
        self.assistant = assistant
        self.faq_matcher = faq_matcher
        self.rag_service = rag_service
        self.intent_router = intent_router
        self.config = config or OrchestratorConfig()

        if tool_registry is None:
            from llm.token_counter import TokenCounter

            tool_registry = build_nexus_tools(
                faq_matcher=faq_matcher,
                rag_service=rag_service,
                intent_router=intent_router,
                token_counter=TokenCounter(),
            )
        self.tool_registry = tool_registry
        self.tool_executor = ToolExecutor(tool_registry)

    def handle_message(self, user_text: str) -> str:
        """编排处理单条用户消息"""
        user_text = (user_text or "").strip()
        if not user_text:
            return "请输入有效内容。"

        if self.config.enable_faq_direct and self.faq_matcher:
            match = self.faq_matcher.match(user_text)
            if match and match.score >= self.config.faq_direct_threshold:
                return f"[FAQ 直答·{match.score:.0%}] {match.entry.answer}"

        if self.config.enable_auto_route:
            self.assistant.auto_route = True

        return self.assistant.chat_turn(user_text)

    def run_tool(self, name: str, arguments: dict | None = None) -> str:
        result = self.tool_executor.execute(name, arguments)
        return result.summary()

    def tools_help(self) -> str:
        return self.tool_executor.list_help()
