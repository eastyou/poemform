"""poemform：中小学古诗词格律入门工具（教学简化版）。"""

from .rhyme import (
    RHYME_FINALS,
    RHYME_GROUPS,
    final_of,
    rhyme_group,
    rhyme_name,
)
from .sheet import SheetQuestion, render_demo, render_sheet
from .tone import (
    BUILTIN_POEMS,
    PUNCTUATION,
    TEMPLATE_FORMS,
    TONE_MAP,
    LineResult,
    Poem,
    PoemResult,
    check_line,
    check_poem,
    classify_form,
    split_chars,
    template_patterns,
    tone_of,
    tone_pattern,
)

__version__ = "0.1.0"

__all__ = [
    "BUILTIN_POEMS",
    "PUNCTUATION",
    "RHYME_FINALS",
    "RHYME_GROUPS",
    "TEMPLATE_FORMS",
    "TONE_MAP",
    "LineResult",
    "Poem",
    "PoemResult",
    "SheetQuestion",
    "check_line",
    "check_poem",
    "classify_form",
    "final_of",
    "render_demo",
    "render_sheet",
    "rhyme_group",
    "rhyme_name",
    "split_chars",
    "template_patterns",
    "tone_of",
    "tone_pattern",
    "__version__",
]
