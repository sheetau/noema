"""Check frame-specific clocks and substitutions restricted to one light ray."""
import argparse
from fractions import Fraction
import hashlib
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, guarded
from scripts.check_real_products import MEANINGS, call, op, assertion
from scripts.check_moving_light_trip import literal
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.compose_longitudinal_light import ROOT, CUT, generic_composed, source_composed, frame_declarations

REPORT=ROOT/'reports/longitudinal-light-v1.json'
RAY_DOMAIN=('rs','ms','ray','depart','arrive','rest','moving','x','y','z','t','time','length','other','r0','r1','m0','m1','raxis','maxis')


def polynomial_checks():
    V,v,a,i,x,t,xi,extra=('v '+n for n in ('light','speed','scale','inverse','xprime','time','xi','extra'))
    add=lambda a,b:call('ab',a,b);mul=lambda a,b:call('ad',a,b);sub=lambda a,b:add(a,call('ac',b))
    ray=call('smx',V,v,x,t);inverse=call('sly',V,v,i);reduced=call('smy',V,a,i,x)
    amended=add(reduced,mul(extra,sub(x,mul(sub(V,v),t))))
    claims={
        'substitution_iff_reduced_longitudinal_coordinate':assertion('light speed scale inverse xprime time xi',op('y',op('w',ray,inverse),op('z',call('smz',V,v,a,i,x,t,xi),op('e',xi,reduced)))),
        'rest_light_path_gives_relative_origin_speed':assertion('light speed time',op('y',op('w',call('aa',literal(0),t),op('w',op('u',call('aa',v,literal(0))),call('aa',v,V))),call('smx',V,v,sub(mul(V,t),mul(v,t)),t))),
        'positive_relative_light_displacement':assertion('light speed xprime time',op('y',ray,call('aa',literal(0),x))),
        'longitudinal_formula_retains_free_scale':assertion('light scale inverse xprime other',op('e',call('smy',V,mul(a,'v other'),i,x),mul('v other',reduced))),
        'infinitely_many_functions_agree_on_the_selected_ray':assertion('light speed scale inverse xprime time extra',op('y',ray,op('e',amended,reduced))),
        'ray_agreement_forces_global_coordinate_formula':assertion('',op('e',add(call('smy',literal(5),literal(2),literal(Fraction(1,16)),literal(1)),literal(1)),call('smy',literal(5),literal(2),literal(Fraction(1,16)),literal(1)))),
        'relative_speed_uses_moving_clock_time':assertion('',op('y',call('smx',literal(5),literal(3),literal(8),literal(4)),op('e',literal(8),mul(literal(2),literal(5))))),
        'auxiliary_xprime_is_the_moving_xi':assertion('',op('e',literal(8),call('smy',literal(5),literal(2),literal(Fraction(1,16)),literal(8)))),
    }
    rejected={'ray_agreement_forces_global_coordinate_formula','relative_speed_uses_moving_clock_time','auxiliary_xprime_is_the_moving_xi'}
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Longitudinal algebra differs: '+name)
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'global_coordinate_transform_proved':False}


def reuse_checks():
    parent=parse((ROOT/'examples/v014/einstein-affine-time-form.noema').read_text(encoding='utf-8'))
    parent['declarations']+=frame_declarations(parent)
    # These declarations refer to the new local-time definition, so normalize in
    # the complete source document rather than an incomplete standalone parent.
    actual={d['name']:d for d in parse(source_composed()[0])['declarations']}
    source=parse(source_composed()[0])
    replacements={d['name']:d for d in parent['declarations'] if d['name'] in ('smu','smv')}
    source['declarations']=[replacements.get(d['name'],d) for d in source['declarations']]
    expected={d['name']:d for d in parse(format_graph(source,'compact'))['declarations']}
    if any(actual[n]!=expected[n] for n in replacements):raise ValueError('Frame-generalized law differs')
    return {'emission_path_and_unit_conditions_preserved':True,'local_times_explicitly_use_frame_reference_and_unique_event_time':True}


def frame_checks():
    doc=abstract(candidate(source_composed()[0],'r ja[] a.q[k smw[k ja[] k tc[] k zb6[]]].'),ARITHMETIC|{'qo','sgp','sax'})
    records={
        'restsegment':('rest','depart','arrive','rc0','rc1','rp0','rp1',0,4,20),
        'movingsegment':('moving','depart','arrive','mc0','mc1','mp0','mp1',0,5,25),
        'part':('moving','middle','arrive','mcm','mc1','mpm','mp1',Fraction(5,2),5,Fraction(25,2))}
    domain=tuple(dict.fromkeys((*records,*(x for row in records.values() for x in row[:7]),'ray','emitter','rref','mref','time','length','speed','other')))
    rows={}
    for label in ('rest_frame','moving_frame','moving_emitter','wrong_reference_clock','wrong_sync_frame','unsynchronized','wrong_end_read','bad_subsegment','empty_scope','incomplete_scope','wrong_emission_frame','wrong_path_frame','missing_vacuum','moving_measurement_clock','wrong_context','relative_speed_substituted'):
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        frame='rest' if label=='rest_frame' else 'moving';context='other' if label=='wrong_context' else 'motion'
        for k,v in {'ja':frame,'tc':5,'zb6':context,'rb':'time','ta':'length','tb':'speed'}.items():model[k]=(lambda v=v:c(v)) if k=='tc' else (lambda v=v:v)
        clocks={'rest':{'rc0','rc1','rref'},'moving':{'mc0','mc1','mcm','mref'}}
        places={(r[3],r[5],r[0]) for r in records.values()}|{(r[4],r[6],r[0]) for r in records.values()}|{(r[1],r[5],r[0]) for r in records.values()}|{(r[2],r[6],r[0]) for r in records.values()}
        readings={(r[3],r[1],r[0]):r[7] for r in records.values()}|{(r[4],r[2],r[0]):r[8] for r in records.values()}
        eventtimes={(r[1],r[0]):r[7] for r in records.values()}|{(r[2],r[0]):r[8] for r in records.values()}
        legs={('ray',r[1],r[2],r[0]) for r in records.values()}|{('ray','depart','middle','moving')}
        model.update(wa=lambda segment,f,tu,lu,ctx:segment in records and (f,tu,lu,ctx)==(records[segment][0],'time','length','motion') and label!='empty_scope',
            ws=lambda f,tu,lu,ctx:(tu,lu,ctx)==('time','length','motion') and label!='incomplete_scope',
            wf=lambda segment:'ray',wg=lambda segment:'emitter',wh=lambda segment:'depart',
            wi=lambda segment:records.get(segment,records['movingsegment'])[1],wj=lambda segment:records.get(segment,records['movingsegment'])[2],
            wk=lambda segment:records.get(segment,records['movingsegment'])[3],wl=lambda segment:records.get(segment,records['movingsegment'])[4],
            wm=lambda segment:records.get(segment,records['movingsegment'])[5],wn=lambda segment:records.get(segment,records['movingsegment'])[6],
            wo=lambda segment:c(records.get(segment,records['movingsegment'])[7]),
            wp=lambda segment:c(records.get(segment,records['movingsegment'])[8]+(1 if label=='wrong_end_read' and segment=='movingsegment' else 0)),
            wq=lambda segment:c(records.get(segment,records['movingsegment'])[9]+(1 if label=='bad_subsegment' and segment=='part' else 0)),
            cf=lambda ray:ray=='ray',wb=lambda emitter:emitter=='emitter',
            wc=lambda ray,emitter,event,f,ctx:(ray,emitter,event,ctx)==('ray','emitter','depart','motion') and label!='wrong_emission_frame',
            wd=lambda emitter,f,event,ctx:label!='moving_emitter',we=lambda emitter,f,event,ctx:label=='moving_emitter',
            cg=lambda *args:args in legs,tk=lambda *args:args in legs and label!='missing_vacuum',
            ti=lambda u:u=='length',tj=lambda lu,tu,su:(lu,tu,su)==('length','time','speed'),
            wr=lambda segment,ray,first,last,f,u,path,ctx:segment in records and (ray,first,last,f,u,ctx)==('ray',records[segment][1],records[segment][2],records[segment][0],'length','motion') and n(path)==records[segment][9]+(1 if label=='bad_subsegment' and segment=='part' else 0) and label!='wrong_path_frame',
            zbh=lambda f,ctx:'rref' if f=='rest' or label=='wrong_reference_clock' else 'mref',
            zbz=lambda f,clock,ctx:clock in clocks.get(f,set()) and ctx=='motion',
            ca=lambda clock:any(clock in group for group in clocks.values()),ci=lambda u:u=='time',
            cb=lambda *args:args in places,cc=lambda clock,f:clock in clocks.get(f,set()) and not(label=='moving_measurement_clock' and clock=='mc1'),
            ce=lambda clock,event,f,u,value:u=='time' and (clock,event,f) in readings and n(value)==readings[clock,event,f],
            qo=lambda clock,reference,f,u,ctx:clock in clocks.get(f,set()) and reference==('rref' if f=='rest' else 'mref') and (u,ctx)==('time','motion') and label not in ('unsynchronized','wrong_sync_frame'),
            sgp=lambda event,place,f,u,ctx,*args:(event,place,f) in places and (u,ctx)==('time','motion'),
            zbe=lambda event,f,u,ctx:c(eventtimes.get((event,f),0)),
            sax=lambda path,start,end,V:n(end)>n(start) and n(path)>0 and n(V)>0 and n(path)==(2 if label=='relative_speed_substituted' else n(V))*(n(end)-n(start)))
        actual=values(doc,model,domain)[0]
        if actual!=(label in ('rest_frame','moving_frame','moving_emitter')):raise ValueError('Frame-local light law differs: '+label)
        rows[label]=actual
    return {'cases':rows,'synchrony_unique_time_and_rate_are_oracles':True,'all_selected_subsegments_checked':True}


def ray_model(doc,label='baseline'):
    fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
    coords={'r0':[0,0,0,0],'r1':[20,0,0,4],'m0':[0,0,0,0],'m1':[25,0,0,5]}
    if label=='wrong_rest_time':coords['r1'][3]=5
    if label=='wrong_moving_time':coords['m1'][3]=4
    if label=='wrong_transverse_coordinate':coords['m1'][1]=1
    if label=='reverse_direction':coords['m1'][0]=-25
    if label=='xprime_substituted_for_xi':coords['m1'][0]=8
    speed=5 if label=='light_speed_boundary' else 3
    for k,v in {'ra':'rest','zbm':'moving','rb':'time','ta':'length','yn':'x','yo':'y','yp':'z','zc7':'t','zb6':'other' if label=='wrong_context' else 'motion','zez':'rs','zey':'ms'}.items():model[k]=lambda v=v:v
    model.update(tc=lambda:c(5),zb7=lambda:c(speed),
        wf=lambda segment:'other' if label=='different_ray' and segment=='rs' else 'ray',
        wi=lambda segment:'other' if label=='different_departure' and segment=='rs' else 'depart',
        wj=lambda segment:'other' if label=='different_arrival' and segment=='rs' else 'arrive',
        wh=lambda segment:'other' if label=='wrong_emission' else 'depart',
        wo=lambda segment:c(1 if label=='nonzero_emission_clock' else 0),wp=lambda segment:c(4 if segment=='rs' else 5),
        wq=lambda segment:c(19 if label=='wrong_path_length' and segment=='rs' else 20 if segment=='rs' else 25),
        wa=lambda segment,f,tu,lu,ctx:(segment,f) in (('rs','rest'),('ms','moving')) and (tu,lu,ctx)==('time','length','motion'),
        smk=lambda event,ctx:(event,ctx)==('depart','motion') and label!='wrong_origin',sfm=lambda ctx:ctx=='motion' and label!='wrong_motion',
        zdz=lambda event,f,ctx:('r' if f=='rest' else 'm')+('0' if event=='depart' else '1'),
        zc6=lambda record,role:c(coords[record][('x','y','z','t').index(role)]),
        shd=lambda event,record,f,ctx:event in ('depart','arrive') and ctx=='motion' and label!='missing_chart',
        zbo=lambda f,role,ctx:'raxis' if f=='rest' else 'maxis',
        zbw=lambda f,axis,role,ctx:role=='x' and ctx=='motion' and axis==('raxis' if f=='rest' else 'maxis'),
        zdw=lambda ray,first,last,axis,f,ctx:(ray,first,last,ctx)==('ray','depart','arrive','motion') and axis==('raxis' if f=='rest' else 'maxis') and label!='not_on_axis')
    callbacks(doc,model,{'zd4':lambda x,y,z,t:c(2*n(t)-Fraction(3,8)*n(x)+(1 if label=='wrong_tau_function' else 0)),
        'zeq':lambda v:c(3 if label=='wrong_phi_value' else 2)})
    primitive_names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {name:value for name,value in model.items() if name in primitive_names},fixture


def ray_checks():
    doc=abstract(candidate(source_composed()[0],'q[k snc[k zez[] k zey[] k zb6[]]].'),ARITHMETIC|{'smk','sfm','shd'})
    rows={}
    for label in ('baseline','different_ray','different_departure','different_arrival','wrong_emission','wrong_origin','wrong_motion','missing_chart','not_on_axis','wrong_transverse_coordinate','reverse_direction','wrong_rest_time','wrong_moving_time','nonzero_emission_clock','wrong_path_length','wrong_tau_function','wrong_context','light_speed_boundary'):
        model,_=ray_model(doc,label);actual=values(doc,model,RAY_DOMAIN)[0]
        if actual!=(label=='baseline'):raise ValueError('Same-ray coordinate binding differs: '+label)
        rows[label]=actual
    return {'cases':rows,'origin_motion_and_measurement_charts_are_oracles':True,'same_ray_and_same_events_required':True}


def equation_checks():
    text=''.join('q[k '+name+'[k wj[k zey[]] k zb6[]]].' for name in ('sng','snh','sni','snj'))
    doc=abstract(candidate(source_composed()[0],text),ARITHMETIC)
    rows={}
    cases={'baseline':[True]*4,'wrong_rest_time':[True,False,False,False],
        'wrong_moving_time':[False,True,True,True],'xprime_substituted_for_xi':[False,False,True,False],
        'wrong_phi_value':[True,False,True,False],'light_speed_boundary':[True,False,False,False]}
    for label,expected in cases.items():
        model,_=ray_model(doc,label);actual=values(doc,model,RAY_DOMAIN)
        if actual!=expected:raise ValueError('Longitudinal equations differ: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'rest_time_four_and_moving_time_five_not_interchanged':True,'xprime_eight_and_xi_twenty_five_not_identified':True}


def premise_checks():
    doc=abstract(candidate(source_composed()[0],'q[k snk[k zez[] k zey[] k zb6[]]].'),ARITHMETIC|{'snc','sbc','smw','smu','smj'})
    rows={}
    for label in ('baseline','missing_ray_binding','missing_rest_law','missing_moving_law','wrong_rest_segment','wrong_moving_segment','missing_tau_form','wrong_context'):
        model,fixture=ray_model(doc,label);n=fixture.read
        model.update(snc=lambda r,m,ctx:(r,m,ctx)==('rs','ms','motion') and label!='missing_ray_binding',
            sbc=lambda V,ctx:n(V)==5 and ctx=='motion' and label!='missing_rest_law',
            smw=lambda f,V,ctx:f=='moving' and n(V)==5 and ctx=='motion' and label!='missing_moving_law',
            smu=lambda segment,V,ctx,sync,rate,f:n(V)==5 and ctx=='motion' and (segment,f) in (('rs','rest'),('ms','moving')) and not(label=='wrong_rest_segment' and segment=='rs') and not(label=='wrong_moving_segment' and segment=='ms'),
            smj=lambda fn,phi,V,v:n(V)==5 and n(v)==3 and n(phi(v))==2 and label!='missing_tau_form')
        actual=values(doc,model,RAY_DOMAIN)[0]
        if actual!=(label=='baseline'):raise ValueError('Law and formula premise connection differs: '+label)
        rows[label]=actual
    return {'cases':rows,'premise_components_are_oracles':True,'both_global_laws_and_same_local_segments_required':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-6:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_prior_result','wrong_coordinate_roles','wrong_task','wrong_principle_premise','wrong_light_equation','wrong_tau_rewrite','wrong_relative_time','wrong_substitution'):
        model=guarded(doc)
        for k,v in {'ze7':'easy','ze2':'principles','ze3':'light','ze4':'tau','ze5':'relative','ze6':'substitution','rd':'author','rh':'scope','ri':'text','zdb':'task','yn':'x','yo':'y','yp':'z'}.items():model[k]=lambda v=v:v
        symbol=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        def inference(node,a,p,d,s,c):
            expected={'principles':('snq' if label=='wrong_principle_premise' else 'sno','snp'),
                'light':('snq','sns' if label=='wrong_light_equation' else 'snr'),
                'relative':('snq','sns' if label=='wrong_relative_time' else 'snt')}
            return common(a,s,c) and node in expected and (symbol(p),symbol(d))==expected[node]
        def rewrite(node,a,p,before,after,s,c):
            expected={'tau':('snq','snr','snu' if label=='wrong_tau_rewrite' else 'sns'),
                'substitution':('snq' if label=='wrong_substitution' else 'snv','sns','snu')}
            return common(a,s,c) and node in expected and (symbol(p),symbol(before),symbol(after))==expected[node]
        model.update(zc=inference,zd3=rewrite,zf2=lambda node,a,result,roles,task,s,c:common(a,s,c) and node=='easy' and symbol(result)==('smo' if label=='wrong_prior_result' else 'smn') and roles.items==(('x','t','z') if label=='wrong_coordinate_roles' else ('x','y','z')) and task==('other' if label=='wrong_task' else 'task'))
        actual=values(doc,model,('author','easy','principles','light','tau','relative','substitution','scope','task','x','y','z'))
        expected=[True]*6
        if label in ('wrong_author','wrong_scope','wrong_context'):expected=[False]*6
        else:
            failures={'wrong_prior_result':0,'wrong_coordinate_roles':0,'wrong_task':0,'wrong_principle_premise':1,'wrong_light_equation':2,'wrong_tau_rewrite':3,'wrong_relative_time':4,'wrong_substitution':5}
            if label in failures:expected[failures[label]]=False
        if actual!=expected:raise ValueError('Longitudinal source attribution differs: '+label)
        rows[label]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'));rows=[]
    unit_hashes=['7a64a854f5f0e9b0ccc0f77a9a1f274fa96c5cdad236e9d700ea042b90a7fdc3','aa94bd3e0f6b1c6eeed2e6645daa5551af64e457da38517e9d3a5f3e5516c265','b81d9593a3f6c4f7d125fd1da37c9b1fb180574cfb728f3db3c70eda3053e079','2b5131095a90e9fcac122c4f7f1ada4febfe8d4a4f965255a6a05ef40abd0c86','83584137cfe4fa04af1ce694e048932946a896fa8948bbd6bc446b302e2af326','aa16c552cfa925ff2a9c5075b241092205859c663cced74a99c62356bb051a0a','d23a3772ad3457075d8dcc0aafbcca08c6ed6d1818ef4fb96fa182db18af0cd7','5475d594ee27aae1987431534cf0d107d90f68b90dab14de22415c2f8c8de7f2']
    math_hashes=['a48213d919fecaac10568845700049babe6411e8244bc12e80e5f16d92ba7553','fad146c158bc7dc725209b362adcee4dfb08d7da13a15bf61ab90897102da806','103f515a57432e988c887a7f1454e0bcceb13f6b751a41b5ccce4e4c35a95a57','695baf67fc513761a4deac11123599fae0e852085ad30788460339f4bf5fc68b','31d9f7dbb2f5d7d234f33a09ddd954dd1a960ba43d16bda138aaf1e647de7a07','c1496691feec349a10bdd6eeb098007a7c903ad36e03725834dcf246beae03a7','2f2fdc1fbf92378b4b4b7b6595b152caa0828803e8f25965683ea9be5076bba3','08988bc0474b17fc6221e99b95881d36f697f1885919cc18d830420f8df4d850','63bb86d88003726f1bf5e53aecc4cfd5bad7db88e14aa35de947885aaa19e863','5d313ada269dfc2378f1e53604207c23be5b19c12a7415b78f9838fcdfea5eef','695baf67fc513761a4deac11123599fae0e852085ad30788460339f4bf5fc68b','196c4b3c4659204175eac13f34174a0dfd02aba5681a5b18c92121d8a89cf837']
    definitions=[['smt','smu','smw','snc','sno','snp'],['sng','snr'],['snr','sns'],['snh','sns'],['sna','sni','snt'],['sni','snt'],['snv','snu'],['snb','snj','snu']]
    for index,(digest,defs) in enumerate(zip(unit_hashes,definitions),65):
        uid=f'einstein-1905:u{index:04d}';unit=next(u for u in artifact['units'] if u['id']==uid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Longitudinal source changed')
        rows.append({'unit':uid,'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],'definitions':defs,'status':'partial_explicit_reading','full_semantic_equivalence':False})
        for mid in unit['math_ids']:
            m=next(m for m in artifact['math'] if m['id']==mid);mdigest=math_hashes[int(mid[1:])-118]
            if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=mdigest:raise ValueError('Longitudinal math changed')
            rows.append({'unit':uid,'unit_sha256':digest,'math_id':mid,'math_sha256':mdigest,'definitions':defs,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'equations_restricted_to_selected_light_ray':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored longitudinal light differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Longitudinal roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/longitudinal-light-basis-v1.json','data/einstein-longitudinal-light-basis-v1.json',
        'examples/v014/einstein-affine-time-form.noema','examples/v014/affine-time-form.noema',
        'scripts/compose_longitudinal_light.py','scripts/check_longitudinal_light.py','scripts/check_tau_differential.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-affine-time-form.noema').read_text(encoding='utf-8')
    return {'status':'partial_longitudinal_light_coordinate_substitutions','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'preserved_law':reuse_checks(),'frame_local_clocks':frame_checks(),
        'same_ray':ray_checks(),'equations':equation_checks(),'premises':premise_checks(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Longitudinal report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Frame-local light law and longitudinal coordinate substitutions checked')


if __name__=='__main__':main()
