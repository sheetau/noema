"""Frozen syntactic coordination evidence, without inferring plural semantics."""
from .japanese_pas import source_spans
from .reference_heads import dependency_evidence
from .semantics import require

TYPES = ("D", "P", "A", "I")
UNIT = "directed_exact_base_phrase_spans"


def typed_dependencies(prediction, parents, labels, root):
    require(len(labels) == len(prediction["tokens"]), "Dependency type/token counts differ")
    require(all(label in TYPES for label in labels), "Unknown dependency type")
    phrases = prediction["phrases"]
    require(len({p["id"] for p in phrases}) == len(phrases), "Duplicate phrase ID")
    evidence = dependency_evidence(prediction, parents, root)
    dependencies = [{**edge, "type": labels[edge["head_word"]]} for edge in evidence]
    return {"status": "research_syntactic_coordination", "analysis": prediction,
            "parent_words": parents, "type_labels": labels, "root_word": root,
            "dependencies": dependencies,
            "parallel_edges": [{"source": e["source"], "target": e["parent_phrase"]}
                               for e in dependencies if e["status"] == "linked" and e["type"] == "P"],
            "semantic_interpretation": "unresolved"}


def extract_coordination(parser, text):
    from kwja.utils.constants import DEPENDENCY_TYPES
    captured = []

    def capture(module, args, output):
        types = output["dependency_type_logits"]
        # Native types are conditioned on the ordered top-k parent candidates.
        parents = output["dependency_logits"].topk(types.shape[2], dim=2).indices
        captured.append((parents[0, :, 0].tolist(), types[0, :, 0].argmax(-1).tolist()))

    hook = parser.models["word"].register_forward_hook(capture)
    try:
        prediction = parser.analyze(text)
    finally:
        hook.remove()
    require(len(captured) == 1, "Expected one native word forward for coordination")
    n = len(prediction["tokens"])
    parents, labels = captured[0]
    require(len(parents) >= n and len(labels) >= n, "Dependency scores omit source tokens")
    special = list(parser.configs["word"].special_tokens)
    require(special.count("[ROOT]") == 1, "Native root token differs")
    return typed_dependencies(prediction, parents[:n], [DEPENDENCY_TYPES[i].value for i in labels[:n]],
                              n + special.index("[ROOT]"))


def corpus_coordination(document):
    """Read actual phrase annotations; never access rhoknp's fallback head."""
    tokens = source_spans(document.text, [m.text for m in document.morphemes])
    phrases, dependencies = [], []
    for phrase in document.base_phrases:
        first, last = phrase.morphemes[0].global_index, phrase.morphemes[-1].global_index
        start, end = tokens[first]["start"], tokens[last]["end"]
        phrases.append({"id": phrase.global_index, "start": start, "end": end, "text": document.text[start:end]})
        parent = phrase.parent_index
        require(isinstance(parent, int) and -1 <= parent < len(phrase.sentence.base_phrases),
                "Corpus dependency target is outside sentence")
        target = phrase.sentence.base_phrases[parent].global_index if parent >= 0 else None
        require(target != phrase.global_index, "Corpus has a self dependency")
        label = phrase.dep_type.value
        require(label in TYPES, "Unknown annotated dependency type")
        dependencies.append({"source": phrase.global_index, "target": target, "type": label})
    require("".join(p["text"] for p in phrases) == document.text, "Corpus phrases omit source characters")
    return {"id": document.doc_id, "text": document.text, "alignment_unit": UNIT,
            "phrases": phrases, "dependencies": dependencies}


def assess_coordination(row, result):
    require(row["alignment_unit"] == UNIT, "Coordination alignment unit differs")
    gold_spans = {p["id"]: (p["start"], p["end"]) for p in row["phrases"]}
    gold = {(gold_spans[e["source"]], gold_spans[e["target"]]) for e in row["dependencies"]
            if e["type"] == "P" and e["target"] is not None}
    spans, predicted, by_source = {}, set(), {}
    invalid = 0
    if result is not None:
        prediction = result["analysis"]
        require(prediction["text"] == row["text"], "Coordination source text differs")
        require(typed_dependencies(prediction, result["parent_words"], result["type_labels"], result["root_word"]) == result,
                "Coordination saved decision differs")
        spans = {p["id"]: (p["start"], p["end"]) for p in prediction["phrases"]}
        predicted = {(spans[e["source"]], spans[e["target"]]) for e in result["parallel_edges"]}
        by_source = {spans[e["source"]]: e for e in result["dependencies"]}
        invalid = sum(e["status"] not in ("linked", "root") for e in result["dependencies"])
    missing = {"missing_endpoint": 0, "invalid_path": 0, "different_parent": 0, "different_type": 0}
    available = set(spans.values())
    for source, target in gold - predicted:
        if source not in available or target not in available:
            reason = "missing_endpoint"
        else:
            edge = by_source[source]
            if edge["status"] not in ("linked", "root"):
                reason = "invalid_path"
            elif spans.get(edge["parent_phrase"]) != target:
                reason = "different_parent"
            else:
                reason = "different_type"
        missing[reason] += 1
    return {"id": row["id"], "parsed": result is not None, "gold_edges": len(gold),
            "predicted_edges": len(predicted), "correct_edges": len(gold & predicted),
            "extra_edges": len(predicted - gold), "missing_edges": len(gold - predicted),
            "edge_exact": result is not None and gold == predicted,
            "phrase_and_edge_exact": result is not None and gold == predicted and available == set(gold_spans.values()),
            "gold_phrases": len(gold_spans), "predicted_phrases": len(spans),
            "correct_phrases": len(available & set(gold_spans.values())),
            "invalid_dependency_phrases": invalid, "missing_reasons": missing}


def summarize_coordination(cases):
    result = {}
    for group in ("all", "with_gold_parallel", "without_gold_parallel"):
        chosen = [c for c in cases if group == "all" or bool(c["gold_edges"]) == (group == "with_gold_parallel")]
        counts = {key: sum(c[key] for c in chosen) for key in (
            "parsed", "gold_edges", "predicted_edges", "correct_edges", "extra_edges", "missing_edges",
            "edge_exact", "phrase_and_edge_exact", "gold_phrases", "predicted_phrases", "correct_phrases",
            "invalid_dependency_phrases")}
        counts.update(documents=len(chosen), documents_with_extra_edges=sum(c["extra_edges"] > 0 for c in chosen))
        for name, denom in (("precision", counts["predicted_edges"]), ("recall", counts["gold_edges"])):
            counts[name] = counts["correct_edges"] / denom if denom else None
        denom = counts["gold_edges"] + counts["predicted_edges"]
        counts["f1"] = 2 * counts["correct_edges"] / denom if denom else None
        counts["missing_reasons"] = {key: sum(c["missing_reasons"][key] for c in chosen)
                                     for key in ("missing_endpoint", "invalid_path", "different_parent", "different_type")}
        result[group] = counts
    return result
