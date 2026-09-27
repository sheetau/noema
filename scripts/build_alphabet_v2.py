"""Author 32 glyphs from grammatical families and explicit functional features."""
import json
from pathlib import Path
from noema.semantics import ALPHABET

FAMILIES = {
    "role": ("役割", "M17 12 L23 18 L17 24 L11 18 L17 12"),
    "time": ("時間", "M5 23 L29 23 M17 18 L17 29"),
    "reference": ("対象の指定・参照", "M6 8 L6 28 L28 28 L28 8"),
    "scope": ("論理・作用範囲", "M9 6 L4 18 L9 30 M25 6 L30 18 L25 30"),
    "discourse": ("発話・未確定", "M6 10 Q6 4 13 4 L22 4 Q28 4 28 10 M6 10 L6 29 M28 10 L28 29"),
    "change": ("状態の変化", "M6 26 L17 26 L17 8 L29 8"),
    "lexical": ("語内専用", "M6 9 L17 9 L17 27 L28 27"),
}
FEATURES = {
    "out_right": "M23 18 L30 18 M26 14 L30 18 L26 22",
    "in_left": "M3 18 L11 18 M7 14 L11 18 L7 22",
    "in_top": "M17 2 L17 11 M13 7 L17 11 L21 7",
    "spatial_frame": "M5 5 L29 5 M5 31 L29 31",
    "out_left": "M11 18 L3 18 M7 14 L3 18 L7 22",
    "in_right": "M31 18 L23 18 M27 14 L23 18 L27 22",
    "support": "M17 24 L17 31 M9 31 L25 31",
    "benefit": "M5 4 L11 4 L11 10 M11 4 L4 11 M23 26 L23 32 L30 32",
    "past": "M11 7 L5 12 L11 17",
    "present": "M17 5 L21 11 L17 17 L13 11 L17 5",
    "future": "M23 7 L29 12 L23 17",
    "past_day": "M5 27 L5 32 M11 27 L11 32",
    "present_day": "M8 27 L8 32 L26 32 L26 27",
    "future_day": "M23 27 L23 32 M29 27 L29 32",
    "calendar": "M10 5 L24 5 L24 15 L10 15 L10 5 M14 3 L14 7 M20 3 L20 7",
    "count": "M11 12 L11 22 M17 12 L17 22 M23 12 L23 22",
    "literal": "M10 12 L14 12 L14 19 L10 19 M20 12 L24 12 L24 19 L20 19",
    "bind": "M17 2 L17 21 M12 16 L17 21 L22 16",
    "reuse": "M17 22 L17 3 M12 8 L17 3 L22 8",
    "negation": "M11 9 L23 27",
    "conjunction": "M12 12 L12 24 M22 12 L22 24 M12 18 L22 18",
    "disjunction": "M10 11 L17 18 L24 11 M17 18 L17 26",
    "conditional": "M11 18 L24 18 M19 12 L24 18 L19 24",
    "question": "M11 15 Q11 10 17 10 Q23 10 23 15 L17 20 L17 23 M17 28 L17 29",
    "query_slot": "M17 11 L24 18 L17 25 L10 18 L17 11",
    "request": "M17 28 L17 13 M11 19 L17 13 L23 19",
    "unspecified": "M11 15 L23 15 M11 23 L23 23",
    "transition": "M24 3 L29 8 L24 13",
    "cause": "M4 7 L11 7 L11 18 M7 14 L11 18 L15 14",
    "lexical_a": "M6 9 L6 27 L12 27",
    "lexical_h": "M22 4 L28 9 L22 14",
    "lexical_7": "M6 4 L6 9 M22 20 L28 14 L28 27",
}
SYMBOLS = {
    "i": ("role", ["out_right"], "主体"), "j": ("role", ["in_left"], "対象"),
    "k": ("role", ["in_top"], "受け手"), "l": ("role", ["spatial_frame"], "場所"),
    "z": ("role", ["spatial_frame", "out_left"], "出発地"), "2": ("role", ["spatial_frame", "in_right"], "到着地"),
    "3": ("role", ["support"], "道具"), "4": ("role", ["benefit"], "受益者"),
    "e": ("time", ["past"], "過去"), "f": ("time", ["present"], "現在"),
    "g": ("time", ["future"], "未来"), "r": ("time", ["past", "past_day"], "昨日"),
    "s": ("time", ["present", "present_day"], "今日"), "t": ("time", ["future", "future_day"], "明日"),
    "q": ("time", ["calendar"], "日付"),
    "m": ("reference", ["count"], "数量"), "n": ("reference", ["literal"], "名前"),
    "o": ("reference", ["bind"], "参照を登録"), "p": ("reference", ["reuse"], "参照を使用"),
    "u": ("scope", ["negation"], "否定"), "w": ("scope", ["conjunction"], "両方"),
    "x": ("scope", ["disjunction"], "少なくとも一方"), "y": ("scope", ["conditional"], "条件"),
    "b": ("discourse", ["question"], "質問"), "c": ("discourse", ["query_slot"], "尋ねる役割"),
    "d": ("discourse", ["request"], "依頼"), "v": ("discourse", ["unspecified"], "肯否未指定"),
    "5": ("change", ["transition"], "状態になる"), "6": ("change", ["transition", "cause"], "状態に変える"),
    "a": ("lexical", ["lexical_a"], "単独の文法標識なし"),
    "h": ("lexical", ["lexical_h"], "単独の文法標識なし"),
    "7": ("lexical", ["lexical_7"], "単独の文法標識なし"),
}


def build():
    assert set(SYMBOLS) == set(ALPHABET)
    entries, paths = {}, []
    for char in ALPHABET:
        family, features, label = SYMBOLS[char]
        path = " ".join([FAMILIES[family][1]] + [FEATURES[f] for f in features])
        entries[char] = {"family": family, "features": features, "function_ja": label}
        paths.append(path)
    assert len(set(paths)) == 32
    return {"version": "2.0-draft", "name": "Noema Functional", "unicode_start": 57600,
            "viewbox": [0, 0, 34, 36], "stroke_width": 2.3,
            "interpretation": "Function hints apply in grammatical positions. Letters inside lexical roots, references or numbers do not add those grammatical meanings.",
            "families": {k: {"label_ja": v[0], "path": v[1], "letters": [c for c, entry in SYMBOLS.items() if entry[0] == k]} for k, v in FAMILIES.items()},
            "features": FEATURES, "letters": entries, "paths": paths}


if __name__ == "__main__":
    Path("noema/resources/alphabet-v2.json").write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
