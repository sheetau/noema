"""Joint typed role assignment, independent of any natural-language word rules.

The v4 decoder remains frozen in structured.py so its recorded evaluations can
still be reproduced. This decoder requires separate development calibration.
"""
import itertools
import math
import torch
from .structured import LABELS, bio_path
from .semantics import CONCEPTS, ROLES, SemanticError, make_graph


def spans_from_logits(text, logits):
    probabilities = logits.softmax(-1)
    spans, current = [], None
    for i, label_id in enumerate(bio_path(logits, text)):
        label = LABELS["span"][label_id]
        if label == "O":
            current = None
        elif label.startswith("B-"):
            current = {"kind": label[2:], "start": i, "end": i + 1, "indices": [i], "scores": [float(probabilities[i, label_id])]}
            spans.append(current)
        else:
            current["end"] = i + 1
            current["indices"].append(i)
            current["scores"].append(float(probabilities[i, label_id]))
    return spans


def assign_roles(predicate, concepts, probabilities, frame):
    """Exact maximum likelihood assignment under the independently predicted frame.

    No missing entity is invented and no predicted frame bit is changed. All
    admissible assignments are scored; ties remain unresolved. Confidence keeps
    both raw role evidence and the posterior over valid assignments.
    """
    roles = [r for i, r in enumerate(ROLES) if frame & (1 << i)]
    if len(roles) != len(concepts) or not set(roles) <= set(CONCEPTS[predicate]["roles"]):
        raise SemanticError("Role presence and extracted entities disagree")
    candidates = []
    for assignment in itertools.permutations(roles):
        if any((CONCEPTS[c]["kind"] == "place") != (r == "location") for c, r in zip(concepts, assignment)):
            continue
        values = [float(p[LABELS["role"].index(r)]) for p, r in zip(probabilities, assignment)]
        score = sum(math.log(max(v, 1e-30)) for v in values)
        candidates.append((score, assignment, values))
    if not candidates:
        raise SemanticError("No typed role assignment")
    candidates.sort(key=lambda c: c[0], reverse=True)
    if len(candidates) > 1 and abs(candidates[0][0] - candidates[1][0]) < 1e-7:
        raise SemanticError("Ambiguous role assignment")
    best, assignment, values = candidates[0]
    posterior = 1 / sum(math.exp(score - best) for score, _, _ in candidates)
    evidence = math.exp(best / len(values)) if values else 1.
    return assignment, min(posterior, evidence), {"valid_assignments": len(candidates), "posterior": posterior, "role_evidence": evidence}


def decode(text, feature, logits, threshold=0.):
    result = {"status": "unresolved", "graph": None, "diagnostics": {"confidence": 0., "spans": [], "reason": None}}
    diag = result["diagnostics"]
    if feature["truncated"]:
        diag["reason"] = "input_too_long"
        return result
    if not text.strip():
        result["status"], diag["reason"] = "unsupported", "empty_input"
        return result
    probs = {k: v.softmax(-1) for k, v in logits.items() if k != "attachment"}
    support = float(probs["support"][1])
    if support < .5:
        result["status"], diag["reason"], diag["confidence"] = "unsupported", "support_classifier", 1 - support
        return result
    confidences = [support]

    def choose(key, indices=None):
        values = probs[key] if indices is None else probs[key][indices].mean(0)
        value, index = values.max(-1)
        confidences.append(float(value))
        return LABELS[key][int(index)]

    try:
        spans = spans_from_logits(text, logits["span"])
        predicates, entities, quantities, times = [], [], [], []
        for span in spans:
            confidences.append(sum(span["scores"]) / len(span["scores"]))
            start, end = span["start"], span["end"]
            while start < end and text[start].isspace():
                start += 1
            while end > start and text[end - 1].isspace():
                end -= 1
            evidence = {"start": start, "end": end, "kind": span["kind"], "text": text[start:end]}
            span["evidence"] = evidence
            diag["spans"].append(evidence)
            if span["kind"] in ("predicate", "entity"):
                concept = choose("concept", span["indices"])
                evidence["concept"] = concept
                if concept not in CONCEPTS:
                    raise SemanticError("Unknown concept prediction")
                if span["kind"] == "predicate":
                    if CONCEPTS[concept]["kind"] not in ("event", "state"):
                        raise SemanticError("Expected an event or state predicate")
                    predicates.append(concept)
                else:
                    if CONCEPTS[concept]["kind"] not in ("entity", "place"):
                        raise SemanticError("Expected an entity or place")
                    entities.append(span)
            elif span["kind"] == "quantity":
                literal = evidence["text"]
                if (not literal.isdecimal() or start and text[start - 1].isdecimal()
                        or end < len(text) and text[end].isdecimal()):
                    raise SemanticError("Quantity requires a complete decimal literal")
                quantities.append(span)
            elif span["kind"] == "time":
                times.append(choose("explicit_time", span["indices"]))
        if len(predicates) != 1:
            raise SemanticError("Expected exactly one predicate")
        if len(times) > 1:
            raise SemanticError("Multiple time scopes")
        frame = int(choose("frame"))
        roles, confidence, assignment_info = assign_roles(predicates[0], [e["evidence"]["concept"] for e in entities],
                                                          [probs["role"][e["indices"]].mean(0) for e in entities], frame)
        confidences.append(confidence)
        diag["role_assignment"] = assignment_info
        nodes = {}
        for span, role in zip(entities, roles):
            evidence = span["evidence"]
            evidence["role"] = role
            concept = evidence["concept"]
            nodes[role] = {"concept": concept, "quantity": None, "name": evidence["text"] if concept == "ag" else None}
        for quantity in quantities:
            if not entities:
                raise SemanticError("Quantity has no entity")
            scores = logits["attachment"][quantity["indices"]].mean(0)
            values = scores[[e["indices"][0] for e in entities]].softmax(-1)
            confidence, index = values.max(0)
            confidences.append(float(confidence))
            role = roles[int(index)]
            if nodes[role]["quantity"] is not None:
                raise SemanticError("Multiple quantities attached to one entity")
            nodes[role]["quantity"] = int(quantity["evidence"]["text"])
            quantity["evidence"].update(role=role, target_start=entities[int(index)]["evidence"]["start"])
        graph = make_graph(predicates[0], nodes, choose("polarity"), times[0] if times else choose("time"))
        diag["confidence"] = min(confidences)
        if diag["confidence"] >= threshold:
            result["status"], result["graph"] = "confirmed", graph
        else:
            diag["reason"] = "low_confidence"
    except SemanticError as exc:
        diag["reason"], diag["confidence"] = "inconsistent_structure: " + str(exc), min(confidences)
    return result
