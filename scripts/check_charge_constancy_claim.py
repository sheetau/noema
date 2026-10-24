"""Check shared theorem identity, native easy derivation and the complete note."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import Content,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_calculation_discourse import sequence,pair,symbol
from scripts.compose_calculation_discourse import STEPS
from scripts.compose_charge_constancy_claim import *

DOC='docs/charge-constancy-claim-v1.md';SOURCE='data/einstein-charge-constancy-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p917-0.jpg'
DEPENDENCIES=('reports/moving-body-charge-history-v1.json','reports/convective-relativity-claim-v1.json','reports/calculation-discourse-v1.json')
CONSTANTS={'eiswu':'intro','eiswv':'theorem','eiswf':'old','eiswn':'transformed','eiswq':'previous','eisv6':'ninth','eiseb':'resting','ra':'K','rd':'author','eirf':'paper','ri':'case'}
DOMAIN=tuple(CONSTANTS.values())+('method','other');POINTS=('case','other')
PARTS={'ek3e':('ekzc','ekz7','ek2j'),'ek3h':('ek3f','ek3g'),'ek3k':('ek3i','ek3j')}
BOUNDS={n:set(xs) for n,xs in PARTS.items()}|{'ek3f':{'ek3e','ek3d'},'ek3g':{'ek3d'},'ek3i':{'ek3h','ekzc','ekz7','ek2j'},'ek3j':{'ek3d'},'ek3m':{'ek3l'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(root,mode='boundary'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in BOUNDS[root]:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if root=='ek3f':
        pairs=json.loads(mode)
        helper=parse('n:r jccprogram[a d '+STEPS+'] '+STEPS+'.')['declarations'][0]
        prefix='n:r ek3e[] e.r ek3d[] e.r jccmid[] e.r jccprogram[a d '+STEPS+'] '+STEPS+'.'
        replacement=parse(prefix+'d zlx[method a stage d] '+STEPS+'[k jccprogram[v method v stage '+sequence(pairs)+']].')['declarations'][-1]
        doc['declarations']=[d for d in doc['declarations'] if d['name']!='zlx']
        missing={n for p in pairs for n in p}-{d['name'] for d in doc['declarations']}
        at=next(i for i,d in enumerate(doc['declarations']) if d['name']==root)
        doc['declarations'][at:at]=[dict(kind='primitive',name=n,parameters=[],result='content') for n in sorted(missing)]+[helper,replacement]
    expr=dict(kind='call',symbol=root,arguments=[])
    if root!='ek3m':
        doc['declarations'].append(dict(kind='primitive',name='jccpoint',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jccpoint',arguments=[]))
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)]
    return doc

def run(root,m,mode='boundary'):
    doc=fixture(root,mode)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jccpoint':lambda:'case'}|m
    mm.setdefault('jccprogram',lambda method,stage,seq:seq if (method,stage)==('method','case') else SequenceValue((),seq.element_type))
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def chain_checks():
    good=[('ek3e','jccmid'),('jccmid','ek3d')];count=0
    cases=((good,2,{},True),([('ek3e','ek3d')],1,{},True),([],2,{},False),(list(reversed(good)),2,{},False),([good[1]],2,{},False),([good[0]],2,{},False),([good[0],('ek3e','ek3d')],2,{},False),(good,1,{},False),(good,2,{good[0]:-1},False),([good[0],('jccmid','jccmid'),good[1]],2,{},False),([good[0],('jccmid','jccmid'),good[1]],3,{},True),(good,0,{('ek3e','ek3d'):0},False))
    for pairs,budget,costs,expected in cases:
        m={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'zlw':lambda a,p,s:(a,p,s)==('author','method','case'),'zla':lambda a,b,s:s=='case','zlb':lambda step,s:Q(costs.get(pair(step),1)),'zlc':lambda n,s:s=='case' and n<=budget}
        assert run('ek3f',m,json.dumps(pairs))==expected;count+=1
    m={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'zlw':lambda a,p,s:(a,p,s)==('author','method','case'),'zla':lambda a,b,s:s=='case' and (symbol(a),symbol(b)) in good,'zlb':lambda step,s:Q(1 if s=='case' else 10),'zlc':lambda n,s:s=='case' and n<=2};mode=json.dumps(good)
    for patch in ({'zlw':lambda *xs:False},{'rd':lambda:'other'},{'zlw':lambda a,p,s:(a,p,s)==('author','other','case')},{'zlw':lambda a,p,s:(a,p,s)==('author','method','other')},{'zla':lambda a,b,s:(symbol(a),symbol(b))==good[0]},{'zlb':lambda step,s:Q(10)},{'zlc':lambda n,s:s=='other' and n<=2},{'jccprogram':lambda p,s,seq:seq if (p,s)==('other','case') else SequenceValue((),seq.element_type)}):
        assert not run('ek3f',m|patch,mode);count+=1
    unknowns(lambda mm:run('ek3f',mm,mode),m,('zlw','zla','zlb','zlc'))
    assert run('ek3f',m|{n:forbidden for n in ('ek3e','ek3d')},mode);count+=1
    return dict(cases=count,native_nonempty_chain_and_same_nonnegative_total=True,same_available_method_premise_theorem_and_context=True,quoted_theorem_not_executed=True)

@lru_cache(None)
def content_checks():
    cases=0
    for root,parts in PARTS.items():
        for values in product((False,True),repeat=len(parts)):
            m={n:lambda x=x:Content(POINTS,(x,not x)) for n,x in zip(parts,values)}
            assert run(root,m)==all(values);cases+=1
    rows={'eiswr':{('ek3d','ninth','case')}};m={n:relation(rs) for n,rs in rows.items()}
    cases+=perturb(lambda mm:run('ek3g',mm),m,rows)
    assert run('ek3g',m|{'ek3d':forbidden});cases+=1
    return dict(cases=cases,same_point_for_premises_and_independent_evaluations=True,importance_is_of_same_theorem_not_truth=True)

@lru_cache(None)
def presentation_checks():
    count=0
    groups=(('ek3i',{'eiswt':{('intro','author','ek3h','previous','ninth','case')},'eisws':{('intro','theorem','ninth','case')},'eiswm':{('intro','author',node,target,'paper','case') for node,target in [('old','ekzc'),('transformed','ekz7'),('previous','ek2j')]}}),('ek3j',{'uh':{('theorem','author','ek3d','ninth','case')},'eismz':{('theorem','resting','K','paper','case')},'uf':{('author','intro','theorem','case')},'ue':{('intro','theorem','case')}}),('ek3m',{'eir3':{('intro','author','paper','ek3l','case')},'ue':{('previous','intro','case')}}))
    for root,rows in groups:
        m={n:relation(rs) for n,rs in rows.items()}
        count+=perturb(lambda mm:run(root,mm),m,rows)
        assert run(root,m|{n:forbidden for n in BOUNDS[root]});count+=1
        unknowns(lambda mm:run(root,mm),m,tuple(rows))
    for root,patch in [('ek3j',{'eiswv':lambda:'intro'}),('ek3m',{'eiswq':lambda:'intro'})]:
        assert not run(root,{n:lambda *xs:True for n in ('uh','eismz','uf','ue','eir3')}|patch);count+=1
    return dict(cases=count,short_span_includes_theorem=True,same_supplement_and_prior_equations=True,quoted_resting_designation_targets_K=True,quoted_content_not_evaluated=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][237];math={m['id']:m for m in inv['math']};ms=[math[n] for n in u['math_ids']]
    assert u['id']=='einstein-1905:u0238' and digest(u['text'].encode())==u['text_sha256']
    assert u['math_ids']==['M0393']
    for m in ms:assert digest(m['mathml'].encode())==m['sha256']
    return dict(version='einstein-charge-constancy-reading-v1',unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=ms,source_nonblank_characters=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',u['text']))),observations=['原刊917頁の第九節末尾を視認した。Es möge noch kurz bemerkt werden、entwickelten Gleichungen、leicht、wichtige Satz、コロン後の任意運動する帯電物体、随伴系で変わらない電荷、auch、引用符付きruhenden、K、konstantまでを同じ全文として照合した。','随伴系を同じ物体の追跡点へ原点を付けた系、過程を対応する任意の正長有限区間、物体を持続的な全物質点集合として読む。原文が追跡点や区間を明記したとはしない。変形・加速・非一様な電荷を排除せず、原文の一定性を二系の数値等値へ強めない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert after.document['statements'][:INDEX]==before.document['statements'] and len(after.document['statements'])==INDEX+1
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[411])==selection_binding(before,[411]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/moving-body-charge-history-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    assert len(MEANINGS)==9 and len(PRIMITIVES)==5
    # Presentation must neither execute the quoted theorem nor add proof completion.
    presentation=extract_document(core(),roots=['ek3i','ek3j','ek3m'],statement_indices=[]).document
    assert 'ui' not in {d['name'] for d in presentation['declarations']}
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=9,new_general_relations=3,new_reference_constants=2,added_statement=INDEX,all_412_prior_statements_and_meanings_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('chain',chain_checks),('content',content_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_calculation_discourse','check_clock_site_time','check_rod_methods','check_calculation_discourse','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_charge_constancy_claim.py','scripts/check_charge_constancy_claim.py','tests/test_charge_constancy_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='charge_constancy_claim_connected_for_whole_unit_review',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
