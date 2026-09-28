"""Exact frame-level concept/role decoding with frozen scores and schema constraints."""
import math

import torch

from .language import policy
from .lexical_frames import LexicalFrameAnalyzer
from .role_transfer import LABELS
from .semantics import require
from .shared_matcher import query_features, SETTINGS


def log_probabilities(values, scale=1.):
    require(values and all(math.isfinite(v) for v in values), 'Expected finite nonempty scores')
    require(math.isfinite(scale) and scale > 0, 'Invalid score scale')
    scaled = [v * scale for v in values]
    require(all(math.isfinite(v) for v in scaled), 'Score scaling overflow')
    maximum = max(scaled)
    normalizer = math.log(math.fsum(math.exp(v - maximum) for v in scaled))
    return [v - maximum - normalizer for v in scaled]


def best_concept(scores, concepts, kinds=None):
    choices = [(value, name) for name, value in scores.items() if kinds is None or concepts[name]['kind'] in kinds]
    return min(choices, key=lambda item: (-item[0], item[1])) if choices else None


def solve_frame(predicate_scores, argument_scores, role_scores, concepts, labels=LABELS):
    """Maximize the full fixed objective, not independent per-role argmaxes."""
    require(labels[0] == 'none' and len(set(labels)) == len(labels), 'Invalid role inventory')
    require(len(argument_scores) == len(role_scores), 'Argument/role score counts differ')
    require(set(predicate_scores) == set(concepts), 'Predicate score inventory differs')
    require(all(set(s) == set(concepts) for s in argument_scores), 'Argument score inventory differs')
    require(all(set(s) == set(labels) for s in role_scores), 'Role score inventory differs')
    require(all(math.isfinite(v) for scores in (predicate_scores, *argument_scores, *role_scores) for v in scores.values()),
            'Non-finite joint score')
    best = None
    for predicate in sorted(concepts):
        spec = concepts[predicate]
        if spec['kind'] not in ('event', 'state'):
            continue
        states = {0: (predicate_scores[predicate], ())}
        for scores, roles in zip(argument_scores, role_scores, strict=True):
            options = []
            for index, role in enumerate(labels):
                if role != 'none' and role not in spec['roles']:
                    continue
                kinds = None if role == 'none' else spec.get('role_types', {}).get(
                    role, ['place'] if role in ('location', 'source', 'destination') else ['entity'])
                concept = best_concept(scores, concepts, kinds)
                if concept is not None:
                    value, name = concept
                    options.append((0 if index == 0 else 1 << (index - 1), roles[role] + value, (index, name)))
            following = {}
            for mask, (value, assignments) in states.items():
                for bit, increment, assignment in options:
                    if mask & bit:
                        continue
                    target = mask | bit
                    candidate = value + increment, (*assignments, assignment)
                    prior = following.get(target)
                    if prior is None or candidate[0] > prior[0] or candidate[0] == prior[0] and candidate[1] < prior[1]:
                        following[target] = candidate
            states = following
        for value, assignments in states.values():
            candidate = value, predicate, assignments
            if best is None or candidate[0] > best[0] or candidate[0] == best[0] and candidate[1:] < best[1:]:
                best = candidate
    require(best is not None, 'No feasible frame assignment')
    value, predicate, assignments = best
    return {'predicate': predicate, 'score': value,
            'arguments': [{'role': labels[index], 'concept': concept} for index, concept in assignments]}


def all_queries(structure):
    pairs = {(s['start'], s['end']) for frame in structure['frames'] for s in (frame['predicate'], *frame['mentions'])}
    return [{'start': a, 'end': b} for a, b in sorted(pairs)]


def complete_concept_scores(matcher, text, spans):
    rows = [{'text': text, 'start': s['start'], 'end': s['end'], 'span': text[s['start']:s['end']]} for s in spans]
    if not rows:
        return {'ids': matcher.index.ids, 'spans': [], 'scores': []}
    features = query_features(matcher.encoder, rows)
    with torch.inference_mode():
        scores = matcher.head(features, matcher.index.vectors).tolist()
    return {'ids': matcher.index.ids, 'spans': spans, 'scores': scores}


def decode_joint(baseline, table, role_logits):
    concepts = policy('0.7')[1]
    require(table['ids'] == sorted(concepts), 'Joint concept inventory differs')
    require(table['spans'] == all_queries(baseline['structure']), 'Joint query positions differ')
    require(len(table['scores']) == len(table['spans']), 'Joint query score counts differ')
    require(all(len(row) == len(concepts) for row in table['scores']), 'Joint concept score width differs')
    distributions = {(s['start'], s['end']): dict(zip(table['ids'], log_probabilities(row, SETTINGS['temperature_multiplier']), strict=True))
                     for s, row in zip(table['spans'], table['scores'], strict=True)}
    require(len(role_logits) == len(baseline['structure']['frames']), 'Role forward count differs')
    frames, decisions, assignments_by_span = [], [], {}
    for frame, logits in zip(baseline['structure']['frames'], role_logits, strict=True):
        mentions = {m['id']: m for m in frame['mentions']}
        roles = frame['roles']
        require(len(mentions) == len(frame['mentions']) == len(roles) == len(logits), 'Joint mention/role inventory differs')
        require({r['target'] for r in roles} == set(mentions), 'Joint role targets differ from mentions')
        require(all(len(values) == len(LABELS) for values in logits), 'Joint role score width differs')
        require(all(LABELS[max(range(len(LABELS)), key=lambda j: values[j])] == role['role']
                    for values, role in zip(logits, roles, strict=True)), 'Native role decisions differ from captured scores')
        spans = [mentions[r['target']] for r in roles]
        p = frame['predicate']
        decoded = solve_frame(distributions[p['start'], p['end']],
                              [distributions[s['start'], s['end']] for s in spans],
                              [dict(zip(LABELS, log_probabilities(v), strict=True)) for v in logits], concepts)
        output_roles = []
        for span, choice in zip(spans, decoded['arguments'], strict=True):
            if choice['role'] == 'none':
                continue
            output_roles.append({'start': span['start'], 'end': span['end'], **choice})
            assignments_by_span.setdefault((span['start'], span['end']), set()).add(choice['concept'])
        errors = ['named_person_requires_name_extraction'] if any(r['concept'] == 'ag' for r in output_roles) else []
        frames.append({'source': frame['source'], 'predicate': {'start': p['start'], 'end': p['end'], 'concept': decoded['predicate']},
                       'roles': output_roles, 'structural_errors': errors})
        decisions.append({'source': frame['source'], **decoded})
    conflicts = [{'start': a, 'end': b, 'concepts': sorted(values)} for (a, b), values in sorted(assignments_by_span.items()) if len(values) > 1]
    return {'status': 'research_joint_lexical_frames', 'confirmed': False, 'document': None, 'source': baseline['source'],
            'frames': frames, 'decisions': decisions, 'cross_frame_concept_conflicts': conflicts,
            'missing_components': [*baseline['missing_components'], 'extended_roles', 'document_level_joint_inference']}


class JointLexicalAnalyzer:
    def __init__(self):
        self.base = LexicalFrameAnalyzer()
        self.metadata = {**self.base.metadata, 'decision': 'exact_per_frame_schema_constrained_sum_log_scores',
                         'concept_multiplier': SETTINGS['temperature_multiplier'], 'score_weights': [1., 1.],
                         'role_labels': list(LABELS), 'training': False}

    def analyze(self, text):
        captured = []
        hook = self.base.structure.frame.role_head.register_forward_hook(
            lambda module, args, result: captured.append(result.detach().cpu().clone()))
        try:
            baseline = self.base.analyze(text)
        finally:
            hook.remove()
        role_logits = [tensor.tolist() for tensor in captured]
        table = complete_concept_scores(self.base.matcher, text, all_queries(baseline['structure']))
        joint = decode_joint(baseline, table, role_logits)
        return {'baseline': baseline, 'joint': joint, 'concept_table': table, 'role_logits': role_logits}
