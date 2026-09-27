"""Hand-authored acceptance and rejection examples, excluded from all training/selection."""
import json
from pathlib import Path
from .semantics import make_graph


def examples():
    rows = []
    dog_cat = {"agent": {"concept": "aa"}, "patient": {"concept": "ab"}}
    cases = [
        ("roles", "犬が猫を追う", "The dog chases the cat", "ba", dog_cat, "affirmed", "unspecified"),
        ("roles", "猫が犬に追われる", "The cat is chased by the dog", "ba", dog_cat, "affirmed", "unspecified"),
        ("swapped", "猫が犬を追う", "The cat chases the dog", "ba", {"agent": {"concept": "ab"}, "patient": {"concept": "aa"}}, "affirmed", "unspecified"),
        ("negative", "犬が猫を追わない", "The dog does not chase the cat", "ba", dog_cat, "negated", "unspecified"),
        ("two", "2匹の犬が猫を追う", "2 dogs chase the cat", "ba", {**dog_cat, "agent": {"concept": "aa", "quantity": 2}}, "affirmed", "unspecified"),
        ("three", "3匹の犬が猫を追う", "3 dogs chase the cat", "ba", {**dog_cat, "agent": {"concept": "aa", "quantity": 3}}, "affirmed", "unspecified"),
        ("tomorrow", "明日、犬が猫を追う", "The dog chases the cat tomorrow", "ba", dog_cat, "affirmed", "tomorrow"),
        ("today", "今日、犬が猫を追う", "The dog chases the cat today", "ba", dog_cat, "affirmed", "today"),
        ("omitted", "猫を追う", "The cat is chased", "ba", {"patient": {"concept": "ab"}}, "affirmed", "unspecified"),
        ("name", "Akiが眠る", "Aki sleeps", "be", {"agent": {"concept": "ag", "name": "Aki"}}, "affirmed", "unspecified"),
        ("new_name", "Hanaが眠る", "Hana sleeps", "be", {"agent": {"concept": "ag", "name": "Hana"}}, "affirmed", "unspecified"),
        ("recipient", "先生が子供に本を渡す", "The teacher gives the book to the child", "bd", {"agent": {"concept": "ad"}, "patient": {"concept": "af"}, "recipient": {"concept": "ac"}}, "affirmed", "unspecified"),
        ("location", "公園で犬が眠る", "The dog sleeps in the park", "be", {"agent": {"concept": "aa"}, "location": {"concept": "ah"}}, "affirmed", "unspecified"),
        ("state", "子供が空腹だ", "The child is hungry", "bf", {"agent": {"concept": "ac"}}, "affirmed", "unspecified"),
    ]
    for i, (group, ja, en, predicate, entities, polarity, time) in enumerate(cases):
        for lang, text in (("ja", ja), ("en", en)):
            graph = make_graph(predicate, entities, polarity, time)
            rows.append({"id": f"challenge{i:02d}{lang}", "group": group, "combination": ["challenge", group],
                         "pattern": "challenge:" + lang, "split": "test", "language": lang, "supported": True,
                         "text": text, "spans": [], "graph": graph})
    for i, (ja, en, category) in enumerate([
        ("宇宙人が猫を追う", "The alien chases the cat", "unknown_concept"),
        ("全ての犬がある猫を追う", "Every dog chases some cat", "quantification"),
        ("犬が猫を追わないわけではない", "It is not the case that the dog does not chase the cat", "nested_negation"),
        ("彼女が眠る", "She sleeps", "anaphora"),
        ("犬が眠る。猫もそうする", "The dog sleeps. The cat does too", "cross_sentence_anaphora"),
        ("希望が眠る", "Hope sleeps", "metaphor"),
        ("犬が走り猫が眠る", "The dog runs and the cat sleeps", "multiple_events"),
    ]):
        for lang, text in (("ja", ja), ("en", en)):
            rows.append({"id": f"reject{i}{lang}", "group": f"reject{i}", "combination": None, "pattern": "challenge:" + lang,
                         "split": "test", "language": lang, "supported": False, "category": category, "text": text, "spans": [], "graph": None})
    return rows


def write(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in examples()), encoding="utf-8", newline="\n")
