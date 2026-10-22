"""Check same-witness extension, source discourse and the complete fourth sentence."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_manifest_example_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,LIMITS,NODE_INFO,FOREIGN,EXTRAS,parent,dependencies,build,closure,quant,args as variables
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/manifest-example-sentence-v1.md';READING='data/manifest-example-sentence-reading-v1.json'
INDEX='data/semantic-review-index-v199.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/manifest-example-v1.json','reports/civic-peace-concord-v1.json','reports/spreading-spirit-sentence-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v2.json','artifacts/eighth-paragraph-source-v1/page-492.jpg','artifacts/eighth-paragraph-source-v1/kant-aa08-041.html')
DOMAIN=('a','b');SCENES=('reference','anchor','outer');FOREIGN_VALUES=('a','b','a','b','a','b','a','b')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),domain=DOMAIN):
    d=deepcopy(catalog().document)
    for row in d['declarations']:
        if row['name'] in boundaries:
            assert row['result']=='truth';row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    prefix=''.join('r z'+n+'[] '+('a' if n in domain else 'd')+'.' for n in (*domain,*SCENES))
    prefix+='r zqualified[a a a d] c.d r53b[] h[a a a] e[i[ruler a office a community a][b point[k zqualified[v ruler v office v community v point]]]].'
    p=parse('p:'+prefix);ns={r['name'] for r in p['declarations']}
    d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d.update(declarations=closure(d,(*roots,*ns)),statements=[])
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def model(d,domain=DOMAIN):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*domain,*SCENES)})
    v.update(h26pp=lambda:'reference',h26q2=lambda:'outer',h26km=lambda:'outer',h26kn=lambda p:'anchor' if p=='outer' else 'reference',zqualified=lambda *a:a[-1]=='anchor')
    return v

@lru_cache(None)
def settings_checks():
    names=(*FOREIGN,*EXTRAS);query='q[k r6ai['+args((*names,'reference'))+']].'
    d=fixture(('r6ai',),query,('r6af',),names);v=model(d,names)
    expected=('example','sourcegovernment','rulingoffice','community','sourcegroup','sourcetopic','government','foreignoffice','foreigncommunity','targetgroup','targettopic','reference','anchor','anchor')
    seen=[];v['r6af']=lambda *a:seen.append(a) is None and a==expected
    assert run(d,v,names)==[True];assert seen==[expected]
    for i in range(len(expected)):
        changed=list(expected);changed[i]='outer' if i>=11 else 'origin'
        w=dict(v);w['r6af']=lambda *a,changed=tuple(changed):a==changed;assert run(d,w,names)==[False]
    w=dict(v);w['h26kn']=lambda *a:'outer';assert run(d,w,names)==[False]
    w=dict(v);w['r6af']=unknown;rejects(d,w,names)
    return dict(all_fourteen_example_arguments_checked=True,source_and_target_roles_not_aliased=True,
        same_prior_reference_and_present=True,unknown_rejected=True,boundary='r6af is the prior manifest-example boundary. All fourteen delivered arguments use distinct individuals to detect swaps, including both current points.')

@lru_cache(None)
def witness_checks():
    d=fixture(('r6aj',),'q[k r6aj['+args((*FOREIGN_VALUES,'reference'))+']].',('r57l','r6ai'));v=model(d)
    v['r57l']=lambda *a:a==(*FOREIGN_VALUES,'reference')
    v['r6ai']=lambda *a:a[:8]==FOREIGN_VALUES and a[8:14]==('b',)*6 and a[-1]=='reference'
    assert run(d,v)==[True];rows={}
    for case in ('no_prior','no_example','different_government','different_origin','different_reference'):
        w=dict(v)
        if case=='no_prior':w['r57l']=lambda *a:False
        if case=='no_example':w['r6ai']=lambda *a:False
        if case in ('different_government','different_origin'):
            changed=list(FOREIGN_VALUES);i=3 if case=='different_government' else 6;changed[i]='a' if changed[i]=='b' else 'b'
            w['r6ai']=lambda *a,changed=tuple(changed):a[:8]==changed
        if case=='different_reference':w['r6ai']=lambda *a:a[-1]=='outer'
        assert run(d,w)==[False];rows[case]=False
    for n in ('r57l','r6ai'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    query='q['+quant(FOREIGN,'e[k r6ak['+variables(FOREIGN)+' '+z('reference')+']][v government]')+'].'
    p=fixture(('r6ak',),query);assert run(p,model(p))==[True]
    d=fixture(('r6al',),'q[k r6al['+args(('a','b','a','reference'))+']].',('r57j','r6aj'));v=model(d)
    v['r57j']=lambda *a:a==('a','b','a','a','b','reference');v['r6aj']=lambda *a:a==(*FOREIGN_VALUES,'reference')
    assert run(d,v)==[True]
    for case in ('different_origins','no_domestic','no_foreign'):
        w=dict(v)
        if case=='different_origins':w['r6aj']=lambda *a:a==(*FOREIGN_VALUES[:6],'b','a','reference')
        if case=='no_domestic':w['r57j']=lambda *a:False
        if case=='no_foreign':w['r6aj']=lambda *a:False
        assert run(d,w)==[False];rows[case]=False
    return dict(cases=rows,six_new_witnesses_extend_same_prior_tuple=True,government_projection_all_256_tuples=True,
        prior_domestic_and_foreign_common_origin_preserved=True,unknown_rejected=True,
        boundary='r57l/r6ai and then r57j/r6aj are explicit prior/body boundaries. Existentials, shared variables, conjunctions and the referent projection execute natively.')

@lru_cache(None)
def universal_checks():
    q=''.join('q[t[k r6an[]]['+z(t)+']].' for t in ('anchor','outer'))
    d=fixture(('r6an',),q,('r6al',));rows={}
    for case in ('all','qualified_exception','unqualified_exception','no_qualified','wrong_reference'):
        v=model(d);v['r6al']=lambda *a:a[-1]=='reference'
        if case in ('qualified_exception','unqualified_exception'):v['r6al']=lambda r,o,c,ref:(r,o,c)!=('b','a','b') and ref=='reference'
        if case=='unqualified_exception':v['zqualified']=lambda r,o,c,t:(r,o,c)!=('b','a','b') and t=='anchor'
        if case=='no_qualified':v['zqualified']=lambda *a:False
        if case=='wrong_reference':v['h26pp']=lambda:'outer'
        got=run(d,v);assert got==[case not in ('qualified_exception','wrong_reference')]*2;rows[case]=got
    v=model(d);v['r6al']=lambda *a:True;v['zqualified']=unknown;rejects(d,v)
    return dict(cases=rows,all_qualified_ruler_tuples_native=True,outer_point_does_not_move_source_present=True,unknown_rejected=True)

@lru_cache(None)
def discourse_checks():
    d=deepcopy(catalog().document);d.update(declarations=closure(d,('r6ao',)),statements=[]);d=parse(format_graph(d,'compact')+'q[k r6ao[]].')
    nodes=(*NODE_INFO,'h26qi');domain=(*nodes,'author','other');scenes=('reference','context')
    def code(n,rank=3,ref=False):return rank,json.dumps(dict(kind='function_ref',symbol=n) if ref else dict(kind='call',symbol=n,arguments=[]),sort_keys=True)
    norm=lambda xs:tuple((v.rank,json.dumps(json.loads(v.syntax),sort_keys=True)) if hasattr(v,'syntax') else v for v in xs)
    expected={'h236i':{('h26ra','author',code('r6an'),'context')},
        'h26q3':{('h26rb','author',code('r57r'),code('r6an'),'context')},
        'h26q4':{('h26rd','author',code('r6an'),code('r57u'),code('r6an'),'context')},
        'h26q5':{('h26rc','author','h26rg',code('r6an'),code('r57l',3,True),code('r6aj',3,True),code('r6ak',0,True),'reference','context')},
        'h26qe':{('h26re','author',code(n),code('r57w',2),'reference','context') for n in ('r53k','r55s')},
        'ue':{('h26qi','h26ra','context'),('h26rg','h26rc','context'),('h26re','h26rf','context')}}
    def values(rows):
        v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
        v.update({n:lambda n=n:n for n in nodes});v.update(wa=lambda:'author',h26pp=lambda:'reference',h26q2=lambda:'context')
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
    assert all(values(expected).get(n,unknown) is unknown for n in ('h26qw','h26qx','h26qy','h26qz','h26qp','h26pj'))
    return dict(argument_mutations=count,same_government_projection_in_anaphora=True,reason_direction_and_concessive_background_checked=True,
        both_prior_liberty_contents_inherited=True,no_execution_of_world_content=True,unknown_rejected=True)

FRAGMENTS=(
 ('Denn ',['r6ao'],'後続を先行する国外への広がりの説明上の理由として提示する。'),
 ('es leuchtet ',['r6ac','r6af','r6ai'],'例の参照可能性・実質的な支持根拠・明瞭さ。非人称esに別の対象を補わず、物理照明や実際の賛同へ替えない。'),
 ('dieser ',['r6aj','r6ak','r6ao'],'前文の同じ自己誤解する政府を、同じ八対象の第四位置から指す。'),
 ('doch ',['r6ao'],'先行の困難を背景に、それでも同じ例が示されていることを保持する。'),
 ('ein Beispiel vor, ',['r6ab','r6af','r6ai','r6aj'],'同じ先行統治圏で自由と平穏・一致が共存する実例。先行の証人を拡張し、唯一性や他政府の例へ替えない。'),
 ('daß bei Freiheit, für die öffentliche Ruhe und Einigkeit des gemeinen Wesens ',['r6ad','r6ae','r56h','r572','r575','r576'],'支持される閉じた内容の内側で、同じ自由条件と同じ共同体の二状態を扱う。'),
 ('nicht das mindeste zu besorgen sei.',['r577','r6aa','r6ad','r6af'],'根拠ある危害候補が一つもない。原刊もseiであり、旧ist観察を訂正。現在の全危害不在や未来の保証へ替えない。'))
def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');cursor=1050;clauses=[]
    for fragment,names,reading in FRAGMENTS:
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in names)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==1209 and sum(not c.isspace() for c in u['text'][1050:cursor])==134
    return dict(status='manifest_example_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1050,cursor],text=u['text'][1050:cursor]),selection=selection_binding(catalog(),[115]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_manifest_example_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=134,semantic_equivalence_automatically_proved=False,
        primary_evidence=[dict(path=p,observation='原刊492頁全体と末尾の拡大、AAのseiを再読。旧ist観察は訂正記録v2で置き換える。') for p in SOURCES],
        holistic_review=[
            '159文字・134非空白文字を七断片と全文で再読。非人称es、同じ政府へのdieser、doch、同じ自由の実例、daßの支持対象、beiの条件、二つの公的状態、最小の懸念の否定、接続法を同じ内容へ結んだ。',
            '先行限定君主と共通出発者、国内・国外の経路を保ち、同じ自己誤解する政府への例示を前文の証人の拡張として構成した。無関係な存在証人を同一視せず、全外国政府への全称に強めない。',
            '例の出所を元の同じ統治圏へ結び、政府組織と君主個人を分けた。現在の実例という採用解釈を明示し、国名・年月日・唯一の例を追加しない。',
            '平穏と一致を別に構成し、どちらかへの根拠ある危害候補が一つもない内容を支持対象として保った。評価漏れや不可能な自由による空虚な安全、単なる意見相違の危害扱い、未知の否定への補完を許さない。',
            'Dennの理由提示とdochの取り立てを、事実の連言から区別した。政府の実際の認識や自由の実現を加えず、著者帰属を検査しても引用内容を実行しない。',
            '原刊の末尾を拡大し、seiをistとした旧記録の誤読を訂正した。固定本文は変更せず、版差という以前の前提をこの新しい読解に残していない。有限検査と意味判断を区別し、先行判断の内容・依存関係は保存した。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,CORE,BASIS,ANNOTATIONS,DOC,INVENTORY,*SOURCES,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert c.document['statements'][:115]==old.document['statements'] and len(c.document['statements'])==116
    assert all(c.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==17
    for row in reviews:assert row['selection']==selection_binding(c,[s['index'] for s in row['selection']['statements']])
    for p,i in (('data/prince-sentence-reading-v1.json',112),('data/public-offers-sentence-reading-v1.json',113),('data/spreading-spirit-sentence-reading-v1.json',114)):
        assert read(p)['selection']==selection_binding(c,[i])
    for p in (*PRIORS,SOURCES[0]):validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(SOURCES[0])['fourth_sentence']['original_reading'].endswith('sei')
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert read(ANNOTATIONS)['entries']==read('data/spreading-spirit-sentence-identifiers-v1.json')['entries']
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        t=format_graph(core,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==core
    ranks={};t=format_graph(core,'compact')
    for name,form in (('r6an','k r6an[]'),('r6aj','p r6aj'),('r6ak','p r6ak')):
        for rank,label in enumerate(('','b','c','d','e')):
            try:parse(t+'q[e[r '+label+'['+form+']][r '+label+'['+form+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert ranks=={'r6an':3,'r6aj':3,'r6ak':0},ranks
    return dict(preserved_statements=115,added_statements=1,preserved_whole_unit_reviews=17,preserved_prior_sentence_characters=899,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_reviewed_sentence_characters=134,minimum_quote_ranks=ranks,
        source_observation_corrected_without_changing_inventory=True,roundtrip_scope='new core compact/full/v2; inherited manuscript and meanings unchanged')
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('settings',settings_checks),('witness',witness_checks),('universal',universal_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*SOURCES,*PRIORS,
        'data/prince-sentence-reading-v1.json','data/public-offers-sentence-reading-v1.json','data/spreading-spirit-sentence-reading-v1.json',
        'scripts/compose_manifest_example_sentence.py','scripts/check_manifest_example_sentence.py','tests/test_manifest_example_sentence.py',
        'scripts/compose_spreading_spirit_sentence.py','scripts/compose_clerical_duty_scope.py','scripts/compose_prince_sentence.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='manifest_example_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[115],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
