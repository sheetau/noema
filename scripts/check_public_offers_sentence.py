"""Check both universal scopes, discourse, and every second-sentence fragment."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_public_offers_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,LIMITS,NODE_INFO,CLERICS,RULERS,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/public-offers-sentence-v1.md';READING='data/public-offers-sentence-reading-v1.json'
INDEX='data/semantic-review-index-v197.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/all-offered-freedoms-v1.json','reports/revered-clerical-scope-v1.json','reports/clerical-duty-scope-v1.json',
        'reports/confessional-divergence-v1.json','reports/offered-judgments-v1.json','reports/preserved-public-duties-v1.json','reports/prince-sentence-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v1.json','artifacts/eighth-paragraph-source-v1/page-492.jpg','artifacts/eighth-paragraph-source-v1/kant-aa08-041.html')
DOMAIN=('a','b');SCENES=('reference','anchor','outer')
def z(n):return 'k z'+n+'[]'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document)
    for row in d['declarations']:
        if row['name'] in boundaries:
            assert row['result']=='truth',row['name']
            row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=parse('p:'+''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES)))
    d['declarations']=extra['declarations']+d['declarations']
    d.update(declarations=closure(d,(*roots,*(x['name'] for x in extra['declarations']))),statements=[])
    return parse(format_graph(d,'compact')+query)

def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

def model(d):
    v={row['name']:unknown for row in d['declarations'] if row['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(h247d=lambda p,r:'b' if (p,r)==('a','reference') else 'a',h26pa=lambda:'reference',h26pb=lambda:'outer',h26km=lambda:'outer',h26kn=lambda p:'anchor' if p=='outer' else 'reference')
    return v

@lru_cache(None)
def other_scope_checks():
    q='q[k r55j['+z('a')+' '+z('reference')+' '+z('anchor')+']].q[k r55k['+z('b')+' '+z('a')+' '+z('b')+' '+z('a')+' '+z('reference')+']].'
    d=fixture(('r55j','r55k'),q,('r54y','r54x'));rows={}
    for case in ('prior_clerical_group','outside_prior_group','under_other_ruler','other_reference','other_anchor','other_scholar'):
        v=model(d)
        v['r54y']=lambda p,o,ch,cr,su,sc,r,t:(p,o,ch,cr,su,sc,r,t)==('a','b','a','b','a','b','reference','anchor')
        v['r54x']=lambda ruler,office,community,p:(ruler,office,community,p)==('b','a','b','a')
        if case=='outside_prior_group':v['r54y']=lambda *a:False
        if case=='under_other_ruler':v['r54x']=lambda *a:False;v['r54y']=lambda *a:False
        if case=='other_reference':
            old=v['r54y'];v['r54y']=lambda *a:old(*a[:-2],'outer',a[-1])
        if case=='other_anchor':
            old=v['r54y'];v['r54y']=lambda *a:old(*a[:-1],'outer')
        if case=='other_scholar':v['h247d']=lambda *a:'a'
        got=run(d,v);expected=[case=='prior_clerical_group',case not in ('prior_clerical_group','under_other_ruler')]
        assert got==expected,(case,got);rows[case]=got
    for name in ('r54y','r54x','h247d'):
        v=model(d);v['r54y']=lambda *a:False;v['r54x']=lambda *a:True;v[name]=unknown;rejects(d,v)
    return dict(cases=rows,other_means_outside_same_prior_group_not_outside_speaker=True,
        exact_office_church_creed_subject_scholar_reference_anchor_bound=True,
        boundary='r54y and r54x are the independently checked exact scope boundaries. Four existential role/context binders, their common person, exclusion and same ruler scope execute natively.')

@lru_cache(None)
def other_permission_checks():
    q='q[k r55l['+z('a')+' '+z('b')+' '+z('a')+' '+z('reference')+']].'
    d=fixture(('r55l',),q,('r55k','r55h','r55i'));rows={}
    for case in ('baseline','second_person_denied','second_person_restricted','second_person_excluded','no_people','wrong_scholar_conclusion','wrong_anchor_conclusion'):
        v=model(d)
        v['r55k']=lambda r,o,c,p,ref:(r,o,c,ref)==('a','b','a','reference')
        v['r55h']=lambda p,s,ref,t:s==v['h247d'](p,ref) and (ref,t)==('reference','anchor')
        v['r55i']=lambda p,s,ref,t:s==v['h247d'](p,ref) and (ref,t)==('reference','anchor')
        if case in ('second_person_denied','second_person_restricted','second_person_excluded'):
            v['r55i']=lambda p,*a:p=='a'
            if case=='second_person_restricted':v['r55h']=lambda p,*a:p=='a'
            if case=='second_person_excluded':v['r55k']=lambda r,o,c,p,ref:p=='a'
        if case=='no_people':v['r55k']=lambda *a:False;v['r55i']=lambda *a:False
        if case=='wrong_scholar_conclusion':v['r55i']=lambda p,s,r,t:s!=v['h247d'](p,r)
        if case=='wrong_anchor_conclusion':v['r55i']=lambda p,s,r,t:t=='outer'
        got=run(d,v);assert got==[case not in ('second_person_denied','wrong_scholar_conclusion','wrong_anchor_conclusion')],(case,got);rows[case]=got[0]
    for name in ('r55k','r55h','r55i'):
        v=model(d);v.update(r55k=lambda *a:True,r55h=lambda *a:True,r55i=lambda *a:True);v[name]=unknown;rejects(d,v)
    return dict(cases=rows,all_persons_quantified=True,same_person_and_scholar_in_condition_and_freedom=True,
        no_existential_population_claim_added=True,boundary='Prior other-person scope, person-wide nonrestriction and all-offer freedom are independent argument boundaries; the new universal conditional executes natively.')

@lru_cache(None)
def clerical_quantifier_checks():
    q='q[k r55m['+z('a')+' '+z('b')+' '+z('a')+' '+z('reference')+']].'
    d=fixture(('r55m',),q,('r55d',));v=model(d);seen=set()
    def complete(*a):
        seen.add(a);return a[:3]==('a','b','a') and a[-1]=='reference'
    v['r55d']=complete;assert run(d,v)==[True] and len(seen)==64
    for pos in range(6):
        wanted=['a']*6;wanted[pos]='b';v['r55d']=lambda *a,wanted=tuple(wanted):a[3:9]!=wanted
        assert run(d,v)==[False],pos
    v['r55d']=unknown;rejects(d,v)
    return dict(native_assignments=64,all_six_clerical_variables_bound=True,one_exception_in_each_position_rejected=True,
        same_ruler_office_community_and_reference=True,boundary='r55d is the prior fully scoped conditional. All six individual quantifiers execute on a two-individual diagnostic domain; this is not an enumeration of all real clergy.')

@lru_cache(None)
def source_checks():
    q=''.join('q[t[k '+n+'[]]['+z(point)+']].' for point in ('outer','anchor') for n in ('r55s','r55t','r55u'))
    d=fixture(('r55s','r55t','r55u'),q,('r55m','r55l'));rows={}
    for case in ('baseline','clerical_exception','other_exception','both_exceptions','wrong_reference'):
        v=model(d)
        v['r55m']=lambda r,o,c,ref:ref=='reference' and not(case in ('clerical_exception','both_exceptions') and (r,o,c)==('b','a','b'))
        v['r55l']=lambda r,o,c,ref:ref=='reference' and not(case in ('other_exception','both_exceptions') and (r,o,c)==('a','b','a'))
        if case=='wrong_reference':v['h26pa']=lambda:'outer'
        first=case not in ('clerical_exception','both_exceptions','wrong_reference');last=case not in ('other_exception','both_exceptions','wrong_reference')
        got=run(d,v);assert got==[first and last,first,last]*2,(case,got);rows[case]=got
    v=model(d);v['r55m']=lambda *a:True;v['r55l']=unknown;rejects(d,v)
    return dict(cases=rows,both_clauses_required=True,all_ruler_role_community_combinations_native=True,
        source_present_not_moved_by_outer_evaluation=True,boundary='The two previously checked policy conditions are separate exact argument boundaries; source constants, both quantifier orders and whole/part conjunction execute natively.')

@lru_cache(None)
def discourse_checks():
    d=deepcopy(catalog().document);d.update(declarations=closure(d,('r55v',)),statements=[]);d=parse(format_graph(d,'compact')+'q[k r55v[]].')
    nodes=(*NODE_INFO,'h26oq');domain=(*nodes,'author','other');scenes=('reference','context')
    code=lambda n,rank:(rank,json.dumps(dict(kind='call',symbol=n,arguments=[]),sort_keys=True))
    normalize=lambda xs:tuple((v.rank,json.dumps(json.loads(v.syntax),sort_keys=True)) if hasattr(v,'syntax') else v for v in xs)
    expected={'h236i':{(n,'author',code(t,3),'context') for n,t in (('h26pc','r55s'),('h26pd','r55t'),('h26pe','r55u'))},
        'h26o7':{('h26pf','author','h26pd','h26pe',code('r55s',3),code('r53b',2),code('r55o',2),code('r55p',2),code('r55q',2),code('r55r',2),'reference','context')},
        'ue':{('h26oq','h26pc','context'),('h26pd','h26pe','context')}}
    def values(wanted):
        v={row['name']:unknown for row in d['declarations'] if row['kind']=='primitive'}
        v.update({n:lambda n=n:n for n in nodes});v.update(wa=lambda:'author',h26pa=lambda:'reference',h26pb=lambda:'context')
        v.update({n:lambda *a,rows=rows:normalize(a) in rows for n,rows in wanted.items()})
        v['ud']=lambda author,premise,focus,context:(author,focus,context)==('author','h26pe','context') and tuple(n for n in domain if premise(n))==('h26pd',)
        return v
    assert run(d,values(expected),domain,scenes)==[True];mutations=0
    for name,rs in expected.items():
        for row in rs:
            for pos in range(len(row)):
                changed=deepcopy(expected);changed[name].remove(row);wrong=list(row);wrong[pos]='other';changed[name].add(tuple(wrong))
                assert run(d,values(changed),domain,scenes)==[False],(name,pos);mutations+=1
        v=values(expected);v[name]=unknown;rejects(d,v,domain,scenes)
    v=values(expected);v['ud']=lambda *a:False;assert run(d,v,domain,scenes)==[False]
    for i,n in enumerate(nodes):
        for other in nodes[i+1:]:
            v=values(expected);v[n]=lambda other=other:other
            for name in expected:v[name]=lambda *a:True
            v['ud']=lambda *a:True;assert run(d,v,domain,scenes)==[False]
    for n in ('h237z','h245c','h26nu','h26o4','h26o5','h26o6'):assert values(expected).get(n,unknown) is unknown
    return dict(argument_mutations=mutations,whole_and_two_clauses_attributed=True,same_prior_qualified_ruler_and_other_person_profiles=True,
        a_fortiori_and_contrast_without_truth_execution=True,prior_and_internal_order_preserved=True,nodes_distinct=True,unknown_rejected=True)

FRAGMENTS=(
 ('Unter ihm ',['r54x','r53b','r55m','r55l'],'前文と同じ限定君主・統治職・共同体の下。同じ本文現在点を共有する。'),
 ('dürfen ',['r55c','r55i','r37c'],'全対象の全公的提示候補への積極的許可と反対要求の不在。'),
 ('verehrungswürdige Geistliche, ',['r54y','r54v','r54u','r55m'],'敬意に値する同じ聖職者という評価による限定。真の根拠と非空の全基準で構成する。'),
 ('unbeschadet ihrer Amtspflicht, ',['r54o','r54i','r54j','r54k'],'同じ本人の同じ職務の全要求を免除せず、同じ一候補で発表と全履行が両立する。'),
 ('ihre ',['r53n','r53o','r53u'],'同じ発表者自身が保持する判断と把握・根拠ある洞察。実行内容の候補内に置く。'),
 ('vom angenommenen Symbol ',['r35r','r53x','r532'],'同じ教会の採用信条の同じ論点の内容と比較する。教示規則や別の信条に替えない。'),
 ('hier oder da abweichenden ',['r533','r532','r545'],'発表群の少なくとも一論点での内容差。少数割合・全否認・他の全論点の一致を補わない。'),
 ('Urtheile und Einsichten, ',['r53n','r53o','r53u','r543'],'本人の保持見解と把握・根拠ある見解を二列に保ち、同じ一発表で扱う。真理を保証しない。'),
 ('in der Qualität der Gelehrten, ',['r2zi','r53q','h247d'],'同じ本人の学識者としての公的理性使用。職務上の教示や職業免許と同一化しない。'),
 ('frei und öffentlich ',['r37c','r53q','r55c'],'同じ公的提示の自由。現実の発表や物理的能力から許可を推論しない。'),
 ('der Welt ',['ce','cc','r53q'],'同じ本来の読者公衆を宛先とする。全世界の受領・理解は要求しない。'),
 ('zur Prüfung darlegen; ',['r53r','r53p','r53u'],'同じ内容を本人名義で提示し、同じ公衆の検討を目的とする。審査成功・賛同を補わず、セミコロンの節境界を保つ。'),
 ('noch mehr aber ',['h26o7','ud','r55v'],'前節を撤回せず対照し、職務制限不在の側にはなおさらという許容側の理由付けを提示する。'),
 ('jeder andere, ',['r55j','r55k','r55l'],'同じ統治下から前節の人物群を除いた全員。話者以外や任意の他国の人へ替えない。'),
 ('der durch keine Amtspflicht eingeschränkt ist.',['r55h','r54p','r55l'],'同じ人の公的提示全般が全職務義務に制限されないことを関係節の条件に置く。義務の不存在や一発表だけの両立に縮めない。'))

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');cursor=574;clauses=[]
    for fragment,names,reading in FRAGMENTS:
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in names)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==889 and sum(not c.isspace() for c in u['text'][574:cursor])==273
    return dict(status='public_offers_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[574,cursor],text=u['text'][574:cursor]),selection=selection_binding(catalog(),[113]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_public_offers_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=273,semantic_equivalence_automatically_proved=False,
        primary_evidence=[dict(path=p,observation='固定した第二文と原刊頁・AA本文の照合資料。第四文の版差は保持する。') for p in SOURCES],
        holistic_review=[
            '315文字・273非空白文字を全15断片と文全体で再読した。文頭の前文照応、同じ本人の二つの立場、所有表現、相違の部分性、自由と非免除、最後の条件付き全称を同じ内容へ結んでいる。',
            '前文の君主は一般条件の同じ三対象として受け、全人物・職務・教会・信条・主題の組について第一節の条件命題を記述した。特定の現実の君主や実例の存在は補っていない。',
            '敬意に値する聖職者という限定的読解と、他者をその同じ先行群の外とする読解を明示した。慣習的敬称や非制限的添え評価の読みを唯一の誤りとして排除せず、採用した範囲内で欠落を点検した。',
            '自由は非事実的規範の内容、見解保持・把握・提示と目的は比較候補内の実行内容として保持した。客観的な全見解の真理、現に公衆の審査が済んだこと、学識者の免許、実際の義務履行は加えていない。',
            '同じ信条の同じ論点の部分との相違を保ち、項目の綴り、別の論点の追加、教示規則違反だけでは代用しない。どこかで相違するという読みで、全項目が異なるとも残り全てが一致するとも述べない。',
            'unbeschadetは全段階1職務要求の非免除と共充足、keine Amtspflichtは全cf職務が該当公的提示全般を制限しない条件として範囲を明示した。型をまたぐ全規範の列挙や因果的な無害性の証明とはしていない。',
            'noch mehr aberを対照と許容側のなおさらの理由付けとして全体・二節・同じ君主・他者・無制約の引用に結んだ。前節の自由は維持し、引用された主張の真理や著者の推論の論理的妥当性は自動で導かない。',
            '意味規約の全範囲入力と、有限検査・引用・型・接続の証拠を区別した。前文の全判断を保存したまま第二文のみを追加し、後続三文と二作品全体の完成は主張しない。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,CORE,BASIS,ANNOTATIONS,DOC,INVENTORY,*SOURCES,*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert c.document['statements'][:113]==old.document['statements'] and len(c.document['statements'])==114
    assert all(c.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==17
    for row in reviews:assert row['selection']==selection_binding(c,[s['index'] for s in row['selection']['statements']])
    first=read('data/prince-sentence-reading-v1.json');assert first['selection']==selection_binding(c,[112])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert read(ANNOTATIONS)['entries']==read('data/prince-sentence-identifiers-v1.json')['entries']
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        t=format_graph(core,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==core
    t=format_graph(core,'compact');parse(t+'q[e[r d[k r55s[]]][r d[k r55s[]]]].')
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')['text']
    assert u[574:813].endswith('darlegen;') and u[814:828]=='noch mehr aber'
    return dict(preserved_statements=113,added_statements=1,preserved_whole_unit_reviews=17,preserved_first_sentence_characters=490,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_reviewed_sentence_characters=273,
        roundtrip_scope='new core compact/full/v2; inherited manuscript and meanings unchanged')

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in (('other_scope',other_scope_checks),('other_permission',other_permission_checks),('clerical_quantifiers',clerical_quantifier_checks),('source',source_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*SOURCES,*PRIORS,'data/prince-sentence-reading-v1.json',
        'scripts/compose_public_offers_sentence.py','scripts/check_public_offers_sentence.py','tests/test_public_offers_sentence.py',
        'scripts/compose_clerical_duty_scope.py','scripts/compose_prince_sentence.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='public_offers_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[113],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
