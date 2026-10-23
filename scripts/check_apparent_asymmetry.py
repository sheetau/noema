"""Check appearance alternatives, theory-application binding and knownness scope."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.extraction import extract_document
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.compose_apparent_asymmetry import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,COMPARISON,APPEARANCE,FIELDS,RULE,MEANINGS,PRIMITIVES,build

DOC='docs/apparent-asymmetry-v1.md';READING='data/apparent-asymmetry-reading-v1.json';INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=['data/einstein-author-credit-review-v1.json','data/interaction-example-reading-v1.json','data/observable-contrast-reading-v1.json','data/moving-magnet-case-reading-v1.json','data/moving-conductor-case-reading-v1.json']
DOMAIN=('scope','framea','frameb','theory','view','paper','node','next','author','other')
CONTEXTS=('first','second','text','candidate')
def forbidden(*xs):raise ValueError('Unknown apparent-asymmetry input')
def symbol(x):return json.loads(x.syntax)['symbol']
def evaluate(doc,model):
    ps={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=DOMAIN,situations=CONTEXTS,primitives={n:model.get(n,forbidden) for n in ps},max_steps=1000000,memoize_definitions=False,memoize_expressions=False)

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    abstract(doc,{'eidd','eiev'} if name=='eiew' else {'eiew'} if name=='eiex' else {'eiez'} if name=='eie2' else set())
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];calls=[]
    for i,p in enumerate(d['parameters']):
        n='jaas'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));calls.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=calls)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jaaref',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jaaref',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots
def run(name,values,model):
    doc,slots=fixture(name);assert len(slots)==len(values);m=dict(model,jaaref=lambda:'text')
    m.update({n:(lambda x=x:x) for (n,_),x in zip(slots,values)})
    return evaluate(doc,m)[0]['value']

@lru_cache(None)
def appearance_checks():
    values=['scope','framea','first','frameb','second','text'];cases=0
    for selected in (set(),{'candidate'},{'candidate','first'},{'text'}):
        for actual,one,two in product((False,True),repeat=3):
            observed={'text':actual,'candidate':one,'first':two,'second':False}
            def candidates(*xs):return tuple(xs[:5])==tuple(values[:5]) and symbol(xs[5])=='eieu' and xs[6]=='text' and xs[7] in selected
            def asymmetry(*xs):assert tuple(xs[:5])==tuple(values[:5]);return observed[xs[5]]
            assert run('eiev',values,dict(eisa3=candidates,eisa2=asymmetry))==(bool(selected) and all(not observed[p] for p in selected));cases+=1
    # The content is negation inside appearance, not a negated appearance operator.
    for actual in (False,True):
        m=dict(eisa3=lambda *xs:xs[-1]=='candidate',eisa2=lambda *xs:actual if xs[-1]=='text' else False)
        assert run('eiev',values,m)
        assert run('eieu',values[:5],m)==(not actual)
    for i in range(6):
        changed=values.copy();changed[i]='other' if i in (0,1,3) else 'candidate'
        def candidates(*xs):return tuple(xs[:5])==tuple(values[:5]) and symbol(xs[5])=='eieu' and xs[6]==values[5] and xs[7]=='candidate'
        assert not run('eiev',changed,dict(eisa3=candidates,eisa2=lambda *xs:False))
        old=values[i];values[i]=changed[i];assert run('eiev',changed,dict(eisa3=candidates,eisa2=lambda *xs:False));values[i]=old
    try:run('eiev',values,dict(eisa3=forbidden,eisa2=lambda *xs:False))
    except ValueError as e:assert 'Unknown apparent' in str(e)
    else:raise AssertionError('Unknown alternatives treated as absence')
    return dict(candidate_cases=cases,argument_mutations=6,actual_asymmetry_compatible_with_appearance=True,empty_or_unknown_candidates_rejected=True)

@lru_cache(None)
def application_checks():
    data=dict(view='view',scope='scope',firstframe='framea',firstcontext='first',secondframe='frameb',secondcontext='second',reference='text',theory='theory',document='paper')
    fields=[n for n,_ in FIELDS];values=[data[n] for n in fields]
    def local(bits=(True,True,True)):
        def app(*xs):return bits[0] and tuple(xs[:-1])==tuple(values) and symbol(xs[-1])=='eiag'
        return dict(eisaz=app,eidd=lambda *xs:bits[1] and tuple(xs)==tuple(values[fields.index(n)] for n,_ in RULE),eiev=lambda *xs:bits[2] and tuple(xs)==tuple(values[fields.index(n)] for n,_ in APPEARANCE))
    for bits in product((False,True),repeat=3):assert run('eiew',values,local(bits))==all(bits)
    for i,n in enumerate(fields):
        changed=values.copy();changed[i]='candidate' if n.endswith('context') or n=='reference' else 'other'
        assert not run('eiew',changed,local()),n
        old=values[i];values[i]=changed[i];assert run('eiew',changed,local());values[i]=old
    # Real existential scope over finite case labels; every supplied case slot is distinct.
    observed=[]
    target=('view','scope','framea','first','frameb','second','text','theory','paper')
    def witness(*xs):
        observed.append(xs);return tuple(xs)==target
    assert run('eiex',['theory','view','paper'],dict(eiew=witness))
    assert target in observed
    assert not run('eiex',['theory','view','paper'],dict(eiew=lambda *xs:False))
    for i in (0,6,7,8):
        wrong=list(target);wrong[i]='other' if i!=6 else 'candidate'
        assert not run('eiex',['theory','view','paper'],dict(eiew=lambda *xs:tuple(xs)==tuple(wrong)))
    return dict(application_truth_cases=8,argument_mutations=len(fields),existential_comparison_checked=True,general_case_scope_not_fixed_to_magnet=True)

@lru_cache(None)
def knownness_checks():
    for proposition,known in product((False,True),repeat=2):
        m=dict(eiez=lambda:Content(CONTEXTS,tuple(proposition for _ in CONTEXTS)),eirf=lambda:'paper',eisa4=lambda doc,code,point:known and doc=='paper' and symbol(code)=='eiez')
        assert run('eie2',[],m)==(proposition and known)
    for usual,interpretation in product((False,True),repeat=2):
        m=dict(eisak=lambda:'view',eirf=lambda:'paper',eisax=lambda:'theory',eisah=lambda view,doc,ref:usual and (view,doc)==('view','paper'),eisay=lambda theory,view,doc,ref:interpretation and (theory,view,doc)==('theory','view','paper'))
        assert run('eiey',[],m)==(usual and interpretation)
    return dict(proposition_and_knownness_cases=4,ordinary_interpretation_cases=4,knownness_does_not_erase_claim_or_qualification=True)

def discourse_model(bits=(True,True,True),bad=None):
    m=dict(eir7=lambda:'node',eir6=lambda:'next',rd=lambda:'author',eirf=lambda:'paper',ri=lambda:'text')
    expected={'eir3':('node','author','paper','eie3','text'),'eisa5':('node','author','eiez','eiey','text'),'ue':('node','next','text')}
    for i,(n,row) in enumerate(expected.items()):
        if bad and bad[0]==n:row=tuple('other' if j==bad[1] else x for j,x in enumerate(row))
        m[n]=lambda *xs,row=row,bit=bits[i]:bit and tuple(symbol(x) if hasattr(x,'syntax') else x for x in xs)==row
    return m

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==212
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,index in zip(PRIORS,(206,207,208,209,210)):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[index])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert ds['eieu']['body']['body']['kind']=='not'
    assert ds['eie3']['body']['force']=='assert'
    deps={d['name'] for d in extract_document(doc,roots=['eiex'],statement_indices=[]).document['declarations']}
    assert not deps&{'eisaa','eisab','eisac','eicr','eici'}
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    count=0
    for path in (CORE,FULL):
        p=parse(read(path));p['statements']=p['statements'][-1:]
        for bits in product((False,True),repeat=3):assert evaluate(p,discourse_model(bits))[0]['value']==all(bits);count+=1
        for name,arity in (('eir3',5),('eisa5',5),('ue',3)):
            for slot in range(arity):assert not evaluate(p,discourse_model(bad=(name,slot)))[0]['value'];count+=1
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003');reading=json.loads(read(READING))
    validate_hashes(ROOT,reading['source_sha256']);assert unit['text'][:209]==reading['source'] and reading['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=211,presentation_cases=count,quoted_physics_not_executed=True,general_scope_preserved=True,prior_reviews_preserved=True,source_range=[0,209])

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_apparent_asymmetry import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')
def build_report():
    results=dict(appearance=appearance_checks(),application=application_checks(),knownness=knownness_checks(),structure=structure_checks())
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,READING,INVENTORY,*PRIORS,'scripts/compose_apparent_asymmetry.py','scripts/check_apparent_asymmetry.py','scripts/review_apparent_asymmetry.py','tests/test_apparent_asymmetry.py','scripts/compose_observable_contrast.py','scripts/compose_material_body_motion.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py','scripts/check_coordinate_correspondence.py'}
    return dict(status='general_asymmetry_appearance_and_knownness_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,209],source=unit['text'][:209],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
