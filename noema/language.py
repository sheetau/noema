"""Noema 0.2–0.7: written clauses, discourse references and explicit scope.

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
from .derivation import predicate_spec, parse_predicate, predicate_word

EDITION = json.loads(files("noema").joinpath("resources/language-v02.json").read_text(encoding="utf-8"))
EXTENSION = json.loads(files("noema").joinpath("resources/language-v03.json").read_text(encoding="utf-8"))
COMPOUNDS = json.loads(files("noema").joinpath("resources/language-v04.json").read_text(encoding="utf-8"))
ROOTS = EDITION["roots"]
CONCEPT_BY_WORD = {word: concept for concept, word in ROOTS.items()}
ROLE_WORDS = dict(zip("ijkl", ROLES))
TIME_WORDS = dict(zip("efgrst", ("past", "present", "future", "yesterday", "today", "tomorrow")))
CONNECTIVES = {"w": "and", "x": "or", "y": "if"}
TOKEN = re.compile(r'\s*("(?:[^"\\\x00-\x1f]|\\["\\/bfnrt]|\\u[0-9a-fA-F]{4})*"|[a-z2-7]+(?:-[a-z2-7]+)*|[\[\].?])')
MAX_DEPTH = 64


def policy(version):
    require(version in ("0.2", "0.3", "0.4", "0.5", "0.6", "0.7"), "Unsupported written language version")
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
        require(match is not None, f"Invalid written Noema token at character {position}")
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
        if isinstance(entity, dict) and entity.get("kind") == "group":
            require(version in ("0.6", "0.7"), "Groups require edition 0.6")
            keys(entity, ("id", "kind", "members"))
            ident, members = entity["id"], entity["members"]
            require(isinstance(ident, str) and re.fullmatch(r"[a-z2-7]+", ident), "Invalid entity reference")
            require(ident not in entities, "Duplicate entity reference")
            require(isinstance(members, list) and len(members) >= 2
                    and all(isinstance(m, str) for m in members), "Group requires at least two entity references")
            require(len(set(members)) == len(members), "Duplicate group member reference")
            entities[ident] = copy.deepcopy(entity)
            continue
        keys(entity, ("id", "kind", "concept", "quantity", "name", "qualifiers") if version in ("0.4", "0.5", "0.6", "0.7") else ("id", "kind", "concept", "quantity", "name"))
        ident, concept = entity["id"], entity["concept"]
        require(isinstance(ident, str) and re.fullmatch(r"[a-z2-7]+", ident), "Invalid entity reference")
        require(ident not in entities, "Duplicate entity reference")
        require(isinstance(concept, str) and concept in ROOTS, "Unknown concept")
        require(entity["kind"] in ("entity", "place") and entity["kind"] == CONCEPTS[concept]["kind"], "Invalid entity type")
        if version in ("0.4", "0.5", "0.6", "0.7"):
            qualifiers = entity["qualifiers"]
            require(isinstance(qualifiers, list) and all(isinstance(q, str) and q in COMPOUNDS["attributive_states"] for q in qualifiers), "Compound requires supported attributive states")
            require(len(qualifiers) == len(set(qualifiers)), "Duplicate compound property")
            for qualifier in qualifiers:
                require(qualifier in CONCEPTS and CONCEPTS[qualifier]["kind"] == "state"
                        and "agent" in CONCEPTS[qualifier]["roles"] and set(CONCEPTS[qualifier]["roles"]) <= {"agent", "location"},
                        "Compound property must be a unary state")
                allowed = CONCEPTS[qualifier].get("role_types", {}).get("agent", ["entity"])
                require(entity["kind"] in allowed, "Compound property is incompatible with the base type")
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
        if version in ("0.4", "0.5", "0.6", "0.7"):
            entities[ident]["qualifiers"] = sorted(entity["qualifiers"])
    mapping, ordered = {}, []

    type_cache, heights = {}, {}

    def entity_types(ident, active=(), depth=0):
        require(depth <= MAX_DEPTH, "Group nesting exceeds 64 levels")
        require(ident in entities, "Dangling group member reference")
        require(ident not in active, "Cyclic group membership")
        if ident in type_cache:
            require(depth + heights[ident] <= MAX_DEPTH, "Group nesting exceeds 64 levels")
            return type_cache[ident]
        entity = entities[ident]
        if entity["kind"] != "group":
            type_cache[ident], heights[ident] = {entity["kind"]}, 0
            return {entity["kind"]}
        kinds = set()
        for member in entity["members"]:
            kinds.update(entity_types(member, (*active, ident), depth + 1))
        type_cache[ident], heights[ident] = kinds, 1 + max(heights[m] for m in entity["members"])
        return kinds

    types = {ident: entity_types(ident) for ident in entities}

    def bind(ident):
        if ident not in mapping:
            mapping[ident] = "n" + number_word(len(mapping))
            node = {**entities[ident], "id": mapping[ident]}
            ordered.append(node)
            if node["kind"] == "group":
                node["members"] = [bind(member) for member in node["members"]]
        return mapping[ident]

    variables, variable_count = {}, 0

    def targets(target):
        if isinstance(target, dict):
            keys(target, ("bound",))
            require(version == "0.7", "Bound members require edition 0.7")
            name = target["bound"]
            require(isinstance(name, str) and name in variables, "Unbound member reference")
            return variables[name][1]
        require(isinstance(target, str) and target in entities, "Dangling entity reference")
        return (target,)

    def normalize_target(target):
        return {"bound": variables[target["bound"]][0]} if isinstance(target, dict) else bind(target)

    def collective_clause(expression):
        current, roles = expression, set()
        while isinstance(current, dict) and current.get("kind") == "collective":
            require(len(roles) <= len(ROLES), "Too many collective roles")
            keys(current, ("kind", "role", "body"))
            role = current["role"]
            require(isinstance(role, str) and role in ROLES, "Invalid collective role")
            require(role not in roles, "Duplicate collective role")
            roles.add(role)
            current = current["body"]
        require(isinstance(current, dict) and current.get("kind") == "clause", "Collective application requires a clause")
        return current

    def visit(expression, speech_act, depth=0):
        nonlocal variable_count
        require(depth <= MAX_DEPTH, "Expression nesting exceeds 64 levels")
        require(isinstance(expression, dict), "Expression must be an object")
        kind = expression.get("kind")
        if kind == "clause":
            keys(expression, ("kind", "predicate", "polarity", "time", "roles"))
            predicate = expression["predicate"]
            spec = predicate_spec(predicate, version, CONCEPTS)
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
                require(role in spec["roles"], "Role is incompatible with predicate")
                if isinstance(target, dict) and "query" in target:
                    keys(target, ("query",))
                    require(target["query"] is True and speech_act == "question", "Queried roles require a question")
                    output["roles"][role] = {"query": True}
                else:
                    candidates = targets(target)
                    allowed = spec.get("role_types", {}).get(role, ["place"] if role in ("location", "source", "destination") else ["entity"])
                    require(all(types[candidate] <= set(allowed) for candidate in candidates), f"Entity type is incompatible with {role}")
                    output["roles"][role] = normalize_target(target)
            return output
        if kind == "each":
            require(version == "0.7", "Distribution requires edition 0.7")
            keys(expression, ("kind", "group", "variable", "body"))
            domains = targets(expression["group"])
            require(all(entities[t]["kind"] == "group" for t in domains), "Distribution requires explicit groups")
            variable = expression["variable"]
            require(isinstance(variable, str) and re.fullmatch(r"[a-z2-7]+", variable), "Invalid bound member name")
            require(variable not in variables, "Bound member shadowing is not allowed")
            group = normalize_target(expression["group"])
            canonical = "v" + number_word(variable_count)
            variable_count += 1
            members = tuple(dict.fromkeys(m for domain in domains for m in entities[domain]["members"]))
            variables[variable] = (canonical, members)
            try:
                body = visit(expression["body"], speech_act, depth + 1)
            finally:
                del variables[variable]
            return {"kind": "each", "group": group, "variable": canonical, "body": body}
        if kind == "collective":
            require(version == "0.7", "Collective application requires edition 0.7")
            clause = collective_clause(expression)
            require(isinstance(clause.get("roles"), dict), "Invalid roles")
            candidates = targets(clause["roles"].get(expression["role"]))
            require(all(entities[t]["kind"] == "group" for t in candidates), "Collective role requires explicit groups")
            return {"kind": "collective", "role": expression["role"],
                    "body": visit(expression["body"], speech_act, depth + 1)}
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


def parse_document(text, compact=False):
    offset = 0
    if compact:
        require(isinstance(text, str), "Noema input must be text")
        header = re.match(r"\s*([a-z2-7]):", text)
        require(header is not None, "Expected compact edition header")
        offset = header.end()
    stream = [(token, a + offset, b + offset) for token, a, b in tokenize(text[offset:])]
    cursor, entities, bindings, variables = 0, [], {}, set()

    def peek():
        return stream[cursor][0] if cursor < len(stream) else None

    def take(expected=None):
        nonlocal cursor
        require(cursor < len(stream), "Unexpected end of written Noema")
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

    def term(depth=0):
        require(depth <= MAX_DEPTH, "Group nesting exceeds 64 levels")
        word = take()
        if word == "?":
            return None
        if word == "c":
            return {"query": True}
        if word == "p":
            name = reference()
            if name in variables:
                return {"bound": name}
            require(name in bindings, f"Reference {name} has not been introduced")
            return bindings[name]
        if word == "w":
            require(version in ("0.6", "0.7"), "Groups require edition 0.6")
            members = []
            while peek() == "[":
                take("[")
                member = term(depth + 1)
                require(isinstance(member, str), "Group members must be specified entities")
                members.append(member)
                take("]")
            require(len(members) >= 2, "Group requires at least two members")
            node = {"id": "n" + number_word(len(entities)), "kind": "group", "members": members}
            entities.append(node)
            if peek() == "o":
                take()
                name = reference()
                require(name not in bindings and name not in variables, f"Reference {name} is already defined")
                bindings[name] = node["id"]
            return node["id"]
        parts = word.split("-")
        require(version in ("0.4", "0.5", "0.6", "0.7") or len(parts) == 1, "Compound words require edition 0.4 or later")
        concept = CONCEPT_BY_WORD.get(parts[0])
        require(concept is not None and CONCEPTS[concept]["kind"] in ("entity", "place"), f"Expected an entity word, got {word}")
        node = {"id": "n" + number_word(len(entities)), "kind": CONCEPTS[concept]["kind"], "concept": concept, "quantity": None, "name": None}
        if version in ("0.4", "0.5", "0.6", "0.7"):
            node["qualifiers"] = [CONCEPT_BY_WORD.get(part) for part in parts[1:]]
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
                require(name not in bindings and name not in variables, f"Reference {name} is already defined")
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
        if peek() == "w-p":
            require(version == "0.7", "Distribution requires edition 0.7")
            take()
            variable = reference()
            take("[")
            group = term()
            take("]")
            require(variable not in bindings and variable not in variables, "Bound member name is already defined")
            take("[")
            variables.add(variable)
            try:
                body = expression(depth + 1)
            finally:
                variables.remove(variable)
            take("]")
            return {"kind": "each", "group": group, "variable": variable, "body": body}
        if peek() == "w-w":
            require(version == "0.7", "Collective application requires edition 0.7")
            take()
            marker = take()
            require(marker in ROLE_WORDS, "Expected a collective role marker")
            take("[")
            body = expression(depth + 1)
            take("]")
            return {"kind": "collective", "role": ROLE_WORDS[marker], "body": body}
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
        predicate = parse_predicate(word, version, CONCEPTS, CONCEPT_BY_WORD)
        roles, primary, explicit = {}, 0, False
        while True:
            if peek() in ROLE_WORDS:
                role = ROLE_WORDS[take()]
                explicit = True
            elif compact and peek() is not None:
                token = peek()
                concept = CONCEPT_BY_WORD.get(token.split("-")[0])
                is_term = token in ("p", "?", "c") or version in ("0.6", "0.7") and token == "w" or concept is not None and CONCEPTS[concept]["kind"] in ("entity", "place")
                if not is_term:
                    break
                require(not explicit, "Unmarked arguments must precede explicit roles")
                require(primary < 2, "Only agent and patient can be unmarked; mark other roles explicitly")
                role = ("agent", "patient")[primary]
                primary += 1
            else:
                break
            require(role not in roles, f"Duplicate {role} role")
            roles[role] = term()
        return {"kind": "clause", "predicate": predicate, "polarity": polarity, "time": time, "roles": roles}

    if compact:
        edition = header.group(1)
    else:
        take("noema")
        edition = take()
    require(edition in ("b", "c", "d", "e", "f", "g"), "Unsupported written language edition")
    if not compact:
        take(edition)
    version = {"b": "0.2", "c": "0.3", "d": "0.4", "e": "0.5", "f": "0.6", "g": "0.7"}[edition]
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


def format_document(document, compact=False):
    document = normalize_document(document)
    ROOTS, CONCEPTS, ROLE_WORDS, ROLES = policy(document["schema_version"])
    entities = {e["id"]: e for e in document["entities"]}
    seen, counts = set(), {}
    expanded, bound_names = set(), []

    def count_term(ident):
        counts[ident] = counts.get(ident, 0) + 1
        if entities[ident]["kind"] == "group" and ident not in expanded:
            expanded.add(ident)
            for member in entities[ident]["members"]:
                count_term(member)

    def count(expr):
        if expr["kind"] == "clause":
            for term in expr["roles"].values():
                if isinstance(term, str):
                    count_term(term)
        elif expr["kind"] == "each":
            if isinstance(expr["group"], str):
                count_term(expr["group"])
            bound_names.append(expr["variable"])
            count(expr["body"])
        elif expr["kind"] in ("not", "collective"):
            count(expr["body"])
        else:
            count(expr["left"])
            count(expr["right"])

    for utterance in document["utterances"]:
        count(utterance["content"])
    references = {ident: number_word(i) for i, ident in enumerate(e["id"] for e in document["entities"] if counts[e["id"]] > 1)} if compact else {ident: ident for ident in entities}
    variable_names, reserved = {}, set(references.values())
    index = 0
    for name in bound_names:
        while "v" + number_word(index) in reserved:
            index += 1
        variable_names[name] = "v" + number_word(index)
        reserved.add(variable_names[name])
        index += 1

    def term(ident):
        if ident is None:
            return "?"
        if isinstance(ident, dict):
            return "p " + variable_names[ident["bound"]] if "bound" in ident else "c"
        if ident in seen:
            return "p " + references[ident]
        seen.add(ident)
        entity = entities[ident]
        if entity["kind"] == "group":
            members = [term(member) for member in entity["members"]]
            words = ["w" + "".join("[" + member + "]" for member in members)] if compact else ["w " + " ".join("[ " + member + " ]" for member in members)]
        else:
            words = ["-".join([ROOTS[entity["concept"]]] + [ROOTS[q] for q in entity.get("qualifiers", [])])]
            if entity["quantity"] is not None:
                words += ["m", number_word(entity["quantity"])]
            if entity["name"] is not None:
                literal = json.dumps(entity["name"], ensure_ascii=False)
                words += ["n" + literal] if compact else ["n", literal]
        if counts[ident] > 1:
            words += ["o", references[ident]]
        return " ".join(words)

    def expression(expr):
        kind = expr["kind"]
        if kind == "each":
            domain = term(expr["group"])
            body = expression(expr["body"])
            prefix = "w-p " + variable_names[expr["variable"]]
            return prefix + "[" + domain + "][" + body + "]" if compact else prefix + " [ " + domain + " ] [ " + body + " ]"
        if kind == "collective":
            marker = {v: k for k, v in ROLE_WORDS.items()}[expr["role"]]
            body = expression(expr["body"])
            return "w-w " + marker + "[" + body + "]" if compact else "w-w " + marker + " [ " + body + " ]"
        if kind == "not":
            if compact:
                return "u[" + expression(expr["body"]) + "]"
            return "u [ " + expression(expr["body"]) + " ]"
        if kind in CONNECTIVES.values():
            marker = {v: k for k, v in CONNECTIVES.items()}[kind]
            if compact:
                return marker + "[" + expression(expr["left"]) + "][" + expression(expr["right"]) + "]"
            return marker + " [ " + expression(expr["left"]) + " ] [ " + expression(expr["right"]) + " ]"
        words = []
        if expr["polarity"] == "unspecified":
            words.append("v")
        t = expr["time"]
        if t["kind"] == "date":
            literal = json.dumps(t["value"])
            words += ["q" + literal] if compact else ["q", literal]
        elif t["kind"] != "unspecified":
            words.append({v: k for k, v in TIME_WORDS.items()}[t["value"]])
        words.append(predicate_word(expr["predicate"], ROOTS))
        for marker, role in ROLE_WORDS.items():
            value = expr["roles"][role]
            if value is not None:
                unmarked = compact and (role == "agent" or role == "patient" and expr["roles"]["agent"] is not None)
                words += [term(value)] if unmarked else [marker, term(value)]
        return " ".join(words)

    marker = {"0.2": "b", "0.3": "c", "0.4": "d", "0.5": "e", "0.6": "f", "0.7": "g"}[document["schema_version"]]
    lines = [] if compact else [f"noema {marker} {marker}"]
    for utterance in document["utterances"]:
        mood = {"assertion": "", "question": "b ", "request": "d "}[utterance["speech_act"]]
        lines.append(mood + expression(utterance["content"]) + ".")
    return (marker + ":" if compact else "") + "\n".join(lines)


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
    require(all(entity["kind"] != "group" for entity in doc["entities"]), "0.1 cannot represent groups")
    if doc["schema_version"] in ("0.4", "0.5", "0.6", "0.7"):
        require(all(not entity["qualifiers"] for entity in doc["entities"]), "0.1 cannot represent compound properties")
        for entity in doc["entities"]:
            del entity["qualifiers"]
    require(len(doc["utterances"]) == 1 and doc["utterances"][0]["speech_act"] == "assertion", "0.1 can represent only a single assertion")
    content = doc["utterances"][0]["content"]
    negated = content["kind"] == "not"
    if negated:
        content = content["body"]
    require(content["kind"] == "clause", "0.1 cannot represent connective or nested negation scope")
    require(not negated or content["polarity"] == "affirmed", "0.1 cannot negate unspecified polarity")
    require(isinstance(content["predicate"], str), "0.1 cannot represent derived predicates")
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
    if source['schema_version'] in ('0.8', '0.9', '0.10', '0.11', '0.12', '0.13') or version in ('0.8', '0.9', '0.10', '0.11', '0.12', '0.13'):
        require(source['schema_version'] in ('0.8', '0.9', '0.10', '0.11', '0.12', '0.13') and version in ('0.8', '0.9', '0.10', '0.11', '0.12', '0.13'),
                'Conversion between editions 0.8/0.9/0.10/0.11/0.12/0.13 and legacy editions is not defined')
        source['schema_version'] = source['lexicon_version'] = version
        return normalize(source)
    if source["schema_version"] == "0.1":
        source = from_graph(source)
    if version == "0.1":
        return to_graph(source)
    _, _, _, roles = policy(version)
    require(version in ("0.6", "0.7") or all(entity["kind"] != "group" for entity in source["entities"]), "Target edition cannot represent groups")
    for entity in source["entities"]:
        if entity["kind"] == "group":
            continue
        if version in ("0.4", "0.5", "0.6", "0.7"):
            entity.setdefault("qualifiers", [])
        elif source["schema_version"] in ("0.4", "0.5", "0.6", "0.7"):
            require(not entity["qualifiers"], "Target edition cannot represent compound properties")
            del entity["qualifiers"]

    def visit(expr):
        if expr["kind"] == "clause":
            require(version in ("0.5", "0.6", "0.7") or isinstance(expr["predicate"], str), "Target edition cannot represent derived predicates")
            require(all(value is None for role, value in expr["roles"].items() if role not in roles), "Target edition cannot represent extended roles")
            expr["roles"] = {r: v for r, v in expr["roles"].items() if r in roles}
        elif expr["kind"] in ("each", "collective"):
            require(version == "0.7", "Target edition cannot represent distribution or collective application")
            visit(expr["body"])
        elif expr["kind"] == "not":
            visit(expr["body"])
        else:
            visit(expr["left"])
            visit(expr["right"])

    for utterance in source["utterances"]:
        visit(utterance["content"])
    source["schema_version"] = source["lexicon_version"] = version
    return normalize_document(source)
