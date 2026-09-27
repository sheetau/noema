"""Train-only unknown-span labels using the existing 'none' concept class."""
from .structured import LABELS, targets as base_targets
from .semantics import require


def targets(row, feature):
    labels = base_targets(row, feature)
    spans = row.get("unknown_spans", [])
    require(not spans or not row["supported"], "Unknown spans require an unsupported training example")
    if "known_spans" in row:
        require(not row["supported"] and spans, "Context annotations require an unsupported span")
        # An authored replacement preserves every other local span. Supervise
        # their full BIO context without fabricating a complete meaning graph.
        for i, (start, end) in enumerate(feature["offsets"]):
            if start < end:
                labels["span"][i] = LABELS["span"].index("O")
        for span in row["known_spans"]:
            require(0 <= span["start"] < span["end"] <= len(row["text"]), "Invalid known span")
            require(all(span["end"] <= s["start"] or span["start"] >= s["end"] for s in spans), "Known and unknown overlap")
            matched = [i for i, (start, end) in enumerate(feature["offsets"])
                       if start < end and start < span["end"] and end > span["start"]]
            for index, i in enumerate(matched):
                require(labels["span"][i] == LABELS["span"].index("O"), "Context annotations overlap")
                labels["span"][i] = LABELS["span"].index(("B-" if index == 0 else "I-") + span["kind"])
                if span["kind"] in ("entity", "predicate"):
                    labels["concept"][i] = LABELS["concept"].index(span["concept"])
                if span["kind"] == "entity":
                    labels["role"][i] = LABELS["role"].index(span["role"])
    for span in spans:
        require(span["kind"] in ("entity", "predicate"), "Invalid unknown span kind")
        require(0 <= span["start"] < span["end"] <= len(row["text"]), "Invalid unknown span")
        for i, (start, end) in enumerate(feature["offsets"]):
            if start < end and start < span["end"] and end > span["start"]:
                labels["concept"][i] = LABELS["concept"].index("none")
                labels["span"][i] = LABELS["span"].index(("B-" if start == span["start"] else "I-") + span["kind"])
    return labels
