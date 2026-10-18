"""Check practical directives without mistaking quotation for performance."""
import argparse
from copy import deepcopy
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_courageous_undertaking import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,MEANINGS,build,closure,replace_symbols

REPORT=ROOT/'reports/courageous-undertaking-v1.json'
EVIDENCE='data/courageous-undertaking-reading-v1.json'
DOMAIN=('person','other','act','otheract','author','first','second','third','latin','german','conclusion')
SCENES=('now','other')


def unknown(*args):raise ValueError('Unknown undertaking interpretation')


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=2000000,memoize_definitions=False,memoize_expressions=False)]


def is_goal(code,name):
    return code.rank==0 and json.loads(code.syntax)==dict(kind='function_ref',symbol=name)


def generic_document():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zperson[] a.r zscene[] d.r zsuccess[a d] c.
d zgoal[person a] e[b scene[k zsuccess[v person v scene]]].
d zothergoal[person a] e[b scene[k zsuccess[v person v scene]]].
q[t[k hzs4[k zperson[] r[p zgoal]]][k zscene[]]].
q[t[o[k hzs5[k zperson[] r[p zgoal]]]][k zscene[]]].
q[u[e[k hzs5[k zperson[] r[p zgoal]]][j s[k hzs4[k zperson[] r[p zgoal]]]]]].
q[t[k zgoal[k zperson[]]][k zscene[]]].
''')


def model(doc,bits=(True,True,True,True),success=False,variant='baseline'):
    courage,attempt,actor,occurs=bits
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    values.update(zperson=lambda:'person',zscene=lambda:'now',zsuccess=lambda p,s:success,
        hzio=lambda p,g,s:courage and (p,s)==('other' if variant=='other_courage_person' else 'person','other' if variant=='other_courage_scene' else 'now') and is_goal(g,'zothergoal' if variant=='other_courage_goal' else 'zgoal'),
        f5=lambda p,a,g,s:attempt and (p,a,s)==('other' if variant=='other_attempt_person' else 'person',
            'otheract' if variant=='other_attempt_act' else 'act','other' if variant=='other_attempt_scene' else 'now') and is_goal(g,'zothergoal' if variant=='other_attempt_goal' else 'zgoal'),
        df=lambda p,a,s:actor and (p,a,s)==('other' if variant=='other_actor' else 'person','act','other' if variant=='other_actor_scene' else 'now'),
        dg=lambda a,s:occurs and (a,s)==('otheract' if variant=='other_occurrence_act' else 'act','other' if variant=='other_occurrence_scene' else 'now'))
    return values


def generic_checks():
    doc=generic_document();count=0
    for bits in product((False,True),repeat=4):
        for success in (False,True):
            actual=evaluate(doc,model(doc,bits,success));assert actual==[all(bits),all(bits),True,success],(bits,success,actual)
            count+=1
    variants=('other_courage_person','other_courage_scene','other_courage_goal','other_attempt_person','other_attempt_act',
        'other_attempt_scene','other_attempt_goal','other_actor','other_actor_scene','other_occurrence_act','other_occurrence_scene')
    for variant in variants:assert evaluate(doc,model(doc,variant=variant))==[False,False,True,False],variant
    quoted=deepcopy(doc);quoted['statements']=doc['statements'][:3]
    values=model(quoted);values['zsuccess']=unknown
    assert evaluate(quoted,values)==[True,True,True]
    for name in ('hzio','f5','df','dg'):
        values=model(quoted);values[name]=unknown
        try:evaluate(quoted,values)
        except ValueError as error:assert 'Unknown undertaking' in str(error)
        else:raise AssertionError(name)
    return dict(courage_attempt_actor_occurrence_success_combinations=count,binding_contrasts=len(variants),
        unknown_inputs_refused=4,target_success_not_evaluated=True,directive_distinct_from_assertion=True,
        failed_attempt_can_satisfy_undertaking=True,uncached_and_unlowered=True)


def source_checks():
    full=parse((ROOT/FULL).read_text(encoding='utf-8'));doc=deepcopy(full)
    doc['declarations']=closure(doc,['hzs6','bl','bn','ao']);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+'r zscene[] d.'+
        'q[t[o[k hzs6[k ao[]]]][k zscene[]]].q[t[o[k bl[k ao[]]]][k zscene[]]].q[t[o[k bn[k ao[]]]][k zscene[]]].')
    rows=[]
    for courage,attempt in product((False,True),repeat=2):
        # Old goal definitions are actually evaluated by this finite engine.
        # Empty assessment and no use make both old goals false, not unknown;
        # courage and trying still need not entail their achievement.
        values={d['name']:(lambda *args:False) for d in doc['declarations'] if d['kind']=='primitive'}
        values.update(ao=lambda:'person',zscene=lambda:'now',al=lambda p,g,s:courage and p=='person',
            hzio=lambda p,g,s:courage and p=='person' and is_goal(g,'bk'),
            f5=lambda p,a,g,s:attempt and (p,a)==('person','act') and is_goal(g,'bk'),
            df=lambda p,a,s:(p,a)==('person','act'),dg=lambda a,s:a=='act')
        actual=evaluate(doc,values);assert actual==[courage and attempt,courage,courage],(courage,attempt,actual)
        rows.append(dict(courage=courage,attempt=attempt,new_latin_old_latin_german=actual))
    motto=deepcopy(full);motto['declarations']=closure(motto,['hzsa']);motto['statements']=[]
    motto=parse(format_graph(motto,'compact')+'r zscene[] d.q[t[k hzsa[]][k zscene[]]].')
    for old_latin in (False,True):
        values={d['name']:unknown for d in motto['declarations'] if d['kind']=='primitive'}
        values['zscene']=lambda:'now'
        def motto_relation(parts,property_code,scene):
            wanted=['bl' if old_latin else 'hzs6','bn']
            return is_goal(property_code,'bi') and [json.loads(c.syntax)['symbol'] for c in parts.items]==wanted
        values['ga']=motto_relation
        assert evaluate(motto,values)==[not old_latin]
    return dict(content_contrasts=rows,motto_uses_updated_latin_and_unchanged_german=True,
        old_goals_false_does_not_preclude_undertaking=True)


def attribution_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));nodes=('first','second','third','latin','german','conclusion')
    rows={}
    for variant in ('baseline','old_latin','old_motto','swapped_quotes','reverse_explanation','other_author','other_context'):
        values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        values.update({n:(lambda value=value:value) for n,value in zip(('wa','wb','wc','wd','we','wf','wg'),('author',*nodes))})
        values['wh']=lambda:'now'
        def context(a,c):return (a,c)==('person' if variant=='other_author' else 'author','other' if variant=='other_context' else 'now')
        def define(n,a,code,c):return context(a,c) and json.loads(code.syntax)==dict(kind='function_ref',symbol={'first':'bi','second':'bf'}.get(n))
        def quoted(n,a,code,c):
            expected={'latin':'bl' if variant=='old_latin' else 'hzs6','german':'bn'}
            if variant=='swapped_quotes':expected={'latin':'bn','german':'hzs6'}
            return context(a,c) and json.loads(code.syntax)==dict(kind='call',symbol=expected.get(n),arguments=[dict(kind='call',symbol='ao',arguments=[])])
        def claim(n,a,code,c):return context(a,c) and json.loads(code.syntax)==dict(kind='call',symbol={'third':'rqrk','conclusion':'bo' if variant=='old_motto' else 'hzsa'}.get(n),arguments=[])
        values.update(ua=define,ub=quoted,uc=claim,
            ue=lambda a,b,c:c=='now' and a in nodes and b in nodes and nodes.index(a)<nodes.index(b),
            uf=lambda a,x,y,c:context(a,c) and (x,y)==(('german','latin') if variant=='reverse_explanation' else ('latin','german')),
            ud=lambda a,p,n,c:context(a,c) and n=='conclusion' and [x for x in DOMAIN if p(x)]==list(nodes[:-1]))
        actual=evaluate(doc,values);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    return dict(cases=rows,all_quoted_world_relations_unknown=True,success_and_undertaking_not_asserted=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-6]==old.document['declarations']
    assert set(new.entries)-set(old.entries)==set(MEANINGS)
    for name in old.entries:assert old.entries[name]==new.entries[name]
    assert new.document['statements'][1]==replace_symbols(old.document['statements'][1],{'cp':'hzsb'})
    for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'],strict=True)):
        if i!=1:assert a==b
    index=json.loads((ROOT/'data/semantic-review-index-v23.json').read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[r['index'] for r in review['selection']['statements']]
        assert selection_binding(old,indices)==review['selection']==selection_binding(new,indices)
    return dict(new_definitions=6,new_primitives=0,changed_statement_indices=[1],other_statements_preserved=34,
        eight_review_bindings_preserved=True,old_definitions_available_for_comparison=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def alignment():
    from scripts.audit_written_progress_extended import collect_alignment
    evidence=json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8'));u=evidence['source']
    result=dict(unit=u['unit'],unit_sha256=u['unit_sha256'],range=u['range'],source=u['text'],
        definitions=['hzs4','hzs5','hzs6','hzsb'],status='partial_practical_latin_directive',full_semantic_equivalence=False)
    units={r['id']:r for r in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']}
    rows=collect_alignment(dict(alignment=result),units,set(MEANINGS),'reports/courageous-undertaking-v1.json')
    assert len(rows)==1 and rows[0]['status']=='partial' and rows[0]['range']==[382,394]
    return result


def build_report():
    files=build()
    for p,body in files.items():assert (ROOT/p).read_text(encoding='utf-8')==body,p
    results={}
    for name,fn in [('generic',generic_checks),('source',source_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    for p in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    prior=json.loads((ROOT/'reports/answer-heading-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    evidence=json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8'));validate_hashes(ROOT,evidence['source_sha256'])
    paths=set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|set(prior['source_sha256'])|set(evidence['source_sha256'])|{
        'reports/answer-heading-v1.json',EVIDENCE,'scripts/compose_courageous_undertaking.py','scripts/check_courageous_undertaking.py',
        'tests/test_courageous_undertaking.py','docs/courageous-undertaking-v1.md','data/semantic-review-index-v23.json'}
    return dict(status='practical_directive_candidate_checked_not_whole_unit_equivalence',document=FULL,**results,roundtrips=True,
        alignment=alignment(),new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Practical directive, motto reference and attribution checked',flush=True)


if __name__=='__main__':main()
