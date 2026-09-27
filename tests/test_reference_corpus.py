from noema.corpus_v2 import realize
from noema.reference_corpus import build, outlier
from noema.annotation_audit import audit


def example(language, index=0):
    text, spans, graph = realize(("ba", "ag", "ab", None, "ah"), {}, "Mio" + str(index), "affirmed", "unspecified", language, "active")
    return {"id": language + str(index), "group": str(index), "corpus_version": "0.2", "language": language, "split": "train",
            "supported": True, "combination": ["ba", "ag", "ab", None, "ah"], "pattern": language + ":active", "text": text, "spans": spans, "graph": graph}


def test_topic_change_preserves_roles_and_new_outliers_are_annotated():
    source = [example(l, i) for i in range(3) for l in ("ja", "en")]
    rows = build(source)
    assert rows[:len(source)] == source
    topics = [r for r in rows if r["id"].startswith("topic")]
    assert len(topics) == 1 and "は" in topics[0]["text"]
    assert topics[0]["graph"] == source[-2]["graph"]
    negatives = [r for r in rows if not r["supported"]]
    assert {r["language"] for r in negatives} == {"ja", "en"}
    assert all(r["unknown_spans"] and r["graph"] is None for r in negatives)
    assert audit(rows)["internal_consistency"]


def test_negative_span_covers_the_replacement_and_preserves_surrounding_text():
    row = example("en")
    span = next(s for s in row["spans"] if s["kind"] == "entity" and s["role"] == "agent")
    changed = outlier(row, span, "Memory", "ambiguous_name_or_abstract", "a")
    unknown = changed["unknown_spans"][0]
    assert changed["text"][unknown["start"]:unknown["end"]] == "Memory"
    assert changed["text"].endswith("chases the cat in the park.")
