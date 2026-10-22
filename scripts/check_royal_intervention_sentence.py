"""Check sentence integration, quoted presentation and complete source reading."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_royal_intervention_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,NODES,NODE_INFO,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_royal_intervention_conditions import DOMAIN,SCENES,EXTRA,TEN,base as condition_base

INDEX='data/semantic-review-index-v190.json'
REPORT='reports/royal-intervention-sentence-v1.json'
READING='data/royal-intervention-sentence-reading-v1.json'
DOC='docs/royal-intervention-sentence-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=tuple('reports/'+n+'-v1.json' for n in ('royal-intervention-conditions','royal-loss-comparison','royal-insight-reproof',
    'royal-despotic-support','royal-dignity-loss','royal-writing-oversight','monarchical-religion-sentence'))

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
def base(d,bindings=TEN):
    v=condition_base(d,bindings)
    v.update(h26je=lambda:'reference',wa=lambda:'author',h255n=lambda:'outside')
    return v
def rejects_unknown(d,v,domain=DOMAIN):
    try:run(d,v,domain)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')
def query(root):return 'q[t[k '+root+'[k zbindings[] k zreference[]]][k zcase[]]].'

@lru_cache(None)
def general_content_checks():
    rows={}
    for root,target in (('r5ro','r5qz'),('r5rp','r5ra'),('r5rq','r5rb'),('r5rr','r5rc'),('r5rs','r5rd')):
        d=fixture((root,),'q[t[k '+root+'[]][k zcase[]]].',(target,));v=base(d)
        v[target]=lambda r:content({'case'} if r=='reference' else set())
        assert run(d,v)==[True]
        v['h26je']=lambda:'outside';assert run(d,v)==[False]
        v[target]=unknown;rejects_unknown(d,v);rows[root]=target
    return dict(same_general_reference=rows,unknown_rejected=True,boundaries=list(rows.values()))

@lru_cache(None)
def evaluative_depiction_checks():
    d=fixture(('r5ru','r5rf'),query('r5ru')+query('r5rf'),('r5pc','r2ui'))
    def values():
        v=base(d)
        v.update(dg=lambda *a:a==('beta','case'),df=lambda *a:a==('alpha','beta','case'),
            h26il=lambda *a:a==('beta','beta','beta','case','case'),
            h26im=lambda *a:a==('alpha','beta','beta','case','case'))
        return v
    rows={}
    for missing in (None,'h26im','h26il','dg','df','r2ui','h234f','r5pc','h26in'):
        v=values()
        if missing:v[missing]=lambda *a:False
        actual=run(d,v);assert actual==[missing in (None,'h26im'),missing is None],(missing,actual)
        rows[missing or 'baseline']=actual
    contrasts=0
    for name,args in (('h26il',5),('h26im',5),('r2ui',4),('h234f',3),('r5pc',8),('h26in',4)):
        for pos in range(args):
            v=values();old=v[name]
            def mismatch(*a,old=old,pos=pos):
                a=list(a);a[pos]='mismatch';return old(*a)
            v[name]=mismatch;assert run(d,v)==[name=='h26im',False],(name,pos);contrasts+=1
    v=values();v['h26im']=unknown;rejects_unknown(d,v)
    bare=fixture(('r5ru',),query('r5ru'),('r5pc','r2ui'));v=values();v['h26im']=unknown
    assert run(bare,v)==[True]
    v=values();v['h26il']=unknown;rejects_unknown(bare,v)
    return dict(same_event_without_approval=rows,argument_mismatches=contrasts,
        bare_scrutiny_does_not_require_evaluation=True,unknown_rejected=True,boundaries=['r5pc','r2ui'])

@lru_cache(None)
def adapter_checks():
    # Individually validated semantic cores are boundaries here; every argument
    # used by the new adapters is tested rather than enumerating their internals.
    specs={
      'r5rt':{'r5pc':(0,2,3,4,5,6,'p','p'),'dg':(7,'p'),'df':(0,7,'p'),'h26in':(7,4,'p','p')},
      'r5rv':{'r5qb':(0,1,2,8,'p','p'),'r5qf':(1,0,2,9,6,8,'p','p')},
      'r5rw':{'r5qa':(0,2,9,6,8,'p','p')},
      'r5rx':{'r5pv':('p',)},
      'r5ry':{'r5pu':(0,2,6,'p','p')},
      'r5rz':{'r5py':(0,2,6,7,'p','p')}}
    rows={}
    for root,spec in specs.items():
        d=fixture((root,),query(root),tuple(n for n in spec if n.startswith('r')))
        def values(binding=TEN):
            v=base(d,binding)
            for name,slots in spec.items():
                expected=tuple('case' if s=='p' else binding[s] for s in slots)
                if name=='r5pv':v[name]=lambda *a,expected=expected:content({'case'} if a==expected else set())
                else:v[name]=lambda *a,expected=expected:a==expected
            return v
        assert run(d,values())==[True],root
        for name,slots in spec.items():
            v=values();v[name]=(lambda *a:content(set())) if name=='r5pv' else (lambda *a:False)
            assert run(d,v)==[False],(root,name)
            v=values();v[name]=unknown;rejects_unknown(d,v)
            for pos in range(len(slots)):
                v=values();old=v[name]
                def mismatch(*a,pos=pos,old=old):
                    a=list(a);a[pos]='mismatch';return old(*a)
                v[name]=mismatch;assert run(d,v)==[False],(root,name,pos)
        used={s for slots in spec.values() for s in slots if type(s) is int}
        for pos in range(10):
            binding=tuple('beta' if j==pos else 'alpha' for j in range(10));v=values(binding)
            assert run(d,v)==[True]
            v['zbindings']=lambda:SequenceValue(('alpha',)*10,'"individual"')
            assert run(d,v)==[pos not in used],(root,pos)
        for length in (9,11):
            v=values();v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False]
        v=values();v['zreference']=lambda:'outside';assert run(d,v)==[True]  # General reference is not the inner point.
        v=values();v['zcase']=lambda:'outside';assert run(d,v)==[False]
        rows[root]=dict(projected_positions=sorted(used),boundaries=list(spec),unknown_rejected=True)
    return dict(adapters=rows,exact_ten_binding_length=True,inner_reference_is_case=True,literal_and_contextual_application_separate=True)

@lru_cache(None)
def discourse_checks():
    d=fixture(('r5sa',),'q[k r5sa[]].');q=lambda n:(n,2);whole=('r5ro',3);a='author';ctx='outside';ref='reference'
    head=(a,whole,q('r5re'))
    expected={
      'h236i':{(node,a,(target,3),ctx) for node,target in (('h26jn','r5ro'),('h26jo','r5rp'),('h26jp','r5rq'),('h26jq','r5rr'),('h26jr','r5rs'))},
      'h26jh':{('h26js',*head,q('r5rg'),ref,ctx)},
      'h26jl':{('h26jt',*head,q('r5rt'),q('r5rf'),ref,ctx)},
      'h26jf':{('h26ju',*head,q('r5ru'),q('r5rf'),ref,ctx)},
      'h26jg':{('h26ju',*head,q('r5ru'),q('r5rf'),ref,ctx)},
      'h26ji':{('h26j2',*head,*(q(n) for n in ('r5rh','r5ri','r5rj','r5rk')),ref,ctx)},
      'h26jj':{('h26jr',*head,*(q(n) for n in ('r5rh','r5rj','r5rm')),ref,ctx)},
      'h26jk':{('h26jw',*head,q('r5rv'),q('r5rw'),ref,ctx)},
      'h26jm':{('h26jv',a,'h26jy',whole,q('r5re'),*(q(n) for n in ('r5rh','r5rz','r5rx','r5ry')),ref,ctx)},
      'ue':{(x,y,ctx) for x,y in (('h26h5','h26jn'),('h26jo','h26jp'),('h26jp','h26jq'),('h26jt','h26ju'),('h26ju','h26jv'),('h26jv','h26jr'),('h26jr','h26jw'))}}
    domain=(*NODES,a,'other');missing=[(key,row) for key,values in expected.items() for row in sorted(values)]
    def values(wanted):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update(h26je=lambda:ref,wa=lambda:a,h255n=lambda:ctx)
        v.update({n:lambda n=n:n for n in NODES})
        v.update({n:lambda *args,values=values:normalized(args) in values for n,values in wanted.items()});return v
    v=values(expected);assert run(d,v,domain)==[True]
    for n in ('h26jd','h26ir','h26im','h26i4','h26dq','h26iz','h26jc'):assert v[n] is unknown,n
    mutations=0
    for key,row in missing:
        wanted=deepcopy(expected);wanted[key].remove(row);assert run(d,values(wanted),domain)==[False]
        for pos in range(len(row)):
            wanted=deepcopy(expected);wanted[key].remove(row);changed=list(row);changed[pos]='mismatch';wanted[key].add(tuple(changed))
            assert run(d,values(wanted),domain)==[False],(key,pos);mutations+=1
    for key,left,right in (('h26ji',4,6),('h26jj',4,5),('h26jk',4,5),('h26jl',4,5),('h26jm',7,8)):
        wanted=deepcopy(expected);row=list(next(iter(wanted[key])));row[left],row[right]=row[right],row[left];wanted[key]={tuple(row)}
        assert run(d,values(wanted),domain)==[False],key
    # Isolate the distinctness clauses even when all presentation relations accept.
    for i,node in enumerate(NODES):
        for other in NODES[i+1:]:
            v=values(expected);v[node]=lambda other=other:other
            for key in expected:v[key]=lambda *a:True
            assert run(d,v,domain)==[False],(node,other)
    for key in expected:
        v=values(expected);v[key]=unknown;rejects_unknown(d,v,domain)
    return dict(required_relations=len(missing),argument_mismatches=mutations,all_node_pairs_distinct=True,
        condition_side_manner_extent_and_literal_application_order=True,quoted_truth_not_executed=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013');cursor=3645;clauses=[]
    for fragment,names,reading in (
      ('Es thut ',['r5qu','r5qz'],'以下の介入を前件とした一般的帰結。現実の行為生起は断言しない。'),
      ('selbst ',['h26jh','r5rg'],'君主自身の威厳にまで及ぶ取り立て。'),
      ('seiner Majestät Abbruch, ',['r5pk','r5pj','h26io'],'同じ君主の公的威厳への因果的な損傷。役職喪失や人気だけにはしない。'),
      ('wenn er sich hierin mischt, ',['r5qt','r5qu','r5qs'],'同じ共同体の宗教的な理解と選択への介入。二側を尽くす二者択一に限定しない。'),
      ('indem er die Schriften, ',['h26jl','r5rt','r5rf'],'同じ作品への統治的内容審査を、介入の具体的な仕方として結ぶ。'),
      ('wodurch seine Unterthanen ',['r5pc','r5ni','r5pa'],'同じ臣民が同じ書かれた表現を実際に使う検討。'),
      ('ihre Einsichten ins Reine zu bringen suchen, ',['r5pb','r5o7','h26hf'],'本人の理解内容の明確化を目指す試み。成功や正しい認識の達成を要求しない。'),
      ('seiner Regierungsaufsicht würdigt, ',['r5ru','r5rf','h26jf','h26jg'],'同じ職による内容審査を、自分の配慮に値する扱いとして示す描写と、その評価からの著者の批判的距離。'),
      ('sowohl ',['h26ji','r5rh','r5ri'],'後続のals auchと、二つの条件付きの側をともに並べる。'),
      ('wenn er dieses aus eigener höchsten Einsicht thut, ',['r5qm','r5pr','r5pq','r5qv'],'同じ介入を、自分が最上だとみなす見識に基づいてする場合。見識の客観的真理と区別する。'),
      ('wo er sich dem Vorwurfe aussetzt: ',['r5py','r5rz','r5qv'],'同じ介入を理由とした、正当化可能な批判への曝露。既に誰かが発言した事実は不要。'),
      ('Caesar non est supra Grammaticos', ['h26jm','h26jy','r5rx','r5ry'],'引用表現、文法等の専門判断への字義的な統治権限の限界、宗教的認識への文脈的適用を区別して結ぶ。'),
      (', als auch ',['h26ji','r5rj','r5rk'],'もう一方も当てはまる条件付きの側。排他性を追加しない。'),
      ('und noch weit mehr, ',['h26jj','r5rs','r5rm','r5qq'],'第一側を撤回しない大きな追加損傷の比較。同じ尺度・共通無介入基準・全対応対を保つ。'),
      ('wenn er seine oberste Gewalt ',['r5qb','r5qn','r5qw'],'同じ君主が保持する最高の統治職の権能を実際に使う条件。'),
      ('so weit erniedrigt, ',['r5rv','r5qf','h26jk'],'同じ最高職に不相応な支援手段化。その程度を後続の同じ支援で具体化する。'),
      ('den geistlichen Despotism ',['r5p6','r2qa','h26i3'],'宗教的領域の個人的裁量に歯止めのない支配。担い手への正式な聖職者資格は追加しない。'),
      ('einiger Tyrannen ',['r5p3','r5p4','r5p7'],'同じ共同体の複数の専制支配者。各支配者に対応する仕組みを許す。'),
      ('in seinem Staate ',['r5p4','r5p6','r5qb'],'同じ君主の同じ政治的共同体と最高職。'),
      ('gegen seine übrigen Unterthanen ',['r5p5','r5qa','r5qf','h26i6'],'その複数者を除く同じ臣民全体を対象にする。全員の服属成功や現在の被害を補わない。'),
      ('zu unterstützen.',['r5rw','r5qa','h26i4','h26jk'],'同じ支配仕組みの運用・維持への実際的支援。単なる賛同・意図や別活動へ替えない。')):
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in names),names
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==4155
    pages=read('data/royal-writing-oversight-reading-v1.json')['primary_pages']
    assert len(pages)==2 and all(digest((ROOT/p['path']).read_bytes())==p['sha256'] for p in pages)
    for n,(span,_) in NODE_INFO.items():assert u['text'][slice(*span)].strip(),n
    quote=dict(range=[3935,3967],text=u['text'][3935:3967],form='h26jy',occurrence='h26jv',
        literal='r5rx',application='r5ry',reproof='r5rz')
    assert quote['text']=='Caesar non est supra Grammaticos'
    return dict(status='royal_intervention_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[3645,4155],text=u['text'][3645:4155]),selection=selection_binding(catalog(),[107]),
        clauses=clauses,quotation=quote,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_royal_intervention_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=sum(not c.isspace() for c in u['text'][3645:4155]),
        semantic_equivalence_automatically_proved=False,original_pages=pages,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/040.html',lines='9–16',observation='原刊490–491頁で最終文を通読。固定転記と原刊のGrammaticosの大文字を保持。')],
        holistic_review=[
          '原刊490頁末尾から491頁冒頭までのEs thutからunterstützenまでを通読した。固定転記の全435非空白文字を連続した語句対応に置き、次段落を混入させていない。',
          'erとseiner/seine/seinemは同じ君主と共同体、Unterthanenとihreは同じ臣民と本人の理解内容へ結ぶ。前文の市民的秩序への監督と、ここで批判する宗教的理解内容への統治的介入を区別した。',
          '一般的な仮定範囲を結果や前件の成立で選別しない。基本介入からの損傷を独立に保持し、二側は排他的・網羅的な二択にしない。比較がない場面で他の条件付き帰結を消さない。',
          'wodurch以下は同じ書かれた表現を用いる実際の試みとその目標を結ぶ。本人の理解の明確化に成功したとはしていない。',
          'würdigtは配慮に値するものとして扱う描写と著者の批判的距離を同じ出来事へ結ぶ。著者の是認・悪意・単純な語義反転を加えない。selbstは君主自身の威厳にまで及ぶ点を取り立てる。',
          '自身の最高の見識は君主自身の基準での評価とし、著者が全知や真理を保証したことにしない。批判への曝露は同じ行為に由来する正当化可能な候補であり、批判発言済みとはしない。',
          '格言の表現対象と引用箇所を分けた。字義的な文法等の原則と宗教的認識への適用を別の合成内容へ結び、適用は明示した解釈とした。専門家の無謬性や歴史的な直接典拠を補わない。',
          '宗教的専制を支える活動では、同じ最高職の実際の権能使用と、不相応な補助手段化と、同じ複数者・残余臣民全体への支援を共有する。役職移譲や権能の物理的減少に替えない。',
          '二側の比較は同じ公的威厳の尺度、共通の無介入基準、背景を対応させた全対での因果的損傷を使う。結果に応じた対の除外や無関係な事例の全交差比較へ替えない。nochとweitに数値比率又は時間的順序を加えない。',
          '全文と部分の著者帰属、二条件の並列、手段説明、程度具体化、評価的描写、引用、順序を結んだ。引用した内容の真理を実行しない。全文は明示した読みの下で確認したが、第六段落全体は別途通読する。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:107]==old.document['statements'] and len(new.document['statements'])==108
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    prior=read('data/monarchical-religion-sentence-reading-v1.json');assert prior['selection']==selection_binding(new,[106])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    before=read('data/monarchical-religion-sentence-identifiers-v1.json');after=read(ANNOTATIONS)
    for key in before:
        if key not in ('document','document_sha256'):assert before[key]==after[key]
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            s=format_graph(doc,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==doc
    assert reading_record()['newly_reviewed_sentence_characters']==435
    return dict(preserved_statements=107,added_statements=1,preserved_whole_unit_reviews=len(reviews),preserved_opening_sentence_characters=3114,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,new_reviewed_sentence_characters=435)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('general_content',general_content_checks),('evaluation',evaluative_depiction_checks),('adapters',adapter_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*PRIORS,*(x['path'] for x in read(READING)['original_pages']),
        'data/monarchical-religion-sentence-reading-v1.json','data/royal-writing-oversight-reading-v1.json',
        'scripts/compose_royal_intervention_sentence.py','scripts/check_royal_intervention_sentence.py','scripts/compose_royal_intervention_conditions.py',
        'tests/test_royal_intervention_sentence.py','scripts/check_royal_intervention_conditions.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','scripts/check_covenant_nullity.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='royal_intervention_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[107],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
