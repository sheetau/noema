"""Local, voluntary written-language exercises; not a human-study simulator."""
import json
import hashlib
from importlib.resources import files
from .grammar import parse, format_graph
from .language import convert
from .script import encode
from .semantics import require

TASK_TEXT = files("noema").joinpath("resources/practice-v1.json").read_text(encoding="utf-8")
TASKS = json.loads(TASK_TEXT)
TASK_SHA256 = hashlib.sha256(TASK_TEXT.encode("utf-8")).hexdigest()
BY_ID = {q["id"]: (kind, q) for kind in ("reading", "writing") for q in TASKS[kind]}


def public_tasks():
    reading = [{k: v for k, v in q.items() if k != "correct"} | {"script": encode(q["noema"])} for q in TASKS["reading"]]
    writing = [{k: v for k, v in q.items() if k != "noema"} for q in TASKS["writing"]]
    return {"version": TASKS["version"], "sha256": TASK_SHA256, "written_version": TASKS["written_version"], "reading": reading, "writing": writing}


def grade(payload):
    require(isinstance(payload, dict) and isinstance(payload.get("id"), str) and payload["id"] in BY_ID, "Unknown exercise")
    kind, question = BY_ID[payload["id"]]
    answer, reveal = payload.get("answer"), payload.get("reveal", False)
    require(type(reveal) is bool, "reveal must be boolean")
    result = {"id": question["id"], "kind": kind, "correct": False, "exercise_sha256": TASK_SHA256}
    if kind == "reading":
        require(type(answer) is int and 0 <= answer < len(question["choices"]), "Select a reading answer")
        result["correct"] = answer == question["correct"]
    else:
        require(isinstance(answer, str), "Write a Noema answer")
        try:
            parsed = convert(parse(answer), TASKS["written_version"])
            result["correct"] = parsed == parse(question["noema"])
            result["canonical"] = format_graph(parsed)
        except (ValueError, RecursionError) as exc:
            result["error"] = str(exc)
    if reveal:
        result["solution"] = question["choices"][question["correct"]] if kind == "reading" else format_graph(parse(question["noema"]))
    return result
