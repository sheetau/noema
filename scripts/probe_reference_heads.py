"""Evaluate native reference evidence without training or lexical corrections."""
import argparse
import json
from pathlib import Path

from noema.definition_probe import digest
from noema.reference_heads import ReferenceFrameAnalyzer, reference_graph, assess_references
from noema.semantics import require
from scripts.train_mention_scope import forbidden_paths

DATA = Path("data/reference-head-v1.json")
CODE = ("noema/reference_heads.py", "noema/japanese_pas.py", "noema/event_frames.py", "noema/event_gate.py",
        "scripts/probe_reference_heads.py")
PREVIOUS = ("reports/event-gate-v6/selection.json", "reports/multi-frame-v5/selection.json")


def gold_mentions(row):
    result = []
    for surface, occurrence, referent in row["mentions"]:
        require(bool(surface) and isinstance(occurrence, int) and occurrence >= 0, "Invalid occurrence annotation")
        start = -1
        for _ in range(occurrence + 1):
            start = row["text"].find(surface, start + 1)
            require(start >= 0, "Missing annotated occurrence")
        result.append({"start": start, "end": start + len(surface), "text": surface, "referent": referent})
    require(len({(m["start"], m["end"]) for m in result}) == len(result), "Duplicate annotated span")
    return result


def evaluate(row, output):
    gold = gold_mentions(row)
    diagnostic = reference_graph(output["analysis"], output["dependencies"]["phrases"], gold)
    return {"id": row["id"], "kind": row["kind"], "gold_span_graph": diagnostic,
            "gold_spans": assess_references(gold, diagnostic),
            "predicted_spans": assess_references(gold, output["references"])}


def summarize(cases):
    results = {}
    for kind in ("all", "nested", "cross_sentence", "distinct"):
        selected = [c for c in cases if kind == "all" or c["kind"] == kind]
        results[kind] = {}
        for mode in ("gold_spans", "predicted_spans"):
            counts = {key: sum(c[mode][key] for c in selected) for key in selected[0][mode]} if selected else {}
            def ratio(a, b):
                return counts[a] / counts[b] if counts[b] else None
            if counts:
                counts.update(documents=len(selected), pair_precision=ratio("correct_pairs", "predicted_pairs"),
                              pair_recall=ratio("correct_pairs", "gold_pairs"),
                              mention_recall=ratio("correct_mentions", "gold_mentions"))
            results[kind][mode] = counts
    return results


def write(root, name, value):
    with (root / name).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/reference-head-v1")
    args = parser.parse_args()
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=False)
    rows = json.loads(DATA.read_text(encoding="utf-8"))
    for row in rows:
        gold_mentions(row)
    cases, evidence = [], []
    with forbidden_paths() as guards:
        analyzer = ReferenceFrameAnalyzer()
        for row in rows:
            output = analyzer.analyze(row["text"])
            assert output == analyzer.analyze(row["text"]), row["id"]
            baseline = analyzer.gated.analyze(row["text"])
            assert all(output[key] == baseline[key] for key in ("analysis", "event_decisions", "frames")), row["id"]
            evidence.append({"row": row, "output": output})
            cases.append(evaluate(row, output))
            print("repeated and baseline equal", row["id"], flush=True)
        counts = [guard.call_count for guard in guards]
    write(root, "evidence.json", evidence)
    write(root, "evaluation.json", {"summary": summarize(cases), "cases": cases})
    write(root, "run.json", {"fixture_sha256": digest(DATA),
          "protocol_sha256": digest("docs/reference-head-v1-protocol.md"),
          "code_sha256": {p: digest(p) for p in CODE}, "previous_files_sha256": {p: digest(p) for p in PREVIOUS},
          "metadata": analyzer.gated.frame.parser.metadata, "training": False,
          "forbidden_path_calls": counts, "raw_repeated_and_baseline_equal": [r["id"] for r in rows],
          "outputs_sha256": {p: digest(root / p) for p in ("evidence.json", "evaluation.json")}})
    print(json.dumps(summarize(cases), indent=2), flush=True)


if __name__ == "__main__":
    main()
