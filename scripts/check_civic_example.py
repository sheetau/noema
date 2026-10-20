"""Check all levy cases, shared criticism conditions and attributed discourse."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_example import (
    ROOT,FULL,CORE,BASIS,ANNOTATIONS,NAMES,DETAILS,PAYMENT_NAMES,PRIMITIVES,MEANINGS,LIMITS,parent,dependencies,build,closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

INDEX='data/semantic-review-index-v168.json'
REPORT='reports/civic-example-v1.json'
AUDIT='data/civic-example-reading-v1.json'
DOC='docs/civic-example-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
EVIDENCE='data/officer-example-evidence-v1.json'
IMAGE='artifacts/officer-example-v1/page-486.jpg'
PRIOR=tuple('reports/'+n+'-v1.json' for n in (
    'protected-remarks','civic-levy-refusal','levy-reproof','general-resistance','scandal-sanction'))
CONSTANTS=(*NAMES,*DETAILS,'response','responseother','norm','standard','other')
DOMAIN=CONSTANTS+('sentence','first','second','aside','prior','officer','author')
SCENES=('reference','other')
EXTRA=''.join('r z'+n+'[] a.' for n in CONSTANTS)+'r zref[] d.'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(kind,target=None):
    target=target or dict(refusal='r34p',conditional='r34q',detail='r34s',quantifier='r34u',whole='r34x',focus='r34y',discourse='r34z')[kind]
    boundaries=dict(conditional=('r34d','r34o','r34i'),detail=('r34q','r34r'),
        quantifier=('r33w','r34p','r34s','r34t'),whole=('r34u','r34v','r34w')).get(kind,())
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[target]),statements=[])
    names=dict(refusal=('community',*PAYMENT_NAMES),conditional=(*NAMES,*DETAILS),detail=NAMES,
        quantifier=(),whole=(),focus=(),discourse=())[kind]
    args=' '.join('k z'+n+'[]' for n in names)+(' k zref[]' if names else '')
    call='k '+target+'['+args+']'
    if kind!='discourse':call='t['+call+'][k zref[]]'
    return parse(format_graph(doc,'compact')+EXTRA+'q['+call+'].')


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    for n in CONSTANTS:v['z'+n]=lambda n=n:n
    v.update(zref=lambda:'reference',h232v=lambda:'reference')
    return v


def content(truth,point='reference'):return Content(SCENES,tuple(truth and p==point for p in SCENES))


def refusal_model(doc,variant='baseline'):
    v=base(doc)
    v['h245d']=lambda community,ref:'norm' if (community,ref)==('community','reference') and variant!='wrong_norm_source' else 'other'
    v['h244k']=lambda response,issuer,person,role,code,bindings,sign,ref:variant!='empty_scope' and (
        response in ('response','responseother') and (issuer,person,role,symbol(code),code.rank,tuple(bindings.items),sign,ref)==(
            'issuer','person','role','r33u',0,('person','transfer','receiver','medium'),True,'reference'))
    def prohibit(source,person,role,code,bindings,ref,sign,point):
        expected=(*PAYMENT_NAMES,bindings.items[-1])
        if variant=='wrong_response_binding':expected=(*PAYMENT_NAMES,'other')
        return not (variant=='second_unprotected' and bindings.items[-1]=='responseother') and (
            source,person,role,symbol(code),code.rank,tuple(bindings.items),ref,sign,point)==(
                'norm','person','role','r33y',1,expected,'other' if variant=='wrong_reference' else 'reference',
                variant=='positive_requirement','other' if variant=='wrong_point' else 'reference')
    v['h237z']=prohibit
    return v


@lru_cache(None)
def refusal_checks():
    doc,rows=fixture('refusal'),{}
    for variant in ('baseline','empty_scope','wrong_norm_source','second_unprotected','wrong_response_binding',
        'wrong_reference','positive_requirement','wrong_point'):
        v=refusal_model(doc,variant)
        assert all(v[n] is unknown for n in ('h7k','h244j','cg','ti'))
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant in ('baseline','empty_scope')],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,all_same_requirement_candidate_responses=True,
        normative_source_separate_from_levy_issuer=True,refusal_and_payment_not_executed=True)


def conditional_model(doc,variant='baseline'):
    v=base(doc)
    expected=(*NAMES,*DETAILS,'reference')
    v['r34d']=lambda *args:content(variant!='no_criticism' and args==expected)
    v['h245d']=lambda community,ref:'norm' if (community,ref)==('community','reference') else 'other'
    def standard(*args):
        wanted=list(NAMES)+['reference']
        if variant.startswith('wrong_standard_'):
            n=variant.removeprefix('wrong_standard_');wanted[8 if n=='reference' else NAMES.index(n)]='other'
        return 'standard' if args==tuple(wanted) else 'other'
    v['h245e']=standard
    def permitted(source,person,criticism,community,rule,ref):
        return content(variant!='no_permission' and (source,person,criticism,community,rule,ref)==(
            'norm','other' if variant=='wrong_permitted_person' else 'person',
            'other' if variant=='wrong_permitted_criticism' else 'criticism','community','standard','reference'),
            'other' if variant=='wrong_permission_point' else 'reference')
    v['r34o']=permitted
    v['r34i']=lambda criticism,community,ref:content(variant!='no_potential' and (criticism,community,ref)==(
        'other' if variant=='wrong_causing_criticism' else 'criticism',
        'other' if variant=='wrong_effect_community' else 'community','reference'),
        'other' if variant=='wrong_potential_point' else 'reference')
    return v


@lru_cache(None)
def conditional_checks():
    rows={}
    for target in ('r34q','r34r'):
        doc=fixture('conditional',target);cases={}
        variants=('baseline','no_criticism','no_permission','no_potential','wrong_permitted_person',
            'wrong_permitted_criticism','wrong_permission_point')+tuple('wrong_standard_'+n for n in (*NAMES,'reference')) if target=='r34q' else (
            'baseline','no_criticism','no_permission','no_potential','wrong_causing_criticism','wrong_effect_community','wrong_potential_point')
        for variant in variants:
            expected=variant in (('baseline','no_criticism','no_potential') if target=='r34q' else ('baseline','no_criticism','no_permission'))
            actual=evaluate(doc,conditional_model(doc,variant),DOMAIN,SCENES,True)
            assert actual==[expected],(target,variant,actual);cases[variant]=actual[0]
        rows[target]=cases
    return dict(contrasts=rows,same_condition_but_separate_main_and_aside=True,
        standard_bound_to_all_eight_levy_fields_and_reference=True,
        boundaries=['r34d/r34o/r34i are typed boundaries for connections; prior pinned reports check their native components.'])


@lru_cache(None)
def detail_checks():
    rows={}
    for target,component in (('r34s','r34q'),('r34t','r34r')):
        doc=fixture('detail',target);cases={}
        for variant in ('baseline','one_failed_combination','wrong_levy','wrong_person','wrong_reference','wrong_point'):
            v=base(doc)
            for n in CONSTANTS:v['z'+n]=lambda n=n:'x' if NAMES.count(n) and NAMES.index(n)%2==0 else 'y'
            wanted=['x','y','x','y','x','y','x','y']
            if variant in ('wrong_levy','wrong_person'):wanted[NAMES.index(variant[6:])]='other'
            def item(*args):
                good=args[:8]==tuple(wanted) and args[-1]==('other' if variant=='wrong_reference' else 'reference')
                if variant=='one_failed_combination' and args[8:12]==('x','y','x','y'):good=False
                return content(good,'other' if variant=='wrong_point' else 'reference')
            v[component]=item
            actual=evaluate(doc,v,('x','y'),SCENES,True)
            assert actual==[variant=='baseline'],(target,variant,actual);cases[variant]=actual[0]
        rows[target]=cases
    return dict(contrasts=rows,all_four_criticism_arguments_quantified=True,
        boundaries=['r34q/r34r are typed boundaries for four-argument universality; conditional checks test their native joins.'])


@lru_cache(None)
def quantifier_checks():
    rows={};mixed=('x','y','x','y','x','y','x','y')
    for target,component in (('r34u','r34p'),('r34v','r34s'),('r34w','r34t')):
        doc=fixture('quantifier',target);cases={}
        for variant in ('baseline','empty_scope','second_failure','wrong_person','wrong_community','wrong_reference','wrong_point'):
            v=base(doc);selected=set() if variant=='empty_scope' else ({mixed,('y',)*8} if variant=='second_failure' else {mixed})
            v['r33w']=lambda *args:args[:-1] in selected and args[-1]=='reference'
            fields=('community',*PAYMENT_NAMES) if component=='r34p' else NAMES
            wanted=[mixed[NAMES.index(n)] for n in fields]+['reference']
            if variant in ('wrong_person','wrong_community'):wanted[fields.index(variant[6:])]='other'
            if variant=='wrong_reference':wanted[-1]='other'
            v[component]=lambda *args:content(args==tuple(wanted),'other' if variant=='wrong_point' else 'reference')
            actual=evaluate(doc,v,('x','y'),SCENES,True)
            assert actual==[variant in ('baseline','empty_scope')],(target,variant,actual);cases[variant]=actual[0]
        rows[target]=cases
    return dict(contrasts=rows,all_eight_levy_arguments_quantified=True,
        refusal_clause_independent_of_actual_criticism=True,
        boundaries=['r33w and each case consequence are typed boundaries for whole-clause quantification; native joins are checked separately.'])


@lru_cache(None)
def whole_checks():
    doc=fixture('whole');rows=[]
    for missing in (None,'r34u','r34v','r34w'):
        v=base(doc)
        for n in ('r34u','r34v','r34w'):v[n]=lambda n=n:content(n!=missing)
        actual=evaluate(doc,v,DOMAIN,SCENES,True);assert actual==[missing is None]
        rows.append(dict(missing=missing,value=actual[0]))
    return dict(cases=rows,all_three_contents_at_same_point=True,boundaries=['The three clause contents are typed boundaries here.'])


@lru_cache(None)
def focus_checks():
    doc,rows=fixture('focus'),{}
    for variant in ('baseline','equal','incomparable','reversed','nonreflexive','wrong_view','wrong_reference'):
        v=base(doc);v['wa']=lambda:'author'
        def ranked(view,left,right,ref):
            if (view,ref)!=('other' if variant=='wrong_view' else 'author','other' if variant=='wrong_reference' else 'reference'):return False
            assert left.rank==right.rank==2
            a,b=symbol(left),symbol(right)
            if a==b:return variant!='nonreflexive'
            if variant=='equal':return True
            if variant=='incomparable':return False
            return (a,b)==(('r34v','r34u') if variant=='reversed' else ('r34u','r34v'))
        v['h245j']=ranked
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,native_strict_qualitative_expectation=True,quoted_contents_not_executed=True)


def discourse_model(doc,variant='baseline'):
    v=base(doc)
    v.update(h245f=lambda:'sentence',h245g=lambda:'first',h245h=lambda:'second',h245i=lambda:'aside',
        h244f=lambda:'prior',h243t=lambda:'officer',wa=lambda:'author',h232o=lambda:'reference')
    records={'sentence':'r34x','first':'r34u','second':'r34v','aside':'r34w'}
    v['h236i']=lambda node,a,code,ctx:(
        not (variant=='missing_aside' and node=='aside') and (a,symbol(code),code.rank,ctx)==('author',records.get(node),3,'reference'))
    v['h245k']=lambda n,a,first,old,second,new,bg,ctx:(n,a,first,symbol(old),old.rank,second,symbol(new),new.rank,symbol(bg),bg.rank,ctx)==(
        'sentence','author','first','r34u',3,'second','r34u' if variant=='wrong_focus' else 'r34v',3,'r34y',3,'reference')
    v['h234k']=lambda aside,a,anchor,ctx:(aside,a,anchor,ctx)==('aside','author','first' if variant=='wrong_aside_anchor' else 'second','reference')
    v['h245l']=lambda n,a,main,code,aside,explanation,assessment,ctx:(n,a,main,symbol(code),code.rank,aside,symbol(explanation),explanation.rank,symbol(assessment),assessment.rank,ctx)==(
        'sentence','author','second','r34v',3,'aside','r34w',3,'r34a' if variant=='wrong_assessment' else 'r34j',0,
        'other' if variant=='wrong_context' else 'reference')
    v['h245m']=lambda n,a,prior,old,new,ctx:(n,a,prior,symbol(old),old.rank,symbol(new),new.rank,ctx)==(
        'sentence','author','officer','r33q' if variant=='wrong_prior_content' else 'r324',3,'r34x',3,'reference')
    v['ue']=lambda before,after,ctx:variant!='wrong_order' and (before,after) in (('prior','sentence'),('first','second')) and ctx=='reference'
    return v


@lru_cache(None)
def discourse_checks():
    doc,rows=fixture('discourse'),{}
    for variant in ('baseline','missing_aside','wrong_focus','wrong_aside_anchor','wrong_assessment','wrong_context','wrong_prior_content','wrong_order'):
        v=discourse_model(doc,variant)
        assert all(v[n] is unknown for n in ('h245d','h245e','h245j','h7k','h245c','h244s'))
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,rank_three_attribution_focus_aside_parallel_example=True,
        assessment_and_all_world_contents_not_executed=True)


@lru_cache(None)
def unknown_checks():
    rows=[]
    for kind,model,names in (('refusal',refusal_model,('h245d','h237z')),
        ('conditional',conditional_model,('h245e',)),('discourse',discourse_model,('h245k','h245l','h245m'))):
        doc=fixture(kind)
        for name in names:
            v=model(doc);v[name]=unknown
            try:evaluate(doc,v,DOMAIN,SCENES,True)
            except ValueError as error:assert 'Unknown' in str(error)
            else:raise AssertionError(name)
            rows.append(name)
    return dict(unknown_inputs_refused=rows)


def reading():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0012')
    parts=[
        ('Der Bürger ',['r33s','r33w','r34u'],'同じ政治的共同体で公的負担を課される市民の一般例。官吏任用は不要。'),
        ('kann sich nicht weigern, ',['r33x','r33y','r34p','r34u'],'同じ要求への全候補反応に、拒否を禁じる規範を適用する。'),
        ('die ihm auferlegten Abgaben zu leisten; ',['r33t','r33u','r33v','r33w'],'同じ本人に課された公的賦課と納付内容を出所・立場・移転・受取先・媒体で束縛する。'),
        ('sogar ',['r34y','h245k','r34z'],'先行の拒否禁止に加えて批判の処罰可能性まで述べる取り立てと、その期待背景。'),
        ('kann ein vorwitziger Tadel solcher Auflagen, ',['r34a','r34b','r34c','r34d','r34q','r34v'],'同じ賦課への批判、自ら取る立場と固定した条件の不足。批判内容の真理とは分ける。'),
        ('wenn sie von ihm geleistet werden sollen, ',['r33v','r34d'],'同じ納付要求が同じ批判時にも適用される条件。納付済み・実際の拒否とはしない。'),
        ('als ein Skandal ',['r34j','r34k','h244z','h245e'],'同じ要求の義務規則を軽視する公然の例として同じ批判を評価した根拠による措置。'),
        ('(das allgemeine Widersetzlichkeiten veranlassen könnte) ',['r34e','r34f','r34g','r34h','r34i','r34r','r34t','r34w','h234k','h245l'],'同じ共同体の一般的反抗を誘発し得るという条件付き補足。実際の反抗を前提にしない。'),
        ('bestraft werden.',['r34k','r34l','r34n','r34o','r34q','r34v'],'同じ規範源から、制度上の施行者・立場・措置についての許可があるという規範的処罰可能性。'),
    ]
    cursor,clauses=2513,[]
    for text,names,meaning in parts:
        assert unit['text'][cursor:cursor+len(text)]==text,(cursor,text)
        clauses.append(dict(range=[cursor,cursor+len(text)],text=text,definitions=names,reading=meaning));cursor+=len(text)
    assert cursor==2770
    text=unit['text'][2513:2770];count=sum(not c.isspace() for c in text)
    page=next(p for p in read(EVIDENCE)['pages'] if p['page']==486)
    assert digest((ROOT/IMAGE).read_bytes())==page['sha256']
    return dict(status='civic_example_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[2513,2770],text=text),selection=selection_binding(catalog(),[84]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_civic_levy_and_qualified_punishability',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=count,
        preserved_reviewed_sentence_characters=2148,paragraph_reviewed_sentence_characters=2148+count,
        semantic_equivalence_automatically_proved=False,holistic_review=[
            '原刊486頁のDer Bürgerからbestraft werdenまでと次の学識者としての批判を認める文を通読し、全ての節と括弧を対応させた。',
            '納付する市民、賦課の対象、実践的拒否、批判、Skandalとしての評価、処罰の対象を同じ束縛に保ち、別の要求・本人・共同体を借りない。',
            '第一節の拒否禁止は批判の有無に依存しない。全候補反応への禁止であり、現に拒否した反応だけを選ぶ構成ではない。',
            '第二節の条件には批判時にも同じ納付要求が適用されることを含め、実際の拒否や未払い、批判の命題の偽を補わない。',
            '規範的処罰可能性を採用し、同じ賦課に関する義務規則を評価へ渡す。実行可能性・実際の処罰・処罰の義務・道徳的正当性は付加しない。',
            '括弧は同じ批判の誘発可能性をSkandal評価に関する補足として提示する。反抗の現実の発生を許可条件へ移さず、因果可能性から一般的な処罰許可を論理的に導出しない。',
            'sogarの焦点は処罰可能性の節であり、拒否禁止との期待比較を背景として分けた。先行将校の例と並べる関係と本文順序を保持する。',
            '次文の学識者としての批判の許容をこの文で撤回せず、全批判の禁止には広げない。採用した語義・様相・一般性・期待比較の読みを明示し、唯一の歴史的解釈や自動証明とはしない。'],
        original_page=page,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (
            FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,EVIDENCE,IMAGE,*PRIOR,'data/vorwitzig-reading-v1.json','data/scandal-reading-v1.json')})


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    assert new.document['statements'][:84]==old.document['statements'] and len(new.document['statements'])==85
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for p in PRIOR:validate_hashes(ROOT,read(p)['source_sha256'])
    prior=read('data/protected-remarks-reading-v1.json');assert prior['selection']==selection_binding(new,[83]);validate_hashes(ROOT,prior['source_sha256'])
    assert read(AUDIT)==reading()
    for p,s in build().items():assert (ROOT/p).read_text(encoding='utf-8')==s,p
    for p in (FULL,CORE):
        doc=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(preserved_statements=84,added_statements=1,preserved_whole_unit_reviews=len(reviews),
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_reviewed_sentence_characters=222,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,s in build().items():write_exact(ROOT/p,s)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('refusal',refusal_checks),('conditional',conditional_checks),('detail',detail_checks),
        ('quantifiers',quantifier_checks),('whole',whole_checks),('focus',focus_checks),('discourse',discourse_checks),
        ('unknown',unknown_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,AUDIT,DOC,INVENTORY,EVIDENCE,IMAGE,*PRIOR,
        'data/protected-remarks-reading-v1.json','scripts/compose_civic_example.py','scripts/check_civic_example.py','tests/test_civic_example.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='civic_levy_refusal_and_qualified_normative_sanction',document=FULL,**results,
        alignment=dict(**read(AUDIT)['source'],statements=[84],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
