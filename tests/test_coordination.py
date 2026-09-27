import copy
from types import SimpleNamespace

import pytest

from noema.coordination import (UNIT, typed_dependencies, corpus_coordination, assess_coordination,
                                summarize_coordination, extract_coordination)
from noema.semantics import SemanticError


def fixture():
    tokens = [{"text": c, "start": i, "end": i + 1} for i, c in enumerate("ABCD")]
    prediction = {"text": "ABCD", "tokens": tokens,
                  "phrases": [{"id": i, **t, "head": t} for i, t in enumerate(tokens)]}
    row = {"id": "sample", "alignment_unit": UNIT, "text": "ABCD", "phrases": prediction["phrases"],
           "dependencies": [{"source": i, "target": i + 1 if i < 3 else None, "type": "P" if i < 2 else "D"}
                            for i in range(4)]}
    return row, prediction


def test_exact_directed_edges_preserve_types_and_do_not_infer_groups():
    row, prediction = fixture()
    before = copy.deepcopy(prediction)
    result = typed_dependencies(prediction, [1, 2, 3, 4], ["P", "P", "A", "I"], 4)
    assert result["parallel_edges"] == [{"source": 0, "target": 1}, {"source": 1, "target": 2}]
    assert result["semantic_interpretation"] == "unresolved"
    assert prediction == before and "groups" not in result
    case = assess_coordination(row, result)
    assert case["phrase_and_edge_exact"] and case["correct_edges"] == 2


@pytest.mark.parametrize("parents", [[1, 0, 1, 4], [0, 0, 1, 4], [7, 0, 1, 4]])
def test_bad_paths_are_exposed_without_tree_repair(parents):
    row, prediction = fixture()
    result = typed_dependencies(prediction, parents, ["P"] * 4, 4)
    assert not result["parallel_edges"]
    assert assess_coordination(row, result)["invalid_dependency_phrases"] == 3


def test_missing_edge_reasons_partition_errors_and_failures_stay_in_denominator():
    row, prediction = fixture()
    result = typed_dependencies(prediction, [2, 2, 3, 4], ["P", "D", "D", "D"], 4)
    case = assess_coordination(row, result)
    assert case["missing_reasons"] == {"missing_endpoint": 0, "invalid_path": 0, "different_parent": 1, "different_type": 1}
    assert case["extra_edges"] == 1
    failed = assess_coordination(row, None)
    assert failed["missing_reasons"]["missing_endpoint"] == 2 and not failed["edge_exact"]
    summary = summarize_coordination([case, failed])
    assert summary["all"]["documents"] == 2 and summary["all"]["gold_edges"] == 4
    assert summary["without_gold_parallel"]["documents"] == 0


def test_no_parallel_gold_reports_false_positives_separately():
    row, prediction = fixture()
    row["dependencies"] = []
    result = typed_dependencies(prediction, [1, 2, 3, 4], ["P", "D", "D", "D"], 4)
    counts = summarize_coordination([assess_coordination(row, result)])["without_gold_parallel"]
    assert counts["documents_with_extra_edges"] == 1 and counts["precision"] == 0 and counts["recall"] is None


def test_partial_span_is_not_an_exact_endpoint_and_saved_decisions_are_checked():
    row, prediction = fixture()
    row = copy.deepcopy(row)
    row["phrases"][0]["end"] = 2
    result = typed_dependencies(prediction, [1, 2, 3, 4], ["P", "P", "D", "D"], 4)
    case = assess_coordination(row, result)
    assert case["missing_reasons"]["missing_endpoint"] == 1 and case["correct_edges"] == 1
    result["parallel_edges"].pop()
    with pytest.raises(SemanticError, match="saved decision"):
        assess_coordination(row, result)


def test_corpus_uses_sentence_local_targets_and_never_fallback_heads():
    class Phrase(SimpleNamespace):
        @property
        def head(self):
            raise AssertionError("Unannotated lexical head accessed")
    tokens = [SimpleNamespace(text=c, global_index=i) for i, c in enumerate("ABCD")]
    phrases = [Phrase(global_index=i, morphemes=[tokens[i]], parent_index=1 if i % 2 == 0 else -1,
                      dep_type=SimpleNamespace(value="P" if i % 2 == 0 else "D")) for i in range(4)]
    for start in (0, 2):
        sentence = SimpleNamespace(base_phrases=phrases[start:start + 2])
        for phrase in sentence.base_phrases:
            phrase.sentence = sentence
    document = SimpleNamespace(doc_id="sample", text="ABCD", morphemes=tokens, base_phrases=phrases)
    row = corpus_coordination(document)
    assert [e["target"] for e in row["dependencies"]] == [1, None, 3, None]
    phrases[2].parent_index = 2
    with pytest.raises(SemanticError, match="outside sentence"):
        corpus_coordination(document)


@pytest.mark.parametrize("fail", [False, True])
def test_native_candidate_type_pairing_and_hook_cleanup(monkeypatch, fail):
    import sys
    torch = pytest.importorskip("torch")
    labels = [SimpleNamespace(value=label) for label in ("D", "P", "A", "I")]
    monkeypatch.setitem(sys.modules, "kwja.utils.constants", SimpleNamespace(DEPENDENCY_TYPES=labels))
    _, prediction = fixture()
    class Word(torch.nn.Module):
        def forward(self):
            parents = torch.zeros(1, 6, 6)  # Deliberate ties test the native top-k order.
            types = torch.zeros(1, 6, 3, 4)
            types[:, :, 0, 1] = 5
            types[:, :, 1, 2] = 5
            return {"dependency_logits": parents, "dependency_type_logits": types}
    word = Word()
    def analyze(text):
        word()
        if fail:
            raise ValueError("parser failure")
        return prediction
    parser = SimpleNamespace(models={"word": word}, analyze=analyze,
                             configs={"word": SimpleNamespace(special_tokens=["[ROOT]", "[OTHER]"])})
    if fail:
        with pytest.raises(ValueError, match="parser failure"):
            extract_coordination(parser, "ABCD")
    else:
        result = extract_coordination(parser, "ABCD")
        assert result["parent_words"] == word()["dependency_logits"].topk(3, dim=2).indices[0, :4, 0].tolist()
        assert result["type_labels"] == ["P"] * 4
    assert not word._forward_hooks
