"""Check one complete conditional epoch question, answer and attribution."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue,Message
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_present_epoch_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,NODE_INFO,SETTINGS,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts import check_progress_indications as prior

INDEX='data/semantic-review-index-v192.json';REPORT='reports/present-epoch-sentence-v1.json'
READING='data/present-epoch-sentence-reading-v1.json';DOC='docs/present-epoch-sentence-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=tuple('reports/'+n+'-v1.json' for n in ('progress-indications','departure-hindrance-trend','qualified-pursuit-opening','religious-collective-assessment','sixth-paragraph'))
SOURCES=('artifacts/judgment-performance-quality-v1/kant-aa08-040.html','artifacts/religious-collective-assessment-v1/kant-aa08-041.html','artifacts/royal-writing-oversight-v1/page-491.jpg')
DOMAIN=prior.DOMAIN;SCENES=prior.SCENES

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),native_name=False,extra=prior.EXTRA):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    text=format_graph(d,'compact')
    if native_name:
        old='r h223h[d] i[d].';assert old in text
        text=text.replace(old,'d h223h[point d] i[d][r[k zactualnow[]]].').replace('p:','p:r zactualnow[] d.',1)
        extra=extra.replace('r zactualnow[] d.','')
    return parse(text+extra+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')
def content(points):return Content(SCENES,tuple(s in points for s in SCENES))

def base(d,attained=False,checked=True,progress=True):
    v=prior.model(d,(progress,True,True,False,False))
    for field,expr in SETTINGS.items():
        name=expr.split()[1].split('[')[0]
        v[name]=v['z'+field]() if expr.startswith('p ') else v['z'+field]
    v['h26km']=v['zactual'];v['h26kc']=lambda g,r:Fraction(1,2)
    def ability(topic,anchor,code,truth):
        valid=(topic,anchor,normalized(code))==('topic','actualnow',('zactualnow',0))
        return FunctionValue(('individual',),'content',lambda p:content({'actualnow'} if valid and p in prior.PEOPLE and truth else set()))
    v['r5ta']=lambda *a:ability(*a,checked);v['r5tb']=lambda *a:ability(*a,attained)
    return v

@lru_cache(None)
def content_checks():
    roots=('r5uy','r5uz','r5u2','r5u3','r5u4','r5u5')
    q=''.join('q[t[k '+n+'[]][k zactualnow[]]].' for n in roots[2:])+'l[k r5uy[]].l[k r5uz[]].'
    d=fixture(roots,q,('r5ta','r5tb','r5ui'),True);rows=[]
    for attained,checked,progress in product((False,True),repeat=3):
        got=run(d,base(d,attained,checked,progress));positive=checked and attained;negative=checked and not attained;answer=negative and progress
        assert got[:4]==[positive,negative,progress,answer],got
        question,response=got[4:];assert isinstance(question,Message) and isinstance(response,Message)
        assert question.force=='ask' and response.force=='assert'
        assert question.content.values==(positive,)*len(SCENES) and response.content.values==(answer,)*len(SCENES)
        rows.append(dict(attained=attained,checked=checked,progress=progress,contents=got[:4]))
    contrasts={}
    for variant,want in (('other_population',[False]*4),('other_topic',[False]*4),('other_present',[False]*4),('other_start',[False,True,False,False]),('other_process',[False,True,False,False])):
        v=base(d)
        if variant=='other_population':v['h26kh']=lambda:'work'
        if variant=='other_topic':v['h26kk']=lambda:'work'
        if variant=='other_present':v['h26kn']=lambda case:'reference'
        if variant=='other_start':v['h26ko']=lambda case:'reference'
        if variant=='other_process':v['h26kp']=lambda *a:'work'
        got=run(d,v);assert got[:4]==want,(variant,got[:4]);contrasts[variant]=got[:4]
    for n in ('h26kh','h26kn','r5ta','r5ui'):
        v=base(d);v[n]=unknown;rejects(d,v)
    return dict(truth_combinations=rows,reference_contrasts=contrasts,native_source_settings_and_population_ratio=True,
        same_negative_and_progress_as_response=True,fixed_outer_point=True,boundaries=['r5ta','r5tb','r5ui'],unknown_rejected=True)

@lru_cache(None)
def setting_checks():
    # Evaluate the native closure and inspect every supplied field at its one
    # independently checked semantic boundary, including all model functions.
    q='q[t[k r5u4[]][k zactualnow[]]].';d=fixture(('r5u4',),q,('r5ui',));seen=[]
    v=base(d)
    def progress(*a):
        seen.append(a)
        assert a[:8]==('alice','group','epoch','reference','actual','actualnow','topic','actualpast')
        processes,obstacles,scope,bound,variables,equations,factors,worlds,matches,frames=a[8:]
        state=FunctionValue(('individual',),'truth',lambda _:False)
        assert processes('alice','work')=='process' and normalized(obstacles)==('obstacle',) and scope('obstacle') and not scope('work') and bound==1
        assert normalized(variables('obstacle'))==('obstacle','factor') and not equations('obstacle','actualpast')('factor',state)
        assert factors('obstacle')=='obstacle' and worlds('obstacle','actualpast',state)=='actualpast'
        assert matches('obstacle','actualpast',state,state) and frames('actualpast')=='frame'
        return True
    v['r5ui']=progress;assert run(d,v)==[True] and seen
    # The common dimension is exactly the same human population.
    d2=fixture(('r5u6',),'q[t[k r5u6[k zspeaker[]]][k zactual[]]].')
    v=base(d2);assert run(d2,v)==[True]
    v['h26kh']=lambda:'work';assert run(d2,v)==[False]
    return dict(all_eighteen_progress_settings_preserved=True,actual_case_separate_from_current_point=True,native_closed_family=True,boundaries=['r5ui'])

@lru_cache(None)
def discourse_checks():
    d=fixture(('r5u7',),'q[k r5u7[]].',extra='');a='author';ctx='presentation';q=('r5uy',3);answer=('r5uz',3)
    expected={
      'h26kz':{('h26lb',a,'h26lc',q,'h26ld',answer,('r5u5',3),ctx)},
      'h26k2':{('h26le',a,'h26k3',q,ctx)},
      'h26k5':{('h26lf',a,q,('r5u2',3),('r5u3',3),answer,ctx)},
      'h236k':{('h26ld',a,'h26lf',('r5u3',3),'h26lg',('r5u4',3),('r5u6',0),ctx)},
      'h26k4':{('h26lh',a,answer,('r5u4',3),ctx)},
      'ue':{(x,y,ctx) for x,y in (('h26jn','h26la'),('h26lb','h26lc'),('h26lc','h26ld'),('h26lf','h26lg'))}}
    nodes=(*NODE_INFO,'h26jn','h26k3');domain=(*nodes,a,'other');scenes=(ctx,'actual')
    def values(wanted):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update(wa=lambda:a,h26k7=lambda:ctx);v.update({n:lambda n=n:n for n in nodes})
        v.update({n:lambda *args,wanted=wanted:normalized(args) in wanted for n,wanted in wanted.items()});return v
    assert run(d,values(expected),domain,scenes)==[True]
    mutations=0;relations=0
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
            for key in expected:v[key]=lambda *args:True
            assert run(d,v,domain,scenes)==[False]
    v=values(expected)
    for n in ('h26kh','h26kl','h26kn','h26ku','h26j7','h26kc'):assert v[n] is unknown
    return dict(required_relations=relations,argument_mismatches=mutations,all_nodes_distinct=True,
        conditional_question_not_material_implication=True,world_contents_and_question_occurrence_not_executed=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0014');cursor=0;clauses=[]
    for fragment,names,reading in (
      ('Wenn ',['h26kz'],'質問が提出される場合という発話行為の仮定。肯定命題を前件にしない。'),
      ('denn nun ',['h26k2','h26k3'],'先行の啓蒙・自由・統治の論述を踏まえ、現在の時代評価へ進む。'),
      ('gefragt wird: ',['h26kz','r5uy'],'同じ問いを誰かが出す場合を取り上げる。実際の質問者や発話生起は補わない。'),
      ('Leben wir ',['r5sc','r5u6','h26kh'],'著者を含む同じ現在人口の生存と所属。専門家の標本や別集団にしない。'),
      ('jetzt ',['h26km','h26kn','r5uy'],'同じ実際の現在を固定し、外側の評価点で動かさない。'),
      ('in einem aufgeklärten Zeitalter? ',['r5u2','r5tj','r5tb','r5th','h26ki'],'現在を含む同じ時代で、質付き宗教能力が固定集団基準に到達しているかを問う。'),
      ('so ist die Antwort: ',['h26kz','r5uz','r5u5'],'同じ問いに対する回答として内容を示す。内容の正しさ又は歴史的対話を要求しない。'),
      ('Nein, ',['h26k5','r5u3','r5tl'],'同じ到達内容への否定。未評価を未到達の根拠にしない。'),
      ('aber ',['h236k','r5u6'],'同じ人々についての未到達と進行を対照し、論理的矛盾や前言撤回としない。'),
      ('wohl ',['h26k4'],'進行中であるという肯定側を明確に取り立てる。推測的な確率表現を加えない。'),
      ('in einem Zeitalter der Aufklärung.',['r5u4','r5ux','r5uj','r5ui'],'同じ現在人口の機会開放と離脱への障害漸減という後続の進行内容へ結ぶ。')):
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in names)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==147
    for n,(span,_) in NODE_INFO.items():assert u['text'][slice(*span)].strip(),n
    return dict(status='present_epoch_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,147],text=u['text'][:147]),selection=selection_binding(catalog(),[108]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_present_epoch_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=124,
        semantic_equivalence_automatically_proved=False,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/040.html',path=SOURCES[0],lines='17–19',observation='原刊491頁と固定転記の第一文を通読。WennからAufklärungまでの条件付き問答を同じ一文として確認。'),
            dict(path=SOURCES[2],observation='原刊のNein, aber wohlと大文字Lebenを固定転記のまま保持。')],
        holistic_review=[
          '固定転記147文字・124非空白文字を連続した語句対応で覆った。第二文にかかるDaß以下を第一文の追加的な主張として混入させていない。',
          '問いと回答を同じ閉じた設定から作った。著者を含む現在の全人口、同じ時代の期間、現在点、宗教的事項、質付き能力と普及基準を共有する。',
          '現在が既に啓蒙された状態かという問いに対するNeinを、同じ評価条件の下の未到達とした。評価不成立・人口欠落は肯定的な否定回答にしない。',
          '進行中という肯定側を後続の機会開放と障害漸減で具体化した。取り組みの目標は同じ質付き宗教能力、障害の対象は冒頭の自己に帰責される未成熟からの離脱に保つ。到達済みと進行中は両立しうる別内容だが、この回答は未到達と進行をともに述べる。',
          'Wenn ... gefragt wird ... soを発話行為上の仮定的な応答として保持した。現実の質問・返答、問いの肯定命題を前件とする物質含意を補っていない。',
          'denn nunは先行論述から次の評価へ移る接続とした。nunをjetztとは別の実時間にせず、先行の一命題から回答が演繹されるとはしていない。',
          'aberの対照は同じ人々についての二内容を保持し、wohlは進行側の肯定を取り立てると読んだ。否定の撤回・二内容の矛盾・数値的な確率は加えない。',
          '著者・第七段落専用の提示文脈・問いと回答の別箇所・先行文との本文順序を結んだ。提示関係を評価しても引用した世界内容の真偽は実行しない。',
          '原刊491頁の一文全体を通読し、採用した読みの下で未処理の語句を残していない。後続文により先行の時代語を具体化する解釈と有限モデルの限界を明示した。第七段落全体と第三文の提示の意味判断は別に残る。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,*SOURCES,*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:108]==old.document['statements'] and len(new.document['statements'])==109
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    before=read('data/royal-intervention-sentence-identifiers-v1.json');after=read(ANNOTATIONS)
    assert {k:v for k,v in before.items() if k not in ('document','document_sha256')}=={k:v for k,v in after.items() if k not in ('document','document_sha256')}
    for p in (FULL,CORE):
        d=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            s=format_graph(d,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==d
    return dict(preserved_statements=108,added_statements=1,preserved_whole_unit_reviews=len(reviews),new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,new_reviewed_sentence_characters=124)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('content',content_checks),('settings',setting_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*SOURCES,*PRIORS,
        'scripts/compose_present_epoch_sentence.py','scripts/check_present_epoch_sentence.py','tests/test_present_epoch_sentence.py',
        'scripts/compose_progress_indications.py','scripts/check_progress_indications.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='present_epoch_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[108],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
