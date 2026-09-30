"""Check length comparison scope and non-factive naming/argument attribution."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_measurements import ARITHMETIC, cut, fingerprint
from scripts.compose_rod_comparison import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/rod-comparison-v1.json'


def values(doc,model,domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('direct','slice','text','other'),
        primitives=model,max_steps=1_000_000,memoize_definitions=True,memoize_expressions=True)]


def guarded(doc):
    def forbidden(*args):raise ValueError('Attributed mathematical or measurement content executed')
    return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}


def callbacks(doc,model,entries):
    sorts={d['name']:d['result'] for d in doc['declarations']}
    for name,callback in entries.items():
        sort=sorts[name]
        model[name]=lambda sort=sort,callback=callback:FunctionValue(tuple(sort['parameters']),sort['result'],callback)


def projected_uniqueness():
    """A finite carrier substitution of the logical kernel, NOT real-cut evaluation.

    Only sort annotations change; quantifier/connective/call structure is kept.
    This isolates existence/uniqueness scope for exhaustive finite countermodels.
    """
    original=parse(generic_composed()[0])
    definitions=[deepcopy(d) for d in original['declarations'] if d['name'] in ('sbx','sby','sbz')]
    cut_sort={'kind':'function','parameters':['number'],'result':'truth'}
    def replace(value):
        if value==cut_sort:return 'individual'
        if isinstance(value,dict):return {k:replace(v) for k,v in value.items()}
        if isinstance(value,list):return [replace(v) for v in value]
        return value
    doc=deepcopy(original);doc['declarations']=replace(definitions);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+'''
r ja[] a.r jb[a] c.r jc[a] c.r jd[a a] c.r je[a a] c.
q[k sbz[k ja[] p jb p jc p jd p je]].''')
    domain=('baseline','alias','different','another')
    number={'baseline':5,'alias':5,'different':4,'another':6}
    rows=[]
    for bits in product((False,True),repeat=4):
        selected={name for name,yes in zip(domain,bits) if yes}
        selected_values={number[name] for name in selected}
        for equal in (False,True):
            for baseline_valid in (False,True):
                model={'ja':lambda:'baseline','jb':lambda v:v in selected,
                    'jc':lambda v:baseline_valid or number[v]!=5,
                    'jd':lambda a,b:number[a]==number[b],
                    'je':lambda a,b:(number[a]==number[b])==equal}
                actual=values(doc,model,domain)[0]
                expected=baseline_valid and len(selected_values)==1 and ((next(iter(selected_values))==5)==equal)
                if actual!=expected:raise ValueError('Existence/uniqueness scope differs from finite value-set oracle')
                rows.append({'selected':sorted(selected),'equals_baseline':equal,'baseline_valid':baseline_valid,'accepted':actual})
    return {'cases':rows,'projection':'Only replace the real-cut value sort with a four-element individual carrier.',
        'real_cut_domain_evaluated':False,'full_real_cut_uniqueness_proved':False,
        'same_value_distinct_representatives':['baseline','alias']}


def candidate_checks():
    doc=parse(generic_composed()[0]+'''
r ja[] h[b] c.r jb[] h[b] c.r jc[] h[h[b] c] c.r jd[] h[h[b] c] c.
r je[] h[h[b] c h[b] c] c.
q[k sbx[k ja[] k jb[] k jc[] k jd[] k je[]]].''')
    rows=[]
    for validvalue,validbase,measured,comparison in product((False,True),repeat=4):
        model={**ARITHMETIC,'ja':lambda:cut(4),'jb':lambda:cut(5)}
        callbacks(doc,model,{
            'jc':lambda v:measured and fingerprint(v)==fingerprint(cut(4)),
            'jd':lambda v:validvalue if fingerprint(v)==fingerprint(cut(4)) else validbase if fingerprint(v)==fingerprint(cut(5)) else False,
            'je':lambda a,b:comparison and (fingerprint(a),fingerprint(b))==(fingerprint(cut(4)),fingerprint(cut(5)))})
        actual=values(doc,model,('object',))[0]
        if actual!=all((validvalue,validbase,measured,comparison)):raise ValueError('Candidate/baseline role differs')
        rows.append({'conditions':[validvalue,validbase,measured,comparison],'accepted':actual})
    return rows


def label_checks():
    doc=candidate(source_composed()[0],'''r ja[] h[b] c.r jb[] d.
q[k scg[k ja[] k jb[]]].q[k sch[k ja[] k jb[]]].''')
    domain=('rod','otherrod','movingframe','restframe','unit','other')
    rows={}
    for name in ('baseline','wrong_rod','wrong_moving_frame','wrong_rest_frame','wrong_unit','wrong_value',
                 'wrong_context','rod_type_missing','frame_type_missing','motion_missing','length_relation_missing'):
        model=guarded(doc)
        model.update(ja=lambda:cut(6 if name=='wrong_value' else 5),jb=lambda:'other' if name=='wrong_context' else 'direct',
            xi=lambda:'otherrod' if name=='wrong_rod' else 'rod',xl=lambda:'other' if name=='wrong_moving_frame' else 'movingframe',
            ra=lambda:'other' if name=='wrong_rest_frame' else 'restframe',ta=lambda:'other' if name=='wrong_unit' else 'unit',
            xa=lambda rod:name!='rod_type_missing' and rod=='rod',va=lambda f:name!='frame_type_missing' and f in ('movingframe','restframe'),
            ti=lambda unit:unit=='unit',xm=lambda *args:name!='motion_missing' and args==('rod','restframe','direct'),
            za=lambda rod,frame,unit,value,ctx:name!='length_relation_missing' and
                rod=='rod' and frame in ('movingframe','restframe') and (unit,ctx)==('unit','direct') and fingerprint(value)==fingerprint(cut(5)))
        actual=values(doc,model,domain)
        expected=[True,True] if name=='baseline' else [False,True] if name=='wrong_moving_frame' else [True,False] if name in ('wrong_rest_frame','motion_missing') else [False,False]
        if actual!=expected:raise ValueError('Frame-relative length name differs: '+name)
        rows[name]=actual
    return rows


def question_checks():
    doc=candidate(source_composed()[0],'''r ja[] h[h[b] c d] c.r jb[] d.r jc[] h[b] c.
q[h[k sce[k ja[] k jb[]]][k jc[]]].''')
    rows={}
    for name in ('correct_method_b_setting','wrong_method_a_setting','different_candidate','empty_candidates'):
        model=guarded(doc)
        model.update(jb=lambda:'direct' if name=='wrong_method_a_setting' else 'slice',jc=lambda:cut(5 if name=='different_candidate' else 4))
        callbacks(doc,model,{'ja':lambda v,ctx:name!='empty_candidates' and ctx=='slice' and fingerprint(v)==fingerprint(cut(4))})
        actual=values(doc,model,('object',))[0]
        if actual!=(name=='correct_method_b_setting'):raise ValueError('Announced value-question setting differs')
        rows[name]=actual
    return rows


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-4:]
    rows={}
    names=('baseline','names_swapped','method_name_wrong_scope','wrong_author','wrong_scope',
        'equality_based_on_second_principle','wrong_equality_conclusion','missing_second_principle',
        'duplicated_first_principle','whole_question_instead_of_method_b','equality_instead_of_difference',
        'wrong_future_argument','premise_order_irrelevant')
    def ref(description):return json.loads(description.syntax)['symbol']
    for name in names:
        model=guarded(doc)
        for key,value in {'ze':'namea','zf':'nameb','zg':'claim','zh':'forecast','zi':'future','rd':'author','xy':'scope','ri':'text'}.items():
            model[key]=lambda value=value:value
        def common(author,scope,context):
            return (author,scope,context)==('other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','text')
        def naming(node,author,method,label,scope,context):
            pairs={('namea','sbi','sch' if name=='names_swapped' else 'scg'),('nameb','sbk','scg' if name=='names_swapped' else 'sch')}
            return (node,ref(method),ref(label)) in pairs and common(author,scope,context) and name!='method_name_wrong_scope'
        def necessary(node,author,premise,conclusion,scope,context):
            return node=='claim' and common(author,scope,context) and ref(premise)==('sbd' if name=='equality_based_on_second_principle' else 'saw') and ref(conclusion)==('scd' if name=='wrong_equality_conclusion' else 'scc')
        def announced(node,author,question,conclusion,premises,later,scope,context):
            expected=('saw',) if name=='missing_second_principle' else ('saw','saw') if name=='duplicated_first_principle' else ('sbd','saw') if name=='premise_order_irrelevant' else ('saw','sbd')
            actual=tuple(ref(item) for item in premises.items)
            return node=='forecast' and common(author,scope,context) and sorted(actual)==sorted(expected) and ref(question)==('sbv' if name=='whole_question_instead_of_method_b' else 'scf') and ref(conclusion)==('scc' if name=='equality_instead_of_difference' else 'scd') and later==('other' if name=='wrong_future_argument' else 'future')
        model.update(zb=naming,zc=necessary,zd=announced)
        actual=values(doc,model,('namea','nameb','claim','forecast','future','author','scope','other'))
        expected=[name not in ('names_swapped','method_name_wrong_scope','wrong_author','wrong_scope')]*2+[
            name not in ('equality_based_on_second_principle','wrong_equality_conclusion','wrong_author','wrong_scope'),
            name not in ('missing_second_principle','duplicated_first_principle','whole_question_instead_of_method_b','equality_instead_of_difference','wrong_future_argument','wrong_author','wrong_scope')]
        if actual!=expected:raise ValueError('Naming/assertion/forecast attribution differs: '+name)
        rows[name]=actual
    return {'cases':rows,'quoted_physical_contents_executed':False,'derivation_completed':False}


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    rows=[]
    for number,digest,math_id,defs in (
        (32,'ff35a78f76f77ce3f65e86eea9d15cd83e63476419d1e21f8feee74735cb2e8f','M0049',['scc','scg']),
        (33,'f79ea394dd42e866834c293d86e024debc5e2cab15a2e317e595bcda8a5ee3f2','M0050',['scd','scf','sch']),
    ):
        unit=next(u for u in artifact['units'] if u['id']==f'einstein-1905:u{number:04d}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Rod comparison source changed')
        rows.append({'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],
            'definitions':defs,'status':'partial_explicit_reading','full_semantic_equivalence':False})
        math=next(m for m in artifact['math'] if m['id']==math_id)
        expected='98c9e8a3097d71b8a3ae6942906867f6b8a85ba1ac02c420d5fd664c66672255'
        if hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest()!=expected:raise ValueError('Initial-length reference changed')
        rows.append({'unit':unit['id'],'unit_sha256':digest,'math_id':math_id,'math_sha256':expected,
            'definitions':defs,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'verified_full_units':0}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored comparison differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Comparison roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/rod-comparison-basis-v1.json','data/einstein-rod-comparison-basis-v1.json',
        'examples/v014/einstein-rod-setup.noema','scripts/compose_rod_comparison.py','scripts/check_rod_comparison.py',
        'noema/discourse.py','noema/finite_semantics.py']
    previous=(ROOT/'examples/v014/einstein-rod-setup.noema').read_text(encoding='utf-8')
    current=source_composed()[0]
    return {'status':'partial_rod_length_naming_attributed_equality_and_announced_determination','documents':documents,
        'finite_sort_projection':projected_uniqueness(),'candidate_conditions':candidate_checks(),'labels':label_checks(),
        'value_question':question_checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'added_declarations_and_statements_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Rod comparison report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Length comparison roles, finite logical projection and non-factive argument attributions checked')


if __name__=='__main__':main()
