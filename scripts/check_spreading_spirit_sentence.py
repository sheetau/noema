"""Check source settings, shared-origin scopes and the complete third sentence."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_spreading_spirit_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,LIMITS,NODE_INFO,RULERS,PATH_PEOPLE,FOREIGN,PATH_SELECTORS,MODEL_SELECTORS,WITNESSES,MAPS,MODELS,parent,dependencies,build,closure
from scripts.compose_attitude_obstacle_struggle import GOAL_FIELDS,GOAL_ARGS,ASSIGNMENT
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/spreading-spirit-sentence-v1.md';READING='data/spreading-spirit-sentence-reading-v1.json'
INDEX='data/semantic-review-index-v198.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/attitude-obstacle-struggle-v1.json','reports/government-self-misunderstanding-v1.json','reports/social-attitude-paths-v1.json','reports/shared-liberty-policy-v1.json','reports/public-offers-sentence-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v1.json','artifacts/eighth-paragraph-source-v1/page-492.jpg','artifacts/eighth-paragraph-source-v1/kant-aa08-041.html')
DOMAIN=('a','b');SCENES=('reference','anchor','outer')
FOREIGN_VALUES=('a','b','a','b','a','b','a','b');PATH_VALUES=('a','b','a','a','b')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

def selector_definitions():
    text=''
    # Return actual native lambdas at each higher-order level; only leaf data are model inputs.
    for n,t in WITNESSES:
        if n in ('first','rest'):tail='';leaf=t;params='scene d';values='v scene'
        elif n=='history':tail='point d';leaf='c';params='scene d';values='v scene v point'
        elif n=='before':tail='left d right d';leaf='c';params='scene d';values='v scene v left v right'
        else:tail='step a';leaf=dict(MAPS)[n];params='scene d';values='v scene v step'
        text+='r z'+n+'[j[a] d d'+(' '+('d' if n=='history' else 'd d' if n=='before' else 'a') if tail else '')+'] '+leaf+'.'
        body='k z'+n+'[v bindings v reference '+values+']'
        if tail:body='i['+tail+']['+body+']'
        text+='d '+PATH_SELECTORS[n]+'[bindings j[a] reference d] h[d] '+t+'[i['+params+']['+body+']].'
    for n,t in MODELS:
        tail={'variables':'','factor':'','equations':'var a state '+ASSIGNMENT,'worlds':'state '+ASSIGNMENT,'matches':'left '+ASSIGNMENT+' right '+ASSIGNMENT,'evaluated':'point d'}[n]
        leaf={'variables':'j[a]','factor':'a','equations':'c','worlds':'d','matches':'c','evaluated':'c'}[n]
        sorts={'variables':'','factor':'','equations':' a '+ASSIGNMENT,'worlds':' '+ASSIGNMENT,'matches':' '+ASSIGNMENT+' '+ASSIGNMENT,'evaluated':' d'}[n]
        values={'variables':'','factor':'','equations':' v var v state','worlds':' v state','matches':' v left v right','evaluated':' v point'}[n]
        text+='r z'+n+'[j[a] d a'+sorts+'] '+leaf+'.'
        body='k z'+n+'[v bindings v reference v condition'+values+']'
        if tail:body='i['+tail+']['+body+']'
        text+='d '+MODEL_SELECTORS[n]+'[bindings j[a] reference d] h[a] '+t+'[i[condition a]['+body+']].'
    text+='r zcases[j[a] d d] c.d h26qd[bindings j[a] reference d] h[d] c[i[point d][k zcases[v bindings v reference v point]]].'
    return text
@lru_cache(None)
def fixture(roots,query,boundaries=(),extra='',selectors=False):
    d=deepcopy(catalog().document)
    for row in d['declarations']:
        if row['name'] in boundaries:
            assert row['result']=='truth';row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    prefix=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    prefix+='r zqualified[a a a d] c.d r53b[] h[a a a] e[i[ruler a office a community a][b point[k zqualified[v ruler v office v community v point]]]].'
    p=parse('p:'+prefix+(selector_definitions() if selectors else '')+extra);ns={r['name'] for r in p['declarations']}
    d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d.update(declarations=closure(d,(*roots,*ns)),statements=[])
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};seen={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(h26pp=lambda:'reference',h26pq=lambda:'outer',h26km=lambda:'outer',h26kn=lambda p:'anchor' if p=='outer' else 'reference',
        zqualified=lambda *a:a[-1]=='anchor')
    def record(n,b,r,value):seen.setdefault(n,set()).add((tuple(b.items),r));return value
    for n,t in WITNESSES:
        value={'first':'a','rest':SequenceValue(('b',),'"individual"'),'history':True,'before':True,
            'sender':'a','recipient':'b','activity':'a','process':'b','start':'reference','acted':'anchor','end':'anchor'}[n]
        v['z'+n]=lambda b,r,*a,n=n,value=value:record(n,b,r,value)
    for n,t in MODELS:
        value={'variables':SequenceValue(('a','b'),'"individual"'),'factor':'a','equations':True,'worlds':'outer','matches':True,'evaluated':True}[n]
        v['z'+n]=lambda b,r,*a,n=n,value=value:record(n,b,r,value)
    v['h26qc']=lambda b,r:record('conditions',b,r,SequenceValue(('a','b'),'"individual"'))
    v['zcases']=lambda b,r,t:record('cases',b,r,t=='outer')
    return v,seen

@lru_cache(None)
def settings_checks():
    local='q[k r57j['+args(PATH_VALUES)+' '+z('reference')+']].'
    d=fixture(('r57j',),local,('r54w','r56v'),selectors=True);v,seen=model(d)
    v['r54w']=lambda r,o,c,p,t:(r,o,c,t)==('a','b','a','anchor') and p in DOMAIN
    def domestic(*a):
        return (a[0],tuple(a[1].items),*a[2:5],a[-1])==('a',('b',),'a','b','reference','anchor') and a[5]('anchor') and a[6]('reference','anchor') and tuple(f('a') for f in a[7:14])==('a','b','a','b','reference','anchor','anchor')
    v['r56v']=domestic;assert run(d,v)==[True];assert all(rows=={(PATH_VALUES,'reference')} for rows in seen.values())
    w=dict(v);w['r54w']=lambda *a:a[3]=='a';assert run(d,w)==[False]
    w=dict(v);w['zrecipient']=lambda *a:'a';assert run(d,w)==[False]
    d2=fixture(('r57j',),local.replace(args(PATH_VALUES),args(('a','b','a','a','a'))),('r54w','r56v'),selectors=True)
    w=dict(v);w['r54w']=lambda *a:True;w['r56v']=lambda *a:True;assert run(d2,w)==[False]
    # Inspect every argument delivered to the already checked combined foreign body.
    q='q[k r57l['+args(FOREIGN_VALUES)+' '+z('reference')+']].'
    d=fixture(('r57l',),q,('r57i',),selectors=True);v,seen=model(d)
    def combined(*a):
        if a[:9]!=(*FOREIGN_VALUES,'reference') or tuple(a[20].items)!=('a','b') or a[21]!='anchor':return False
        witness=a[9:20];point='outer';first,rest,history,before,*maps=witness
        if (first(point),tuple(rest(point).items),history(point)(point),before(point)('reference',point))!=('a',('b',),True,True):return False
        if tuple(f(point)('a') for f in maps)!=('a','b','a','b','reference','anchor','anchor'):return False
        variables,equations,factor,worlds,matches,evaluated=a[22:28];s=FunctionValue(('individual',),'truth',lambda x:x=='a')
        return variables('b').items==('a','b') and equations('b')('a',s) and factor('b')=='a' and worlds('b')(s)=='outer' and matches('b')(s,s) and evaluated('b')('outer') and a[28]('outer') and not a[28]('anchor')
    v['r57i']=combined;assert run(d,v)==[True]
    assert set(seen)=={*PATH_SELECTORS,*MODEL_SELECTORS,'conditions','cases'}
    for n,rows in seen.items():assert rows=={((PATH_VALUES if n in PATH_SELECTORS else FOREIGN_VALUES),'reference')},(n,rows)
    for n in ('zcases','zevaluated','zmatches','zequations'):
        w=dict(v);w[n]=lambda *a:False;assert run(d,w)==[False],n
    w=dict(v);w['r57i']=unknown;rejects(d,w)
    # The general foreign clause receives the identical paths and fixed source current point.
    arrival_sorts=' '.join(['a']*8+['d']+['h[d] '+t for n,t in WITNESSES]+['d'])
    extra='r zarrival['+arrival_sorts+'] c.d r57a['+GOAL_FIELDS+'] e[b point[k zarrival['+GOAL_ARGS+' v point]]].'
    d=fixture(('r57k',),'q[k r57k['+args(FOREIGN_VALUES)+' '+z('reference')+']].',extra=extra,selectors=True);v,seen=model(d)
    v['zarrival']=lambda *a:a[:9]==(*FOREIGN_VALUES,'reference') and a[-1]=='anchor' and a[9]('outer')=='a' and a[13]('outer')('a')=='a'
    assert run(d,v)==[True]
    w=dict(v);w['h26kn']=lambda *a:'outer';assert run(d,w)==[False]
    return dict(domestic_scope_and_different_people=True,all_path_and_obstacle_selectors_use_exact_bindings=True,
        same_fixed_reference_and_source_current=True,unknown_rejected=True,
        boundary='r54w/r56v and r57a/r57i have prior native deep evidence. Here actual native selector functions and every source tuple reach those boundaries; no truth-only source-sentence primitive is used.')

@lru_cache(None)
def shared_origin_checks():
    q=''.join('q[k '+n+'['+args(('a','b','a','reference'))+']].' for n in ('r57m','r57n','r57o','r57p'))
    d=fixture(('r57m','r57n','r57o','r57p'),q,('r57j','r57k','r57l'));rows={}
    for case in ('same','different_origins','no_domestic','no_foreign','no_difficult_foreign'):
        v,_=model(d)
        v['r57j']=lambda r,o,c,origin,target,ref:(r,o,c,origin,target,ref)==('a','b','a','a','b','reference')
        v['r57k']=lambda *a:a==(*FOREIGN_VALUES,'reference');v['r57l']=v['r57k']
        if case=='different_origins':v['r57k']=lambda *a:a[:6]==FOREIGN_VALUES[:6] and a[6:] ==('b','a','reference');v['r57l']=v['r57k']
        if case=='no_domestic':v['r57j']=lambda *a:False
        if case=='no_foreign':v['r57k']=lambda *a:False;v['r57l']=lambda *a:False
        if case=='no_difficult_foreign':v['r57l']=lambda *a:False
        got=run(d,v);expected=[case=='same',case!='no_domestic',case!='no_foreign',case not in ('no_foreign','no_difficult_foreign')]
        assert got==expected,(case,got);rows[case]=got
    return dict(cases=rows,same_origin_required_in_whole=True,domestic_and_foreign_witnesses_exist_only_inside_ruler_condition=True,
        boundary='Previously checked r57j/k/l bodies are exact tuple boundaries. All existential witnesses and shared-origin conjunction execute over the full finite domain.')

@lru_cache(None)
def universal_current_checks():
    q=''.join('q[t[k '+n+'[]]['+z(t)+']].' for t in ('anchor','outer') for n in ('r57r','r57s','r57t','r57u'))
    d=fixture(('r57r','r57s','r57t','r57u'),q,('r57m','r57n','r57o','r57p'));rows={}
    for case in ('all','one_qualified_exception','exception_not_qualified','no_qualified','wrong_reference','wrong_present'):
        v,_=model(d)
        for n in ('r57m','r57n','r57o','r57p'):v[n]=lambda r,o,c,ref:ref=='reference'
        if case in ('one_qualified_exception','exception_not_qualified'):
            for n in ('r57m','r57n','r57o','r57p'):v[n]=lambda r,o,c,ref:(r,o,c)!=('b','a','b') and ref=='reference'
        if case=='exception_not_qualified':v['zqualified']=lambda r,o,c,t:(r,o,c)!=('b','a','b') and t=='anchor'
        if case=='no_qualified':v['zqualified']=lambda *a:False
        if case=='wrong_reference':v['h26pp']=lambda:'outer'
        if case=='wrong_present':
            v['zqualified']=lambda r,o,c,t:t=='anchor';v['h26kn']=lambda *a:'outer'
        got=run(d,v);expected=case not in ('one_qualified_exception','wrong_reference');assert got==[expected]*8,(case,got);rows[case]=got[:4]
    v,_=model(d)
    for n in ('r57m','r57n','r57o','r57p'):v[n]=lambda *a:True
    v['zqualified']=unknown;rejects(d,v)
    return dict(cases=rows,all_eight_ruler_role_community_tuples_native=True,outer_evaluation_does_not_move_present=True,
        no_assertion_of_actual_qualified_ruler_existence=True,boundary='Native universal condition and fixed source reference/current; prior source r53b and existential bodies are explicit boundaries.')

@lru_cache(None)
def discourse_checks():
    d=deepcopy(catalog().document);d.update(declarations=closure(d,('r57x',)),statements=[]);d=parse(format_graph(d,'compact')+'q[k r57x[]].')
    nodes=(*NODE_INFO,'h26pc');domain=(*nodes,'author','other');scenes=('reference','context')
    code=lambda n,rank:(rank,json.dumps(dict(kind='call',symbol=n,arguments=[]),sort_keys=True))
    norm=lambda xs:tuple((v.rank,json.dumps(json.loads(v.syntax),sort_keys=True)) if hasattr(v,'syntax') else v for v in xs)
    expected={'h236i':{(n,'author',code(t,3),'context') for n,t in (('h26qi','r57r'),('h26qk','r57t'),('h26qo','r57u'))},
        'h26qe':{('h26qj','author',code(t,3),code('r57w',2),'reference','context') for t in ('r53k','r55s')},
        'h26qf':{(n,'author',code('r57v',2),'h26qi','context') for n in ('h26qj','h26qn')},
        'h26qg':{('h26ql','author',code('r57r',3),code('r57s',3),code('r57t',3),'reference','context')},
        'h26qh':{('h26qm','author',code('r57r',3),code('r57t',3),code('r57u',3),'reference','context')},
        'ue':{('h26pc','h26qi','context'),('h26qj','h26qn','context'),('h26qk','h26qo','context')}}
    def values(rows):
        v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
        v.update({n:lambda n=n:n for n in nodes});v.update(wa=lambda:'author',h26pp=lambda:'reference',h26pq=lambda:'context')
        v.update({n:lambda *a,allowed=rs:norm(a) in allowed for n,rs in rows.items()});return v
    assert run(d,values(expected),domain,scenes)==[True];count=0
    for n,rs in expected.items():
        for row in rs:
            for i in range(len(row)):
                changed=deepcopy(expected);changed[n].remove(row);bad=list(row);bad[i]='other';changed[n].add(tuple(bad))
                assert run(d,values(changed),domain,scenes)==[False],(n,i);count+=1
        v=values(expected);v[n]=unknown;rejects(d,v,domain,scenes)
    for i,n in enumerate(nodes):
        for other in nodes[i+1:]:
            v=values(expected);v[n]=lambda other=other:other
            for name in expected:v[name]=lambda *a:True
            assert run(d,v,domain,scenes)==[False]
    # Opposing government, policy truth and all paths remain unknown in attribution.
    for n in ('h26pg','h26pn','h26pj','h245q','h26pr','h26p4','h26qd'):assert values(expected).get(n,unknown) is unknown
    return dict(argument_mutations=count,whole_main_and_focus_attributed=True,same_attitude_for_demonstrative_and_pronoun=True,
        both_antecedents_same_policy=True,additive_and_scalar_focus_separated=True,world_truth_not_executed=True,unknown_rejected=True)

FRAGMENTS=(
 ('Dieser Geist der Freiheit ',['r57v','r57w','r56n','r56j','r57x'],'先行二文の自由の型を支持する同じ態度。指示と内容の継承を結び、君主の功績や個人の信念の真理へ替えない。'),
 ('breitet sich ',['r56r','r56t','r56u','r57m'],'同じ態度の社会的取得の経路と現在までの保持。態度の表れと結果生成を分け、全員への完了とはしない。'),
 ('auch außerhalb aus, ',['r57j','r57k','r57m','r57s','r57t','r57x'],'同じ出発者から元の統治圏内への広がりを背景に、その外への広がりを追加する。国外の人が元の管轄外であることを保つ。'),
 ('selbst da, ',['r57p','r57t','r57u','r57x'],'同じ国外の広がりを、不利な障害条件を伴う適用例まで取り立てる。全外国への全称にしない。'),
 ('wo er ',['r57v','r57l','r57x'],'erをこの同じ態度へ照応させ、後続の障害と格闘を国外の同じ取得者の例へ接続する。'),
 ('mit äußeren Hindernissen ',['r564','r566','r57f','r57g'],'同じ取得・保持を潜在的に妨げる異なる複数条件で、同じ本人の内的態度とは別の環境条件。存在だけで妨害とせず、全条件を結ぶ。'),
 ('einer sich selbst mißverstehenden Regierung ',['r56z','r562','r563','r564','r57f'],'同じ政府に由来し、その政府自身に帰属する公的役割の自己理解が同じ内容の真偽と食い違う。職員の私見や他政府の誤解、誤解から障害への因果を混ぜない。'),
 ('zu ringen hat.',['r57b','r57d','r57e','r57h','r57i','r57l'],'同じ態度を担う人の対抗的努力があり、同じ障害背景で到達・保持に要る。達成不能からの空虚な必要性、法的義務、克服完了に替えない。'))
def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');cursor=890;clauses=[]
    for fragment,names,reading in FRAGMENTS:
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in names)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==1049 and sum(not c.isspace() for c in u['text'][890:cursor])==136
    return dict(status='spreading_spirit_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[890,cursor],text=u['text'][890:cursor]),selection=selection_binding(catalog(),[114]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_spreading_spirit_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=136,semantic_equivalence_automatically_proved=False,
        primary_evidence=[dict(path=p,observation='固定第三文と原刊492頁・AA本文。第三文の連続語句と前後の文脈を再読し、第四文ist/sei差は別に保持する。') for p in SOURCES],
        holistic_review=[
            '159文字・136非空白文字を八つの連続断片と一文全体で再読した。先行二文から同じ自由の型を受け、同じ態度への二箇所の照応、内外への広がり、障害のある場合への焦点、自己誤解・外的障害・格闘と必要性を同じ内容に接続した。',
            '先行二文の一般的な君主条件を保つ読みを明示した。該当する同じ君主の統治圏から、国内への広がりと困難な国外への広がりに共通する出発者を取る。特定の王・国・全世界の全取得者を原文にない指示対象として加えていない。',
            '政策内容の支持と政策の現実の実現を分けた。外国政府の自由政策や賛同・君主制は要求せず、社会的経路は発話の受領だけに限定しない。現実の証人を全仮定へ固定せず、候補の経路を供給する規約と深い内容を区別した。',
            'auchに国内側の背景を、selbst daにより不利な国外側の焦点を保持した。単なる連言だけで語用を済ませず、追加と期待上の取り立てを同じ閉じた全体・部分に帰属する。物理的な格闘の比喩を別事件として追加せず、態度を担う人の対抗的努力という採用解釈を明記した。',
            '政府の自己理解は組織に帰属する同じ項目について肯否と真偽を比較し、外的条件の政府由来を別に結ぶ。複数障害は条件ごとの同じ目標への妨害、全条件への対抗、同じ障害背景における必要性を保つ。政府の悪意、誤解が障害の原因、努力の十分性、克服完了は追加しない。',
            '原文の現在点、全称と存在量化、解釈基準、談話帰属の区別を保った。各基本関係の意味とモデル入力の条件を公開し、原文の真偽だけを返す記号で代用していない。検査境界と読みの判断を分け、既存17単位判断と先行二文763文字をそのまま保存する。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,CORE,BASIS,ANNOTATIONS,DOC,INVENTORY,*SOURCES,*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert c.document['statements'][:114]==old.document['statements'] and len(c.document['statements'])==115
    assert all(c.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==17
    for row in reviews:assert row['selection']==selection_binding(c,[s['index'] for s in row['selection']['statements']])
    for p,i in (('data/prince-sentence-reading-v1.json',112),('data/public-offers-sentence-reading-v1.json',113)):
        assert read(p)['selection']==selection_binding(c,[i])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert read(ANNOTATIONS)['entries']==read('data/public-offers-sentence-identifiers-v1.json')['entries']
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        t=format_graph(core,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==core
    ranks={};t=format_graph(core,'compact')
    for name in ('r57r','r57v','r57w'):
        for rank,label in enumerate(('','b','c','d','e')):
            try:parse(t+'q[e[r '+label+'[k '+name+'[]]][r '+label+'[k '+name+'[]]]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert ranks=={'r57r':3,'r57v':2,'r57w':2},ranks
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')['text']
    for n,(span,_) in NODE_INFO.items():assert u[span[0]:span[1]]
    assert u[963:965]=='er' and u[929:933]=='auch' and u[949:958]=='selbst da'
    return dict(preserved_statements=114,added_statements=1,preserved_whole_unit_reviews=17,preserved_prior_sentence_characters=763,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_reviewed_sentence_characters=136,minimum_quote_ranks=ranks,
        roundtrip_scope='new core compact/full/v2; inherited manuscript and meanings unchanged')
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('settings',settings_checks),('shared_origin',shared_origin_checks),('universal_current',universal_current_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*SOURCES,*PRIORS,'data/prince-sentence-reading-v1.json','data/public-offers-sentence-reading-v1.json',
        'scripts/compose_spreading_spirit_sentence.py','scripts/check_spreading_spirit_sentence.py','tests/test_spreading_spirit_sentence.py',
        'scripts/compose_clerical_duty_scope.py','scripts/compose_prince_sentence.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_attitude_obstacle_struggle.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='spreading_spirit_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[114],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
