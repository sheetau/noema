"""Check x-vt invariance and the clock-bound question for moving-frame time."""
import argparse
from fractions import Fraction
import hashlib
import json

from noema.finite_semantics import SequenceValue, evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, embedding, guarded
from scripts.check_rod_measurements import ARITHMETIC, cut
from scripts.check_real_products import MEANINGS, call, op, assertion, ZERO
from scripts.check_moving_light_trip import literal
from scripts.compose_comoving_labels import ROOT, TAU, generic_composed, source_composed
from scripts.compose_homogeneous_coordinates import CUT, OP, SAME, VALID

REPORT=ROOT/'reports/comoving-labels-v1.json'


def values(doc,model,domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('motion','text','other'),
        primitives=model,max_steps=5_000_000,memoize_definitions=True,memoize_expressions=True)]


def polynomial_checks():
    sub=lambda a,b:call('ab',a,call('ac',b));mul=lambda a,b:call('ad',a,b);add=lambda a,b:call('ab',a,b)
    left=call('sif','v speed','v firstx','v firstt');right=call('sif','v speed','v lastx','v lastt')
    claims={
        'constant_auxiliary_coordinate_iff_uniform_displacement':assertion('speed firstx firstt lastx lastt',op('z',op('e',left,right),op('e',sub('v lastx','v firstx'),mul('v speed',sub('v lastt','v firstt'))))),
        'translated_trajectory_keeps_its_initial_label':assertion('speed origin time',op('e',call('sif','v speed',add('v origin',mul('v speed','v time')),'v time'),'v origin')),
        'recover_rest_position_from_auxiliary_coordinate':assertion('speed position time',op('e',add(call('sif','v speed','v position','v time'),mul('v speed','v time')),'v position')),
        'changing_speed_can_change_the_label':assertion('firstspeed secondspeed position time',op('e',call('sif','v firstspeed','v position','v time'),call('sif','v secondspeed','v position','v time'))),
        'auxiliary_label_automatically_equals_rescaled_coordinate':assertion('speed position time scale',op('e',call('sif','v speed','v position','v time'),mul('v scale',call('sif','v speed','v position','v time')))),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        expected='invalid' if name in ('changing_speed_can_change_the_label','auxiliary_label_automatically_equals_rescaled_coordinate') else 'valid'
        if result['status']!=expected:raise ValueError('Auxiliary coordinate rational lemma differs: '+name)
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'physical_stationarity_equivalence_proved':False}


def trajectory_checks(source=False):
    if source:
        doc=candidate(source_composed()[0],'r ja[] d.r jb[] '+VALID+'.r jc[] '+SAME+'.r jd[] '+SAME+'.r je[] '+OP+'.r jf[] '+OP+'.q[k sik[k ja[] k jb[] k jc[] k jd[] k je[] k jf[]]].')
    else:
        doc=parse(generic_composed()[0]+'''
r ja[a] c.r jb[a] c.r jc[] j[a].r jd[a a] c.r je[a a] c.r jf[a a a] h[b] c.r jg[] h[h[b] c h[b] c] c.
q[k sih[p ja p jb k jc[] p jd p je p jf k jg[]]].''')
    names=('baseline','middle_x_changes','middle_y_changes','middle_z_changes','second_point_changes',
        'missing_middle_coordinates','missing_middle_time','empty_points','empty_times','no_time_width',
        'moving_point_ignored','invalid_coordinate','wrong_speed','wrong_length_unit','wrong_time_unit','wrong_context','duplicate_axes')
    if not source:names=names[:11]+('duplicate_axes',)
    domain=('p','q','first','middle','last','x','y','z','rest','moving','length','time','speedunit')
    rows={};frames_seen=set()
    for name in names:
        times={'first':0,'middle':0 if name=='no_time_width' else 1,'last':0 if name=='no_time_width' else 2}
        def position(p,m,axis):
            time=times.get(m,0);base={'p':3,'q':-2}.get(p,0)
            value=base+time if axis=='x' else (0 if p=='p' else 1) if axis=='y' else 2
            if p=='p' and m=='middle' and name=='middle_'+axis+'_changes':value+=1
            if p=='q' and m=='last' and (name=='second_point_changes' or name=='moving_point_ignored') and axis=='x':value+=1
            if name=='invalid_coordinate' and p=='p' and m=='middle' and axis=='z':value=30
            return value
        selected=lambda p:name!='empty_points' and p in ('p','q') and (name!='moving_point_ignored' or p!='q')
        selected_time=lambda m:name!='empty_times' and m in times
        coordinate_available=lambda p,m:not(name=='missing_middle_coordinates' and (p,m)==('p','middle'))
        time_available=lambda m:not(name=='missing_middle_time' and m=='middle')
        if source:
            model=guarded(doc)
            constants={'ja':'other' if name=='wrong_context' else 'motion','ra':'rest','zbm':'moving',
                'ta':'time' if name=='wrong_length_unit' else 'length','rb':'length' if name=='wrong_time_unit' else 'time',
                'tb':'speedunit','yn':'x','yo':'x' if name=='duplicate_axes' else 'y','yp':'z'}
            for k,v in constants.items():model[k]=lambda v=v:v
            def measured(p,m,f,u,axis,ctx):
                frames_seen.add(f)
                return cut(position(p,m,axis))
            model.update(aa=lambda a,b:a<b,va=lambda f:f in ('rest','moving'),ci=lambda u:u=='time',ti=lambda u:u=='length',
                tj=lambda l,t,s:(l,t,s)==('length','time','speedunit'),zb7=lambda:cut(1),
                zbi=lambda f,g,l,t,ctx:cut(2 if name=='wrong_speed' else 1),
                zdi=lambda p,ctx:p in ('p','q') and name!='empty_points' and ctx=='motion',
                x4=lambda p,f,ctx:p in ('p','q') and (f,ctx)==('moving','motion') and (name!='moving_point_ignored' or p!='q'),
                ys=lambda m,ctx:selected_time(m) and ctx=='motion',
                zce=lambda p,m,f,u,ctx:coordinate_available(p,m) and (f,u,ctx)==('rest','length','motion'),
                zcf=lambda m,f,u,ctx:time_available(m) and (f,u,ctx)==('rest','time','motion'),
                yl=lambda m,f,u,ctx:cut(times.get(m,0)),ym=measured)
            callbacks(doc,model,{'jb':lambda v:abs(embedding(v))<25,'jc':lambda a,b:embedding(a)==embedding(b),
                'jd':lambda a,b:embedding(a)<embedding(b),'je':lambda a,b:cut(embedding(a)-embedding(b)),
                'jf':lambda a,b:cut(embedding(a)*embedding(b))})
        else:
            model={**ARITHMETIC,'ja':selected,'jb':selected_time,
                'jc':lambda:SequenceValue(('x','x','z') if name=='duplicate_axes' else ('x','y','z'),'"individual"'),
                'jd':lambda p,m:coordinate_available(p,m) and time_available(m),
                'je':lambda a,b:times.get(a,0)<times.get(b,0),
                'jf':lambda p,m,r:cut(position(p,m,r)-(times.get(m,0) if r=='x' else 0))}
            callbacks(doc,model,{'jg':lambda a,b:embedding(a)==embedding(b)})
        actual=values(doc,model,domain)[0]
        expected=name in ('baseline','moving_point_ignored')
        if actual!=expected:raise ValueError('Comoving point trajectory differs: '+name+repr(actual))
        rows[name]=actual
    if source and frames_seen!={'rest'}:raise ValueError('Moving-frame coordinates were substituted for x-vt')
    return {'cases':rows,'integer_embedding_oracles':True,'only_stationary_frame_coordinates_read':source,
        'continuous_time_interval_proved':False}


def time_question_checks():
    doc=abstract(candidate(source_composed()[0],'r ja[] '+TAU+'.q[k sio[k ja[]]].q[h[k sip[]][k ja[]]].'),
        {'shf','shg','she','shh','ba','sca','bf','shv'})
    coords={'a':(3,0,0,1),'b':(4,1,0,2),'c':(6,0,2,2),
        'd':(10,0,0,3),'e':(20,0,0,6),'f':(30,0,0,12)}
    roles=('x','y','z','t');domain=(*coords,*roles,'rest','moving','length','time')
    rows={}
    for name in ('baseline','uses_x_instead_of_xprime','wrong_shift_sign','uses_rest_time_only','ignores_time','ignores_y','ignores_z',
        'invalid_output','missing_correspondence','wrong_reference_speed','wrong_source_frame','wrong_target_frame','wrong_unit','wrong_context'):
        pairs={('a','d'),('b','e'),('c','f')}
        if name=='missing_correspondence':pairs.remove(('b','e'))
        model=guarded(doc)
        constants={'yn':'x','yo':'y','yp':'z','zc7':'t','ra':'moving' if name=='wrong_source_frame' else 'rest',
            'zbm':'rest' if name=='wrong_target_frame' else 'moving','ta':'time' if name=='wrong_unit' else 'length',
            'rb':'time','zb6':'other' if name=='wrong_context' else 'motion'}
        for k,v in constants.items():model[k]=lambda v=v:v
        def function(xp,y,z,t):
            x,y,z,t=(embedding(v) for v in (xp,y,z,t))
            if name=='invalid_output':return cut(31)
            if name=='uses_x_instead_of_xprime':x+=t
            if name=='uses_rest_time_only':return cut(t)
            return cut(x+(0 if name=='ignores_y' else 2*y)+(0 if name=='ignores_z' else 3*z)+(0 if name=='ignores_time' else t))
        model.update(shf=lambda x:x in ('a','b','c'),shg=lambda x:x in ('d','e','f'),she=lambda a,b:(a,b) in pairs,
            shh=lambda a,b:coords.get(a)==coords.get(b),ba=lambda v:abs(embedding(v))<30,sca=lambda a,b:embedding(a)==embedding(b),
            bf=lambda a,b:cut(embedding(a)+(1 if name=='wrong_shift_sign' else -1)*embedding(b)),
            shv=lambda a,b:cut(embedding(a)*embedding(b)),zb7=lambda:cut(1),
            zbi=lambda f,g,l,t,ctx:cut(1 if (f,g,l,t,ctx)==('rest','moving','length','time','motion') and name!='wrong_reference_speed' else 2),
            zc6=lambda tup,r:cut(coords.get(tup,(0,0,0,0))[roles.index(r)]))
        callbacks(doc,model,{'ja':function})
        actual=values(doc,model,domain)
        if actual!=[name=='baseline']*2:raise ValueError('Moving time function question differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'coordinate_correspondence_and_cut_operations_are_oracles':True,'tau_formula_derived':False}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-4:];rows={}
    for name in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_definition','wrong_stationarity','wrong_obviousness',
        'wrong_parent_task','wrong_question','wrong_clock_rule','wrong_subtask'):
        model=guarded(doc)
        constants={'zdj':'definition','zdk':'stationarity','zdl':'time_task','zdp':'purpose','zdb':'parent_task','rd':'author','rh':'scope','ri':'text'}
        for k,v in constants.items():model[k]=lambda v=v:v
        symbol=lambda d:json.loads(d.syntax)['symbol']
        def common(a,s,c):return (a,s,c)==('other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','other' if name=='wrong_context' else 'text')
        model.update(zdm=lambda n,a,d,s,c:common(a,s,c) and (n,symbol(d))==('definition','sif' if name=='wrong_definition' else 'sin'),
            uh=lambda n,a,d,s,c:common(a,s,c) and (n,symbol(d))==('stationarity','sil' if name=='wrong_stationarity' else 'sim'),
            zdg=lambda n,a,d,s,c:common(a,s,c) and (n,symbol(d))==('stationarity','sil' if name=='wrong_obviousness' else 'sim'),
            zdn=lambda n,a,p,d,s,c:common(a,s,c) and (n,p,symbol(d))==('time_task','other' if name=='wrong_parent_task' else 'parent_task','sio' if name=='wrong_question' else 'sip'),
            zdo=lambda n,a,d,t,s,c:common(a,s,c) and (n,symbol(d),t)==('purpose','sip' if name=='wrong_clock_rule' else 'sio','other' if name=='wrong_subtask' else 'time_task'))
        actual=values(doc,model,tuple(constants.values()))
        bad={'wrong_author','wrong_scope','wrong_context'}
        expected=[name not in bad|{'wrong_definition'},name not in bad|{'wrong_stationarity','wrong_obviousness'},
            name not in bad|{'wrong_parent_task','wrong_question'},name not in bad|{'wrong_clock_rule','wrong_subtask'}]
        if actual!=expected:raise ValueError('Definition, first subtask or clock purpose attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0048')
    digest='3c5d2ae9509876ee9f0bfb7f87bb80d968071fbf6b82d1aa365ffb062113ac95'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Comoving label source changed')
    rows=[{'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],
        'definitions':['sif','sig','sij','sik','sim','sin','sio','sip'],'status':'partial_explicit_reading','full_semantic_equivalence':False}]
    for math_id,expected,definitions in (
        ('M0084','ace89d769f91c7d4be64d38f5dab7bf5c2df9081513448a75da4adffc13da00f',['sif','sin']),
        ('M0085','2f2fdc1fbf92378b4b4b7b6595b152caa0828803e8f25965683ea9be5076bba3',['sik']),
        ('M0086','00c54ebd10cc5df750055f36c9ded18b8cb4393d7cbc5f9a2228543bea6bb95d',['sij','sik']),
        ('M0087','700a7fdfb3e6ad045fb18df09fc70eee7632677a54d49c061b0177d7e5bd8931',['sio','sip']),
        ('M0088','00c54ebd10cc5df750055f36c9ded18b8cb4393d7cbc5f9a2228543bea6bb95d',['sio']),
        ('M0089','5d313ada269dfc2378f1e53604207c23be5b19c12a7415b78f9838fcdfea5eef',['sio']),
        ('M0090','700a7fdfb3e6ad045fb18df09fc70eee7632677a54d49c061b0177d7e5bd8931',['sio']),
        ('M0091','2f2fdc1fbf92378b4b4b7b6595b152caa0828803e8f25965683ea9be5076bba3',['sio'])):
        math=next(m for m in artifact['math'] if m['id']==math_id)
        if hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest()!=expected:raise ValueError('Comoving label math changed: '+math_id)
        rows.append({'unit':unit['id'],'unit_sha256':digest,'math_id':math_id,'math_sha256':expected,
            'definitions':definitions,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,
        'facsimile_checked':False,'auxiliary_xprime_not_identified_with_xi':True,'verified_full_units':0}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored comoving label differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Comoving label roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/comoving-labels-basis-v1.json','data/einstein-comoving-labels-basis-v1.json',
        'examples/v014/einstein-homogeneous-coordinates.noema','scripts/compose_comoving_labels.py','scripts/check_comoving_labels.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    current=source_composed()[0];previous=(ROOT/'examples/v014/einstein-homogeneous-coordinates.noema').read_text(encoding='utf-8')
    return {'status':'partial_comoving_labels_and_synchronized_time_subtask','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'generic_trajectories':trajectory_checks(),'source_trajectories':trajectory_checks(True),
        'time_function_question':time_question_checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'added_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Comoving label report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Auxiliary-coordinate invariance, clock-time candidates and subtask attribution checked')


if __name__=='__main__':main()
