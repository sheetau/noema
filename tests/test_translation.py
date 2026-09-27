from http.server import ThreadingHTTPServer
import json
from threading import Thread
from urllib.request import Request, urlopen
import pytest
from noema.editor import Handler
from noema.grammar import parse
from noema.language import convert
from noema.semantics import make_graph, SemanticError
from noema.translation import Translator
from noema.verbalize import realize


def chase(**kwargs):
    return make_graph("ba", {"agent": {"concept": "aa"}, "patient": {"concept": "ab"}}, **kwargs)


def test_reverse_keeps_direction_polarity_quantity_and_relative_time():
    graph = make_graph("ba", {"agent": {"concept": "ab", "quantity": 2}, "patient": {"concept": "aa"}}, "negated", "tomorrow")
    assert realize(graph, "ja") == "明日、2匹の猫が犬を追わない。"
    assert realize(graph, "en") == "2 cats will not chase the dog tomorrow."
    assert realize(chase(time="past"), "en") == "The dog chased the cat."
    missing = make_graph("ba", {"patient": {"concept": "ab"}})
    assert realize(missing, "ja") == "猫を追う。"
    assert realize(missing, "en") == "The cat is chased."
    with pytest.raises(SemanticError, match="omitted subject"):
        realize(make_graph("be", {}), "en")


def test_reverse_never_drops_name_quantity_scope_or_properties():
    value = 9007199254740993
    g = make_graph("be", {"agent": {"concept": "aa", "quantity": value, "name": 'A "B"'}})
    assert str(value) in realize(g, "en") and 'named "A \\"B\\""' in realize(g, "en")
    with pytest.raises(SemanticError):
        realize(chase(polarity="unspecified"), "ja")
    translator = Translator()
    for text in ("noema d d po i mu-sai.", "noema d d y [ po i mu ] [ po i si ].", "noema d d b po i mu."):
        r = translator.translate({"direction": "from_noema", "language": "ja", "text": text})
        assert r["status"] == "unsupported" and r["text"] is None
    shared = chase()
    shared["relations"][1]["target"] = shared["relations"][0]["target"]
    shared["nodes"] = shared["nodes"][:2]
    with pytest.raises(SemanticError, match="Shared referents"):
        realize(shared, "en")


def test_ui_adapter_uses_the_analyzer_and_preserves_uncertainty():
    class FakeAnalyzer:
        def analyze(self, text, language):
            assert (text, language) == ("test input", "ja")
            return {"status": "confirmed", "graph": chase()}
    result = Translator(analyzer=FakeAnalyzer()).translate({"text": "test input", "language": "ja", "direction": "to_noema"})
    assert parse(result["text"]) == parse(result["canonical"]) == convert(chase(), "0.4")
    result = Translator().translate({"text": "test input", "language": "ja", "direction": "to_noema"})
    assert result["status"] == "unresolved" and result["text"] is None


def test_main_page_has_two_editable_areas_and_reverse_http():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base) as response:
            html = response.read().decode("utf-8")
        assert html.count('<textarea ') == 2
        payload = {"direction": "from_noema", "language": "en", "text": "noema d d ih i mu j si."}
        with urlopen(Request(base + "/translate", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})) as response:
            result = json.load(response)
        assert result["status"] == "confirmed" and result["text"] == "The dog chases the cat."
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
