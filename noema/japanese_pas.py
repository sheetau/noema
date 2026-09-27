"""Frozen Japanese case-link probe without generation or dictionary enrichment.

Optional KWJA environment, kept separate from the production translator.
Native case labels are evidence, not a mapping to Noema semantic roles.
"""
import json
import os
import platform
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory

from .definition_probe import digest
from .semantics import require


def source_spans(text, surfaces):
    """Every source character must survive, including punctuation and spaces."""
    require("".join(surfaces) == text, "Japanese analysis changed or omitted source characters")
    offset, result = 0, []
    for surface in surfaces:
        require(bool(surface), "Empty source token")
        result.append({"text": surface, "start": offset, "end": offset + len(surface)})
        offset += len(surface)
    return result


class JapanesePAS:
    def __init__(self, root="artifacts/japanese-pas-model"):
        os.environ["KWJA_CLI_MODE"] = "1"
        import torch
        from omegaconf import OmegaConf
        from safetensors.torch import load_file
        from transformers import AutoTokenizer
        from kwja.modules import CharModule, WordModule
        from .encoder import deterministic
        deterministic()
        root = Path(root)
        provenance = json.loads((root / "provenance.json").read_text(encoding="utf-8"))
        self.models, self.tokenizers, self.configs = {}, {}, {}
        for task, cls in (("char", CharModule), ("word", WordModule)):
            folder = root / task
            require(digest(folder / "model.safetensors") == provenance["models"][task]["weights_sha256"]
                    and digest(folder / "hparams.json") == provenance["models"][task]["hparams_sha256"],
                    "Japanese model artifacts differ from preparation record")
            hparams = OmegaConf.create(json.loads((folder / "hparams.json").read_text(encoding="utf-8")))
            hparams.encoder.from_config.config.pretrained_model_name_or_path = str(folder / "encoder")
            hparams.encoder.from_config.config.local_files_only = True
            hparams.encoder.from_config.config.trust_remote_code = False
            model = cls(hparams)
            weights = load_file(str(folder / "model.safetensors"))
            # This was made non-persistent in Transformers 4.31, as noted upstream.
            weights.pop("encoder.embeddings.position_ids", None)
            model.load_state_dict(weights, strict=True)
            self.models[task] = model.eval().requires_grad_(False)
            options = {"additional_special_tokens": list(hparams.special_tokens), "local_files_only": True,
                       "trust_remote_code": False}
            if task == "char":
                options["do_word_tokenize"] = False
            self.tokenizers[task] = AutoTokenizer.from_pretrained(folder / "encoder", **options)
            self.configs[task] = hparams
        import kwja
        package = Path(kwja.__file__).parent
        source_files = ("modules/char.py", "modules/word.py", "modules/components/deberta_v2.py", "callbacks/utils.py",
                        "datamodule/datasets/word_inference.py", "datamodule/datamodule.py", "utils/constants.py")
        self.metadata = {"provenance": provenance,
                         "versions": {p: version(p) for p in ("kwja", "torch", "transformers", "rhoknp", "cohesion-tools")},
                         "python": platform.python_version(), "device": "cpu", "dtype": "float32", "seed": 17,
                         "modules": ["char", "word"], "dictionary_enrichment": False, "normalization": False,
                         "adapter_sha256": digest(__file__),
                         "upstream_source_sha256": {p: digest(package / p) for p in source_files}}

    def segment(self, text):
        import torch
        from rhoknp import Document, Sentence
        from kwja.callbacks.utils import _build_morpheme
        from kwja.utils.constants import SENT_SEGMENTATION_TAGS, WORD_SEGMENTATION_TAGS
        tokenizer = self.tokenizers["char"]
        encoded = tokenizer(text, return_tensors="pt", truncation=False)
        require(encoded["input_ids"].shape[1] <= self.configs["char"].max_seq_length, "Japanese char context exceeded")
        with torch.inference_mode():
            output = self.models["char"](encoded)
        special = {getattr(tokenizer, f"{prefix}_token_id") for prefix in ("bos", "eos", "sep", "pad", "cls", "mask")}
        indices = [i for i, token in enumerate(encoded["input_ids"][0].tolist()) if token not in special]
        require(len(indices) == len(text), "Character tokenizer lost source alignment")
        sentence_tags = [SENT_SEGMENTATION_TAGS[i] for i in output["sent_segmentation_logits"][0, indices].argmax(-1).tolist()]
        word_tags = [WORD_SEGMENTATION_TAGS[i] for i in output["word_segmentation_logits"][0, indices].argmax(-1).tolist()]
        sentences, morphemes, buffer = [], [], ""
        for char, sentence_tag, word_tag in zip(text, sentence_tags, word_tags, strict=True):
            if (sentence_tag == "B" or word_tag == "B" or char == " " or buffer == " ") and buffer:
                morphemes.append(_build_morpheme(buffer, buffer))
                buffer = ""
            if sentence_tag == "B" and morphemes:
                sentence = Sentence()
                sentence.morphemes = morphemes
                sentence.sid = f"noema-{len(sentences)}"
                sentences.append(sentence)
                morphemes = []
            buffer += char
        if buffer:
            morphemes.append(_build_morpheme(buffer, buffer))
        if morphemes:
            sentence = Sentence()
            sentence.morphemes = morphemes
            sentence.sid = f"noema-{len(sentences)}"
            sentences.append(sentence)
        document = Document.from_sentences(sentences)
        document.doc_id = "noema"
        source_spans(text, [m.text for m in document.morphemes])
        return document

    def analyze(self, text, *, return_features=False):
        import torch
        from kwja.datamodule.datasets import WordInferenceDataset
        from kwja.datamodule.datamodule import word_dataclass_data_collator
        from kwja.callbacks.utils import (get_morpheme_attribute_predictions, build_morphemes, chunk_morphemes,
                                         add_base_phrase_features, add_cohesion)
        document = self.segment(text)
        hparams = self.configs["word"]
        tokenizer = self.tokenizers["word"]
        word_ids = tokenizer([m.text for m in document.morphemes], is_split_into_words=True, truncation=False)["input_ids"]
        require(len(word_ids) + len(hparams.special_tokens) <= hparams.max_seq_length, "Japanese word context exceeded")
        options = {key: hparams[key] for key in ("max_seq_length", "document_split_stride", "cohesion_tasks",
                   "exophora_referents", "restrict_cohesion_target", "pas_cases", "br_cases", "special_tokens")}
        with TemporaryDirectory(prefix="noema-pas-") as temporary:
            path = Path(temporary) / "input.juman"
            path.write_text(document.to_jumanpp(), encoding="utf-8", newline="\n")
            dataset = WordInferenceDataset(tokenizer=tokenizer, juman_file=path, **options)
        require(len(dataset) == 1, "Japanese word input was split or omitted")
        example = dataset.examples[0]
        original = dataset.doc_id2document[example.doc_id]
        require(original.text == text, "Japanese word dataset changed source")
        batch = word_dataclass_data_collator([dataset[0]])
        batch["step"] = "predict"
        captured = []
        hook = self.models["word"].encoder.register_forward_hook(
            lambda module, args, result: captured.append(result.last_hidden_state)) if return_features else None
        try:
            with torch.inference_mode():
                output = self.models["word"](batch)
        finally:
            if hook is not None:
                hook.remove()
        n = len(original.morphemes)
        attributes = get_morpheme_attribute_predictions(*(output[key][0, :n].tolist()
            for key in ("pos_logits", "subpos_logits", "conjtype_logits", "conjform_logits")))
        surfaces = [m.text for m in original.morphemes]
        morphemes = build_morphemes(surfaces, surfaces, ["_"] * n, attributes)
        predicted = chunk_morphemes(original, morphemes, output["word_feature_probabilities"][0].tolist())
        for sentence in predicted.sentences:
            add_base_phrase_features(sentence, output["base_phrase_feature_probabilities"][0].tolist())
        add_cohesion(predicted, output["cohesion_logits"][0].tolist(), dataset.cohesion_task2extractor,
                     dataset.cohesion_task2rels, dataset.restrict_cohesion_target, example.special_token_indexer)
        tokens = source_spans(text, [m.text for m in predicted.morphemes])
        phrases = []
        lookup = {(bp.sentence.sid, bp.index): bp.global_index for bp in predicted.base_phrases}
        for bp in predicted.base_phrases:
            start = tokens[bp.morphemes[0].global_index]["start"]
            end = tokens[bp.morphemes[-1].global_index]["end"]
            relations = []
            for rel in bp.rel_tags:
                relations.append({"label": rel.type, "target_phrase": lookup[(rel.sid, rel.base_phrase_index)]
                                  if rel.sid is not None else None, "external": rel.target if rel.sid is None else None})
            phrases.append({"id": bp.global_index, "start": start, "end": end, "text": text[start:end],
                            "head": tokens[bp.head.global_index], "features": dict(bp.features), "relations": relations})
        result = {"status": "research_native_case_links", "language": "ja", "text": text,
                  "tokens": tokens, "phrases": phrases, "pas_labels": list(hparams.pas_cases)}
        if return_features:
            from kwja.modules.components.pooling import pool_subwords, PoolingStrategy
            with torch.inference_mode():
                vectors = pool_subwords(captured[0], batch["subword_map"], PoolingStrategy.FIRST)[0, :n]
            return result, vectors.clone()
        return result
