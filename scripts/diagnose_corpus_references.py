"""Separate strict reference errors from unmatched source head boundaries."""
import json

from noema.definition_probe import digest
from noema.kwdlc_references import gold_partition, predicted_partition, assess_corpus_references
from scripts.prepare_reference_corpus import ARTIFACTS, REPORT, write


def diagnose(rows, outputs):
    counts = {"documents": 0, "gold_pairs": 0, "predicted_pairs": 0, "correct_pairs": 0,
              "gold_pairs_missing_head": 0, "predicted_pairs_extra_head": 0,
              "gold_pairs_matching_heads": 0, "predicted_pairs_matching_heads": 0}
    for row, output in zip(rows, outputs, strict=True):
        assert row["id"] == output["id"]
        prediction = output["prediction"]
        if not assess_corpus_references(row, prediction)["annotation_supported"]:
            continue
        counts["documents"] += 1
        gh, gp = gold_partition(row)
        ph, pp = predicted_partition(prediction) if prediction is not None else (set(), set())
        common = gh & ph
        matched_gold = {p for p in gp if all(h in common for h in p)}
        matched_predicted = {p for p in pp if all(h in common for h in p)}
        counts["gold_pairs"] += len(gp)
        counts["predicted_pairs"] += len(pp)
        counts["correct_pairs"] += len(gp & pp)
        counts["gold_pairs_missing_head"] += len(gp - matched_gold)
        counts["predicted_pairs_extra_head"] += len(pp - matched_predicted)
        counts["gold_pairs_matching_heads"] += len(matched_gold)
        counts["predicted_pairs_matching_heads"] += len(matched_predicted)
    for name, denominator in (("matching_heads_pair_precision", "predicted_pairs_matching_heads"),
                              ("matching_heads_pair_recall", "gold_pairs_matching_heads")):
        counts[name] = counts["correct_pairs"] / counts[denominator] if counts[denominator] else None
    return counts


def main():
    preparation = json.loads((REPORT / "preparation.json").read_text(encoding="utf-8"))
    run = json.loads((REPORT / "run.json").read_text(encoding="utf-8"))
    assert digest(ARTIFACTS / "dev.jsonl") == preparation["prepared_sha256"]["dev"]
    assert digest(ARTIFACTS / "predictions.jsonl") == run["predictions_sha256"]
    def read(name):
        return [json.loads(line) for line in (ARTIFACTS / name).read_text(encoding="utf-8").splitlines()]
    result = diagnose(read("dev.jsonl"), read("predictions.jsonl"))
    path = REPORT / "boundary-diagnostic.json"
    if path.exists():
        assert result == json.loads(path.read_text(encoding="utf-8"))
    else:
        write(path, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
