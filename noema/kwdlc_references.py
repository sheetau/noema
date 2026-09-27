"""Corpus adapters and source-position reference metrics; no inference dictionaries."""
from collections import Counter
from itertools import combinations

from .japanese_pas import source_spans
from .semantics import require

IDENTITY_TYPES = ("=", "=構", "=役")


def corpus_document(document):
    tokens = source_spans(document.text, [m.text for m in document.morphemes])
    lookup = {(p.sentence.sid, p.index): p.global_index for p in document.base_phrases}
    heads, relations = [], []
    for phrase in document.base_phrases:
        heads.append({"id": phrase.global_index, **tokens[phrase.head.global_index]})
        for rel in phrase.rel_tags:
            if not rel.type.startswith("="):
                continue
            target = None
            if rel.sid is not None:
                require((rel.sid, rel.base_phrase_index) in lookup, "Corpus reference target is outside document")
                target = lookup[rel.sid, rel.base_phrase_index]
            relations.append({"source": phrase.global_index, "target": target, "type": rel.type,
                              "mode": rel.mode.value if rel.mode is not None else None,
                              "external": rel.target if rel.sid is None else None})
    return {"id": document.doc_id, "text": document.text, "sentences": len(document.sentences),
            "heads": heads, "relations": relations}


def identity_partition(heads, links):
    parents = {head["id"]: head["id"] for head in heads}
    require(len(parents) == len(heads), "Duplicate reference head ID")
    spans = {h["id"]: (h["start"], h["end"]) for h in heads}
    require(len(set(spans.values())) == len(spans), "Duplicate reference head span")
    def root(i):
        while parents[i] != i:
            i = parents[i]
        return i
    for a, b in links:
        require(a in parents and b in parents, "Reference endpoint is absent")
        a, b = root(a), root(b)
        parents[max(a, b)] = min(a, b)
    groups = {}
    for key, span in spans.items():
        groups.setdefault(root(key), []).append(span)
    pairs = {tuple(sorted(pair)) for group in groups.values() for pair in combinations(group, 2)}
    return set(spans.values()), pairs


def gold_partition(row):
    links = [(r["source"], r["target"]) for r in row["relations"]
             if r["type"] in IDENTITY_TYPES and r["mode"] is None and r["target"] is not None]
    return identity_partition(row["heads"], links)


def predicted_partition(prediction):
    heads = [{"id": p["id"], **p["head"]} for p in prediction["phrases"]]
    links = [(p["id"], r["target_phrase"]) for p in prediction["phrases"] for r in p["relations"]
             if r["label"] == "=" and r["target_phrase"] is not None and r["external"] is None]
    return identity_partition(heads, links)


def assess_corpus_references(row, prediction):
    gh, gp = gold_partition(row)
    ph, pp = predicted_partition(prediction) if prediction is not None else (set(), set())
    supported = not any(r["type"] in IDENTITY_TYPES and r["mode"] is not None for r in row["relations"])
    if prediction is not None:
        require(prediction["text"] == row["text"], "Corpus evaluation source changed")
    result = {"id": row["id"], "parsed": prediction is not None, "annotation_supported": supported,
              "gold_heads": len(gh), "predicted_heads": len(ph), "correct_heads": len(gh & ph),
              "missing_heads": len(gh - ph), "extra_heads": len(ph - gh),
              "heads_exact": prediction is not None and gh == ph}
    result.update({key: None for key in ("gold_pairs", "predicted_pairs", "correct_pairs", "missing_pairs", "extra_pairs",
                                         "pairs_exact", "document_exact")})
    if supported:
        result.update(gold_pairs=len(gp), predicted_pairs=len(pp), correct_pairs=len(gp & pp),
                      missing_pairs=len(gp - pp), extra_pairs=len(pp - gp),
                      pairs_exact=prediction is not None and gp == pp,
                      document_exact=prediction is not None and gh == ph and gp == pp)
    return result


def corpus_summary(cases):
    summary = {}
    for name, selected in (("all", cases),
                           ("with_gold_pairs", [c for c in cases if c["gold_pairs"]]),
                           ("without_gold_pairs", [c for c in cases if c["gold_pairs"] == 0]),
                           ("unsupported_annotation", [c for c in cases if not c["annotation_supported"]])):
        counts = {"documents": len(selected), "parsed": sum(c["parsed"] for c in selected),
                  "annotation_supported": sum(c["annotation_supported"] for c in selected)}
        for key in ("gold_heads", "predicted_heads", "correct_heads", "missing_heads", "extra_heads", "heads_exact",
                    "gold_pairs", "predicted_pairs", "correct_pairs", "missing_pairs", "extra_pairs", "pairs_exact", "document_exact"):
            counts[key] = sum(c[key] for c in selected if c[key] is not None)
        for name_, numerator, denominator in (("head_recall", "correct_heads", "gold_heads"),
                ("pair_precision", "correct_pairs", "predicted_pairs"), ("pair_recall", "correct_pairs", "gold_pairs")):
            counts[name_] = counts[numerator] / counts[denominator] if counts[denominator] else None
        summary[name] = counts
    return summary


def annotation_counts(row):
    return dict(Counter(f"{r['type']}|{r['mode'] or 'plain'}|{'internal' if r['target'] is not None else 'external'}"
                        for r in row["relations"]))
