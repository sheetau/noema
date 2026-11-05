"""Small distinguishing interpretations for the four semantic boundaries."""
import json
from copy import deepcopy
from fractions import Fraction
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document, Content
from scripts.semantic_boundaries import *
from scripts.general_language import dependencies


def ref(n):return dict(kind='function_ref',symbol=n)
def quote(x):return dict(kind='quote',body=x)
def num(n):return dict(kind='number',numerator=n,denominator=1)
def seq(t,xs):return dict(kind='sequence',element=t,items=xs)
def primitive(n,ps,t):return dict(kind='primitive',name=n,parameters=ps,result=t)
def unknown(*xs):raise ValueError('Unknown interpretation')


def make(extra,bodies):
    ds=raw()+extra
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=dependencies([d['name'] for d in ds],ds),statements=[dict(kind='ask',body=b) for b in bodies]))


def values(d,m,people=('a','b')):
    return [r['value'] for r in evaluate_document(d,individuals=people,situations=('now','later'),primitives=m,max_steps=300000)]


def value_cases():
    extra=[primitive('fixturea',[],I),primitive('fixtureb',[],I),primitive('fixtureleft',[],C),primitive('fixtureright',[],C)]
    model=dict(fixturea=lambda:'a',fixtureb=lambda:'b',fixtureleft=unknown,fixtureright=unknown)
    types=[(I,'individual',call('fixturea'),call('fixtureb')),(N,'number',num(20),num(21)),
           (DC,'description',quote(call('fixtureleft')),quote(call('fixtureright')))]
    rows=[];documents=[]
    cases=[('unobserved',True,False,[]),('empty-complete',True,True,[]),('one-unfinished',True,False,[0]),
           ('one-complete',True,True,[0]),('repetition',True,True,[0,0]),('alternatives',True,True,[0,1]),
           ('inapplicable',False,True,[0])]
    for t,suffix,a,b in types:
        bodies=[];expected=[]
        for label,applicable,complete,indices in cases:
            candidates=seq(t,[(a,b)[i] for i in indices])
            bodies.extend([call('listeduniquevalue'+suffix,truth(applicable),truth(complete),candidates,a),
                call('listedmissingvalue'+suffix,truth(applicable),truth(complete),candidates),
                call('listedalternativevalues'+suffix,candidates)])
            wanted=[applicable and complete and bool(indices) and set(indices)=={0},applicable and complete and not indices,len(set(indices))>1]
            expected.extend(wanted);rows.append(dict(type=suffix,case=label,expected=wanted))
        d=make(extra,bodies);assert values(d,model)==expected;documents.append(('values-'+suffix,d,expected))
    # The relational schema itself is checked on a fully enumerated tiny type.
    pred=lam([('x',I)],eq(v('x'),call('fixturea')))
    d=make(extra,[call('uniquevalueindividual',truth(True),truth(True),pred,call('fixturea')),
                  call('missingvalueindividual',truth(True),truth(True),pred)])
    assert values(d,model)==[True,False]
    # All uses are type-correct even when the finite evaluator cannot quantify
    # the semantic domain. Never replace infinite quantification with samples.
    for t in (I,N,DC,Q(I),F([I],T),C):
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=value_schema(t,'probe'),statements=[]))
    return rows,documents


def target_cases():
    extra=[primitive('fixturea',[],I),primitive('fixtureb',[],I),primitive('fixtureworld',[],S),
           primitive('fixtureproperty',[I,S],T),primitive('fixtureactual',[I,S],T),
           definition('fixturefamily',[('x',I)],C,dict(kind='content',variable='world',body=call('fixtureproperty',v('x'),v('world'))))]
    family=quote(ref('fixturefamily')); left=call('anchoredcontent',family,quote(call('fixturea')));right=call('anchoredcontent',family,quote(call('fixtureb')))
    extra+=dependencies(['nonfactivecontentbelief'])
    bodies=[eq(call('fixturea'),call('fixtureb')),eq(left,right),eq(dq(left),dq(right)),
        call('nonfactivecontentbelief',call('fixturea'),left,call('fixtureworld')),
        call('nonfactivecontentbelief',call('fixturea'),right,call('fixtureworld')),
        call('actualtargetexists',family,ref('fixtureactual'),call('fixtureworld'))]
    d=make(extra,bodies)
    def believes(person,desc,world):
        node=json.loads(desc.syntax)
        return person=='a' and world=='now' and node['arguments'][0]['symbol']=='fixturea'
    model=dict(fixturea=lambda:'a',fixtureb=lambda:'a',fixtureworld=lambda:'now',fixtureproperty=lambda *xs:True,
        fixtureactual=lambda *xs:False,nonfactivecontentbelief=believes)
    expected=[True,False,True,True,False,False];assert values(d,model)==expected
    # The belief attribution does not execute its quoted content.
    only=deepcopy(d);only['statements']=[d['statements'][3]]
    assert values(only,{**model,'fixtureproperty':unknown})==[True]
    actual=values(d,{**model,'fixtureactual':lambda *xs:True});assert actual[-1] is True
    # Different witnesses per situation are not one fixed witness across them.
    different=q('forall','world',S,q('exists','x',I,call('fixtureproperty',v('x'),v('world'))))
    fixed=q('exists','x',I,q('forall','world',S,call('fixtureproperty',v('x'),v('world'))))
    scope=make(extra,[different,fixed]);scope_model={**model,'fixtureproperty':lambda x,w:(x,w) in [('a','now'),('b','later')]}
    assert values(scope,scope_model)==[True,False]
    return dict(same_referent_different_description=expected,actual_witness=actual[-1],unknown_quoted_content_preserved=True,
                varying_and_fixed_witness=[True,False]),[('targets',d,expected),('target-scope',scope,[True,False])]


def binding_cases():
    extra=[primitive('fixtureworld',[],S),primitive('fixturerelation',[I,N,S],T),
        definition('fixturefamily',[('person',I),('amount',N)],C,dict(kind='content',variable='world',
            body=call('fixturerelation',v('person'),v('amount'),v('world'))))]
    template=quote(ref('fixturefamily'))
    package=call('boundcontentindividualnumber',template,v('person'),num(20))
    same=call('boundcontentmatchesindividualnumber',package,template,v('person'),num(20))
    wrong=call('boundcontentmatchesindividualnumber',package,template,v('person'),num(21))
    holds=call('boundcontentholdsindividualnumber',package,call('fixtureworld'))
    bodies=[q('forall','person',I,same),q('exists','person',I,wrong),q('exists','person',I,holds)]
    d=make(extra,bodies);m=dict(fixtureworld=lambda:'now',fixturerelation=lambda p,n,w:(p,n,w)==('a',Fraction(20),'now'))
    assert values(d,m)==[True,False,True]
    only=deepcopy(d);only['statements']=d['statements'][:2]
    assert values(only,{**m,'fixturerelation':unknown})==[True,False]
    for types in ([N],[DC],[Q(I)],[F([I],T)],[I,N,DC]):
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=binding_schema(types,'probe'),statements=[]))
    return dict(unnamed_witnesses=[True,False,True],construction_without_evaluation=True,typed_schemas=5),[('typed-binding',d,[True,False,True])]


def support_cases():
    sort=F([I,DC,S],T)
    extra=[primitive('fixturea',[],I),primitive('fixtureb',[],I),primitive('fixtureworld',[],S),primitive('fixtureclaim',[],C),
        primitive('fixturepositive',sort['parameters'],T),primitive('fixturenegative',sort['parameters'],T)]
    args_=[seq(I,[call('fixturea'),call('fixtureb')]),quote(call('fixtureclaim')),call('fixtureworld'),ref('fixturepositive'),ref('fixturenegative')]
    names=['supportpositiveonly','supportnegativeonly','supportboth','supportneither']
    d=make(extra,[call(n,*args_) for n in names]);rows=[]
    for pos,no in [(False,False),(True,False),(False,True),(True,True)]:
        model=dict(fixturea=lambda:'a',fixtureb=lambda:'b',fixtureworld=lambda:'now',fixtureclaim=unknown,
            fixturepositive=lambda source,desc,world:pos and source=='a' and world=='now',
            fixturenegative=lambda source,desc,world:no and source=='b' and world=='now')
        expected=[pos and not no,no and not pos,pos and no,not(pos or no)]
        assert values(d,model)==expected;rows.append(dict(positive=pos,negative=no,values=expected))
    try:values(d,{**model,'fixturepositive':unknown})
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Missing information became no support')
    return rows,[('support',d,[False,False,True,False])]


def value_conflict_cases():
    extra=[primitive('fixturefield',[],I),primitive('fixtureworld',[],S),primitive('fixturea',[],I),primitive('fixtureb',[],I),
           primitive('fixturereports',[I,I,N,S],T),primitive('fixturesingle',[I,S],T)]
    body=call('valueconflictnumber',call('fixturefield'),call('fixtureworld'),call('fixturea'),call('fixtureb'),num(20),num(21),ref('fixturereports'),ref('fixturesingle'))
    d=make(extra,[body]);rows=[]
    for label,single,world in [('same-age-field',True,'now'),('multiple-values-allowed',False,'now'),('other-context',True,'later')]:
        m=dict(fixturefield=lambda:'a',fixtureworld=lambda:world,fixturea=lambda:'a',fixtureb=lambda:'b',
               fixturesingle=lambda field,w:single,fixturereports=lambda source,field,value,w:field=='a' and w=='now' and
               (source,value) in [('a',Fraction(20)),('b',Fraction(21))])
        expected=[single and world=='now'];assert values(d,m)==expected;rows.append(dict(case=label,values=expected))
    return rows,[('value-conflict',d,[False])]


def reading_cases():
    extra=[primitive('fixturea',[],I),primitive('fixtureb',[],I),primitive('fixturepath',[I,I,I,S],T),
           primitive('fixturecommunicates',[I,I,I,S],T)]
    # Both meanings expose a pair of distinct endpoints. Only the physical vs
    # communicative connection remains an interpreted, reusable base relation.
    for name,relation in [('fixturebridge','fixturepath'),('fixturemediator','fixturecommunicates')]:
        body=q('exists','left',I,q('exists','right',I,op('and',neg(eq(v('left'),v('right'))),
            call(relation,v('object'),v('left'),v('right'),v('world')))))
        extra.append(definition(name,[('object',I)],C,dict(kind='content',variable='world',body=body)))
    src=quote(ref('fixturebridge'));dst=quote(ref('fixturemediator'));a=quote(call('fixturea'));b=quote(call('fixtureb'))
    literal=call('anchoredcontent',src,a);intended=call('anchoredcontent',dst,b)
    bodies=[call('readingconstruction',src,a,literal,dst,b,intended),
            call('readingconstruction',src,a,literal,dst,a,intended)]
    d=make(extra,bodies);m=dict(fixturea=lambda:'a',fixtureb=lambda:'b',fixturepath=unknown,fixturecommunicates=unknown)
    assert values(d,m)==[True,False]
    return dict(values=[True,False],base_relations=['physical path through distinct endpoints','communication mediated between distinct participants'],
                conditions='The abstract correspondence and use in context must be stated; construction alone is not a license.'),[('constructed-reading',d,[True,False])]


def closure_cases():
    extra=[primitive('fixturea',[],I),primitive('fixtureb',[],I),primitive('fixtureedge',[I,I],T)]
    d=make(extra,[call('relationreachable',ref('fixtureedge'),call(a),call(b)) for a,b in
        [('fixturea','fixturea'),('fixturea','fixtureb'),('fixtureb','fixturea'),('fixtureb','fixtureb')]])
    cases=[('empty',set(),[False]*4),('one-edge',{('a','b')},[False,True,False,False]),
        ('cycle',{('a','b'),('b','a')},[True]*4),('self-edge',{('a','a')},[True,False,False,False])]
    rows=[]
    for name,edges,expected in cases:
        m=dict(fixturea=lambda:'a',fixtureb=lambda:'b',fixtureedge=lambda a,b:(a,b) in edges)
        assert values(d,m)==expected;rows.append(dict(case=name,expected=expected))
    return rows,[('reachability',d,[True]*4)]


def graph_cases():
    extra=[primitive('fixturenodes',[I],T),primitive('fixturepositive',[I,I],T),primitive('fixturenegative',[I,I],T),
           primitive('fixturegrounded',[I],T),primitive('fixturegiven',[I],T),primitive('fixturea',[],I)]
    params=[ref('fixture'+s) for s in ('nodes','positive','negative','grounded','given')]
    bodies=[call('truthgraphvalid',*params),call('truthgraphsolvable',*params),
            call('truthgraphtrue',*params,call('fixturea')),call('truthgraphfalse',*params,call('fixturea'))]
    d=make(extra,bodies)
    cases=[('grounded-true',set(),set(),{'a'},[True,True,True,False]),
           ('self-affirming',{('a','a')},set(),set(),[True,True,False,False]),
           ('self-negating',set(),{('a','a')},set(),[True,False,False,False]),
           ('mutual-negative',set(),{('a','b'),('b','a')},set(),[True,True,False,False]),
           ('fixed-contradiction',set(),{('a','b')},{'a','b'},[True,False,False,False]),
           ('two-signs',{('a','a')},{('a','a')},set(),[False,False,False,False])]
    rows=[]
    for name,pos,no,ground,expected in cases:
        m=dict(fixturenodes=lambda x:True,fixturepositive=lambda a,b:(a,b) in pos,fixturenegative=lambda a,b:(a,b) in no,
               fixturegrounded=lambda x:x in ground,fixturegiven=lambda x:True,fixturea=lambda:'a')
        assert values(d,m)==expected;rows.append(dict(case=name,positive=sorted(pos),negative=sorted(no),grounded=sorted(ground),expected=expected))
    return rows,[('self-reference',d,[False,False,False,False])]


def constraint_cases():
    extra=[primitive('fixturea',[],I),primitive('fixtureb',[],I)]
    # a says "not(a and b)". Fixing b false yields a true; fixing b
    # true yields the self-negation equation. This is beyond one-edge graphs.
    compound=eq(app('valuation',call('fixturea')),neg(op('and',app('valuation',call('fixturea')),app('valuation',call('fixtureb')))))
    bodies=[]
    for b in (False,True):
        constraint=lam([('valuation',P)],op('and',compound,eq(app('valuation',call('fixtureb')),truth(b))))
        bodies.extend([call('constraintsolvable',constraint),call('constrainttrue',constraint,call('fixturea')),call('constraintfalse',constraint,call('fixturea'))])
    d=make(extra,bodies);expected=[True,True,False,False,False,False]
    assert values(d,dict(fixturea=lambda:'a',fixtureb=lambda:'b'))==expected
    return dict(compound_reference=expected),[('compound-reference',d,expected)]


def diagnose():
    rows={};documents=[]
    for name,fn in [('values',value_cases),('targets',target_cases),('binding',binding_cases),('support',support_cases),('value_conflict',value_conflict_cases),('reading',reading_cases),
                    ('closure',closure_cases),('self_reference',graph_cases),('constraints',constraint_cases)]:
        result,docs=fn();rows[name]=result;documents.extend(docs)
    return rows,documents


def build_report():
    from scripts.two_work_inventory import sha
    rows,_=diagnose()
    paths=['scripts/semantic_boundaries.py','scripts/check_semantic_boundaries.py','scripts/general_language.py',
           'scripts/shared_reference.py','scripts/shared_modality.py','scripts/shared_time.py',
           'noema/constructed_discourse.py','noema/constructed_semantics.py','data/general-language-catalog-v1.json']
    return dict(schema='noema-semantic-boundaries-1',new_definitions=len(raw()),new_primitives=0,diagnostics=rows,
                source_sha256={p:sha(p) for p in paths},limits=['Small distinguishing interpretations, not exhaustive natural-language coverage.',
                'Infinite-domain statements are typechecked without replacing their quantifiers by finite samples.'])
