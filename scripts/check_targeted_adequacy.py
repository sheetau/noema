"""Check explicit goal binding in deficits, causation and source quotation."""
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
from scripts import check_factive_cause as cause
from scripts import check_subject_bound_departure as subject
from scripts.compose_targeted_adequacy import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,build,closure

REPORT=ROOT/'reports/targeted-adequacy-v1.json'
REVIEW='data/targeted-adequacy-review-v1.json'


@lru_cache(None)
def fixture(path):
    doc=deepcopy(subject.fixture(path));doc['statements']=[]
    return parse(format_graph(doc,'compact')+
        'q[k bd[k jstarget[] k jsstart[]]].q[k be[k jstarget[] k jsprocess[] k jsstart[] k jsend[]]].'+
        'q[t[k bi[k jsprocess[]]][k jsend[]]].'+
        'q[k rqqv[k jstarget[] r[p rqrh] r[p rqri] r[p bf] k jsstart[]]].')


def model(doc,bits=(True,True,True,False,False),legacy=(True,True,False),variant='baseline',old_variant='baseline'):
    resolve,courage,selected,understanding,excluded=bits
    values=cause.model(doc,bits=(legacy[0],legacy[1],selected,legacy[2],excluded),old_variant=old_variant)
    targeted=any(d['name']=='hzin' for d in doc['declarations'])
    def assessment(deficit):
        records={(person,'bb',scene):not(deficit and (person,scene)==('reader','start'))
            for person in subject.DOMAIN for scene in subject.SCENES}
        other_key={'missing_goal_assessment':('reader','bf','start'),
            'different_assessment_person':('other','bb','start'),
            'different_assessment_scene':('reader','bb','outside')}.get(variant)
        if other_key:
            records.pop(('reader','bb','start'));records[other_key]=not deficit
        def sufficient(person,goal,scene):
            body=json.loads(goal.syntax)
            if goal.rank!=0 or body.get('kind')!='function_ref':
                raise ValueError('Unknown assessment goal')
            key=(person,body['symbol'],scene)
            if key not in records:raise ValueError('Unknown assessment for this person, goal and scene')
            return records[key]
        return sufficient
    if targeted:values.update(hzin=assessment(resolve),hzio=assessment(courage),hzip=assessment(understanding))
    def causal(person,factor,target,result,scene):
        if variant=='unknown_cause':raise ValueError('Unknown causal contribution')
        if (person,target,scene)!=('other' if variant=='different_cause_person' else 'reader','reader','start'):return False
        if result.rank!=0 or json.loads(result.syntax)!=dict(kind='function_ref',symbol='bf'):return False
        name=json.loads(factor.syntax).get('symbol')
        chosen='rqrh' if targeted else 'bs';removed='rqri' if targeted else 'bj'
        if variant=='old_unqualified_cause':chosen,removed='bs','bj'
        if variant=='reversed_cause':return name=='bf'
        return selected if name==chosen else excluded if name==removed else False
    values['hzie']=causal
    return values


@lru_cache(None)
def goal_assessment_checks():
    doc=deepcopy(subject.fixture(LIBRARY));doc['statements']=[]
    queries=''.join('q[k '+r+'[k jstarget[] r[p '+goal+'] k jsstart[]]].' for r in PRIMITIVES for goal in ('bb','bf'))
    doc=parse(format_graph(doc,'compact')+queries);count=0
    for bits in product((False,True),repeat=6):
        values={d['name']:subject.forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        values.update(jstarget=lambda:'reader',jsstart=lambda:'start')
        for index,relation in enumerate(PRIMITIVES):
            def assessment(person,goal,scene,index=index):
                assert (person,scene)==('reader','start') and goal.rank==0
                name=json.loads(goal.syntax)['symbol'];assert name in ('bb','bf')
                return bits[2*index+(name=='bf')]
            values[relation]=assessment
        assert subject.evaluate(doc,values,short=False,memoize=False)==list(bits);count+=1
    return dict(two_goal_three_assessment_combinations=count,goals_not_evaluated=True,unlowered_uncached=True)


@lru_cache(None)
def checks():
    doc=fixture(LIBRARY);count=0
    for bits in product((False,True),repeat=5):
        expected=bits[0] and bits[1] and bits[2] and not(bits[3] and bits[4])
        actual=subject.evaluate(doc,model(doc,bits=bits));assert actual==[expected]*4,(bits,actual);count+=1
    old=subject.fixture(PARENT);new=fixture(FULL);regression={}
    cases={
        'old_resolve_refers_to_another_goal':((False,True,True,False,False),(True,True,False),True,False),
        'old_courage_refers_to_another_goal':((True,False,True,False,False),(True,True,False),True,False),
        'old_understanding_refers_to_another_goal':((True,True,True,True,True),(True,True,False),True,False),
        'actual_deficits_despite_other_goal_adequacy':((True,True,True,False,False),(False,False,True),False,True),
    }
    for name,(bits,legacy,previous,revised) in cases.items():
        before=subject.evaluate(old,model(old,bits=bits,legacy=legacy));after=subject.evaluate(new,model(new,bits=bits,legacy=legacy))
        assert before==[previous]*2 and after==[revised]*4,(name,before,after)
        regression[name]=dict(previous=before,revised=after)
    legacy_cases=[]
    for legacy in product((False,True),repeat=3):
        actual=subject.evaluate(doc,model(doc,legacy=legacy));assert actual==[True]*4
        legacy_cases.append(dict(legacy=list(legacy),values=actual))
    contrasts={}
    for path in (LIBRARY,FULL):
        current=fixture(path);contrasts[path]={}
        for variant in ('baseline','old_unqualified_cause','different_cause_person','reversed_cause'):
            actual=subject.evaluate(current,model(current,variant=variant));assert actual==[variant=='baseline']*4
            contrasts[path][variant]=actual
    refused=[]
    for variant in ('missing_goal_assessment','different_assessment_person','different_assessment_scene','unknown_cause'):
        try:subject.evaluate(doc,model(doc,variant=variant))
        except ValueError as error:assert 'Unknown' in str(error);refused.append(variant)
        else:raise AssertionError('Unknown evidence became a deficit: '+variant)
    inherited={}
    for variant in ('different_person','different_process','different_start','different_end','empty_final_assessment','still_guided'):
        actual=subject.evaluate(new,model(new,old_variant=variant));assert actual[1:3]==[False,False]
        inherited[variant]=actual
    direct=deepcopy(doc);direct['statements']=[doc['statements'][i] for i in (0,3)]
    for bits in ((True,True,True,False,False),(False,True,True,False,False)):
        assert subject.evaluate(direct,model(direct,bits=bits),short=False,memoize=False)==subject.evaluate(direct,model(direct,bits=bits))
    return dict(condition_combinations=count,previous_and_revised=regression,independent_legacy_assessments=legacy_cases,
        cause_contrasts=contrasts,unknown_evidence_refused=refused,inherited_departure_contrasts=inherited,unlowered_uncached_cases=2)


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    a={d['name']:d for d in old.document['declarations']};b={d['name']:d for d in new.document['declarations']}
    assert set(b)-set(a)==set(PRIMITIVES)|{'rqqy','rqqz','rqrh','rqri'} and not set(a)-set(b)
    assert [n for n in a if a[n]!=b[n]]==['bd']
    assert [n for n in b if n in a]==list(a)
    assert old.document['statements']==new.document['statements'] and len(new.document['statements'])==17
    for n in a:
        if n not in ('bd','be'):assert old.entries[n]['meaning_ja']==new.entries[n]['meaning_ja']
        if a[n]['kind']=='primitive':assert old.entries[n]['arguments']==new.entries[n]['arguments']
    for n,meaning in MEANINGS.items():assert new.entries[n]['meaning_ja']==meaning
    assert closure(old.document,['hzil'])==closure(new.document,['hzil'])
    annotations=load_annotations(ROOT,BASIS,ANNOTATIONS)
    previous=load_annotations(ROOT,PARENT_BASIS,'data/author-credit-identifiers-v1.json')
    assert annotations.show()['entries']==previous.show()['entries']
    dependencies=new.audit()['definition_primitive_dependencies']['bd']
    assert set(PRIMITIVES)<=set(dependencies) and not {'ai','aj','ak'}&set(dependencies)
    assert load_catalog(ROOT,BASIS,document_path=LIBRARY).document['declarations']==closure(new.document,['bi','ed','rqqv','bs','bj'])
    return dict(new_primitives=3,new_definitions=4,changed_bodies=['bd'],statement_syntax_preserved=17,
        legacy_assessments_preserved=True,signature_dependency_declarations_and_conventions_unchanged=True,
        identifier_forms_unchanged=True,source_deficits_require_goal_bound_assessments=True)


def attribution():
    doc=deepcopy(subject.document(FULL));doc['statements']=[];prefix=format_graph(doc,'compact')
    parse(prefix+'q[e[r[p bd]][r[p bd]]].')
    doc['statements']=deepcopy(subject.document(FULL)['statements'][:1])
    values={d['name']:subject.forbidden for d in doc['declarations'] if d['kind']=='primitive'};seen=[]
    def question(node,author,code,scene):
        seen.append('question');return code.rank==1
    def answer(node,author,code,scene):
        seen.append('answer');return code.rank==0 and json.loads(code.syntax)==dict(kind='function_ref',symbol='bi')
    values.update(hzia=lambda:'reader',wb=lambda:'plan',wa=lambda:'other',wh=lambda:'start',hzib=question,ua=answer,
        ue=lambda a,b,s:(a,b,s)==('reader','plan','start'),hzcs=lambda author,a,b,s:(author,a,b,s)==('other','reader','plan','start'))
    assert subject.evaluate(doc,values)==[True] and seen==['question','answer']
    doc['statements']=deepcopy(subject.document(FULL)['statements'][1:2]);presented=[]
    values={d['name']:subject.forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    nodes={'wb':'reader','wc':'plan','wd':'faculty','we':'act','wf':'change','wg':'unrelated','wa':'other'}
    values.update({key:(lambda value=value:value) for key,value in nodes.items()});values['wh']=lambda:'start'
    def concept(node,author,code,scene):
        name=json.loads(code.syntax).get('symbol');presented.append(name)
        return (node,author,name,scene) in (('reader','other','bi','start'),('plan','other','bf','start'),('faculty','other','bp','start')) and code.rank==0
    order={nodes[name]:i for i,name in enumerate(('wb','wc','wd','we','wf','wg'))}
    values.update(ua=concept,ub=lambda *args:True,uc=lambda *args:True,uf=lambda *args:True,ud=lambda *args:True,
        ue=lambda first,second,scene:scene=='start' and first in order and second in order and order[first]<order[second])
    assert subject.evaluate(doc,values)==[True] and presented==['bi','bf','bp']
    return dict(source_condition_rank_zero=True,definition_presentation_does_not_evaluate_assessments=True,
        opening_three_definition_descriptions=presented)


def build_report():
    files=build()
    for p,body in files.items():assert (ROOT/p).read_text(encoding='utf-8')==body,p
    goals=goal_assessment_checks();finite=checks();structural=structure();presentation=attribution()
    for p in (FULL,LIBRARY):
        doc=subject.document(p)
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==doc
    review=json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']==review['unit'])
    start,end=review['range'];assert unit['text_sha256']==review['unit_sha256'] and unit['text'][start:end]==review['source']
    comparison=review['comparison'];assert hashlib.sha256((ROOT/comparison['snapshot']).read_bytes()).hexdigest()==comparison['sha256']
    paths=set(files)|set(load_catalog(ROOT,PARENT_BASIS).source_sha256)|{
        REVIEW,comparison['snapshot'],'data/author-credit-identifiers-v1.json','docs/targeted-adequacy-v1.md','tests/test_targeted_adequacy.py',
        'scripts/compose_targeted_adequacy.py','scripts/check_targeted_adequacy.py','scripts/check_factive_cause.py','scripts/compose_factive_cause.py',
        'scripts/check_described_transition.py','scripts/compose_described_transition.py','scripts/check_subject_bound_departure.py',
        'scripts/compose_subject_bound_departure.py','artifacts/written-units-v1/kant-1784.json',
        'noema/__init__.py','noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path:paths.add(Path(path).resolve().relative_to(ROOT).as_posix())
    added=set(PRIMITIVES)|{'rqqy','rqqz','rqrh','rqri'}
    lines=files[FULL].splitlines()
    new_declarations=[line for line in lines if line.startswith(('r ','d ')) and line.split()[1].split('[')[0] in added]
    assert len(new_declarations)==7
    sizes=dict(manuscript_characters=len(files[FULL]),library_characters=len(files[LIBRARY]),
        new_declaration_characters=sum(len(line) for line in new_declarations),
        manuscript_character_increase=len(files[FULL])-len((ROOT/PARENT).read_text(encoding='utf-8')),
        note='Explicit goal arguments and their shared declarations have a cost; unchanged statement references are not a compression ratio.')
    return dict(status='opening_deficits_bound_to_explicit_goal',document=FULL,goal_assessments=goals,finite=finite,structure=structural,
        presentation=presentation,roundtrips=True,cli_parse=True,source_review=REVIEW,size_accounting=sizes,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],source=review['source'],
            status='partial_goal_bound_causal_condition',definitions=['rqqy','rqqz','rqrh','rqri','bd'],remaining=review['remaining'])]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Explicit goal assessments, causal conditions, inherited scope and source presentation checked')


if __name__=='__main__':main()
