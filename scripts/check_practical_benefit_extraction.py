"""Check all benefits, same source application and actual causal outcomes."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_practical_benefit_extraction import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parents,build
from scripts.check_responsible_exposition import EXTRA,PROVIDERS,DOMAIN as OLD_DOMAIN,SCENES,ARGS,model as old_model,read
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.fetch_pastoral_role_evidence import entry

DOC='docs/practical-benefit-extraction-v1.md'
REPORT='reports/practical-benefit-extraction-v1.json'
EVIDENCE='data/practical-benefit-extraction-evidence-v1.json'
PRIORS=('reports/clerical-report-forecast-v1.json','reports/responsible-exposition-v1.json','reports/personal-endorsement-case-v1.json')
BENEFITS=('benefita','benefitb')
DOMAIN=OLD_DOMAIN+BENEFITS
ALL='k r43a[k zperson[] k zbundle[] k zcongregation[] k zref[] k zpoint[]]'
FULL='k r43b['+ARGS+' k zpoint[]]'
SOURCE='k r42h[k h252g[k zbundle[] k zref[]] k zref[]]'
MORE='''r zbenefita[] a.r zbenefitb[] a.r zbenefittruth[a a d] c.
r zsource[i[e]] c.r zgoal[a i[h[a] e]] c.r zshown[i b[c]] c.
r zbenefitpick[a d i[e] i[e] i[e]] i[e].
d zgoala[] e[b point[k zbenefittruth[k zcongregation[] k zbenefita[] v point]]].
d zgoalb[] e[b point[k zbenefittruth[k zcongregation[] k zbenefitb[] v point]]].
d h246e[formulation a reference d] i[e][k zbenefitpick[v formulation v reference
k zbase[v formulation v reference] r[k zgoala[]] r[k zgoalb[]]]].
'''


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(query=None,records=True):
    doc=deepcopy(catalog().document);doc['statements']=[]
    prefix=parse('p:'+EXTRA+PROVIDERS.replace('d h246e[','d zbase[')+MORE)
    providers={d['name']:d for d in prefix['declarations'] if d['name'] in ('h246e','h246j')}
    doc['declarations']=[d for d in prefix['declarations'] if d['name'] not in providers]+[providers.get(d['name'],d) for d in doc['declarations']]
    saved='q[k zsource['+SOURCE+']].'+''.join('q[k zgoal[k z'+b+'[] k r426[k z'+b+'[] k zref[]]]].' for b in BENEFITS) if records else ''
    if query is None:query='q['+ALL+'].q['+FULL+'].'
    return parse(format_graph(doc,'compact')+saved+query)


def model(doc,variant='baseline',available=BENEFITS,practical=BENEFITS,true=BENEFITS,used=BENEFITS,caused=BENEFITS):
    v,observed=old_model(doc)
    observed.update(source=None,goals={},applications=[],causes=[],classifications=[])
    v.update({'z'+b:(lambda b=b:b) for b in BENEFITS})
    # Quantified implication evaluates its consequent even outside the scope.
    # Give those contents total interpretations, then vary them independently.
    v['zbelief']=lambda:Content(SCENES,tuple(variant=='true_doctrine' for _ in SCENES))
    v['zotherbelief']=v['zbelief']
    def save_source(code):observed['source']=code;return code.rank==0
    def save_goal(b,code):observed['goals'][b]=code;return code.rank==0
    v.update(zsource=save_source,zgoal=save_goal)
    def pick(form,ref,fallback,first,second):
        return {'benefita':first,'benefitb':second}.get(form,fallback) if ref=='reference' and variant!='wrong_content' else fallback
    v['zbenefitpick']=pick
    v['zbenefittruth']=lambda who,b,point:who=='congregation' and b in true and point==('reference' if variant=='wrong_result_point' else 'outcome')
    def match(actual,expected,category,fields):
        expected=list(expected)
        for i,field in enumerate(fields):
            if variant==category+'_'+field:expected[i]='other'
        return tuple(actual)==tuple(expected)
    def good(b,who,code,ref):
        observed['classifications'].append((b,who,symbol(code),ref))
        return b in practical and code.rank==0 and symbol(code)=={'benefita':'zgoala','benefitb':'zgoalb'}.get(b) and match(
            (who,ref),('congregation','reference'),'benefit',('beneficiary','reference'))
    v['h252p']=good
    v['h252q']=lambda person,bundle,who,b,ref:b in available and match((person,bundle,who,ref),
        ('person','bundle','congregation','reference'),'scope',('person','source','beneficiary','reference'))
    def act_for(b):return 'secondactivity' if variant=='split_acts' and b=='benefitb' else 'activity'
    def application(act,bundle,code,b,result,ref,point):
        observed['applications'].append((act,bundle,code.syntax,b,symbol(result),ref,point))
        return b in used and code.rank==0 and code.syntax==observed['source'].syntax and symbol(result)=={'benefita':'zgoala','benefitb':'zgoalb'}.get(b) and match(
            (act,bundle,ref,point),(act_for(b),'bundle','reference','outcome'),'application',('act','source','reference','point'))
    v['h252r']=application
    def cause(act,factor,b,result,point):
        observed['causes'].append((act,symbol(factor),b,result.syntax,point))
        return b in caused and factor.rank==result.rank==0 and symbol(factor)=='rqye' and result.syntax==observed['goals'][b].syntax and match(
            (act,point),(act_for(b),'outcome'),'cause',('act','point'))
    v['hzie']=cause
    v['dg']=lambda act,point:act in ('activity','secondactivity') and point=='outcome' and variant!='no_event'
    v['df']=lambda person,act,point:act in ('activity','secondactivity') and match((person,point),('person','outcome'),'actor',('person','point'))
    return v,observed


def run(doc,pair,records=True):
    result=evaluate(doc,pair[0],DOMAIN,SCENES,True)
    if records:assert result[:3]==[True]*3;return result[3:]
    return result


@lru_cache(None)
def all_checks():
    doc=fixture('q['+ALL+'].');rows=[]
    for bits in product((False,True),repeat=6):
        sets=[tuple(b for b,flag in zip(BENEFITS,bits[i:i+2]) if flag) for i in (0,2,4)]
        result=run(doc,model(doc,true=sets[0],used=sets[1],caused=sets[2]))
        assert result==[all(bits)],(bits,result)
        rows.append(dict(true=sets[0],used=sets[1],caused=sets[2],result=result))
    cases=[dict(available=(),expected=False),dict(practical=(),expected=False),
        dict(available=('benefita',),true=('benefita',),expected=True),
        dict(practical=('benefita',),true=('benefita',),expected=True),
        dict(true=('benefita',),expected=False),dict(variant='split_acts',expected=False),dict(variant='no_event',expected=False)]
    for case in cases:
        opts=dict(case);expected=opts.pop('expected');assert run(doc,model(doc,**opts))==[expected],case
    return dict(truth_application_cause_cases=rows,scope_cases=cases,nonempty_practical_benefits_required=True,
        all_eligible_benefits_not_one_or_achieved_subset=True,one_common_possibly_composite_activity=True,
        native_rqqu_checks_occurrence_result_and_cause=True)


@lru_cache(None)
def reference_checks():
    doc=fixture();rows={}
    assert run(doc,model(doc))==[True,True]
    for category,fields in [('benefit',('beneficiary','reference')),('scope',('person','source','beneficiary','reference')),
            ('application',('act','source','reference','point')),('cause',('act','point')),('actor',('person','point'))]:
        for field in fields:
            variant=category+'_'+field;result=run(doc,model(doc,variant=variant))
            assert result==[False,False],(variant,result);rows[variant]=result
    for variant in ('wrong_content','wrong_result_point'):
        assert run(doc,model(doc,variant=variant))==[False,False],variant
    # Preserve the inner benefit calculation while rejecting another congregation.
    pair=model(doc);pair[0]['h246k']=lambda *args:False
    assert run(doc,pair)==[True,False]
    pair=model(doc);pair[0]['h252e']=lambda *args:False
    assert run(doc,pair)==[True,False]
    pair=model(doc)
    assert run(doc,pair)==[True,True]
    assert run(doc,model(doc,variant='true_doctrine'))==[True,True]
    assert all(code==pair[1]['source'].syntax and ref=='reference' for _,_,code,_,_,ref,_ in pair[1]['applications'])
    for name in ('h252p','h252q','h252r','h252g','hzie','df','dg','zbenefitpick','zbenefittruth'):
        pair=model(doc);pair[0][name]=unknown
        try:run(doc,pair)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,same_congregation_and_native_r35t_r42j=True,source_and_outcome_codes_fixed=True,
        result_independent_of_doctrine_truth=True,unknown_inputs_refused=True,
        finite_evaluator_requires_total_out_of_scope_content_interpretations=True)


@lru_cache(None)
def quotation_checks():
    quoted='r b['+FULL+']';doc=fixture('q[k zshown['+quoted+']].',False)
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'};seen=[]
    def record(code):seen.append((code.rank,json.loads(code.syntax)));return code.rank==1
    values['zshown']=record
    assert run(doc,(values,{}),False)==[True] and seen[0][1]['symbol']=='r43b'
    native=fixture('q[s['+quoted+']].')
    assert run(native,model(native))==[True]
    assert run(native,model(native,true=('benefita',)))==[False]
    return dict(closed_rank_one_quotation=True,quotation_not_execution=True,exact_body_evaluated=True)


@lru_cache(None)
def structure_checks():
    old={n:e for c in parents() for n,e in c.entries.items()};new=catalog()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    evidence=read(EVIDENCE);raw=(ROOT/evidence['path']).read_bytes()
    assert digest(raw)==evidence['sha256'] and entry(raw.decode(evidence['encoding']))==evidence['text']
    for prior in PRIORS:validate_hashes(ROOT,read(prior)['source_sha256'])
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        no_source_sentence_added=True,primary_evidence_pinned=True,
        diagnostic_replaces_only_content_providers_with_explicit_noema_values=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    result={name:fn() for name,fn in [('all_benefits',all_checks),('references',reference_checks),('quotation',quotation_checks),('structure',structure_checks)]}
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,EVIDENCE,read(EVIDENCE)['path'],
        'scripts/compose_practical_benefit_extraction.py','scripts/check_practical_benefit_extraction.py','tests/test_practical_benefit_extraction.py',
        'scripts/compose_responsible_exposition.py','scripts/check_responsible_exposition.py',
        'scripts/check_representative_teaching.py','scripts/check_teaching_policy.py','scripts/check_confessional_teaching.py',
        'scripts/check_clerical_audiences.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/check_scoped_counts.py','scripts/fetch_pastoral_role_evidence.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='all_scoped_practical_benefits_from_same_doctrinal_content',document=LIBRARY,**result,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
