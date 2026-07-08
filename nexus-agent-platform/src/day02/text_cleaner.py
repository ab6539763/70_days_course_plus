"""
NexusAgent 文档文本清洗 CLI 工具

对 OCR、网页抓取等来源的脏文本执行标准化清洗，为 RAG 向量化入库做准备。

清洗管道（按顺序）：
    1. 逐行 strip 去除首尾空白
    2. 合并连续空白字符合并为单个空格
    3. 合并连续相同标点
    4. 敏感词打码（不区分大小写）
    5. 可选：统一转小写 (--lower)
    6. 删除纯空行

需求文档：ZL-NA-REQ-002
架构文档：ZL-NA-ARCH-002

使用示例：
    python src/day02/text_cleaner.py --input src/day02/sample_docs/raw_notice.txt --report
    python src/day02/text_cleaner.py --text "  内部资料！！！  " --report
    python src/day02/text_cleaner.py --input sample.txt --output cleaned.txt --lower

作者：NexusAgent 项目组
创建日期：2026-07-07
版本：0.2.0
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

# 将 day02 目录加入模块搜索路径（Day 10 包重构后移除）
_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))


def _load_local_module(module_name: str, filename: str):
    """
    从当前目录加载模块，避免与 day01/constants 等同名模块冲突

    各 Day 目录均有 constants.py，pytest 全量运行时会因 sys.modules 缓存冲突。
    使用唯一模块名 day02_xxx 加载本地文件。
    """
    path = _CURRENT_DIR / filename
    spec = importlib.util.spec_from_file_location(f"day02_{module_name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_constants = _load_local_module("constants", "constants.py")

MASK_TOKEN = _constants.MASK_TOKEN
PHONE_MASK = _constants.PHONE_MASK
SENSITIVE_WORDS = _constants.SENSITIVE_WORDS
TOOL_NAME = _constants.TOOL_NAME
TOOL_VERSION = _constants.TOOL_VERSION


def collapse_whitespace(text: str) -> str:
    """
    将连续空白字符合并为单个空格

    空白字符包括：空格、制表符 \\t
    OCR 常见问题是多个空格、Tab 混杂，影响分词质量。

    Args:
        text: 单行文本

    Returns:
        合并空白后的文本

    Example:
        >>> collapse_whitespace("a    b\\t\\tc")
        'a b c'
    """
    result: list[str] = []
    prev_was_space = False

    for char in text:
        if char in (" ", "\t"):
            # 只有上一个字符不是空白时，才添加一个空格
            if not prev_was_space:
                result.append(" ")
                prev_was_space = True
        else:
            result.append(char)
            prev_was_space = False

    return "".join(result)


def collapse_duplicate_punctuation(text: str) -> str:
    """
    合并连续相同的非字母数字字符为一个

    例如 "!!!" -> "!", "。。" -> "。"
    字母数字不合并，避免 "aaa" 被错误压缩。

    Args:
        text: 输入文本

    Returns:
        合并标点后的文本
    """
    if not text:
        return text

    result: list[str] = [text[0]]

    for char in text[1:]:
        # 如果当前字符与上一个相同，且不是字母数字，则跳过
        if char == result[-1] and not char.isalnum():
            continue
        result.append(char)

    return "".join(result)


def mask_sensitive_words(text: str, words: list[str]) -> tuple[str, int]:
    """
    敏感词替换（不区分大小写）

    遍历敏感词表，在文本中查找并替换为 MASK_TOKEN。
    使用 lower() 副本定位，在原串上替换以保持其余字符大小写。

    Args:
        text: 待处理文本
        words: 敏感词列表

    Returns:
        (替换后文本, 替换次数)

    Note:
        Day 11 将改用正则和 Aho-Corasick 算法优化性能。
    """
    count = 0
    result = text

    for word in words:
        if not word:
            continue

        lower_word = word.lower()
        # 使用 lower 副本查找位置，但在原串上替换
        lower_result = result.lower()
        start = 0

        while True:
            idx = lower_result.find(lower_word, start)
            if idx == -1:
                break

            # 在原串对应位置替换（保留 MASK_TOKEN 长度一致便于统计）
            result = result[:idx] + MASK_TOKEN + result[idx + len(word) :]
            lower_result = result.lower()
            count += 1
            # 从替换后继续搜索，避免无限循环
            start = idx + len(MASK_TOKEN)

    return result, count


def mask_phone_numbers(text: str) -> tuple[str, int]:
    """
    将大陆 11 位手机号脱敏

    模式：1 开头 + 10 位数字
    Day 11 会扩展支持固话、身份证等模式。

    Args:
        text: 输入文本

    Returns:
        (脱敏后文本, 脱敏数量)
    """
    pattern = r"1\d{10}"
    matches = re.findall(pattern, text)
    result = re.sub(pattern, PHONE_MASK, text)
    return result, len(matches)


def clean_text(raw: str, to_lower: bool = False, mask_phone: bool = False) -> tuple[str, dict]:
    """
    执行完整文本清洗管道

    Args:
        raw: 原始文本（可含多行）
        to_lower: 是否统一转小写
        mask_phone: 是否脱敏手机号

    Returns:
        (清洗后文本, 统计信息字典)

    统计字典键：
        - raw_len: 原始字符数
        - clean_len: 清洗后字符数
        - replace_count: 敏感词替换次数
        - phone_masked: 手机号脱敏次数
        - empty_dropped: 删除的空行数
        - raw_lines: 原始行数
        - clean_lines: 清洗后行数
    """
    stats = {
        "raw_len": len(raw),
        "replace_count": 0,
        "phone_masked": 0,
        "empty_dropped": 0,
        "raw_lines": len(raw.splitlines()),
    }

    cleaned_lines: list[str] = []

    # splitlines() 比 split("\\n") 更好：自动处理 \\r\\n (Windows)
    for line in raw.splitlines():
        # 规则 1：去除行首尾空白
        line = line.strip()

        # 规则 6：跳过纯空行
        if not line:
            stats["empty_dropped"] += 1
            continue

        # 规则 2：合并连续空白
        line = collapse_whitespace(line)

        # 规则 3：合并重复标点
        line = collapse_duplicate_punctuation(line)

        # 规则 4：敏感词打码
        line, n = mask_sensitive_words(line, SENSITIVE_WORDS)
        stats["replace_count"] += n

        # 可选：手机号脱敏
        if mask_phone:
            line, phone_n = mask_phone_numbers(line)
            stats["phone_masked"] += phone_n

        # 规则 5：可选统一小写
        if to_lower:
            line = line.lower()

        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines)
    stats["clean_len"] = len(result)
    stats["clean_lines"] = len(cleaned_lines)

    return result, stats


def format_report(source: str, stats: dict) -> str:
    """
    生成 f-string 格式化的清洗报告

    使用 f-string 格式说明符：
        - {n:,}     千分位
        - {r:.1%}   百分比保留 1 位小数
        - {s:<24}   左对齐宽度 24

    Args:
        source: 输入来源描述（文件名或 --text）
        stats: clean_text 返回的统计字典

    Returns:
        格式化报告字符串
    """
    raw_len = stats["raw_len"]
    clean_len = stats["clean_len"]

    # 计算压缩率，避免除零
    if raw_len > 0:
        compression = (raw_len - clean_len) / raw_len
    else:
        compression = 0.0

    report = f"""
╔══════════════════════════════════════╗
║     NexusAgent 文本清洗报告           ║
╠══════════════════════════════════════╣
║  输入来源：{source:<24}║
║  原始字符数：{raw_len:>10,}                ║
║  清洗后字符数：{clean_len:>10,}              ║
║  压缩率：{compression:>10.1%}                    ║
║  敏感词替换次数：{stats['replace_count']:>6}              ║
║  删除空行数：{stats['empty_dropped']:>10}                ║
║  行数变化：{stats['raw_lines']} → {stats['clean_lines']:<14}║
╚══════════════════════════════════════╝
"""
    return report


def load_input_text(args: argparse.Namespace) -> tuple[str, str]:
    """
    根据命令行参数加载待清洗文本

    Args:
        args: argparse 解析结果

    Returns:
        (文本内容, 来源描述)

    Raises:
        SystemExit: 参数不合法或文件不存在
    """
    if args.input:
        path = Path(args.input)
        if not path.exists():
            print(f"错误：文件不存在 → {path}", file=sys.stderr)
            sys.exit(1)
        text = path.read_text(encoding="utf-8")
        source = path.name
        return text, source

    if args.text is not None:
        return args.text, "--text"

    print("错误：必须指定 --input 或 --text", file=sys.stderr)
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数

    使用 argparse 标准库，企业 CLI 工具的标准做法。
    Day 3 的交互菜单用 input()，命令行工具用 argparse。
    """
    parser = argparse.ArgumentParser(
        prog="text_cleaner",
        description=f"{TOOL_NAME} v{TOOL_VERSION} — 文档文本清洗工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python text_cleaner.py --input sample.txt --report
  python text_cleaner.py --text "  内部资料  " --lower --report
  python text_cleaner.py --input sample.txt --output cleaned.txt
        """,
    )

    # 输入源（互斥）
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input", "-i",
        type=str,
        help="输入文件路径（UTF-8 编码）",
    )
    input_group.add_argument(
        "--text", "-t",
        type=str,
        help="直接传入待清洗的文本字符串",
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="输出文件路径（默认打印到 stdout）",
    )
    parser.add_argument(
        "--lower",
        action="store_true",
        help="将文本统一转换为小写",
    )
    parser.add_argument(
        "--mask-phone",
        action="store_true",
        help="脱敏 11 位手机号",
    )
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="输出清洗统计报告",
    )

    return parser.parse_args()


def main() -> None:
    """程序主入口"""
    args = parse_args()

    # 1. 加载输入
    raw_text, source = load_input_text(args)

    # 2. 执行清洗
    cleaned, stats = clean_text(
        raw_text,
        to_lower=args.lower,
        mask_phone=args.mask_phone,
    )

    # 3. 输出清洗结果
    if args.output:
        out_path = Path(args.output)
        out_path.write_text(cleaned, encoding="utf-8")
        print(f"清洗结果已写入: {out_path}")
    else:
        print(cleaned)

    # 4. 可选：输出报告
    if args.report:
        # 若已打印清洗结果，报告前加换行分隔
        if not args.output:
            print()
        print(format_report(source, stats))


if __name__ == "__main__":
    main()
