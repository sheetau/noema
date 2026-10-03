import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_relative_simultaneity import (
    alignment, attribution_checks, comparison_scope_checks, local_time_checks, logical_checks, numeric_checks,
    polynomial_checks, projected_uniqueness,
)
from scripts.check_rod_comparison import callbacks, guarded
from scripts.check_rod_measurements import cut
from scripts.compose_relative_simultaneity import ROOT, generic_composed, source_composed


def test_frame_dependence_does_not_mean_every_pair_changes_or_missing_times_are_unequal():
    result=logical_checks();rows=result['cases']
    assert len(rows)==128 and result['invariance_iff_no_disagreement_checked']
    assert result['changing_and_preserved_pairs_together']==[False,True,True,False]
    for row in rows:
        if not all(row['bits'][:4]):assert row['results']==[True,False,False,True]
    gain=next(r for r in rows if r['bits']==[True]*4+[False,True,True])
    assert gain['results']==[False,False,True,True]


def test_longitudinal_gap_speed_sign_and_shared_origin_have_distinct_effects():
    rows=numeric_checks()
    assert len(rows)==12 and sum(row['relation'] for row in rows.values())==7
    assert rows['longitudinal_separation']=={'relation':True,'source_simultaneous':True,'target_simultaneous':False}
    assert rows['same_longitudinal_coordinate']==rows['zero_relative_speed']=={
        'relation':True,'source_simultaneous':True,'target_simultaneous':True}
    assert rows['simultaneous_only_in_target']=={'relation':True,'source_simultaneous':False,'target_simultaneous':True}


def test_time_mixing_proves_restricted_loss_and_refutes_both_overgeneralizations():
    rows=polynomial_checks()
    assert len(rows)==7 and sum(r['status']=='valid' for r in rows.values())==5
    assert rows['existing_four_coordinate_equations_imply_time_component']['status']=='valid'
    assert rows['all_nonzero_motion_destroys_every_simultaneous_pair']['status']=='invalid'
    assert rows['all_simultaneous_pairs_stay_simultaneous']['status']=='invalid'


def test_local_time_requires_same_event_frame_unit_reference_and_actual_reading():
    result=local_time_checks();rows=result['cases']
    assert len(rows)==16 and {k for k,v in rows.items() if v}=={'baseline'}
    assert not result['full_real_uniqueness_evaluated']


def test_a_valid_selected_reading_does_not_establish_unique_time():
    result=projected_uniqueness();rows=result['cases']
    assert len(rows)==8 and not result['real_cut_uniqueness_proved']
    assert next(r for r in rows if r['selected']==['alias','seven'])['results']==[True,True]
    assert next(r for r in rows if r['selected']==['nine','seven'])['results']==[False,True]
    assert next(r for r in rows if r['selected']==[])['results']==[False,False]


def test_unbounded_cut_uniqueness_is_refused_even_with_a_valid_selected_time():
    doc=candidate(source_composed()[0],'''
r ja[] a.r jb[] a.r jc[] a.r jd[] d.r je[] h[a a a a d] c.r jf[] h[h[b] c] c.r jg[] h[h[b] c h[b] c] c.
q[k seh[k ja[] k jb[] k jc[] k jd[] k je[] k jf[] k jg[]]].''')
    model=guarded(doc)
    model.update(ja=lambda:'event',jb=lambda:'frame',jc=lambda:'unit',jd=lambda:'comparison',
        zbe=lambda *args:cut(7),zbh=lambda *args:'reference',ca=lambda clock:True,cb=lambda *args:True,
        cc=lambda *args:True,ci=lambda unit:True,ce=lambda *args:True)
    callbacks(doc,model,{'je':lambda *args:True,'jf':lambda value:True,'jg':lambda a,b:True})
    with pytest.raises(ValueError,match='rational number domain'):
        evaluate_document(doc,individuals=('event','frame','unit','reference'),situations=('comparison',),primitives=model)


def test_relative_motion_and_longitudinal_restriction_preserve_frame_unit_and_context():
    result=comparison_scope_checks();rows=result['cases']
    assert len(rows)==12 and rows['baseline']==rows['negative_speed']==[True,True]
    assert rows['same_longitudinal_position']==rows['invalid_position']==[True,False]
    assert rows['zero_speed']==rows['wrong_unit']==rows['wrong_context']==[False,False]
    assert not result['full_real_scope_evaluated']


def test_author_generalization_does_not_execute_the_unproved_contents():
    rows=attribution_checks()
    assert len(rows)==7 and rows['baseline']==[True,True]
    assert rows['wrong_premise']==rows['wrong_conclusion']==[False,True]
    assert rows['reversed_contrast']==[True,False]


def test_alignment_discloses_added_scope_and_keeps_full_equivalence_unverified():
    result=alignment();row=result['segments'][0]
    assert row['unit']=='einstein-1905:u0041'
    assert result['longitudinal_scope_is_explicit_interpretive_addition']
    assert not row['full_semantic_equivalence'] and not result['facsimile_checked']
    assert result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,9)),(source_composed,(200,145))])
def test_basis_roundtrip_and_preceding_source_are_preserved(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-observer-judgments.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-2]==old['statements'] and len(doc['statements'])==25
