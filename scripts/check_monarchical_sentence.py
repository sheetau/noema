"""Check the tenth sentence and preserve the reviewed predecessor unchanged."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_monarchical_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,NODES,NODE_INFO,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_persistent_compact_progress import SCENES,DOMAIN,EXTRA

INDEX='data/semantic-review-index-v188.json'
REPORT='reports/monarchical-sentence-v1.json'
READING='data/monarchical-sentence-reading-v1.json'
DOC='docs/monarchical-sentence-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/personal-renunciation-sentence-v1.json','reports/monarchical-legislation-v1.json')

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+EXTRA+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def content(points):return Content(SCENES,tuple(s in points for s in SCENES))
def base(d,bindings=('alpha',)*4):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(zbindings=lambda:SequenceValue(bindings,'"individual"'),h26b7=lambda:'reference')
    return v

@lru_cache(None)
def core_checks():
    d=fixture(('r5mo','r5mt','r5mu'),''.join('q[t[k '+n+'[]][k zcandidate[]]].' for n in ('r5mo','r5mt','r5mu')),('r5mg','r5mn'));rows={}
    for limits,grounding in product((False,True),repeat=2):
        v=base(d)
        v['r5mg']=lambda r:content({'candidate'} if r=='reference' and limits else set())
        v['r5mn']=lambda r:content({'candidate'} if r=='reference' and grounding else set())
        actual=run(d,v);assert actual==[limits and grounding,limits,grounding];rows[str((limits,grounding))]=actual
    v['h26b7']=lambda:'assessment';assert run(d,v)==[False]*3
    return dict(both_halves_and_fixed_reference=rows,boundaries=['r5mg: pinned general conditional prohibitions','r5mn: pinned authority grounds and necessary will incorporation'])

@lru_cache(None)
def adapter_checks():
    rows={}
    for root,target,length in (('r5mp','r5mb',4),('r5mq','r5md',4),('r5mr','r5me',4),('r5ms','r5mm',3)):
        d=fixture((root,),'q[t[k '+root+'[k zbindings[] k zreference[]]][k zcandidate[]]].',(target,));positions=[]
        for i in range(length):
            b=tuple('beta' if j==i else 'alpha' for j in range(length));wanted=b[1:] if root=='r5mq' else b
            v=base(d,b);v[target]=lambda *a:a==(*wanted,'reference','candidate')
            assert run(d,v)==[True],(root,i)
            v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"')
            ignored=root=='r5mq' and i==0
            assert run(d,v)==[ignored],(root,i);positions.append(dict(position=i,projected_out=ignored))
        for variant in ('short','long','other_reference','other_candidate','unknown'):
            v=base(d,('alpha',)*length);wanted=('alpha',)*(length-1 if root=='r5mq' else length)
            v[target]=lambda *a:a==(*wanted,'reference','candidate')
            if variant in ('short','long'):v['zbindings']=lambda:SequenceValue(('alpha',)*(length+(-1 if variant=='short' else 1)),'"individual"')
            if variant=='other_reference':v['zreference']=lambda:'assessment'
            if variant=='other_candidate':v['zcandidate']=lambda:'outer'
            if variant=='unknown':
                v[target]=unknown
                try:run(d,v)
                except ValueError as e:assert 'Unknown' in str(e)
                else:raise AssertionError('Unknown boundary accepted')
            else:assert run(d,v)==[False],(root,variant)
        rows[root]=positions
    return dict(all_binding_positions=rows,exact_lengths_reference_candidate_and_unknown_checked=True,boundaries=['r5mb','r5md','r5me','r5mm'])

@lru_cache(None)
def conditional_checks():
    # Native implication and universal coverage; the three old semantic relations
    # have their own pinned native checks in monarchical-legislation-v1.
    d=fixture(('r5mg',),'q[t[k r5mg[k zreference[]]][k zcandidate[]]].',('r5mb','r5md','r5me'));rows={}
    for variant in ('baseline','missing_second_monarch_denial','no_people_denial','outside_scope','different_law','different_candidate'):
        v=base(d)
        v['r5mb']=lambda a,p,c,l,r,t:(p,c,l,r,t)==('alpha','beta','alpha','reference','candidate') and variant!='outside_scope'
        v['r5md']=lambda p,c,l,r,t:(p,c,l,r,t)==('alpha','beta','alpha','reference','candidate') and variant!='no_people_denial'
        def denial(a,p,c,l,r,t):
            wanted=('alpha','beta','beta' if variant=='different_law' else 'alpha','reference','outer' if variant=='different_candidate' else 'candidate')
            return (p,c,l,r,t)==wanted and not(variant=='missing_second_monarch_denial' and a=='beta')
        v['r5me']=denial
        actual=run(d,v);assert actual==[variant in ('baseline','no_people_denial','outside_scope')],(variant,actual);rows[variant]=actual[0]
    return dict(all_monarchs_same_law_and_candidate_conditional=rows,boundaries=['r5mb','r5md','r5me'],no_blanket_denial=True)

@lru_cache(None)
def discourse_checks():
    d=fixture(('r5mv',),'q[k r5mv[]].');q=lambda n:(n,2);whole=('r5mo',3);a='author';ctx='outer';ref='reference'
    expected={
      'h236i':{(node,a,(target,3),ctx) for node,target in (('h26gw','r5mo'),('h26gx','r5mt'),('h26gy','r5mu'))},
      'h222q':{('h26gz',a,'h26gd',('r5l3',1),'h26gw',('r5mo',1),('r5l4',0),ctx)},
      'h26gu':{('h26g2','h26g3',a,whole,q('r5mp'),q('r5mq'),q('r5mr'),ref,ctx)},
      'h26gv':{('h26g5',a,whole,q('r5ms'),q('r5ml'),ref,ctx)},
      'ue':{(x,y,ctx) for x,y in (('h26gd','h26gw'),('h26gx','h26gy'),('h26gz','h26g2'),('h26g2','h26g3'),('h26g3','h26g4'),('h26g4','h26g5'))}}
    missing=[(key,row) for key,values in expected.items() for row in sorted(values)]
    variants=['baseline','wrong_author','wrong_context','wrong_reference','merged_nodes','missing_reason','reverse_reason','reverse_comparison','wrong_comparison_scope','wrong_grounding_scope','wrong_grounding','unknown']
    variants+=['missing_'+str(i) for i in range(len(missing))];rows={}
    for variant in variants:
        v=base(d);v.update({n:lambda n=n:n for n in NODES});v['wa']=lambda:'other' if variant=='wrong_author' else a
        v['h255n']=lambda:'candidate' if variant=='wrong_context' else ctx
        if variant=='wrong_reference':v['h26b7']=lambda:'assessment'
        wanted=deepcopy(expected)
        if variant.startswith('missing_') and variant!='missing_reason':
            key,row=missing[int(variant.split('_')[1])];wanted[key].remove(row)
        if variant in ('reverse_comparison','wrong_comparison_scope','wrong_grounding_scope','wrong_grounding'):
            key='h26gu' if variant in ('reverse_comparison','wrong_comparison_scope') else 'h26gv';row=list(next(iter(wanted[key])))
            if variant=='reverse_comparison':row[5],row[6]=row[6],row[5]
            if variant=='wrong_comparison_scope':row[4]=q('r5ms')
            if variant=='wrong_grounding_scope':row[3]=q('r5mp')
            if variant=='wrong_grounding':row[4]=q('r5mk')
            wanted[key]={tuple(row)}
        v.update({n:lambda *args,values=values:normalized(args) in values for n,values in wanted.items()})
        def reason(author,premises,conclusion,context):
            selected=frozenset(n for n in NODES if premises(n))
            premise,conclusion_node=('h26gx','h26gy') if variant=='reverse_reason' else ('h26gy','h26gx')
            return variant!='missing_reason' and (author,selected,conclusion,context)==(a,frozenset((premise,)),conclusion_node,ctx)
        v['ud']=reason
        if variant=='merged_nodes':
            v['h26gw']=lambda:'h26gx'
            for n in (*expected,'ud'):v[n]=lambda *args:True
        if variant=='unknown':
            v['h26gu']=unknown
            try:run(d,v,(*NODES,a,'other'))
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown comparison accepted')
            continue
        actual=run(d,v,(*NODES,a,'other'));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        for n in ('h237z','h26gq','h26gr','h26gs','h26gt'):assert v[n] is unknown
    return dict(all_attributions_comparison_focus_reason_and_order=rows,every_required_relation_individually_removed=len(missing)+1,
        quoted_choices_prohibitions_wills_and_authority_not_executed=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013');cursor=2986;clauses=[]
    for fragment,names,reading in (
      ('Was ',['r5mg','r5mb'],'同じ共同体の全公的法案と全仮定候補を条件付きで量化する。'),
      ('aber ',['h222q','r5l4'],'前文の本人・後代の放棄から、同じ人々に関わる政治的決定への対照。'),
      ('nicht einmal ',['h26gu','r5mq'],'比較上の基準となる人民自身でさえ否認される場合を取り立てる。'),
      ('ein Volk ',['r45d','r5ei'],'同じ共同体の完全な人民。好都合な一部分へ狭めない。'),
      ('über sich selbst ',['r5en','r5em'],'人民自身を同じ公的決定の主体と対象にする。'),
      ('beschließen darf, ',['r5ek','r5md'],'全条項を伴う同じ規律の採択を内容とした負極性の規範要求。'),
      ('das darf ',['r5mf','r5mg'],'同じ法案・候補での人民側の禁止を前件、君主側の禁止を後件とする。'),
      ('noch weniger ',['h26gu','r5mr'],'人民自身でさえ否認されるなら、君主にはなおさら許されないという方向付き比較。'),
      ('ein Monarch ',['r2uj','r5mb','r5mc'],'同じ共同体の君主的役職を持つ人。採択の引用内で役職と実行を同一点に結ぶ。'),
      ('über das Volk ',['r5mc','r5me'],'先行の自己決定と同じ人民・共同体を、君主による決定の対象に保持する。'),
      ('beschließen; ',['r5mc','r5me'],'同じ全条項の公的採択について、君主の立場で明示的な否認を置く。'),
      ('denn ',['ud','r5mt','r5mu'],'後半の権威の根拠を、前半の制約命題の論述上の理由として提示する。'),
      ('sein gesetzgebendes Ansehen ',['r5mk','h26gs'],'同じ君主の、同じ共同体における正当な立法上の資格・権威。'),
      ('beruht ',['r5ml','r5mn','h26gt'],'後続の意志統合を規範的根拠とし、同じ権威に必要な条件に置く。十分性へ逆転しない。'),
      ('eben ',['h26gv','r5ms','r5ml'],'まさにその同じ意志統合に基づくという根拠関係への焦点。'),
      ('darauf, daß er ',['r5mj','r5ml'],'根拠の内容を後続節で特定し、erを同じ君主に固定する。'),
      ('den gesammten Volkswillen ',['r5mh','r5es','r45d'],'全人民の理性的な自己賦課の可能性に対応する公的意志。全成員と全法案で範囲を保つ。'),
      ('in dem seinigen vereinigt.',['r5mi','h26gp','h26gq','h26gr'],'同じ君主自身の公的意志へ構成的に取り込み、人民意志の全引受け可能範囲を過不足なく保持する。')):
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==3225
    pages=[p for p in read('data/personal-enlightenment-choice-reading-v1.json')['primary_pages'] if '490' in p['path']]
    assert len(pages)==1 and all(digest((ROOT/p['path']).read_bytes())==p['sha256'] for p in pages)
    for n,(span,_) in NODE_INFO.items():assert u['text'][slice(*span)].strip(),n
    assert u['text'][3153:3157]=='eben'
    return dict(status='monarchical_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[2986,3225],text=u['text'][2986:3225]),selection=selection_binding(catalog(),[105]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_monarchical_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=sum(not c.isspace() for c in u['text'][2986:3225]),
        semantic_equivalence_automatically_proved=False,original_pages=pages,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/039.html',lines='37',observation='第十文の始まりを照合。'),
            dict(url='https://korpora.org/kant/aa08/040.html',lines='1–3',observation='原刊490頁の全文を再表示して通読し、AAの続きと固定転記の綴りを区別。')],
        holistic_review=[
          '原刊490頁のWas aberからvereinigtまでを再表示して通読した。直前の本人・後代の放棄と、次文の君主が臣民へ委ねる範囲を混入せず、全語句を連続した対応表へ置いた。',
          'Was ... dasを全対象での条件として追跡した。人民側の禁止が成立しない場合に君主側の禁止を一律には要求せず、人民と君主の同じ法案・共同体・候補への対応を保持している。',
          'über sich selbstとüber das Volkの人民は同じ範囲である。異なる君主への対応も全称量化に含め、役職・採択・禁止を別にした。禁止の内容は同じ全法条項の公的な採択であり、部分条項や単なる希望には替えていない。',
          'nicht einmalとnoch wenigerを同じ比較の二側として結んだ。人民自身でさえ否認される場合を基準に、君主への許容はなおさら認められないという方向を保持し、数値や逆向き許可を補っていない。',
          'sein、er、seinigenを同じ君主へ固定した。全人民意志は既存の立法試金石に沿う規範的読解で、全成員と全法案の引受け可能範囲を過不足なく保つ。現実の全員一致や同時採択とは解していない。',
          '構成的な取り込みと全範囲の対応を別に要求し、偶然の一致で統合を満たさない。Ansehenを立法の正当な権威と読み、その成立には同じ意志統合が必要だが、統合だけから権威を十分には導かない。',
          'beruhtの規範的な根拠とdennの論述上の理由を分離した。後半を前半の理由へ向け、ebenを同じ根拠関係への焦点にした。aberは先行命題との対照に接続し、前文の判断を撤回していない。',
          '全文・二節の著者帰属と順序を保持した。引用された決定・禁止・意志統合・権威を、帰属の検証から現実の事実として実行しない。明示した解釈の下でこの203文字を確認し、第六段落全体と二作品完成は未確認のままとする。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:105]==old.document['statements'] and len(new.document['statements'])==106
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    prior=read('data/personal-renunciation-sentence-reading-v1.json');assert prior['selection']==selection_binding(new,[104])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            s=format_graph(doc,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==doc
    assert reading_record()['newly_reviewed_sentence_characters']==203
    return dict(preserved_statements=105,added_statements=1,preserved_whole_unit_reviews=len(reviews),preserved_opening_sentence_characters=2557,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,new_reviewed_sentence_characters=203)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('core',core_checks),('adapters',adapter_checks),('conditional',conditional_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*PRIORS,*(x['path'] for x in read(READING)['original_pages']),
        'data/personal-renunciation-sentence-reading-v1.json','scripts/compose_monarchical_sentence.py','scripts/check_monarchical_sentence.py',
        'tests/test_monarchical_sentence.py','scripts/check_persistent_compact_progress.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','scripts/check_covenant_nullity.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='monarchical_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[105],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
