"""Check the last sentence's shared progress, epoch name and scoped discourse."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_named_epoch_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,NODE_INFO,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_fifth_paragraph import calls,named

INDEX='data/semantic-review-index-v195.json';REPORT='reports/named-epoch-sentence-v1.json'
READING='data/named-epoch-sentence-reading-v1.json';DOC='docs/named-epoch-sentence-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=tuple('reports/'+n+'-v1.json' for n in ('present-epoch-sentence','present-shortfall-sentence','progress-indications-sentence'))
SOURCES=('artifacts/royal-writing-oversight-v1/page-491.jpg','artifacts/judgment-performance-quality-v1/kant-aa08-040.html',
    'artifacts/named-epoch-sentence-v1/dwb-jahrhundert.html','artifacts/named-epoch-sentence-v1/friedrich-ii-medal.html')
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=''):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+extra+query)
def run(d,v,domain,scenes):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain,scenes):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def component_checks():
    domain=('epoch','other','person','office');scenes=('reference','actual','past','now','outside')
    extra='r zepoch[] a.r zouter[] d.'
    q='q[t[k r5vs[k zepoch[]]][k zouter[]]].q[t[c[k r5vt[]][k zepoch[]]][k zouter[]]].q[t[k r5vu[]][k zouter[]]].'
    d=fixture(('r5vs','r5vt','r5vu'),q,('r5u4',),extra);rows={}
    def values(variant):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        points=('past',) if variant=='single_point' else ('past','now')
        v.update(h26ki=lambda:'epoch',h26mu=lambda:'person',h26mw=lambda:'office',h26km=lambda:'actual',h26kj=lambda:'reference',
            h26kl=lambda c:'actual',zepoch=lambda:'other' if variant=='other_epoch' else 'epoch',zouter=lambda:'outside',
            r5u4=lambda:Content(scenes,(variant!='no_progress',)*len(scenes)),aa=lambda p:p=='person' and variant!='not_person',
            h257z=lambda r,c,t:(r,c)==('reference','actual') and t in ('past','now'),
            ic=lambda a,b,c:(a,b,c)==('past','now','actual'),
            h26ab=lambda e,r,c,t:(e,r,c)==('epoch','reference','actual') and t in points and variant!='empty_epoch',
            h26mx=lambda p,o,t:(p,o)==('person','office') and t==('outside' if variant=='no_overlap' else 'past'))
        if variant=='wrong_holder':v['h26mx']=lambda p,o,t:(p,o,t)==('other','office','past')
        if variant=='wrong_office':v['h26mx']=lambda p,o,t:(p,o,t)==('person','other','past')
        if variant=='foreign_history':v['h257z']=lambda r,c,t:r=='outside'
        return v
    expected={'baseline':[True,True,True],'no_progress':[False,True,False],'single_point':[True,True,True],
        'other_epoch':[False,False,True],**{v:[True,False,False] for v in ('not_person','no_overlap','empty_epoch','wrong_holder','wrong_office','foreign_history')}}
    for variant,wanted in expected.items():
        got=run(d,values(variant),domain,scenes);assert got==wanted,(variant,got,wanted);rows[variant]=got
    for n in ('r5u4','h26mx','h257z','h26ab'):
        v=values('baseline');v[n]=unknown;rejects(d,v,domain,scenes)
    return dict(cases=rows,native_rmw_and_interval=True,progress_boundary='r5u4: already checked current progress, both truth values',
        no_century_duration_or_tenure_identity=True,unknown_rejected=True)

@lru_cache(None)
def discourse_checks():
    d=fixture(('r5vv',),'q[k r5vv[]].');ctx='context';author='author'
    nodes=(*NODE_INFO,'h26mj','h26la','h26mu','h26mv','h26mw','h26ki')
    domain=(*nodes,author,'other');scenes=(ctx,)
    expected={'h236i':{('h26m4',author,('r5vu',3),ctx)},
        'h26my':{('h26m5',author,('r5vu',3),('r5u4',3),ctx)},
        'h26mz':{('h26na',author,'h26ki',('r5vs',3),('r5vt',0),ctx)},
        'h26m2':{('h26na',author,'h26ki','h26mu',('r5vt',0),ctx)},
        'h26m3':{('h26m6',author,'h26la','h26ki',ctx)},
        'hzih':{('h26nb','h26mv','h26mu',ctx)},
        'ue':{('h26mj','h26m4',ctx),('h26m7','h26na',ctx)}}
    def values(wanted):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update({n:lambda n=n:n for n in nodes});v.update(wa=lambda:author,h26k7=lambda:ctx)
        v.update({n:lambda *args,rows=rows:normalized(args) in rows for n,rows in wanted.items()});return v
    assert run(d,values(expected),domain,scenes)==[True];mutations=0
    for n,rows in expected.items():
        for row in rows:
            wanted=deepcopy(expected);wanted[n].remove(row);assert run(d,values(wanted),domain,scenes)==[False]
            for pos in range(len(row)):
                changed=list(row);changed[pos]='other';wanted=deepcopy(expected);wanted[n].remove(row);wanted[n].add(tuple(changed))
                assert run(d,values(wanted),domain,scenes)==[False],(n,pos);mutations+=1
        v=values(expected);v[n]=unknown;rejects(d,v,domain,scenes)
    for i,n in enumerate(nodes):
        for other in nodes[i+1:]:
            v=values(expected);v[n]=lambda other=other:other
            for key in expected:v[key]=lambda *args:True
            assert run(d,v,domain,scenes)==[False]
    return dict(required_relations=sum(map(len,expected.values())),argument_mismatches=mutations,
        nodes_and_person_and_designation_distinct=True,quoted_progress_not_executed=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0014');cursor=675;clauses=[]
    for fragment,names,reading in (
        ('In diesem Betracht ',['h26my','r5u4'],'直前までの同じ開放・障害漸減という進行の観点に限る。'),
        ('ist ',['r5vu','h236i'],'同じ時代についての性質の肯定を著者に帰属する。'),
        ('dieses Zeitalter ',['h26m3','h26ki','h26la'],'第一文の現在の時代と同じ対象を指す。'),
        ('das Zeitalter der Aufklärung, ',['r5vs','r5u4'],'同じ進行を特徴とする時代であり、達成済みの時代ではない。'),
        ('oder ',['h26mz'],'同じ時代への説明的な第二呼称を導入する。'),
        ('das Jahrhundert ',['rmw','r5vt','h26m2'],'王職の在職と重なる同じ時代を、その人物によって特徴づけて呼ぶ。厳密な百年という長さは要求しない。'),
        ('Friederichs.',['hzih','h26mu','h26mv','h26mw','h26mx'],'フリードリヒ二世を指す名称を同じ人物に結び、その人物の時代という呼称にする。')):
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in names)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==778
    return dict(status='named_epoch_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[675,778],text=u['text'][675:778]),selection=selection_binding(catalog(),[111]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_named_epoch_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=90,semantic_equivalence_automatically_proved=False,
        primary_evidence=[dict(path=SOURCES[0],observation='原刊491頁の全段落と末尾のFriederichsを目視照合。'),
            dict(path=SOURCES[1],url='https://korpora.org/kant/aa08/040.html',observation='In diesem Betrachtと二つの時代呼称を確認。AAのFriedrichsへ原刊の綴りを変更しない。'),
            dict(path=SOURCES[2],url='https://www.dwds.de/wb/dwb/jahrhundert',observation='DWB IV,II (1877), Sp.2243: Zeitalter又はMenschenalterという広い用法を記載。カントの唯一の読みの証明には用いない。'),
            dict(path=SOURCES[3],url='https://ikmk.smb.museum/object?id=18202077',observation='ベルリン国立博物館の1786年追悼メダル記録。Friedrich II.、王職と1740–1786を人物参照確認に用いる。年号は原文の追加主張にしない。')],
        holistic_review=[
            '103文字・90非空白文字を全語句と句読点まで覆った。第一文の肯定側を同じ進行の内容で受け、第二文の不足と第三文の徴候を撤回していない。',
            '観点限定と指示の照応を別に保持し、時代名を無条件な達成又は歴史全体の判断へ拡げていない。徴候による確実な真理保証も追加していない。',
            '啓蒙の時代と人物の時代の呼称を同じ対象の説明関係とし、一般的な同義語や選言にしていない。在職と重なる区間のプロフィールだけでは足りず、同じ人物で特徴づけて呼ぶ関係を持つ。',
            '人物の参照と文字列は分けた。原刊の綴りを保存し、暦年や在位の端点を主張に加えず、次段落にある君主の義務・寛容・解放の全叙述はまだ取り込んでいない。',
            '引用段階と内容の接続を局所検査し、意味判断はこれと原刊・補助一次資料・全語句と文全体の読解を合わせて行った。段落全体の登録は別に行う。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,*SOURCES,*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:111]==old.document['statements'] and len(new.document['statements'])==112
    assert all(new.entries[n]==e for n,e in old.entries.items())
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==16
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for i,stem in enumerate(('present-epoch-sentence','present-shortfall-sentence','progress-indications-sentence'),108):
        assert read('data/'+stem+'-reading-v1.json')['selection']==selection_binding(new,[i])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert read(ANNOTATIONS)['entries'][:-1]==read('data/progress-indications-sentence-identifiers-v1.json')['entries']
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    assert len(calls(new.entries['r5vs']['declaration'],'r5u4'))==1
    assert not calls(new.entries['r5vs']['declaration'],'r5u2')
    label=new.entries['r5vt']['declaration'];assert len(calls(label,'rmw'))==1
    assert calls(label,'h26kl')[0]['arguments']==[named('h26km')]
    assert calls(label,'h26ab')[0]['arguments'][1]==named('h26kj')
    d=parse((ROOT/CORE).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        s=format_graph(d,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==d
    return dict(preserved_statements=111,added_statements=1,preserved_whole_unit_reviews=16,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        new_reviewed_sentence_characters=90,roundtrip_scope='new core compact/full/v2; old manuscript and meaning entries unchanged')
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('components',component_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*SOURCES,*PRIORS,
        'scripts/compose_named_epoch_sentence.py','scripts/check_named_epoch_sentence.py','tests/test_named_epoch_sentence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py','scripts/check_fifth_paragraph.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_present_epoch_sentence.py'}
    return dict(status='named_epoch_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[111],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
