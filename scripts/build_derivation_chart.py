"""Render the common morphemes of written 0.5 using its actual SVG alphabet."""
from html import escape
from pathlib import Path
from noema.render import glyph_path
from noema.semantics import ALPHABET


def build():
    rows = [("sam", ["開いている", "開く", "開ける"]),
            ("sai", ["赤い", "赤くなる", "赤くする"]),
            ("sap", ["乾いている", "乾く", "乾かす"])]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1020" height="570" viewBox="0 0 1020 570">',
             '<title>Noema 0.5 — 状態から変化の語を構成する</title>',
             '<rect width="1020" height="570" fill="#101114"/>',
             '<g font-family="system-ui,sans-serif" fill="#e4e7ec">',
             '<text x="36" y="45" font-size="23">同じ状態語に、同じ作用を付ける</text>',
             '<text x="36" y="76" font-size="14" fill="#a4acb9">固有文字で示す語形成 · 青い部分が変化／使役変化の標識</text>']
    for column, label in enumerate(["状態", "その状態になる", "その状態に変える"]):
        parts.append(f'<text x="{36 + column * 330}" y="121" font-size="16">{label}</text>')
    for row, (base, meanings) in enumerate(rows):
        for col in range(3):
            x, y = 36 + col * 330, 142 + row * 127
            word = ("" if col == 0 else "5-" if col == 1 else "6-") + base
            parts.append(f'<rect x="{x - 10}" y="{y - 9}" width="305" height="113" rx="7" fill="#181a1e" stroke="#34363b"/>')
            for i, char in enumerate(word):
                gx, gy = x + i * 39, y
                color = "#91b9ff" if col and i < 2 else "#e4e7ec"
                path = "M8 18 L25 18" if char == "-" else glyph_path(ALPHABET.index(char))
                parts.append(f'<path transform="translate({gx},{gy})" d="{path}" fill="none" stroke="{color}" stroke-width="2.3" stroke-linejoin="round" stroke-linecap="round"/>')
            parts.append(f'<text x="{x}" y="{y + 65}" font-size="18">{escape(meanings[col])}</text>')
            parts.append(f'<text x="{x}" y="{y + 88}" font-size="13" fill="#a4acb9">代用表記 {word}</text>')
    parts.append('<text x="36" y="548" font-size="13" fill="#a4acb9">代用表記の5・6は、この位置では数量を表さない。字形は既存の32文字を使用。</text></g></svg>')
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    Path("examples/word-formation.svg").write_text(build(), encoding="utf-8", newline="\n")
