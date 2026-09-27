"""Count actual written documents; these fixtures are not translation lookup data."""
import argparse
import json
from pathlib import Path

from noema.grammar import parse, format_graph
from noema.script import encode


def measure(path):
    rows = []
    for item in json.loads(Path(path).read_text(encoding="utf-8")):
        graph = parse(item["noema"])
        full = format_graph(graph)
        compact = format_graph(graph, "compact")
        assert parse(full) == parse(compact) == graph
        native = encode(compact, "v2")
        assert parse(native) == graph and len(native) == len(compact)
        counts = {"full": len(full), "compact": len(compact),
                  "full_body": len(full.split("\n", 1)[1]), "compact_body": len(compact[2:]),
                  "ja": len(item["ja"]), "en": len(item["en"])}
        rows.append({**item, "full": full, "compact": compact, "counts": counts})
    totals = {key: sum(row["counts"][key] for row in rows) for key in rows[0]["counts"]}
    return {"unit": "Unicode code points including header, spaces, newlines, punctuation and literals",
            "scope": "12 manually written examples; length and formal roundtrip only, not translation accuracy or usability",
            "totals": totals,
            "reduction_percent": round(100 * (1 - totals["compact"] / totals["full"]), 2),
            "longer_than_source": {lang: sum(row["counts"]["compact"] > row["counts"][lang] for row in rows) for lang in ("ja", "en")},
            "cases": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/compact-length-v1.json")
    parser.add_argument("--output", default="reports/compact-length-v1.json")
    args = parser.parse_args()
    result = measure(args.input)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: value for key, value in result.items() if key != "cases"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
