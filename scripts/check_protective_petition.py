"""Check policy/model identity, both selected groups and quoted joint submission."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_protective_petition import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_joint_petition import model as petition_model,DOMAIN as PETITION_DOMAIN,SCENES as PETITION_SCENES

REPORT='reports/protective-petition-v1.json'
DOC='docs/protective-petition-v1.md'
READING='data/protective-petition-reading-v1.json'
PRIORS=('reports/observed-protection-v1.json','reports/community-protection-v1.json','reports/personal-insight-grounds-v1.json','reports/congregational-choices-v1.json','reports/joint-petition-v1.json')
DOMAIN=('p','t','s')
BITS=tuple(product((False,True),repeat=3))
SCENES=('reference','candidate','anchor','actual',*('w'+''.join(str(int(b)) for b in row) for row in BITS))
STATE={'kind':'function','parameters':['individual'],'result':'truth'}
NAMES=('policy','community','congregation','field','subject','configuration')
CONTEXT=('reference','candidate','anchor')
BOUND=('p','p','t','s','p','t',*CONTEXT)
EXTRA=''.join('r z'+n+'[] a.' for n in NAMES)+''.join('r z'+n+'[] d.' for n in SCENES[:4])+'r zbindings[] j[a].'
ARGS=' '.join('k z'+n+'[]' for n in (*NAMES,*CONTEXT))

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=EXTRA):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+extra+query)
def run(doc,v,domain=DOMAIN,scenes=SCENES):return evaluate(doc,v,domain,scenes,True)

def model(doc,variant='baseline'):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda value=value:value for n,value in zip(NAMES,BOUND[:6])})
    v.update({'z'+n:lambda n=n:n for n in SCENES})
    v['zbindings']=lambda:SequenceValue(('p','p'),'"individual"')
    natural=(False,False) if variant=='inactive' else (True,True) if variant=='threat_present' else (True,False)
    actual=(*natural,False if variant in ('harmful','impossible','false_activity') else True)
    observed=(*natural,True if variant=='false_activity' else actual[2])
    if variant=='wrong_threat':actual=(True,True,True)
    def bits(point):return tuple(x=='1' for x in point[1:]) if point.startswith('w') else actual
    v['h26ds']=lambda p,c,r,h,t:(p,c,r,h)==('p','p','reference','candidate') and bits(t)[0]
    v['h26dg']=lambda g,c,r:(g,c,r)==('t','p','reference')
    v['h246d']=lambda g,r:(g,r)==('t','reference')
    v['h245z']=lambda s,r:(s,r)==('p','reference')
    v['h246h']=lambda g,target,r:normalized((g,target,r))==('t',('hzxi',0),'reference')
    v['h246v']=lambda f,g,s,r:(f,g,s,r)==('s','t','p','reference')
    v['h246c']=lambda g,p,r:g=='t' and p in ('p','s') and r=='reference'
    v['aa']=lambda p:p in ('p','s')
    v['h246w']=lambda i,f,r:(i,f,r)==('t','s','reference')
    v['h246x']=lambda i,f,t:(i,f)==('t','s') and bits(t)[2]
    calls=[]
    def provide(name,result):
        def given(*a):
            assert a==BOUND,(name,a,BOUND);calls.append(name);return result
        return given
    variables=('p','t','s','p') if variant=='duplicate_variables' else DOMAIN
    def equation(item,state):
        if item=='p':return natural[0]
        if item=='t':return natural[1]
        if item!='s':return False
        if variant=='unprotected':return not state('t')
        if variant=='harmful':return not state('p')
        if variant=='impossible':return False
        if variant=='mixed':return state('s')
        if variant=='no_solution':return not state('s')
        return state('p') or not state('t')
    def worlds(state):return 'w000' if variant=='wrong_worlds' else 'w'+''.join(str(int(state(x))) for x in DOMAIN)
    def record(t):
        row=tuple(x=='1' for x in t[1:]) if t.startswith('w') else observed
        return FunctionValue(('individual',),'truth',lambda item:row[DOMAIN.index(item)] if item in DOMAIN else False)
    values={
        'h26dt':SequenceValue(variables,'"individual"'),
        'h26du':FunctionValue(('individual',STATE),'truth',equation),
        'h26dv':'p','h26dw':'p' if variant=='same_factors' else 't',
        'h26dx':FunctionValue((STATE,),'truth',lambda state:state('s')),
        'h26dy':FunctionValue((STATE,),'situation',worlds),
        'h26dz':Content(SCENES,tuple(bits(t)[1] for t in SCENES)),
        'h26d2':FunctionValue(('situation',),STATE,record),
    }
    v.update({n:provide(n,value) for n,value in values.items()})
    return v,calls

@lru_cache(None)
def native_effect_checks():
    q=''.join('q[t[k '+n+'['+ARGS+']][k zactual[]]].' for n in ('r5gg','r5gh'))
    doc=fixture(('r5gg','r5gh'),q);rows={}
    expected={
        'baseline':[True,True],'threat_present':[True,True],'inactive':[False,False],
        'unprotected':[False,True],'harmful':[False,False],'impossible':[False,True],
        'mixed':[False,False],'no_solution':[False,False],'false_activity':[False,False],
        'wrong_threat':[False,True],'wrong_worlds':[False,False],'same_factors':[False,True],
        'duplicate_variables':[False,False],
    }
    for variant,wanted in expected.items():
        v,calls=model(doc,variant);actual=run(doc,v);assert actual==wanted,(variant,actual,wanted);rows[variant]=actual
        assert set(calls)==set(PRIMITIVES)-{'h26ds'}
    rejected=[]
    for n in (*PRIMITIVES,'h246x'):
        v,_=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
        rejected.append(n)
    return dict(native_protection_and_nonhindrance=rows,all_providers_use_same_nine_arguments=True,
        native_definitions_without_boundaries=True,unknown_rejected=rejected)

@lru_cache(None)
def selected_policy_checks():
    q='q[t[k r5gi[k zpolicy[] k zcommunity[] k zreference[] k zcandidate[] k zanchor[]]][k zactual[]]].'
    doc=fixture(('r5gi',),q,('r5ge','r5f7','r5gg','r5gh'));rows={}
    for variant in ('both','only_reform','only_retention','empty','overlap','missing_protection','missing_nonhindrance','different_configuration','different_policy','different_point','late_selection','inactive'):
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        v.update({'z'+n:lambda:'alpha' for n in NAMES});v.update({'z'+n:lambda n=n:n for n in SCENES})
        v['h26ds']=lambda p,c,r,h,t:(p,c,r,h,t)==('alpha','alpha','reference','candidate','actual') and variant!='inactive'
        def reform(g,c,cong,f,s,old,new,r,h,a):
            return variant not in ('only_retention','empty') and(g,c,cong,f,s,old,new,r,h,a)==('alpha','alpha','alpha','alpha','alpha','alpha','beta','reference','candidate','actual' if variant=='late_selection' else 'anchor')
        def retained(c,cong,f,s,old,r,h,a):
            return variant not in ('only_reform','empty') and(c,cong,f,s,old,r,h,a)==('alpha','alpha' if variant=='overlap' else 'beta','alpha','alpha','alpha','reference','candidate','anchor')
        v['r5ge']=reform;v['r5f7']=retained
        def effect(kind,*a):
            wanted=('beta' if variant=='different_policy' else 'alpha','alpha','alpha' if kind=='protect' or variant=='overlap' else 'beta','alpha','alpha','alpha' if kind=='retain' or variant=='different_configuration' else 'beta','reference','candidate','anchor')
            valid=a==wanted and variant!=('missing_protection' if kind=='protect' else 'missing_nonhindrance')
            return Content(SCENES,tuple(valid and t==('anchor' if variant=='different_point' else 'actual') for t in SCENES))
        v['r5gg']=lambda *a:effect('protect',*a);v['r5gh']=lambda *a:effect('retain',*a)
        actual=run(doc,v,('alpha','beta'));wanted=variant in ('both','only_reform','only_retention','empty','overlap','late_selection')
        assert actual==[wanted],(variant,actual);rows[variant]=actual[0]
    return dict(all_selected_congregations_and_configurations=rows,
        selection_held_at_anchor_not_outcome=True,empty_groups_do_not_remove_policy=True,
        boundaries=['r5ge','r5f7','r5gg','r5gh'],components_checked_natively_in_their_reports=True)

@lru_cache(None)
def binding_checks():
    doc=fixture(('r5gj',),'q[t[k r5gj[k zbindings[] k zreference[] k zcandidate[] k zanchor[]]][k zactual[]]].',('r5gi',));rows=[]
    for expected in product(('alpha','beta'),repeat=2):
        count=0
        for offered in (*product(('alpha','beta'),repeat=2),(),('alpha',),('alpha',)*3):
            v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
            v.update({'z'+n:lambda n=n:n for n in SCENES});v['zbindings']=lambda offered=offered:SequenceValue(offered,'"individual"')
            v['r5gi']=lambda p,c,r,h,a:Content(SCENES,tuple((p,c)==expected and(r,h,a)==CONTEXT and t=='actual' for t in SCENES))
            actual=run(doc,v,('alpha','beta'));assert actual==[offered==expected];count+=actual[0]
        assert count==1;rows.append(dict(expected=expected,accepted=count))
    return dict(exact_policy_and_community=rows,wrong_lengths_rejected=True,boundary='r5gi selection and effect connections checked above')

@lru_cache(None)
def petition_checks():
    extra=''.join('r z'+n+'[] a.' for n in (*PETITION_DOMAIN,'policy'))+''.join('r z'+n+'[] d.' for n in PETITION_SCENES)
    q='q[k r5gk[k zgroup[] k zcommunity[] k zruler[] k zpolicy[] k zreference[] k zcandidate[] k zanchor[]]].'
    doc=fixture(('r5gk',),q,('r2uj',),extra);rows={}
    for variant in ('baseline','all_citizens','unavailable','empty_outcomes','only_failure','missing_voice','other_policy','other_proposal','other_bindings','other_reference'):
        v=petition_model(doc,variant);v['zpolicy']=lambda:'policy'
        old=v['df']
        def voice(p,a,target,b,r,c,start,t):
            expected=('other' if variant=='other_policy' else 'policy','group' if variant=='other_bindings' else 'community')
            return old(p,a,t) and normalized((target,b,r,c,start,t))==(('r5gi' if variant=='other_proposal' else 'r5gj',1),expected,'outside' if variant=='other_reference' else 'reference','candidate','anchor','success') and not(variant=='missing_voice' and p=='q')
        v['h26dd']=voice
        # Every concrete policy/model and selected-congregation input is unknown.
        # Passing the policy as the petition's quoted content must not evaluate it.
        for n in PRIMITIVES:v[n]=unknown
        actual=run(doc,v,(*PETITION_DOMAIN,'policy'),PETITION_SCENES)
        assert actual==[variant in ('baseline','all_citizens')],(variant,actual);rows[variant]=actual[0]
    return dict(shared_quoted_protective_petition=rows,policy_models_and_effects_not_executed=True,
        native_joint_proposal_and_ability=True,boundary='r2uj; preserved native monarch evidence in joint-petition-v1')

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(x for x in read(inv)['units'] if x['id']=='kant-1784:u0013')
    return dict(status='protective_petition_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1437,2309],text=u['text'][1437:2309]),
        adopted_readings=LIMITS,reuse=['rk3/rk4 causal effects with observations','r5ge grounded reform agreement','r5f7 positive retention intention','r5f2 same arrangement operation','r5fy shared possible petition'],
        remaining=['public insight sufficient for this petition','purpose discourse and temporal milestone','remaining emphasis modality and whole attribution'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    sources=parents();new=catalog();old={n:e for s in sources for n,e in s.entries.items()}
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record() and not new.document['statements'] and len(sources[0].document['statements'])==102
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=102)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('native_effects',native_effect_checks),('selected_policy',selected_policy_checks),('bindings',binding_checks),('petition',petition_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,reading_record()['source_inventory'],
        'scripts/compose_protective_petition.py','scripts/check_protective_petition.py','tests/test_protective_petition.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py','scripts/check_joint_petition.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/compose_observed_protection.py','scripts/compose_community_protection.py'}
    return dict(status='protective_petition_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
