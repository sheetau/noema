"""Verify a same-pair departure, its stronger diagnostic, and its causal quotation."""
import argparse,hashlib,json,subprocess,sys
from copy import deepcopy
from functools import lru_cache
from itertools import product
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,evaluate_document
from noema.diagnostic_short_circuit import lower
from noema.script import transcribe
from scripts.compose_relational_departure import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,SETTINGS,MEANINGS,build
from scripts.compose_qualified_utterance import closure
from scripts.check_rod_setup import guarded
from scripts.check_quoted_outcomes import structure as parent_structure

REPORT=ROOT/'reports/relational-departure-v1.json'
DOMAIN=('holder','replacement','target','other','process','cause')
SCENES=('before','after','outside')
REFS=' '.join('p jdr'+n for n,t in SETTINGS)
CODES=' '.join('r[p jdr'+n+']' for n,t in SETTINGS)


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


@lru_cache(None)
def fixture(path=LIBRARY,causal=False):
    doc=parse(text(path));doc['statements']=[]
    extra=''.join('r jdr'+n+t[1:]+'.' for n,t in SETTINGS)
    extra+='''r jdrtarget[] a.r jdrholder[] a.r jdrprocess[] a.r jdrstart[] d.r jdrend[] d.
r jdrkind[a] c.r jdrprospects[a d d] c.r jdrsecond[a] e.r jdrrelationalias[a a d] c.'''
    event='k jdrtarget[] k jdrholder[] k jdrprocess[] k jdrstart[] k jdrend[] '+REFS
    if not causal:
        queries='q[k rqr['+event+']].q[k rqs['+event+']].q[t[c[k hzhn['+REFS+']][k jdrtarget[]]][k jdrend[]]].'
    else:
        assembled='k hzhp[r b[k jdrtarget[]] r b[p jdrkind] r b[r[p jdrsecond]] r b[k jdrstart[]] r b[p jdrprospects] '+CODES+']'
        literal='r b[c[p hzhk][k jdrtarget[] p jdrkind r[c[p hzhn]['+REFS+']] r[p jdrsecond] k jdrstart[] p jdrprospects]]'
        queries='q[e['+assembled+']['+literal+']].q[s['+assembled+']].q[t[c[k hzhn['+REFS+']][k jdrtarget[]]][k jdrend[]]].'
    return parse(format_graph(doc,'compact')+extra+queries)


def model(doc,variant='baseline',bits=(True,False,True,True,True,True)):
    initial,final,known_before,known_after,changes,affected=bits
    def relation(holder,target,scene):
        if variant=='unknown_relation':raise ValueError('unknown relation')
        if target!=('other' if variant=='different_target' else 'target'):return False
        if variant=='already_free':return False
        if holder=='replacement':return variant=='replacement' and scene=='after' or variant=='different_holder' and scene=='before'
        if holder!='holder' or variant=='different_holder':return False
        return (scene=='before' and initial) or (scene=='after' and (final or variant=='relation_continues'))
    def assessed(holder,target,scene):
        if variant=='unknown_assessment':raise ValueError('unknown assessment')
        return target=='target' and holder in ('holder','replacement') and ((scene=='before' and known_before and variant!='unassessed_before') or
            (scene=='after' and known_after and variant!='unassessed_after' and not(variant=='replacement_unassessed' and holder=='replacement')))
    values=guarded(doc)
    values.update(jdrtarget=lambda:'target',jdrholder=lambda:'holder',jdrprocess=lambda:'process',jdrstart=lambda:'before',jdrend=lambda:'after',
        jdrholders=lambda h:h in ('holder','replacement'),jdrhistory=lambda s:s in ('before','after') and variant!='missing_history',
        jdrbefore=lambda a,b:(a,b)==('before','after') or variant=='reflexive_order' and a==b=='before',
        jdrassessed=assessed,jdrrelation=relation,jdrrelationalias=relation,
        jdrtransitions=lambda p,a,b:changes and (p,a,b)==('cause' if variant=='different_transition' else 'process','before','after'),
        jdraffected=lambda t,p,a,b:affected and (t,p,a,b)==('other' if variant=='different_affected' else 'target','process','before','after'),
        jdrkind=lambda a:a=='cause',jdrprospects=lambda a,b,s:(a,b,s)==('cause','before','after'),
        jdrsecond=lambda t:Content(SCENES,(False,variant=='second_possible' and t=='target',False)),
        dg=lambda a,s:variant!='cause_absent' and (a,s)==('cause','outside' if variant=='cause_at_other_scene' else 'after'))
    expected=dict(kind='apply',function=dict(kind='function_ref',symbol='hzhn'),
        arguments=[dict(kind='function_ref',symbol='jdrrelationalias' if n=='relation' and variant=='other_result_record' else 'jdr'+n) for n,t in SETTINGS])
    def produces(activity,target,description,scene):
        if variant=='unknown_cause':raise ValueError('unknown cause')
        if (activity,target,scene)!=('cause','other' if variant=='other_causal_target' else 'target','after'):return False
        syntax=json.loads(description.syntax)
        return syntax==expected or variant=='second_possible' and syntax==dict(kind='function_ref',symbol='jdrsecond')
    values['g3']=produces
    return values


def evaluate(doc,values,*,indices=None,short=True,memoize=True):
    if indices is not None:
        doc=deepcopy(doc);doc['statements']=[doc['statements'][i] for i in indices]
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'};values={n:values[n] for n in names}
    if short:doc,values=lower(doc,values)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=values,
        max_steps=8_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(None)
def checks():
    doc=fixture();count=0
    for bits in product((False,True),repeat=6):
        valid=bits[0] and not bits[1] and all(bits[2:])
        actual=evaluate(doc,model(doc,bits=bits));assert actual==[valid]*3,(bits,actual);count+=1
    expected={n:[False]*3 for n in ('different_target','already_free','relation_continues','unassessed_before','unassessed_after',
        'different_transition','different_affected','missing_history','reflexive_order')}
    expected.update(baseline=[True]*3,replacement=[True,False,True],replacement_unassessed=[True,False,True],different_holder=[False,False,True])
    events={};causal={}
    for path in (LIBRARY,FULL):
        doc=fixture(path);events[path]={}
        for variant,wanted in expected.items():
            actual=evaluate(doc,model(doc,variant));assert actual==wanted,(path,variant,actual);events[path][variant]=actual
        doc=fixture(path,True);causal[path]={}
        variants={'baseline':[True,True,True],'replacement':[True,True,True],
            'already_free':[True,False,False],'different_transition':[True,False,False],'different_affected':[True,False,False],
            'cause_absent':[True,False,True],'cause_at_other_scene':[True,False,True],'other_causal_target':[True,False,True],
            'other_result_record':[True,False,True],'second_possible':[True,False,True]}
        for variant,wanted in variants.items():
            actual=evaluate(doc,model(doc,variant));assert actual==wanted,(path,variant,actual);causal[path][variant]=actual
        def forbidden(*args):raise AssertionError('Constructing the result quote executed its relation or causal content')
        values={n:forbidden for n in model(doc)}
        assert evaluate(doc,values,indices=(0,))==[True]
    refused=[]
    for variant in ('unknown_relation','unknown_assessment','unknown_cause'):
        try:evaluate(doc,model(doc,variant),indices=(1,))
        except ValueError as exc:assert 'unknown' in str(exc);refused.append(variant)
        else:raise AssertionError(variant)
    doc=fixture()
    for variant in ('baseline','replacement'):
        assert evaluate(doc,model(doc,variant),short=False,memoize=False)==expected[variant]
    return dict(truth_cases=count,event_contrasts=events,causal_contrasts=causal,unknown_inputs_refused=refused,
        actual_tg_and_causal_rfk_executed=True,construction_does_not_execute_result=True,unlowered_uncached_event_cases=2,
        nonpolitical_example='ending a service relationship with one supplier while entering a relationship with another supplier')


def structure():
    inherited=parent_structure();old=parse(text(PARENT));doc=parse(text(FULL));basis=json.loads(text(BASIS))
    assert doc['declarations'][:len(old['declarations'])]==old['declarations'] and doc['statements']==old['statements']
    added=doc['declarations'][len(old['declarations']):]
    assert all(d['kind']=='definition' for d in added) and {d['name'] for d in added}==set(MEANINGS)==set(basis['definitions'])
    assert {d['name']:{k:d[k] for k in ('parameters','result')} for d in added}==basis['new_signatures']
    assert parse(text(LIBRARY))['declarations']==closure(doc,['rqs','hzho','hzhp'])
    return dict(inherited_basis_checked=inherited['inherited_basis_signature_coverage'],
        previous_15_statements_and_all_declarations_unchanged=True,new_definitions=5,new_primitives=0,new_assertions=0)


def build_report():
    files=build()
    for name,body in files.items():assert text(name)==body,name
    for path in (FULL,LIBRARY):
        doc=parse(text(path))
        for notation in ('full','compact'):
            body=format_graph(doc,notation);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==doc
    alignment=deepcopy(json.loads(text('reports/quoted-outcomes-v1.json'))['alignment'])
    for row in alignment['segments']:
        row['definitions']=['rqr','rqs','hzhn','hzho','hzhp'];row['status']='partial_relational_departure_as_causal_result'
        row['remaining'].append('meaning of the selected relation and source reading of departure from a particular holder')
    paths=set(files)|{PARENT,PARENT_BASIS,'reports/quoted-outcomes-v1.json','examples/v014/kant-causal-outcome-contrast.noema',
        'data/kant-causal-outcome-contrast-basis-v1.json','examples/v016/quoted-causal-outcomes.noema',
        'docs/relational-departure-v1.md','tests/test_relational_departure.py','artifacts/written-units-v1/kant-1784.json'}
    paths.update('scripts/'+n+'.py' for n in ('compose_relational_departure','check_relational_departure','compose_quoted_outcomes',
        'check_quoted_outcomes','compose_origin_clock','compose_limits','compose_situated_criticism','compose_qualified_utterance','check_rod_setup'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','meaning_basis','script','constructed',
        'constructed_discourse','constructed_semantics','guarded_ranked_semantics','diagnostic_short_circuit'))
    return dict(status='partial_relational_departure_result_with_source_relation_unfilled',document=FULL,
        finite=checks(),structure=structure(),alignment=alignment,roundtrips=True,cli_parse=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Relational departure and its same-description causal outcome checked',flush=True)


if __name__=='__main__':main()
