"""Check the same person's departure, including an accepted old counterexample."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from pathlib import Path
import subprocess
import sys

from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.diagnostic_short_circuit import lower
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from scripts.compose_subject_bound_departure import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,MEANING,build,closure

REPORT=ROOT/'reports/subject-bound-departure-v1.json'
REVIEW=ROOT/'data/subject-bound-departure-review-v1.json'
DOMAIN=('reader','other','plan','faculty','act','change','unrelated')
SCENES=('start','after','left','right','outside')


def forbidden(*args):raise ValueError('Unspecified primitive evaluated')


@lru_cache(None)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(None)
def fixture(path):
    doc=deepcopy(document(path));doc['statements']=[]
    return parse(format_graph(doc,'compact')+
        'r jstarget[] a.r jsprocess[] a.r jsstart[] d.r jsend[] d.'+
        'q[k be[k jstarget[] k jsprocess[] k jsstart[] k jsend[]]].'+
        'q[t[k bi[k jsprocess[]]][k jsend[]]].')


def model(doc,variant='baseline',bits=(True,True,True,True)):
    transition,affected,initial,successful=bits
    available_start={'left','right'} if initial else {'left'}
    selected_end={'left'} if successful else {'left','right'}
    if variant=='empty_final_assessment':selected_end=set()
    if variant=='foreign_final_assessment':selected_end={'outside'}
    if variant=='unknown_initial_assessment':available_start=set()
    values={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def change_subject(person,process,start,end):
        if variant=='unknown_subject':raise ValueError('Unknown process subject')
        wanted=('other' if variant=='different_person' else 'reader',
            'unrelated' if variant=='different_process' else 'change',
            'outside' if variant=='different_start' else 'start',
            'outside' if variant=='different_end' else 'after')
        return affected and variant not in ('witness_only','cause_only','no_affected_subject') and (person,process,start,end)==wanted
    values.update(jstarget=lambda:'reader',jsprocess=lambda:'change',jsstart=lambda:'start',jsend=lambda:'after',
        aa=lambda p:p=='reader',ab=lambda f,p,s:(f,p)==('faculty','reader'),
        ac=lambda p,f,a,s:(p,f,a,s)==('reader','faculty','act','left'),
        ad=lambda guide,p,a,s:variant=='still_guided' and (guide,p,a,s)==('other','reader','act','left'),
        ae=lambda p,m,s:(p,m)==('reader','plan') and s in ('start','after') and variant!='no_available_method',
        af=lambda p,m,s,t:(p,m)==('reader','plan') and t in ('left','right'),
        ap=lambda p,m,s,t:(p,m)==('reader','plan') and t in (selected_end if s=='after' else available_start),
        ag=lambda p,a,b:transition and (p,a,b)==('change','after' if variant=='reversed_transition' else 'start',
            'start' if variant=='reversed_transition' else 'after'),
        la=change_subject,
        ea=lambda p,factor,target,result,s:variant!='absent_cause_explanation' and (p,target,s)==('reader','reader','start')
            and json.loads(factor.syntax)==dict(kind='function_ref',symbol='bs') and json.loads(result.syntax)==dict(kind='function_ref',symbol='bf'))
    return {d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}


def evaluate(doc,values,*,short=True,memoize=True):
    if short:doc,values=lower(doc,values)
    return [row['value'] for row in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=values,
        max_steps=8_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(None)
def checks():
    truth=[];doc=fixture(LIBRARY)
    for bits in product((False,True),repeat=4):
        expected=[all(bits)]*2;actual=evaluate(doc,model(doc,bits=bits))
        assert actual==expected,(bits,actual)
        truth.append(dict(bits=list(bits),values=actual))
    variants=('baseline','different_person','different_process','different_start','different_end','witness_only','cause_only',
        'no_affected_subject','empty_final_assessment','foreign_final_assessment','unknown_initial_assessment',
        'still_guided','no_available_method','absent_cause_explanation','reversed_transition')
    contrasts={}
    for path in (LIBRARY,FULL):
        doc=fixture(path);contrasts[path]={}
        for variant in variants:
            actual=evaluate(doc,model(doc,variant));assert actual==[variant=='baseline']*2,(path,variant,actual)
            contrasts[path][variant]=actual
    old=fixture(PARENT);new=fixture(FULL);counterexamples={}
    for variant in ('different_person','different_process','different_start','different_end','witness_only','cause_only','no_affected_subject'):
        before=evaluate(old,model(old,variant));after=evaluate(new,model(new,variant))
        assert before==[True,True] and after==[False,False],(variant,before,after)
        counterexamples[variant]=dict(previous=before,revised=after)
    for variant in ('baseline','different_person'):
        doc=fixture(LIBRARY)
        assert evaluate(doc,model(doc,variant),short=False,memoize=False)==contrasts[LIBRARY][variant]
    try:evaluate(new,model(new,'unknown_subject'))
    except ValueError as error:assert 'Unknown process subject' in str(error)
    else:raise AssertionError('Unspecified subject was silently accepted')
    return dict(four_condition_combinations=truth,contrasts=contrasts,old_counterexamples=counterexamples,
        unlowered_uncached_cases=2,unknown_subject_refused=True)


def structure():
    old=document(PARENT);new=document(FULL);previous={d['name']:d for d in old['declarations']};current={d['name']:d for d in new['declarations']}
    assert previous.keys()==current.keys()
    assert [n for n in previous if previous[n]!=current[n]]==['be']
    assert [d for d in old['declarations'] if d['name']!='la']==[
        previous[d['name']] for d in new['declarations'] if d['name']!='la']
    assert current['be']['body']['kind']=='and' and current['be']['body']['arguments'][0]==previous['be']['body']
    assert current['be']['body']['arguments'][1]==dict(kind='call',symbol='la',arguments=[dict(kind='variable',name=n) for n in ('va','vb','vc','vd')])
    assert old['statements']==new['statements']
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert after.entries['be']['meaning_ja']==MEANING
    for name in previous:
        if name!='be':assert before.entries[name]['meaning_ja']==after.entries[name]['meaning_ja'],name
    projection=load_catalog(ROOT,BASIS,document_path=LIBRARY)
    assert document(LIBRARY)['declarations']==closure(new,['bi'])
    prior_dependencies=before.audit()['definition_primitive_dependencies']
    dependent=[name for name,deps in after.audit()['definition_primitive_dependencies'].items()
        if 'la' in deps and 'la' not in prior_dependencies[name]]
    assert 'bi' in dependent and 'hzic' in dependent and 'cp' in dependent
    return dict(new_declarations=0,changed_definition_bodies=['be'],moved_declarations=['la'],
        unchanged_statement_syntax=len(new['statements']),new_subject_dependencies=dependent,
        complete_basis_checked=True,library_declarations=len(projection.entries))


def attribution():
    # The actual title statement presents bi without evaluating its contents.
    doc=deepcopy(document(FULL));doc['statements']=doc['statements'][:1]
    values={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    seen=[]
    expected=dict(kind='apply',function=dict(kind='function_ref',symbol='rqqq'),arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol='bi'))])
    def question(node,author,code,scene):
        seen.append('question');return (node,author,scene)==('reader','other','start') and code.rank==1 and json.loads(code.syntax)==expected
    def answer(node,author,code,scene):
        seen.append('answer');return (node,author,scene)==('plan','other','start') and code.rank==0 and json.loads(code.syntax)==dict(kind='function_ref',symbol='bi')
    values.update(hzia=lambda:'reader',wb=lambda:'plan',wa=lambda:'other',wh=lambda:'start',hzib=question,ua=answer,
        ue=lambda a,b,s:(a,b,s)==('reader','plan','start'),hzcs=lambda author,a,b,s:(author,a,b,s)==('other','reader','plan','start'))
    assert evaluate(doc,values)==[True] and seen==['question','answer'],seen
    return dict(same_bi_in_question_and_answer=True,underlying_content_not_executed=True)


def build_report():
    for name,body in build().items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    finite=checks();structural=structure();presentation=attribution()
    for path in (FULL,LIBRARY):
        doc=document(path)
        for notation in ('full','compact'):
            body=format_graph(doc,notation);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    review=json.loads(REVIEW.read_text(encoding='utf-8'))
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']==review['unit'])
    assert unit['text_sha256']==review['unit_sha256']
    start,end=review['range'];assert unit['text'][start:end]==review['source']
    paths=set(build())|set(load_catalog(ROOT,PARENT_BASIS).source_sha256)|{
        'scripts/compose_subject_bound_departure.py','scripts/check_subject_bound_departure.py',
        'tests/test_subject_bound_departure.py','docs/subject-bound-departure-v1.md',
        'data/subject-bound-departure-review-v1.json','artifacts/written-units-v1/kant-1784.json',
        'noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path:paths.add(Path(path).resolve().relative_to(ROOT).as_posix())
    return dict(status='corrected_subject_binding_partial_semantic_review',document=FULL,finite=finite,structure=structural,
        attribution=presentation,roundtrips=True,cli_parse=True,source_review='data/subject-bound-departure-review-v1.json',
        new_source_coverage_claimed=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Subject-bound departure, old counterexamples and nonfactive title attribution verified')


if __name__=='__main__':main()
