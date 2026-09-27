import copy

import pytest

from noema.head_candidates import scored_candidates, assess_head_candidates, summarize_head_candidates
from noema.semantics import SemanticError


def fixture():
    tokens = [{"text": c, "start": i, "end": i + 1} for i, c in enumerate("ABCDE")]
    prediction = {"text": "ABCDE", "tokens": tokens,
                  "phrases": [{"head": tokens[0]}, {"head": tokens[3]}]}
    row = {"id": "sample", "text": prediction["text"],
           "heads": [{"id": i, **tokens[i]} for i in (0, 2)],
           "relations": [{"source": 2, "target": 0, "type": "=", "mode": None, "external": None}]}
    return row, prediction


def test_direct_scores_recover_candidates_without_changing_phrase_references():
    row, prediction = fixture()
    before = copy.deepcopy(prediction)
    result = scored_candidates(prediction, [.8, .1, .5, .2, .1])
    assert result["candidate_token_indices"] == [0, 2]
    assert prediction == before
    case = assess_head_candidates(row, result)
    assert case["direct_score_changes"] == {"recovered_gold": 1, "lost_gold": 0, "added_extra": 0, "removed_extra": 1}
    assert case["methods"]["direct_head_scores"]["exact"]
    assert case["methods"]["union_candidates"]["extra"] == 1
    assert case["methods"]["native_phrase_heads"]["pairs_with_available_endpoints"] == 0
    assert case["methods"]["direct_head_scores"]["pairs_with_available_endpoints"] == 1


def test_failures_and_modal_annotations_keep_their_denominators():
    row, prediction = fixture()
    case = assess_head_candidates(row, scored_candidates(prediction, [.8, .1, .5, .2, .1]))
    failed = assess_head_candidates(row, None)
    modal = copy.deepcopy(row)
    modal["relations"][0]["mode"] = "OR"
    summary = summarize_head_candidates([case, failed, assess_head_candidates(modal, None)])
    assert summary["documents"] == 3 and summary["parsed"] == 1 and summary["annotation_supported"] == 2
    counts = summary["methods"]["direct_head_scores"]
    assert counts["gold"] == 6 and counts["recall"] == 1 / 3
    assert counts["gold_pairs"] == 2 and counts["reference_recall_ceiling"] == .5


def test_boundary_mismatch_is_not_rounded_to_a_candidate():
    row, prediction = fixture()
    row["heads"][1].update(start=1, end=3)
    result = scored_candidates(prediction, [.8, .1, .5, .2, .1])
    case = assess_head_candidates(row, result)
    assert case["missing_native_heads"]["multiple_complete_tokens"] == 1
    assert case["methods"]["all_tokens_ceiling"]["correct"] == 1
    prediction["tokens"] = [prediction["tokens"][0], {"text": "BC", "start": 1, "end": 3}, *prediction["tokens"][3:]]
    row["heads"][1].update(start=2, end=3)
    case = assess_head_candidates(row, scored_candidates(prediction, [.8, .5, .1, .1]))
    assert case["missing_native_heads"]["token_boundary_mismatch"] == 1


@pytest.mark.parametrize("scores", [[.5], [float("nan")] * 5, [1.1] * 5])
def test_invalid_scores_are_rejected(scores):
    _, prediction = fixture()
    with pytest.raises(SemanticError):
        scored_candidates(prediction, scores)


def test_tampered_decision_and_missing_source_characters_are_rejected():
    row, prediction = fixture()
    result = scored_candidates(prediction, [.8, .1, .5, .2, .1])
    result["candidate_token_indices"] = [0]
    with pytest.raises(SemanticError, match="decision"):
        assess_head_candidates(row, result)
    prediction["tokens"].pop()
    with pytest.raises(SemanticError, match="omit source"):
        scored_candidates(prediction, [.8] * 4)


@pytest.mark.parametrize("fail", [False, True])
def test_extraction_uses_native_scores_and_always_removes_hook(monkeypatch, fail):
    import sys
    from types import SimpleNamespace
    torch = pytest.importorskip("torch")
    from noema.head_candidates import extract_head_candidates
    monkeypatch.setitem(sys.modules, "kwja.utils.constants", SimpleNamespace(WORD_FEATURES=["other", "基本句-主辞"]))
    _, prediction = fixture()
    class Word(torch.nn.Module):
        def forward(self):
            output = torch.zeros(1, 8, 2)
            output[0, :5, 1] = torch.tensor([.8, .1, .5, .2, .1])
            return {"word_feature_probabilities": output}
    word = Word()
    def analyze(text):
        word()
        if fail:
            raise ValueError("parser failure")
        assert text == prediction["text"]
        return prediction
    parser = SimpleNamespace(models={"word": word}, analyze=analyze)
    if fail:
        with pytest.raises(ValueError, match="parser failure"):
            extract_head_candidates(parser, prediction["text"])
    else:
        result = extract_head_candidates(parser, prediction["text"])
        assert result["candidate_token_indices"] == [0, 2]
        assert len(result["head_probabilities"]) == 5
    assert not word._forward_hooks
