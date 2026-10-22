"""Check religious arrangement identity, completed assent and unexecuted retention aims."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_congregational_choices import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_covenant_nullity import normalized

REPORT='reports/congregational-choices-v1.json'
DOC='docs/congregational-choices-v1.md'
READING='data/congregational-choices-reading-v1.json'
PRIORS=('reports/reform-proposals-v1.json','reports/joint-petition-v1.json')
DOMAIN=('p','q','community','congregation','field','subject','older','newer','agreement','actone','acttwo','other')
SCENES=('reference','candidate','before','anchor','after','comparison','outside')
POINTS=('before','anchor','after')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r z'+n+'[] d.' for n in SCENES)+'r zbindings[] j[a].'
FRAME='k zcommunity[] k zcongregation[] k zfield[] k zsubject[]'
CONTEXT='k zreference[] k zcandidate[] k zanchor[]'
BIND=('community','congregation','field','subject','newer')

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(root,query=None,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[root]),statements=[])
    if query is None:
        query={'r5fz':'q[k r5fz['+FRAME+' k zreference[]]].',
            'r5f3':'q[k r5f3['+FRAME+' k zolder[] k znewer[] '+CONTEXT+']].',
            'r5f4':'q[k r5f4[k zp[] k zactone[] k zagreement[] '+FRAME+' k znewer[] '+CONTEXT+' k zbefore[]]].',
            'r5f5':'q[k r5f5[k zagreement[] '+FRAME+' k zolder[] k znewer[] '+CONTEXT+']].',
            'r5f7':'q[k r5f7['+FRAME+' k zolder[] '+CONTEXT+']].'}[root]
    return parse(format_graph(doc,'compact')+EXTRA+query)
def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)

def model(doc,variant='baseline'):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['zbindings']=lambda:SequenceValue(BIND,'"individual"')
    v['h26dg']=lambda g,c,r:(g,c,r)==('congregation','community','reference')
    v['h246d']=lambda g,r:(g,r)==('congregation','reference')
    v['h245z']=lambda s,r:(s,r)==('subject','reference')
    v['h246h']=lambda g,target,r:(g,r)==('congregation','reference') and symbol(target)=='hzxi' and target.rank==0
    v['h246v']=lambda f,g,s,r:(f,g,s,r)==('field','congregation','subject','reference')
    v['h246c']=lambda g,p,t:g=='congregation' and p in (() if variant=='empty_congregation' else ('p','q')) and t in ('reference','anchor') and not(variant=='outside_member' and p=='q' and t=='anchor')
    v['aa']=lambda p:p in ('p','q') and not(variant=='nonhuman' and p=='q')
    v['h246w']=lambda i,f,r:i in ('older','newer') and(f,r)==('field','reference')
    def actual(i,f,t):
        if f!='field':return False
        if variant=='alias_only':return i in ('older','newer') and t=='anchor'
        return (i=='older' and t=='anchor' and variant!='old_not_current') or(i=='newer' and t=='comparison')
    v['h246x']=actual
    v['h26dh']=lambda g,f,r,t:(g,f,r,t)==('congregation','field','reference','comparison') and variant!='empty_comparisons'
    v['h26di']=lambda a,g,r,c,t:(a,g,r,c,t)==('agreement','congregation','reference','candidate','anchor') and variant!='private_agreement'
    v['h26dj']=lambda a,p,r,c,t:(a,r,c,t)==('agreement','reference','candidate','anchor') and p in (() if variant=='no_parties' else ('p',) if variant=='one_party' else ('p','q'))
    v['h26dk']=lambda a,target,bindings,r,c,t:normalized((a,target,bindings,r,c,t))==('agreement',('r5f2',0),BIND,'reference','candidate','anchor') and variant!='other_terms'
    v['dg']=lambda a,t:(a,t) in (('actone','before'),('acttwo','anchor')) and variant!='no_occurrence'
    v['f3']=lambda p,a,t:(p,a,t) in (('p','actone','before'),('q','acttwo','anchor')) and variant!='wrong_performer'
    v['h26dl']=lambda p,a,g,target,bindings,r,c,start,t:normalized((g,target,bindings,r,c,start))==('agreement',('r5f2',0),BIND,'reference','candidate','anchor') and(p,a,t) in (('p','actone','before'),('q','acttwo','anchor')) and not(variant=='missing_assent' and p=='q')
    v['h26dm']=lambda g,target,bindings,r,c,t:normalized((g,target,bindings,r,c,t))==('congregation',('r5f6',0),(*BIND[:-1],'older'),'reference','candidate','anchor') and variant!='no_retention_aim'
    v['h257z']=lambda r,c,t:(r,c)==('reference','candidate') and t in POINTS and not(variant=='missing_history' and t=='before')
    v['ic']=lambda a,b,c:c=='candidate' and a in POINTS and b in POINTS and(POINTS.index(a)<POINTS.index(b) or(variant=='cycle' and(a,b)==('anchor','before')))
    return v

def reject_unknown(doc,names):
    for n in names:
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return list(names)

@lru_cache(None)
def scope_change_checks():
    scope=fixture('r5fz');scope_rows={}
    for n in (None,'h26dg','h246d','h245z','h246h','h246v','h246c','aa'):
        v=model(scope)
        if n:v[n]=lambda *a:False
        actual=run(scope,v);assert actual==[n is None],(n,actual);scope_rows[n or 'baseline']=actual[0]
    doc=fixture('r5f3');rows={}
    for variant in ('baseline','alias_only','old_not_current','empty_comparisons','empty_congregation','nonhuman'):
        actual=run(doc,model(doc,variant));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(native_religious_community=scope_rows,changed_same_arrangement_content=rows,
        unknown_rejected=reject_unknown(doc,('h246x','h26dh')))

@lru_cache(None)
def state_binding_checks():
    query='q[t[k r5f2[k zbindings[] '+CONTEXT+']][k zafter[]]].'
    doc=fixture('r5f2',query,('r5fz',));rows=[]
    # Each slot can independently carry either marker. Test all 32 exact patterns
    # against all 32 offered bindings without enumerating a large individual domain.
    for expected in product(('alpha','beta'),repeat=5):
        accepted=[]
        for offered in product(('alpha','beta'),repeat=5):
            v=model(doc);v['zbindings']=lambda offered=offered:SequenceValue(offered,'"individual"')
            v['r5fz']=lambda c,g,f,s,r:(c,g,f,s)==expected[:4] and r=='reference'
            v['h246w']=lambda i,f,r:(i,f,r)==(expected[4],expected[2],'reference')
            v['h246x']=lambda i,f,t:(i,f,t)==(expected[4],expected[2],'after')
            actual=run(doc,v,('alpha','beta'));assert actual==[offered==expected];accepted.append(actual[0])
        assert sum(accepted)==1;rows.append(dict(expected=expected,accepted=sum(accepted)))
    v['r5fz']=lambda *a:True;v['h246w']=lambda *a:True;v['h246x']=lambda *a:True
    for bad in ((),('alpha',)*4,('alpha',)*6):
        v['zbindings']=lambda bad=bad:SequenceValue(bad,'"individual"');assert run(doc,v,('alpha','beta'))==[False]
    return dict(exact_five_positions=rows,offered_binding_cases=1024,wrong_lengths_rejected=True,
        boundary='r5fz checked natively in scope_change_checks')

@lru_cache(None)
def assent_checks():
    doc=fixture('r5f4');rows={}
    for variant in ('baseline','missing_history','cycle','no_occurrence','wrong_performer'):
        actual=run(doc,model(doc,variant));assert actual==[variant=='baseline'];rows[variant]=actual[0]
    positions={}
    for pos in range(9):
        v=model(doc);old=v['h26dl']
        def changed(*a,pos=pos):
            if pos in (3,4):return False
            a=list(a);a[pos]='outside' if pos>=5 else 'other';return old(*a)
        v['h26dl']=changed;actual=run(doc,v);assert actual==[False];positions[str(pos)]=actual[0]
    # Assent must not execute the agreed institutional arrangement.
    v=model(doc);v['h246x']=unknown;assert run(doc,v)==[True]
    return dict(past_same_act_and_person=rows,same_assent_arguments=positions,agreement_content_not_executed=True,
        unknown_rejected=reject_unknown(doc,('h26dl','dg','f3','h257z','ic')))

@lru_cache(None)
def agreement_checks():
    doc=fixture('r5f5');rows={}
    for variant in ('baseline','alias_only','old_not_current','empty_comparisons','private_agreement','no_parties','one_party','outside_member','other_terms','missing_assent','missing_history','cycle'):
        actual=run(doc,model(doc,variant));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    # A third congregation member need not be a party; unrelated future membership
    # does not repair an absent anchor party or an absent assent.
    v=model(doc);old=v['h246c'];v['h246c']=lambda g,p,t:old(g,p,t) or(g=='congregation' and p=='other' and t in ('reference','anchor'))
    v['aa']=lambda p:p in ('p','q','other');assert run(doc,v)==[True]
    v=model(doc);old=v['h26dl'];v['h26dl']=lambda p,a,g,target,b,r,c,start,t:old(p,a,g,target,b,r,c,start,t) and not(p=='q' and t=='anchor')
    assert run(doc,v)==[False]
    return dict(native_whole_agreement=rows,not_all_congregation_members_required=True,different_assent_times_supported=True,
        native_definitions_without_boundaries=True)

@lru_cache(None)
def retention_checks():
    doc=fixture('r5f7');rows={}
    for variant in ('baseline','no_retention_aim','old_not_current','empty_congregation'):
        v=model(doc,variant);v['h257z']=unknown
        actual=run(doc,v);assert actual==[variant=='baseline'];rows[variant]=actual[0]
    # Evaluate continuation separately: current truth alone cannot cover a later loss.
    query=''.join('q[t[k r5f6[k zbindings[] '+CONTEXT+']][k z'+p+'[]]].' for p in ('before','anchor','after','outside'))
    target=fixture('r5f6',query,('r5f2',));continuation={}
    for variant in ('all_future','future_loss','missing_history','cycle'):
        v=model(target,variant)
        from noema.constructed_semantics import Content
        v['r5f2']=lambda b,r,c,start:Content(SCENES,tuple(normalized(b)==BIND and(r,c,start)==('reference','candidate','anchor') and not(variant=='future_loss' and t=='after') for t in SCENES))
        actual=run(target,v);expected=[False,True,True,False] if variant in ('all_future','missing_history') else [False]*4
        assert actual==expected,(variant,actual);continuation[variant]=actual
    return dict(positive_retention_intention=rows,unexecuted_goal_can_fail_in_future=True,
        native_timeline_with_state_boundary=continuation,boundary='r5f2 checked separately in state_binding_checks')

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(x for x in read(inv)['units'] if x['id']=='kant-1784:u0013')
    return dict(status='congregational_choices_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1437,2309],text=u['text'][1437:2309]),
        adopted_readings=LIMITS,reuse=['r363 religious institution and domain','h246c full congregation membership','h246w/h246x arrangement and actual operation','mutual-undertakings temporal witness skeleton'],
        remaining=['personal better-insight grounds of the same assent','protection and nonhindrance of the same arrangement','public insight sufficient for proposal','temporal milestone and whole attribution'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    sources=parents();new=catalog();old={n:e for s in sources for n,e in s.entries.items()}
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record() and not new.document['statements'] and len(sources[0].document['statements'])==102
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=102)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('scope_change',scope_change_checks),('state_bindings',state_binding_checks),('assent',assent_checks),('agreement',agreement_checks),('retention',retention_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,reading_record()['source_inventory'],
        'scripts/compose_congregational_choices.py','scripts/check_congregational_choices.py','tests/test_congregational_choices.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='congregational_choices_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
