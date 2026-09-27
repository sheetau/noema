import pytest
from noema.augment import build, parenthesize_location, partition_hash
from noema.corpus_v2 import build as base_corpus, realize, validate


@pytest.mark.parametrize("language", ["ja", "en"])
def test_parenthetical_location_retains_every_annotation_literal(language):
    combo = ("bb", "aa", "ab", None, "ah")
    text, spans, _ = realize(combo, {"agent": 12345}, "Ada", "negated", "tomorrow", language, "object_first")
    expected = [text[s["start"]:s["end"]] for s in spans]
    modified, shifted = parenthesize_location(text, spans, language)
    assert [modified[s["start"]:s["end"]] for s in shifted] == expected
    assert ("(" if language == "en" else "（") in modified


def test_training_augmentation_preserves_evaluation_rows_and_split_disjointness():
    rows = base_corpus()
    combined = build(rows, variants=3)
    assert len(combined) > len(rows)
    assert combined[:len(rows)] == rows
    assert all(row["split"] == "train" for row in combined[len(rows):])
    for split in ("dev", "test"):
        assert partition_hash(rows, split) == partition_hash(combined, split)
    validate(combined)
    from noema.annotation_audit import audit
    assert audit(combined)["internal_consistency"]


def test_annotation_audit_rejects_semantic_and_literal_mismatches():
    import copy
    from noema.annotation_audit import audit
    from noema.semantics import SemanticError
    text, spans, graph = realize(("bb", "ag", "ab", None, "ah"), {"patient": 17}, "Ada", "affirmed", "today", "en", "active")
    row = {"id": "audit", "group": "audit", "supported": True, "text": text, "spans": spans, "graph": graph}
    assert audit([row])["internal_consistency"]
    wrong_name = copy.deepcopy(row)
    next(n for n in wrong_name["graph"]["nodes"] if n["concept"] == "ag")["name"] = "Amina"
    with pytest.raises(SemanticError, match="Name span"):
        audit([wrong_name])
    wrong_quantity = copy.deepcopy(row)
    next(s for s in wrong_quantity["spans"] if s["kind"] == "quantity")["end"] -= 1
    with pytest.raises(SemanticError, match="Quantity"):
        audit([wrong_quantity])
