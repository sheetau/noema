"""Noema a/a: word-based, explicit references and scoped proposition attributes."""
import json
import re
from .semantics import ALPHABET, CONCEPTS, SemanticError, normalize, require, time_value

TOKEN = re.compile(r'\s*("(?:[^"\\\x00-\x1f]|\\["\\/bfnrt]|\\u[0-9a-fA-F]{4})*"|[a-z2-7]+|[{};?])')
POL = {"pos": "affirmed", "neg": "negated", "unspec": "unspecified"}


def number_word(value):
    require(type(value) is int and value >= 0, "Quantity must be a nonnegative integer")
    if value == 0:
        return "a"
    word = ""
    while value:
        value, remainder = divmod(value, 32)
        word = ALPHABET[remainder] + word
    return word


def read_number(word):
    require(isinstance(word, str), "Quantity word must be text")
    require(bool(re.fullmatch("[a-z2-7]+", word)), "Invalid quantity")
    require(len(word) == 1 or not word.startswith("a"), "Quantity has leading zero")
    value = 0
    for c in word:
        value = value * 32 + ALPHABET.index(c)
    return value


def tokens(text):
    require(isinstance(text, str), "Noema input must be text")
    result, position = [], 0
    while position < len(text):
        if text[position:].isspace():
            break
        match = TOKEN.match(text, position)
        require(match is not None, f"Invalid token at character {position}")
        result.append(match.group(1))
        position = match.end()
    return result


def notation_of(text):
    """Identify an explicit notation header, including either native alphabet."""
    if not isinstance(text, str):
        return "full"
    from .script import transcribe
    return "compact" if re.match(r"\s*[a-z2-7]:", transcribe(text, reverse=True)) else "full"


def parse(text):
    if isinstance(text, str) and any(0xE000 <= ord(c) <= 0xE01F or 0xE100 <= ord(c) <= 0xE11F for c in text):
        from .script import transcribe
        text = transcribe(text, reverse=True)
    if isinstance(text, str) and re.match(r'\s*(?:[hi]:|noema\s+([hi])\s+\1(?:\s|$))', text):
        from .discourse import parse_document
        return parse_document(text)
    if notation_of(text) == "compact":
        from .language import parse_document
        return parse_document(text, compact=True)
    if isinstance(text, str) and re.match(r"\s*noema\s+([bcdefg])\s+\1(?:\s|$)", text):
        from .language import parse_document
        return parse_document(text)
    stream = tokens(text)
    pos = 0

    def take(expected=None):
        nonlocal pos
        require(pos < len(stream), "Unexpected end of Noema")
        value = stream[pos]
        pos += 1
        require(expected is None or value == expected, f"Expected {expected}, got {value}")
        return value

    take("noema")
    take("a")
    take("a")
    take("{")
    graph = {"schema_version": "0.1", "lexicon_version": "0.1", "nodes": [], "relations": []}
    while pos < len(stream) and stream[pos] != "}":
        clause = take()
        if clause == "ev":
            ident, concept, polarity, time = take(), take(), take(), take()
            require(concept in CONCEPTS, "Unknown concept")
            require(polarity in POL, "Invalid polarity word")
            if time == "date":
                literal = take()
                require(literal.startswith('"'), "Date requires a quoted literal")
                t = {"kind": "date", "value": json.loads(literal)}
            else:
                t = time_value("unspecified" if time == "unspec" else time)
            graph["nodes"].append({"id": ident, "kind": CONCEPTS[concept]["kind"], "concept": concept, "polarity": POL[polarity], "time": t})
        elif clause == "en":
            ident, concept, quantity, name = take(), take(), take(), take()
            require(concept in CONCEPTS, "Unknown concept")
            require(name == "?" or name.startswith('"'), "Name requires a quoted literal")
            graph["nodes"].append({"id": ident, "kind": CONCEPTS[concept]["kind"], "concept": concept, "quantity": None if quantity == "?" else read_number(quantity), "name": None if name == "?" else json.loads(name)})
        else:
            source, target = take(), take()
            graph["relations"].append({"source": source, "role": clause, "target": None if target == "?" else target})
        take(";")
    take("}")
    require(pos == len(stream), "Trailing input")
    return normalize(graph)


def format_graph(graph, notation="full"):
    require(notation in ("full", "compact"), "Unknown written notation")
    if isinstance(graph, dict) and graph.get("schema_version") in ("0.8", "0.9"):
        from .discourse import format_document
        return format_document(graph, compact=notation == "compact")
    if isinstance(graph, dict) and graph.get("schema_version") in ("0.2", "0.3", "0.4", "0.5", "0.6", "0.7"):
        from .language import format_document
        return format_document(graph, compact=notation == "compact")
    require(notation == "full", "Compact notation requires written edition 0.2 or later; convert explicitly")
    graph = normalize(graph)
    lines = ["noema a a {"]
    for node in graph["nodes"]:
        if node["kind"] in ("event", "state"):
            t = node["time"]
            time = "unspec" if t["kind"] == "unspecified" else "date " + json.dumps(t["value"]) if t["kind"] == "date" else t["value"]
            pol = {v: k for k, v in POL.items()}[node["polarity"]]
            lines.append(f"  ev {node['id']} {node['concept']} {pol} {time};")
        else:
            quantity = "?" if node["quantity"] is None else number_word(node["quantity"])
            name = "?" if node["name"] is None else json.dumps(node["name"], ensure_ascii=False)
            lines.append(f"  en {node['id']} {node['concept']} {quantity} {name};")
    for rel in graph["relations"]:
        lines.append(f"  {rel['role']} {rel['source']} {rel['target'] or '?'};")
    return "\n".join(lines + ["}"])
