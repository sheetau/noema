"""Correct KWDLC relation endpoints to annotated phrase spans and audit old head labels."""
from collections import Counter
import json
import logging
from pathlib import Path

from noema.definition_probe import digest
from noema.kwdlc_phrase_references import corpus_phrase_document, UNIT
from noema.semantics import require
from scripts.prepare_reference_corpus import SOURCE, REPORT as PREVIOUS, write

ROOT = Path("artifacts/corpus-reference-v2")
REPORT = Path("reports/corpus-reference-v2")


def main():
    from rhoknp import Document
    logging.disable(logging.WARNING)
    previous_path = PREVIOUS / "preparation.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    ROOT.mkdir(parents=True, exist_ok=False)
    REPORT.mkdir(parents=True, exist_ok=True)
    counts, records, prepared = {}, [], {}
    for split in ("train", "dev", "test"):
        count = Counter()
        path = ROOT / f"{split}.jsonl"
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            for item in previous["records"]:
                if item["split"] != split:
                    continue
                source = SOURCE / item["path"]
                require(digest(source) == item["file_sha256"], "Original corpus source changed")
                document = Document.from_knp(source.read_text(encoding="utf-8"))
                row = corpus_phrase_document(document)
                require(row["id"] == item["id"], "Phrase corpus ID differs")
                row["split"] = split
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                count.update(documents=1, phrases=len(row["phrases"]))
                for phrase in document.base_phrases:
                    evidence = any(any(key in m.features for key in ("内容語", "準内容語", "基本句-主辞")) for m in phrase.morphemes)
                    count["explicit_head_feature_phrases"] += evidence
                    count["fallback_first_token_phrases"] += not evidence
                records.append({"id": row["id"], "split": split, "source_sha256": digest(source)})
        prepared[split] = digest(path)
        counts[split] = dict(count)
    write(REPORT / "preparation.json", {"alignment_unit": UNIT, "source": previous["source"], "revision": previous["revision"],
          "previous_preparation_sha256": digest(previous_path), "summary": counts, "records": records,
          "prepared_sha256": prepared, "code_sha256": {p: digest(p) for p in (
              "noema/kwdlc_phrase_references.py", "scripts/prepare_phrase_reference_corpus.py")},
          "invalidates": ["corpus-reference-v1 head labels", "reference-ranker-v1 supervision and selection",
                          "native-heads-v1 accuracy against unannotated lexical heads"]})
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
