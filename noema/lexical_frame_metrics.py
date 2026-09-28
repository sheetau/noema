"""Evaluation-only alignment; never imported by the lexical inference API."""
from collections import Counter

from .language import policy
from .role_transfer import anchor, overlap
from .semantics import require


def oracle_queries(row):
    concepts = policy('0.7')[1]
    spans = {}
    for frame in row['frames']:
        entries = [(frame['predicate'], frame['concept']), *((s, c) for _, s, c in frame['roles'])]
        for text, concept in entries:
            require(concept is None or concept in concepts, 'Unknown annotated concept')
            span = anchor(row['text'], text)
            key = span['start'], span['end']
            require(key not in spans or spans[key] == concept, 'Conflicting annotated span concept')
            spans[key] = concept
    return [{'start': a, 'end': b, 'expected': c} for (a, b), c in sorted(spans.items())]


def assess_lexical_frames(row, result):
    require(result['source'] == row['text'], 'Lexical frame evaluation text differs')
    gold_predicates, predicted_predicates, gold_roles, predicted_roles = (Counter() for _ in range(4))
    gold_spans, predicted_spans = Counter(), Counter()
    anchors = [anchor(row['text'], f['predicate']) for f in row['frames']]
    for i, frame in enumerate(row['frames']):
        gold_predicates[i, frame['concept']] += 1
        for role, surface, concept in frame['roles']:
            span = anchor(row['text'], surface)
            key = i, role, span['start'], span['end']
            gold_spans[key] += 1
            gold_roles[*key, concept] += 1
    for i, frame in enumerate(result['frames']):
        matches = [k for k, a in enumerate(anchors) if overlap(a, frame['predicate'])]
        require(len(matches) <= 1, 'Predicted event overlaps several annotated events')
        key = matches[0] if matches else f'unmatched-{i}'
        predicted_predicates[key, frame['predicate']['concept']] += 1
        for role in frame['roles']:
            item = key, role['role'], role['start'], role['end']
            predicted_spans[item] += 1
            predicted_roles[*item, role['concept']] += 1
    return {'id': row['id'], 'gold_frames': len(row['frames']), 'predicted_frames': len(result['frames']),
            'correct_predicate_concepts': sum((gold_predicates & predicted_predicates).values()),
            'gold_roles': gold_roles.total(), 'predicted_roles': predicted_roles.total(),
            'correct_role_spans': (gold_spans & predicted_spans).total(),
            'correct_role_span_concepts': (gold_roles & predicted_roles).total(),
            'missing_role_span_concepts': (gold_roles - predicted_roles).total(),
            'extra_role_span_concepts': (predicted_roles - gold_roles).total(),
            'core_frames_exact': gold_predicates == predicted_predicates and gold_roles == predicted_roles,
            'structurally_invalid_frames': sum(bool(f['structural_errors']) for f in result['frames']),
            'confirmed': result['confirmed']}


def summarize_lexical_frames(cases):
    counts = {key: sum(c[key] for c in cases) for key in cases[0] if key != 'id'} if cases else {}
    return {**counts, 'documents': len(cases), 'accepted_coverage': counts.get('confirmed', 0) / len(cases) if cases else None,
            'accepted_full_meaning_exact_accuracy': None, 'acceptance_gate_passed': False}
