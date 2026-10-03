"""Check midpoint algebra, frame-bound trial records and synchronization scope."""
import argparse
import hashlib
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import embedding, guarded
from scripts.check_rod_measurements import cut
from scripts.check_real_products import MEANINGS, call, op, assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_axial_clock_trip import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/axial-clock-trip-v1.json'


def polynomial_checks():
    a,b,c,s,o=('v '+n for n in ('first','middle','last','scale','offset'))
    add=lambda x,y:call('ab',x,y);mul=lambda x,y:call('ad',x,y)
    sub=lambda x,y:add(x,call('ac',y))
    base=call('siq',a,b,c)
    claims={
        'mean_iff_equal_differences':assertion('first middle last',op('z',base,op('e',sub(b,a),sub(c,b)))),
        'mean_iff_doubled_middle':assertion('first middle last',op('z',base,op('e',add(a,c),add(b,b)))),
        'common_nonzero_affine_clock_change':assertion('first middle last scale offset',op('y','u[e['+s+']['+literal(0)+']]',op('z',base,call('siq',*(add(mul(s,x),o) for x in (a,b,c)))))),
        'midpoint_alone_implies_order':assertion('first middle last',op('y',base,call('aa',a,b))),
        'changing_only_reflection_clock_preserves_midpoint':assertion('first middle last offset',op('y',base,call('siq',a,add(b,o),c))),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        expected='invalid' if name in ('midpoint_alone_implies_order','changing_only_reflection_clock_preserves_midpoint') else 'valid'
        if result['status']!=expected:raise ValueError('Midpoint lemma differs: '+name)
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'general_real_cut_equivalence_proved':False}


def arithmetic(model):
    model.update(aa=lambda a,b:a<b,ba=lambda v:abs(embedding(v))<30,
        sca=lambda a,b:embedding(a)==embedding(b),bg=lambda a,b:embedding(a)<embedding(b),
        bd=lambda a,b:cut(embedding(a)+embedding(b)),bf=lambda a,b:cut(embedding(a)-embedding(b)),
        shv=lambda a,b:cut(embedding(a)*embedding(b)),bj=lambda scale,value:cut(scale*embedding(value)))


def midpoint_checks():
    doc=abstract(candidate(source_composed()[0],'''
r ja[] h[b] c.r jb[] h[b] c.r jc[] h[b] c.
q[k sis[k ja[] k jb[] k jc[]]].q[k sit[k ja[] k jb[] k jc[]]].'''),{'ba','sca','bd','bf','bg','shv','bj'})
    rows={}
    for name,(readings,expected) in {
        'ordinary':((0,2,4),True),'shifted_origin':((-4,-2,0),True),
        'rest_times_are_not_moving_readings':((0,3,4),False),
        'wrong_reflection_clock_origin':((0,4,4),False),
        'reversed_still_satisfies_equation':((4,2,0),True),
        'coincident_still_satisfies_equation':((2,2,2),True),
        'invalid_middle':((0,30,4),False),
    }.items():
        model=guarded(doc);arithmetic(model)
        for symbol,value in zip(('ja','jb','jc'),readings):model[symbol]=lambda value=value:cut(value)
        actual=values(doc,model,('object',))
        if actual!=[expected,expected]:raise ValueError('Cut midpoint differs: '+name)
        rows[name]=actual
    return {'cases':rows,'integer_embedding_operations_are_oracles':True,'equation_does_not_assert_causality':True}


def source_checks():
    doc=abstract(candidate(source_composed()[0],'q[k six[k zb6[]]].'),
        {'qo','sgp','shc','ba','sca','bg','bf','shv','bd','bj'})
    names=('baseline','negative_axial_label','missing_outward_leg','missing_return_leg','different_return_ray',
        'missing_reflection','wrong_axis_assignment','return_path_off_axis','wrong_origin','wrong_return_place',
        'wrong_return_clock','clock_not_stationary','clock_not_deployed','clocks_not_synchronized','wrong_trial_scope',
        'wrong_reading','rest_time_substituted','missing_local_time','duplicate_event','reversed_times',
        'missing_rest_tuple','swapped_event_tuples','wrong_auxiliary_label','xi_substituted','wrong_shift_sign',
        'wrong_y','wrong_z','wrong_return_label','zero_label','wrong_speed','wrong_reference_frame',
        'wrong_moving_frame','wrong_length_unit','wrong_time_unit','wrong_context','invalid_reading')
    domain=('trial','ca','cb','origin','mirror','depart','reflect','arrive','ray','xaxis','rest','moving','length','time',
        'speedunit','x','y','z','t','tuple0','tuple1','tuple2','other')
    rows={}
    for name in names:
        model=guarded(doc);arithmetic(model)
        constants={'zdq':'trial','zdr':'ca','zds':'cb','ra':'moving' if name=='wrong_reference_frame' else 'rest',
            'zbm':'rest' if name=='wrong_moving_frame' else 'moving','ta':'time' if name=='wrong_length_unit' else 'length',
            'rb':'length' if name=='wrong_time_unit' else 'time','tb':'speedunit','zb6':'other' if name=='wrong_context' else 'motion',
            'yn':'x','yo':'y','yp':'z','zc7':'t'}
        for key,value in constants.items():model[key]=lambda value=value:value
        label=-3 if name=='negative_axial_label' else 3
        coords={'tuple0':(0,0,0,0),'tuple1':(3+label,0,0,3),'tuple2':(4,0,0,4)}
        if name in ('wrong_y','wrong_z'):
            v=list(coords['tuple1']);v[1 if name=='wrong_y' else 2]=1;coords['tuple1']=tuple(v)
        if name=='wrong_return_label':coords['tuple2']=(5,0,0,4)
        byevent={'depart':'tuple0','reflect':'tuple1','arrive':'tuple2'}
        if name=='swapped_event_tuples':byevent['depart'],byevent['reflect']=byevent['reflect'],byevent['depart']
        reading={'depart':0,'reflect':2,'arrive':4}
        actual_clock_reading=reading.copy()
        if name=='wrong_reading':reading['arrive']=6
        if name=='rest_time_substituted':reading['reflect']=3
        if name=='reversed_times':reading={'depart':4,'reflect':2,'arrive':0};actual_clock_reading=reading.copy()
        if name=='invalid_reading':reading['reflect']=30;actual_clock_reading=reading.copy()
        placed={('ca','origin'),('cb','mirror'),('depart','origin'),('reflect','mirror'),('arrive','origin')}
        if name=='wrong_return_place':placed.remove(('arrive','origin'));placed.add(('arrive','mirror'))
        legs={('ray','depart','reflect','moving'),('ray','reflect','arrive','moving')}
        if name=='missing_outward_leg':legs.remove(('ray','depart','reflect','moving'))
        if name in ('missing_return_leg','different_return_ray'):
            legs.remove(('ray','reflect','arrive','moving'))
            if name=='different_return_ray':legs.add(('other','reflect','arrive','moving'))
        def clock_read(clock,event,frame,unit,value):
            correct='cb' if event=='reflect' or (name=='wrong_return_clock' and event=='arrive') else 'ca'
            return event in actual_clock_reading and (clock,frame,unit)==(correct,'moving','time') and embedding(value)==actual_clock_reading[event]
        def chart(event,tup,frame,ctx,sync,valid,same):
            return byevent.get(event)==tup and (frame,ctx)==('rest','motion') and not(name=='missing_rest_tuple' and event=='reflect')
        model.update(va=lambda f:f in ('rest','moving'),ci=lambda u:u=='time',ti=lambda u:u=='length',
            tj=lambda l,t,s:(l,t,s)==('length','time','speedunit'),zb7=lambda:cut(1),
            zbi=lambda f,g,l,t,ctx:cut(2 if name=='wrong_speed' or (f,g,l,t,ctx)!=('rest','moving','length','time','motion') else 1),
            zdt=lambda:cut(0 if name=='zero_label' else 4 if name in ('wrong_auxiliary_label','xi_substituted') else label),
            qc=lambda trial:'mirror' if name=='wrong_origin' else 'origin',qd=lambda trial:'mirror',
            qe=lambda trial:'depart',qf=lambda trial:'reflect',qg=lambda trial:'depart' if name=='duplicate_event' else 'arrive',
            qh=lambda trial:'ray',qi=lambda trial:cut(reading['depart']),qj=lambda trial:cut(reading['reflect']),qk=lambda trial:cut(reading['arrive']),
            qb=lambda ca,cb,f,u,ctx,tr:(ca,cb,f,u,ctx,tr)==('ca','cb','moving','time','motion','trial') and name!='wrong_trial_scope',
            zbn=lambda f,ctx:'origin',zbv=lambda f,o,ctx:(f,o,ctx)==('moving','origin','motion'),
            zbo=lambda f,r,ctx:'xaxis',zbw=lambda f,a,r,ctx:(f,a,r,ctx)==('moving','xaxis','x','motion') and name!='wrong_axis_assignment',
            zbz=lambda f,c,ctx:(f,ctx)==('moving','motion') and c in ('ca','cb') and not(name=='clock_not_deployed' and c=='cb'),
            zcu=lambda p,f,ctx:p in ('origin','mirror') and (f,ctx)==('moving','motion'),
            ca=lambda c:c in ('ca','cb'),cd=lambda a,b:(a,b)==('ca','cb'),
            cb=lambda o,p,f:(o,p) in placed and f=='moving',
            cc=lambda c,f:c in ('ca','cb') and f=='moving' and not(name=='clock_not_stationary' and c=='cb'),
            ce=clock_read,cf=lambda r:r in ('ray','other'),cg=lambda *args:args in legs,
            ch=lambda r,e,f:(r,e,f)==('ray','reflect','moving') and name!='missing_reflection',
            qo=lambda a,b,f,u,ctx:(a,b,f,u,ctx)==('ca','cb','moving','time','motion') and name!='clocks_not_synchronized',
            sgp=lambda e,p,f,u,ctx,*callbacks:(e,p) in placed and (f,u,ctx)==('moving','time','motion') and not(name=='missing_local_time' and e=='arrive'),
            zbe=lambda e,f,u,ctx:cut(actual_clock_reading.get(e,0)),
            zdw=lambda r,a,b,axis,f,ctx:(r,a,b,f) in legs and (axis,ctx)==('xaxis','motion') and not(name=='return_path_off_axis' and a=='reflect'),
            shc=chart,zc6=lambda tup,role:cut(coords.get(tup,(0,0,0,0))[('x','y','z','t').index(role)]))
        if name=='wrong_shift_sign':model['bf']=lambda a,b:cut(embedding(a)+embedding(b))
        actual=values(doc,model,domain)[0]
        if actual!=(name in ('baseline','negative_axial_label')):raise ValueError('Axial trial binding differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'clock_synchrony_local_time_and_rest_chart_are_oracles':True,
        'integer_embedding_operations_are_oracles':True,'general_physical_derivation_proved':False}


def synchronization_checks():
    doc=abstract(candidate(source_composed()[0],'''
q[k qo[k zdr[] k zds[] k zbm[] k rb[] k zb6[]]].
q[k qb[k zdr[] k zds[] k zbm[] k rb[] k zb6[] k zdq[]]].
q[k sit[k qi[k zdq[]] k qj[k zdq[]] k qk[k zdq[]]]].
'''),{'da','bi','ba','sca','bd','bf','bg','shv','bj'})
    rows={};domain=('ca','cb','origin','mirror','trial','second','moving','time','other')
    for name in ('baseline','selected_midpoint_fails','other_midpoint_fails','selected_trial_outside_scope',
        'scope_not_complete','empty_scope','invalid_other_reading'):
        model=guarded(doc);arithmetic(model)
        for k,v in {'zdr':'ca','zds':'cb','zbm':'moving','rb':'time','zb6':'motion','zdq':'trial'}.items():model[k]=lambda v=v:v
        selected=set() if name=='empty_scope' else {'second'} if name=='selected_trial_outside_scope' else {'trial','second'}
        reads={'trial':(0,3 if name in ('selected_midpoint_fails','selected_trial_outside_scope') else 2,4),
            'second':(10,13 if name=='other_midpoint_fails' else 30 if name=='invalid_other_reading' else 12,14)}
        model.update(qa=lambda c,f,ctx:c in ('ca','cb') and (f,ctx)==('moving','motion'),
            ca=lambda c:c in ('ca','cb'),cc=lambda c,f:c in ('ca','cb') and f=='moving',
            cb=lambda c,p,f:(c,p) in (('ca','origin'),('cb','mirror')) and f=='moving',ci=lambda u:u=='time',
            ql=lambda *args:name!='scope_not_complete',
            qb=lambda a,b,f,u,ctx,tr:(a,b,f,u,ctx)==('ca','cb','moving','time','motion') and tr in selected,
            da=lambda *args:True,bi=lambda a,b,c:2*embedding(b)==embedding(a)+embedding(c))
        for key in ('qc','qd','qe','qf','qg','qh'):model[key]=lambda tr:tr
        for key,index in (('qi',0),('qj',1),('qk',2)):model[key]=lambda tr,index=index:cut(reads.get(tr,(0,0,0))[index])
        actual=values(doc,model,domain)
        expected=[name in ('baseline','selected_trial_outside_scope'),name not in ('selected_trial_outside_scope','empty_scope'),
            name not in ('selected_midpoint_fails','selected_trial_outside_scope')]
        if actual!=expected:raise ValueError('Synchronization scope differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'synchrony_scope_logic_evaluated':True,'physical_protocol_and_real_midpoint_are_oracles':True,
        'single_passing_trial_does_not_establish_synchrony':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for name in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_assumption','wrong_premise','wrong_conclusion'):
        model=guarded(doc)
        for k,v in {'zdu':'setup','zdv':'inference','rd':'author','rh':'scope','ri':'text'}.items():model[k]=lambda v=v:v
        symbol=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','other' if name=='wrong_context' else 'text')
        model.update(ug=lambda n,a,d,s,c:common(a,s,c) and (n,symbol(d))==('setup','siz' if name=='wrong_assumption' else 'siy'),
            zc=lambda n,a,p,d,s,c:common(a,s,c) and (n,symbol(p),symbol(d))==('inference','six' if name=='wrong_premise' else 'siy','siy' if name=='wrong_conclusion' else 'siz'))
        actual=values(doc,model,('setup','inference','author','scope'))
        bad={'wrong_author','wrong_scope','wrong_context'}
        if actual!=[name not in bad|{'wrong_assumption'},name not in bad|{'wrong_premise','wrong_conclusion'}]:raise ValueError('Axial trial attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    rows=[]
    for uid,digest,defs in (
        ('einstein-1905:u0049','1138727944105c1b0671ae116c45b78bb597cbf9c6899f358b925cacab781b96',['siu','siv','siw','six','siy']),
        ('einstein-1905:u0050','ba635f46d0bbf84bfb67385be8910cd65f1d33686d93b744ef84b95e2d28d538',['sit','siz'])):
        unit=next(u for u in artifact['units'] if u['id']==uid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Axial trial source changed')
        rows.append({'unit':uid,'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],
            'definitions':defs,'status':'partial_explicit_reading','full_semantic_equivalence':False})
    for mid,digest,defs in (
        ('M0092','2f2fdc1fbf92378b4b4b7b6595b152caa0828803e8f25965683ea9be5076bba3',['siu']),
        ('M0093','44b0eab89825db77b853721064e6b0d03018b3c4a18ac9903adc711750187182',['siu','siz']),
        ('M0094','05e2173afcb26f4b60597d5ea28c890a39c433570302700b3b66a40fd91b5023',['siu']),
        ('M0095','5789f9fd8ca6ee1a7ad7b9d6fdd7d9d84bd2ac37e2e0869db607ee20d6aa8e62',['siv','siw']),
        ('M0096','51523aaa986ad981dc656a2452927294667e63e26dcbcec3f8fc1ca3850f67df',['siu','siz']),
        ('M0097','0abceef182324b52931be9eb3f4a9e1fb88145b9387952b4059eee4456747897',['siu','siz']),
        ('M0098','8d964d62564fa8399378d66eb5a43411472032f11712a8507a4361130a3d75af',['siq','sit','siz'])):
        m=next(m for m in artifact['math'] if m['id']==mid)
        if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Axial trial math changed: '+mid)
        unit=rows[1] if mid=='M0098' else rows[0]
        rows.append({'unit':unit['unit'],'unit_sha256':unit['unit_sha256'],'math_id':mid,'math_sha256':digest,
            'definitions':defs,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,
        'stationary_time_arguments_not_yet_expanded':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored axial trial differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Axial trial roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/axial-clock-trip-basis-v1.json','data/einstein-axial-clock-trip-basis-v1.json',
        'examples/v014/einstein-comoving-labels.noema','scripts/compose_axial_clock_trip.py','scripts/check_axial_clock_trip.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    current=source_composed()[0];previous=(ROOT/'examples/v014/einstein-comoving-labels.noema').read_text(encoding='utf-8')
    return {'status':'partial_axial_light_trial_and_moving_clock_midpoint','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'midpoint':midpoint_checks(),'source_trial':source_checks(),
        'synchronization_scope':synchronization_checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'added_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Axial trial report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Axial trip, clock midpoint and synchronization scope checked')


if __name__=='__main__':main()
