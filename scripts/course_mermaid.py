"""Sanitize Mermaid blocks in course markdown for reliable rendering."""

from __future__ import annotations

import re


def sanitize_mermaid_blocks(text: str) -> str:
    """Fix common Mermaid syntax issues that break GitHub / VS Code preview."""

    def _fix_block(match: re.Match[str]) -> str:
        body = match.group(1)
        lines: list[str] = []
        for line in body.splitlines():
            stripped = line.strip()
            if re.match(r"^(sequenceDiagram|flowchart|stateDiagram|graph|classDiagram)", stripped):
                lines.append(line)
                continue
            if "->>" in line or "-->>" in line:
                lines.append(_quote_sequence_arrow(line))
                continue
            if re.match(r"^\s*\w+-->", line) or re.match(r"^\s*\w+---", line):
                lines.append(_quote_flow_edge(line))
                continue
            # flowchart nodes only — skip stateDiagram transition lines
            if "-->" in line and ":" in line and re.match(r"^\s*[\w\[\*]+\s*-->", line.strip()):
                lines.append(line)
                continue
            if re.search(r"\[[^\]\"]+\]", line) or re.search(r"\{[^}\"]+\}", line):
                lines.append(_quote_inline_nodes(line))
                continue
            lines.append(line)
        return "```mermaid\n" + "\n".join(lines) + "\n```"

    return re.sub(r"```mermaid\n(.*?)```", _fix_block, text, flags=re.S)


def _quote_inline_nodes(line: str) -> str:
    """Quote flowchart node labels that contain = ? / spaces."""

    def repl_square(m: re.Match[str]) -> str:
        inner = m.group(1)
        if inner == "*" or inner.startswith('"'):
            return m.group(0)
        if not any(ch in inner for ch in "?=/*") and "top_k" not in inner:
            return m.group(0)
        return f'["{inner}"]'

    def repl_curly(m: re.Match[str]) -> str:
        inner = m.group(1)
        if inner.startswith('"') or "?" not in inner:
            return m.group(0)
        return f'{{"{inner}"}}'

    line = re.sub(r"\[([^\]]+)\]", repl_square, line)
    line = re.sub(r"\{([^}]+)\}", repl_curly, line)
    return line


def _quote_sequence_arrow(line: str) -> str:
    """Wrap sequence diagram message text in double quotes when needed."""
    for sep in ("->>", "-->>"):
        if sep not in line:
            continue
        left, msg = line.split(sep, 1)
        msg = msg.strip()
        if msg.startswith('"') and msg.endswith('"'):
            return line
        if any(ch in msg for ch in "?=()[]{}/\\"):
            return f'{left}{sep} "{msg}"'
    return line


def _quote_flow_edge(line: str) -> str:
    """Quote flowchart edge labels and node text with special characters."""
    # A -->|label with = ?| B[node text]
    m = re.match(r"^(\s*\S+)\s*(-->|---)\s*(.*)$", line)
    if not m:
        return line
    head, arrow, tail = m.groups()
    tail = _quote_flow_tail(tail)
    return f"{head} {arrow} {tail}"


def _quote_flow_tail(tail: str) -> str:
    # |label|NODE[id]
    pipe = re.match(r"^\|([^|]+)\|\s*(.*)$", tail)
    if pipe:
        label, rest = pipe.groups()
        if any(ch in label for ch in "?=()[]{}"):
            label = f'"{label}"'
        return f"|{label}| {_quote_flow_tail(rest)}"

    # NODE{text}
    for open_b, close_b in (("[", "]"), ("{", "}"), ("(", ")")):
        if tail.startswith(open_b) and close_b in tail:
            end = tail.index(close_b)
            inner = tail[1:end]
            rest = tail[end + 1 :]
            if inner and not (inner.startswith('"') and inner.endswith('"')):
                if any(ch in inner for ch in "?=/*") or "top_k" in inner or " " in inner.strip():
                    tail = f'{open_b}"{inner}"{close_b}{rest}'
            return tail
    return tail
