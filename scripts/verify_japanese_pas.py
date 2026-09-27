"""Verify segmentation compatibility, local source, limits, and converted weights."""
import json
from pathlib import Path

from noema.definition_probe import digest
from noema.japanese_pas import JapanesePAS
from noema.semantics import SemanticError


def main():
    model = JapanesePAS()
    import torch
    from rhoknp import Document
    from kwja.callbacks.utils import convert_char_predictions_into_tags, set_sentences, set_morphemes
    source = Path("artifacts/kwja-source/src/kwja")
    source_equal = {name: digest(source / name) == sha for name, sha in model.metadata["upstream_source_sha256"].items()}
    assert all(source_equal.values())
    files = ("char/model.safetensors", "word/model.safetensors", "char/hparams.json", "word/hparams.json", "provenance.json")
    conversion_equal = {name: digest(Path("artifacts/japanese-pas-model", name)) ==
                       digest(Path("artifacts/japanese-pas-conversion-repeat", name)) for name in files}
    assert all(conversion_equal.values())
    rows = [r for path in ("data/srl-span-v1.json", "data/srl-boundary-v1.json")
            for r in json.loads(Path(path).read_text(encoding="utf-8"))]
    tokenizer = model.tokenizers["char"]
    matched = []
    for row in rows:
        text = row["ja"]
        batch = tokenizer(text, return_tensors="pt", truncation=False)
        with torch.inference_mode():
            output = model.models["char"](batch)
        special = {getattr(tokenizer, f"{prefix}_token_id") for prefix in ("bos", "eos", "sep", "pad", "cls", "mask")}
        indices = [i for i, token in enumerate(batch["input_ids"][0].tolist()) if token not in special]
        sent, word, _ = convert_char_predictions_into_tags(
            output["sent_segmentation_logits"][0].argmax(-1).tolist(),
            output["word_segmentation_logits"][0].argmax(-1).tolist(),
            output["word_norm_op_logits"][0].argmax(-1).tolist(), indices)
        expected = Document(text)
        set_sentences(expected, sent)
        # The comparison disables upstream normalization explicitly.
        set_morphemes(expected, word, ["K"] * len(text))
        actual = model.segment(text)
        same = [[m.text for m in s.morphemes] for s in actual.sentences] == [
            [m.text for m in s.morphemes] for s in expected.sentences]
        assert same
        matched.append(row["id"])
    limits = {}
    for name, text in (("char", "猫" * 513), ("word", "犬 " * 200)):
        try:
            model.analyze(text)
        except SemanticError as exc:
            assert "context exceeded" in str(exc), str(exc)
            limits[name] = str(exc)
        else:
            raise AssertionError("Overlong source was not rejected")
    report = {"upstream_source_equal": source_equal, "conversion_equal": conversion_equal,
              "segmentation_equal_cases": matched, "overlong_rejected": limits,
              "scope": "Unchanged upstream forward; char segmentation matches upstream with normalization disabled; not full stock KWJA output equivalence"}
    path = Path("reports/japanese-pas-v1/verification.json")
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("Verified", len(matched), "segmentations and both context limits")


if __name__ == "__main__":
    main()
