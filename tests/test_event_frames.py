import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
from noema.event_frames import (conditioned_vectors, scoped_candidates, supervised_frames, assess_document)
from noema.role_transfer import UNLINKED
from scripts.train_event_frames import connected_folds


def sample():
    text = "A B C D"
    tokens = [{"text": text[i:i + 1], "start": i, "end": i + 1} for i in (0, 2, 4, 6)]
    phrases = [{"id": i, **t, "head": t, "features": {"用言": "動"} if i in (0, 2) else {}, "relations": []}
               for i, t in enumerate(tokens)]
    row = {"id": "nested", "split": "train", "text": text, "complete_frames": True, "frames": [
        {"predicate": "A", "family": "outer", "roles": [["patient", "B C D"]]},
        {"predicate": "C", "family": "inner", "roles": [["patient", "D"]]}]}
    return {"document": row, "prediction": {"text": text, "tokens": tokens, "phrases": phrases}, "vectors": torch.eye(4)}


def expected_frames():
    return [{"source": 0, "mentions": [{"id": 0, "text": "B C D", "start": 2, "end": 7}],
             "roles": [{"source": 0, "target": 0, "role": "patient"}]},
            {"source": 2, "mentions": [{"id": 0, "text": "D", "start": 6, "end": 7}],
             "roles": [{"source": 2, "target": 0, "role": "patient"}]}]


def test_overlapping_scopes_have_distinct_predicate_conditioned_sequences():
    document = sample()
    examples = supervised_frames([document])
    assert len(examples) == 2
    assert examples[0]["tags"].tolist() == [0, 1, 2, 2]
    assert examples[1]["tags"].tolist() == [0, 0, 0, 1]
    assert torch.equal(examples[0]["vectors"][:, :4], examples[1]["vectors"][:, :4])
    assert not torch.equal(examples[0]["vectors"][:, 4:], examples[1]["vectors"][:, 4:])
    assert examples[0]["vectors"].shape == (4, 20)


def test_role_candidates_stay_with_their_predicate():
    d = sample()
    for source, expected in ((d["prediction"]["phrases"][0], 0), (d["prediction"]["phrases"][2], 2)):
        pairs, features = scoped_candidates(d["prediction"], d["vectors"], source, expected_frames()[0]["mentions"], (UNLINKED,))
        assert len(pairs) == 1 and pairs[0]["source"] == expected
        assert features.shape == (1, 37)


def test_evaluation_preserves_overlap_and_penalizes_cross_event_roles():
    d = sample()
    frames = expected_frames()
    result = assess_document(d["document"], d["prediction"], frames)
    assert result["document_exact"] and result["exact_roles"] == result["exact_spans"] == 2
    frames[1]["mentions"] = frames[0]["mentions"]
    result = assess_document(d["document"], d["prediction"], frames)
    assert not result["document_exact"] and result["exact_roles"] == 1
    assert result["missing_roles"] == result["extra_roles"] == 1


def test_duplicates_and_unannotated_events_are_not_silently_accepted():
    d = sample()
    frames = expected_frames()
    result = assess_document(d["document"], d["prediction"], frames + [frames[0]])
    assert result["duplicate_roles"] == result["extra_roles"] == 1
    assert not result["document_exact"] and result["frames_exact"] == 1
    partial = {**d["document"], "frames": d["document"]["frames"][:1], "complete_frames": False}
    assert assess_document(partial, d["prediction"], frames)["document_exact"]
    partial["complete_frames"] = True
    assert assess_document(partial, d["prediction"], frames)["extra_roles"] == 1


def test_missing_predicate_is_reported_and_never_injected_for_training():
    d = sample()
    d["prediction"]["phrases"][2]["features"] = {}
    assert len(supervised_frames([d])) == 1
    result = assess_document(d["document"], d["prediction"], expected_frames()[:1])
    assert result["detected_frames"] == 1 and result["gold_frames"] == 2 and result["missing_roles"] == 1


def test_connected_fold_assignment_keeps_shared_families_together():
    rows = [{"document": {"id": str(i), "frames": [{"family": f} for f in families]}}
            for i, families in enumerate((("a", "b"), ("b", "c"), ("c",), ("d",), ("e",), ("f",)))]
    folds = connected_folds(rows)
    assert len({folds["family_folds"][f] for f in ("a", "b", "c")}) == 1
    assert len({folds["document_folds"][str(i)] for i in (0, 1, 2)}) == 1
    assert len(set(folds["family_folds"].values())) == 4


def test_multi_frame_corpus_has_held_out_predicates_and_nested_roles():
    from scripts.train_mention_learning import DATA
    old = [r for path in DATA for r in json.loads(Path(path).read_text(encoding="utf-8")) if r["split"] in ("train", "dev")]
    new = json.loads(Path("data/multi-frame-v5.json").read_text(encoding="utf-8"))
    groups = {split: {f["family"] for r in new if r["split"] == split for f in r["frames"]} for split in ("train", "dev", "frame_confirmation")}
    groups["train"].update(r["family"] for r in old if r["split"] == "train")
    groups["dev"].update(r["family"] for r in old if r["split"] == "dev")
    assert not groups["train"] & groups["dev"] and not groups["frame_confirmation"] & (groups["train"] | groups["dev"])
    assert len(new) == 28 and all(len(r["frames"]) == 2 for r in new)
    assert len([r for r in new if r["split"] == "frame_confirmation"]) == 8
