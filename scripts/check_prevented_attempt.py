"""Check factual prevention, prior stages and attribution of a partial reading."""
import argparse
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_prevented_attempt import ROOT,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,parent,build,closure

REPORT='reports/prevented-attempt-v1.json'
READING='data/prevented-attempt-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
DOMAIN=('person','other','guardone','guardtwo','guards','population','conditioning_act','blocking_act','warning','otheract','low','high')
SCENES=('conditioning','prior','actual','belief','loss')


def unknown(*args):raise ValueError('Unknown prevention input')
def ref(code,name):return code.rank==0 and json.loads(code.syntax)==dict(kind='function_ref',symbol=name)


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    doc=deepcopy(catalog().document);doc['declarations']=closure(doc,roots);doc['statements']=[]
    return parse(format_graph(doc,'compact')+suffix)


def evaluate(doc,values,*,memoize=False,domain=DOMAIN,scenes=SCENES):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=scenes,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=100000000,memoize_definitions=memoize,memoize_expressions=memoize)]


def causal_checks():
    doc=fixture(['hzsn','db'],'r zp[] a.r zs[] d.q[t[k hzsn[k db[] k zp[]]][k zs[]]].')
    def model(bits=(True,True,True,True,True),variant='baseline'):
        absent,occurs,first,second,cause=bits;v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        v.update(zp=lambda:'person',zs=lambda:'prior',db=lambda:'guards',
            ha=lambda a,b:a+b,hc=lambda a,b:a<b,hd=lambda truth:Fraction(int(truth)),
            mp=lambda g:SequenceValue(() if variant=='empty_agents' else ('guardone','guardtwo'),'"individual"'),
            aa=lambda p:p in ('person','guardone','guardtwo') and not(variant=='nonhuman_target' and p=='person'),
            ei=lambda p,g,s:not absent,
            dg=lambda a,s:occurs and (a,s)==('blocking_act','prior'),
            df=lambda p,a,s:(a,s)==('otheract' if variant=='split_acts' and p=='guardtwo' else 'blocking_act','prior') and (first and p=='guardone' or second and p=='guardtwo'),
            g3=lambda a,p,g,s:cause and (a,p,s)==('otheract' if variant=='other_cause_act' else 'blocking_act','other' if variant=='other_target' else 'person','actual' if variant=='other_scene' else 'prior') and ref(g,'ej' if variant=='positive_description' else 'hzsm'))
        return v
    rows=[]
    for bits in product((False,True),repeat=5):
        result=evaluate(doc,model(bits),scenes=('prior',));assert result==[all(bits)],(bits,result);rows.append(result)
    variants=('empty_agents','nonhuman_target','split_acts','other_cause_act','other_target','other_scene','positive_description')
    for variant in variants:assert evaluate(doc,model(variant=variant))==[False],variant
    for name in ('ei','dg','df','g3'):
        v=model();v[name]=unknown
        try:evaluate(doc,v)
        except ValueError as e:assert 'Unknown prevention' in str(e)
        else:raise AssertionError(name)
    return dict(combinations=len(rows),binding_contrasts=len(variants),unknown_inputs_refused=4,
        mere_nonattempt_does_not_prove_prevention=True,actual_defined_bodies_uncached=True)


def source_model(doc,variant='baseline'):
    from scripts.check_described_appraisals import source_model as appraisal
    v=appraisal(doc,judged_people={'person','other'});humans={'person','other','guardone','guardtwo'}
    first='prior' if variant in ('simultaneous','reverse_prefix') else 'belief' if variant=='late_conditioning' else 'conditioning'
    second='conditioning' if variant=='reverse_prefix' else 'belief' if variant=='late_blocking' else 'actual' if variant=='blocking_now' else 'prior'
    v.update(db=lambda:'guards',mv=lambda:'population',za=lambda:'actual',zb=lambda:first,zc=lambda:second,
        aa=lambda p:p in humans,
        mp=lambda g:SequenceValue(() if variant=='empty_agents' and g=='guards' else ('guardone','guardtwo') if g=='guards' else ('person','other'),'"individual"'),
        ak=lambda p,s:not(p in ('person','other') and s==first) or variant=='no_conditioning_result',
        ei=lambda p,g,s:variant=='actually_attempts' and p=='person' and s==second,
        dd=lambda a,b:SCENES.index(a)<SCENES.index(b))
    def occurs(a,s):return (a,s) in (('conditioning_act',first),('blocking_act',second),('warning','actual')) and not(variant=='no_warning' and a=='warning')
    def participates(p,a,s):
        return p in ('guardone','guardtwo') and (a,s) in (('conditioning_act',first),('otheract' if variant=='split_blocking' and p=='guardtwo' else 'blocking_act',second))
    def produces(a,p,g,s):
        if p not in ('person','other'):return False
        if variant=='different_earlier_target' and p=='person':return False
        if ref(g,'bj'):return (a,s)==('conditioning_act',first)
        return variant!='no_blocking_cause' and ref(g,'hzsm') and (a,s)==('blocking_act',second)
    v.update(dg=occurs,df=participates,g3=produces,
        f3=lambda p,a,s:p in ('guardone','guardtwo') and (a,s)==('otheract' if variant=='split_warning' and p=='guardtwo' else 'warning','actual'),
        f2=lambda a,p,q,g,s:p in ('person','other') and (a,q,s)==('warning','other' if variant=='wrong_warning_subject' else p,'actual') and ref(g,'ev'),
        f4=unknown)
    if variant=='empty_audience':v['u3']=lambda *a:False
    return v


def temporal_checks():
    doc=fixture(['hzsp','hzso','db'],'r za[] d.r zb[] d.r zc[] d.'+
        'q[k hzso[k db[] k za[] k zb[] k zc[]]].q[t[k hzsp[k db[]]][k za[]]].q[g p a[k dj[v p k zb[]]]].')
    rows={}
    variants=('baseline','simultaneous','reverse_prefix','late_conditioning','late_blocking','blocking_now','empty_agents',
        'empty_audience','no_conditioning_result','actually_attempts','no_blocking_cause','different_earlier_target','split_blocking','no_warning','split_warning','wrong_warning_subject')
    for variant in variants:
        actual=evaluate(doc,source_model(doc,variant),memoize=True)
        expected=[variant in ('baseline','simultaneous','reverse_prefix','no_warning','split_warning','wrong_warning_subject'),variant in ('baseline','simultaneous','reverse_prefix'),False]
        assert actual==expected,(variant,actual);rows[variant]=actual
    # Check the selected native precursor with the ordinary evaluator. Full
    # existential temporal search uses pure caching, not substituted bodies.
    precursor=deepcopy(doc);precursor['statements']=doc['statements'][:1]
    ordinary=evaluate(precursor,source_model(precursor));assert ordinary==rows['baseline'][:1]
    return dict(cases=rows,pure_memoization_for_contrasts=True,ordinary_precursor_agrees=True,
        recipients_fixed_at_presentation=True,warning_content_not_endorsed=True)


def attribution_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    for variant in ('baseline','other_author','other_context','other_node','old_model_content','reverse_order','missing_claim'):
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        v.update(wa=lambda:'author',wh=lambda:'context',hzsq=lambda:'clause',dq=lambda:'priorclause')
        def claim(n,a,g,s):
            return variant!='missing_claim' and (n,a,s)==('other' if variant=='other_node' else 'clause','other' if variant=='other_author' else 'author','other' if variant=='other_context' else 'context') and json.loads(g.syntax)==dict(kind='call',symbol='g6' if variant=='old_model_content' else 'hzsp',arguments=[dict(kind='call',symbol='db',arguments=[])])
        v.update(uc=claim,ue=lambda a,b,s:(a,b,s)==(('clause','priorclause','context') if variant=='reverse_order' else ('priorclause','clause','context')))
        actual=evaluate(doc,v,domain=('author','clause','priorclause','other'),scenes=('context',));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    return dict(cases=rows,all_world_and_model_inputs_unknown=True)


def structure():
    old=parent();new=catalog();assert new.document['declarations'][:-6]==old.document['declarations']
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==36
    active={d['name'] for d in closure(new.document,['hzsp'])};assert not active&{'er','ek','rx','eh','eg','ee','ef'}
    old_inputs={d['name'] for d in closure(old.document,['g6'])};assert {'er','ek','rx','eh'}<=old_inputs
    idx=json.loads((ROOT/'data/semantic-review-index-v26.json').read_text(encoding='utf-8'))
    for p in idx['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/p).read_text(encoding='utf-8'));indices=[x['index'] for x in r['selection']['statements']]
        assert selection_binding(old,indices)==r['selection']==selection_binding(new,indices)
    for p in (FULL,CORE):
        d=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    return dict(new_definitions=5,new_local_references=1,new_semantic_primitives=0,previous_statements_preserved=35,
        new_statement_index=35,nine_review_bindings_preserved=True,causal_equation_model_not_required=True,roundtrips=True)


def source_record():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    start=unit['text'].index('Nachdem sie ihr Hausvieh');end=unit['text'].index('Nun ist diese Gefahr')
    return dict(status='partial_factual_prevention_and_prior_presentation_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],text=unit['text'][start:end]),
        reference='https://korpora.org/Kant/aa08/035.html',
        decision='対象側の妨害を、同じ行為者の行為が本人の試みの不成立を生じさせることとして記述する。先行する二つの働きかけはともに提示より前とし、相互の厳密な順序は追加しない。',
        reason='原文は先行する働きかけと後続の提示を対比する。特定の二変数方程式、反事実割当て、唯一解、二つの先行行為の厳密な時刻順は明示していない。採用する最小の前後関係を原文の唯一の読解としない。',
        limits=['これは複文の対象側の部分記述。許可・機会・勇気を非試行だけへ還元しない。','家畜・歩行器・閉じ込め・身体的歩行の描写、慎重さ・穏順さ・強調、第二段落全体の確認が残る。',
            'g3の因果関係を原文の主張として表す。実世界の因果を発見・証明したわけではない。'],
        whole_unit_semantically_verified=False,binding=selection_binding(catalog(),[35]),
        source_sha256={INVENTORY:digest((ROOT/INVENTORY).read_bytes())})


def build_report():
    for p,text in build().items():assert (ROOT/p).read_text(encoding='utf-8')==text,p
    results={}
    for name,fn in [('causal',causal_checks),('temporal',temporal_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=source_record();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==reading
    historical=('reports/caused-conditions-v1.json','reports/scoped-interventions-v1.json','reports/directed-presentations-v1.json')
    records=[json.loads((ROOT/p).read_text(encoding='utf-8')) for p in historical]
    fragments=[records[0]['alignment'],records[1]['alignment']['segments'][0],records[2]['alignment']['segments'][0]]
    segments=[dict(start=f['start'],end=f['end'],source=f['source'],definitions=list(MEANINGS),status='partial_factual_prevention_reading') for f in fragments]
    alignment=dict(unit=reading['source']['unit'],unit_sha256=reading['source']['unit_sha256'],segments=segments,full_semantic_equivalence=False)
    prior=json.loads((ROOT/'reports/contextual-motto-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    paths=set(build())|set(catalog().source_sha256)|set(prior['source_sha256'])|set(reading['source_sha256'])|set(historical)|{READING,
        'reports/contextual-motto-v1.json','scripts/compose_prevented_attempt.py','scripts/check_prevented_attempt.py','scripts/check_described_appraisals.py',
        'tests/test_prevented_attempt.py','docs/prevented-attempt-v1.md'}
    return dict(status='partial_prevention_and_warning_connected',document=FULL,**results,alignment=alignment,
        historical_report_usage='Source alignment ranges only; historical runtime checks are not claimed reproduced.',
        verified_full_units={'kant-1784':0,'einstein-1905':0},new_covered_characters=0,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--reading-only',action='store_true');cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(source_record()))
    if args.reading_only:print('Partial prevention reading recorded',flush=True);return
    report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Factual prevention, prior stages and author attribution checked',flush=True)


if __name__=='__main__':main()
