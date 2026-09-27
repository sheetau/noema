"""Frozen raw-text SRL transfer trial. Partial requirements, not full semantics."""
import argparse
import ast
import json
from pathlib import Path

from noema.definition_probe import digest
from noema.srl_transfer import SRLTransfer


def overlaps(token, span):
    return token["start"] < span[1] and token["end"] > span[0]


def span(text, anchor):
    start = text.index(anchor)
    return start, start + len(anchor)


def assess(row, prediction):
    lang = prediction["language"]
    require_text = row[lang]
    if prediction["text"] != require_text:
        raise ValueError("Prediction text differs from evaluation text")
    clauses = [(s["tokens"], p) for s in prediction["sentences"] for p in s["inventories"]["EN"]]
    checks = []
    for gold in row["predicates"]:
        anchor = span(require_text, gold[lang])
        matching = [(tokens, p) for tokens, p in clauses if overlaps(tokens[p["token"]], anchor)]
        role_checks = []
        for label, ja, en in gold["roles"]:
            arg = span(require_text, ja if lang == "ja" else en)
            correct = any(r["label"] == label and overlaps(tokens[r["token"]], arg)
                          for tokens, p in matching for r in p["roles"])
            role_checks.append({"label": label, "span": arg, "correct": correct})
        checks.append({"span": anchor, "detected": bool(matching), "roles": role_checks,
                       "predicted_A0": any(r["label"] == "A0" for _, p in matching for r in p["roles"])})
    return {"id": row["id"], "language": lang, "checks": checks,
            "all_specified_checks": all(c["detected"] and all(r["correct"] for r in c["roles"]) for c in checks)}


def verify_upstream(probe, source):
    """Compare with the unchanged public forward function; no training imports."""
    import torch
    path = Path(source) / "srl/models/cross_lingual_model.py"
    if digest(path) != "9c71f5036ee7ddf87bfa978a7d77b310c94fbee72bbee02f612a7c2ed2c38a20":
        raise ValueError("Upstream reference source differs from the audited revision")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "CrossLingualModel")
    forward = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "forward")
    namespace = {"torch": torch}
    exec(compile(ast.Module(body=[forward], type_ignores=[]), str(path), "exec"), namespace)
    payload = probe.payload(["A", "dog", "chases", "a", "cat", "."])
    payload["predicate_indices"] = ([0, 0], [1, 2])
    deltas = {}
    with torch.inference_mode():
        for inv in ("EN", "VA"):
            payload["language"] = inv
            original = namespace["forward"](probe.model, payload, inv)
            current = probe.model.classify(probe.model.states(payload), inv, [1, 2])
            for key in ("predicates", "senses", "roles"):
                expected = original[key][0] if key == "predicates" else original[key]
                actual = current[key]
                torch.testing.assert_close(actual, expected, rtol=1e-5, atol=1e-6)
                deltas[inv + "/" + key] = float((actual - expected).abs().max())
    return {"source_file_sha256": digest(path), "max_absolute_logit_difference": deltas,
            "scope": "Original forward composition using identical frozen modules, two supplied predicate positions for adapter verification only"}


def frame_agreement(rows, predictions):
    lookup = {(r["id"], r["language"]): r for r in predictions}
    cases = []
    for row in rows:
        for gold in row["predicates"]:
            senses = {}
            for lang in ("ja", "en"):
                senses[lang] = [p["sense"] for s in lookup[row["id"], lang]["sentences"]
                                for p in s["inventories"]["VA"] if overlaps(s["tokens"][p["token"]], span(row[lang], gold[lang]))]
            cases.append({"id": row["id"], "anchors": {k: gold[k] for k in ("ja", "en")}, "frames": senses,
                          "single_equal": len(senses["ja"]) == len(senses["en"]) == 1 and senses["ja"] == senses["en"]})
    return {"scope": "post-hoc agreement, not frame correctness", "same": sum(r["single_equal"] for r in cases),
            "total": len(cases), "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/srl-transfer-v1.json")
    parser.add_argument("--output", default="reports/srl-transfer-v1")
    parser.add_argument("--source", default="artifacts/unify-srl-source")
    args = parser.parse_args()
    out = Path(args.output)
    if out.exists():
        raise ValueError("Refusing to overwrite probe results")
    out.mkdir(parents=True)
    def save(name, content):
        (out / name).write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    probe = SRLTransfer()
    save("adapter-verification.json", verify_upstream(probe, args.source))
    save("run.json", {**probe.metadata, "fixture_sha256": digest(args.input), "code_sha256": digest("noema/srl_transfer.py")})
    predictions, assessment = [], []
    repeat_equal = True
    rows = json.loads(Path(args.input).read_text(encoding="utf-8"))
    for row in rows:
        for lang in ("ja", "en"):
            result = probe.analyze(row[lang], lang)
            repeat_equal &= result == probe.analyze(row[lang], lang)
            predictions.append({"id": row["id"], **result})
            assessment.append(assess(row, result))
            print(row["id"], lang, assessment[-1]["all_specified_checks"], flush=True)
    save("frame-agreement.json", frame_agreement(rows, predictions))
    summary = {"repeat_equal": repeat_equal, "scope": "Partial predicate and argument checks; not precision or full meaning exact match", "languages": {}}
    for lang in ("ja", "en"):
        rows = [r for r in assessment if r["language"] == lang]
        checks = [c for r in rows for c in r["checks"]]
        roles = [role for c in checks for role in c["roles"]]
        summary["languages"][lang] = {"documents": len(rows), "all_specified_checks": sum(r["all_specified_checks"] for r in rows),
                                       "predicates_expected": len(checks), "predicates_detected": sum(c["detected"] for c in checks),
                                       "roles_expected": len(roles), "roles_correct": sum(r["correct"] for r in roles),
                                       "omitted_subject_filled": next(r for r in rows if r["id"] == "omission")["checks"][0]["predicted_A0"]}
    save("predictions.json", predictions)
    save("assessment.json", assessment)
    save("summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
