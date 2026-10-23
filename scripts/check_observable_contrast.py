"""Check scoped invariance, all-account distinction, and nonfactive discourse."""
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.extraction import extract_document
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic
from scripts.check_conductor_cases import sentinel,same_value
from scripts.compose_observable_contrast import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,FIELDS,RULE,ELIGIBILITY,CAPABILITIES,CASES,PREPARATION,MOTION,MEANINGS,current_args,observed_args,case_args,history,build

DOC='docs/observable-contrast-v1.md';READING='data/observable-contrast-reading-v1.json'
PRIOR='data/einstein-author-credit-review-v1.json';PREVIOUS='data/interaction-example-reading-v1.json';INVENTORY='artifacts/written-units-v1/einstein-1905.json'
DOMAIN=('body','view','scope','framea','frameb','accounta','accountb','labela','labelb','node','prior','author','paper','process','other')
CONTEXTS=('first','second','text','other')
def forbidden(*xs):raise ValueError('Unknown observable-contrast input')
def symbol(x):return json.loads(x.syntax)['symbol']

def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=DOMAIN,situations=CONTEXTS,primitives={n:model.get(n,forbidden) for n in names},
        max_steps=1000000,memoize_definitions=False,memoize_expressions=False)

@lru_cache(None)
def fixture(name):
    doc=parse(read(CORE));doc['statements']=[]
    boundaries={'eicj','eics','eibg'} if name=='eida' else {'eida','eia2','eibi','eiag','eiah','eidd'} if name in ('eidb','eide') else set()
    abstract(doc,boundaries)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];calls=[]
    for i,p in enumerate(d['parameters']):
        n='joc'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        calls.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=calls))]
    return doc,slots

def run(name,values,model):
    doc,slots=fixture(name);assert len(slots)==len(values);model=dict(model)
    for (n,s),value in zip(slots,values):
        if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    return evaluate(doc,model)[0]['value']

def setup(name):
    cuts,base=arithmetic();slots=fixture(name)[1];fields=FIELDS+[('view','a')] if name=='eide' else FIELDS
    supplied=[sentinel(s,i+1,cuts) for i,(_,s) in enumerate(slots)];pos={n:i for i,(n,_) in enumerate(fields)}
    def gate(keys,xs,bit=True):
        return bit and len(xs)==len(keys) and all(same_value(x,supplied[pos[n]],slots[pos[n]][1],cuts) for x,n in zip(xs,keys))
    return cuts,base,slots,fields,supplied,pos,gate

@lru_cache(None)
def comparison_checks():
    cuts,base,slots,fields,supplied,pos,gate=setup('eida')
    names=lambda xs:[x.removeprefix('v ') for x in xs]
    def local(missing=None):
        calls={'eirz':0,'eisae':0}
        def repeated(name,*xs):
            case=('first','second')[calls[name]];calls[name]+=1
            keys=names(observed_args(case)) if name=='eisae' else ['process','right']+names(case_args(case))
            if name=='eirz':assert symbol(xs[-1])=='eicw';xs=xs[:-1]
            return gate(keys,xs,missing!=(name,case))
        return dict(base,eisad=lambda *xs:gate([n for n,_ in ELIGIBILITY],xs,missing!='eisad'),
            eicj=lambda *xs:gate([n for n,_ in CAPABILITIES],xs,missing!='eicj'),
            eics=lambda *xs:gate([n for n,_ in CASES],xs,missing!='eics'),
            eirs=lambda *xs:gate([n for n,_ in PREPARATION],xs,missing!='eirs'),
            eibg=lambda *xs:gate(names(current_args()),xs,missing!='eibg'),
            eirz=lambda *xs:repeated('eirz',*xs),eisae=lambda *xs:repeated('eisae',*xs))
    assert run('eida',supplied,local())
    used=set(n for group in (ELIGIBILITY,CAPABILITIES,CASES,PREPARATION) for n,_ in group)|set(names(current_args()))
    used|={'process','right'}|set(names(case_args('first')))|set(names(case_args('second')))
    used|=set(names(observed_args('first')))|set(names(observed_args('second')))
    for i,(_,sort) in enumerate(slots):
        changed=supplied.copy();changed[i]=sentinel(sort,100+i,cuts)
        assert run('eida',changed,local())==(fields[i][0] not in used),fields[i][0]
        old=supplied[i];supplied[i]=changed[i];assert run('eida',changed,local()),fields[i][0];supplied[i]=old
    missing=['eisad','eicj','eics','eirs','eibg']+[(n,c) for n in ('eirz','eisae') for c in ('first','second')]
    for name in missing:assert not run('eida',supplied,local(name)),name
    count=0
    for valid,relative,current in product((False,True),repeat=3):
        assert run('eidb',supplied,dict(eida=lambda *xs:valid,eia2=lambda *xs:relative,eibi=lambda *xs:current))==((not(valid and relative)) or current);count+=1
    # Forwarding must be checked independently of permissive truth-table gates.
    assert run('eidb',supplied,dict(eida=lambda *xs:gate([n for n,_ in FIELDS],xs),eia2=lambda *xs:gate([n for n,_ in MOTION],xs),eibi=lambda *xs:gate(names(current_args()),xs)))
    motion_names=[n for n,_ in MOTION];current_names=names(current_args())
    for target,keys in (('relative',motion_names),('current',current_names)):
        for n in keys:
            i=pos[n];changed=supplied.copy();changed[i]=sentinel(slots[i][1],100+i,cuts)
            m=dict(eida=lambda *xs:True,eia2=(lambda *xs:gate(motion_names,xs)) if target=='relative' else (lambda *xs:True),
                eibi=(lambda *xs:False) if target=='relative' else (lambda *xs:gate(current_names,xs)))
            assert run('eidb',changed,m)==(target=='relative'),(target,n)
    assert used|set(motion_names)|set(current_names)==set(pos)
    return dict(shared_argument_mutations=len(slots),distinguishing_variants=len(slots),preparation_arguments=len(used),
        relative_history_argument_mutations=len(motion_names),current_argument_mutations=len(current_names),missing_pair_connections=len(missing),truth_combinations=count,
        different_relative_motion_may_have_same_current=True,opposite_motion_roles_not_in_dependence=True,
        boundaries=['eicj','eics','eibg','eia2','eibi','physical comparison/coupling/observability'])

@lru_cache(None)
def distinction_checks():
    values=['view','scope','framea','first','frameb','second','text'];count=0
    def model(allowed,classes,bad=None):
        def permits(view,scope,fa,ca,fb,cb,account,ref):
            row=(view,scope,fa,ca,fb,cb,ref)
            return row==tuple(values) and account in allowed
        def category(view,scope,account,frame,ctx,label,ref):
            if (view,scope,ref)!=('view','scope','text'):return False
            side=0 if (frame,ctx)==('framea','first') else 1 if (frame,ctx)==('frameb','second') else None
            return side is not None and label in classes.get(account,(set(),set()))[side]
        return dict(eisaf=permits,eisag=category)
    options=[(set(),set()),({'labela'},{'labelb'}),({'labela'},{'labela'}),({'labela','labelb'},{'labelb'}),({'labelb'},{'labela'})]
    for a,b,include_b in product(options,options,(False,True)):
        allowed={'accounta'}|({'accountb'} if include_b else set());classes={'accounta':a,'accountb':b}
        expected=all(left and right and not(left&right) for left,right in (classes[n] for n in allowed))
        assert run('eidd',values,model(allowed,classes))==bool(expected);count+=1
    assert not run('eidd',values,model(set(),{}))
    good=model({'accounta'},{'accounta':({'labela'},{'labelb'})})
    for i in range(len(values)):
        changed=values.copy();changed[i]='other';assert not run('eidd',changed,good)
    try:run('eidd',values,dict(good,eisag=forbidden))
    except ValueError as e:assert 'Unknown observable-contrast' in str(e)
    else:raise AssertionError('Unknown account classification accepted')
    # Only the latter clause calls the four moving/resting roles.
    cuts,base,slots,fields,supplied,pos,gate=setup('eide')
    role_keys=[[x.removeprefix('v ') for x in history(c,s)] for c,s in (('first','left'),('first','right'),('second','left'),('second','right'))]
    for valid,roles,rule in product((False,True),repeat=3):
        calls={'eiag':0,'eiah':0}
        def role(name,*xs):
            indices=(0,3) if name=='eiag' else (1,2);i=indices[calls[name]];calls[name]+=1
            return roles and gate(role_keys[i],xs)
        m=dict(eida=lambda *xs:valid and gate([n for n,_ in FIELDS],xs),eiag=lambda *xs:role('eiag',*xs),eiah=lambda *xs:role('eiah',*xs),
            eidd=lambda *xs:rule and gate([n for n,_ in RULE],xs))
        assert run('eide',supplied,m)==(not(valid and roles) or rule)
    return dict(account_classification_cases=count,empty_account_set_rejected=True,all_allowed_accounts_checked=True,
        classification_arguments=len(values),role_condition_combinations=8,no_relative_or_current_equality_required_for_distinction=True)

def discourse_model(bits=(True,)*3,bad=None):
    m={n:lambda value=value:value for n,value in dict(eisaj='node',eir6='prior',rd='author',eirf='paper',eisac='process',ri='text',eisak='view').items()}
    expected={'eir3':('node','author','paper','eidk','text'),'zbc':('node','author','eidg','eidi','process','text'),'ue':('prior','node','text')}
    for i,(n,row) in enumerate(expected.items()):
        if bad and bad[0]==n:row=tuple('other' if j==bad[1] else x for j,x in enumerate(row))
        def callback(*xs,row=row,bit=bits[i]):return bit and tuple(symbol(x) if hasattr(x,'syntax') else x for x in xs)==row
        m[n]=callback
    return m

@lru_cache(None)
def discourse_checks():
    count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:]
        for bits in product((False,True),repeat=3):assert evaluate(doc,discourse_model(bits))[0]['value']==all(bits);count+=1
        for n,arity in (('eir3',5),('zbc',6),('ue',3)):
            for slot in range(arity):assert not evaluate(doc,discourse_model(bad=(n,slot)))[0]['value'];count+=1
    source=parse(read(CORE));source['statements']=[]
    attributed=parse(format_graph(source,'compact')+'q[t[k eidi[]][k ri[]]].')
    for usual,maintains in product((False,True),repeat=2):
        m=discourse_model();m.update(eisah=lambda view,document,ref:usual and (view,document)==('view','paper'),
            eisai=lambda view,content,ref:maintains and view=='view' and symbol(content)=='eidh')
        assert evaluate(attributed,m)[0]['value']==(usual and maintains)
    full=parse(format_graph(source,'compact')+'q[t[k eidg[]][k ri[]]].');m=discourse_model();m.update(eisaa=lambda:'body',eisab=lambda:'other')
    try:evaluate(full,m)
    except ValueError as e:assert 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Universal real comparison sampled')
    m['eisac']=lambda:'body'
    names={d['name'] for d in full['declarations'] if d['kind']=='primitive'}
    try:evaluate_document(full,individuals=('body','other'),situations=('text','first'),primitives={n:m.get(n,forbidden) for n in names},max_steps=100000)
    except ValueError as e:assert 'rational number domain' in str(e)
    else:raise AssertionError('Small individual domain permitted real comparison sampling')
    return dict(presentation_cases=count,usual_view_cases=4,physical_and_account_content_not_executed=True,
        ordered_contrast_preserved=True,full_comparison_domain_refused=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==209
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in ((PRIOR,[206]),(PREVIOUS,[207])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    def dependencies(root):return {d['name'] for d in extract_document(doc,roots=[root],statement_indices=[]).document['declarations']}
    assert not dependencies('eidb')&{'eia3','eiag','eiah'}
    assert 'eia2' not in dependencies('eide') and 'eibi' not in dependencies('eide')
    for name,last in (('eidc','eidb'),('eidf','eide')):
        body=ds[name]['body']['body'];count=0
        while body['kind']=='forall':count+=1;body=body['body']
        assert count==len(FIELDS)-4 and body['symbol']==last
    assert ds['eidk']['body']['kind']=='message' and ds['eidk']['body']['force']=='assert'
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003');reading=json.loads(read(READING))
    validate_hashes(ROOT,reading['source_sha256']);assert unit['text'][308:549]==reading['source'] and reading['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=12,new_primitives=8,preserved_statements=208,appended_statement=INDEX,
        previous_unit_and_sentence_reviews_preserved=True,quantified_parameters=len(FIELDS)-4,source_range=[308,549])

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_observable_contrast import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

def build_report():
    results=dict(comparison=comparison_checks(),distinction=distinction_checks(),discourse=discourse_checks(),structure=structure_checks())
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,READING,PRIOR,PREVIOUS,INVENTORY,
        'scripts/compose_observable_contrast.py','scripts/check_observable_contrast.py','scripts/review_observable_contrast.py',
        'scripts/compose_interaction_example.py','scripts/compose_magnet_source.py','scripts/compose_conductor_cases.py','scripts/compose_relative_history_match.py',
        'scripts/compose_current_distribution.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py',
        'scripts/check_conductor_cases.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','tests/test_observable_contrast.py'}
    return dict(status='observable_dependence_and_usual_account_contrast_checked',document=FULL,**results,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[308,549],source=unit['text'][308:549],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
