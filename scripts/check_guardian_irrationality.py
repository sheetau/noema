"""Check specified criterion, common references, self focus and Denn direction."""
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
from scripts.compose_guardian_irrationality import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

INDEX='data/semantic-review-index-v179.json'
REPORT='reports/guardian-irrationality-v1.json'
AUDIT='data/guardian-irrationality-reading-v1.json'
DOC='docs/guardian-irrationality-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
EVIDENCE='data/irrational-perpetuation-evidence-v1.json'
PRIORS=('reports/spiritual-guardians-v2.json','reports/irrational-perpetuation-v1.json','reports/unrestricted-scholarly-freedom-v1.json')
SCENES=('reference','actual','context')
DOMAIN=('source','people','community','standard','requirement','guardian','role','matter','public','other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'r zref[] d.r zpoint[] d.'
ARGS=' '.join('k z'+n+'[]' for n in DOMAIN[:5])+' k zref[]'


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
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update(zref=lambda:'reference',zpoint=lambda:'actual',h232v=lambda:'reference',h232o=lambda:'context')
    return v
def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)
def content(value):return Content(SCENES,tuple(value and p=='actual' for p in SCENES))


@lru_cache(None)
def criterion_checks():
    from scripts.check_spiritual_guardians_v2 import model
    from scripts.check_spiritual_guardians import EXTRA as NEXTRA,DOMAIN as NDOMAIN,SCENES as NSCENES,POLICY
    doc=fixture(('r45v','r45r'),'q[t[k r45v['+POLICY+']][k zpoint[]]].q[t[k r45r['+POLICY+']][k zpoint[]]].',extra=NEXTRA)
    rows=[]
    for bits in product((False,True),repeat=2):
        v,_=model(doc);old=v['h237z']
        v['h237z']=lambda source,person,*args:old(source,person,*args) and dict(g=bits[0],h=bits[1]).get(person,False)
        actual=evaluate(doc,v,NDOMAIN,NSCENES,True)
        assert actual==[not any(bits),all(bits)],(bits,actual);rows.append([*bits,*actual])
    v,_=model(doc,'no_guardians');assert evaluate(doc,v,NDOMAIN,NSCENES,True)==[True,False]
    # The requirement is a uniform condition over all guardians; its use as a
    # criterion does not assert it true in the present world.
    adapters={}
    for members in ((),('source','people'),('source','people','community'),('people','source','community'),('source','people','community','source')):
        seq='l[a]['+' '.join('k z'+n+'[]' for n in members)+']'
        d=fixture(('r45w',),'q[t[k r45w['+seq+' k zref[]]][k zpoint[]]].',('r45v',))
        v=base(d);v['r45v']=lambda s,p,c,r:content((s,p,c,r)==('source','people','community','reference'))
        actual=run(d,v,('source','people','community'));assert actual==[members==('source','people','community')];adapters[str(members)]=actual[0]
    return dict(native_criterion_and_policy=rows,empty_guardians_do_not_supply_policy=True,exact_condition_bindings=adapters,
        adapter_boundary='r45v; all guardians evaluated separately',criterion_not_asserted_as_actual=True)


@lru_cache(None)
def grounding_checks():
    doc=fixture(('r45x',),'q[t[k r45x['+ARGS+']][k zpoint[]]].',('r45d','r45q'))
    variants=('baseline','wrong_people','no_guardian','no_condition','wrong_condition','wrong_requirement','wrong_standard','wrong_reference',
        'inapplicable','other_failed_requirement','no_negative','conflict','no_consequence','old_policy','wrong_result','wrong_result_bindings','wrong_point')
    rows={}
    for variant in variants:
        v=base(doc)
        v['r45d']=lambda p,c,r:variant!='wrong_people' and (p,c,r)==('people','community','reference')
        v['r45q']=lambda p,role,people,c,m,r:variant!='no_guardian' and (p,role,people,c,m,r)==('guardian','role','people','community','matter','reference')
        def condition(s,req,code,ref):
            wanted=['standard','requirement','r45w',2,'reference']
            i={'wrong_standard':0,'wrong_requirement':1,'wrong_condition':2,'wrong_reference':4}.get(variant)
            if i is not None:wanted[i]='other'
            return variant!='no_condition' and (s,req,symbol(code),code.rank,ref)==tuple(wanted)
        v['h253y']=condition
        def applicable(s,req,code,bindings,ref):
            return variant!='inapplicable' and (s,req,symbol(code),code.rank,tuple(bindings.items),ref)==('standard',
                'other' if variant=='other_failed_requirement' else 'requirement','r45i' if variant=='old_policy' else 'r45s',2,('source','people','community'),'reference')
        v['h253s']=applicable
        v['h253t']=lambda s,req,code,b,r,pos,point:applicable(s,req,code,b,r) and point==('context' if variant=='wrong_point' else 'actual') and (variant=='conflict' if pos else variant!='no_negative')
        v['h253x']=lambda cause,cb,result,rb,ref,point:variant!='no_consequence' and (symbol(cause),cause.rank,tuple(cb.items),symbol(result),result.rank,tuple(rb.items),ref,point)==(
            'r45s',2,('source','people','community'),'other' if variant=='wrong_result' else 'r45o',2,
            ('community','other') if variant=='wrong_result_bindings' else ('community','standard'),'reference','actual')
        actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        if variant=='baseline':
            for n in ('h253y','h253s','h253t','h253x'):
                original=v[n];v[n]=unknown
                try:run(doc,v)
                except ValueError as error:assert 'Unknown' in str(error)
                else:raise AssertionError(n)
                v[n]=original
    return dict(contrasts=rows,specified_requirement_not_arbitrary_failure=True,native_appraisal_and_causal_connection=True,
        boundaries=['r45d','r45q; previously checked natively'],unknown_rejected=True,policy_condition_and_result_not_executed=True)


def references(v,variant='baseline'):
    v['h234t']=lambda context:'public' if context=='context' else 'other'
    v['h227a']=lambda public,ref:'community' if (public,ref)==('public','reference') else 'other'
    for name,value in (('h254a','source'),('h253z','people'),('h254b','standard'),('h254c','requirement')):
        v[name]=lambda community,ref,name=name,value=value:value if (community,ref)==('community','reference') and variant!=name else 'other'


@lru_cache(None)
def reference_focus_checks():
    doc=fixture(('r45y',),'q[t[k r45y[]][k zpoint[]]].',('r45x',));rows={}
    for variant in ('baseline','h254a','h253z','h254b','h254c','community','public','reference','context'):
        v=base(doc);references(v,variant)
        for key,name in (('community','h227a'),('public','h234t'),('reference','h232v'),('context','h232o')):
            if variant==key:v[name]=lambda *a,key=key:'other' if key in ('community','public') else 'actual'
        v['r45x']=lambda s,p,c,standard,req,ref:content((s,p,c,standard,req,ref)==('source','people','community','standard','requirement','reference'))
        actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    focus_rows={};small=('one','two');extra='r zone[] a.r ztwo[] a.r zpoint[] d.'
    correct=('one','two','one','one','two')
    choices=[(),correct,(*correct,'one')]+[tuple(('two' if x=='one' else 'one') if j==i else x for j,x in enumerate(correct)) for i in range(5)]
    for members in choices:
        seq='l[a]['+' '.join('k z'+n+'[]' for n in members)+']'
        d=fixture(('r45z','r452'),'q[t[k r45z['+seq+']][k zpoint[]]].q[t[k r452['+seq+']][k zpoint[]]].',('r45q',),extra)
        v=base(d);v.update(zone=lambda:'one',ztwo=lambda:'two',h234t=lambda ctx:'one',h227a=lambda p,r:'two',h253z=lambda c,r:'one',h254a=lambda c,r:'one')
        v['r45q']=lambda person,role,people,c,m,ref:(person,role,people,c,m,ref)==('two','one','one','two','one','reference')
        v['h237z']=lambda s,p,role,code,b,ref,positive,point:(s,p,role,symbol(code),code.rank,tuple(b.items),ref,positive,point)==('one','two','one','r45f',1,('two',),'reference',True,'actual')
        actual=run(d,v,small);assert actual==[members==correct]*2,(members,actual);focus_rows[str(members)]=actual
    return dict(reference_contrasts=rows,self_focus_exact_five_bindings=focus_rows,last_position_is_guardian_not_ward=True,
        boundaries=['r45x','r45q'],native_same_person_norm_target=True)


@lru_cache(None)
def discourse_checks():
    doc=fixture(('r453',),'q[k r453[]].');domain=('whole','focus','prior','author','other');rows={}
    for variant in ('baseline','author','context','whole_content','scope','focus_content','ground','conclusion','order','merged'):
        v=base(doc);v.update(wa=lambda:'author',h254d=lambda:'whole',h254e=lambda:'focus',h253m=lambda:'prior')
        v['h236i']=lambda n,a,c,ctx:(n,a,symbol(c),c.rank,ctx)==('whole','other' if variant=='author' else 'author',
            'r447' if variant=='whole_content' else 'r45y',3,'actual' if variant=='context' else 'context')
        v['h224s']=lambda n,a,c,s,f,ctx:(n,a,symbol(c),symbol(s),symbol(f),ctx)==('focus','author','r45y',
            'r452' if variant=='scope' else 'r45z','r45z' if variant=='focus_content' else 'r452','context') and c.rank==s.rank==f.rank==3
        v['ud']=lambda a,grounds,conclusion,ctx:(a,{n for n in domain if grounds(n)},conclusion,ctx)==('author',
            {'prior'} if variant=='ground' else {'whole'},'whole' if variant=='conclusion' else 'prior','context')
        v['ue']=lambda a,b,ctx:(a,b,ctx)==(*(('whole','prior') if variant=='order' else ('prior','whole')),'context')
        if variant=='merged':
            v['h254e']=lambda:'whole'
            for n in ('h236i','h224s','ud','ue'):v[n]=lambda *a:True
        actual=run(doc,v,domain);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,reason_points_back_to_prior_freedom=True,text_order_opposite_to_reason_direction=True,
        same_author_context_rank_three_contents=True,quoted_contents_not_executed=True)


def reading():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0012');text=u['text'][5022:5190]
    parts=[
        ('Denn ',['ud','h254d','h253m'],'この最終文全体を、先行する学識者の無制限の自由を支える理由として提示する。'),
        ('daß die Vormünder des Volks ',['r45d','r45q','h253z','h227a'],'同じ政治的共同体の全成員である人民の、宗教上の後見役を方針の対象に取る。'),
        ('(in geistlichen Dingen) ',['sg','h253r','r45q'],'同じ相手の宗教的な事柄が同じ指導役割の担当範囲であることを明示する。'),
        ('selbst wieder ',['h224s','r45z','r452'],'他者を導く役割の本人自身も依存を要求されるという自己取り立て。以前の成熟から再転落した履歴は加えない。'),
        ('unmündig sein sollen, ',['bf','r45f','r45g','r45r','r45s'],'本人の未成熟への要求を全該当する後見役について構成し、その方針を引用して評価する。本人の現実の未成熟や著者の要求を主張しない。'),
        ('ist eine Ungereimtheit, ',['r45v','r45w','h253y','h253s','h253t','r45x'],'指導する役割の本人に自立的判断の不能を要求しないという指定要件への不適合として方針を評価する。'),
        ('die auf Verewigung der Ungereimtheiten hinausläuft.',['r45m','r45n','r45o','rca','h253x','r45u'],'同じ方針の適用・維持が、同じ共同体の不合理と評価される全関連内容の将来履歴全体での社会的維持へ至る。')]
    cursor=5022;clauses=[]
    for t,names,meaning in parts:
        assert u['text'][cursor:cursor+len(t)]==t,(cursor,t)
        clauses.append(dict(range=[cursor,cursor+len(t)],text=t,definitions=names,reading=meaning));cursor+=len(t)
    assert cursor==5190 and sum(not c.isspace() for c in text)==146
    pages=read(EVIDENCE)['pages']
    for p in pages:assert p['visually_inspected'] and digest((ROOT/p['path']).read_bytes())==p['sha256']
    return dict(status='guardian_irrationality_final_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[5022,5190],text=text),selection=selection_binding(catalog(),[95]),clauses=clauses,
        interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_guardian_irrationality',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=146,
        preserved_reviewed_sentence_characters=4286,paragraph_reviewed_sentence_characters=4432,semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '原刊487頁末から488頁冒頭へ続く最終文を、直前の無制限の公的自由と続く次段落から区別した。人民の宗教上の後見役という主語、括弧の範囲限定、本人の未成熟への要求を一つの方針内容へ接続した。',
            '本人が未成熟だという事実と、未成熟を要求する方針の評価を分けた。sgの引数訂正を引き継ぎ、同じ本人・相手・役割・事柄を保つ。selbst wiederは指導者本人も依存を要求される取り立てとし、時間的な再発を補わない。',
            '単数の不合理は方針に対する整合性評価、複数の不合理は同じ共同体の宗教上の教え・実践のうち同じ基準時に不合理と評価する全関連内容として区別した。指定した評価要件を閉じたNoema条件へ結び、任意の別要件の失敗で済ませない。',
            'Verewigungは基準以後の同じ履歴全体で各内容が社会的に維持される読み。原因側の同じ方針と結果側の構成・束縛をh253xに保持し、単なる同時成立へ弱めない。数値的無限や個人の不死は追加しない。',
            '全文主張と本人の取り立てを同じ著者・段落文脈へ帰属し、Dennの理由提示を前文へ向けた。引用した要求・未成熟・評価要件・結果は外側で実行しない。全語句と参照・範囲を通読し146文字を判断した。第五段落全体の統合通読は別に残す。'],
        original_pages=pages,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,EVIDENCE,*PRIORS,*[p['path'] for p in pages])})


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:95]==old.document['statements'] and len(new.document['statements'])==96
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert not {'r45e','r45h','r45i','r45k','r45p'}&set(new.entries)
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    prior=read('data/unrestricted-scholarly-freedom-reading-v1.json');assert prior['selection']==selection_binding(new,[94]);validate_hashes(ROOT,prior['source_sha256'])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(AUDIT)==reading()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            t=format_graph(doc,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==doc
    return dict(preserved_statements=95,added_statements=1,preserved_whole_unit_reviews=len(reviews),new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        obsolete_guardian_definitions_excluded=True,new_reviewed_sentence_characters=146,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for n,f in [('criterion',criterion_checks),('grounding',grounding_checks),('references_and_focus',reference_focus_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,AUDIT,DOC,INVENTORY,EVIDENCE,*PRIORS,*[p['path'] for p in read(EVIDENCE)['pages']],
        'data/unrestricted-scholarly-freedom-reading-v1.json','scripts/compose_guardian_irrationality.py','scripts/check_guardian_irrationality.py',
        'tests/test_guardian_irrationality.py','scripts/check_spiritual_guardians_v2.py','scripts/check_spiritual_guardians.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/compose_spiritual_guardians.py','scripts/compose_irrational_perpetuation.py'}
    return dict(status='guardian_irrationality_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(AUDIT)['source'],statements=[95],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
