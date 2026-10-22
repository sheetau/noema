"""Check fixed progress targets, fallible signs and fourth-stage attribution."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue,DescriptionValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_progress_indications_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,NODE_INFO,SETTINGS,SCORE_SETTINGS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts import check_progress_indications as prior

INDEX='data/semantic-review-index-v194.json';REPORT='reports/progress-indications-sentence-v1.json'
READING='data/progress-indications-sentence-reading-v1.json';DOC='docs/progress-indications-sentence-v1.md'
INVENTORY=prior.INVENTORY;SOURCES=prior.SOURCES
PRIORS=tuple('reports/'+n+'-v1.json' for n in ('present-shortfall-sentence','present-epoch-sentence','progress-indications','qualified-pursuit-opening','departure-hindrance-trend'))
DOMAIN=prior.DOMAIN;SCENES=prior.SCENES

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=prior.EXTRA):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+extra+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def normalized_code(value):
    if isinstance(value,DescriptionValue):
        node=json.loads(value.syntax)
        return (node.get('symbol',value.syntax),value.rank)
    if isinstance(value,tuple):return tuple(normalized_code(x) for x in value)
    return normalized(value)

def base(d,variant='baseline'):
    v=prior.model(d,variant=variant)
    for field,expr in (SETTINGS|SCORE_SETTINGS).items():
        name=expr.split()[1].split('[')[0]
        v[name]=v['z'+field]() if expr.startswith('p ') else v['z'+field]
    v['h26km']=v['zactual'];return v

@lru_cache(None)
def depiction_checks():
    domain=('alice','bob','area','otherarea','process','otherprocess','group');scenes=('reference','past','now')
    d=fixture(('r5vm',),'r znow[] d.q[t[k r5vm[]][k znow[]]].',extra='');rows={}
    def values(variant):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update(h26kh=lambda:'group',h26kj=lambda:'reference',znow=lambda:'now',aa=lambda p:p in ('alice','bob'),
            h246c=lambda g,p,r:(g,r)==('group','reference') and p in (() if variant=='empty_people' else ('alice','bob')),
            dd=lambda a,b:(a,b)==('past','now'),h26ly=lambda area,s:area=='area' and s in ('past','now'),
            h26lz=lambda p,a,s:p in ('alice','bob') and a=='area' and s=='now',
            ag=lambda process,a,b:process in ('process','otherprocess') and (a,b)==('past','now'),
            la=lambda p,process,a,b:(p,process) in (('alice','process'),('bob','otherprocess')) and (a,b)==('past','now'),
            dg=lambda p,s:p in ('process','otherprocess') and s=='now')
        if variant=='old_access':v['h26lz']=lambda p,a,s:p in ('alice','bob') and a=='area' and s in ('past','now')
        if variant=='no_access':v['h26lz']=lambda *a:False
        if variant=='one_person_only':v['h26lz']=lambda p,a,s:(p,a,s)==('alice','area','now')
        if variant=='foreign_area':v['h26lz']=lambda p,a,s:p in ('alice','bob') and (a,s)==('otherarea','now')
        if variant=='not_field':v['h26ly']=lambda *a:False
        if variant=='reversed':v['dd']=lambda a,b:(a,b)==('now','past')
        if variant=='foreign_transition':v['ag']=lambda p,a,b:p=='area'
        if variant=='not_affected':v['la']=lambda *a:False
        if variant=='not_occurring':v['dg']=lambda *a:False
        return v
    for variant in ('baseline','old_access','no_access','one_person_only','foreign_area','not_field','reversed','foreign_transition','not_affected','not_occurring','empty_people'):
        got=run(d,values(variant),domain,scenes);assert got==[variant=='baseline'],(variant,got);rows[variant]=got[0]
    for n in ('h26ly','h26lz','ag','la'):
        v=values('baseline');v[n]=unknown;rejects(d,v,domain,scenes)
    return dict(cases=rows,same_people_area_and_transition=True,distinct_person_processes_allowed=True,unknown_rejected=True)

@lru_cache(None)
def component_checks():
    roots=('r5vn','r5vo','r5u4','r5vp')
    q=''.join('q[t['+('s[k r5vp[]]' if n=='r5vp' else 'k '+n+'[]')+'][k z'+s+'[]]].' for s in ('actualnow','reference') for n in roots)
    d=fixture(roots,q,('r5t3','r5uh'));rows=[]
    def model(opened,declining):
        v=base(d);seen=[]
        def opening(*a):
            seen.append('opening');assert a[:8]==('alice','group','epoch','reference','actual','actualnow','topic','actualpast')
            assert a[8]('alice','work')=='process' and a[8]('bob','work')=='process';return opened
        def decline(*a):
            seen.append('decline');assert a[:5]==('group','reference','actual','actualpast','actualnow')
            obstacles,scope,bound,variables,equations,factors,worlds,matches,frames=a[5:]
            state=FunctionValue(('individual',),'truth',lambda _:False)
            assert normalized(obstacles)==('obstacle',) and scope('obstacle') and not scope('work') and bound==1
            assert normalized(variables('obstacle'))==('obstacle','factor') and not equations('obstacle','actualpast')('factor',state)
            assert factors('obstacle')=='obstacle' and worlds('obstacle','actualpast',state)=='actualpast'
            assert matches('obstacle','actualpast',state,state) and frames('actualpast')=='frame';return declining
        v.update(r5t3=opening,r5uh=decline);return v,seen
    for a,b in product((False,True),repeat=2):
        v,seen=model(a,b);got=run(d,v);assert got==[a,b,a and b,a and b]*2,got
        assert {'opening','decline'}<=set(seen);rows.append(dict(opening=a,decline=b,values=got))
    for n in ('r5t3','r5uh'):
        v,_=model(True,True);v[n]=unknown;rejects(d,v)
    return dict(combinations=rows,native_progress_conjunction_and_target_dequotation=True,all_source_fields_preserved=True,
        outer_point_does_not_rebind_current=True,boundaries=['r5t3','r5uh'],unknown_rejected=True)

@lru_cache(None)
def source_checks():
    d=fixture(('r5vq','r5vp'),'q[k zinspect[k r5vp[]]].q[t[k r5vq[]][k zactualnow[]]].q[t[k r5vq[]][k zreference[]]].',('r5ut',),extra=prior.EXTRA+'r zinspect[i d[e]] c.')
    rows=[]
    for truth in (False,True):
        v=base(d);targets=[];seen=[]
        v['zinspect']=lambda code:targets.append(code) is None
        def score(*a):
            seen.append(a)
            assert [normalized(x) for x in a[:18]]==[(expr.split()[1].split('[')[0],0) for expr in SETTINGS.values()]
            assert normalized(a[18])==('h26km',0)
            cases,selected,weight,threshold,classified,contents,linked,accessible=a[19:]
            assert normalized(cases)==prior.CASES and all(selected(c) and weight(c)==1 for c in prior.CASES) and not selected('reference') and threshold==2
            assert classified('signone','actual') and contents('signone').values==prior.content({'actual','positiveone','positivetwo'}).values
            assert targets and linked('signone',targets[0],'actualnow') and not linked('signone',targets[0],'reference')
            assert accessible('alice','signone','actualnow') and not accessible('bob','signone','actualnow')
            return truth
        v['r5ut']=score;got=run(d,v);assert got==[True,truth,truth] and seen;rows.append(got)
    v=base(d);v.update(zinspect=lambda code:True,r5ut=unknown);rejects(d,v)
    return dict(all_twenty_seven_source_arguments_checked=True,closed_setting_names_not_executed=True,constant_current_content=rows,
        boundaries=['r5ut'],unknown_rejected=True)

@lru_cache(None)
def indication_checks():
    # Execute the diagnostic and two-item requirement on five comparison cases;
    # the unchanged quantified progress implementation is a separate boundary.
    scenes=(*prior.CASES,'reference')
    args='k r5ux[] r[k h26km[]] k wa[] k h26kn[k h26km[]] '+' '.join(SCORE_SETTINGS.values())
    q='q[k zinspect[k r5vp[]]].q[k r5us['+args+']].q[t[k r5u4[]][k h26km[]]].'
    score_roots=tuple(expr.split()[1].split('[')[0] for expr in SCORE_SETTINGS.values())
    d=fixture(('r5us','r5vp','r5u4',*score_roots),q,('r5ul',),extra=prior.EXTRA+'r zinspect[i d[e]] c.');rows={}
    def values(variant):
        v=base(d,variant if variant in ('single','unclassified','actual_omitted','zero_weight','bad_threshold') else 'baseline');targets=[]
        v['h26kn']=lambda c:c
        profile=(False,True,True,False,False)
        v['r5ul']=lambda *a:FunctionValue(('situation',),'content',lambda c:Content(scenes,(profile[prior.CASES.index(c)] if c in prior.CASES else False,)*len(scenes)))
        signal_cases=('positiveone','positivetwo') if variant=='absent_actual_sign' else ('actual','positiveone','positivetwo')
        v['h26l7']=lambda item:Content(scenes,tuple(item in prior.ITEMS and c in signal_cases for c in scenes))
        v['h26mb']=lambda observer,item,point:(observer,point)==('alice','actual') and item in (prior.ITEMS[:1] if variant=='single' else prior.ITEMS)
        v['zinspect']=lambda code:targets.append((code.rank,code.syntax)) is None
        def linked(item,code,point):
            assert targets and (code.rank,code.syntax)==targets[0]
            return variant!='wrong_target' and item in prior.ITEMS and point=='actual'
        v['h26ma']=linked;return v
    for variant in ('baseline','absent_actual_sign','single','unclassified','actual_omitted','zero_weight','bad_threshold','wrong_target'):
        got=run(d,values(variant),DOMAIN,scenes);assert got==[True,variant=='baseline',False],(variant,got);rows[variant]=got
    for n in ('h26l6','h26l7','h26ma','h26mb'):
        v=values('baseline');v[n]=unknown;rejects(d,v,DOMAIN,scenes)
    return dict(cases=rows,native_ratio_and_plurality_and_exact_target=True,actual_target_false_with_clear_signs=True,
        boundaries=['r5ul: explicit finite comparison family'],unknown_rejected=True)

@lru_cache(None)
def discourse_checks():
    d=fixture(('r5vr','r5vp'),'q[k zinspect[k r5vp[]]].q[k r5vr[]].',extra='r zinspect[i d[e]] c.')
    a='author';ctx='presentation';now='now';whole=('r5vq',4);lack=('r5vg',3);opening=('r5vn',3);decline=('r5vo',3)
    expected={'h26me':{(n,a,whole,ctx) for n in ('h26mj','h26mt')},
        'h26mf':{('h26mk',a,'h26lr',lack,'h26mj',whole,('r5u6',0),ctx)},
        'h26mc':{('h26ml',a,whole,opening,('r5vm',0),('r5u6',0),ctx)},
        'h26md':{('h26mq',a,whole,decline,'h26mp','h26mq',('r5t7',3),'group','reference',ctx)},
        'h26mg':{('h26mm',a,whole,lack,('r5vn',4),ctx),('h26ms',a,whole,lack,whole,ctx)},
        'h26mh':{(n,a,whole,body,now,ctx) for n,body in (('h26mn',opening),('h26mo',decline))},
        'ue':{(x,y,ctx) for x,y in (('h26lr','h26mj'),('h26mn','h26mo'),('h26mp','h26mq'),('h26mo','h26mt'))}}
    nodes=(*NODE_INFO,'h26lr');domain=(*nodes,a,'group','other');scenes=(ctx,now,'actual','reference');target=[]
    def values(wanted,anaphora=True):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update(wa=lambda:a,h26k7=lambda:ctx,h26kh=lambda:'group',h26kj=lambda:'reference',h26km=lambda:'actual',h26kn=lambda case:now)
        v.update({n:lambda n=n:n for n in nodes})
        v.update({n:lambda *args,wanted=wanted:normalized_code(args) in wanted for n,wanted in wanted.items()})
        v['zinspect']=lambda code:target.append(normalized_code(code)) is None
        v['h26mi']=lambda *args:anaphora and normalized_code(args)==('h26mr',a,whole,target[-1],opening,decline,ctx)
        return v
    assert run(d,values(expected),domain,scenes)==[True,True];relations=1;mutations=0
    for key,tuples in expected.items():
        for row in tuples:
            wanted=deepcopy(expected);wanted[key].remove(row);assert run(d,values(wanted),domain,scenes)==[True,False];relations+=1
            for pos in range(len(row)):
                wanted=deepcopy(expected);wanted[key].remove(row);replacement=list(row);replacement[pos]='other';wanted[key].add(tuple(replacement))
                assert run(d,values(wanted),domain,scenes)==[True,False],(key,pos);mutations+=1
    assert run(d,values(expected,False),domain,scenes)==[True,False]
    for pos in range(7):
        v=values(expected)
        def wrong(*args):
            row=['h26mr',a,whole,target[-1],opening,decline,ctx];row[pos]='other';return normalized_code(args)==tuple(row)
        v['h26mi']=wrong;assert run(d,v,domain,scenes)==[True,False];mutations+=1
    for key in (*expected,'h26mi'):
        v=values(expected);v[key]=unknown;rejects(d,v,domain,scenes)
    for i,n in enumerate(nodes):
        for other in nodes[i+1:]:
            v=values(expected);v[n]=lambda other=other:other
            for key in (*expected,'h26mi'):v[key]=lambda *args:True
            assert run(d,v,domain,scenes)==[True,False]
    return dict(required_relations=relations,argument_mismatches=mutations,nodes_distinct=True,
        fourth_stage_attribution_and_mixed_stage_contrast=True,world_and_depiction_not_executed=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0014');cursor=413;clauses=[]
    for fragment,names,reading in (
      ('Allein, ',['h26mf','r5vg','r5vq'],'前文の同じ大きな不足を保ちつつ、徴候がある側を対照する。'),
      ('daß ',['r5vp','h26mi'],'後のdavonが受ける二節を徴候の対象として置く。'),
      ('jetzt ',['h26kn','h26km','h26mh'],'第一・第二文と同じ実際の現在。'),
      ('ihnen ',['h26kh','r5sc','r5ty'],'同じ現在の人々に機会が開かれる。'),
      ('doch ',['h26mg'],'不足を理由として開放まで退ける見通しに対し、開放側をなお取り立てる。'),
      ('das Feld geöffnet wird, ',['r5vk','r5vl','r5vm','r5vn','h26mc','h26mh'],'地表の活動域が開かれる描写で、同じ現在まで進む実践機会の新規開放を提示する。'),
      ('sich dahin frei zu bearbeiten, ',['r5tp','r5tq','r5tt','r5tu','r5tv','r5tz'],'同じ本人が前文の質付き宗教能力を目指して自ら学習・探究・吟味する自由な機会。実際の着手や成功は要求しない。'),
      ('und ',['r5ui','r5u4','r5vp'],'開放と障害減少を同じ現在・人々の進行として連言する。'),
      ('die Hindernisse ',['r5ud','r5uh','h26kq','h26kr'],'固定された全候補と同じ比較規則の下で離脱を妨げうる条件。'),
      ('der allgemeinen Aufklärung, ',['r5t7','r5ud','h26md'],'同じ人々における一般的な離脱の普及を妨げるもの。'),
      ('oder des Ausganges ',['h26md','r5t5','be'],'一般的啓蒙を同じ離脱として説明する。選言にしない。'),
      ('aus ihrer selbst verschuldeten Unmündigkeit, ',['be','bp','up'],'同じ本人の自己に帰責される未成熟からの離脱。別人の状態や宗教的な質条件を加えない。'),
      ('allmälig weniger werden, ',['r5ug','r5vo','h26mh'],'固定粒度の妨害件数が現在まで段階的に減る。途中の増加を排除せず、一挙の減少だけにしない。'),
      ('davon ',['r5vp','h26mi'],'直前の二節の同じ連言を指す。'),
      ('haben wir ',['r5vq','h26mb','wa'],'著者を含む話者側に同じ現在の徴候が利用可能である。'),
      ('doch ',['h26mg'],'不足があっても徴候の存在をなお保つ主節の取り立て。'),
      ('deutliche Anzeigen.',['r5ur','r5us','r5ut','r5vq','h26l2','h26l3','h26l4','h26l5','h26l6','h26l7','h26ma'],'同じ全比較範囲で識別力を持つ複数の別項目。内容・対象対応・評価を保持し、確実な真理保証へ変えない。')):
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in names),(fragment,names)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==674
    return dict(status='progress_indications_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[413,674],text=u['text'][413:674]),selection=selection_binding(catalog(),[110]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_progress_indications_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=225,semantic_equivalence_automatically_proved=False,
        primary_evidence=[dict(path=SOURCES[0],url='https://korpora.org/kant/aa08/040.html',lines='22–26',observation='AlleinからAnzeigenまでの二対象節と徴候主節、二つのdochとoderの説明。'),dict(path=SOURCES[1],observation='原刊491頁でFeld geöffnet、allmälig weniger、davonと次の時代名との区切りを確認。')],
        holistic_review=[
          '原文261文字・225非空白文字を連続した語句対応で覆った。前文の不足と本節の進行・徴候は両立する内容として同じ現在人口に保つ。',
          '第一文が述べた進行r5u4と、この文のdavonの対象r5vpは同じr5uxの実際の例を使う。開放r5vnと障害漸減r5voの連言を同じ設定で検査し、片方だけを徴候の対象へすり替えていない。',
          '場の比喩では、地表の活動域の前後と同じ人の接近利用可能性・変化過程を描写側で構成した。現実には自由な自己形成の機会を対象とし、物理的な場やそこでの仕事を事実条件に加えていない。',
          '現在の受動・変化表現を、同じ現在まで進む開放と減少の提示として保つ。将来完了・全員の同時達成・特定行為者を付け足さない。二つのdochはそれぞれ対象節と徴候主節に結ぶ。',
          '一般的啓蒙と自己に帰責される未成熟からの離脱は説明関係とした。障害評価の同じbe/r5t7を明示し、oderを二つの障害群の選言にしない。dahinの宗教的な質付き能力目標と、この離脱対象の違いを保った。',
          '明瞭な徴候には既採用の比較上の識別力という読みを適用し、全比較例の評価、正の重み、対象真偽両群、現に成り立つ複数項目と同じ話者側の利用可能性を保持した。原文のない具体的な徴候を捏造しない。対象の実際の真理を徴候から演繹しない。',
          '段階4の内容帰属と段階3の先行内容・対象を別々に保持した。有限検査は原文の自動同値証明ではなく、ここでの全語句・文全体の読解と合わせた判断である。最後の時代名と段落全体の判断は残る。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,*SOURCES,*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:110]==old.document['statements'] and len(new.document['statements'])==111
    assert all(new.entries[n]==e for n,e in old.entries.items())
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for p,i in (('data/present-epoch-sentence-reading-v1.json',108),('data/present-shortfall-sentence-reading-v1.json',109)):
        assert read(p)['selection']==selection_binding(new,[i])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    d=parse((ROOT/CORE).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        s=format_graph(d,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==d
    return dict(preserved_statements=110,added_statements=1,preserved_whole_unit_reviews=len(reviews),new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        roundtrip_scope='new core including rank 4, compact/full/v2; unchanged parent preserved by identity and pinned evidence',new_reviewed_sentence_characters=225)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('depiction',depiction_checks),('components',component_checks),('source',source_checks),('indications',indication_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*SOURCES,*PRIORS,
        'scripts/compose_progress_indications_sentence.py','scripts/check_progress_indications_sentence.py','tests/test_progress_indications_sentence.py',
        'scripts/check_progress_indications.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='progress_indications_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[110],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
