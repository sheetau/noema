"""One-to-one SVG glyph substitution. Literals are visibly quoted Unicode text."""
from html import escape
from .grammar import format_graph, parse, tokens
from .semantics import ALPHABET


def glyph_path(index):
    # Eight distinct open skeletons, four positional diacritics: 32 fixed letters.
    skeletons = ["M8 6 Q24 6 24 18 Q24 30 8 30", "M8 6 L24 18 L8 30",
                 "M24 6 L8 6 L8 30 L24 30", "M8 6 L24 6 L8 30 L24 30",
                 "M16 6 Q0 18 16 30 Q32 18 16 6", "M8 30 L16 6 L24 30",
                 "M8 6 L8 24 Q16 36 24 24 L24 6", "M8 6 Q28 12 16 18 Q4 24 24 30"]
    marks = ["M12 1 L20 1", "M29 11 L29 19", "M12 35 L20 35", "M3 11 L3 19"]
    return skeletons[index % 8] + " " + marks[index // 8]


def render(text, columns=34):
    if type(columns) is not int or columns < 8:
        raise ValueError("columns must be an integer >= 8")
    canonical = format_graph(parse(text))
    defs = ''.join(f'<path id="g{i}" d="{glyph_path(i)}"/>' for i in range(32))
    body, x, y = [], 18, 20
    width = columns * 34 + 36
    for token in tokens(canonical):
        literal = token.startswith('"')
        units = list(token) if literal else [token] if token in "{};?" else list(token)
        if x + min(len(units), columns) * 34 > width - 18:
            x, y = 18, y + 54
        for char in units:
            if x + 34 > width - 18:
                x, y = 18, y + 54
            if not literal and char in ALPHABET:
                body.append(f'<use href="#g{ALPHABET.index(char)}" x="{x}" y="{y}"/>')
            else:
                body.append(f'<text x="{x + 4}" y="{y + 26}" stroke="none" fill="#162736" font-family="sans-serif" font-size="22">{escape(char)}</text>')
            x += 34
        x += 14
        if token in ("{", ";", "}"):
            x, y = 18, y + 54
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{y + 50}" viewBox="0 0 {width} {y + 50}"><title>Noema a/a</title><metadata>{escape(canonical)}</metadata><rect width="100%" height="100%" fill="#fbfaf4"/><defs>{defs}</defs><g fill="none" stroke="#162736" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{"".join(body)}</g></svg>'


def alphabet_svg():
    body = []
    for i, c in enumerate(ALPHABET):
        x, y = 25 + (i % 8) * 80, 20 + (i // 8) * 90
        body.append(f'<path transform="translate({x},{y})" d="{glyph_path(i)}"/><text x="{x + 12}" y="{y + 60}" stroke="none" fill="#162736" font-size="16">{c}</text>')
    return '<svg xmlns="http://www.w3.org/2000/svg" width="660" height="380"><rect width="100%" height="100%" fill="#fbfaf4"/><g fill="none" stroke="#162736" stroke-width="2">' + ''.join(body) + '</g></svg>'
