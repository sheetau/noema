"""Keep answer attribution, quotation scopes, contrasts and all four text spans distinct."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_answer_discourse_visible as check
from scripts.shared_modality import call,renamed
from scripts.sentence_text_span_references import SentenceTextSpanReferences
import test_kant_question_discourse_visible as parent

REFERENCES={n:'answer-discourse-'+n for n in ('h236n','h235s','h235t','h236j')}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())
SCENES=parent.parent.parent.parent.parent.SCENES
CONTEXT=parent.parent.parent.parent.parent.parent.CONTEXT
ROOTS=('r2yi','r2yn','r2z6','r2zh')

def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives=values,max_steps=25000000,memoize_definitions=memo,memoize_expressions=memo)]

def expectations():
    q=lambda rank,name,kind='call':('quote',rank,kind,name)
    rows=[('r2yi','hzon',('h235s','wa',q(1,'r2yh'),'h232o')),
        ('r2yn','hzon',('h235t','wa',q(1,'r2ym'),'h232o')),
        ('r2yn','ue',('h235s','h235t','h232o')),
        ('r2z6','h236i',('h236j','wa',q(3,'r2z5'),'h232o')),
        ('r2z6','ue',('h235t','h236j','h232o')),
        ('r2zh','h236i',('h235p','wa',q(3,'r2zf'),'h232o')),
        ('r2zh','h236k',('h235p','wa','h235s',q(3,'r2yh'),'h236j',q(3,'r2z5'),q(0,'r2zg','function_ref'),'h232o')),
        ('r2zh','h236l',('h236j','wa',q(3,'r2z5'),q(0,'r2zd','function_ref'),q(2,'r2zb','function_ref'),q(2,'r2zc','function_ref'),q(2,'r2yz','function_ref'),'h232o'))]
    for left,right in (('h236n','h235s'),('h235s','h235t'),('h235t','h236j')):
        rows.append(('r2zh','ue',(left,right,'h232o')))
    for question in ('h235n','h235o'):
        rows += [('r2zh','h236m',('h236n','wa',question,'h235p',q(3,'r2zf'),'h232o')),
            ('r2zh','hzcs',('wa',question,'h235p','h232o')),
            ('r2zh','ue',(question,'h236n','h232o'))]
    return rows

def model(doc,omitted=None,seen=None):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    anchors=check.read(check.ANCHORS);answer=parent.REFERENCES['h235p']
    oldspan=values[voc._symbols['sentencetextspanreference']]
    refs=SentenceTextSpanReferences({('document',answer,'closing'):anchors['text']},
        {('document',answer,row['first_character'],row['past_last_character'],'closing'):REFERENCES[n]
         for n,row in anchors['source_character_spans'].items()})
    def span(document,sentence,first,last,context):
        if sentence==answer:return refs.span(document,sentence,first,last,context)
        return oldspan(document,sentence,first,last,context)
    values[voc._symbols['sentencetextspanreference']]=span
    labels={v:k for k,v in (parent.REFERENCES|REFERENCES).items()}|{'author':'wa',CONTEXT:'h232o'}
    rows=expectations();expected=[(n,args) for _,n,args in rows]
    def normalized(value):
        if isinstance(value,str):return labels.get(value,value)
        if hasattr(value,'syntax'):
            code=renamed(json.loads(value.syntax),inverse)
            return ('quote',value.rank,code['kind'],code['symbol'])
        raise AssertionError(type(value))
    def handler(name,previous):
        def relation(*args):
            row=(name,tuple(normalized(a) for a in args))
            if row in expected:
                if seen is not None:seen.update(i for i,r in enumerate(expected) if r==row)
                return omitted is None or expected[omitted]!=row
            if name in {'h236i','h236k','h236l','h236m'} or any(isinstance(a,str) and a in REFERENCES.values() for a in args):return False
            return previous(*args)
        return relation
    for name in {n for _,n,_ in rows}:values[m[name]]=handler(name,values.get(m[name],lambda *args:False))
    return values

def selection(start=52):
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][start:]
    return doc

def test_source_and_every_prior_declaration_are_preserved():
    doc=check.restored()['document'];old=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:52]==old['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert (len(doc['declarations']),len(doc['statements']))==(1647,56)
    assert len(check.source_excerpt()['declarations'])==1616
    assert check.SOURCE_ORDER[-4:]==[69,70,71,72]
    current=selection(50);assert evaluate(current,model(current))==[True]*6

def test_every_attribution_contrast_concession_and_answer_link_is_required():
    doc=selection();seen=set();assert evaluate(doc,model(doc,seen=seen),memo=False)==[True]*4
    rows=expectations();assert seen==set(range(len(rows)))
    for index,(_,name,args) in enumerate(rows):
        expected=[not any(root==r and (n,a)==(name,args) for r,n,a in rows) for root in ROOTS]
        assert evaluate(doc,model(doc,omitted=index))==expected,(index,name)

def test_each_relation_argument_is_bound():
    doc=selection();m=check.mapping();occurrences={}
    substitutions={n:'h234o' for n in REFERENCES|parent.REFERENCES}
    substitutions.update(wa='h234o',h232o='hzp3')
    for root,name,_ in expectations():
        occurrence=occurrences.get((root,name),0);occurrences[root,name]=occurrence+1
        original=parent.calls(next(d for d in doc['declarations'] if d['name']==m[root])['body'],m[name])[occurrence]
        for slot,arg in enumerate(original['arguments']):
            changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m[root])['body']
            if arg['kind']=='quote':
                target=arg['body']['symbol']
                declaration=next(d for d in doc['declarations'] if d['name']==target)
                changed['declarations'].insert(0,dict(kind='primitive',name='jmutation',
                    parameters=[deepcopy(p['sort']) for p in declaration['parameters']],result=deepcopy(declaration['result'])))
                replacement=renamed(arg,{target:'jmutation'})
            else:replacement=renamed(arg,{m[a]:m[b] for a,b in substitutions.items()})
            assert replacement!=arg,(root,name,slot)
            parent.calls(body,m[name])[occurrence]['arguments'][slot]=replacement
            assert evaluate(changed,model(changed))[ROOTS.index(root)] is False,(root,name,occurrence,slot)

def test_unknown_presentations_refused_and_quoted_policy_contents_not_executed():
    doc=selection();m=check.mapping()
    def unknown(*args):raise ValueError('Unspecified answer discourse input')
    for name in {n for _,n,_ in expectations()}:
        with pytest.raises(ValueError,match='Unspecified answer'):evaluate(doc,model(doc)|{m[name]:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-{n for _,n,_ in expectations()}:values[m[name]]=unknown
    assert evaluate(doc,values)==[True]*4

def test_four_exact_text_spans_reuse_the_answer_sentence_and_refuse_unknown_offsets():
    m=check.mapping();voc=check.vocabulary();anchors=check.read(check.ANCHORS)
    assert ''.join(r['text'] for r in anchors['source_character_spans'].values())==anchors['text']
    assert check.names()['h235p']==check.previous.names()['h235p']
    for name,expected in REFERENCES.items():
        doc=selection();doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
        doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[name]),call('jexpected')]))]
        assert evaluate(doc,model(doc)|{'jexpected':lambda:expected})==[True]
        assert evaluate(doc,model(doc)|{'jexpected':lambda:parent.REFERENCES['h235p']})==[False]
        changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m[name])['body']
        body['arguments'][2]['numerator']=999
        with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:expected})
        for slot,other in ((0,'wh'),(1,'h235n'),(4,'h232o')):
            changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m[name])['body']
            body['arguments'][slot]=call(m[other])
            with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:expected})
    def unknown(*args):raise ValueError('Unspecified answer span')
    with pytest.raises(ValueError,match='Unspecified answer span'):
        evaluate(doc,model(doc)|{voc._symbols['sentencetextspanreference']:unknown,'jexpected':lambda:expected})

def test_inherited_description_wrapper_mutations_are_refused():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    next(d for d in doc['declarations'] if d['name']==m['h227c'])['body']['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(doc)
