"""可打印 A4 练习纸与演示页：纯字符串拼接生成 HTML。"""

import html
import random
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from .tone import BUILTIN_POEMS, Poem, check_poem, tone_pattern

__all__ = [
    "SheetQuestion",
    "render_sheet",
    "render_demo",
]

_SHEET_STYLE = """
@page { size: A4; margin: 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
    "Noto Sans CJK SC", serif;
  color: #1f2328;
  background: #ffffff;
  margin: 0 auto;
  padding: 24px;
  max-width: 820px;
  line-height: 1.6;
}
h1 { font-size: 22px; text-align: center; margin: 0 0 8px; letter-spacing: 2px; }
.meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 8px;
  font-size: 13px;
  color: #57606a;
  border-bottom: 1px solid #d0d7de;
  padding-bottom: 8px;
  margin-bottom: 14px;
}
.note { font-size: 12px; color: #57606a; margin: 0 0 16px; }
.question { margin: 0 0 22px; page-break-inside: avoid; }
.question h2 { font-size: 15px; margin: 0 0 4px; }
.author { font-size: 12px; color: #8c959f; font-weight: normal; margin-left: 6px; }
.hint { font-size: 12px; color: #57606a; margin: 0 0 8px; }
.poem { margin: 0 0 6px; }
.line { margin: 0 0 10px; }
.text { font-size: 17px; letter-spacing: 3px; display: block; }
.blank {
  display: block;
  height: 22px;
  border-bottom: 1px dashed #d0d7de;
  margin-top: 2px;
}
.ask { font-size: 13px; color: #1f2328; margin: 6px 0 0; }
.answers { page-break-before: always; }
.answers h2 { font-size: 18px; margin: 0 0 10px; }
.answers ol { margin: 0; padding-left: 22px; font-size: 13px; }
.answers li { margin-bottom: 10px; }
.answers .pattern { color: #57606a; letter-spacing: 2px; }
footer { margin-top: 18px; font-size: 12px; color: #8c959f; text-align: center; }
@media print { body { padding: 0; max-width: none; } }
"""

_DEMO_STYLE = """
@page { size: A4; margin: 14mm; }
* { box-sizing: border-box; }
body {
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
    "Noto Sans CJK SC", serif;
  color: #1f2328;
  background: #ffffff;
  margin: 0 auto;
  padding: 24px;
  max-width: 900px;
  line-height: 1.6;
}
h1 { font-size: 22px; text-align: center; margin: 0 0 6px; letter-spacing: 1px; }
.lead { text-align: center; font-size: 13px; color: #57606a; margin: 0 0 20px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }
.card { border: 1px solid #d0d7de; border-radius: 8px; padding: 14px 16px; page-break-inside: avoid; }
.card h2 { font-size: 15px; margin: 0 0 4px; }
.card .author { font-size: 12px; color: #8c959f; font-weight: normal; margin-left: 6px; }
.card .line { font-size: 14px; margin: 4px 0; }
.card .tone { color: #57606a; letter-spacing: 2px; margin-left: 8px; }
.card .rhyme { font-size: 12px; color: #57606a; margin: 8px 0 0; }
footer { margin-top: 20px; font-size: 12px; color: #8c959f; text-align: center; }
@media print { body { padding: 0; max-width: none; } }
"""


@dataclass(frozen=True)
class SheetQuestion:
    """练习纸上的一个题目：一首诗及其平仄、押韵答案。"""

    number: int
    poem: Poem
    patterns: Tuple[str, ...]
    form: str
    rhyme_chars: Tuple[str, ...]
    rhyme_names: Tuple[str, ...]


def _validate_count(count: int) -> int:
    if isinstance(count, bool) or not isinstance(count, int):
        raise ValueError("题目数量必须是整数")
    if count < 1 or count > 50:
        raise ValueError("题目数量必须在 1 到 50 之间，当前为 %d" % count)
    return count


def _validate_seed(seed: Optional[int]) -> Optional[int]:
    if seed is None:
        return None
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("随机种子必须是整数")
    return seed


def _build_question(number: int, poem: Poem) -> SheetQuestion:
    result = check_poem(poem.lines)
    patterns = tuple(tone_pattern(line) for line in poem.lines)
    chars = tuple(item for item in result.even_chars if item is not None)
    names: List[str] = []
    for item in result.even_rhymes:
        for line in result.lines:
            if line.rhyme_group == item and line.rhyme_name is not None:
                names.append(line.rhyme_name)
                break
    return SheetQuestion(
        number=number,
        poem=poem,
        patterns=patterns,
        form=result.form,
        rhyme_chars=chars,
        rhyme_names=tuple(names),
    )


def _make_questions(count: int, seed: Optional[int]) -> List[SheetQuestion]:
    """按 seed 生成可复现的题目序列。"""
    total = _validate_count(count)
    real_seed = _validate_seed(seed)
    rng = random.Random(real_seed)
    order: List[Poem] = list(BUILTIN_POEMS)
    rng.shuffle(order)
    questions: List[SheetQuestion] = []
    for index in range(total):
        poem = order[index % len(order)]
        questions.append(_build_question(index + 1, poem))
    return questions


def _render_line(line: str) -> str:
    return (
        '<div class="line"><span class="text">%s</span>'
        '<span class="blank"></span></div>' % html.escape(line)
    )


def _render_question(question: SheetQuestion) -> str:
    poem = question.poem
    parts = ['<section class="question">']
    parts.append(
        '<h2>%d. %s<span class="author">%s</span></h2>'
        % (
            question.number,
            html.escape(poem.title),
            html.escape(poem.author),
        )
    )
    parts.append(
        '<p class="hint">给每句标注平仄，判断是五言还是七言，并圈出押韵的末字。</p>'
    )
    parts.append('<div class="poem">')
    for line in poem.lines:
        parts.append(_render_line(line))
    parts.append("</div>")
    parts.append('<p class="ask">诗体：□ 五言　□ 七言</p>')
    parts.append("</section>")
    return "".join(parts)


def _render_answer(question: SheetQuestion) -> str:
    parts = ["<li>"]
    parts.append(
        "<strong>%d. %s</strong>（%s）"
        % (
            question.number,
            html.escape(question.poem.title),
            html.escape(question.form),
        )
    )
    parts.append(
        '<div class="pattern">%s</div>'
        % html.escape("　".join(question.patterns))
    )
    if question.rhyme_chars:
        pairs = []
        for index, char in enumerate(question.rhyme_chars):
            if index < len(question.rhyme_names):
                pairs.append("%s（%s）" % (char, question.rhyme_names[index]))
            else:
                pairs.append(char)
        parts.append("<div>押韵字：%s</div>" % html.escape("、".join(pairs)))
    else:
        parts.append("<div>押韵字：无</div>")
    parts.append("</li>")
    return "".join(parts)


def render_sheet(count: int, seed: Optional[int], answers: bool) -> str:
    """渲染 A4 练习纸 HTML，count 为 1..50，seed 相同则结果可复现。"""
    if not isinstance(answers, bool):
        raise ValueError("answers 参数必须是布尔值")
    questions = _make_questions(count, seed)

    parts = [
        "<!DOCTYPE html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>古诗词平仄练习纸</title>",
        "<style>",
        _SHEET_STYLE.strip(),
        "</style>",
        "</head>",
        "<body>",
        "<h1>古诗词平仄练习纸</h1>",
        '<div class="meta">'
        "<span>姓名：____________</span>"
        "<span>班级：____________</span>"
        "<span>日期：____________</span>"
        "</div>",
        '<p class="note">共 %d 题。平仄按现代普通话简化判断：一、二声为平，'
        "三、四声为仄，不处理入声。</p>" % len(questions),
    ]
    for question in questions:
        parts.append(_render_question(question))
    parts.append("<footer>poemform · 教学简化版</footer>")
    if answers:
        parts.append('<section class="answers">')
        parts.append("<h2>参考答案</h2>")
        parts.append("<ol>")
        for question in questions:
            parts.append(_render_answer(question))
        parts.append("</ol>")
        parts.append("</section>")
    parts.append("</body>")
    parts.append("</html>")
    return "\n".join(parts)


def render_demo() -> str:
    """渲染内置古诗与平仄标注演示页。"""
    parts = [
        "<!DOCTYPE html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>古诗词平仄演示</title>",
        "<style>",
        _DEMO_STYLE.strip(),
        "</style>",
        "</head>",
        "<body>",
        "<h1>古诗词平仄演示</h1>",
        '<p class="lead">内置 8 首公有领域古诗，平仄按现代普通话简化判断，'
        "不处理入声。</p>",
        '<div class="grid">',
    ]
    for poem in BUILTIN_POEMS:
        result = check_poem(poem.lines)
        parts.append('<article class="card">')
        parts.append(
            '<h2>%s<span class="author">%s</span></h2>'
            % (html.escape(poem.title), html.escape(poem.author))
        )
        for line in poem.lines:
            parts.append(
                '<p class="line">%s<span class="tone">%s</span></p>'
                % (html.escape(line), html.escape(tone_pattern(line)))
            )
        parts.append(
            '<p class="rhyme">诗体：%s；押韵：%s</p>'
            % (html.escape(result.form), html.escape(result.message))
        )
        parts.append("</article>")
    parts.append("</div>")
    parts.append("<footer>poemform · 教学简化版</footer>")
    parts.append("</body>")
    parts.append("</html>")
    return "\n".join(parts)
