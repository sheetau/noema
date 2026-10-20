"""Check doctrinal scope, constructed content and fixed-basis possible truth."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_doctrinal_statutes import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parents,build,closure
from scripts.compose_confessional_teaching import STANDARD,CRITERIA,CRITERION
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_scoped_counts import arithmetic
from scripts.fetch_pastoral_role_evidence import entry

DOC='docs/doctrinal-statutes-v1.md'
REPORT='reports/doctrinal-statutes-v1.json'
EVIDENCE='data/doctrinal-statutes-evidence-v1.json'
PRIORS=('reports/clerical-report-forecast-v1.json','reports/personal-conviction-v1.json')
DOMAIN=('person','church','creed','subject','standard','bundle','rulea','ruleb','part','tail','outsider','judgment','other')
SCENES=('reference','actual','p1','p2','other')
RULES='l[a][k zrulea[] k zruleb[]]'
FIELDS='k zchurch[] k zcreed[] k zsubject[] k zstandard[] k zbundle[] '+RULES+' k zref[]'
CODE='k r42i['+RULES+' k zref[]]'
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'''r zref[] d.r zactual[] d.r zpoint[] d.
r ztruth[a d] c.r zcondition[d] c.r zsave[i[h[a d] e]] c.
r zchoose[a d i[e] i[e] i[e] i[e] i[e] i[e]] i[e].
r zalternatives[a a d d] c.
d zpartbody[] e[b point[k ztruth[k zpart[] v point]]].
d ztailbody[] e[b point[k ztruth[k ztail[] v point]]].
d zbodya[] e[b point[w[t[k zpartbody[]][v point]][t[k ztailbody[]][v point]]]].
d zbodyb[] e[b point[k ztruth[k zruleb[] v point]]].
d zcreedbody[] e[b point[k ztruth[k zcreed[] v point]]].
d zotherbody[] e[b point[k ztruth[k zoutsider[] v point]]].
d zpremise[point d] c[k zcondition[v point]].
'''
PROVIDERS='''d h246e[formulation a reference d] i[e][k zchoose[v formulation v reference
r[k zbodya[]] r[k zbodyb[]] r[k zpartbody[]] r[k ztailbody[]] r[k zcreedbody[]] r[k zotherbody[]]]].
'''+ 'd zcriteria[] '+CRITERIA+'[l['+CRITERION+'][]].d h246j[standard a reference d] '+STANDARD+'[r[k zcriteria[]]].'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(query=None):
    doc=deepcopy(catalog().document);doc['statements']=[]
    prefix=parse('p:'+EXTRA+PROVIDERS);providers={d['name']:d for d in prefix['declarations'] if d['name'] in ('h246e','h246j')}
    doc['declarations']=[d for d in prefix['declarations'] if d['name'] not in providers]+[providers.get(d['name'],d) for d in doc['declarations']]
    if query is None:query='q[k r42j['+FIELDS+']].'
    return parse(format_graph(doc,'compact')+'q[k zsave['+CODE+']].'+query)


def model(doc,members=('rulea','ruleb'),variant='baseline',true_atoms=(),alternatives=('p1',),convinced=False):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update(arithmetic())
    v.update({'z'+n:(lambda n=n:n) for n in DOMAIN})
    v.update(zref=lambda:'reference',zactual=lambda:'actual',zpoint=lambda:'p1',zcondition=lambda at:True)
    observed=dict(codes=[],judgments=[],providers=[],selection=[])
    def save(code):observed['codes'].append(code);return code.rank==0
    v['zsave']=save
    def choose(form,ref,*codes):
        observed['providers'].append((form,ref))
        index={'rulea':0,'ruleb':1,'part':2,'tail':3,'creed':4}.get(form,5)
        if ref!='reference' or variant=='provider_'+form:index=5
        return codes[index]
    v['zchoose']=choose
    def match(actual,expected,category,fields):
        expected=list(expected)
        for i,field in enumerate(fields):
            if variant==category+'_'+field:expected[i]='other'
        return tuple(actual)==tuple(expected)
    v.update(h246d=lambda church,ref:(church,ref)==('church','reference'),
        h245z=lambda subject,ref:(subject,ref)==('subject','reference'),
        h246f=lambda creed,subject,ref:(creed,subject,ref)==('creed','subject','reference'),
        h246h=lambda church,code,ref:(church,symbol(code),ref)==('church','hzxi','reference'),
        h246i=lambda church,creed,standard,code,ref:match((church,creed,standard,symbol(code),ref),
            ('church','creed','standard','zcriteria','reference'),'adoption',('church','creed','standard','code','reference')),
        h6t=lambda bundle,rule,ref:rule in members and match((bundle,ref),('bundle','reference'),'membership',('bundle','reference')),
        h252e=lambda standard,rule,ref:rule in ('rulea','ruleb') and match((standard,ref),('standard','reference'),'prescription',('standard','reference')) and not (variant=='missing_prescription' and rule=='ruleb'),
        h252f=lambda rule,part,ref:(rule,part) in (('rulea','part'),('rulea','tail')) and ref=='reference' and variant!='no_parts',
        ztruth=lambda atom,at:(atom,at) in true_atoms)
    def avowal(church,form,code,ref):
        expected={'creed':'zcreedbody','rulea':'zbodya','ruleb':'zbodyb'}.get(form)
        return expected is not None and match((church,ref),('church','reference'),'avowal',('church','reference')) and symbol(code)==expected and code.rank==0 and not (variant=='missing_avowal' and form=='ruleb')
    v['h246g']=avowal
    def alt(person,bundle,ref,at):
        observed['selection'].append((person,bundle,ref,at))
        return at in alternatives and match((person,bundle,ref),('person','bundle','reference'),'possibility',('person','bundle','reference'))
    v['zalternatives']=alt
    v['fa']=lambda person,judgment,at:(person,judgment)==('person','judgment')
    def assent(judgment,target,code,ref,positive,at):
        observed['judgments'].append((judgment,target,ref,positive,at,code.syntax))
        return (judgment,target,ref,positive)==('judgment','bundle','reference',True) and code.syntax==observed['codes'][0].syntax
    v['h245q']=assent
    v['h252d']=lambda judgment,at:judgment=='judgment' and convinced
    v['hzko']=lambda person,premise,actual,at:(person,symbol(premise),actual)==('person','zpremise','actual') and at in ('p1','p2')
    return v,observed


def run(doc,pair):
    v,observed=pair;result=evaluate(doc,v,DOMAIN,SCENES,True)
    assert result[0] is True
    return result[1:]


@lru_cache(None)
def scope_checks():
    rows={};doc=fixture()
    variants=('baseline','adoption_church','adoption_creed','adoption_standard','adoption_code','adoption_reference',
        'membership_bundle','membership_reference','prescription_standard','prescription_reference','missing_prescription',
        'avowal_church','avowal_reference','missing_avowal','provider_rulea','provider_ruleb','provider_creed')
    for variant in variants:
        pair=model(doc,variant=variant);pair[0]['ztruth']=unknown
        result=run(doc,pair);assert result==[variant=='baseline'],(variant,result);rows[variant]=result
    for members in ((),('rulea',),('rulea','ruleb','outsider')):
        assert run(doc,model(doc,members=members))==[False]
    for rules,expected in (('l[a][]',False),('l[a][k zrulea[]]',False),
        ('l[a][k zrulea[] k zruleb[] k zoutsider[]]',False),('l[a][k zruleb[] k zrulea[]]',True),
        ('l[a][k zrulea[] k zruleb[] k zrulea[]]',False)):
        case=fixture('q[k r42j['+FIELDS.replace(RULES,rules)+']].')
        assert run(case,model(case))==[expected]
    return dict(contrasts=rows,exact_scope_and_plural_membership=True,extra_unrelated_rules_refused=True,
        order_retained_and_duplicate_members_refused=True,native_r35s_and_rcm=True,doctrine_truth_not_executed=True)


@lru_cache(None)
def content_checks():
    q='q[t[s[k r42h['+RULES+' k zref[]]]][k zpoint[]]].q[t[c[s['+CODE+']][k zbundle[] k zref[]]][k zpoint[]]].'
    doc=fixture(q);rows=[]
    for bits in product((False,True),repeat=3):
        atoms=tuple((atom,'p1') for atom,b in zip(('part','tail','ruleb'),bits) if b)
        result=run(doc,model(doc,true_atoms=atoms));assert result==[all(bits)]*2,(bits,result)
        rows.append(dict(bits=bits,results=result))
    doc=fixture('q[e['+CODE+'][k r42i[l[a][k zruleb[] k zrulea[]] k zref[]]]].')
    assert run(doc,model(doc))==[False]
    empty=fixture('q[t[s[k r42h[l[a][] k zref[]]]][k zpoint[]]].')
    assert run(empty,model(empty))==[True]
    # Construction itself preserves a rank-zero code without running its truth.
    doc=fixture('q[e['+CODE+']['+CODE+']].');pair=model(doc);pair[0]['ztruth']=unknown
    assert run(doc,pair)==[True]
    return dict(conjunction_truth_table=rows,native_constructed_code_and_lifted_body=True,
        rank_zero_preserved=True,code_construction_does_not_execute_truth=True,order_not_erased_by_truth_equivalence=True,
        empty_conjunction_not_evidence_for_nonempty_statutes=True)


@lru_cache(None)
def possibility_checks():
    doc=fixture('q[k r42l[k zperson[] k zbundle[] k zref[] p zalternatives]].');rows={}
    cases={'none':((),False),'internal_part':((('part','p1'),),True),'other_internal_part':((('tail','p1'),),True),
        'whole_member':((('ruleb','p1'),),True),'unrelated':((('outsider','p1'),),False),
        'wrong_candidate':((('part','other'),),False)}
    for name,(atoms,expected) in cases.items():
        pair=model(doc,true_atoms=atoms);result=run(doc,pair);assert result==[expected],(name,result)
        assert {ref for form,ref in pair[1]['providers']}=={'reference'}
        rows[name]=result
    assert run(doc,model(doc,true_atoms=(('part','p1'),),alternatives=()))==[False]
    for variant in ('possibility_person','possibility_bundle','possibility_reference','membership_bundle','membership_reference','no_parts'):
        assert run(doc,model(doc,variant=variant,true_atoms=(('part','p1'),)))==[False],variant
    native=fixture('q[k r42k[k zbundle[] k zpart[] k zref[]]].q[k r42k[k zbundle[] k zruleb[] k zref[]]].q[k r42k[k zbundle[] k zoutsider[] k zref[]]].')
    assert run(native,model(native))==[True,True,False]
    return dict(cases=rows,empty_alternatives_false=True,native_rgn_rgm=True,
        same_reference_for_all_membership_and_content=True,part_truth_does_not_require_whole_truth=True)


@lru_cache(None)
def endorsement_checks():
    q='q[k r42m[k zperson[] '+FIELDS+' r[p zpremise] k zactual[]]].'
    doc=fixture(q);rows=[]
    for convinced in (False,True):
        pair=model(doc,convinced=convinced);pair[0]['ztruth']=unknown
        result=run(doc,pair);assert result==[not convinced]
        observed=pair[1];assert observed['judgments']
        assert all(target=='bundle' and ref=='reference' and positive and code==observed['codes'][0].syntax
            for j,target,ref,positive,at,code in observed['judgments'])
        assert {ref for form,ref in observed['providers']}=={'reference'}
        rows.append(dict(convinced=convinced,result=result))
    for name in ('h252e','h246g','h6t','zchoose','fa','h245q','h252d','hzko'):
        pair=model(doc);pair[0][name]=unknown
        try:run(doc,pair)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    possible=fixture('q[k r42l[k zperson[] k zbundle[] k zref[] p zalternatives]].')
    for name in ('h252f','zalternatives','ztruth'):
        pair=model(possible);pair[0][name]=unknown
        try:run(possible,pair)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(cases=rows,native_personal_conviction_and_hypothetical_negation=True,
        exact_constructed_content_and_fixed_bundle_passed_to_judgment=True,
        unknown_inputs_refused=True,truth_not_derived_from_adoption_or_conviction=True)


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
    assert digest(raw)==evidence['sha256'] and entry(raw.decode(evidence['encoding']))==evidence['entry_text']
    for prior in PRIORS:validate_hashes(ROOT,read(prior)['source_sha256'])
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        no_source_sentence_added=True,lexical_evidence_pinned=True,
        diagnostic_replaces_only_code_providers_with_explicit_noema_values=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    result={name:fn() for name,fn in [('scope',scope_checks),('content',content_checks),('possibility',possibility_checks),
        ('endorsement',endorsement_checks),('structure',structure_checks)]}
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,EVIDENCE,read(EVIDENCE)['path'],
        'scripts/compose_doctrinal_statutes.py','scripts/check_doctrinal_statutes.py','tests/test_doctrinal_statutes.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py','scripts/fetch_pastoral_role_evidence.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_personal_conviction.py',
        'scripts/compose_unsettled_teaching.py','scripts/compose_confessional_teaching.py'}
    return dict(status='same_prescribed_doctrines_conjunction_and_possible_contained_truth',document=LIBRARY,**result,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
