"""Compare actual causal conditions, explanatory adoption and source quotation."""
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
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from scripts import check_described_transition as transition
from scripts import check_subject_bound_departure as subject
from scripts.compose_factive_cause import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,MEANINGS,build,closure

REPORT=ROOT/'reports/factive-cause-v1.json'
REVIEW='data/factive-cause-review-v1.json'


@lru_cache(None)
def fixture(path):
    doc=deepcopy(subject.fixture(path));doc['statements']=[]
    params='k jstarget[] r[p bs] r[p bj] r[p bf] k jsstart[]'
    return parse(format_graph(doc,'compact')+
        'q[k bd[k jstarget[] k jsstart[]]].'+
        'q[k be[k jstarget[] k jsprocess[] k jsstart[] k jsend[]]].'+
        'q[t[k bi[k jsprocess[]]][k jsend[]]].'+
        'q[k rqqv['+params+']].q[k ed['+params+']].')


def model(doc,variant='baseline',bits=(True,True,True,False,False),adoption=(True,False),old_variant='baseline'):
    lacks_resolve,lacks_courage,selected_cause,lacks_understanding,excluded_cause=bits
    values=transition.model(doc,old_variant=old_variant)
    values.update(ai=lambda p,s:not lacks_resolve,aj=lambda p,s:not lacks_courage,ak=lambda p,s:not lacks_understanding)
    def causal(person,factor,target,result,scene):
        if variant=='unknown_causality':raise ValueError('Unknown causal contribution')
        wanted=('other' if variant=='other_factor_person' else 'reader',
            'other' if variant=='other_result_person' else 'reader','outside' if variant=='other_scene' else 'start')
        if (person,target,scene)!=wanted or factor.rank!=0 or result.rank!=0:return False
        if json.loads(result.syntax)!=dict(kind='function_ref',symbol='up' if variant=='other_result' else 'bf'):return False
        name=json.loads(factor.syntax).get('symbol')
        if variant=='reversed_causality':return name=='bf'
        if variant=='other_factor':return name=='bq' and selected_cause
        return selected_cause if name=='bs' else excluded_cause if name=='bj' else False
    def adopted(person,factor,target,result,scene):
        if (person,target,scene)!=('reader','reader','start') or json.loads(result.syntax)!=dict(kind='function_ref',symbol='bf'):return False
        name=json.loads(factor.syntax).get('symbol')
        return adoption[0] if name=='bs' else adoption[1] if name=='bj' else False
    values['ea']=adopted
    if 'hzie' in values:values['hzie']=causal
    return values


@lru_cache(None)
def checks():
    doc=fixture(LIBRARY);count=0
    for bits in product((False,True),repeat=5):
        expected=bits[0] and bits[1] and bits[2] and not(bits[3] and bits[4])
        actual=subject.evaluate(doc,model(doc,bits=bits));assert actual==[expected]*4+[True],(bits,actual)
        count+=1
    contrasts={}
    for path in (LIBRARY,FULL):
        doc=fixture(path);contrasts[path]={}
        for variant in ('baseline','other_factor_person','other_result_person','other_scene','other_result','other_factor','reversed_causality'):
            actual=subject.evaluate(doc,model(doc,variant));assert actual==[variant=='baseline']*4+[True],(path,variant,actual)
            contrasts[path][variant]=actual
    doc=fixture(LIBRARY);adoptions=[]
    for adopted in product((False,True),repeat=2):
        actual=subject.evaluate(doc,model(doc,adoption=adopted));assert actual==[True]*4+[adopted[0] and not adopted[1]]
        adoptions.append(dict(adopted=list(adopted),values=actual))
    cases={
        'adopted_but_no_cause':((True,True,False,False,False),(True,False),True,False),
        'adopted_but_no_resolve_deficit':((False,True,True,False,False),(True,False),True,False),
        'adopted_but_no_courage_deficit':((True,False,True,False,False),(True,False),True,False),
        'excluded_factor_actually_causes':((True,True,True,True,True),(True,False),True,False),
        'actual_cause_not_adopted':((True,True,True,False,False),(False,False),False,True),
        'excluded_factor_exists_without_causing':((True,True,True,True,False),(True,False),True,True),
    }
    regression={};old=subject.fixture(PARENT);new=fixture(FULL)
    for name,(bits,adopted,before,after) in cases.items():
        prior=subject.evaluate(old,model(old,bits=bits,adoption=adopted));current=subject.evaluate(new,model(new,bits=bits,adoption=adopted))
        assert prior==[before]*2 and current[:4]==[after]*4,(name,prior,current)
        regression[name]=dict(previous_departure=prior,revised=current)
    inherited={}
    for variant in ('different_person','different_process','different_start','different_end','witness_only','cause_only',
        'no_affected_subject','empty_final_assessment','foreign_final_assessment','unknown_initial_assessment',
        'still_guided','no_available_method','reversed_transition'):
        actual=subject.evaluate(new,model(new,old_variant=variant));assert actual[1:3]==[False,False],(variant,actual)
        inherited[variant]=actual
    for bits in ((True,True,True,False,False),(True,True,False,False,False)):
        doc=deepcopy(fixture(LIBRARY))
        # Audit the changed causal predicate, its generic form and adoption
        # directly. Eagerly expanding the entire process-valued bi repeatedly
        # enumerates unrelated before/after possibilities and exceeds the
        # finite evaluator's budget; the full process uses the guarded checks.
        doc['statements']=[doc['statements'][i] for i in (0,3,4)]
        assert subject.evaluate(doc,model(doc,bits=bits),short=False,memoize=False)==subject.evaluate(doc,model(doc,bits=bits))
    try:subject.evaluate(doc,model(doc,'unknown_causality'))
    except ValueError as error:assert 'Unknown causal contribution' in str(error)
    else:raise AssertionError('Unknown causal relation was silently accepted')
    return dict(five_condition_combinations=count,role_contrasts=contrasts,independent_adoption_cases=adoptions,
        previous_and_revised=regression,inherited_departure_contrasts=inherited,unlowered_uncached_cases=2,
        unlowered_scope=['bd','rqqv','ed'],unknown_causality_refused=True)


def structure():
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    old=before.document;new=after.document;a={d['name']:d for d in old['declarations']};b={d['name']:d for d in new['declarations']}
    assert set(b)-set(a)=={'hzie','rqqu','rqqv'} and not set(a)-set(b)
    assert [n for n in a if a[n]!=b[n]]==['bd']
    assert [d['name'] for d in old['declarations']]==[d['name'] for d in new['declarations'] if d['name'] in a]
    assert old['statements']==new['statements']
    for n in a:
        if n not in ('bd','be'):assert before.entries[n]['meaning_ja']==after.entries[n]['meaning_ja']
    for n,meaning in MEANINGS.items():assert after.entries[n]['meaning_ja']==meaning
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY);assert lib.document['declarations']==closure(new,['bi','ed','rqqv'])
    dependencies=after.audit()['definition_primitive_dependencies']
    assert 'ea' not in dependencies['bd'] and 'hzie' in dependencies['bd']
    assert dependencies['ed']==['ea']
    return dict(new_primitives=1,new_definitions=2,changed_bodies=['bd'],statement_syntax_preserved=16,
        causal_condition_replaces_adoption_in_bd=True,old_adoption_definitions_preserved=True,library_declarations=len(lib.entries))


def rank_and_attribution():
    doc=deepcopy(subject.document(FULL));doc['statements']=[];prefix=format_graph(doc,'compact')
    parse(prefix+'q[e[r[p bd]][r[p bd]]].')
    parse(prefix+'q[e[r b[p rqqv]][r b[p rqqv]]].')
    try:parse(prefix+'q[e[r[p rqqv]][r[p rqqv]]].')
    except ValueError as error:assert 'Quoted evaluation must target strictly lower ranks' in str(error)
    else:raise AssertionError('Arbitrary description evaluation was quoted at rank zero')
    doc=deepcopy(subject.document(FULL));doc['statements']=doc['statements'][:1]
    values={d['name']:subject.forbidden for d in doc['declarations'] if d['kind']=='primitive'};seen=[]
    expected=dict(kind='apply',function=dict(kind='function_ref',symbol='rqqq'),arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol='bi'))])
    def question(node,author,code,scene):
        seen.append('question');return (node,author,scene)==('reader','other','start') and code.rank==1 and json.loads(code.syntax)==expected
    def answer(node,author,code,scene):
        seen.append('answer');return (node,author,scene)==('plan','other','start') and code.rank==0 and json.loads(code.syntax)==dict(kind='function_ref',symbol='bi')
    values.update(hzia=lambda:'reader',wb=lambda:'plan',wa=lambda:'other',wh=lambda:'start',hzib=question,ua=answer,
        ue=lambda a,b,s:(a,b,s)==('reader','plan','start'),hzcs=lambda author,a,b,s:(author,a,b,s)==('other','reader','plan','start'))
    assert subject.evaluate(doc,values)==[True] and seen==['question','answer']
    return dict(generic_requires_rank_one=True,specialized_source_remains_rank_zero=True,presentation_does_not_evaluate_causality=True)


def build_report():
    files=build()
    for path,body in files.items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    finite=checks();structural=structure();ranks=rank_and_attribution()
    for path in (FULL,LIBRARY):
        doc=subject.document(path)
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    review=json.loads((ROOT/REVIEW).read_text(encoding='utf-8'));unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']==review['unit'])
    start,end=review['range'];assert unit['text_sha256']==review['unit_sha256'] and unit['text'][start:end]==review['source']
    paths=set(files)|set(load_catalog(ROOT,PARENT_BASIS).source_sha256)|{REVIEW,review['comparison']['snapshot'],
        'docs/factive-cause-v1.md','tests/test_factive_cause.py','artifacts/written-units-v1/kant-1784.json',
        'scripts/compose_factive_cause.py','scripts/check_factive_cause.py','scripts/check_described_transition.py',
        'scripts/compose_described_transition.py','scripts/check_subject_bound_departure.py','scripts/compose_subject_bound_departure.py',
        'noema/__init__.py','noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    assert hashlib.sha256((ROOT/review['comparison']['snapshot']).read_bytes()).hexdigest()==review['comparison']['sha256']
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path:paths.add(Path(path).resolve().relative_to(ROOT).as_posix())
    return dict(status='actual_cause_distinguished_from_explanatory_adoption',document=FULL,finite=finite,structure=structural,
        quotation=ranks,roundtrips=True,cli_parse=True,source_review=REVIEW,new_source_coverage_claimed=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Factive cause, explanatory adoption, source binding and quotation ranks checked')


if __name__=='__main__':main()
