import copy
import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
from noema.event_gate import EventGateHead, event_features, gate_targets, event_decisions, assess_gate, kept_frames
from noema.semantics import SemanticError


def sample():
    text = "A B C"
    tokens = [{"text": text[i:i + 1], "start": i, "end": i + 1} for i in (0, 2, 4)]
    phrases = [{"id": i, **token, "head": token, "features": {"用言": "動"} if i in (0, 2) else {}, "relations": []}
               for i, token in enumerate(tokens)]
    document = {"text": text, "complete_frames": True, "frames": [{"predicate": "A", "roles": [["patient", "B"]]}]}
    return document, {"text": text, "tokens": tokens, "phrases": phrases}


def test_partial_annotation_never_becomes_a_negative_event_example():
    document, prediction = sample()
    candidates, _ = event_features(prediction, torch.eye(3))
    assert gate_targets(document, candidates).tolist() == [1, 0]
    document["complete_frames"] = False
    assert gate_targets(document, candidates).tolist() == [1, -100]


def test_context_features_ignore_spelling_and_preserve_document_edges():
    _, prediction = sample()
    _, features = event_features(prediction, torch.eye(3))
    assert features.shape == (2, 18)
    assert features[0, 6:9].tolist() == [0., 0., 0.]
    assert features[0, 9:12].tolist() == [0., 1., 0.]
    assert features[1, 9:12].tolist() == [0., 0., 0.]
    changed = copy.deepcopy(prediction)
    changed["text"] = "X Y Z"
    for i, token in enumerate(changed["tokens"]):
        token["text"] = "XYZ"[i]
    for phrase in changed["phrases"]:
        phrase["text"] = phrase["head"]["text"] = "renamed"
    assert torch.equal(features, event_features(changed, torch.eye(3))[1])


def test_gold_event_loss_is_separate_from_upstream_missing_candidates():
    document, prediction = sample()
    decisions = [{"source": 0, "keep": False}, {"source": 2, "keep": True}]
    result = assess_gate(document, prediction, decisions)
    assert result["newly_lost_events"] == result["positive_rejected"] == result["negative_kept"] == 1
    assert result["upstream_misses"] == 0
    prediction["phrases"][0]["features"] = {}
    result = assess_gate(document, prediction, decisions[1:])
    assert result["newly_lost_events"] == 0 and result["upstream_misses"] == 1


def test_rejected_candidate_skips_role_inference_without_deleting_raw_evidence():
    _, prediction = sample()
    before = copy.deepcopy(prediction)
    decisions = [{"source": 0, "keep": False}, {"source": 2, "keep": False}]
    assert kept_frames(prediction, torch.eye(3), None, None, decisions) == []
    assert prediction == before
    with pytest.raises(SemanticError, match="decisions differ"):
        kept_frames(prediction, torch.eye(3), None, None, decisions[:1])


def test_empty_candidates_remain_empty_and_head_inventory_is_binary():
    _, prediction = sample()
    for phrase in prediction["phrases"]:
        phrase["features"] = {}
    head = EventGateHead(3, 4)
    candidates, features = event_features(prediction, torch.eye(3))
    assert not candidates and features.shape == (0, 18)
    assert head(features).shape == (0, 2)
    assert event_decisions(prediction, torch.eye(3), head) == []


def test_new_same_stem_cases_are_held_out_and_include_both_clause_structures():
    from scripts.train_mention_learning import DATA
    old = [r for p in DATA for r in json.loads(Path(p).read_text(encoding="utf-8")) if r["split"] in ("train", "dev")]
    nested = json.loads(Path("data/multi-frame-v5.json").read_text(encoding="utf-8"))
    old_families = {r["family"] for r in old} | {f["family"] for r in nested if r["split"] in ("train", "dev") for f in r["frames"]}
    new = json.loads(Path("data/event-gate-v6.json").read_text(encoding="utf-8"))
    assert len(new) == 12 and sum(len(r["frames"]) for r in new) == 16
    assert sum(len(f["roles"]) for r in new for f in r["frames"]) == 38
    assert not old_families & {f["family"] for r in new for f in r["frames"]}
    assert sum(len(r["frames"]) == 2 for r in new) == 4
    assert any("料理人" in r["text"] and "料理した" in r["text"] for r in new)
