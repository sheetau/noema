"""Verify contact/load distinctions without pretending to classify every gait."""
import argparse
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_support_phases import ROOT,LIBRARY,EXAMPLE,BASIS,EXAMPLE_BASIS,MEANINGS,LIMITS,build,source

REPORT='reports/support-phases-v1.json'
READING='data/support-phases-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
DOMAIN=('person','act','first','second','other')
SCENES=('start','middle','end','outside')
LOAD=(True,False,True,True,False,True)


def unknown(*args):raise ValueError('Unknown support-phase input')


@lru_cache(None)
def example():return parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))


def evaluate(model,doc=None):
    doc=example() if doc is None else doc
    return [row['value'] for row in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=200000,memoize_definitions=False,memoize_expressions=False)]


def model(contact=(True,)*6,load=LOAD,variant='baseline'):
    def scope(s):return s in SCENES[:3] and not(variant in ('omitted_middle','unobserved_middle') and s=='middle') and not(variant=='singleton' and s!='end') and variant!='empty'
    def foot(p,f,c):return (p,c)==('other' if variant=='other_owner' else 'person','outside' if variant=='other_foot_context' else 'end') and f in ('first','second')
    def known(p,a,f,s):return (p,a)==('person','act') and f in ('first','second') and s in SCENES[:3] and not(variant=='unassessed_middle' and s=='middle')
    def state(p,a,f,s,bits,label):
        who='other' if variant==label+'_person' else 'person';act='other' if variant==label+'_act' else 'act'
        if (p,a)!=(who,act) or f not in ('first','second') or s not in SCENES[:3]:return False
        part=('second' if f=='first' else 'first') if variant==label+'_swapped_feet' else f
        return bits[SCENES.index(s)*2+(part=='second')]
    def complete(p,a,chosen,c):
        return variant!='incomplete' and (p,a,c)==('other' if variant=='other_complete_person' else 'person',
            'other' if variant=='other_complete_act' else 'act','outside' if variant=='other_complete_context' else 'end') and all(chosen(s)==(s in SCENES[:3]) for s in SCENES)
    def before(a,b):
        if variant=='reversed_time':return SCENES.index(a)>SCENES.index(b)
        return SCENES.index(a)<SCENES.index(b) or variant=='cyclic_time' and (a,b)==('end','start')
    return dict(za=lambda:'person',zb=lambda:'act',zc=lambda:'first',zd=lambda:'first' if variant=='same_foot' else 'second',
        ze=lambda:'end',zf=lambda:'middle' if variant=='wrong_start' else 'start',zg=lambda:'middle' if variant=='wrong_end' else 'end',
        zh=lambda s:s!='outside' and not(variant=='unobserved_middle' and s=='middle'),zi=scope,zj=before,zk=foot,zl=complete,zm=known,
        zn=lambda p,a,f,s:state(p,a,f,s,contact,'contact'),zo=lambda p,a,f,s:state(p,a,f,s,load,'load'))


def expected(contact,load):
    assessed=all(not w or c for c,w in zip(contact,load,strict=True))
    supported=all(contact[i] or contact[i+1] for i in (0,2,4))
    noncontact=any(not contact[i] and not contact[i+1] for i in (0,2,4))
    return [assessed,assessed and supported,assessed and supported and tuple(load)==LOAD,assessed and noncontact]


def truth_checks():
    count=0;accepted_transfer=0
    for bits in product((False,True),repeat=6):
        for contact,load in ((bits,(False,)*6),(bits,LOAD),((True,)*6,bits)):
            result=evaluate(model(contact,load));assert result==expected(contact,load),(contact,load,result)
            assert not(result[1] and result[3]);count+=1;accepted_transfer+=result[2]
    return dict(combinations=count,accepted_transfer_cases=accepted_transfer,contact_distinct_from_load=True,
        inconsistent_support_rejected=True,noncontact_and_continuous_contact_exclusive=True,uncached=True)


def scope_checks():
    rows={}
    for variant in ('baseline','empty','singleton','omitted_middle','unobserved_middle','incomplete','unassessed_middle','same_foot',
        'other_owner','other_foot_context','other_complete_person','other_complete_act','other_complete_context',
        'wrong_start','wrong_end','reversed_time','cyclic_time','contact_person','contact_act','load_person','load_act','load_swapped_feet'):
        result=evaluate(model(variant=variant))
        want=[True,True,True,False] if variant=='baseline' else [True,True,False,False] if variant in ('load_person','load_act','load_swapped_feet') else [False]*4
        assert result==want,(variant,result,want);rows[variant]=result
    for name in ('zh','zi','zj','zk','zl','zm','zn','zo'):
        m=model();m[name]=unknown
        try:evaluate(m)
        except ValueError as e:assert 'Unknown support' in str(e)
        else:raise AssertionError(name)
    return dict(cases=rows,unknown_inputs_refused=8,missing_unobserved_phase_not_completed_by_finite_order=True)


def counterexamples():
    # No locomotion or gait-class predicate is supplied: equal support patterns
    # can describe a moving gait or a stationary shift of body weight.
    cases={
        'overlapping_transfer':((True,False,True,True,False,True),LOAD,[True,True,True,False]),
        'touch_without_load':((True,)*6,(False,)*6,[True,True,False,False]),
        'constant_two_foot_support':((True,)*6,(True,)*6,[True,True,False,False]),
        'noncontact_gap':((True,False,False,False,False,True),(True,False,False,False,False,True),[True,False,False,True]),
        'claimed_load_without_contact':((True,False,False,False,False,True),LOAD,[False]*4),
        'reversed_transfer':((True,)*6,(False,True,True,True,True,False),[True,True,False,False]),
    };rows={}
    for name,(contact,load,want) in cases.items():
        result=evaluate(model(contact,load));assert result==want,(name,result);rows[name]=result
    # The three positive transfer witnesses still exist, but there is an
    # additional noncontact phase between the overlap and the final support.
    m=model();states={'start':(True,False),'middle':(True,True),'end':(False,False),'outside':(False,True)}
    m.update(zg=lambda:'outside',zh=lambda s:True,zi=lambda s:True,
        zl=lambda p,a,scope,c:(p,a,c)==('person','act','end') and all(scope(s) for s in SCENES),
        zm=lambda p,a,f,s:(p,a)==('person','act') and f in ('first','second'),
        zn=lambda p,a,f,s:(p,a)==('person','act') and f in ('first','second') and states[s][f=='second'],
        zo=lambda p,a,f,s:(p,a)==('person','act') and f in ('first','second') and states[s][f=='second'])
    result=evaluate(m);assert result==[True,False,False,True];rows['three_witnesses_with_intermediate_gap']=result
    d=example();declared={x['name'] for x in d['declarations']}
    assert not declared&{'zai','zal','hzux','hzuy','hzv3','rcq'}
    return dict(cases=rows,no_walking_running_skill_or_control_inferred=True,
        grounded_gait_and_stationary_transfer_can_share_description=True)


def structure():
    cat=load_catalog(ROOT,EXAMPLE_BASIS);assert len(cat.document['statements'])==4
    for name,text in build().items():assert (ROOT/name).read_text(encoding='utf-8')==text,name
    for name in (LIBRARY,EXAMPLE):
        d=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    index=json.loads((ROOT/'data/semantic-review-index-v34.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT,index['source_sha256']);active=index['works']['kant-1784']
    assert active['document']=='examples/v016/kant-bodily-acquisition.noema'
    assert len(source().document['statements'])==40
    assert all(name not in set(build()) for name in index['source_sha256'])
    return dict(new_definitions=5,new_source_primitives=0,context_inputs_in_example=15,roundtrips=True,
        active_manuscript_unchanged=True,source_adoption=False)


def reading():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    phrase='gehen lernen';a=unit['text'].index(phrase)
    return dict(status='locomotion_description_component_not_a_walking_definition',reviewer='assistant_review',
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[a,a+len(phrase)],text=phrase),
        references=[dict(url='https://korpora.org/Kant/aa08/036.html',use='歩行の習得を述べる原文箇所。'),
            dict(url='https://d-nb.info/1228757739/34',doi='10.1007/s00421-020-04592-2',pages=[1,2],
                use='研究対象は子ども22名と成人7名。接地・空中期やエネルギー関係だけで発達中の運動を一律に分類せず、多くの特徴を比較している。有限の接地条件をgehenの完全な語義としない判断の根拠。')],
        decision='全過程の接地と荷重支持の移行を記述する一般構成を追加する。これを歩行の必要十分条件としてカント本文に採用する判断は行わない。',
        limitations=LIMITS,whole_unit_semantically_verified=False)


def build_report():
    results={}
    for name,fn in [('truth',truth_checks),('scope',scope_checks),('counterexamples',counterexamples),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    note=reading();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==note;s=note['source']
    prior='reports/bodily-acquisition-v1.json';validate_hashes(ROOT,json.loads((ROOT/prior).read_text(encoding='utf-8'))['source_sha256'])
    paths=set(build())|set(source().source_sha256)|{READING,INVENTORY,prior,'scripts/compose_support_phases.py','scripts/check_support_phases.py',
        'scripts/compose_limits.py','scripts/compose_falling_depiction.py','scripts/compose_bodily_acquisition.py','tests/test_support_phases.py',
        'docs/support-phases-v1.md','noema/constructed_semantics.py','noema/meaning_catalog.py','noema/semantic_reviews.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/script.py','data/semantic-review-index-v34.json'}
    return dict(status='support_phase_component_not_source_equivalence',document=EXAMPLE,**results,
        alignment=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],start=s['range'][0],end=s['range'][1],source=s['text'],
            definitions=list(MEANINGS),status='explicit_interpretive_annotation',full_semantic_equivalence=False),
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(reading()));report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Covered contact, load transfer and gait-classification limits checked',flush=True)


if __name__=='__main__':main()
