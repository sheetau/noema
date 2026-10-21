"""Verify vocation content, grave normative qualification and hypothetical scope."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_human_vocation_offense import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure,NAMES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/human-vocation-offense-v1.json'
DOC='docs/human-vocation-offense-v1.md'
READING='data/human-vocation-offense-reading-v1.json'
PRIORS=('reports/cohort-covenant-denial-v1.json','reports/cohort-progress-options-v1.json',
        'reports/cohort-covenant-purpose-v1.json','reports/posterity-repudiation-v1.json')
DOMAIN=(*NAMES,'nature','vocation','source','role','other','alpha','beta')
SCENES=('reference','candidate','first','last','outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)
ARGS=' '.join('k z'+n+'[]' for n in NAMES)
SIX='l[a]['+ARGS+']'
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
    v.update(h26av=lambda:'reference',h26ax=lambda:'source',h26ay=lambda:'role')
    return v
def rejected(doc,model,names,domain=DOMAIN):
    for name in names:
        v=model();v[name]=unknown
        try:run(doc,v,domain)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    return list(names)

def vocation_model(doc,variant='baseline',nature='nature',vocation='vocation'):
    v=base(doc)
    v['h26bo']=lambda n,k,r:variant!='not_human_nature' and(n,symbol(k),k.rank,r)==(nature,'aa',0,'reference')
    v['h26bp']=lambda n,b,r:variant!='no_vocation' and(n,b,r)==(nature,vocation,'reference')
    v['h26bq']=lambda n,b,r:variant!='acquired_only' and(n,b,r)==(nature,'other' if variant=='different_original_vocation' else vocation,'reference')
    v['h26br']=lambda b,c,r:variant!='no_content_identity' and(b,symbol(c),c.rank,r)==(vocation,
        'r5db' if variant=='wrong_development' else 'r5dw',0,'outside' if variant=='different_reference' else 'reference')
    return v

@lru_cache(None)
def vocation_checks():
    doc=fixture(('r5dx',),'q[k r5dx[k znature[] k zvocation[]]].');rows={}
    for variant in ('baseline','not_human_nature','no_vocation','acquired_only','different_original_vocation',
                    'no_content_identity','wrong_development','different_reference'):
        v=vocation_model(doc,variant);actual=run(doc,v);assert actual==[variant=='baseline'];rows[variant]=actual[0]
        for name in ('aa','h256o','h226u'):assert v[name] is unknown
    return dict(native_vocation_contrasts=rows,progress_not_executed=True,
        unknown_rejected=rejected(doc,lambda:vocation_model(doc),('h26bo','h26bp','h26bq','h26br')))

@lru_cache(None)
def progress_checks():
    doc=fixture(('r5dw',),'q[t[k r5dw[k znextgroup[] k ztfirst[] k ztlast[]]][k ztcandidate[]]].',('r5cr',));rows={}
    target=('nextgroup','reference','candidate','first','last')
    for i in range(-1,5):
        v=base(doc);expected=list(target)
        if i>=0:expected[i]='other' if i==0 else 'outside'
        v['r5cr']=lambda *a:a==tuple(expected)
        actual=run(doc,v);assert actual==[i==-1];rows[str(i)]=actual[0]
    return dict(same_group_reference_history_and_ordered_points=rows,
        boundary='r5cr; native progress semantics are pinned in cohort-progress-options-v1',
        no_knowledge_implies_autonomy_rule=True)

def offense_model(doc,variant='baseline',names=NAMES,nature='nature',vocation='vocation',source='source',role='role'):
    v=vocation_model(doc,variant,nature,vocation)
    v.update(h26ax=lambda:source,h26ay=lambda:role)
    v['h26bs']=lambda n,s,r:variant!='no_ground' and(n,s,r)==(nature,source,'reference')
    def demand(s,p,r,c,b,sign,t):
        return variant!='no_prohibition' and(s,p,r,symbol(c),c.rank,tuple(b.items),sign,t)==(source,names[0],role,'r5db',0,names,variant=='positive_requirement','candidate')
    v['h7k']=demand
    def grave(s,n,p,r,c,b,ref,t):
        target=[source,nature,names[0],role,'r5db',0,names,'reference','candidate']
        keys=('source','protected','bearer','role','conduct','rank','bindings','reference','point')
        for i,key in enumerate(keys):
            if variant=='other_'+key:target[i]=tuple(reversed(names)) if i==6 else 1 if i==5 else 'other'
        return variant!='not_grave' and(s,n,p,r,symbol(c),c.rank,tuple(b.items),ref,t)==tuple(target)
    v['h26bt']=grave
    return v

@lru_cache(None)
def offense_checks():
    doc=fixture(('r5dy',),'q[k r5dy[k znature[] k zvocation[] '+ARGS+' k ztcandidate[]]].');rows={}
    variants=('baseline','no_ground','no_prohibition','positive_requirement','not_grave','acquired_only')+tuple(
        'other_'+n for n in ('source','protected','bearer','role','conduct','rank','bindings','reference','point'))
    for variant in variants:
        v=offense_model(doc,variant);actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        for n in ('h255a','h26at','h26as','h26am'):assert v[n] is unknown
    return dict(same_norm_ground_conduct_and_protected_nature=rows,formation_and_goal_not_executed=True,
        unknown_rejected=rejected(doc,lambda:offense_model(doc),('h26bs','h7k','h26bt')))

@lru_cache(None)
def binding_checks():
    matrices={};lengths={};small=('alpha','beta')
    for root in ('r5dz','r5d2'):
        def case(selected,expected,length=0):
            ns=NAMES[:-1] if length==-1 else (*NAMES,NAMES[-1]) if length==1 else NAMES
            seq='l[a]['+' '.join('k z'+n+'[]' for n in ns)+']'
            boundaries=('r5dy',) if root=='r5dz' else ('r5db','r5dz')
            doc=fixture((root,),'q[t[k '+root+'['+seq+']][k ztcandidate[]]].',boundaries);v=base(doc)
            v.update({'z'+n:lambda i=i:'beta' if i==selected else 'alpha' for i,n in enumerate(NAMES)})
            wanted=tuple('beta' if i==expected else 'alpha' for i in range(6))
            if root=='r5dz':v['r5dy']=lambda n,b,*a:(n,b)==('alpha','beta') and a==(*wanted,'candidate')
            else:
                v['r5db']=lambda bs:Content(SCENES,tuple(True for _ in SCENES))
                v['r5dz']=lambda bs:Content(SCENES,tuple(tuple(bs.items)==wanted and t=='candidate' for t in SCENES))
            return run(doc,v,small)[0]
        matrix=[]
        for selected,expected in product(range(6),repeat=2):
            actual=case(selected,expected);assert actual==(selected==expected);matrix.append(actual)
        assert not case(0,0,-1) and not case(0,0,1)
        matrices[root]=matrix;lengths[root]=dict(short=False,long=False)
    return dict(six_position_matrices=matrices,wrong_lengths=lengths,boundaries=['r5dy','r5db','r5dz'])

@lru_cache(None)
def conditional_checks():
    doc=fixture(('r5d2',),'q[t[k r5d2['+SIX+']][k ztcandidate[]]].',('r5db','r5dz'));rows={};small=('alpha','beta')
    for formed,wrong in product((False,True),repeat=2):
        v=base(doc);v.update({'z'+n:lambda:'alpha' for n in NAMES})
        v['r5db']=lambda b:Content(SCENES,tuple(formed for _ in SCENES))
        v['r5dz']=lambda b:Content(SCENES,tuple(wrong for _ in SCENES))
        actual=run(doc,v,small);assert actual==[not formed or wrong];rows[str((formed,wrong))]=actual[0]
    doc=fixture(('r5d3',),'q[t[k r5d3[]][k ztcandidate[]]].',('r5dc','r5d2'));universal={}
    left,right=('alpha',)*6,('beta',)*6
    for in_left,in_right,good_left,good_right in product((False,True),repeat=4):
        v=base(doc);v['r5dc']=lambda *a:(a==(*left,'candidate') and in_left) or(a==(*right,'candidate') and in_right)
        v['r5d2']=lambda b:Content(SCENES,tuple((tuple(b.items)==left and good_left) or(tuple(b.items)==right and good_right) for _ in SCENES))
        actual=run(doc,v,small);assert actual==[(not in_left or good_left) and(not in_right or good_right)]
        universal[str((in_left,in_right,good_left,good_right))]=actual[0]
    return dict(conditional_truth_table=rows,all_candidate_oracle=universal,
        boundaries=['r5db and r5dz for conditional; r5dc and r5d2 for quantification'])

@lru_cache(None)
def integrated_checks():
    doc=fixture(('r5d2',),'q[t[k r5d2['+SIX+']][k ztcandidate[]]].',('r5db',));rows={}
    small=('alpha','beta');names=('alpha','beta','alpha','beta','alpha','alpha')
    for formed,variant in ((False,'not_grave'),(True,'baseline'),(True,'not_grave'),(True,'positive_requirement'),(True,'acquired_only')):
        v=offense_model(doc,variant,names,'alpha','beta','alpha','beta')
        v.update({'z'+n:lambda value=value:value for n,value in zip(NAMES,names)})
        v['r5db']=lambda b:Content(SCENES,tuple(formed and tuple(b.items)==names and t=='candidate' for t in SCENES))
        actual=run(doc,v,small);assert actual==[not formed or variant=='baseline'],(formed,variant,actual)
        rows[str((formed,variant))]=actual[0]
        assert 'h26as' not in v and v['h256o'] is unknown
    supplement=fixture(('r5d4',),'q[t[k r5d4[]][k ztcandidate[]]].')
    v=vocation_model(supplement,nature='alpha',vocation='beta');assert run(supplement,v,small)==[True]
    v=vocation_model(supplement,'acquired_only',nature='alpha',vocation='beta');assert run(supplement,v,small)==[False]
    return dict(native_vocation_offense_and_condition=rows,
        boundary='r5db formation only, with prior native formation evidence pinned',
        relative_supplement_independent_of_agreement_existence=True,progress_and_success_not_evaluated=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='human_original_vocation_hypothetical_offense_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1005,1264],text=u['text'][1005:1264]),
        primary_page=read('data/covenant-question-reading-v1.json')['original_page'],
        corroboration=dict(url='https://korpora.org/kant/aa08/039.html',lines='9–13',
            observation='Dasは直前の企て、derenは同じ人間本性、diesem Fortschreitenは直前の啓蒙進展を受けるという採用解釈。義務の実行や実際の犯罪事件の報告として読まない。'),
        adopted_readings=LIMITS,remaining=['geradeの焦点','後代の拒否資格との接続・also・vollkommen',
            '同じ決議の採択への二つの否定評価','著者帰属と全文の通読'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

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
    for n,f in [('vocation',vocation_checks),('progress',progress_checks),('offense',offense_checks),
                ('bindings',binding_checks),('conditional',conditional_checks),('integrated',integrated_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,read(READING)['source_inventory'],read(READING)['primary_page']['path'],
        'scripts/compose_human_vocation_offense.py','scripts/check_human_vocation_offense.py','tests/test_human_vocation_offense.py',
        'scripts/compose_cohort_covenant_purpose.py','scripts/compose_protected_remarks.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='human_original_vocation_and_hypothetical_grave_offense_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
