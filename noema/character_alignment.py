"""Map normalized model characters back to lossless source ranges."""
import unicodedata

from .semantics import require


def normalized_ranges(text):
    normalized, mapping = "", []
    for end in range(1, len(text) + 1):
        updated = unicodedata.normalize("NFKC", text[:end])
        common = 0
        while common < min(len(normalized), len(updated)) and normalized[common] == updated[common]:
            common += 1
        start = min((span[0] for span in mapping[common:]), default=end - 1)
        mapping[common:] = [(start, end)] * (len(updated) - common)
        normalized = updated
    groups = []
    for index, (start, end) in enumerate(mapping):
        group = {"source_start": start, "source_end": end, "model_start": index, "model_end": index + 1}
        while groups and groups[-1]["source_end"] > group["source_start"]:
            previous = groups.pop()
            group.update(source_start=min(previous["source_start"], group["source_start"]),
                         source_end=max(previous["source_end"], group["source_end"]), model_start=previous["model_start"])
        groups.append(group)
    source_end = model_end = 0
    for group in groups:
        require(group["source_start"] == source_end and group["model_start"] == model_end,
                "Normalization alignment has a gap or overlap")
        source_end, model_end = group["source_end"], group["model_end"]
        require(unicodedata.normalize("NFKC", text[group["source_start"]:source_end])
                == normalized[group["model_start"]:model_end], "Normalization alignment range differs")
    require(source_end == len(text) and model_end == len(normalized), "Normalization alignment lost source")
    return normalized, groups


def character_ids(text, tokenizer):
    """Use the frozen character vocabulary, with literal control-token text."""
    require(not tokenizer.do_word_tokenize and tokenizer.subword_tokenizer_type == "character",
            "Expected a character-only tokenizer")
    require(tokenizer.subword_tokenizer.normalize_text, "Expected native NFKC normalization")
    normalized, groups = normalized_ranges(text)
    vocabulary = tokenizer.subword_tokenizer.vocab
    added = {token: index for token, index in tokenizer.get_added_vocab().items() if len(token) == 1}
    ids = []
    for group in groups:
        source = text[group["source_start"]:group["source_end"]]
        piece = normalized[group["model_start"]:group["model_end"]]
        if len(source) == len(piece) == 1 and source in added:
            ids.append(added[source])
        else:
            ids.extend(vocabulary.get(char, tokenizer.unk_token_id) for char in piece)
    require(len(ids) == len(normalized), "Character ID alignment differs")
    return ids, groups


def source_tags(text, groups, sentence_tags, word_tags):
    """Project only whole source groups, preserving composed/expanded units."""
    require(len(sentence_tags) == len(word_tags) == (groups[-1]["model_end"] if groups else 0),
            "Model tag count differs from normalization alignment")
    sentences, words = ["I"] * len(text), ["I"] * len(text)
    end = 0
    for group in groups:
        require(group["source_start"] == end and group["source_end"] <= len(text), "Invalid source tag alignment")
        end = group["source_end"]
        sentences[group["source_start"]] = sentence_tags[group["model_start"]]
        words[group["source_start"]] = word_tags[group["model_start"]]
    require(end == len(text), "Source tags omit source characters")
    return sentences, words
