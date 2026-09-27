from types import SimpleNamespace as NS
import unicodedata

import pytest

from noema.character_alignment import normalized_ranges, character_ids, source_tags
from noema.semantics import SemanticError


@pytest.mark.parametrize("text", ["", "ABC", "A…B", "ＡＢ", "か\u3099", "e\u0301", "\ufb03\u0301", "\u1100\u1161\u11a8",
                                   "a\u0315\u0300", "㍍", "[MASK]", "🙂 A　B", "¨\u0301"])
def test_ranges_cover_source_and_normalized_text_without_reordering_source(text):
    normalized, groups = normalized_ranges(text)
    assert normalized == unicodedata.normalize("NFKC", text)
    assert "".join(text[g["source_start"]:g["source_end"]] for g in groups) == text
    assert "".join(normalized[g["model_start"]:g["model_end"]] for g in groups) == normalized


def test_expansion_and_composition_do_not_create_internal_source_boundaries():
    for text in ("…", "e\u0301", "\ufb03\u0301", "a\u0315\u0300"):
        normalized, groups = normalized_ranges(text)
        assert len(groups) == 1
        sentences, words = source_tags(text, groups, ["B"] * len(normalized), ["B"] * len(normalized))
        assert sentences == words == ["B"] + ["I"] * (len(text) - 1)


def test_token_ids_preserve_raw_added_space_but_do_not_interpret_control_token_text():
    class Tokenizer:
        do_word_tokenize = False
        subword_tokenizer_type = "character"
        subword_tokenizer = NS(normalize_text=True, vocab={c: i + 10 for i, c in enumerate(".AMSK[]")})
        unk_token_id = 3
        def get_added_vocab(self):
            return {" ": 99, "[MASK]": 4}
    tokenizer = Tokenizer()
    assert character_ids(" ", tokenizer)[0] == [99]
    assert character_ids("　", tokenizer)[0] == [3]  # Matches the old native character vocabulary.
    assert character_ids("…", tokenizer)[0] == [10] * 3
    assert len(character_ids("[MASK]", tokenizer)[0]) == 6
    assert 4 not in character_ids("[MASK]", tokenizer)[0]


def test_tag_projection_rejects_missing_positions():
    _, groups = normalized_ranges("A…B")
    with pytest.raises(SemanticError, match="tag count"):
        source_tags("A…B", groups, ["B"] * 3, ["B"] * 3)
    with pytest.raises(SemanticError, match="omit"):
        source_tags("AB", [], [], [])


def test_mixed_unicode_sequences_preserve_all_source_ranges():
    import random
    rng = random.Random(17)
    alphabet = list("AqéÅかが…㍍ﬃ🙂 \u1100\u1161\u11a8") + [chr(i) for i in range(0x300, 0x370)]
    for _ in range(1000):
        text = "".join(rng.choices(alphabet, k=rng.randrange(1, 18)))
        normalized, groups = normalized_ranges(text)
        assert normalized == unicodedata.normalize("NFKC", text)
        assert "".join(text[g["source_start"]:g["source_end"]] for g in groups) == text
        assert "".join(normalized[g["model_start"]:g["model_end"]] for g in groups) == normalized
