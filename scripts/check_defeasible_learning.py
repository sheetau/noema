"""Check open-outcome hypotheses, plausibility and native acquisition separately."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_defeasible_learning import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure,new_index,reindex_binding
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts import check_walking_acquisition as learning
from scripts import check_reasoned_concession as discourse

INDEX='data/semantic-review-index-v85.json'
REPORT='reports/defeasible-learning-v1.json'
AUDIT='data/defeasible-learning-reading-v1.json'
DOC='docs/defeasible-learning-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(roots,suffix):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots.split()),statements=[])
    return parse(format_graph(d,'compact')+suffix)


@lru_cache(None)
def generic_checks():
    d=fixture('ri r2by','''r zanchor[] d.r zcases[d] c.r zpreferred[d d] c.r zlater[d d] c.r ztruth[d] c.
d zcontent[] e[b scene[k ztruth[v scene]]].
q[k ri[k zcontent[] k zanchor[] p zcases p zlater]].
q[k r2by[k zcontent[] k zanchor[] p zcases p zpreferred p zlater]].''')
    points=('good','bad');times=('anchor',*points,'outside');count=0
    def values(relation,truth,future,cases=points,observed=False):
        return dict(zanchor=lambda:'anchor',zcases=lambda s:s in cases,zpreferred=lambda a,b:(a,b) in relation,
            zlater=lambda a,b:a=='anchor' and b in future,ztruth=lambda s:(s=='anchor' and observed) or s in truth)
    for bits in product((False,True),repeat=4):
        relation={p for p,flag in zip(product(points,repeat=2),bits) if flag}
        composed={(a,c) for a,b in relation for mid,c in relation if b==mid}
        strict=not any(a==b for a,b in relation) and composed<=relation
        best=set(points)-{b for a,b in relation}
        for truth_bits,future_bits,observed in product(product((False,True),repeat=2),product((False,True),repeat=2),(False,True)):
            truth={p for p,flag in zip(points,truth_bits) if flag};future={p for p,flag in zip(points,future_bits) if flag}
            actual=evaluate(d,values(relation,truth,future,observed=observed),('person',),times,True)
            expected=[set(points)<=truth and set(points)<=future,strict and bool(best) and best<=truth and set(points)<=future]
            assert actual==expected,(relation,truth,future,observed,actual);count+=1
    variants={
        'dominated_failure':({('good','bad')},{'good'},set(points),points,[False,True]),
        'unranked_failure':(set(),{'good'},set(points),points,[False,False]),
        'outside_preference':({('outside','good')},{'good'},set(points),('good',),[True,True]),
        'empty':(set(),set(),set(),(),[False,False]),
        'current_exception':({('good','anchor')},{'good'},set(times),('good','anchor'),[False,False]),
    };rows={}
    for name,(relation,truth,future,cases,wanted) in variants.items():
        actual=evaluate(d,values(relation,truth,future,cases),('person',),times,True)
        assert actual==wanted,(name,actual);rows[name]=actual
    for name in ('zcases','zpreferred','zlater','ztruth'):
        v=values({('good','bad')},{'good'},set(points));v[name]=unknown
        try:evaluate(d,v,('person',),times,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(independent_relation_response_time_and_actual_combinations=count,contrasts=rows,unknown_inputs_refused=4,
        all_hypotheses_time_checked=True,failed_hypotheses_retained=True,current_truth_independent=True)


@lru_cache(None)
def native_document():
    return fixture('fr r2ay r2bz r2ca','''r zp[] a.r znow[] d.
q[t[k fr[k zp[]]][k znow[]]].q[t[k r2bz[k zp[]]][k znow[]]].
q[t[k r2ay[k zp[]]][k znow[]]].q[t[k r2ca[k zp[]]][k znow[]]].''')


def native_values(mind=True,body=True,variant='baseline'):
    d=native_document();v=learning.model(d,variant,body=body,mind=mind)
    points=('end','actual' if variant=='current_exception' else 'otherend')
    v.update(wa=lambda:'author',fl=lambda p,a,s:(p,a)==('person','actual') and s in points,
        tx=lambda a,s:a=='actual' and s in points and not(variant=='invalid_exception_time' and s=='otherend'))
    def hypotheses(p,g,a,s):
        return variant!='empty_hypotheses' and p==('other' if variant=='wrong_person' else 'person') and a==(
            'start' if variant=='wrong_anchor' else 'actual') and symbol(g) in (
                ('zal',) if variant=='only_body_background' else ('bb','zal')) and s in points
    def plausible(observer,p,g,a,first,last):
        valid=(observer,p,a)==('other' if variant=='wrong_observer' else 'author','person','actual') and symbol(g) in ('bb','zal')
        return valid and variant!='unranked_failure' and ((first,last)==points or variant=='cyclic_preference' and (last,first)==points)
    v.update(hzyu=hypotheses,hzyv=plausible)
    return v


@lru_cache(None)
def native_checks():
    d=native_document();people=learning.PEOPLE+('author',);rows=[]
    for mind,body in product((False,True),repeat=2):
        actual=evaluate(d,native_values(mind,body),people,learning.SCENES,True)
        assert actual==[False,mind,False,body],(mind,body,actual)
        rows.append(dict(intellectual_acquisition=mind,bodily_acquisition=body,values=actual));print('native content pair checked',flush=True)
    contrasts={}
    for name,wanted in {
        'baseline':[False,True,False,True], 'only_body_background':[False,False,False,True],
        'wrong_person':[False]*4,'wrong_anchor':[False]*4,'wrong_observer':[False]*4,
        'empty_hypotheses':[False]*4,'unranked_failure':[False]*4,'cyclic_preference':[False]*4,
        'invalid_exception_time':[False]*4,'current_exception':[False]*4,'no_contribution':[False]*4,
    }.items():
        actual=evaluate(d,native_values(variant=name),people,learning.SCENES,True)
        assert actual==wanted,(name,actual,wanted);contrasts[name]=actual;print(name+' checked',flush=True)
    selected=dict(d,statements=[d['statements'][1],d['statements'][3]])
    for name in ('hzyu','hzyv','tx','fk'):
        v=native_values();v[name]=unknown
        try:evaluate(selected,v,people,learning.SCENES,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(independent_contents=rows,contrasts=contrasts,unknown_inputs_refused=4,
        native_capacity_experience_contribution_and_acquisition_executed=True,
        no_factive_learning_in_actual_context=True,columns=['old_universal_mind','new_mind','old_universal_body','new_body'])


@lru_cache(None)
def attribution_checks():
    d=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    def values(bits=(True,True,True),variant='baseline'):
        v=discourse.source_model(d)
        def claim(node,a,c,s):
            expected={'low':'e4','learn':'fs' if variant=='old_learning' else 'r2cc','outcome':'r2bt'}
            return (a,s)==('author','anchor') and node in expected and (node!='learn' or bits[0]) and json.loads(c.syntax)==dict(kind='call',symbol=expected[node],arguments=[])
        def report(node,a,c,scope,s):
            return (node,a,scope,s)==('outcome','author','outcome','anchor') and discourse.unwrap(c)==dict(kind='call',symbol='r2bt',arguments=[])
        def background(node,a,f,b,fs,bs,s):
            return (node,a,fs,bs,s)==('outcome','author','outcome','contrast','anchor') and [discourse.unwrap(f),discourse.unwrap(b)]==[
                dict(kind='call',symbol='r2bt',arguments=[]),dict(kind='call',symbol='r2bv',arguments=[])]
        reason=v['ud']
        v.update(uc=claim,hznreport=report,hzrbgreport=background,ud=lambda *args:bits[1] and variant!='missing_reason' and reason(*args),
            qa=lambda node,a,target,body,s:bits[2] and (node,a,symbol(target),symbol(body),s)==(
                'other' if variant=='wrong_depiction_node' else 'learn','author',
                'fr' if variant=='old_depiction_target' else 'r2bz','r2ay' if variant=='old_depiction_body' else 'r2ca','anchor'))
        if variant=='wrong_author':v['wa']=lambda:'other'
        if variant=='wrong_context':v['wh']=lambda:'elsewhere'
        return v
    for bits in product((False,True),repeat=3):
        assert evaluate(d,values(bits),discourse.DOMAIN,discourse.SCENES)==[bits[0] and bits[1],bits[2]]
    wanted={'baseline':[True,True],'old_learning':[False,True],'missing_reason':[False,True],
        'wrong_depiction_node':[True,False],'old_depiction_target':[True,False],'old_depiction_body':[True,False],
        'wrong_author':[False,False],'wrong_context':[False,False]}
    for name,expected in wanted.items():
        actual=evaluate(d,values(variant=name),discourse.DOMAIN,discourse.SCENES)
        assert actual==expected,(name,actual,expected);rows[name]=actual
    for name in ('uc','ud','ue','qa','hznreport','hzrbgreport'):
        v=values();v[name]=unknown
        try:evaluate(d,v,discourse.DOMAIN,discourse.SCENES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(independent_conditions=8,contrasts=rows,unknown_inputs_refused=6,world_contents_unknown=True)


def reading():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    text='denn sie würden durch einigemahl Fallen wohl endlich gehen lernen';start=unit['text'].index(text)
    paths=(INDEX,INVENTORY,PARENT,PARENT_BASIS,FULL,BASIS,'reports/walking-acquisition-v1.json','artifacts/first-cause-reading-v1/page-482.jpg')
    return dict(status='hypothesis_plausibility_and_acquisition_separated',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(text)],text=text),
        decision='学習結果を含まない試行の仮定範囲と、著者による認識的な優先関係を分け、優先候補での取得を推量として記述する。',
        selection=selection_binding(catalog(),[37,49]),interpretation_limits=LIMITS,
        references=[
            dict(url='https://grammis.ids-mannheim.de/systematische-grammatik/312',title='IDS, Würde-Formen',accessed='2026-10-20',
                use='würde形だけから未来時制とはしない。同時・後時の関係は文脈で区別する。'),
            dict(url='https://lexika.digitale-sammlungen.de/adelung///lemma/bsb00009134_6_2_2635',title='Adelung, Wohl, 3(1)',accessed='2026-10-20',
                use='推量・疑いの用法を採用する根拠。数値確率や今回の形式モデルを辞書へ帰属しない。'),
            dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009131_7_1_1214',title='Adelung, Endlich, 2(1)',accessed='2026-10-20',
                use='時間・順序の終わりという用法を採用する。別の用法にある長い期間を必須とはしない。')],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def structure():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-9]==old.document['declarations'] and all(new.entries[n]==e for n,e in old.entries.items())
    assert len(old.document['statements'])==52 and len(new.document['statements'])==51
    assert old.document['statements'][39]['body']['symbol']=='hzv4'
    changed=[]
    for i,s in enumerate(old.document['statements']):
        if i==39:continue
        if s!=new.document['statements'][new_index(i)]:changed.append(i)
    assert changed==[37,50] and set(new.entries)-set(old.entries)==set(MEANINGS)|set(PRIMITIVES)
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for p in index['works']['kant-1784']['reviews']:
        row=json.loads((ROOT/p).read_text(encoding='utf-8'));binding=row['selection'];ids=[s['index'] for s in binding['statements']]
        assert not set(ids)&{37,39,50} and binding==selection_binding(old,ids)
        assert reindex_binding(binding)==selection_binding(new,[new_index(i) for i in ids])
    preceding=json.loads((ROOT/'reports/guarded-walking-reading-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,preceding['source_sha256'])
    bindings=[r['current_selection'] for r in preceding['preceding']['reviews'].values()]
    bindings.append(json.loads((ROOT/'data/guarded-walking-reading-v1.json').read_text(encoding='utf-8'))['selection'])
    for binding in bindings:assert reindex_binding(binding)==selection_binding(new,[new_index(s['index']) for s in binding['statements']])
    active=selection_binding(new,list(range(51)))['dependencies']
    assert not set(active)&{'fl','fr','fs','ft','hzv2','hzv3','hzv4','r2ay','r2az','r2bx'}
    assert {'r2bz','r2ca','r2cc','r2cd','r2ce','r2by','r2bt','r2bi'}<=set(active)
    for p,body in build().items():assert (ROOT/p).read_text(encoding='utf-8')==body,p
    for p in (FULL,CORE,LIBRARY):
        d=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    r=reading();assert r==json.loads((ROOT/AUDIT).read_text(encoding='utf-8'));validate_hashes(ROOT,r['source_sha256'])
    return dict(new_definitions=7,new_primitives=2,revised_old_statement_indices=changed,removed_old_statement_indices=[39],
        revised_statement_indices=[37,49],preserved_statements=49,total_statements=51,
        preserved_review_selections=11,preserved_reviewed_sentence_characters=1021,roundtrips=True,
        obsolete_prospect_dependencies_absent=True,review_bindings_reindexed_without_meaning_change=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('generic',generic_checks),('native',native_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_defeasible_learning.py','scripts/check_defeasible_learning.py','scripts/register_defeasible_learning.py',
        'tests/test_defeasible_learning.py','scripts/compose_courageous_undertaking.py','scripts/check_walking_acquisition.py',
        'scripts/check_reasoned_concession.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py'}
    return dict(status='defeasible_learning_and_shared_depiction_adopted',document=FULL,**results,
        alignment=dict(**r['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
