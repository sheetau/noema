"""Exercise the native ability definitions with anchored method restrictions."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_subject_bound_departure import closure
from scripts.compose_method_scope import ROOT,SOURCE,SOURCE_BASIS,LIBRARY,EXAMPLE,BASIS,EXAMPLE_BASIS,PARENT,PARENT_BASIS,build,catalog

REPORT='reports/method-scope-v1.json'
DOMAIN=('person','direct','training','faculty','act','guide','other')
SCENES=('anchor','opportunity','success','failure')


def unknown(*args):raise ValueError('Unknown method scope input')


def evaluate(doc,values,domain=DOMAIN):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=SCENES,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=7000000,memoize_definitions=False,memoize_expressions=False)]


@lru_cache(None)
def generic():
    parent=catalog().document;doc=deepcopy(parent);doc['declarations']=closure(parent,['xd','xg','xf']);doc['statements']=[]
    from scripts.compose_method_scope import definition
    text=format_graph(doc,'compact')+definition()+'''
r zperson[] a.r zanchor[] d.r zscope[a a d d] c.r zavailable[a a d] c.
r zoutcomes[a a d d] c.r zselected[a a d d] c.r zsuccess[d] c.
d zgoal[] e[b scene[k zsuccess[v scene]]].
'''
    args='k zperson[] k zgoal[] k zanchor[] '
    scoped='k rqve[k zanchor[] p zscope p zavailable]'
    tail=' p zoutcomes p zselected'
    for name,available in [('xd','p zavailable'),('xg','p zavailable'),('xd',scoped),('xg',scoped),('xf',scoped)]:
        text+='q[k '+name+'['+args+available+tail+']].'
    return parse(text)


def model(doc,available=('direct','training'),eligible=('direct',),success=('training',),variant='baseline',now=True):
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    def enabled(p,m,s):return p=='person' and m in available and (s=='opportunity' or now and s=='anchor')
    def scope(p,m,a,s):
        return (p,a)==('other' if variant=='other_person' else 'person','opportunity' if variant=='other_anchor' else 'anchor') and m in eligible and s==('success' if variant=='other_scene' else s)
    def outcomes(p,m,s,t):return enabled(p,m,s) and t in ('success','failure')
    def selected(p,m,s,t):
        if not enabled(p,m,s) or variant=='missing_direct_assessment' and m=='direct' or variant=='missing_training_assessment' and m=='training':return False
        if variant=='foreign_direct_result' and m=='direct':return t=='opportunity'
        if variant=='mixed_direct_results' and m=='direct':return t in ('success','failure')
        return t==('success' if m in success else 'failure')
    values.update(zperson=lambda:'person',zanchor=lambda:'anchor',zscope=scope,
        zavailable=enabled,zoutcomes=outcomes,zselected=selected,zsuccess=lambda s:s=='success',
        zcases=lambda p,a,s:(p,a,s)==('person','anchor','opportunity'),
        zpreserved=lambda p,a,s:(p,a)==('person','anchor'),
        zopportunity=lambda p,s:p=='person' and (s=='opportunity' or now and s=='anchor'),
        zpreferred=lambda *args:False)
    return values


def combinations():
    doc=generic();subsets=[{m for i,m in enumerate(('direct','training')) if mask&(1<<i)} for mask in range(4)]
    rows=[]
    for available,eligible,success in product(subsets,repeat=3):
        actual=evaluate(doc,model(doc,available,eligible,success),('person','direct','training','other'))
        raw=bool(available&success);restricted=bool(available&eligible&success)
        assert actual==[raw,not raw,restricted,not restricted,True],(available,eligible,success,actual)
        rows.append(dict(available=sorted(available),eligible=sorted(eligible),successful=sorted(success),values=actual))
    return dict(count=len(rows),cases=rows,independent_set_intersection=True,uncached_and_unlowered=True)


def scope_checks():
    doc=generic();rows={}
    for name,options,expected in [
        ('training_route_only_succeeds',{},[True,False,False,True,True]),
        ('both_routes_succeed',{'success':('direct','training')},[True,False,True,False,True]),
        ('eligible_but_unavailable',{'available':('training',)},[True,False,False,True,True]),
        ('empty_method_scope',{'eligible':()},[True,False,False,True,True]),
        ('other_person',{'variant':'other_person'},[True,False,False,True,True]),
        ('other_anchor',{'variant':'other_anchor'},[True,False,False,True,True]),
        ('other_scene',{'variant':'other_scene'},[True,False,False,True,True]),
        ('missing_direct_assessment',{'variant':'missing_direct_assessment'},[True,False,False,False,False]),
        ('foreign_direct_result',{'variant':'foreign_direct_result'},[True,False,False,False,False]),
        ('excluded_unassessed_training',{'variant':'missing_training_assessment'},[False,False,False,True,True]),
        ('retained_failure_is_not_removed',{'variant':'mixed_direct_results','success':('direct','training')},[True,False,False,True,True]),
    ]:
        actual=evaluate(doc,model(doc,**options),('person','direct','training','other'));assert actual==expected,(name,actual);rows[name]=actual
    direct=deepcopy(doc);direct['statements']=direct['statements'][2:]
    for name in ('zscope','zavailable','zoutcomes','zselected'):
        values=model(direct);values[name]=unknown
        try:evaluate(direct,values,('person','direct','training','other'))
        except ValueError as error:assert 'Unknown method scope' in str(error)
        else:raise AssertionError(name)
    return dict(cases=rows,unknown_inputs_refused=4,scope_absence_not_global_inability=True,
        retained_method_outcomes_not_reselected=True)


def source_checks():
    doc=parse((ROOT/EXAMPLE).read_text(encoding='utf-8'));rows={}
    for name,options,expected in [
        ('training_route_only_succeeds',{},[True,False,False,True,True,False,True]),
        ('existing_execution_succeeds',{'success':('direct','training')},[True,False,True,False,True,True,False]),
        ('no_current_opportunity',{'now':False,'success':('direct','training')},[False,True,False,True,True,True,False]),
        ('missing_execution_assessment',{'variant':'missing_direct_assessment'},[True,False,False,False,True,False,False]),
        ('other_baseline',{'variant':'other_anchor'},[True,False,False,True,True,False,True]),
        ('same_person_but_guided',{},[False,True,False,True,False,False,True]),
    ]:
        values=model(doc,**options)
        values.update(ae=values['zavailable'],af=values['zoutcomes'],ap=values['zselected'],aa=lambda p:p=='person',
            ab=lambda f,p,s:(f,p)==('faculty','person'),ac=lambda p,f,a,s:(p,f,a,s)==('person','faculty','act','success'),
            ad=lambda g,p,a,s:name=='same_person_but_guided' and (g,p,a,s)==('guide','person','act','success'))
        actual=evaluate(doc,values);assert actual==expected,(name,actual);rows[name]=actual
    return dict(cases=rows,native_bb_bc_and_ability_profiles_executed=True,
        preparation_classification_is_explicit_fixture_input=True,not_a_definition_of_learning=True)


def structure():
    old=catalog();lib=load_catalog(ROOT,BASIS);example=load_catalog(ROOT,EXAMPLE_BASIS)
    assert len(lib.document['declarations'])==1 and not lib.document['statements']
    assert set(example.entries)-set(old.entries)=={'rqve','zscope'}
    for name,entry in old.entries.items():
        assert example.entries[name]['declaration']==entry['declaration']
        assert example.entries[name]['meaning_ja']==entry['meaning_ja']
    for path in (LIBRARY,EXAMPLE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(new_generic_definitions=1,new_generic_primitives=0,new_diagnostic_relations=1,
        example_questions=7,canonical_manuscript_not_changed=True,roundtrips=True,
        library_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for path,text in outputs.items():assert (ROOT/path).read_text(encoding='utf-8')==text,path
    results={}
    for name,fn in [('combinations',combinations),('scope',scope_checks),('source',source_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    prior=json.loads((ROOT/'reports/opening-claims-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    inventory='artifacts/written-units-v1/kant-1784.json';units=json.loads((ROOT/inventory).read_text(encoding='utf-8'))['units']
    unit=next(u for u in units if u['id']=='kant-1784:u0008')
    alignment=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[86,181],source=unit['text'][86:181],
        definitions=['bc','rqve','rqva'],status='partial_method_scope_comparison',full_semantic_equivalence=False)
    from scripts.audit_written_progress_extended import collect_alignment
    assert len(collect_alignment(dict(alignment=alignment),{u['id']:u for u in units},set(load_catalog(ROOT,EXAMPLE_BASIS).entries),REPORT))==1
    paths=set(outputs)|set(prior['source_sha256'])|set(catalog().source_sha256)|{SOURCE,SOURCE_BASIS,
        'reports/opening-claims-v1.json','reports/standing-ability-v1.json',inventory,
        'scripts/compose_method_scope.py','scripts/check_method_scope.py','tests/test_method_scope.py','docs/method-scope-v1.md'}
    return dict(status='method_range_explicit_without_selecting_source_ability_reading',document=EXAMPLE,**results,
        alignment=alignment,new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==result
    else:
        with (ROOT/REPORT).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Method scope, present opportunity and outcome assessment checked separately',flush=True)


if __name__=='__main__':main()
