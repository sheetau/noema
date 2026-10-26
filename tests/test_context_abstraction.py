from copy import deepcopy
import pytest
from noema.constructed_discourse import normalize_document
from scripts.context_abstraction import abstract, instantiate
from scripts.check_manuscript_context import (
    SPECS, inventory, interfaces, document, template, slice_for, names_for, restored, diagnostics)
from scripts.shared_modality import call, op, v
from scripts.shared_reference import definition
from scripts.shared_time import q
from scripts.shared_focus import quote


def small(body, *, helpers=()):
    return normalize_document(dict(schema_version='0.16', lexicon_version='0.16', declarations=[
        dict(kind='primitive', name='anchor', parameters=[], result='individual'),
        dict(kind='primitive', name='property', parameters=['individual'], result='truth'),
        *helpers, definition('target', [], 'truth', body)], statements=[]))


def test_context_audit_uses_actual_types_not_zero_arity_as_a_name_test():
    inv = inventory()
    assert inv['kant-1784']['result_kinds'] == dict(individual=467, situation=40, sequence=2, number=2)
    assert inv['einstein-1905']['result_kinds'] == dict(individual=799, situation=22, function=234, sequence=3, number=12)
    assert sum(r['zero_argument_primitives'] for r in inv.values()) == 1581
    assert inv['kant-1784']['quoted_directly'] == 16
    assert inv['einstein-1905']['quoted_directly'] == 0
    # A zero direct count does not mean definitions containing contextual
    # references are never quoted; this inventory deliberately says "direct".


@pytest.mark.parametrize('work', SPECS)
def test_actual_source_slice_is_reconstructed_without_refreshing_old_judgments(work):
    doc, records = template(work)
    assert instantiate(doc, records, slice_for(work), SPECS[work]['target'], names_for(work)) == slice_for(work)
    assert not interfaces()[work]['source_assertion_migrated']
    assert all(d['kind'] == 'definition' for d in doc['declarations'])


def test_saved_geometry_and_small_distinguishing_contexts():
    assert restored()['document'] == document()
    rows = diagnostics()
    assert len(rows) == 38 and all(r['original'] == r['template'] == r['expected'] for r in rows)


def test_nested_binder_is_not_captured_and_direct_primitive_call_is_restored():
    original = small(q('forall', 'contextvalue', 'individual',
        op('and', call('property', v('contextvalue')), op('equal', v('contextvalue'), call('anchor')))))
    doc, records = abstract(original, 'target', {'target':'template'}, {'anchor':'referent','property':'criterion'})
    restored_doc = instantiate(doc, records, original, 'target', {'target':'template'})
    assert restored_doc == original


def test_quoted_contextual_identity_is_not_silently_replaced():
    original = small(op('equal', quote(call('anchor')), quote(call('anchor'))))
    with pytest.raises(ValueError, match='Quoted contextual identity'):
        abstract(original, 'target', {'target':'template'}, {'anchor':'referent'})


def test_nullary_function_reference_and_explicit_application_remain_distinct():
    reference = dict(kind='function_ref',symbol='anchor')
    original = small(op('equal',reference,reference))
    with pytest.raises(ValueError, match='Nullary function reference'):
        abstract(original, 'target', {'target':'template'}, {'anchor':'referent'})
    original = small(dict(kind='apply',function=dict(kind='function_ref',symbol='property'),arguments=[call('anchor')]))
    with pytest.raises(ValueError, match='separate preservation rule'):
        abstract(original, 'target', {'target':'template'}, {'anchor':'referent','property':'criterion'})


def test_hidden_dependency_context_is_rejected():
    original = small(call('helper'), helpers=[definition('helper',[],'truth',call('property',call('anchor')))])
    with pytest.raises(ValueError, match='Dependency needs its own explicit context'):
        abstract(original, 'target', {'target':'template','helper':'helpercopy'}, {})


def test_incomplete_context_and_changed_reinstantiation_types_are_rejected():
    original = small(call('property',call('anchor')))
    with pytest.raises(ValueError, match='exactly'):
        abstract(original, 'target', {'target':'template'}, {'anchor':'referent'})
    doc, records = abstract(original, 'target', {'target':'template'}, {'anchor':'referent','property':'criterion'})
    bad = deepcopy(records); bad[0]['sort'] = 'situation'
    with pytest.raises(ValueError, match='type differs'):
        instantiate(doc,bad,original,'target',{'target':'template'})
    with pytest.raises(ValueError, match='Repeated context binding'):
        instantiate(doc,records+[records[0]],original,'target',{'target':'template'})
