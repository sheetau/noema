"""Check snapshot scope, counterpart identity and non-factive tacit assumption reports."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_measurements import ARITHMETIC, cut
from scripts.compose_geometric_replacement import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/geometric-replacement-v1.json'
SCENES=('motion','restrod','restdisc','restother','text')


def values(doc,model,domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=SCENES,primitives=model,
        max_steps=1_000_000,memoize_definitions=True,memoize_expressions=True)]


def guarded(doc):
    def forbidden(*args):raise ValueError('Quoted physical content unexpectedly executed')
    return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}


def key(value):
    # Supplied integer embeddings only. Not equality for arbitrary real cuts.
    return tuple(value(Fraction(i)) for i in range(-5,7))


def ref(description):return json.loads(description.syntax)['symbol']


def compared_results_projection():
    """Change only real-cut sort annotations to a finite value carrier."""
    original=parse(generic_composed()[0])
    cut_sort={'kind':'function','parameters':['number'],'result':'truth'}
    def replace(value):
        if value==cut_sort:return 'individual'
        if isinstance(value,dict):return {k:replace(v) for k,v in value.items()}
        if isinstance(value,list):return [replace(v) for v in value]
        return value
    doc=deepcopy(original)
    doc['declarations']=replace([d for d in original['declarations'] if d['name'] in ('sbx','sby','sck')])
    doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+'''
r ja[a] c.r jb[a] c.r jc[a] c.r jd[a a] c.q[k sck[p ja p jb p jc p jd]].''')
    domain=('five','fivealias','four','zero')
    numbers={'five':5,'fivealias':5,'four':4,'zero':0}
    subsets=[{p for p,b in zip(domain,bits) if b} for bits in product((False,True),repeat=4)]
    rows=[]
    for first,second in product(subsets,repeat=2):
        model={'ja':lambda p:p in first,'jb':lambda p:p in second,'jc':lambda p:numbers[p]>0,
            'jd':lambda a,b:numbers[a]==numbers[b]}
        actual=values(doc,model,domain)[0]
        first_values={numbers[p] for p in first};second_values={numbers[p] for p in second}
        expected=len(first_values)==1 and first_values==second_values and min(first_values)>0
        if actual!=expected:raise ValueError('Two-method existence/equality differs in finite sort projection')
        rows.append({'first':sorted(first),'second':sorted(second),'accepted':actual})
    return {'cases':rows,'projection':'Only real-cut sort annotations replaced by four individual representatives.',
        'real_cut_existence_or_uniqueness_evaluated':False}


def snapshot_checks():
    doc=parse(generic_composed()[0]+'''
r ja[a] c.r jb[a] c.r jc[a] c.q[k sci[p ja p jb p jc]].''')
    domain=('p0','p1','p2')
    subsets=[{p for p,b in zip(domain,bits) if b} for bits in product((False,True),repeat=3)]
    rows=[]
    for places,first,second in product(subsets,repeat=3):
        model={**ARITHMETIC,'ja':lambda p:p in places,'jb':lambda p:p in first,'jc':lambda p:p in second}
        actual=values(doc,model,domain)[0]
        expected=bool(first) and first==second and first<=places
        if actual!=expected:raise ValueError('Whole occupied set comparison differs')
        rows.append({'places':sorted(places),'first':sorted(first),'second':sorted(second),'accepted':actual})
    counterexamples=[]
    for first,second in (({'p0','p2'},{'p0','p1','p2'}),({'p0','p1'},{'p1','p2'})):
        model={**ARITHMETIC,'ja':lambda p:True,'jb':lambda p:p in first,'jc':lambda p:p in second}
        actual=values(doc,model,domain)[0]
        span=lambda points:max(int(p[1]) for p in points)-min(int(p[1]) for p in points)
        if actual or span(first)!=span(second):raise ValueError('Expected same-span/different-geometry counterexample')
        counterexamples.append({'first':sorted(first),'second':sorted(second),'common_x_span':span(first),'same_geometry':actual})
    return {'cases':rows,'equal_span_counterexamples':counterexamples,'continuous_space_evaluated':False}


def source_checks():
    doc=candidate(source_composed()[0],'''r ja[] h[h[b] c] c.q[k sco[k ja[]]].''')
    callbacksort=next(d['result'] for d in doc['declarations'] if d['name']=='ja')
    domain=('rod','disc','copy','frame','otherframe','p0','p1','p2')
    base={'selected':{'rod','disc'},'epoch':3,'actual_epoch':3,'frame':'frame','valid':True,
        'bodytypes':{'rod','disc'},'places':{'p0','p1','p2'},
        'rigid':{('rod','motion'),('rod','restrod'),('disc','motion'),('disc','restdisc')},
        'moving':{('rod','frame','motion'),('disc','frame','motion')},
        'resting':{('rod','frame','restrod'),('disc','frame','restdisc')},
        'counterparts':{('rod','motion','restrod'),('disc','motion','restdisc')},
        'complete':{('rod','motion'),('rod','restrod'),('disc','motion'),('disc','restdisc')},
        'occupied':{('rod','motion'):{'p0','p1'},('rod','restrod'):{'p0','p1'},
            ('disc','motion'):{'p0','p1','p2'},('disc','restdisc'):{'p0','p1','p2'}}}
    cases={'baseline_two_bodies_with_separate_rest_configurations':(base,True)}
    negative=deepcopy(base);negative.update(epoch=-3,actual_epoch=-3)
    cases['negative_epoch_allowed']=(negative,True)
    for name,field,item in (
        ('second_body_cannot_be_replaced','counterparts',('disc','motion','restdisc')),
        ('missing_motion','moving',('rod','frame','motion')),
        ('missing_rest','resting',('rod','frame','restrod')),
        ('not_rigid_while_moving','rigid',('rod','motion')),
        ('not_rigid_while_resting','rigid',('rod','restrod')),
        ('incomplete_moving_geometry','complete',('rod','motion')),
        ('incomplete_rest_geometry','complete',('disc','restdisc')),
        ('nonphysical_selected_object','bodytypes','disc'),
        ('occupied_point_has_wrong_type','places','p1'),
    ):
        changed=deepcopy(base);changed[field].remove(item);cases[name]=(changed,False)
    for name,field,value in (
        ('empty_selection','selected',set()),('wrong_epoch','epoch',4),('invalid_epoch','valid',False),
        ('wrong_frame','frame','otherframe'),
    ):
        changed=deepcopy(base);changed[field]=value;cases[name]=(changed,False)
    for name,occupied in (
        ('missing_interior_point',{'p0','p2'}),('extra_or_shifted_point',{'p1','p2'}),('empty_counterpart',set()),
    ):
        changed=deepcopy(base)
        changed['occupied']['disc' if name=='missing_interior_point' else 'rod','restdisc' if name=='missing_interior_point' else 'restrod']=occupied
        cases[name]=(changed,False)
    changed=deepcopy(base)
    changed['occupied']['copy','restrod']=changed['occupied'].pop(('rod','restrod'))
    cases['same_shape_on_a_different_body']=(changed,False)
    changed=deepcopy(base);changed['occupied']['rod','motion']=set();changed['occupied']['rod','restrod']=set()
    cases['both_shapes_empty']=(changed,False)
    changed=deepcopy(base)
    changed['counterparts'].remove(('rod','motion','restrod'));changed['counterparts'].add(('rod','motion','motion'))
    changed['resting'].add(('rod','frame','motion'))
    cases['same_context_is_not_a_rest_counterpart']=(changed,False)
    rows={}
    for name,(facts,expected) in cases.items():
        model=guarded(doc)
        model.update(ja=lambda:FunctionValue(tuple(callbacksort['parameters']),callbacksort['result'],lambda v:facts['valid'] and key(v)==key(cut(facts['epoch']))),
            yd=lambda:'motion',ra=lambda:facts['frame'],zp=lambda:cut(facts['epoch']),
            zn=lambda body,ctx:body in facts['selected'] and ctx=='motion',zm=lambda body:body in facts['bodytypes'],
            va=lambda frame:frame=='frame',zq=lambda *args:args in facts['rigid'],xm=lambda *args:args in facts['moving'],
            x4=lambda *args:args in facts['resting'],zl=lambda *args:args in facts['counterparts'],zj=lambda p:p in facts['places'],
            zo=lambda body,frame,epoch,ctx:frame=='frame' and key(epoch)==key(cut(facts['actual_epoch'])) and (body,ctx) in facts['complete'],
            zk=lambda point,body,frame,epoch,ctx:frame=='frame' and key(epoch)==key(cut(facts['actual_epoch'])) and point in facts['occupied'].get((body,ctx),set()))
        actual=values(doc,model,domain)[0]
        if actual!=expected:raise ValueError('Geometric replacement binding differs: '+name)
        rows[name]=actual
    return {'cases':rows,'finite_geometry_only':True,'real_time_validity_supplied_for_fixture_cuts':True,
        'all_physical_bodies_or_all_spatial_points_enumerated':False,'motion_histories_identified':False}


def tacit_checks():
    doc=candidate(source_composed()[0],'''q[t[k scq[]][k ri[]]].q[t[k scr[]][k ri[]]].''')
    rows={}
    for used,stated,common in product((False,True),repeat=3):
        model=guarded(doc)
        model.update(zr=lambda:'theory',xy=lambda:'scope',ri=lambda:'text',zs=lambda system,ctx:common and (system,ctx)==('theory','text'),
            zt=lambda system,desc,scope,ctx:used and ref(desc) in ('scl','scp') and (system,scope,ctx)==('theory','scope','text'),
            zu=lambda system,desc,scope,ctx:stated and ref(desc) in ('scl','scp') and (system,scope,ctx)==('theory','scope','text'))
        actual=values(doc,model,('theory','scope'))
        if actual!=[used and not stated and common]*2:raise ValueError('Tacit use versus explicit statement differs')
        rows[f'{int(used)}{int(stated)}{int(common)}']=actual
    # A different description with the same truth profile does not count as use.
    model=guarded(doc)
    model.update(zr=lambda:'theory',xy=lambda:'scope',ri=lambda:'text',zs=lambda *args:True,
        zt=lambda system,desc,scope,ctx:ref(desc)=='scc',zu=lambda *args:False)
    wrong=values(doc,model,('theory','scope'))
    if wrong!=[False,False]:raise ValueError('Different assumption description collapsed')
    rows['different_assumption']=wrong
    return rows


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-3:]
    rows={}
    for name in ('baseline','wrong_theory','wrong_author','wrong_scope','wrong_first_content','wrong_second_content','reverse_reformulation'):
        model=guarded(doc)
        for key,value in {'zv':'ascription','zw':'restatement','rd':'author','zr':'theory','xy':'scope','ri':'text'}.items():
            model[key]=lambda value=value:value
        def correct(author,scope,ctx):
            return (author,scope,ctx)==('other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','text')
        def attributed(node,author,content,scope,ctx):
            accepted={'scc' if name=='wrong_first_content' else 'scq','scd' if name=='wrong_second_content' else 'scr'}
            return node=='ascription' and correct(author,scope,ctx) and ref(content) in accepted
        def restated(node,author,theory,first,second,scope,ctx):
            pair=('scp','scl') if name=='reverse_reformulation' else ('scl','scp')
            return node=='restatement' and correct(author,scope,ctx) and theory==('other' if name=='wrong_theory' else 'theory') and (ref(first),ref(second))==pair
        model.update(uh=attributed,zx=restated)
        actual=values(doc,model,('ascription','restatement','author','theory','scope','other'))
        expected=[name not in ('wrong_first_content','wrong_author','wrong_scope'),name not in ('wrong_second_content','wrong_author','wrong_scope'),
            name not in ('wrong_theory','wrong_author','wrong_scope','reverse_reformulation')]
        if actual!=expected:raise ValueError('Tacit-assumption attribution or reformulation differs')
        rows[name]=actual
    return {'cases':rows,'attributed_contents_executed':False,'logical_equivalence_proved':False}


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0034')
    digest='5b9a7a24ec6a14ffcd5aadc69592c782881414508dd3865f8eff2a979feac9dd'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Conventional kinematics source changed')
    math=next(m for m in artifact['math'] if m['id']=='M0051')
    math_digest='5d313ada269dfc2378f1e53604207c23be5b19c12a7415b78f9838fcdfea5eef'
    if hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest()!=math_digest:raise ValueError('Snapshot epoch symbol changed')
    return {'segments':[{'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],
        'definitions':['sci','scj','scl','scm','scp','scq','scr'],'status':'partial_explicit_reading','full_semantic_equivalence':False},
        {'unit':unit['id'],'unit_sha256':digest,'math_id':'M0051','math_sha256':math_digest,
         'definitions':['scm','scp'],'status':'partial','full_semantic_equivalence':False}], 'verified_full_units':0}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored geometric replacement differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Geometric replacement roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/geometric-replacement-basis-v1.json','data/einstein-geometric-replacement-basis-v1.json',
        'examples/v014/einstein-rod-comparison.noema','scripts/compose_geometric_replacement.py','scripts/check_geometric_replacement.py',
        'noema/discourse.py','noema/finite_semantics.py']
    previous=(ROOT/'examples/v014/einstein-rod-comparison.noema').read_text(encoding='utf-8')
    current=source_composed()[0]
    return {'status':'partial_geometric_snapshot_replacement_and_tacit_assumption_reformulation','documents':documents,
        'compared_results_projection':compared_results_projection(),
        'snapshots':snapshot_checks(),'source_adapter':source_checks(),'tacit_use':tacit_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'added_declarations_and_statements_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Geometric replacement report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Whole snapshots, counterpart identity, tacit use and reformulation attributions checked')


if __name__=='__main__':main()
