import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_measurements import cut
from scripts.check_carried_clocks import alignment, attribution_checks, guarded, point_checks, source_checks
from scripts.compose_carried_clocks import ROOT, generic_composed, source_composed


def test_current_position_reading_needs_both_records_and_value_agreement():
    rows=point_checks()
    assert len(rows)==64 and sum(r['accepted'] for r in rows)==1
    assert next(r for r in rows if r['accepted'])['conditions']==[True]*6


def test_carried_clocks_track_each_local_time_without_being_stationary():
    result=source_checks();rows=result['cases']
    assert len(rows)==29
    assert {k for k,v in rows.items() if v}=={
        'moving_clocks_change_locations_and_local_comparators','two_ends_need_not_have_simultaneous_records'}
    assert not rows['later_carried_clock_drifts'] and not rows['old_local_clock_at_new_position']
    assert not rows['local_is_carried_clock'] and not rows['reference_is_carried_clock']
    assert not rows['one_clock_has_no_records'] and not rows['incomplete_record_scope']
    assert not result['carried_clocks_in_stationary_clock_set']
    assert not result['all_continuous_time_readings_verified']
    assert not result['natural_unadjusted_clock_rate_law_asserted']


def test_additional_setting_and_frame_qualified_name_do_not_execute_physics():
    rows=attribution_checks()
    assert len(rows)==7 and rows['baseline']==[True,True]
    assert rows['missing_extension']==rows['wrong_prior_setting']==[False,True]
    assert rows['wrong_qualification']==rows['wrong_frame']==[True,False]
    assert rows['wrong_author']==rows['wrong_scope']==[False,False]


def test_full_real_reading_validity_is_not_finitely_sampled():
    doc=candidate(source_composed()[0],'''
r ja[] a.r jb[] a.r jc[] a.r jd[] a.r je[] a.r jf[] h[b] c.r jg[] d.
q[k scv[k ja[] k jb[] k jc[] k jd[] k je[] k jf[] k jf[] k jg[] p qo p sca p ba]].''')
    model=guarded(doc)
    model.update(ja=lambda:'carried',jb=lambda:'endpoint',jc=lambda:'event',jd=lambda:'place',je=lambda:'local',
        jf=lambda:cut(5),jg=lambda:'motion',rc=lambda:'reference')
    with pytest.raises(ValueError,match='rational number domain'):
        evaluate_document(doc,individuals=('carried','endpoint','event','place','local','reference'),situations=('motion',),primitives=model)


def test_carried_clock_and_endpoint_alignment_is_partial():
    result=alignment()
    assert result['verified_full_units']==0 and len(result['segments'])==3
    assert all(r['unit']=='einstein-1905:u0035' and not r['full_semantic_equivalence'] for r in result['segments'])
    assert {r['math_id'] for r in result['segments'][1:]}=={'M0052','M0053'}


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,36)),(source_composed,(176,100))])
def test_basis_notation_roundtrips_and_previous_source_are_preserved(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-geometric-replacement.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-2]==old['statements'] and len(doc['statements'])==19
