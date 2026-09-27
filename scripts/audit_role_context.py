"""Separate absent candidates, rejected exact spans, and wrong semantic roles."""
import json
from pathlib import Path

from noema.role_transfer import LABELS, anchor, overlap


def audit(examples, evaluation):
    by_id = {e["row"]["id"]: e for e in examples}
    results = {}
    for name, splits in evaluation.items():
        results[name] = {}
        for split, evaluation_split in splits.items():
            cases = []
            for case in evaluation_split["cases"]:
                example = by_id[case["id"]]
                row = example["row"]
                mentions = {(m["start"], m["end"]): m["id"] for m in example["mentions"]}
                phrases = {p["id"]: p for p in example["prediction"]["phrases"]}
                event = anchor(row["text"], row["predicate"])
                arguments = []
                for role, surface in row["roles"]:
                    span = anchor(row["text"], surface)
                    target = mentions.get((span["start"], span["end"]))
                    labels = [output["role"] for output in case["outputs"] if output["target"] == target
                              and overlap(phrases[output["source"]]["head"], event)] if target is not None else []
                    state = "absent_candidate" if not labels else "correct" if role in labels else "rejected" if set(labels) == {"none"} else "wrong_role"
                    arguments.append({"role": role, "surface": surface, "span": span, "predicted": labels, "outcome": state})
                cases.append({"id": row["id"], "arguments": arguments})
            arguments = [a for c in cases for a in c["arguments"]]
            counts = {state: sum(a["outcome"] == state for a in arguments) for state in ("correct", "absent_candidate", "rejected", "wrong_role")}
            assert counts["correct"] == evaluation_split["summary"]["exact_roles"]
            assert sum(counts.values()) == evaluation_split["summary"]["gold_roles"]
            results[name][split] = {"summary": counts, "by_role": {
                role: {"expected": sum(a["role"] == role for a in arguments),
                       "correct": sum(a["role"] == role and a["outcome"] == "correct" for a in arguments)} for role in LABELS[1:]}, "cases": cases}
    return results


def main():
    root = Path("reports/role-context-v3")
    old = json.loads(Path("reports/mention-learning-v2/evidence.json").read_text(encoding="utf-8"))
    new = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
    result = audit(old + new, json.loads((root / "evaluation.json").read_text(encoding="utf-8")))
    with (root / "error-audit.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({name: {split: value["summary"] for split, value in splits.items()} for name, splits in result.items()}, indent=2))


if __name__ == "__main__":
    main()
