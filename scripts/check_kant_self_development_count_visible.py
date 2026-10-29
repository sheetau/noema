"""Current count bindings with explicit histories; no finite substitute for all lists."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import permutations,product
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,Content,SequenceValue
from noema.meaning_catalog import _references
from scripts import check_kant_self_development_visible as check
from scripts import check_fifth_sentence_scope as retained
from scripts.check_fifth_sentence_scope import criteria,PAIR
from scripts.check_motive_causes import unknown,symbol
from scripts.check_scoped_counts import arithmetic

PEOPLE=('one','two','three','author','node')
SCENES=('now','expected')
BOUNDARIES=('r2kc','h4q','h4t')
RESULTS={}


def fixture(roots,extra):
    doc=deepcopy(check.backprojection(check.restored()['document']))
    original={d['name']:d for d in retained.catalog().document['declarations']}
    existing={d['name']:d for d in doc['declarations']}
    for name in ('rst','rsu','rsv'):
        assert existing[name]==original[name],('Shared package helper changed',name)
    for name in ('rsw','rsx','rsy'):
        assert name not in existing
        doc['declarations'].append(deepcopy(original[name]))
    for d in doc['declarations']:
        if d['name'] in BOUNDARIES:
            assert d['kind']=='definition'
            d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    ds={d['name']:d for d in doc['declarations']};needed=set();pending=set(roots)
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.update(_references(ds[name].get('body')))
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    return parse(format_graph(doc,'compact')+extra)


def run(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=PEOPLE,situations=SCENES,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=2000000,memoize_definitions=True,memoize_expressions=True)]


def model(doc,selected=('one',),expectation=True,predicted=False,population=('one','two','three'),
          candidates=('one','two','three'),prior=('one','two'),upper=2,incomplete=False,premise=True):
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    values.update(arithmetic())
    values.update(zpopulation=lambda:SequenceValue(tuple(population),'"individual"'),znow=lambda:'now',
        aa=lambda p:p in PEOPLE[:3],h4i=lambda p,s:p in candidates,
        hzzq=lambda:'node',wh=lambda:'now',hzzn=lambda n,p,s:(n,s)==('node','now') and p in prior,
        h4h=lambda n,s:Fraction(upper),h5v=lambda n,s:criteria(lambda count:count>=upper),
        r2kc=lambda p:Content(SCENES,(p in selected,p in selected and predicted)),
        h4q=lambda p:Content(SCENES,(p in selected,p in selected and premise)),
        h4t=lambda p,s:not(incomplete and p=='two'),wa=lambda:'author',
        ke=lambda author,p,description,anchor,alternative:expectation and author=='author' and symbol(description)=='h4q' and alternative=='expected')
    return values


@lru_cache(None)
def count_document():
    return fixture(['r2ki','r2kj','r2kp','rst','rsx','rsy','rsw'],'''
r zpopulation[] j[a].r znow[] d.
d zforeground[] e[b point[w[k r2kp[v point]][t[k r2ki[k zpopulation[]]][v point]]]].
d zbackground[] e[b point[w[k r2kp[v point]][t[k r2kj[k zpopulation[]]][v point]]]].
d zpair[] '''+PAIR+'''[k rst[r c[k zforeground[]] r c[k zbackground[]]]].
q[k rsx[k zpair[] k znow[]]].q[k rsy[k zpair[] k znow[]]].
q[k rsx[k rsw[k zpair[]] k znow[]]].q[k rsy[k rsw[k zpair[]] k znow[]]].
''')


def count_checks():
    doc=count_document();rows={}
    cases=[('baseline',{},[True,True,False,True]),
        ('no_expected_cases',dict(expectation=False),[True,False,False,False]),
        ('predicted_success',dict(predicted=True),[True,False,False,False]),
        ('premise_not_held',dict(premise=False),[True,False,False,False]),
        ('zero_success',dict(selected=()),[False,True,True,True]),
        ('not_few',dict(selected=('one','two')),[False,True,True,True]),
        ('missing_counted_person',dict(population=('one',)),[False,False,True,False]),
        ('duplicated_person',dict(population=('one','two','two')),[False,False,True,False]),
        ('unqualified_missing_history',dict(incomplete=True),[False,False,True,False]),
        ('qualified_missing_other_history',dict(selected=('two',),incomplete=True),[True,True,False,True]),
        ('unrelated_success_sample',dict(population=('one',),candidates=('one',)),[False,False,True,False])]
    for name,kwargs,wanted in cases:
        actual=run(doc,model(doc,**kwargs));assert actual==wanted,(name,actual);rows[name]=actual
    combinations=0
    for bits,expected,predicted in product(product((False,True),repeat=3),(False,True),(False,True)):
        selected=tuple(p for p,yes in zip(PEOPLE[:3],bits) if yes)
        actual=run(doc,model(doc,selected=selected,expectation=expected,predicted=predicted))
        assert actual[0]==(len(selected)==1)
        assert actual[1]==(not selected or expected and not predicted)
        assert actual[2:]==[not actual[0],actual[1]];combinations+=1
    for population in permutations(PEOPLE[:3]):assert run(doc,model(doc,population=population))==rows['baseline']
    RESULTS['counts']=dict(cases=rows,finite_combinations=combinations,permutations=6,
        current_roots=['r2ki','r2kj','r2kp'],explicit_boundary_definitions=list(BOUNDARIES),
        scope='One explicit finite population list at a time; this does not execute the unbounded list quantifier.')
    return RESULTS['counts']


def unknown_checks():
    doc=count_document();missing=('r2kc','h4q','h4t','h4h','h5v','ke','hzzn','h4i')
    for name in missing:
        try:run(doc,model(doc)|{name:unknown})
        except ValueError as error:assert 'Unknown' in str(error),(name,str(error))
        else:raise AssertionError(name)
    foreground=deepcopy(doc);foreground['statements']=foreground['statements'][:1]
    assert run(foreground,model(foreground)|{'ke':unknown})==[True]
    RESULTS['unknowns']=dict(refused=list(missing),foreground_does_not_evaluate_expectations=True)
    return RESULTS['unknowns']


def unbounded_checks():
    source=check.backprojection(check.restored()['document']);ds={d['name']:d for d in source['declarations']}
    for outer,inner in [('r2kk','r2ki'),('r2kl','r2kj')]:
        body=ds[outer]['body'];binder=body['body']
        assert body['kind']=='content' and binder['kind']=='exists'
        assert binder['sort']==dict(kind='sequence',element='individual')
        assert binder['body']['content']==dict(kind='call',symbol=inner,arguments=[dict(kind='variable',name=binder['variable'])])
        doc=fixture([outer],'r znow[] d.q[t[k '+outer+'[]][k znow[]]].')
        try:run(doc,model(doc))
        except ValueError as error:assert 'unbounded sequence domain' in str(error)
        else:raise AssertionError('One population list replaced the unbounded quantifier')
    RESULTS['unbounded']=dict(exact_current_quantifier_bindings=True,finite_evaluator_refuses_all_lists=True)
    return RESULTS['unbounded']


def source_pins():
    paths=set(check.source_pins())|{'scripts/check_kant_self_development_count_visible.py','tests/test_kant_self_development_count_visible.py',
        'scripts/check_fifth_sentence_scope.py','scripts/check_scoped_counts.py','scripts/check_motive_causes.py'}
    paths.update(retained.catalog().source_sha256)
    return {p:check.digest(p) for p in sorted(paths)}


def build_report():
    for key,fn in [('counts',count_checks),('unknowns',unknown_checks),('unbounded',unbounded_checks)]:
        if key not in RESULTS:fn()
    return dict(schema='noema-current-self-development-count-diagnostics-1',results=RESULTS,source_sha256=source_pins(),
        actual_svg_decoding_performed='Determined by the calling production receipt',formal_integration_credit=0,
        limitations=['Explicit r2kc/h4q/h4t boundary histories; their bodies are tested by retained diagnostics separately.',
            'Binding diagnostics for finite listed populations, not proof or evaluation over the unbounded sequence domain.'])
