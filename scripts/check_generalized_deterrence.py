"""Check distinct case normality and avoidance frequency in the adopted clause."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_generalized_deterrence import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_example_deterrence import DOMAIN,SCENES
from scripts.check_caused_deterrence import source_model
from scripts import check_reasoned_concession as discourse

INDEX='data/semantic-review-index-v83.json'
REPORT='reports/generalized-deterrence-v1.json'
AUDIT='data/generalized-deterrence-reading-v1.json'
DOC='docs/generalized-deterrence-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
POINTS=('first','second','third')
TIMES=SCENES+('regular','perturbation')


@lru_cache(None)
def catalog(): return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(roots,suffix):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots.split()),statements=[])
    return parse(format_graph(d,'compact')+suffix)


@lru_cache(None)
def generic_checks():
    d=fixture('r2bf r2bg','''r zcases[a] c.r zpreferred[a a] c.r zresponse[a] c.
q[k r2bf[p zcases p zpreferred]].q[k r2bg[p zcases p zpreferred p zresponse]].''')
    def model(relation,truth=POINTS,cases=POINTS):
        return dict(zcases=lambda x:x in cases,zpreferred=lambda a,b:(a,b) in relation,zresponse=lambda x:x in truth)
    orders=[]
    for bits in product((False,True),repeat=9):
        relation={p for p,b in zip(product(POINTS,repeat=2),bits) if b}
        composed={(a,c) for a,b in relation for middle,c in relation if b==middle}
        valid=not any(a==b for a,b in relation) and composed<=relation
        assert evaluate(d,model(relation),POINTS,('now',),True)==[valid,valid]
        if valid: orders.append(relation)
    for relation in orders:
        minimal=set(POINTS)-{b for a,b in relation}
        for bits in product((False,True),repeat=3):
            truth={p for p,b in zip(POINTS,bits) if b}
            assert evaluate(d,model(relation,truth),POINTS,('now',),True)==[True,minimal<=truth]
    assert len(orders)==19
    assert evaluate(d,model(set(),cases=()),POINTS,('now',),True)==[True,False]
    assert evaluate(d,model({('third','first')},{'first'},('first',)),POINTS,('now',),True)==[True,True]
    for name in ('zcases','zpreferred','zresponse'):
        v=model(set());v[name]=unknown
        try:evaluate(d,v,POINTS,('now',),True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(relations=512,strict_orders=19,response_combinations=152,unknown_inputs_refused=3,
        independent_relation_composition_oracle=True,empty_refused=True,outside_cases_do_not_dominate=True)


@lru_cache(None)
def source_document():
    return fixture('hzud r2bi r2bj r2bk','''r zanchor[] d.
q[t[k hzud[]][k zanchor[]]].q[t[k r2bj[]][k zanchor[]]].
q[t[k r2bi[]][k zanchor[]]].q[t[k r2bk[]][k zanchor[]]].''')


def model(observed=True,fear=True,avoid=True,variant='baseline'):
    d=source_document();base=source_model(d,variant)
    def adapt(name,callback):
        def call(*args):
            world=next((a for a in args if isinstance(a,str) and a in ('regular','perturbation')),None)
            mapped=tuple('actual' if a in ('regular','perturbation') else a for a in args)
            value=callback(*mapped)
            if name=='md' and value:
                if not world and not observed and args[0]=='other':return False
                if world=='perturbation' and variant=='bad_perturbation' and args[0]=='other':return False
            if name=='hzie' and world:
                if symbol(args[3])=='hzua' and not fear or symbol(args[3])=='gt' and not avoid:return False
            if name=='mc' and world and variant in ('atypical_fear_exception','unranked_fear_exception') and args[0]=='third':return False
            if name=='u3':
                if variant=='outside_anchor_group' and not world and args[-1]=='actual':return False
                if variant=='different_varied_group' and world:return False
            return value
        return call
    v={n:adapt(n,f) for n,f in base.items()}
    def case_order(anchor,scene,a,b):
        if (anchor,scene) not in (('actual','regular'),('actual','perturbation')):return False
        if variant=='atypical_fear_exception':return a in ('casea','caseb') and b=='casec'
        if variant=='case_cycle':return (a,b) in (('casea','caseb'),('caseb','casea'))
        return False
    v.update(zanchor=lambda:'actual',
        hzyl=lambda a,s:variant!='empty_comparison' and a==('belief' if variant=='wrong_anchor' else 'actual') and s in ('regular','perturbation'),
        hzym=lambda a,s,t:variant=='world_cycle' and a=='actual' and (s,t) in (('regular','perturbation'),('perturbation','regular')),
        hzyn=case_order)
    return v


@lru_cache(None)
def source_checks():
    d=source_document();rows=[]
    for observed,fear,avoid in product((False,True),repeat=3):
        actual=evaluate(d,model(observed,fear,avoid),DOMAIN,TIMES,True)
        assert actual==[observed,fear,avoid,fear and avoid],(observed,fear,avoid,actual)
        rows.append(dict(observed=observed,generic_cause=fear,frequency_cause=avoid,values=actual))
    wanted={
        'baseline':[True,True,True,True],
        'atypical_fear_exception':[True,True,True,True],
        'unranked_fear_exception':[True,False,True,False],
        'case_cycle':[True,False,True,False],
        'world_cycle':[True,False,False,False],
        'empty_comparison':[True,False,False,False],
        'wrong_anchor':[True,False,False,False],
        'outside_anchor_group':[False,False,False,False],
        'different_varied_group':[True,True,True,True],
        'bad_perturbation':[True,True,False,False],
        'omit_exception':[False,True,False,False],
        'duplicate_cases':[False,True,False,False],
        'strict_criterion':[False,True,False,False],
        'wrong_task':[False,False,False,False],
        'wrong_recognized_example':[False,False,False,False],
        'one_attempt_not_avoided':[False,True,False,False],
        'different_causal_target':[False,False,False,False],
    }
    contrasts={}
    for name,expected in wanted.items():
        actual=evaluate(d,model(variant=name),DOMAIN,TIMES,True)
        assert actual==expected,(name,actual,expected);contrasts[name]=actual
        print(name+' checked',flush=True)
    for name in ('hzyl','hzym','hzyn','u3','hzie','gg','gl'):
        v=model();v[name]=unknown
        try:evaluate(d,v,DOMAIN,TIMES,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(independent_conditions=rows,contrasts=contrasts,unknown_inputs_refused=7,
        columns=['previous_observed_claim','generic_intimidation','avoidance_frequency','new_joint_claim'],
        existing_recognition_failure_courage_fear_reason_and_cause_executed=True,
        fixed_anchor_audience=True,atypical_fear_cases_remain_in_frequency_population=True,pure_memoization=True)


@lru_cache(None)
def attribution_checks():
    d=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    def values(bits=(True,True,True),variant='baseline'):
        v=discourse.source_model(d)
        def claim(node,a,c,s):
            expected={'low':'e4','learn':'fs','outcome':'hzud' if variant=='old_claim' else 'r2bk'}
            return (a,s)==('author','anchor') and node in expected and (node!='outcome' or bits[0]) and json.loads(c.syntax)==dict(kind='call',symbol=expected[node],arguments=[])
        def report(node,a,c,scope,s):
            return bits[1] and (node,a,scope,s)==('outcome','author','outcome','anchor') and discourse.unwrap(c)==dict(kind='call',symbol='hzud' if variant=='old_foreground' else 'r2bk',arguments=[])
        def background(node,a,f,b,fs,bs,s):
            return bits[2] and (node,a,fs,bs,s)==('outcome','author','outcome','contrast','anchor') and [discourse.unwrap(f),discourse.unwrap(b)]==[
                dict(kind='call',symbol='r2bk',arguments=[]),dict(kind='call',symbol='hzuf' if variant=='old_background' else 'r2bm',arguments=[])]
        v.update(uc=claim,hznreport=report,hzrbgreport=background)
        if variant=='wrong_author':v['wa']=lambda:'other'
        if variant=='wrong_scope':v['hztz']=lambda:'other'
        if variant=='missing_reason':v['ud']=lambda *args:False
        return v
    for bits in product((False,True),repeat=3):
        assert evaluate(d,values(bits),discourse.DOMAIN,discourse.SCENES)==[all(bits)]
    for name in ('baseline','old_claim','old_foreground','old_background','wrong_author','wrong_scope','missing_reason'):
        actual=evaluate(d,values(variant=name),discourse.DOMAIN,discourse.SCENES)
        assert actual==[name=='baseline'],(name,actual);rows[name]=actual
    for name in ('uc','ud','ue','hznreport','hzrbgreport'):
        v=values();v[name]=unknown
        try:evaluate(d,v,discourse.DOMAIN,discourse.SCENES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    bg=fixture('r2bm','r za[] d.q[t[k r2bm[]][k za[]]].')
    v={x['name']:unknown for x in bg['declarations'] if x['kind']=='primitive'}
    v.update(za=lambda:'anchor',wa=lambda:'author',hzpt=discourse.ranker(premise='e4',outcome='r2bk',observer='author'))
    assert evaluate(bg,v,discourse.DOMAIN,discourse.SCENES)==[True]
    return dict(combinations=8,contrasts=rows,unknown_inputs_refused=5,world_contents_unknown=True,
        background_uses_new_outcome_on_both_sides=True,ordinary_evaluation=True)


def reading():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    start=unit['text'].index('ein Beispiel');text=unit['text'][start:]
    paths=(INDEX,INVENTORY,PARENT,PARENT_BASIS,FULL,BASIS,'reports/frequency-under-variation-v1.json',
        'data/frequency-under-variation-reading-v1.json','artifacts/first-cause-reading-v1/page-482.jpg')
    return dict(status='generic_intimidation_and_robust_frequency_adopted',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,len(unit['text'])],text=text),
        decision='一般的な因果的萎縮と、例外を残す回避の頻度を別の範囲で記述し、同じ基準の対象集団と比較背景を保つ読みを本文へ採用する。',
        selection=selection_binding(catalog(),[37]),interpretation_limits=LIMITS,
        references=['https://korpora.org/Kant/aa08/036.html','https://tzin.bgu.ac.il/~arikc/gen.pdf'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def structure():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-15]==old.document['declarations']
    assert all(new.entries[n]==e for n,e in old.entries.items())
    changed=[i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'],strict=True)) if a!=b]
    assert changed==[37] and len(new.document['statements'])==52
    assert set(new.entries)-set(old.entries)==set(MEANINGS)|set(PRIMITIVES)
    borrowed=load_catalog(ROOT,'data/frequency-under-variation-basis-v1.json').entries['r2bd']
    assert borrowed['declaration']==new.entries['r2bd']['declaration'] and borrowed['meaning_ja']==new.entries['r2bd']['meaning_ja']
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for p in index['works']['kant-1784']['reviews']:
        row=json.loads((ROOT/p).read_text(encoding='utf-8'));ids=[s['index'] for s in row['selection']['statements']]
        assert 37 not in ids and row['selection']==selection_binding(old,ids)==selection_binding(new,ids)
    preceding=json.loads((ROOT/'reports/guarded-walking-reading-v1.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT,preceding['source_sha256'])
    bindings=[r['current_selection'] for r in preceding['preceding']['reviews'].values()]
    bindings.append(json.loads((ROOT/'data/guarded-walking-reading-v1.json').read_text(encoding='utf-8'))['selection'])
    for binding in bindings:assert binding==selection_binding(new,[s['index'] for s in binding['statements']])
    for p,body in build().items():assert (ROOT/p).read_text(encoding='utf-8')==body,p
    for p in (FULL,CORE,LIBRARY):
        d=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    r=reading();assert r==json.loads((ROOT/AUDIT).read_text(encoding='utf-8'));validate_hashes(ROOT,r['source_sha256'])
    return dict(new_definitions=12,new_primitives=3,changed_statement_indices=changed,preserved_statements=51,total_statements=52,
        preserved_review_selections=11,preserved_reviewed_sentence_characters=1021,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('generic',generic_checks),('source',source_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_generalized_deterrence.py','scripts/check_generalized_deterrence.py','scripts/register_generalized_deterrence.py',
        'tests/test_generalized_deterrence.py','scripts/compose_frequency_variation.py','scripts/compose_courageous_undertaking.py',
        'scripts/check_caused_deterrence.py','scripts/check_example_deterrence.py','scripts/check_reasoned_concession.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py'}
    return dict(status='generic_reaction_and_frequency_connected_to_author_and_expectation',document=FULL,**results,
        alignment=dict(**r['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
