"""Separate actual causal contribution from explanatory adoption in the source."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.finite_semantics import SequenceValue as LegacySequence
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_caused_deterrence import ROOT,PARENT,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,LIMITS,parent,build,closure
from scripts import check_example_deterrence as old_fixture
from scripts import check_reasoned_concession as discourse

REPORT='reports/caused-deterrence-v1.json'
READING='data/caused-deterrence-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'


def unknown(*args):raise ValueError('Unknown deterrence input')


def symbol(code):
    body=json.loads(code.syntax)
    assert body['kind']=='function_ref'
    return body['symbol']


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    doc=deepcopy(catalog().document);doc['declarations']=closure(doc,roots);doc['statements']=[]
    return parse(format_graph(doc,'compact')+suffix)


def evaluate(doc,model,domain=('factor','result','other'),scenes=('now','later'),memoize=False):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=scenes,
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=100000000,memoize_definitions=memoize,memoize_expressions=memoize)]


def generic_checks():
    doc=fixture(['rqqu','ec'],'''
r za[] a.r zb[] a.r zscene[] d.r zfactor[a d] c.r zresult[a d] c.
d zp[person a] e[b scene[k zfactor[v person v scene]]].
d zq[person a] e[b scene[k zresult[v person v scene]]].
q[k rqqu[k za[] r[p zp] k zb[] r[p zq] k zscene[]]].
q[k ec[k za[] r[p zp] k zb[] r[p zq] k zscene[]]].
''')
    def model(bits=(True,True,True,True),variant='baseline'):
        factor,result,cause,adopted=bits
        def causal(a,f,b,r,s):
            expected=('result','zq','factor','zp','now') if variant=='reversed_causality' else (
                'other' if variant=='other_factor_subject' else 'factor','zq' if variant=='other_factor' else 'zp',
                'other' if variant=='other_result_subject' else 'result','zp' if variant=='other_result' else 'zq',
                'later' if variant=='other_scene' else 'now')
            return cause and (a,symbol(f),b,symbol(r),s)==expected
        return dict(za=lambda:'factor',zb=lambda:'result',zscene=lambda:'now',
            zfactor=lambda p,s:factor and (p,s)==('factor','now'),zresult=lambda p,s:result and (p,s)==('result','now'),
            hzie=causal,ea=lambda *args:adopted)
    rows=[]
    for bits in product((False,True),repeat=4):
        result=evaluate(doc,model(bits));assert result==[all(bits[:3]),bits[0] and bits[1] and bits[3]],(bits,result)
        rows.append(dict(factor=bits[0],result=bits[1],cause=bits[2],adopted=bits[3],values=result))
    contrasts={}
    for variant in ('baseline','other_factor_subject','other_result_subject','other_factor','other_result','other_scene','reversed_causality'):
        result=evaluate(doc,model(variant=variant));assert result==[variant=='baseline',True],(variant,result);contrasts[variant]=result
    for name in ('zfactor','zresult','hzie'):
        m=model();m[name]=unknown
        try:evaluate(doc,m)
        except ValueError as e:assert 'Unknown deterrence' in str(e)
        else:raise AssertionError(name)
    return dict(combinations=rows,contrasts=contrasts,unknown_inputs_refused=3,uncached_native_definitions=True)


def courage_checks():
    doc=fixture(['hzua'],'r za[] a.r zb[] d.q[t[k hzua[k za[]]][k zb[]]].')
    domain=('person','other','case','act','unrelated');scenes=('now','later');rows={}
    for variant in ('baseline','same_goal_courage','other_goal_courage','other_person_courage','other_scene_courage',
        'no_fear','empty_future_scope','wrong_future_task','not_future'):
        m={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        def courage(p,g,s):return variant in ('same_goal_courage','other_goal_courage','other_person_courage','other_scene_courage') and (p,symbol(g),s)==(
            'other' if variant=='other_person_courage' else 'person','bm' if variant=='other_goal_courage' else 'bb',
            'later' if variant=='other_scene_courage' else 'now')
        m.update(za=lambda:'case',zb=lambda:'now',gd=lambda c:'person',hzio=courage,
            ma=lambda p,a,s:variant!='empty_future_scope' and (p,a,s)==('person','act','now'),
            dd=lambda a,b:(a,b)==('now','later'),go=lambda a:'now' if variant=='not_future' else 'later',
            gp=lambda a,g,s:(a,symbol(g),s)==('act','bm' if variant=='wrong_future_task' else 'bb','now'),
            mc=lambda p,a,s:variant!='no_fear' and (p,a,s)==('person','act','now'))
        result=evaluate(doc,m,domain,scenes)
        expected=variant in ('baseline','other_goal_courage','other_person_courage','other_scene_courage')
        assert result==[expected],(variant,result);rows[variant]=result
    m['hzio']=unknown
    try:evaluate(doc,m,domain,scenes)
    except ValueError as e:assert 'Unknown deterrence' in str(e)
    else:raise AssertionError('Unknown courage was replaced by its absence')
    return dict(cases=rows,goal_content_unknown=True,unknown_courage_refused=True,uncached=True)


def adapt(callback):
    def current(*args):
        result=callback(*args)
        return SequenceValue(result.items,result.element_type) if isinstance(result,LegacySequence) else result
    return current


def source_model(doc,variant='baseline',causes=(True,True),adopted=True):
    m={name:adapt(callback) for name,callback in old_fixture.source_model(doc,variant).items()}
    m.update(hzio=lambda p,g,s:variant=='courage_present' and p=='person' and symbol(g)=='bb',
        hzie=lambda a,f,b,r,s:(a in old_fixture.CASES and b==('casec' if variant=='different_causal_target' else a) and
            symbol(f)==('gs' if variant=='different_causal_factor' else 'gr') and
            symbol(r) in ('hzua','gt') and s==('belief' if variant=='different_causal_scene' else 'actual') and
            (causes[0] if symbol(r)=='hzua' else causes[1])))
    if not adopted:m['ea']=lambda *args:False
    return m


@lru_cache(None)
def reaction_document():
    return fixture(['hzub','hzuc','gu','gv','rqqu'],'r za[] a.r zb[] d.'+
        'q[t[k hzub[k za[]]][k zb[]]].q[t[k hzuc[k za[]]][k zb[]]].'+
        'q[k rqqu[k za[] r[p gr] k za[] r[p hzua] k zb[]]].q[k rqqu[k za[] r[p gr] k za[] r[p gt] k zb[]]].'+
        'q[t[k gu[k za[]]][k zb[]]].q[t[k gv[k za[]]][k zb[]]].')


def reaction_checks():
    doc=reaction_document();rows=[]
    for fear_cause,avoid_cause,adopted in product((False,True),repeat=3):
        m=source_model(doc,causes=(fear_cause,avoid_cause),adopted=adopted)
        actual=evaluate(doc,m,old_fixture.DOMAIN,old_fixture.SCENES,True)
        expected=[fear_cause,avoid_cause,fear_cause,avoid_cause,adopted,adopted]
        assert actual==expected,(fear_cause,avoid_cause,adopted,actual);rows.append(dict(causes=[fear_cause,avoid_cause],adopted=adopted,values=actual))
    contrasts={}
    for variant in ('unknown_example_result','wrong_task','wrong_recognized_example','empty_attempts','courage_present','mere_nonexecution',
        'one_attempt_not_avoided','wrong_avoidance_reason','different_causal_target','different_causal_factor','different_causal_scene'):
        actual=evaluate(doc,source_model(doc,variant),old_fixture.DOMAIN,old_fixture.SCENES,True)
        fear=variant not in ('unknown_example_result','wrong_task','wrong_recognized_example','empty_attempts','courage_present',
            'different_causal_target','different_causal_factor','different_causal_scene')
        avoidance=variant not in ('unknown_example_result','wrong_task','wrong_recognized_example','empty_attempts','mere_nonexecution',
            'one_attempt_not_avoided','wrong_avoidance_reason','different_causal_target','different_causal_factor','different_causal_scene')
        assert actual[:4]==[fear,avoidance,fear,avoidance],(variant,actual);contrasts[variant]=actual
    selected=dict(doc,statements=doc['statements'][:2]);m=source_model(doc);m['hzie']=unknown
    try:evaluate(selected,m,old_fixture.DOMAIN,old_fixture.SCENES,True)
    except ValueError as e:assert 'Unknown deterrence' in str(e)
    else:raise AssertionError('Unknown cause accepted')
    return dict(independent_cause_and_adoption_cases=rows,contrasts=contrasts,specializations_equal_generic_factive_cause=True,
        current_runtime_with_pure_memoization=True,legacy_fixture_sequences_adapted=True,unknown_cause_refused=True)


def aggregate_checks():
    doc=fixture(['hzud','gx'],'r zb[] d.q[t[k hzud[]][k zb[]]].q[t[k gx[]][k zb[]]].');rows={}
    for variant in ('baseline','reordered_cases','omit_exception','duplicate_cases','empty_cases','strict_criterion',
        'ineligible_case','outside_current_group','nonhuman_observer','no_fear_for_exception','one_attempt_not_avoided',
        'actual_cause_not_adopted','adopted_without_actual_cause'):
        m=source_model(doc,variant,causes=(variant!='adopted_without_actual_cause',)*2,adopted=variant!='actual_cause_not_adopted')
        actual=evaluate(doc,m,old_fixture.DOMAIN,old_fixture.SCENES,True)
        expected=[variant in ('baseline','reordered_cases','actual_cause_not_adopted'),variant in ('baseline','reordered_cases','adopted_without_actual_cause')]
        assert actual==expected,(variant,actual,expected);rows[variant]=actual
    return dict(cases=rows,exception_retained_in_complete_scope=True,current_runtime_with_pure_memoization=True)


def attribution_checks():
    doc=fixture(['hzuh'],'q[k hzuh[]].');rows={}
    def model(bits=(True,True,True),variant='baseline'):
        m=discourse.source_model(doc)
        def claim(node,a,c,s):
            expected={'low':'e4','learn':'fs','outcome':'gx' if variant=='old_causal_claim' else 'hzud'}
            return (a,s)==('author','anchor') and node in expected and (node!='outcome' or bits[0]) and json.loads(c.syntax)==dict(kind='call',symbol=expected[node],arguments=[])
        def report(node,a,c,scope,s):
            return bits[1] and (node,a,scope,s)==('outcome','author','outcome','anchor') and discourse.unwrap(c)==dict(kind='call',symbol='gx' if variant=='old_foreground' else 'hzud',arguments=[])
        def background(node,a,f,b,fs,bs,s):
            return bits[2] and (node,a,fs,bs,s)==('outcome','author','outcome','contrast','anchor') and [discourse.unwrap(f),discourse.unwrap(b)]==[
                dict(kind='call',symbol='hzud',arguments=[]),dict(kind='call',symbol='hztv' if variant=='old_background' else 'hzuf',arguments=[])]
        m.update(uc=claim,hznreport=report,hzrbgreport=background)
        if variant=='wrong_author':m['wa']=lambda:'other'
        if variant=='wrong_scope':m['hztz']=lambda:'other'
        if variant=='missing_reason':m['ud']=lambda *args:False
        return m
    for bits in product((False,True),repeat=3):
        actual=evaluate(doc,model(bits),discourse.DOMAIN,discourse.SCENES)
        assert actual==[all(bits)],(bits,actual)
    for variant in ('baseline','old_causal_claim','old_foreground','old_background','wrong_author','wrong_scope','missing_reason'):
        actual=evaluate(doc,model(variant=variant),discourse.DOMAIN,discourse.SCENES);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    bgdoc=fixture(['hzuf'],'r za[] d.q[t[k hzuf[]][k za[]]].')
    bm={d['name']:unknown for d in bgdoc['declarations'] if d['kind']=='primitive'}
    bm.update(wa=lambda:'author',za=lambda:'anchor',hzpt=discourse.ranker(premise='e4',outcome='hzud',observer='author'))
    assert evaluate(bgdoc,bm,discourse.DOMAIN,discourse.SCENES)==[True]
    return dict(attribution_combinations=8,contrasts=rows,world_cause_and_courage_unknown=True,
        background_uses_revised_outcome_on_both_sides=True,uncached=True)


def structure():
    old=parent();new=catalog();assert new.document['declarations'][:-8]==old.document['declarations']
    assert all(new.entries[n]==entry for n,entry in old.entries.items())
    assert len(new.document['statements'])==len(old.document['statements'])==38
    changed=[i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'],strict=True)) if a!=b];assert changed==[37]
    reaction={d['name'] for d in closure(new.document,['hzub','hzuc'])}
    assert {'hzie','hzio','gr','gt','hzua','me'}<=reaction and not reaction&{'ea','al','gs','gu','gv','rqqu'}
    idx=json.loads((ROOT/'data/semantic-review-index-v31.json').read_text(encoding='utf-8'))
    for path in idx['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[s['index'] for s in review['selection']['statements']]
        assert selection_binding(old,indices)==review['selection']==selection_binding(new,indices)
    for path in (FULL,CORE):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    return dict(new_definitions=8,new_primitives=0,changed_statement_indices=changed,other_statements_preserved=37,
        nine_review_bindings_preserved=True,source_reaction_uses_factual_cause_and_described_courage=True,roundtrips=True)


def source_record():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    start=unit['text'].index('allein ein Beispiel');end=len(unit['text'])
    return dict(status='explicit_actual_causal_contribution_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],text=unit['text'][start:end]),
        references=['https://korpora.org/Kant/aa08/036.html'],decision='例による萎縮と回避を、認識された例が反応へ実際に因果的に寄与する内容として著者へ帰属させる。',
        reasoning='原文は一例が萎縮させ、通常は後続の試みを思いとどまらせると述べる。誰かがそれを原因説明に採用したことだけではこの主張を保持しない。既存hzieの因果寄与と、要因・結果の成立を併用する読みを選ぶ。',
        limits=LIMITS,whole_unit_semantically_verified=False,binding=selection_binding(catalog(),[37]),
        source_sha256={INVENTORY:digest((ROOT/INVENTORY).read_bytes())})


def build_report():
    for p,text in build().items():assert (ROOT/p).read_text(encoding='utf-8')==text,p
    results={}
    for name,fn in [('generic',generic_checks),('courage',courage_checks),('reactions',reaction_checks),('aggregate',aggregate_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=source_record();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==reading;s=reading['source']
    prior=json.loads((ROOT/'reports/reasoned-concession-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    assert any(x['start']==s['range'][0] and x['end']==s['range'][1] for x in prior['alignment']['segments'])
    alignment=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],start=s['range'][0],end=s['range'][1],source=s['text'],
        definitions=list(MEANINGS),status='partial_actual_causal_contribution_reading',full_semantic_equivalence=False)
    paths=set(build())|set(catalog().source_sha256)|set(prior['source_sha256'])|set(reading['source_sha256'])|{READING,
        'reports/reasoned-concession-v1.json','scripts/compose_courageous_undertaking.py','scripts/check_example_deterrence.py',
        'scripts/check_described_appraisals.py','scripts/check_described_explanations.py','scripts/compose_caused_deterrence.py',
        'scripts/check_caused_deterrence.py','tests/test_caused_deterrence.py','docs/caused-deterrence-v1.md'}
    return dict(status='actual_causation_replaces_adopted_explanation_in_deterrence',document=FULL,**results,alignment=alignment,
        verified_full_units={'kant-1784':0,'einstein-1905':0},new_covered_characters=0,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(source_record()));report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Actual cause, recognition, response and attributed contrast checked',flush=True)


if __name__=='__main__':main()
