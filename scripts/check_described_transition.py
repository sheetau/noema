"""Check transition content independently of coincident endpoint truths."""
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
from scripts import check_subject_bound_departure as previous
from scripts.compose_described_transition import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,PRIMITIVE,CONVENTION,MEANING,build,closure

REPORT=ROOT/'reports/described-transition-v1.json'
REVIEW=ROOT/'data/described-transition-review-v1.json'


@lru_cache(None)
def fixture(path):
    doc=deepcopy(previous.fixture(path));statements=doc['statements'];doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+'d jdbefore[x a] e[k bp[v x]].d jdafter[x a] e[k up[v x]].')
    doc['statements']=statements
    return doc


def model(doc,variant='baseline',bits=(True,True,True,True,True),old_variant='baseline'):
    values=previous.model(doc,old_variant,bits=bits[:4])
    def binding(person,process,prior,later,start,end):
        if variant=='unknown_transition_content':raise ValueError('Unknown transition content')
        expected=['reader','change','bp','up','start','after']
        replacement={'other_property_pair':(2,'bq'),'other_after_property':(3,'br'),
            'weaker_before_property':(2,'bf'),'other_person':(0,'other'),'other_process':(1,'unrelated'),
            'other_start':(4,'outside'),'other_end':(5,'outside')}
        if variant in replacement:
            index,value=replacement[variant];expected[index]=value
        if variant=='reversed_properties':expected[2:4]=['up','bp']
        if variant=='equivalent_alias_record':expected[2:4]=['jdbefore','jdafter']
        actual=[person,process,json.loads(prior.syntax).get('symbol'),json.loads(later.syntax).get('symbol'),start,end]
        return bits[4] and variant!='no_content_record' and prior.rank==later.rank==0 and actual==expected
    if PRIMITIVE in values:values[PRIMITIVE]=binding
    return values


@lru_cache(None)
def checks():
    doc=fixture(LIBRARY);combinations=0
    for bits in product((False,True),repeat=5):
        actual=previous.evaluate(doc,model(doc,bits=bits));assert actual==[all(bits)]*2,(bits,actual)
        combinations+=1
    variants=('baseline','other_property_pair','other_after_property','weaker_before_property','reversed_properties',
        'other_person','other_process','other_start','other_end','equivalent_alias_record','no_content_record')
    contrasts={};counterexamples={}
    for path in (LIBRARY,FULL):
        doc=fixture(path);contrasts[path]={}
        for variant in variants:
            actual=previous.evaluate(doc,model(doc,variant));assert actual==[variant=='baseline']*2,(path,variant,actual)
            contrasts[path][variant]=actual
    old=previous.fixture(PARENT)
    for variant in variants[1:]:
        actual=previous.evaluate(old,model(old,variant));assert actual==[True,True],variant
        counterexamples[variant]=dict(previous=actual,revised=contrasts[FULL][variant])
    inherited={};doc=fixture(FULL)
    for variant in ('different_person','different_process','different_start','different_end','witness_only','cause_only',
        'no_affected_subject','empty_final_assessment','foreign_final_assessment','unknown_initial_assessment',
        'still_guided','no_available_method','absent_cause_explanation','reversed_transition'):
        actual=previous.evaluate(doc,model(doc,old_variant=variant));assert actual==[False,False],variant
        inherited[variant]=actual
    for variant in ('baseline','other_property_pair'):
        doc=fixture(LIBRARY)
        assert previous.evaluate(doc,model(doc,variant),short=False,memoize=False)==contrasts[LIBRARY][variant]
    try:previous.evaluate(doc,model(doc,'unknown_transition_content'))
    except ValueError as error:assert 'Unknown transition content' in str(error)
    else:raise AssertionError('Unknown transition content was silently accepted')
    # Equal endpoint values do not substitute one intensional record for another.
    alias=deepcopy(doc);alias['statements']=[]
    alias=parse(format_graph(alias,'compact')+
        'q[z[t[k bp[k jstarget[]]][k jsstart[]]][t[k jdbefore[k jstarget[]]][k jsstart[]]]].'+
        'q[z[t[k up[k jstarget[]]][k jsend[]]][t[k jdafter[k jstarget[]]][k jsend[]]]].'+
        'q[k hzid[k jstarget[] k jsprocess[] r[p jdbefore] r[p jdafter] k jsstart[] k jsend[]]].')
    alias_values=previous.evaluate(alias,model(alias,'equivalent_alias_record'));assert alias_values==[True,True,True]
    return dict(five_condition_combinations=combinations,content_contrasts=contrasts,old_counterexamples=counterexamples,
        inherited_contrasts=inherited,unlowered_uncached_cases=2,unknown_content_refused=True,
        equivalent_aliases_require_their_own_record=alias_values)


def structure():
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    old=before.document;new=after.document
    a={d['name']:d for d in old['declarations']};b={d['name']:d for d in new['declarations']}
    assert set(b)-set(a)=={PRIMITIVE} and not set(a)-set(b)
    assert [n for n in a if a[n]!=b[n]]==['be']
    assert [d for d in old['declarations'] if d['name'] not in ('bp','up')]==[
        a[d['name']] for d in new['declarations'] if d['name'] not in ('bp','up',PRIMITIVE)]
    assert b['be']['body']['arguments'][0]==a['be']['body']
    quoted=b['be']['body']['arguments'][1]
    assert quoted==dict(kind='call',symbol=PRIMITIVE,arguments=[dict(kind='variable',name='va'),dict(kind='variable',name='vb'),
        dict(kind='quote',body=dict(kind='function_ref',symbol='bp')),dict(kind='quote',body=dict(kind='function_ref',symbol='up')),
        dict(kind='variable',name='vc'),dict(kind='variable',name='vd')])
    assert new['statements']==old['statements']
    assert after.entries['be']['meaning_ja']==MEANING and after.entries[PRIMITIVE]['meaning_ja']==CONVENTION
    for n in a:
        if n!='be':assert before.entries[n]['meaning_ja']==after.entries[n]['meaning_ja'],n
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY)
    assert lib.document['declarations']==closure(new,['bi'])
    depends=[n for n,refs in after.audit()['definition_primitive_dependencies'].items() if PRIMITIVE in refs]
    assert {'be','bi','cp','hzic'}<=set(depends)
    # The final property is exactly the previous xd achievement plus aa. aa
    # is already required by bd, so quoting up adds no new endpoint condition.
    assert set(after.explain(['up'])['retained_symbols'])=={'aa','ab','ac','ad','ae','af','ap','bb','xa','xd','up'}
    return dict(new_primitives=[PRIMITIVE],new_definitions=0,changed_bodies=['be'],moved_declarations=['bp','up'],
        unchanged_statement_syntax=len(new['statements']),dependent_definitions=depends,library_declarations=len(lib.entries))


def attribution():
    doc=deepcopy(previous.document(FULL));doc['statements']=doc['statements'][:1]
    values={d['name']:previous.forbidden for d in doc['declarations'] if d['kind']=='primitive'};seen=[]
    expected=dict(kind='apply',function=dict(kind='function_ref',symbol='rqqq'),arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol='bi'))])
    def question(node,author,code,scene):
        seen.append('question');return (node,author,scene)==('reader','other','start') and code.rank==1 and json.loads(code.syntax)==expected
    def answer(node,author,code,scene):
        seen.append('answer');return (node,author,scene)==('plan','other','start') and code.rank==0 and json.loads(code.syntax)==dict(kind='function_ref',symbol='bi')
    values.update(hzia=lambda:'reader',wb=lambda:'plan',wa=lambda:'other',wh=lambda:'start',hzib=question,ua=answer,
        ue=lambda a,b,s:(a,b,s)==('reader','plan','start'),hzcs=lambda author,a,b,s:(author,a,b,s)==('other','reader','plan','start'))
    assert previous.evaluate(doc,values)==[True] and seen==['question','answer']
    return dict(same_revised_bi_in_question_and_answer=True,transition_content_not_executed=True)


def build_report():
    files=build()
    for path,body in files.items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    finite=checks();structural=structure();presented=attribution()
    for path in (FULL,LIBRARY):
        doc=previous.document(path)
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    review=json.loads(REVIEW.read_text(encoding='utf-8'));unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']==review['unit'])
    start,end=review['range'];assert unit['text_sha256']==review['unit_sha256'] and unit['text'][start:end]==review['source']
    prior_review=json.loads((ROOT/review['previous_review']).read_text(encoding='utf-8'))
    assert review['corrected_item']==prior_review['remaining'][0]
    paths=set(files)|set(load_catalog(ROOT,PARENT_BASIS).source_sha256)|{
        'data/described-transition-review-v1.json','data/subject-bound-departure-review-v1.json','artifacts/written-units-v1/kant-1784.json',
        'docs/described-transition-v1.md','tests/test_described_transition.py',
        'scripts/compose_described_transition.py','scripts/check_described_transition.py',
        'scripts/compose_subject_bound_departure.py','scripts/check_subject_bound_departure.py',
        'noema/__init__.py','noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path:paths.add(Path(path).resolve().relative_to(ROOT).as_posix())
    return dict(status='described_transition_bound_to_opening_departure',document=FULL,finite=finite,structure=structural,
        attribution=presented,roundtrips=True,cli_parse=True,source_review='data/described-transition-review-v1.json',
        new_source_coverage_claimed=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Described transition, old counterexamples, source binding and quotation verified')


if __name__=='__main__':main()
