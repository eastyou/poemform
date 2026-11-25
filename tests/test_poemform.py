"""poemform 单元测试：覆盖库 API、边界条件与命令行契约。"""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from html.parser import HTMLParser
from typing import List, Optional, Sequence, Tuple

import poemform
from poemform import (
    BUILTIN_POEMS,
    RHYME_FINALS,
    RHYME_GROUPS,
    TEMPLATE_FORMS,
    TONE_MAP,
    check_line,
    check_poem,
    classify_form,
    final_of,
    render_demo,
    render_sheet,
    rhyme_group,
    rhyme_name,
    split_chars,
    template_patterns,
    tone_of,
    tone_pattern,
)
from poemform import cli


class _TagCollector(HTMLParser):
    """收集 HTML 开始标签，用于校验页面结构。"""

    def __init__(self) -> None:
        super().__init__()
        self.tags: List[str] = []

    def handle_starttag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> None:
        self.tags.append(tag)


def _parse_tags(text: str) -> List[str]:
    collector = _TagCollector()
    collector.feed(text)
    collector.close()
    return collector.tags


def _run_cli(argv: Sequence[str]) -> Tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(argv)
    return code, out.getvalue(), err.getvalue()


class TestSplitChars(unittest.TestCase):
    def test_normal_line(self) -> None:
        self.assertEqual(split_chars("床前明月光"), ["床", "前", "明", "月", "光"])

    def test_removes_chinese_punctuation(self) -> None:
        self.assertEqual(split_chars("床前，明月。光！"), ["床", "前", "明", "月", "光"])

    def test_removes_ascii_punctuation(self) -> None:
        self.assertEqual(split_chars("床前,明月!"), ["床", "前", "明", "月"])

    def test_removes_whitespace(self) -> None:
        self.assertEqual(split_chars("  床 前\t明 月 "), ["床", "前", "明", "月"])

    def test_keeps_letters_and_digits(self) -> None:
        self.assertEqual(split_chars("A1"), ["A", "1"])

    def test_returns_list(self) -> None:
        self.assertIsInstance(split_chars("春晓"), list)

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            split_chars("")

    def test_blank_raises(self) -> None:
        with self.assertRaises(ValueError):
            split_chars("   ")

    def test_pure_punctuation_raises(self) -> None:
        with self.assertRaises(ValueError):
            split_chars("，。！？")

    def test_non_string_raises(self) -> None:
        with self.assertRaises(ValueError):
            split_chars(None)  # type: ignore[arg-type]


class TestToneOf(unittest.TestCase):
    def test_flat_char(self) -> None:
        self.assertEqual(tone_of("床"), "平")

    def test_oblique_char(self) -> None:
        self.assertEqual(tone_of("月"), "仄")

    def test_unknown_hanzi(self) -> None:
        self.assertEqual(tone_of("囧"), "？")

    def test_ascii_char(self) -> None:
        self.assertEqual(tone_of("a"), "？")

    def test_digit_char(self) -> None:
        self.assertEqual(tone_of("3"), "？")

    def test_multi_char_raises(self) -> None:
        with self.assertRaises(ValueError):
            tone_of("床前")

    def test_non_string_raises(self) -> None:
        with self.assertRaises(ValueError):
            tone_of(5)  # type: ignore[arg-type]

    def test_tone_map_immutable(self) -> None:
        with self.assertRaises(TypeError):
            TONE_MAP["床"] = "仄"  # type: ignore[index]

    def test_tone_map_values(self) -> None:
        for value in TONE_MAP.values():
            self.assertIn(value, ("平", "仄"))


class TestTonePattern(unittest.TestCase):
    def test_jingyesi_first_line(self) -> None:
        self.assertEqual(tone_pattern("床前明月光"), "平平平仄平")

    def test_pattern_matches_char_count(self) -> None:
        self.assertEqual(len(tone_pattern("疑是地上霜")), 5)

    def test_with_punctuation(self) -> None:
        self.assertEqual(tone_pattern("床前明月光，"), "平平平仄平")

    def test_unknown_char_in_pattern(self) -> None:
        self.assertEqual(tone_pattern("鑫"), "？")

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            tone_pattern("")


class TestClassifyForm(unittest.TestCase):
    def test_five(self) -> None:
        self.assertEqual(classify_form("春眠不觉晓"), "五言")

    def test_seven(self) -> None:
        self.assertEqual(classify_form("日照香炉生紫烟"), "七言")

    def test_four_is_other(self) -> None:
        self.assertEqual(classify_form("床前明月"), "其他")

    def test_eight_is_other(self) -> None:
        self.assertEqual(classify_form("床前明月光疑是地上霜"), "其他")

    def test_punctuation_ignored(self) -> None:
        self.assertEqual(classify_form("春眠，不觉晓。"), "五言")

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            classify_form("")


class TestRhyme(unittest.TestCase):
    def test_guang_shuang_xiang_same(self) -> None:
        groups = [rhyme_group(char) for char in "光霜乡"]
        self.assertEqual(len(set(groups)), 1)
        self.assertEqual(groups[0], "ang")

    def test_rhyme_name_contains(self) -> None:
        name = rhyme_name("光")
        self.assertIsNotNone(name)
        self.assertIn("阳韵", name)

    def test_final_of_guang(self) -> None:
        self.assertEqual(final_of("光"), "uang")

    def test_final_of_unknown(self) -> None:
        self.assertIsNone(final_of("囧"))

    def test_group_of_unknown(self) -> None:
        self.assertIsNone(rhyme_group("囧"))

    def test_name_of_unknown(self) -> None:
        self.assertIsNone(rhyme_name("囧"))

    def test_different_groups(self) -> None:
        self.assertNotEqual(rhyme_group("光"), rhyme_group("明"))

    def test_non_string_raises(self) -> None:
        with self.assertRaises(ValueError):
            rhyme_group(None)  # type: ignore[arg-type]

    def test_multi_char_raises(self) -> None:
        with self.assertRaises(ValueError):
            rhyme_group("光明")

    def test_groups_immutable(self) -> None:
        with self.assertRaises(TypeError):
            RHYME_GROUPS["ang"] = "x"  # type: ignore[index]

    def test_finals_immutable(self) -> None:
        with self.assertRaises(TypeError):
            RHYME_FINALS["ang"] = "x"  # type: ignore[index]


class TestCheckLine(unittest.TestCase):
    def test_fields(self) -> None:
        result = check_line("床前明月光")
        self.assertEqual(result.chars, ["床", "前", "明", "月", "光"])
        self.assertEqual(result.tones, ["平", "平", "平", "仄", "平"])
        self.assertEqual(result.pattern, "平平平仄平")
        self.assertEqual(result.form, "五言")

    def test_last_char_rhyme(self) -> None:
        result = check_line("床前明月光")
        self.assertEqual(result.last_char, "光")
        self.assertEqual(result.rhyme_group, "ang")

    def test_seven_char_line(self) -> None:
        result = check_line("日照香炉生紫烟")
        self.assertEqual(result.form, "七言")
        self.assertEqual(len(result.chars), 7)

    def test_with_punctuation(self) -> None:
        result = check_line("床前明月光，")
        self.assertEqual(result.pattern, "平平平仄平")

    def test_other_form(self) -> None:
        result = check_line("床前明月")
        self.assertEqual(result.form, "其他")

    def test_unknown_char(self) -> None:
        result = check_line("囧")
        self.assertEqual(result.tones, ["？"])
        self.assertIsNone(result.rhyme_group)

    def test_returns_line_result(self) -> None:
        self.assertIsInstance(check_line("春眠不觉晓"), poemform.LineResult)

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            check_line("")


class TestCheckPoem(unittest.TestCase):
    def test_jingyesi_form(self) -> None:
        result = check_poem(BUILTIN_POEMS[0].lines)
        self.assertEqual(result.form, "五言绝句")
        self.assertEqual(result.line_count, 4)

    def test_jingyesi_consistent(self) -> None:
        result = check_poem(BUILTIN_POEMS[0].lines)
        self.assertTrue(result.rhyme_consistent)
        self.assertEqual(result.even_chars, ["霜", "乡"])

    def test_wang_lushan_form(self) -> None:
        result = check_poem(BUILTIN_POEMS[3].lines)
        self.assertEqual(result.form, "七言绝句")

    def test_shanxing_rhyme(self) -> None:
        result = check_poem(BUILTIN_POEMS[5].lines)
        self.assertTrue(result.rhyme_consistent)
        self.assertEqual(result.even_chars, ["家", "花"])

    def test_jiangxue_rhyme(self) -> None:
        result = check_poem(BUILTIN_POEMS[6].lines)
        self.assertTrue(result.rhyme_consistent)

    def test_all_builtin_consistent(self) -> None:
        for poem in BUILTIN_POEMS:
            result = check_poem(poem.lines)
            self.assertTrue(result.rhyme_consistent, poem.title)

    def test_skips_blank_lines(self) -> None:
        lines = ["床前明月光", "", "疑是地上霜", "举头望明月", "低头思故乡"]
        result = check_poem(lines)
        self.assertEqual(result.line_count, 4)

    def test_inconsistent_rhyme(self) -> None:
        lines = ["床前明月光", "疑是地上霜", "举头望明月", "花落知多少"]
        result = check_poem(lines)
        self.assertFalse(result.rhyme_consistent)

    def test_single_line(self) -> None:
        result = check_poem(["床前明月光"])
        self.assertEqual(result.line_count, 1)
        self.assertTrue(result.rhyme_consistent)

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            check_poem([])

    def test_blank_sequence_raises(self) -> None:
        with self.assertRaises(ValueError):
            check_poem(["", "  "])

    def test_string_raises(self) -> None:
        with self.assertRaises(ValueError):
            check_poem("床前明月光")  # type: ignore[arg-type]

    def test_none_raises(self) -> None:
        with self.assertRaises(ValueError):
            check_poem(None)  # type: ignore[arg-type]


class TestTemplates(unittest.TestCase):
    def test_five_jue_has_four_lines(self) -> None:
        self.assertEqual(len(template_patterns("五言绝句")), 4)

    def test_seven_jue_has_four_lines(self) -> None:
        self.assertEqual(len(template_patterns("七言绝句")), 4)

    def test_five_lv_has_eight_lines(self) -> None:
        self.assertEqual(len(template_patterns("五言律诗")), 8)

    def test_seven_lv_has_eight_lines(self) -> None:
        self.assertEqual(len(template_patterns("七言律诗")), 8)

    def test_contains_zhong(self) -> None:
        patterns = template_patterns("五言绝句")
        self.assertTrue(all("中" in line for line in patterns))

    def test_first_five_jue_line(self) -> None:
        self.assertEqual(template_patterns("五言绝句")[0], "中仄平平仄")

    def test_all_forms_supported(self) -> None:
        self.assertEqual(set(TEMPLATE_FORMS), set(["五言绝句", "七言绝句", "五言律诗", "七言律诗"]))

    def test_invalid_raises(self) -> None:
        with self.assertRaises(ValueError):
            template_patterns("七言歌行")

    def test_non_string_raises(self) -> None:
        with self.assertRaises(ValueError):
            template_patterns(None)  # type: ignore[arg-type]


class TestSheet(unittest.TestCase):
    def test_render_returns_str(self) -> None:
        self.assertIsInstance(render_sheet(4, 1, False), str)

    def test_starts_with_doctype(self) -> None:
        self.assertTrue(render_sheet(2, 1, False).startswith("<!DOCTYPE html>"))

    def test_html_parseable(self) -> None:
        tags = _parse_tags(render_sheet(3, 1, False))
        self.assertIn("html", tags)
        self.assertIn("body", tags)
        self.assertIn("section", tags)

    def test_count_text(self) -> None:
        self.assertIn("共 4 题", render_sheet(4, 1, False))

    def test_answers_page(self) -> None:
        text = render_sheet(2, 1, True)
        self.assertIn("参考答案", text)

    def test_no_answers_page(self) -> None:
        text = render_sheet(2, 1, False)
        self.assertNotIn("参考答案", text)

    def test_seed_reproducible(self) -> None:
        self.assertEqual(render_sheet(5, 7, False), render_sheet(5, 7, False))

    def test_answers_reproducible(self) -> None:
        self.assertEqual(render_sheet(5, 7, True), render_sheet(5, 7, True))

    def test_count_one(self) -> None:
        self.assertEqual(render_sheet(1, 1, False).count('<section class="question">'), 1)

    def test_count_fifty(self) -> None:
        self.assertEqual(render_sheet(50, 1, False).count('<section class="question">'), 50)

    def test_count_zero_raises(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(0, 1, False)

    def test_count_too_large_raises(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(51, 1, False)

    def test_count_bool_raises(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(True, 1, False)  # type: ignore[arg-type]

    def test_count_float_raises(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(3.0, 1, False)  # type: ignore[arg-type]

    def test_seed_bool_raises(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(2, True, False)  # type: ignore[arg-type]

    def test_seed_float_raises(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(2, 1.5, False)  # type: ignore[arg-type]

    def test_answers_not_bool_raises(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(2, 1, 1)  # type: ignore[arg-type]

    def test_demo_returns_str(self) -> None:
        self.assertIsInstance(render_demo(), str)

    def test_demo_parseable(self) -> None:
        tags = _parse_tags(render_demo())
        self.assertIn("html", tags)
        self.assertIn("article", tags)

    def test_demo_contains_titles(self) -> None:
        text = render_demo()
        for poem in BUILTIN_POEMS:
            self.assertIn(poem.title, text)

    def test_demo_contains_tone_pattern(self) -> None:
        self.assertIn("平平平仄平", render_demo())


class TestCli(unittest.TestCase):
    def test_help_exits_zero(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with redirect_stdout(io.StringIO()):
                cli.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_version_exits_zero(self) -> None:
        out = io.StringIO()
        with self.assertRaises(SystemExit) as ctx:
            with redirect_stdout(out):
                cli.main(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("poemform 0.1.0", out.getvalue())

    def test_no_command_exits_two(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with redirect_stderr(io.StringIO()):
                cli.main([])
        self.assertEqual(ctx.exception.code, 2)

    def test_check_returns_zero(self) -> None:
        code, out, err = _run_cli(["check", "床前明月光"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")

    def test_check_output_pattern(self) -> None:
        _, out, _ = _run_cli(["check", "床前明月光"])
        self.assertIn("平仄：平平平仄平", out)

    def test_check_output_form(self) -> None:
        _, out, _ = _run_cli(["check", "床前明月光"])
        self.assertIn("字数：5（五言）", out)

    def test_check_output_rhyme(self) -> None:
        _, out, _ = _run_cli(["check", "床前明月光"])
        self.assertIn("阳韵", out)

    def test_check_multiple_lines(self) -> None:
        code, out, _ = _run_cli(
            ["check", "床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"]
        )
        self.assertEqual(code, 0)
        self.assertIn("五言绝句", out)
        self.assertIn("押韵是否一致：是", out)

    def test_check_empty_returns_two(self) -> None:
        code, _, err = _run_cli(["check", ""])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_check_unknown_char(self) -> None:
        code, out, _ = _run_cli(["check", "囧"])
        self.assertEqual(code, 0)
        self.assertIn("？", out)

    def test_rhyme_returns_zero(self) -> None:
        code, out, _ = _run_cli(["rhyme", "光", "霜", "乡"])
        self.assertEqual(code, 0)
        self.assertIn("3 字同韵", out)
        self.assertIn("阳韵", out)

    def test_rhyme_multiple_groups(self) -> None:
        code, out, _ = _run_cli(["rhyme", "光", "明"])
        self.assertEqual(code, 0)
        self.assertIn("分为 2 组", out)

    def test_rhyme_unknown_char(self) -> None:
        code, out, _ = _run_cli(["rhyme", "囧"])
        self.assertEqual(code, 0)
        self.assertIn("未收录", out)

    def test_rhyme_multi_char_returns_two(self) -> None:
        code, _, err = _run_cli(["rhyme", "光明"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_template_five_jue(self) -> None:
        code, out, _ = _run_cli(["template", "五言绝句"])
        self.assertEqual(code, 0)
        self.assertIn("中仄平平仄", out)

    def test_template_seven_jue(self) -> None:
        code, out, _ = _run_cli(["template", "七言绝句"])
        self.assertEqual(code, 0)
        self.assertIn("中平中仄仄平平", out)

    def test_template_seven_lv_eight_lines(self) -> None:
        _, out, _ = _run_cli(["template", "七言律诗"])
        numbered = [line for line in out.splitlines() if line.strip()[:2] in ("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.")]
        self.assertEqual(len([line for line in numbered if line.strip().endswith(("平", "仄"))]), 8)

    def test_template_invalid_exits_two(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with redirect_stderr(io.StringIO()):
                cli.main(["template", "七言歌行"])
        self.assertEqual(ctx.exception.code, 2)

    def test_unknown_command_exits_two(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with redirect_stderr(io.StringIO()):
                cli.main(["unknown"])
        self.assertEqual(ctx.exception.code, 2)

    def test_scan_reads_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "poem.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("床前明月光\n疑是地上霜\n\n举头望明月\n低头思故乡\n")
            code, out, _ = _run_cli(["scan", path])
        self.assertEqual(code, 0)
        self.assertIn("五言绝句", out)
        self.assertIn("押韵是否一致：是", out)

    def test_scan_missing_file_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "missing.txt")
            code, _, err = _run_cli(["scan", path])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_scan_empty_file_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "empty.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("\n  \n")
            code, _, err = _run_cli(["scan", path])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_sheet_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sheet.html")
            code, out, _ = _run_cli(["sheet", "--count", "4", "--seed", "1", "-o", path])
            self.assertEqual(code, 0)
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
        self.assertIn("古诗词平仄练习纸", text)
        self.assertIn("已生成练习纸", out)

    def test_sheet_answers_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sheet.html")
            code, _, _ = _run_cli(
                ["sheet", "--count", "2", "--seed", "1", "-o", path, "--answers"]
            )
            self.assertEqual(code, 0)
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
        self.assertIn("参考答案", text)

    def test_sheet_invalid_count_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sheet.html")
            code, _, err = _run_cli(["sheet", "--count", "0", "-o", path])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_sheet_bad_seed_exits_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sheet.html")
            with self.assertRaises(SystemExit) as ctx:
                with redirect_stderr(io.StringIO()):
                    cli.main(["sheet", "--count", "2", "-o", path, "--seed", "x"])
        self.assertEqual(ctx.exception.code, 2)

    def test_demo_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "demo.html")
            code, out, _ = _run_cli(["demo", "-o", path])
            self.assertEqual(code, 0)
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
        self.assertIn("古诗词平仄演示", text)
        self.assertIn("已生成演示页", out)

    def test_demo_write_error_returns_two(self) -> None:
        code, _, err = _run_cli(["demo", "-o", "/tmp/不存在目录/demo.html"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)


class TestPackage(unittest.TestCase):
    def test_version(self) -> None:
        self.assertEqual(poemform.__version__, "0.1.0")

    def test_builtin_poem_count(self) -> None:
        self.assertEqual(len(BUILTIN_POEMS), 8)

    def test_builtin_titles(self) -> None:
        titles = [poem.title for poem in BUILTIN_POEMS]
        self.assertIn("静夜思", titles)
        self.assertIn("悯农", titles)

    def test_all_poems_four_lines(self) -> None:
        for poem in BUILTIN_POEMS:
            self.assertEqual(len(poem.lines), 4)

    def test_all_poems_no_question_marks(self) -> None:
        for poem in BUILTIN_POEMS:
            for line in poem.lines:
                self.assertNotIn("？", tone_pattern(line), line)


if __name__ == "__main__":
    unittest.main()
