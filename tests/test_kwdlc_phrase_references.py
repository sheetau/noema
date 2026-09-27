import copy
from types import SimpleNamespace as NS

import pytest

from noema.kwdlc_phrase_references import corpus_phrase_document, assess_phrase_references, phrase_summary, UNIT
from noema.semantics import SemanticError


def fixture():
    tokens = [NS(text=t, global_index=i) for i, t in enumerate(('「', '犬', '」は', '犬だ。'))]
    relation = NS(type="=", mode=None, sid="doc-1", base_phrase_index=0, target="犬")
    class Phrase:
        @property
        def head(self):
            raise AssertionError("Unannotated lexical head must never be read")
    phrases = []
    for i, words in enumerate((tokens[:3], tokens[3:])):
        phrase = Phrase()
        phrase.global_index = phrase.index = i
        phrase.sentence = NS(sid="doc-1")
        phrase.morphemes = words
        phrase.rel_tags = [relation] if i else []
        phrases.append(phrase)
    doc = NS(doc_id="doc", text='「犬」は犬だ。', morphemes=tokens, base_phrases=phrases, sentences=[NS()])
    row = corpus_phrase_document(doc)
    prediction = {"text": doc.text, "phrases": [
        {"id": p["id"], "start": p["start"], "end": p["end"], "head": {"start": 1, "end": 2},
         "relations": [{"label": "=", "target_phrase": 0, "external": None}] if p["id"] else []}
        for p in row["phrases"]]}
    return row, prediction


def test_adapter_uses_annotated_phrase_spans_without_accessing_missing_head_features():
    row, prediction = fixture()
    assert row["alignment_unit"] == UNIT and "heads" not in row
    assert [(p["start"], p["end"]) for p in row["phrases"]] == [(0, 4), (4, 7)]
    counts = assess_phrase_references(row, prediction)
    assert counts["correct_phrases"] == 2 and counts["correct_pairs"] == 1 and counts["document_exact"]
    prediction["phrases"][0]["head"] = {"start": 0, "end": 1}
    assert assess_phrase_references(row, prediction) == counts


def test_phrase_boundary_errors_are_not_forgiven_by_matching_head_or_overlap():
    row, prediction = fixture()
    prediction["phrases"][0]["start"] = 1
    result = assess_phrase_references(row, prediction)
    assert result["missing_phrases"] == result["extra_phrases"] == 1
    assert result["correct_pairs"] == 0 and result["missing_pairs"] == result["extra_pairs"] == 1
    assert not result["document_exact"]


def test_failures_and_modal_relations_remain_explicit_with_correct_units():
    row, prediction = fixture()
    failed = assess_phrase_references(row, None)
    modal = copy.deepcopy(row)
    modal["relations"][0]["mode"] = "OR"
    unsupported = assess_phrase_references(modal, prediction)
    assert unsupported["correct_pairs"] is None
    summary = phrase_summary([failed, unsupported])
    assert summary["all"]["documents"] == 2 and summary["all"]["parsed"] == 1
    assert summary["all"]["gold_pairs"] == summary["all"]["missing_pairs"] == 1
    assert summary["all"]["gold_phrases"] == 4 and "gold_heads" not in summary["all"]
    del row["alignment_unit"]
    with pytest.raises(SemanticError, match="alignment unit"):
        assess_phrase_references(row, prediction)
