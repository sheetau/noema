"""Check hypothetical physical content and nonfactive example invitation."""
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic
from scripts.check_conductor_cases import sentinel,same_value
from scripts.compose_interaction_example import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,FIELDS,MEANINGS,source_args,capacity_args,build

DOC='docs/interaction-example-v1.md';READING='data/interaction-example-reading-v1.json'
PRIOR='data/einstein-author-credit-review-v1.json';INVENTORY='artifacts/written-units-v1/einstein-1905.json'
DOMAIN=('left','right','process','body','node','prior','author','paper','reader','readerb','other');CONTEXTS=('text','thought','first','other')
def forbidden(*xs):raise ValueError('Unexpected physical or mental evaluation')
def symbol(value):return json.loads(value.syntax)['symbol']

def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=DOMAIN,situations=CONTEXTS,primitives={n:model.get(n,forbidden) for n in names},
        max_steps=100000,memoize_definitions=False,memoize_expressions=False)

def discourse_model(bits=(True,True,True),bad=None):
    model={n:lambda value=value:value for n,value in dict(eir6='node',eir7='prior',rd='author',eirf='paper',ri='text').items()}
    expected={'eir3':('node','author','paper','eic6','text'),'eir5':('node','author','prior','eic4','text'),'ue':('prior','node','text')}
    for i,(name,row) in enumerate(expected.items()):
        if bad and bad[0]==name:row=tuple('other' if j==bad[1] else x for j,x in enumerate(row))
        def callback(*xs,name=name,row=row,bit=bits[i]):
            converted=tuple(symbol(x) if hasattr(x,'syntax') else x for x in xs)
            return bit and converted==row
        model[name]=callback
    return model

@lru_cache(None)
def attribution_checks():
    count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:]
        for bits in product((False,True),repeat=3):
            assert evaluate(doc,discourse_model(bits))[0]['value']==all(bits);count+=1
        for n,arity in (('eir3',5),('eir5',5),('ue',3)):
            for slot in range(arity):assert not evaluate(doc,discourse_model(bad=(n,slot)))[0]['value'];count+=1
        model=discourse_model();model['eir7']=lambda:'node'
        assert not evaluate(doc,model)[0]['value']
    return dict(cases=count+2,full_and_core_native=True,physical_and_mental_content_not_executed=True,
        message_target_and_example_target_preserved=True)

@lru_cache(None)
def message_checks():
    doc=parse(read(CORE));doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+'r jcapture[f] c.q[k jcapture[k eic6[]]].')
    captured=[]
    def capture(message):captured.append(message);return True
    count=0
    for first,second in product((False,True),repeat=2):
        seen=[];model=discourse_model()
        model.update(jcapture=capture,eir4=lambda p,d,ctx:p in ('reader','readerb') and (d,ctx)==('paper','text'))
        def considers(person,target,point):
            seen.append((person,symbol(target),point))
            return symbol(target)=='eic4' and (first if person=='reader' else second if person=='readerb' else False)
        model['eir2']=considers
        assert evaluate(doc,model)[0]['value'];message=captured[-1]
        assert message.force=='direct' and message.content.values==(first and second,)*len(CONTEXTS)
        assert all(target=='eic4' for _,target,_ in seen)
        assert evaluate(parse(read(CORE)),discourse_model())[0]['value'];count+=1
    # Evaluating the hypothetical content cannot enumerate its full real/function domain.
    query=parse(format_graph(parse(read(CORE)),'compact')+'q[t[k eic4[]][k ri[]]].');query['statements']=query['statements'][-1:]
    model=discourse_model();model.update(eisaa=lambda:'left',eisab=lambda:'right',eisac=lambda:'process')
    try:evaluate(query,model)
    except ValueError as e:assert 'rational number domain' in str(e)
    else:raise AssertionError('Hypothetical physical configuration sampled')
    return dict(reader_combinations=count,directive_force=True,all_addressed_readers=True,
        no_obedience_or_physical_truth_required_for_attribution=True,full_real_content_refused=True)

@lru_cache(None)
def binding_fixture():
    doc=parse(read(CORE));doc['statements']=[];abstract(doc,{'eicr','eici'})
    d=next(d for d in doc['declarations'] if d['name']=='eic2');slots=[];calls=[]
    for i,p in enumerate(d['parameters']):
        n='jiex'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        calls.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol='eic2',arguments=calls))]
    return doc,slots

@lru_cache(None)
def coupling_checks():
    cuts,base=arithmetic();doc,slots=binding_fixture();supplied=[sentinel(s,i+1,cuts) for i,(_,s) in enumerate(slots)]
    pos={n:i for i,(n,_) in enumerate(FIELDS)};supplied[pos['left']]='left';supplied[pos['right']]='right'
    names=lambda xs:[x.removeprefix('v ') for x in xs]
    def gate(keys,bit,xs):return bit and len(xs)==len(keys) and all(same_value(x,supplied[pos[n]],slots[pos[n]][1],cuts) for x,n in zip(xs,keys))
    def run(values,bits=(True,)*3,wrong_schema=False):
        model=dict(base,eicr=lambda *xs:gate(names(source_args()),bits[0],xs),eici=lambda *xs:gate(names(capacity_args()),bits[1],xs),
            eirz=lambda *xs:gate(['process','right']+names(source_args()),bits[2],xs[:-1]) and symbol(xs[-1])==('eicp' if wrong_schema else 'eicw'))
        for (n,s),value in zip(slots,values):
            if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
            model[n]=lambda value=value:value
        return evaluate(doc,model)[0]['value']
    for bits in product((False,True),repeat=3):assert run(supplied,bits)==all(bits)
    assert not run(supplied,wrong_schema=True)
    for i,(_,s) in enumerate(slots):
        changed=supplied.copy();changed[i]=sentinel(s,100+i,cuts)
        assert not run(changed),FIELDS[i][0]
        old=supplied[i];supplied[i]=changed[i];assert run(changed),FIELDS[i][0];supplied[i]=old
    aliased=supplied.copy();aliased[pos['right']]=supplied[pos['left']]
    old=supplied[pos['right']];supplied[pos['right']]=supplied[pos['left']];assert not run(aliased);supplied[pos['right']]=old
    return dict(truth_combinations=8,argument_mutations=len(slots),distinguishing_variants=len(slots),
        distinct_bodies_required=True,local_source_action_schema_preserved=True,boundaries=['eicr','eici','eirz physical coupling interpretation'])

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==208
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[206])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert ds['eic6']['body']['kind']=='message' and ds['eic6']['body']['force']=='direct'
    assert ds['eic3']['body']['kind']=='content'
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003')
    reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256'])
    assert unit['text'][210:307]==reading['source'] and reading['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=6,new_primitives=10,preserved_statements=207,appended_statement=INDEX,
        author_review_preserved=True,source_range=[210,307],whole_paragraph_not_completed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    from scripts.review_interaction_example import build_reading
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

def build_report():
    results=dict(attribution=attribution_checks(),message=message_checks(),coupling=coupling_checks(),structure=structure_checks())
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,READING,PRIOR,INVENTORY,
        'scripts/compose_interaction_example.py','scripts/check_interaction_example.py','scripts/review_interaction_example.py',
        'scripts/compose_source_action.py','scripts/compose_magnet_source.py','scripts/compose_conductor_reading.py','scripts/compose_material_relative_frame.py',
        'scripts/compose_limits.py','scripts/check_conductor_cases.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py',
        'scripts/check_coordinate_correspondence.py','tests/test_interaction_example.py'}
    return dict(status='interaction_example_invitation_checked',document=FULL,**results,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[210,307],source=unit['text'][210:307],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
