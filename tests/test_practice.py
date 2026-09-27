import json
from urllib.request import Request, urlopen
import pytest
from noema.practice import TASKS, public_tasks, grade
from noema.grammar import parse
from noema.script import decode


def test_public_tasks_omit_solutions_and_all_authored_examples_parse():
    public = public_tasks()
    assert len(public["reading"]) == 12 and len(public["writing"]) == 6
    for question in public["reading"]:
        assert "correct" not in question
        assert parse(question["noema"]) == parse(decode(question["script"]))
    assert all("noema" not in q for q in public["writing"])
    for kind in ("reading", "writing"):
        for question in TASKS[kind]:
            parse(question["noema"])
            answer = question["correct"] if kind == "reading" else question["noema"]
            result = grade({"id": question["id"], "answer": answer})
            assert result["correct"] and "solution" not in result


def test_writing_grades_meaning_instead_of_text_and_keeps_role_errors():
    correct = 'noema d d vac j jx o object i fo o person. ku k zr j p object i p person.'
    assert grade({"id": "w04", "answer": correct})["correct"]
    swapped = 'noema d d vac j jx o object i fo o person. ku k p person j p object i zr.'
    assert not grade({"id": "w04", "answer": swapped})["correct"]
    assert grade({"id": "w01", "answer": "noema c c t po i mu."})["correct"]
    assert not grade({"id": "w01", "answer": "noema d d s po i mu."})["correct"]
    invalid = grade({"id": "w01", "answer": "not Noema", "reveal": True})
    assert not invalid["correct"] and invalid["error"] and invalid["solution"]


@pytest.mark.parametrize("payload", [None, [], {"id": []}, {"id": "missing"}, {"id": "r01", "answer": True}, {"id": "r01", "answer": 8}, {"id": "w01", "answer": []}, {"id": "w01", "answer": "", "reveal": 1}])
def test_bad_practice_requests_are_errors(payload):
    with pytest.raises(ValueError):
        grade(payload)
