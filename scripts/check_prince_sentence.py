"""Check the integrated prince sentence and review every source fragment."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_prince_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,LIMITS,NODE_FRAGMENTS,parent,dependencies,build,closure
from scripts import check_prince_merit_scope as scope
from scripts import check_release_merit as prior
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/prince-sentence-v1.md';READING='data/prince-sentence-reading-v1.json';INDEX=prior.INDEX;INVENTORY=prior.INVENTORY
PRIORS=('reports/prince-merit-scope-v1.json','reports/release-merit-v1.json','reports/haughty-designation-v1.json','reports/qualified-prince-frame-v1.json','reports/prince-conclusion-v1.json','reports/religious-freedom-policy-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v1.json','artifacts/royal-writing-oversight-v1/page-491.jpg','artifacts/eighth-paragraph-source-v1/page-492.jpg',
    'artifacts/judgment-performance-quality-v1/kant-aa08-040.html','artifacts/eighth-paragraph-source-v1/kant-aa08-041.html')
DOMAIN=prior.DOMAIN;SCENES=prior.SCENES;z=prior.z;ns=prior.ns;identity=prior.identity;G=scope.G;B=scope.B
def response(side):
    names=tuple(n for n in prior.scope_names(side) if n!='hearers')
    return 'k r52z['+' '.join('r['+z(n)+']' for n in names)+' o r['+B+'] o r['+G+']]'
SAVE=scope.SAVE.replace(scope.response('current'),response('current')).replace(scope.response('post'),response('post'))
SAVE+='q[k zsavemessage[o a[r[p ro7]]['+G+']]].'
COHORT=ns(('currentgroup','postgroup','currentepoch','postepoch'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def truth_profile(d,name,primitive):
    row=next(x for x in d['declarations'] if x['name']==name);result=row['result'];sorts=[p['sort'] for p in row['parameters']]
    names=[p['name'] for p in row['parameters']]
    inner=['test'+c for c in 'abcdef'[:len(result['parameters'])]]
    # Native function/content wrappers preserve values of function sorts.
    args=[dict(kind='variable',name=n) for n in (*names,*inner,'testpoint')]
    template=parse('p:r ztruth[a d] c.d zstub[] h[a] e[i[person a][b point[k ztruth[v person v point]]]].')['declarations'][1]['body']
    template['parameters']=[dict(name=n,sort=s) for n,s in zip(inner,result['parameters'])]
    template['body']['variable']='testpoint';template['body']['body']=dict(kind='call',symbol=primitive,arguments=args)
    row['body']=template
    d['declarations'].insert(0,dict(kind='primitive',name=primitive,parameters=sorts+result['parameters']+['situation'],result='truth'))
@lru_cache(None)
def fixture(roots,query,profiles=False):
    d=deepcopy(scope.fixture(('r52x','r52g','r5yo'),''));present={x['name'] for x in d['declarations']}
    for x in catalog().document['declarations']:
        if x['name'] not in present:d['declarations'].append(deepcopy(x));present.add(x['name'])
    truth_profile(d,'r5yo','zgratitude')
    if profiles:
        truth_profile(d,'r5xj','zqualifiedfull');truth_profile(d,'r526','zconclusionfull')
        x=next(x for x in d['declarations'] if x['name']=='r5xg');x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    helpers=tuple(x['name'] for x in d['declarations'] if x['name'].startswith('z'))
    d.update(declarations=closure(d,(*roots,'r52q','r52s','r52t','r5zp',*helpers)),statements=[])
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def audience_checks():
    rows={}
    for side,point,recipient in (('current','now','hearer'),('post','later','other')):
        values=tuple(n for n in prior.scope_names(side) if n!='hearers')
        q=SAVE+''.join('q[t[c['+f+']['+ns(('holder','response','actor'))+']]['+z(point)+']].' for f in ('k r52y['+ns(values)+' '+B+' '+G+']','s['+response(side)+']'))
        d=fixture(('r52y','r52z','r52t','r5zp','r52q'),q)
        def model():
            v,saved=prior.praise_model(d,point)
            v['h234g']=lambda a,p,s,m,t:(a,p,s,identity(m),t)==('response',recipient,'actor',saved['message'],point)
            v['zsaveachievement']=lambda c:saved.update(achievement=identity(c)) is None
            return v
        v=model();assert run(d,v)==[True]*8
        for n in ('h234g','h26n3','h26n4','zgratitude','dg','f3','h256o','h26ab'):
            v=model();v[n]=lambda *a:False;assert run(d,v)==[True]*6+[False]*2,(side,n)
            v[n]=unknown;rejects(d,v)
        v=model();old=v['aa'];v['aa']=lambda p:old(p) and p!=recipient;assert run(d,v)==[True]*6+[False]*2
        v=model();v['h246c']=lambda g,p,r:r=='reference' and (g,p) in (('currentgroup','holder'),('postgroup','holder'))
        assert run(d,v)==[True]*8 # No fixed hearers group remains.
        rows[side]=dict(recipient=recipient,native_and_dequoted=True,empty_or_nonhuman_audience_rejected=True)
    return dict(cases=rows,each_utterance_can_have_different_human_recipients=True,no_fixed_cross_epoch_audience=True,
        actual_merit_not_evaluated_by_praise=True,unknown_rejected=True,
        boundary='Previously checked gratitude is a native-function truth boundary. Speech, human recipient existence, scoped response and quotations execute natively.')

@lru_cache(None)
def merit_checks():
    selected=ns(prior.VALUES)+' '+COHORT+' '+z('beneficiary')
    d=fixture(('r525','r52q','r52z'),SAVE+'q[t[c[k r525['+selected+']]['+z('actor')+']]['+z('now')+']].');rows={}
    for case in ('baseline','no_assessment','no_benefit','false_merit','false_current','false_post','empty_current','empty_post'):
        v,_=scope.base(d)
        if case=='no_assessment':v['h26n5']=lambda *a:False
        if case=='no_benefit':v['r52d']=lambda *a:False
        if case=='false_merit':v['r52c']=lambda *a:False
        if case=='false_current':v['zcriterion']=lambda *a:False
        if case=='false_post':v['zpostcriterion']=lambda *a:False
        if case in ('empty_current','empty_post'):
            old=v['zpickstandards'];side='currentgroup' if case=='empty_current' else 'postgroup'
            v['zpickstandards']=lambda *a:a[-1] if a[3]==side else old(*a)
        got=run(d,v);assert got==[True]*6+[case=='baseline'],(case,got);rows[case]=got[-1]
    for n in ('h26n5','zpickstandards','zcriterion','zpostcriterion','r52c','r52d'):
        v,_=scope.base(d);v[n]=unknown;rejects(d,v)
    # The per-person witness and generic quantifier bodies change only the
    # unused fixed-audience argument and the corresponding callee names.
    for new,old,index,renames in (('r526','r52w',10,{'r52v':'r525'}),('r527','r52x',15,{'r52w':'r526'})):
        original=deepcopy(dependencies()[0].entries[old]['declaration']);removed=original['parameters'].pop(index)['name'];original['name']=new
        def walk(x):
            if isinstance(x,list):return [walk(y) for y in x]
            if isinstance(x,dict):
                y={k:walk(v) for k,v in x.items()}
                if y.get('kind')=='call' and y.get('symbol') in renames:
                    y['symbol']=renames[y['symbol']];y['arguments']=[a for a in y['arguments'] if a!=dict(kind='variable',name=removed)]
                return y
            return x
        original['body']=walk(original['body']);copy=deepcopy(catalog().document)
        copy['declarations']=[original if x['name']==new else x for x in copy['declarations']];copy['statements']=[]
        copy.update(declarations=closure(copy,(new,)))
        normalized=parse(format_graph(copy,'compact'))
        assert next(x for x in normalized['declarations'] if x['name']==new)==catalog().entries[new]['declaration'],new
    return dict(cases=rows,same_concrete_release_and_both_criteria_after_audience_change=True,per_prince_quantifier_structure_preserved=True,
        unknown_rejected=True,boundary='Previously checked release and population frames keep exact argument boundaries; supplied evaluation, both criterion folds and new response codes execute natively. Quantifier ASTs match the pinned predecessor after only the fixed-audience argument is removed.')

@lru_cache(None)
def source_checks():
    d=fixture(('r53i','r53j','r53k'),'q[t[k r53i[]]['+z('later')+']].q[t[k r53j[]]['+z('later')+']].q[t[k r53k[]]['+z('later')+']].',True)
    domain=('actor','other','office','community','label','users','source','audience','currentgroup','postgroup','currentepoch','postepoch','topic')
    scenes=('reference','candidate','before','now','later')
    def model():
        v,_=scope.base(d)
        v.update(h26oi=lambda:'label',h26oj=lambda c:'users',h26ok=lambda:'source',h26ol=lambda c:'audience',h26oh=lambda:'reference',
            h26kh=lambda:'currentgroup',h26ki=lambda:'currentepoch',h26kk=lambda:'topic',h26km=lambda:'before',
            h26kl=lambda c:'candidate',h26kn=lambda c:'now',h26om=lambda:'postgroup',h26on=lambda:'postepoch',
            h26op=lambda o,c:'other',h26oo=lambda o,c,t:(o,c)==('office','community') and t=='before',
            h234f=lambda o,c,t:(o,c,t)==('office','community','now'))
        prefix=('label','users','source','office','currentgroup','community','topic','audience','reference')
        v['zqualifiedfull']=lambda *a:a[:9]==prefix and a[9:] in (('actor','now'),('other','now'))
        frame=('office','community','topic','reference','candidate','now','currentgroup','postgroup','currentepoch','postepoch')
        v['zconclusionfull']=lambda *a:a[:10]==frame and a[10:] in (('actor','now'),('other','now'))
        v['r5xg']=lambda *a:a[:-1]==('label','source','office','currentgroup','community','topic','reference','other') and a[-1]('before') is True
        return v
    rows={}
    for case in ('baseline','one_conclusion_missing','false_name_evaluation','no_qualified_and_false_name','no_qualified','wrong_reference_name','wrong_case_scope'):
        v=model()
        if case=='one_conclusion_missing':old=v['zconclusionfull'];v['zconclusionfull']=lambda *a:old(*a) and a[-2]!='other'
        if case in ('false_name_evaluation','no_qualified_and_false_name'):v['r5xg']=lambda *a:False
        if case in ('no_qualified','no_qualified_and_false_name'):v['zqualifiedfull']=lambda *a:False
        if case=='wrong_reference_name':old=v['zrefpick'];v['zrefpick']=lambda p,*cs:old('later' if p=='reference' else p,*cs)
        if case=='wrong_case_scope':v['h26oo']=lambda *a:False
        general=case not in ('one_conclusion_missing','wrong_reference_name');appraisal=case not in ('false_name_evaluation','no_qualified_and_false_name','wrong_case_scope')
        got=run(d,v,domain,scenes);assert got==[general,appraisal,general and appraisal],(case,got);rows[case]=got
    for n in ('zqualifiedfull','zconclusionfull','r5xg','h26oo'):
        v=model();v[n]=unknown;rejects(d,v,domain,scenes)
    return dict(cases=rows,independent_name_evaluation_not_hidden_in_antecedent=True,same_actor_office_community_and_anchor=True,
        outer_time_does_not_move_source_present=True,unknown_rejected=True,
        boundary='Full qualification/conclusion profiles and prior designation appraisal are exact argument boundaries. Source constants, name checks, role/community and person quantifiers, independence of the two assertions execute natively.')

@lru_cache(None)
def discourse_checks():
    d=deepcopy(catalog().document);d.update(declarations=closure(d,('r53l',)),statements=[]);d=parse(format_graph(d,'compact')+'q[k r53l[]].')
    nodes=(*NODE_FRAGMENTS,'h26o2','h26oi','h26m4');domain=(*nodes,'author','other');scenes=('context',)
    code=lambda n,rank=7:(rank,json.dumps(dict(kind='call',symbol=n,arguments=[]),sort_keys=True))
    fun=lambda n:(0,json.dumps(dict(kind='function_ref',symbol=n),sort_keys=True))
    normalize=lambda args:tuple((a.rank,json.dumps(json.loads(a.syntax),sort_keys=True)) if hasattr(a,'syntax') else a for a in args)
    head=code('r53a');qualified=code('r53b');whole=code('r53k');shared=('author','h26o2')
    expected={
        'h26n7':{('h26oq','author',whole,'context'),('h26oz','author',code('r53j'),'context')},
        'h26oa':{('h26or',*shared,head,code('r53c'),'context')},
        'h26ob':{('h26os',*shared,head,code('r53d'),'context'),('h26ou',*shared,qualified,code('r53f'),'context'),('h26ow',*shared,qualified,code('r53e'),'context')},
        'h26oc':{('h26ot',*shared,'h26os',head,code('r53d'),'h26oi','context')},
        'h26od':{('h26ov',*shared,'h26ou',qualified,code('r53f'),'context')},
        'h26oe':{('h26ox','author',whole,code('r53g',2),code('r53h',2),'context')},
        'h26of':{('h26oy','author',whole,fun('r5zn'),'context')},
        'ue':{(a,b,'context') for a,b in (('h26m4','h26oq'),('h26or','h26os'),('h26ou','h26ow'))}}
    def model(wanted):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update({n:lambda n=n:n for n in nodes});v.update(wa=lambda:'author',h26og=lambda:'context')
        v.update({n:lambda *a,rows=rows:normalize(a) in rows for n,rows in wanted.items()})
        v['ud']=lambda a,p,r,c:(a,r,c)==('author','h26os','context') and tuple(n for n in domain if p(n))==('h26or',)
        return v
    assert run(d,model(expected),domain,scenes)==[True];mutations=0
    for n,rows in expected.items():
        for row in rows:
            wanted=deepcopy(expected);wanted[n].remove(row);assert run(d,model(wanted),domain,scenes)==[False]
            for pos in range(len(row)):
                wanted=deepcopy(expected);wanted[n].remove(row);changed=list(row);changed[pos]='other';wanted[n].add(tuple(changed))
                assert run(d,model(wanted),domain,scenes)==[False],(n,pos);mutations+=1
        v=model(expected);v[n]=unknown;rejects(d,v,domain,scenes)
    v=model(expected);v['ud']=lambda *a:False;assert run(d,v,domain,scenes)==[False]
    for i,n in enumerate(nodes):
        for other in nodes[i+1:]:
            v=model(expected);v[n]=lambda other=other:other
            for key in expected:v[key]=lambda *a:True
            v['ud']=lambda *a:True;assert run(d,v,domain,scenes)==[False]
    for n in ('h26ni','h26nf','h26ne','h26n5','h26n6','h26n3','h26n4','h26nm'):assert model(expected).get(n,unknown) is unknown
    return dict(required_relations=sum(map(len,expected.values()))+1,argument_mismatches=mutations,
        same_three_bindings_in_premises_conclusions_and_focus=True,embedded_contrast_and_minimum_aspect_preserved=True,
        nodes_distinct=True,quoted_belief_policy_merit_gratitude_and_name_evaluation_not_executed=True,unknown_rejected=True)

FRAGMENTS=(
 ('Ein Fürst, ',['r53a','r53i'],'同じ現在における君主職・共同体と本人の一般条件。特定の王の存在を補わない。'),
 ('der es seiner nicht unwürdig findet, ',['r53c','r5wq'],'自己報告が自分の品位に反しないと受け入れる外側の本人の判断。単に悪いと思わないことではない。'),
 ('zu sagen: ',['r5wf','r5wh'],'義務判断を本人が自分について述べる行為を評価対象とし、現実の報告を要求しない。'),
 ('daß er es für Pflicht halte, ',['r5we','r5wb'],'同じ本人の義務判断を自己報告の内容に保持する。判断・義務・方針の真理は別。'),
 ('in Religionsdingen den Menschen nichts vorzuschreiben, ',['r53g','r5vw','r5v6'],'同じ現在の全人間の宗教的自己選択について、両方向の指図をしない。'),
 ('sondern ihnen darin volle Freiheit zu lassen, ',['h26oe','r53h','r5v7'],'先行の非指図を保ち、同じ人々の同じ領域の全面的な自己選択の自由を採用側として対照提示する。'),
 ('der also ',['h26ob','ud','r53d'],'同じ君主の描写から名称拒否を帰結として提示する。心理的因果や論理的必然を補わない。'),
 ('selbst den hochmüthigen Namen der Toleranz ',['h26oc','r53j','r5xg','h26oi'],'その名称さえという取り立て。高慢は同じ呼称の採用の評価で、著者に独立に帰属する。'),
 ('von sich ablehnt: ',['r5w4','r53d'],'名称の適用対象と拒否主体が同じ本人。既存の名付け事件や他人の遵守を補わない。コロンを保存。'),
 ('ist selbst aufgeklärt, ',['r53f','h26od'],'同じ当人自身の宗教的な自立的・適切・安定した判断の既有行使能力。周囲だけの啓蒙とは区別する。'),
 ('und verdient ',['r53i','r53e','r52k'],'同じ人・現在点に能力と真の功績に基づく非空の全基準による応答適合を連言する。'),
 ('von der dankbaren Welt und Nachwelt ',['r5ys','r523','r5yo'],'現在の全人間と現在時代より後の全人間の双方。感謝は値する応答内の態度と読み、実際の未来全員の心情を断言しない。'),
 ('als derjenige gepriesen zu werden, ',['r52y','r52z','r52t'],'同じ具体的功績の下で同じ対象者を強く肯定的に評価する表明。任意の肯定報告や他人の引用だけにしない。'),
 ('der zuerst das menschliche Geschlecht der Unmündigkeit, ',['r52b','r52c','r5z3','r5z4'],'同じ人類の基準を各時点の全生存者へ具体化し、積極的な政府の拘束から自由への同じ出来事を最初の達成として比較する。'),
 ('wenigstens von Seiten der Regierung, ',['h26of','r5zn'],'少なくとも政府側という肯定の下限を示す。他側面の自由又は不自由、全員の能力取得は補わない。'),
 ('entschlug, und Jedem frei ließ, ',['r52d','r5zs','r5z4'],'同じ公的行為による解放と、結果時の全員の自由。出生・死亡を扱い、人口入替だけを解放とはしない。'),
 ('sich in allem, was Gewissensangelegenheit ist, ',['r5y3','r5y5','r5zn'],'各本人の良心事項の全候補を固定し、宗教だけ又は現に成功する判断だけへ縮めない。'),
 ('seiner eigenen Vernunft zu bedienen.',['r5y4','r5y6','r5y7'],'同じ本人の自分の理性使用について、指図・介入なしの両方向の自由を保持する。正しく推論した実行や能力取得そのものは要求しない。'))
def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');cursor=0;clauses=[]
    for fragment,names,reading in FRAGMENTS:
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in names)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==573 and sum(not c.isspace() for c in u['text'][:cursor])==490
    return dict(status='qualified_prince_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,cursor],text=u['text'][:cursor]),selection=selection_binding(catalog(),[112]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_prince_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=490,semantic_equivalence_automatically_proved=False,
        primary_evidence=[dict(path=p,observation='固定原刊照合と版差の記録を保持する。補助語義と個々の意味構成の根拠は固定した先行検査・読解記録を参照。') for p in SOURCES],
        holistic_review=[
            '573文字・490非空白文字を全語句と句読点まで点検した。自己報告の品位判断、内側の義務判断、義務、宗教的自由の方針、実際の報告を分けて同じ本人へ結ぶ。',
            '主文は一般的な君主についての条件とし、同じ人物・役職・共同体を各節に保持する。個人の規範出所と政府組織を同一視せず、その本人ごとの公的な解放を結論内で選ぶ。',
            '名称の意味を裁量から宗教的自由を授ける立場として明示し、拒否を同じ呼称の自分への適用への実践的立場にする。高慢な名称の評価は独立した著者の評価として一般条件の外側に保持する。',
            'also・二つのselbst・sondern・wenigstensの提示を別に保持した。非指図を撤回せず全面的自由へ対照し、政府側という肯定下限から他側面の肯否を導かない。',
            '政府側の解放を各時点の全生存者で具体化する読みを明示した。全人類に歴史的に実現したことの実証や能力取得の断言ではなく、著者に帰属する政治的・規範的な主張内容を記述する。',
            '感謝を伴う高い評価表明に値することを、真の同じ功績と全適合基準で構成した。各発言に人間の受け手を要求するが、両時代へ固定の聴衆を加えず、未来の実際の心情や発話を要求しない。',
            '引用・量化・参照・提示の有限検査と原文の読解を合わせた判断であり、自動同値証明や独立査読ではない。原刊のコロンと頁またぎを保持し、後続文のist/sei差と第二文以後の判断は残す。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,CORE,BASIS,ANNOTATIONS,DOC,INVENTORY,*SOURCES,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert c.document['statements'][:112]==old.document['statements'] and len(c.document['statements'])==113
    assert all(c.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==17
    for row in reviews:assert row['selection']==selection_binding(c,[s['index'] for s in row['selection']['statements']])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert read(ANNOTATIONS)['entries'][:-1]==read('data/named-epoch-sentence-identifiers-v1.json')['entries']
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        s=format_graph(core,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==core
    return dict(preserved_statements=112,added_statements=1,preserved_whole_unit_reviews=17,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        new_reviewed_sentence_characters=490,roundtrip_scope='new core compact/full/v2; inherited manuscript and meanings unchanged')
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('audience',audience_checks),('merit',merit_checks),('source',source_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*SOURCES,*PRIORS,
        'scripts/compose_prince_sentence.py','scripts/check_prince_sentence.py','tests/test_prince_sentence.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_release_merit.py',
        'scripts/check_prince_merit_scope.py','scripts/check_release_merit.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='qualified_prince_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[112],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
