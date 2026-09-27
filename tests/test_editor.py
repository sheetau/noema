from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import re
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import pytest
from noema.editor import Handler, inspect_text, lexicon
from noema.grammar import parse, format_graph


def test_lessons_and_readings_parse_and_round_trip():
    for name in ("writing-v03.md", "lessons.md"):
        text = Path("docs", name).read_text(encoding="utf-8")
        for example in re.findall(r"```text\n(.*?)\n```", text, re.S):
            graph = parse(example)
            assert parse(format_graph(graph)) == graph
    for story in json.loads(Path("examples/reading.json").read_text(encoding="utf-8")):
        data = inspect_text(story["noema"])
        assert len(data["graph"]["utterances"]) == len(story["ja"]) == len(story["en"])
        assert parse(data["script"]) == data["graph"]
        assert parse(data["canonical"]) == data["graph"]
    assert len(lexicon()["words"]) == 91
    assert all(w["ja"] for w in lexicon()["words"])
    from scripts.build_learning_materials import build
    for name, expected in build(Path(".")).items():
        assert Path(name).read_text(encoding="utf-8") == expected


@pytest.fixture
def server():
    instance = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{instance.server_port}"
    instance.shutdown()
    instance.server_close()
    thread.join(timeout=2)


def test_editor_http_uses_the_same_parser_and_reports_errors(server):
    with urlopen(server) as response:
        html = response.read().decode("utf-8")
    assert "Noema" in html
    initial = re.search(r'<textarea[^>]*>(.*?)</textarea>', html, re.S)[1]
    request = Request(server + "/inspect", data=json.dumps({"text": initial}).encode(), headers={"Content-Type": "application/json"})
    with urlopen(request) as response:
        data = json.load(response)
    assert data["graph"] == parse(initial)
    assert parse(data["script"]) == data["graph"]
    for payload in (b'{"text": "noema c c wrong."}', b'[]', b'\xff'):
        with pytest.raises(HTTPError) as failure:
            urlopen(Request(server + "/inspect", data=payload, headers={"Content-Type": "application/json"}))
        assert failure.value.code == 400
    with pytest.raises(HTTPError) as failure:
        urlopen(Request(server + "/inspect", data=b'{}', headers={"Content-Type": "application/json", "Origin": "https://example.org"}))
    assert failure.value.code == 403
