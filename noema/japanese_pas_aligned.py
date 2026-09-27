"""Frozen Japanese parser with normalized-character/source alignment."""
import unicodedata

from .character_alignment import character_ids, source_tags
from .definition_probe import digest
from .japanese_pas import JapanesePAS, source_spans
from .semantics import require


class AlignedJapanesePAS(JapanesePAS):
    def __init__(self, root="artifacts/japanese-pas-model"):
        super().__init__(root)
        self.metadata.update(base_adapter_sha256=self.metadata["adapter_sha256"], adapter_sha256=digest(__file__),
                             alignment_sha256=digest("noema/character_alignment.py"),
                             unicode_version=unicodedata.unidata_version, source_normalization=False,
                             character_model_normalization="NFKC", literal_control_tokens=True,
                             boundary_projection="first_model_character_of_source_group")

    def character_input(self, text):
        import torch
        tokenizer = self.tokenizers["char"]
        # Bound the quadratic prefix-alignment work before computing it.
        require(len(unicodedata.normalize("NFKC", text)) + tokenizer.num_special_tokens_to_add(False)
                <= self.configs["char"].max_seq_length, "Japanese char context exceeded")
        ids, groups = character_ids(text, tokenizer)
        encoded = tokenizer.prepare_for_model(ids, add_special_tokens=True, return_attention_mask=True,
                                               return_special_tokens_mask=True, truncation=False)
        indices = [i for i, special in enumerate(encoded.pop("special_tokens_mask")) if not special]
        require(len(indices) == len(ids), "Tokenizer wrapper lost character positions")
        return {key: torch.tensor([value], dtype=torch.long) for key, value in encoded.items()}, indices, groups

    def segment(self, text):
        import torch
        from rhoknp import Document, Sentence
        from kwja.callbacks.utils import _build_morpheme
        from kwja.utils.constants import SENT_SEGMENTATION_TAGS, WORD_SEGMENTATION_TAGS
        encoded, indices, groups = self.character_input(text)
        with torch.inference_mode():
            output = self.models["char"](encoded)
        sentences = [SENT_SEGMENTATION_TAGS[i] for i in output["sent_segmentation_logits"][0, indices].argmax(-1).tolist()]
        words = [WORD_SEGMENTATION_TAGS[i] for i in output["word_segmentation_logits"][0, indices].argmax(-1).tolist()]
        sentence_tags, word_tags = source_tags(text, groups, sentences, words)
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
