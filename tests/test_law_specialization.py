from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_law_specialization import generic_checks, source_checks, field_binding_checks, attribution_checks, alignment
from scripts.compose_law_specialization import ROOT, PARENT, generic_composed, composed


def test_law_fitness_transfers_only_through_matching_content_bridges():
    result=generic_checks();rows=result['cases'];assert len(rows)==96
    assert all(row['result'][2] for row in rows)
    assert all(not row['result'][0] for row in rows if row['variant'] in ('missing_left','wrong_history','extra_disagrees'))
    assert result['same_fitness_does_not_imply_same_representation']
    rejected=next(r for r in rows if r['variant']=='baseline' and not any(r[k] for k in ('left_fit','right_fit','source','target')))
    assert rejected['result']==[True,True,True]


def test_full_principle_and_selected_history_are_both_needed():
    result=source_checks();rows=result['cases'];assert len(rows)==32
    assert rows['11:baseline']==[True,True,True,True]
    assert rows['10:baseline']==[False,True,False,False]
    assert rows['00:baseline']==[True,True,True,True]
    assert rows['11:wrong_selected_history']==rows['11:wrong_selected_law']==[True,False,False,True]
    assert rows['11:incomplete_scope']==rows['11:extra_disagrees']==[False,True,False,True]
    assert all(not r[2] or r[3] for r in rows.values())
    assert not result['arbitrary_physical_systems_verified']


def test_primed_fields_bind_frame_context_region_and_shared_light_speed():
    result=field_binding_checks();rows=result['cases'];assert len(rows)==8
    assert all(row==[name=='baseline'] for name,row in rows.items())
    assert result['six_equation_predicate_is_an_explicit_fixture_oracle']
    assert result['computed_mixed_fields_not_invoked']


def test_conditional_attribution_keeps_the_author_and_direction_without_disquotation():
    result=attribution_checks();rows=result['cases'];assert len(rows)==7
    assert all(row==[name=='baseline'] for name,row in rows.items())
    assert result['quoted_contents_not_executed_as_truth']


def test_source_ranges_exclude_unexplained_force_and_mass_definitions():
    result=alignment();rows=result['segments'];assert len(rows)==9
    ranges=[r for r in rows if 'start' in r];assert len(ranges)==2
    assert all('ponderomotorischen' not in r['source'] and 'Massen' not in r['source'] for r in ranges)
    assert {r['math_id'] for r in rows if 'math_id' in r}=={f'M{i:04}' for i in range(294,301)}
    assert result['verified_full_units']==0 and not result['facsimile_review']
    assert len(result['source_fraction_order'])==24


def test_inherited_source_and_both_notations_are_lossless():
    for builder,counts in ((generic_composed,(0,6,0)),(composed,(541,861,155))):
        text,basis=builder();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-1]==parent['statements']
    definitions={d['name']:d for d in doc['declarations']}
    assert all(d==definitions[d['name']] for d in parse(generic_composed()[0])['declarations'])
