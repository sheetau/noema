"""Compare learned argument spans with frozen bilingual partial annotations."""
import argparse
import ast
import json
from pathlib import Path
from types import SimpleNamespace

from noema.definition_probe import digest
from noema.srl_transfer import SRLTransfer
from noema.srl_spans import FrozenSpanSRL, bio_potentials
from scripts.probe_srl_transfer import span, overlaps


def assess_spans(row, prediction):
    lang = prediction["language"]
    if prediction["text"] != row[lang]:
        raise ValueError("Prediction source differs from annotation")
    all_spans = [(s["tokens"], p) for s in prediction["sentences"] for p in s["span_annotations"]]
    checks = []
    for gold in row["predicates"]:
        anchor = span(row[lang], gold[lang])
        matched = [(t, p) for t, p in all_spans if overlaps(t[p["predicate_token"]], anchor)]
        outputs = [p for _, p in matched if p["status"] == "valid_bio"]
        roles = []
        for label, ja, en in gold["roles"]:
            expected = span(row[lang], ja if lang == "ja" else en)
            exact = any(s["label"] == label and (s["start"], s["end"]) == expected for p in outputs for s in p["spans"])
            covered = any(s["label"] == label and s["start"] <= expected[0] and s["end"] >= expected[1] for p in outputs for s in p["spans"])
            roles.append({"label": label, "expected": expected, "exact": exact, "covered": covered})
        checks.append({"anchor": anchor, "detected": bool(matched), "roles": roles,
                       "invalid_bio": any(p["status"] != "valid_bio" for _, p in matched),
                       "predicted_A0": any(s["label"] == "A0" for p in outputs for s in p["spans"])})
    return {"id": row["id"], "language": lang, "checks": checks,
            "all_specified_exact": all(c["detected"] and not c["invalid_bio"] and all(r["exact"] for r in c["roles"]) for c in checks)}


def verify_reference(model, source):
    """Run audited public preprocessing, constraints and forward on shared weights."""
    import torch
    import torch.nn.functional as F
    import typing
    source = Path(source)
    env = {"torch": torch, "List": typing.List, "Tuple": typing.Tuple, "Dict": typing.Dict,
           "Any": typing.Any, "TextFieldTensors": dict, "F": F,
           "get_text_field_mask": lambda tokens: tokens["attention_mask"],
           "util": SimpleNamespace(get_token_ids_from_text_field_tensors=lambda tokens: tokens["input_ids"])}
    for file, cls, methods in (("my_reader.py", "SrlReader", ["_wordpiece_tokenize_input"]),
                               ("my_model.py", "SrlMyModel", ["forward", "get_viterbi_pairwise_potentials", "get_start_transitions"])):
        expected = {"my_reader.py": "148e327255d84c72a4fd5500b71698fb1e3aa96f6297419036b6714216372084",
                    "my_model.py": "ebd386612297f85152ad96040b8fb7a7c2eb82f7201f510e3698d763f9302fa6"}[file]
        if digest(source / file) != expected:
            raise ValueError("Unaudited upstream reference source")
        tree = ast.parse((source / file).read_text(encoding="utf-8"))
        klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
        selected = [n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name in methods]
        for n in selected:
            n.decorator_list = []
        exec(compile(ast.Module(body=selected, type_ignores=[]), file, "exec"), env)
    words = ["A", "multilingual", "researcher", "retested", "devices", "."]
    reader = SimpleNamespace(xlm=True, bert_tokenizer=model.tokenizer)
    pieces, ends, starts = env["_wordpiece_tokenize_input"](reader, words)
    encoded, own_starts, own_ends = model.encode(words, 3)
    ids = model.tokenizer.convert_tokens_to_ids([model.tokenizer.cls_token] + pieces + [model.tokenizer.sep_token])
    assert ids == encoded["input_ids"][0].tolist() and ends == own_ends and starts == own_starts
    expected_indicator = [0] * len(ids)
    expected_indicator[starts[3]:ends[3] + 1] = [1] * (ends[3] - starts[3] + 1)
    assert expected_indicator == encoded["token_type_ids"][0].tolist()
    reference = SimpleNamespace(bert_model=model.model, embedding_dropout=torch.nn.Identity(),
                                tag_projection_layer=model.classifier, num_classes=len(model.labels),
                                vocab=SimpleNamespace(get_index_to_token_vocabulary=lambda _: dict(enumerate(model.labels))))
    transitions, begin = bio_potentials(model.labels)
    assert torch.equal(transitions, env["get_viterbi_pairwise_potentials"](reference))
    assert torch.equal(begin, env["get_start_transitions"](reference))
    with torch.inference_mode():
        original = env["forward"](reference, encoded, encoded["token_type_ids"], [{"words": words, "verb": words[3], "offsets": starts}])
        current = model.classifier(model.model(**encoded).last_hidden_state)
    torch.testing.assert_close(current, original["logits"], rtol=0, atol=0)
    return {"wordpieces_offsets_indicators_equal": True, "bio_constraints_equal": True,
            "max_absolute_logit_difference": float((current - original["logits"]).abs().max()),
            "scope": "Audited upstream preprocessing and forward using identical frozen Transformer and head modules; not the old full runtime"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/srl-span-v1")
    args = parser.parse_args()
    out = Path(args.output)
    if out.exists():
        raise ValueError("Refusing to overwrite span trial results")
    out.mkdir(parents=True)
    def save(name, data):
        (out / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    detector, model = SRLTransfer(), FrozenSpanSRL()
    save("compatibility.json", verify_reference(model, "artifacts/span-srl-source"))
    save("run.json", {"predicate_detector": detector.metadata, "span_model": model.metadata,
                      "fixture_sha256": digest("data/srl-span-v1.json"), "adapter_sha256": digest("noema/srl_spans.py"),
                      "gold_predicates": False})
    rows = json.loads(Path("data/srl-span-v1.json").read_text(encoding="utf-8"))
    old_rows = {r["id"]: r for r in json.loads(Path("data/srl-transfer-v1.json").read_text(encoding="utf-8"))}
    predictions, assessments, content_checks = [], [], []
    repeated = True
    for row in rows:
        for lang in ("ja", "en"):
            base = detector.analyze(row[lang], lang)
            prediction = model.annotate(base)
            repeated &= prediction == model.annotate(base)
            predictions.append({"id": row["id"], **prediction})
            assessments.append(assess_spans(row, prediction))
            content_checks.append(assess_spans(old_rows[row["id"]], prediction))
            print(row["id"], lang, assessments[-1]["all_specified_exact"], flush=True)
    summary = {"scope": "Partial specified spans, not full semantic graph accuracy", "repeat_equal": repeated, "languages": {}}
    for lang in ("ja", "en"):
        cases = [c for c in assessments if c["language"] == lang]
        checks = [c for case in cases for c in case["checks"]]
        roles = [r for c in checks for r in c["roles"]]
        content = [r for case in content_checks if case["language"] == lang for c in case["checks"] for r in c["roles"]]
        summary["languages"][lang] = {"documents": len(cases), "all_specified_exact": sum(c["all_specified_exact"] for c in cases),
                                       "roles_expected": len(roles), "roles_exact": sum(r["exact"] for r in roles),
                                       "roles_covered": sum(r["covered"] for r in roles),
                                       "previous_content_checks": len(content), "previous_content_covered": sum(r["covered"] for r in content),
                                       "invalid_bio_annotations": sum(p["status"] != "valid_bio" for doc in predictions if doc["language"] == lang for s in doc["sentences"] for p in s["span_annotations"]),
                                       "omitted_subject_filled": next(c for c in cases if c["id"] == "omission")["checks"][0]["predicted_A0"]}
    save("predictions.json", predictions)
    save("assessment.json", assessments)
    save("content-checks.json", content_checks)
    save("summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
