from noema.context_corpus import build
from noema.reference_corpus import build as references
import pytest
pytest.importorskip("torch")
from noema.unknown_supervision import targets
from noema.structured import LABELS
from test_reference_corpus import example


def test_unknown_context_preserves_known_words_without_claiming_whole_meaning():
    original = [example("en"), example("ja")]
    source = references(original)
    rows = build(source, original)
    assert [(r["id"], r["text"]) for r in rows] == [(r["id"], r["text"]) for r in source]
    row = next(r for r in rows if "known_spans" in r and r["language"] == "en")
    feature = {"offsets": [(i, i + 1) for i in range(len(row["text"]))]}
    labels = targets(row, feature)
    assert int(labels["support"]) == 0
    assert int(labels["frame"]) == -100
    assert int(labels["polarity"]) == -100
    assert (labels["attachment"] == -100).all()
    for word in ("chases", "cat", "park"):
        start = row["text"].index(word)
        assert LABELS["span"][labels["span"][start]].startswith("B-")
    start = row["text"].index("in ")
    assert LABELS["span"][labels["span"][start]] == "O"
    unknown, = row["unknown_spans"]
    assert LABELS["concept"][labels["concept"][unknown["start"]]] == "none"
    assert LABELS["span"][labels["span"][unknown["start"]]] == "B-entity"
