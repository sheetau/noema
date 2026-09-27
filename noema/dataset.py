"""Deterministic annotated fixtures. Templates are data construction, never an analyzer."""
import hashlib
import itertools
import json
import random
import re
from pathlib import Path
from .semantics import CONCEPTS, ROLES, make_graph, normalize, require

NOUNS = {"aa": ("犬", "dog", "dogs"), "ab": ("猫", "cat", "cats"),
         "ac": ("子供", "child", "children"), "ad": ("先生", "teacher", "teachers"),
         "ae": ("鳥", "bird", "birds"), "af": ("本", "book", "books"),
         "ag": ("Aki", "Aki", "Aki"), "ah": ("公園", "park", "parks"), "ai": ("家", "home", "homes")}
VERBS = {"ba": ("追う", "追わ", "追われる", "chases", "chase", "chased"),
         "bb": ("見る", "見", "見られる", "sees", "see", "seen"),
         "bc": ("助ける", "助け", "助けられる", "helps", "help", "helped"),
         "bd": ("渡す", "渡さ", "渡される", "gives", "give", "given"),
         "be": ("眠る", "眠ら", "", "sleeps", "sleep", ""),
         "bf": ("空腹だ", "空腹で", "", "is hungry", "be hungry", "")}
MARKER = re.compile(r"\[([^|\]]+)\|([^\]]+)\]")


def mark(kind, text, role="none", concept="none", quantity=None):
    return f"[{kind}:{role}:{concept}:{quantity if quantity is not None else 'unspecified'}|{text}]"


def unmark(template):
    text, spans, cursor = "", [], 0
    for match in MARKER.finditer(template):
        text += template[cursor:match.start()]
        start = len(text)
        text += match[2]
        kind, role, concept, quantity = match[1].split(":")
        spans.append({"start": start, "end": len(text), "kind": kind, "role": role, "concept": concept, "quantity": quantity})
        cursor = match.end()
    return text + template[cursor:], spans


def phrase(concept, role, lang, quantity=None):
    noun = NOUNS[concept][0 if lang == "ja" else 2 if quantity is not None and quantity != 1 else 1]
    entity = mark("entity", noun, role, concept, quantity)
    if quantity is not None:
        count = mark("quantity", str(quantity), role)
        return count + ("匹の" if concept in ("aa", "ab") else "羽の" if concept == "ae" else "人の" if concept in ("ac", "ad", "ag") else "冊の") + entity if lang == "ja" else count + " " + entity
    return entity if lang == "ja" or concept == "ag" else "the " + entity


def build_example(predicate, agent, patient, recipient, location, polarity, time, quantity, lang, style):
    entities = {}
    for role, concept in zip(ROLES, (agent, patient, recipient, location)):
        if concept:
            entities[role] = {"concept": concept, "quantity": quantity if role == "agent" else None, "name": NOUNS[concept][0] if concept == "ag" else None}
    parts = {r: phrase(c["concept"], r, lang, c["quantity"]) for r, c in entities.items()}
    a, p, r, loc = (parts.get(k, "") for k in ROLES)
    ja, stem, passive, en, base, participle = VERBS[predicate]
    pred = lambda s: mark("predicate", s, concept=predicate)
    neg = lambda s: mark("negation", s)
    # Styles are split-exclusive template families; no runtime use of these functions.
    if lang == "ja":
        if style == "dev" and p:
            sentence = p + "が" + (a + "によって" if a else "") + (r + "に" if r else "")
            sentence += pred(passive) if polarity == "affirmed" else pred(passive[:-1]) + neg("ない")
        else:
            subject = a + "が" if a else ""
            objects = (r + "に" if r else "") + (p + "を" if p else "")
            sentence = objects + subject if style == "test" and p else subject + objects
            sentence += pred(ja) if polarity == "affirmed" else pred(stem) + neg("ない")
        if loc:
            sentence = loc + "で、" + sentence if style == "dev" else sentence + "、" + loc + "で"
        if time != "unspecified":
            t = mark("time", {"yesterday": "昨日", "today": "今日", "tomorrow": "明日"}[time])
            sentence = t + "、" + sentence if style == "test" else sentence + "、" + t
        if style == "test":
            sentence += "。"
    else:
        if not a and p:
            sentence = p + " is " + (neg("not") + " " if polarity == "negated" else "") + pred(participle)
        elif style == "dev" and p:
            sentence = p + " is " + (neg("not") + " " if polarity == "negated" else "") + pred(participle) + (" to " + r if r else "") + " by " + a
        elif predicate == "bf":
            sentence = a + (" are " if quantity not in (None, 1) else " is ") + (neg("not") + " " if polarity == "negated" else "") + pred("hungry")
        else:
            verb = base if quantity not in (None, 1) else en
            sentence = a + " " + (pred(verb) if polarity == "affirmed" else ("do " if quantity not in (None, 1) else "does ") + neg("not") + " " + pred(base))
            sentence += (" " + p if p and style != "test" else "") + (" to " + r if r else "")
            if style == "test" and p:
                sentence = p + ", " + sentence
        if loc:
            sentence = "in " + loc + ", " + sentence if style == "dev" and not p else sentence + " in " + loc
        if time != "unspecified":
            t = mark("time", time)
            sentence = t + ", " + sentence if style == "test" else sentence + " " + t
        if style == "test":
            sentence += "."
    text, spans = unmark(sentence)
    return text, spans, make_graph(predicate, entities, polarity, time)


def build_dataset():
    combinations = []
    for predicate in VERBS:
        for agent in ("aa", "ab", "ac", "ad", "ae", "ag", None):
            if agent is None and predicate in ("be", "bf", "bd"):
                continue
            for patient in (("af",) if predicate == "bd" else (None,) if predicate in ("be", "bf") else ("aa", "ab", "ac", "ad", "ae")):
                if agent == patient:
                    continue
                for location in (None, "ah", "ai"):
                    combinations.append((predicate, agent, patient, "ac" if predicate == "bd" else None, location))
    random.Random(41).shuffle(combinations)
    examples = []
    for index, combo in enumerate(combinations):
        split = "train" if index % 10 < 6 else "dev" if index % 10 < 8 else "test"
        # Hold out genuinely different order/voice families, not just different IDs.
        if split == "dev" and combo[2] is None and combo[4] is None:
            continue
        if split in ("dev", "test") and combo[1] is None:
            continue
        for variant, (polarity, time, quantity) in enumerate(itertools.product(("affirmed", "negated"), ("unspecified", "today", "tomorrow"), (None, 2))):
            if split == "test" and combo[2] is None and time == "unspecified":
                continue
            # Named persons and omitted actors do not receive an artificial count.
            if combo[1] in (None, "ag") and quantity is not None:
                continue
            for lang in ("ja", "en"):
                text, spans, graph = build_example(*combo, polarity, time, quantity, lang, split)
                group = f"c{index:04d}v{variant:02d}"
                examples.append({"id": group + lang, "group": group, "combination": list(combo), "pattern": lang + ":" + split,
                                 "split": split, "language": lang, "supported": True, "text": text, "spans": spans, "graph": graph})
    unsupported = {
        "train": [("全ての犬が猫を追う", "Every dog chases a cat", "quantification"), ("犬が猫を追い、鳥が眠る", "The dog chases the cat and the bird sleeps", "multiple_events"), ("ドラゴンが猫を追う", "The dragon chases the cat", "unknown_concept"), ("彼が眠る", "He sleeps", "anaphora")],
        "dev": [("猫が眠らないわけではない", "It is not true that the cat does not sleep", "nested_negation"), ("心が踊る", "My heart dances", "metaphor"), ("犬はなぜ眠るのか", "Why does the dog sleep?", "question"), ("ロボットが本を渡す", "The robot gives a book", "unknown_concept")],
        "test": [("ほとんどの鳥が犬を見る", "Most birds see a dog", "quantification"), ("先生が眠らないとは限らない", "The teacher is not necessarily not sleeping", "nested_negation"), ("犬を見た。それは眠った", "I saw a dog. It slept", "cross_sentence_anaphora"), ("時間が走る", "Time runs", "metaphor"), ("猫を追う犬が眠る", "The dog that chases the cat sleeps", "relative_clause"), ("ユニコーンが鳥を助ける", "The unicorn helps the bird", "unknown_concept"), ("", "", "empty")]
    }
    for split, rows in unsupported.items():
        for index, (ja, en, category) in enumerate(rows):
            for lang, text in (("ja", ja), ("en", en)):
                ident = f"u{split}{index}"
                examples.append({"id": ident + lang, "group": ident, "combination": None, "pattern": lang + ":unsupported:" + split,
                                 "split": split, "language": lang, "supported": False, "category": category, "text": text, "spans": [], "graph": None})
    return examples


def validate_dataset(rows):
    ids, groups, combinations, patterns, texts = set(), {}, {}, {}, {}
    for row in rows:
        require(row["id"] not in ids, "Duplicate example ID")
        ids.add(row["id"])
        require(row["split"] in ("train", "dev", "test") and row["language"] in ("ja", "en"), "Invalid split/language")
        for table, key in ((groups, row["group"]), (patterns, row["pattern"]), (texts, (row["language"], row["text"]))):
            require(key not in table or table[key] == row["split"], "Cross-split leakage")
            table[key] = row["split"]
        if row["supported"]:
            key = tuple(row["combination"])
            require(key not in combinations or combinations[key] == row["split"], "Concept-combination leakage")
            combinations[key] = row["split"]
            normalize(row["graph"])
            last = 0
            for span in row["spans"]:
                require(last <= span["start"] < span["end"] <= len(row["text"]), "Invalid or overlapping annotation")
                last = span["end"]
    return {split: {lang: sum(r["split"] == split and r["language"] == lang for r in rows) for lang in ("ja", "en")} for split in ("train", "dev", "test")}


def write_dataset(path):
    rows = build_dataset()
    validate_dataset(rows)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8", newline="\n")
    return rows


def load_dataset(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    validate_dataset(rows)
    return rows


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
