"""Check resistance responses, complete population, and aligned possible outcomes."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_general_resistance import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/general-resistance-v1.json'
DOC='docs/general-resistance-v1.md'
PRIOR='reports/levy-reproof-v1.json'
DOMAIN=('issuer','person','role','response','community','criticism','second','third','other')
SCENES=('reference','possible','other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'r zref[] d.r zpoint[] d.r zsign[] c.r zcontent[j[a]] e.'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(kind):
    target=dict(response='r34e',individual='r34f',coverage='r34g',breadth='r34h',potential='r34i')[kind]
    doc=deepcopy(catalog().document)
    if kind in ('breadth','potential'):
        declaration=next(d for d in doc['declarations'] if d['name']=='r34f')
        declaration.update(kind='primitive',parameters=[p['sort'] for p in declaration['parameters']]);declaration.pop('body')
    doc.update(declarations=closure(doc,[target]),statements=[])
    args=dict(response='k zissuer[] k zperson[] k zrole[] k zresponse[] k zcommunity[] r[p zcontent] '
        'l[a][k zperson[] k zresponse[]] k zsign[] k zref[]',
        individual='k zperson[] k zcommunity[] k zref[]',coverage='k zcommunity[] k zref[]',
        breadth='k zcommunity[] k zref[]',potential='k zcriticism[] k zcommunity[] k zref[]')[kind]
    call='k '+target+'['+args+']'
    if kind!='coverage':call='t['+call+'][k zpoint[]]'
    return parse(format_graph(doc,'compact')+EXTRA+'q['+call+'].')


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    for n in DOMAIN:v['z'+n]=lambda n=n:n
    v.update(zref=lambda:'reference',zpoint=lambda:'possible',zsign=lambda:True)
    return v


def response_model(doc,variant='baseline',sign=True):
    v=base(doc);v['zsign']=lambda:sign
    v.update(aa=lambda p:p=='person',
        h237c=lambda p,community,ref:(p,community,ref)==('person','community','reference'),
        hzwn=lambda p,role,ref:(p,role,ref)==('person','role','reference'),
        h244g=lambda role,community,ref:(role,community,ref)==('role','community','reference'),
        h244p=lambda issuer,community,ref:variant!='private_direction' and (issuer,community,ref)==(
            'issuer','other' if variant=='other_public_community' else 'community','reference'),
        cg=lambda p,act,point:variant!='not_enacted' and (p,act,point)==('person','response','possible'))
    def requirement(issuer,p,role,code,bindings,polarity,point):
        return variant!='no_requirement' and (issuer,p,role,symbol(code),code.rank,tuple(bindings.items),polarity,point)==(
            'other' if variant=='other_issuer' else 'issuer','person','role',
            'other' if variant=='other_required_description' else 'zcontent',0,('person','response'),sign,'possible')
    def reply(act,issuer,p,role,code,bindings,polarity,ref):
        return (act,issuer,p,role,symbol(code),code.rank,tuple(bindings.items),polarity,ref)==(
            'other' if variant=='other_response' else 'response','issuer','person','role','zcontent',0,
            ('response','person') if variant=='other_response_bindings' else ('person','response'),
            not sign if variant=='other_response_sign' else sign,
            'other' if variant=='other_response_reference' else 'reference')
    def stance(p,act,code,bindings,polarity,point):
        return variant!='no_stance' and (p,act,symbol(code),code.rank,tuple(bindings.items),polarity,point)==(
            'person','other' if variant=='other_stance_event' else 'response','zcontent',0,
            ('response','person') if variant=='other_stance_bindings' else ('person','response'),
            sign if variant=='acceptance' else not sign,'other' if variant=='other_stance_point' else 'possible')
    v.update(h7k=requirement,h244k=reply,h244j=stance)
    return v


@lru_cache(None)
def response_checks():
    doc,rows=fixture('response'),{}
    for sign in (False,True):
        cases={}
        for variant in ('baseline','private_direction','other_public_community','not_enacted','no_requirement',
            'other_issuer','other_required_description','other_response','other_response_bindings','other_response_sign',
            'other_response_reference','no_stance','other_stance_event','other_stance_bindings','acceptance','other_stance_point'):
            v=response_model(doc,variant,sign)
            assert v['zcontent'] is unknown
            actual=evaluate(doc,v,DOMAIN,SCENES,True)
            assert actual==[variant=='baseline'],(sign,variant,actual);cases[variant]=actual[0]
        rows[str(sign)]=cases
    return dict(polarity_contrasts=rows,native_response_definition=True,
        arbitrary_requirement_description_not_payment_only=True,required_content_not_executed=True,
        failure_to_comply_alone_insufficient=True)


def breadth_model(doc,variant='baseline'):
    v=base(doc)
    population=('person','second','third')
    listed=population
    if variant=='missing_member':listed=('person','second')
    if variant=='extra_member':listed=population+('other',)
    if variant=='duplicate':listed=population+('person',)
    if variant=='empty':population=listed=()
    if variant=='reordered':listed=tuple(reversed(population))
    v.update(aa=lambda p:p in ('person','second','third','other'),
        h237c=lambda p,community,ref:p in population and (community,ref)==('community','reference'),
        h244q=lambda community,ref:SequenceValue(listed if (community,ref)==('community','reference') else (), '"individual"'),
        ha=lambda a,b:a+b,hb=lambda a,b:a*b,hc=lambda a,b:a<b,hd=lambda truth:Fraction(int(truth)),
        pa=lambda a,b:a/b if b else Fraction(0))
    selected=() if variant in ('no_resistance','zero_accepted') else (
        ('person',) if variant=='isolated' else ('person','second'))
    def individual(person,community,ref):
        return Content(SCENES,tuple(person in selected and (community,ref)==(
            'other' if variant=='other_resistance_community' else 'community',
            'other' if variant=='other_resistance_reference' else 'reference') and point==(
            'other' if variant=='other_resistance_point' else 'possible') for point in SCENES))
    v['r34f']=individual
    v['h244r']=lambda community,ref,ratio:(community,ref)==(
        'community','other' if variant=='other_breadth_reference' else 'reference') and (
        True if variant=='zero_accepted' else ratio >= (Fraction(1) if variant=='strict_context' else Fraction(2,3)))
    return v


@lru_cache(None)
def breadth_checks():
    rows={}
    for variant in ('baseline','reordered','missing_member','extra_member','duplicate','empty','no_resistance','isolated',
        'zero_accepted','other_resistance_community','other_resistance_reference','other_resistance_point',
        'other_breadth_reference','strict_context'):
        doc=fixture('breadth')
        actual=evaluate(doc,breadth_model(doc,variant),DOMAIN,SCENES,True)
        assert actual==[variant in ('baseline','reordered')],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,native_complete_population_and_rfl_ratio=True,
        zero_rejected_even_if_context_accepts_it=True,all_people_or_majority_not_hardcoded=True,
        boundaries=['r34f is a typed boundary; r34e is checked natively and unrestricted r34f quantification is preserved.'])


def potential_model(doc,variant='baseline'):
    v=breadth_model(doc,variant);v['zpoint']=lambda:'reference'
    def prospects(act,community,evaluation,outcome):
        return variant!='no_candidates' and (act,community,evaluation)==(
            'criticism','other' if variant=='other_candidate_community' else 'community','reference') and outcome in (
            ('possible','other') if variant in ('mixed_candidates','split_cause','split_effect') else ('possible',))
    v['h244t']=prospects
    v['dg']=lambda act,point:variant!='no_criticism' and (act,point)==('criticism','possible')
    def induces(act,community,code,ref,outcome):
        return variant!='cooccurrence_only' and (act,community,symbol(code),code.rank,ref,outcome)==(
            'other' if variant=='other_cause_activity' else 'criticism',
            'other' if variant=='other_effect_community' else 'community','r34h',1,
            'other' if variant=='other_effect_reference' else 'reference','other' if variant=='split_cause' else 'possible')
    v['h244s']=induces
    if variant=='split_effect':
        original=v['r34f']
        v['r34f']=lambda *args:Content(SCENES,(False,False,original(*args).values[1]))
    return v


@lru_cache(None)
def potential_checks():
    rows={};doc=fixture('potential')
    for variant in ('baseline','mixed_candidates','no_candidates','other_candidate_community','no_criticism',
        'cooccurrence_only','other_cause_activity','other_effect_community','other_effect_reference','split_cause',
        'split_effect','no_resistance','missing_member'):
        v=potential_model(doc,variant)
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant in ('baseline','mixed_candidates')],(variant,actual);rows[variant]=actual[0]
    # The positive possibility model has no actual resistance at its reference situation.
    actual=breadth_model(fixture('breadth'));actual['zpoint']=lambda:'reference'
    assert evaluate(fixture('breadth'),actual,DOMAIN,SCENES,True)==[False]
    return dict(contrasts=rows,native_rfj_and_breadth_with_individual_boundary=True,
        one_shared_possible_outcome_required=True,actual_resistance_not_required=True,
        no_permission_or_punishment_inference=True)


@lru_cache(None)
def domain_checks():
    doc=fixture('individual')
    try:evaluate(doc,response_model(doc),DOMAIN,SCENES,True)
    except ValueError as error:assert 'Cannot finitely quantify the description domain' in str(error)
    else:raise AssertionError('Unrestricted descriptions were finitely substituted')
    declaration=catalog().entries['r34f']['declaration']
    nodes=[]
    def visit(value):
        if isinstance(value,dict):
            nodes.append(value)
            for x in value.values():visit(x)
        elif isinstance(value,list):
            for x in value:visit(x)
    visit(declaration)
    assert any(n.get('kind')=='description' for n in nodes)
    assert any(n.get('kind')=='sequence' and n.get('element')=='individual' for n in nodes)
    return dict(full_description_domain_rejected_by_finite_evaluator=True,
        unbounded_binding_sequence_domain_preserved=True,finite_known_requirement_substitution=False)


@lru_cache(None)
def unknown_checks():
    rows=[]
    for kind,model,names in (('response',response_model,('h244p','h7k','h244j','h244k')),
        ('breadth',breadth_model,('h244q','h244r','r34f')),
        ('potential',potential_model,('h244s','h244t'))):
        doc=fixture(kind)
        for name in names:
            v=model(doc);v[name]=unknown
            try:evaluate(doc,v,DOMAIN,SCENES,True)
            except ValueError as error:assert 'Unknown' in str(error)
            else:raise AssertionError(name)
            rows.append(name)
    return dict(unknown_inputs_refused=rows)


@lru_cache(None)
def structure_checks():
    new=catalog();assert not new.document['statements']
    source={n:e for parent in parents() for n,e in parent.entries.items()}
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==source[n]['declaration'] and e['meaning_ja']==source[n]['meaning_ja'],n
    validate_hashes(ROOT,read(PRIOR)['source_sha256'])
    for p,s in build().items():assert (ROOT/p).read_text(encoding='utf-8')==s,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    validate_hashes(ROOT,{'artifacts/officer-example-v1/page-486.jpg':
        '3b28819f5cd9574b720ed7a81a0df7141992bc49c9542400cc6a95f9dcc09759'})
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_semantic_reviews=0,
        active_manuscript_unchanged=True,roundtrips=True,primary_page_hash_verified=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,s in build().items():write_exact(ROOT/p,s)


def build_report():
    results={}
    for name,fn in [('response',response_checks),('breadth',breadth_checks),('potential',potential_checks),
        ('domains',domain_checks),('unknown',unknown_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set().union(*(set(c.source_sha256) for c in parents()))|{
        DOC,PRIOR,'scripts/compose_general_resistance.py','scripts/check_general_resistance.py','tests/test_general_resistance.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','data/officer-example-evidence-v1.json'}
    return dict(status='general_civic_resistance_and_aligned_possible_induction',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
