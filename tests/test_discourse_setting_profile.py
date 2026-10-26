from copy import deepcopy
from fractions import Fraction
import pytest

from noema.constructed_semantics import evaluate_document
from scripts import check_einstein_discourse_setting as check
from scripts import discourse_setting_profile as profile
from scripts import check_einstein_name_presentation as author
from scripts.name_presentation_profile import NamePresentationVocabulary,NamePresentation
from scripts.visible_vectors_vocabulary import VectorsVocabulary
from scripts.visible_collection import decode_collection
from scripts.visible_syntax_geometry import from_svg


def test_profile_preserves_prior_semantics_and_uses_distinct_spellings():
    old=NamePresentationVocabulary();new=check.vocabulary();math=VectorsVocabulary()
    assert len(old._words)==383 and len(new._words)==391
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new.document()[field][n]==d for n,d in old.document()[field].items())
    assert not ({new._symbols[n] for n in profile.PARAMETERS}&set(math._by_symbol))


def test_whole_visible_document_contains_author_annotation_and_setting():
    doc=check.restored()['document'];assert doc==check.document()
    assert len(doc['declarations'])==38 and len(doc['statements'])==3
    assert doc['statements'][:2]==author.document()['statements']
    new={d['name']:d for d in doc['declarations']}
    assert all(new[d['name']]==d for d in author.document()['declarations'])
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.bridge()['source_range']==[0,95]


def test_five_definitions_keep_conditions_assumption_directive_and_attribution_distinct():
    ds={d['name']:d for d in check.document()['declarations']};n=check.names()
    assert ds[n['eihv']]['body']==dict(kind='message',force='direct',content=dict(kind='call',symbol=n['eihu'],arguments=[]))
    assert ds[n['eiht']]['result']=='content' and ds[n['eihu']]['result']=='content'
    assert ds[n['eihw']]['body']['arguments'][0]['arguments'][3]['kind']=='quote'


def test_each_reference_slot_and_relation_is_distinguished_in_native_bodies():
    rows=check.diagnostics();assert len(rows)==35
    assert all(r['answer']['value'] for r in rows[:5])
    assert all(not r['answer']['value'] for r in rows[5:-1])
    assert rows[-1]['answer']['value'] is True


def test_attribution_does_not_execute_settings_or_physical_conditions():
    row=check.interpreted_pair(truths=dict(introducesreferent=False,adoptsassumption=False,physicalframe=False,newtonianframe=False))
    assert row['answer']['value'] is True
    assert [c['relation'] for c in row['calls']]==['presentsmessage','textbefore']
    row=check.interpreted_pair(target='eihu',truths=dict(physicalframe=False,newtonianframe=False))
    assert row['answer']['value'] is True
    assert {c['relation'] for c in row['calls']}=={'introducesreferent','adoptsassumption'}


def test_combined_assertions_keep_frontmatter_and_body_contexts_separate():
    model=NamePresentation('front',{('front',2):('x','x','y','y')},
        presented={('x','front'):True},applied={('x','x','y','front'):True},
        authors={('x','y','y','front'):True},forms={('x','de','A. Einstein','front'):True})
    refs=profile.DiscourseReferences({'y':'body'},{('body',2):'x'},{('body',4,1):'y'},{('y','y',1,'body'):'x'})
    def unexpected(*args):raise AssertionError('Quoted setting was executed')
    def presents(node,person,doc,msg,s):
        assert (node,person,doc,s)==('y','y','y','body')
        return True
    handlers=model.handlers()|refs.handlers()|dict(presentsmessage=presents,
        textbefore=lambda a,b,s:(a,b,s)==('x','y','body'),adoptsassumption=unexpected,
        introducesreferent=unexpected,physicalframe=unexpected,newtonianframe=unexpected)
    handlers={check.vocabulary()._symbols[n]:f for n,f in handlers.items()}
    result=evaluate_document(check.restored()['document'],individuals=('x','y'),situations=('front','body'),primitives=handlers)
    assert [row['value'] for row in result]==[True,True,True]


def test_references_only_supply_values_and_unknown_input_is_rejected():
    refs=profile.DiscourseReferences({'doc':'body'},{('body',2):'heading'},
        {('body',4,1):'sentence'},{('doc','sentence',1,'body'):'frame'})
    h=refs.handlers()
    assert h['documentcontext']('doc')=='body'
    assert h['discoursereferent']('doc','sentence',Fraction(1),'body')=='frame'
    assert set(h)=={'documentcontext','headingreference','sentencereference','discoursereferent'}
    for operation in [lambda:h['documentcontext']('other'),lambda:h['headingreference']('front',2),
        lambda:h['headingreference']('body',1),lambda:h['sentencereference']('body',4,2),
        lambda:h['discoursereferent']('doc','sentence',2,'body'),lambda:h['discoursereferent']('doc','heading',1,'body')]:
        with pytest.raises(ValueError,match='Unknown'):operation()


@pytest.mark.parametrize('position',[0,-1,True,2.0,Fraction(3,2)])
def test_reference_positions_require_positive_exact_integers(position):
    with pytest.raises(ValueError):profile.DiscourseReferences({}, {('body',position):'heading'}, {}, {})


def test_changed_force_or_context_binding_cannot_reuse_source_evidence():
    doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']};n=check.names()
    ds[n['eihv']]['body']['force']='assert'
    with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)
    doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']}
    ds[n['ri']]['body']=dict(kind='call',symbol=n['eirg'],arguments=[])
    with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)


def test_old_profile_rejects_new_header():
    pages=[from_svg(p.read_text(encoding='utf-8')) for p in sorted(check.OUT.glob('*.svg'))]
    with pytest.raises(ValueError):decode_collection(pages,NamePresentationVocabulary())
