"""Check shared voices, typed content, institutional recipient and possible outcomes."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_joint_petition import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_covenant_nullity import normalized
from scripts.check_single_ruler import role_checks

REPORT='reports/joint-petition-v1.json'
DOC='docs/joint-petition-v1.md'
READING='data/joint-petition-reading-v1.json'
PRIORS=('reports/single-ruler-v1.json','reports/public-insight-v1.json','reports/public-deliberation-v1.json')
DOMAIN=('p','q','outsider','group','community','ruler','act','secondact','method')
SCENES=('reference','candidate','anchor','success','failure','outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r z'+n+'[] d.' for n in SCENES)
EXTRA+='r zinner[] i[e].d zproposal[bindings j[a] reference d candidate d anchor d] e[b point[t[s[k zinner[]]][v point]]].'
ARGS='k zgroup[] k zcommunity[] k zruler[] r b[p zproposal] l[a][k zcommunity[] k zgroup[]] k zreference[] k zcandidate[] k zanchor[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(root,boundaries=('r2uj',)):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[root]),statements=[])
    query={'r5fw':'k zgroup[] k zcommunity[] k zreference[] k zcandidate[] k zanchor[]','r5fx':ARGS+' k zsuccess[]','r5fy':ARGS}[root]
    return parse(format_graph(doc,'compact')+EXTRA+'q[k '+root+'['+query+']].')
def run(doc,v):return evaluate(doc,v,DOMAIN,SCENES,True)

def model(doc,variant='baseline'):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    members=() if variant=='empty' else ('p',) if variant=='single' else ('p','q','outsider') if variant in ('outsider_member','all_citizens') else ('p','q')
    v['h26db']=lambda g,p,r,c,t:(g,r,c,t)==('group','reference','candidate','anchor') and p in members
    v['aa']=lambda p:p in ('p','q','outsider') and not(variant=='nonhuman_member' and p=='q')
    v['h26cu']=lambda p,c,r,h,t:(c,r,h,t)==('community','reference','candidate','anchor') and p in ('p','q','outsider') and not(variant=='outsider_member' and p=='outsider')
    v['r2uj']=lambda p,c,t:(p,c,t)==('ruler','community','success') and variant!='not_monarch'
    v['dg']=lambda a,t:a in ('act','secondact') and t=='success' and variant!='no_occurrence'
    v['h26dc']=lambda a,p,r,c,t:a in ('act','secondact') and(p,r,c,t)==('ruler','reference','candidate','success') and variant!='other_recipient'
    def participation(p,a,t):
        return p in members and a==('secondact' if variant=='separate_acts' and p=='q' else 'act') and t=='success' and not(variant=='missing_participant' and p=='q')
    v['df']=participation
    def voice(p,a,target,bindings,r,c,start,t):
        return participation(p,a,t) and symbol(target)=='zproposal' and target.rank==1 and normalized(bindings)==('community','group') and(r,c,start,t)==('reference','candidate','anchor','success') and not(variant=='missing_voice' and p=='q')
    v['h26dd']=voice
    v['h26de']=lambda g,m,r,c,t:(g,m,r,c,t)==('group','method','reference','candidate','anchor') and variant!='unavailable'
    v['h26df']=lambda g,m,r,c,start,t:(g,m,r,c,start)==('group','method','reference','candidate','anchor') and t in (() if variant=='empty_outcomes' else ('failure',) if variant=='only_failure' else ('success','failure'))
    v['h257z']=lambda r,c,t:(r,c)==('reference','candidate') and t in (('anchor','failure') if variant=='success_outside_history' else ('success','failure') if variant=='anchor_outside_history' else ('anchor','success','failure'))
    v['ic']=lambda a,b,c:c=='candidate' and ((a,b) in (('anchor','success'),('anchor','failure'),('success','failure')) or (variant=='cycle' and a=='success' and b=='anchor'))
    if variant=='changed_members_at_result':
        old=v['h26db'];v['h26db']=lambda g,p,r,c,t:old(g,p,r,c,t) or(t=='success' and p=='outsider')
    if variant=='result_only_members':v['h26db']=lambda g,p,r,c,t:t=='success' and p in ('p','q')
    return v

def unknown_checks(doc,names):
    for name in names:
        v=model(doc);v[name]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    return list(names)

@lru_cache(None)
def membership_checks():
    doc=fixture('r5fw');rows={}
    for variant in ('baseline','all_citizens','empty','single','outsider_member','nonhuman_member','changed_members_at_result','result_only_members'):
        actual=run(doc,model(doc,variant));assert actual==[variant in ('baseline','all_citizens','changed_members_at_result')],(variant,actual);rows[variant]=actual[0]
    return dict(anchored_plural_citizens=rows,unknown_rejected=unknown_checks(doc,('h26db','h26cu','aa')))

@lru_cache(None)
def submission_checks():
    doc=fixture('r5fx');rows={}
    for variant in ('baseline','all_citizens','empty','single','outsider_member','nonhuman_member','separate_acts','missing_participant','missing_voice','not_monarch','no_occurrence','other_recipient','changed_members_at_result'):
        actual=run(doc,model(doc,variant));assert actual==[variant in ('baseline','all_citizens','changed_members_at_result')],(variant,actual);rows[variant]=actual[0]
    # Position changes exercise shared identity, content rank, binding order and fixed context.
    contrasts={}
    for name,length in (('h26dd',8),('h26dc',5),('r2uj',3),('df',3)):
        for pos in range(length):
            v=model(doc);old=v[name]
            def changed(*a,old=old,pos=pos,name=name):
                if name=='h26dd' and pos==2:return False
                if name=='h26dd' and pos==3:return False
                a=list(a);a[pos]='outside' if isinstance(a[pos],str) and a[pos] in SCENES else 'outsider';return old(*a)
            v[name]=changed;actual=run(doc,v);assert actual==[False],(name,pos,actual);contrasts[name+'_'+str(pos)]=actual[0]
    # Query substitutions, rather than callbacks, verify the quoted family and sequence.
    for label,old,new in [('bindings_order','l[a][k zcommunity[] k zgroup[]]','l[a][k zgroup[] k zcommunity[]]'),('bindings_empty','l[a][k zcommunity[] k zgroup[]]','l[a][]')]:
        changed=parse(format_graph(doc,'compact').replace(old,new));actual=run(changed,model(changed));assert actual==[False];contrasts[label]=actual[0]
    return dict(shared_submission=rows,same_arguments=contrasts,proposal_body_not_executed=True,
        boundary='r2uj only; native institutional checks below',unknown_rejected=unknown_checks(doc,('df','dg','h26dc','h26dd','r2uj')))

@lru_cache(None)
def ability_checks():
    doc=fixture('r5fy');rows={}
    for variant in ('baseline','all_citizens','changed_members_at_result','unavailable','empty_outcomes','only_failure','success_outside_history','anchor_outside_history','cycle','result_only_members','missing_voice','not_monarch'):
        actual=run(doc,model(doc,variant));assert actual==[variant in ('baseline','all_citizens','changed_members_at_result')],(variant,actual);rows[variant]=actual[0]
    contrast={}
    for name,length in (('h26de',5),('h26df',6)):
        for pos in range(length):
            v=model(doc);old=v[name]
            def changed(*a,old=old,pos=pos):
                a=list(a);a[pos]='outside' if pos>=2 else 'outsider';return old(*a)
            v[name]=changed;actual=run(doc,v);assert actual==[False];contrast[name+'_'+str(pos)]=actual[0]
    return dict(available_possible_shared_submission=rows,same_method_and_outcome_context=contrast,
        mixed_success_and_failure_is_possible=True,native_xb_and_timeline=True,
        unknown_rejected=unknown_checks(doc,('h26de','h26df','h257z','ic')))

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(x for x in read(inv)['units'] if x['id']=='kant-1784:u0013')
    return dict(status='joint_petition_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1437,2309],text=u['text'][1437:2309]),
        adopted_readings=LIMITS,reuse=['rko/rkp shared-act construction','xb possible available method','r2uj monarch of the same community','h26cu current citizens'],
        remaining=['public insight sufficient for this proposal ability','protection and nonhindrance content','concession and throne metonymy in discourse','temporal milestone and whole attribution'],
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
    for n,f in [('membership',membership_checks),('submission',submission_checks),('ability',ability_checks),('native_monarch',role_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,reading_record()['source_inventory'],
        'scripts/compose_joint_petition.py','scripts/check_joint_petition.py','tests/test_joint_petition.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py','scripts/check_single_ruler.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='joint_petition_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
