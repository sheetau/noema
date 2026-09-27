"""Keep one model position for every source word, even if normalization erases it."""
from .semantics import require


class PreservingWordTokenizer:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.fallback_calls = self.fallback_words = 0

    def __getattr__(self, name):
        return getattr(self.tokenizer, name)

    def __len__(self):
        return len(self.tokenizer)

    def __call__(self, *args, **kwargs):
        return self._encode(self.tokenizer, *args, **kwargs)

    def encode_plus(self, *args, **kwargs):
        return self._encode(self.tokenizer.encode_plus, *args, **kwargs)

    def _encode(self, method, *args, **kwargs):
        result = method(*args, **kwargs)
        if not kwargs.get("is_split_into_words", False):
            return result
        words = args[0] if args else kwargs.get("text")
        require(isinstance(words, list) and all(isinstance(word, str) for word in words)
                and len(result.encodings) == 1, "Expected a single pretokenized word sequence")
        def pieces(encoded):
            groups = {}
            for word, index in zip(encoded.encodings[0].word_ids, encoded.encodings[0].ids, strict=True):
                if word is not None:
                    require(0 <= word < len(words), "Tokenizer returned an invalid word index")
                    groups.setdefault(word, []).append(index)
            return groups
        before = pieces(result)
        missing = set(range(len(words))) - before.keys()
        if not missing:
            return result
        require(bool(self.tokenizer.unk_token) and self.tokenizer.unk_token_id is not None,
                "Tokenizer has no unknown token for an erased source word")
        replacements = [self.tokenizer.unk_token if i in missing else word for i, word in enumerate(words)]
        if args:
            result = method(replacements, *args[1:], **kwargs)
        else:
            result = method(**{**kwargs, "text": replacements})
        after = pieces(result)
        require(set(after) == set(range(len(words))), "Tokenizer still omitted source word positions")
        require(all(after[i] == [self.tokenizer.unk_token_id] for i in missing), "Erased source word is not represented by UNK")
        require(all(after[i] == values for i, values in before.items()), "Preserving missing words changed existing token pieces")
        self.fallback_calls += 1
        self.fallback_words += len(missing)
        return result
