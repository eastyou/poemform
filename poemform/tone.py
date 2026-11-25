"""平仄判定与诗句分析（教学简化版）。

简化规则：
    一、二声（阴平、阳平）≈ 平声；
    三、四声（上声、去声）≈ 仄声；
    不处理入声，也不做「一、七、八、不」等变调。
多音字在字表里只固定一个读音，遇到字表外的字统一返回「？」。
"""

from types import MappingProxyType
from typing import Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

from .rhyme import rhyme_group, rhyme_name

__all__ = [
    "TONE_MAP",
    "PUNCTUATION",
    "BUILTIN_POEMS",
    "TEMPLATE_FORMS",
    "Poem",
    "LineResult",
    "PoemResult",
    "split_chars",
    "tone_of",
    "tone_pattern",
    "classify_form",
    "check_line",
    "check_poem",
    "template_patterns",
]

# 需要在统计字数前去掉的标点与符号。
PUNCTUATION = frozenset(
    "，。！？；：、,.!?;:"
    "（）()《》〈〉“”‘’\"'"
    "【】[]{}<>…—－·~～"
    "／/＼\\|"
)

# 汉字 -> 平仄。只收录内置诗作与常用练习字，未收录返回「？」。
_TONE_TABLE: Dict[str, str] = {
    # 《静夜思》
    "床": "平",
    "前": "平",
    "明": "平",
    "月": "仄",
    "光": "平",
    "疑": "平",
    "是": "仄",
    "地": "仄",
    "上": "仄",
    "霜": "平",
    "举": "仄",
    "头": "平",
    "望": "仄",
    "低": "平",
    "思": "平",
    "故": "仄",
    "乡": "平",
    # 《春晓》
    "春": "平",
    "眠": "平",
    "不": "仄",
    "觉": "平",
    "晓": "仄",
    "处": "仄",
    "闻": "平",
    "啼": "平",
    "鸟": "仄",
    "夜": "仄",
    "来": "平",
    "风": "平",
    "雨": "仄",
    "声": "平",
    "花": "平",
    "落": "仄",
    "知": "平",
    "多": "平",
    "少": "仄",
    # 《登鹳雀楼》
    "白": "平",
    "日": "仄",
    "依": "平",
    "山": "平",
    "尽": "仄",
    "黄": "平",
    "河": "平",
    "入": "仄",
    "海": "仄",
    "流": "平",
    "欲": "仄",
    "穷": "平",
    "千": "平",
    "里": "仄",
    "目": "仄",
    "更": "仄",
    "一": "平",
    "层": "平",
    "楼": "平",
    # 《望庐山瀑布》
    "照": "仄",
    "香": "平",
    "炉": "平",
    "生": "平",
    "紫": "仄",
    "烟": "平",
    "遥": "平",
    "看": "仄",
    "瀑": "仄",
    "布": "仄",
    "挂": "仄",
    "川": "平",
    "飞": "平",
    "直": "平",
    "下": "仄",
    "三": "平",
    "尺": "仄",
    "银": "平",
    "九": "仄",
    "天": "平",
    # 《绝句》
    "两": "仄",
    "个": "仄",
    "鹂": "平",
    "鸣": "平",
    "翠": "仄",
    "柳": "仄",
    "行": "平",
    "鹭": "仄",
    "青": "平",
    "窗": "平",
    "含": "平",
    "西": "平",
    "岭": "仄",
    "秋": "平",
    "雪": "仄",
    "门": "平",
    "泊": "平",
    "东": "平",
    "吴": "平",
    "万": "仄",
    "船": "平",
    # 《山行》
    "远": "仄",
    "寒": "平",
    "石": "平",
    "径": "仄",
    "斜": "平",
    "云": "平",
    "有": "仄",
    "人": "平",
    "家": "平",
    "停": "平",
    "车": "平",
    "坐": "仄",
    "爱": "仄",
    "枫": "平",
    "林": "平",
    "晚": "仄",
    "叶": "仄",
    "红": "平",
    "于": "平",
    "二": "仄",
    # 《江雪》
    "绝": "平",
    "灭": "仄",
    "孤": "平",
    "舟": "平",
    "踪": "平",
    "蓑": "平",
    "笠": "仄",
    "翁": "平",
    "独": "平",
    "钓": "仄",
    "江": "平",
    # 《悯农》
    "锄": "平",
    "禾": "平",
    "当": "平",
    "午": "仄",
    "汗": "仄",
    "滴": "平",
    "土": "仄",
    "谁": "平",
    "盘": "平",
    "中": "平",
    "餐": "平",
    "粒": "仄",
    "皆": "平",
    "辛": "平",
    "苦": "仄",
    # 其他常用练习字
    "小": "仄",
    "草": "仄",
    "好": "仄",
    "老": "仄",
    "高": "平",
    "新": "平",
    "心": "平",
    "金": "平",
    "清": "平",
    "情": "平",
    "星": "平",
    "影": "仄",
    "晴": "平",
    "听": "平",
    "停": "平",
    "亭": "平",
    "城": "平",
    "成": "平",
    "争": "平",
    "登": "平",
    "灯": "平",
    "峰": "平",
    "逢": "平",
    "松": "平",
    "龙": "平",
    "空": "平",
    "钟": "平",
    "湖": "平",
    "初": "平",
    "书": "平",
    "路": "仄",
    "树": "仄",
    "竹": "平",
    "足": "平",
    "谷": "仄",
    "木": "仄",
    "屋": "平",
    "鱼": "平",
    "渔": "平",
    "语": "仄",
    "玉": "仄",
    "曲": "平",
    "合": "平",
    "开": "平",
    "台": "平",
    "裁": "平",
    "菜": "仄",
    "非": "平",
    "杯": "平",
    "归": "平",
    "水": "仄",
    "吹": "平",
    "垂": "平",
    "对": "仄",
    "苗": "平",
    "桥": "平",
    "飘": "平",
    "朝": "平",
    "愁": "平",
    "州": "平",
    "游": "平",
    "留": "平",
    "求": "平",
    "酒": "仄",
    "后": "仄",
    "厚": "仄",
    "口": "仄",
    "手": "仄",
    "间": "平",
    "年": "平",
    "边": "平",
    "田": "平",
    "圆": "平",
    "原": "平",
    "园": "平",
    "欢": "平",
    "官": "平",
    "兰": "平",
    "残": "平",
    "单": "平",
    "安": "平",
    "关": "平",
    "身": "平",
    "尘": "平",
    "晨": "平",
    "真": "平",
    "深": "平",
    "文": "平",
    "林": "平",
    "亲": "平",
    "今": "平",
    "音": "平",
    "琴": "平",
    "阴": "平",
    "村": "平",
    "魂": "平",
    "存": "平",
    "君": "平",
    "群": "平",
    "长": "平",
    "忙": "平",
    "芳": "平",
    "塘": "平",
    "墙": "平",
    "张": "平",
    "藏": "平",
    "浪": "仄",
    "让": "仄",
    "轻": "平",
    "重": "仄",
}

TONE_MAP: Mapping[str, str] = MappingProxyType(_TONE_TABLE)


class Poem(NamedTuple):
    """一首内置古诗：题目、作者、去除标点的诗句。"""

    title: str
    author: str
    lines: Tuple[str, ...]


class LineResult(NamedTuple):
    """单句分析结果。"""

    text: str
    chars: List[str]
    tones: List[str]
    pattern: str
    form: str
    last_char: Optional[str]
    rhyme_group: Optional[str]
    rhyme_name: Optional[str]


class PoemResult(NamedTuple):
    """整首（或若干句）分析结果。"""

    lines: List[LineResult]
    form: str
    line_count: int
    rhyme_consistent: bool
    rhyme_group: Optional[str]
    rhyme_name: Optional[str]
    even_chars: List[str]
    even_rhymes: List[Optional[str]]
    message: str


BUILTIN_POEMS: Tuple[Poem, ...] = (
    Poem(
        title="静夜思",
        author="李白",
        lines=("床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"),
    ),
    Poem(
        title="春晓",
        author="孟浩然",
        lines=("春眠不觉晓", "处处闻啼鸟", "夜来风雨声", "花落知多少"),
    ),
    Poem(
        title="登鹳雀楼",
        author="王之涣",
        lines=("白日依山尽", "黄河入海流", "欲穷千里目", "更上一层楼"),
    ),
    Poem(
        title="望庐山瀑布",
        author="李白",
        lines=("日照香炉生紫烟", "遥看瀑布挂前川", "飞流直下三千尺", "疑是银河落九天"),
    ),
    Poem(
        title="绝句",
        author="杜甫",
        lines=("两个黄鹂鸣翠柳", "一行白鹭上青天", "窗含西岭千秋雪", "门泊东吴万里船"),
    ),
    Poem(
        title="山行",
        author="杜牧",
        lines=("远上寒山石径斜", "白云生处有人家", "停车坐爱枫林晚", "霜叶红于二月花"),
    ),
    Poem(
        title="江雪",
        author="柳宗元",
        lines=("千山鸟飞绝", "万径人踪灭", "孤舟蓑笠翁", "独钓寒江雪"),
    ),
    Poem(
        title="悯农",
        author="李绅",
        lines=("锄禾日当午", "汗滴禾下土", "谁知盘中餐", "粒粒皆辛苦"),
    ),
)


def split_chars(line: str) -> List[str]:
    """去掉空白与标点，返回逐字列表。空串或纯标点会抛出 ValueError。"""
    if not isinstance(line, str):
        raise ValueError("诗句必须是字符串，当前类型为 %s" % type(line).__name__)
    chars: List[str] = []
    for char in line:
        if char.isspace():
            continue
        if char in PUNCTUATION:
            continue
        chars.append(char)
    if not chars:
        raise ValueError("诗句为空或只有标点，无法分析")
    return chars


def tone_of(char: str) -> str:
    """返回单字的平仄：平、仄或「？」（非汉字、字表外均返回「？」）。"""
    if not isinstance(char, str):
        raise ValueError("字符必须是字符串，当前类型为 %s" % type(char).__name__)
    if len(char) != 1:
        raise ValueError("字符必须恰好为一个字，当前为 %r" % (char,))
    return TONE_MAP.get(char, "？")


def tone_pattern(line: str) -> str:
    """返回整句的平仄串，例如「平平平仄平」。"""
    return "".join(tone_of(char) for char in split_chars(line))


def classify_form(line: str) -> str:
    """按字数判断诗体：五言、七言或其他。"""
    count = len(split_chars(line))
    if count == 5:
        return "五言"
    if count == 7:
        return "七言"
    return "其他"


def check_line(line: str) -> LineResult:
    """分析单句：逐字平仄、句式、末字韵部。"""
    chars = split_chars(line)
    tones = [tone_of(char) for char in chars]
    pattern = "".join(tones)
    form = classify_form(line)
    last_char = chars[-1]
    return LineResult(
        text=line,
        chars=chars,
        tones=tones,
        pattern=pattern,
        form=form,
        last_char=last_char,
        rhyme_group=rhyme_group(last_char),
        rhyme_name=rhyme_name(last_char),
    )


def _poem_form(lengths: List[int]) -> str:
    """根据各句字数与句数给出诗体名称。"""
    unique = set(lengths)
    if unique == set([5]):
        base = "五言"
    elif unique == set([7]):
        base = "七言"
    else:
        base = "杂言"
    count = len(lengths)
    if count == 4:
        return base + "绝句"
    if count == 8:
        return base + "律诗"
    return base + "诗"


def check_poem(lines: Sequence[str]) -> PoemResult:
    """分析多句诗：逐句平仄、诗体判断与偶数句押韵一致性。"""
    if lines is None:
        raise ValueError("诗句序列不能为空")
    if isinstance(lines, str):
        raise ValueError("请传入多行诗句组成的序列，而不是单个字符串")
    cleaned: List[str] = []
    for line in lines:
        if not isinstance(line, str):
            raise ValueError("每个诗句都必须是字符串")
        if line.strip() == "":
            continue
        cleaned.append(line)
    if not cleaned:
        raise ValueError("没有可分析的诗句")

    results = [check_line(line) for line in cleaned]
    lengths = [len(result.chars) for result in results]
    form = _poem_form(lengths)

    even = results[1::2]
    even_chars = [result.last_char for result in even]
    even_rhymes = [result.rhyme_group for result in even]

    if len(even) < 2:
        consistent = True
        group = even_rhymes[0] if even_rhymes else None
        name = even[0].rhyme_name if even else None
        message = "偶数句不足两句，暂不比较押韵。"
    elif any(item is None for item in even_rhymes):
        consistent = False
        group = None
        name = None
        message = "偶数句末字有字表外的字，无法判断是否押韵。"
    elif len(set(even_rhymes)) == 1:
        consistent = True
        group = even_rhymes[0]
        name = even[0].rhyme_name
        message = "偶数句末字同韵，押「%s」。" % (name if name is not None else group)
    else:
        consistent = False
        group = None
        name = None
        parts = []
        for result in even:
            label = result.rhyme_name if result.rhyme_name is not None else "未知"
            parts.append("%s（%s）" % (result.last_char, label))
        message = "偶数句末字不同韵：%s。" % "、".join(parts)

    return PoemResult(
        lines=results,
        form=form,
        line_count=len(results),
        rhyme_consistent=consistent,
        rhyme_group=group,
        rhyme_name=name,
        even_chars=even_chars,
        even_rhymes=even_rhymes,
        message=message,
    )


# 标准平仄模板：「中」表示可平可仄，已按「一三五不论」做入门简化。
_TEMPLATES: Dict[str, Tuple[str, ...]] = {
    "五言绝句": (
        "中仄平平仄",
        "中平仄仄平",
        "中平平仄仄",
        "中仄仄平平",
    ),
    "五言律诗": (
        "中仄平平仄",
        "中平仄仄平",
        "中平平仄仄",
        "中仄仄平平",
        "中仄平平仄",
        "中平仄仄平",
        "中平平仄仄",
        "中仄仄平平",
    ),
    "七言绝句": (
        "中平中仄仄平平",
        "中仄中平仄仄平",
        "中仄中平平仄仄",
        "中平中仄仄平平",
    ),
    "七言律诗": (
        "中平中仄仄平平",
        "中仄中平仄仄平",
        "中仄中平平仄仄",
        "中平中仄仄平平",
        "中平中仄平平仄",
        "中仄中平仄仄平",
        "中仄中平平仄仄",
        "中平中仄仄平平",
    ),
}

TEMPLATE_FORMS: Tuple[str, ...] = (
    "五言绝句",
    "七言绝句",
    "五言律诗",
    "七言律诗",
)


def template_patterns(name: str) -> List[str]:
    """返回指定诗体的标准平仄模板（绝句四行，律诗八行）。"""
    if not isinstance(name, str):
        raise ValueError("诗体名称必须是字符串")
    patterns = _TEMPLATES.get(name)
    if patterns is None:
        raise ValueError(
            "不支持的诗体：%s（可选：%s）" % (name, "、".join(TEMPLATE_FORMS))
        )
    return list(patterns)
