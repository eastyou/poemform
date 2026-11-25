# poemform

[![CI](https://github.com/eastyou/poemform/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/poemform/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)

poemform 是一个面向中小学课堂的古诗词格律入门工具。它按现代普通话粗略判断平仄、用韵母归并表做同韵判断，并能生成可打印的 A4 练习纸。只依赖 Python 标准库，安装后即可使用。

本工具是**教学简化版**，不研究入声、平水韵或严格格律，适合入门练习，不适合作为音韵学或格律考证的依据。

## 特性

- 平仄判定：一、二声记为平，三、四声记为仄，字表外返回「？」。
- 诗句分析：自动去标点，统计字数并判断五言、七言或其他。
- 押韵判断：按普通话韵母归并为若干韵部，粗略判断多字是否同韵。
- 诗体识别：根据句数与字数给出「五言绝句」「七言律诗」等名称。
- 押韵检查：检查偶数句末字是否同韵，并输出韵部名。
- 标准模板：内置五言/七言绝句与律诗的平仄模板，「中」表示可平可仄。
- 练习纸：可生成 A4 排版 HTML，支持随机种子复现与答案页。
- 演示页：内置 8 首公有领域古诗，直接展示逐句平仄。
- 零依赖：仅使用 Python 标准库，支持 Python 3.9 及以上。

## 安装

```bash
pip install .
```

安装后可直接运行 `poemform`。也可以在仓库根目录用模块方式运行：

```bash
python -m poemform --help
```

## 使用

### check：分析诗句

```text
$ poemform check "床前明月光"
诗句：床前明月光
字数：5（五言）
平仄：平平平仄平
  床：平
  前：平
  明：平
  月：仄
  光：平
末字韵：光 → 阳韵（ang/iang/uang）
```

一次传入多句时，会额外给出诗体与押韵结论：

```text
$ poemform check "床前明月光" "疑是地上霜" "举头望明月" "低头思故乡"
...
诗体：五言绝句（共 4 句）
偶数句押韵：偶数句末字同韵，押「阳韵（ang/iang/uang）」。
押韵是否一致：是
```

### rhyme：判断是否同韵

```text
$ poemform rhyme 光 霜 乡
光：uang → 阳韵（ang/iang/uang）
霜：uang → 阳韵（ang/iang/uang）
乡：iang → 阳韵（ang/iang/uang）

结果：3 字同韵，同属阳韵（ang/iang/uang）。
```

### template：查看标准平仄模板

```text
$ poemform template 七言绝句
诗体：七言绝句
平仄模板（「中」表示可平可仄）：
  1. 中平中仄仄平平
  2. 中仄中平仄仄平
  3. 中仄中平平仄仄
  4. 中平中仄仄平平
```

### scan：分析诗句文件

文件每行一句，空行会被忽略，句中标点会自动去掉。

```text
$ poemform scan poem.txt
第 1 句：床前明月光
  平仄：平平平仄平（五言）
第 2 句：疑是地上霜
  平仄：平仄仄仄平（五言）
第 3 句：举头望明月
  平仄：仄平仄平仄（五言）
第 4 句：低头思故乡
  平仄：平平平仄平（五言）

诗体：五言绝句（共 4 句）
偶数句押韵：偶数句末字同韵，押「阳韵（ang/iang/uang）」。
押韵是否一致：是
```

### sheet：生成练习纸

```text
$ poemform sheet --count 4 --seed 1 -o sheet.html --answers
已生成练习纸：sheet.html（4 题，含答案页）
```

打开 `sheet.html` 即可打印。练习内容包括标平仄、判断五言/七言与圈出押韵字。

### demo：生成演示页

```text
$ poemform demo -o demo.html
已生成演示页：demo.html
```

### 参数

| 子命令 | 参数 | 说明 |
| --- | --- | --- |
| `check` | `诗句...` | 一句或多句诗，按顺序传入 |
| `rhyme` | `汉字...` | 要比较的汉字，每个参数一个字 |
| `template` | `诗体` | `五言绝句`、`七言绝句`、`五言律诗`、`七言律诗` |
| `scan` | `文件` | UTF-8 文本文件，每行一句 |
| `sheet` | `--count` | 题目数量，1 到 50，默认 10 |
| `sheet` | `--seed` | 随机种子，相同种子结果可复现 |
| `sheet` | `-o, --output` | 输出 HTML 路径，默认 `sheet.html` |
| `sheet` | `--answers` | 附加参考答案页 |
| `demo` | `-o, --output` | 输出 HTML 路径，默认 `demo.html` |

### 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 执行成功 |
| `2` | 参数错误或输入校验失败（如空诗句、题数越界、文件无法读取） |

## 作为库使用

```python
from poemform import (
    check_line,
    check_poem,
    classify_form,
    render_sheet,
    rhyme_group,
    rhyme_name,
    tone_of,
    tone_pattern,
)

print(tone_of("床"))                 # 平
print(tone_pattern("床前明月光"))     # 平平平仄平
print(classify_form("春眠不觉晓"))    # 五言
print(rhyme_group("光"))             # ang
print(rhyme_name("光"))              # 阳韵（ang/iang/uang）

result = check_line("床前明月光")
print(result.form, result.rhyme_name)

poem = check_poem(["床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"])
print(poem.form, poem.rhyme_consistent)

html_text = render_sheet(count=4, seed=1, answers=False)
```

主要 API：

| 名称 | 说明 |
| --- | --- |
| `TONE_MAP` | 只读字表，汉字到平仄 |
| `RHYME_FINALS` / `RHYME_GROUPS` | 只读韵母表与韵部名表 |
| `split_chars(line)` | 去标点后返回逐字列表 |
| `tone_of(char)` | 返回「平」「仄」或「？」 |
| `tone_pattern(line)` | 返回整句平仄串 |
| `classify_form(line)` | 返回「五言」「七言」或「其他」 |
| `rhyme_group(char)` / `rhyme_name(char)` | 返回韵部键或韵部名，无法判断时为 `None` |
| `check_line(line)` | 返回单句分析结果 `LineResult` |
| `check_poem(lines)` | 返回整首分析结果 `PoemResult` |
| `template_patterns(name)` | 返回指定诗体的平仄模板列表 |
| `render_sheet(count, seed, answers)` | 返回练习纸 HTML 字符串 |
| `render_demo()` | 返回演示页 HTML 字符串 |

空字符串、纯标点、非字符串等非法输入会抛出中文 `ValueError`。

## 开发与测试

```bash
python -m unittest discover -s tests -v
```

当前共 125 个单元测试，覆盖正常输入、边界条件、命令行退出码与 HTML 结构。CI 会在 Python 3.9 到 3.13 上运行同一套测试，并检查 `python -m poemform --help`。

## 教学简化说明

- 平仄：按现代普通话判断，一、二声约等于平声，三、四声约等于仄声。诗中不处理入声，也不处理「一」「不」等的变调，因此部分在传统格律中读仄的字可能被标为平。
- 多音字：字表只固定一个读音，例如「觉」取 jué，记作平声；不同读音可能改变结果。
- 字表范围：只收录内置诗作和常用练习字，遇到字表外的字会返回「？」，不会猜测读音。
- 韵部：按普通话韵母归并，例如把 `ang`、`iang`、`uang` 视为同韵，把 `ou`、`iu` 视为同韵。这只是「听起来押韵」的粗略判断，不等同于平水韵。
- 押韵检查：只比较偶数句末字，不评价首句是否入韵，也不判断是否合律。

## License

[MIT](LICENSE) © 2026 eastyou
