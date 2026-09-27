"""Identify raw character alignment failures without loading model weights."""
from collections import Counter
import json
from pathlib import Path
import unicodedata

from noema.definition_probe import digest
from scripts.prepare_reference_corpus import ARTIFACTS, REPORT, write


def audit(rows, tokenizer):
    special = {getattr(tokenizer, f"{prefix}_token_id") for prefix in ("bos", "eos", "sep", "pad", "cls", "mask")}
    issues, characters = [], Counter()
    for row in rows:
        indices = tokenizer(row["text"])["input_ids"]
        count = sum(index not in special for index in indices)
        if count != len(row["text"]):
            changes = [{"codepoint": f"U+{ord(char):04X}", "name": unicodedata.name(char, ""),
                        "normalized_length": len(unicodedata.normalize("NFKC", char))}
                       for char in sorted(set(row["text"])) if len(unicodedata.normalize("NFKC", char)) != 1]
            issues.append({"id": row["id"], "source_characters": len(row["text"]), "model_characters": count,
                           "nfkc_characters": len(unicodedata.normalize("NFKC", row["text"])), "expanding_characters": changes})
            characters.update(c["codepoint"] for c in changes)
    return {"tokenizer_class": type(tokenizer).__name__, "subword_normalize_text": tokenizer.subword_tokenizer.normalize_text,
            "documents": len(rows), "alignment_failures": issues, "expanding_character_document_counts": dict(characters)}


def main():
    from transformers import AutoTokenizer
    preparation = json.loads((REPORT / "preparation.json").read_text(encoding="utf-8"))
    assert digest(ARTIFACTS / "dev.jsonl") == preparation["prepared_sha256"]["dev"]
    rows = [json.loads(line) for line in (ARTIFACTS / "dev.jsonl").read_text(encoding="utf-8").splitlines()]
    tokenizer = AutoTokenizer.from_pretrained("artifacts/japanese-pas-model/char/encoder", local_files_only=True,
                                               trust_remote_code=False, do_word_tokenize=False)
    result = audit(rows, tokenizer)
    path = REPORT / "character-audit.json"
    if path.exists():
        assert result == json.loads(path.read_text(encoding="utf-8"))
        print("Character audit replay equal")
    else:
        write(path, result)
    print("Alignment failures", len(result["alignment_failures"]), "of", result["documents"])


if __name__ == "__main__":
    main()
