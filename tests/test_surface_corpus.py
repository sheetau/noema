import pytest
from noema.corpus_v2 import realize
from noema.surface_corpus import variations, build
from noema.annotation_audit import audit


def fixture(language, combo=("ba", "aa", "ab", None, "ah"), style="active"):
    text, spans, graph = realize(combo, {}, "Ada", "affirmed", "unspecified", language, style)
    return {"id": language, "group": "example", "corpus_version": "0.2", "language": language, "split": "train", "supported": True,
            "combination": list(combo), "pattern": language + ":" + style, "text": text, "spans": spans, "graph": graph}


def test_surface_changes_preserve_every_annotated_meaning():
    en = fixture("en")
    variants = dict(variations(en))
    assert variants["medial_location"]["text"] == "The dog, in the park, chases the cat."
    assert variants["bare"]["text"] == "the dog chases the cat in the park"
    ja = fixture("ja", style="passive")
    assert dict(variations(ja))["passive_ni"]["text"] == "公園で猫が犬に追われる。"
    omitted = fixture("ja", ("ba", None, "ab", None, None), "passive")
    assert dict(variations(omitted))["omitted_active_bare"]["text"] == "猫を追う"
    for original in (en, ja, omitted):
        for _, changed in variations(original):
            assert changed["graph"] == original["graph"]
            assert audit([changed])["internal_consistency"]


def test_outlier_sampling_uses_each_language_instead_of_pair_index_parity():
    rows = [fixture("ja"), fixture("en")]
    augmented = build(rows)
    unknown = [r for r in augmented if r.get("unknown_spans")]
    assert {r["language"] for r in unknown} == {"ja", "en"}
    assert audit(augmented)["internal_consistency"]


def test_unknown_spans_supervise_rejection_without_a_positive_graph():
    torch = pytest.importorskip("torch")
    from noema.unknown_supervision import targets
    from noema.structured import LABELS
    row = next(r for r in build([fixture("en")]) if r.get("unknown_spans"))
    feature = {"offsets": [(i, i+1) for i in range(len(row["text"]))], "truncated": False}
    gold = targets(row, feature)
    span = row["unknown_spans"][0]
    assert (gold["concept"][span["start"]:span["end"]] == LABELS["concept"].index("none")).all()
    assert (gold["concept"][:span["start"]] == -100).all()
    assert gold["support"] == 0 and gold["frame"] == -100
    assert (gold["role"] == -100).all()
