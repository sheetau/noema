"""Check constructed norm targets, exact bindings, and actual/normative independence."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_delegated_teaching_freedom import ROOT,LIBRARY,BASIS,NAMES,PRIMITIVES,MEANINGS,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_congregational_private_use import model as congregation_model,ARGS as CASE_ARGS
from scripts.check_teaching_policy import EXTRA_LOCAL,PROVIDERS,SMALL,SCENES

REPORT='reports/delegated-teaching-freedom-v1.json'
DOC='docs/delegated-teaching-freedom-v1.md'
EVIDENCE='data/delegated-teaching-freedom-evidence-v1.json'
PRIORS=('reports/teaching-discretion-v1.json','reports/congregational-private-use-v1.json')
FOCUSED=NAMES
DOMAIN=(*NAMES,'other','norm')
EXTRA=''.join('r z'+n+'[] a.' for n in (*NAMES,'other','norm'))+'r zref[] d.r zpoint[] d.'
EXTRA+='r zmeaning[a] e.d zmessage[subject a] f[j s[k zmeaning[v subject]]].d zalias[subject a] f[k zmessage[v subject]].'
SEQ='l[a]['+' '.join('k z'+n+'[]' for n in NAMES)+']'
ARGS=' '.join('k z'+n+'[]' for n in NAMES)+' r[p zmessage] k zref[]'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(query=None,integrated=False):
    doc=deepcopy(catalog().document);doc['statements']=[]
    if integrated:
        prefix=parse('p:'+EXTRA_LOCAL+PROVIDERS)
        providers={d['name']:d for d in prefix['declarations'] if d['name'] in ('h246e','h246j')}
        doc['declarations']=[d for d in prefix['declarations'] if d['name'] not in providers]+[
            deepcopy(providers.get(d['name'],d)) for d in doc['declarations']]
        return parse(format_graph(doc,'compact')+'q[t[k r44l['+CASE_ARGS+']][k zpoint[]]].')
    if query is None:query=''.join('q[t[k '+n+'['+ARGS+']][k zpoint[]]].' for n in ('r4d','r44i','r44j','r44k'))
    return parse(format_graph(doc,'compact')+EXTRA+query)


def embedded_message(code):
    assert code.rank==1
    syntax=json.loads(code.syntax)
    assert syntax['kind']=='apply' and len(syntax['arguments'])==1
    function=syntax['function'];assert function['kind']=='lambda' and function['body']['kind']=='lambda'
    assert function['body']['body']['kind']=='call' and function['body']['body']['symbol']=='r44g'
    argument=syntax['arguments'][0]
    assert argument['kind']=='quote' and argument.get('rank',0)==0 and argument['body']['kind']=='function_ref'
    return argument['body']['symbol']


def model(doc,bits=(True,False,True),variant='baseline',integrated=False):
    competence,criterion,demand=bits
    v=congregation_model(doc,variant) if integrated else {d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    if not integrated:
        v.update({'z'+n:lambda n=n:n for n in (*NAMES,'other','norm')})
        v.update(zref=lambda:'reference',zpoint=lambda:'outcome')
    seen={'authority':[],'demands':[]}
    def authority(enabled,relation):
        def check(church,person,role,subject,message,ref,point):
            actual=(church,person,role,subject,symbol(message),message.rank,ref,point)
            wanted=['church','person','role','subject','zmessage',0,'reference','outcome']
            fields=('church','person','role','subject','message','rank','reference','point')
            for i,f in enumerate(fields):
                if variant==relation+'_'+f:wanted[i]=1 if f=='rank' else 'other'
            seen['authority'].append((relation,actual))
            return enabled and actual==tuple(wanted)
        return check
    v.update(h247p=authority(competence,'competence'),h247q=authority(criterion,'criterion'))
    def source(church,role,ref):
        wanted=['church','role','reference']
        for i,n in enumerate(('church','role','reference')):
            if variant=='source_'+n:wanted[i]='other'
        return 'norm' if (church,role,ref)==tuple(wanted) else 'other'
    def requirement(source,person,role,code,bindings,ref,positive,point):
        actual=(source,person,role,embedded_message(code),code.rank,tuple(bindings.items),ref,positive,point)
        wanted=['norm','person','role','zmessage',1,NAMES,'reference',False,'outcome']
        fields=('source','person','role','message','rank','bindings','reference','polarity','point')
        for i,n in enumerate(fields):
            if variant=='demand_'+n:wanted[i]=True if n=='polarity' else 0 if n=='rank' else tuple(reversed(NAMES)) if n=='bindings' else 'other'
        seen['demands'].append(actual)
        return demand and actual==tuple(wanted)
    v.update(h253f=source,h237z=requirement)
    return v,seen


def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)


@lru_cache(None)
def target_checks():
    direct='t[k r4d['+ARGS+']][k zpoint[]]'
    adapted='t[k r44g[r[p zmessage] '+SEQ+' k zref[]]][k zpoint[]]'
    constructed='t[c[s[k r44h[r[p zmessage]]]]['+SEQ+' k zref[]]][k zpoint[]]'
    doc=fixture(''.join('q['+q+'].' for q in (direct,adapted,constructed)));rows=[]
    for a,b in product((False,True),repeat=2):
        v,_=model(doc,(a,b,False));result=run(doc,v,FOCUSED);assert result==[a and b]*3,(a,b,result);rows.append([a,b,*result])
    for seq in ('l[a][]','l[a][k zchurch[]]','l[a][k zperson[] k zchurch[] k zrole[] k zsubject[]]',
                SEQ[:-1]+' k zchurch[]]'):
        q=fixture('q[t[c[s[k r44h[r[p zmessage]]]]['+seq+' k zref[]]][k zpoint[]]].')
        v,_=model(q,(True,True,False));assert run(q,v,FOCUSED)==[False],seq
    alias=fixture('q[t[c[s[k r44h[r[p zalias]]]]['+SEQ+' k zref[]]][k zpoint[]]].')
    v,seen=model(alias,(True,True,False));assert run(alias,v,FOCUSED)==[False]
    assert any(row[1][4]=='zalias' for row in seen['authority'])
    # An alias with identical denotation is not silently substituted for the
    # original closed utterance; the normative payload retains that alias too.
    alias_norm=fixture('q[t[k r44j['+ARGS.replace('r[p zmessage]','r[p zalias]')+']][k zpoint[]]].')
    v,seen=model(alias_norm);assert run(alias_norm,v)==[False]
    assert any(row[3]=='zalias' for row in seen['demands'])
    return dict(native_direct_adapter_constructed_target_table=rows,exact_four_individual_binding_order_and_length=True,
        exact_message_description_preserved=True,focused_native_domain=list(FOCUSED),no_definition_boundaries=True)


@lru_cache(None)
def independence_checks():
    doc=fixture();table=[]
    for bits in product((False,True),repeat=3):
        v,_=model(doc,bits);free=bits[0] and bits[1];result=run(doc,v)
        assert result==[free,not free,bits[2],not free and bits[2]],(bits,result)
        table.append([*bits,*result])
    norm=fixture('q[t[k r44j['+ARGS+']][k zpoint[]]].');v,seen=model(norm)
    for name in ('h247p','h247q','zmeaning'):v[name]=unknown
    assert run(norm,v)==[True] and not seen['authority']
    negative=fixture('q[t[k r44i['+ARGS+']][k zpoint[]]].')
    for name in ('h247p','h247q'):
        v,_=model(negative);v[name]=unknown
        try:run(negative,v)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    for name in ('h253f','h237z'):
        v,_=model(norm);v[name]=unknown
        try:run(norm,v)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(competence_criterion_norm_table=table,actual_nonfreedom_and_negative_demand_independent=True,
        norm_does_not_execute_freedom_or_message=True,unknown_is_not_negation=True)


@lru_cache(None)
def identity_checks():
    doc=fixture();rows={}
    for category,fields in [('competence',('church','person','role','subject','message','rank','reference','point')),
        ('criterion',('church','person','role','subject','message','rank','reference','point')),
        ('source',('church','role','reference')),
        ('demand',('source','person','role','message','rank','bindings','reference','polarity','point'))]:
        for field in fields:
            variant=category+'_'+field;v,_=model(doc,(True,True,True),variant);result=run(doc,v)
            assert result==([False,True,True,True] if category in ('competence','criterion') else [True,False,False,False]),(variant,result)
            rows[variant]=result
    return dict(contrasts=rows,same_church_person_role_subject_message_reference_point=True,
        negative_polarity_required=True,distinct_norm_source_preserved=True)


@lru_cache(None)
def integration_checks():
    doc=fixture(integrated=True);rows={}
    for variant,bits,wanted in [('baseline',(True,False,True),True),('baseline',(True,True,True),False),
        ('baseline',(True,False,False),False),('no_commission_execution',(True,False,True),False),
        ('only_pupil_reached',(True,False,True),False),('not_internal',(True,False,True),False),
        ('demand_reference',(True,False,True),False),('source_church',(True,False,True),False)]:
        v,_=model(doc,bits,variant,True);result=run(doc,v,(*SMALL,'norm'));assert result==[wanted],(variant,bits,result)
        rows[variant+str(bits)]=result[0]
    quoted=deepcopy(catalog().document);quoted['statements']=[]
    declaration=catalog().entries['r44l']['declaration']
    sort={'kind':'function','parameters':[p['sort'] for p in declaration['parameters']],'result':'content'}
    quoted['declarations'].append(dict(kind='primitive',name='zshown',parameters=[{'kind':'description','result':sort,'rank':2}],result='truth'))
    quoted=parse(format_graph(quoted,'compact')+'q[k zshown[r c[p r44l]]].')
    v={d['name']:unknown for d in quoted['declarations'] if d['kind']=='primitive'}
    v['zshown']=lambda code:code.rank==2 and symbol(code)=='r44l'
    assert run(quoted,v)==[True]
    return dict(contrasts=rows,native_congregational_content_connected=True,rank_two_family_quote=True,
        no_normative_rejection_from_actual_nonfreedom_alone=True,no_exposition_execution_from_norm=True)


@lru_cache(None)
def structure_checks():
    old,dep,new=parent(),dependency(),catalog();previous=old.entries|dep.entries
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:assert e['declaration']==previous[n]['declaration'] and e['meaning_ja']==previous[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        t=format_graph(new.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==new.document
    for path in PRIORS:validate_hashes(ROOT,read(path)['source_sha256'])
    evidence=read(EVIDENCE)
    for p in evidence['pages']:assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    unit=next(u for u in read(evidence['source_inventory'])['units'] if u['id']==evidence['source']['unit'])
    s=evidence['source'];assert unit['text_sha256']==s['unit_sha256'] and unit['text'][slice(*s['range'])]==s['text']
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        existing_h237z_reused=True,no_source_sentence_added=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    results={}
    for name,fn in [('targets',target_checks),('independence',independence_checks),('identity',identity_checks),('integration',integration_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    evidence=read(EVIDENCE)
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,EVIDENCE,evidence['source_inventory'],*[p['path'] for p in evidence['pages']],
        'scripts/compose_delegated_teaching_freedom.py','scripts/check_delegated_teaching_freedom.py','tests/test_delegated_teaching_freedom.py',
        'scripts/check_congregational_private_use.py','scripts/check_teaching_policy.py','scripts/check_confessional_teaching.py','scripts/check_clerical_audiences.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_representative_teaching.py','scripts/compose_confessional_teaching.py',
        'scripts/compose_protected_remarks.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='same_teaching_freedom_actual_negation_and_normative_rejection',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
