"""Research reference identities from frozen dependency and coreference outputs."""
from itertools import combinations

from .event_gate import GatedEventFrameAnalyzer, event_decisions, kept_frames
from .semantics import require


def span_key(span):
    return span["start"], span["end"]


def dependency_evidence(prediction, parent_words, root_word):
    """Use native top-1 decisions; never repair the predicted dependency tree."""
    tokens, phrases = prediction["tokens"], prediction["phrases"]
    require(len(parent_words) == len(tokens), "Dependency token count differs")
    owners = {}
    for phrase in phrases:
        for i, token in enumerate(tokens):
            if phrase["start"] <= token["start"] and token["end"] <= phrase["end"]:
                require(i not in owners, "Overlapping base phrases")
                owners[i] = phrase["id"]
    by_span = {span_key(token): i for i, token in enumerate(tokens)}
    result = []
    for phrase in phrases:
        require(span_key(phrase["head"]) in by_span, "Phrase head is not a source token")
        word = by_span[span_key(phrase["head"])]
        parent = parent_words[word]
        target = owners.get(parent)
        status = "root" if parent == root_word else "linked" if target is not None else "unknown_parent"
        if target == phrase["id"]:
            status = "self_parent"
        result.append({"source": phrase["id"], "head_word": word, "parent_word": parent,
                       "parent_phrase": target, "status": status})
    lookup = {d["source"]: d for d in result}
    invalid = {}
    for item in result:
        current, seen = item, set()
        while current["status"] == "linked":
            if current["source"] in seen:
                invalid[item["source"]] = "cycle_path"
                break
            seen.add(current["source"])
            current = lookup[current["parent_phrase"]]
        else:
            if current["status"] != "root":
                invalid[item["source"]] = current["status"] if current is item else "invalid_parent_path"
    for item in result:
        if item["source"] in invalid:
            item["status"] = invalid[item["source"]]
    return result


def analyze_dependencies(parser, text):
    captured = []
    hook = parser.models["word"].register_forward_hook(
        lambda module, args, output: captured.append(output["dependency_logits"][0].argmax(-1).tolist()))
    try:
        prediction, vectors = parser.analyze(text, return_features=True)
    finally:
        hook.remove()
    require(len(captured) == 1, "Expected exactly one native word forward")
    n = len(prediction["tokens"])
    special = list(parser.configs["word"].special_tokens)
    require(special.count("[ROOT]") == 1, "Native root token differs")
    parents = captured[0][:n]
    root = n + special.index("[ROOT]")
    return prediction, vectors, {"parent_words": parents, "root_word": root,
                                 "phrases": dependency_evidence(prediction, parents, root)}


def align_head(span, prediction, dependencies):
    heads = {p["id"] for p in prediction["phrases"]
             if span["start"] <= p["head"]["start"] and p["head"]["end"] <= span["end"]}
    if not heads:
        return {"head_phrase": None, "head_status": "no_head"}
    lookup = {d["source"]: d for d in dependencies}
    if any(lookup[h]["status"] not in ("linked", "root") for h in heads):
        return {"head_phrase": None, "head_status": "invalid_dependency"}
    outgoing = sorted(h for h in heads if lookup[h]["parent_phrase"] not in heads)
    return {"head_phrase": outgoing[0] if len(outgoing) == 1 else None,
            "head_status": "aligned" if len(outgoing) == 1 else "ambiguous_head"}


def reference_graph(prediction, dependencies, spans):
    """Span observations remain distinct; referent IDs express predicted identity."""
    phrases = prediction["phrases"]
    parent = {p["id"]: p["id"] for p in phrases}

    def root(item):
        while parent[item] != item:
            item = parent[item]
        return item

    evidence = []
    for phrase in phrases:
        for relation in phrase["relations"]:
            target = relation["target_phrase"]
            if relation["label"] == "=" and target in parent and relation["external"] is None:
                a, b = root(phrase["id"]), root(target)
                parent[max(a, b)] = min(a, b)
                evidence.append({"kind": "native_coreference", "source": phrase["id"], "target": target})
    unique = {}
    for span in spans:
        start, end = span_key(span)
        require(0 <= start < end <= len(prediction["text"]), "Invalid reference span")
        unique[(start, end)] = {"start": start, "end": end, "text": prediction["text"][start:end]}
    mentions, groups, heads = [], {}, {}
    for key, span in sorted(unique.items()):
        alignment = align_head(span, prediction, dependencies)
        head = alignment["head_phrase"]
        identity = ("head", root(head)) if head is not None else ("unresolved", key)
        group = groups.setdefault(identity, len(groups))
        mention = {"id": len(mentions), **span, **alignment, "referent": group}
        if head is not None:
            if head in heads:
                evidence.append({"kind": "same_source_head", "source_mention": heads[head],
                                 "target_mention": mention["id"], "head_phrase": head})
            else:
                heads[head] = mention["id"]
        mentions.append(mention)
    return {"mentions": mentions, "referents": [{"id": i, "mentions": [m["id"] for m in mentions if m["referent"] == i]}
                                                for i in range(len(groups))], "evidence": evidence}


def frame_references(prediction, dependencies, frames):
    spans, edges = [], []
    for frame in frames:
        mentions = {m["id"]: m for m in frame["mentions"]}
        for role in frame["roles"]:
            if role["role"] != "none":
                mention = mentions[role["target"]]
                spans.append(mention)
                edges.append({"source": frame["source"], "role": role["role"], "span": span_key(mention)})
    graph = reference_graph(prediction, dependencies, spans)
    by_span = {span_key(m): m for m in graph["mentions"]}
    graph["roles"] = [{"source": edge["source"], "role": edge["role"],
                       "mention": by_span[edge["span"]]["id"], "referent": by_span[edge["span"]]["referent"]}
                      for edge in edges]
    return graph


def assess_references(gold, graph):
    expected = {span_key(m): m["referent"] for m in gold}
    actual = {span_key(m): m["referent"] for m in graph["mentions"]}

    def pairs(mapping):
        return {tuple(sorted((a, b))) for a, b in combinations(mapping, 2) if mapping[a] == mapping[b]}

    gp, ap = pairs(expected), pairs(actual)
    return {"gold_mentions": len(expected), "predicted_mentions": len(actual),
            "correct_mentions": len(expected.keys() & actual.keys()),
            "missing_mentions": len(expected.keys() - actual.keys()),
            "extra_mentions": len(actual.keys() - expected.keys()),
            "unresolved_heads": sum(m["head_phrase"] is None for m in graph["mentions"]),
            "gold_pairs": len(gp), "predicted_pairs": len(ap), "correct_pairs": len(gp & ap),
            "missing_pairs": len(gp - ap), "extra_pairs": len(ap - gp),
            "partition_exact": expected.keys() == actual.keys() and gp == ap}


class ReferenceFrameAnalyzer:
    def __init__(self):
        self.gated = GatedEventFrameAnalyzer()

    def analyze(self, text):
        frame = self.gated.frame
        prediction, vectors, dependencies = analyze_dependencies(frame.parser, text)
        decisions = event_decisions(prediction, vectors, self.gated.gate)
        frames = kept_frames(prediction, vectors, frame.mention_head, frame.role_head, decisions)
        return {"status": "research_reference_frames", "analysis": prediction,
                "event_decisions": decisions, "frames": frames, "dependencies": dependencies,
                "references": frame_references(prediction, dependencies["phrases"], frames)}
