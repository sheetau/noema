"""Check complete communication freedom, distinct calling and exact targets."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_scholarly_mission import ROOT,LIBRARY,BASIS,NAMES,POLICY,THOUGHT,PROPOSAL,PRIMITIVES,MEANINGS,parents,build,closure
from scripts.compose_qualitative_influence import TRUE,FALSE
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/scholarly-mission-v1.json'
DOC='docs/scholarly-mission-v1.md'
PRIOR=('reports/creed-opinions-v1.json','reports/reform-proposals-v1.json')
TIMES=('reference','early','late','outside')
DOMAIN=('x','y')
EXTRA='r zx[] a.r zy[] a.r zref[] d.r zpoint[] d.'
BOUNDARIES=('r36v','r364','r36x','r366','r36y','r367')


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def boundary(doc,names):
    for d in doc['declarations']:
        if d['name'] in names:
            d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')


@lru_cache(None)
def fixture():
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,['r37l','r37h']),statements=[])
    boundary(doc,BOUNDARIES)
    args=' '.join('k zx[]' for _ in NAMES)+' k zref[]'
    query=''.join('q[t[k '+n+'['+args+']][k zpoint[]]].' for n in ('r37j','r37k','r37l'))
    query+='q[t[k r37h['+' '.join('k zx[]' for _ in POLICY)+' k zref[]]][k zpoint[]]].'
    return parse(format_graph(doc,'compact')+EXTRA+query)


def model(variant='baseline',bits=(True,False,True)):
    doc=fixture();v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    allowed,banned,called=bits
    v.update(zx=lambda:'x',zy=lambda:'y',zref=lambda:'reference',zpoint=lambda:'late')
    def thought(person,item,judgment,beneficiary,creed,ref):
        return variant!='no_items' and item in DOMAIN and (person,judgment,beneficiary,creed,ref)==('x','x','x','x','reference')
    def proposal(person,item,church,field,subject,older,newer,standard,ref):
        return variant!='no_items' and item in DOMAIN and (person,church,field,subject,older,newer,standard,ref)==('x',)*7+('reference',)
    def candidate(kind,values):
        fields=dict(zip(THOUGHT if kind=='thought' else PROPOSAL,values[:-1]));ref=values[-1]
        if variant=='no_candidates' or variant=='missing_candidate' and fields['thought' if kind=='thought' else 'proposal']=='y':return False
        actual=(thought(fields['person'],fields['thought'],fields['judgment'],fields['beneficiary'],fields['creed'],ref) if kind=='thought' else
            proposal(fields['person'],fields['proposal'],fields['church'],fields['field'],fields['subject'],fields['older'],fields['newer'],fields['standard'],ref))
        return actual and fields['scholar']==fields['audience']=='x' and fields['activity'] in DOMAIN
    def delivered(kind,*values):
        fields=dict(zip(THOUGHT if kind=='thought' else PROPOSAL,values[:-1]));item=fields['thought' if kind=='thought' else 'proposal']
        when='early' if item=='x' else 'outside' if variant=='outside_period' else 'late'
        valid=candidate(kind,values) and fields['activity']==item and variant!='no_execution'
        if variant=='missing_thought' and kind=='thought' and item=='y':valid=False
        if variant=='missing_proposal' and kind=='proposal' and item=='y':valid=False
        return Content(TIMES,tuple(valid and at==when for at in TIMES))
    def correct(source,person,role,code,bindings,ref,point):
        return (source,person,role,code.rank,ref,point)==('x','x','x',1,'reference','late')
    def permission(source,person,role,code,bindings,ref,sign,point):
        if not correct(source,person,role,code,bindings,ref,point) or not sign:return False
        if symbol(code) not in ('r37a','r37b'):return False
        items=tuple(bindings.items)
        if variant=='one_unpermitted' and items[1]=='y' and items[4]=='y':return False
        return allowed
    def requirement(source,person,role,code,bindings,ref,sign,point):
        if not correct(source,person,role,code,bindings,ref,point):return False
        if symbol(code)=='r37i':return called and sign and tuple(bindings.items)==('x',)*6
        if symbol(code) not in ('r37a','r37b') or sign:return False
        return banned or variant=='one_banned' and tuple(bindings.items)[1]=='y'
    def history(frame,candidate,at):return (frame,candidate)==('x','late') and at in ('early','late','outside')
    def period(frame,candidate,at):
        return variant!='empty_period' and (frame,candidate)==('x','late') and at in (('early','outside') if variant=='gapped_period' else ('early','late'))
    def order(first,last,candidate):
        return candidate=='late' and (TIMES.index(first)<TIMES.index(last) or variant=='cyclic' and (first,last)==('late','early'))
    v.update(r36v=thought,r364=proposal,r36x=lambda *values:candidate('thought',values),r366=lambda *values:candidate('proposal',values),
        r36y=lambda *values:delivered('thought',*values),r367=lambda *values:delivered('proposal',*values),
        h247b=lambda p,r,ref:'x',h247c=lambda p,r,ref:'x',h245c=permission,h237z=requirement,h7q=history,h7r=period,ic=order)
    return v


@lru_cache(None)
def scope_checks():
    rows={}
    for variant,expected in [('baseline',[True]*4),('one_unpermitted',[False,True,False,True]),('one_banned',[False,True,False,True]),
        ('missing_candidate',[False,True,False,False]),('no_candidates',[False,True,False,False]),
        ('no_execution',[True,True,True,False]),('missing_thought',[True,True,True,False]),('missing_proposal',[True,True,True,False]),
        ('outside_period',[True,True,True,False]),('empty_period',[True,True,True,False]),('gapped_period',[True,True,True,False]),
        ('cyclic',[True,True,True,False]),('no_items',[True]*4)]:
        actual=evaluate(fixture(),model(variant),DOMAIN,TIMES,True)
        assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(contrasts=rows,all_candidates_and_both_item_classes_checked=True,
        different_items_may_be_communicated_at_different_times=True,no_extra_items_required_when_scope_empty=True,
        boundaries=list(BOUNDARIES),boundary_evidence=list(PRIOR))


@lru_cache(None)
def independence_checks():
    rows=[]
    for bits in product((False,True),repeat=3):
        free=bits[0] and not bits[1]
        actual=evaluate(fixture(),model(bits=bits),DOMAIN,TIMES,True)
        assert actual==[free,bits[2],free and bits[2],True],(bits,actual)
        rows.append(dict(allowed=bits[0],banned=bits[1],called=bits[2],results=actual))
    doc=deepcopy(fixture());doc['statements']=doc['statements'][:3]
    v=model()
    for n in ('r36y','r367','h7q','h7r','ic'):v[n]=unknown
    assert evaluate(doc,v,DOMAIN,TIMES,True)==[True]*3
    return dict(truth_table=rows,calling_and_freedom_independent=True,quoted_mission_not_executed=True)


@lru_cache(None)
def adapter(target,bindings):
    mapping={'r37a':('r36y',THOUGHT),'r37b':('r367',PROPOSAL),'r37i':('r37h',POLICY)}
    inner,names=mapping[target];doc=deepcopy(catalog().document)
    doc.update(declarations=closure(doc,[target]),statements=[]);boundary(doc,[inner])
    seq='l[a]['+' '.join('k z'+n+'[]' for n in bindings)+']'
    return parse(format_graph(doc,'compact')+EXTRA+'q[t[k '+target+'['+seq+' k zref[]]][k zpoint[]]].'),inner,names


@lru_cache(None)
def binding_checks():
    result={}
    for target,names in [('r37a',THOUGHT),('r37b',PROPOSAL),('r37i',POLICY)]:
        for position in range(len(names)):
            inputs=tuple('x' if i==position else 'y' for i in range(len(names)))
            doc,inner,_=adapter(target,inputs);v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
            v.update(zx=lambda:'x',zy=lambda:'y',zref=lambda:'reference',zpoint=lambda:'late')
            v[inner]=lambda *args:Content(TIMES,tuple(args==(*inputs,'reference') for _ in TIMES))
            assert evaluate(doc,v,DOMAIN,TIMES,True)==[True],(target,position)
        for count in (0,len(names)-1,len(names)+1):
            doc,inner,_=adapter(target,('x',)*count);v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
            v.update(zx=lambda:'x',zy=lambda:'y',zref=lambda:'reference',zpoint=lambda:'late')
            v[inner]=lambda *args:Content(TIMES,(True,)*4)
            assert evaluate(doc,v,DOMAIN,TIMES,True)==[False],(target,count)
        result[target]=dict(independent_positions=len(names),wrong_lengths=[0,len(names)-1,len(names)+1])
    return result


@lru_cache(None)
def norm_identity_checks():
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,['r37c','r37k','r37a']),statements=[])
    labels=tuple(dict.fromkeys(('source','role',*THOUGHT,*POLICY,'other')))
    extra=''.join('r z'+n+'[] a.' for n in labels)+'r zref[] d.r zpoint[] d.'
    extra+='d zalias[bindings j[a] reference d] e[k r37a[v bindings v reference]].'
    b='l[a]['+' '.join('k z'+n+'[]' for n in THOUGHT)+']'
    query='q[k r37c[k zsource[] k zperson[] k zrole[] r b[p r37a] '+b+' k zref[] k zpoint[]]].'
    query+='q[t[k r37k['+' '.join('k z'+n+'[]' for n in NAMES)+' k zref[]]][k zpoint[]]].'
    doc=parse(format_graph(doc,'compact')+extra+query)
    def values(variant):
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        for n in labels:v['z'+n]=lambda n=n:n
        v.update(zref=lambda:'reference',zpoint=lambda:'late',h247b=lambda *args:'source',h247c=lambda *args:'frame')
        def matches(args,prefix,calling=False):
            source,person,role,code,bindings,ref,sign,point=args
            expected=['source','person','scholar' if calling else 'role','r37i' if calling else 'r37a',1,
                tuple(POLICY if calling else THOUGHT),'reference',True,'late']
            fields=('source','person','role','description','rank','bindings','reference','sign','point')
            for i,f in enumerate(fields):
                if variant==prefix+'_'+f:expected[i]=not expected[i] if f=='sign' else 'other'
            for i,n in enumerate(POLICY if calling else THOUGHT):
                if variant==prefix+'_binding_'+n:
                    expected[5]=tuple('other' if j==i else x for j,x in enumerate(expected[5]))
            return (source,person,role,symbol(code),code.rank,tuple(bindings.items),ref,sign,point)==tuple(expected)
        v['h245c']=lambda *args:matches(args,'permission')
        v['h237z']=lambda *args:matches(args,'calling',True) if symbol(args[3])=='r37i' else False
        return v
    rows={}
    for prefix,names in [('permission',THOUGHT),('calling',POLICY)]:
        for field in ('source','person','role','description','rank','bindings','reference','sign','point',*('binding_'+n for n in names)):
            variant=prefix+'_'+field;actual=evaluate(doc,values(variant),labels,TIMES,True)
            assert actual==([False,True] if prefix=='permission' else [True,False]),(variant,actual)
            rows[variant]=actual
    assert evaluate(doc,values('baseline'),labels,TIMES,True)==[True,True]
    return dict(contrasts=rows,description_rank_bindings_reference_and_polarity_preserved=True)


@lru_cache(None)
def structure_checks():
    new=catalog();old={n:e for p in parents() for n,e in p.entries.items()}
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for path in PRIOR:validate_hashes(ROOT,read(path)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    rejected=[]
    for n in ('r36v','r364','r36x','r366','h245c','h237z','h247b','h247c','h7q','h7r','ic'):
        v=model();v[n]=unknown
        try:evaluate(fixture(),v,DOMAIN,TIMES,True)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
        rejected.append(n)
    return dict(new_primitives=len(PRIMITIVES),new_definitions=len(MEANINGS),inherited_meanings_preserved=True,
        roundtrips=True,unknown_relations_rejected=rejected,new_semantic_reviews=0)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    results={}
    for name,fn in [('scope',scope_checks),('independence',independence_checks),('bindings',binding_checks),('norm_identity',norm_identity_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set().union(*(set(p.source_sha256) for p in parents()))|set(PRIOR)|{DOC,
        'scripts/compose_scholarly_mission.py','scripts/check_scholarly_mission.py','tests/test_scholarly_mission.py',
        'scripts/compose_creed_opinions.py','scripts/compose_reform_proposals.py','scripts/compose_protected_remarks.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='all_qualified_communication_freedom_and_distinct_calling',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
