"""Reuse frozen features only after aligning supervision to corrected annotated phrases."""
import json
from pathlib import Path

import torch
from safetensors.torch import save_file

from noema.definition_probe import digest
from noema.encoder import deterministic
from noema.kwdlc_phrase_references import UNIT, assess_phrase_references, phrase_summary
from noema.phrase_reference_ranker import ROOT, REPORT, PROTOCOL, phrase_targets
from noema.reference_ranker import scalar_features, marginal_reference_loss, rank_references
from noema.semantics import require
from scripts.cache_reference_features import ROOT as FEATURES, REPORT as FEATURE_REPORT, CORPUS as OLD_CORPUS, read_cached
from scripts.prepare_phrase_reference_corpus import ROOT as CORPUS, REPORT as CORPUS_REPORT
from scripts.prepare_reference_corpus import write
from scripts.train_reference_ranker import fit, ARCHITECTURES, EPOCHS, BATCH

CODE = ("noema/phrase_reference_ranker.py", "noema/reference_ranker.py", "noema/kwdlc_phrase_references.py",
        "noema/kwdlc_references.py", "scripts/train_reference_ranker.py", "scripts/train_phrase_reference_ranker.py")


def training_record(row, legacy, cached, features):
    require(all(row[k] == legacy[k] for k in ("id", "text", "relations", "split")), "Corrected annotation source or relations differ")
    prediction = cached["prediction"]
    target, statistics = None, {}
    if prediction is not None:
        require(features is not None, "Missing frozen phrase features")
        phrases, tokens = prediction["phrases"], prediction["tokens"]
        require([p["id"] for p in phrases] == list(range(len(phrases))), "Frozen phrase IDs differ")
        require(len(features["nodes"]) == len(phrases), "Frozen phrase node count differs")
        indices = features["word_indices"].tolist()
        require(len(indices) == len(phrases) and all(tokens[i] == p["head"] for i, p in zip(indices, phrases, strict=True)),
                "Frozen node vectors do not match native phrase heads")
        require(int(features["word_count"]) == len(tokens), "Frozen token count differs")
        features["scalars"] = scalar_features(features)
        target, statistics = phrase_targets(row, prediction)
    else:
        require(features is None and cached["failure"] is not None, "Invalid failed phrase record")
    return {"row": row, "prediction": prediction, "failure": cached["failure"], "features": features, "target": target}, statistics


def load_split(split):
    manifest_path = FEATURES / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(all(digest(p) == sha for p, sha in manifest["code_sha256"].items()), "Frozen feature extraction code changed")
    completion = json.loads((FEATURE_REPORT / f"features-{split}.json").read_text(encoding="utf-8"))
    require(completion["complete"] and completion["manifest_sha256"] == digest(manifest_path), "Incomplete frozen features")
    preparation = json.loads((CORPUS_REPORT / "preparation.json").read_text(encoding="utf-8"))
    require(preparation["alignment_unit"] == UNIT, "Corrected corpus unit differs")
    require(all(digest(p) == sha for p, sha in preparation["code_sha256"].items()), "Corrected corpus preparation code changed")
    path, legacy_path = CORPUS / f"{split}.jsonl", OLD_CORPUS / f"{split}.jsonl"
    require(digest(path) == preparation["prepared_sha256"][split], "Corrected corpus changed")
    require(digest(legacy_path) == manifest["corpus_sha256"][split], "Original cache source changed")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    legacy = [json.loads(line) for line in legacy_path.read_text(encoding="utf-8").splitlines()]
    require([r["id"] for r in rows] == [r["id"] for r in legacy] == [r["id"] for r in completion["records"]], "Phrase feature inventory differs")
    records, counts = [], {}
    for row, before, item in zip(rows, legacy, completion["records"], strict=True):
        require(digest(FEATURES / split / f"{row['id']}.json") == item["record_sha256"], "Frozen prediction changed")
        cached, features = read_cached(FEATURES, before)
        record, statistics = training_record(row, before, cached, features)
        records.append(record)
        for key, value in statistics.items():
            counts[key] = counts.get(key, 0) + value
    counts.update(documents=len(records), failed_documents=sum(r["failure"] is not None for r in records))
    return records, counts, manifest


def evaluate(records, head=None):
    cases, total_loss, sources = [], 0., 0
    for record in records:
        prediction = record["prediction"]
        if head is not None and record["features"] is not None:
            with torch.inference_mode():
                loss, n = marginal_reference_loss(head(record["features"]), record["target"])
            total_loss += float(loss)
            sources += n
            prediction, _ = rank_references(prediction, record["features"], head)
        cases.append({**assess_phrase_references(record["row"], prediction), "failure": record["failure"]})
    summary = phrase_summary(cases)
    count = summary["all"]
    denominator = count["gold_pairs"] + count["predicted_pairs"]
    return {"summary": summary, "cases": cases, "pair_f1": 2 * count["correct_pairs"] / denominator if denominator else 0.,
            "mean_loss": total_loss / sources if sources else None}


def main():
    require(not (REPORT / "selection.json").exists(), "Phrase ranker selection already exists")
    ROOT.mkdir(parents=True, exist_ok=False)
    REPORT.mkdir(parents=True, exist_ok=True)
    deterministic()
    train, train_counts, manifest = load_split("train")
    dev, dev_counts, _ = load_split("dev")
    dimension = next(r["features"]["nodes"].shape[1] // 2 for r in train if r["features"] is not None)
    baseline = evaluate(dev)
    expected = json.loads((CORPUS_REPORT / "native-development.json").read_text(encoding="utf-8"))
    require(baseline["summary"] == expected["summary"] and baseline["cases"] == expected["cases"], "Corrected native baseline differs")
    choices, weights, evaluations = {}, {}, {"native": baseline}
    for name, hidden in ARCHITECTURES:
        head, choice, history = fit(train, dev, dimension, hidden, evaluate_fn=evaluate)
        path = ROOT / f"ranker-{name}.safetensors"
        require(not path.exists(), "Phrase ranker checkpoint already exists")
        save_file(head.state_dict(), str(path))
        choices[name], weights[name] = choice, digest(path)
        evaluations[name] = evaluate(dev, head)
        write(REPORT / f"history-{name}.json", history)
    selected = max(choices, key=lambda name: (choices[name]["dev_pair_f1"], -choices[name]["dev_loss"],
                                             -choices[name]["epoch"], name == "linear"))
    write(REPORT / "development.json", evaluations)
    write(REPORT / "selection.json", {"alignment_unit": UNIT, "selected": selected, "dimension": dimension,
          "choices": choices, "weights_sha256": weights, "decision": "argmax_previous_or_none", "model": manifest["model"]})
    write(REPORT / "training.json", {"alignment_unit": UNIT, "code_sha256": {p: digest(p) for p in CODE},
          "protocol_sha256": digest(PROTOCOL), "feature_manifest_sha256": digest(FEATURES / "manifest.json"),
          "corpus_preparation_sha256": digest(CORPUS_REPORT / "preparation.json"),
          "feature_reports_sha256": {s: digest(FEATURE_REPORT / f"features-{s}.json") for s in ("train", "dev")},
          "train": train_counts, "dev": dev_counts, "seed": 17, "epochs": EPOCHS, "batch_documents": BATCH,
          "learning_rate": .001, "weight_decay": .01, "selection_sha256": digest(REPORT / "selection.json")})
    print("Selected", selected, choices[selected], flush=True)


if __name__ == "__main__":
    main()
