"""Check the same resolutions, active repudiation and all later persons' rights."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_posterity_repudiation import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure,NAMES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/posterity-repudiation-v1.json'
DOC='docs/posterity-repudiation-v1.md'
READING='data/posterity-repudiation-reading-v1.json'
PRIORS=('reports/cohort-covenant-denial-v1.json','reports/epoch-undertakings-v1.json',
        'reports/cohort-normative-denial-v1.json','reports/civic-levy-refusal-v1.json')
TRIPLE=('person','agreement','resolution')
DOMAIN=tuple(dict.fromkeys((*NAMES,*TRIPLE,'response','other','alpha','beta','gamma','role','source')))
SCENES=('reference','candidate','anchor','later','farther','outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)
ARGS=' '.join('k z'+n+'[]' for n in NAMES)
TARGS=' '.join('k z'+n+'[]' for n in TRIPLE)

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
def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)
def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update({'zt'+n:lambda n=n:n for n in SCENES})
    v.update(h26av=lambda:'reference',h26ax=lambda:'source',h26bm=lambda:'role',h254z=lambda a:'anchor')
    return v
def unknown_rejected(doc,model,names,domain=DOMAIN):
    for name in names:
        v=model();v[name]=unknown
        try:run(doc,v,domain)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    return list(names)

def refusal_model(doc,variant='baseline'):
    v=base(doc)
    v['h26bk']=lambda a,r,t:variant!='unadopted' and (a,r,t)==('other' if variant=='other_agreement' else 'agreement','resolution','anchor')
    v['h26bn']=lambda r,p,a,d,t:(r,p,a,d,t)==('other' if variant=='other_response' else 'response',
        'other' if variant=='other_person' else 'person','agreement',
        'other' if variant=='other_resolution' else 'resolution','outside' if variant=='other_reference' else 'reference')
    v['cg']=lambda p,r,t:variant!='no_action' and(p,r,t)==('person','response','later')
    def stance(p,r,c,b,sign,t):
        return variant!='no_stance' and(p,r,symbol(c),c.rank,tuple(b.items),sign,t)==('person',
            'other' if variant=='other_stance_action' else 'response','r5dp',0,
            tuple(reversed(TRIPLE)) if variant=='other_stance_bindings' else TRIPLE,
            variant=='positive_stance','outside' if variant=='other_stance_point' else 'later')
    v['h244j']=stance
    return v

@lru_cache(None)
def refusal_checks():
    doc=fixture(('r5dq',),'q[k r5dq['+TARGS+' k zresponse[] k ztlater[]]].');rows={}
    for variant in ('baseline','unadopted','other_agreement','other_response','other_person','other_resolution',
                    'other_reference','no_action','no_stance','other_stance_action','other_stance_bindings','positive_stance','other_stance_point'):
        v=refusal_model(doc,variant);actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual)
        assert v['h26bl'] is unknown;rows[variant]=actual[0]
    rejected=unknown_rejected(doc,lambda:refusal_model(doc),('h26bk','h26bn','cg','h244j'))
    # Exercise the existential choice natively, including its response variable.
    doc=fixture(('r5dr',),'q[t[k r5dr[l[a]['+TARGS+']]][k ztlater[]]].')
    for variant in ('baseline','no_action','positive_stance'):
        assert run(doc,refusal_model(doc,variant),(*TRIPLE,'response','other'))==[variant=='baseline']
    return dict(native_refusal_contrasts=rows,unknown_rejected=rejected,acceptance_truth_not_evaluated=True,
                native_existential_response=True)

def epoch_model(doc,variant='baseline'):
    v=base(doc);history=('anchor','later','farther')
    v.update(zperson=lambda:'beta',zearlier=lambda:'alpha')
    v['h257z']=lambda r,c,t:(r,c)==('reference','candidate') and t in history and not(variant=='uncovered_point' and t=='later')
    v['ic']=lambda a,b,c:c=='candidate' and a in history and b in history and history.index(a)<history.index(b)
    v['h26aa']=lambda e,r:r=='reference' and e in ('alpha','beta','gamma')
    v['h26ab']=lambda e,r,c,t:(r,c)==('reference','candidate') and(e,t) in (('alpha','anchor'),('beta','later'),('gamma','farther'))
    v['aa']=lambda p:variant!='nonhuman' and p in ('alpha','beta')
    v['h256o']=lambda p,c,t:variant!='dead' and c=='candidate' and (p,t) in (('alpha','anchor'),('alpha','farther'),('beta','later'),('beta','farther'))
    if variant=='uncatalogued_earlier':
        v['zearlier']=lambda:'gamma'
        v['h26ab']=lambda e,r,c,t:(r,c)==('reference','candidate') and(e,t) in (('alpha','anchor'),('beta','later'),('gamma','farther'))
        v['h26aa']=lambda e,r:r=='reference' and e in ('alpha','beta')
    return v

@lru_cache(None)
def scope_checks():
    rows={};small=('alpha','beta','gamma')
    for point in ('anchor','later','farther','outside'):
        doc=fixture(('r5ds',),'q[k r5ds[k zperson[] k zearlier[] k ztcandidate[] k zt'+point+'[]]].')
        actual=run(doc,epoch_model(doc),small);assert actual==[point in ('later','farther')],(point,actual);rows[point]=actual[0]
    doc=fixture(('r5ds',),'q[k r5ds[k zperson[] k zearlier[] k ztcandidate[] k ztfarther[]]].')
    for variant in ('dead','nonhuman','uncovered_point','uncatalogued_earlier'):
        actual=run(doc,epoch_model(doc,variant),small);assert actual==[False],(variant,actual);rows[variant]=actual[0]
    v=epoch_model(doc);v['zperson']=lambda:'alpha';assert run(doc,v,small)==[True]
    rejected=unknown_rejected(doc,lambda:epoch_model(doc),('h26aa','h26ab','h257z','h256o','ic'),small)
    return dict(native_three_epoch_scope=rows,earlier_survivor_included=True,unknown_rejected=rejected,
                no_genealogy_or_immediate_successor_restriction=True)

@lru_cache(None)
def norm_checks():
    doc=fixture(('r5dt',),'q[k r5dt['+TARGS+' k ztlater[]]].');rows={};contrasts={}
    target=('source','person','role','r5dr',0,TRIPLE,True,'later')
    def normalized(a):
        s,p,r,c,b,sign,t=a
        return s,p,r,symbol(c),c.rank,tuple(b.items),sign,t
    for permit,oppose in product((False,True),repeat=2):
        v=base(doc);v['h7l']=lambda *a:permit and normalized(a)==target
        v['h7k']=lambda *a:oppose and normalized(a)==(*target[:6],False,'later')
        actual=run(doc,v);assert actual==[permit and not oppose];rows[str((permit,oppose))]=actual[0]
        assert all(v[n] is unknown for n in ('h26bl','h26bk','h26bn','cg','h244j'))
    for i,key in enumerate(('source','person','role','code','rank','bindings','polarity','point')):
        other=list(target);other[i]=(tuple(reversed(TRIPLE)) if i==5 else 1 if i==4 else False if i==6 else 'other')
        v=base(doc);v['h7l']=lambda *a:normalized(a)==tuple(other);v['h7k']=lambda *a:False
        actual=run(doc,v);assert actual==[False];contrasts[key]=False
    def model():
        v=base(doc);v['h7l']=lambda *a:True;v['h7k']=lambda *a:False;return v
    return dict(permission_and_opposition=rows,exact_target_contrasts=contrasts,
        unknown_rejected=unknown_rejected(doc,model,('h7l','h7k')),quoted_refusal_not_executed=True)

@lru_cache(None)
def universal_checks():
    doc=fixture(('r5du',),'q[k r5du['+ARGS+' k ztcandidate[]]].',('r5dc','r5ds','r5dt'));rows={}
    for variant in ('baseline','no_candidate','no_decisions','denied_first','denied_second','denied_farther_person','denied_outsider','denied_other_decision'):
        v=base(doc);v['r5dc']=lambda *a:variant!='no_candidate' and a==(*NAMES,'candidate')
        v['r5ds']=lambda p,e,c,t:(e,c)==('earlier','candidate') and(p,t) in (('alpha','later'),('beta','farther'))
        v['h26bk']=lambda a,r,t:variant!='no_decisions' and(a,t)==('agreement','anchor') and r in ('alpha','beta')
        def entitled(p,a,r,t):
            denied={'denied_first':('alpha','agreement','alpha','later'),'denied_second':('alpha','agreement','beta','later'),
                'denied_farther_person':('beta','agreement','beta','farther'),'denied_outsider':('other','agreement','alpha','later'),
                'denied_other_decision':('alpha','agreement','other','later')}.get(variant)
            return (p,a,r,t)!=denied
        v['r5dt']=entitled
        actual=run(doc,v);want=variant in ('baseline','denied_outsider','denied_other_decision')
        assert actual==[want],(variant,actual);rows[variant]=actual[0]
    return dict(all_people_decisions_and_points=rows,boundaries=['r5dc','r5ds','r5dt'])

@lru_cache(None)
def binding_checks():
    matrices={};lengths={}
    for root,boundary,names in (('r5dp','h26bl',TRIPLE),('r5dr','r5dq',TRIPLE),('r5dv','r5du',NAMES)):
        def case(selected,expected,length=0):
            ns=names[:-1] if length==-1 else (*names,names[-1]) if length==1 else names
            seq='l[a]['+' '.join('k z'+n+'[]' for n in ns)+']'
            doc=fixture((root,),'q[t[k '+root+'['+seq+']][k ztlater[]]].',() if boundary=='h26bl' else (boundary,))
            v=base(doc);v.update({'z'+n:lambda i=i:'beta' if i==selected else 'alpha' for i,n in enumerate(names)})
            wanted=tuple('beta' if i==expected else 'alpha' for i in range(len(names)))
            if root=='r5dp':v[boundary]=lambda *a:a==(*wanted,'reference','later')
            elif root=='r5dr':v[boundary]=lambda *a:a==(*wanted,'alpha','later')
            else:v[boundary]=lambda *a:a==(*wanted,'later')
            return run(doc,v,('alpha','beta'))[0]
        matrix=[]
        for selected,expected in product(range(len(names)),repeat=2):
            actual=case(selected,expected);assert actual==(selected==expected);matrix.append(actual)
        assert not case(0,0,-1) and not case(0,0,1)
        matrices[root]=matrix;lengths[root]=dict(short=False,long=False)
    return dict(exact_position_matrices=matrices,wrong_lengths=lengths,boundaries=['r5dq','r5du'],acceptance_adapter_native=True)

@lru_cache(None)
def integrated_checks():
    doc=fixture(('r5du',),'q[k r5du['+ARGS+' k ztcandidate[]]].',('r5dc',));rows={}
    chosen=('alpha','beta','alpha','beta','alpha','alpha');small=('alpha','beta','gamma')
    for variant in ('baseline','no_decisions','denied_later','denied_farther','opposed_farther','denied_survivor'):
        v=epoch_model(doc);v.update({'z'+n:lambda value=value:value for n,value in zip(NAMES,chosen)})
        v.update(h26ax=lambda:'alpha',h26bm=lambda:'gamma')
        v['r5dc']=lambda *a:a==(*chosen,'candidate')
        v['h26bk']=lambda a,r,t:variant!='no_decisions' and a=='alpha' and r in ('alpha','beta') and t=='anchor'
        def match(s,p,r,c,b,sign,t):
            return (s,r,symbol(c),c.rank,sign)==('alpha','gamma','r5dr',0,True) and tuple(b.items) in ((p,'alpha','alpha'),(p,'alpha','beta'))
        def permission(*a):
            denied={'denied_later':('beta','later'),'denied_farther':('beta','farther'),'denied_survivor':('alpha','farther')}.get(variant)
            return match(*a) and (a[1],a[-1])!=denied
        v['h7l']=permission
        v['h7k']=lambda s,p,r,c,b,sign,t:variant=='opposed_farther' and not sign and match(s,p,r,c,b,True,t) and(p,t)==('beta','farther')
        actual=run(doc,v,small);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert all(v[n] is unknown for n in ('h26bl','h26bn','h244j','cg'))
    return dict(native_three_epochs_and_rdu=rows,boundary='r5dc candidate only; its native evidence is pinned in prior report',
                refusal_not_executed=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='posterity_repudiation_entitlement_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1005,1264],text=u['text'][1005:1264]),
        primary_page=read('data/covenant-question-reading-v1.json')['original_page'],adopted_readings=LIMITS,
        remaining=['同じ拘束の仮定と人間本性への犯罪','本来的使命が同じ進展にあることとgerade',
                   'alsoの理由付けとvollkommenの全面性','採択された同じ決議へのunbefugter/frevelhafterの二評価',
                   '著者帰属・全文接続・通読'],new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    new,old=catalog(),parent()
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record();page=read(READING)['primary_page'];assert digest((ROOT/page['path']).read_bytes())==page['sha256']
    assert not new.document['statements'] and len(old.document['statements'])==100
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=100)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('refusal',refusal_checks),('scope',scope_checks),('norm',norm_checks),('universal',universal_checks),
                ('bindings',binding_checks),('integrated',integrated_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,read(READING)['source_inventory'],read(READING)['primary_page']['path'],
        'scripts/compose_posterity_repudiation.py','scripts/check_posterity_repudiation.py','tests/test_posterity_repudiation.py',
        'scripts/compose_cohort_covenant_purpose.py','scripts/compose_protected_remarks.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='posterity_same_resolutions_repudiation_entitlement_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
