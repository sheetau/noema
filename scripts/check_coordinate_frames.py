"""Check material triads, alignment, instrument identity and comparison refinement."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_moving_light_trip import literal
from scripts.check_real_products import MEANINGS, ZERO, call, op, conjunction, assertion
from scripts.check_rod_comparison import guarded
from scripts.check_rod_measurements import ARITHMETIC, cut, fingerprint
from scripts.compose_coordinate_frames import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/coordinate-frames-v1.json'


def values(doc,model,domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('initial','comparison','text','other'),
        primitives=model,max_steps=3_000_000,memoize_definitions=True,memoize_expressions=True)]


def direction_checks():
    cases={
        'orthogonal_unit_axes':((1,0,0,0,1,0),(True,False)),
        'orthogonal_scaled_axes':((2,0,0,0,3,0),(True,False)),
        'orthogonal_oblique_axes':((1,1,0,1,-1,0),(True,False)),
        'same_direction':((1,0,0,3,0,0),(False,True)),
        'opposite_direction':((1,0,0,-2,0,0),(False,True)),
        'oblique_parallel':((1,2,3,2,4,6),(False,True)),
        'fractional_parallel':((1,2,3,Fraction(1,2),1,Fraction(3,2)),(False,True)),
        'neither_parallel_nor_orthogonal':((1,0,0,1,1,0),(False,False)),
        'zero_first':((0,0,0,1,0,0),(False,False)),
        'zero_second':((1,0,0,0,0,0),(False,False)),
        'both_zero':((0,0,0,0,0,0),(False,False)),
    }
    rows={}
    for name,(args,expected) in cases.items():
        doc=parse(generic_composed()[0]+''.join('q['+call(s,*(literal(x) for x in args))+'].' for s in ('sev','sew')))
        actual=values(doc,ARITHMETIC,('object',))
        if actual!=list(expected):raise ValueError('Axis direction condition differs: '+name)
        rows[name]=actual
    return rows


def polynomial_checks():
    a=[f'v {n}' for n in ('x','y','z')];b=[f'v {n}' for n in ('u','v','w')]
    claims={
        'perpendicular_is_symmetric':assertion('x y z u v w',op('z',call('sev',*a,*b),call('sev',*b,*a))),
        'parallel_is_symmetric':assertion('x y z u v w',op('z',call('sew',*a,*b),call('sew',*b,*a))),
        'nonzero_direction_is_parallel_to_itself':assertion('x y z',op('z',call('seu',*a),call('sew',*a,*a))),
        'nonzero_direction_is_not_perpendicular_to_itself':assertion('x y z',op('y',call('seu',*a),op('u',call('sev',*a,*a)))),
        'parallel_directions_must_have_identical_components':assertion('x y z u v w',op('y',call('sew',*a,*b),conjunction(*(op('e',x,y) for x,y in zip(a,b))))),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        expected='invalid' if name=='parallel_directions_must_have_identical_components' else 'valid'
        if result['status']!=expected:raise ValueError('Direction proof differs: '+name)
        rows[name]=result
    return rows


def source_checks():
    doc=candidate(source_composed()[0],'''
r ja[] d.r jb[] d.
q[k sfc[k ra[] k zbm[] k ja[]]].q[k sfd[k ra[] k zbm[] k ja[]]].
q[t[k sfe[]][k ri[]]].q[k sel[k zas[] k zat[] k ra[] k zbm[] k jb[]]].''')
    old=parse((ROOT/'examples/v014/einstein-relative-simultaneity.noema').read_text(encoding='utf-8'))
    before=deepcopy(next(d for d in old['declarations'] if d['name']=='sel'));before['name']='sfg'
    doc['declarations'].append(before)
    comparison=deepcopy(doc['statements'][-1]);comparison['body']['symbol']='sfg';doc['statements'].append(comparison)
    # Only the prior comparison's cut validity/equality are supplied as fixture
    # oracles. The axis/instrument composition executes its actual definitions.
    for i,d in enumerate(doc['declarations']):
        if d['name'] in ('ba','sca'):
            doc['declarations'][i]={'kind':'primitive','name':d['name'],
                'parameters':[p['sort'] for p in d['parameters']],'result':d['result']}
    names=('baseline','antiparallel_y','fixed_rotated_axes','parallel_but_offset_x','nonorthogonal_triad',
        'zero_direction','duplicate_axis','wrong_axis_role','axis_not_material','axis_not_rigid',
        'wrong_origin_assignment','axis_different_origin','missing_x_coincidence','missing_y_parallel',
        'ruler_not_rigid','ruler_wrong_type','missing_second_ruler','no_second_clocks','clock_wrong_type',
        'one_clock_different','only_some_clocks_match','outside_clock_different','same_ruler_instance',
        'different_ruler_specification','wrong_context','second_frame_already_moving','unknown_frame','zero_relative_speed')
    rows={}
    directions={'x1':(1,0,0),'y1':(0,1,0),'z1':(0,0,1),'x2':(1,0,0),'y2':(0,2,0),'z2':(0,0,3)}
    assigned={('frame1','xrole'):'x1',('frame1','yrole'):'y1',('frame1','zrole'):'z1',
        ('frame2','xrole'):'x2',('frame2','yrole'):'y2',('frame2','zrole'):'z2'}
    domain=('frame1','frame2','origin1','origin2','xrole','yrole','zrole',*directions,
        'ruler1','ruler2','clock1','clock2','clock3','clock4','outside','event1','event2','lengthunit','timeunit','other')
    for name in names:
        model=guarded(doc);model.update(ARITHMETIC)
        constants={'ja':'other' if name=='wrong_context' else 'initial','zb4':'other' if name=='wrong_context' else 'initial',
            'jb':'other' if name=='wrong_context' else 'comparison',
            'ra':'frame1','zbm':'frame2','yn':'xrole','yo':'yrole','yp':'zrole','ri':'text',
            'zas':'event1','zat':'event2','ta':'lengthunit','rb':'timeunit'}
        for k,v in constants.items():model[k]=lambda v=v:v
        vec=dict(directions)
        if name=='fixed_rotated_axes':vec.update(x2=(0,1,0),y2=(-1,0,0),z2=(0,0,1))
        if name=='antiparallel_y':vec['y2']=(0,-2,0)
        if name=='nonorthogonal_triad':vec['y2']=(1,1,0)
        if name=='zero_direction':vec['x2']=(0,0,0)
        origins={'origin1':(0,0,0),'origin2':(0,5,0) if name=='parallel_but_offset_x' else (5,0,0)}
        def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
        def parallel(a,b):return a in vec and b in vec and any(vec[a]) and any(vec[b]) and not any(cross(vec[a],vec[b]))
        def origin(line):return 'origin1' if line.endswith('1') else 'origin2'
        def coincident(a,b,ctx):
            if ctx not in ('initial','comparison') or name=='missing_x_coincidence' or not parallel(a,b):return False
            delta=tuple(y-x for x,y in zip(origins[origin(a)],origins[origin(b)]))
            return not any(cross(delta,vec[a]))
        def axis(frame,role,ctx):
            if name=='duplicate_axis' and (frame,role)==('frame2','yrole'):return 'x2'
            return assigned.get((frame,role),'other')
        rulers={'frame1':'ruler1','frame2':'ruler1' if name=='same_ruler_instance' else 'ruler2'}
        clocks={'frame1':{'clock1','clock2'},'frame2':set() if name=='no_second_clocks' else {'clock3','clock4'}}
        specs={c:'same' for c in ('clock1','clock2','clock3','clock4','outside')}
        if name=='outside_clock_different':specs['outside']='different'
        if name=='one_clock_different':specs['clock4']='different'
        if name=='only_some_clocks_match':specs.update(clock2='different',clock4='different')
        model.update(va=lambda frame:frame in ('frame1','frame2') and not(name=='unknown_frame' and frame=='frame2'),
            zbn=lambda frame,ctx:'origin1' if frame=='frame1' else 'origin2',zbo=axis,
            zbv=lambda frame,o,ctx:ctx in ('initial','comparison') and (frame,o) in (('frame1','origin1'),('frame2','origin2')) and name!='wrong_origin_assignment',
            zbw=lambda frame,line,role,ctx:ctx in ('initial','comparison') and assigned.get((frame,role))==line and not(name=='wrong_axis_role' and role=='xrole'),
            zbp=lambda line:line in vec and not(name=='axis_not_material' and line=='z2'),
            zbq=lambda obj,ctx:ctx in ('initial','comparison') and obj in (*vec,'ruler1','ruler2') and not(name=='axis_not_rigid' and obj=='x2' or name=='ruler_not_rigid' and obj=='ruler2'),
            zbr=lambda line,o,ctx:ctx in ('initial','comparison') and line in vec and o==origin(line) and not(name=='axis_different_origin' and line=='z2'),
            zbs=lambda a,b,ctx:ctx in ('initial','comparison') and a in vec and b in vec and any(vec[a]) and any(vec[b]) and sum(x*y for x,y in zip(vec[a],vec[b]))==0,
            zbt=lambda a,b,ctx:ctx in ('initial','comparison') and parallel(a,b) and not(name=='missing_y_parallel' and a=='y1'),zbu=coincident,
            zby=lambda frame,ctx:rulers.get(frame,'other'),
            zbx=lambda frame,ruler,ctx:ctx=='initial' and rulers.get(frame)==ruler and not(name=='missing_second_ruler' and frame=='frame2'),
            xc=lambda ruler:ruler in ('ruler1','ruler2') and not(name=='ruler_wrong_type' and ruler=='ruler2'),
            ca=lambda clock:clock in specs and not(name=='clock_wrong_type' and clock=='clock4'),
            zbz=lambda frame,clock,ctx:ctx=='initial' and clock in clocks.get(frame,set()),
            zb2=lambda a,b,ctx:ctx=='initial' and a in rulers.values() and b in rulers.values() and name!='different_ruler_specification',
            zb3=lambda a,b,ctx:ctx=='initial' and a in specs and b in specs and specs[a]==specs[b],
            x4=lambda obj,frame,ctx:ctx=='initial' and frame=='frame1' and obj in ('frame1','frame2') and not(name=='second_frame_already_moving' and obj=='frame2'),
            vb=lambda *args:args==('frame1','frame2','comparison'),vc=lambda *args:args==('frame1','frame2','comparison'),
            zbi=lambda *args:cut(0 if name=='zero_relative_speed' or args[-1]=='initial' else 3),
            ba=lambda value:fingerprint(value) in (fingerprint(cut(0)),fingerprint(cut(3))),
            sca=lambda a,b:fingerprint(a)==fingerprint(b))
        actual=values(doc,model,domain)
        geometry_bad=set(names[2:14])|{'wrong_context','unknown_frame'}
        equipment_bad=set(names[14:21])|{'same_ruler_instance','different_ruler_specification','wrong_context'}
        g,e=name not in geometry_bad,name not in equipment_bad
        expected=[g,e,g and e and name!='second_frame_already_moving',g and name!='zero_relative_speed',
            name not in ('unknown_frame','wrong_context','zero_relative_speed')]
        if actual!=expected:raise ValueError('Frame setup differs: '+name+' '+repr(actual)+' '+repr(expected))
        rows[name]=actual
    return {'cases':rows,'result_columns':['geometry','instruments','initial_setting','refined_comparison','previous_comparison'],
        'distinct_origins_and_distinct_axis_objects_accepted':True,
        'initial_rest_and_nonzero_motion_use_different_contexts':True,
        'clock_reading_primitive_executed':False,'instrument_agreement_covers_all_selected_clocks':True,
        'comparison_cut_validity_and_equality_are_integer_fixture_oracles':True,
        'full_real_geometry_evaluated':False}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-1:]
    rows={}
    for name in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_setting'):
        model=guarded(doc)
        for k,v in {'zb5':'node','rd':'author','rh':'scope','ri':'text'}.items():model[k]=lambda v=v:v
        model['ug']=lambda node,author,desc,scope,ctx:(node,author,scope,ctx)==('node',
            'other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope',
            'other' if name=='wrong_context' else 'text') and json.loads(desc.syntax)['symbol']==('sbt' if name=='wrong_setting' else 'sfe')
        actual=values(doc,model,('node','author','scope','other'))[0]
        if actual!=(name=='baseline'):raise ValueError('Coordinate setup attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0043')
    digest='dc4d3477894bd39f1690f063aa87594a28c16a5076843ab57123bbdf9ad7f7ce'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Frame source changed')
    hashes={'M0063':'05e2173afcb26f4b60597d5ea28c890a39c433570302700b3b66a40fd91b5023',
        'M0064':'2ad0085a85a116c56d9d4ba500fb7558d171e0bbf6dd05c93bb51bb674aca2a6',
        'M0065':'c912c500979e56eb818f0a914ae903cc477c24063e9ebbd8a31a9f9e8f1fda04'}
    rows=[{'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],
        'definitions':['sfb','sfc','sfd','sfe'],'status':'partial_explicit_reading','full_semantic_equivalence':False}]
    for key,digest_math in hashes.items():
        math=next(m for m in artifact['math'] if m['id']==key)
        if hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest()!=digest_math:raise ValueError('Axis label changed')
        rows.append({'unit':unit['id'],'unit_sha256':digest,'math_id':key,'math_sha256':digest_math,
            'definitions':['sfb','sfc'],'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'verified_full_units':0,'facsimile_checked':False}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored frame differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Frame roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/coordinate-frames-basis-v1.json','data/einstein-coordinate-frames-basis-v1.json',
        'examples/v014/einstein-relative-simultaneity.noema','scripts/compose_coordinate_frames.py','scripts/check_coordinate_frames.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    current=source_composed()[0];previous=(ROOT/'examples/v014/einstein-relative-simultaneity.noema').read_text(encoding='utf-8')
    return {'status':'partial_material_coordinate_frames_and_matching_instruments','documents':documents,
        'directions':direction_checks(),'polynomial':polynomial_checks(),'source_adapter':source_checks(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'semantic_revision':{'changed_inherited_definition':'sel','added_condition':'sfc',
            'reason':'Fixed relative orientation does not ensure orthogonal triads and aligned corresponding axes.',
            'frozen_predecessor_unchanged':True},
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'net_added_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Coordinate frame report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Material axes, geometric alignment, complete instrument agreement and comparison scope checked')


if __name__=='__main__':main()
