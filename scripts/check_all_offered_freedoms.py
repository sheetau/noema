"""Check constructed list names, possible offers, and complete candidate scope."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_all_offered_freedoms import ROOT,LIBRARY,BASIS,CODE,COMPARISONS,NAMES,MEANINGS,PRIMITIVES,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/all-offered-freedoms-v1.md';READING='data/all-offered-freedoms-reading-v1.json'
INDEX='data/semantic-review-index-v197.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/clerical-duty-scope-v1.json','reports/revered-clerical-scope-v1.json','reports/offered-judgments-v1.json','reports/confessional-divergence-v1.json')
DOMAIN=('person','scholar','activity','otheractivity','audience','church','creed','subject','office','ruler','rulingoffice','community','one','two','other')
SCENES=('reference','anchor','possible','bad')
def z(n):return 'k z'+n+'[]'
def ns(names):return ' '.join(z(n) for n in names)
def seq(items):return 'l[a]['+ns(items)+']'
def codeid(c):return c.rank,json.loads(c.syntax)
J=seq(('one',));I=seq(());COMP='r[p zcompare]'
CLERGY='k r536[k r543['+J+'] k r543['+I+'] '+COMP+']'
PUBLIC='k r53w[k r543['+J+'] k r543['+I+']]'
SAVE='q[k zsaveclergy['+CLERGY+']].q[k zsavepublic['+PUBLIC+']].q[k zsaveone[k r543['+J+']]].q[k zsaveempty[k r543['+I+']]].'
CARGS=ns(NAMES)+' '+J+' '+I+' '+ns(('reference','anchor'))+' '+COMP
PARGS=ns(NAMES[:4])+' '+J+' '+I+' '+ns(('reference','anchor'))
LOCAL=ns(('person','office','church','creed','subject','scholar','reference','anchor'))+' '+COMP
GENERAL=ns(('person','scholar','reference','anchor'))

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

def bounded_lists(row):
    t=parse('p:r zone[] a.r ztwo[] a.q[e[l[j[a]][l[a][] l[a][k zone[]] l[a][k ztwo[]]]][l[j[a]][]]].q[e[n p a b][n p a b]].')
    samples=t['statements'][0]['body']['arguments'][0];truth=t['statements'][1]['body'];count=0
    def walk(x):
        nonlocal count
        if isinstance(x,list):return [walk(v) for v in x]
        if not isinstance(x,dict):return x
        if x.get('kind') in ('forall','exists') and isinstance(x['sort'],dict) and x['sort']['kind']=='sequence':
            count+=1;body=walk(x['body']);acc='listacc'+str(count);all_=x['kind']=='forall'
            return dict(kind='fold',sequence=deepcopy(samples),initial=deepcopy(truth) if all_ else dict(kind='not',arguments=[deepcopy(truth)]),
                step=dict(kind='lambda',parameters=[dict(name=acc,sort='truth'),dict(name=x['variable'],sort=x['sort'])],
                    body=dict(kind='and' if all_ else 'or',arguments=[dict(kind='variable',name=acc),body])))
        return {k:walk(v) for k,v in x.items()}
    row['body']=walk(row['body']);assert count==4,(row['name'],count)

@lru_cache(None)
def fixture(roots,query,mode='public',limited=False):
    d=deepcopy(catalog().document)
    replaced=('r534','r53u','r54o','r54p') if mode=='public' else ('r55a','r55b','r55e','r55f','r55g') if mode=='quantified' else ('r54z','r55c')
    for row in d['declarations']:
        if row['name'] in replaced:
            row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
        elif limited and row['name'] in ('r55c','r55h','r55i'):bounded_lists(row)
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zcompare[a d] c.r zsaveclergy['+CODE+'] c.r zsavepublic['+CODE+'] c.r zsaveone[i[j[a]]] c.r zsaveempty[i[j[a]]] c.'
    if mode=='public':
        extra+='r zpublic[j[a] j[a] j[a] d d] c.r zclerical[j[a] j[a] h[a d] c j[a] d d] c.'
        extra+='d r53v[judgments j[a] insights j[a] bindings j[a] reference d] e[b point[k zpublic[v judgments v insights v bindings v reference v point]]].'
        extra+='d r535[judgments j[a] insights j[a] comparisons h[a d] c bindings j[a] reference d] e[b point[k zclerical[v judgments v insights v comparisons v bindings v reference v point]]].'
    prefix=parse('p:'+extra);names={x['name'] for x in prefix['declarations']}
    d['declarations']=prefix['declarations']+[x for x in d['declarations'] if x['name'] not in names]
    # Query helpers include the real list construction and both target constructors.
    d.update(declarations=closure(d,(*roots,'r543','r536','r53w',*names)),statements=[])
    return parse(format_graph(d,'compact')+query)

def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

def model(d):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['znamepick']=lambda p,*codes:codes[DOMAIN.index(p)];v['zrefpick']=lambda p,*codes:codes[SCENES.index(p)]
    for n in ('clergy','public','one','empty'):v['zsave'+n]=lambda c,n=n:saved.update({n:codeid(c)}) is None
    v['zcompare']=lambda item,t:(item,t)==('one','possible')
    v['r53u']=lambda p,a,s,au,j,i,r,t:(p,a,s,au,tuple(j.items),tuple(i.items),r,t)==('person','activity','scholar','audience',('one',),(),'reference','possible')
    v['r534']=lambda p,a,s,au,ch,cr,su,j,i,r,comp,t:(ch,cr,su)==('church','creed','subject') and v['r53u'](p,a,s,au,j,i,r,t) and comp('one','possible') is True
    v['zpublic']=lambda j,i,b,r,t:tuple(b.items)==NAMES[:4] and v['r53u'](*b.items,j,i,r,t)
    v['zclerical']=lambda j,i,comp,b,r,t:tuple(b.items)==NAMES and v['r534'](*b.items,j,i,r,comp,t)
    def cases(p,target,b,r,anchor,t):
        key='clergy' if len(b.items)==7 else 'public'
        return (p,tuple(b.items),r,anchor)==('person',NAMES if key=='clergy' else NAMES[:4],'reference','anchor') and codeid(target)==saved[key] and t in ('possible','bad')
    v['h26o4']=cases
    v['h247b']=lambda p,s,r:'ruler' if (p,s,r)==('person','scholar','reference') else 'other'
    v['h245c']=lambda source,p,role,c,b,r,sign,t:(source,p,role,tuple(b.items),r,sign,t)==('ruler','person','scholar',NAMES[:4],'reference',True,'anchor') and codeid(c)==saved['public']
    v['h237z']=lambda *a:False
    return v,saved

@lru_cache(None)
def sequence_checks():
    rows={}
    for items in ((),('one',),('one','two'),('two','one'),('one','two','one')):
        literal=seq(items);d=fixture(('r544',),'q[k r544['+literal+']].q[e[s[k r543['+literal+']]]['+literal+']].')
        v,_=model(d);got=run(d,v);assert got==[True,True];rows[str(items)]=got
        if items:
            v['znamepick']=lambda p,*codes:codes[DOMAIN.index('other' if p=='one' else p)]
            assert run(d,v)==[False,False]
    d=fixture(('r544',),'q[k r544['+J+']].');v,_=model(d);v['znamepick']=unknown;rejects(d,v)
    return dict(cases=rows,empty_order_and_duplicates_preserved=True,wrong_names_and_unknown_rejected=True,new_sequence_name_primitive=False)

@lru_cache(None)
def candidate_checks():
    d=fixture(('r55a','r55e'),SAVE+'q[k r55a['+CARGS+']].q[k r55e['+PARGS+']].');rows={}
    for case in ('baseline','empty_cases','no_offer','no_confessional_difference','wrong_compare','wrong_item_name','only_nonperforming_case'):
        v,_=model(d)
        if case=='empty_cases':v['h26o4']=lambda *a:False
        if case=='no_offer':v['r53u']=lambda *a:False
        if case=='no_confessional_difference':v['r534']=lambda *a:False
        if case=='wrong_compare':v['zcompare']=lambda *a:False
        if case=='wrong_item_name':v['znamepick']=lambda p,*codes:codes[DOMAIN.index('other' if p=='one' else p)]
        if case=='only_nonperforming_case':old=v['h26o4'];v['h26o4']=lambda *a:old(*a) and a[-1]=='bad'
        # Candidate classification must never ask whether publication is permitted.
        v['h245c']=unknown;v['h237z']=unknown
        got=run(d,v);expected=[case=='baseline',case in ('baseline','no_confessional_difference','wrong_compare')]
        assert got==[True]*4+expected,(case,got);rows[case]=got[4:]
    v,_=model(d);v['h26o4']=unknown;rejects(d,v)
    return dict(cases=rows,no_actual_anchor_publication_required=True,permission_and_duty_fulfillment_not_used_to_select_candidates=True,
        boundary='r535 and r53v are exact list/four-or-seven-binding/reference/content boundaries backed by prior native evidence. Their exhaustive individual witness search is not repeated here. List and target construction, dequotation into those boundaries and the candidate quantifier are native.')

@lru_cache(None)
def freedom_connections():
    d=fixture(('r55b','r55f','r55g'),SAVE+'q[k r55b['+CARGS+' '+z('office')+']].q[k r55f['+PARGS+']].q[k r55g['+PARGS+']].');rows={}
    for case in ('baseline','clerical_no_freedom','all_offices_restrict','no_public_permission','public_prohibition','wrong_public_source'):
        v,saved=model(d)
        def clergy(p,a,s,au,ch,cr,su,o,r,anchor,j,i,comp):
            return (p,a,s,au,ch,cr,su,o,r,anchor)==(*NAMES,'office','reference','anchor') and codeid(j)==saved['one'] and codeid(i)==saved['empty'] and codeid(comp)==(0,{'kind':'function_ref','symbol':'zcompare'})
        def unrestricted(p,anchor,required,trigger,cases):
            return (p,anchor)==('person','anchor') and trigger.values==(False,False,True,False) and tuple(t for t in SCENES if cases(t))==('possible','bad')
        v['r54o']=clergy;v['r54p']=unrestricted
        if case=='clerical_no_freedom':v['r54o']=lambda *a:False
        if case=='all_offices_restrict':v['r54p']=lambda *a:False
        if case=='no_public_permission':v['h245c']=lambda *a:False
        if case=='public_prohibition':v['h237z']=lambda *a:True
        if case=='wrong_public_source':v['h247b']=lambda *a:'other'
        got=run(d,v);expected=[case!='clerical_no_freedom',case!='all_offices_restrict',case not in ('no_public_permission','public_prohibition','wrong_public_source')]
        assert got==[True]*4+expected,(case,got);rows[case]=got[4:]
    return dict(cases=rows,same_constructed_lists_targets_bindings_and_candidate_ranges=True,
        boundary='r54o and r54p check their complete incoming argument/trigger boundary; their normative bodies retain prior native evidence. r53w/r536, r37c and the new connections execute natively.')

def quantified_model(d):
    v,saved=model(d)
    def eligible(p,a,s,au,j,i,r,anchor):
        return (p,a,s,au,r,anchor)==('person','activity','scholar','audience','reference','anchor') and tuple(j.items) in (('one',),('two',)) and not i.items
    v['r55e']=eligible
    v['r55a']=lambda p,a,s,au,ch,cr,su,j,i,r,anchor,comp:(ch,cr,su)==('church','creed','subject') and eligible(p,a,s,au,j,i,r,anchor)
    v['r55b']=lambda *a:a[-1]=='office';v['r55f']=lambda *a:True;v['r55g']=lambda *a:True
    return v,saved

@lru_cache(None)
def quantifier_checks():
    query='q[k r55c['+LOCAL+']].q[k r55h['+GENERAL+']].q[k r55i['+GENERAL+']].'
    full=fixture(('r55c','r55h','r55i'),query,'quantified');v,_=quantified_model(full)
    try:run(full,v)
    except ValueError as e:assert 'Cannot finitely quantify the unbounded sequence domain' in str(e),str(e)
    else:raise AssertionError('All finite lists treated as a finite domain')
    d=fixture(('r55c','r55h','r55i'),query,'quantified',True);rows={}
    for case in ('baseline','second_clerical_offer_denied','one_offer_restricted','one_offer_denied','no_candidates','another_activity_denied','irrelevant_denial'):
        v,_=quantified_model(d)
        if case=='second_clerical_offer_denied':v['r55b']=lambda *a:tuple(a[7].items)!=('two',)
        if case=='one_offer_restricted':v['r55f']=lambda *a:tuple(a[4].items)!=('two',)
        if case=='one_offer_denied':v['r55g']=lambda *a:tuple(a[4].items)!=('two',)
        if case=='no_candidates':v['r55a']=lambda *a:False;v['r55e']=lambda *a:False
        if case=='another_activity_denied':
            old=v['r55e'];v['r55e']=lambda p,a,*xs:old(p,'activity',*xs) and a in ('activity','otheractivity')
            v['r55g']=lambda p,a,*xs:a!='otheractivity'
        if case=='irrelevant_denial':v['r55g']=lambda p,a,*xs:a=='activity'
        got=run(d,v);expected=[case not in ('second_clerical_offer_denied','no_candidates'),case not in ('one_offer_restricted','no_candidates'),case not in ('one_offer_denied','another_activity_denied','no_candidates')]
        assert got==expected,(case,got);rows[case]=got
    v,_=quantified_model(d);v['r55e']=unknown;rejects(d,v)
    return dict(full_list_domain_rejected=True,diagnostic_cases=rows,all_activity_and_audience_quantifiers_native=True,
        person_wide_nonrestriction_not_one_compatible_offer=True,
        boundary='Only sequence binders are replaced by empty, singleton-one and singleton-two lists. Candidate and conclusion relations are separate exact boundaries. This checks quantifier wiring, not full semantic-domain completeness or the prior deep action bodies.')

@lru_cache(None)
def source_scope_checks():
    frame=ns(('ruler','rulingoffice','community','person','office','church','creed','subject','scholar','reference'))
    d=fixture(('r55d',),'q[k r55d['+frame+']].','scope');rows={}
    for case in ('baseline','no_all_offer_freedom','outside_scope','wrong_creed_name','wrong_reference_name','wrong_comparison_scope'):
        v,_=model(d)
        v['r54z']=lambda *a:a==('ruler','rulingoffice','community','person','office','church','creed','subject','scholar','reference')
        v['h26km']=lambda:'reference';v['h26kn']=lambda p:'anchor' if p=='reference' else 'bad'
        v['h26o6']=lambda ch,cr,su,item,ref,t:(ch,cr,su,item,ref,t)==('church','creed','subject','one','reference','possible')
        # Evaluate the supplied comparison code natively via an adapter below.
        v['zlocalscope']=lambda p,o,ch,cr,su,s,r,a,one,other:(p,o,ch,cr,su,s,r,a)==('person','office','church','creed','subject','scholar','reference','anchor') and one is True and other is False
        if case=='no_all_offer_freedom':v['zlocalscope']=lambda *a:False
        if case=='outside_scope':v['r54z']=lambda *a:False;v['zlocalscope']=lambda *a:False
        if case=='wrong_creed_name':v['znamepick']=lambda p,*codes:codes[DOMAIN.index('other' if p=='creed' else p)]
        if case=='wrong_reference_name':v['zrefpick']=lambda p,*codes:codes[SCENES.index('bad')]
        if case=='wrong_comparison_scope':v['h26o6']=lambda *a:True
        native=deepcopy(d)
        extra=parse('p:r zone[] a.r ztwo[] a.r zpossible[] d.r zlocalscope[a a a a a a d d c c] c.'+
            'd r55c[person a office a church a creed a subject a scholar a reference d anchor d comparisons '+COMPARISONS+'] c[k zlocalscope[v person v office v church v creed v subject v scholar v reference v anchor c[s[v comparisons]][k zone[] k zpossible[]] c[s[v comparisons]][k ztwo[] k zpossible[]]]].')
        replacements={x['name']:x for x in extra['declarations'] if x['name']=='r55c'}
        native['declarations']=[x for x in extra['declarations'] if x['name']=='zlocalscope']+[replacements.get(x['name'],x) for x in native['declarations']]
        native=parse(format_graph(native,'compact'));got=run(native,v);assert got==[case in ('baseline','outside_scope')],(case,got);rows[case]=got[0]
    return dict(cases=rows,same_prior_ruler_and_clerical_scope=True,four_comparison_names_checked=True,
        boundary='r54z is its exact prior scope boundary; r55c is an exact local-freedom boundary which evaluates the actual supplied comparison code for two items. Conditional scope, name checks and comparison construction are native.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='all_public_offers_and_person_wide_nonrestriction_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[574,889],text=u['text'][574:889]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['全人物範囲とjeder andereの除外範囲','noch mehrの論述関係','本文設定・全文帰属と通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    c=catalog()
    for parent in parents():
        for n,e in c.entries.items():
            if n in parent.entries:assert e['declaration']==parent.entries[n]['declaration'] and e['meaning_ja']==parent.entries[n]['meaning_ja']
    assert not c.document['statements'] and len(load_catalog(ROOT,'data/prince-sentence-basis-v1.json').document['statements'])==113
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact')
    try:parse(t+'q[e[r b[p r55d]][r b[p r55d]]].')
    except ValueError as e:assert 'Quoted evaluation' in str(e)
    else:raise AssertionError('Low-rank quote accepted')
    parse(t+'q[e[r c[p r55d]][r c[p r55d]]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),main_statements_preserved=113,new_verified_characters=0,inherited_meanings_preserved=True,roundtrips=True,scope_quote_rank=2)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in (('sequences',sequence_checks),('candidates',candidate_checks),('freedom',freedom_connections),('quantifiers',quantifier_checks),('source',source_scope_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json',
        'scripts/compose_all_offered_freedoms.py','scripts/check_all_offered_freedoms.py','tests/test_all_offered_freedoms.py',
        'scripts/compose_clerical_duty_scope.py','scripts/compose_confessional_divergence.py','scripts/compose_prince_sentence.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='all_offered_candidates_and_person_wide_nonrestriction_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
