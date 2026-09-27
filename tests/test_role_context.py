import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
from noema.role_context import ContextRoleHead, context_candidates
from noema.role_transfer import UNLINKED
from noema.mention_scope import mention_candidates
from noema.semantics import SemanticError


def document():
    text = "A B C"
    tokens = [{"text": text[a:b], "start": a, "end": b} for a, b in ((0, 1), (2, 3), (4, 5))]
    phrases = [{"id": i, **token, "head": token, "features": {"用言": "動"} if i == 0 else {}, "relations": []}
               for i, token in enumerate(tokens)]
    return {"text": text, "tokens": tokens, "phrases": phrases}


def test_context_changes_features_without_extending_meaning_span():
    prediction = document()
    mentions = [{"id": 9, "text": "B", "start": 2, "end": 3}]
    original = [dict(m) for m in mentions]
    vectors = torch.eye(3)
    pairs, features = context_candidates(prediction, vectors, mentions, (UNLINKED,))
    expected_pairs, base = mention_candidates(prediction, vectors, mentions, (UNLINKED,))
    assert pairs == expected_pairs and mentions == original
    assert torch.equal(features[:, :16], base)
    assert features[0, 16:].tolist() == [0., 1., 0., 0., 0., 1., 0., 0., 0., 1., 0., -1.]
    changed = vectors.clone()
    changed[2] = torch.tensor([1., 0., 0.])
    _, alternative = context_candidates(prediction, changed, mentions, (UNLINKED,))
    assert torch.equal(features[:, :16], alternative[:, :16])
    assert not torch.equal(features[:, 16:], alternative[:, 16:])


def test_end_of_text_uses_zero_neighbor_and_empty_candidates_keep_width():
    prediction = document()
    mentions = [{"id": 0, "text": "C", "start": 4, "end": 5}]
    _, features = context_candidates(prediction, torch.eye(3), mentions, (UNLINKED,))
    assert features[0, 19:22].tolist() == [0., 0., 0.]
    pairs, empty = context_candidates(prediction, torch.eye(3), [], (UNLINKED,))
    assert not pairs and empty.shape == (0, 28)
    assert ContextRoleHead(3, (UNLINKED,))(empty).shape == (0, 5)


def test_mean_mode_preserves_baseline_and_token_interior_is_rejected():
    prediction = document()
    mentions = [{"id": 0, "text": "B", "start": 2, "end": 3}]
    _, features = context_candidates(prediction, torch.eye(3), mentions, (UNLINKED,), "mean")
    _, expected = mention_candidates(prediction, torch.eye(3), mentions, (UNLINKED,))
    assert torch.equal(features, expected)
    with pytest.raises(SemanticError, match="Invalid contextual role features"):
        ContextRoleHead(3, (UNLINKED,), features="boundary")(features)
    prediction["tokens"][1] = {"text": "B C", "start": 2, "end": 5}
    prediction["tokens"] = prediction["tokens"][:2]
    prediction["phrases"] = prediction["phrases"][:2]
    with pytest.raises(SemanticError, match="inside a source token"):
        context_candidates(prediction, torch.eye(2), mentions, (UNLINKED,))


def test_new_predicates_are_separate_and_voices_preserve_role_annotations():
    from scripts.train_mention_learning import DATA
    old = [r for p in DATA for r in json.loads(Path(p).read_text(encoding="utf-8"))]
    new = json.loads(Path("data/role-context-v3.json").read_text(encoding="utf-8"))
    assert len(new) == 8 and sum(len(r["roles"]) for r in new) == 24
    assert not ({r["family"] for r in old} & {r["family"] for r in new})
    for family in {r["family"] for r in new}:
        pair = [r for r in new if r["family"] == family]
        assert len(pair) == 2 and sorted(pair[0]["roles"]) == sorted(pair[1]["roles"])


def test_error_audit_distinguishes_missing_rejected_and_wrong_role():
    from scripts.audit_role_context import audit
    prediction = document()
    example = {"row": {"id": "test", "text": "A B C", "predicate": "A", "roles": [["agent", "B"], ["patient", "C"]]},
               "prediction": prediction, "mentions": [{"id": 0, "start": 2, "end": 3, "text": "B"}]}
    def evaluated(role):
        return {"model": {"test": {"summary": {"gold_roles": 2, "exact_roles": 0},
                "cases": [{"id": "test", "outputs": [{"source": 0, "target": 0, "role": role}]}]}}}
    result = audit([example], evaluated("none"))["model"]["test"]["summary"]
    assert result == {"correct": 0, "absent_candidate": 1, "rejected": 1, "wrong_role": 0}
    result = audit([example], evaluated("patient"))["model"]["test"]["summary"]
    assert result == {"correct": 0, "absent_candidate": 1, "rejected": 0, "wrong_role": 1}
