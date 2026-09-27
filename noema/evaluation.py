"""Selective prediction metrics, reported separately for Japanese and English."""
from collections import defaultdict
from .semantics import normalize, ROLES


def components(graph):
    graph = normalize(graph)
    nodes = {n["id"]: n for n in graph["nodes"]}
    event = nodes["e"]
    result = {"predicate": event["concept"], "polarity": event["polarity"], "time": event["time"]}
    for relation in graph["relations"]:
        n = nodes.get(relation["target"])
        result[relation["role"]] = {k: n[k] for k in ("concept", "quantity", "name")} if n else None
    return result


def evaluate(rows, predictions):
    if len(rows) != len(predictions):
        raise ValueError("Prediction count does not match dataset")
    report = {}
    for language in ("ja", "en"):
        subset = [(r, p) for r, p in zip(rows, predictions) if r["language"] == language]
        inside = [(r, p) for r, p in subset if r["supported"]]
        outside = [(r, p) for r, p in subset if not r["supported"]]
        confirmed = [(r, p) for r, p in inside if p["status"] == "confirmed"]
        exact = sum(normalize(r["graph"]) == normalize(p["graph"]) for r, p in confirmed)
        errors = defaultdict(int)
        for row, prediction in inside:
            if prediction["graph"] is None:
                errors["abstained"] += 1
            else:
                gold, pred = components(row["graph"]), components(prediction["graph"])
                for key in gold:
                    errors[key] += gold[key] != pred[key]
        coverage = len(confirmed) / len(inside) if inside else None
        accuracy = exact / len(confirmed) if confirmed else None
        false_accepts = sum(p["status"] == "confirmed" for _, p in outside)
        report[language] = {"in_scope": len(inside), "confirmed": len(confirmed), "exact": exact,
                            "coverage": coverage, "confirmed_exact_match": accuracy,
                            "unsupported": len(outside), "unsupported_false_accepts": false_accepts,
                            "unsupported_false_accept_rate": false_accepts / len(outside) if outside else None,
                            "component_errors_on_confirmed": {k: errors[k] for k in ("predicate", "polarity", "time", *ROLES)},
                            "abstained": errors["abstained"],
                            "passes_provisional_gate": coverage is not None and accuracy is not None and coverage >= .8 and accuracy >= .95}
    pairs = defaultdict(list)
    for row, prediction in zip(rows, predictions):
        if row["supported"]:
            pairs[row["group"]].append(prediction)
    complete = [p for p in pairs.values() if len(p) > 1 and all(x["status"] == "confirmed" for x in p)]
    report["equivalence"] = {"groups": len(pairs), "fully_confirmed_groups": len(complete),
                             "equal_confirmed_groups": sum(all(normalize(p[0]["graph"]) == normalize(x["graph"]) for x in p[1:]) for p in complete)}
    return report
