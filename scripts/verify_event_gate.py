"""Reproduce event gate training and ensure retained frame outputs are unchanged."""
import json
from pathlib import Path

import torch
from safetensors.torch import load_file

from noema.definition_probe import digest
from noema.event_frames import predict_frames
from noema.event_gate import GatedEventFrameAnalyzer
from noema.mention_scope import mention_targets
from scripts.train_event_gate import (DATA, PREVIOUS, ARCHITECTURES, cached_documents,
    fit, groups, evaluate, forbidden_paths)


def main():
    root, artifacts = Path("reports/event-gate-v6"), Path("artifacts/event-gate-v6")
    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    selection, run, expected = read("selection.json"), read("run.json"), read("evaluation.json")
    for group in ("code_sha256", "previous_files_sha256"):
        assert all(digest(p) == sha for p, sha in run[group].items()), group
    assert digest(DATA) == run["fixture_sha256"]
    assert digest(artifacts / "new-vectors.safetensors") == run["new_vectors_sha256"]
    documents, frame_heads, previous_selection, _ = cached_documents()
    old_evaluation = json.loads((PREVIOUS / "evaluation.json").read_text(encoding="utf-8"))[previous_selection["role"]["selected"]]
    vectors = load_file(str(artifacts / "new-vectors.safetensors"))
    rows = {r["id"]: r for r in json.loads(Path(DATA).read_text(encoding="utf-8"))}
    for d in read("evidence.json"):
        row = d["document"]
        assert row == {**rows[row["id"]], "complete_frames": True}
        for frame in row["frames"]:
            mention_targets({**frame, "text": row["text"]}, d["prediction"]["tokens"])
        documents.append({**d, "vectors": vectors[row["id"]]})
    raw_frames = {d["document"]["id"]: predict_frames(d["prediction"], d["vectors"], frame_heads["mention"], frame_heads["role"]) for d in documents}
    checks = {}
    for name, hidden in ARCHITECTURES:
        head, choice, history = fit(documents, selection["dimension"], hidden)
        path = artifacts / f"gate-{name}.safetensors"
        assert digest(path) == selection["weights_sha256"][name]
        weights = load_file(str(path))
        assert head.state_dict().keys() == weights.keys()
        assert all(torch.equal(value, weights[key]) for key, value in head.state_dict().items())
        assert choice == selection["choices"][name] and history == read(f"gate-{name}-history.json")
        for group, ds in groups(documents).items():
            assert evaluate(ds, raw_frames, head) == expected[name][group]
        checks[name] = {"weights_equal": True, "history_equal": True, "all_evaluation_equal": True}
    for group, ds in groups(documents).items():
        actual = evaluate(ds, raw_frames)
        assert actual == expected["ungated"][group]
        if group in old_evaluation:
            assert {k: v for k, v in actual["summary"].items() if k != "gate"} == old_evaluation[group]["summary"]
            for current, previous in zip(actual["cases"], old_evaluation[group]["cases"], strict=True):
                assert {k: v for k, v in current.items() if k not in ("gate", "event_decisions")} == previous
    checks["ungated_pipeline_exactly_matches_previous"] = True
    by_id, matches = {d["document"]["id"]: d for d in documents}, []
    with forbidden_paths() as guards:
        analyzer = GatedEventFrameAnalyzer(str(root), str(artifacts))
        for case in expected[selection["selected"]]["multi_gate_confirmation"]["cases"]:
            d = by_id[case["id"]]
            actual = analyzer.analyze(d["document"]["text"])
            assert actual["analysis"] == d["prediction"]
            assert actual["event_decisions"] == case["event_decisions"] and actual["frames"] == case["frames"]
            assert actual == analyzer.analyze(d["document"]["text"])
            matches.append(case["id"])
        checks["forbidden_path_calls"] = [g.call_count for g in guards]
    checks["raw_api_equal_and_repeated"] = matches
    with (root / "verification.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(checks, indent=2) + "\n")
    print("Verified both gate training runs, frozen frame equivalence, and", len(matches), "fresh repeated text cases")


if __name__ == "__main__":
    main()
