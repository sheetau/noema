import itertools
import json
import math
import random
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from noema.joint_lexical import JointLexicalAnalyzer, log_probabilities, solve_frame
from noema.lexical_frame_metrics import oracle_queries
from noema.semantics import SemanticError


CONCEPTS = {'a': {'kind': 'entity'}, 'b': {'kind': 'place'},
            'p': {'kind': 'event', 'roles': ['agent', 'location']},
            'q': {'kind': 'state', 'roles': ['agent']}}
LABELS = ('none', 'agent', 'location')


def brute_force(predicates, arguments, roles):
    feasible = []
    for predicate in ('p', 'q'):
        for choices in itertools.product(list(itertools.product(range(3), sorted(CONCEPTS))), repeat=len(arguments)):
            used, score, valid = set(), predicates[predicate], True
            for i, (index, concept) in enumerate(choices):
                role = LABELS[index]
                if index:
                    if role in used or role not in CONCEPTS[predicate]['roles']:
                        valid = False
                        break
                    used.add(role)
                    if CONCEPTS[concept]['kind'] != ('place' if role == 'location' else 'entity'):
                        valid = False
                        break
                score += roles[i][role] + arguments[i][concept]
            if valid:
                feasible.append((score, predicate, choices))
    score, predicate, choices = min(feasible, key=lambda x: (-x[0], x[1], x[2]))
    return {'predicate': predicate, 'score': score,
            'arguments': [{'role': LABELS[i], 'concept': c} for i, c in choices]}


def test_dynamic_program_agrees_with_exhaustive_search_including_ties():
    rng = random.Random(17)
    for n in range(4):
        for _ in range(15):
            predicates = {c: rng.randint(-5, 0) for c in CONCEPTS}
            arguments = [{c: rng.randint(-5, 0) for c in CONCEPTS} for _ in range(n)]
            roles = [{r: rng.randint(-5, 0) for r in LABELS} for _ in range(n)]
            assert solve_frame(predicates, arguments, roles, CONCEPTS, LABELS) == brute_force(predicates, arguments, roles)


def test_joint_assignment_can_reserve_role_for_stronger_later_argument():
    predicates = dict.fromkeys(CONCEPTS, -100)
    predicates['p'] = 0
    arguments = [dict.fromkeys(CONCEPTS, 0) for _ in range(2)]
    roles = [{'none': -2, 'agent': 0, 'location': -1}, {'none': -9, 'agent': 0, 'location': -8}]
    result = solve_frame(predicates, arguments, roles, CONCEPTS, LABELS)
    assert [a['role'] for a in result['arguments']] == ['location', 'agent']


def test_none_includes_latent_concept_score_and_empty_frame_is_allowed():
    scores = dict.fromkeys(CONCEPTS, -4)
    result = solve_frame(scores, [scores], [{'none': 0, 'agent': -2, 'location': -2}], CONCEPTS, LABELS)
    assert result['score'] == -8
    assert result['arguments'] == [{'role': 'none', 'concept': 'a'}]
    assert solve_frame(scores, [], [], CONCEPTS, LABELS)['arguments'] == []


def test_log_scores_are_stable_and_invalid_scores_fail():
    values = log_probabilities([10000, 10001], 10)
    assert sum(math.exp(x) for x in values) == pytest.approx(1)
    assert values[1] - values[0] == pytest.approx(10)
    for invalid in ([], [float('nan')], [float('inf')]):
        with pytest.raises(SemanticError):
            log_probabilities(invalid)
    with pytest.raises(SemanticError):
        solve_frame(dict.fromkeys(CONCEPTS, float('nan')), [], [], CONCEPTS, LABELS)


def test_forward_hook_is_removed_after_upstream_failure():
    head = torch.nn.Linear(1, 1)
    def fail(text):
        head(torch.ones(1, 1))
        raise RuntimeError('upstream failure')
    analyzer = JointLexicalAnalyzer.__new__(JointLexicalAnalyzer)
    analyzer.base = SimpleNamespace(structure=SimpleNamespace(frame=SimpleNamespace(role_head=head)), analyze=fail)
    with pytest.raises(RuntimeError, match='upstream failure'):
        analyzer.analyze('text')
    assert not head._forward_hooks


def test_confirmation_annotations_are_valid_and_include_unrepresentable_roles():
    rows = json.loads(Path('data/joint-lexical-v2.json').read_text(encoding='utf-8'))
    assert len(rows) == len({r['id'] for r in rows}) == 14
    queries = [q for row in rows for q in oracle_queries(row)]
    assert sum(q['expected'] is None for q in queries) == 1
    assert any(role == 'instrument' for row in rows for frame in row['frames'] for role, _, _ in frame['roles'])
