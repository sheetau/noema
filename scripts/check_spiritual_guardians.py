"""Check religious guardianship, complete people, and nonexecuted norm targets."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_spiritual_guardians import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_scoped_counts import arithmetic

REPORT='reports/spiritual-guardians-v1.json'
DOC='docs/spiritual-guardians-v1.md'
EVIDENCE='data/spiritual-guardians-evidence-v1.json'
PRIORS=('reports/unrestricted-scholarly-freedom-v1.json','reports/conditioned-persistence-v1.json')
DOMAIN=('g','h','p','q','r','s','matter','people','community','source','other')
SCENES=('reference','actual')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'r zref[] d.r zpoint[] d.'
POPULATION='k zpeople[] k zcommunity[] k zref[]'
GUARDIAN='k zg[] k zr[] k zpeople[] k zcommunity[] k zmatter[] k zref[]'
POLICY='k zsource[] k zpeople[] k zcommunity[] k zref[]'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+EXTRA+query)


def model(doc,variant='baseline'):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update(arithmetic())
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update(zref=lambda:'reference',zpoint=lambda:'actual')
    population={'empty':(),'duplicate':('p','p','q'),'missing_member':('p',),'extra_member':('p','q','other')}.get(variant,('p','q'))
    v.update(aa=lambda p:p in ('g','h','p','q') and not (variant=='nonhuman' and p=='g'),
        mp=lambda group:SequenceValue(population if group=='people' else (),'"individual"'),
        h237c=lambda p,c,ref:p in ('p','q') and (c,ref)==('other' if variant=='wrong_community' else 'community','reference'),
        hzwn=lambda p,r,ref:variant!='no_guardians' and (p,r) in ({('g','r'),('h','s'),('g','other')} if variant=='extra_guardian_role' else {('g','r'),('h','s')}) and ref=='reference',
        dc=lambda g,p,ref:(g,p) in ({('g','q'),('h','q')} if variant=='split_supervision' else {('g','p'),('h','q')}) and ref=='reference',
        sg=lambda p,m,ref:p in (('q',) if variant in ('split_religion','not_religious') else ('p','q')) and (m,ref)==('matter','reference'))
    def scope(g,p,r,m,ref):
        expected={('g','p','r','matter','reference'),('h','q','s','matter','reference')}
        if variant=='extra_guardian_role':expected.add(('g','p','other','matter','reference'))
        if variant=='wrong_scope_role':expected={('g','p','s','matter','reference'),('h','q','s','matter','reference')}
        if variant=='wrong_scope_matter':expected={('g','p','r','other','reference'),('h','q','s','matter','reference')}
        if variant=='self_only':expected={('g','g','r','matter','reference')}
        return (g,p,r,m,ref) in expected
    seen=[]
    def demand(source,person,role,code,bindings,ref,positive,point):
        row=(source,person,role,symbol(code),code.rank,tuple(bindings.items),ref,positive,point);seen.append(row)
        wanted=('source',person,role,'r45f',1,(person,),'reference',True,'actual')
        if variant.startswith('norm_'):
            i={'norm_source':0,'norm_person':1,'norm_role':2,'norm_target':3,'norm_rank':4,'norm_bindings':5,'norm_reference':6,'norm_polarity':7,'norm_point':8}[variant]
            changed=list(wanted);changed[i]=0 if i==4 else ('p',) if i==5 else False if i==7 else 'other';wanted=tuple(changed)
        return row==wanted and (person,role) in ({('g','r')} if variant=='missing_second_requirement' else {('g','r'),('h','s')})
    v.update(h253r=scope,h237z=demand)
    if variant=='self_only':
        v.update(mp=lambda group:SequenceValue(('g',),'"individual"'),h237c=lambda p,c,ref:(p,c,ref)==('g','community','reference'),
            dc=lambda g,p,ref:(g,p,ref)==('g','g','reference'),sg=lambda p,m,ref:(p,m,ref)==('g','matter','reference'))
    return v,seen


def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)


@lru_cache(None)
def guardian_checks():
    doc=fixture(('r45d','r45e'),'q[k r45d['+POPULATION+']].q[k r45e['+GUARDIAN+']].');rows={}
    for variant in ('baseline','empty','duplicate','missing_member','extra_member','wrong_community','nonhuman','no_guardians',
        'split_supervision','split_religion','not_religious','wrong_scope_role','wrong_scope_matter','self_only'):
        v,_=model(doc,variant);result=run(doc,v)
        population_ok=variant not in ('empty','duplicate','missing_member','extra_member','wrong_community')
        assert result==[population_ok,variant=='baseline'],(variant,result);rows[variant]=result
    for n in ('mp','h237c','hzwn','dc','sg','h253r'):
        v,_=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
    return dict(contrasts=rows,native_complete_people_and_same_ward_role_matter=True,
        self_supervision_insufficient=True,unknown_not_false=True)


@lru_cache(None)
def policy_checks():
    doc=fixture(('r45h',),'q[t[k r45h['+POLICY+']][k zpoint[]]].');rows={}
    variants=('baseline','missing_second_requirement','extra_guardian_role','no_guardians','missing_member',
        *('norm_'+n for n in ('source','person','role','target','rank','bindings','reference','polarity','point')))
    for variant in variants:
        v,seen=model(doc,variant);result=run(doc,v);assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
        if variant=='baseline':
            assert any(r[1:3]==('g','r') and r[5]==('g',) for r in seen)
            assert any(r[1:3]==('h','s') and r[5]==('h',) for r in seen)
    # All primitives needed only by the quoted bf remain unknown in this model.
    native=set(d['name'] for d in closure(catalog().document,['bf']) if d['kind']=='primitive')
    baseline,_=model(doc)
    assert native-{'aa'} and all(baseline[n] is unknown for n in native-{'aa'})
    quoted=fixture(('r45i',),'r zshown[i c[h[j[a] d] e]] c.q[k zshown[r c[p r45i]]].')
    v={d['name']:unknown for d in quoted['declarations'] if d['kind']=='primitive'}
    v['zshown']=lambda code:code.rank==2 and symbol(code)=='r45i'
    assert run(quoted,v)==[True]
    return dict(contrasts=rows,native_all_person_role_matter_quantifiers=True,nonempty_guardians_required=True,
        positive_requirement_on_guardian_not_ward=True,quoted_policy_and_immaturity_not_executed=True)


@lru_cache(None)
def target_checks():
    from scripts.check_conditioned_persistence import source_values,PEOPLE,SCENES as NATIVE_SCENES
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,['r45f']),statements=[])
    doc=parse(format_graph(doc,'compact')+'r zperson[] a.r zanchor[] d.r zfirst[] d.'+
        'q[t[k bf[k zperson[]]][k zfirst[]]].q[t[k r45f[l[a][k zperson[]] k zanchor[]]][k zfirst[]]].'+
        'q[t[k bf[k zperson[]]][k zanchor[]]].q[t[k r45f[l[a][k zperson[]] k zanchor[]]][k zanchor[]]].')
    v=source_values(doc);v['zfirst']=lambda:'first';native=evaluate(doc,v,PEOPLE,NATIVE_SCENES,True)
    assert native==[True,True,False,False],native
    rows={}
    for sequence in ('l[a][]','l[a][k zsource[] k zpeople[]]','l[a][k zsource[] k zpeople[] k zcommunity[] k zsource[]]',
        'l[a][k zsource[] k zpeople[] k zcommunity[]]','l[a][k zpeople[] k zsource[] k zcommunity[]]'):
        doc=fixture(('r45i',),'q[t[k r45i['+sequence+' k zref[]]][k zpoint[]]].',('r45h',));v,_=model(doc)
        v['r45h']=lambda source,people,community,ref:Content(SCENES,tuple((source,people,community,ref)==('source','people','community','reference') and p=='actual' for p in SCENES))
        result=run(doc,v);wanted=sequence=='l[a][k zsource[] k zpeople[] k zcommunity[]]';assert result==[wanted],(sequence,result);rows[sequence]=result[0]
    return dict(native_existing_bf_and_single_person_adapter=native,exact_policy_binding_contrasts=rows,
        bf_not_replaced_in_native_check=True,policy_adapter_boundary='r45h')


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    e=read(EVIDENCE)
    for p in [*e['pages'],*e['lexical_sources']]:assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    s=e['source'];u=next(u for u in read(e['source_inventory'])['units'] if u['id']==s['unit'])
    assert u['text_sha256']==s['unit_sha256'] and u['text'][slice(*s['range'])]==s['text']
    assert not new.document['statements']
    return dict(unchanged_imports=True,roundtrips=True,new_primitives=len(PRIMITIVES),new_definitions=len(MEANINGS),
        no_new_source_sentence=True,primary_page_488_and_lexical_evidence_pinned=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)


def build_report():
    results={}
    for name,fn in [('guardians',guardian_checks),('policy',policy_checks),('targets',target_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    evidence=read(EVIDENCE)
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,EVIDENCE,evidence['source_inventory'],
        *[p['path'] for p in [*evidence['pages'],*evidence['lexical_sources']]],
        'scripts/compose_spiritual_guardians.py','scripts/check_spiritual_guardians.py','tests/test_spiritual_guardians.py',
        'scripts/check_conditioned_persistence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='same_peoples_religious_guardians_and_quoted_immaturity_requirement',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
