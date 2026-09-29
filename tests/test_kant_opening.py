from copy import deepcopy
import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_kant_opening import DOCUMENT, BASIS, run_checks


def test_composed_definitions_preserve_guidance_causal_and_transition_distinctions():
    audit, cases = run_checks()
    assert len(cases) == 17
    assert all(c['actual'] == c['expected'] for c in cases.values())
    assert audit['primitive_count'] == 11 and audit['definition_count'] == 6
    assert audit['semantic_equivalence_to_source_proven'] is False


@pytest.mark.parametrize('mutation', ['missing', 'extra', 'duplicate', 'signature', 'arguments', 'meaning', 'definition'])
def test_semantic_conventions_cannot_silently_drift_from_the_document(mutation):
    doc = parse(DOCUMENT.read_text(encoding='utf-8'))
    basis = json.loads(BASIS.read_text(encoding='utf-8'))
    if mutation == 'missing':
        basis['primitives'].pop()
    elif mutation == 'extra':
        basis['primitives'].append({**basis['primitives'][0], 'symbol': 'zz'})
    elif mutation == 'duplicate':
        basis['primitives'].append(deepcopy(basis['primitives'][0]))
    elif mutation == 'signature':
        basis['primitives'][0]['result'] = 'individual'
    elif mutation == 'arguments':
        basis['primitives'][1]['arguments'] = ['x', 'x', 'x']
    elif mutation == 'meaning':
        basis['primitives'][0]['meaning_ja'] = ' '
    else:
        del basis['definitions']['be']
    with pytest.raises(ValueError):
        audit_basis(doc, basis)
