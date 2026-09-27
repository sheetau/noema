"""Private-use character encoding for Noema's original alphabet.

Literal strings are preserved byte-for-byte at the Unicode text level. The
private-use allocation is a transport convention, not a Unicode standard claim.
"""
import json
from importlib.resources import files
from .semantics import ALPHABET

ALPHABET_SPEC = json.loads(files("noema").joinpath("resources/alphabet-v1.json").read_text(encoding="utf-8"))
SCRIPT_START = ALPHABET_SPEC["unicode_start"]
TO_SCRIPT = {letter: chr(SCRIPT_START + i) for i, letter in enumerate(ALPHABET)}
FROM_SCRIPT = {value: key for key, value in TO_SCRIPT.items()}


def transcribe(text, reverse=False):
    mapping = FROM_SCRIPT if reverse else TO_SCRIPT
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
            result.append(mapping.get(char, char))
    return "".join(result)


def encode(text):
    from .grammar import parse, format_graph
    return transcribe(format_graph(parse(text)))


def decode(text):
    from .grammar import parse, format_graph
    return format_graph(parse(transcribe(text, reverse=True)))
