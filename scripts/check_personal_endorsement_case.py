"""Check a constructed personal supposition and native same-doctrine composition."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_personal_endorsement_case import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parents,build,CONTENT,PREMISE
from scripts.check_responsible_exposition import EXTRA,PROVIDERS,DOMAIN,SCENES,ARGS,model as old_model,read
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/personal-endorsement-case-v1.md'
REPORT='reports/personal-endorsement-case-v1.json'
PRIORS=('reports/personal-conviction-v1.json','reports/doctrinal-statutes-v1.json','reports/responsible-exposition-v1.json','reports/latent-truth-compatibility-v1.json')
CODE='k r42i[k h252g[k zbundle[] k zref[]] k zref[]]'
NAMES='r[k zperson[]] r[k zbundle[]] r[k zref[]]'
SUPPOSITION='k r423[r[k zperson[]] r[k zbundle[]] '+CODE+' r[k zref[]]]'
STATUTE_ARGS='k zperson[] k zchurch[] k zcreed[] k zsubject[] k zstandard[] k zbundle[] k zref[]'
NEG='k r424['+STATUTE_ARGS+' '+NAMES+' k zactual[]]'
COMBINED='k r425['+ARGS+' '+NAMES+' k zactual[]]'
MORE='r zcontent['+CONTENT+'] c.r zpremise['+PREMISE+'] c.r zshown[i c[c]] c.'


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(query=None,records=True):
    doc=deepcopy(catalog().document);doc['statements']=[]
    prefix=parse('p:'+EXTRA+PROVIDERS+MORE)
    providers={d['name']:d for d in prefix['declarations'] if d['name'] in ('h246e','h246j')}
    doc['declarations']=[d for d in prefix['declarations'] if d['name'] not in providers]+[providers.get(d['name'],d) for d in doc['declarations']]
    saved='q[k zrecord[k r42n[k zbundle[] k zref[]]]].q[k zcontent['+CODE+']].q[k zpremise['+SUPPOSITION+']].' if records else ''
    if query is None:query='q['+NEG+'].q[k r42s['+ARGS+' k zactual[]]].q['+COMBINED+'].'
    return parse(format_graph(doc,'compact')+saved+query)


def model(doc,variant='baseline',selected=('reference','outcome'),opportunity=('reference','outcome'),
          personal=('reference','outcome'),full=(),bits=(True,True,True,True)):
    v,observed=old_model(doc,variant=variant,bits=bits)
    observed.update(content=None,premise=None,questions=[],judgments=[],hypotheticals=[])
    def save(kind,code):observed[kind]=code;return code.rank==0
    v['zcontent']=lambda code:save('content',code)
    v['zpremise']=lambda code:save('premise',code)
    def match(actual,expected,category,fields):
        expected=list(expected)
        for i,n in enumerate(fields):
            if variant==category+'_'+n:expected[i]='reference' if expected[i]=='other' else 'other'
        return tuple(actual)==tuple(expected)
    v['hzzzv']=lambda person,target,at:at in opportunity and match((person,target),('person','bundle'),'opportunity',('person','target'))
    def issue(person,target,code,ref,at):
        observed['questions'].append((person,target,code.syntax,ref,at))
        return at in personal and code.syntax==observed['content'].syntax and match((person,target,ref),
            ('person','bundle','reference'),'issue',('person','target','reference'))
    v['h252o']=issue
    def chosen(person,premise,actual,at):
        observed['hypotheticals'].append((person,premise.syntax,actual,at))
        return at in selected and premise.rank==0 and premise.syntax==observed['premise'].syntax and match((person,actual),
            ('person','other'),'selection',('person','actual'))
    v['hzko']=chosen
    v['fa']=lambda person,judgment,at:(person,judgment)==('person','event')
    def judgment(j,target,code,ref,positive,at):
        observed['judgments'].append((j,target,code.syntax,ref,positive,at))
        return code.rank==0 and code.syntax==observed['content'].syntax and match((j,target,ref,positive),
            ('event','bundle','reference',True),'judgment',('act','target','reference','polarity'))
    v['h245q']=judgment
    v['h252d']=lambda j,at:j=='event' and at in full
    return v,observed


def run(doc,pair,records=True):
    result=evaluate(doc,pair[0],DOMAIN,SCENES,True)
    if records:assert result[:3]==[True]*3;return result[3:]
    return result


@lru_cache(None)
def supposition_checks():
    doc=fixture('q['+NEG+'].');rows=[]
    for bits in product((False,True),repeat=6):
        selected=tuple(p for p,b in zip(('reference','outcome'),bits[:2]) if b)
        opportunity=tuple(p for p,b in zip(('reference','outcome'),bits[2:4]) if b)
        full=tuple(p for p,b in zip(('reference','outcome'),bits[4:]) if b)
        expected=bool(selected) and set(selected)<=set(opportunity) and not set(selected)&set(full)
        result=run(doc,model(doc,selected=selected,opportunity=opportunity,full=full))
        assert result==[expected],(bits,result)
        rows.append(dict(selected=selected,opportunity=opportunity,full_conviction=full,result=result))
    for personal in ((),('reference',),('outcome',)):
        assert run(doc,model(doc,personal=personal))==[False]
    # A premise can also hold at the actual evaluation; no factual falsity required.
    assert run(doc,model(doc,opportunity=SCENES,personal=SCENES,full=('other',)))==[True]
    premise=fixture('q[c[s['+SUPPOSITION+']][k zpoint[]]].')
    for opportunity,personal,expected in (((),(),False),(('outcome',),(),False),((),('outcome',),False),(('outcome',),('outcome',),True)):
        pair=model(premise,opportunity=opportunity,personal=personal)
        pair[0]['fa']=pair[0]['h245q']=pair[0]['h252d']=unknown
        assert run(premise,pair)==[expected]
    return dict(cases=rows,native_r42m_r42g_r42f=True,premise_neither_assent_nor_actual_request=True,
        opportunity_and_personal_issue_both_required=True,actual_premise_and_conviction_independent=True)


@lru_cache(None)
def composition_checks():
    doc=fixture();rows=[]
    for convinced,possible in product((False,True),repeat=2):
        pair=model(doc,full=('outcome',) if convinced else (),bits=(possible,True,True,True))
        result=run(doc,pair);assert result==[not convinced,possible,not convinced and possible]
        obs=pair[1];assert obs['questions'] and obs['judgments'] and obs['hypotheticals']
        assert all(code==obs['content'].syntax and ref=='reference' for _,_,code,ref,_ in obs['questions'])
        assert all(code==obs['content'].syntax and ref=='reference' and positive for _,_,code,ref,positive,_ in obs['judgments'])
        assert all(code==obs['premise'].syntax for _,code,_,_ in obs['hypotheticals'])
        assert pair[0]['zbelief'] is unknown and pair[0]['zotherbelief'] is unknown
        rows.append(dict(convinced=convinced,possible=possible,result=result))
    # Personal assessment is at reference; the practical undertaking is at outcome.
    assert run(doc,model(doc,selected=('reference',),opportunity=('reference',),personal=('reference',)))==[True]*3
    for variant in ('not_prescribed','undertaking_person','admissible_act'):
        result=run(doc,model(doc,variant=variant));assert result[-1] is False,(variant,result)
    return dict(cases=rows,native_r42j_and_r42s_composed=True,same_fixed_doctrinal_content=True,
        independent_hypothetical_and_practical_scopes=True,doctrine_truth_and_goal_not_executed=True)


@lru_cache(None)
def reference_checks():
    doc=fixture('q['+NEG+'].');rows={}
    for category,fields in [('opportunity',('person','target')),('issue',('person','target','reference')),('selection',('person','actual'))]:
        for field in fields:
            variant=category+'_'+field;result=run(doc,model(doc,variant=variant));assert result==[False],(variant,result);rows[variant]=result
    for original,replacement in [('r[k zperson[]]','r[k zchurch[]]'),('r[k zbundle[]]','r[k zchurch[]]'),('r[k zref[]]','r[k zpoint[]]')]:
        bad=fixture('q['+NEG.replace(original,replacement)+'].')
        assert run(bad,model(bad))==[False]
    for name in ('hzzzv','h252o','hzko','h252g','fa','h245q','h252d'):
        pair=model(doc);pair[0][name]=unknown
        try:run(doc,pair)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,closed_names_must_denote_same_values=True,unknown_inputs_refused=True)


@lru_cache(None)
def quotation_checks():
    quoted='r c['+COMBINED+']';doc=fixture('q[k zshown['+quoted+']].',False)
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'};seen=[]
    def record(code):seen.append((code.rank,json.loads(code.syntax)));return code.rank==2
    values['zshown']=record
    assert run(doc,(values,{}),False)==[True] and seen[0][1]['symbol']=='r425'
    native=fixture('q[s['+quoted+']].')
    assert run(native,model(native))==[True]
    assert run(native,model(native,full=('outcome',)))==[False]
    return dict(closed_rank_two_composition=True,quotation_not_execution=True,exact_body_evaluated=True)


@lru_cache(None)
def structure_checks():
    old={n:e for c in parents() for n,e in c.entries.items()};new=catalog()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for prior in PRIORS:validate_hashes(ROOT,read(prior)['source_sha256'])
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        no_source_sentence_added=True,implicit_supposition_explicit_not_claimed_unique=True,
        diagnostic_replaces_only_content_providers_with_explicit_noema_values=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    result={name:fn() for name,fn in [('supposition',supposition_checks),('composition',composition_checks),
        ('references',reference_checks),('quotation',quotation_checks),('structure',structure_checks)]}
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,
        'scripts/compose_personal_endorsement_case.py','scripts/check_personal_endorsement_case.py','tests/test_personal_endorsement_case.py',
        'scripts/compose_personal_conviction.py','scripts/compose_responsible_exposition.py',
        'scripts/check_responsible_exposition.py','scripts/check_representative_teaching.py','scripts/check_teaching_policy.py',
        'scripts/check_confessional_teaching.py','scripts/check_clerical_audiences.py','scripts/check_ranked_appointment.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='same_doctrines_personal_endorsement_supposition_and_responsible_exposition',document=LIBRARY,**result,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
