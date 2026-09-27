"""Productive state-to-event operators, independent of model labels and roots."""
import json
from importlib.resources import files
from .semantics import keys, require

DERIVATION = json.loads(files("noema").joinpath("resources/language-v05.json").read_text(encoding="utf-8"))


def predicate_spec(predicate, version, concepts):
    if isinstance(predicate, str):
        require(predicate in concepts and concepts[predicate]["kind"] in ("event", "state"), "Expected an event or state concept")
        return concepts[predicate]
    require(version == "0.5", "Derived predicates require edition 0.5")
    keys(predicate, ("operator", "state"))
    operator, state = predicate["operator"], predicate["state"]
    require(isinstance(operator, str) and operator in DERIVATION["operators"], "Unknown derivation operator")
    require(isinstance(state, str) and state in DERIVATION["state_bases"], "Derivation requires a supported unary state")
    base = concepts[state]
    require(base["kind"] == "state" and set(base["roles"]) <= {"agent", "location"}, "Invalid derivation base")
    rule = DERIVATION["operators"][operator]
    role_types = {"agent": ["entity"], "patient": ["entity"], "location": ["place"], "instrument": ["entity"]}
    role_types[rule["bearer_role"]] = base.get("role_types", {}).get("agent", ["entity"])
    return {"kind": "event", "roles": rule["roles"], "role_types": {r: role_types[r] for r in rule["roles"]}}


def parse_predicate(word, version, concepts, by_word):
    parts = word.split("-")
    if len(parts) == 1:
        predicate = by_word.get(word)
    else:
        require(version == "0.5", "Derived predicates require edition 0.5")
        operators = {v["marker"]: k for k, v in DERIVATION["operators"].items()}
        require(len(parts) == 2 and parts[0] in operators, "Expected operator-state word")
        predicate = {"operator": operators[parts[0]], "state": by_word.get(parts[1])}
    predicate_spec(predicate, version, concepts)
    return predicate


def predicate_word(predicate, roots):
    if isinstance(predicate, str):
        return roots[predicate]
    return DERIVATION["operators"][predicate["operator"]]["marker"] + "-" + roots[predicate["state"]]
