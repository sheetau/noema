from noema.dataset import build_dataset, validate_dataset
from noema.evaluation import evaluate, category_gates
from noema.analyzer import Analyzer
from noema.semantics import make_graph


def test_data_integrity_and_bilingual_equivalence():
    rows = build_dataset()
    validate_dataset(rows)
    groups = {}
    for row in rows:
        if row["supported"]:
            assert groups.setdefault(row["group"], row["graph"]) == row["graph"]
    assert {r["category"] for r in rows if not r["supported"]} >= {"quantification", "nested_negation", "metaphor", "unknown_concept", "cross_sentence_anaphora"}


def test_metrics_denominators_and_null_accuracy():
    g = make_graph("be", {})
    rows = [{"language": "ja", "supported": True, "graph": g, "group": "a"}, {"language": "ja", "supported": False}]
    report = evaluate(rows, [{"status": "unresolved", "graph": None}, {"status": "confirmed", "graph": g}])
    assert report["ja"]["coverage"] == 0
    assert report["ja"]["confirmed_exact_match"] is None
    assert report["ja"]["unsupported_false_accept_rate"] == 1
    assert not report["ja"]["passes_provisional_gate"]


def test_analyzer_never_fakes_untrained_predictions():
    a = Analyzer()
    assert a.analyze("犬が猫を追う", "ja")["status"] == "unresolved"
    assert a.analyze("bonjour", "fr")["status"] == "unsupported"


def test_category_gate_cannot_hide_errors_in_other_categories():
    rows = [{"language": lang, "supported": False, "category": cat}
            for lang in ("ja", "en") for cat, count in (("anaphora", 12), ("unknown", 600)) for _ in range(count)]
    predictions = [{"status": "unresolved"} for _ in rows]
    predictions[0] = {"status": "confirmed"}
    result = category_gates(rows, predictions, {"anaphora": .05})
    assert result["ja:anaphora"]["false_accept_rate"] == 1 / 12
    assert not result["ja:anaphora"]["passes"]
    assert result["en:anaphora"]["passes"]
    assert not category_gates(rows, predictions, {"missing": .05})["ja:missing"]["passes"]
