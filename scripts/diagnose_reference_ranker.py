"""Separate upstream head omissions from ranking errors without changing inference."""
import json

from noema.definition_probe import digest
from noema.encoder import deterministic
from noema.kwdlc_references import assess_corpus_references, gold_partition, predicted_partition
from noema.reference_ranker import rank_references
from noema.semantics import require
from scripts.cache_reference_features import REPORT
from scripts.evaluate_reference_ranker import selected_head
from scripts.prepare_reference_corpus import write
from scripts.train_reference_ranker import load_split


def compare_partitions(row, native, ranked):
    assessment = assess_corpus_references(row, native)
    assess_corpus_references(row, ranked)
    gh, gold = gold_partition(row)
    heads, before = predicted_partition(native) if native is not None else (set(), set())
    after_heads, after = predicted_partition(ranked) if ranked is not None else (set(), set())
    require(heads == after_heads and (native is None) == (ranked is None), "Ranker changed upstream head availability")
    result = {"id": row["id"], "parsed": native is not None,
              "annotation_supported": assessment["annotation_supported"]}
    if not assessment["annotation_supported"]:
        return result
    available = {pair for pair in gold if set(pair) <= heads}
    result.update(gold_pairs=len(gold), gold_pairs_with_predicted_endpoints=len(available),
                  gold_pairs_missing_endpoints=len(gold - available),
                  gained_correct_pairs=len((after - before) & gold),
                  lost_correct_pairs=len((before - after) & gold),
                  removed_extra_pairs=len((before - after) - gold),
                  added_extra_pairs=len((after - before) - gold))
    for label, pairs in (("native", before), ("selected", after)):
        extra = pairs - gold
        result[label] = {"correct_pairs": len(pairs & gold),
                         "missing_pairs_with_available_endpoints": len(available - pairs),
                         "extra_pairs_with_gold_endpoints": sum(set(pair) <= gh for pair in extra),
                         "extra_pairs_with_non_gold_endpoints": sum(not set(pair) <= gh for pair in extra)}
    return result


def summarize(cases):
    supported = [c for c in cases if c["annotation_supported"]]
    result = {"documents": len(cases), "parsed": sum(c["parsed"] for c in cases),
              "annotation_supported": len(supported)}
    for key in ("gold_pairs", "gold_pairs_with_predicted_endpoints", "gold_pairs_missing_endpoints",
                "gained_correct_pairs", "lost_correct_pairs", "removed_extra_pairs", "added_extra_pairs"):
        result[key] = sum(c[key] for c in supported)
    for label in ("native", "selected"):
        result[label] = {key: sum(c[label][key] for c in supported) for key in (
            "correct_pairs", "missing_pairs_with_available_endpoints",
            "extra_pairs_with_gold_endpoints", "extra_pairs_with_non_gold_endpoints")}
    total = result["gold_pairs"]
    result["endpoint_availability_recall_ceiling"] = result["gold_pairs_with_predicted_endpoints"] / total if total else None
    return result


def main():
    deterministic()
    head, _ = selected_head()
    records, _, _ = load_split("dev")
    cases = []
    for record in records:
        native = record["prediction"]
        ranked = rank_references(native, record["features"], head)[0] if native is not None else None
        cases.append(compare_partitions(record["row"], native, ranked))
    report = {"split": "dev", "purpose": "post_selection_diagnostic_only", "summary": summarize(cases), "cases": cases,
              "selection_sha256": digest(REPORT / "selection.json"),
              "development_sha256": digest(REPORT / "development.json"),
              "diagnostic_code_sha256": digest(__file__)}
    write(REPORT / "development-diagnostic.json", report)
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
