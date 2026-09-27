"""Compare published and whole-word SRL decoding on identical frozen scores."""
import argparse
import json
from pathlib import Path

from noema.definition_probe import digest
from noema.srl_transfer import SRLTransfer
from noema.srl_spans import FrozenSpanSRL
from scripts.probe_srl_spans import assess_spans, verify_reference

DECODERS = ("published", "word_boundary")
FIXTURES = {"regression": "data/srl-span-v1.json", "new": "data/srl-boundary-v1.json"}


def annotate_variants(model, base):
    sentences = {name: [] for name in DECODERS}
    for sentence in base["sentences"]:
        annotations = {name: [] for name in DECODERS}
        for predicate in sentence["inventories"]["EN"]:
            variants = model.predict_variants(base["text"], sentence["tokens"], predicate["token"])
            for name in DECODERS:
                annotations[name].append(variants[name])
        for name in DECODERS:
            sentences[name].append({**sentence, "span_annotations": annotations[name]})
    return {name: {**base, "status": "research_span_annotation", "sentences": sentences[name]} for name in DECODERS}


def summarize(assessments, predictions):
    result = {}
    for dataset in FIXTURES:
        result[dataset] = {}
        for lang in ("ja", "en"):
            cases = [c for c in assessments if c["dataset"] == dataset and c["language"] == lang]
            docs = [p for p in predictions if p["dataset"] == dataset and p["language"] == lang]
            language = {"documents": len(cases), "decoders": {}}
            paired = []
            for case in cases:
                left = case["decoders"]["published"]["checks"]
                right = case["decoders"]["word_boundary"]["checks"]
                for a, b in zip(left, right, strict=True):
                    for ar, br in zip(a["roles"], b["roles"], strict=True):
                        assert ar["label"] == br["label"] and ar["expected"] == br["expected"]
                        paired.append((ar["exact"], br["exact"]))
            language.update(roles_expected=len(paired), improved=sum(not a and b for a, b in paired),
                            regressed=sum(a and not b for a, b in paired))
            for name in DECODERS:
                checks = [c for case in cases for c in case["decoders"][name]["checks"]]
                annotations = [a for doc in docs for s in doc["decoders"][name]["sentences"] for a in s["span_annotations"]]
                language["decoders"][name] = {
                    "roles_exact": sum(r["exact"] for c in checks for r in c["roles"]),
                    "all_specified_exact": sum(c["decoders"][name]["all_specified_exact"] for c in cases),
                    "predicate_annotations": len(annotations),
                    "invalid_bio_annotations": sum(a["status"] != "valid_bio" for a in annotations),
                    "omitted_subject_filled": any(c["predicted_A0"] for case in cases
                        if case["id"] in ("omission", "omitted-translator") for c in case["decoders"][name]["checks"])}
            result[dataset][lang] = language
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/srl-boundary-v1")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    detector, model = SRLTransfer(), FrozenSpanSRL()
    save("compatibility.json", verify_reference(model, "artifacts/span-srl-source"))
    save("run.json", {"predicate_detector": detector.metadata, "span_model": model.metadata,
                      "decoders": {"published": "subword BIO then first tag per word",
                                   "word_boundary": "whole-word BIO; sum of expanded subword probabilities; specials O"},
                      "fixture_sha256": {k: digest(v) for k, v in FIXTURES.items()},
                      "adapter_sha256": digest("noema/srl_spans.py"),
                      "probe_sha256": digest(__file__), "gold_predicates": False})
    prior = {(p["id"], p["language"]): p for p in json.loads(Path("reports/srl-span-v1/predictions.json").read_text(encoding="utf-8"))}
    predictions, assessments = [], []
    repeated, prior_equal = True, True
    for dataset, path in FIXTURES.items():
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
        for row in rows:
            for lang in ("ja", "en"):
                base = detector.analyze(row[lang], lang)
                variants = annotate_variants(model, base)
                repeated &= variants == annotate_variants(model, base)
                if dataset == "regression":
                    prior_equal &= {"id": row["id"], **variants["published"]} == prior[row["id"], lang]
                predictions.append({"dataset": dataset, "id": row["id"], "language": lang, "decoders": variants})
                assessments.append({"dataset": dataset, "id": row["id"], "language": lang,
                                    "decoders": {name: assess_spans(row, variants[name]) for name in DECODERS}})
                print(dataset, row["id"], lang, flush=True)
    summary = {"scope": "Partial specified argument spans; not full semantic graph accuracy",
               "repeat_equal": repeated, "prior_published_equal": prior_equal,
               "datasets": summarize(assessments, predictions)}
    save("predictions.json", predictions)
    save("assessment.json", assessments)
    save("summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
