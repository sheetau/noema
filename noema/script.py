"""Private-use character encoding for Noema's original alphabet.

Literal strings are preserved byte-for-byte at the Unicode text level. The
private-use allocation is a transport convention, not a Unicode standard claim.
"""
import json
import hashlib
from importlib.resources import files
from .semantics import ALPHABET, require

ALPHABET_SPEC = json.loads(files("noema").joinpath("resources/alphabet-v1.json").read_text(encoding="utf-8"))
FUNCTIONAL_SPEC = json.loads(files("noema").joinpath("resources/alphabet-v2.json").read_text(encoding="utf-8"))
SPECS = {"v1": ALPHABET_SPEC, "v2": FUNCTIONAL_SPEC}
SCRIPT_START = ALPHABET_SPEC["unicode_start"]
TO_SCRIPT = {letter: chr(SCRIPT_START + i) for i, letter in enumerate(ALPHABET)}
SCRIPT_MAPS = {key: {letter: chr(spec["unicode_start"] + i) for i, letter in enumerate(ALPHABET)} for key, spec in SPECS.items()}
FROM_SCRIPT = {value: key for mapping in SCRIPT_MAPS.values() for key, value in mapping.items()}


def alphabet_metadata(alphabet="v2"):
    require(alphabet in SPECS, "Unknown alphabet edition")
    canonical = json.dumps(SPECS[alphabet], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"key": alphabet, "version": SPECS[alphabet]["version"],
            "spec_sha256": hashlib.sha256(canonical).hexdigest(),
            "font_sha256": hashlib.sha256(files("noema").joinpath("resources/NoemaWritten.ttf").read_bytes()).hexdigest()}


def transcribe(text, reverse=False, alphabet="v1"):
    require(alphabet in SPECS, "Unknown alphabet edition")
    mapping = FROM_SCRIPT if reverse else SCRIPT_MAPS[alphabet]
    quoted = escaped = False
    result = []
    for char in text:
        if quoted:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
            result.append(char)
        else:
            result.append(mapping.get(char if reverse else FROM_SCRIPT.get(char, char), char))
    return "".join(result)


def encode(text, alphabet="v1", notation=None):
    from .grammar import parse, format_graph, notation_of
    return transcribe(format_graph(parse(text), notation or notation_of(text)), alphabet=alphabet)


def decode(text, notation=None):
    from .grammar import parse, format_graph, notation_of
    return format_graph(parse(transcribe(text, reverse=True)), notation or notation_of(text))
