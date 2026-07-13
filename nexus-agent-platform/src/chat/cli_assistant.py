"""
命令行多轮对话 AI 助手 — Sprint 1 阶段项目

整合 ChatMessage、MessageHistoryService、ResilientLLMClient，
提供可交互的多轮对话 CLI。

需求：ZL-NA-REQ-014 / ZL-NA-REQ-015 / ZL-NA-REQ-017 / ZL-NA-REQ-018 / ZL-NA-REQ-019 / ZL-NA-REQ-020 / ZL-NA-REQ-021

运行：
    NEXUS_LLM_MOCK=1 python3 src/chat/cli_assistant.py
    NEXUS_LLM_MOCK=1 python3 src/day14/cli_assistant_demo.py

作者：NexusAgent 项目组
创建日期：2026-07-19
版本：1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from core.exceptions import APIError, ConfigError, NexusError
from core.paths import get_path
from llm.client import LLMClient
from llm.resilient_client import ResilientLLMClient
from llm.token_counter import TokenSessionTracker
from models import ChatMessage, ModelConfig
from prompts import (
    DEFAULT_ASSISTANT,
    IntentRouter,
    PromptRegistry,
    PromptTemplate,
    default_registry,
)
from rag.context import RAGContextService
from services import MessageHistory, SimilarQuestionMatcher
from tools.executor import ToolExecutor
from tools.tool_registry import ToolRegistry, parse_tool_arguments

# 内置斜杠命令
COMMANDS = {
    "/help": "显示帮助",
    "/exit": "退出助手",
    "/quit": "退出助手（同 /exit）",
    "/clear": "清空对话历史（保留 system）",
    "/history": "查看当前对话记录",
    "/save": "保存对话到文件",
    "/system": "设置系统提示（/system 文本）",
    "/tokens": "查看会话 token 用量与估算费用",
    "/template": "切换 Prompt 模板（/template 名称 或 /template list）",
    "/route": "意图分类预览（/route 用户话术）",
    "/retrieve": "RAG 检索预览（/retrieve 查询词）",
    "/similar": "相似 FAQ 匹配（/similar 用户问题）",
    "/tool": "调用工具（/tool list 或 /tool 名称 JSON参数）",
}

DEFAULT_SYSTEM_PROMPT = (
    "你是智链科技 NexusAgent 助手，专业、简洁地回答用户关于企业文档与产品的问题。"
)


class ChatAssistant:
    """
    多轮对话助手核心类

    维护 messages 历史，每轮将完整上下文发送给 LLM。
    """

    def __init__(
        self,
        *,
        client: LLMClient | None = None,
        history: MessageHistory | None = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        history_path: Path | None = None,
        on_retry_log: bool = False,
        track_tokens: bool = True,
        prompt_template: PromptTemplate | None = None,
        prompt_registry: PromptRegistry | None = None,
        template_variables: dict[str, str] | None = None,
        intent_router: IntentRouter | None = None,
        auto_route: bool = False,
        rag_service: RAGContextService | None = None,
        faq_matcher: SimilarQuestionMatcher | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.history = history or MessageHistory()
        self.history_path = history_path or get_path("chat_session")
        self.client = client or ResilientLLMClient(
            ModelConfig(),
            on_retry_log=on_retry_log,
        )
        self.track_tokens = track_tokens
        self.token_tracker = TokenSessionTracker() if track_tokens else None
        self.prompt_registry = prompt_registry or default_registry
        self.prompt_template = prompt_template
        self.template_variables = dict(template_variables or {"company": "智链科技"})
        self.intent_router = intent_router
        self.auto_route = auto_route
        self.rag_service = rag_service
        self.faq_matcher = faq_matcher
        self.tool_registry = tool_registry
        self.tool_executor = ToolExecutor(tool_registry) if tool_registry else None
        self._last_intent = None
        self._running = False
        self._init_system_prompt(system_prompt)

    def _init_system_prompt(self, system_prompt: str) -> None:
        if self.prompt_template:
            msg = self.prompt_template.to_system_message(**self.template_variables)
            if not self._has_system_message():
                self.history.add(msg)
            return
        if system_prompt and not self._has_system_message():
            self.history.add_system(system_prompt)

    def apply_template(
        self,
        name: str,
        *,
        variables: dict[str, str] | None = None,
    ) -> str:
        """切换 Prompt 模板并更新 system 消息"""
        tmpl = self.prompt_registry.get(name)
        merged = {**self.template_variables, **(variables or {})}
        rendered = tmpl.render(**merged)
        self.prompt_template = tmpl
        self.template_variables = merged
        # 保留非 system 消息，替换 system
        non_system = [m for m in self.history.messages if m.role != "system"]
        self.history = MessageHistory()
        self.history.add_system(rendered)
        for m in non_system:
            self.history.add(m)
        return rendered

    def _has_system_message(self) -> bool:
        return any(m.role == "system" for m in self.history.messages)

    def is_command(self, text: str) -> bool:
        return text.strip().startswith("/")

    def handle_command(self, text: str) -> tuple[bool, str, bool]:
        """
        处理斜杠命令。

        Returns:
            (handled, message, should_exit)
        """
        raw = text.strip()
        if not raw.startswith("/"):
            return False, "", False

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("/exit", "/quit"):
            return True, "再见！期待下次对话。", True

        if cmd == "/help":
            lines = ["可用命令："] + [f"  {k} — {v}" for k, v in COMMANDS.items()]
            lines.append("直接输入文字开始对话。")
            return True, "\n".join(lines), False

        if cmd == "/clear":
            system_msgs = [m for m in self.history.messages if m.role == "system"]
            self.history = MessageHistory(system_msgs)
            return True, "已清空对话（system 提示已保留）。", False

        if cmd == "/history":
            if not self.history.messages:
                return True, "（暂无消息）", False
            lines = [f"  {i}. {m.format_line()}" for i, m in enumerate(self.history.messages, 1)]
            return True, "--- 对话历史 ---\n" + "\n".join(lines), False

        if cmd == "/save":
            self.save_history()
            return True, f"已保存到 {self.history_path}", False

        if cmd == "/system":
            if not arg:
                return True, "用法：/system 你的系统提示词", False
            self.history.add_system(arg)
            return True, "已更新 system 提示。", False

        if cmd == "/tokens":
            if not self.token_tracker:
                return True, "Token 追踪未启用。", False
            return True, self.token_tracker.report(), False

        if cmd == "/template":
            if arg.lower() == "list":
                names = self.prompt_registry.list_names()
                lines = ["可用模板："] + [f"  - {n}" for n in names]
                return True, "\n".join(lines), False
            if not arg:
                current = self.prompt_template.name if self.prompt_template else "（硬编码 system）"
                return True, f"当前模板: {current}\n用法: /template 名称", False
            try:
                rendered = self.apply_template(arg.split()[0])
                preview = rendered[:80] + ("..." if len(rendered) > 80 else "")
                return True, f"已切换模板 {arg.split()[0]}：{preview}", False
            except (ConfigError, NexusError) as exc:
                return True, f"模板切换失败: {exc.message}", False

        if cmd == "/route":
            if not self.intent_router:
                return True, "意图路由未启用。请传入 intent_router。", False
            query = arg or "请帮我总结这份文档要点"
            match = self.intent_router.classify(query)
            return True, match.summary(), False

        if cmd == "/retrieve":
            if not self.rag_service:
                return True, "RAG 检索未启用。请传入 rag_service。", False
            query = arg or "年化收益率"
            return True, self.rag_service.retrieve_summary(query), False

        if cmd == "/similar":
            if not self.faq_matcher:
                return True, "FAQ 匹配未启用。请传入 faq_matcher。", False
            query = arg or "投资回报率怎么算"
            match = self.faq_matcher.match(query)
            if not match:
                return True, f"未找到相似 FAQ（阈值以上），查询：{query}", False
            return True, f"{match.summary()}\n答案：{match.entry.answer}", False

        if cmd == "/tool":
            if not self.tool_executor:
                return True, "工具调用未启用。请传入 tool_registry。", False
            if not arg or arg.strip() == "list":
                return True, self.tool_executor.list_help(), False
            parts = arg.split(maxsplit=1)
            name = parts[0]
            raw_args = parts[1] if len(parts) > 1 else ""
            try:
                arguments = parse_tool_arguments(raw_args)
            except Exception as exc:  # noqa: BLE001
                return True, f"参数解析失败: {exc}", False
            result = self.tool_executor.execute(name, arguments)
            return True, result.summary(), False

        return True, f"未知命令 {cmd}，输入 /help 查看帮助。", False

    def chat_turn(self, user_text: str) -> str:
        """
        执行一轮对话：追加 user → 调用 LLM → 追加 assistant。

        Raises:
            APIError / ConfigError: 调用失败（由上层捕获展示）
        """
        user_text = user_text.strip()
        if not user_text:
            return "请输入有效内容。"

        route_info = ""
        if self.intent_router and self.auto_route:
            match = self.intent_router.route_and_apply(self, user_text)
            self._last_intent = match
            route_info = f"[路由: {match.template_name}] "

        err = self.history.add_user(user_text)
        if err:
            return f"消息无效：{err}"

        messages_snapshot = list(self.history.messages)
        result = self.client.complete(self.history.messages)
        reply = result.message.content
        self.history.add_assistant(reply)

        if self.token_tracker:
            self.token_tracker.record_turn(result, messages_snapshot)

        return route_info + reply

    def save_history(self) -> None:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self.history.save(self.history_path)

    def load_history(self) -> None:
        if self.history_path.exists():
            self.history = MessageHistory.load(self.history_path)

    def run_scripted(self, lines: list[str]) -> list[str]:
        """
        脚本模式：依次处理输入行，返回输出列表（供测试与 CI）。
        """
        outputs: list[str] = []
        for line in lines:
            out, done = self._process_line(line)
            if out:
                outputs.append(out)
            if done:
                break
        return outputs

    def _process_line(self, line: str) -> tuple[str, bool]:
        text = line.strip()
        if not text:
            return "", False

        if self.is_command(text):
            handled, msg, should_exit = self.handle_command(text)
            if handled:
                return msg, should_exit
            return "", False

        try:
            reply = self.chat_turn(text)
            out = f"助手: {reply}"
            if self.token_tracker and self.token_tracker.stats.last_usage():
                out += f"\n  [{self.token_tracker.last_line()}]"
            return out, False
        except ConfigError as exc:
            return f"配置错误: {exc.message}", False
        except APIError as exc:
            return f"API 调用失败: {exc.message}", False
        except NexusError as exc:
            return f"错误: {exc.message}", False

    def run_interactive(
        self,
        *,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
        prompt: str = "你: ",
    ) -> None:
        """交互式主循环"""
        self._running = True
        output_fn("")
        output_fn("=" * 50)
        output_fn("  NexusAgent CLI 多轮对话助手")
        output_fn("  输入 /help 查看命令，/exit 退出")
        output_fn("=" * 50)

        while self._running:
            try:
                line = input_fn(prompt)
            except (EOFError, KeyboardInterrupt):
                output_fn("\n再见！")
                break

            out, done = self._process_line(line)
            if out:
                output_fn(out)
            if done:
                break

        try:
            self.save_history()
        except NexusError:
            pass


def run_cli() -> None:
    """CLI 入口"""
    ChatAssistant().run_interactive()


if __name__ == "__main__":
    run_cli()
