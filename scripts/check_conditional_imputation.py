"""Check conditional direction, imputation scope and attribution of the claim."""
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
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from scripts import check_targeted_adequacy as targeted
from scripts import check_subject_bound_departure as subject
from scripts.compose_conditional_imputation import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,MEANINGS,build,closure

REPORT=ROOT/'reports/conditional-imputation-v1.json'
REVIEW='data/conditional-imputation-review-v1.json'


@lru_cache(None)
def fixture(path):
    doc=deepcopy(subject.fixture(path));doc['statements']=[]
    return parse(format_graph(doc,'compact')+
        'q[k bd[k jstarget[] k jsstart[]]].q[k rqrj[k jstarget[] k jsstart[]]].q[t[k bp[k jstarget[]]][k jsstart[]]].'+
        'q[k be[k jstarget[] k jsprocess[] k jsstart[] k jsend[]]].q[t[k bi[k jsprocess[]]][k jsend[]]].'+
        'q[t[k rqrk[]][k jsstart[]]].q[t[k rqrl[]][k jsstart[]]].')


def model(doc,criterion=True,imputed=True,variant='baseline',old_variant='baseline',bits=None):
    values=targeted.model(doc,bits=bits or (True,True,criterion,False,False),old_variant=old_variant)
    if variant=='no_initial_state':values['ap']=lambda p,m,s,t:(p,m,t)==('reader','plan','left')
    def imputes(person,state,scene):
        if variant=='unknown_imputation':raise ValueError('Unknown imputation')
        return imputed and (person,scene)==('other' if variant=='other_person' else 'reader','outside' if variant=='other_scene' else 'start') and state.rank==0 and json.loads(state.syntax)==dict(kind='function_ref',symbol='bb' if variant=='other_state' else 'bf')
    if 'hziq' in values:values['hziq']=imputes
    return {d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}


@lru_cache(None)
def checks():
    combinations=[];new=fixture(FULL);old=subject.fixture(PARENT)
    for criterion,imputed in product((False,True),repeat=2):
        actual=subject.evaluate(new,model(new,criterion,imputed))
        expected=[criterion,imputed,imputed,imputed,imputed,not criterion or imputed,criterion==imputed]
        assert actual==expected,(criterion,imputed,actual)
        before=subject.evaluate(old,model(old,criterion,imputed));assert before==[criterion]*2
        combinations.append(dict(criterion=criterion,imputed=imputed,revised=actual,previous_departure=before))
    direct=deepcopy(new);direct['statements']=[new['statements'][i] for i in (0,1,5,6)]
    for criterion,imputed in product((False,True),repeat=2):
        assert subject.evaluate(direct,model(direct,criterion,imputed),short=False,memoize=False)==subject.evaluate(direct,model(direct,criterion,imputed))
    finite=deepcopy(new);finite['statements']=new['statements'][:1];count=0
    for bits in product((False,True),repeat=5):
        expected=bits[0] and bits[1] and bits[2] and not(bits[3] and bits[4])
        assert subject.evaluate(finite,model(finite,bits=bits))==[expected];count+=1
    contrasts={}
    for path in (LIBRARY,FULL):
        doc=fixture(path);contrasts[path]={}
        for variant in ('baseline','other_person','other_state','other_scene','no_initial_state'):
            actual=subject.evaluate(doc,model(doc,variant=variant))
            expected=[True]*7 if variant=='baseline' else [False]*5+[True,True] if variant=='no_initial_state' else [True]+[False]*6
            assert actual==expected,(variant,actual)
            contrasts[path][variant]=actual
    unknown=deepcopy(new);unknown['statements']=new['statements'][1:2]
    try:subject.evaluate(unknown,model(unknown,variant='unknown_imputation'))
    except ValueError as error:assert 'Unknown imputation' in str(error)
    else:raise AssertionError('Causal criterion substituted for unknown imputation')
    inherited={}
    for variant in ('different_person','different_process','different_start','different_end','empty_final_assessment','still_guided'):
        actual=subject.evaluate(new,model(new,old_variant=variant));assert actual[3:5]==[False,False]
        inherited[variant]=actual
    return dict(direction_combinations=combinations,causal_combinations_preserved=count,imputation_contrasts=contrasts,
        inherited_departure_contrasts=inherited,unknown_imputation_refused=True,unlowered_uncached_cases=4)


def second_person():
    doc=deepcopy(fixture(LIBRARY));doc['statements']=doc['statements'][5:];rows=[]
    for other_cause,other_imputation in product((False,True),repeat=2):
        values=model(doc);values['aa']=lambda p:p in ('reader','other')
        # Give each person the same ability/transition assessment; their causal
        # criterion and imputation remain independently assigned below.
        for name,index in [('ab',1),('ac',0),('ad',1),('ae',0),('af',0),('ap',0)]:
            original=values[name]
            def mapped(*args,original=original,index=index):
                args=list(args)
                if args[index]=='other':args[index]='reader'
                return original(*args)
            values[name]=mapped
        values['hzin']=lambda person,goal,scene:scene!='start'
        values['hzio']=lambda person,goal,scene:scene!='start'
        values['hzip']=lambda *args:True
        values['hzie']=lambda person,factor,target,result,scene:person==target and scene=='start' and json.loads(factor.syntax)==dict(kind='function_ref',symbol='rqrh') and json.loads(result.syntax)==dict(kind='function_ref',symbol='bf') and (person=='reader' or person=='other' and other_cause)
        values['hziq']=lambda person,state,scene:scene=='start' and json.loads(state.syntax)==dict(kind='function_ref',symbol='bf') and (person=='reader' or person=='other' and other_imputation)
        actual=subject.evaluate(doc,values);assert actual==[not other_cause or other_imputation,other_cause==other_imputation]
        rows.append(dict(other_cause=other_cause,other_imputation=other_imputation,values=actual))
    return rows


def presentation():
    doc=deepcopy(subject.document(FULL));doc['statements']=doc['statements'][1:2]
    nodes={'wb':'reader','wc':'plan','wd':'faculty','we':'act','wf':'change','wg':'unrelated','wa':'other'}
    order={nodes[n]:i for i,n in enumerate(('wb','wc','wd','we','wf','wg'))};results={}
    for variant in ('baseline','missing_condition','equivalence_instead','other_author','other_node','other_context'):
        values={d['name']:subject.forbidden for d in doc['declarations'] if d['kind']=='primitive'};seen=[]
        values.update({n:(lambda value=value:value) for n,value in nodes.items()});values['wh']=lambda:'start'
        def defines(node,author,code,scene):
            name=json.loads(code.syntax).get('symbol');seen.append(('defines',name))
            return (node,author,name,scene) in (('reader','other','bi','start'),('plan','other','bf','start')) and code.rank==0
        def asserts(node,author,code,scene):
            name=json.loads(code.syntax).get('symbol');seen.append(('asserts',name))
            if name=='bo':return True
            if variant=='missing_condition':return False
            return (node,author,scene)==('act' if variant=='other_node' else 'faculty','reader' if variant=='other_author' else 'other','outside' if variant=='other_context' else 'start') and code.rank==0 and json.loads(code.syntax)==dict(kind='call',symbol='rqrl' if variant=='equivalence_instead' else 'rqrk',arguments=[])
        values.update(ua=defines,uc=asserts,ub=lambda *args:True,uf=lambda *args:True,ud=lambda *args:True,
            ue=lambda a,b,s:s=='start' and a in order and b in order and order[a]<order[b])
        actual=subject.evaluate(doc,values);assert actual==[variant=='baseline'],(variant,actual)
        if variant=='baseline':assert seen==[('defines','bi'),('defines','bf'),('asserts','rqrk'),('asserts','bo')]
        results[variant]=actual
    return dict(cases=results,underlying_causality_and_imputation_not_evaluated=True)


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    a={d['name']:d for d in old.document['declarations']};b={d['name']:d for d in new.document['declarations']}
    assert set(b)-set(a)=={'hziq','rqrj','rqrk','rqrl'} and not set(a)-set(b)
    assert [n for n in a if a[n]!=b[n]]==['bp','be','cp']
    assert [n for n in b if n in a]==list(a) and old.document['statements']==new.document['statements']
    for n in a:
        if n not in MEANINGS:assert old.entries[n]['meaning_ja']==new.entries[n]['meaning_ja']
        if a[n]['kind']=='primitive':assert old.entries[n]['arguments']==new.entries[n]['arguments']
    assert closure(old.document,['hzil'])==closure(new.document,['hzil'])
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==load_annotations(ROOT,PARENT_BASIS,'data/targeted-adequacy-identifiers-v1.json').show()['entries']
    assert load_catalog(ROOT,BASIS,document_path=LIBRARY).document['declarations']==closure(new.document,['bi','bd','rqrk','rqrl'])
    deps=new.audit()['definition_primitive_dependencies']
    assert 'hziq' in deps['be'] and 'hzie' not in deps['be'] and 'hziq' not in deps['bd']
    for path in (FULL,LIBRARY):
        doc=deepcopy(subject.document(path));doc['statements']=[]
        parse(format_graph(doc,'compact')+'q[e[r[p bi]][r[p bi]]].q[e[r[k rqrk[]]][r[k rqrk[]]]].')
    return dict(new_primitives=1,new_definitions=3,changed_bodies=['bp','be','cp'],statement_syntax_preserved=17,
        causal_criterion_unchanged=True,source_rank_zero_preserved=True,signature_dependencies_and_forms_unchanged=True)


def build_report():
    files=build()
    for path,body in files.items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    finite=checks();universal=second_person();attribution=presentation();structural=structure()
    for path in (FULL,LIBRARY):
        doc=subject.document(path)
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==doc
    review=json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']==review['unit'])
    start,end=review['range'];assert unit['text_sha256']==review['unit_sha256'] and unit['text'][start:end]==review['source']
    for name,value in review['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value,name
    paths=set(files)|set(load_catalog(ROOT,PARENT_BASIS).source_sha256)|set(review['source_sha256'])|{
        REVIEW,'data/targeted-adequacy-identifiers-v1.json','docs/conditional-imputation-v1.md','tests/test_conditional_imputation.py',
        'scripts/compose_conditional_imputation.py','scripts/check_conditional_imputation.py',
        'scripts/check_targeted_adequacy.py','scripts/compose_targeted_adequacy.py','scripts/check_factive_cause.py','scripts/compose_factive_cause.py',
        'scripts/check_described_transition.py','scripts/compose_described_transition.py','scripts/check_subject_bound_departure.py',
        'scripts/compose_subject_bound_departure.py','artifacts/written-units-v1/kant-1784.json',
        'noema/__init__.py','noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path:paths.add(Path(path).resolve().relative_to(ROOT).as_posix())
    return dict(status='explicit_conditional_reading_not_whole_unit_equivalence',document=FULL,finite=finite,
        universal_scope=universal,presentation=attribution,structure=structural,roundtrips=True,cli_parse=True,
        size_accounting=dict(manuscript_characters=len(files[FULL]),library_characters=len(files[LIBRARY]),
            manuscript_character_increase=len(files[FULL])-len((ROOT/PARENT).read_text(encoding='utf-8'))),
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],source=review['source'],
            status='partial_conditional_imputation_reading',definitions=['bd','rqrj','bp','rqrk','cp'],remaining=review['remaining'])]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Conditional direction, imputed state and source attribution checked separately')


if __name__=='__main__':main()
