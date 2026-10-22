"""Check the complete seventh sentence and its explicit generic interpretation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_provisional_order_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,NAMES,NODES,NODE_INFO,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

INDEX='data/semantic-review-index-v185.json'
REPORT='reports/provisional-order-sentence-v1.json'
READING='data/provisional-order-sentence-reading-v1.json'
DOC='docs/provisional-order-sentence-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/legislative-touchstone-v1.json','reports/provisional-self-legislation-v1.json','reports/civic-participation-discourse-v1.json','reports/protective-petition-discourse-v1.json','reports/insight-threshold-v1.json','reports/institutional-outlook-v1.json')
SCENES=('reference','assessment','candidate','start','end','outer','context','outside')
EXTRA='r zbindings[] j[a].r zprior[] j[a].r zpeople[] a.r zcommunity[] a.'+''.join('r z'+n+'[] d.' for n in SCENES)
FRAME='k zbindings[] k zassessment[] k zcandidate[] k zstart[] k zend[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries and d['kind']=='definition':d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+EXTRA+query)
def run(doc,v,domain=('alpha','beta')):return evaluate(doc,v,domain,SCENES,True)
def base(doc,bindings=('alpha',)*10,prior=('alpha',)*3):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in SCENES})
    v.update(zbindings=lambda:SequenceValue(bindings,'"individual"'),zprior=lambda:SequenceValue(prior,'"individual"'),
        zpeople=lambda:'alpha',zcommunity=lambda:'alpha',h26b7=lambda:'reference',h26ar=lambda r:'assessment')
    return v

@lru_cache(None)
def generic_checks():
    d=fixture(('r5hv',),'q[t[k r5hv[]][k zouter[]]].',('r45d','r5gt'));rows={}
    first=('alpha',)*10
    second=('beta','beta','beta','alpha','beta','alpha','alpha','beta','alpha','beta')
    for variant in ('both','different_laws','missing_second','only_outside_scope','mixed_scope','empty_scope','no_plan','wrong_assessment','wrong_reference'):
        v=base(d)
        scopes=() if variant=='empty_scope' else (('alpha','beta'),) if variant=='mixed_scope' else (('alpha','alpha'),('beta','beta'))
        v['r45d']=lambda p,c,r:r==('outside' if variant=='wrong_reference' else 'reference') and(p,c) in scopes
        plans=() if variant=='no_plan' else (first,) if variant=='missing_second' else (('alpha','beta',*first[2:]),) if variant=='only_outside_scope' else (first,second)
        if variant=='mixed_scope':plans=(('alpha','beta',*second[2:]),)
        v['r5gt']=lambda *a:a[-1]==('outside' if variant=='wrong_assessment' else 'assessment') and a[:-1] in plans
        actual=run(d,v)
        # A genuinely empty frame is universal vacuity, not an existence claim.
        wanted=variant in ('both','different_laws','mixed_scope','empty_scope','wrong_reference')
        assert actual==[wanted],(variant,actual);rows[variant]=actual[0]
    v=base(d);v['r45d']=lambda p,c,r:(p,c,r)==('alpha','alpha','reference');v['r5gt']=lambda *a:a==(*first,'assessment')
    v['h26ar']=unknown
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('unknown assessment accepted')
    return dict(generic_people_existential_eight_target_configuration=rows,
        one_good_law_suffices_without_licensing_all_laws=True,
        different_peoples_need_not_share_law_or_configuration=True,
        empty_frame_does_not_assert_people_exist=True,truth_assessment_fixed=True,
        boundaries=['r45d complete population','r5gt normative bounded self-imposition; prior native evidence preserved'])

@lru_cache(None)
def projection_checks():
    d=fixture(('r5ht',),'q[k r5ht[k zbindings[] k zprior[]]].');rows=[]
    for i in range(10):
        ten=tuple('beta' if k==i else 'alpha' for k in range(10));prior=ten[:3]
        assert run(d,base(d,ten,prior))==[True]
        for pos in range(3):
            wrong=list(prior);wrong[pos]='alpha' if prior[pos]=='beta' else 'beta'
            assert run(d,base(d,ten,tuple(wrong)))==[False]
        rows.append(i)
    for ten,prior in ((('alpha',)*9,('alpha',)*3),(('alpha',)*11,('alpha',)*3),(('alpha',)*10,('alpha',)*2),(('alpha',)*10,('alpha',)*4)):
        assert run(d,base(d,ten,prior))==[False]
    q='q[e[k r5hs[k zbindings[]]][k r5eu[k zprior[]]]].'
    questions=fixture(('r5hs','r5eu'),q,('r5es',));answers={}
    for answer in (False,True):
        ten=('beta','alpha','beta',*('alpha',)*7);v=base(questions,ten,ten[:3]);v['r5es']=lambda *a:answer and a==ten[:3]
        actual=run(questions,v);assert actual==[True];answers[str(answer)]=actual[0]
        if answer:
            v['zprior']=lambda:SequenceValue(('alpha',)*3,'"individual"');assert run(questions,v)==[False]
    return dict(exact_ten_to_three_projection=rows,wrong_lengths_and_changed_prior_objects_rejected=True,
        lifted_question_equals_prior_question_for_both_answers=answers,
        boundary='r5es only for question truth; projection has no definition boundary')

@lru_cache(None)
def frame_checks():
    rows={}
    for root,target in (('r5hq','r5gs'),('r5hx','r5gp'),('r5hy','r5gk')):
        d=fixture((root,),'q[t[k '+root+'['+FRAME+']][k zouter[]]].',(target,));cases=[]
        for i in range(10):
            ten=tuple('beta' if k==i else 'alpha' for k in range(10));v=base(d,ten)
            if root=='r5hq':wanted=(*ten,'assessment','candidate','start','end');used=set(range(10))
            elif root=='r5hx':wanted=(*[ten[j] for j in (7,1,3,5,6,8,9)],'reference','assessment','candidate','start','end');used={7,1,3,5,6,8,9}
            else:wanted=(*[ten[j] for j in (7,1,8,9)],'reference','candidate','end');used={7,1,8,9}
            v[target]=lambda *a,wanted=wanted:a==wanted;assert run(d,v)==[True],(root,i)
            if i in used:
                v['zbindings']=lambda:SequenceValue(('alpha',)*10,'"individual"');assert run(d,v)==[False],(root,i)
            cases.append(i)
        for n in ('zcandidate','zend')+ (('zassessment','zstart') if root!='r5hy' else ()):
            v=base(d,ten);v[target]=lambda *a,wanted=wanted:a==wanted;v[n]=lambda:'outside';assert run(d,v)==[False],(root,n)
        rows[root]=cases
    d=fixture(('r5hr',),'q[t[k r5hr['+FRAME+']][k zouter[]]].',('r5gw',))
    for i in range(10):
        ten=tuple('beta' if k==i else 'alpha' for k in range(10));v=base(d,ten)
        v['r5gw']=lambda b,r,h,a:Content(SCENES,tuple(normalized(b)==ten and(r,h,a)==('reference','candidate','start') and t=='outer' for t in SCENES))
        assert run(d,v)==[True]
        v['zbindings']=lambda:SequenceValue(('alpha',)*10,'"individual"');assert run(d,v)==[False]
    return dict(exact_modal_and_cognitive_capacity_frames=rows,
        expectation_keeps_same_ten_objects_candidate_and_start=True,
        boundaries=['r5gs','r5gp','r5gk','r5gw; all native constructions preserved in prior reports'])

@lru_cache(None)
def discourse_checks():
    d=fixture(('r5hw',),'q[k r5hw[]].');f=lambda n:(n,1);scope=('r5gv',0);whole=('r5hv',3);a='author';ctx='context'
    expected={
      'h236i':{('h26ei',a,whole,ctx)},
      'h26eh':{('h26ej',a,'h26cq',f('r5eu'),f('r5hs'),('r5ht',0),f('r5gu'),scope,whole,ctx)},
      'h26ef':{('h26ek',a,whole,f('r5hq'),ctx)},
      'h26eg':{('h26el',a,whole,scope,f('r5hq'),f('r5hr'),ctx)},
      'h26ew':{('h26ev',a,whole,scope,f('r5hx'),f('r5hy'),ctx)},
      'h26d5':{('h26em',a,whole,f('r5g5'),f('r5gy'),f('r5gz'),f('r5g2'),ctx)},
      'h26d6':{(a,'h26en','h26eo',whole,f('r5gy'),f('r5g3'),f('r5g4'),ctx)},
      'h26d7':{('h26ep',a,whole,f('r5g6'),f('r5hb'),f('r5g7'),ctx)},
      'h234k':{('h26ep',a,'h26eq',ctx)},
      'h26eb':{('h26er',a,whole,f('r5g6'),f('r5hi'),f('r5hj'),ctx)},
      'h26ec':{('h26es',a,whole,f('r5g6'),f('r5he'),f('r5hg'),ctx)},
      'h26ed':{('h26eu',a,whole,f('r5g6'),f('r5hf'),f('r5hg'),f('r5hh'),ctx)},
      'h26ee':{('h26et',a,whole,f('r5ho'),f('r5hk'),f('r5hm'),ctx)},
      'uf':{(a,'h26co','h26ei',ctx),(a,'h26en','h26eo',ctx)},
      'ue':{(x,y,ctx) for x,y in (('h26co','h26ei'),('h26ej','h26ek'),('h26ek','h26el'),('h26el','h26em'),('h26eo','h26eq'),('h26ev','h26ep'),('h26ep','h26er'),('h26en','h26eo'),('h26er','h26es'),('h26es','h26et'),('h26et','h26eu'))}}
    rows={}
    for variant in ('baseline',*expected,'wrong_author','wrong_context','different_whole','other_question','other_projection','literal_expectation','wrong_cognition','full_participation_only','merged_nodes'):
        v=base(d);v.update({n:lambda n=n:n for n in NODES});v['wa']=lambda:'other' if variant=='wrong_author' else a;v['h255n']=lambda:'reference' if variant=='wrong_context' else ctx
        v['h26ar']=unknown  # Quoted world content must not request truth assessment.
        wanted=deepcopy(expected)
        changes={'different_whole':('h26ed',2,('r5e2',3)),'other_question':('h26eh',3,f('r5hs')),
          'other_projection':('h26eh',5,('r5gv',0)),'literal_expectation':('h26eg',4,f('r5hr')),
          'wrong_cognition':('h26ew',4,f('r5hy')),'full_participation_only':('h26d7',5,f('r5ha'))}
        if variant in changes:
            key,pos,value=changes[variant];row=list(next(iter(wanted[key])));row[pos]=value;wanted[key]={tuple(row)}
        v.update({n:lambda *args,n=n,values=values:n!=variant and normalized(args) in values for n,values in wanted.items()})
        if variant=='merged_nodes':
            v['h26ei']=lambda:'h26co'
            for n in expected:v[n]=lambda *args:True
        actual=run(d,v,(*NODES,a,'other'));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        for n in ('h26cf','h26c4','h26ea','h26ar','h245c','h26ds'):assert v[n] is unknown
    v=base(d);v.update({n:lambda n=n:n for n in NODES});v['wa']=lambda:a;v['h255n']=lambda:ctx
    v['h26ar']=unknown
    v.update({n:lambda *args,values=values:normalized(args) in values for n,values in expected.items()});v['h26ef']=unknown
    try:run(d,v,(*NODES,a,'other'))
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('unknown discourse accepted')
    return dict(one_whole_author_anaphora_qualification_depiction_and_all_discourse=rows,
        native_discourse_packages=['r5hc','r5hd','r5hp'],quoted_world_not_executed=True,unknown_rejected=True)

def reading_record():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013');cursor=1437;clauses=[]
    for fragment,names,reading in (
      ('Nun ',['uf','r5hw'],'前文の基準・問いから暫定例を説明する展開。暦上の現在は追加しない。'),
      ('wäre dieses wohl, ',['r5hu','r5hv','r5hs','r5ht','h26eh','h26ef'],'同じ人民による同じ法の自己賦課の問いを受け、限定条件の下で可能性を認める。'),
      ('gleichsam in der Erwartung eines bessern, ',['r5fj','r5fk','r5fn','r5hr','h26eg'],'同じ主体・活動がよりよい法を待つ態度への見立て。現実の心理や改善法の到来は連言しない。'),
      ('auf eine bestimmte kurze Zeit möglich, ',['r5fe','r5gs','r5gt','r5hq','r5hu'],'導入時に定まる一定の短期について、同じ候補の実施と規範的許可がそろう可能性。'),
      ('um eine gewisse Ordnung einzuführen; ',['r5ff','r5fl','r5fm','r5fo','r5hu'],'同じ人民の同じ採択活動によって、ある宗教上の秩序を導入する目的。対象制度は人民ごとの構成内で存在量化する。'),
      ('indem man es zugleich jedem der Bürger, ',['r5fa','r5fg','r5fp','r5gr'],'同じ短期に同じ共同体の全市民へ批評の自由を保つ条件。市民の範囲は各点で追う。'),
      ('vornehmlich dem Geistlichen, ',['r5gz','r5g5','r5hc'],'その中で聖職者を取り立てる。他の市民の自由を除かない。'),
      ('frei ließe, ',['r5e6','r5e7'],'作成・提出・両方の各活動への衝突のない積極的許可。実際の刊行とは区別する。'),
      ('in der Qualität eines Gelehrten ',['r2zi','r5e5'],'同じ本人の学識者としての公的な理性使用の立場。教会の職務上の私的使用へ戻さない。'),
      ('öffentlich, ',['r5g3','r5hc'],'同じ本人・活動・本来の公衆への使用の分類。'),
      ('d. i. durch Schriften, ',['r5g4','r5hc'],'同じ公的使用を、その同じ書面・公衆への提供によって説明する。'),
      ('über das Fehlerhafte der dermaligen Einrichtung ',['r33a','r5e5'],'同じ制度・領域についての非空の欠点所見。批判内容が真であることは追加しない。'),
      ('seine Anmerkungen zu machen, ',['h243y','r5e5','r5e6'],'同じ本人の作成する所見。別人の作品・活動を代用せず、本人による実際の発表は自由から導かない。'),
      ('indessen die eingeführte Ordnung noch immer fortdauerte, ',['r5fb','r5fc','r5fg','r5fi'],'同じ導入された秩序が批評自由と同時に期間中ずっと存続する。'),
      ('bis die Einsicht in die Beschaffenheit dieser Sachen ',['r5fq','r5ft','r5gq','r5gr'],'同じ制度の事柄のあり方を把握する公的な認識を到達条件にする。'),
      ('öffentlich so weit gekommen und bewähret worden, ',['r5fr','r5fs','r5fu','r5gl','r5gp'],'同じ内容の公開・根拠・確証を伴う認識が、この共同提案に十分な程度へ到達する。背景を固定した明示した質的比較を用いる。'),
      ('daß sie durch Vereinigung ihrer Stimmen ',['r5hx','r5hy','h26ew','r5fw','r5fx'],'単数のsieは洞察を受け、その洞察が同じ市民の共同の声による提案能力として働く描写。実行主体は同じ集団に保つ。'),
      ('(wenn gleich nicht aller) ',['r5g6','r5g7','r5ha','r5hb','r5hd'],'全員の声を必須としない括弧の譲歩。部分参加を必須にせず全員参加も排除しない。'),
      ('einen Vorschlag vor den Thron bringen könnte, ',['r5fy','r5gk','r5he','r5hi','r5hj','r5hp'],'同じ政策の一つの共同提案を同じ公的統治者へ提出し得る。王座の換喩を分け、現実の提出・採用・対面を補わない。'),
      ('um diejenigen Gemeinden in Schutz zu nehmen, ',['r5gi','r5hg','r5hp'],'同じ政策によって該当する全宗教共同体の同じ制度運用を保護する目的。'),
      ('die sich etwa nach ihren Begriffen der besseren Einsicht ',['r5ga','r5gb','r5gc','r5gd','r5hk','h26ee'],'本人たちのよりよい認識についての判断を理由とする仮定的な対象。客観的な公的知識と本人の判断を区別する。'),
      ('zu einer veränderten Religionseinrichtung geeinigt hätten, ',['r5fz','r5f3','r5f4','r5f5','r5ge'],'同じ共同体の同じ当事者が同じ新配置への合意を形成する。単なる別名、現実の実施、全成員の満場一致は補わない。'),
      ('ohne doch diejenigen zu hindern, ',['r5gh','r5hh','r5hp'],'同じ政策で他方の運用可能性を失わせない留保。保護目的を撤回せず両条件を保つ。'),
      ('die es beim Alten wollten bewenden lassen.',['r5f6','r5f7','r5hl','r5hn'],'同じ旧配置を続けたい肯定的な意向による独立した対象選択。改革しないという否定だけでは代用しない。')):
        assert unit['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==2309
    pages=[p for p in read('data/law-enactment-reading-v1.json')['primary_pages'] if 'page-489' in p['path']]
    assert len(pages)==1 and all(digest((ROOT/p['path']).read_bytes())==p['sha256'] for p in pages)
    return dict(status='provisional_order_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[1437,2309],text=unit['text'][1437:2309]),
        selection=selection_binding(catalog(),[102]),clauses=clauses,interpretation=LIMITS,unresolved=[],
        decision='equivalent_under_stated_reading_for_provisional_order_sentence',whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,
        newly_reviewed_sentence_characters=sum(not c.isspace() for c in unit['text'][1437:2309]),semantic_equivalence_automatically_proved=False,
        original_pages=pages,primary_evidence=[
          dict(url='https://korpora.org/kant/aa08/039.html',lines='15–27; following contrast 28–34',observation='自己賦課の問いから暫定的な可能性と後続条件へ続き、次文では持続的な宗教体制の不許可へ対照する。'),
          dict(url='https://lexika.digitale-sammlungen.de/adelung///lemma/bsb00009134_6_2_2635',section='3(4)',observation='wohlの譲歩的な用法を補助資料として確認した。ここでは前文の疑問用法とは分け、限定付きの肯定として読む。')],
        holistic_review=[
          '原刊489頁を表示して読み直し、固定原文の第七文全体を確認した。wohlの後の挿入、書面の説明、非全員の括弧、続くAberとの境界を保持し、範囲外の不許可文を今回の文字数に含めない。',
          '一般的な人民について可能な暫定例を述べる読みを、全人民の組とその内側の法以下八対象の存在として明示した。全法案への一括の許容にせず、一つの特定国だけの出来事へも縮めない。規範源・候補範囲・真偽評価を固定し、同じ候補の許可と実施を結ぶ。',
          'diesesとeines bessernは前文の同じ人民・法へ結ぶ。前者は十対象から先頭三対象への射影と同じ問い、後者は同じ元の法よりよい法の描写で追跡した。期待描写は現実の心理的条件として世界内容に加えない。',
          '同じ法と導入活動、宗教制度・共同体・期間を追跡し、その全内点で存続と全市民への批評自由を保つ。学識者の立場、自作の所見、同じ公衆と書面、欠点所見の非空性を既存構成で保持し、聖職者の焦点で全市民範囲を削らない。',
          '同じ制度の事柄についての把握・真偽・根拠・公開・確証から、同じ政策の共同提案に足りる到達条件を追跡した。十分性の比較モデルと最初の到達点という強い操作的読解を明記し、現実の必然的な到達や全知識の単調増加を追加しない。',
          '単数のsieとkönnteを洞察への照応として読み、抽象的な洞察を主体のように表す語法を同じ集団の声と能力へ結んだ。市民全員が全知識を個別に持つことや、抽象的認識の身体的発声へ置き換えていない。',
          '共同提案の固定した全当事者・同じ行為・同じ政策・同じ公的宛先を保持する。全員でも一部でもよいという譲歩、王座の換喩、同じ政策の保護目的、仮定的改革対象、独立した維持意向と非妨害を同じ全体内容へ接続した。',
          '全文の引用、前文への照応、限定付きの肯定、見立て、各説明・焦点・譲歩・目的・留保は、同じ著者と提示文脈を共有する。引用によって政策・合意・椅子・実施・成功を評価しない。',
          '連続する全語句の範囲と合成定義を照合して通読した。独立した本文の意味判断であり、有限検査の成功を原文同値の自動証明にはしていない。第七文を確認対象に加えても、第六段落全体と二作品全体は未完である。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:102]==old.document['statements'] and len(new.document['statements'])==103
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for p,indices in (('data/covenant-question-reading-v1.json',[96,97]),('data/covenant-nullity-reading-v1.json',[98]),('data/cohort-covenant-denial-reading-v1.json',[99]),('data/posterity-rights-reading-v1.json',[100]),('data/legislative-touchstone-reading-v1.json',[101])):
        assert read(p)['selection']==selection_binding(new,indices)
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    record=reading_record();assert record['newly_reviewed_sentence_characters']==747
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013')
    for name,(span,meaning) in NODE_INFO.items():assert unit['text'][span[0]:span[1]] and name in new.entries
    actual={d['name'] for d in closure(new.document,['r5hv'])}
    assert not actual&{'r5fn','r5gw','r5hr','h26c4','r5hj','h26ea'}
    return dict(preserved_statements=102,added_statements=1,preserved_whole_unit_reviews=len(reviews),preserved_opening_sentence_characters=1234,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,new_reviewed_sentence_characters=747,
        literal_expectation_and_physical_throne_absent_from_world_conditions=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('generic',generic_checks),('projection',projection_checks),('frames',frame_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*PRIORS,*(p['path'] for p in read(READING)['original_pages']),
        'data/covenant-question-reading-v1.json','data/covenant-nullity-reading-v1.json','data/cohort-covenant-denial-reading-v1.json','data/posterity-rights-reading-v1.json','data/legislative-touchstone-reading-v1.json',
        'scripts/compose_provisional_order_sentence.py','scripts/check_provisional_order_sentence.py','tests/test_provisional_order_sentence.py',
        'scripts/check_covenant_nullity.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/compose_provisional_self_legislation.py'}
    return dict(status='provisional_order_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[102],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
