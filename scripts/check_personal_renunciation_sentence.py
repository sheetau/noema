"""Check the whole ninth sentence, shared referents, quotation and source reading."""
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
from scripts.compose_personal_renunciation_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,NODES,NODE_INFO,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_persistent_compact_progress import SCENES,DOMAIN,EXTRA

INDEX='data/semantic-review-index-v187.json'
REPORT='reports/personal-renunciation-sentence-v1.json'
READING='data/personal-renunciation-sentence-reading-v1.json'
DOC='docs/personal-renunciation-sentence-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/fixed-compact-sentence-v1.json','reports/limited-personal-deferral-v1.json','reports/renunciation-rights-v1.json','reports/personal-enlightenment-choice-v1.json')

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
def base(d,bindings=('alpha',)*5):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(zbindings=lambda:SequenceValue(bindings,'"individual"'),h26f2=lambda:'reference',
        h26fw=lambda a,r:'start',h26ax=lambda:'alpha',h26fz=lambda:'beta')
    return v

@lru_cache(None)
def core_checks():
    d=fixture(('r5l3',),'q[t[k r5l3[]][k zcandidate[]]].',('r5la','r5lo'));rows={}
    for permitted,rights in product((False,True),repeat=2):
        v=base(d);v['r5la']=lambda:content({'candidate'} if permitted else set());v['r5lo']=lambda:content({'candidate'} if rights else set())
        actual=run(d,v);assert actual==[permitted and rights];rows[str((permitted,rights))]=actual[0]
    return dict(both_halves_required=rows,boundaries=['r5la; pinned permission and restriction evidence','r5lo; pinned complete rights and renunciation evidence'])

@lru_cache(None)
def adapter_checks():
    rows={}
    cases=(('r5lq','r5lm',3),('r5lr','r5ln',5),('r5lx','r5ls',5),('r5l5','r5lq',5),
        ('r5ly','r5k3',4),('r5lz','r5k2',4),('r5l6','r5lg',3),('r5l7','r5lh',5))
    for root,target,length in cases:
        d=fixture((root,),'q[t[k '+root+'[k zbindings[] k zreference[]]][k zcandidate[]]].',(target,));positions=[]
        for i in range(length):
            b=tuple('beta' if i==j else 'alpha' for j in range(length));v=base(d,b)
            if root in ('r5lq','r5lr'):v[target]=lambda *a:a==(*b,'candidate')
            elif root in ('r5ly','r5lz'):v[target]=lambda *a:a==(*b,'reference','candidate')
            else:
                projection=b[:3] if root in('r5lx','r5l5') else b[1:]
                v[target]=lambda bindings,r:content({'candidate'}) if(normalized(bindings),r)==(projection,'reference') else content(set())
            assert run(d,v)==[True],(root,i)
            v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"')
            ignored=(root in('r5lx','r5l5') and i>=3) or(root in('r5l6','r5l7') and i==0)
            assert run(d,v)==[ignored],(root,i);positions.append(dict(position=i,projected_out=ignored))
        for size in (length-1,length+1):
            v['zbindings']=lambda:SequenceValue(('alpha',)*size,'"individual"');assert run(d,v)==[False]
        rows[root]=positions
    for root,target,length in (('r5lt','r5li',3),('r5lu','r5lj',5)):
        d=fixture((root,),'q[t[k '+root+'[k zbindings[] k zreference[]]][k zcandidate[]]].')
        for i in range(length):
            b=tuple('beta' if i==j else 'alpha' for j in range(length));v=base(d,b)
            wanted=('alpha',b[0],b[1],'beta',(target,0),b[1:],'reference','candidate')
            v['h26bv']=lambda *a:normalized(a)==wanted
            assert run(d,v)==[True];v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False]
        rows[root]='all positions checked against the same quoted conduct and protected rights'
    return dict(all_positions_and_exact_lengths=rows,boundaries=[target for _,target,_ in cases],native_contempt_appraisal=True)

@lru_cache(None)
def scope_checks():
    rows={}
    for root,length in (('r5lp',5),('r5lv',3),('r5lw',5)):
        d=fixture((root,),'q[t[k '+root+'[k zbindings[] k zreference[]]][k zcandidate[]]].',('r5ll','r5lc','r5kn'));cases={}
        for variant in ('baseline','no_rights','no_personal_candidate','no_posterity_candidate','no_duties','no_posterity_frame','outside_anchor','cycle','wrong_reference'):
            v=base(d,('alpha',)*length);v['r5ll']=lambda rights:rights=='alpha' and variant!='no_rights'
            v['aa']=lambda p:p=='alpha'
            v['r5kn']=lambda s,p,role,r:(s,p,role,r)==('alpha','alpha','beta','reference') and variant!='no_duties'
            v['r5lc']=lambda *a:a==('alpha','alpha','alpha','alpha','reference','candidate') and variant!='no_posterity_frame'
            history=('start','end')
            v['h257z']=lambda r,c,t:(r,c)==('reference','candidate') and t in history
            v['ic']=lambda a,b,c:c=='candidate' and a in history and b in history and (a!=b if variant=='cycle' else (a,b)==('start','end'))
            def candidate(target,b,r,c):
                if(r,c)!=('reference','candidate'):return False
                return (normalized(target),normalized(b))==(('r5lg',0),('alpha',)*2) and variant!='no_personal_candidate' or (
                    (normalized(target),normalized(b))==(('r5lh',0),('alpha',)*4) and variant!='no_posterity_candidate')
            v['h26f3']=candidate
            if variant=='outside_anchor':v['h26fw']=lambda *a:'outer'
            if variant=='wrong_reference':v['zreference']=lambda:'assessment'
            rejected={'no_rights','wrong_reference'}
            if root in('r5lp','r5lv'):rejected|={'no_personal_candidate','no_duties','outside_anchor','cycle'}
            if root in('r5lp','r5lw'):rejected|={'no_posterity_candidate','no_posterity_frame'}
            actual=run(d,v);assert actual==[variant not in rejected],(root,variant,actual);cases[variant]=actual[0]
        rows[root]=cases
    d=fixture(('r5l2',),'q[t[k r5l2[k zbindings[] k zreference[]]][k zcandidate[]]].',('r5kw','r5kz'));restriction={}
    for frame,executed in product((False,True),repeat=2):
        v=base(d,('alpha',)*4);v['r5kw']=lambda *a:a==('alpha','alpha','alpha','alpha','reference','candidate') and frame
        v['r5kz']=lambda b,r:content({'candidate'}) if executed and (normalized(b),r)==(('alpha',)*4,'reference') else content(set())
        actual=run(d,v);assert actual==[frame and executed];restriction[str((frame,executed))]=actual[0]
    return dict(separate_personal_posterity_and_comparison_scopes=rows,restriction_scope_without_permission_or_qualification=restriction,
        boundaries=['r5ll rights','r5lc posterity and duties','r5kn personal duties','r5kw/r5kz restriction scope'],no_actual_choice_or_appraisal_in_comparison=True)

@lru_cache(None)
def depiction_checks():
    d=fixture(('r5ls',),'q[t[k r5ls[k zbindings[] k zreference[]]][k zcandidate[]]].');rows={}
    for variant in ('baseline','no_action','no_foot','no_pressure','other_person','other_response','other_foot','other_object','other_reference','other_point'):
        v=base(d,('alpha',)*3)
        v['cg']=lambda p,a,t:(p,a,t)==('alpha','alpha','start') and variant!='no_action'
        v['h26f6']=lambda p,f,r:(p,f,r)==('beta' if variant=='other_person' else 'alpha','beta','reference') and variant!='no_foot'
        wanted=['alpha','beta','alpha','reference','start']
        changes={'other_response':(0,'beta'),'other_foot':(1,'alpha'),'other_object':(2,'beta'),'other_reference':(3,'assessment'),'other_point':(4,'end')}
        if variant in changes:i,value=changes[variant];wanted[i]=value
        v['h26f7']=lambda *a:a==tuple(wanted) and variant!='no_pressure'
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    v=base(d,('alpha',)*3);v['cg']=lambda *a:True;v['h26f6']=unknown
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown body part accepted')
    return dict(same_actor_response_own_foot_and_rights_object=rows,unknown_rejected=True,boundaries=[])

@lru_cache(None)
def discourse_checks():
    d=fixture(('r5ma',),'q[k r5ma[]].');q=lambda n:(n,2);whole=('r5l3',3);a='author';ctx='outer';ref='reference'
    expected={
      'h236i':{(node,a,(target,3),ctx) for node,target in (('h26gd','r5l3'),('h26ge','r5la'),('h26gf','r5lo'))},
      'h26gb':{('h26gg',a,whole,('r5la',3),('r5lo',3),ctx)},
      'h26ga':{('h26gh',a,whole,q('r5l2'),q('r5lz'),q('r5ly'),ref,ctx)},
      'h222q':{('h26gi',a,'h26ge',('r5la',1),'h26gf',('r5lo',1),('r5l4',0),ctx)},
      'h26fe':{('h26gl',a,whole,q('r5lp'),q('r5l5'),q('r5lr'),ref,ctx)},
      'h26fd':{('h26gl',a,whole,q('r5lp'),q('r5l5'),q('r5lr'),ref,ctx)},
      'h26gc':{('h26gm',a,whole,q(scope),q(conduct),q(appraisal),ref,ctx) for scope,conduct,appraisal in (('r5lv','r5l6','r5lq'),('r5lw','r5l7','r5lr'))},
      'h26fc':{('h26gn',a,whole,q(scope),q(described),q(depiction),ref,ctx) for scope,described,depiction in (('r5lv','r5lt','r5ls'),('r5lw','r5lu','r5lx'))},
      'ue':{(x,y,ctx) for x,y in (('h26fi','h26gd'),('h26gg','h26gh'),('h26ge','h26gf'),('h26gi','h26gj'),('h26gj','h26gl'),('h26gl','h26gk'),('h26gk','h26gm'),('h26gm','h26gn'))}}
    variants=['baseline','wrong_author','wrong_context','wrong_reference','merged_nodes']
    missing=[(key,row) for key,values in expected.items() for row in sorted(values)]
    variants+=['missing_'+str(i) for i in range(len(missing))];rows={}
    for variant in variants:
        v=base(d);v.update({n:lambda n=n:n for n in NODES});v['wa']=lambda:'other' if variant=='wrong_author' else a
        v['h255n']=lambda:'candidate' if variant=='wrong_context' else ctx
        if variant=='wrong_reference':v['h26f2']=lambda:'assessment'
        wanted=deepcopy(expected)
        if variant.startswith('missing_'):
            key,row=missing[int(variant.split('_')[1])];wanted[key].remove(row)
        v.update({n:lambda *args,values=values:normalized(args) in values for n,values in wanted.items()})
        if variant=='merged_nodes':
            v['h26gd']=lambda:'h26ge'
            for n in expected:v[n]=lambda *a:True
        actual=run(d,v,(*NODES,a,'other'));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        for n in ('h26f6','h26f7','h26ft','h26bt','h26bv','h245c'):assert v[n] is unknown
    return dict(same_whole_clauses_author_reference_and_presentations=rows,
        every_required_relation_individually_removed=len(missing),quoted_literal_action_choice_and_rights_not_executed=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013');cursor=2678;clauses=[]
    for fragment,names,reading in (
      ('Ein Mensch ',['r5la','aa'],'人一般。成功例だけを主語の範囲へ選別しない。'),
      ('kann ',['r5k4','r5k5','r5la'],'各人に一つ以上の衝突のない許容構成が可能であるという規範的な読み。'),
      ('zwar ',['h26gb'],'前半を認めながら後半を保持する譲歩的な承認。'),
      ('für seine Person, ',['r5k3','r5k7'],'選択主体と対象本人の一致という許容の必要限定。'),
      ('und auch alsdann nur auf einige Zeit, ',['r5jd','r5k3','r5k7','r5l2','r5ly','r5lz','h26ga'],'本人の場合にも有界で再開方針を保つという必要条件。任意の有限期間の一括許可にはしない。'),
      ('in dem was ihm zu wissen obliegt ',['r5km','r5kn','r5ko'],'同じ本人の知るべき全事項を固定し、その全項目と自己判断対象の対応を保つ。'),
      ('die Aufklärung aufschieben; ',['r5kq','r5kx','r5ky','r5kz','r5k3'],'知るべき事項について理由ある自己判断を目指す営みを、一時中断して後に続ける方針。'),
      ('aber ',['h222q','r5l4'],'同じ人の啓蒙に関わる選択について、延期と放棄を対照する。'),
      ('auf sie Verzicht zu thun, ',['r5ku','r5kv','r5ld','r5lf'],'同じ啓蒙の継続を退ける方針の採用。引用内容の実際の永続的不成功は要求しない。'),
      ('es sei für seine Person, ',['r5lg','r5li','r5lm','r5lo'],'本人についての放棄の場合も同じ権利への評価に含む。'),
      ('mehr aber noch für die Nachkommenschaft, ',['r5lb','r5lc','r5lh','r5ln','r5lp','r5l5','r5lr','h26fe','h26fd'],'完全な後代についての放棄も評価し、本人の場合を越えるものとして対照・増幅する。'),
      ('heißt ',['r5lo','r5l6','r5l7','h26gc'],'同じ放棄を侵害・軽視に当たるものとして性格づける。逆向きの全同値にはしない。'),
      ('die heiligen Rechte der Menschheit ',['r5lk','r5ll','h26f4','h26f5','h256m'],'通時的人類の啓蒙の進展を追求する条件・機会への全関連請求と、侵してはならない尊重。'),
      ('verletzen ',['r5lm','r5ln','h26bt'],'本人・後代の同じ放棄への同じ権利の重大な侵害評価。'),
      ('und mit Füßen treten.',['r5lt','r5lu','r5ls','r5lx','h26fc'],'同じ軽視を、同じ主体が自身の足で同じ権利を踏む姿へ見立てる。字義的な出来事は断言しない。')):
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==2985
    pages=read('data/personal-enlightenment-choice-reading-v1.json')['primary_pages']
    assert all(digest((ROOT/p['path']).read_bytes())==p['sha256'] for p in pages)
    return dict(status='personal_renunciation_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[2678,2985],text=u['text'][2678:2985]),selection=selection_binding(catalog(),[104]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_personal_renunciation_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=sum(not c.isspace() for c in u['text'][2678:2985]),
        semantic_equivalence_automatically_proved=False,original_pages=pages,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/039.html',lines='33–37',observation='保存済み原刊489頁末と490頁冒頭を再表示し、第九文の全文と前後の境界を照合。')],
        holistic_review=[
          '原刊489頁末のEin Menschから490頁のmit Füßen tretenまでを再表示して通読した。前文の全面的不許可と次文の人民/君主の権限比較を混入せず、全語句を連続する対応表に置いた。',
          '一人の実例に縮めない一般性、本人自身という対象、知るべき事項全体、一定期間だけという限定を追跡した。規範的可能性と必要条件を分け、全ての有限期間への許可や実際の延期を導かない。',
          '同じ啓蒙の営みを受けるsieを、本人と後代の二場合で保持した。本人の放棄と、現在の主体が後代の継続を退ける方針を採ることを区別し、後代の同意・代理権・実際の服従を追加していない。',
          '同じ選択点が属する時代より後に生存する人々の全範囲を保ち、血縁・直後の世代・現存する人だけに狭めない。全成員の義務事項対応を保持し、引用内容の成功や未来の実現を方針採用から実行しない。',
          '権利の担い手を通時的人類に、内容を啓蒙進展を追求する条件と機会への全関連請求に固定した。神聖は侵してはならない尊重と読む。認識獲得・訂正・自己判断の進展という既存の選言を保持した。',
          '本人と後代の両場合が同じ権利集合への侵害・不遜な軽視の評価に当たる構成を確認した。heißtをこの性格づけとして提示し、全権利侵害から放棄へ逆推論しない。実際の放棄がなくても権利の存在を落とさない。',
          '足の描写は現在の主体自身の身体の足、同じ選択応答、同じ権利対象を共有する。後代の人々が踏まれる描写に替えず、描写を中心内容の事実条件へ加えていない。',
          'zwarの承認とaberの対照、本人の場合にも残る限定、後代の場合を強めるmehr aber nochを同じ全体・著者・基準・文脈へ接続した。二場合を排他的にせず、数値的な程度差や前半の撤回を補わない。',
          '明示した解釈の下で第九文全体の対応を判断した。有限模型は引数と作用域の検証であり、この通読判断を自動的に証明するものではない。第六段落全体と二作品完成は未確認である。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:104]==old.document['statements'] and len(new.document['statements'])==105
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    prior=read('data/fixed-compact-sentence-reading-v1.json');assert prior['selection']==selection_binding(new,[103])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            s=format_graph(doc,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==doc
    record=reading_record();assert record['newly_reviewed_sentence_characters']==256
    actual={d['name'] for d in closure(new.document,['r5l3'])};assert not actual&{'h26f6','h26f7','r5ls','r5lx'}
    return dict(preserved_statements=104,added_statements=1,preserved_whole_unit_reviews=len(reviews),preserved_opening_sentence_characters=2301,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,new_reviewed_sentence_characters=256,literal_trampling_absent_from_world_conditions=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('core',core_checks),('adapters',adapter_checks),('scopes',scope_checks),('depiction',depiction_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*PRIORS,*(x['path'] for x in read(READING)['original_pages']),
        'data/fixed-compact-sentence-reading-v1.json','scripts/compose_personal_renunciation_sentence.py','scripts/check_personal_renunciation_sentence.py',
        'tests/test_personal_renunciation_sentence.py','scripts/check_persistent_compact_progress.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','scripts/check_covenant_nullity.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='personal_renunciation_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[104],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
