import itertools
import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
from noema.mention_scope import (TAGS, MentionHead, mention_targets, decode_mentions,
                                 mention_candidates, scope_targets, assess_scope)
from noema.role_transfer import LABELS, UNLINKED
from noema.semantics import SemanticError


def document():
    text = "A BC D"
    tokens = [{"text": text[a:b], "start": a, "end": b} for a, b in ((0, 1), (2, 3), (3, 4), (5, 6))]
    phrases = [{"id": i, **token, "head": token, "features": {"用言": "動"} if i == 0 else {}, "relations": []}
               for i, token in enumerate(tokens)]
    phrases[0]["relations"] = [{"label": "first", "target_phrase": 1}, {"label": "second", "target_phrase": 2},
                                {"label": "first", "target_phrase": None, "external": "writer"}]
    return {"text": text, "tokens": tokens, "phrases": phrases}


def row():
    return {"id": "synthetic-a", "split": "test", "family": "synthetic", "text": "A BC D",
            "predicate": "A", "roles": [["agent", "BC"]]}


def test_gold_boundaries_are_not_rounded():
    prediction = document()
    assert mention_targets(row(), prediction["tokens"]).tolist() == [0, 1, 2, 0]
    merged = [prediction["tokens"][0], {"text": "BC D", "start": 2, "end": 6}]
    with pytest.raises(SemanticError, match="not aligned"):
        mention_targets(row(), merged)


def test_decode_is_global_log_probability_bio_and_preserves_source():
    prediction = document()
    probabilities = torch.tensor([[.30, .05, .65], [.30, .35, .35], [.20, .10, .70], [.80, .10, .10]])
    scores = probabilities.log()
    valid = [path for path in itertools.product(range(3), repeat=4)
             if path[0] != 2 and all(current != 2 or previous in (1, 2) for previous, current in zip(path, path[1:]))]
    best = max(valid, key=lambda path: sum(float(scores[i, label]) for i, label in enumerate(path)))
    assert best == (0, 1, 2, 0)
    assert decode_mentions(prediction["text"], prediction["tokens"], scores) == [
        {"id": 0, "start": 2, "end": 4, "text": "BC"}]
    assert decode_mentions("", [], torch.empty(0, 3)) == []


def test_compound_is_one_candidate_with_all_linked_cases():
    prediction = document()
    mentions = [{"id": 5, "start": 2, "end": 4, "text": "BC"}, {"id": 6, "start": 5, "end": 6, "text": "D"}]
    pairs, features = mention_candidates(prediction, torch.eye(4), mentions, ("first", "second", UNLINKED))
    assert pairs == [{"source": 0, "target": 5, "native_cases": ["first", "second"]},
                     {"source": 0, "target": 6, "native_cases": []}]
    assert features[:, -3:].tolist() == [[1., 1., 0.], [0., 0., 1.]]
    assert torch.allclose(features[0, 4:8], torch.tensor([0., 2 ** -.5, 2 ** -.5, 0.]))
    assert scope_targets(row(), prediction, mentions, pairs).tolist() == [LABELS.index("agent"), 0]


def test_partial_span_is_not_correct_role_and_extra_prevents_exactness():
    prediction = document()
    mentions = [{"id": 5, "start": 3, "end": 4, "text": "C"}]
    pairs, _ = mention_candidates(prediction, torch.eye(4), mentions, ("first", "second", UNLINKED))
    assert scope_targets(row(), prediction, mentions, pairs).tolist() == [0]
    result = assess_scope(row(), prediction, mentions, pairs, [LABELS.index("agent")])
    assert result["exact_mentions"] == result["exact_roles"] == 0
    assert result["extra_roles"] == result["missing_roles"] == 1
    assert not result["annotated_frame_exact"]


def test_empty_predictions_report_misses_and_other_events_have_no_supervision():
    prediction = document()
    pairs, features = mention_candidates(prediction, torch.eye(4), [], ("first", UNLINKED))
    assert not pairs and features.shape == (0, 22)
    result = assess_scope(row(), prediction, [], [], [])
    assert result["missing_roles"] == 1 and result["extra_roles"] == 0
    prediction["phrases"][3]["features"] = {"用言": "動"}
    mentions = [{"id": 0, "start": 2, "end": 4, "text": "BC"}]
    pairs, _ = mention_candidates(prediction, torch.eye(4), mentions, ("first", UNLINKED))
    assert scope_targets(row(), prediction, mentions, pairs).tolist() == [LABELS.index("agent"), -100]


def test_head_output_inventory_does_not_depend_on_word_count():
    head = MentionHead(4, 8)
    assert head(torch.randn(1, 4)).shape == (1, len(TAGS))
    assert head(torch.randn(30, 4)).shape == (30, len(TAGS))


def test_new_confirmation_is_disjoint_and_has_compound_mentions():
    old = [r for path in ("data/role-transfer-v1.json", "data/role-candidates-v2.json")
           for r in json.loads(Path(path).read_text(encoding="utf-8"))]
    new = json.loads(Path("data/mention-scope-v1.json").read_text(encoding="utf-8"))
    assert len(new) == 8 and sum(len(r["roles"]) for r in new) == 20
    assert not ({r["family"] for r in old} & {r["family"] for r in new})
    assert not ({r["text"] for r in old} & {r["text"] for r in new})
    assert any("の" in surface for r in new for _, surface in r["roles"])
