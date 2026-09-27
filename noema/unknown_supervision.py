"""Train-only unknown-span labels using the existing 'none' concept class."""
from .structured import LABELS, targets as base_targets
from .semantics import require


def targets(row, feature):
    labels = base_targets(row, feature)
    spans = row.get("unknown_spans", [])
    require(not spans or not row["supported"], "Unknown spans require an unsupported training example")
    for span in spans:
        require(span["kind"] in ("entity", "predicate"), "Invalid unknown span kind")
        require(0 <= span["start"] < span["end"] <= len(row["text"]), "Invalid unknown span")
        for i, (start, end) in enumerate(feature["offsets"]):
            if start < end and start < span["end"] and end > span["start"]:
                labels["concept"][i] = LABELS["concept"].index("none")
                labels["span"][i] = LABELS["span"].index(("B-" if start == span["start"] else "I-") + span["kind"])
    return labels
