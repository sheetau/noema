"""Check goodwill, a high evaluation, and critical framing without factivity."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_benevolent_framing import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,parent,build,closure,substitute
from scripts.check_supervisory_rank import source_values as previous_values
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_designation_order import substantive
from scripts.fetch_benevolent_framing_evidence import PATH as EVIDENCE,validate

INDEX='data/semantic-review-index-v64.json'
REPORT='reports/benevolent-framing-v1.json'
AUDIT='data/benevolent-framing-reading-v1.json'
DOC='docs/benevolent-framing-v1.md'


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def projected(roots,extra):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+extra)


def action_checks():
    d=projected(['rqyn'],'r ja[] a.r jb[] a.r jc[] a.r js[] d.q[k rqyn[k ja[] k jb[] k jc[] k js[]]].')
    rows=[]
    for bits,truth in product(product((False,True),repeat=4),(False,True,None)):
        occurs,performs,ready,aims=bits
        def willingness(actor,goal,bindings,scene):
            return ready and (actor,symbol(goal),bindings.items,scene)==('giver','rqym',('receiver',),'now')
        def purpose(actor,act,goal,bindings,scene):
            return aims and (actor,act,symbol(goal),bindings.items,scene)==('giver','act','rqym',('receiver',),'now')
        v=dict(ja=lambda:'act',jb=lambda:'giver',jc=lambda:'receiver',js=lambda:'now',
            dg=lambda a,s:occurs and (a,s)==('act','now'),df=lambda p,a,s:performs and (p,a,s)==('giver','act','now'),
            hzxq=willingness,hztl=purpose,hzxp=unknown if truth is None else lambda p,s:truth)
        actual=evaluate(d,v,('giver','receiver','act'),('now',))
        assert actual==[all(bits)];rows.append(dict(bits=list(bits),benefit_truth=truth,values=actual))
    v['jc']=lambda:'giver';assert evaluate(d,v,('giver','receiver','act'),('now',))==[False]
    v['jc']=lambda:'receiver'
    for n in ('dg','df','hzxq','hztl'):
        u=dict(v);u[n]=unknown
        try:evaluate(d,u,('giver','receiver','act'),('now',))
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return dict(combinations=rows,actual_benefit_not_required_or_executed=True,
        instrumental_goal_without_positive_readiness_rejected=True,unknown_inputs_refused=4,ordinary_evaluation=True)


def frame_checks():
    d=projected(['rqyq'],'''r jn[] a.r ja[] a.r js[] d.r world[d] c.
r claims[a a i[e] d] c.r presents[a a i[e] i[h[a a a d] c] i[h[a a a d] c] d] c.
r distances[a a i[e] i[h[a a a d] c] i[h[a a a d] c] d] c.
d jclaim[] e[b s[k world[v s]]].d jevent[a a b a c a s d] c[k world[v s]].
d jevaluation[a a b a c a s d] c[k world[v s]].
q[k rqyq[k jn[] k ja[] r[k jclaim[]] r[p jevent] r[p jevaluation] k js[] p presents p distances p claims]].''')
    rows=[]
    for claimed,presented,critical in product((False,True),repeat=3):
        v=dict(jn=lambda:'node',ja=lambda:'author',js=lambda:'text',world=unknown,
            claims=lambda n,a,p,s:claimed and (n,a,symbol(p),s)==('node','author','jclaim','text'),
            presents=lambda n,a,h,p,q,s:presented and (n,a,symbol(h),symbol(p),symbol(q),s)==('node','author','jclaim','jevent','jevaluation','text'),
            distances=lambda n,a,h,p,q,s:critical and (n,a,symbol(h),symbol(p),symbol(q),s)==('node','author','jclaim','jevent','jevaluation','text'))
        actual=evaluate(d,v,('node','author'),('text','world'))
        assert actual==[claimed and presented and critical]
        rows.append(dict(claimed=claimed,presented=presented,critical=critical,value=actual[0]))
    mismatches={}
    for name,key in [('node',('other','author','jclaim','jevent','jevaluation','text')),
            ('author',('node','other','jclaim','jevent','jevaluation','text')),
            ('claim',('node','author','other','jevent','jevaluation','text')),
            ('event',('node','author','jclaim','jevaluation','jevaluation','text')),
            ('evaluation',('node','author','jclaim','jevent','jevent','text')),
            ('context',('node','author','jclaim','jevent','jevaluation','world')),
            ('reversed',('node','author','jclaim','jevaluation','jevent','text'))]:
        u=dict(v);u['distances']=lambda n,a,h,p,q,s:(n,a,symbol(h),symbol(p),symbol(q),s)==key
        actual=evaluate(d,u,('node','author','other'),('text','world'))
        assert actual==[False];mismatches[name]=actual[0]
    for name in ('claims','presents','distances'):
        u=dict(v);u[name]=unknown
        try:evaluate(d,u,('node','author'),('text','world'))
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    prefix=deepcopy(d);prefix['statements']=[]
    multiple=parse(format_graph(prefix,'compact')+'''d jother[] e[b s[k world[v s]]].
q[k rqyq[k jn[] k ja[] r[k jother[]] r[p jevent] r[p jevaluation] k js[] p presents p distances p claims]].''')
    multiple['statements']=deepcopy(d['statements'])+multiple['statements']
    u=dict(v);u['claims']=lambda n,a,h,s:(n,a,s)==('node','author','text') and symbol(h) in ('jclaim','jother')
    assert evaluate(multiple,u,('node','author'),('text','world'))==[True,False]
    return dict(combinations=rows,mismatches=mismatches,quoted_world_facts_unknown=True,
        same_node_multiple_claims_not_conflated=True,
        sincere_praise_not_critical=True,unknown_inputs_refused=3,ordinary_evaluation=True)


def source_values(variant='baseline'):
    v=previous_values(variant);dg,df=v['dg'],v['df']
    v.update(ja=lambda:'guardone',jb=lambda:'person',jc=lambda:'appointment',js=lambda:'prior',
        dg=lambda a,s:dg(a,s) or (a,s)==('appointment','prior'),
        df=lambda a,act,s:df(a,act,s) or (a,act,s)==('guardone','appointment','prior'),
        hzxp=unknown)
    def ready(actor,goal,bindings,scene):
        return variant!='no_ready' and (actor,symbol(goal),bindings.items,scene)==(
            'other' if variant=='ready_other_actor' else 'guardone',
            'rqyo' if variant=='ready_other_goal' else 'rqym',
            ('other',) if variant=='ready_other_beneficiary' else ('person',),
            'actual' if variant=='ready_other_time' else 'prior')
    def aim(actor,act,goal,bindings,scene):
        return variant!='no_aim' and (actor,act,symbol(goal),bindings.items,scene)==(
            'guardone','appointmenttwo' if variant=='aim_other_act' else 'appointment','rqym',
            ('other',) if variant=='aim_other_beneficiary' else ('person',),'prior')
    def degree(goal,bindings,scene):
        return variant!='low_degree' and (symbol(goal),bindings.items,scene)==(
            'rqym' if variant=='degree_other_property' else 'rqyo',
            ('appointment','person','guardone') if variant=='degree_swapped_positions' else ('appointment','guardone','person'),
            'actual' if variant=='degree_other_time' else 'prior')
    v.update(hzxq=ready,hztl=aim,hzxr=degree)
    return v


def source_checks():
    d=projected(['rqyl','rqyp'],'''r ja[] a.r jb[] a.r jc[] a.r js[] d.
q[k rqyl[k ja[] k jb[] k jc[] k js[]]].q[k rqyp[k ja[] k jb[] k jc[] k js[]]].''')
    people=('guardone','person','appointment','appointmenttwo','other','guardtwo');scenes=('prior','actual','belief')
    variants=('baseline','no_ready','ready_other_actor','ready_other_goal','ready_other_beneficiary','ready_other_time',
        'no_aim','aim_other_act','aim_other_beneficiary','low_degree','degree_other_property','degree_swapped_positions',
        'degree_other_time','different_position','no_past_position')
    rows={}
    for name in variants:
        actual=evaluate(d,source_values(name),people,scenes,True)
        assert actual==[name not in ('different_position','no_past_position'),name=='baseline'],(name,actual)
        rows[name]=actual
    ordinary={}
    for name in ('baseline','no_ready','different_position'):
        actual=evaluate(d,source_values(name),people,scenes)
        assert actual==rows[name];ordinary[name]=actual
    for name in ('hzxq','hztl','hzxr'):
        v=source_values();v[name]=unknown
        try:evaluate(d,v,people,scenes,True)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    # Explicitly evaluate the descriptions with well-formed and ill-formed lists.
    q=projected(['rqym','rqyo'],'r jl[] j[a].r js[] d.q[t[k rqym[k jl[]]][k js[]]].q[t[k rqyo[k jl[]]][k js[]]].')
    bindings={}
    for name,items,expected in [('goal',('person',),[True,False]),('action',('appointment','guardone','person'),[False,True]),
            ('empty',(),[False,False]),('extra',('appointment','guardone','person','other'),[False,False]),
            ('swapped',('appointment','person','guardone'),[False,False])]:
        v=source_values();v.update(jl=lambda:SequenceValue(items,'"individual"'),hzxp=lambda p,s:(p,s)==('person','prior'))
        actual=evaluate(q,v,people,scenes,True);assert actual==expected,(name,actual);bindings[name]=actual
    return dict(contrasts=rows,ordinary_comparisons=ordinary,argument_lists=bindings,
        actual_benefit_unknown=True,unknown_inputs_refused=3,same_assumption_witness_executed=True)


def presentation_checks():
    d=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    for name in ('baseline','no_claim','no_positive_frame','no_critical_distance','other_claim','other_event','other_evaluation','other_context','no_order'):
        v={n['name']:unknown for n in d['declarations'] if n['kind']=='primitive'}
        v.update(dq=lambda:'node',wa=lambda:'author',wh=lambda:'text',t4=lambda:'payment',
            uc=lambda n,a,p,s:name!='no_claim' and (n,a,symbol(p),s)==('node','author','un' if name=='other_claim' else 'dp','text'),
            ue=lambda a,b,s:name!='no_order' and (a,b,s)==('payment','node','text'),
            hzxs=lambda n,a,h,p,q,s:name!='no_positive_frame' and (n,a,symbol(h),symbol(p),symbol(q),s)==('node','author','dp','rqyl','rqyp','text'),
            hzxt=lambda n,a,h,p,q,s:name!='no_critical_distance' and (n,a,symbol(h),symbol(p),symbol(q),s)==('node','author','dp',
                'rqyp' if name=='other_event' else 'rqyl','rqyl' if name=='other_evaluation' else 'rqyp',
                'actual' if name=='other_context' else 'text'))
        actual=evaluate(d,v,('node','author','payment'),('text','actual'))
        assert actual==[name not in ('no_claim','other_claim','no_order'),name in ('baseline','no_order')],(name,actual)
        rows[name]=actual
    return dict(contrasts=rows,all_event_and_evaluation_world_facts_unknown=True,
        positive_evaluation_and_its_negation_not_asserted=True,ordinary_evaluation=True)


def structure():
    old,new=parent(),catalog();assert len(new.document['statements'])==45 and new.document['statements'][:44]==old.document['statements']
    assert set(new.entries)-set(old.entries)=={'rqyl','rqym','rqyn','rqyo','rqyp','rqyq','rqyr','hzxp','hzxq','hzxr','hzxs','hzxt'}
    assert [n for n in old.entries if old.entries[n]['declaration']!=new.entries[n]['declaration']]==['di']
    assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in old.entries if n!='di')
    assert old.entries['di']['meaning_ja']==new.entries['di']['meaning_ja']
    helper=new.entries['rqyl']['declaration'];count=0
    def expand(node):
        nonlocal count
        if isinstance(node,list):return [expand(n) for n in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node['symbol']=='rqyl':
            count+=1;return substitute(helper['body'],{p['name']:a for p,a in zip(helper['parameters'],node['arguments'],strict=True)})
        return {k:expand(v) for k,v in node.items()}
    assert expand(new.entries['di']['declaration']['body'])==old.entries['di']['declaration']['body'] and count==1
    evaluation=new.entries['rqyp']['declaration'];base=evaluation['body']['arguments'][0]
    assert base['kind']=='call' and base['symbol']=='rqyl'
    assert base['arguments']==[dict(kind='variable',name=p['name']) for p in evaluation['parameters']]
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/path).read_text(encoding='utf-8'));ids=[s['index'] for s in r['selection']['statements']]
        a,b=selection_binding(old,ids),selection_binding(new,ids)
        assert a==r['selection'] and a['statements']==b['statements'] and a['dependencies']==b['dependencies']
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in a['dependencies'])
    for ids in ([2,3],[4,42],[6],[5,43]):
        a,b=selection_binding(old,ids),selection_binding(new,ids)
        assert a['statements']==b['statements'] and a['dependencies']==b['dependencies']
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in a['dependencies'])
    for p,s in build().items():assert (ROOT/p).read_text(encoding='utf-8')==s
    for p in (FULL,CORE,LIBRARY):
        d=parse((ROOT/p).read_text(encoding='utf-8'))
        for style in ('compact','full'):
            s=format_graph(d,style);assert parse(s)==parse(transcribe(s,alphabet='v2'))==d
    validate(json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8')))
    return dict(preserved_statements=44,new_statements=[44],refactored_definitions=['di'],refactor_expansion_exact=True,
        event_evaluation_has_identical_four_bindings=True,new_primitives=5,new_definitions=7,
        preserved_review_meanings=11,preceding_four_sentence_meanings_preserved=True,roundtrips=True)


def audit():
    inventory='artifacts/written-units-v1/kant-1784.json'
    unit=next(u for u in json.loads((ROOT/inventory).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    start=unit['text'].index('gütigst');end=start+len('gütigst')
    paths=(PARENT,PARENT_BASIS,INDEX,inventory,EVIDENCE,'artifacts/first-cause-reading-v1/page-482.jpg',
        'data/supervisory-rank-reading-v1.json','reports/supervisory-rank-v1.json')
    return dict(status='critical_benevolent_framing_not_whole_sentence_review',reviewer='assistant_review',
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],text=unit['text'][start:end]),
        reading='同じ最高位の監督を引き受けた行為を、高い程度の他者本位の好意として描写しながら、その評価から批判的に距離を置く読み。',
        evidence_limit='辞典は他者の善を図る態度、その態度に基づく振る舞い、礼儀的用法の根拠である。高い程度という読みと批判的距離は、後続の人々を依存させる叙述との対照に基づく解釈であり、辞典だけで皮肉や著者の内心を証明しない。',
        decisions=['引受け条件rqylを前版diから同じ量化位置で抽出し、展開の完全一致を確認する。',
            '評価rqypは同じ主体・対象・行為・時点に、他者の利益をそれ自体求める姿勢と同じ行為の目的、高い程度を結ぶ。',
            '好意的描写と批判的距離は別の関係で、同じ箇所・提示者・主張・出来事・評価・文脈へ結ぶ。同じ箇所の別の主張へ流用しない。',
            '引用した評価の真理も否定も実行せず、実際の悪意、過去の発話の反復、聞き手の理解を補わない。'],
        remaining=['他者の善・意向・程度・表現態度の基礎説明と皮肉の全類型',
            '集団目的の読み、schon・auch、当該文と第二段落全体','二作品全文の意味確認'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def build_report():
    results={}
    for name,fn in [('action',action_checks),('frame',frame_checks),('source',source_checks),('presentation',presentation_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=audit();assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))==r;validate_hashes(ROOT,r['source_sha256'])
    previous=json.loads((ROOT/'reports/supervisory-rank-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,previous['source_sha256'])
    paths=set(build())|set(parent().source_sha256)|set(r['source_sha256'])|set(previous['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_benevolent_framing.py','scripts/check_benevolent_framing.py','scripts/register_benevolent_framing.py',
        'scripts/fetch_benevolent_framing_evidence.py','tests/test_benevolent_framing.py'}
    return dict(status='benevolent_evaluation_with_critical_distance',document=FULL,**results,
        alignment=dict(**r['source'],definitions=['rqyl','rqym','rqyn','rqyo','rqyp','rqyq','rqyr'],status='explicit_interpretive_annotation'),
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(audit()));write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
