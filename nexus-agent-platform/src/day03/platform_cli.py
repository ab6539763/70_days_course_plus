"""
NexusAgent 平台 CLI 统一入口

将 Day 1 入职登记、Day 2 文本清洗整合为交互式菜单，
是 NexusAgent 命令行工具链的骨架（Shell 层）。

核心控制流：
    while True 主循环
    if/elif 菜单路由
    for 循环批量处理文件
    break 退出

需求文档：ZL-NA-REQ-003
架构文档：ZL-NA-ARCH-003

使用方式：
    python src/day03/platform_cli.py

作者：NexusAgent 项目组
创建日期：2026-07-08
版本：0.3.0
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_CURRENT_DIR = Path(__file__).resolve().parent


def _load_constants():
    path = _CURRENT_DIR / "constants.py"
    spec = importlib.util.spec_from_file_location("day03_platform_constants", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_cfg = _load_constants()
OUTPUT_DIR_REL = _cfg.OUTPUT_DIR_REL
PLATFORM_CLI_VERSION = _cfg.PLATFORM_CLI_VERSION
PLATFORM_NAME = _cfg.PLATFORM_NAME
SAMPLE_DOCS_REL = _cfg.SAMPLE_DOCS_REL
VALID_MENU_CHOICES = _cfg.VALID_MENU_CHOICES

if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

from module_loader import get_src_root, load_day_module  # noqa: E402


def show_menu() -> None:
    """显示主菜单（平台工具箱）"""
    print()
    print("╔══════════════════════════════════════╗")
    print(f"║     {PLATFORM_NAME} v{PLATFORM_CLI_VERSION}        ║")
    print("╠══════════════════════════════════════╣")
    print("║  1. 开发者入职登记                    ║")
    print("║  2. 单文件文本清洗                    ║")
    print("║  3. 批量清洗 sample_docs              ║")
    print("║  4. 猜数字游戏（练习）                 ║")
    print("║  5. 九九乘法表（练习）                 ║")
    print("║  6. 查看敏感词表                      ║")
    print("║  7. 统计 output 目录                  ║")
    print("║  0. 退出                              ║")
    print("╚══════════════════════════════════════╝")


def handle_onboarding() -> None:
    """
    菜单 1：调用 Day 1 入职登记

    通过 module_loader 加载 day01/personal_info_card，避免路径冲突。
    """
    print("\n--- 开发者入职登记 ---\n")
    try:
        card_module = load_day_module("day01", "personal_info_card")
        card_module.main()
    except FileNotFoundError as e:
        print(f"错误：无法加载入职登记模块 → {e}")
    except Exception as e:
        print(f"运行出错：{e}")


def handle_single_clean() -> None:
    """
    菜单 2：单文件文本清洗

    提示用户输入路径，调用 Day 2 clean_text，打印结果和报告。
    """
    print("\n--- 单文件文本清洗 ---\n")
    file_path_str = input("请输入文件路径：").strip()

    if not file_path_str:
        print("⚠️  路径不能为空")
        return

    path = Path(file_path_str)
    if not path.is_absolute():
        # 相对路径基于项目 nexus-agent-platform 根目录
        base = get_src_root().parent
        path = base / file_path_str

    if not path.exists():
        print(f"⚠️  文件不存在：{path}")
        return

    try:
        cleaner = load_day_module("day02", "text_cleaner")
        raw = path.read_text(encoding="utf-8")
        cleaned, stats = cleaner.clean_text(raw)

        print("\n--- 清洗结果 ---\n")
        print(cleaned)
        print(cleaner.format_report(path.name, stats))
    except Exception as e:
        print(f"清洗失败：{e}")


def handle_batch_clean() -> None:
    """
    菜单 3：批量清洗 sample_docs

    使用 for 循环遍历所有 .txt 文件，输出到 day03/output/。
    """
    print("\n--- 批量清洗 sample_docs ---\n")

    src_root = get_src_root()
    sample_dir = src_root / SAMPLE_DOCS_REL
    output_dir = src_root / OUTPUT_DIR_REL

    if not sample_dir.exists():
        print(f"⚠️  样本目录不存在：{sample_dir}")
        return

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        cleaner = load_day_module("day02", "text_cleaner")
    except FileNotFoundError as e:
        print(f"错误：无法加载清洗模块 → {e}")
        return

    # glob 获取所有 txt 文件
    txt_files = sorted(sample_dir.glob("*.txt"))

    if not txt_files:
        print("⚠️  未找到 .txt 文件")
        return

    print(f"找到 {len(txt_files)} 个文件，开始清洗...\n")

    # for 循环：逐个处理
    for path in txt_files:
        raw = path.read_text(encoding="utf-8")
        cleaned, stats = cleaner.clean_text(raw)

        out_name = f"cleaned_{path.name}"
        out_path = output_dir / out_name
        out_path.write_text(cleaned, encoding="utf-8")

        raw_len = stats["raw_len"]
        if raw_len > 0:
            ratio = (raw_len - stats["clean_len"]) / raw_len
        else:
            ratio = 0.0

        print(f"  ✅ {path.name}")
        print(f"     → {out_name}")
        print(f"     压缩率 {ratio:.1%}，敏感词替换 {stats['replace_count']} 次")

    print(f"\n全部完成！输出目录：{output_dir}")


def handle_guess_number() -> None:
    """菜单 4：猜数字游戏"""
    from guess_number import play_guess_number

    play_guess_number()


def handle_multiplication_table() -> None:
    """菜单 5：九九乘法表"""
    from multiplication_table import print_multiplication_table

    print_multiplication_table(9)


def handle_show_sensitive_words() -> None:
    """菜单 6：显示 Day 2 敏感词表"""
    print("\n--- 敏感词表 ---\n")
    try:
        # 加载 day02 constants
        constants = load_day_module("day02", "constants")
        words = getattr(constants, "SENSITIVE_WORDS", [])
        for idx, word in enumerate(words, start=1):
            print(f"  {idx}. {word}")
        print(f"\n共 {len(words)} 个敏感词")
    except FileNotFoundError:
        print("⚠️  无法加载敏感词配置")


def handle_output_stats() -> None:
    """
    菜单 7：统计 output 目录

    遍历 output/ 下所有文件，统计数量和总字符数。
    """
    print("\n--- output 目录统计 ---\n")

    output_dir = get_src_root() / OUTPUT_DIR_REL

    if not output_dir.exists():
        print("⚠️  output 目录不存在，请先执行「批量清洗」")
        return

    files = list(output_dir.glob("*.txt"))
    if not files:
        print("⚠️  output 目录为空")
        return

    total_chars = 0
    for path in files:
        content = path.read_text(encoding="utf-8")
        total_chars += len(content)

    print(f"  文件数量：{len(files)}")
    print(f"  总字符数：{total_chars:,}")
    print(f"  目录路径：{output_dir}")
    print("\n  文件列表：")
    for path in files:
        size = len(path.read_text(encoding="utf-8"))
        print(f"    - {path.name} ({size:,} 字符)")


# 菜单路由表：选项 -> (描述, 处理函数)
MENU_HANDLERS = {
    "1": handle_onboarding,
    "2": handle_single_clean,
    "3": handle_batch_clean,
    "4": handle_guess_number,
    "5": handle_multiplication_table,
    "6": handle_show_sensitive_words,
    "7": handle_output_stats,
}


def main() -> None:
    """
    平台 CLI 主入口

    while True 循环显示菜单，根据用户选择路由到对应功能。
    输入 0 时 break 退出。
    """
    print(f"\n欢迎使用 {PLATFORM_NAME}！输入菜单数字选择功能。")

    # 主循环：反复显示菜单直到用户选择退出
    while True:
        show_menu()
        choice = input("请选择：").strip()

        # 退出
        if choice == "0":
            print("\n感谢使用 NexusAgent，再见！👋\n")
            break

        # 非法输入校验
        if choice not in VALID_MENU_CHOICES:
            print("\n⚠️  无效选择，请输入 0-7 之间的数字")
            continue

        # 路由到对应处理函数
        handler = MENU_HANDLERS.get(choice)
        if handler:
            try:
                handler()
            except KeyboardInterrupt:
                print("\n\n操作已取消")
            except Exception as e:
                print(f"\n❌ 发生错误：{e}")
        else:
            print("\n⚠️  功能暂未实现")


if __name__ == "__main__":
    main()
