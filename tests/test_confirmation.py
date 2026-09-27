import json
import hashlib
from pathlib import Path
from noema.confirmation import build, realize
from noema.corpus_v2 import build as original_corpus
from noema.annotation_audit import audit


def test_confirmation_voice_pair_keeps_roles_numbers_and_names():
    combo = ("bb", "ag", "ab", None, "ah")
    rows = []
    for language in ("ja", "en"):
        for variant in (0, 1):
            text, spans, graph, pattern = realize(combo, {"patient": 17}, "Iris", "negated", "tomorrow", language, variant)
            rows.append({"id": language + str(variant), "group": "same", "text": text, "spans": spans, "graph": graph, "supported": True})
    assert rows[0]["text"] == "明日、17匹の猫はIrisによって公園で見られない。"
    assert rows[1]["text"] == "公園で明日、17匹の猫をIrisが見ない。"
    assert rows[2]["text"] == "17 cats tomorrow will not be seen in the park by Iris."
    assert rows[3]["text"] == "In the park tomorrow, Iris will not see 17 cats."
    assert audit(rows)["internal_consistency"]


def test_confirmation_has_preregistered_counts_and_preserves_missing_agents():
    original = original_corpus()
    rows = build(original)
    serialized = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows).encode("utf-8")
    # Parameterizing later confirmations must not rewrite the historical v1 cases.
    assert hashlib.sha256(serialized).hexdigest() == "c13c55b5ad35c195f95b4537b6f01db145e1a090ec6d501b6b7e2d8fe35ef4b2"
    assert len(rows) == 1344
    assert len({r["group"] for r in rows if r["supported"]}) == 300
    for language in ("ja", "en"):
        positive = [r for r in rows if r["supported"] and r["language"] == language]
        negative = [r for r in rows if not r["supported"] and r["language"] == language]
        assert len(positive) == 600 and len(negative) == 72
        assert any(r["combination"][1] is None for r in positive)
        assert len({r["graph"]["nodes"][0]["concept"] for r in positive}) == 6
        assert any(all(n.get("quantity") is None for n in r["graph"]["nodes"]) for r in positive)
        assert {r["graph"]["nodes"][0]["polarity"] for r in positive} == {"affirmed", "negated"}
    assert audit(rows)["internal_consistency"]
