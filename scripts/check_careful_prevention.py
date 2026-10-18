"""Test distributed attention and causal-event identity without success inference."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_careful_prevention import ROOT,PARENT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,parent,build,closure
from scripts.check_prevented_attempt import DOMAIN,SCENES,unknown,ref
from scripts.check_confinement_depiction import target_model

REPORT='reports/careful-prevention-v1.json'
READING='data/careful-prevention-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    doc=deepcopy(catalog().document);doc['declarations']=closure(doc,roots);doc['statements']=[]
    return parse(format_graph(doc,'compact')+suffix)


def evaluate(doc,model,domain,scenes,memoize=True):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=scenes,
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=100000000,memoize_definitions=memoize,memoize_expressions=memoize)]


def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zact[] a.r ztarget[] a.r zscene[] d.r zagents[a] c.r zrelevant[a] c.
r zattention[a a i[h[j[a]] e] j[a] a d] c.r zaims[a a i[h[j[a]] e] j[a] d] c.
r zoccurs[a d] c.r zperforms[a a d] c.r zstate[j[a] d] c.
d zgoal[bindings j[a]] e[b scene[k zstate[v bindings v scene]]].
q[k rqvp[p zagents k zact[] r[p zgoal] l[a][k ztarget[]] p zrelevant p zattention p zaims p zoccurs p zperforms k zscene[]]].
''')
    domain=('one','two','outsider','act','otheract','target','other','detailone','detailtwo','irrelevant');times=('now','later')
    def model(bits=(True,True,True,True,True),variant='baseline'):
        occurs,first,second,aimone,aimtwo=bits
        def attention(actor,act,goal,bindings,aspect,scene):
            wanted='one' if variant=='one_actor_handles_all' or aspect=='detailone' else 'outsider' if variant=='foreign_attender' else 'two'
            return (actor,act,bindings.items,scene)==(wanted,
                'otheract' if variant=='split_attention' and aspect=='detailtwo' else 'act',
                ('other',) if variant=='other_bindings' else ('target',),'later' if variant=='other_scene' else 'now') and \
                ref(goal,'zother' if variant=='other_goal' else 'zgoal') and (first if aspect=='detailone' else second if aspect=='detailtwo' else False)
        def aims(actor,act,goal,bindings,scene):
            return actor in ('one','two') and (aimone if actor=='one' else aimtwo) and (act,bindings.items,scene)==(
                'act',('target',),'later' if variant=='other_aim_scene' else 'now') and ref(goal,'zother' if variant=='other_aim_goal' else 'zgoal')
        return dict(zact=lambda:'act',ztarget=lambda:'target',zscene=lambda:'now',
            zagents=lambda a:variant!='no_agents' and a in ('one','two'),
            zrelevant=lambda a:variant!='empty_scope' and a in ('detailone','detailtwo'),
            zattention=attention,zaims=aims,zoccurs=lambda a,s:occurs and (a,s)==('act','now'),
            zperforms=lambda a,e,s:a in ('one','two') and (e,s)==('act','now') and not(variant=='nonparticipant' and a=='two'),zstate=unknown)
    count=0
    for bits in product((False,True),repeat=5):
        result=evaluate(doc,model(bits),domain,times,False);assert result==[all(bits)],(bits,result);count+=1
    rows={}
    for variant in ('baseline','empty_scope','no_agents','split_attention','foreign_attender','other_goal','other_bindings','other_scene',
        'nonparticipant','other_aim_goal','other_aim_scene','one_actor_handles_all'):
        result=evaluate(doc,model(variant=variant),domain,times,False)
        assert result==[variant in ('baseline','one_actor_handles_all')],(variant,result);rows[variant]=result
    for name in ('zrelevant','zattention','zaims','zoccurs','zperforms'):
        m=model();m[name]=unknown
        try:evaluate(doc,m,domain,times,False)
        except ValueError as e:assert 'Unknown prevention' in str(e)
        else:raise AssertionError(name)
    return dict(combinations=count,contrasts=rows,unknown_inputs_refused=5,
        goal_content_unknown=True,uncached_native_definitions=True,no_kant_specific_dependencies=True)


def goal_checks():
    suffix='r zp[] a.r zo[] a.r za[] d.'
    for bindings in ('l[a][]','l[a][k zp[]]','l[a][k zo[]]','l[a][k zp[] k zo[]]'):
        suffix+='q[t[k hztm['+bindings+']][k za[]]].'
    suffix+='q[t[k hzsm[k zp[]]][k za[]]].'
    doc=fixture(['hztm'],suffix)
    rows=[]
    for attempts in (False,True):
        model={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        model.update(zp=lambda:'person',zo=lambda:'other',za=lambda:'prior',
            ei=lambda p,g,s:(attempts if p=='person' else not attempts) if ref(g,'bb') else False)
        actual=evaluate(doc,model,('person','other'),('prior',),False)
        assert actual==[False,not attempts,attempts,False,not attempts],actual;rows.append(actual)
    model['ei']=unknown
    try:evaluate(doc,model,('person','other'),('prior',),False)
    except ValueError as e:assert 'Unknown prevention' in str(e)
    else:raise AssertionError('Unknown trial became an absence goal')
    return dict(cases=rows,same_person_and_result_content=True,extra_and_empty_bindings_rejected=True,unknown_attempt_refused=True)


def source_checks():
    doc=fixture(['hztr','hztt','hztf','hzth'],'r zp[] a.r za[] d.r zb[] d.'+
        'q[t[k hztr[k db[]]][k za[]]].q[t[k hztt[k zp[]]][k za[]]].'+
        'q[t[k hztf[k db[]]][k za[]]].q[t[k hzth[k zp[]]][k za[]]].')
    variants=('baseline','missing_detail','empty_scope','foreign_attender','other_goal','other_bindings','other_scene',
        'no_purpose','separate_careful_act','no_cause','actually_attempts','permission_present')
    rows={}
    for variant in variants:
        model=target_model(doc,'actually_attempts' if variant=='actually_attempts' else 'baseline')
        model.update(hztd=lambda:'supervised',h7k=unknown,h7l=lambda *a:variant=='permission_present')
        careact='otheract' if variant=='separate_careful_act' else 'blocking_act'
        if variant=='separate_careful_act':
            occurs=model['dg'];performs=model['df']
            model['dg']=lambda a,s:(a,s)==('otheract','prior') or occurs(a,s)
            model['df']=lambda a,e,s:a in ('guardone','guardtwo') and (e,s)==('otheract','prior') or performs(a,e,s)
        if variant=='no_cause':model['g3']=lambda *a:False
        def target(goal,bindings):return ref(goal,'hztm') and bindings.items in (('person',),('other',))
        def relevant(group,act,goal,bindings,aspect,scene):
            return variant!='empty_scope' and (group,act,scene)==('guards',careact,'prior') and target(goal,bindings) and aspect in ('detailone','detailtwo')
        def attention(actor,act,goal,bindings,aspect,scene):
            return (actor,act,scene)==('outsider' if variant=='foreign_attender' else 'guardone' if aspect=='detailone' else 'guardtwo',
                careact,'actual' if variant=='other_scene' else 'prior') and ref(goal,'hzta' if variant=='other_goal' else 'hztm') and \
                bindings.items in ((('foreign',),) if variant=='other_bindings' else (('person',),('other',))) and \
                aspect in ('detailone','detailtwo') and not(variant=='missing_detail' and aspect=='detailtwo')
        model.update(hztk=relevant,hztj=attention,hztl=lambda actor,act,goal,bindings,scene:variant!='no_purpose' and actor in ('guardone','guardtwo') and
            (act,scene)==(careact,'prior') and target(goal,bindings))
        actual=evaluate(doc,model,DOMAIN+('supervised','detailone','detailtwo'),SCENES)
        old=variant not in ('no_cause','actually_attempts','permission_present');expected=[variant=='baseline',variant=='baseline',old,old]
        assert actual==expected,(variant,actual,expected);rows[variant]=actual
    return dict(cases=rows,same_causal_event_required=True,success_alone_insufficient=True,pure_memoization=True)


def attribution_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    for variant in ('baseline','old_timeline','old_figure','other_author','other_context','other_clause','reverse_order'):
        model={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        model.update(wa=lambda:'author',wh=lambda:'context',hzsq=lambda:'clause',hzst=lambda:'relative',dq=lambda:'previous')
        def same(a,s):return (a,s)==('other' if variant=='other_author' else 'author','other' if variant=='other_context' else 'context')
        model.update(uc=lambda n,a,c,s:same(a,s) and n==('other' if variant=='other_clause' else 'clause') and json.loads(c.syntax)==dict(
            kind='call',symbol='hztf' if variant=='old_timeline' else 'hztr',arguments=[dict(kind='call',symbol='db',arguments=[])]),
            qa=lambda n,a,t,d,s:same(a,s) and n=='relative' and ref(t,'hzth' if variant=='old_figure' else 'hztt') and ref(d,'zbf'),
            ue=lambda a,b,s:(a,b,s)==(('clause','previous','context') if variant=='reverse_order' else ('previous','clause','context')))
        actual=evaluate(doc,model,('author','clause','relative','previous','other'),('context',))
        expected=[variant not in ('old_timeline','other_author','other_context','other_clause','reverse_order'),variant not in ('old_figure','other_author','other_context')]
        assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(cases=rows,attention_relevance_purpose_and_world_unknown=True)


def structure():
    old=parent();new=catalog();assert new.document['declarations'][:-13]==old.document['declarations']
    assert all(new.entries[n]==entry for n,entry in old.entries.items())
    changed=[i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'],strict=True)) if a!=b]
    assert changed==[35,36] and len(new.document['statements'])==37
    used={d['name'] for d in closure(new.document,['hzts','hztu'])};assert {'rqvp','hzto','hztn','hztc','hztj','hztk','hztl'}<=used
    assert not used&{'hzsn','er','ek','rx','q3','hztg','hzti'}
    idx=json.loads((ROOT/'data/semantic-review-index-v29.json').read_text(encoding='utf-8'))
    for path in idx['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[s['index'] for s in review['selection']['statements']]
        assert not set(indices)&set(changed)
        assert selection_binding(old,indices)==review['selection']==selection_binding(new,indices)
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    return dict(new_definitions=10,new_primitive_relations=3,changed_statement_indices=changed,other_statements_preserved=35,
        nine_review_bindings_preserved=True,generic_library_has_no_source_primitives=True,roundtrips=True)


def source_record():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    phrase='sorgfältig';start=unit['text'].index(phrase)
    return dict(status='explicit_goal_directed_attention_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase),
        references=['https://korpora.org/Kant/aa08/035.html','https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_2_1_1145'],
        decision='同じ阻止行為の遂行で、目標と関係する事項へ目的に沿って注意を配るという読みを採る。共同の行為で担当を分けてもよい。',
        reasoning='AdelungのSorgfalt項は対象とその細部へ向ける精神の方向付けを説明する。それを参考に、単なる成功や好意で代用せず、関連事項への注意を構成する。集団内の分担や範囲の具体化は今回の解釈であり、資料から一意に決まるとはしない。',
        limits=['原文は具体的な注意事項や担当者を列挙していない。関連範囲を解釈として固定し、全称条件の有限検査で現実の網羅性を証明しない。',
            '注意・関連性と、引数を保つ目的志向を三つの基本関係として明示する。認知的機構・尺度・持続時間の一般理論まで還元したものではない。',
            '穏順さ・強調・身体的描写・皮肉・学習と萎縮の接続、第二段落全体の確認は残る。'],
        whole_unit_semantically_verified=False,binding=selection_binding(catalog(),[35,36]),source_sha256={INVENTORY:digest((ROOT/INVENTORY).read_bytes())})


def build_report():
    for p,text in build().items():assert (ROOT/p).read_text(encoding='utf-8')==text,p
    results={}
    for name,fn in [('generic',generic_checks),('goal',goal_checks),('source',source_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=source_record();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==reading;s=reading['source']
    old=json.loads((ROOT/'reports/prevented-attempt-v1.json').read_text(encoding='utf-8'))
    assert any(x['start']<=s['range'][0]<s['range'][1]<=x['end'] for x in old['alignment']['segments'])
    alignment=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],start=s['range'][0],end=s['range'][1],source=s['text'],
        definitions=list(MEANINGS),status='partial_explicit_attention_reading',full_semantic_equivalence=False)
    prior=json.loads((ROOT/'reports/unpermitted-undertaking-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    paths=set(build())|set(catalog().source_sha256)|set(prior['source_sha256'])|set(reading['source_sha256'])|{READING,
        'reports/unpermitted-undertaking-v1.json','scripts/compose_courageous_undertaking.py',
        'scripts/compose_careful_prevention.py','scripts/check_careful_prevention.py','tests/test_careful_prevention.py','docs/careful-prevention-v1.md'}
    return dict(status='goal_directed_attention_bound_to_actual_cause',document=FULL,**results,alignment=alignment,
        verified_full_units={'kant-1784':0,'einstein-1905':0},new_covered_characters=0,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(source_record()));report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Careful prevention and same-event attribution checked',flush=True)


if __name__=='__main__':main()
