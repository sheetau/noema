"""Check the same hypothetical contract through nullity, confirmation and prose."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,DescriptionValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_covenant_nullity import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

INDEX='data/semantic-review-index-v181.json'
REPORT='reports/covenant-nullity-v1.json'
READING='data/covenant-nullity-reading-v1.json'
DOC='docs/covenant-nullity-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/covenant-question-v1.json','reports/human-enlightenment-block-v1.json','reports/normative-nullity-v1.json','reports/public-confirmation-v1.json','reports/peace-conclusion-v1.json')
SCENES=('reference','candidate','context','formation')
EXTRA='r zone[] a.r ztwo[] a.r zreference[] d.r zcandidate[] d.'

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=EXTRA):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+extra+query)
def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update(zone=lambda:'one',ztwo=lambda:'two',zreference=lambda:'reference',zcandidate=lambda:'candidate',
        h255o=lambda:'reference',h255n=lambda:'context',h255r=lambda:'two',h254z=lambda agreement:'formation')
    return v
def run(doc,v,domain=('one','two')):return evaluate(doc,v,domain,SCENES,True)
def content(points):return Content(SCENES,tuple(p in points for p in SCENES))

@lru_cache(None)
def reference_checks():
    doc=fixture(('r5bk','r5bl'),'q[t[k r5bk[k zone[] k ztwo[] k zreference[]]][k zcandidate[]]].q[t[k r5bl[k zone[] k ztwo[] k zreference[]]][k zcandidate[]]].',('r475','r5bj'));rows={}
    for variant in ('baseline','other_source','other_assessor','other_community','other_reference','other_point'):
        v=base(doc);v['h255p']=lambda community,reference:'one' if (community,reference)==('two','reference') else 'two'
        wanted=('two' if variant=='other_source' else 'one','two' if variant=='other_assessor' else 'one','context' if variant=='other_reference' else 'reference')
        v['r475']=lambda *a:content(('reference' if variant=='other_point' else 'candidate',)) if a==wanted else content(())
        v['r5bj']=lambda *a:content(('reference' if variant=='other_point' else 'candidate',)) if a==('two' if variant=='other_source' else 'one','one' if variant=='other_community' else 'two','context' if variant=='other_reference' else 'reference') else content(())
        actual=run(doc,v);expected=[variant in ('baseline','other_community'),variant in ('baseline','other_assessor')]
        assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(same_contract_assessor_community_reference_and_point=rows,boundaries=['r475','r5bj'])

@lru_cache(None)
def nullity_checks():
    from scripts.check_normative_nullity import fixture as norm_fixture,model as norm_model,DOMAIN,SCENES as POINTS
    # Reuse the native three-position consequence model, including locally issued descriptions.
    supplied=norm_fixture(('r475',),'');doc=fixture(('r5bm',),'',('r5bl',),extra='')
    names={d['name'] for d in supplied['declarations']}
    doc['declarations']=supplied['declarations']+[d for d in doc['declarations'] if d['name'] not in names]
    doc=parse(format_graph(doc,'compact')+'q[t[k r5bm[k zcontract[] k zcommunity[] k ztreference[]]][k ztreference[]]].')
    cases=0
    for grounded in product((False,True),repeat=3):
        facts={('zadditional',p) for p,on in zip(POINTS,grounded) if on}
        for confirmed in product((False,True),repeat=2):
            v=norm_model(doc,facts)
            v['h257l']=lambda ag,ref,p:(ag,ref)==('contract','reference') and p in ('candidate','other')
            v['r5bl']=lambda ag,community,ref:Content(POINTS,tuple((ag,community,ref)==('contract','community','reference') and p in {x for x,on in zip(POINTS[1:],confirmed) if on} for p in POINTS))
            expected=not grounded[0] and all(not on or not bad for on,bad in zip(confirmed,grounded[1:]))
            actual=evaluate(doc,v,DOMAIN,POINTS,True);assert actual==[expected],(grounded,confirmed,actual);cases+=1
    variants={}
    for variant in ('baseline','no_candidates','wrong_candidate_source','moving_candidate_reference','other_norm_source','other_norm_assessor'):
        v=norm_model(doc,{('zadditional','candidate')},'external_source' if variant=='other_norm_source' else 'other_assessor' if variant=='other_norm_assessor' else 'baseline')
        v['h257l']=lambda ag,ref,p:variant!='no_candidates' and (ag,ref,p)==('other' if variant=='wrong_candidate_source' else 'contract','candidate' if variant=='moving_candidate_reference' else 'reference','candidate')
        v['r5bl']=lambda *a:Content(POINTS,tuple(p=='candidate' and a==('contract','community','reference') for p in POINTS))
        actual=evaluate(doc,v,DOMAIN,POINTS,True);assert actual==[variant!='baseline'];variants[variant]=actual[0]
    v['h257l']=unknown
    try:evaluate(doc,v,DOMAIN,POINTS,True)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('unknown candidates were accepted')
    return dict(native_all_consequences_with_two_confirmed_candidates=cases,contrasts=variants,
        current_nullity_required_without_confirmation=True,confirmation_existence_not_asserted=True,
        boundary='r5bl; three concrete confirmation kinds were checked in public-confirmation/peace-conclusion',
        unknown_rejected=True)

@lru_cache(None)
def family_checks():
    seq=('one','two','two','one','two');rows={}
    shapes=(seq,seq[:-1],(*seq,'one'),tuple(reversed(seq)))
    for items in shapes:
        literal='l[a]['+' '.join('k z'+x+'[]' for x in items)+']'
        roots=('r5bn','r5bo','r5bp','r5bs','r5bt','r5bu')
        doc=fixture(roots,''.join('q[t[k '+n+'['+literal+']][k zcandidate[]]].' for n in roots),('r5bk','r5bl','r5bm','r5av','r5aw','r5bi'))
        v=base(doc)
        for n in ('r5bk','r5bl','r5bm'):v[n]=lambda *a:content(('candidate',)) if a==('two','two','reference') else content(())
        v['r5av']=lambda *a:a==('two','two','candidate');v['r5aw']=lambda *a:a==('two','candidate');v['r5bi']=lambda *a:a==('two','reference','candidate')
        actual=run(doc,v);assert actual==[items==seq]*6,(items,actual);rows[str(items)]=actual
    return dict(exact_five_arguments_for_all_families=rows,
        boundaries=['r5bk','r5bl','r5bm','r5av','r5aw','r5bi'])

@lru_cache(None)
def conditional_checks():
    seq=('one','two','two','one','two');literal='l[a]['+' '.join('k z'+x+'[]' for x in seq)+']'
    doc=fixture(('r5bq',),'q[t[k r5bq['+literal+']][k zcandidate[]]].',('r5ak','r5bm'));rows={}
    for formed,null in product((False,True),repeat=2):
        v=base(doc);v['r5ak']=lambda *a:formed and a==(*seq,'formation')
        v['r5bm']=lambda *a:content(('candidate',)) if null and a==('two','two','reference') else content(())
        actual=run(doc,v);assert actual==[not formed or null];rows[str((formed,null))]=actual[0]
    # Invalid argument lists are rejected, rather than passing by a false antecedent.
    short=fixture(('r5bq',),'q[t[k r5bq[l[a][k zone[]]]][k zcandidate[]]].',('r5ak','r5bm'))
    v=base(short);v['r5ak']=lambda *a:False;v['r5bm']=lambda *a:content(())
    assert run(short,v)==[False]
    doc=fixture(('r5br',),'q[t[k r5br[]][k zcandidate[]]].',('r5ak','r5bm'));generic={}
    for variant in ('valid','one_counterexample','none_formed','outside_community','other_contract','other_reference','other_formation_reference'):
        v=base(doc)
        formed=(*seq[:-1],'one' if variant=='outside_community' else 'two','reference' if variant=='other_formation_reference' else 'formation')
        v['r5ak']=lambda *a:variant!='none_formed' and a==formed
        v['r5bm']=lambda *a:content(('candidate',)) if variant!='one_counterexample' and a==('one' if variant=='other_contract' else 'two','two','formation' if variant=='other_reference' else 'reference') else content(())
        actual=run(doc,v);expected=variant not in ('one_counterexample','other_contract','other_reference')
        assert actual==[expected],(variant,actual);generic[variant]=actual[0]
        assert 'h255k' not in v and 'h255l' not in v  # Removed with the declared r5ak boundary.
    return dict(native_material_condition=rows,native_all_four_variables_and_fixed_community=generic,
        malformed_bindings_not_vacuous=True,actual_contract_and_goal_success_not_required=True,boundaries=['r5ak','r5bm'])

@lru_cache(None)
def enumeration_checks():
    seq=('one','two','two','one','two');literal='l[a]['+' '.join('k z'+x+'[]' for x in seq)+']'
    roots=('r5bo','r5bs','r5bt','r5bu')
    doc=fixture(roots,''.join('q[t[k '+n+'['+literal+']][k zcandidate[]]].' for n in roots),('r5av','r5aw','r5bh','r5au'));rows={}
    for bits in product((False,True),repeat=3):
        v=base(doc);v['r5av']=lambda *a:bits[0] and a==('two','two','candidate')
        v['r5aw']=lambda *a:bits[1] and a==('two','candidate')
        v['r5bh']=lambda *a:a==('one','candidate');v['r5au']=lambda *a:a==('one','reference','candidate')
        v['h256y']=lambda *a:bits[2] and a==('one','two','candidate')
        actual=run(doc,v);assert actual==[any(bits),*bits],(bits,actual);rows[str(bits)]=actual
    return dict(native_aggregate_equals_inclusive_three_members=rows,boundaries=['r5av','r5aw','r5bh','r5au'])

def normalized(value):
    if isinstance(value,DescriptionValue):return (symbol(value),value.rank)
    if hasattr(value,'items') and not callable(value.items):return tuple(normalized(x) for x in value.items)
    if isinstance(value,tuple):return tuple(normalized(x) for x in value)
    return value

@lru_cache(None)
def discourse_checks():
    doc=fixture(('r5bv',),'q[k r5bv[]].',extra='');nodes=('h255s','h255t','h257r','h257s','h257t','h257u','h257v','h257w','h257x','h257y')
    whole=('r5br',3);a='author';ctx='context';family=lambda n:(n,0)
    expected={
        'h236i':{('h257r',a,whole,ctx)},
        'h257m':{('h257s',a,'h255s',whole,family('r47f'),family('r5al'),ctx)},
        'h257n':{('h257t',a,whole,family('r5al'),family('r5bp'),ctx)},
        'h257o':{('h257u',a,whole,family('r5bn'),ctx)},
        'h257p':{('h257v',a,whole,family('r5bo'),family('r5bn'),family('r5bp'),ctx)},
        'h257q':{('h257v',a,whole,tuple(family(n) for n in ('r5bs','r5bt','r5bu')),family('r5bo'),ctx)},
        'ue':{(left,right,ctx) for left,right in (('h255t','h257r'),('h257s','h257t'),('h257t','h257u'),('h257u','h257v'),('h257w','h257x'),('h257x','h257y'))},
    }
    rows={}
    for variant in ('baseline',*expected,'author','context','merged','reverse_concession','reordered_members','unknown'):
        v=base(doc);v.update({n:lambda n=n:n for n in nodes});v['wa']=lambda:'other' if variant=='author' else a
        for n,wanted in expected.items():v[n]=lambda *args,n=n,wanted=wanted:n!=variant and normalized(args) in wanted
        if variant=='context':v['h255n']=lambda:'reference'
        if variant=='merged':
            v['h257r']=lambda:'h255t'
            for n in expected:v[n]=lambda *a:True
        if variant=='reverse_concession':v['h257p']=lambda *args:normalized(args)==('h257v',a,whole,family('r5bn'),family('r5bo'),family('r5bp'),ctx)
        if variant=='reordered_members':v['h257q']=lambda *args:normalized(args)==('h257v',a,whole,tuple(family(n) for n in ('r5bu','r5bt','r5bs')),family('r5bo'),ctx)
        if variant=='unknown':
            v['h257p']=unknown
            try:run(doc,v,nodes+(a,'other'))
            except ValueError as error:assert 'Unknown' in str(error)
            else:raise AssertionError('unknown discourse was accepted')
            continue
        actual=run(doc,v,nodes+(a,'other'));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert all(v[n] is unknown for n in ('h257l','h256l','h255l','h255k','h256x','h256y'))
    return dict(closed_contents_and_same_scoped_discourse=rows,quotation_not_execution=True,unknown_rejected=True)

def reading_record():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013');cursor=444;clauses=[]
    for text,names,meaning in (
        ('Ein solcher Kontrakt, ',['r47f','r5al','r5bq','r5br','h257m'],'先の種類を保持する契約についての一般的な条件。現実の一契約を存在量化しない。'),
        ('der auf immer alle weitere Aufklärung vom Menschengeschlechte abzuhalten geschlossen würde, ',['r5aa','r5ad','r5ag','r5ah','r5ai','r5aj','r5ak','r5bq','h257n'],'全人類の今後の自己判断の進展を終点なしに妨げる同じ共同目的を持つ形成を仮定する。形成や目的の成功は断言しない。'),
        ('ist schlechterdings null und nichtig; ',['r475','r5bk','r5bn','h257o'],'同じ正当性の評価規範の下で、全規範的帰結の効力の根拠にならないという、留保のない無効性の判断。'),
        ('und sollte er auch ',['r5bm','h257p'],'同じ契約の確認を反対考慮として仮に認めても、この無効性を維持する譲歩を追加する。'),
        ('durch die oberste Gewalt, ',['r5am','r5an','r5av','r5bs'],'同じ政治的共同体の統治権限体系で最高役職を担う主体による承認。'),
        ('durch Reichstäge und ',['r5ao','r5ap','r5aq','r5ar','r5as','r5aw','r5bt','h257q'],'帝国の身分による共通事項の審議機関による承認。複数形は種類として読み列挙を継続する。'),
        ('die feierlichsten Friedensschlüsse ',['r5at','r5au','r5bh','r5bi','r5bu'],'従前の交戦を終える政治的当事者の合意で、固定比較範囲の最高度に厳粛な方式を備えるもの。'),
        ('bestätigt sein.',['h256x','h256y','r5bl','r5bo'],'同じ契約が主体の承認または和平条項を通じて確認されている状態。確認自体は正当性を保証しない。')):
        assert unit['text'][cursor:cursor+len(text)]==text,(cursor,text)
        clauses.append(dict(range=[cursor,cursor+len(text)],text=text,definitions=names,reading=meaning));cursor+=len(text)
    assert cursor==712
    page=read('data/covenant-question-reading-v1.json')['original_page'];assert digest((ROOT/page['path']).read_bytes())==page['sha256']
    return dict(status='covenant_nullity_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[444,712],text=unit['text'][444:712]),selection=selection_binding(catalog(),[98]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_covenant_nullity_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,
        newly_reviewed_sentence_characters=sum(not c.isspace() for c in unit['text'][444:712]),semantic_equivalence_automatically_proved=False,
        original_page=page|dict(visually_inspected=True),
        holistic_review=[
            '原刊488頁の前回答から次の世代への拘束を扱う後続文まで含めて再読した。solcherは先の目的付き相互宣誓の種類を受け、同じ契約に全人類への永久的な啓蒙妨害という共同目的を結ぶ。追加目的を達成済みの事実にしない。',
            '一般的なEinとgeschlossen würdeを、同種の形成を仮定する全対象への条件として読む。現在の団体や契約が一つ実在するという存在主張や、目的が実現可能だという主張は加えない。',
            '全規範的帰結について契約を効力の根拠にしない無効性を、同じ契約・共同体・固定基準・正当性の規範に結ぶ。schlechterdingsの全面性を保ち、現行権力の事実的な強制や無関係な規範源まで否定しない。',
            'und sollte er auchでは、erを同じ合意の束縛位置に保ち、確認がある全候補でも同じ無効性を維持する。確認を覆し得る反対考慮として提示する譲歩は、条件内容とは別に帰属する。確認の実在・可能性は補わない。',
            '三種類の確認を原文順に提示し、いずれの種類やその重なりでも無効性を変えない読みを明示した。最高権力と帝国身分会議は主体、和平合意は条項を通じた確認として区別する。最上級の比較範囲と同程度を保ち、全歴史的な議会・和平条約の承認へ強めない。',
            '文全体の著者帰属、前回答からの順序、仮定・照応・全面性・列挙・譲歩の作用範囲を確認した。検査はこの読解の接続を点検する証拠であり、原著者の規範判断の真理や意味同値性の自動証明ではない。第六段落全体は未判断。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,page['path'],*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:98]==old.document['statements'] and len(new.document['statements'])==99
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    assert read('data/covenant-question-reading-v1.json')['selection']==selection_binding(new,[96,97])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(preserved_statements=98,added_statements=1,preserved_whole_unit_reviews=len(reviews),preserved_opening_sentence_characters=380,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,new_reviewed_sentence_characters=read(READING)['newly_reviewed_sentence_characters'])

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('references',reference_checks),('nullity',nullity_checks),('families',family_checks),('conditional',conditional_checks),('enumeration',enumeration_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*PRIORS,read(READING)['original_page']['path'],'data/covenant-question-reading-v1.json',
        'scripts/compose_covenant_nullity.py','scripts/check_covenant_nullity.py','tests/test_covenant_nullity.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_normative_nullity.py','scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='covenant_nullity_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[98],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
