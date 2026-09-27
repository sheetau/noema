"""Evaluate a frozen development-selected ranker on the official test split."""
import json

from safetensors.torch import load_file

from noema.definition_probe import digest
from noema.encoder import deterministic
from noema.reference_ranker import ReferenceRanker
from noema.semantics import require
from scripts.cache_reference_features import ROOT, REPORT, CORPUS_REPORT
from scripts.prepare_reference_corpus import write
from scripts.train_reference_ranker import load_split, evaluate


def selected_head(root=ROOT, report=REPORT):
    require(not (report / "invalidated.json").exists(), "Reference ranker invalidated: incorrect corpus head supervision")
    selection = json.loads((report / "selection.json").read_text(encoding="utf-8"))
    training = json.loads((report / "training.json").read_text(encoding="utf-8"))
    require(digest(report / "selection.json") == training["selection_sha256"], "Reference selection changed")
    require(digest("docs/reference-ranker-v1-protocol.md") == training["protocol_sha256"], "Reference training protocol changed")
    require(all(digest(p) == sha for p, sha in training["code_sha256"].items()), "Reference training code changed")
    require(digest(root / "manifest.json") == selection["feature_manifest_sha256"], "Reference feature contract changed")
    choices = selection["choices"]
    expected = max(choices, key=lambda name: (choices[name]["dev_pair_f1"], -choices[name]["dev_loss"],
                                             -choices[name]["epoch"], name == "linear"))
    require(expected == selection["selected"], "Reference selection violates the frozen development criterion")
    require(selection["decision"] == "argmax_previous_or_none", "Reference decision policy changed")
    name = selection["selected"]
    path = root / f"ranker-{name}.safetensors"
    require(digest(path) == selection["weights_sha256"][name], "Selected reference weights changed")
    head = ReferenceRanker(selection["dimension"], choices[name]["hidden"])
    head.load_state_dict(load_file(str(path)), strict=True)
    return head.eval().requires_grad_(False), selection


def training_overlap_ids(preparation):
    return sorted({row["id"] for group in preparation["cross_split_duplicate_texts"]
                   if any(row["split"] == "train" for row in group)
                   for row in group if row["split"] == "test"})


def test_evaluation(records, head, overlap):
    remaining = [r for r in records if r["row"]["id"] not in set(overlap)]
    return {"all": {"native": evaluate(records), "selected": evaluate(records, head, include_decisions=True)},
            "without_training_text_overlap": {"native": evaluate(remaining),
                                                "selected": evaluate(remaining, head, include_decisions=True)}}


def main():
    deterministic()
    head, selection = selected_head()
    records, statistics, manifest = load_split("test")
    require(manifest["model"] == selection["model"], "Test feature model differs from training")
    preparation = json.loads((CORPUS_REPORT / "preparation.json").read_text(encoding="utf-8"))
    overlap = training_overlap_ids(preparation)
    require(set(overlap) <= {r["row"]["id"] for r in records}, "Training overlap is outside test split")
    results = test_evaluation(records, head, overlap)
    write(REPORT / "test.json", {"selected": selection["selected"], "training_text_overlap_ids": overlap,
          "supervision_diagnostic": statistics, "evaluation": results,
          "selection_sha256": digest(REPORT / "selection.json"),
          "test_features_sha256": digest(REPORT / "features-test.json"),
          "code_sha256": {p: digest(p) for p in ("scripts/evaluate_reference_ranker.py", "scripts/train_reference_ranker.py", "noema/reference_ranker.py")}})
    print(json.dumps({group: {name: result["summary"]["all"] for name, result in values.items()}
                      for group, values in results.items()}, indent=2))


if __name__ == "__main__":
    main()
