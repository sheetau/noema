"""Check latent truth, modal negation and fixed-content religious compatibility."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_latent_truth_compatibility import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parents,build
from scripts.check_doctrinal_statutes import EXTRA,PROVIDERS,DOMAIN as OLD_DOMAIN,SCENES,model as old_model,read
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.fetch_pastoral_role_evidence import entry
from scripts.check_teaching_discretion import extract

DOC='docs/latent-truth-compatibility-v1.md'
REPORT='reports/latent-truth-compatibility-v1.json'
EVIDENCE='data/latent-truth-compatibility-evidence-v1.json'
PRIORS=('reports/clerical-report-forecast-v1.json','reports/doctrinal-statutes-v1.json','reports/responsible-exposition-v1.json')
DOMAIN=OLD_DOMAIN+('religion',)
ARGS='k zperson[] k zbundle[] k zref[] k zactual[]'
ALL_ARGS='k zperson[] k zbundle[] k zsubject[] k zreligion[] k zref[] k zactual[]'
MORE='''r zreligion[] a.r zstrict[d] c.r zshown[i b[c]] c.
r zreligionpick[a d i[e] i[e]] i[e].
d znorm[] e[b point[y[k zstrict[v point]][u[t[k zpartbody[]][v point]]]]].
d h246e[formulation a reference d] i[e][k zreligionpick[v formulation v reference
k zbase[v formulation v reference] r[k znorm[]]]].
'''


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(query=None):
    doc=deepcopy(catalog().document);doc['statements']=[]
    prefix=parse('p:'+EXTRA+PROVIDERS.replace('d h246e[','d zbase[')+MORE)
    providers={d['name']:d for d in prefix['declarations'] if d['name'] in ('h246e','h246j')}
    doc['declarations']=[d for d in prefix['declarations'] if d['name'] not in providers]+[providers.get(d['name'],d) for d in doc['declarations']]
    if query is None:query=''.join('q[k '+n+'['+ARGS+']].' for n in ('r42u','r42v','r42w'))
    return parse(format_graph(doc,'compact')+query)


def model(doc,selected=('p1','p2'),true_atoms=(('part','p1'),),hidden=('p1',),strict=(),variant='baseline'):
    v,observed=old_model(doc,variant=variant,true_atoms=true_atoms)
    observed.update(hidden=[],clashes=[],cases=[])
    v.update(zreligion=lambda:'religion',zstrict=lambda at:at in strict)
    def match(actual,expected,category,fields):
        expected=list(expected)
        for i,field in enumerate(fields):
            if variant==category+'_'+field:expected[i]='other'
        return tuple(actual)==tuple(expected)
    def pick(form,ref,fallback,norm):
        return norm if (form,ref)==('religion','reference') and variant!='provider_religion' else fallback
    v['zreligionpick']=pick
    def latent(person,bundle,part,code,ref,at):
        observed['hidden'].append((person,bundle,part,symbol(code),ref,at))
        return at in hidden and code.rank==0 and match((person,bundle,part,symbol(code),ref),
            ('person','bundle','part','zpartbody','reference'),'hidden',('person','bundle','part','code','reference'))
    v['h252k']=latent
    def case(person,bundle,ref,actual,at):
        observed['cases'].append((person,bundle,ref,actual,at))
        return at in selected and match((person,bundle,ref,actual),('person','bundle','reference','actual'),
            'selection',('person','bundle','reference','actual'))
    v['h252l']=case
    v['h252m']=lambda religion,subject,ref:match((religion,subject,ref),('religion','subject','reference'),
        'religion',('standard','subject','reference'))
    def clash(content,norm,ref,at):
        observed['clashes'].append((symbol(content),symbol(norm),ref,at))
        return at in strict and content.rank==norm.rank==0 and symbol(content) in ('zpartbody','zbodya') and match(
            (symbol(norm),ref),('znorm','reference'),'clash',('code','reference'))
    v['h252n']=clash
    return v,observed


def run(doc,pair):return evaluate(doc,pair[0],DOMAIN,SCENES,True)


@lru_cache(None)
def possibility_checks():
    doc=fixture();rows=[]
    for bits in product((False,True),repeat=6):
        selected=tuple(p for p,b in zip(('p1','p2'),bits[:2]) if b)
        true=tuple(p for p,b in zip(('p1','p2'),bits[2:4]) if b)
        hidden=tuple(p for p,b in zip(('p1','p2'),bits[4:]) if b)
        possible=bool(set(selected)&set(true)&set(hidden))
        pair=model(doc,selected=selected,true_atoms=tuple(('part',p) for p in true),hidden=hidden)
        result=run(doc,pair);assert result==[possible,bool(selected) and not possible,possible],(bits,result)
        rows.append(dict(selected=selected,true_at=true,hidden_at=hidden,result=result))
    empty=fixture('q[u[k r42v['+ARGS+']]].q[k r42w['+ARGS+']].')
    assert run(empty,model(empty,selected=()))==[True,False]
    return dict(selection_truth_hidden_cases=rows,nonempty_range_required=True,
        double_negation_not_unknown_or_empty_range_optimism=True,truth_possible_not_actual=True)


@lru_cache(None)
def containment_checks():
    doc=fixture('q[k r42t[k zperson[] k zbundle[] k zref[] k zpoint[]]].q[k r42w['+ARGS+']].');rows={}
    cases={'latent_part':((('part','p1'),),('p1',),[True,True]),
        'true_but_manifest':((('part','p1'),),(),[False,False]),
        'hidden_but_false':((),('p1',),[False,False]),
        'unrelated_truth':((('outsider','p1'),),('p1',),[False,False]),
        'actual_truth_only':((('part','actual'),),('actual',),[False,False]),
        'truth_and_hidden_at_different_cases':((('part','p2'),),('p1',),[False,False]),
        'candidate_two':((('part','p2'),),('p2',),[False,True])}
    for name,(atoms,hidden,expected) in cases.items():
        pair=model(doc,true_atoms=atoms,hidden=hidden);result=run(doc,pair)
        assert result==expected,(name,result);rows[name]=result
        assert {ref for _,ref in pair[1]['providers']}=={'reference'}
    for variant in ('no_parts','membership_bundle','membership_reference','provider_part'):
        assert run(doc,model(doc,variant=variant))==[False,False],variant
    # The whole first member is false (part AND tail); a true contained part suffices.
    whole=fixture('q[t[s[k h246e[k zrulea[] k zref[]]]][k zpoint[]]].q[k r42w['+ARGS+']].')
    assert run(whole,model(whole))==[False,True]
    return dict(cases=rows,positive_containment_required=True,same_part_code_and_reference=True,
        true_part_does_not_require_whole_truth=True,manifest_truth_and_nonassent_not_latent_truth=True)


@lru_cache(None)
def compatibility_checks():
    doc=fixture('q[k r42x[k zbundle[] k zreligion[] k zref[] k zpoint[]]].'
        +'q[k r42y['+ALL_ARGS+']].q[k r42z['+ALL_ARGS+']].');rows=[]
    for selected,strict in product(((),('p1',),('p1','p2')), ((),('p1',),('p2',),('p1','p2'))):
        pair=model(doc,selected=selected,strict=strict);result=run(doc,pair)
        compatible=bool(selected) and not set(selected)&set(strict)
        expected=['p1' not in strict,compatible,compatible and 'p1' in selected]
        assert result==expected,(selected,strict,result)
        assert pair[1]['clashes'] and all(n=='znorm' and ref=='reference' for _,n,ref,_ in pair[1]['clashes'])
        rows.append(dict(selected=selected,opposition_at=strict,result=result))
    for variant in ('religion_standard','religion_subject','religion_reference'):
        assert run(doc,model(doc,variant=variant))==[True,False,False],variant
    v,obs=model(doc);v['h245z']=lambda *args:False
    assert run(doc,(v,obs))==[True,False,False]
    # No latent truth need exist when every contained formulation avoids opposition.
    assert run(doc,model(doc,true_atoms=()))==[True,True,False]
    assert run(doc,model(doc,strict=('p2',)))==[True,False,False]
    return dict(cases=rows,native_rgv_and_r42k=True,all_selected_cases_required=True,
        religion_classification_and_fixed_content_required=True,
        possibility_and_compatibility_do_not_imply_each_other=True,
        point_dependent_opposition_against_explicit_conditional_norm=True,
        no_completed_search_or_personal_belief_required=True)


@lru_cache(None)
def reference_checks():
    doc=fixture();rows={}
    for category,fields in [('hidden',('person','bundle','part','code','reference')),
            ('selection',('person','bundle','reference','actual'))]:
        for field in fields:
            variant=category+'_'+field;result=run(doc,model(doc,variant=variant))
            assert result==([False,True,False] if category=='hidden' else [False]*3),(variant,result)
            rows[variant]=result
    combined=fixture('q[k r42z['+ALL_ARGS+']].')
    for name in ('h252k','h252l','h252m','h252n','h245z','h6t','h252f','zchoose','zreligionpick','ztruth'):
        pair=model(combined);pair[0][name]=unknown
        try:run(combined,pair)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,unknown_inputs_refused=True,same_fixed_reference_and_actual_anchor=True)


@lru_cache(None)
def quotation_checks():
    body='k r42z['+ALL_ARGS+']';quoted='r b['+body+']'
    shown=fixture('q[k zshown['+quoted+']].')
    v={d['name']:unknown for d in shown['declarations'] if d['kind']=='primitive'};seen=[]
    def record(code):seen.append((code.rank,json.loads(code.syntax)));return code.rank==1
    v['zshown']=record
    assert run(shown,(v,{}))==[True] and seen[0][1]['symbol']=='r42z'
    actual=fixture('q[s['+quoted+']].')
    assert run(actual,model(actual))==[True]
    assert run(actual,model(actual,strict=('p2',)))==[False]
    return dict(rank_one_closed_quotation=True,quotation_not_execution=True,exact_quoted_body_evaluated=True)


@lru_cache(None)
def structure_checks():
    old={n:e for c in parents() for n,e in c.entries.items()};new=catalog()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for page in read(EVIDENCE)['pages']:
        raw=(ROOT/page['path']).read_bytes();extractor=entry if page['extractor']=='adelung' else extract
        assert digest(raw)==page['sha256'] and extractor(raw.decode(page['encoding']))==page['text']
    for prior in PRIORS:validate_hashes(ROOT,read(prior)['source_sha256'])
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        no_source_sentence_added=True,primary_evidence_pinned=True,
        diagnostic_replaces_only_content_providers_with_explicit_noema_values=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    result={name:fn() for name,fn in [('possibility',possibility_checks),('containment',containment_checks),
        ('compatibility',compatibility_checks),('references',reference_checks),('quotation',quotation_checks),('structure',structure_checks)]}
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,EVIDENCE,
        'scripts/compose_latent_truth_compatibility.py','scripts/check_latent_truth_compatibility.py','tests/test_latent_truth_compatibility.py',
        'scripts/check_doctrinal_statutes.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/check_scoped_counts.py','scripts/fetch_pastoral_role_evidence.py','scripts/check_teaching_discretion.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_confessional_teaching.py'}
    paths.update(p['path'] for p in read(EVIDENCE)['pages'])
    return dict(status='possible_latent_truth_and_scoped_inward_religious_compatibility',document=LIBRARY,**result,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
