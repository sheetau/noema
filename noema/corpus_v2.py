"""Broader, frozen-before-training fixtures for a second extraction experiment.

All surface realization is data authoring. Inference never imports this module.
The historical corpus remains a regression set, not a newly blinded benchmark.
"""
import hashlib
import itertools
import json
import random
from pathlib import Path
from .dataset import NOUNS, VERBS, mark, unmark
from .semantics import ROLES, make_graph, normalize, require

SPLITS = ("train", "dev", "test")
NAMES = {"train": ("Aki", "Mio", "Ren", "Sora"), "dev": ("Kai", "Yui"), "test": ("Hana", "Tao")}
TEMPLATES = {"train": ("active", "passive"), "dev": ("place_first", "passive_time_first"), "test": ("object_first", "passive_place_first")}
PAST = {"ba": ("追った", "追わなかった", "chased"), "bb": ("見た", "見なかった", "saw"),
        "bc": ("助けた", "助けなかった", "helped"), "bd": ("渡した", "渡さなかった", "gave"),
        "be": ("眠った", "眠らなかった", "slept"), "bf": ("空腹だった", "空腹でなかった", "was hungry")}


def phrase(concept, role, lang, quantity=None, name=None):
    ja, en, plural = NOUNS[concept]
    noun = name if concept == "ag" else ja if lang == "ja" else plural if quantity not in (None, 1) else en
    token = mark("entity", noun, role, concept, quantity)
    if quantity is not None:
        num = mark("quantity", str(quantity), role, quantity=quantity)
        counter = "匹の" if concept in ("aa", "ab") else "羽の" if concept == "ae" else "人の" if concept in ("ac", "ad") else "冊の"
        return num + counter + token if lang == "ja" else num + " " + token
    return token if lang == "ja" or concept == "ag" else "the " + token


def realize(combo, quantities, name, polarity, temporal, lang, template):
    predicate, agent, patient, recipient, location = combo
    concepts = dict(zip(ROLES, (agent, patient, recipient, location)))
    entities = {role: {"concept": c, "quantity": quantities.get(role), "name": name if c == "ag" else None} for role, c in concepts.items() if c}
    p = {role: phrase(e["concept"], role, lang, e["quantity"], e["name"]) for role, e in entities.items()}
    a, obj, receiver, loc = (p.get(role, "") for role in ROLES)
    ja, stem, passive, en, base, participle = VERBS[predicate]
    negative = polarity == "negated"
    past = temporal in ("past", "yesterday")
    future = temporal in ("future", "tomorrow")
    passive_voice = bool(obj) and (template.startswith("passive") or not a)
    pred = lambda value: mark("predicate", value, concept=predicate)
    # Inflected predicates are annotated as one span; polarity remains independent.
    if lang == "ja":
        if passive_voice:
            verb = passive[:-1] + ("なかった" if negative and past else "ない" if negative else "た" if past else "る")
            sentence = obj + "が" + (a + "によって" if a else "") + (receiver + "に" if receiver else "") + pred(verb)
        else:
            verb = PAST[predicate][1 if negative else 0] if past else stem + "ない" if negative else ja
            subject = a + "が" if a else ""
            objects = (receiver + "に" if receiver else "") + (obj + "を" if obj else "")
            sentence = (objects + subject if template == "object_first" else subject + objects) + pred(verb)
        if loc:
            if "place_first" in template:
                sentence = loc + "で、" + sentence
            elif a and not passive_voice:
                subject = a + "が"
                sentence = sentence.replace(subject, subject + loc + "で", 1)
            else:
                sentence = loc + "で" + sentence
        if temporal in ("today", "tomorrow", "yesterday"):
            t = mark("time", {"today": "今日", "tomorrow": "明日", "yesterday": "昨日"}[temporal])
            sentence = t + "、" + sentence if "first" in template else sentence + "、" + t
        elif temporal == "future":
            sentence = mark("time", "今後") + "、" + sentence
        elif temporal == "present":
            sentence = mark("time", "今") + "、" + sentence
        sentence += "。"
    else:
        plural_agent = quantities.get("agent") not in (None, 1)
        plural_patient = quantities.get("patient") not in (None, 1)
        if passive_voice:
            auxiliary = "will be" if future else ("were" if plural_patient else "was") if past else ("are" if plural_patient else "is")
            if negative:
                auxiliary = auxiliary.replace("will be", "will not be") if future else auxiliary + " not"
            sentence = obj + " " + auxiliary + " " + pred(participle) + (" to " + receiver if receiver else "") + (" by " + a if a else "")
        elif predicate == "bf":
            auxiliary = "will be" if future else ("were" if plural_agent else "was") if past else ("are" if plural_agent else "is")
            if negative:
                auxiliary = "will not be" if future else auxiliary + " not"
            sentence = a + " " + auxiliary + " " + pred("hungry")
        else:
            if negative:
                auxiliary = "will not" if future else "did not" if past else "do not" if plural_agent else "does not"
                verb = auxiliary + " " + pred(base)
            elif future:
                verb = "will " + pred(base)
            else:
                verb = pred(PAST[predicate][2] if past else base if plural_agent else en)
            sentence = a + " " + verb + (" " + obj if obj and template != "object_first" else "") + (" to " + receiver if receiver else "")
            if template == "object_first" and obj:
                sentence = obj + ", " + sentence
        if loc:
            sentence = "in " + loc + ", " + sentence if "place_first" in template else sentence + " in " + loc
        if temporal in ("today", "tomorrow", "yesterday", "present"):
            t = mark("time", "now" if temporal == "present" else temporal)
            sentence = t + ", " + sentence if "first" in template else sentence + " " + t
        sentence += "."
    text, spans = unmark(sentence)
    return text, spans, make_graph(predicate, entities, polarity, temporal)


def build():
    combinations = []
    for predicate in VERBS:
        for a in ("aa", "ab", "ac", "ad", "ae", "ag", None):
            if a is None and predicate in ("bd", "be", "bf"):
                continue
            for p in (("af",) if predicate == "bd" else (None,) if predicate in ("be", "bf") else ("aa", "ab", "ac", "ad", "ae", "ag")):
                if a == p:
                    continue
                for place in (None, "ah", "ai"):
                    combinations.append((predicate, a, p, "ac" if predicate == "bd" else None, place))
    random.Random(203).shuffle(combinations)
    rows = []
    for i, combo in enumerate(combinations):
        split = "train" if i % 10 < 6 else "dev" if i % 10 < 8 else "test"
        rng = random.Random(991 + i)
        for variant in range(16):
            polarity = ("affirmed", "negated")[variant % 2]
            temporal = ("unspecified", "past", "present", "future", "today", "tomorrow", "yesterday")[variant % 7]
            quantities = {}
            for role, concept in zip(ROLES, combo[1:]):
                if role != "location" and concept not in (None, "ag") and rng.random() < .4:
                    quantities[role] = rng.choice((1, 2, 3, 4, 7, 12, 23, 100))
            name = rng.choice(NAMES[split])
            group = f"v2c{i:04d}v{variant:02d}"
            # Both training voices occur for both polarities/time classes.
            template = TEMPLATES[split][(variant // 2) % 2]
            for lang in ("ja", "en"):
                text, spans, graph = realize(combo, quantities, name, polarity, temporal, lang, template)
                rows.append({"corpus_version": "0.2", "id": group + lang, "group": group, "combination": list(combo),
                             "pattern": lang + ":" + template, "split": split, "language": lang, "supported": True,
                             "text": text, "spans": spans, "graph": graph})
    # Remove degenerate templates (e.g. place-first without a place) that become
    # a surface frame already used by another partition. Compare the actual
    # annotated frames rather than trusting names assigned to templates.
    assigned_frames, retained = {}, []
    for split in SPLITS:
        for row in rows:
            if row["split"] != split:
                continue
            signature = frame(row)
            if signature in assigned_frames and assigned_frames[signature] != split:
                continue
            assigned_frames[signature] = split
            retained.append(row)
    rows = retained
    # Varied out-of-scope constructions. Unknown categories and lexical items are
    # distinct between partitions, with no correction table in the analyzer.
    unknown = {"train": [("狼", "wolf"), ("ロボット", "robot"), ("魚", "fish"), ("馬", "horse")],
               "dev": [("ライオン", "lion"), ("宇宙人", "alien")], "test": [("ドラゴン", "dragon"), ("ユニコーン", "unicorn")]}
    for split in SPLITS:
        base = [r for r in rows if r["split"] == split and r["supported"] and "aa" in r["combination"]]
        for i, row in enumerate(base[:240]):
            lang, text = row["language"], row["text"]
            choice = (i // 2) % 6
            noun = unknown[split][(i // 12) % len(unknown[split])][0 if lang == "ja" else 1]
            if choice == 0:
                span = next((s for s in row["spans"] if s["concept"] == "aa"), None)
                if span is None:
                    continue
                if lang == "en" and span["quantity"] not in ("unspecified", "1"):
                    noun = {"wolf": "wolves", "fish": "fish"}.get(noun, noun + "s")
                text = text[:span["start"]] + noun + text[span["end"]:]
                category = "unknown_concept"
            elif choice == 1:
                span = next((s for s in row["spans"] if s["concept"] == "aa" and s["quantity"] == "unspecified"), None)
                if span is None:
                    continue
                if lang == "ja":
                    text = text[:span["start"]] + "全ての" + text[span["start"]:]
                else:
                    prefix = text[:span["start"]]
                    require(prefix.endswith("the "), "Quantified fixture requires its article")
                    text = prefix[:-4] + "every " + text[span["start"]:]
                category = "quantification"
            elif choice == 2:
                text = text.rstrip("。.") + "とは限らない。" if lang == "ja" else "It is not necessarily true that " + text
                category = "nested_scope"
            elif choice == 3:
                text = text + ("鳥も眠る。" if lang == "ja" else " The bird also sleeps.")
                category = "multiple_events"
            elif choice == 4:
                text = ("たぶん" if lang == "ja" else "Perhaps ") + text
                category = "modality"
            else:
                text = text.rstrip("。.") + ("のですか？" if lang == "ja" else "?")
                category = "question"
            rows.append({**row, "id": "u" + row["id"], "group": "u" + row["group"], "combination": None,
                         "pattern": lang + ":unsupported:" + split, "supported": False, "category": category,
                         "text": text, "spans": [], "graph": None})
    # Stable deduplication within a partition; cross-partition duplication is an error.
    unique = {}
    for row in rows:
        key = (row["language"], row["text"])
        require(key not in unique or unique[key]["split"] == row["split"], "Duplicate text across splits")
        unique.setdefault(key, row)
    return list(unique.values())


def frame(row):
    parts, end = [], 0
    for span in sorted(row["spans"], key=lambda s: s["start"]):
        parts += [row["text"][end:span["start"]], "<" + span["kind"] + ":" + span["role"] + ">"]
        end = span["end"]
    return (row["language"], "".join(parts) + row["text"][end:])


def validate(rows):
    ids, groups, combos, patterns, texts, frames = set(), {}, {}, {}, {}, {}
    for row in rows:
        require(row.get("corpus_version") == "0.2", "Mixed corpus editions")
        require(row["id"] not in ids, "Duplicate example ID")
        ids.add(row["id"])
        require(row["split"] in SPLITS and row["language"] in ("ja", "en"), "Invalid partition/language")
        for table, key in ((groups, row["group"]), (patterns, row["pattern"]), (texts, (row["language"], row["text"]))):
            require(key not in table or table[key] == row["split"], "Cross-partition leakage")
            table[key] = row["split"]
        if row["supported"]:
            signature = frame(row)
            require(signature not in frames or frames[signature] == row["split"], "Realized syntactic frame leakage")
            frames[signature] = row["split"]
            key = tuple(row["combination"])
            require(key not in combos or combos[key] == row["split"], "Concept combination leakage")
            combos[key] = row["split"]
            normalize(row["graph"])
            for span in row["spans"]:
                require(0 <= span["start"] < span["end"] <= len(row["text"]), "Invalid span")
    return {s: {lang: sum(r["split"] == s and r["language"] == lang for r in rows) for lang in ("ja", "en")} for s in SPLITS}


def write(path):
    rows = build()
    counts = validate(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding="utf-8", newline="\n")
    manifest = {"corpus_version": "0.2", "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "counts": counts,
                "purpose": "new fixed fixture evaluation; historical 0.1 is regression only", "templates": TEMPLATES,
                "names": NAMES, "seed": 203}
    return manifest
