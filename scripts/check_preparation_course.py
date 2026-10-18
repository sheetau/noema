"""Check acquisition inside a method without treating missing data as no gain."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_preparation_course import ROOT,SOURCE,SOURCE_BASIS,PARENT,PARENT_BASIS,LIBRARY,EXAMPLE,BASIS,EXAMPLE_BASIS,MEANINGS,build,catalogs

REPORT='reports/preparation-course-v1.json'


def unknown(*args):raise ValueError('Unknown preparation input')


def evaluate(doc,values,domain=('person','process','event','other'),scenes=('start','middle','end','outside')):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=scenes,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=20000000,memoize_definitions=False,memoize_expressions=False)]


@lru_cache(None)
def generic():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zp[] a.r zh[d] c.r zo[d d] c.r zs[] d.r ze[] d.r za[a d] c.r zc[a d] c.
r zr[] a.r zv[] j[a].r zw[a] d.r zt[a d d] c.r zx[a a d d] c.r zy[a a d] c.r zz[a a a d d] c.
'''
    args='k zp[] p zh p zo k zs[] k ze[] p za'
    tail=' p zc k zr[] k zv[] p zw p zt p zx p zy p zz'
    text+='q[k rqvf['+args+']].q[k rqvh['+args+' p zc]].q[k rqvg['+args+' p zc]].q[k rqvi['+args+tail+']].'
    text+='q[k r5[k zp[] k zr[] k zv[] p zw p zo k zs[] k ze[] p za p zc p zt p zx p zy p zz]].'
    return parse(text)


def model(capable=(False,True,True),assessed=(True,True,True),variant='baseline'):
    points=('start','middle','end');order={'start':0,'middle':1,'outside':1.5,'end':2}
    def before(a,b):return order[a]<order[b] or variant=='cycle' and (a,b)==('end','start')
    event_point='outside' if variant=='outside_experience' else 'middle'
    return dict(zp=lambda:'person',zh=lambda s:variant!='empty_history' and s in points,zo=before,zs=lambda:'start',ze=lambda:'end',
        za=lambda p,s:p=='person' and s in points and assessed[points.index(s)],
        zc=lambda p,s:p=='person' and s in points and capable[points.index(s)],
        zr=lambda:'process',zv=lambda:SequenceValue(() if variant=='empty_experience' else ('event',),'"individual"'),zw=lambda e:event_point,
        zt=lambda p,s,t:variant!='other_process' and (p,s,t)==('process','start','end'),
        zx=lambda p,r,s,t:variant!='other_learner' and (p,r,s,t)==('person','process','start','end'),
        zy=lambda p,e,s:(p,e,s)==('person','event',event_point),
        zz=lambda e,p,r,s,t:variant!='no_contribution' and (e,p,r,s,t)==('event','person','process','start','end'))


def combinations():
    doc=generic();rows=[]
    for capable,assessed in product(list(product((False,True),repeat=3)),repeat=2):
        valid=all(assessed);gain=any(not capable[i] and capable[j] for i in range(3) for j in range(i+1,3))
        acquisition=not capable[0] and capable[2]
        actual=evaluate(doc,model(capable,assessed))
        assert actual==[valid,valid and gain,valid and not gain,valid and acquisition,assessed[0] and assessed[2] and acquisition],(capable,assessed,actual)
        rows.append(dict(capable=capable,assessed=assessed,values=actual))
    return dict(count=len(rows),cases=rows,intermediate_gain_not_hidden_by_equal_endpoints=True,
        experiential_acquisition_implies_interval_gain_when_valid=True,uncached_and_unlowered=True)


def contrasts():
    doc=generic();rows={}
    for name,options,expected in [
        ('gained_then_lost',{'capable':(False,True,False)},[True,True,False,False,False]),
        ('already_held',{'capable':(True,True,True)},[True,False,True,False,False]),
        ('lost_only',{'capable':(True,False,False)},[True,False,True,False,False]),
        ('unassessed_middle',{'assessed':(True,False,True)},[False,False,False,False,True]),
        ('no_contribution',{'variant':'no_contribution'},[True,True,False,False,False]),
        ('other_process',{'variant':'other_process'},[True,True,False,False,False]),
        ('other_learner',{'variant':'other_learner'},[True,True,False,False,False]),
        ('outside_experience',{'variant':'outside_experience'},[True,True,False,False,True]),
        ('empty_experience',{'variant':'empty_experience'},[True,True,False,False,False]),
        ('empty_history',{'variant':'empty_history'},[False,False,False,False,True]),
        ('cycle',{'variant':'cycle'},[False,False,False,False,True]),
    ]:
        actual=evaluate(doc,model(**options));assert actual==expected,(name,actual);rows[name]=actual
    for name in ('zh','zo','za','zc','zz'):
        values=model();values[name]=unknown
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown preparation' in str(error)
        else:raise AssertionError(name)
    return dict(cases=rows,unknown_inputs_refused=5,absence_of_learning_witness_not_no_gain=True)


def source_model(doc,variant='baseline'):
    from scripts.check_method_scope import model as previous
    values=previous(doc,success=('direct','training') if variant=='known_success_unassessed_other' else ('training',))
    order={'anchor':0,'middle':1,'directend':2,'trainend':3,'task':4,'success':5,'failure':6}
    points={'direct':{'anchor','directend','task'},'training':{'anchor','middle','trainend','task'}}
    values.update(zdirect=lambda:'direct',ztraining=lambda:'training',
        zhistory=lambda p,m,a,s,t:(p,a,s)==('person','anchor','anchor') and t in points.get(m,set()),
        zfinish=lambda p,m,a,s:'directend' if m=='direct' else 'trainend' if m=='training' else 'anchor',
        ztaskpoint=lambda p,m,a,s:'middle' if variant=='task_before_preparation' else 'failure' if variant=='task_outside_history' else 'task',
        zbefore=lambda s,t:order[s]<order[t],
        zassessed=lambda p,s:p=='person' and not(variant in ('missing_middle','known_success_unassessed_other') and s=='middle'),
        zcapable=lambda p,s:p=='person' and (s=='middle' or s=='trainend' and variant!='gained_then_lost'),
        zprocess=lambda m:'process' if m=='training' else 'other',
        zevents=lambda m:SequenceValue(('event',) if m=='training' else (),'"individual"'),zwhen=lambda e:'middle',
        ztransitions=lambda r,s,t:(r,s,t)==('process','anchor','trainend'),
        zaffected=lambda p,r,s,t:(p,r,s,t)==('person','process','anchor','trainend'),
        zexperience=lambda p,e,s:(p,e,s)==('person','event','middle'),
        zcontributes=lambda e,p,r,s,t:variant!='no_contribution' and (e,p,r,s,t)==('event','person','process','anchor','trainend'),
        ae=values['zavailable'],af=values['zoutcomes'],ap=values['zselected'],aa=lambda p:p=='person',
        ab=lambda f,p,s:(f,p)==('faculty','person'),ac=lambda p,f,a,s:(p,f,a,s)==('person','faculty','act','success'),ad=lambda *args:False)
    return values


def source_checks():
    doc=parse((ROOT/EXAMPLE).read_text(encoding='utf-8'));rows={}
    for variant,expected in [
        ('baseline',[True,False,True,False,True,True,True,True]),
        ('gained_then_lost',[False,False,True,False,True,True,True,True]),
        ('no_contribution',[False,False,True,False,True,True,True,True]),
        ('missing_middle',[False,False,True,False,True,False,False,False]),
        ('known_success_unassessed_other',[False,False,True,True,False,False,False,True]),
        ('task_before_preparation',[False,False,True,False,True,False,False,False]),
        ('task_outside_history',[False,False,True,False,True,False,False,False]),
    ]:
        actual=evaluate(doc,source_model(doc,variant),('person','direct','training','faculty','act','other','process','event'),
            ('anchor','middle','directend','trainend','task','success','failure'))
        assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(cases=rows,scope_is_native_definition_not_boolean_input=True,
        unknown_method_classification_does_not_certify_inability=True,known_eligible_success_does_not_require_all_classifications=True)


def structure():
    source,parent=catalogs();lib=load_catalog(ROOT,BASIS);example=load_catalog(ROOT,EXAMPLE_BASIS)
    assert all(d['kind']=='definition' for d in lib.document['declarations'])
    assert len(set(lib.entries)-set(source.entries))==5
    assert example.entries['zscope']['declaration']['kind']=='definition'
    for name,entry in parent.entries.items():
        if name!='zscope':
            assert example.entries[name]['declaration']==entry['declaration']
            assert example.entries[name]['meaning_ja']==entry['meaning_ja']
    for name in ('ta','rlz','r4','r5'):
        assert lib.entries[name]['declaration']==source.entries[name]['declaration']
        assert lib.entries[name]['meaning_ja']==source.entries[name]['meaning_ja']
    for path in (LIBRARY,EXAMPLE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(new_generic_definitions=5,new_generic_primitives=0,scope_replaced_by_composition=True,
        original_acquisition_and_interval_bodies_preserved=True,roundtrips=True,example_questions=8)


def build_report():
    outputs=build()
    for p,text in outputs.items():assert (ROOT/p).read_text(encoding='utf-8')==text,p
    results={}
    for name,fn in [('combinations',combinations),('contrasts',contrasts),('source',source_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    prior=json.loads((ROOT/'reports/method-scope-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    inventory='artifacts/written-units-v1/kant-1784.json';units=json.loads((ROOT/inventory).read_text(encoding='utf-8'))['units']
    unit=next(u for u in units if u['id']=='kant-1784:u0008')
    alignment=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[86,181],source=unit['text'][86:181],
        definitions=['rqvf','rqvh','rqvg','rqvi','rqvj','zscope'],status='partial_preparation_comparison',full_semantic_equivalence=False)
    from scripts.audit_written_progress_extended import collect_alignment
    assert len(collect_alignment(dict(alignment=alignment),{u['id']:u for u in units},set(load_catalog(ROOT,EXAMPLE_BASIS).entries),REPORT))==1
    paths=set(outputs)|set(prior['source_sha256'])|set(catalogs()[0].source_sha256)|set(catalogs()[1].source_sha256)|{
        'reports/method-scope-v1.json','scripts/compose_preparation_course.py','scripts/check_preparation_course.py',
        'scripts/compose_limits.py','tests/test_preparation_course.py','docs/preparation-course-v1.md',inventory}
    return dict(status='preparatory_gain_derived_from_assessed_history_not_canonical_reading',document=EXAMPLE,**results,
        alignment=alignment,new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==result
    else:
        with (ROOT/REPORT).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Assessed preparation and experience connected without treating missing classification as inability',flush=True)


if __name__=='__main__':main()
