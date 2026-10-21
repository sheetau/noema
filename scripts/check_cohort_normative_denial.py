"""Check prospective scope, fixed normative targets and universal denial."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_cohort_normative_denial import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure,NAMES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/cohort-normative-denial-v1.json'
DOC='docs/cohort-normative-denial-v1.md'
READING='data/cohort-normative-denial-reading-v1.json'
PRIORS=('reports/cohort-covenant-purpose-v1.json','reports/covenant-entitlement-v1.json','reports/epoch-undertakings-v1.json')
DOMAIN=(*NAMES,'assessor','role','other','alpha','beta')
SCENES=('reference','candidate','anchor','later','outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)
ARGS=' '.join('k z'+n+'[]' for n in NAMES)
NORM='k zassessor[] '+ARGS+' k zrole[] k ztcandidate[]'
WHOLE='q[t[k r5dh[]][k ztcandidate[]]].'

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
    v['h26av']=lambda:'reference';v['h26ax']=lambda:'alpha';v['h26ay']=lambda:'beta'
    return v

@lru_cache(None)
def norm_checks():
    doc=fixture(('r5dd',),'q[k r5dd['+NORM+']].');rows={}
    def matches(source,person,role,code,bs,polarity,point):
        return code.rank==0 and(source,person,role,symbol(code),tuple(bs.items),point)==('assessor','firstgroup','role','r5db',NAMES,'candidate')
    for permitted,opposed in product((False,True),repeat=2):
        v=base(doc);v['h7l']=lambda *a:matches(*a) and a[5] and permitted;v['h7k']=lambda *a:matches(*a) and not a[5] and opposed
        actual=run(doc,v);assert actual==[permitted and not opposed];rows[str((permitted,opposed))]=actual[0]
        assert v['h26at'] is unknown and v['h26as'] is unknown and v['h255a'] is unknown
    contrasts={}
    for variant in ('source','addressee','role','code','bindings','polarity','context','positive_requirement'):
        v=base(doc);expected=['assessor','firstgroup','role','r5db',NAMES,True,'candidate']
        if variant!='positive_requirement':
            i=('source','addressee','role','code','bindings','polarity','context').index(variant)
            expected[i]=tuple(reversed(NAMES)) if i==4 else False if i==5 else 'other'
        v['h7l']=lambda s,p,r,c,b,sign,t:(s,p,r,symbol(c),tuple(b.items),sign,t)==tuple(expected)
        v['h7k']=lambda *a:variant=='positive_requirement' and matches(*a) and a[5]
        actual=run(doc,v);assert actual==[variant=='positive_requirement'];contrasts[variant]=actual[0]
    for n in ('h7l','h7k'):
        v=base(doc);v['h7l']=lambda *a:True;v['h7k']=lambda *a:False;v[n]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return dict(permission_and_opposition=rows,exact_normative_target=contrasts,unknown_rejected=True,formation_and_achievement_not_evaluated=True)

def native_model(doc,variant='baseline',permitted=False,opposed=False):
    v=base(doc);pair=('alpha','beta','alpha','beta','alpha','alpha')
    v.update({'z'+n:lambda value=value:value for n,value in zip(NAMES,pair)})
    v['h26aw']=lambda ag,r:variant!='no_proposals' and(ag,r)==('alpha','reference')
    v['h26al']=lambda state,aspect,r:variant!='no_aspects' and(state,aspect,r)==('alpha','alpha','reference')
    v['h254z']=lambda ag:'later' if variant=='late_anchor' else 'anchor'
    v['h257z']=lambda r,c,p:(r,c)==('reference','candidate') and p in ('anchor','later')
    v['ic']=lambda a,b,c:(a,b,c)==('anchor','later','candidate')
    v['h26aa']=lambda e,r:r=='reference' and e in ('alpha','beta')
    v['h26ab']=lambda e,r,c,p:(r,c)==('reference','candidate') and(e,p) in (('alpha','anchor'),('beta','later'))
    v['aa']=lambda p:p in ('alpha','beta')
    v['h256o']=lambda p,c,t:c=='candidate' and(p,t) in (('alpha','anchor'),('beta','later'))
    v['h246c']=lambda g,p,c:variant!='wrong_cohort' and c=='candidate' and g==p
    def match(s,p,r,code,bs,sign,c):
        return code.rank==0 and(s,p,r,symbol(code),tuple(bs.items),c)==('alpha','alpha','beta','r5db',pair,'candidate')
    v['h7l']=lambda *a:permitted and match(*a) and a[5]
    v['h7k']=lambda *a:opposed and match(*a) and not a[5]
    return v

@lru_cache(None)
def scope_checks():
    doc=fixture(('r5dc',),'q[k r5dc['+ARGS+' k ztcandidate[]]].');rows={}
    for variant in ('baseline','no_proposals','no_aspects','late_anchor','wrong_cohort'):
        v=native_model(doc,variant);actual=run(doc,v,('alpha','beta'));assert actual==[variant=='baseline'];rows[variant]=actual[0]
    for name in ('h26aw','h26al','h254z','h257z'):
        v=native_model(doc);v[name]=unknown
        try:run(doc,v,('alpha','beta'))
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    return dict(native_epoch_and_prospective_scope=rows,no_formation_or_state_truth_dependencies=True,unknown_rejected=True)

@lru_cache(None)
def universal_checks():
    doc=fixture(('r5dh',),WHOLE,('r5dc',));rows={};left=('alpha',)*6;right=('beta',)*6
    for in_left,in_right,allowed_left,allowed_right in product((False,True),repeat=4):
        v=base(doc)
        v['r5dc']=lambda *a:(a==(*left,'candidate') and in_left) or(a==(*right,'candidate') and in_right)
        def allowed(s,p,r,code,bs,sign,t):
            return code.rank==0 and(s,r,symbol(code),sign,t)==('alpha','beta','r5db',True,'candidate') and p==bs.items[0] and ((tuple(bs.items)==left and allowed_left) or(tuple(bs.items)==right and allowed_right))
        v['h7l']=allowed;v['h7k']=lambda *a:False
        want=not(in_left and allowed_left or in_right and allowed_right)
        actual=run(doc,v,('alpha','beta'));assert actual==[want];rows[str((in_left,in_right,allowed_left,allowed_right))]=actual[0]
    positions=[]
    for i in range(6):
        chosen=tuple('beta' if j==i else 'alpha' for j in range(6));v=base(doc)
        v['r5dc']=lambda *a:a==(*chosen,'candidate')
        v['h7l']=lambda s,p,r,c,b,sign,t:(s,p,r,symbol(c),tuple(b.items),sign,t)==('alpha',chosen[0],'beta','r5db',chosen,True,'candidate')
        v['h7k']=lambda *a:False
        actual=run(doc,v,('alpha','beta'));assert actual==[False];positions.append(actual[0])
    return dict(two_candidate_oracle=rows,counterexample_in_each_position=positions,unselected_permission_does_not_refute_denial=True,boundary='r5dc only; native rdu and six quantifiers')

@lru_cache(None)
def binding_checks():
    matrices={};lengths={}
    for root,boundary in (('r5df','r5dc'),('r5dg','r5dd')):
        def evaluate_case(selected,expected,length=None):
            names=list(NAMES)
            if length=='short':names.pop()
            if length=='long':names.append(NAMES[-1])
            seq='l[a]['+' '.join('k z'+n+'[]' for n in names)+']'
            doc=fixture((root,),'q[t[k '+root+'['+seq+']][k ztcandidate[]]].',(boundary,));v=base(doc)
            v.update({'z'+n:lambda i=i:'beta' if i==selected else 'alpha' for i,n in enumerate(NAMES)})
            wanted=tuple('beta' if i==expected else 'alpha' for i in range(6))
            if root=='r5dg':wanted=('alpha',*wanted,'beta')
            v[boundary]=lambda *a:a==(*wanted,'candidate')
            return run(doc,v,('alpha','beta'))[0]
        matrix=[]
        for selected,expected in product(range(6),repeat=2):
            actual=evaluate_case(selected,expected);assert actual==(selected==expected);matrix.append(actual)
        assert not evaluate_case(0,0,'short') and not evaluate_case(0,0,'long')
        matrices[root]=matrix;lengths[root]=dict(short=False,long=False)
    return dict(position_matrices=matrices,wrong_lengths=lengths,boundaries=['r5dc','r5dd'])

@lru_cache(None)
def integrated_checks():
    doc=fixture(('r5dh',),WHOLE);rows={}
    for variant,permitted,opposed in (('baseline',False,False),('allowed',True,False),('conflicted',True,True),('no_proposals',True,False)):
        v=native_model(doc,variant,permitted,opposed);actual=run(doc,v,('alpha','beta'));assert actual==[variant!='allowed'];rows[variant]=actual[0]
        for name in ('h26ac','h26at','h26as','h26am','h255a'):assert v[name] is unknown
    return dict(all_new_definitions_and_epoch_scope_native=rows,no_definition_boundaries=True,unknown_formation_and_goal_allowed=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='prospective_universal_normative_denial_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[713,1004],text=unit['text'][713:1004]),
        primary_page=read('data/covenant-question-reading-v1.json')['original_page'],adopted_readings=LIMITS,
        contextual_reason='直前の同種契約の無効性と、直後のVerbrechen・unbefugter und frevelhafter Weise・子孫による拒否の記述から、物理的不能ではなく正当な資格の否認を採る。後続文そのものの意味判断は行わない。',
        remaining=['共謀的提示・重要性・総括・著者帰属と一文全体の通読'],new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    new=catalog();sources=parents();imported={n:e for s in sources for n,e in s.entries.items()}
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):assert e['declaration']==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record();p=read(READING)['primary_page'];assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    assert not new.document['statements'] and len(sources[0].document['statements'])==99
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=99)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('norm',norm_checks),('scope',scope_checks),('universal',universal_checks),('bindings',binding_checks),('integrated',integrated_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,read(READING)['source_inventory'],read(READING)['primary_page']['path'],
        'scripts/compose_cohort_normative_denial.py','scripts/check_cohort_normative_denial.py','tests/test_cohort_normative_denial.py',
        'scripts/compose_cohort_covenant_purpose.py','scripts/compose_protected_remarks.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='prospective_universal_normative_denial_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
