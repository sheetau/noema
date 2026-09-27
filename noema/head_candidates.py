"""Expose frozen token head scores before native phrase grouping loses alternatives."""
import math

from .kwdlc_references import IDENTITY_TYPES, gold_partition
from .semantics import require


def scored_candidates(prediction, probabilities):
    tokens = prediction["tokens"]
    require(len(probabilities) == len(tokens), "Head score/token counts differ")
    require(all(math.isfinite(p) and 0 <= p <= 1 for p in probabilities), "Invalid native head probability")
    offset = 0
    for token in tokens:
        require(token["start"] == offset and token["end"] > offset
                and prediction["text"][offset:token["end"]] == token["text"], "Head token alignment differs")
        offset = token["end"]
    require(offset == len(prediction["text"]), "Head tokens omit source characters")
    return {"status": "research_native_head_candidates", "analysis": prediction,
            "head_probabilities": probabilities,
            "candidate_token_indices": [i for i, p in enumerate(probabilities) if p >= .5],
            "decision": "native_head_probability_ge_0.5"}


def extract_head_candidates(parser, text):
    from kwja.utils.constants import WORD_FEATURES
    captured = []
    index = WORD_FEATURES.index("基本句-主辞")
    hook = parser.models["word"].register_forward_hook(
        lambda module, args, result: captured.append(result["word_feature_probabilities"][0, :, index].detach().cpu().clone()))
    try:
        prediction = parser.analyze(text)
    finally:
        hook.remove()
    require(len(captured) == 1, "Expected one native word forward for head candidates")
    n = len(prediction["tokens"])
    require(len(captured[0]) >= n, "Native head scores omit tokens")
    return scored_candidates(prediction, captured[0][:n].tolist())


def assess_head_candidates(row, result):
    gold, pairs = gold_partition(row)
    supported = not any(r["type"] in IDENTITY_TYPES and r["mode"] is not None for r in row["relations"])
    predicted, direct, tokens = set(), set(), set()
    if result is not None:
        prediction = result["analysis"]
        require(prediction["text"] == row["text"], "Head evaluation source differs")
        checked = scored_candidates(prediction, result["head_probabilities"])
        require(checked == result, "Native head decision differs")
        tokens = {(t["start"], t["end"]) for t in prediction["tokens"]}
        predicted = {(p["head"]["start"], p["head"]["end"]) for p in prediction["phrases"]}
        require(predicted <= tokens, "Native phrase head is outside tokens")
        direct = {(prediction["tokens"][i]["start"], prediction["tokens"][i]["end"])
                  for i in result["candidate_token_indices"]}
    methods = {"native_phrase_heads": predicted, "direct_head_scores": direct,
               "union_candidates": predicted | direct, "all_tokens_ceiling": tokens}
    counts = {}
    for name, candidates in methods.items():
        counts[name] = {"gold": len(gold), "predicted": len(candidates), "correct": len(gold & candidates),
                        "missing": len(gold - candidates), "extra": len(candidates - gold),
                        "exact": result is not None and gold == candidates,
                        "gold_pairs": len(pairs) if supported else None,
                        "pairs_with_available_endpoints": sum(set(pair) <= candidates for pair in pairs) if supported else None}
    missing = gold - predicted
    starts, ends = {a for a, _ in tokens}, {b for _, b in tokens}
    not_token = missing - tokens
    mergeable = {(a, b) for a, b in not_token if a in starts and b in ends}
    return {"id": row["id"], "parsed": result is not None, "annotation_supported": supported,
            "methods": counts, "missing_native_heads": {
                "available_token": len(missing & tokens), "multiple_complete_tokens": len(mergeable),
                "token_boundary_mismatch": len(not_token - mergeable)},
            "direct_score_changes": {"recovered_gold": len((direct - predicted) & gold),
                                     "lost_gold": len((predicted - direct) & gold),
                                     "added_extra": len((direct - predicted) - gold),
                                     "removed_extra": len((predicted - direct) - gold)}}


def summarize_head_candidates(cases):
    result = {"documents": len(cases), "parsed": sum(c["parsed"] for c in cases),
              "annotation_supported": sum(c["annotation_supported"] for c in cases)}
    for section in ("missing_native_heads", "direct_score_changes"):
        result[section] = {key: sum(c[section][key] for c in cases) for key in cases[0][section]} if cases else {}
    result["methods"] = {}
    for name in ("native_phrase_heads", "direct_head_scores", "union_candidates", "all_tokens_ceiling"):
        counts = {key: sum(c["methods"][name][key] for c in cases if c["methods"][name][key] is not None)
                  for key in ("gold", "predicted", "correct", "missing", "extra", "exact", "gold_pairs", "pairs_with_available_endpoints")}
        counts["precision"] = counts["correct"] / counts["predicted"] if counts["predicted"] else None
        counts["recall"] = counts["correct"] / counts["gold"] if counts["gold"] else None
        counts["f1"] = 2 * counts["correct"] / (counts["gold"] + counts["predicted"]) if counts["gold"] + counts["predicted"] else None
        counts["reference_recall_ceiling"] = counts["pairs_with_available_endpoints"] / counts["gold_pairs"] if counts["gold_pairs"] else None
        result["methods"][name] = counts
    return result
