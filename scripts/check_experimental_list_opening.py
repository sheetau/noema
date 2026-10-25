"""Check list intention, ordered property contents and the shared source of inference."""
from scripts.compose_experimental_list_opening import *
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.finite_semantics import evaluate_document,Content
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_clock_site_time import relation,perturb

DOC='docs/experimental-list-opening-v1.md';SOURCE='data/einstein-experimental-list-opening-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf'
DEPENDENCIES=('reports/experimental-relation-tests-v1.json','reports/deflection-speed-determination-v1.json','reports/traversed-potential-v1.json','reports/local-magnetic-radius-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','ri':'case','eisxg':'tenth','eis3w':'intro','eis3x':'first','eis4q':'second','eis4u':'third','eisym':'equations','eis3p':'previous'}
PEOPLE=tuple(CONSTANTS.values())+('other',)
BOUNDS={'eun':{'erb','erc','eq7'},'euo':{'esz','es2','es3'},'eup':{'eun','esd','euo'},'euq':{'elk','eq6','epd','esw'},'eur':{'eun','esd','euo','elk','euq','eup','eul'},'eut':{'eus'}}
def forbidden(*xs):raise ValueError('Unknown experimental-list input')
def reject(f):
    try:f()
    except ValueError:return
    raise AssertionError('Unknown input accepted')
@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in BOUNDS.get(root,set())|{'aa'}:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document
def evaluate(doc,m):
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'aa':lambda a,b:a<b}|m
    return evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=100000,memoize_definitions=True,memoize_expressions=True)[0]['value']
@lru_cache(None)
def fixture(root,instance=False):
    doc=deepcopy(boundary(root));d=next(d for d in doc['declarations'] if d['name']==root)
    if instance:
        def expose(x):
            if isinstance(x,list):return [expose(y) for y in x]
            if not isinstance(x,dict):return x
            if x.get('kind')=='exists':return dict(kind='call',symbol='eq6',arguments=[dict(kind='number',numerator=1,denominator=1),dict(kind='variable',name=d['body']['variable'])])
            return {k:expose(y) for k,y in x.items()}
        d['body']=expose(d['body'])
    expr=dict(kind='call',symbol=root,arguments=[])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].insert(0,dict(kind='primitive',name='ri',parameters=[],result='situation'))
    doc['statements']=[dict(kind='ask',body=expr)];return doc
def run(root,m,instance=False):return evaluate(fixture(root,instance),m)
@lru_cache(None)
def content_checks():
    cases=0
    for root,parts in [('eun',('erb','erc','eq7')),('euo',('esz','es2','es3')),('eup',('eun','esd','euo'))]:
        for vals in product((False,True),repeat=3):
            m={n:lambda x=x:Content(('case','other'),(x,False)) for n,x in zip(parts,vals)};assert run(root,m)==all(vals);cases+=1
    for vals in product((False,True),repeat=4):
        m={n:lambda x=x:Content(('case','other'),(x,False)) for n,x in zip(('elk','epd','esw'),vals[:3])}|{'eq6':lambda scale,context:vals[3] and scale==Q(1) and context=='case'}
        assert run('euq',m,True)==all(vals);cases+=1
    reject(lambda:run('euq',m));cases+=1
    return dict(cases=cases,all_first_and_third_item_contents_preserved=True,all_three_properties_and_applicability_premises_required=True,unbounded_calibration_scale_not_finitely_enumerated=True)
@lru_cache(None)
def enumeration_checks():
    cases=0;doc=deepcopy(boundary('eur'))
    # eur binds its own situation; the standalone generic calls need a constant.
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].insert(0,dict(kind='primitive',name='ri',parameters=[],result='situation'))
    # Exercise the generic length constraints with literal, interpreter-issued quotations.
    for items,contents,wanted in [(['first'],['eun'],True),(['first','second'],['eun','esd'],True),([],[],False),(['first'],[],False),(['first'],['eun','esd'],False)]:
        nodes={'first':'eis3x','second':'eis4q'}
        extra='q[k eum[k eis3w[] k rd[] l[a]['+' '.join(k(nodes[n]) for n in items)+'] l[i[e]]['+' '.join(quote(n) for n in contents)+'] k eisxg[] k eirf[] k ri[]]].'
        d=parse(format_graph(doc,'compact')+extra)
        assert evaluate(d,{'eis6v':lambda *xs:True})==wanted;cases+=1
    return dict(cases=cases,arbitrary_nonempty_equal_length_lists=True,not_a_three_item_source_sentence_primitive=True)
@lru_cache(None)
def presentation_checks():
    rows={'eis6v':{('intro','author',('first','second','third'),('eun','esd','euo'),'tenth','paper','case')},'eislk':{(item,'intro',Q(i+1),'paper','case') for i,item in enumerate(('first','second','third'))},'eiswm':{('intro','author','equations','elk','paper','case')},'eis3v':{('elk','euq',Q(1),'case')},'zc':{('intro','author','euq','eup','tenth','case')},'uh':{('intro','author','eul','tenth','case')}}
    m={n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in BOUNDS['eur']}
    cases=perturb(lambda mm:run('eur',mm),m,rows)
    for baditems,badcontents in [(('second','first','third'),('eun','esd','euo')),(('first','second','third'),('esd','eun','euo')),(('first','second'),('eun','esd'))]:
        assert not run('eur',m|{'eis6v':relation({('intro','author',baditems,badcontents,'tenth','paper','case')})});cases+=1
    rows={'eir3':{('intro','author','paper','eus','case')},'ue':{('previous','intro','case'),('intro','first','case')}}
    cases+=perturb(lambda mm:run('eut',mm),{n:relation(rs) for n,rs in rows.items()}|{'eus':forbidden},rows)
    return dict(cases=cases,current_undertaking_and_ordered_three_items=True,same_A_reference_applicability_and_inference=True,all_three_experimental_access_claimed=True,quoted_physical_contents_never_executed=True)
@lru_cache(None)
def source_record():
    u=json.loads(read(INVENTORY))['units'][264];assert u['id']=='einstein-1905:u0265' and not u['math_ids'];assert digest(u['text'].encode())==u['text_sha256']
    return dict(version='einstein-experimental-list-opening-reading-v1',unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=[],source_nonblank_characters=len(re.sub(r'\s','',u['text'])),facsimile_pages=[920],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==445 and after.document['statements'][:444]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[441,442,443])==selection_binding(before,[441,442,443]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_statements=1,all_444_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('content',content_checks),('enumeration',enumeration_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_experimental_list_opening.py','scripts/check_experimental_list_opening.py','tests/test_experimental_list_opening.py'}
    for p in DEPENDENCIES:paths.update(json.loads(read(p))['source_sha256'])
    return dict(status='three_experimental_properties_list_opening_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
