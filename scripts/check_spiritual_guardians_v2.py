"""Use the published sg contract as an independent argument-order oracle."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_spiritual_guardians_v2 import ROOT,LIBRARY,BASIS,MEANINGS,REPLACEMENTS,parent,build
from scripts.compose_grounded_step import closure
from scripts.check_spiritual_guardians import model as old_model,DOMAIN,SCENES,EXTRA,GUARDIAN,POLICY,run
from scripts.check_motive_causes import unknown,symbol
from scripts.check_pastoral_roles import evaluate

REPORT='reports/spiritual-guardians-v2.json'
DOC='docs/spiritual-guardians-v2.md'
PRIORS=('reports/spiritual-guardians-v1.json','reports/irrational-perpetuation-v1.json','reports/unrestricted-scholarly-freedom-v1.json')


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
    v,seen=old_model(doc,variant)
    # The old test used person/matter order. Interpret the published relation
    # directly as sg(matter, person, scene); do not duplicate the faulty call.
    religious_people=('q',) if variant in ('split_religion','not_religious') else ('p','q')
    if variant=='self_only':religious_people=('g',)
    v['sg']=lambda matter,person,scene:person in religious_people and (matter,scene)==('matter','reference')
    return v,seen


@lru_cache(None)
def order_checks():
    assert catalog().entries['sg']['arguments']==['matter','person','scene']
    doc=fixture(('r45e','r45q'),'q[k r45e['+GUARDIAN+']].q[k r45q['+GUARDIAN+']].')
    v,_=model(doc);correct=run(doc,v);assert correct==[False,True],correct
    v['sg']=lambda matter,person,scene:(matter,person,scene)==('p','matter','reference')
    inverted=run(doc,v);assert inverted==[True,False],inverted
    # Both are individual-typed; an asymmetric interpretation catches what
    # parser/type/roundtrip checks and the earlier mirrored fixture could not.
    return dict(published_arguments=['matter','person','scene'],old_then_corrected=correct,
        inverted_relation_old_then_corrected=inverted,distinct_person_and_matter=True)


@lru_cache(None)
def guardian_policy_checks():
    guardian=fixture(('r45q',),'q[k r45q['+GUARDIAN+']].');guards={}
    for variant in ('baseline','empty','duplicate','missing_member','extra_member','wrong_community','nonhuman','no_guardians',
        'split_supervision','split_religion','not_religious','wrong_scope_role','wrong_scope_matter','self_only'):
        v,_=model(guardian,variant);result=run(guardian,v);assert result==[variant=='baseline'],(variant,result);guards[variant]=result[0]
    policy=fixture(('r45r',),'q[t[k r45r['+POLICY+']][k zpoint[]]].');policies={}
    for variant in ('baseline','missing_second_requirement','extra_guardian_role','no_guardians','missing_member',
        *('norm_'+n for n in ('source','person','role','target','rank','bindings','reference','polarity','point'))):
        v,seen=model(policy,variant);result=run(policy,v);assert result==[variant=='baseline'],(variant,result);policies[variant]=result[0]
        if variant=='baseline':
            assert any(row[1:3]==('g','r') for row in seen) and any(row[1:3]==('h','s') for row in seen)
    for name in ('sg','h253r','h237z'):
        v,_=model(policy);v[name]=unknown
        try:run(policy,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(guardian_contrasts=guards,policy_contrasts=policies,
        native_all_guardians_and_nonempty_range=True,unknown_not_false=True,immaturity_not_executed=True)


@lru_cache(None)
def target_checks():
    rows={}
    for members in ((),('source','people'),('source','people','community'),('people','source','community'),('source','people','community','source')):
        seq='l[a]['+' '.join('k z'+n+'[]' for n in members)+']'
        doc=fixture(('r45s',),'q[t[k r45s['+seq+' k zref[]]][k zpoint[]]].',('r45r',))
        v,_=model(doc)
        v['r45r']=lambda source,people,community,ref:Content(SCENES,tuple((source,people,community,ref,point)==('source','people','community','reference','actual') for point in SCENES))
        result=evaluate(doc,v,('source','people','community'),SCENES,True)
        assert result==[members==('source','people','community')],(members,result);rows[str(members)]=result[0]
    # Evaluate the corrected appraisal and quoted consequence without executing
    # either the policy or persistence. Existing r45o result is unchanged.
    extra='r zstandard[] a.r zrequirement[] a.'
    doc=fixture(('r45u',),extra+'q[t[k r45u[k zsource[] k zpeople[] k zcommunity[] k zstandard[] k zref[]]][k zpoint[]]].')
    domain=(*DOMAIN,'standard','requirement')
    def values(bits=(True,True),old_target=False):
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        v.update({'z'+n:lambda n=n:n for n in domain});v.update(zref=lambda:'reference',zpoint=lambda:'actual')
        policy_symbol='r45i' if old_target else 'r45s'
        def applies(s,req,code,bindings,ref):
            return (s,req,symbol(code),code.rank,tuple(bindings.items),ref)==('standard','requirement',policy_symbol,2,('source','people','community'),'reference')
        v['h253s']=applies
        v['h253t']=lambda s,req,code,bindings,ref,positive,point:bits[0] and applies(s,req,code,bindings,ref) and not positive and point=='actual'
        v['h253x']=lambda cause,cb,result,rb,ref,point:bits[1] and (symbol(cause),cause.rank,tuple(cb.items),symbol(result),result.rank,tuple(rb.items),ref,point)==(policy_symbol,2,('source','people','community'),'r45o',2,('community','standard'),'reference','actual')
        return v
    matrix=[]
    for bits in product((False,True),repeat=2):
        result=evaluate(doc,values(bits),domain,SCENES,True);assert result==[all(bits)],(bits,result);matrix.append([*bits,result[0]])
    assert evaluate(doc,values(old_target=True),domain,SCENES,True)==[False]
    return dict(exact_policy_bindings=rows,adapter_boundary='r45r; evaluated natively in guardian_policy_checks',independent_evaluation_consequence=matrix,
        obsolete_policy_rejected=True,unchanged_persistence_target='r45o',quoted_policy_and_result_not_executed=True)


def calls(node,symbol_name):
    if isinstance(node,dict):
        return ([node] if node.get('kind')=='call' and node.get('symbol')==symbol_name else [])+sum((calls(v,symbol_name) for v in node.values()),[])
    if isinstance(node,list):return sum((calls(v,symbol_name) for v in node),[])
    return []


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    for n,e in old.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    guardian=new.entries['r45q']['declaration'];sg=calls(guardian,'sg');scope=calls(guardian,'h253r')
    assert len(sg)==len(scope)==1
    assert sg[0]['arguments']==[scope[0]['arguments'][3],scope[0]['arguments'][1],scope[0]['arguments'][4]]
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    main=load_catalog(ROOT,'data/unrestricted-scholarly-freedom-basis-v1.json')
    assert not set(REPLACEMENTS)&set(main.entries)
    users=[n for n,e in main.entries.items() if calls(e['declaration'],'sg')]
    assert users==['so'],users
    # so: the judgment's subject is the matter; the content's person parameter
    # is the second sg argument. The authoritative manuscript was unaffected.
    so=main.entries['so']['declaration'];direct=calls(so,'sg')[0]['arguments']
    assert direct[0]==calls(so,'fb')[0]['arguments'][1]
    assert direct[1]==dict(kind='variable',name=so['parameters'][0]['name'])
    assert len(main.document['statements'])==95 and not new.document['statements']
    return dict(unchanged_imports=True,roundtrips=True,correction_propagated=REPLACEMENTS,
        sg_matches_same_matter_and_ward_in_scope=True,main_sg_users_checked=users,
        current_main_unaffected=True,no_new_source_sentence=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)


def build_report():
    results={}
    for name,fn in [('order',order_checks),('guardians_and_policy',guardian_policy_checks),('targets',target_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,
        'scripts/compose_spiritual_guardians_v2.py','scripts/check_spiritual_guardians_v2.py','tests/test_spiritual_guardians_v2.py',
        'scripts/check_spiritual_guardians.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py'}
    return dict(status='corrected_matter_person_order_with_independent_contract_contrasts',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
