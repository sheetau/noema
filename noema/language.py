"""Noema 0.2: human-facing clauses, discourse references and explicit scope.

This edition deliberately has its own document schema. The 0.1 graph remains
supported; conversion to it must explicitly reject meanings it cannot express.
"""
import copy
import json
import re
from datetime import date
from importlib.resources import files
from .grammar import number_word, read_number
from .semantics import CONCEPTS, ROLES, TIMES, SemanticError, keys, require, time_value

EDITION = json.loads(files("noema").joinpath("resources/language-v02.json").read_text(encoding="utf-8"))
EXTENSION = json.loads(files("noema").joinpath("resources/language-v03.json").read_text(encoding="utf-8"))
ROOTS = EDITION["roots"]
CONCEPT_BY_WORD = {word: concept for concept, word in ROOTS.items()}
ROLE_WORDS = dict(zip("ijkl", ROLES))
TIME_WORDS = dict(zip("efgrst", ("past", "present", "future", "yesterday", "today", "tomorrow")))
CONNECTIVES = {"w": "and", "x": "or", "y": "if"}
TOKEN = re.compile(r'\s*("(?:[^"\\\x00-\x1f]|\\["\\/bfnrt]|\\u[0-9a-fA-F]{4})*"|[a-z2-7]+|[\[\].?])')
MAX_DEPTH = 64


def policy(version):
    require(version in ("0.2", "0.3"), "Unsupported written language version")
    if version == "0.2":
        return ROOTS, CONCEPTS, ROLE_WORDS, ROLES
    roots = {**ROOTS, **EXTENSION["roots"]}
    concepts = {**{k: {**v, "ja": EXTENSION["inherited_ja"][k]} for k, v in CONCEPTS.items()}, **EXTENSION["concepts"]}
    markers = {**ROLE_WORDS, **EXTENSION["role_markers"]}
    return roots, concepts, markers, tuple(markers.values())


def tokenize(text):
    require(isinstance(text, str), "Noema input must be text")
    result, position = [], 0
    while position < len(text):
        if text[position:].isspace():
            break
        match = TOKEN.match(text, position)
        require(match is not None, f"Invalid 0.2 token at character {position}")
        result.append((match.group(1), match.start(1), match.end(1)))
        position = match.end()
    return result


def _time(t):
    keys(t, ("kind", "value"))
    if t["kind"] == "date":
        require(isinstance(t["value"], str), "Date must be a string")
        try:
            require(date.fromisoformat(t["value"]).isoformat() == t["value"], "Use YYYY-MM-DD dates")
        except ValueError as exc:
            raise SemanticError("Invalid date") from exc
    else:
        require(t in [time_value(v) for v in TIMES], "Invalid time")


def normalize_document(document):
    """Keep speech acts, connective order, explicit negation and identity intact."""
    keys(document, ("schema_version", "lexicon_version", "entities", "utterances"))
    version = document["schema_version"]
    require(version == document["lexicon_version"], "Document and lexicon editions must match")
    ROOTS, CONCEPTS, ROLE_WORDS, ROLES = policy(version)
    require(isinstance(document["entities"], list) and isinstance(document["utterances"], list), "Expected entity and utterance arrays")
    require(bool(document["utterances"]), "A document requires at least one utterance")
    entities = {}
    for entity in document["entities"]:
        keys(entity, ("id", "kind", "concept", "quantity", "name"))
        ident, concept = entity["id"], entity["concept"]
        require(isinstance(ident, str) and re.fullmatch(r"[a-z2-7]+", ident), "Invalid entity reference")
        require(ident not in entities, "Duplicate entity reference")
        require(isinstance(concept, str) and concept in ROOTS, "Unknown concept")
        require(entity["kind"] in ("entity", "place") and entity["kind"] == CONCEPTS[concept]["kind"], "Invalid entity type")
        q, name = entity["quantity"], entity["name"]
        require(q is None or type(q) is int and q >= 0, "Quantity must be a nonnegative integer or null")
        require(name is None or isinstance(name, str) and bool(name), "Name must be a nonempty string or null")
        require(concept != "ag" or name is not None, "A named person requires a name")
        if name is not None:
            try:
                name.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise SemanticError("Name contains invalid Unicode") from exc
        entities[ident] = copy.deepcopy(entity)
    mapping, ordered = {}, []

    def visit(expression, speech_act, depth=0):
        require(depth <= MAX_DEPTH, "Expression nesting exceeds 64 levels")
        require(isinstance(expression, dict), "Expression must be an object")
        kind = expression.get("kind")
        if kind == "clause":
            keys(expression, ("kind", "predicate", "polarity", "time", "roles"))
            predicate = expression["predicate"]
            require(isinstance(predicate, str) and predicate in ROOTS and CONCEPTS[predicate]["kind"] in ("event", "state"), "Expected an event or state concept")
            require(expression["polarity"] in ("affirmed", "unspecified"), "Negative scope uses a not expression")
            _time(expression["time"])
            require(isinstance(expression["roles"], dict) and set(expression["roles"]) <= set(ROLES), "Invalid roles")
            output = copy.deepcopy(expression)
            output["roles"] = {}
            for role in ROLES:
                target = expression["roles"].get(role)
                if target is None:
                    output["roles"][role] = None
                    continue
                require(role in CONCEPTS[predicate]["roles"], "Role is incompatible with predicate")
                if isinstance(target, dict):
                    keys(target, ("query",))
                    require(target["query"] is True and speech_act == "question", "Queried roles require a question")
                    output["roles"][role] = {"query": True}
                else:
                    require(isinstance(target, str) and target in entities, "Dangling entity reference")
                    allowed = CONCEPTS[predicate].get("role_types", {}).get(role, ["place"] if role in ("location", "source", "destination") else ["entity"])
                    require(entities[target]["kind"] in allowed, f"Entity type is incompatible with {role}")
                    if target not in mapping:
                        mapping[target] = "n" + number_word(len(mapping))
                        ordered.append({**entities[target], "id": mapping[target]})
                    output["roles"][role] = mapping[target]
            return output
        if kind == "not":
            keys(expression, ("kind", "body"))
            return {"kind": "not", "body": visit(expression["body"], speech_act, depth + 1)}
        require(kind in ("and", "or", "if"), "Unknown expression kind")
        keys(expression, ("kind", "left", "right"))
        return {"kind": kind, "left": visit(expression["left"], speech_act, depth + 1), "right": visit(expression["right"], speech_act, depth + 1)}

    utterances = []
    for utterance in document["utterances"]:
        keys(utterance, ("speech_act", "content"))
        act = utterance["speech_act"]
        require(act in ("assertion", "question", "request"), "Unknown speech act")
        utterances.append({"speech_act": act, "content": visit(utterance["content"], act)})
    require(set(mapping) == set(entities), "Unreferenced entity")
    return {"schema_version": version, "lexicon_version": version, "entities": ordered, "utterances": utterances}


def parse_document(text):
    stream, cursor, entities, bindings = tokenize(text), 0, [], {}

    def peek():
        return stream[cursor][0] if cursor < len(stream) else None

    def take(expected=None):
        nonlocal cursor
        require(cursor < len(stream), "Unexpected end of Noema 0.2")
        token, start, _ = stream[cursor]
        require(expected is None or expected == token, f"Expected {expected}, got {token} at character {start}")
        cursor += 1
        return token

    def reference():
        token = take()
        require(re.fullmatch(r"[a-z2-7]+", token), "Expected a reference word")
        return token

    def literal():
        value = take()
        require(value.startswith('"'), "Expected a quoted literal")
        return json.loads(value)

    def term():
        word = take()
        if word == "?":
            return None
        if word == "c":
            return {"query": True}
        if word == "p":
            name = reference()
            require(name in bindings, f"Reference {name} has not been introduced")
            return bindings[name]
        concept = CONCEPT_BY_WORD.get(word)
        require(concept is not None and CONCEPTS[concept]["kind"] in ("entity", "place"), f"Expected an entity word, got {word}")
        node = {"id": "n" + number_word(len(entities)), "kind": CONCEPTS[concept]["kind"], "concept": concept, "quantity": None, "name": None}
        modifiers = set()
        while peek() in ("m", "n", "o"):
            marker = take()
            require(marker not in modifiers, "Duplicate entity modifier")
            modifiers.add(marker)
            if marker == "m":
                node["quantity"] = read_number(take())
            elif marker == "n":
                node["name"] = literal()
            else:
                name = reference()
                require(name not in bindings, f"Reference {name} is already defined")
                bindings[name] = node["id"]
        entities.append(node)
        return node["id"]

    def expression(depth=0):
        require(depth <= MAX_DEPTH, "Expression nesting exceeds 64 levels")
        if peek() == "[":
            take("[")
            content = expression(depth + 1)
            take("]")
            return content
        if peek() == "u":
            take()
            return {"kind": "not", "body": expression(depth + 1)}
        if peek() in CONNECTIVES:
            kind = CONNECTIVES[take()]
            take("[")
            left = expression(depth + 1)
            take("]")
            take("[")
            right = expression(depth + 1)
            take("]")
            return {"kind": kind, "left": left, "right": right}
        polarity, time, modifiers = "affirmed", time_value("unspecified"), set()
        while peek() in (*TIME_WORDS, "q", "v"):
            marker = take()
            key = "polarity" if marker == "v" else "time"
            require(key not in modifiers, f"Duplicate {key} modifier")
            modifiers.add(key)
            if marker == "v":
                polarity = "unspecified"
            elif marker == "q":
                time = {"kind": "date", "value": literal()}
            else:
                time = time_value(TIME_WORDS[marker])
        word = take()
        predicate = CONCEPT_BY_WORD.get(word)
        require(predicate is not None and CONCEPTS[predicate]["kind"] in ("event", "state"), f"Expected a predicate word, got {word}")
        roles = {}
        while peek() in ROLE_WORDS:
            role = ROLE_WORDS[take()]
            require(role not in roles, f"Duplicate {role} role")
            roles[role] = term()
        return {"kind": "clause", "predicate": predicate, "polarity": polarity, "time": time, "roles": roles}

    take("noema")
    edition = take()
    require(edition in ("b", "c"), "Unsupported written language edition")
    take(edition)
    version = {"b": "0.2", "c": "0.3"}[edition]
    ROOTS, CONCEPTS, ROLE_WORDS, ROLES = policy(version)
    CONCEPT_BY_WORD = {word: concept for concept, word in ROOTS.items()}
    utterances = []
    while peek() is not None:
        act = {"b": "question", "d": "request"}.get(peek(), "assertion")
        if act != "assertion":
            take()
        utterances.append({"speech_act": act, "content": expression()})
        take(".")
    return normalize_document({"schema_version": version, "lexicon_version": version, "entities": entities, "utterances": utterances})


def format_document(document):
    document = normalize_document(document)
    ROOTS, CONCEPTS, ROLE_WORDS, ROLES = policy(document["schema_version"])
    entities = {e["id"]: e for e in document["entities"]}
    seen, counts = set(), {}

    def count(expr):
        if expr["kind"] == "clause":
            for term in expr["roles"].values():
                if isinstance(term, str):
                    counts[term] = counts.get(term, 0) + 1
        elif expr["kind"] == "not":
            count(expr["body"])
        else:
            count(expr["left"])
            count(expr["right"])

    for utterance in document["utterances"]:
        count(utterance["content"])

    def term(ident):
        if ident is None:
            return "?"
        if isinstance(ident, dict):
            return "c"
        if ident in seen:
            return "p " + ident
        seen.add(ident)
        entity = entities[ident]
        words = [ROOTS[entity["concept"]]]
        if entity["quantity"] is not None:
            words += ["m", number_word(entity["quantity"])]
        if entity["name"] is not None:
            words += ["n", json.dumps(entity["name"], ensure_ascii=False)]
        if counts[ident] > 1:
            words += ["o", ident]
        return " ".join(words)

    def expression(expr):
        kind = expr["kind"]
        if kind == "not":
            return "u [ " + expression(expr["body"]) + " ]"
        if kind in CONNECTIVES.values():
            marker = {v: k for k, v in CONNECTIVES.items()}[kind]
            return marker + " [ " + expression(expr["left"]) + " ] [ " + expression(expr["right"]) + " ]"
        words = []
        if expr["polarity"] == "unspecified":
            words.append("v")
        t = expr["time"]
        if t["kind"] == "date":
            words += ["q", json.dumps(t["value"])]
        elif t["kind"] != "unspecified":
            words.append({v: k for k, v in TIME_WORDS.items()}[t["value"]])
        words.append(ROOTS[expr["predicate"]])
        for marker, role in ROLE_WORDS.items():
            value = expr["roles"][role]
            if value is not None:
                words += [marker, term(value)]
        return " ".join(words)

    marker = {"0.2": "b", "0.3": "c"}[document["schema_version"]]
    lines = [f"noema {marker} {marker}"]
    for utterance in document["utterances"]:
        mood = {"assertion": "", "question": "b ", "request": "d "}[utterance["speech_act"]]
        lines.append(mood + expression(utterance["content"]) + ".")
    return "\n".join(lines)


def from_graph(graph):
    """Lossless lifting of a 0.1 assertion into the 0.2 document schema."""
    from .semantics import normalize
    require(isinstance(graph, dict) and graph.get("schema_version") == "0.1", "Expected a 0.1 graph")
    graph = normalize(graph)
    event = graph["nodes"][0]
    content = {"kind": "clause", "predicate": event["concept"], "polarity": "affirmed" if event["polarity"] == "negated" else event["polarity"],
               "time": event["time"], "roles": {r["role"]: r["target"] for r in graph["relations"]}}
    if event["polarity"] == "negated":
        content = {"kind": "not", "body": content}
    return normalize_document({"schema_version": "0.2", "lexicon_version": "0.2", "entities": graph["nodes"][1:],
                               "utterances": [{"speech_act": "assertion", "content": content}]})


def to_graph(document):
    """Only the exactly representable assertion subset can be lowered to 0.1."""
    from .semantics import normalize
    doc = normalize_document(document)
    require(len(doc["utterances"]) == 1 and doc["utterances"][0]["speech_act"] == "assertion", "0.1 can represent only a single assertion")
    content = doc["utterances"][0]["content"]
    negated = content["kind"] == "not"
    if negated:
        content = content["body"]
    require(content["kind"] == "clause", "0.1 cannot represent connective or nested negation scope")
    require(not negated or content["polarity"] == "affirmed", "0.1 cannot negate unspecified polarity")
    require(content["predicate"] in CONCEPTS and all(e["concept"] in CONCEPTS for e in doc["entities"]), "Concepts are not in the 0.1 lexicon")
    require(all(target is None for role, target in content["roles"].items() if role not in ROLES), "0.1 cannot represent extended roles")
    event = {"id": "e", "kind": CONCEPTS[content["predicate"]]["kind"], "concept": content["predicate"],
             "polarity": "negated" if negated else content["polarity"], "time": content["time"]}
    return normalize({"schema_version": "0.1", "lexicon_version": "0.1", "nodes": [event] + doc["entities"],
                      "relations": [{"source": "e", "role": role, "target": target} for role, target in content["roles"].items() if role in ROLES]})


def convert(document, version):
    """Explicit edition conversion; reject any meaning absent from the target."""
    from .semantics import normalize
    source = normalize(document)
    if source["schema_version"] == version:
        return source
    if source["schema_version"] == "0.1":
        source = from_graph(source)
    if version == "0.1":
        return to_graph(source)
    _, _, _, roles = policy(version)

    def visit(expr):
        if expr["kind"] == "clause":
            require(all(value is None for role, value in expr["roles"].items() if role not in roles), "Target edition cannot represent extended roles")
            expr["roles"] = {r: v for r, v in expr["roles"].items() if r in roles}
        elif expr["kind"] == "not":
            visit(expr["body"])
        else:
            visit(expr["left"])
            visit(expr["right"])

    for utterance in source["utterances"]:
        visit(utterance["content"])
    source["schema_version"] = source["lexicon_version"] = version
    return normalize_document(source)
