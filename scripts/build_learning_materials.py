"""Build reference tables and reading artifacts from versioned source data."""
import json
from pathlib import Path
from noema.language import policy
from noema.glossary import lexicon
from noema.grammar import parse
from noema.render import render


def build(root):
    roots, concepts, markers, _ = policy("0.3")
    localized = {w["id"]: w["definition_ja"] for w in lexicon()["words"]}
    inverse = {v: k for k, v in markers.items()}
    lines = ["# Noema 0.3の語彙参照", "", "語形・概念ID・定義は版付き資源から生成する。短い日本語見出しは検索用であり、意味の範囲は定義と役割の型で定める。英語の定義も資源に保持する。詳しい文法は [記述体系](writing-v03.md) を参照。", "", "定義中の主体は `i`、対象は `j`、受け手は `k`、場所は `l`、出発地は `z`、到着地は `2`、道具は `3`、受益者は `4` に対応する。", ""]
    for kind, title in (("entity", "対象"), ("place", "場所"), ("event", "出来事"), ("state", "状態")):
        lines += ["## " + title, "", "| 語 | 日本語見出し | ID | 役割標識 | 定義 |", "|---|---|---|---|---|"]
        for ident, value in concepts.items():
            if value["kind"] == kind:
                roles = " ".join(inverse[r] for r in value.get("roles", [])) or "—"
                lines.append(f"| `{roots[ident]}` | {value['ja']} | `{ident}` | {roles} | {localized[ident]} |")
        lines.append("")
    reference = "\n".join(lines)
    readings = json.loads((root / "examples/reading.json").read_text(encoding="utf-8"))
    lines = ["# Noemaの対訳読本", "", "各文章は一つの文書で、空行は段落の区切りである。対訳の行番号は文の順と対応する。原文にない主体・時刻・同一性を読み足さない。", ""]
    for story in readings:
        parse(story["noema"])
        lines += ["## " + story["title"], "", "```text", story["noema"], "```", "", "| 文 | 日本語 | English |", "|---|---|---|"]
        lines += [f"| {i+1} | {ja} | {en} |" for i, (ja, en) in enumerate(zip(story["ja"], story["en"]))]
        lines.append("")
    return {"docs/lexicon-v03.md": reference, "docs/readings.md": "\n".join(lines),
            "examples/school.noema": readings[0]["noema"] + "\n", "examples/school.svg": render(readings[0]["noema"], 26) + "\n"}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    for path, text in build(root).items():
        (root / path).write_text(text, encoding="utf-8", newline="\n")
