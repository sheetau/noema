"""Check existential role slots, their scope in attempts, and four permission shapes."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_quantified_step_goals import ROOT,FULL,CORE,LIBRARY,BASIS,PARENT,PARENT_BASIS,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_grounded_step import source_values as physical_values,DOMAIN as PHYSICAL_DOMAIN,TIMES

INDEX='data/semantic-review-index-v71.json'
REPORT='reports/quantified-step-goals-v1.json'
READING='data/quantified-step-goals-reading-v1.json'
DOC='docs/quantified-step-goals-v1.md'
DOMAIN=('body','frame','foot','otherfoot','process','otherprocess','trial','source','role','item')
SCENES=('now','elsewhere')
SHAPES=(('rqzn','rqzr',('body','frame')),('rqzo','rqzs',('body','frame','foot')),
    ('rqzp','rqzt',('body','frame','process')),('rqzg','rqzk',('body','frame','foot','process')))


def seq(values):return SequenceValue(tuple(values),'"individual"')


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+suffix)


@lru_cache(None)
def generic():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jfirst[] j[a].r jsecond[] j[a].r jscene[] d.r jrelation[a a d] c.
d jpair[left a right a] e[b scene[k jrelation[v left v right v scene]]].
q[t[k rqzm[k jfirst[] k jsecond[] p jpair]][k jscene[]]].
''')


def generic_checks():
    domain=('one','two');pairs=list(product(domain,repeat=2));rows=[];d=generic()
    def values(first,second,truths):
        return dict(jfirst=lambda:seq(first),jsecond=lambda:seq(second),jscene=lambda:'now',
            jrelation=lambda a,b,s:s=='now' and (a,b) in truths)
    for bits in product((False,True),repeat=4):
        truths={p for p,b in zip(pairs,bits) if b}
        for first,second in product(((),('one',)),repeat=2):
            actual=evaluate(d,values(first,second,truths),domain,SCENES)
            expected=any((not first or a==first[0]) and (not second or b==second[0]) for a,b in truths)
            assert actual==[expected],(bits,first,second,actual)
            rows.append(dict(bits=bits,first=first,second=second,value=actual[0]))
    contrasts={}
    cases={'other_fixed':(('two',),('two',),{('two','two')},True),
        'separate_witnesses':(('one',),('one',),{('one','two'),('two','one')},False),
        'two_first':(('one','two'),(),set(pairs),False),'duplicate_first':(('one','one'),(),set(pairs),False),
        'two_second':((),('one','two'),set(pairs),False)}
    for name,(first,second,truths,expected) in cases.items():
        actual=evaluate(d,values(first,second,truths),domain,SCENES)
        assert actual==[expected];contrasts[name]=actual
    for name in ('jfirst','jsecond','jrelation'):
        v=values((),(),set(pairs));v[name]=unknown
        try:evaluate(d,v,domain,SCENES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(combinations=rows,contrasts=contrasts,unknown_inputs_refused=3,
        shared_pair_required=True,no_unknown_object_placeholder=True,ordinary_evaluation=True)


@lru_cache(None)
def physical_fixture():
    suffix='r jbody[] a.r jcarrier[] a.r jfoot[] a.r jact[] a.r jend[] d.'
    for goal,args in [('rqzn',('jbody','jcarrier')),('rqzo',('jbody','jcarrier','jfoot')),
            ('rqzp',('jbody','jcarrier','jact')),('rqzg',('jbody','jcarrier','jfoot','jact'))]:
        suffix+='q[t[k '+goal+'[l[a]['+' '.join('k '+a+'[]' for a in args)+']]][k jend[]]].'
    return fixture(['rqzn','rqzo','rqzp','rqzg'],suffix)


def physical_checks():
    d=physical_fixture();rows={}
    for name in ('baseline','other_named_foot','other_named_process','other_carrier','no_initial_contact',
            'same_position','flight_middle','boundary_only'):
        variant='baseline' if name in ('other_named_foot','other_named_process','other_carrier') else name
        v=physical_values(d,variant)
        if name=='other_named_foot':v['jfoot']=lambda:'otherfoot'
        if name=='other_named_process':v['jact']=lambda:'origin'
        if name=='other_carrier':v['jcarrier']=lambda:'origin'
        actual=evaluate(d,v,PHYSICAL_DOMAIN,TIMES,True)
        expected=[True]*4 if name=='baseline' else [True,False,True,False] if name=='other_named_foot' else [True,True,False,False] if name=='other_named_process' else [False]*4
        assert actual==expected,(name,actual,expected);rows[name]=actual
    return dict(contrasts=rows,actual_contact_and_movement_definitions_evaluated=True,
        named_role_not_replaced_by_another_witness=True,pure_memoization=True)


@lru_cache(None)
def undertaking_fixture():
    suffix='r js[] d.'+''.join('r jb'+chr(97+i)+'[] j[a].' for i in range(4))
    for i,(goal,attempt,args) in enumerate(SHAPES):
        suffix+='q[t[k '+attempt+'[k jb'+chr(97+i)+'[]]][k js[]]].'
    # The new arity adapter also reproduces the existing fully bound wrapper.
    suffix+='q[t[k rqzq[r[p rqzg] n p e b k jbd[]]][k js[]]].'
    return fixture(['rqzr','rqzs','rqzt','rqzk','rqzq'],suffix)


def undertaking_values(d,flags=(True,True,True,True),selected=None,variant='baseline'):
    courage,attempt,actor,occurs=flags
    targets={goal:args for goal,_,args in SHAPES if selected is None or goal==selected}
    def matching(goal,args):return symbol(goal) in targets and args.items==targets[symbol(goal)]
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update(js=lambda:'now',**{'jb'+chr(97+i):(lambda args=args:seq(args)) for i,(_,_,args) in enumerate(SHAPES)})
    v.update(hzxz=lambda p,g,b,s:courage and (p,s)==('body','now') and matching(g,b),
        hzya=lambda p,a,g,b,s:attempt and (p,a,s)==('body','trial','now') and matching(g,b),
        df=lambda p,a,s:actor and (p,a,s)==('body','trial','now'),dg=lambda a,s:occurs and (a,s)==('trial','now'))
    if variant=='extra':v['jba']=lambda:seq(('body','frame','foot'))
    if variant=='short':v['jbb']=lambda:seq(('body','frame'))
    if variant=='swapped_optional_role':v['jbc']=lambda:seq(('body','frame','foot'))
    if variant=='swapped_body_carrier':v['jba']=lambda:seq(('frame','body'))
    return v


def undertaking_checks():
    d=undertaking_fixture();rows=[]
    for bits in product((False,True),repeat=4):
        actual=evaluate(d,undertaking_values(d,bits),DOMAIN,SCENES)
        assert actual==[all(bits)]*5,(bits,actual)
        rows.append(dict(bits=bits,values=actual))
    contrasts={}
    for i,(goal,_,_) in enumerate(SHAPES):
        actual=evaluate(d,undertaking_values(d,selected=goal),DOMAIN,SCENES)
        expected=[j==i for j in range(4)]+[i==3]
        assert actual==expected,(goal,actual);contrasts[goal+'_only']=actual
    for name,expected in [('extra',[False,True,True,True,True]),('short',[True,False,True,True,True]),
            ('swapped_optional_role',[True,True,False,True,True]),('swapped_body_carrier',[False,True,True,True,True])]:
        actual=evaluate(d,undertaking_values(d,variant=name),DOMAIN,SCENES)
        assert actual==expected,(name,actual);contrasts[name]=actual
    return dict(combinations=rows,contrasts=contrasts,goal_specific_physical_relations_unknown=True,
        existential_witnesses_not_sought_when_quoting_goal=True,
        existential_goal_attempt_not_a_specific_goal_attempt=True,existing_bound_wrapper_agrees=True,
        ordinary_evaluation=True)


@lru_cache(None)
def norm_fixture():
    return fixture(['rqzu','rqzl'],'''
r js[] a.r jp[] a.r jr[] a.r jc[] a.r jnow[] d.r jfeet[a] c.r jprocesses[a] c.
r jmembers[a] c.r jbindings[a] j[a].
q[k rqzu[k js[] k jp[] k jr[] k jc[] p jfeet p jprocesses k jnow[]]].
q[k rqzl[k js[] k jp[] k jr[] k jc[] p jmembers p jbindings k jnow[]]].
''')


def norm_values(d,flags=(False,False,False,False),variant='baseline'):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    targets={attempt:args for _,attempt,args in SHAPES}
    allowed={attempt:flag for (_,attempt,_),flag in zip(SHAPES,flags)}
    def permits(source,person,role,desc,args,positive,scene):
        name=symbol(desc)
        if name not in targets:return False
        return allowed[name] and (source,person,role,positive,scene)==('source','body','role',True,
            'elsewhere' if variant=='other_scene' else 'now') and args.items==targets[name]
    v.update(js=lambda:'source',jp=lambda:'body',jr=lambda:'role',jc=lambda:'frame',jnow=lambda:'now',
        jfeet=lambda part:part in ('foot','otherfoot') and not(variant in ('omit_foot','empty') and part=='foot') and variant!='empty',
        jprocesses=lambda process:process in ('process','otherprocess') and not(variant in ('omit_process','empty') and process=='process') and variant!='empty',
        jmembers=lambda item:item=='item',jbindings=lambda item:seq(('body','frame','foot','process')),h7l=permits)
    return v


def norm_checks():
    d=norm_fixture();rows=[]
    for flags in product((False,True),repeat=4):
        actual=evaluate(d,norm_values(d,flags),DOMAIN,SCENES)
        assert actual==[not any(flags),not flags[3]],(flags,actual)
        rows.append(dict(unspecified_foot_process_specific_permissions=flags,values=actual))
    contrasts={}
    for name,flags,expected in [('omit_foot',(False,True,False,False),[True,True]),
            ('omit_process',(False,False,True,False),[True,True]),
            ('empty',(True,False,False,False),[False,True]),('other_scene',(True,True,True,True),[True,True])]:
        actual=evaluate(d,norm_values(d,flags,name),DOMAIN,SCENES)
        assert actual==expected,(name,actual);contrasts[name]=actual
    for name in ('jfeet','jprocesses','h7l'):
        v=norm_values(d);v[name]=unknown
        try:evaluate(d,v,DOMAIN,SCENES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    counter=next(r for r in rows if r['unspecified_foot_process_specific_permissions']==(True,False,False,False))
    assert counter['values']==[False,True]
    return dict(combinations=rows,contrasts=contrasts,unknown_inputs_refused=3,countermodel=counter,
        courage_attempt_and_physical_relations_unknown=True,all_four_specification_shapes_checked=True,
        selected_object_ranges_still_require_source_justification=True,ordinary_evaluation=True)


def reading():
    previous=json.loads((ROOT/'data/bound-undertaking-reading-v1.json').read_text(encoding='utf-8'))
    paths=(PARENT,PARENT_BASIS,INDEX,'data/bound-undertaking-reading-v1.json',
        'data/walking-warning-reading-v1.json','data/grounded-step-evidence-v1.json')
    return dict(status='existential_goal_shapes_and_permission_scope_comparison_not_source_adopted',
        reviewer='assistant_review',document=FULL,source=previous['source'],context=previous['context'],source_adoption=False,
        findings=['足と過程の指定・未指定を四形に分け、未指定は目標内部の存在量化とする。',
            '成功の存在証拠を、引用された試みや許容に必要な証拠へ取り違えない。',
            '具体的な目標だけへの無許容では、未指定の一歩への取り組みの許容を落とす反例がある。',
            '四形の許容欠如を同じ身体・装置・出所・役割・状況に結び、具体的な足と過程は明示的な選択範囲で全称化する。'],
        interpretation_limits=LIMITS,whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,
        next_required=['原文の全該当対象を尽くす足と過程の範囲','先行する阻止と同じ時点への結合',
            '身体描写と知的活動の非字義的な対応','ruhigenとja、一文全体の確認'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def structure():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-9]==old.document['declarations']
    assert old.document['statements']==new.document['statements'] and len(new.document['statements'])==47
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert set(new.entries)-set(old.entries)==set(MEANINGS)
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
    return dict(active_manuscript_unchanged=True,preserved_statements=47,new_definitions=9,new_primitives=0,
        preserved_review_selections=11,general_library_has_no_primitives=True,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('generic',generic_checks),('physical',physical_checks),('undertaking',undertaking_checks),('norms',norm_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{READING,DOC,
        'scripts/compose_quantified_step_goals.py','scripts/check_quantified_step_goals.py','scripts/register_quantified_step_goals.py',
        'tests/test_quantified_step_goals.py','scripts/compose_grounded_step.py','scripts/compose_falling_depiction.py',
        'scripts/check_grounded_step.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'noema/constructed.py','noema/constructed_semantics.py','noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='existential_goal_slots_and_four_permission_shapes_comparison',document=FULL,**results,
        alignment=dict(**r['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
