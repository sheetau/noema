"""Japanese reading aids, separate from stable semantic definitions and models."""
import json
from importlib.resources import files
from .language import policy, COMPOUNDS
from .semantics import require

ROLE_NAMES = {"agent": "主体", "patient": "対象", "recipient": "受け手", "location": "場所",
              "source": "出発地", "destination": "到着地", "instrument": "道具", "beneficiary": "受益者"}


def lexicon():
    roots, concepts, markers, _ = policy("0.3")
    japanese = json.loads(files("noema").joinpath("resources/definitions-ja-v03.json").read_text(encoding="utf-8"))
    require(japanese["version"] == "0.3" and set(japanese["definitions"]) == set(concepts), "Japanese glossary differs from the written lexicon")
    return {"words": [{"id": k, "word": roots[k], **v, "definition_ja": japanese["definitions"][k]} for k, v in concepts.items()],
            "roles": markers, "role_names": ROLE_NAMES, "written_version": "0.4",
            "compound_properties": [roots[k] for k in COMPOUNDS["attributive_states"]]}
