"""Train shared antecedent scorers on frozen official corpus features."""
import argparse
import copy
import json
from pathlib import Path
import random

import torch
from safetensors.torch import save_file

from noema.definition_probe import digest
from noema.encoder import deterministic
from noema.kwdlc_references import assess_corpus_references, corpus_summary
from noema.reference_ranker import ReferenceRanker, reference_targets, scalar_features, marginal_reference_loss, rank_references
from noema.semantics import require
from scripts.cache_reference_features import ROOT, REPORT, CORPUS, read_cached
from scripts.prepare_reference_corpus import write

ARCHITECTURES = (("linear", 0), ("context", 64))
EPOCHS = 20
BATCH = 16


def load_split(split, root=ROOT, report=REPORT):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    require(all(digest(p) == sha for p, sha in manifest["code_sha256"].items()), "Frozen reference extraction code changed")
    path = CORPUS / f"{split}.jsonl"
    require(digest(path) == manifest["corpus_sha256"][split], "Reference corpus changed")
    completion = json.loads((report / f"features-{split}.json").read_text(encoding="utf-8"))
    require(completion["complete"] and completion["manifest_sha256"] == digest(root / "manifest.json"), "Reference features are incomplete")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    require([r["id"] for r in rows] == [r["id"] for r in completion["records"]], "Reference feature inventory differs")
    records, statistics = [], {}
    for row, committed in zip(rows, completion["records"], strict=True):
        require(digest(root / split / f"{row['id']}.json") == committed["record_sha256"], "Reference prediction cache changed")
        record, features = read_cached(root, row)
        target = None
        if features is not None:
            features["scalars"] = scalar_features(features)
            target, counts = reference_targets(row, record["prediction"])
            for key, value in counts.items():
                statistics[key] = statistics.get(key, 0) + value
        records.append({"row": row, "prediction": record["prediction"], "failure": record["failure"],
                        "features": features, "target": target})
    statistics["documents"] = len(records)
    statistics["failed_documents"] = sum(r["failure"] is not None for r in records)
    return records, statistics, manifest


def evaluate(records, head=None, include_decisions=False):
    cases, total_loss, total_sources = [], 0., 0
    for record in records:
        prediction, decisions = record["prediction"], []
        if head is not None and record["features"] is not None:
            with torch.inference_mode():
                loss, count = marginal_reference_loss(head(record["features"]), record["target"])
            total_loss += float(loss)
            total_sources += count
            prediction, decisions = rank_references(prediction, record["features"], head)
        case = {**assess_corpus_references(record["row"], prediction), "failure": record["failure"]}
        if include_decisions:
            case["decisions"] = decisions
        cases.append(case)
    summary = corpus_summary(cases)
    count = summary["all"]
    denominator = count["gold_pairs"] + count["predicted_pairs"]
    return {"summary": summary, "cases": cases,
            "pair_f1": 2 * count["correct_pairs"] / denominator if denominator else 0.,
            "mean_loss": total_loss / total_sources if total_sources else None}


def fit(train, dev, dimension, hidden, *, epochs=EPOCHS, batch_size=BATCH, evaluate_fn=evaluate):
    deterministic()
    head = ReferenceRanker(dimension, hidden)
    optimizer = torch.optim.AdamW(head.parameters(), lr=.001, weight_decay=.01)
    usable = [r for r in train if r["target"] is not None and bool(r["target"].any())]
    require(bool(usable), "No supervised reference training sources")
    best, history = None, []
    for epoch in range(1, epochs + 1):
        head.train()
        order = list(range(len(usable)))
        random.Random(17 + epoch).shuffle(order)
        total_loss, total_sources = 0., 0
        for start in range(0, len(order), batch_size):
            optimizer.zero_grad()
            losses, count = [], 0
            for index in order[start:start + batch_size]:
                r = usable[index]
                loss, sources = marginal_reference_loss(head(r["features"]), r["target"])
                if sources:
                    losses.append(loss)
                    count += sources
            if not count:
                continue
            loss = torch.stack(losses).sum() / count
            require(bool(torch.isfinite(loss)), "Non-finite reference training loss")
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach()) * count
            total_sources += count
        head.eval()
        assessment = evaluate_fn(dev, head)
        require(assessment["mean_loss"] is not None, "No supervised reference development sources")
        item = {"epoch": epoch, "train_loss": total_loss / total_sources, "dev_loss": assessment["mean_loss"],
                "dev_pair_f1": assessment["pair_f1"], "dev_summary": assessment["summary"]}
        history.append(item)
        key = (item["dev_pair_f1"], -item["dev_loss"], -epoch)
        if best is None or key > best["key"]:
            best = {"key": key, "epoch": epoch, "dev_loss": item["dev_loss"], "dev_pair_f1": item["dev_pair_f1"],
                    "state": {k: v.detach().clone() for k, v in head.state_dict().items()}}
        print("ranker", hidden, "epoch", epoch, "dev_f1", round(item["dev_pair_f1"], 6), "dev_loss", round(item["dev_loss"], 6), flush=True)
    head.load_state_dict(best["state"])
    choice = {"hidden": hidden, "epoch": best["epoch"], "dev_loss": best["dev_loss"], "dev_pair_f1": best["dev_pair_f1"],
              "parameters": sum(p.numel() for p in head.parameters())}
    return head.eval(), choice, history


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    require(not (args.report / "invalidated.json").exists(), "Reference ranker training invalidated: incorrect corpus head supervision")
    require(not (args.report / "selection.json").exists(), "Reference ranker selection already exists")
    deterministic()
    train, train_counts, manifest = load_split("train", args.root, args.report)
    dev, dev_counts, _ = load_split("dev", args.root, args.report)
    dimension = next(r["features"]["nodes"].shape[1] // 2 for r in train if r["features"] is not None)
    baseline = evaluate(dev)
    previous = json.loads(Path("reports/character-alignment-v1/evaluation.json").read_text(encoding="utf-8"))
    require(baseline["summary"] == previous["summary"], "Native reference baseline differs")
    heads, choices, weights, evaluations = {}, {}, {}, {"native": baseline}
    for name, hidden in ARCHITECTURES:
        head, choice, history = fit(train, dev, dimension, hidden)
        path = args.root / f"ranker-{name}.safetensors"
        require(not path.exists(), "Reference ranker weights already exist")
        save_file(head.state_dict(), str(path))
        heads[name], choices[name], weights[name] = head, choice, digest(path)
        evaluations[name] = evaluate(dev, head, include_decisions=True)
        write(args.report / f"history-{name}.json", history)
    selected = max(choices, key=lambda name: (choices[name]["dev_pair_f1"], -choices[name]["dev_loss"],
                                             -choices[name]["epoch"], name == "linear"))
    write(args.report / "development.json", evaluations)
    write(args.report / "selection.json", {"selected": selected, "dimension": dimension, "choices": choices,
          "weights_sha256": weights, "decision": "argmax_previous_or_none", "model": manifest["model"],
          "feature_manifest_sha256": digest(args.root / "manifest.json")})
    write(args.report / "training.json", {"code_sha256": {p: digest(p) for p in ("noema/reference_ranker.py", "noema/kwdlc_references.py", "scripts/train_reference_ranker.py")},
          "feature_reports_sha256": {s: digest(args.report / f"features-{s}.json") for s in ("train", "dev")},
          "protocol_sha256": digest("docs/reference-ranker-v1-protocol.md"), "train": train_counts, "dev": dev_counts,
          "seed": 17, "epochs": EPOCHS, "batch_documents": BATCH, "learning_rate": .001, "weight_decay": .01,
          "selection_sha256": digest(args.report / "selection.json")})
    print("Selected", selected, choices[selected], flush=True)


if __name__ == "__main__":
    main()
