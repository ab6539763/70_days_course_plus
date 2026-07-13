"""
Token 计数与成本估算 — 大模型用量可视化

提供本地 token 估算（中英混合启发式）与 API usage 解析、会话累计与费用估算。
Day 15 使用标准库；生产环境可替换为 tiktoken（见课件扩展）。

需求：ZL-NA-REQ-015

作者：NexusAgent 项目组
创建日期：2026-07-20
版本：0.1.0
"""

from __future__ import annotations

from dataclasses import dataclass, field

from llm.response import ChatCompletionResult
from models import ChatMessage

# DeepSeek-Chat 参考单价（元 / 百万 token，2026 教学用近似值）
DEFAULT_INPUT_PRICE_PER_M = 1.0
DEFAULT_OUTPUT_PRICE_PER_M = 2.0

# 每条 message 的格式开销（role、分隔符等，近似）
MESSAGE_OVERHEAD_TOKENS = 4


def _is_cjk(char: str) -> bool:
    code = ord(char)
    return (
        0x4E00 <= code <= 0x9FFF
        or 0x3400 <= code <= 0x4DBF
        or 0x3000 <= code <= 0x303F
    )


def estimate_tokens(text: str) -> int:
    """
    估算文本 token 数（启发式，非精确 BPE）。

    规则：
    - 中日韩字符约 1 token/字
    - 其他字符约 4 字符 1 token
    - 空文本返回 0
    """
    if not text:
        return 0

    cjk = sum(1 for c in text if _is_cjk(c))
    other = len(text) - cjk
    other_tokens = (other + 3) // 4 if other else 0
    return cjk + other_tokens


def estimate_message_tokens(message: ChatMessage) -> int:
    """单条消息的估算 token（含 role 开销）"""
    return MESSAGE_OVERHEAD_TOKENS + estimate_tokens(message.content)


def estimate_messages_tokens(messages: list[ChatMessage]) -> int:
    """消息列表的总估算 token"""
    return sum(estimate_message_tokens(m) for m in messages)


@dataclass
class TokenUsage:
    """单次 API 调用的 token 用量"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_prompt: int = 0

    @classmethod
    def from_result(cls, result: ChatCompletionResult, *, estimated_prompt: int = 0) -> TokenUsage:
        return cls(
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            estimated_prompt=estimated_prompt,
        )

    @classmethod
    def from_usage_dict(cls, usage: dict) -> TokenUsage:
        prompt = int(usage.get("prompt_tokens", 0))
        completion = int(usage.get("completion_tokens", 0))
        total = int(usage.get("total_tokens", prompt + completion))
        return cls(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=total,
        )

    def format_line(self) -> str:
        return (
            f"tokens: 输入={self.prompt_tokens}, 输出={self.completion_tokens}, "
            f"合计={self.total_tokens}"
        )


@dataclass
class TokenCost:
    """费用估算（元）"""

    input_cost: float
    output_cost: float

    @property
    def total(self) -> float:
        return self.input_cost + self.output_cost

    def format_yuan(self) -> str:
        return f"¥{self.total:.6f}（输入 ¥{self.input_cost:.6f} + 输出 ¥{self.output_cost:.6f}）"


class TokenCounter:
    """Token 计数与成本计算器"""

    def __init__(
        self,
        *,
        input_price_per_m: float = DEFAULT_INPUT_PRICE_PER_M,
        output_price_per_m: float = DEFAULT_OUTPUT_PRICE_PER_M,
    ) -> None:
        self.input_price_per_m = input_price_per_m
        self.output_price_per_m = output_price_per_m

    def estimate_text(self, text: str) -> int:
        return estimate_tokens(text)

    def estimate_messages(self, messages: list[ChatMessage]) -> int:
        return estimate_messages_tokens(messages)

    def usage_from_result(
        self,
        result: ChatCompletionResult,
        messages_before_reply: list[ChatMessage],
    ) -> TokenUsage:
        """从 API 结果构建 TokenUsage，并附带发送前的本地估算"""
        estimated = self.estimate_messages(messages_before_reply)
        return TokenUsage.from_result(result, estimated_prompt=estimated)

    def estimate_cost(self, usage: TokenUsage) -> TokenCost:
        input_cost = usage.prompt_tokens / 1_000_000 * self.input_price_per_m
        output_cost = usage.completion_tokens / 1_000_000 * self.output_price_per_m
        return TokenCost(input_cost=input_cost, output_cost=output_cost)

    def compare_estimate(self, usage: TokenUsage) -> str:
        """比较 API 回报与本地估算的差异"""
        if usage.estimated_prompt <= 0:
            return "（无本地估算）"
        diff = usage.prompt_tokens - usage.estimated_prompt
        pct = diff / usage.estimated_prompt * 100 if usage.estimated_prompt else 0
        return f"输入估算偏差: {diff:+d} ({pct:+.1f}%)"


@dataclass
class TokenSessionStats:
    """会话级 token 累计"""

    turns: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_yuan: float = 0.0
    history: list[TokenUsage] = field(default_factory=list)

    def record(self, usage: TokenUsage, cost: TokenCost) -> None:
        self.turns += 1
        self.prompt_tokens += usage.prompt_tokens
        self.completion_tokens += usage.completion_tokens
        self.total_tokens += usage.total_tokens
        self.total_cost_yuan += cost.total
        self.history.append(usage)

    def summary(self) -> str:
        return (
            f"会话累计 {self.turns} 轮 | "
            f"输入 {self.prompt_tokens} + 输出 {self.completion_tokens} = {self.total_tokens} tokens | "
            f"约 ¥{self.total_cost_yuan:.6f}"
        )

    def last_usage(self) -> TokenUsage | None:
        return self.history[-1] if self.history else None


class TokenSessionTracker:
    """结合 TokenCounter 的会话追踪器"""

    def __init__(self, counter: TokenCounter | None = None) -> None:
        self.counter = counter or TokenCounter()
        self.stats = TokenSessionStats()

    def record_turn(
        self,
        result: ChatCompletionResult,
        messages_before_reply: list[ChatMessage],
    ) -> TokenUsage:
        usage = self.counter.usage_from_result(result, messages_before_reply)
        cost = self.counter.estimate_cost(usage)
        self.stats.record(usage, cost)
        return usage

    def last_line(self) -> str:
        usage = self.stats.last_usage()
        if not usage:
            return "暂无 token 数据"
        return usage.format_line()

    def summary(self) -> str:
        return self.stats.summary()

    def report(self) -> str:
        """详细报表"""
        lines = ["--- Token 会话报表 ---", self.stats.summary()]
        usage = self.stats.last_usage()
        if usage:
            lines.append(f"最近一轮: {usage.format_line()}")
            lines.append(self.counter.compare_estimate(usage))
        return "\n".join(lines)
