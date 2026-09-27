import copy
import math

import pytest

torch = pytest.importorskip("torch")
from noema.reference_ranker import ReferenceRanker, scalar_features, reference_targets, marginal_reference_loss, rank_references
from noema.semantics import SemanticError
from scripts.cache_reference_features import save_cached, read_cached, exclusive_cache


def sample():
    text = "A B C"
    heads = [{"id": i, "start": i * 2, "end": i * 2 + 1, "text": text[i * 2]} for i in range(3)]
    row = {"id": "case", "split": "train", "text": text, "heads": heads,
           "relations": [{"source": 1, "target": 0, "type": "=", "mode": None, "external": None},
                         {"source": 2, "target": 1, "type": "=", "mode": None, "external": None}]}
    prediction = {"text": text, "phrases": [{"id": h["id"], "head": h, "relations": []} for h in heads]}
    features = {"nodes": torch.cat((torch.eye(3), torch.eye(3)), -1), "native": torch.zeros(3, 4),
                "word_indices": torch.arange(3), "word_count": torch.tensor(3)}
    return row, prediction, features


def test_targets_allow_all_valid_previous_members_and_ignore_missing_heads():
    row, prediction, _ = sample()
    target, counts = reference_targets(row, prediction)
    assert target.tolist() == [[True, False, False, False], [False, True, False, False], [False, True, True, False]]
    assert counts["supervised"] == 3 and counts["positive"] == 2
    prediction["phrases"][0]["head"] = {"start": 0, "end": 2}
    target, counts = reference_targets(row, prediction)
    assert counts["unmatched_source"] == 1 and counts["missing_antecedent"] == 1
    assert not target[:2].any() and target[2, 2]


def test_unsupported_annotations_are_not_negative_training_labels():
    row, prediction, _ = sample()
    row["relations"][0]["mode"] = "AND"
    targets, counts = reference_targets(row, prediction)
    assert not targets.any() and counts["unsupported_annotation"] == 3


def test_marginal_loss_rewards_probability_of_any_correct_antecedent():
    scores = torch.tensor([[0., 0., 0.]], requires_grad=True)
    target = torch.tensor([[False, True, True]])
    loss, count = marginal_reference_loss(scores, target)
    assert count == 1 and float(loss.detach()) == pytest.approx(math.log(3 / 2))
    loss.backward()
    assert torch.isfinite(scores.grad).all() and scores.grad[0, 0] > 0
    with pytest.raises(SemanticError, match="masked"):
        marginal_reference_loss(torch.tensor([[0., -torch.inf]]), torch.tensor([[False, True]]))


@pytest.mark.parametrize("hidden", [0, 64])
def test_ranker_has_no_future_or_self_links_and_has_finite_gradients(hidden):
    row, prediction, features = sample()
    head = ReferenceRanker(3, hidden)
    scores = head(features)
    assert scores.shape == (3, 4)
    assert torch.isneginf(scores[0, 1:]).all() and torch.isneginf(scores[2, 3])
    target, _ = reference_targets(row, prediction)
    loss, _ = marginal_reference_loss(scores, target)
    loss.backward()
    assert all(torch.isfinite(p.grad).all() for p in head.parameters() if p.grad is not None)
    original = copy.deepcopy(prediction)
    output, decisions = rank_references(prediction, features, head)
    assert prediction == original
    assert all(d["target"] is None or d["target"] < d["source"] for d in decisions)
    assert len(output["phrases"]) == 3


def test_native_scores_are_shift_invariant_and_word_spelling_is_not_a_feature():
    _, _, features = sample()
    before = scalar_features(features)
    features["native"] += torch.tensor([[8.], [-3.], [17.]])
    assert torch.equal(before, scalar_features(features))
    assert before[:, 0, 4].tolist() == [1, 1, 1]


def test_committed_cache_checks_both_source_and_tensor_bytes(tmp_path):
    row, prediction, features = sample()
    record = save_cached(tmp_path, row, prediction, features, None, True)
    cached, tensors = read_cached(tmp_path, row)
    assert record == cached and all(torch.equal(tensors[k], features[k]) for k in tensors)
    changed = {**row, "text": "different"}
    with pytest.raises(SemanticError, match="source differs"):
        read_cached(tmp_path, changed)
    with (tmp_path / "train/case.safetensors").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(SemanticError, match="tensors changed"):
        read_cached(tmp_path, row)


def test_failed_and_interrupted_cache_records_are_distinct(tmp_path):
    row, prediction, features = sample()
    folder = tmp_path / "train"
    folder.mkdir()
    (folder / "case.safetensors").write_bytes(b"interrupted")
    assert read_cached(tmp_path, row) is None
    save_cached(tmp_path, row, prediction, features, None, False)
    assert read_cached(tmp_path, row)[0]["failure"] is None
    failed = {**row, "id": "failed"}
    save_cached(tmp_path, failed, None, None, "context exceeded", False)
    record, tensors = read_cached(tmp_path, failed)
    assert record["failure"] == "context exceeded" and tensors is None


def test_cache_extraction_lock_is_released_after_failure(tmp_path):
    path = tmp_path / "cache.lock"
    with pytest.raises(RuntimeError):
        with exclusive_cache(path):
            raise RuntimeError("failed extraction")
    with exclusive_cache(path):
        assert path.exists()


def test_cached_scalar_features_and_small_training_run_are_reproducible():
    from scripts.train_reference_ranker import fit, evaluate
    row, prediction, features = sample()
    target, _ = reference_targets(row, prediction)
    torch.manual_seed(17)
    head = ReferenceRanker(3, 64)
    expected = head(features)
    features["scalars"] = scalar_features(features)
    assert torch.equal(head(features), expected)
    records = [{"row": row, "prediction": prediction, "features": features, "target": target, "failure": None}]
    first, choice, history = fit(records, records, 3, 64, epochs=3, batch_size=1)
    second, choice2, history2 = fit(records, records, 3, 64, epochs=3, batch_size=1)
    assert choice == choice2 and history == history2
    assert all(torch.equal(value, second.state_dict()[key]) for key, value in first.state_dict().items())
    assert evaluate(records, first) == evaluate(records, second)
