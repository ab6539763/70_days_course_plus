"""
大模型 API 响应 JSON 解析器

从模拟的 Chat Completion / Error 响应中提取关键字段。
这是 Day 12 首次真实 API 调用前的「离线排练」。

需求：ZL-NA-REQ-005 (ZL-NA-021)

使用方式：
    python src/day05/api_response_parser.py --input src/day05/sample_data/chat_completion.json
    python src/day05/api_response_parser.py --input src/day05/sample_data/error_response.json

作者：NexusAgent 项目组
创建日期：2026-07-10
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_json_file(path: Path) -> dict:
    """从文件加载 JSON，失败时友好退出"""
    if not path.exists():
        print(f"错误：文件不存在 → {path}", file=sys.stderr)
        sys.exit(1)
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败：{e}", file=sys.stderr)
        sys.exit(1)


def parse_chat_completion(response: dict) -> dict:
    """
    解析标准 Chat Completion 响应

    安全使用 .get() 链，避免字段缺失导致 KeyError。

    Returns:
        提取后的扁平 dict
    """
    result = {
        "type": "chat.completion",
        "id": response.get("id", ""),
        "model": response.get("model", "unknown"),
        "content": "",
        "role": "",
        "finish_reason": "",
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }

    choices = response.get("choices", [])
    if choices:
        first = choices[0]
        message = first.get("message", {})
        result["content"] = message.get("content", "")
        result["role"] = message.get("role", "")
        result["finish_reason"] = first.get("finish_reason") or ""

    usage = response.get("usage", {})
    result["prompt_tokens"] = usage.get("prompt_tokens", 0)
    result["completion_tokens"] = usage.get("completion_tokens", 0)
    result["total_tokens"] = usage.get("total_tokens", 0)

    return result


def parse_stream_chunk(response: dict) -> dict:
    """解析流式 chunk 响应（Day 16 流式输出预习）"""
    result = {
        "type": "chat.completion.chunk",
        "model": response.get("model", "unknown"),
        "delta_content": "",
        "finish_reason": "",
    }
    choices = response.get("choices", [])
    if choices:
        delta = choices[0].get("delta", {})
        result["delta_content"] = delta.get("content", "")
        result["finish_reason"] = choices[0].get("finish_reason") or ""
    return result


def parse_error_response(response: dict) -> dict:
    """解析 API 错误响应"""
    error = response.get("error", {})
    return {
        "type": "error",
        "message": error.get("message", "未知错误"),
        "error_type": error.get("type", ""),
        "code": error.get("code", ""),
    }


def detect_and_parse(response: dict) -> dict:
    """自动检测响应类型并解析"""
    if "error" in response:
        return parse_error_response(response)
    obj = response.get("object", "")
    if obj == "chat.completion.chunk":
        return parse_stream_chunk(response)
    return parse_chat_completion(response)


def format_report(parsed: dict, source: str) -> str:
    """f-string 格式化解析报告"""
    if parsed.get("type") == "error":
        return f"""
╔══════════════════════════════════════╗
║       API 错误响应解析报告            ║
╠══════════════════════════════════════╣
║  来源：{source:<28}║
║  错误码：{parsed.get('code', ''):<26}║
║  类型：{parsed.get('error_type', ''):<28}║
║  消息：{parsed.get('message', '')[:30]:<28}║
╚══════════════════════════════════════╝
"""

    if parsed.get("type") == "chat.completion.chunk":
        return f"""
╔══════════════════════════════════════╗
║       流式 Chunk 解析报告             ║
╠══════════════════════════════════════╣
║  来源：{source:<28}║
║  model: {parsed.get('model', ''):<27}║
║  delta: {parsed.get('delta_content', ''):<27}║
╚══════════════════════════════════════╝
"""

    content_preview = parsed.get("content", "")[:40]
    if len(parsed.get("content", "")) > 40:
        content_preview += "..."

    return f"""
╔══════════════════════════════════════╗
║       API 响应解析报告                ║
╠══════════════════════════════════════╣
║  来源：{source:<28}║
║  model: {parsed.get('model', ''):<27}║
║  role: {parsed.get('role', ''):<28}║
║  finish_reason: {parsed.get('finish_reason', ''):<20}║
║  content: {content_preview:<25}║
╠══════════════════════════════════════╣
║  prompt_tokens: {parsed.get('prompt_tokens', 0):<18}║
║  completion_tokens: {parsed.get('completion_tokens', 0):<14}║
║  total_tokens: {parsed.get('total_tokens', 0):<18}║
╚══════════════════════════════════════╝
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NexusAgent API 响应 JSON 解析器")
    parser.add_argument("--input", "-i", required=True, help="JSON 响应文件路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="输出完整 JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = Path(args.input)
    response = load_json_file(path)
    parsed = detect_and_parse(response)
    print(format_report(parsed, path.name))
    if args.verbose:
        print("\n--- 完整解析结果 (dict) ---")
        print(json.dumps(parsed, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
