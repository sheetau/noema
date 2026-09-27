"""Shared reference ranking trained against annotated phrase spans, not invented heads."""
import json
from pathlib import Path

from safetensors.torch import load_file

from .definition_probe import digest
from .kwdlc_phrase_references import UNIT, span_metric_inputs
from .reference_ranker import ReferenceRanker, reference_targets, rank_references
from .reference_features import extract_reference_features
from .semantics import require

ROOT = Path("artifacts/reference-ranker-v2")
REPORT = Path("reports/reference-ranker-v2")
PROTOCOL = Path("docs/reference-ranker-v2-protocol.md")


def phrase_targets(row, prediction):
    require(row["text"] == prediction["text"], "Phrase target source differs")
    return reference_targets(*span_metric_inputs(row, prediction))


def load_phrase_ranker(root=ROOT, report=REPORT):
    root, report = Path(root), Path(report)
    require(not (report / "invalidated.json").exists(), "Phrase reference ranker invalidated")
    selection = json.loads((report / "selection.json").read_text(encoding="utf-8"))
    training = json.loads((report / "training.json").read_text(encoding="utf-8"))
    require(selection["alignment_unit"] == UNIT and training["alignment_unit"] == UNIT, "Ranker annotation unit differs")
    require(digest(report / "selection.json") == training["selection_sha256"], "Phrase ranker selection changed")
    require(digest(PROTOCOL) == training["protocol_sha256"], "Phrase ranker protocol changed")
    require(all(digest(p) == sha for p, sha in training["code_sha256"].items()), "Phrase ranker implementation changed")
    require(digest("reports/corpus-reference-v2/preparation.json") == training["corpus_preparation_sha256"], "Phrase annotations changed")
    require(digest("artifacts/reference-ranker-v1/manifest.json") == training["feature_manifest_sha256"], "Frozen feature contract changed")
    choices = selection["choices"]
    expected = max(choices, key=lambda name: (choices[name]["dev_pair_f1"], -choices[name]["dev_loss"],
                                             -choices[name]["epoch"], name == "linear"))
    require(selection["selected"] == expected, "Phrase ranker selection criterion differs")
    require(selection["decision"] == "argmax_previous_or_none", "Phrase ranker decision differs")
    path = root / f"ranker-{expected}.safetensors"
    require(digest(path) == selection["weights_sha256"][expected], "Phrase ranker weights changed")
    head = ReferenceRanker(selection["dimension"], choices[expected]["hidden"])
    head.load_state_dict(load_file(str(path)), strict=True)
    return head.eval().requires_grad_(False), selection


class PhraseReferenceRankerAnalyzer:
    def __init__(self, root=ROOT, report=REPORT):
        from .encoder import deterministic
        from .japanese_pas_aligned import AlignedJapanesePAS
        deterministic()
        self.head, selection = load_phrase_ranker(root, report)
        self.parser = AlignedJapanesePAS()
        require(self.parser.metadata == selection["model"], "Phrase ranker encoder environment differs")

    def analyze(self, text):
        prediction, features = extract_reference_features(self.parser, text)
        ranked, decisions = rank_references(prediction, features, self.head)
        return {"status": "research_phrase_reference_ranker", "alignment_unit": UNIT,
                "analysis": prediction, "ranked_prediction": ranked, "reference_decisions": decisions}
