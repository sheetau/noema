from types import SimpleNamespace as NS

import pytest

from noema.preserving_word_tokenizer import PreservingWordTokenizer
from noema.semantics import SemanticError


class Tokenizer:
    unk_token, unk_token_id = "<unknown>", 3
    def __call__(self, text, **kwargs):
        ids, word_ids = [1], [None]
        for i, word in enumerate(text):
            if word.strip():
                ids.append(3 if word == self.unk_token else 100 + i)
                word_ids.append(i)
        ids.append(2)
        word_ids.append(None)
        return NS(encodings=[NS(ids=ids, word_ids=word_ids)])
    encode_plus = __call__


@pytest.mark.parametrize("method", ["__call__", "encode_plus"])
def test_erased_words_keep_their_positions_without_changing_input_or_existing_tokens(method):
    tokenizer = PreservingWordTokenizer(Tokenizer())
    words = ["A", "　", "B", " "]
    result = getattr(tokenizer, method)(words, is_split_into_words=True)
    assert result.encodings[0].ids == [1, 100, 3, 102, 3, 2]
    assert result.encodings[0].word_ids == [None, 0, 1, 2, 3, None]
    assert words == ["A", "　", "B", " "]
    assert tokenizer.fallback_calls == 1 and tokenizer.fallback_words == 2


def test_keyword_input_and_normal_encodings_are_preserved():
    tokenizer = PreservingWordTokenizer(Tokenizer())
    assert tokenizer(text=[" ", "A"], is_split_into_words=True).encodings[0].ids == [1, 3, 101, 2]
    tokenizer(["A", "B"], is_split_into_words=True)
    tokenizer(["A", "B"])
    assert tokenizer.fallback_calls == 1


def test_missing_unknown_token_is_explicitly_rejected():
    native = Tokenizer()
    native.unk_token = None
    with pytest.raises(SemanticError, match="no unknown token"):
        PreservingWordTokenizer(native)([" "], is_split_into_words=True)


def test_fallback_cannot_change_previously_encoded_words():
    class ChangingTokenizer(Tokenizer):
        def __call__(self, text, **kwargs):
            result = super().__call__(text, **kwargs)
            if self.unk_token in text:
                result.encodings[0].ids[-2] += 1
            return result
    with pytest.raises(SemanticError, match="existing token pieces"):
        PreservingWordTokenizer(ChangingTokenizer())([" ", "A"], is_split_into_words=True)
