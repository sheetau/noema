"""Test conditional scope and future anchors using the actual payment definitions."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts.compose_conditional_forecast import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,parent,build,closure
from scripts.check_payment_expectation import source_model,PEOPLE,SCENES,alignment
from scripts.check_motive_causes import unknown,symbol
from scripts.check_designation_order import substantive

INDEX='data/semantic-review-index-v44.json'
REPORT='reports/conditional-forecast-v1.json'
AUDIT='data/conditional-forecast-reading-v1.json'
DOC='docs/conditional-forecast-v1.md'

def evaluate(doc,v,people,scenes,memo=False):
    return [r['value'] for r in evaluate_document(doc,individuals=people,situations=scenes,
        primitives={d['name']:v[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=100000000,memoize_definitions=memo,memoize_expressions=memo)]

def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''r jperson[] a.
r jp[a d] c.r jl[a d] c.r jr[a d] c.r js[d] c.
d jpre[who a] e[b scene[k jp[v who v scene]]].
d jleft[who a] e[b scene[k jl[v who v scene]]].
d jright[who a] e[b scene[k jr[v who v scene]]].
q[k rqxg[k jperson[] p jpre p jleft p jright p js]].''')
    scenes=('A','B');rows=[]
    for selected in ((),('A',),('B',),scenes):
        for bits in product((False,True),repeat=6):
            sets=[{s for s,b in zip(scenes,bits[i:i+2]) if b} for i in (0,2,4)]
            v=dict(jperson=lambda:'person',js=lambda s:s in selected)
            for name,truth in zip(('jp','jl','jr'),sets):v[name]=lambda p,s,truth=truth:p=='person' and s in truth
            actual=evaluate(doc,v,('person','other'),scenes)[0]
            expected=bool(selected) and all(s not in sets[0] or s in sets[1]&sets[2] for s in selected)
            assert actual==expected,(selected,bits,actual)
            rows.append(dict(selected=list(selected),bits=list(bits),value=actual))
    return dict(cases=rows,ordinary_evaluation=True,empty_scope_rejected=True)

@lru_cache(None)
def source_doc(previous=False):
    c=parent() if previous else load_catalog(ROOT,BASIS)
    d=deepcopy(c.document);d.update(declarations=closure(d,['tp','tq','t2','t3','wh']),statements=[])
    return parse(format_graph(d,'compact')+'r jperson[] a.'+''.join('q[t[k '+n+'[k jperson[]]][k wh[]]].' for n in ('tp','tq','t2','t3')))

def source_values(variant):
    doc=source_doc();v=source_model(doc,variant);v['jperson']=lambda:'person'
    if variant=='unable_and_no_forecast':
        v['ae']=lambda *a:False;v['tw']=lambda *a:False
    if variant in ('hypothetical_anchor','wrong_forecast_anchor'):
        v['s2']=lambda p,c,s:(p,c,s)==('person','now','hyp')
        v['ae']=lambda p,m,s:(p,m,s)==('person','plan','hyp')
        v['af']=lambda p,m,s,e:(p,m,s,e)==('person','plan','hyp','paid')
        v['ap']=v['af']
        anchor='now' if variant=='wrong_forecast_anchor' else 'hyp'
        v['tu']=lambda p,t,c:(p,symbol(t),c)==('person','bm',anchor)
        v['tw']=lambda p,t,c,s:(p,symbol(t),c,s)==('person','tz',anchor,'future')
        v['tx']=lambda s,e:(s,e)==(anchor,'future')
    return v

def source_checks():
    variants=('baseline','already_paid','no_method','empty_results','no_transfer','gift','failed_goal',
        'thinking_required','empty_cases','self_takes_over','artifact_takes_over','wrong_beneficiary',
        'not_unpleasant','empty_forecast','wrong_forecast_description','not_future',
        'unable_and_no_forecast','hypothetical_anchor','wrong_forecast_anchor')
    rows={}
    for variant in variants:
        v=source_values(variant);scenes=(*SCENES,'hyp') if 'anchor' in variant else SCENES
        new=evaluate(source_doc(),v,PEOPLE,scenes,True)
        old=evaluate(source_doc(True),v,PEOPLE,scenes,True)
        if variant=='hypothetical_anchor':expected=[False,False,False,True];old_expected=[False]*4
        elif variant=='wrong_forecast_anchor':expected=[False,False,True,False];old_expected=[False,False,True,True]
        else:
            capacity=variant not in ('no_method','empty_results','no_transfer','gift','unable_and_no_forecast')
            effort=variant not in ('no_method','empty_results','failed_goal','thinking_required','unable_and_no_forecast')
            forecast=variant not in ('self_takes_over','artifact_takes_over','wrong_beneficiary','not_unpleasant',
                'empty_forecast','wrong_forecast_description','not_future','unable_and_no_forecast')
            expected=[capacity,effort,forecast,variant!='empty_cases' and (not capacity or effort and forecast)]
            old_expected=[capacity,effort,forecast,variant!='empty_cases' and (not capacity or effort) and forecast]
        assert new==expected and old==old_expected,(variant,new,old,expected,old_expected)
        rows[variant]=dict(previous=old,current=new)
    for variant in ('baseline','unable_and_no_forecast','hypothetical_anchor'):
        scenes=(*SCENES,'hyp') if 'anchor' in variant else SCENES
        assert evaluate(source_doc(),source_values(variant),PEOPLE,scenes)==rows[variant]['current']
    for n in ('s2','ae','tw','tu','tx','ts'):
        v=source_values('baseline');v[n]=unknown
        try:evaluate(source_doc(),v,PEOPLE,SCENES,True)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return dict(contrasts=rows,definitions_replaced_by_primitives=False,
        ordinary_comparisons=3,pure_memoization=True,unknown_inputs_refused=6,
        described_thinking_not_executed=True)

def attribution_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    for variant in ('baseline','other_author','other_node','other_description','other_context','reverse_order'):
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        v.update(t4=lambda:'payment',s3=lambda:'examples',wa=lambda:'author',wh=lambda:'text',
            s4=lambda n,a,t,c:(n,a,symbol(t),c)==('other' if variant=='other_node' else 'payment',
                'other' if variant=='other_author' else 'author','tr' if variant=='other_description' else 't3',
                'other' if variant=='other_context' else 'text'),
            ue=lambda a,b,c:(a,b,c)==(('payment','examples','text') if variant=='reverse_order' else ('examples','payment','text')))
        rows[variant]=evaluate(doc,v,('payment','examples','author','other'),('text',))
        assert rows[variant]==[variant=='baseline']
    return dict(contrasts=rows,all_payment_and_forecast_facts_unknown=True)

def structure():
    old,new=parent(),load_catalog(ROOT,BASIS)
    assert old.document['statements']==new.document['statements'] and len(new.document['statements'])==42
    assert set(new.entries)-set(old.entries)=={'rqxg'}
    changed=[n for n in old.entries if old.entries[n]['declaration']!=new.entries[n]['declaration']]
    assert changed==['t3']
    assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in old.entries if n!='t3')
    affected=[i for i,s in enumerate(new.document['statements']) if 't3' in {d['name'] for d in closure(new.document,_references(s))}]
    assert affected==[5]
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));ids=[s['index'] for s in review['selection']['statements']]
        a,b=selection_binding(old,ids),selection_binding(new,ids)
        assert a==review['selection'] and a['statements']==b['statements'] and a['dependencies']==b['dependencies']
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in a['dependencies'])
    sentence=json.loads((ROOT/'data/first-cause-reading-v1.json').read_text(encoding='utf-8'))
    assert sentence['selection']==selection_binding(old,[2,3])
    assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in sentence['selection']['dependencies'])
    for p,s in build().items():assert (ROOT/p).read_text(encoding='utf-8')==s
    for p in (FULL,CORE,LIBRARY):
        d=parse((ROOT/p).read_text(encoding='utf-8'))
        for style in ('full','compact'):
            s=format_graph(d,style);assert parse(s)==parse(transcribe(s,alphabet='v2'))==d
    return dict(preserved_statements=42,changed_definitions=changed,affected_statements=affected,
        new_definitions=1,new_primitives=0,preserved_review_meanings=11,
        first_cause_sentence_meanings_unchanged=True,roundtrips=True)

def audit():
    a=alignment()
    paths=(PARENT,PARENT_BASIS,INDEX,'artifacts/written-units-v1/kant-1784.json',
        'artifacts/first-cause-reading-v1/page-482.jpg','docs/payment-expectation-v1.md',
        'data/first-cause-reading-v1.json')
    return dict(status='conditional_forecast_scope_revision_not_whole_sentence_review',reviewer='assistant_review',
        source=dict(unit=a['unit'],unit_sha256=a['unit_sha256'],range=[a['start'],a['end']],text=a['source']),
        consulted='https://korpora.org/Kant/aa08/035.html',facsimile='artifacts/first-cause-reading-v1/page-482.jpg',
        reading='他者による引受けの見込みを、支払えるという同じ仮定内の続きとして採る。',
        evidence='原刊482頁で条件の後にセミコロンを挟んで後半が続くことを照合した。句読点だけで作用域が一意に決まるとはしない。',
        repair='旧定義は仮定外の現在にt2を要求した。新定義は同じ仮定状況でtqとt2をともに要求し、未来の基準もその状況へ結ぶ。',
        alternatives='後半を独立した見込みとする読みも可能であり、旧構造はその別の読みとして保存する。',
        remaining=['思考・支払い・仕事の語義とnur・schonの談話的な効果','代行の名詞と第二段落全体','後続本文とアインシュタイン全文'],
        whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})

def build_report():
    results={}
    for n,f in [('generic',generic_checks),('source',source_checks),('attribution',attribution_checks),('structure',structure)]:
        results[n]=f();print(n+' checked',flush=True)
    reading=audit();assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))==reading
    paths=set(build())|set(parent().source_sha256)|set(reading['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_conditional_forecast.py','scripts/check_conditional_forecast.py','scripts/register_conditional_forecast.py',
        'tests/test_conditional_forecast.py','scripts/check_payment_expectation.py','scripts/check_motive_causes.py',
        'scripts/check_designation_order.py','scripts/compose_falling_depiction.py','noema/constructed.py',
        'noema/constructed_semantics.py','noema/constructed_discourse.py','noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='conditional_forecast_scope_repaired_under_stated_reading',document=FULL,**results,
        alignment=dict(**reading['source'],definitions=['rqxg','t3','tp','tq','t2'],status='explicit_interpretive_annotation'),
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

def main():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(audit()));write_exact(ROOT/REPORT,encoded(build_report()))

if __name__=='__main__':main()
