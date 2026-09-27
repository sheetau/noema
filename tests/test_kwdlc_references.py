import json
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from noema.kwdlc_references import (identity_partition, corpus_document, assess_corpus_references,
                                   corpus_summary, gold_partition)
from noema.semantics import SemanticError
from scripts.prepare_reference_corpus import official_splits


def row():
    return {"id": "sample", "text": "A A B", "heads": [{"id": i, "start": n, "end": n + 1, "text": "AAB"[i]}
            for i, n in enumerate((0, 2, 4))], "relations": [
            {"source": 1, "target": 0, "type": "=", "mode": None, "external": None}]}


def prediction(gold):
    return {"text": gold["text"], "phrases": [{"id": h["id"], "head": h, "relations": [
            {"label": "=", "target_phrase": r["target"], "external": None}
            for r in gold["relations"] if r["source"] == h["id"]]} for h in gold["heads"]]}


def test_partitions_use_positions_and_preserve_transitive_identity():
    gold = row()
    assert gold_partition(gold)[1] == {((0, 1), (2, 3))}
    _, pairs = identity_partition(gold["heads"], [(0, 1), (1, 2)])
    assert len(pairs) == 3
    assert identity_partition(gold["heads"], [])[1] == set()  # Same spelling alone is insufficient.
    with pytest.raises(SemanticError, match="endpoint"):
        identity_partition(gold["heads"], [(0, 99)])


def test_boundary_error_is_not_repaired_by_overlap():
    gold = row()
    output = prediction(gold)
    output["phrases"][1]["head"] = {"start": 1, "end": 3}
    counts = assess_corpus_references(gold, output)
    assert counts["correct_pairs"] == 0 and counts["missing_pairs"] == counts["extra_pairs"] == 1
    assert not counts["document_exact"]


def test_failed_documents_keep_gold_pair_denominators_and_never_become_exact():
    gold = row()
    counts = assess_corpus_references(gold, None)
    assert counts["gold_pairs"] == counts["missing_pairs"] == 1
    assert not counts["pairs_exact"] and not counts["document_exact"]
    gold["relations"] = []
    empty_pairs = assess_corpus_references(gold, None)
    assert not empty_pairs["pairs_exact"]
    summary = corpus_summary([counts, empty_pairs])
    assert summary["all"]["documents"] == 2 and summary["all"]["parsed"] == 0
    assert summary["with_gold_pairs"]["pair_recall"] == 0


def test_modal_identity_is_explicitly_unscored_not_converted_to_a_negative():
    gold = row()
    for mode in ("AND", "OR", "？"):
        gold["relations"][0]["mode"] = mode
        counts = assess_corpus_references(gold, prediction(gold))
        assert counts["annotation_supported"] is False and counts["correct_pairs"] is None
        assert counts["document_exact"] is None
        assert corpus_summary([counts])["unsupported_annotation"]["documents"] == 1


def test_nonidentical_and_external_links_are_not_forced_to_identity():
    gold = row()
    gold["relations"][0]["type"] = "=≒"
    assert not gold_partition(gold)[1]
    gold["relations"][0].update(type="=", target=None, external="author")
    assert not gold_partition(gold)[1]


def test_corpus_adapter_preserves_source_positions_and_rejects_missing_targets():
    tokens = [NS(text="A", global_index=0), NS(text="B", global_index=1)]
    relation = NS(type="=", mode=None, sid="doc-1", base_phrase_index=0, target="A")
    phrases = [NS(global_index=i, index=i, sentence=NS(sid="doc-1"), head=tokens[i], rel_tags=[relation] if i else []) for i in range(2)]
    document = NS(text="AB", morphemes=tokens, base_phrases=phrases, doc_id="doc", sentences=[NS()])
    converted = corpus_document(document)
    assert [h["start"] for h in converted["heads"]] == [0, 1]
    assert converted["relations"][0]["target"] == 0
    relation.sid = "absent"
    with pytest.raises(SemanticError, match="outside document"):
        corpus_document(document)


def test_split_integrity_rejects_overlap_and_missing_files(tmp_path):
    (tmp_path / "id/split_for_pas").mkdir(parents=True)
    (tmp_path / "knp").mkdir()
    for name, key in zip(("train", "dev", "test"), ("a", "b", "c")):
        (tmp_path / "id/split_for_pas" / f"{name}.id").write_text(key + "\n", encoding="utf-8")
        (tmp_path / "knp" / f"{key}.knp").write_text("", encoding="utf-8")
    assert len(official_splits(tmp_path)[1]) == 3
    (tmp_path / "id/split_for_pas/dev.id").write_text("a\n", encoding="utf-8")
    with pytest.raises(SemanticError, match="Repeated"):
        official_splits(tmp_path)
    (tmp_path / "id/split_for_pas/dev.id").write_text("d\n", encoding="utf-8")
    with pytest.raises(SemanticError, match="inventories"):
        official_splits(tmp_path)


def test_boundary_diagnostic_keeps_dropped_pairs_in_full_counts():
    from scripts.diagnose_corpus_references import diagnose
    gold = row()
    bad = prediction(gold)
    bad["phrases"][1]["head"] = {"start": 1, "end": 3}
    result = diagnose([gold, gold], [{"id": "sample", "prediction": prediction(gold)},
                                    {"id": "sample", "prediction": bad}])
    assert result["gold_pairs"] == result["predicted_pairs"] == 2
    assert result["correct_pairs"] == 1
    assert result["gold_pairs_missing_head"] == result["predicted_pairs_extra_head"] == 1
    assert result["matching_heads_pair_precision"] == result["matching_heads_pair_recall"] == 1


def test_character_audit_reports_expansion_without_rewriting_source():
    import copy
    import unicodedata
    from scripts.audit_corpus_characters import audit
    class Tokenizer:
        bos_token_id = eos_token_id = mask_token_id = None
        cls_token_id, sep_token_id, pad_token_id = 1, 2, 0
        subword_tokenizer = NS(normalize_text=True)
        def __call__(self, text):
            return {"input_ids": [1] + [5] * len(unicodedata.normalize("NFKC", text)) + [2]}
    rows = [{"id": "expansion", "text": "A…B"}, {"id": "plain", "text": "ABC"}]
    original = copy.deepcopy(rows)
    result = audit(rows, Tokenizer())
    assert len(result["alignment_failures"]) == 1
    assert result["alignment_failures"][0]["source_characters"] == 3
    assert result["alignment_failures"][0]["model_characters"] == 5
    assert result["expanding_character_document_counts"] == {"U+2026": 1}
    assert rows == original
