"""Check coherence failures and persistence of the same selected contents."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_irrational_perpetuation import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/irrational-perpetuation-v1.json'
DOC='docs/irrational-perpetuation-v1.md'
EVIDENCE='data/irrational-perpetuation-evidence-v1.json'
PRIORS=('reports/spiritual-guardians-v1.json','reports/unrestricted-scholarly-freedom-v1.json','reports/unending-persistence-v1.json')
DOMAIN=('source','people','community','standard','requirement','one','two','other')
SCENES=('past','reference','later')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'r zref[] d.r zpoint[] d.'
POLICY='k zsource[] k zpeople[] k zcommunity[] k zstandard[] k zref[]'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(roots,query,boundaries=(),provider=False):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    if provider:
        prefix=parse('p:r ztruth[d] c.r zchoose[a d i[e] i[e]] i[e].'+
            'd h246e[formulation a reference d] i[e][k zchoose[v formulation v reference r[b point[k ztruth[v point]]] r[b point[u[e[v point][v point]]]]]].')
        doc['declarations']=prefix['declarations']+[d for d in doc['declarations'] if d['name']!='h246e']
    return parse(format_graph(doc,'compact')+EXTRA+query)


def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)


def model(doc,variant='baseline',bits=(True,True)):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update(zref=lambda:'reference',zpoint=lambda:'later')
    seen=[]
    def target(standard,requirement,code,bindings,ref):
        row=(standard,requirement,symbol(code),code.rank,tuple(bindings.items),ref)
        policy=('standard','requirement','r45i',2,('source','people','community'),'reference')
        formulation=('standard','requirement','r45l',2,tuple(bindings.items),'reference')
        matched=row==policy or row==formulation and tuple(bindings.items) in (('one',),('two',))
        if variant.startswith('target_'):
            i={'standard':0,'requirement':1,'code':2,'rank':3,'bindings':4,'reference':5}[variant[7:]]
            wanted=list(policy);wanted[i]=1 if i==3 else ('other',) if i==4 else 'other'
            matched=row==tuple(wanted)
        return matched
    def applies(*args):
        if variant=='target_requirement':
            standard,requirement,code,bindings,ref=args
            return (standard,requirement,symbol(code),tuple(bindings.items),ref)==('standard','requirement','r45i',('source','people','community'),'reference')
        return variant!='inapplicable' and target(*args)
    def verdict(standard,requirement,code,bindings,ref,positive,point):
        seen.append((symbol(code),tuple(bindings.items),ref,positive,point))
        if not target(standard,requirement,code,bindings,ref):return False
        correct_point='reference' if symbol(code)=='r45l' else 'later'
        if variant=='wrong_point':correct_point='past'
        if variant=='no_verdict':return False
        if positive:return variant in ('conflict','satisfied')
        return bits[0] and variant!='satisfied' and point==correct_point
    def scope(c,f,ref):return variant!='empty_selection' and (c,ref)==('community','reference') and f in ('one','two','other')
    def history(c,candidate,point):
        points=() if variant=='empty_history' else ('past','later') if variant=='missing_anchor' else SCENES
        return (c,candidate)==('community','later') and point in points
    def before(first,last,candidate):
        return candidate=='later' and (SCENES.index(first)<SCENES.index(last) or variant=='cycle' and (first,last)==('later','past'))
    def maintains(c,f,point):
        if c!='community' or f not in ('one','two'):return False
        if variant=='lost_one' and (f,point)==('one','later'):return False
        if variant=='alternating' and (f,point) in (('one','later'),('two','reference')):return False
        if variant=='missing_at_anchor' and (f,point)==('one','reference'):return False
        return point!='past'  # Past absence must not invalidate a future tail.
    causal=[]
    def consequence(cause,cb,result,rb,ref,point):
        row=(symbol(cause),cause.rank,tuple(cb.items),symbol(result),result.rank,tuple(rb.items),ref,point);causal.append(row)
        wanted=['r45i',2,('source','people','community'),'r45o',2,('community','standard'),'reference','later']
        if variant.startswith('causal_'):
            i={'cause':0,'cause_rank':1,'cause_bindings':2,'result':3,'result_rank':4,'result_bindings':5,'reference':6,'point':7}[variant[7:]]
            wanted[i]=1 if i in (1,4) else ('other',) if i in (2,5) else 'other'
        return bits[1] and row==tuple(wanted)
    v.update(h253s=applies,h253t=verdict,h253u=scope,h253w=history,ic=before,h253v=maintains,h253x=consequence)
    return v,seen,causal


@lru_cache(None)
def evaluation_checks():
    doc=fixture(('r45k',),'q[t[k r45k['+POLICY+']][k zpoint[]]].');rows={}
    for variant in ('baseline','inapplicable','no_verdict','conflict','satisfied','wrong_point',
        *('target_'+n for n in ('standard','requirement','code','rank','bindings','reference'))):
        v,seen,_=model(doc,variant);result=run(doc,v);assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
        assert seen and all(row[0]=='r45i' and row[1]==('source','people','community') for row in seen)
    for name in ('h253s','h253t'):
        v,_,_=model(doc);v[name]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,unknown_rejected=True,quoted_immaturity_policy_not_executed=True)


@lru_cache(None)
def persistence_checks():
    query='q[t[k r45n[k zcommunity[] k zstandard[] k zref[]]][k zpoint[]]].'
    doc=fixture(('r45n',),query);rows={}
    for variant in ('baseline','empty_selection','empty_history','missing_anchor','cycle','lost_one','alternating','missing_at_anchor','no_verdict','conflict'):
        v,seen,_=model(doc,variant);result=run(doc,v);assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
        assert all(row[0]=='r45l' and row[2]=='reference' and row[4]=='reference' for row in seen)
    for name in ('h253u','h253v','h253w','ic','h253t'):
        v,_,_=model(doc);v[name]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    for name in ('zcommunity','zstandard'):
        v,_,_=model(doc);v[name]=lambda:'other';assert run(doc,v)==[False],name
    return dict(contrasts=rows,native_rca_and_all_formulations=True,fixed_reference_selection=True,
        past_absence_allowed=True,irrelevant_or_coherent_contents_not_required=True,
        unknown_rejected=True,finite_histories_not_proof_of_unbounded_future=True)


@lru_cache(None)
def adapter_checks():
    rows={}
    for members in ((),('one',),('one','two')):
        seq='l[a]['+' '.join('k z'+n+'[]' for n in members)+']'
        doc=fixture(('r45l',),'q[t[k r45l['+seq+' k zref[]]][k zpoint[]]].',provider=True)
        v,_,_=model(doc);v['ztruth']=lambda point:point=='later'
        v['zchoose']=lambda f,ref,yes,no:yes if (f,ref)==('one','reference') else no
        result=run(doc,v,('one','two'));assert result==[members==('one',)],(members,result);rows[str(members)]=result[0]
        if members==('one',):
            for name in ('zone','zref'):
                original=v[name];v[name]=lambda:'two' if name=='zone' else 'past'
                assert run(doc,v,('one','two'))==[False],name
                v[name]=original
            v['ztruth']=lambda point:False;assert run(doc,v,('one','two'))==[False]
            v['ztruth']=unknown
            try:run(doc,v,('one','two'))
            except ValueError as error:assert 'Unknown' in str(error)
            else:raise AssertionError('unquotation was skipped')
    outcomes={}
    for members in ((),('community',),('community','standard'),('standard','community'),('community','standard','community')):
        seq='l[a]['+' '.join('k z'+n+'[]' for n in members)+']'
        doc=fixture(('r45o',),'q[t[k r45o['+seq+' k zref[]]][k zpoint[]]].',('r45n',))
        v,_,_=model(doc)
        v['r45n']=lambda c,s,ref:Content(SCENES,tuple((c,s,ref,p)==('community','standard','reference','later') for p in SCENES))
        result=run(doc,v,('community','standard'));assert result==[members==('community','standard')],(members,result);outcomes[str(members)]=result[0]
    return dict(native_formulation_unquotation=rows,unknown_content_rejected_when_executed=True,
        exact_result_bindings=outcomes,result_adapter_boundary='r45n; evaluated natively in persistence_checks')


@lru_cache(None)
def consequence_checks():
    doc=fixture(('r45p',),'q[t[k r45p['+POLICY+']][k zpoint[]]].');rows=[]
    for bits in product((False,True),repeat=2):
        v,_,seen=model(doc,bits=bits);result=run(doc,v);assert result==[all(bits)],(bits,result)
        rows.append(dict(evaluation=bits[0],consequence=bits[1],result=result[0]))
        assert seen
    contrasts={}
    for name in ('cause','cause_rank','cause_bindings','result','result_rank','result_bindings','reference','point'):
        v,_,_=model(doc,'causal_'+name);result=run(doc,v);assert result==[False],name;contrasts[name]=False
    v,_,_=model(doc);v['h253x']=unknown
    try:run(doc,v)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('unknown causal relation')
    # The native result description is quoted; make every outcome-only relation unknown.
    v,_,_=model(doc)
    for n in ('h246e','h253u','h253v','h253w','ic','h237z'):v[n]=unknown
    assert run(doc,v)==[True]
    quoted=fixture(('r45p',),'r zshown[i d[h[a a a a d] e]] c.q[k zshown[r d[p r45p]]].')
    v,_,_=model(quoted);v['zshown']=lambda code:code.rank==3 and symbol(code)=='r45p'
    assert run(quoted,v)==[True]
    return dict(independent_evaluation_and_consequence=rows,exact_causal_payload=contrasts,
        result_and_policy_not_executed=True,rank_three_outer_quote=True,unknown_consequence_rejected=True)


@lru_cache(None)
def structure_checks():
    old,dep,new=parent(),dependency(),catalog()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            previous=old.entries[n] if n in old.entries else dep.entries[n]
            assert e['declaration']==previous['declaration'] and e['meaning_ja']==previous['meaning_ja'],n
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
        no_new_source_sentence=True,source_and_lexical_evidence_pinned=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)


def build_report():
    results={}
    for name,fn in [('evaluation',evaluation_checks),('persistence',persistence_checks),('adapters',adapter_checks),('consequence',consequence_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    evidence=read(EVIDENCE)
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,EVIDENCE,evidence['source_inventory'],
        *[p['path'] for p in [*evidence['pages'],*evidence['lexical_sources']]],
        'scripts/compose_irrational_perpetuation.py','scripts/check_irrational_perpetuation.py','tests/test_irrational_perpetuation.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='coherence_failure_same_contents_persistence_and_quoted_causal_consequence',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
