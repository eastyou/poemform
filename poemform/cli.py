"""命令行入口。"""

import argparse
import sys
from typing import Dict, List, Optional, Sequence

from . import __version__
from .rhyme import final_of, rhyme_group, rhyme_name
from .sheet import render_demo, render_sheet
from .tone import (
    TEMPLATE_FORMS,
    LineResult,
    check_line,
    check_poem,
    template_patterns,
)


def _ensure_utf8_console() -> None:
    """尽量把标准输出与标准错误切换到 UTF-8，失败时忽略。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            continue


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="poemform",
        description="中小学古诗词格律入门工具（教学简化版）：平仄、押韵与练习纸。",
    )
    parser.add_argument("--version", action="version", version="poemform " + __version__)
    subparsers = parser.add_subparsers(dest="command", metavar="命令")

    check = subparsers.add_parser("check", help="逐字分析平仄、句式与押韵")
    check.add_argument("lines", nargs="+", metavar="诗句", help="一句或多句诗，按顺序传入")

    rhyme = subparsers.add_parser("rhyme", help="判断多个字是否同韵")
    rhyme.add_argument("chars", nargs="+", metavar="汉字", help="要比较的汉字")

    template = subparsers.add_parser("template", help="查看标准平仄模板")
    template.add_argument("form", choices=list(TEMPLATE_FORMS), metavar="诗体", help="诗体名称")

    scan = subparsers.add_parser("scan", help="读取诗句文件并逐句分析")
    scan.add_argument("path", metavar="文件", help="UTF-8 文本文件，每行一句")

    sheet = subparsers.add_parser("sheet", help="生成可打印的 A4 练习纸")
    sheet.add_argument(
        "--count", type=int, default=10, metavar="题数", help="题目数量 1..50，默认 10"
    )
    sheet.add_argument("--seed", type=int, default=None, metavar="种子", help="随机种子，便于复现")
    sheet.add_argument(
        "-o", "--output", default="sheet.html", metavar="路径", help="输出 HTML 路径"
    )
    sheet.add_argument("--answers", action="store_true", help="附加答案页")

    demo = subparsers.add_parser("demo", help="生成内置诗作与平仄演示页")
    demo.add_argument(
        "-o", "--output", default="demo.html", metavar="路径", help="输出 HTML 路径"
    )
    return parser


def _print_line_result(index: int, total: int, result: LineResult) -> None:
    if total > 1:
        print("【第 %d 句】%s" % (index, result.text))
    else:
        print("诗句：%s" % result.text)
    print("字数：%d（%s）" % (len(result.chars), result.form))
    print("平仄：%s" % result.pattern)
    for char, tone in zip(result.chars, result.tones):
        print("  %s：%s" % (char, tone))
    if result.rhyme_name is not None:
        print("末字韵：%s → %s" % (result.last_char, result.rhyme_name))
    else:
        print("末字韵：%s → 未收录（教学中可忽略）" % result.last_char)


def _run_check(args: argparse.Namespace) -> int:
    lines: List[str] = list(args.lines)
    results = [check_line(line) for line in lines]
    for index, result in enumerate(results, 1):
        _print_line_result(index, len(results), result)
        if index < len(results):
            print("")
    if len(results) > 1:
        poem = check_poem(lines)
        print("")
        print("诗体：%s（共 %d 句）" % (poem.form, poem.line_count))
        print("偶数句押韵：%s" % poem.message)
        print("押韵是否一致：%s" % ("是" if poem.rhyme_consistent else "否"))
    return 0


def _run_rhyme(args: argparse.Namespace) -> int:
    chars: List[str] = list(args.chars)
    groups: Dict[Optional[str], List[str]] = {}
    for char in chars:
        group = rhyme_group(char)
        final = final_of(char)
        if final is None:
            print("%s：未收录" % char)
        else:
            print("%s：%s → %s" % (char, final, rhyme_name(char)))
        groups.setdefault(group, []).append(char)

    known = [key for key in groups if key is not None]
    print("")
    if len(groups) == 1 and len(known) == 1:
        sample = groups[known[0]][0]
        print("结果：%d 字同韵，同属%s。" % (len(chars), rhyme_name(sample)))
    else:
        print("结果：分为 %d 组。" % len(groups))
        for key in groups:
            members = groups[key]
            if key is None:
                print("  未收录：%s" % "、".join(members))
            else:
                print("  %s：%s" % (rhyme_name(members[0]), "、".join(members)))
    return 0


def _run_template(args: argparse.Namespace) -> int:
    patterns = template_patterns(args.form)
    print("诗体：%s" % args.form)
    print("平仄模板（「中」表示可平可仄）：")
    for index, pattern in enumerate(patterns, 1):
        print("  %d. %s" % (index, pattern))
    return 0


def _read_text(path: str) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("输入路径不能为空")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        raise ValueError("无法读取文件 %s：%s" % (path, exc))


def _run_scan(args: argparse.Namespace) -> int:
    text = _read_text(args.path)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("文件里没有可分析的诗句")
    poem = check_poem(lines)
    for index, result in enumerate(poem.lines, 1):
        print("第 %d 句：%s" % (index, result.text))
        print("  平仄：%s（%s）" % (result.pattern, result.form))
    print("")
    print("诗体：%s（共 %d 句）" % (poem.form, poem.line_count))
    print("偶数句押韵：%s" % poem.message)
    print("押韵是否一致：%s" % ("是" if poem.rhyme_consistent else "否"))
    return 0


def _write_text(path: str, text: str) -> None:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("输出路径不能为空")
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    except OSError as exc:
        raise ValueError("无法写入文件 %s：%s" % (path, exc))


def _run_sheet(args: argparse.Namespace) -> int:
    text = render_sheet(args.count, args.seed, bool(args.answers))
    _write_text(args.output, text)
    suffix = "，含答案页" if args.answers else ""
    print("已生成练习纸：%s（%d 题%s）" % (args.output, args.count, suffix))
    return 0


def _run_demo(args: argparse.Namespace) -> int:
    text = render_demo()
    _write_text(args.output, text)
    print("已生成演示页：%s" % args.output)
    return 0


def _run(args: argparse.Namespace) -> int:
    command = args.command
    if command == "check":
        return _run_check(args)
    if command == "rhyme":
        return _run_rhyme(args)
    if command == "template":
        return _run_template(args)
    if command == "scan":
        return _run_scan(args)
    if command == "sheet":
        return _run_sheet(args)
    if command == "demo":
        return _run_demo(args)
    raise ValueError("未知命令：%s" % command)


def main(argv: Optional[Sequence[str]] = None) -> int:
    _ensure_utf8_console()
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.error("请指定子命令：check、rhyme、template、scan、sheet 或 demo")
    try:
        return _run(args)
    except (TypeError, ValueError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2
