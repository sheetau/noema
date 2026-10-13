import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_motion_question import selector_checks, generic_checks, source_checks, attribution_checks, alignment
from scripts.compose_motion_question import ROOT, generic_composed, source_composed


@pytest.fixture(scope='module')
def motion():
    return source_checks()['cases']


def test_equation_description_reuses_language_outside_motion():
    result=generic_checks();rows=result['cases']
    assert len(rows)==11
    for name in ('exact_area','reordered','duplicate','outside_scope_irrelevant'):
        assert rows[name]==[True,True]
    for name in ('empty_equations','extra_solution','excluded_target','invalid_side','empty_scope','empty_target','missing_target'):
        assert rows[name]==[False,False]
    assert result['unbounded_answer_enumeration_rejected']


def test_boolean_side_selection_keeps_strict_cut_boundaries():
    result=selector_checks()['cases']
    assert len(result)==10
    assert result['True:-3']==[True] and result['True:-2']==[False]
    assert result['False:0']==[True] and result['False:3']==[False]


def test_satisfying_motion_equations_is_weaker_than_describing_whole_trajectory(motion):
    assert motion['baseline']==[True]*5
    assert motion['excess_solution']==[False,False,False,True,True]
    assert motion['off_curve_event']==[False,False,False,False,True]


def test_answer_preserves_record_equivalence_and_all_event_representation(motion):
    assert motion['value_alias']==[True]*5
    for name in ('missing_record','invalid_record','unselected_event','incorrect_component'):
        assert motion[name]==[False,False,False,False,True]
    for name in ('wrong_point','wrong_frame','wrong_setting','empty_history'):
        assert motion[name]==[False]*5


def test_asking_does_not_execute_question_or_candidate():
    result=attribution_checks()
    assert len(result['cases'])==5 and result['cases']['baseline']==[True]
    assert all(value==[False] for name,value in result['cases'].items() if name!='baseline')
    assert result['question_and_candidate_not_executed_by_attribution']


def test_question_does_not_insert_known_velocity_answer():
    doc=parse(source_composed()[0]);definitions={d['name']:d for d in doc['declarations']}
    def symbols(node):
        if isinstance(node,list):return set().union(*(symbols(x) for x in node)) if node else set()
        if not isinstance(node,dict):return set()
        return ({node['symbol']} if 'symbol' in node else set())|set().union(*(symbols(x) for x in node.values()))
    reached=set();pending=['sze']
    while pending:
        name=pending.pop()
        if name in reached:continue
        reached.add(name);pending.extend(symbols(definitions[name].get('body'))-reached)
    assert 'szb' in reached and 'szj' in reached
    assert not reached & {'szf','szg','syt','syv','syz','sys','soy'}
    assert doc['statements'][-1]['body']['symbol']=='zdc'


def test_source_alignment_only_adds_question_sentence():
    result=alignment();sentence,frame=result['segments']
    assert sentence['unit']=='einstein-1905:u0133'
    assert sentence['source']=='Gesucht ist die Bewegung des Punktes relativ zum System [M0249].'
    assert frame['math_id']=='M0249'
    assert result['verified_full_units']==0 and not result['facsimile_checked']


def test_roundtrip_basis_and_preserved_parent():
    for compose,counts in ((generic_composed,(0,11)),(source_composed,(467,671))):
        text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'])==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-velocity-components.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-1]==parent['statements'] and len(doc['statements'])==129
