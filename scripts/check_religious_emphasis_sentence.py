"""Check the complete first sentence of Kant's ninth paragraph."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_religious_emphasis_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,LIMITS,NODE_INFO,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/religious-emphasis-sentence-v1.md';READING='data/religious-emphasis-sentence-reading-v1.json'
INDEX='data/semantic-review-index-v201.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
SOURCE='data/ninth-paragraph-source-reading-v1.json'
PRIORS=('reports/topical-guardian-interest-v1.json','reports/retrospective-emphasis-v1.json','reports/immaturity-comparison-v1.json','reports/eighth-paragraph-v1.json')
DOMAIN=('author','reader','rulera','rulerb','communitya','communityb','groupa','groupb','public','religion','arts','sciences','work','outside')
SCENES=('reference','now','elsewhere')
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=''):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:
            row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']}
    d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d['declarations']=closure(d,(*roots,*ns))
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update(wa=lambda:'author',h26kh=lambda:'public',h26kk=lambda:'religion',h26km=lambda:'reference',h26kn=lambda w:'now',
        h26sk=lambda:'work',h26sl=lambda:'reference',h26sm=lambda:'arts',h26sn=lambda:'sciences',
        aa=lambda p:p in ('author','reader','rulera','rulerb'),
        h246c=lambda g,p,r:g=='public' and p in ('author','reader') and r=='reference',
        h26so=lambda a,p,r,c,ref,t:(a,p,ref,t)==('author','public','reference','now') and (r,c) in (('rulera','communitya'),('rulerb','communityb')),
        h26sp=lambda r,c,ref:'groupa' if (r,c,ref)==('rulera','communitya','reference') else 'groupb',
        r6bp=lambda r,c,g,a,s,ref,t:(r,c,g) in (('rulera','communitya','groupa'),('rulerb','communityb','groupb')) and (a,s,ref,t)==('arts','sciences','reference','now'),
        r6bt=lambda a,w,t,r,p:(a,w,t,r,p)==('author','work','religion','reference','now'),
        h26j7=lambda t,r:(t,r)==('religion','reference'),
        r6b5=lambda t,p,r:(t,p,r)==('religion','public','reference'),
        r6b6=lambda t,p,r:(t,p,r)==('religion','public','reference'))
    return v

@lru_cache(None)
def content_checks():
    names=('r6cc','r6cd','r6ce','r6cf','r6cg','r6ch')
    extra='r znow[] d.r zelsewhere[] d.'
    query=''.join('q[t[k '+n+'[]][k z'+point+'[]]].' for point in ('now','elsewhere') for n in names)
    d=fixture(names,query,('r6bt','r6bp','r6b5','r6b6'),extra);v=model(d);v.update(znow=lambda:'now',zelsewhere=lambda:'elsewhere')
    assert run(d,v)==[True]*12;rows={}
    for case in ('second_ruler_interested','wrong_subject_group','empty_rulers','wrong_ruling_community','empty_public','author_not_in_public','nonhuman_member','wrong_author','wrong_work','wrong_topic','wrong_reference','wrong_now','swapped_arts_sciences','not_religious','no_harm_maximum','no_dishonor_maximum','outside_ruler'):
        w=dict(v);want=[True]*6
        if case=='second_ruler_interested':w['r6bp']=lambda r,*a:r=='rulera';want[1]=False
        if case=='wrong_subject_group':w['h26sp']=lambda *a:'groupa';want[1]=False
        if case=='empty_rulers':w['h26so']=lambda *a:False;want[1]=False
        if case=='wrong_ruling_community':w['h26so']=lambda a,p,r,c,ref,t:r=='rulera' and c=='communityb';want[1]=False
        if case=='empty_public':w['h246c']=lambda *a:False;want[1]=False
        if case=='author_not_in_public':w['h246c']=lambda g,p,r:p=='reader';want[1]=False
        if case=='nonhuman_member':w['aa']=lambda p:p=='author';want[1]=False
        if case=='wrong_author':w['wa']=lambda:'reader';want[0]=want[1]=False
        if case=='wrong_work':w['h26sk']=lambda:'outside';want[0]=False
        if case=='wrong_topic':w['h26kk']=lambda:'arts';want[0]=want[2]=want[3]=False
        if case=='wrong_reference':w['h26sl']=lambda:'elsewhere';want[:4]=[False]*4
        if case=='wrong_now':w['h26kn']=lambda *a:'elsewhere';want[0]=want[1]=False
        if case=='swapped_arts_sciences':w['h26sm']=lambda:'sciences';w['h26sn']=lambda:'arts';want[1]=False
        if case=='not_religious':w['h26j7']=lambda *a:False;want[2]=want[3]=False
        if case=='no_harm_maximum':w['r6b5']=lambda *a:False;want[2]=False
        if case=='no_dishonor_maximum':w['r6b6']=lambda *a:False;want[3]=False
        if case=='outside_ruler':w['r6bp']=lambda r,*a:r!='outside'
        want[4]=want[2] and want[3];want[5]=all(want[:2]) and want[4]
        got=run(d,w);assert got==want*2,(case,got,want);rows[case]=want
    for n in ('h26so','h26sp','h246c','r6bp','r6bt','r6b5','r6b6'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,every_ruler_community_pair=True,same_subjects_and_two_topics=True,shared_fixed_reference_and_present=True,
        boundary='r6bt/r6bp/r6b5/r6b6 are explicit test boundaries with exact argument checks; their native bodies are separately checked by the three pinned dependency reports. r6cb quantification and r5ty execute here.',unknown_rejected=True)

@lru_cache(None)
def conjunction_checks():
    d=fixture(('r6ch',),'q[t[k r6ch[]][k znow[]]].',('r6cc','r6cd','r6cg'),'r znow[] d.');rows=[]
    from noema.constructed_semantics import Content
    for bits in product((False,True),repeat=3):
        v=model(d);v['znow']=lambda:'now'
        for name,bit in zip(('r6cc','r6cd','r6cg'),bits):v[name]=lambda bit=bit:Content(SCENES,tuple(bit for _ in SCENES))
        got=run(d,v);assert got==[all(bits)],(bits,got);rows.append(dict(parts=list(bits),whole=got[0]))
    return dict(all_three_content_combinations=rows,neither_reason_replaces_the_retrospective=True)

@lru_cache(None)
def expansion_checks():
    c=catalog();a=deepcopy(c.entries['bi']['declaration']);b=deepcopy(c.entries['r6ca']['declaration']);a['name']=b['name'];assert a==b
    return dict(expansion_same_normalized_body_as_bi=True,be_same_person_process_and_endpoints=True,
        semantic_boundary='The existing be/rqrj/up meaning chain is preserved; this expansion adds no new state-change law.')

def callcode(n,rank=3,ref=False):return rank,json.dumps(dict(kind='function_ref',symbol=n) if ref else dict(kind='call',symbol=n,arguments=[]),sort_keys=True)
def norm(xs):return tuple((v.rank,json.dumps(json.loads(v.syntax),sort_keys=True)) if hasattr(v,'syntax') else v for v in xs)
@lru_cache(None)
def discourse_checks():
    extra='r h26kk[] a.r h26sl[] d.d h223g[item a] i[a][r[k h26kk[]]].d h223h[point d] i[d][r[k h26sl[]]].'
    d=fixture(('r6cj',),'q[k r6cj[]].',extra=extra)
    nodes=(*NODE_INFO,'h26r3');domain=(*nodes,'author','other','religion');scenes=('context','reference')
    state=(1,json.dumps(dict(kind='apply',function=dict(kind='function_ref',symbol='r6bz'),arguments=[dict(kind='call',symbol=n,arguments=[]) for n in ('h26kk','h26sl')]),sort_keys=True))
    expected={
      'hzon':{('h26sv','author',callcode('r6ch',1),'context')},
      'h26st':{('h26sx','author','h26sw','h26sx',callcode('bi',0,True),callcode('r6ca',0,True),'context')},
      'h26su':{('h26s2','author','h26s5',callcode('bp',0,True),state,'religion','reference','context')},
      'h26q3':{('h26sy','author',callcode('r6cc'),callcode('r6cd'),'context'),('h26sz','author',callcode('r6cc'),callcode('r6cg'),'context')},
      'h26sr':{('h26sz','author',callcode('r6ch'),callcode('r6cd'),callcode('r6cg'),'context')},
      'h26ss':{('h26s4','author',callcode('r6cg'),callcode('r6ce'),callcode('r6cf'),'context')},
      'ue':{(a,b,'context') for a,b in (('h26r3','h26sv'),('h26sw','h26sx'),('h26s6','h26s7'),('h26s7','h26ta'),('h26s5','h26s2'),('h26s3','h26s4'))}}
    def values(rows):
        v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
        v.update({n:lambda n=n:n for n in nodes});v.update(wa=lambda:'author',h26sq=lambda:'context',h26kk=lambda:'religion',h26sl=lambda:'reference')
        v.update({n:lambda *a,allowed=rs:norm(a) in allowed for n,rs in rows.items()});return v
    assert run(d,values(expected),domain,scenes)==[True];count=0
    for n,rs in expected.items():
        for row in rs:
            for i in range(len(row)):
                changed=deepcopy(expected);changed[n].remove(row);bad=list(row);bad[i]='other';changed[n].add(tuple(bad))
                assert run(d,values(changed),domain,scenes)==[False],(n,i);count+=1
    for i,n in enumerate(nodes):
        for other in nodes[i+1:]:
            v=values(expected);v[n]=lambda other=other:other
            for name in expected:v[name]=lambda *a:True
            assert run(d,v,domain,scenes)==[False]
    for n in expected:
        v=values(expected);v[n]=unknown;rejects(d,v,domain,scenes)
    v=values(expected)
    for n in ('h26so','h26sp','h26sa','h26sc','h26sg','h26sh','h26se','ab','ac'):assert v[n] is unknown
    return dict(argument_mutations=count,same_explained_content_for_both_reasons=True,independent_predications_presented_in_parallel=True,
        anaphora_matches_comparisons_state=True,quotation_not_executed=True,distinct_source_nodes=True,unknown_rejected=True)

FRAGMENTS=(
 ('Ich habe den Hauptpunkt der Aufklärung, ',['r6cc','r6bt','r6bs','r6bq'],'Ichを著者wa、同じ作品の過去の重点設定と現在の最大重点に結ぶ。'),
 ('die des Ausganges der Menschen aus ihrer selbst verschuldeten Unmündigkeit, ',['r6ca','bi','be','bp','h26st'],'自己帰責される未成熟からの同じ人の離脱として啓蒙を展開する説明。全員の実際の離脱を追加しない。'),
 ('vorzüglich in Religionssachen gesetzt: ',['r6cc','r6bt','h26j7'],'宗教事項を同じ概念の最大の論述重点とする。唯一性は補わない。'),
 ('weil in Ansehung der Künste und Wissenschaften ',['r6cd','r6bn','h26r5','h26r6','h26q3'],'技芸と学問の両方についての第一理由を同じ回顧へ向ける。'),
 ('unsere Beherrscher kein Interesse haben, ',['r6cb','r6bp','r6bm','h26so','h26sa'],'著者と同時代の公衆に関わる全統治者に実践的関心の不在を述べる。'),
 ('den Vormund über ihre Unterthanen zu spielen; ',['r6bo','r6bj','r6bk','r6bl','h26sp'],'各統治者の同じ全臣民について後見の立場を取る行為を関心の対象として引用する。'),
 ('überdem auch ',['r6cj','h26q3','h26sr'],'同じ回顧への第二理由を第一理由に追加する。'),
 ('jene Unmündigkeit, ',['r6ci','r6bz','h26su'],'先行の自己帰責される未成熟を、同じ宗教領域へ具体化して受ける。'),
 ('so wie die schädlichste, ',['r6ce','r6b5','h26ss'],'同じ全関連領域で肯定的な有害さと最大を要求する第一述定。'),
 ('also auch die entehrendste unter allen ist.',['r6cf','r6b6','r6cg','r6cj','h26ss'],'同じ範囲で不名誉の肯定と最大を独立に要求し、両述定を並列する。'))
def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0016');cursor=0;clauses=[]
    for fragment,names,reading in FRAGMENTS:
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in names)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==389 and sum(not c.isspace() for c in u['text'][:cursor])==336
    return dict(status='religious_emphasis_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
      source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,cursor],text=u['text'][:cursor]),selection=selection_binding(catalog(),[117]),
      clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_religious_emphasis_sentence',
      whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=336,semantic_equivalence_automatically_proved=False,
      primary_evidence=[dict(path=SOURCE,observation='原刊492頁とAA VIII 41を照合した記録v1。固定dieを保存し、離脱句を説明として読む。')],
      holistic_review=[
       '389文字・336非空白文字を十断片と全文で再読。Ichの著者、同じ作品の回顧、啓蒙の離脱句による説明、宗教事項の最大重点、技芸と学問の二領域、全統治者と各全臣民、関心の否定と後見活動の引用を接続した。',
       '原刊dieの文字をAAのd. i.に書き換えず、説明としての読みを明示した。biとr6caは同じbeの展開であり、Menschenを全員の離脱の既成事実にせず、人間一般の啓蒙概念として保持した。',
       'unsereの範囲とその全臣民は関心や後見の実行から選ばない。関心を実行・職務・単なる好奇心へ替えず、芸術だけ又は自然科学だけに狭めない。回顧・第一理由は同じ本文現在に固定した。',
       'jeneは同じ宗教主題の自己帰責される未成熟を指す。能力の未評価を不能としない構成と同じ状態の帰責を保ち、有害さと不名誉は同じ対象・全比較範囲で別々に最大を要求する。比較時に現実の未成熟者数や実害は要求しない。',
       '二つの理由は同じ回顧の内容へ向けた著者の説明として結び、追加と並列を別に示す。理由から結論への形式的含意、尺度の等値、第一理由の撤回や未知からの否定を補わない。',
       '全文は閉じた同じ内容として著者へ帰属し、説明・照応・順序は実際の世界内容を実行せずに記述する。既存18全単位判断は保持し、第一文だけでu0016全体を確認済みとしない。'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,CORE,BASIS,ANNOTATIONS,DOC,INVENTORY,SOURCE,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert c.document['statements'][:117]==old.document['statements'] and len(c.document['statements'])==118
    assert all(c.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==18
    for row in reviews:assert row['selection']==selection_binding(c,[s['index'] for s in row['selection']['statements']])
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert read(ANNOTATIONS)['entries']==read('data/self-departure-sentence-identifiers-v1.json')['entries']
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        t=format_graph(core,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==core
    ranks={};t=format_graph(core,'compact')
    for name in ('r6ca','r6cc','r6cd','r6ce','r6cf','r6cg','r6ch','r6ci'):
        for rank,label in enumerate(('','b','c','d')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert ranks=={n:int(n not in ('r6ca','r6cc')) for n in ranks},ranks
    return dict(preserved_statements=117,added_statements=1,preserved_whole_unit_reviews=18,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        new_reviewed_sentence_characters=336,minimum_quote_ranks=ranks,roundtrip_scope='new core compact/full/v2; inherited manuscript and meanings unchanged')
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('content',content_checks),('conjunction',conjunction_checks),('expansion',expansion_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,SOURCE,*PRIORS,
      'scripts/compose_religious_emphasis_sentence.py','scripts/check_religious_emphasis_sentence.py','tests/test_religious_emphasis_sentence.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_prince_sentence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='religious_emphasis_sentence_under_explicit_reading',document=FULL,**results,
      alignment=dict(**read(READING)['source'],statements=[117],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
      whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
