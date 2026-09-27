import json
import subprocess
import sys
from pathlib import Path


def cli(*args):
    return subprocess.run([sys.executable, "-m", "noema", *args], capture_output=True, text=True, encoding="utf-8")


def test_cli_roundtrip_utf8_files(tmp_path):
    source = Path(__file__).parent.parent / "examples/chase.noema"
    graph = tmp_path / "意味.json"
    assert cli("parse", "-i", str(source), "-o", str(graph)).returncode == 0
    result = cli("format", "-i", str(graph))
    assert result.returncode == 0
    assert result.stdout.strip() == source.read_text(encoding="utf-8").strip()
    assert not graph.read_bytes().startswith(b"\xef\xbb\xbf")


def test_cli_invalid_and_missing_checkpoint():
    bad = cli("parse", "--text", "noema a a {}")
    assert bad.returncode == 2 and "error" in json.loads(bad.stderr)
    missing = cli("analyze", "--language", "ja", "--text", "犬が猫を追う")
    assert missing.returncode == 0
    assert json.loads(missing.stdout)["diagnostics"]["reason"] == "checkpoint_required"


def test_cli_formal_import_does_not_load_ml():
    result = subprocess.run([sys.executable, "-c", "import noema,sys; assert 'torch' not in sys.modules; assert 'transformers' not in sys.modules"], capture_output=True)
    assert result.returncode == 0


def test_edition_conversion_reports_wrong_json_types_without_a_traceback():
    for payload in ("[]", "null", "3", '"text"'):
        result = cli("format", "--edition", "0.3", "--text", payload)
        assert result.returncode == 2
        assert "JSON object" in json.loads(result.stderr)["error"]
        assert not result.stdout
