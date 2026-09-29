"""Strict, versioned single-proposition graph validation and canonicalization."""
import copy
import json
import re
from datetime import date
from importlib.resources import files

LEXICON = json.loads(files("noema").joinpath("resources/lexicon.json").read_text(encoding="utf-8"))
CONCEPTS = LEXICON["concepts"]
ROLES = ("agent", "patient", "recipient", "location")
POLARITIES = ("affirmed", "negated", "unspecified")
TIMES = ("unspecified", "past", "present", "future", "yesterday", "today", "tomorrow")
ALPHABET = "abcdefghijklmnopqrstuvwxyz234567"


class SemanticError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise SemanticError(message)


def keys(obj, expected):
    require(isinstance(obj, dict) and set(obj) == set(expected), f"Expected fields: {', '.join(expected)}")


def time_value(label):
    require(label in TIMES, "Unsupported time label")
    return {"kind": "unspecified" if label == "unspecified" else "tense" if label in TIMES[1:4] else "relative", "value": None if label == "unspecified" else label}


def normalize(graph):
    """Reject unrepresentable data instead of silently dropping it. Rename references by role order."""
    if isinstance(graph, dict) and graph.get("schema_version") in ("0.8", "0.9", "0.10", "0.11", "0.12", "0.13"):
        from .discourse import normalize_document
        return normalize_document(graph)
    if isinstance(graph, dict) and graph.get("schema_version") in ("0.2", "0.3", "0.4", "0.5", "0.6", "0.7"):
        from .language import normalize_document
        return normalize_document(graph)
    keys(graph, ("schema_version", "lexicon_version", "nodes", "relations"))
    require(graph["schema_version"] == "0.1" and graph["lexicon_version"] == "0.1", "Unsupported schema or lexicon version")
    require(isinstance(graph["nodes"], list) and isinstance(graph["relations"], list), "nodes and relations must be arrays")
    nodes = {}
    events = []
    for node in graph["nodes"]:
        require(isinstance(node, dict), "Node must be an object")
        kind = node.get("kind")
        keys(node, ("id", "kind", "concept", "polarity", "time") if kind in ("event", "state") else ("id", "kind", "concept", "quantity", "name"))
        ident = node["id"]
        require(isinstance(ident, str) and re.fullmatch(r"[a-z2-7]+", ident), "Invalid node reference")
        require(ident not in nodes, "Duplicate node reference")
        concept = node["concept"]
        require(isinstance(concept, str) and concept in CONCEPTS, "Unknown concept")
        require(kind == CONCEPTS[concept]["kind"], "Concept and node type disagree")
        if kind in ("event", "state"):
            require(node["polarity"] in POLARITIES, "Invalid polarity")
            t = node["time"]
            keys(t, ("kind", "value"))
            if t["kind"] == "date":
                require(isinstance(t["value"], str), "Date must be a string")
                try:
                    require(date.fromisoformat(t["value"]).isoformat() == t["value"], "Use YYYY-MM-DD dates")
                except ValueError as exc:
                    raise SemanticError("Invalid date") from exc
            else:
                require(t in [time_value(v) for v in TIMES], "Invalid time")
            events.append(ident)
        else:
            q, name = node["quantity"], node["name"]
            require(q is None or (type(q) is int and q >= 0), "Quantity must be an exact nonnegative integer or null")
            require(name is None or (isinstance(name, str) and bool(name)), "Name must be a nonempty string or null")
            require(concept != "ag" or name is not None, "A named person requires a name")
            if name is not None:
                try:
                    name.encode("utf-8")
                except UnicodeEncodeError as exc:
                    raise SemanticError("Name contains invalid Unicode") from exc
        nodes[ident] = copy.deepcopy(node)
    require(len(events) == 1, "Exactly one event or state is supported")
    event = nodes[events[0]]
    targets = {}
    for rel in graph["relations"]:
        keys(rel, ("source", "role", "target"))
        require(rel["source"] == events[0], "Relation source must be the proposition")
        role, target = rel["role"], rel["target"]
        require(isinstance(role, str) and role in ROLES and role not in targets, "Unknown or duplicate role")
        require(target is None or isinstance(target, str), "Invalid reference type")
        require(target is None or target in nodes and nodes[target]["kind"] in ("entity", "place"), "Dangling or non-entity reference")
        if target is not None:
            require(role in CONCEPTS[event["concept"]]["roles"], "Role is incompatible with predicate")
            require((nodes[target]["kind"] == "place") == (role == "location"), "Location requires a place; other roles require entities")
        targets[role] = target
    require(set(nodes) == {events[0]} | {v for v in targets.values() if v is not None}, "Unreferenced node")
    mapping = {events[0]: "e"}
    output = [event]
    event["id"] = "e"
    relations = []
    for role in ROLES:
        target = targets.get(role)
        if target is not None and target not in mapping:
            mapping[target] = "n" + ALPHABET[len(mapping) - 1]
            nodes[target]["id"] = mapping[target]
            output.append(nodes[target])
        relations.append({"source": "e", "role": role, "target": mapping[target] if target else None})
    return {"schema_version": "0.1", "lexicon_version": "0.1", "nodes": output, "relations": relations}


def make_graph(predicate, entities, polarity="affirmed", time="unspecified"):
    """Construct a graph from explicit annotations or classifier outputs, never infer missing roles."""
    nodes = [{"id": "e", "kind": CONCEPTS[predicate]["kind"], "concept": predicate, "polarity": polarity, "time": time_value(time)}]
    relations = []
    for role, entity in entities.items():
        ident = "n" + ALPHABET[len(nodes) - 1]
        nodes.append({"id": ident, "kind": CONCEPTS[entity["concept"]]["kind"], "quantity": None, "name": None, **entity})
        relations.append({"source": "e", "role": role, "target": ident})
    return normalize({"schema_version": "0.1", "lexicon_version": "0.1", "nodes": nodes, "relations": relations})
