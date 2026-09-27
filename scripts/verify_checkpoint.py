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
    trainable = sum(p.numel() for p in analyzer.encoder.model.parameters() if p.requires_grad)
    training_modules = sum(m.training for m in analyzer.encoder.model.modules())
    if trainable or training_modules:
        raise AssertionError("Encoder must be frozen and entirely in evaluation mode")
    rows = examples()
    predictions = [analyzer.analyze(r["text"], r["language"]) for r in rows]
    repeated = [analyzer.analyze(rows[i]["text"], rows[i]["language"]) == predictions[i] for i in range(4)]
    report = {"checkpoint": args.checkpoint, "encoder_trainable_parameters": trainable, "encoder_training_modules": training_modules,
              "repeat_identical_results": all(repeated), "repeated_examples": len(repeated),
              "metrics": evaluate(rows, predictions), "predictions": [{"id": r["id"], "text": r["text"], **pred} for r, pred in zip(rows, predictions)]}
    save_json(args.output, report)
    print({"repeat_identical_results": report["repeat_identical_results"], "metrics": report["metrics"]})


if __name__ == "__main__":
    main()
