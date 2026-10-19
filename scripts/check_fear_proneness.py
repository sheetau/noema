"""Check actual fear, courage and fear proneness independently."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_fear_proneness import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_example_deterrence import DOMAIN,SCENES,CASES,PEOPLE
from scripts.check_caused_deterrence import source_model
from scripts import check_reasoned_concession as discourse
from scripts import check_generalized_deterrence as previous

INDEX='data/semantic-review-index-v84.json'
REPORT='reports/fear-proneness-v1.json'
AUDIT='data/fear-proneness-reading-v1.json'
DOC='docs/fear-proneness-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
CUES=('cueone','cuetwo')
TIMES=SCENES+CUES


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(roots,suffix):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots.split()),statements=[])
    return parse(format_graph(d,'compact')+suffix)


def comparison_values(variant='baseline'):
    def candidates(p,g,a,s):
        return variant!='empty_comparison' and p in PEOPLE and symbol(g)==('bm' if variant=='wrong_goal' else 'bb') and a==(
            'belief' if variant=='wrong_anchor' else 'actual') and s in CUES and (variant!='wrong_person' or p=='other')
    def preferred(p,g,a,s,t):
        if variant=='cycle':return (s,t) in ((CUES[0],CUES[1]),(CUES[1],CUES[0]))
        return variant=='dominated_exception' and (s,t)==CUES
    return dict(hzys=candidates,hzyt=preferred)


def reaction_values(doc,observed=True,courage=False,prone=True,cause=True,variant='baseline'):
    base=source_model(doc,variant);v={n:unknown for n in (d['name'] for d in doc['declarations'] if d['kind']=='primitive')}
    def adapt(name,callback):
        def call(*args):
            cue=any(a in CUES for a in args if isinstance(a,str))
            mapped=tuple('actual' if isinstance(a,str) and a in CUES else a for a in args)
            if name=='mc':
                answer=prone if cue else observed
                if cue and variant in ('dominated_exception','unranked_exception') and args[-1]==CUES[1]:answer=False
                return answer and callback(*mapped)
            if name=='hzio':return courage and args[0]=='person' and symbol(args[1])=='bb'
            return callback(*mapped)
        return call
    v.update({n:adapt(n,f) for n,f in base.items()})
    def causal(a,f,b,r,s):
        return cause and a in CASES and b==('casec' if variant=='wrong_causal_target' else a) and symbol(f)==(
            'gt' if variant=='wrong_causal_factor' else 'gr') and symbol(r)==(
            'hzua' if variant=='old_causal_result' else 'r2bq') and s==('belief' if variant=='wrong_causal_scene' else 'actual')
    v.update(comparison_values(variant));v.update(za=lambda:'casea',zb=lambda:'actual',hzie=causal)
    if variant=='wrong_future_task':v['gp']=lambda a,g,s:symbol(g)=='bm'
    if variant=='not_future':v['go']=lambda a:'actual'
    return v


@lru_cache(None)
def disposition_checks():
    d=fixture('hzua r2bq','r za[] a.r zb[] d.q[t[k hzua[k za[]]][k zb[]]].q[t[k r2bq[k za[]]][k zb[]]].')
    rows=[]
    for observed,courage,prone in product((False,True),repeat=3):
        actual=evaluate(d,reaction_values(d,observed,courage,prone),DOMAIN,TIMES,True)
        assert actual==[observed and not courage,prone],(observed,courage,prone,actual)
        rows.append(dict(actual_fear=observed,sufficient_courage=courage,prone=prone,values=actual))
    wanted={'baseline':[True,True],'wrong_person':[True,False],'wrong_goal':[True,False],
        'wrong_anchor':[True,False],'empty_comparison':[True,False],'cycle':[True,False],
        'dominated_exception':[True,True],'unranked_exception':[True,False],
        'wrong_future_task':[False,False],'not_future':[False,False],'empty_attempts':[False,False]}
    contrasts={}
    for name,expected in wanted.items():
        actual=evaluate(d,reaction_values(d,variant=name),DOMAIN,TIMES,True)
        assert actual==expected,(name,actual,expected);contrasts[name]=actual
    selected=dict(d,statements=d['statements'][1:])
    v=reaction_values(d);v['hzio']=unknown
    assert evaluate(selected,v,DOMAIN,TIMES,True)==[True]
    for name in ('hzys','hzyt','mc','ma','dd','gp'):
        v=reaction_values(d);v[name]=unknown
        try:evaluate(selected,v,DOMAIN,TIMES,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(independent_conditions=rows,contrasts=contrasts,unknown_inputs_refused=6,
        current_fear_and_courage_independent_of_disposition=True,existing_hzq6_executed=True)


@lru_cache(None)
def causal_checks():
    d=fixture('r2br','r za[] a.r zb[] d.q[t[k r2br[k za[]]][k zb[]]].');rows=[]
    for recognized,prone,cause in product((False,True),repeat=3):
        v=reaction_values(d,observed=False,prone=prone,cause=cause)
        if not recognized:v['gg']=lambda *args:False
        actual=evaluate(d,v,DOMAIN,TIMES,True)
        assert actual==[recognized and prone and cause],(recognized,prone,cause,actual)
        rows.append(dict(recognized=recognized,prone=prone,cause=cause,values=actual))
    contrasts={}
    for name in ('baseline','wrong_causal_factor','wrong_causal_target','wrong_causal_scene','old_causal_result','wrong_recognized_example','unknown_example_result','wrong_task'):
        actual=evaluate(d,reaction_values(d,observed=False,variant=name),DOMAIN,TIMES,True)
        assert actual==[name=='baseline'],(name,actual);contrasts[name]=actual
    for name in ('hzie','gg','hzys'):
        v=reaction_values(d);v[name]=unknown
        try:evaluate(d,v,DOMAIN,TIMES,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(independent_conditions=rows,contrasts=contrasts,unknown_inputs_refused=3,
        native_recognition_and_disposition_executed=True,old_actual_state_not_accepted_as_causal_result=True)


@lru_cache(None)
def integration_checks():
    d=fixture('r2bs r2bi r2bt','r zanchor[] d.q[t[k r2bs[]][k zanchor[]]].q[t[k r2bi[]][k zanchor[]]].q[t[k r2bt[]][k zanchor[]]].')
    times=previous.TIMES+CUES
    def values(prone=True,avoid=True,variant='baseline'):
        base=previous.model(fear=True,avoid=avoid,variant=variant)
        v={p['name']:unknown for p in d['declarations'] if p['kind']=='primitive'}
        def adapt(name,f):
            def call(*args):
                cue=any(a in CUES for a in args if isinstance(a,str))
                mapped=tuple('actual' if isinstance(a,str) and a in CUES else a for a in args)
                if name=='mc' and cue:
                    return prone and not (variant in ('atypical_fear_exception','unranked_fear_exception') and args[0]=='third') and f(*mapped)
                return f(*mapped)
            return call
        v.update({n:adapt(n,f) for n,f in base.items()});old_cause=base['hzie']
        v['hzie']=lambda a,f,b,r,s:((a==b and a in CASES and symbol(f)=='gr' and s in previous.TIMES)
            if symbol(r)=='r2bq' else old_cause(a,f,b,r,s))
        v.update(hzys=lambda p,g,a,s:p in PEOPLE and symbol(g)=='bb' and a in previous.TIMES and s in CUES,
            hzyt=lambda *args:False)
        return v
    rows=[]
    for prone,avoid in product((False,True),repeat=2):
        actual=evaluate(d,values(prone,avoid),DOMAIN,times,True)
        assert actual==[prone,avoid,prone and avoid],(prone,avoid,actual)
        rows.append(dict(prone=prone,avoidance=avoid,values=actual));print('integrated conditions checked',flush=True)
    contrasts={}
    for name,expected in {'atypical_fear_exception':[True,True,True], 'unranked_fear_exception':[False,True,False],
        'empty_comparison':[False,False,False],'omit_exception':[True,False,False]}.items():
        actual=evaluate(d,values(variant=name),DOMAIN,times,True)
        assert actual==expected,(name,actual,expected);contrasts[name]=actual;print(name+' checked',flush=True)
    return dict(independent_conditions=rows,contrasts=contrasts,existing_avoidance_frequency_executed=True,
        person_disposition_case_generality_and_population_frequency_distinct=True)


@lru_cache(None)
def attribution_checks():
    d=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    def values(bits=(True,True,True),variant='baseline'):
        v=discourse.source_model(d)
        def claim(node,a,c,s):
            expected={'low':'e4','learn':'fs','outcome':'r2bk' if variant=='old_claim' else 'r2bt'}
            return (a,s)==('author','anchor') and node in expected and (node!='outcome' or bits[0]) and json.loads(c.syntax)==dict(kind='call',symbol=expected[node],arguments=[])
        def report(node,a,c,scope,s):
            return bits[1] and (node,a,scope,s)==('outcome','author','outcome','anchor') and discourse.unwrap(c)==dict(kind='call',symbol='r2bk' if variant=='old_foreground' else 'r2bt',arguments=[])
        def background(node,a,f,b,fs,bs,s):
            return bits[2] and (node,a,fs,bs,s)==('outcome','author','outcome','contrast','anchor') and [discourse.unwrap(f),discourse.unwrap(b)]==[
                dict(kind='call',symbol='r2bt',arguments=[]),dict(kind='call',symbol='r2bm' if variant=='old_background' else 'r2bv',arguments=[])]
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
    bg=fixture('r2bv','r za[] d.q[t[k r2bv[]][k za[]]].')
    v={x['name']:unknown for x in bg['declarations'] if x['kind']=='primitive'}
    v.update(za=lambda:'anchor',wa=lambda:'author',hzpt=discourse.ranker(premise='e4',outcome='r2bt',observer='author'))
    assert evaluate(bg,v,discourse.DOMAIN,discourse.SCENES)==[True]
    return dict(combinations=8,contrasts=rows,unknown_inputs_refused=5,world_contents_unknown=True,
        background_uses_new_outcome_on_both_sides=True,ordinary_evaluation=True)


def reading():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    start=unit['text'].index('ein Beispiel');text=unit['text'][start:]
    paths=(INDEX,INVENTORY,PARENT,PARENT_BASIS,FULL,BASIS,'artifacts/first-cause-reading-v1/page-482.jpg')
    return dict(status='local_fear_proneness_adopted',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,len(unit['text'])],text=text),
        decision='schüchternを活動へ向かう際に害の手掛かりに恐れやすい局所的性向と読み、現況の恐れと勇気の欠如の連言を置き換える。',
        selection=selection_binding(catalog(),[37]),interpretation_limits=LIMITS,
        references=[dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009133_7_2_2938',
            title='Adelung, Schüchtern, columns 1669–1670',accessed='2026-10-20',
            paraphrase='受動的用法は、害を目にすると容易に恐れ、近づくと逃げようとする傾向を述べる。応答の傾向として読む根拠であり、生涯の性格や原文の唯一の意味を保証するものではない。',
            applied_reading='恐れやすさを第一節に、回避を後続の明示的な節に置く。逃走を第一節の全事例へ強制しない。弱い刺激の比較基準は今回の解釈規約であり、辞書が同じ形式化を提案したとはしない。'),
            dict(url='https://korpora.org/Kant/aa08/036.html',title='Kant AA VIII, page 36',accessed='2026-10-20',
                paraphrase='先行例が萎縮を生み、通常は後の試みを避けさせる二つの反応を区別する。')],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def structure():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-11]==old.document['declarations']
    assert all(new.entries[n]==e for n,e in old.entries.items())
    changed=[i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'],strict=True)) if a!=b]
    assert changed==[37] and len(new.document['statements'])==52
    assert set(new.entries)-set(old.entries)==set(MEANINGS)|set(PRIMITIVES)
    assert new.entries['hzq6']==old.entries['hzq6'] and new.entries['r2bi']==old.entries['r2bi']
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
    return dict(new_definitions=9,new_primitives=2,changed_statement_indices=changed,preserved_statements=51,total_statements=52,
        preserved_review_selections=11,preserved_reviewed_sentence_characters=1021,roundtrips=True,
        disposition_operator_and_avoidance_frequency_unchanged=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('disposition',disposition_checks),('causal',causal_checks),('integration',integration_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_fear_proneness.py','scripts/check_fear_proneness.py','scripts/register_fear_proneness.py',
        'tests/test_fear_proneness.py','scripts/compose_courageous_undertaking.py',
        'scripts/check_caused_deterrence.py','scripts/check_example_deterrence.py','scripts/check_reasoned_concession.py',
        'scripts/check_generalized_deterrence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py'}
    return dict(status='fear_proneness_connected_to_cause_author_and_expectation',document=FULL,**results,
        alignment=dict(**r['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
