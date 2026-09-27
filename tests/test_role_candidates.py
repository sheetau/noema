import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
from noema.role_transfer import UNLINKED, LABELS, RoleHead, candidates, all_phrase_candidates, targets
from scripts.train_role_candidates import evaluate_strict


def document():
    return {"text": "A B C", "tokens": [
        {"text": "A", "start": 0, "end": 1}, {"text": "B", "start": 2, "end": 3}, {"text": "C", "start": 4, "end": 5}],
        "phrases": [
            {"id": 0, "start": 0, "end": 1, "head": {"start": 0, "end": 1}, "features": {"用言": "動"}, "relations": [
                {"label": "case", "target_phrase": 1}, {"label": "case", "target_phrase": None, "external": "writer"}]},
            {"id": 1, "start": 2, "end": 3, "head": {"start": 2, "end": 3}, "features": {"体言": True}, "relations": []},
            {"id": 2, "start": 4, "end": 5, "head": {"start": 4, "end": 5}, "features": {"体言": True}, "relations": []}]}


def test_unlinked_phrase_is_compared_without_becoming_an_external_entity():
    prediction = document()
    native, nf = candidates(prediction, torch.eye(3), ("case",))
    pairs, features = all_phrase_candidates(prediction, torch.eye(3), ("case", UNLINKED))
    assert [(p["source"], p["target"]) for p in pairs] == [(0, 1), (0, 2)]
    assert pairs[1]["native_cases"] == []
    assert features[:, -2:].tolist() == [[1., 0.], [0., 1.]]
    assert torch.equal(features[0, :-1], nf[0])
    assert len(native) == 1
    assert all(p["source"] != p["target"] for p in pairs)


def test_multiple_cases_are_features_of_one_pair():
    prediction = document()
    prediction["phrases"][0]["relations"].append({"label": "second", "target_phrase": 1})
    pairs, features = all_phrase_candidates(prediction, torch.eye(3), ("case", "second", UNLINKED))
    assert len(pairs) == 2
    assert features[0, -3:].tolist() == [1., 1., 0.]
    prediction["phrases"][0]["features"] = {}
    pairs, features = all_phrase_candidates(prediction, torch.eye(3), ("case", "second", UNLINKED))
    assert not pairs and features.shape == (0, 18)


def test_extra_role_prevents_annotated_frame_exactness():
    prediction = document()
    pairs, features = all_phrase_candidates(prediction, torch.eye(3), ("case", UNLINKED))
    row = {"id": "synthetic-a", "split": "test", "family": "synthetic", "text": prediction["text"],
           "predicate": "A", "roles": [["agent", "B"]]}
    head = RoleHead(3, ("case", UNLINKED))
    with torch.no_grad():
        head.network.weight.zero_()
        head.network.bias.zero_()
        head.network.bias[LABELS.index("agent")] = 5
    example = {"row": row, "prediction": prediction, "pairs": pairs, "features": features,
               "targets": targets(row, prediction, pairs)}
    result = evaluate_strict([example], head)
    assert result["cases"][0]["all_specified_correct"]
    assert not result["cases"][0]["annotated_frame_exact"]
    assert result["summary"]["extra_roles"] == 1


def test_confirmation_predicates_are_held_out_from_all_old_splits():
    old = json.loads(Path("data/role-transfer-v1.json").read_text(encoding="utf-8"))
    new = json.loads(Path("data/role-candidates-v2.json").read_text(encoding="utf-8"))
    assert len(new) == 16 and len({r["family"] for r in new}) == 8
    assert not ({r["family"] for r in old} & {r["family"] for r in new})
    assert not ({r["text"] for r in old} & {r["text"] for r in new})
