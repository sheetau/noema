"""Check bound attempts without executing their goals or quoted norm contents."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_bound_undertaking import ROOT,FULL,CORE,LIBRARY,BASIS,PARENT,PARENT_BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

INDEX='data/semantic-review-index-v70.json'
REPORT='reports/bound-undertaking-v1.json'
READING='data/bound-undertaking-reading-v1.json'
DOC='docs/bound-undertaking-v1.md'
DOMAIN=('person','other','attempt','otheract','frame','foot','process')
SCENES=('now','elsewhere')
BINDINGS=('person','frame','foot','process')


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+suffix)


def seq(values):return SequenceValue(tuple(values),'"individual"')


@lru_cache(None)
def generic():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jp[] a.r js[] d.r jb[] j[a].r jvalid[j[a]] c.
r jcourage[a i[h[j[a]] e] j[a] d] c.r jtries[a a i[h[j[a]] e] j[a] d] c.
r jperforms[a a d] c.r joccurs[a d] c.r jcompleted[j[a] d] c.
d jgoal[bindings j[a]] e[b scene[k jcompleted[v bindings v scene]]].
d jothergoal[bindings j[a]] e[b scene[k jcompleted[v bindings v scene]]].
q[t[k rqzi[k jp[] r[p jgoal] k jb[] p jvalid p jcourage p jtries p jperforms p joccurs]][k js[]]].
q[t[k jgoal[k jb[]]][k js[]]].
''')


def generic_values(bits=(True,True,True,True,False),variant='baseline'):
    courage,attempt,actor,occurs,success=bits
    bindings=BINDINGS[:3] if variant=='short_bindings' else BINDINGS+('other',) if variant=='extra_bindings' else BINDINGS
    def expected_bindings(prefix):
        return ('person','frame','other','process') if variant==prefix+'_bindings' else BINDINGS
    return dict(jp=lambda:'person',js=lambda:'now',jb=lambda:seq(bindings),jvalid=lambda b:len(b.items)==4,
        jcompleted=lambda b,s:success,
        jcourage=lambda p,g,b,s:courage and (p,s)==('other' if variant=='courage_person' else 'person',
            'elsewhere' if variant=='courage_scene' else 'now') and b.items==expected_bindings('courage') and
            symbol(g)==('jothergoal' if variant=='courage_goal' else 'jgoal'),
        jtries=lambda p,a,g,b,s:attempt and (p,a,s)==('other' if variant=='attempt_person' else 'person',
            'otheract' if variant=='attempt_act' else 'attempt','elsewhere' if variant=='attempt_scene' else 'now') and
            b.items==expected_bindings('attempt') and symbol(g)==('jothergoal' if variant=='attempt_goal' else 'jgoal'),
        jperforms=lambda p,a,s:actor and (p,a,s)==('other' if variant=='performer' else 'person','attempt',
            'elsewhere' if variant=='performer_scene' else 'now'),
        joccurs=lambda a,s:occurs and (a,s)==('otheract' if variant=='occurrence_act' else 'attempt',
            'elsewhere' if variant=='occurrence_scene' else 'now'))


def generic_checks():
    rows=[];d=generic()
    for bits in product((False,True),repeat=5):
        actual=evaluate(d,generic_values(bits),DOMAIN,SCENES)
        assert actual==[all(bits[:4]),bits[4]],(bits,actual)
        rows.append(dict(bits=bits,values=actual))
    contrasts={}
    for name in ('courage_person','courage_goal','courage_bindings','courage_scene','attempt_person','attempt_act',
            'attempt_goal','attempt_bindings','attempt_scene','performer','performer_scene','occurrence_act',
            'occurrence_scene','short_bindings','extra_bindings'):
        actual=evaluate(d,generic_values(variant=name),DOMAIN,SCENES)
        assert actual==[False,False],(name,actual);contrasts[name]=actual
    only=deepcopy(d);only['statements']=d['statements'][:1]
    v=generic_values();v['jcompleted']=unknown
    assert evaluate(only,v,DOMAIN,SCENES)==[True]
    for name in ('jvalid','jcourage','jtries','jperforms','joccurs'):
        v=generic_values();v[name]=unknown
        try:evaluate(only,v,DOMAIN,SCENES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(combinations=rows,contrasts=contrasts,unknown_inputs_refused=5,
        goal_not_executed=True,failed_attempt_allowed=True,ordinary_evaluation=True)


@lru_cache(None)
def adapter_fixture():
    return fixture(['rqzi','hzs4','hztb'],'''
r jp[] a.r js[] d.r jcompleted[a d] c.
d jold[person a] e[b scene[k jcompleted[v person v scene]]].
d jwrapped[bindings j[a]] e[b scene[w[k hztb[v bindings]][g person a[
 w[a[v bindings][n p a b][v person]][t[k jold[v person]][v scene]]
]]]].
q[t[k hzs4[k jp[] r[p jold]]][k js[]]].
q[t[k rqzi[k jp[] r[p jwrapped] l[a][k jp[]] p hztb
 i[person a goal i[h[j[a]] e] bindings j[a] scene d][w[a[v bindings][n p a b][v person]][k hzio[v person r[p jold] v scene]]]
 i[person a act a goal i[h[j[a]] e] bindings j[a] scene d][w[a[v bindings][n p a b][v person]][k f5[v person v act r[p jold] v scene]]]
 p df p dg]][k js[]]].
q[t[k jold[k jp[]]][k js[]]].
q[t[k jwrapped[l[a][k jp[]]]][k js[]]].
''')


def adapter_checks():
    d=adapter_fixture();rows=[]
    for courage,attempt,actor,occurs,success in product((False,True),repeat=5):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update(jp=lambda:'person',js=lambda:'now',jcompleted=lambda p,s:success and (p,s)==('person','now'),
            hzio=lambda p,g,s:courage and (p,s)==('person','now') and symbol(g)=='jold',
            f5=lambda p,a,g,s:attempt and (p,a,s)==('person','attempt','now') and symbol(g)=='jold',
            df=lambda p,a,s:actor and (p,a,s)==('person','attempt','now'),
            dg=lambda a,s:occurs and (a,s)==('attempt','now'))
        actual=evaluate(d,v,DOMAIN,SCENES)
        expected=courage and attempt and actor and occurs
        assert actual==[expected,expected,success,success],actual
        rows.append(dict(bits=[courage,attempt,actor,occurs,success],values=actual))
    return dict(combinations=rows,existing_unary_goal_and_attempt_actually_evaluated=True,
        explicitly_adapted_relations_only=True,not_automatic_equivalence_of_independent_primitives=True,
        ordinary_evaluation=True)


@lru_cache(None)
def source_fixture():
    return fixture(['rqzk'], 'r jb[] j[a].r js[] d.q[t[k rqzk[k jb[]]][k js[]]].')


def source_values(d,variant='baseline'):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    bindings=BINDINGS[:3] if variant=='short_bindings' else BINDINGS+('other',) if variant=='extra_bindings' else BINDINGS
    if variant=='swapped_body_foot':bindings=('foot','frame','person','process')
    def match(prefix,b):
        changed=list(BINDINGS)
        for index,label in enumerate(('body','carrier','foot','process')):
            if variant==prefix+'_'+label:changed[index]='other'
        return b.items==tuple(changed)
    act='process' if variant=='same_act_and_goal_process' else 'attempt'
    v.update(jb=lambda:seq(bindings),js=lambda:'now',
        hzxz=lambda p,g,b,s:(p,s)==('person','now') and symbol(g)=='rqzg' and match('courage',b),
        hzya=lambda p,a,g,b,s:(p,a,s)==('person',act,'now') and symbol(g)=='rqzg' and match('attempt',b),
        df=lambda p,a,s:(p,a,s)==('person',act,'now'),dg=lambda a,s:(a,s)==(act,'now'))
    if variant=='wrong_goal':v['hzya']=lambda p,a,g,b,s:symbol(g)=='rqzk'
    if variant=='wrong_attempt_person':v['hzya']=lambda p,a,g,b,s:p=='other' and a==act
    if variant=='wrong_attempt_scene':v['hzya']=lambda p,a,g,b,s:s=='elsewhere' and a==act
    if variant=='different_attempt_act':v['hzya']=lambda p,a,g,b,s:a=='otheract'
    if variant=='goal_process_never_occurs':
        # dg is false for the process named by the goal, but true for the trial.
        # All other physical relations remain unknown.
        assert act!=BINDINGS[3]
    return v


def source_checks():
    d=source_fixture();rows={}
    variants=('baseline','goal_process_never_occurs','same_act_and_goal_process','short_bindings','extra_bindings',
        'swapped_body_foot','wrong_goal','wrong_attempt_person','wrong_attempt_scene','different_attempt_act',
        'courage_body','courage_carrier','courage_foot','courage_process',
        'attempt_body','attempt_carrier','attempt_foot','attempt_process')
    for name in variants:
        actual=evaluate(d,source_values(d,name),DOMAIN,SCENES)
        assert actual==[name in ('baseline','goal_process_never_occurs','same_act_and_goal_process')],(name,actual)
        rows[name]=actual
    v=source_values(d,'goal_process_never_occurs')
    assert v['dg']('attempt','now') and not v['dg']('process','now')
    return dict(contrasts=rows,goal_specific_physical_relations_unknown=True,
        attempt_act_and_goal_process_can_differ=True,goal_process_occurrence_not_required=True,
        source_adoption=False,ordinary_evaluation=True)


@lru_cache(None)
def norm_fixture():
    return fixture(['rqzl','rqzh'],'''
r jsource[] a.r jp[] a.r jrole[] a.r jcarrier[] a.r jm[a] c.r jb[a] j[a].r js[] d.
q[k rqzl[k jsource[] k jp[] k jrole[] k jcarrier[] p jm p jb k js[]]].
q[k rqzh[k jsource[] k jp[] k jrole[] k jcarrier[] p jm p jb k js[]]].
''')


def norm_values(d,allowed=(False,False),step_allowed=False,variant='baseline'):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    def bindings(item):
        row=['person','frame','foot','process' if item=='first' else 'otheract']
        if item=='second':
            if variant=='wrong_body':row[0]='other'
            if variant=='wrong_carrier':row[1]='other'
            if variant=='short':row.pop()
            if variant=='extra':row.append('other')
        return seq(row)
    def permits(source,person,role,desc,args,positive,scene):
        if (source,person,role,positive,scene)!=('source','person','role',True,
                'elsewhere' if variant=='wrong_norm_scene' else 'now'):return False
        if args.items not in (BINDINGS,('person','frame','foot','otheract')):return False
        if symbol(desc)=='rqzg':return step_allowed
        return symbol(desc)=='rqzk' and allowed[args.items[3]=='otheract']
    v.update(jsource=lambda:'source',jp=lambda:'person',jrole=lambda:'role',jcarrier=lambda:'frame',js=lambda:'now',
        jm=lambda item:item in ('first','second') and not(variant=='outside_family' and item=='second'),
        jb=bindings,h7l=permits)
    return v


def norm_checks():
    d=norm_fixture();domain=DOMAIN+('first','second','source','role');rows=[]
    for first,second,step in product((False,True),repeat=3):
        actual=evaluate(d,norm_values(d,(first,second),step),domain,SCENES)
        assert actual==[not(first or second),not step],(first,second,step,actual)
        rows.append(dict(attempts_allowed=[first,second],step_allowed=step,values=actual))
    contrasts={}
    for name in ('wrong_body','wrong_carrier','short','extra'):
        actual=evaluate(d,norm_values(d,variant=name),domain,SCENES)
        assert actual==[False,False],(name,actual);contrasts[name]=actual
    actual=evaluate(d,norm_values(d,(False,True),False,'outside_family'),domain,SCENES)
    assert actual==[True,True];contrasts['outside_family']=actual
    actual=evaluate(d,norm_values(d,(True,True),True,'wrong_norm_scene'),domain,SCENES)
    assert actual==[True,True];contrasts['wrong_norm_scene']=actual
    for name in ('jm','jb','h7l'):
        v=norm_values(d);v[name]=unknown
        try:evaluate(d,v,domain,SCENES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(combinations=rows,contrasts=contrasts,unknown_inputs_refused=3,
        courage_attempt_and_physical_contents_unknown=True,quoted_contents_not_executed=True,
        permission_to_step_distinct_from_permission_to_attempt=True,ordinary_evaluation=True)


def reading():
    previous=json.loads((ROOT/'data/grounded-step-reading-v1.json').read_text(encoding='utf-8'))
    context=json.loads((ROOT/'data/walking-warning-reading-v1.json').read_text(encoding='utf-8'))
    paths=(PARENT,PARENT_BASIS,INDEX,'data/grounded-step-reading-v1.json','data/walking-warning-reading-v1.json',
        'data/unpermitted-undertaking-reading-v1.json','data/grounded-step-evidence-v1.json')
    return dict(status='bound_goal_courageous_attempt_and_permission_composed_not_yet_source_adopted',
        reviewer='assistant_review',document=FULL,source=previous['source'],context=context['source'],source_adoption=False,
        findings=['閉じた目標記述と対象列を保持して、同じ本人の勇気と試みを結ぶ。',
            '身体・装置・足・目標の移動過程を、目標側と規範対象の双方で保持する。',
            '試みの行為と目標の移動過程を区別し、失敗した試みから移動の生起を補わない。',
            '一歩への許容と、その一歩を敢えて試みることへの許容を引用された内容の違いとして保持する。'],
        interpretation_limits=LIMITS,whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,
        next_required=['原文での候補全体の範囲','先行する阻止と同じ時点への結合','身体描写と知的活動の非字義的な対応',
            'ruhigenとja、一文全体の確認'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def structure():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-6]==old.document['declarations']
    assert old.document['statements']==new.document['statements'] and len(new.document['statements'])==47
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert set(new.entries)-set(old.entries)==set(MEANINGS)|set(PRIMITIVES)
    idx=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    active=load_catalog(ROOT,idx['works']['kant-1784']['meaning_basis'])
    assert selection_binding(active,list(range(47)))==selection_binding(new,list(range(47)))
    for p in idx['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/p).read_text(encoding='utf-8'));ids=[x['index'] for x in r['selection']['statements']]
        assert r['selection']==selection_binding(new,ids)
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('full','compact'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    r=reading();assert r==json.loads((ROOT/READING).read_text(encoding='utf-8'));validate_hashes(ROOT,r['source_sha256'])
    return dict(active_manuscript_unchanged=True,preserved_statements=47,new_definitions=4,new_primitives=2,
        preserved_review_selections=11,general_library_has_no_primitives=True,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('generic',generic_checks),('adapter',adapter_checks),('source',source_checks),('norms',norm_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{READING,DOC,
        'scripts/compose_bound_undertaking.py','scripts/check_bound_undertaking.py','scripts/register_bound_undertaking.py',
        'tests/test_bound_undertaking.py','scripts/compose_grounded_step.py','scripts/compose_falling_depiction.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','noema/constructed.py',
        'noema/constructed_semantics.py','noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='bound_courageous_attempt_and_quoted_permission_comparison',document=FULL,**results,
        alignment=dict(**r['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
