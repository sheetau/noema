"""One-to-one SVG glyph substitution. Literals are visibly quoted Unicode text."""
from html import escape
from .grammar import format_graph, parse, tokens, notation_of
from .semantics import ALPHABET, require
from .script import SPECS


def glyph_path(index, alphabet="v1"):
    require(alphabet in SPECS, "Unknown alphabet edition")
    return SPECS[alphabet]["paths"][index]


def legacy_glyph_path(index):
    # Eight distinct open skeletons, four positional diacritics: 32 fixed letters.
    skeletons = ["M8 6 Q24 6 24 18 Q24 30 8 30", "M8 6 L24 18 L8 30",
                 "M24 6 L8 6 L8 30 L24 30", "M8 6 L24 6 L8 30 L24 30",
                 "M16 6 Q0 18 16 30 Q32 18 16 6", "M8 30 L16 6 L24 30",
                 "M8 6 L8 24 Q16 36 24 24 L24 6", "M8 6 Q28 12 16 18 Q4 24 24 30"]
    marks = ["M12 1 L20 1", "M29 11 L29 19", "M12 35 L20 35", "M3 11 L3 19"]
    return skeletons[index % 8] + " " + marks[index // 8]


def render(text, columns=34, alphabet="v1", notation=None):
    require(alphabet in SPECS, "Unknown alphabet edition")
    if type(columns) is not int or columns < 8:
        raise ValueError("columns must be an integer >= 8")
    graph = parse(text)
    notation = notation or notation_of(text)
    canonical = format_graph(graph, notation)
    gaps = None
    if graph["schema_version"] in ("0.8", "0.9", "0.10", "0.11", "0.12", "0.13", "0.14"):
        from .discourse import tokenize
        stream = tokenize(canonical)
    elif graph["schema_version"] in ("0.2", "0.3", "0.4", "0.5", "0.6", "0.7"):
        from .language import tokenize
        if notation == "compact":
            spans = [(canonical[:2], 0, 2)] + [(t, a + 2, b + 2) for t, a, b in tokenize(canonical[2:])]
            stream = [t[0] for t in spans]
            gaps = [bool(canonical[b:spans[i + 1][1]]) if i + 1 < len(spans) else False for i, (_, _, b) in enumerate(spans)]
        else:
            stream = [t[0] for t in tokenize(canonical)]
    else:
        stream = tokens(canonical)
    shape = (lambda i: glyph_path(i, alphabet)) if alphabet == "v2" or graph["schema_version"] in ("0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "0.10", "0.11", "0.12", "0.13", "0.14") else legacy_glyph_path
    defs = ''.join(f'<path id="g{i}" d="{shape(i)}"/>' for i in range(32))
    body, x, y = [], 18, 20
    width = columns * 34 + 36
    for index, token in enumerate(stream):
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
        if gaps is None or gaps[index]:
            x += 14
        if token in ("{", ";", "}", "."):
            x, y = 18, y + 54
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{y + 50}" viewBox="0 0 {width} {y + 50}"><title>Noema {graph["schema_version"]}</title><metadata>{escape(canonical)}</metadata><rect width="100%" height="100%" fill="#fbfaf4"/><defs>{defs}</defs><g fill="none" stroke="#162736" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{"".join(body)}</g></svg>'


def alphabet_svg(alphabet="v1"):
    require(alphabet in SPECS, "Unknown alphabet edition")
    if alphabet == "v2":
        return functional_alphabet_svg()
    body = []
    for i, c in enumerate(ALPHABET):
        x, y = 25 + (i % 8) * 80, 20 + (i // 8) * 90
        body.append(f'<path transform="translate({x},{y})" d="{glyph_path(i, alphabet)}"/><text x="{x + 12}" y="{y + 60}" stroke="none" fill="#162736" font-size="16">{c}</text>')
    return '<svg xmlns="http://www.w3.org/2000/svg" width="660" height="380"><rect width="100%" height="100%" fill="#fbfaf4"/><g fill="none" stroke="#162736" stroke-width="2">' + ''.join(body) + '</g></svg>'


def functional_alphabet_svg():
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="940" viewBox="0 0 1200 940">',
             '<title>Noema文字版2 — 文法上の働きから字形を構成する</title>',
             '<rect width="1200" height="940" fill="#101114"/>',
             '<g font-family="system-ui,sans-serif" fill="#e4e7ec">',
             '<text x="28" y="40" font-size="23">Noema · 文法の働きを字形にも表す</text>',
             '<text x="28" y="70" font-size="14" fill="#a4acb9">白：群に共通する骨格　青：働きを区別する線　／　人による読みやすさは未検証</text>']
    for row, (family, data) in enumerate(SPECS["v2"]["families"].items()):
        y = 104 + row * 111
        parts.append(f'<text x="28" y="{y + 35}" font-size="16">{escape(data["label_ja"])}</text>')
        for col, alias in enumerate(data["letters"]):
            x = 204 + col * 120
            letter = SPECS["v2"]["letters"][alias]
            parts.append(f'<rect x="{x - 12}" y="{y - 9}" width="113" height="100" rx="5" fill="#181a1e"/>')
            parts.append(f'<g transform="translate({x + 16},{y}) scale(1.2)" fill="none" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">')
            parts.append(f'<path stroke="#e4e7ec" d="{data["path"]}"/>')
            feature_path = " ".join(SPECS["v2"]["features"][f] for f in letter["features"])
            parts.append(f'<path stroke="#91b9ff" d="{feature_path}"/></g>')
            label = letter["function_ja"] if family != "lexical" else "語内の文字"
            parts.append(f'<text text-anchor="middle" x="{x + 44}" y="{y + 65}" font-size="13">{escape(label)}</text>')
            parts.append(f'<text text-anchor="middle" x="{x + 44}" y="{y + 83}" font-size="12" fill="#a4acb9">{alias} · U+{SPECS["v2"]["unicode_start"] + ALPHABET.index(alias):04X}</text>')
    parts.append('<text x="28" y="910" font-size="14" fill="#a4acb9">文法標識として使う位置での対応。語・参照名・数量の中の文字に、これらの意味を追加しない。</text></g></svg>')
    return "\n".join(parts) + "\n"
