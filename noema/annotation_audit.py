"""Cross-check annotations against gold graphs without lexical inference rules.

This validates internal consistency, not whether an authored sentence actually
means its gold graph. Linguistic review remains a separate requirement.
"""
import argparse
import json
from .dataset import load_dataset, digest
from .semantics import normalize, require


def audit(rows):
    groups = {}
    supported = 0
    for row in rows:
        prefix = row["id"] + ": "
        if not row["supported"]:
            require(row["graph"] is None and row["spans"] == [], prefix + "Unsupported rows must not carry a positive gold graph")
            end = 0
            for span in sorted(row.get("unknown_spans", []), key=lambda s: s["start"]):
                require(span["kind"] in ("entity", "predicate"), prefix + "Invalid unknown span kind")
                require(type(span["start"]) is int and type(span["end"]) is int and end <= span["start"] < span["end"] <= len(row["text"]), prefix + "Invalid unknown annotation span")
                end = span["end"]
            continue
        supported += 1
        graph = normalize(row["graph"])
        require(graph["schema_version"] == "0.1", prefix + "Expected extraction graph edition 0.1")
        require(row["group"] not in groups or groups[row["group"]] == graph, prefix + "Equivalent examples have different gold graphs")
        groups[row["group"]] = graph
        nodes = {n["id"]: n for n in graph["nodes"]}
        entities = {r["role"]: nodes[r["target"]] for r in graph["relations"] if r["target"] is not None}
        event = graph["nodes"][0]
        entity_spans, quantity_spans, predicates = {}, {}, []
        previous_end = 0
        for span in sorted(row["spans"], key=lambda s: s["start"]):
            require(previous_end <= span["start"] < span["end"] <= len(row["text"]), prefix + "Invalid or overlapping span")
            previous_end = span["end"]
            literal = row["text"][span["start"]:span["end"]]
            if span["kind"] == "predicate":
                predicates.append(span["concept"])
            elif span["kind"] in ("entity", "quantity"):
                role = span["role"]
                require(role in entities, prefix + "Span refers to an absent role")
                node = entities[role]
                if span["kind"] == "entity":
                    require(role not in entity_spans, prefix + "Duplicate entity annotation")
                    require(node["concept"] == span["concept"], prefix + "Entity concept disagrees with gold graph")
                    if node["concept"] == "ag":
                        require(literal == node["name"], prefix + "Name span differs from the literal gold name")
                    entity_spans[role] = span
                else:
                    require(role not in quantity_spans, prefix + "Duplicate quantity annotation")
                    require(literal.isdecimal() and int(literal) == node["quantity"], prefix + "Quantity span disagrees with gold graph")
                    require(not (span["start"] and row["text"][span["start"] - 1].isdecimal()), prefix + "Quantity starts inside a number")
                    require(not (span["end"] < len(row["text"]) and row["text"][span["end"]].isdecimal()), prefix + "Quantity ends inside a number")
                    quantity_spans[role] = span
            else:
                require(span["kind"] in ("time", "negation"), prefix + "Unknown annotation kind")
        require(predicates == [event["concept"]], prefix + "Predicate annotation disagrees with gold graph")
        require(set(entity_spans) == set(entities), prefix + "Missing entity annotation")
        require(set(quantity_spans) == {r for r, n in entities.items() if n["quantity"] is not None}, prefix + "Missing or extra quantity annotation")
    return {"rows": len(rows), "supported": supported, "equivalence_groups": len(groups), "internal_consistency": True,
            "linguistic_correctness": "not established by this audit"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = {"dataset_sha256": digest(args.dataset), **audit(load_dataset(args.dataset))}
    if args.output:
        from .training import save_json
        save_json(args.output, result)
    print(json.dumps(result, indent=2))
