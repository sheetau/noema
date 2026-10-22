"""Check direct duty quantifiers, all-office scope and same clerical bindings."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_clerical_duty_scope import ROOT,LIBRARY,BASIS,CODE,MEANINGS,PRIMITIVES,LIMITS,parents,build,closure
from scripts import check_preserved_public_duties as prior
from scripts.check_motive_causes import unknown

DOC='docs/clerical-duty-scope-v1.md';READING='data/clerical-duty-scope-reading-v1.json'
INDEX=prior.INDEX;INVENTORY=prior.INVENTORY
PRIORS=('reports/preserved-public-duties-v1.json','reports/clerical-audiences-v1.json','reports/confessional-teaching-v1.json','reports/clerical-public-freedom-v1.json')
DOMAIN=prior.DOMAIN;SCENES=prior.SCENES
z=prior.z;ns=prior.ns;run=prior.run;codeid=prior.codeid
B=ns(('person','office','anchor'))+' p zrequired'
CASE=B+' k ztrigger[] p zcases'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

def bounded(row):
    """Only code/list binders are diagnostically replaced; never a full proof."""
    t=parse('p:r zperson[] a.r zother[] a.r zpositive[j[a] d] e.r znegative[j[a] d] e.'+
        'q[e[l['+CODE+'][r b[p zpositive] r b[p znegative]]][l['+CODE+'][]]].'+
        'q[e[l[j[a]][l[a][k zperson[]] l[a][k zother[]]]][l[j[a]][]]].q[e[n p a b][n p a b]].')
    codes,bindings,truth=[s['body']['arguments'][0] if i<2 else s['body'] for i,s in enumerate(t['statements'])]
    count=0
    def walk(x):
        nonlocal count
        if isinstance(x,list):return [walk(y) for y in x]
        if not isinstance(x,dict):return x
        if x.get('kind') in ('forall','exists') and isinstance(x['sort'],dict) and x['sort']['kind'] in ('description','sequence'):
            count+=1;body=walk(x['body']);acc='boundedacc'+str(count);universal=x['kind']=='forall'
            return dict(kind='fold',sequence=deepcopy(codes if x['sort']['kind']=='description' else bindings),
                initial=deepcopy(truth) if universal else dict(kind='not',arguments=[deepcopy(truth)]),
                step=dict(kind='lambda',parameters=[dict(name=acc,sort='truth'),dict(name=x['variable'],sort=x['sort'])],
                    body=dict(kind='and' if universal else 'or',arguments=[dict(kind='variable',name=acc),body])))
        return {k:walk(v) for k,v in x.items()}
    row['body']=walk(row['body']);assert count==2,(row['name'],count)

@lru_cache(None)
def fixture(roots,query,limited=True,source=False):
    d=deepcopy(prior.fixture(('r54f',),'','finite',source));known={x['name'] for x in d['declarations']}
    for row in closure(catalog().document,[n for n in roots if n not in known]):
        if row['name'] not in known:d['declarations'].append(deepcopy(row));known.add(row['name'])
    if limited:
        for row in d['declarations']:
            if row['name'] in ('r54i','r54j','r54m'):bounded(row)
    if source:
        for row in d['declarations']:
            if row['name'] in ('r35m','r35r'):
                row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    helpers=parse('p:r zoffices[a] c.')['declarations'];d['declarations']+=helpers
    # Keep helper definitions, then eliminate unused imported context machinery.
    keep=[x['name'] for x in d['declarations'] if x['name'].startswith('z')]
    d.update(declarations=closure(d,(*roots,*keep)),statements=[])
    return parse(format_graph(d,'compact')+query)

def model(d):
    v,saved=prior.model(d);v['zoffices']=lambda o:o in ('office','other')
    return v,saved

@lru_cache(None)
def direct_checks():
    q='q[k r54i['+B+' '+z('good')+']].q[k r54j['+B+' '+z('good')+']].q[k r54k['+CASE+']].q[k r54f['+prior.CASE+']].'
    d=fixture(('r54i','r54j','r54k','r54f'),q);rows={}
    expected={'baseline':[True,True,True,True],'exempted':[False,False,False,False],
        'unfulfilled':[True,False,False,False],'contradictory':[True,False,False,False],
        'no_instance':[True,True,False,False],'empty_cases':[True,True,False,False],
        'split_fulfillment':[True,False,False,False],'omitted_ledger_item':[True,True,True,False],
        'extra_binding':[True,False,False,False],'empty_without_requirements':[True,True,True,True]}
    for case in expected:
        v,_=model(d)
        if case=='exempted':old=v['zrequired'];v['zrequired']=lambda *a:old(*a) and a[-1]=='anchor'
        if case=='unfulfilled':v['zvalue']=lambda *a:True
        if case=='contradictory':
            v['ztargetpick']=lambda i,p,n:p
            v['zrequired']=lambda issuer,p,o,c,b,r,s,t:(issuer,p,o,tuple(b.items),r)==('issuer','person','office',('person',),'anchor') and codeid(c)[1].get('symbol')=='zpositive'
        if case=='no_instance':v['ztriggers']=lambda t:False
        if case=='empty_cases':v['zcases']=lambda t:False
        if case=='split_fulfillment':
            v['ztriggers']=lambda t:t in ('good','bad');v['zvalue']=lambda tag,b,r,t:t=='good'
        if case=='omitted_ledger_item':v['zitems']=lambda i:i=='positive'
        if case=='extra_binding':
            old=v['zrequired'];v['zrequired']=lambda issuer,p,o,c,b,r,s,t:old(issuer,p,o,c,b,r,s,t) or ((issuer,p,o,tuple(b.items),r,s)==('issuer','person','office',('other',),'anchor',True) and codeid(c)[1].get('symbol')=='zpositive')
        if case=='empty_without_requirements':v['zrequired']=lambda *a:False;v['zitems']=lambda i:False
        got=run(d,v);assert got==expected[case],(case,got);rows[case]=got
    pure=fixture(('r54i',),'q[k r54i['+B+' '+z('good')+']].');v,_=model(pure);v['zvalue']=unknown;assert run(pure,v)==[True]
    for name in ('zrequired','zvalue'):
        v,_=model(d);v[name]=unknown
        try:run(d,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    return dict(cases=rows,nonexemption_does_not_execute_targets=True,unknown_rejected=True,
        bounded_equivalence_with_complete_ledger=True,ledger_omission_does_not_drop_direct_requirements=True)

@lru_cache(None)
def domain_checks():
    rows={}
    for name in ('r54i','r54j','r54k'):
        a=B+' '+z('good') if name!='r54k' else CASE
        d=fixture((name,),'q[k '+name+'['+a+']].',False);v,_=model(d)
        try:run(d,v)
        except ValueError as e:assert 'Cannot finitely quantify the description domain' in str(e);rows[name]=str(e)
        else:raise AssertionError(name)
    return dict(full_domain_rejected=rows,limited_diagnostic='Only rank-one code and individual-sequence quantifiers are replaced by two values each; issuer, office, reference, sign, point, exact arguments and dequotation remain native. No full-domain semantic completeness is inferred.')

@lru_cache(None)
def all_office_checks():
    a=ns(('person','anchor'))+' p zoffices p zrequired k ztrigger[] p zcases'
    actual=ns(('person','anchor'))+' p zrequired k ztrigger[] p zcases'
    q='q[k r54k['+CASE+']].q[k r54l['+a+']].q[k r54p['+actual+']].';d=fixture(('r54k','r54l','r54p'),q);rows={}
    for case in ('baseline','second_office_conflict','some_harmful_instance','no_offices','no_instance'):
        v,_=model(d)
        if case=='second_office_conflict':
            old=v['zrequired'];v['zrequired']=lambda issuer,p,o,c,b,r,s,t:old(issuer,p,o,c,b,r,s,t) or ((issuer,p,o,tuple(b.items),r,s)==('issuer','person','other',('person',),'anchor',False) and codeid(c)[1].get('symbol')=='zpositive')
        if case=='some_harmful_instance':v['ztriggers']=lambda t:t in ('good','bad')
        if case=='no_offices':v['zoffices']=lambda o:False
        if case=='no_instance':v['ztriggers']=lambda t:False
        v['cf']=lambda p,o,t:p=='person' and t=='anchor' and v['zoffices'](o)
        got=run(d,v);expected=[case!='no_instance',case in ('baseline','no_offices'),case in ('baseline','no_offices')]
        assert got==expected,(case,got);rows[case]=got
    return dict(cases=rows,second_office_cannot_be_ignored=True,all_current_cf_roles_bound_natively=True,compatibility_distinct_from_no_restriction=True)

@lru_cache(None)
def source_checks():
    target='k r536[r[l[a][]] r[l[a][]] r[p zcompare]]'
    source=ns(prior.NAMES)+' '+ns(('office','anchor','anchor'))+' r[l[a][]] r[l[a][]] r[p zcompare]'
    q='q[k zsavetarget['+target+']].q[k r54o['+source+']].';d=fixture(('r54o',),q,source=True);rows={}
    for case in ('baseline','wrong_clerical_office','other_church_creed','no_current_office','other_church_service','other_scholar','other_public_source','no_permission','opposite_required','empty_duties','empty_candidates','only_bad_candidate','wrong_public_binding','wrong_case_target'):
        v,saved=model(d)
        v['r35m']=lambda p,o,c,r:(p,o,c,r)==('person','office','church','anchor')
        v['r35r']=lambda c,cr,s,r:(c,cr,s,r)==('church','creed','subject','anchor')
        v['cf']=lambda p,o,t:(p,o,t)==('person','office','anchor')
        v['h246k']=lambda p,c,o,t:(p,c,o,t)==('person','church','office','anchor')
        v['h247d']=lambda p,r:'scholar' if (p,r)==('person','anchor') else 'other'
        v['h247b']=lambda p,s,r:'source' if (p,s,r)==('person','scholar','anchor') else 'other'
        v['zpublic']=lambda b,r,t:tuple(b.items)==prior.NAMES and r=='anchor' and t=='good'
        v['h245c']=lambda s,p,role,c,b,r,sign,t:(s,p,role,tuple(b.items),r,sign,t)==('source','person','scholar',prior.NAMES,'anchor',True,'anchor') and codeid(c)==saved['target']
        v['h237z']=v['zrequired']
        def candidates(p,c,b,r,a,t):
            return (p,tuple(b.items),r,a)==('person',prior.NAMES,'anchor','anchor') and codeid(c)==saved['target'] and t in ('good','bad')
        v['h26o4']=candidates
        if case=='wrong_clerical_office':v['r35m']=lambda *a:False
        if case=='other_church_creed':v['r35r']=lambda *a:False
        if case=='no_current_office':v['cf']=lambda *a:False
        if case=='other_church_service':v['h246k']=lambda *a:False
        if case=='other_scholar':v['h247d']=lambda *a:'other'
        if case=='other_public_source':v['h247b']=lambda *a:'other'
        if case=='no_permission':v['h245c']=lambda *a:False
        if case=='opposite_required':
            old=v['h237z'];v['h237z']=lambda s,p,o,c,b,r,sign,t:old(s,p,o,c,b,r,sign,t) or o=='scholar'
        if case=='empty_duties':v['h237z']=lambda *a:False
        if case=='empty_candidates':v['h26o4']=lambda *a:False
        if case=='only_bad_candidate':v['h26o4']=lambda *a:candidates(*a) and a[-1]=='bad'
        if case=='wrong_public_binding':v['zpublic']=lambda *a:False
        if case=='wrong_case_target':v['h26o4']=lambda p,c,b,r,a,t:codeid(c)[1].get('symbol')=='zpositive'
        got=run(d,v);assert got==[True,case=='baseline'],(case,got);rows[case]=got[-1]
    return dict(cases=rows,same_person_office_church_creed_and_scholar=True,same_target_for_permission_and_candidates=True,
        no_current_publication_required=True,boundary='r35m/r35r are exact argument boundaries backed by prior native checks; r535 is the prior exact public-content binding boundary. r54i–o, r536, r37c and role/service/source relations execute natively except for the explicitly bounded code/list quantifiers.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='same_clerical_office_with_direct_complete_requirements_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[574,889],text=u['text'][574:889]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['同じ限定君主への照応と敬意評価','全発表候補と全職務の他者への本文接続','noch mehrと全文帰属・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    c=catalog()
    for parent in parents():
        for n,e in c.entries.items():
            if n in parent.entries:assert e['declaration']==parent.entries[n]['declaration'] and e['meaning_ja']==parent.entries[n]['meaning_ja']
    assert not c.document['statements'] and len(parents()[1].document['statements'])==113
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact')
    try:parse(t+'q[e[r b[p r54o]][r b[p r54o]]].')
    except ValueError as e:assert 'Quoted evaluation' in str(e)
    else:raise AssertionError('Low-rank quote accepted')
    parse(t+'q[e[r c[p r54o]][r c[p r54o]]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),main_statements_preserved=113,new_verified_characters=0,inherited_meanings_preserved=True,roundtrips=True,combined_quote_rank=2)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in (('direct',direct_checks),('domains',domain_checks),('all_offices',all_office_checks),('source',source_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json',
        'scripts/compose_clerical_duty_scope.py','scripts/check_clerical_duty_scope.py','tests/test_clerical_duty_scope.py',
        'scripts/check_preserved_public_duties.py','scripts/compose_preserved_public_duties.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='direct_complete_requirements_and_same_clerical_office_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
