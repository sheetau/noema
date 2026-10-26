from copy import deepcopy
from fractions import Fraction
import json
import pytest

from noema.constructed_semantics import evaluate_document
from scripts import check_einstein_designation_purpose as check
from scripts import designation_purpose_profile as profile
from scripts import check_einstein_discourse_setting as previous
from scripts.discourse_setting_profile import DiscourseSettingVocabulary,DiscourseReferences
from scripts.name_presentation_profile import NamePresentation
from scripts.shared_modality import call
from scripts.visible_vectors_vocabulary import VectorsVocabulary
from scripts.visible_collection import decode_collection
from scripts.visible_syntax_geometry import from_svg


def test_profile_preserves_prior_semantics_and_distinct_spellings():
    old=DiscourseSettingVocabulary();new=check.vocabulary();math=VectorsVocabulary()
    assert len(old._words)==391 and len(new._words)==397
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new.document()[field][n]==d for n,d in old.document()[field].items())
    assert not ({new._symbols[n] for n in profile.PARAMETERS}&set(math._by_symbol))


def test_visible_document_preserves_first_sentence_and_covers_the_two_sentence_paragraph():
    doc=check.restored()['document'];assert doc==check.document()
    assert len(doc['declarations'])==53 and len(doc['statements'])==5
    assert doc['statements'][:3]==previous.document()['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in previous.document()['declarations'])
    assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['paragraph_ranges']==[[0,95],[96,266]] and b['inter_sentence_whitespace']==[95,96]
    assert b['newly_connected_source_assertions']==1 and b['total_connected_source_assertions']==3
    assert check.visible_form(doc)==dict(designation=check.names()['eiseb'],language='de',text='ruhende System',context=check.names()['ri'])


def test_statement_forces_and_quoted_purposes_are_preserved_separately():
    ds={d['name']:d for d in check.document()['declarations']};n=check.names()
    assert ds[n['eihv']]['body']['force']=='direct' and ds[n['eih4']]['body']['force']=='assert'
    goals=ds[n['eih3']]['body']['body']['arguments'][1]['arguments']
    assert [g['arguments'][1] for g in goals]==[dict(kind='quote',body=call(n['eih2']))]*2
    assert [g['arguments'][2] for g in goals]==[dict(kind='quote',body=call(n[s])) for s in ('eihy','eihz')]
    # The whole anticipated range remains a function description.
    alt=ds[n['eihy']]['body']['body']['arguments'][2]
    assert alt==dict(kind='quote',body=dict(kind='function_ref',symbol=n['eihx']))


def test_each_binding_and_both_purposes_have_distinguishing_diagnostics():
    rows=check.diagnostics();assert len(rows)==59
    assert all(row['answer']['value'] is row['expected'] for row in rows)
    masks=rows[42:50]
    assert [r['answer']['value'] for r in masks]==[False]*7+[True]
    for row in masks:
        goals=[x['arguments'][2] for x in row['calls'] if x['relation'].startswith('purpose_')]
        assert set(goals)=={'eihy','eihz'}


def test_same_frame_is_excluded_even_when_it_is_physical_and_anticipated():
    row=check.interpreted_pair(target='eihx',candidate='x')
    assert row['answer']['value'] is False
    assert row['calls']==[dict(relation='physicalframe',arguments=['x']),
                          dict(relation='anticipatedreferent',arguments=['x','y','x','body'])]


def test_goals_are_not_executed_by_the_purpose_relation_and_naming_is_not_executed_by_attribution():
    row=check.interpreted_pair(target='eih3',truths=dict(designationdistinguishes=False,designationclarifies=False,anticipatedreferent=False,physicalframe=False))
    assert row['answer']['value'] is True
    assert {c['relation'] for c in row['calls']}=={'adoptsdesignation','purpose_distinguish','purpose_clarify'}
    row=check.interpreted_pair(target='eih5',truths=dict(adoptsdesignation=False,purpose_distinguish=False,purpose_clarify=False))
    assert row['answer']['value'] is True
    assert [c['relation'] for c in row['calls']]==['presentsmessage','textbefore']


def test_whole_paragraph_and_two_names_share_document_but_keep_contexts_and_force():
    model=NamePresentation('front',{('front',2):('use','name','author','doc')},
        presented={('use','front'):True},applied={('use','name','author','front'):True},
        authors={('use','doc','author','front'):True},
        forms={('name','de','A. Einstein','front'):True,('designation','de','ruhende System','body'):True})
    refs=DiscourseReferences({'doc':'body'},{('body',2):'heading'},
        {('body',4,1):'first',('body',4,2):'second'},{('doc','first',1,'body'):'frame'})
    designations=profile.DesignationReferences({('doc','second',1,'body'):'designation'})
    calls=[];n=check.names()
    def unexpected(*args):raise AssertionError('A quoted act, purpose or physical condition was executed')
    def presents(node,person,doc,message,context):
        assert (person,doc,context)==('author','doc','body')
        expected={'first':'eihv','second':'eih4'}[node]
        assert json.loads(message.syntax)==call(n[expected]);calls.append(node);return True
    order=['heading','first','second']
    handlers=model.handlers()|refs.handlers()|designations.handlers()|dict(
        presentsmessage=presents,textbefore=lambda a,b,s:s=='body' and order.index(a)<order.index(b),
        adoptsassumption=unexpected,introducesreferent=unexpected,newtonianframe=unexpected,physicalframe=unexpected,
        **{name:unexpected for name in profile.SOURCE_RELATIONS.values()})
    result=evaluate_document(check.restored()['document'],
        individuals=('use','name','author','doc','heading','first','second','frame','designation'),
        situations=('front','body'),primitives={check.vocabulary()._symbols[n]:f for n,f in handlers.items()})
    assert [r['value'] for r in result]==[True]*5 and calls==['first','second']


def test_unknown_designation_positions_are_rejected_without_implying_naming():
    r=profile.DesignationReferences({('doc','node',1,'body'):'name'})
    assert r.reference('doc','node',Fraction(1),'body')=='name'
    assert set(r.handlers())=={'designationreference'}
    for args in [('other','node',1,'body'),('doc','other',1,'body'),('doc','node',2,'body'),('doc','node',1,'front')]:
        with pytest.raises(ValueError,match='Unknown'):r.reference(*args)


@pytest.mark.parametrize('position',[0,-1,True,1.0,Fraction(3,2)])
def test_designation_order_requires_positive_exact_integers(position):
    with pytest.raises(ValueError):profile.DesignationReferences({('doc','node',position,'body'):'name'})


def test_changed_goal_reference_force_or_printed_form_cannot_reuse_evidence():
    n=check.names()
    for mutation in ('goal','force','form'):
        doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']}
        if mutation=='goal':
            goals=ds[n['eih3']]['body']['body']['arguments'][1]['arguments']
            goals[1]['arguments'][2]=deepcopy(goals[0]['arguments'][2])
        elif mutation=='force':ds[n['eih4']]['body']['force']='direct'
        else:doc['statements'][4]['body']['arguments'][2]['items'][0]['numerator']=82
        with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)


def test_previous_profile_rejects_new_profile_header():
    pages=[from_svg(p.read_text(encoding='utf-8')) for p in sorted(check.OUT.glob('*.svg'))]
    with pytest.raises(ValueError):decode_collection(pages,DiscourseSettingVocabulary())
