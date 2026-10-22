"""Check assessed large shortfall, practical possibility and sentence scope."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_present_shortfall_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,NODE_INFO,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts import check_religious_collective_assessment as religious
from scripts import check_present_epoch_sentence as first

INDEX='data/semantic-review-index-v193.json';REPORT='reports/present-shortfall-sentence-v1.json'
READING='data/present-shortfall-sentence-reading-v1.json';DOC='docs/present-shortfall-sentence-v1.md'
INVENTORY=first.INVENTORY;SOURCES=first.SOURCES
PRIORS=('reports/present-epoch-sentence-v1.json','reports/religious-collective-assessment-v1.json','reports/judgment-performance-quality-v1.json')
DOMAIN=religious.DOMAIN;SCENES=religious.SCENES;PEOPLE=religious.PEOPLE
EXTRA=religious.EXTRA+'r zagents[a a d] c.r zenabling[a a a d] c.r zeffects[a a a d d] c.'
SOURCE=religious.SOURCE+' p zagents p zenabling p zeffects'
BOUNDARIES=('r5ta','r5tb','r5tc','r5td')

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=EXTRA,native_names=False):
    d=deepcopy(catalog().document)
    if native_names:
        ds=[]
        for x in d['declarations']:
            if x['name']=='h26kb':
                text='r zone[] a.r ztwo[] a.r zchoose[a i[a] i[a]] i[a].d h26kb[matter a reference d] i[a][k zchoose[v matter r[k zone[]] r[k ztwo[]]]].'
                ds.extend(parse(format_graph(dict(d,declarations=ds,statements=[]),'compact')+text)['declarations'][len(ds):])
            else:ds.append(x)
        d['declarations']=ds
        for declaration in ('r zone[] a.','r ztwo[] a.','r zchoose[a i[a] i[a]] i[a].'):extra=extra.replace(declaration,'')
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+extra+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')

def base(d,current=(True,False,False),support=(False,True,False),assessed=(True,True,True),support_assessed=(True,True,True),threshold=Fraction(2,3),margin=Fraction(1,3)):
    v=religious.base(d,current,assessed,threshold=threshold)
    v.update(h26li=lambda g,r:margin,zagents=lambda a,p,r:(a,p,r)==('outsider','alice','now'),
        zenabling=lambda a,p,m,r:(a,p,m,r)==('outsider','alice','matter','now'),
        zeffects=lambda a,p,m,r,s:(a,p,m,r,s)==('outsider','alice','matter','now','future'))
    def activity(topic,anchor,code,agents,enabling,effects,bits):
        valid=(topic,anchor,normalized(code))==('topic','now',('znow',0))
        # Observe the actual supplied functions, not just the count of arguments.
        valid=valid and agents('outsider','alice','now') and not agents('alice','outsider','now')
        valid=valid and enabling('outsider','alice','matter','now') and effects('outsider','alice','matter','now','future')
        return FunctionValue(('individual',),'content',lambda p:religious.epoch.content({'now'} if valid and p in PEOPLE and bits[PEOPLE.index(p)] else set()))
    v['r5tc']=lambda *a:activity(*a,support_assessed);v['r5td']=lambda *a:activity(*a,support)
    return v

@lru_cache(None)
def gap_checks():
    args='k zgroup[] k zreference[] k znow[] p zassessed p zcapable'
    d=fixture(('r5vc',),'q[k r5vc['+args+']].');count=0;boundaries={}
    for theta,delta in ((Fraction(2,3),Fraction(1,3)),(Fraction(1),Fraction(1,3)),(Fraction(1,2),Fraction(1,6))):
        for bits in product((False,True),repeat=3):
            got=run(d,base(d,current=bits,threshold=theta,margin=delta))[0]
            assert got==(Fraction(sum(bits),3)+delta<=theta),(bits,theta,delta,got);count+=1
    for variant,want in (('equality',True),('smaller_gap',False),('unassessed',False),('zero_margin',False),('negative_margin',False),('too_large_margin',False),('zero_threshold',False),('above_one_threshold',False),('missing',False),('duplicate',False),('extra',False),('reordered',True),('nonhuman',False)):
        kw={}
        if variant=='smaller_gap':kw['margin']=Fraction(1,2)
        if variant=='unassessed':kw['assessed']=(True,True,False)
        if variant in ('zero_margin','negative_margin','too_large_margin'):kw['margin']={'zero_margin':Fraction(0),'negative_margin':Fraction(-1,3),'too_large_margin':Fraction(1)}[variant]
        if variant in ('zero_threshold','above_one_threshold'):kw['threshold']=Fraction(0) if variant=='zero_threshold' else Fraction(4,3)
        v=base(d,**kw)
        listed={'missing':PEOPLE[:2],'duplicate':(*PEOPLE,'alice'),'extra':(*PEOPLE,'outsider'),'reordered':tuple(reversed(PEOPLE))}
        if variant in listed:v['mp']=lambda g:SequenceValue(listed[variant],'"individual"')
        if variant=='nonhuman':v['aa']=lambda p:p in PEOPLE[:2]
        got=run(d,v);assert got==[want],(variant,got);boundaries[variant]=got[0]
    for name in ('h26li','h26kc','mp','zassessed','zcapable'):
        v=base(d);v[name]=unknown;rejects(d,v)
    return dict(distributions=count,boundaries=boundaries,native_exact_ratio=True,unknown_rejected=True)

@lru_cache(None)
def source_checks():
    roots=('r5vd','r5vf');q=''.join('q[k '+n+'['+SOURCE+']].' for n in roots)
    d=fixture(roots,q,BOUNDARIES);rows={}
    cases=(('disjoint',(True,False,False),(False,True,False),[True,False]),
        ('current_reached',(True,True,False),(False,False,False),[False,False]),
        ('support_reached',(False,False,False),(True,True,False),[False,True]),
        ('both_reached',(True,True,False),(True,True,False),[False,True]),
        ('neither',(False,False,False),(False,False,False),[True,False]))
    for name,a,b,want in cases:
        got=run(d,base(d,a,b));assert got==want,(name,got);rows[name]=got
    # Union would reach 2/3 in the disjoint case; each side is only 1/3.
    assert sum(a or b for a,b in zip(cases[0][1],cases[0][2]))==2
    for name in ('current_unassessed','support_unassessed','wrong_topic','wrong_now','wrong_group','wrong_agents','wrong_method','wrong_result'):
        kw={}
        if name=='current_unassessed':kw['assessed']=(True,True,False)
        if name=='support_unassessed':kw['support_assessed']=(True,True,False)
        v=base(d,**kw)
        if name in ('wrong_topic','wrong_now','wrong_group'):v[{'wrong_topic':'ztopic','wrong_now':'znow','wrong_group':'zgroup'}[name]]=lambda:'outside' if name=='wrong_now' else 'outsider'
        if name in ('wrong_agents','wrong_method','wrong_result'):v[{'wrong_agents':'zagents','wrong_method':'zenabling','wrong_result':'zeffects'}[name]]=lambda *a:False
        got=run(d,v);assert got==[False,False],(name,got);rows[name]=got
    v=base(d,support=(True,True,False),margin=Fraction(0));assert run(d,v)==[False,True]
    for name in ('r5ta','r5tc','h26li','zagents','zenabling','zeffects'):
        v=base(d);v[name]=unknown;rejects(d,v)
    return dict(cases=rows,positive_possibility_independent_of_gap_parameter=True,disjunction_not_population_union=True,
        native_frame_and_population=True,boundaries=list(BOUNDARIES),unknown_rejected=True)

@lru_cache(None)
def native_support_checks():
    quality=religious.quality;prior=quality.prior
    args='k ztopic[] k zanchor[] r[k zqualitycontext[]] p zagents p zenabling p zeffects'
    q=''.join('q[t[c[k '+n+'['+args+']][k zperson[]]][k zcontext[]]].' for n in ('r5tc','r5td'))
    d=fixture(('r5tc','r5td'),q,extra=prior.prior.EXTRA+prior.REFERENCES,native_names=True);rows={}
    for variant,want in (('baseline',[True,True]),('quality_failure',[True,False]),('unassessed_after',[False,False]),('empty_agents',[True,False]),('no_method',[True,False]),('foreign_result',[False,False])):
        v=quality.ability_model(d,variant)
        v.update(h26j7=lambda topic,r:(topic,r)==('one','now'),h26ka=v['ztopics'])
        if variant=='empty_agents':v['zagents']=lambda *a:False
        if variant=='no_method':v['zenabling']=lambda *a:False
        if variant=='foreign_result':
            effects=v['zeffects'];v['zeffects']=lambda a,p,m,s,t:p=='other' and effects(a,'person',m,s,t)
        got=run(d,v,prior.DOMAIN,prior.SCENES);assert got==want,(variant,got);rows[variant]=got
    v=quality.ability_model(d);v.update(h26j7=lambda topic,r:(topic,r)==('one','now'),h26ka=v['ztopics'],zagents=unknown)
    rejects(d,v,prior.DOMAIN,prior.SCENES)
    return dict(cases=rows,native_religious_scope_names_quality_and_support=True,known_empty_distinct_from_unknown=True,
        all_results_assessed=True,same_person_and_current_preserved=True)

@lru_cache(None)
def settings_checks():
    # Close the actual source setting without executing the costly ability body.
    d=fixture(('r5vg',),'q[t[k r5vg[]][k zactualnow[]]].',('r5vd',),extra=first.prior.EXTRA)
    v=first.base(d);seen=[]
    v.update(h26lj=lambda a,p,r:(a,p,r)==('alice','bob','actualnow'),
        h26lk=lambda a,p,m,r:(a,p,m,r)==('alice','bob','work','actualnow'),
        h26ll=lambda a,p,m,r,s:(a,p,m,r,s)==('alice','bob','work','actualnow','reference'))
    # Supply the closed actual-current name through a native fixture definition.
    text=format_graph(d,'compact').replace('r zactualnow[] d.','').replace('p:','p:r zactualnow[] d.',1)
    text=text.replace('r h223h[d] i[d].','d h223h[point d] i[d][r[k zactualnow[]]].')
    d=parse(text)
    def checked(*args):
        seen.append(args);assert args[:7]==('alice','group','epoch','reference','actual','actualnow','topic')
        assert normalized(args[7])==('zactualnow',0)
        agents,methods,effects=args[8:]
        assert agents('alice','bob','actualnow') and not agents('bob','alice','actualnow')
        assert methods('alice','bob','work','actualnow') and effects('alice','bob','work','actualnow','reference')
        return True
    v['r5vd']=checked;assert run(d,v,first.DOMAIN,first.SCENES)==[True] and seen
    d2=fixture(('r5vi',),'q[t[k r5vi[]][k zactualnow[]]].q[t[k r5vi[]][k zreference[]]].',('r5u2','r5vf'),extra=first.prior.EXTRA)
    text=format_graph(d2,'compact').replace('r zactualnow[] d.','').replace('p:','p:r zactualnow[] d.',1)
    d2=parse(text.replace('r h223h[d] i[d].','d h223h[point d] i[d][r[k zactualnow[]]].'))
    for a,b in product((False,True),repeat=2):
        v2=first.base(d2);v2.update({n:v[n] for n in ('h26lj','h26lk','h26ll')})
        v2['r5u2']=lambda:first.content(set(first.SCENES) if a else set())
        v2['r5vf']=lambda *args:checked(*args) and b
        assert run(d2,v2,first.DOMAIN,first.SCENES)==[a or b,a or b]
    return dict(all_source_arguments_bound=True,boundaries=['r5vd','r5u2','r5vf'],world_content_evaluated_at_fixed_current=True,
        collective_disjunction_combinations=4,alternative_evaluation_point_preserves_fixed_current=True)

@lru_cache(None)
def discourse_checks():
    d=fixture(('r5vj',),'q[k r5vj[]].',extra='');a='author';ctx='presentation';now='now'
    whole=('r5vg',3);one=('r5u2',3);two=('r5vh',3);alt=('r5vi',3)
    expected={'h236i':{(n,a,whole,ctx) for n in ('h26lr','h26lw')},
        'h26lm':{('h26ls',a,whole,alt,now,ctx)},'h26ln':{('h26lt',a,whole,one,now,ctx)},
        'h26lq':{('h26lu',a,whole,one,two,alt,ctx)},'h26lo':{('h26lx',a,whole,one,two,ctx)},
        'h26lp':{('h26lv',a,whole,alt,now,ctx)},
        'ue':{(x,y,ctx) for x,y in (('h26la','h26lr'),('h26lt','h26lu'),('h26lu','h26lw'))}}
    nodes=(*NODE_INFO,'h26la');domain=(*nodes,a,'other');scenes=(ctx,now,'actual')
    def values(wanted):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update(wa=lambda:a,h26k7=lambda:ctx,h26km=lambda:'actual',h26kn=lambda case:now if case=='actual' else ctx)
        v.update({n:lambda n=n:n for n in nodes})
        v.update({n:lambda *args,wanted=wanted:normalized(args) in wanted for n,wanted in wanted.items()});return v
    assert run(d,values(expected),domain,scenes)==[True];mutations=0;relations=0
    for key,tuples in expected.items():
        for row in tuples:
            wanted=deepcopy(expected);wanted[key].remove(row);assert run(d,values(wanted),domain,scenes)==[False];relations+=1
            for pos in range(len(row)):
                wanted=deepcopy(expected);wanted[key].remove(row);replacement=list(row);replacement[pos]='other';wanted[key].add(tuple(replacement))
                assert run(d,values(wanted),domain,scenes)==[False],(key,pos);mutations+=1
    for key in expected:
        v=values(expected);v[key]=unknown;rejects(d,v,domain,scenes)
    for i,n in enumerate(nodes):
        for other in nodes[i+1:]:
            v=values(expected);v[n]=lambda other=other:other
            for key in expected:v[key]=lambda *a:True
            assert run(d,v,domain,scenes)==[False]
    return dict(required_relations=relations,argument_mismatches=mutations,nodes_distinct=True,
        quoted_contents_not_executed=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0014');cursor=148;clauses=[]
    for fragment,names,reading in (
      ('Daß ',['r5vg','r5vi','h26lq'],'後続のdaranが受ける二つの到達条件を不足の対象として置く。独立の肯定断言にしない。'),
      ('die Menschen, ',['r5te','r5sc','h26kh'],'第一文と同じ現在の人々の完全な有限母集団。'),
      ('wie die Sachen jetzt stehen, ',['h26lm','h26lk','h26ll'],'現在の事情の下で評価し、別の将来の事情だけで可能な方法を借りない。'),
      ('im Ganzen genommen, ',['r5vb','r5vc','r5tg'],'固定集団の普及割合と固定基準による全体評価。全員一致とはしない。'),
      ('schon im Stande wären, ',['h26ln','r5u2','r5ta','r5tb'],'現在に既に質付き能力があるという候補を、外側の大きな不足の対象にする。'),
      ('oder darin auch nur gesetzt werden könnten, ',['h26lq','h26lo','r5vh','r5tc','r5td'],'同じ能力状態へ置かれうる可能性まで要求を下げる選択肢。人ごとに同じ一結果を要求し、実際の支援や成功保証にはしない。'),
      ('in Religionsdingen ',['r5s6','h26j7','h26ka','h26kb'],'元の宗教主題に属する本人の全関連事項を保つ。'),
      ('sich ihres eigenen Verstandes ',['r5ta','r5tb','r5tc','r5td'],'同じ本人が自分自身の理解力を使う能力。支援者や別人の理解力へ移さない。'),
      ('ohne Leitung eines Andern ',['r5sv','r5ss'],'その判断で他者の指導を必要としない。能力を得る条件整備まで禁じない。'),
      ('sicher und gut zu bedienen, ',['r5sv','r5ss','r5sy','r5sz','r5s2','r5s3'],'同じ使用の確かさと適切さを実判断の質・安定性・適用条件に保持する。主観的自信だけにしない。'),
      ('daran fehlt ',['r5vd','r5ve','r5vg','r5vi'],'前の二つの集団的到達条件がそれぞれ不足する。両側の成功者を先に混ぜない。'),
      ('noch ',['h26lp'],'解消を見込む進行の中でなお残る不足。将来の必ずの達成を補わない。'),
      ('sehr viel.',['h26li','r5va','r5vc'],'到達閾値から正の文脈的最小幅以上の隔たりがある。評価不明やわずかな未到達と区別する。')):
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in names)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==412
    return dict(status='present_shortfall_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[148,412],text=u['text'][148:412]),selection=selection_binding(catalog(),[109]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_present_shortfall_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=223,
        semantic_equivalence_automatically_proved=False,
        primary_evidence=[dict(path=SOURCES[0],url='https://korpora.org/kant/aa08/040.html',lines='19–22',observation='同じ人々への現在能力・可能性を不足の対象にする第二文全体。'),dict(path=SOURCES[2],observation='原刊491頁のDaßからsehr vielまでと前後の問答・Alleinの接続を通読。')],
        holistic_review=[
          '原文264文字・223非空白文字の全語句を連続して対応づけた。第一文の到達状態、第二文の不足、第三文の進行の対照を混ぜず、同じ人々・現在・宗教的能力へ結んだ。',
          'die Menschen/im Ganzen genommenに有限の完全母集団と同じ割合尺度を採る。sehr vielに数値を捏造せず、事前に定める文脈的な最小隔たりを与えるという解釈条件を明記した。',
          'oderの両側は集団条件の選言であり、その両方に大きな不足がある。既有能力の人と支援可能な人を和集合として数えない。この区別を交わらない成功者の反例で点検した。',
          'wären/könntenを不足の対象とされた到達と実践的可能性として保持した。同じ現在の事情の下の方法と結果を使い、本人の全関連事項が一結果で成立することを要求する。全員同時の一政策・実施済み・必然的成功は加えない。',
          '質付き能力の実定義を継承し、同じ宗教主題・本人の理解力・他者の指導なし・確かで適切な使用を保った。未知の評価を不足へ変換せず、既知の空の支援範囲と区別する。',
          '現在限定、schon、auch nur、nochを別の提示関係として同じ全体内容へ結んだ。程度を下げた焦点を二条件の無条件な論理的含意とせず、現在不足を永続的不能としない。',
          '著者帰属は引用した内容の真理を要求しない。原刊と固定転記の一文全体の読解を、有限モデルの成功とは別の根拠として記録する。第三文・時代名と第七段落全体の意味確認は残る。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,*SOURCES,*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:109]==old.document['statements'] and len(new.document['statements'])==110
    assert all(new.entries[n]==e for n,e in old.entries.items())
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    assert first.read(first.READING)['selection']==selection_binding(new,[108])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    d=parse((ROOT/CORE).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        s=format_graph(d,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==d
    return dict(preserved_statements=109,added_statements=1,preserved_whole_unit_reviews=len(reviews),new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        roundtrip_scope='new core in compact/full and v2; unchanged parent checked by identity and pinned evidence',new_reviewed_sentence_characters=223)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('gap',gap_checks),('source',source_checks),('native_support',native_support_checks),('settings',settings_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*SOURCES,*PRIORS,
        'scripts/compose_present_shortfall_sentence.py','scripts/check_present_shortfall_sentence.py','tests/test_present_shortfall_sentence.py',
        'scripts/check_religious_collective_assessment.py','scripts/check_present_epoch_assessment.py','scripts/check_present_epoch_sentence.py',
        'scripts/check_judgment_performance_quality.py','scripts/check_qualified_judgment.py','scripts/check_topical_standing.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='present_shortfall_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[109],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
