"""Check the eleventh sentence without executing quoted policies or duties."""
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
from scripts.compose_monarchical_religion_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,NODES,NODE_INFO,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_persistent_compact_progress import SCENES,DOMAIN,EXTRA

INDEX='data/semantic-review-index-v189.json'
REPORT='reports/monarchical-religion-sentence-v1.json'
READING='data/monarchical-religion-sentence-reading-v1.json'
DOC='docs/monarchical-religion-sentence-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/monarchical-sentence-v1.json','reports/civic-oversight-v1.json','reports/personal-religious-remit-v1.json','reports/salvation-work-protection-v1.json')

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
def run(d,v,domain=(*DOMAIN,'author','other')):return evaluate(d,v,domain,SCENES,True)
def content(points):return Content(SCENES,tuple(s in points for s in SCENES))
def base(d,bindings=('alpha',)*3):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(zbindings=lambda:SequenceValue(bindings,'"individual"'),h26hz=lambda:'reference',wa=lambda:'author',h255n=lambda:'outer')
    return v
def rejects_unknown(d,v,domain=(*DOMAIN,'author','other')):
    try:run(d,v,domain)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def conditional_checks():
    d=fixture(('r5op',),'q[k r5op[k zalpha[] k zbeta[] k zalpha[] k zreference[] k zcandidate[]]].',('r5nh','r5ol','r5n2','r5oj'));rows={}
    for oversight,permission,no_remit,duty in product((False,True),repeat=4):
        v=base(d)
        v['r5nh']=lambda b,r:content({'candidate'} if normalized((b,r))==(('alpha','beta','alpha'),'candidate') and oversight else set())
        v['r5ol']=lambda *a:a==('alpha','beta','candidate') and permission
        v['r5n2']=lambda b,r:content({'candidate'} if normalized((b,r))==(('alpha','beta'),'candidate') and no_remit else set())
        v['r5oj']=lambda *a:a==('author','alpha','beta','candidate','candidate') and duty
        actual=run(d,v);assert actual==[(not oversight or permission) and no_remit and duty]
        rows[str((oversight,permission,no_remit,duty))]=actual[0]
    v['r5oj']=unknown;rejects_unknown(d,v)
    return dict(native_conditional_and_independent_remits=rows,inner_reference_is_same_case=True,unknown_rejected=True,
        boundaries=['r5nh: effective oversight','r5ol: permission tested natively below','r5n2: personal religious non-remit','r5oj: protective remit and requirement'])

@lru_cache(None)
def permission_checks():
    d=fixture(('r5ol',),'q[k r5ol[k zalpha[] k zbeta[] k zcandidate[]]].',('r2ui',));rows={}
    for variant in ('baseline','no_permission','negative_requirement','wrong_author','wrong_actor','wrong_office','wrong_community','wrong_family','wrong_bindings','wrong_reference','wrong_point','unknown'):
        v=base(d);v['h234f']=lambda *a:a==('beta','beta','candidate')
        v['r2ui']=lambda *a:a==('alpha','beta','alpha' if variant=='wrong_community' else 'beta','candidate')
        expected=['author','alpha','beta',('r5nz',1),('alpha','beta'),'candidate',True,'candidate']
        changes={'wrong_author':(0,'alpha'),'wrong_actor':(1,'beta'),'wrong_office':(2,'alpha'),'wrong_family':(3,('r5n2',1)),
            'wrong_bindings':(4,('beta','alpha')),'wrong_reference':(5,'reference'),'wrong_point':(7,'assessment')}
        if variant in changes:i,value=changes[variant];expected[i]=value
        v['h245c']=lambda *a:variant!='no_permission' and normalized(a)==tuple(expected)
        negative=('author','alpha','beta',('r5nz',1),('alpha','beta'),'candidate',False,'candidate')
        v['h237z']=lambda *a:variant=='negative_requirement' and normalized(a)==negative
        if variant=='unknown':v['h245c']=unknown;rejects_unknown(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert v['h26hm'] is unknown and v['h26ho'] is unknown
    return dict(native_permission_without_conflicting_negative_requirement=rows,quoted_nonintervention_not_executed=True,unknown_rejected=True,boundaries=['r2ui: same office holding'])

@lru_cache(None)
def scope_checks():
    d=fixture(('r5ok',),'q[k r5ok[k zalpha[] k zbeta[] k zalpha[] k zreference[] k zcandidate[]]].',('r2uj','r5m5'));frame={}
    for variant in ('baseline','no_case','no_role','no_order','other_general_reference','other_inner_reference','unknown'):
        v=base(d)
        v['h26hy']=lambda *a:variant!='no_case' and a==('alpha','beta','alpha','assessment' if variant=='other_general_reference' else 'reference','candidate')
        v['r2uj']=lambda *a:variant!='no_role' and a==('alpha','beta','candidate')
        v['r5m5']=lambda *a:variant!='no_order' and a==('alpha','beta','reference' if variant=='other_inner_reference' else 'candidate')
        if variant=='unknown':v['h26hy']=unknown;rejects_unknown(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'];frame[variant]=actual[0]
    roots=('r5oq','r5or','r5os','r5ot');boundaries=('r5ok','r5om','r5on','r5oo')
    d=fixture(roots,''.join('q[t[k '+n+'[]][k zouter[]]].' for n in roots),boundaries);rows={}
    for variant in ('baseline','missing_second_actor_permission','missing_second_case_remit','missing_second_case_duty','outside_scope','wrong_general_reference'):
        v=base(d)
        v['r5ok']=lambda a,c,o,r,p:variant!='outside_scope' and (c,o,r)==('beta','alpha','reference') and p in ('candidate','assessment')
        v['r5om']=lambda a,c,o,r,p:(c,o,r)==('beta','alpha','reference') and not(variant=='missing_second_actor_permission' and a=='beta')
        v['r5on']=lambda a,c,p:c=='beta' and not(variant=='missing_second_case_remit' and p=='assessment')
        v['r5oo']=lambda a,c,p:c=='beta' and not(variant=='missing_second_case_duty' and p=='assessment')
        if variant=='wrong_general_reference':
            v['h26hz']=lambda:'before'
            # Keep this scope populated to test propagation to the conditional.
            v['r5ok']=lambda a,c,o,r,p:(c,o)==('beta','alpha') and p=='candidate'
        actual=run(d,v)
        expected=[variant not in ('missing_second_actor_permission','missing_second_case_remit','missing_second_case_duty','wrong_general_reference'),
            variant not in ('missing_second_actor_permission','wrong_general_reference'),variant!='missing_second_case_remit',variant!='missing_second_case_duty']
        assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(native_scope=frame,all_actors_and_cases=rows,boundaries=list(boundaries)+['r2uj','r5m5'],no_oversight_or_policy_success_in_scope=True)

@lru_cache(None)
def adapter_checks():
    rows={}
    for root,target in (('r5ou','r5ok'),('r5ov','r5nh'),('r5ow','r5ol'),('r5ox','r5on'),('r5oy','r5oo'),('r5o2','r5nz')):
        d=fixture((root,),'q[t[k '+root+'[k zbindings[] k zreference[]]][k zcandidate[]]].',(target,));positions=[]
        for i in range(3):
            b=tuple('beta' if j==i else 'alpha' for j in range(3));v=base(d,b)
            if root=='r5ou':v[target]=lambda *a:a==(*b,'reference','candidate')
            elif root in ('r5ov','r5o2'):
                wanted=b if root=='r5ov' else b[:2]
                v[target]=lambda seq,r:content({'candidate'} if normalized((seq,r))==(wanted,'candidate') else set())
            else:v[target]=lambda *a:a==(*b[:2],'candidate')
            assert run(d,v)==[True],(root,i)
            v['zbindings']=lambda:SequenceValue(('alpha',)*3,'"individual"')
            ignored=i==2 and root not in ('r5ou','r5ov')
            assert run(d,v)==[ignored],(root,i);positions.append(dict(position=i,projected_out=ignored))
        for variant in ('short','long','other_reference','other_point','unknown'):
            b=('alpha',)*3;v=base(d,b)
            if root=='r5ou':v[target]=lambda *a:a==(*b,'reference','candidate')
            elif root in ('r5ov','r5o2'):
                wanted=b if root=='r5ov' else b[:2]
                v[target]=lambda seq,r:content({'candidate'} if normalized((seq,r))==(wanted,'candidate') else set())
            else:v[target]=lambda *a:a==(*b[:2],'candidate')
            if variant in ('short','long'):v['zbindings']=lambda:SequenceValue(('alpha',)*(2 if variant=='short' else 4),'"individual"')
            if variant=='other_reference':v['zreference']=lambda:'assessment'
            if variant=='other_point':v['zcandidate']=lambda:'outer'
            if variant=='unknown':v[target]=unknown;rejects_unknown(d,v);continue
            assert run(d,v)==[variant=='other_reference' and root!='r5ou'],(root,variant)
        rows[root]=positions
    return dict(exact_three_positions=rows,general_reference_only_selects_scope=True,inner_reference_is_evaluation_case=True,unknown_rejected=True)

@lru_cache(None)
def discourse_checks():
    d=fixture(('r5o4',),'q[k r5o4[]].');q=lambda n:(n,2);whole=('r5oq',3);a='author';ctx='outer';ref='reference'
    expected={
      'h236i':{(node,a,(target,3),ctx) for node,target in (('h26h5','r5oq'),('h26h6','r5or'),('h26ia','r5os'),('h26ib','r5ot'))},
      'h26h2':{('h26ic','h26h7',a,whole,q('r5ou'),q('r5ov'),q('r5ow'),ref,ctx)},
      'h26h3':{('h26id',a,whole,q('r5ou'),q('r5ov'),q('r5o2'),ref,ctx)},
      'h26h4':{('h26ie',a,whole,q('r5ou'),q('r5ow'),q('r5o2'),ref,ctx)},
      'h236k':{('h26if',a,'h26ia',('r5os',3),'h26ib',('r5ot',3),('r5o3',0),ctx)},
      'h26ig':{('h26if',a,whole,q('r5ou'),q('r5oy'),ref,ctx)},
      'ue':{(x,y,ctx) for x,y in (('h26gw','h26h5'),('h26h7','h26ia'),('h26ia','h26ib'),('h26ic','h26id'),('h26id','h26ie'),('h26ie','h26if'))}}
    missing=[(key,row) for key,values in expected.items() for row in sorted(values)];rows={}
    variants=['baseline','wrong_author','wrong_context','wrong_reference','merged_nodes','reverse_condition','wrong_remaining','wrong_minimal_response','reverse_contrast','wrong_focus','unknown']+['missing_'+str(i) for i in range(len(missing))]
    for variant in variants:
        v=base(d);v.update({n:lambda n=n:n for n in NODES});wanted=deepcopy(expected)
        if variant=='wrong_author':v['wa']=lambda:'other'
        if variant=='wrong_context':v['h255n']=lambda:'candidate'
        if variant=='wrong_reference':v['h26hz']=lambda:'assessment'
        if variant.startswith('missing_'):key,row=missing[int(variant.split('_')[1])];wanted[key].remove(row)
        changes={'reverse_condition':'h26h2','wrong_remaining':'h26h3','wrong_minimal_response':'h26h4','reverse_contrast':'h236k','wrong_focus':'h26ig'}
        if variant in changes:
            key=changes[variant];row=list(next(iter(wanted[key])))
            if variant=='reverse_condition':row[5],row[6]=row[6],row[5]
            if variant in ('wrong_remaining','wrong_minimal_response'):row[5]=q('r5ov')
            if variant=='reverse_contrast':row[2:6]=row[4:6]+row[2:4]
            if variant=='wrong_focus':row[4]=q('r5ox')
            wanted[key]={tuple(row)}
        v.update({n:lambda *args,values=values:normalized(args) in values for n,values in wanted.items()})
        if variant=='merged_nodes':
            v['h26h5']=lambda:'h26h6'
            for n in expected:v[n]=lambda *args:True
        if variant=='unknown':v['h26h2']=unknown;rejects_unknown(d,v,(*NODES,a,'other'));continue
        actual=run(d,v,(*NODES,a,'other'));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        for n in ('h237z','h245c','h26hy','h26hf','h26hx'):assert v[n] is unknown
    return dict(attribution_focus_residual_scope_contrast_and_order=rows,every_required_relation_individually_removed=len(missing),quoted_policies_and_duties_not_executed=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013');cursor=3226;clauses=[]
    for fragment,names,reading in (
      ('Wenn ',['r5om','r5ok'],'一般的な全仮定場面での条件。後半二職責をこの前件の中へ狭めない。'),
      ('er ',['r2uj','r5ok'],'直前と同じ君主的役職にある人と共同体。'),
      ('nur ',['h26h2','r5ov','r5ow'],'この監督条件さえ満たせばよいという十分条件の焦点。'),
      ('darauf sieht, daß ',['r5nf','r5ng','r5nh'],'同じ秩序条件への注意と目的、成立又は維持への実効的寄与。'),
      ('alle ',['r5nd'],'同じ候補枠の全改善。実施されるものについて秩序保持を要求。'),
      ('wahre oder vermeinte Verbesserung ',['r5mw','r5m4','r5nc'],'同じ対象の真の改善又は本人が改善と信じるもの。信念の真理を要求しない。'),
      ('mit der bürgerlichen Ordnung zusammen bestehe; ',['r5m5','r5m6','r5nd'],'非空の市民的秩序の全条件が実施下で保たれる。全提案の実施可能性とはしない。'),
      ('so kann er ',['r5om','r5ol','r37c'],'同じ前件に対応する、著者を評価源とした君主の衝突のない規範的許容。'),
      ('seine Unterthanen ',['r5ni','r5nx'],'同じ君主・共同体の制度的服属にある全臣民。'),
      ('übrigens ',['h26h3','r5ou','r5ov','r5o2'],'秩序への監督を留保した残余の宗教的自己選択。'),
      ('nur ',['h26h4','r5ow','r5o2'],'さらに宗教的な指図や介入を加えず本人に委ねればよいという応答。'),
      ('selbst machen lassen, ',['r5nz','r5ns','r5nu','r5nv'],'本人の選択に宗教上の命令・禁止や権威的な代行・妨害を加えない内容。許可から実行は導かない。'),
      ('was sie um ihres Seelenheils willen zu thun nöthig finden; ',['r5nj','r5nl','r5no','r5nq'],'本人自身の救済を目的に必要だと本人が判断する営み。客観的必要性や現実の救済と区別。'),
      ('das geht ihn nichts an, ',['r5n2','r5on','r5os'],'その宗教的必要性を本人に代わって決める同じ君主の公的所管はない。'),
      ('wohl aber ',['h236k','h26ig','r5o3','r5oy'],'同じ君主の職責を観点に所管外と積極的職責を対照し、後者を肯定的に取り立てる。'),
      ('zu verhüten, daß nicht einer den andern gewaltthätig hindere, ',['r5oe','r5od','r5of','r5oh','r5oj'],'同じ範囲の異なる二人について権限なき強制による妨害を防ぐ公的所管と要求。実際の予防履行は断言しない。'),
      ('an der Bestimmung und Beförderung desselben ',['r5n4','r5n3','r5n5','r5oc'],'被害側本人の同じ救済について見解を定める目標と達成を促す目標の双方への営み。'),
      ('nach allem seinen Vermögen ',['r5n6','r5n7'],'同じ本人の固定能力範囲で可能な最大の投入。固定転記seinenとAAのseinemを区別。'),
      ('zu arbeiten.',['r5oa','r5ob','r5oc','r5od'],'その全力の営みへの候補を保護対象とする。既に必要と信じる対象だけへ狭めず、妨害と実行の成功・失敗を区別する。')):
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in names),names
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==3644
    pages=[p for p in read('data/personal-enlightenment-choice-reading-v1.json')['primary_pages'] if '490' in p['path']]
    assert len(pages)==1 and all(digest((ROOT/p['path']).read_bytes())==p['sha256'] for p in pages)
    for n,(span,_) in NODE_INFO.items():assert u['text'][slice(*span)].strip(),n
    return dict(status='monarchical_religion_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[3226,3644],text=u['text'][3226:3644]),selection=selection_binding(catalog(),[106]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_monarchical_religion_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=sum(not c.isspace() for c in u['text'][3226:3644]),
        semantic_equivalence_automatically_proved=False,original_pages=pages,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/040.html',lines='3–11',observation='原刊490頁の当該全文を表示して通読。AAのseinemと固定転記seinenを区別。')],
        holistic_review=[
          '原刊490頁のWennからarbeitenまでを通読し、固定転記の全354非空白文字を連続した語句対応へ置いた。後続の検閲批判の文は混入していない。',
          '同じ君主と政治的共同体を全仮定場面で追跡した。各場面を内部基準にし、監督成功や許可の存在で仮定場面を先取りして選別しない。',
          '最初のnurを十分条件への焦点、二つ目を最小限の応答への焦点として区別した。übrigensは公的秩序の留保を除く残余範囲とし、宗教的選択の無限定な全行為自由には拡張しない。',
          '真の改善と本人が改善と思うものの双方を量化し、実施された改善が全市民的秩序条件を保つよう監督する。全提案が秩序と両立可能だという旧nbは前件に使っていない。',
          'kannを著者の統治評価における積極的許容と読んだ。許可対象は同じ全臣民への非指図・非介入で、その許可を実際の履行や臣民の成功へ置き換えていない。',
          '本人が救済のため必要と思う内容と、その真理・実行を分離した。dasはその宗教的必要性の決定を受け、本人に代わる君主の公的所管はない。',
          'wohl aber以下では別の積極的所管と要求が同じ君主へ残る。前半の監督が成立しなくても、この予防職責と宗教的所管外は一般的説明として残る。',
          'einer/andernを同じ臣民範囲の異なる二人にし、desselbenと所有表現を被害側本人の救済と能力へ結んだ。二目標と最大努力を保ち、予防対象を既存の必要性信念だけに限定していない。',
          '暴力的妨害は保存済みAdelung語義に沿う権限なき優越的強制とした。身体力だけには狭めず、正当な公的規律を自動的に妨害とせず、妨害下の営みの成功も失敗も排除しない。',
          '全文と条件付き前半と職責二側を著者へ帰属し、条件の前件だけを無条件に断言しない。焦点・残余範囲・対照・順序を保持する。引用内容の実行なしに帰属を検査する。第六段落全体と二作品完成は未確認。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:106]==old.document['statements'] and len(new.document['statements'])==107
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    prior=read('data/monarchical-sentence-reading-v1.json');assert prior['selection']==selection_binding(new,[105])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            s=format_graph(doc,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==doc
    assert reading_record()['newly_reviewed_sentence_characters']==354
    return dict(preserved_statements=106,added_statements=1,preserved_whole_unit_reviews=len(reviews),preserved_opening_sentence_characters=2760,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,new_reviewed_sentence_characters=354)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('conditional',conditional_checks),('permission',permission_checks),('scope',scope_checks),('adapters',adapter_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*PRIORS,*(x['path'] for x in read(READING)['original_pages']),
        'data/monarchical-sentence-reading-v1.json','scripts/compose_monarchical_religion_sentence.py','scripts/check_monarchical_religion_sentence.py',
        'tests/test_monarchical_religion_sentence.py','scripts/check_persistent_compact_progress.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','scripts/check_covenant_nullity.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='monarchical_religion_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[106],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
