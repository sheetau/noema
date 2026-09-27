"""Reference endpoints in KWDLC's annotated base-phrase spans, without invented heads."""
from .japanese_pas import source_spans
from .kwdlc_references import assess_corpus_references, corpus_summary
from .semantics import require

UNIT = "annotated_base_phrase_span"


def corpus_phrase_document(document):
    tokens = source_spans(document.text, [m.text for m in document.morphemes])
    lookup = {(p.sentence.sid, p.index): p.global_index for p in document.base_phrases}
    phrases, relations = [], []
    for phrase in document.base_phrases:
        first, last = phrase.morphemes[0].global_index, phrase.morphemes[-1].global_index
        start, end = tokens[first]["start"], tokens[last]["end"]
        phrases.append({"id": phrase.global_index, "start": start, "end": end, "text": document.text[start:end]})
        for relation in phrase.rel_tags:
            if not relation.type.startswith("="):
                continue
            target = None
            if relation.sid is not None:
                key = relation.sid, relation.base_phrase_index
                require(key in lookup, "Corpus phrase reference target is outside document")
                target = lookup[key]
            relations.append({"source": phrase.global_index, "target": target, "type": relation.type,
                              "mode": relation.mode.value if relation.mode is not None else None,
                              "external": relation.target if relation.sid is None else None})
    require("".join(p["text"] for p in phrases) == document.text, "Corpus phrases omit source characters")
    return {"id": document.doc_id, "text": document.text, "sentences": len(document.sentences),
            "alignment_unit": UNIT, "phrases": phrases, "relations": relations}


def span_metric_inputs(row, prediction):
    """Adapt exact span sets to the existing set metric; do not infer a lexical head."""
    require(row.get("alignment_unit") == UNIT, "Reference alignment unit is not annotated phrase spans")
    adapted_row = {**row, "heads": row["phrases"]}
    adapted_prediction = None
    if prediction is not None:
        adapted_prediction = {**prediction, "phrases": [
            {**p, "head": {"start": p["start"], "end": p["end"]}} for p in prediction["phrases"]]}
    return adapted_row, adapted_prediction


def assess_phrase_references(row, prediction):
    result = assess_corpus_references(*span_metric_inputs(row, prediction))
    return {key.replace("heads", "phrases").replace("head_recall", "phrase_recall"): value for key, value in result.items()}


def phrase_summary(cases):
    legacy_keys = [{key.replace("phrases", "heads"): value for key, value in case.items()} for case in cases]
    summary = corpus_summary(legacy_keys)
    return {group: {key.replace("heads", "phrases").replace("head_recall", "phrase_recall"): value
                    for key, value in counts.items()} for group, counts in summary.items()}
