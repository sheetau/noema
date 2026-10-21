"""Check unrestricted ranges, same-cleric scope, discourse, and sentence review."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_unrestricted_scholarly_freedom import ROOT,FULL,CORE,BASIS,ANNOTATIONS,NAMES,PRIMITIVES,MEANINGS,LIMITS,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_teaching_policy import substitute

INDEX='data/semantic-review-index-v178.json'
REPORT='reports/unrestricted-scholarly-freedom-v1.json'
AUDIT='data/unrestricted-scholarly-freedom-reading-v1.json'
DOC='docs/unrestricted-scholarly-freedom-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
EVIDENCE='data/scholarly-own-voice-evidence-v1.json'
PRIORS=('reports/clerical-private-conclusion-v1.json','reports/scholarly-own-voice-v1.json')
SCENES=('reference','actual','other')
DOMAIN=('one','two')
EXTRA='r zperson[] a.r zscholar[] a.r zref[] d.r zpoint[] d.'
EXTRA+='r zmeaning[a] e.d zmessage[subject a] f[j s[k zmeaning[v subject]]].d zalias[subject a] f[k zmessage[v subject]].'
ARGS='k zperson[] k zscholar[] k zref[]'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(target,boundaries=(),finite=False):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[target]),statements=[])
    prefix=parse('p:'+EXTRA);doc['declarations']=prefix['declarations']+doc['declarations']
    query='k '+target+'['+('' if target in ('r447','r45a','r45b','r45c') else ARGS)+']'
    if target!='r45c':query='t['+query+'][k zpoint[]]'
    doc=parse(format_graph(doc,'compact')+'q['+query+'].')
    if finite:
        def expr(t):return parse(format_graph(prefix,'compact')+'q[e['+t+']['+t+']].')['statements'][0]['body']['arguments'][0]
        choices=[expr('r[p '+n+']') for n in ('zmessage','zalias')];changed=[]
        def reduce(node):
            if isinstance(node,dict):
                if node.get('kind') in ('forall','exists') and isinstance(node.get('sort'),dict) and node['sort']['kind']=='description':
                    changed.append(node['kind'])
                    return dict(kind='and' if node['kind']=='forall' else 'or',arguments=[reduce(substitute(node['body'],node['variable'],c)) for c in choices])
                return {k:reduce(v) for k,v in node.items()}
            if isinstance(node,list):return [reduce(v) for v in node]
            return node
        doc=reduce(doc);assert changed==(['exists'] if target=='r442' else ['forall']),(target,changed)
        doc=parse(format_graph(doc,'compact'))
    return doc


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update(zperson=lambda:'one',zscholar=lambda:'two',zref=lambda:'reference',zpoint=lambda:'actual',h232v=lambda:'reference')
    return v


def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)
def content(truth):return Content(SCENES,tuple(truth and p=='actual' for p in SCENES))


@lru_cache(None)
def range_checks():
    rows={}
    for target in ('r442','r444'):
        doc=fixture(target,('r44s','r44y'),True)
        selected={('one','one','two','two','one','two','zmessage','reference'),
                  ('one','two','two','one','two','one','zalias','reference')}
        for variant in ('baseline','missing_second','extra_candidate','no_candidates','wrong_message','wrong_subject','wrong_reference','wrong_scholar'):
            v=base(doc);v['cd']=lambda r,ref:(r,ref)==('two','reference')
            candidates=set(selected);allowed=set(selected)
            if variant=='missing_second':allowed.remove(sorted(selected)[1])
            if variant=='extra_candidate':candidates.add(('one','two','two','two','two','one','zmessage','reference'))
            if variant=='no_candidates':candidates=set()
            if variant.startswith('wrong_'):
                position={'wrong_message':6,'wrong_subject':5,'wrong_reference':7,'wrong_scholar':2}[variant]
                allowed={tuple('other' if i==position else x for i,x in enumerate(row)) for row in allowed}
            def key(a):return (*a[:6],symbol(a[6]),a[7])
            v['r44s']=lambda *a:key(a) in candidates
            v['r44y']=lambda *a:content(key(a) in allowed)
            wanted=variant!='no_candidates' if target=='r442' else variant in ('baseline','no_candidates')
            result=run(doc,v);assert result==[wanted],(target,variant,result);rows[target+':'+variant]=result[0]
    doc=fixture('r443',('r2zi','r44x'))
    for variant in ('baseline','missing_second','extra_candidate','wrong_reference'):
        v=base(doc);candidates={'one','two'} if variant!='extra_candidate' else {'two'}
        v['r2zi']=lambda person,activity,role,ref:(person,role,ref)==('one','two','reference') and activity in candidates
        v['r44x']=lambda person,activity,role,ref:content((person,role,ref)==('one','two','other' if variant=='wrong_reference' else 'reference') and (variant=='baseline' or activity=='one'))
        result=run(doc,v);assert result==[variant=='baseline'],(variant,result);rows['r443:'+variant]=result[0]
    refusals={}
    for target in ('r442','r444'):
        doc=fixture(target,('r44s','r44y'));v=base(doc)
        v.update(cd=lambda *a:True,r44s=lambda *a:False,r44y=lambda *a:content(True))
        try:run(doc,v)
        except ValueError as error:assert 'Cannot finitely quantify the description domain' in str(error);refusals[target]=str(error)
        else:raise AssertionError('Description domain silently reduced')
    return dict(contrasts=rows,native_four_individual_universals_and_existentials=True,
        diagnostic_messages=['zmessage','zalias'],extra_unpermitted_candidate_rejected=True,
        full_description_domains_refused=refusals,boundaries=['r44s','r44y','r2zi','r44x'])


@lru_cache(None)
def connection_checks():
    table=[];doc=fixture('r445',('r442','r443','r444'))
    for bits in product((False,True),repeat=3):
        v=base(doc)
        for name,bit in zip(('r442','r443','r444'),bits):v[name]=lambda *a,bit=bit:content(bit and a==('one','two','reference'))
        result=run(doc,v);assert result==[all(bits)];table.append([*bits,result[0]])
    rows={};selected={tuple('one' if i%2==0 else 'two' for i in range(9)),tuple('two' if i%2==0 else 'one' for i in range(9))}
    for target,lower in (('r447','r445'),('r45a','r442'),('r45b','r446')):
        doc=fixture(target,('r35t',lower))
        for variant in ('baseline','missing_second_cleric','wrong_person','wrong_role','wrong_reference','wrong_point','no_case'):
            v=base(doc)
            v['r35t']=lambda *a:variant!='no_case' and a[:-1] in selected and a[-1]=='reference'
            v['h247d']=lambda person,ref:person if variant=='wrong_role' else 'two' if person=='one' else 'one'
            def lower_content(person,role,ref):
                correct=(role==('two' if person=='one' else 'one') and ref=='reference')
                if variant=='missing_second_cleric':correct=correct and person=='one'
                if variant=='wrong_person':correct=correct and person not in DOMAIN
                if variant=='wrong_reference':correct=ref=='other'
                return Content(SCENES,tuple(correct and p==('other' if variant=='wrong_point' else 'actual') for p in SCENES))
            v[lower]=lower_content
            result=run(doc,v);assert result==[variant in ('baseline','no_case')],(target,variant,result);rows[target+':'+variant]=result[0]
    # The universal reason branch also runs without a definition boundary,
    # reusing the already verified concrete candidate/norm interpretation.
    from scripts.check_scholarly_own_voice import EXTRA as NATIVE_EXTRA,DOMAIN as NATIVE_DOMAIN,SCENES as NATIVE_SCENES,model
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,['r443','r446']),statements=[])
    doc=parse(format_graph(doc,'compact')+NATIVE_EXTRA+'q[t[k r443['+ARGS+']][k zpoint[]]].q[t[k r446['+ARGS+']][k zpoint[]]].')
    native=[]
    for bits in ((True,False,True,False),(False,False,True,False),(True,True,True,False)):
        v,_=model(doc,bits=bits);result=evaluate(doc,v,NATIVE_DOMAIN,NATIVE_SCENES,True)
        assert result==[bits[0] and not bits[1],True],(bits,result);native.append([*bits,*result])
    return dict(nonempty_and_two_universal_freedoms_table=table,same_cleric_role_and_reference=rows,
        native_nine_individual_case_universals=True,native_reason_range_and_public_classification=native,
        boundaries=['r442','r443','r444','r35t','r445','r446'])


@lru_cache(None)
def discourse_checks():
    doc=fixture('r45c');rows={}
    nodes=('prior','whole','public_name','world_name','written','public','author','other')
    mappings=dict(h253g='prior',h253m='whole',h253n='public_name',h253o='world_name',h253p='written',h253q='public',wa='author')
    variants=('baseline','wrong_author','wrong_context','wrong_whole','wrong_written','wrong_public','contrast_reversed',
        'wrong_dimension','apposition_reversed','inference_reversed','wrong_inference_ground','wrong_order','merged_nodes')
    for variant in variants:
        v=base(doc);v.update({n:lambda value=value:value for n,value in mappings.items()});v['h232o']=lambda:'reference'
        expected_author='other' if variant=='wrong_author' else 'author';expected_ctx='other' if variant=='wrong_context' else 'reference'
        claims={'whole':'r447','written':'r45a','public':'r45b'}
        for name,node in (('wrong_whole','whole'),('wrong_written','written'),('wrong_public','public')):
            if variant==name:claims[node]='r44q'
        v['h236i']=lambda n,w,c,ctx:w==expected_author and ctx==expected_ctx and c.rank==3 and claims.get(n)==symbol(c)
        def contrast(n,w,left,lc,right,rc,dimension,ctx):
            wanted=('whole','author','prior','r44q','whole','r447','r2zg','reference')
            if variant=='contrast_reversed':wanted=('whole','author','whole','r447','prior','r44q','r2zg','reference')
            if variant=='wrong_dimension':wanted=(*wanted[:6],'r2zi',wanted[7])
            return lc.rank==rc.rank==3 and dimension.rank==0 and (n,w,left,symbol(lc),right,symbol(rc),symbol(dimension),ctx)==wanted
        v['h236k']=contrast
        v['uf']=lambda w,a,b,ctx:(w,a,b,ctx)==('author',* (('world_name','public_name') if variant=='apposition_reversed' else ('public_name','world_name')),'reference')
        def explanation(w,grounds,conclusion,ctx):
            expected={'public'} if variant=='inference_reversed' else {'prior'} if variant=='wrong_inference_ground' else {'written'}
            return {n for n in nodes if grounds(n)}==expected and (w,conclusion,ctx)==('author','written' if variant=='inference_reversed' else 'public','reference')
        v['ud']=explanation
        orders={('prior','whole'),('written','public'),('public_name','world_name')}
        if variant=='wrong_order':orders={tuple(reversed(pair)) for pair in orders}
        v['ue']=lambda a,b,ctx:(a,b) in orders and ctx=='reference'
        if variant=='merged_nodes':
            v['h253o']=lambda:'public_name'
            for n in ('h236i','h236k','uf','ud','ue'):v[n]=lambda *a:True
        result=run(doc,v,nodes);assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
    return dict(contrasts=rows,same_author_context_and_exact_rank_three_contents=True,
        private_public_contrast_same_dimension=True,public_world_explanation_and_mithin_direction=True,
        contents_not_executed=True)


def reading():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0012');text=u['text'][4735:5021]
    parts=[
        ('Dagegen ',['h236k','r44q','r447'],'先行する同じ聖職者の私的職務上の非自由と、学識者としての公的自由との対照。'),
        ('als Gelehrter, ',['h247d','cd','r442','r45a'],'同じ本人の学識者としての立場。職務上の任用や学位だけでは代用しない。'),
        ('der durch Schriften zum eigentlichen Publikum, ',['r3z','h242g','cc','ce','r442'],'書面を介して本来の公衆へ語るという一般的な活動構成の特徴。非空の候補を保つが実行済みの発言に限らない。'),
        ('nämlich der Welt, ',['ce','uf','h253n','h253o'],'同じ宛先を全読者世界として説明する。同じ候補内の同じaudienceであり、別の宛先を加えない。'),
        ('spricht, ',['r44s','r44t','r442'],'関係節の一般的な発言活動の特徴。引用した発言実行内容では同じ書面の記録と少なくとも一人の公衆への実際の提示を要求する。'),
        ('mithin der Geistliche im öffentlichen Gebrauche seiner Vernunft, ',['r35t','r2zi','r446','r45b','ud'],'同じ聖職者がこの立場では公的に理性を用いるという説明。先行する書面で世界へ語る特徴を受ける。'),
        ('genießt einer uneingeschränkten Freiheit, ',['r442','r443','r444','r445','r447','r37c'],'当該立場の全公的理性使用候補と全本人名義の書面発言候補に、積極的許可と反対要求の不在がある。'),
        ('sich seiner eigenen Vernunft zu bedienen ',['ca','r2zi','r44u','r44x','r443'],'同じ本人が自分の理性を公的に用いる全活動候補の実行への自由。'),
        ('und in seiner eigenen Person zu sprechen.',['h253l','rhe','r44v','r44w','r44y','r444'],'それに加え、同じ本人の名による発言の実行への自由。他者名義の不在や発話の真理で代用しない。')]
    cursor=4735;clauses=[]
    for t,names,meaning in parts:
        assert u['text'][cursor:cursor+len(t)]==t,(cursor,t)
        clauses.append(dict(range=[cursor,cursor+len(t)],text=t,definitions=names,reading=meaning));cursor+=len(t)
    assert cursor==5021 and sum(not c.isspace() for c in text)==249
    pages=read(EVIDENCE)['pages']
    for p in pages:assert p['visually_inspected'] and digest((ROOT/p['path']).read_bytes())==p['sha256']
    return dict(status='unrestricted_scholarly_freedom_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[4735,5021],text=text),selection=selection_binding(catalog(),[94]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_unrestricted_scholarly_freedom',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=249,
        preserved_reviewed_sentence_characters=4037,paragraph_reviewed_sentence_characters=4286,semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '原刊487頁の対象文と前後を通読し、同じ聖職者を職務上の私的使用から学識者の公的使用へ対照した。職務上の非自由を撤回せず、別人の自由や全生活上の無制限へ拡張しない。',
            '書面で語る関係節をこの立場の一般的な活動構成として解釈した。r442で非空の候補を保ち、発言済み・許可済みだけに対象を縮めない。実際の記録と発話は引用したr44tの実行内容に置いた。',
            '全称する理性使用と本人名義の発言を別々に構成し、同じ人の二つの自由として結んだ。発話の主題と閉じた記述を全称で取り、以前の教義批評の吟味・善意などを新たな制限として追加しない。',
            '本来の公衆と世界を同じ宛先に保ち、namlichの同格的な説明をufで示した。mithinは書面で公衆へ語る特徴から公的使用への説明に結び、その二つの内容も同じ事例・本人・学識者の立場で帰属した。',
            '連続する全語句と作用域、geniesstの規範的な自由の保持、二つの不定詞の並列、Dagegenの対照と本文順序を確認した。旧94主張・14全単位判断を保持し、今回249文字のみを加える。第五段落全体と二作品は未完。'],
        original_pages=pages,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,EVIDENCE,*PRIORS,*[p['path'] for p in pages])})


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:94]==old.document['statements'] and len(new.document['statements'])==95
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for n,e in dependency().entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for path in PRIORS:validate_hashes(ROOT,read(path)['source_sha256'])
    prior=read('data/clerical-private-conclusion-reading-v1.json');assert prior['selection']==selection_binding(new,[93]);validate_hashes(ROOT,prior['source_sha256'])
    assert read(AUDIT)==reading()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            t=format_graph(doc,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==doc
    return dict(preserved_statements=94,added_statements=1,preserved_whole_unit_reviews=len(reviews),new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        new_reviewed_sentence_characters=249,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for n,f in [('ranges',range_checks),('connections',connection_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,AUDIT,DOC,INVENTORY,EVIDENCE,*PRIORS,*[p['path'] for p in read(EVIDENCE)['pages']],
        'data/clerical-private-conclusion-reading-v1.json','scripts/compose_unrestricted_scholarly_freedom.py','scripts/check_unrestricted_scholarly_freedom.py',
        'tests/test_unrestricted_scholarly_freedom.py','scripts/check_teaching_policy.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_confessional_teaching.py','scripts/compose_scholarly_own_voice.py','scripts/check_scholarly_own_voice.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='unrestricted_scholarly_freedom_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(AUDIT)['source'],statements=[94],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
