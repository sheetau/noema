"""Deterministic surface realization of the existing single-clause subset.

This is a limited meaning-to-text renderer, not recovery of an original sentence.
It is independent of training fixtures and never repairs analyzer predictions.
"""
import json
from .language import convert
from .semantics import require

NOUNS = {
    "aa": ("犬", "匹", "dog", "dogs"), "ab": ("猫", "匹", "cat", "cats"),
    "ac": ("子供", "人", "child", "children"), "ad": ("先生", "人", "teacher", "teachers"),
    "ae": ("鳥", "羽", "bird", "birds"), "af": ("本", "冊", "book", "books"),
    "ag": ("人", "人", "person", "people"), "ah": ("公園", "か所", "park", "parks"),
    "ai": ("家", "軒", "home", "homes"),
}
VERBS = {
    "ba": ("追う", "追わない", "追った", "追わなかった", "chase", "chases", "chased", "chased"),
    "bb": ("見る", "見ない", "見た", "見なかった", "see", "sees", "saw", "seen"),
    "bc": ("助ける", "助けない", "助けた", "助けなかった", "help", "helps", "helped", "helped"),
    "bd": ("渡す", "渡さない", "渡した", "渡さなかった", "give", "gives", "gave", "given"),
    "be": ("眠る", "眠らない", "眠った", "眠らなかった", "sleep", "sleeps", "slept", ""),
    "bf": ("空腹だ", "空腹でない", "空腹だった", "空腹でなかった", "", "", "", ""),
}


def realize(document, language):
    require(language in ("ja", "en"), "Choose Japanese or English")
    graph = convert(document, "0.1")  # Reject unsupported scope/roles/properties without dropping them.
    nodes = {n["id"]: n for n in graph["nodes"]}
    event = nodes["e"]
    require(event["polarity"] != "unspecified", "Unspecified polarity has no supported natural-language rendering")
    refs = [r["target"] for r in graph["relations"] if r["target"] is not None]
    require(len(refs) == len(set(refs)), "Shared referents require an explicit reference renderer")
    entities = {r["role"]: nodes.get(r["target"]) for r in graph["relations"]}

    def noun(entity):
        if entity is None:
            return ""
        word, counter, singular, plural = NOUNS[entity["concept"]]
        quantity, name = entity["quantity"], entity["name"]
        if language == "ja":
            if entity["concept"] == "ag" and quantity is None:
                return "「" + name + "」"
            phrase = (str(quantity) + counter + "の" if quantity is not None else "") + word
            return phrase + ("（名前：" + name + "）" if name else "")
        if entity["concept"] == "ag" and quantity is None:
            return json.dumps(name, ensure_ascii=False)
        phrase = ("the " if quantity is None else str(quantity) + " ") + (plural if quantity not in (None, 1) else singular)
        return phrase + (" named " + json.dumps(name, ensure_ascii=False) if name else "")

    agent, patient, recipient, location = (noun(entities[r]) for r in ("agent", "patient", "recipient", "location"))
    predicate = event["concept"]
    require(predicate not in ("ba", "bb", "bc", "bd") or patient, "This rendering requires an explicit patient")
    negative = event["polarity"] == "negated"
    temporal = event["time"]["value"] or "unspecified"
    past, future = temporal in ("past", "yesterday"), temporal in ("future", "tomorrow")
    verb = VERBS[predicate]
    if language == "ja":
        time = {"present": "今", "future": "今後", "yesterday": "昨日", "today": "今日", "tomorrow": "明日"}.get(temporal, "")
        if event["time"]["kind"] == "date":
            time = temporal
        return ((time + "、" if time else "") + (agent + "が" if agent else "")
                + (location + "で" if location else "") + (recipient + "に" if recipient else "")
                + (patient + "を" if patient else "") + verb[2 * past + negative] + "。")
    passive = not agent and bool(patient)
    require(agent or passive, "English rendering cannot supply an omitted subject")
    subject = patient if passive else agent
    subject_entity = entities["patient" if passive else "agent"]
    plural = subject_entity["quantity"] not in (None, 1)
    if passive or predicate == "bf":
        auxiliary = "will be" if future else ("were" if plural else "was") if past else ("are" if plural else "is")
        if negative:
            auxiliary = "will not be" if future else auxiliary + " not"
        action = auxiliary + " " + (verb[7] if passive else "hungry")
    elif negative:
        action = ("will not" if future else "did not" if past else "do not" if plural else "does not") + " " + verb[4]
    else:
        action = "will " + verb[4] if future else verb[6] if past else verb[4] if plural else verb[5]
    text = subject + " " + action + (" " + patient if patient and not passive else "")
    text += (" to " + recipient if recipient else "") + (" in " + location if location else "")
    time = "now" if temporal == "present" else temporal if temporal in ("today", "tomorrow", "yesterday") else ""
    if event["time"]["kind"] == "date":
        time = "on " + temporal
    if text.startswith("the "):
        text = "The " + text[4:]
    return text + (" " + time if time else "") + "."
