"""Bind prediction, comparative background, metaphor and reason to exact text."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_public_dissemination_visible as check
from scripts.shared_modality import call,renamed
from scripts.sentence_text_span_references import SentenceTextSpanReferences
import test_kant_public_enlightenment_visible as parent

REFERENCES={'hzp5':'dissemination-sentence','hzpz':'dissemination-clause','hzq2':'guardian-focus',
    'h223m':'crowd-label','hzpo':'yoke-clause'}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())
SMALL_DOMAIN=parent.SMALL_DOMAIN+tuple(REFERENCES.values())


def evaluate(doc,values,memo=True,domain=SMALL_DOMAIN):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,
        situations=('body','closing','public-context','other'),primitives=values,max_steps=20000000,
        memoize_definitions=memo,memoize_expressions=memo)]


def model(doc,variant='baseline',bits=(True,)*6):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    oldsentence=values[voc._symbols['sentencereference']];oldspan=values[voc._symbols['sentencetokenspanreference']]
    oldfg,oldbg,oldpair,oldreason,oldorder=[values[m[n]] for n in ('hznreport','hzrbgreport','qa','ud','ue')]
    anchor=check.read(check.ANCHORS)
    refs=SentenceTextSpanReferences({('document','dissemination-sentence','closing'):anchor['text']},
        {('document','dissemination-sentence',r['first_character'],r['past_last_character'],'closing'):REFERENCES[n]
         for n,r in anchor['source_character_spans'].items()})
    def syntax(value,name,rank,kind='call'):
        return value.rank==rank and renamed(json.loads(value.syntax),inverse)==(
            call(name) if kind=='call' else dict(kind='function_ref',symbol=name))
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',4,2):return 'dissemination-sentence'
        return oldsentence(context,paragraph,index)
    def span(document,first,a,last,b,context):
        if first=='dissemination-sentence':
            if (document,last,context)==('document','dissemination-sentence','closing'):
                if (a,b)==(3,46):return 'dissemination-clause'
                if (a,b)==(8,12):return 'guardian-focus'
            raise ValueError('Unknown dissemination text span')
        return oldspan(document,first,a,last,b,context)
    def fg(node,author,description,scope,point):
        if node=='dissemination-sentence':
            return bits[0] and (author,scope,point)==('author','guardian-focus' if variant=='wrong_foreground_scope' else 'dissemination-clause','public-context') and syntax(description,'r2md',3)
        return oldfg(node,author,description,scope,point)
    def bg(node,author,foreground,background,fs,bs,point):
        if node=='dissemination-sentence':
            return bits[1] and (author,fs,bs,point)==('author','dissemination-clause',
                'dissemination-clause' if variant=='wrong_background_scope' else 'guardian-focus','public-context') and syntax(foreground,'r2md',3) and syntax(background,'r2me',3)
        return oldbg(node,author,foreground,background,fs,bs,point)
    def pair(node,author,left,right,point):
        if node=='yoke-clause':
            targets=('hzpn','h4q') if variant=='reversed_metaphor' else ('h4q','hzpn')
            return bits[2] and (author,point)==('author','public-context') and syntax(left,targets[0],0,'function_ref') and syntax(right,targets[1],0,'function_ref')
        return oldpair(node,author,left,right,point)
    def reason(author,premises,node,point):
        if node=='public-sentence':
            expected={'dissemination-sentence'}
            if variant=='extra_premise':expected.add('self-development')
            if variant=='missing_premise':expected.clear()
            return bits[3] and (author,point)==('author','public-context') and {x for x in SMALL_DOMAIN if premises(x)}==expected
        return oldreason(author,premises,node,point)
    def order(first,last,point):
        if last=='dissemination-sentence':
            return bits[4] and (first,point)==('public-sentence','public-context') and variant!='reversed_order'
        return oldorder(first,last,point)
    def disparaging(node,presenter,scope,referent,point):
        return bits[5] and (node,presenter,point)==('crowd-label','author','public-context') and syntax(scope,'h222e',1,'function_ref') and syntax(referent,'h223i',1,'function_ref')
    for name,fn in dict(sentencereference=sentence,sentencetokenspanreference=span,**refs.handlers()).items():
        values[voc._symbols[name]]=fn
    values.update({m[n]:fn for n,fn in dict(hznreport=fg,hzrbgreport=bg,qa=pair,ud=reason,ue=order,h223l=disparaging).items()})
    return values


def new_statement():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][38:]
    return doc


def test_complete_source_and_previous_group_are_preserved():
    doc=check.restored()['document']
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:38]==check.previous.document()['statements']
    assert (len(doc['declarations']),len(doc['statements']))==(1078,39)
    assert len(check.source_excerpt()['declarations'])==1053
    assert evaluate(doc,model(doc),domain=DOMAIN)==[True]*39


def test_prediction_background_metaphor_reason_and_label_are_independent():
    doc=new_statement()
    assert evaluate(doc,model(doc),memo=False)==[True]
    for variant in ('wrong_foreground_scope','wrong_background_scope','reversed_metaphor','extra_premise','missing_premise','reversed_order'):
        assert evaluate(doc,model(doc,variant))==[False],variant
    for slot in range(6):
        bits=[True]*6;bits[slot]=False
        assert evaluate(doc,model(doc,bits=bits))==[False],slot
    # Corrupt the actual same-typed foreground/background arguments.
    changed=deepcopy(doc);d=next(d for d in changed['declarations'] if d['name']==check.mapping()['r2mf'])
    args=d['body']['arguments'];args[2],args[3]=args[3],args[2]
    assert evaluate(changed,model(changed))==[False]


def test_unknown_relations_are_refused_without_executing_quoted_worlds():
    doc=new_statement()
    def unknown(*args):raise ValueError('Unspecified dissemination relation')
    for name in ('hznreport','hzrbgreport','qa','ud','ue','h223l'):
        with pytest.raises(ValueError,match='Unspecified dissemination'):
            evaluate(doc,model(doc)|{check.mapping()[name]:unknown})
    with pytest.raises(ValueError,match='Unspecified dissemination'):
        evaluate(doc,model(doc,bits=(False,True,True,True,True,True))|{check.mapping()['hzrbgreport']:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-{'h223l'}:values[check.mapping()[name]]=unknown
    assert evaluate(doc,values)==[True]


def test_exact_reference_extents_and_the_inherited_paragraph_context():
    doc=new_statement();m=check.mapping()
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[n]),call('jexpected')])) for n in REFERENCES]
    for index,target in enumerate(REFERENCES.values()):
        assert evaluate(doc,model(doc)|{'jexpected':lambda target=target:target})==[i==index for i in range(len(REFERENCES))]
    for name in ('h223m','hzpo'):
        changed=new_statement();d=next(d for d in changed['declarations'] if d['name']==m[name])
        d['body']['arguments'][3]['numerator']+=1
        with pytest.raises(ValueError,match='Unknown sentence text span'):evaluate(changed,model(changed))
    changed=new_statement()
    next(d for d in changed['declarations'] if d['name']==m['hzp3'])['body']=call(m['wh'])
    assert evaluate(changed,model(changed))==[False]


def test_wrong_documents_sentences_and_unknown_reference_inputs_are_rejected():
    doc=new_statement();m=check.mapping();voc=check.vocabulary()
    for slot,other in ((0,'wa'),(1,'hzp4'),(4,'wh')):
        changed=deepcopy(doc)
        next(d for d in changed['declarations'] if d['name']==m['h223m'])['body']['arguments'][slot]=call(m[other])
        with pytest.raises(ValueError,match='Unknown fixed sentence'):evaluate(changed,model(changed))
    def unknown(*args):raise ValueError('Unspecified dissemination reference')
    for name in ('sentencereference','sentencetokenspanreference','sentencetextspanreference','paragraphpresentationcontext'):
        with pytest.raises(ValueError,match='Unspecified dissemination reference'):
            evaluate(doc,model(doc)|{voc._symbols[name]:unknown})
