"""Whole selected source bodies, quoted title content and author-reference scope."""
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_title_author_visible as check
from scripts.closing_presentation_profile import ClosingPresentationReferences
from scripts.shared_modality import renamed
from scripts.check_explanatory_question import query_syntax


def forbidden(*args):raise ValueError('Unspecified title content or relation was evaluated')


def test_selected_source_bodies_and_visible_references_are_complete():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(check.source_excerpt()['declarations'])==60 and len(doc['statements'])==3
    ds={d['name']:d for d in doc['declarations']}
    for name in ('wa','wh','hzia','hzif','hzig','hzik','hzim'):
        assert ds[check.names()[name]]['kind']=='definition'
    assert check.bridge()['source_statement_indices']==[0,16]
    assert set(check.SHARED)=={'xa','xd','xe'}


def model(doc,*,question=True,bits=(True,True,True),same_name=False,body_context='body'):
    vocabulary=check.vocabulary();m=check.mapping()
    result={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    name='author' if same_name else 'designation'
    references=ClosingPresentationReferences({('closing',1):'signature'},
        {('closing',1):('use',name,'author','document')})
    expected=renamed(query_syntax('bi','wh','hzv6'),m)
    def context(document):
        if document!='document':raise ValueError('Unknown document')
        return body_context
    def frontmatter(context,item):
        if (context,item)!=('closing',6):raise ValueError('Unknown title location')
        return 'title'
    handlers=dict(textpresentation=lambda:'closing',closingpresentationrecord=references.record,
        documentcontext=context,frontmatterreference=frontmatter,
        presentspropertyquestion=lambda node,author,description,point:question and (node,author,point)==('title','author','body')
            and description.rank==1 and json.loads(description.syntax)==expected,
        actionoccurrence=lambda use,point:bits[0] and (use,point)==('use','closing'),
        nameapplies=lambda use,label,target,point:bits[1] and (use,label,target,point)==('use',name,'author','closing'),
        authordisplay=lambda use,document,target,point:bits[2] and (use,document,target,point)==('use','document','author','closing'),
        printedform=lambda label,language,form,point:(label,check.names_profile.scalar_text(language),
            check.names_profile.scalar_text(form),point)==(name,'de','I. Kant.','closing'))
    result.update({vocabulary._symbols[n]:function for n,function in handlers.items()})
    return result


def evaluate(doc,handlers):
    return [r['value'] for r in evaluate_document(doc,individuals=('use','designation','author','document','title','signature','other'),
        situations=('body','closing','other'),primitives=handlers,max_steps=1000000,
        memoize_definitions=False,memoize_expressions=False)]


def test_question_and_each_author_condition_remain_independent():
    doc=check.restored()['document']
    for question in (False,True):
        for mask in range(8):
            bits=tuple(bool(mask&(1<<i)) for i in range(3))
            assert evaluate(doc,model(doc,question=question,bits=bits))==[question,all(bits),True]


def test_name_identity_and_body_context_do_not_replace_author_scope():
    doc=check.restored()['document']
    assert evaluate(doc,model(doc,same_name=True))==[True,False,True]
    assert evaluate(doc,model(doc,body_context='closing'))==[False,True,True]


def test_unknown_references_and_relations_are_not_silently_false():
    doc=check.restored()['document'];vocabulary=check.vocabulary()
    for name in ('textpresentation','closingpresentationrecord','documentcontext','frontmatterreference',
        'presentspropertyquestion','actionoccurrence','nameapplies','authordisplay','printedform'):
        handlers=model(doc);handlers[vocabulary._symbols[name]]=forbidden
        with pytest.raises(ValueError,match='Unspecified'):evaluate(doc,handlers)
