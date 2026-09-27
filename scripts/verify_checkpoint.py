"""Run the real analyzer on hand-authored held-out examples, plus repetition checks."""
import argparse
from noema.analyzer import Analyzer
from noema.challenge import examples
from noema.evaluation import evaluate
from noema.training import save_json


def main():
    p = argparse.ArgumentParser()
    p.add_argument("checkpoint")
    p.add_argument("--output", required=True)
    p.add_argument("--offline", action="store_true")
    args = p.parse_args()
    analyzer = Analyzer(args.checkpoint, offline=args.offline)
    rows = examples()
    predictions = [analyzer.analyze(r["text"], r["language"]) for r in rows]
    repeated = [analyzer.analyze(rows[i]["text"], rows[i]["language"]) == predictions[i] for i in range(4)]
    report = {"checkpoint": args.checkpoint, "repeat_identical_results": all(repeated), "repeated_examples": len(repeated),
              "metrics": evaluate(rows, predictions), "predictions": [{"id": r["id"], "text": r["text"], **pred} for r, pred in zip(rows, predictions)]}
    save_json(args.output, report)
    print({"repeat_identical_results": report["repeat_identical_results"], "metrics": report["metrics"]})


if __name__ == "__main__":
    main()
