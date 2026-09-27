"""Replay dependency decoding, reference groups and evaluation from saved evidence."""
import json
from pathlib import Path

from noema.definition_probe import digest
from noema.reference_heads import dependency_evidence, frame_references
from scripts.probe_reference_heads import DATA, evaluate, summarize, write


def main():
    root = Path("reports/reference-head-v1")
    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    run = read("run.json")
    assert digest(DATA) == run["fixture_sha256"]
    assert digest("docs/reference-head-v1-protocol.md") == run["protocol_sha256"]
    for group in ("code_sha256", "previous_files_sha256"):
        assert all(digest(path) == sha for path, sha in run[group].items()), group
    assert all(digest(root / path) == sha for path, sha in run["outputs_sha256"].items())
    rows = json.loads(DATA.read_text(encoding="utf-8"))
    evidence, cases = read("evidence.json"), []
    assert [e["row"] for e in evidence] == rows
    for entry in evidence:
        row, output = entry["row"], entry["output"]
        prediction, deps = output["analysis"], output["dependencies"]
        assert dependency_evidence(prediction, deps["parent_words"], deps["root_word"]) == deps["phrases"]
        assert frame_references(prediction, deps["phrases"], output["frames"]) == output["references"]
        cases.append(evaluate(row, output))
    assert {"summary": summarize(cases), "cases": cases} == read("evaluation.json")
    assert run["forbidden_path_calls"] == [0] * 5 and not run["training"]
    write(root, "verification.json", {"cached_dependency_and_reference_replay_equal": True,
          "all_evaluation_equal": True, "documents": len(cases), "forbidden_path_calls": run["forbidden_path_calls"],
          "raw_repeated_and_baseline_equal": run["raw_repeated_and_baseline_equal"]})
    print("Verified", len(cases), "reference documents and all evaluation counts")


if __name__ == "__main__":
    main()
