"""Verify trajectory constraints, stage bindings and method-tagged questions."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json

from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_real_products import MEANINGS, call, conjunction, op, assertion
from scripts.check_rod_measurements import ARITHMETIC, cut
from scripts.compose_rod_setup import ROOT, generic_composed, source_composed

REPORT = ROOT/'reports/rod-setup-v1.json'
SCENES = ('initial','motion','direct','slice','text','other')


def values(doc, model, domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=SCENES,primitives=model,
        max_steps=3_000_000,memoize_definitions=True,memoize_expressions=True)]


def guarded(doc):
    def forbidden(*args):
        raise ValueError('Unrelated primitive or full real-cut physical condition executed')
    return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}


def callbacks(doc, model, entries):
    declarations = {d['name']:d['result'] for d in doc['declarations']}
    for name, callback in entries.items():
        sort = declarations[name]
        model[name] = lambda sort=sort,callback=callback:FunctionValue(tuple(sort['parameters']),sort['result'],callback)


def embedding(value):
    """Decode ONLY supplied integer embeddings; this is not real-function equality."""
    # All inputs in these fixtures are constructed by cut(integer). Binary
    # search avoids spending the interpreter budget on 99 redundant probes.
    # It does not decide equality or integrality of an arbitrary real cut.
    low, high = -32, 66
    while low < high:
        middle = (low+high)//2
        if value(Fraction(middle)):
            low = middle+1
        else:
            high = middle
    if low == 66 or not value(Fraction(low-1)):
        raise ValueError('Outside the supplied integer fixture range')
    return low


def pair_condition(speed, first, last, firstx, lastx, firsty, lasty, firstz, lastz):
    return speed > 0 and first <= last and lastx-firstx == speed*(last-first) and firsty==lasty and firstz==lastz


def numeric_checks():
    cases = {
        'positive_motion':((2,-2,3,-7,3,4,4,-1,-1),True),
        'same_time_same_place':((2,3,3,5,5,4,4,-1,-1),True),
        'same_time_different_place':((2,3,3,5,6,4,4,-1,-1),False),
        'wrong_x_displacement':((2,-2,3,-7,2,4,4,-1,-1),False),
        'transverse_motion':((2,-2,3,-7,3,4,5,-1,-1),False),
        'other_transverse_motion':((2,-2,3,-7,3,4,4,-1,0),False),
        'zero_velocity':((0,0,2,1,1,4,4,-1,-1),False),
        'negative_velocity':((-2,0,2,1,-3,4,4,-1,-1),False),
        'reversed_time':((2,3,-2,3,-7,4,4,-1,-1),False),
    }
    rows = {}
    for name,(args,expected) in cases.items():
        def literal(x):
            q=Fraction(x)
            return 'n '+('u' if q<0 else 'p')+' '+number_word(abs(q.numerator))+' '+number_word(q.denominator)
        doc=parse(generic_composed()[0]+'q['+call('sbl',*(literal(x) for x in args))+'].')
        actual=values(doc,ARITHMETIC,('point',))[0]
        if actual!=expected:raise ValueError('Numeric trajectory differs: '+name)
        rows[name]=actual
    return rows


def polynomial_checks():
    v,a,b,x,y,z,k,j,r,s=('v '+n for n in 'v a b x y z k j r s'.split())
    add=lambda left,right:call('ab',left,right)
    base=call('sbl',v,a,b,x,y,z,z,k,k)
    claims={
        'time_origin_shift':assertion('v a b x y z k j',op('z',base,call('sbl',v,add(a,j),add(b,j),x,y,z,z,k,k))),
        'space_origin_shift':assertion('v a b x y z k j',op('z',base,call('sbl',v,a,b,add(x,j),add(y,j),z,z,k,k))),
        'positive_time_positive_x':assertion('v a b x y z k',op('y',conjunction(base,call('aa',a,b)),call('aa',x,y))),
        'same_time_same_x':assertion('v a b x y z k',op('y',conjunction(base,op('e',a,b)),op('e',x,y))),
        'point_separation_preserved':assertion('v a b x y z k r s',op('y',conjunction(base,call('sbl',v,a,b,r,s,z,z,k,k)),
            op('e',add(r,call('ac',x)),add(s,call('ac',y))))),
        'endpoint_pair_determines_intermediate_position':assertion('v a b x y z k j r',op('y',conjunction(base,call('aa',a,j),call('aa',j,b)),
            call('sbl',v,a,j,x,r,z,z,k,k))),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=('invalid' if name=='endpoint_pair_determines_intermediate_position' else 'valid'):
            raise ValueError('Trajectory polynomial claim differs: '+name)
        rows[name]=result
    return rows


def initial_checks():
    doc=candidate(source_composed()[0],'''r za[] d.r zb[] h[h[b] c] c.q[k sbp[k za[] k zb[]]].''')
    domain=('rod','ruler','initialobserver','laterobserver','frame','unit','other')
    rows={}
    cases=('distinct_initial_observer','rod_not_resting','ruler_not_resting','no_rigidity_assumption',
        'no_alignment','no_read','zero_length','wrong_context','wrong_unit','missing_observer_type')
    for name in cases:
        model=guarded(doc)
        model.update(za=lambda:'other' if name=='wrong_context' else 'initial',ya=lambda:cut(0 if name=='zero_length' else 5),
            xi=lambda:'rod',xj=lambda:'ruler',xk=lambda:'laterobserver',ra=lambda:'frame',ta=lambda:'other' if name=='wrong_unit' else 'unit',
            xa=lambda p:p=='rod',xc=lambda p:p=='ruler',xb=lambda p:name!='missing_observer_type' and p=='initialobserver',
            yt=lambda *args:name!='no_rigidity_assumption' and args==('rod','initial'),
            ti=lambda unit:unit=='unit',xd=lambda *args:name!='no_alignment' and args==('ruler','rod','frame','initial'),
            x4=lambda p,f,c:(f,c)==('frame','initial') and p in ('rod','ruler') and not(
                name=='rod_not_resting' and p=='rod' or name=='ruler_not_resting' and p=='ruler'),
            xe=lambda observer,ruler,rod,frame,unit,length,context:name!='no_read' and
                (observer,ruler,rod,frame,unit,context)==('initialobserver','ruler','rod','frame','unit','initial') and embedding(length)==5)
        callbacks(doc,model,{'zb':lambda length:embedding(length)>0})
        actual=values(doc,model,domain)[0]
        if actual!=(name=='distinct_initial_observer'):raise ValueError('Initial setting differs: '+name)
        rows[name]=actual
    return rows


def motion_checks():
    doc=candidate(source_composed()[0],'''r za[] d.r zb[] h[h[b] c h[b] c] c.
r zc[] h[h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c] c.
q[k sbr[k za[] k zb[] k zc[]]].''')
    domain=('rod','left','middle','right','tfirst','tmiddle','tlast','tduplicate','frame','lengthunit','timeunit','xaxis','yaxis','zaxis','other')
    times={'tfirst':-2,'tmiddle':0,'tlast':2,'tduplicate':0}
    offsets={'left':-6,'middle':-1,'right':4}
    base={'points':set(offsets),'moments':set(times),'speed':2,'complete':True,'coordinate_changes':{}}
    cases={'baseline':(base,True)}
    for name,changes in (
        ('middle_time_x_deviation',{('left','tmiddle','xaxis'):1}),
        ('interior_point_deviation',{('middle','tmiddle','xaxis'):1}),
        ('transverse_y_change',{('right','tlast','yaxis'):4}),
        ('transverse_z_change',{('right','tlast','zaxis'):3}),
        ('duplicate_time_different_position',{('right','tduplicate','xaxis'):5}),
    ):
        modified=deepcopy(base);modified['coordinate_changes']=changes;cases[name]=(modified,False)
    for name,key,new in (
        ('wrong_shared_velocity','speed',3),('zero_velocity','speed',0),('negative_velocity','speed',-2),
        ('empty_points','points',set()),('missing_endpoint','points',{'left','middle'}),
        ('empty_times','moments',set()),('one_time','moments',{'tmiddle'}),
        ('no_time_width','moments',{'tmiddle','tduplicate'}),('unconfirmed_complete_scope','complete',False),
    ):
        modified=deepcopy(base);modified[key]=new;cases[name]=(modified,False)
    for name in ('wrong_context','wrong_frame','wrong_length_unit','wrong_time_unit','axes_identified'):
        cases[name]=(deepcopy(base),False)
    rows={}
    for name,(facts,expected) in cases.items():
        model=guarded(doc)
        model.update(za=lambda:'other' if name=='wrong_context' else 'motion',xi=lambda:'rod',xn=lambda:'left',xo=lambda:'right',
            ra=lambda:'other' if name=='wrong_frame' else 'frame',ta=lambda:'other' if name=='wrong_length_unit' else 'lengthunit',
            rb=lambda:'other' if name=='wrong_time_unit' else 'timeunit',
            yn=lambda:'yaxis' if name=='axes_identified' else 'xaxis',yo=lambda:'yaxis',yp=lambda:'zaxis',yb=lambda:cut(facts['speed']),
            ci=lambda u:u=='timeunit',ti=lambda u:u=='lengthunit',
            yq=lambda *args:facts['complete'] and args==('rod','frame','motion'),
            yr=lambda p,rod,ctx:p in facts['points'] and (rod,ctx)==('rod','motion'),
            ys=lambda moment,ctx:moment in facts['moments'] and ctx=='motion')
        def time(moment,frame,unit,context):
            return cut(times.get(moment,0) if (frame,unit,context)==('frame','timeunit','motion') else 0)
        def position(point,moment,frame,unit,axis,context):
            if (frame,unit,context)!=('frame','lengthunit','motion') or point not in offsets or moment not in times:return cut(0)
            natural={'xaxis':offsets[point]+2*times[moment],'yaxis':3,'zaxis':2}[axis]
            return cut(facts['coordinate_changes'].get((point,moment,axis),natural))
        model.update(yl=time,ym=position)
        callbacks(doc,model,{'zb':lambda first,last:embedding(first)<embedding(last),
            'zc':lambda *args:pair_condition(*(embedding(arg) for arg in args))})
        actual=values(doc,model,domain)[0]
        if actual!=expected:raise ValueError('Full point/time selection differs: '+name)
        rows[name]=actual
    return {'cases':rows,'finite_fixture_points':3,'finite_fixture_moments':4,
        'supplied_integer_embedding_oracles':True,'continuous_time_physics_evaluated':False,
        'scope_completeness_is_an_explicit_assumption_not_inferred_from_samples':True}


def stage_checks():
    doc=candidate(source_composed()[0],'''r za[] h[d] c.r zb[] h[d] c.
q[t[k sbw[k za[] k zb[]]][k ri[]]].''')
    rows={}
    for name in ('baseline','initial_is_motion','methods_share_context','reverse_transition','wrong_axis','wrong_rod',
                 'missing_direct_connection','missing_slice_connection','initial_condition_false','motion_condition_false'):
        model=guarded(doc)
        model.update(yc=lambda:'motion' if name=='initial_is_motion' else 'initial',yd=lambda:'motion',ye=lambda:'direct',
            yf=lambda:'direct' if name=='methods_share_context' else 'slice',ri=lambda:'text',xi=lambda:'other' if name=='wrong_rod' else 'rod',
            ra=lambda:'frame',yn=lambda:'other' if name=='wrong_axis' else 'xaxis',
            yu=lambda *args:args==('rod','frame','xaxis','initial'),
            yv=lambda *args:args==(('rod','motion','initial') if name=='reverse_transition' else ('rod','initial','motion')),
            yx=lambda first,last:first=='motion' and last in ('direct','slice') and not(
                name=='missing_direct_connection' and last=='direct' or name=='missing_slice_connection' and last=='slice'))
        callbacks(doc,model,{'za':lambda ctx:name!='initial_condition_false' and ctx=='initial',
            'zb':lambda ctx:name!='motion_condition_false' and ctx=='motion'})
        actual=values(doc,model,('rod','frame','xaxis','other'))[0]
        if actual!=(name=='baseline'):raise ValueError('Stage binding differs: '+name)
        rows[name]=actual
    return rows


def question_checks():
    doc=candidate(source_composed()[0],'''r za[] h[h[b] c d] c.r zb[] h[h[b] c d] c.
r zc[] a.r zd[] h[b] c.q[h[k sbu[k za[] k zb[]]][k zc[] k zd[]]].''')
    rows={}
    cases={
        'direct_five':('directmethod',5,True),'slice_four':('slicemethod',4,True),
        'slice_five':('slicemethod',5,False),'direct_four':('directmethod',4,False),
        'unknown_method':('other',5,False),'same_method_identity':('directmethod',5,False),
        'contexts_swapped':('directmethod',5,False),'no_answers':('directmethod',5,False),
        'equal_values_allowed':('slicemethod',5,True),
        'multiple_candidates_allowed':('directmethod',6,True),
    }
    for name,(method,value,expected) in cases.items():
        model=guarded(doc)
        model.update(xw=lambda:'directmethod',xx=lambda:'directmethod' if name=='same_method_identity' else 'slicemethod',
            ye=lambda:'slice' if name=='contexts_swapped' else 'direct',yf=lambda:'direct' if name=='contexts_swapped' else 'slice',
            zc=lambda:method,zd=lambda:cut(value))
        callbacks(doc,model,{
            'za':lambda length,ctx:name!='no_answers' and ctx=='direct' and embedding(length) in ({5,6} if name=='multiple_candidates_allowed' else {5}),
            'zb':lambda length,ctx:name!='no_answers' and ctx=='slice' and embedding(length)==(5 if name=='equal_values_allowed' else 4)})
        actual=values(doc,model,('directmethod','slicemethod','other'))[0]
        if actual!=expected:raise ValueError('Method-tagged candidate differs: '+name)
        rows[name]=actual
    return rows


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-2:]
    rows={}
    for name in ('baseline','wrong_setup','wrong_question','wrong_author','wrong_scope'):
        model=guarded(doc)
        model.update(y2=lambda:'setupnode',y3=lambda:'questionnode',rd=lambda:'author',xy=lambda:'scope',ri=lambda:'text')
        def matches(node,author,description,scope,context,expectednode,expecteddefinition):
            return (node,author,json.loads(description.syntax)['symbol'],scope,context)==(expectednode,
                'other' if name=='wrong_author' else 'author',expecteddefinition,'other' if name=='wrong_scope' else 'scope','text')
        model['ug']=lambda *args:matches(*args,'setupnode','sbs' if name=='wrong_setup' else 'sbt')
        model['yz']=lambda *args:matches(*args,'questionnode','sbu' if name=='wrong_question' else 'sbv')
        actual=values(doc,model,('setupnode','questionnode','author','scope','other'))
        expected=[name not in ('wrong_setup','wrong_author','wrong_scope'),name not in ('wrong_question','wrong_author','wrong_scope')]
        if actual!=expected:raise ValueError('Setup/question attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0029')
    digest='468608189adc04c35f4f92607127cc2577e617272c6623fb0f2d9f8dbcf1d910'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Initial rod source changed')
    rows=[{'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),
        'source':unit['text'],'definitions':['sbl','sbm','sbn','sbp','sbr','sbt','sbv'],
        'status':'partial_explicit_reading','full_semantic_equivalence':False}]
    for math_id,expected,definitions in (
        ('M0043','98c9e8a3097d71b8a3ae6942906867f6b8a85ba1ac02c420d5fd664c66672255',['sbp','sbq']),
        ('M0044','05e2173afcb26f4b60597d5ea28c890a39c433570302700b3b66a40fd91b5023',['sbt']),
        ('M0045','35d6c10b7951f0b3bffc37d697478962ef369bf2966173f808ff56fa35d08280',['sbr','sbs']),
        ('M0046','05e2173afcb26f4b60597d5ea28c890a39c433570302700b3b66a40fd91b5023',['sbr','sbs']),
        ('M0047','4b492acb2c9720990d49fd35470cab7019a0426611b096321d6cb6f3838fd593',['sbl','sbm']),
    ):
        math=next(m for m in artifact['math'] if m['id']==math_id)
        if hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest()!=expected:raise ValueError('Rod setup symbol changed')
        rows.append({'unit':unit['id'],'unit_sha256':digest,'math_id':math_id,'math_sha256':expected,
            'definitions':definitions,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'verified_full_units':0}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose()
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored rod setup differs')
        doc=parse(text)
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Rod setup notation differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/rod-setup-basis-v1.json','data/einstein-rod-setup-basis-v1.json',
        'examples/v014/einstein-rod-measurements.noema','scripts/compose_rod_setup.py','scripts/check_rod_setup.py',
        'noema/discourse.py','noema/finite_semantics.py']
    previous=(ROOT/'examples/v014/einstein-rod-measurements.noema').read_text(encoding='utf-8')
    current=source_composed()[0]
    return {'status':'partial_rod_initial_setting_uniform_translation_and_question','documents':documents,
        'numeric':numeric_checks(),'polynomial':polynomial_checks(),'initial':initial_checks(),
        'motion':motion_checks(),'stages':stage_checks(),'questions':question_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),
            'added_declarations_and_statements_characters':len(current)-len(previous),
            'limit':'Includes reusable definitions and inherited library; not a completed translation compression ratio.'},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Rod setup report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Rod initial setting, point/time motion, stage bindings and method-tagged questions checked')


if __name__=='__main__':main()
