"""Check identity, observer, unit and two-frame bindings without sampling proofs."""
import argparse
from fractions import Fraction as F
import hashlib
import json

from noema.finite_semantics import FunctionValue
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup, OPS, expected_values
from scripts.check_parallel_composition import transform
from scripts.check_rod_setup import callbacks
from scripts.compose_limits import call as k
from scripts.compose_wave_readings import ROOT, PARENT, CUT, FIELD, POINT, PROFILE, ROLES, pair_parameters, source_composed, core_composed

REPORT=ROOT/'reports/wave-readings-v1.json'
GLOBAL={'sdv2','sai2','saj2'}
AXES=('x','y','z','t')
IDS={'wave':'wave','electrickind':'electric-kind','magnetickind':'magnetic-kind',
    'oldframe':'rest','newframe':'moving','oldobserver':'rest-observer','newobserver':'moving-observer',
    'oldrecord':'rest-record','newrecord':'moving-record','oldevent':'rest-event','newevent':'moving-event',
    'oldunit':'rest-unit','newunit':'moving-unit'}
DOMAIN=(*AXES,*dict.fromkeys(IDS.values()),'other')
SAMPLES=((0,0,0,0),(1,0,0,1),(0,1,0,1),(-2,0,0,0),(1,2,-1,F(1,2)))
BASE=(F(5),F(3),F(2),F(0),F(1),F(0),F(3),F(0),F(4),F(4),F(0),F(-3))
POINTS={'rest':(0,1,0,F(1,2)),'moving':(1,2,0,F(1,2))}


def query_document(text,globals=GLOBAL):
    items=pair_parameters()
    declarations=''.join('r j'+n+'[] '+t+'.' for n,t in items)
    query='q['+k('seaq',*(k('j'+n) for n,t in items))+'].'
    return abstract(candidate(text,declarations+query),OPS|globals)


def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return values(doc,{n:f for n,f in model.items() if n in names},DOMAIN)


def model_for(doc,side=False,label='baseline'):
    fixture,model=setup(doc);make,read=fixture.make,fixture.read
    numeric=dict(zip(('light','speed','rate','ax','ay','az','ex','ey','ez','hx','hy','hz'),BASE))
    numeric.update(oldscale=F(2),oldvalue=F(5,2),newscale=F(5),newvalue=F(5,4))
    changes={'same_number_different_unit':('newvalue',F(5,2)),
        'wrong_new_amplitude':('newvalue',F(1)), 'negative_amplitude':('newvalue',F(-5,4)),
        'zero_unit_scale':('newscale',F(0)),'negative_unit_scale':('newscale',F(-5)),
        'wrong_frequency':('rate',F(3)), 'wrong_direction':('ay',F(-1)),
        'wrong_transverse_amplitude':('ez',F(5)), 'wrong_speed':('speed',F(-3))}
    if label in changes:numeric[changes[label][0]]=changes[label][1]
    for name,value in IDS.items():model['j'+name]=lambda value=value:value
    for name,value in numeric.items():
        model['j'+name]=(lambda value=value:value) if name.endswith('scale') else (lambda value=value:make(value))
    model['jcontext']=lambda:'other' if label=='wrong_context' else 'text'
    model['jmagneticside']=lambda:side
    kinds=('electric-kind','magnetic-kind');kind=kinds[int(side)]
    def inside(frame,point):
        old=transform(point,F(-3),F(5)) if frame=='moving' else point
        return old[0]>-1
    def field_values(frame,point):
        if frame=='moving':return expected_values(BASE,point,lambda phase:phase)
        phase=F(2)*(point[3]-point[1]/F(5))
        return [component*phase for component in BASE[6:]]
    def fingerprint(e,h):
        return tuple(tuple(read(field(role)(*(make(x) for x in p))) for field in (e,h) for role in AXES[:3]) for p in SAMPLES)
    def region_fingerprint(region):return tuple(region(*(make(x) for x in p)) for p in SAMPLES)
    def expected_fingerprint(frame):return tuple(tuple(field_values(frame,p)) for p in SAMPLES)
    def matching_fields(frame,e,h,region):
        return frame in ('rest','moving') and fingerprint(e,h)==expected_fingerprint(frame) and region_fingerprint(region)==tuple(inside(frame,p) for p in SAMPLES)
    fields={}
    declarations={d['name']:d for d in doc['declarations']}
    for prefix,frame in (('old','rest'),('new','moving')):
        for field,offset in (('electric',0),('magnetic',3)):
            symbol='j'+prefix+field;scalar=declarations[symbol]['result']['result']
            def component(role,frame=frame,offset=offset,scalar=scalar):
                def at(*xs):
                    point=tuple(map(read,xs));index=AXES.index(role) if role in AXES[:3] else None
                    value=field_values(frame,point)[offset+index] if index is not None else 0
                    if label=='wrong_new_field' and frame=='moving' and offset==0 and role=='z':value+=1
                    return make(value)
                return FunctionValue(tuple(scalar['parameters']),scalar['result'],at)
            fields[symbol]=component
        fields['j'+prefix+'region']=lambda *xs,frame=frame:True if label=='wrong_new_region' and frame=='moving' else inside(frame,tuple(map(read,xs)))
        fields['j'+prefix+'point']=lambda axis,frame=frame:make(POINTS[frame][AXES.index(axis)] if axis in AXES else 0)
    fields['jsine']=lambda x:make(read(x))
    fields['jcosine']=lambda x:make(2 if label=='wrong_cosine' else 1)
    def assigned(wave,frame,e,h,region,ek,hk,ctx):
        return (wave,ek,hk,ctx)==('other' if label=='wrong_wave_assignment' else 'wave',*kinds,'text') and matching_fields(frame,e,h,region)
    fields['jassigned']=assigned
    fields['jrecordedby']=lambda record,observer,ctx:(record,observer,ctx) in {
        ('rest-record','rest-observer','text'),('moving-record','other' if label=='wrong_record_observer' else 'moving-observer','text')}
    fields['jmotion']=lambda old,new,V,s,ctx:(old,new,read(V),read(s),ctx)==('rest','moving',F(5),F(-3) if label=='wrong_motion_binding' else F(3),'text')
    callbacks(doc,model,fields)
    model.update(va=lambda frame:frame in ('rest','moving'),cf=lambda wave:wave=='wave',
        xb=lambda who:who in ('rest-observer','moving-observer') and label!='not_an_observer',
        x4=lambda who,frame,ctx:(who,frame,ctx) in {('rest-observer','rest','text'),('moving-observer','other' if label=='observer_in_wrong_frame' else 'moving','text')},
        zpb=lambda who,frame,event,point,ctx:(who,frame,event,ctx) in {
            ('rest-observer','rest','rest-event','text'),('moving-observer','moving','other' if label=='wrong_coordinate_event' else 'moving-event','text')}
            and tuple(read(point(axis)) for axis in AXES)==POINTS[frame],
        znn=lambda frame,e,h,region,ctx:ctx=='text' and label!='missing_frame_field_assignment' and matching_fields(frame,e,h,region))
    profiles={('rest-unit',kind,F(2),'text'),('moving-unit',kind,F(5),'text')}
    records={('rest-record','wave',kind,'rest','rest-event','rest-unit',F(5,2),'text'),
             ('moving-record','wave',kind,'moving','moving-event','moving-unit',F(5,4),'text')}
    for prefix,facts in (('record',records),('unit',profiles)):
        replacements={'record':{'wrong_record_id':(0,'other'),'wrong_record_wave':(1,'other'),
            'wrong_record_kind':(2,kinds[1-int(side)]),'wrong_record_frame':(3,'rest'),
            'wrong_record_event':(4,'other'),'wrong_record_unit':(5,'rest-unit'),'wrong_record_context':(7,'other')},
            'unit':{'wrong_unit_kind':(1,kinds[1-int(side)]),'wrong_unit_scale':(2,F(2)),'wrong_unit_context':(3,'other')}}[prefix]
        if label in replacements:
            row=next(row for row in facts if row[0].startswith('moving'))
            facts.remove(row);new=list(row);index,value=replacements[label];new[index]=value;facts.add(tuple(new))
    model['zof']=lambda *args:args in profiles
    model['zog']=lambda rec,wave,kind,frame,event,unit,value,ctx:(rec,wave,kind,frame,event,unit,read(value),ctx) in records
    # Explicit abstraction boundary: this finite fixture's profile is linear,
    # not sine. The global harmonic predicate is supplied only to test wiring.
    model['sdv2']=lambda S,C:label!='missing_global_harmonic_condition' and read(S(make(0)))==0 and read(S(make(1)))==1 and read(C(make(0)))==1
    def same_fields(scale,e,h,ne,nh,region):
        if label=='missing_global_field_condition':return False
        inside_points=[p for p in SAMPLES if region(*(make(x) for x in p))]
        return bool(inside_points) and all(read(field(role)(*(make(x) for x in p)))*read(scale)==read(other(role)(*(make(x) for x in p)))
            for p in inside_points for field,other in ((e,ne),(h,nh)) for role in AXES[:3])
    model['sai2']=same_fields
    model['saj2']=lambda a,b:label!='missing_global_region_condition' and region_fingerprint(a)==region_fingerprint(b)
    return model


def binding_checks(texts):
    docs=[query_document(text) for text in texts]
    scenarios=('baseline','same_number_different_unit','wrong_new_amplitude','negative_amplitude','zero_unit_scale','negative_unit_scale',
        'wrong_frequency','wrong_direction','wrong_transverse_amplitude','wrong_speed','wrong_context','wrong_new_field','wrong_new_region',
        'wrong_cosine','wrong_wave_assignment','wrong_record_observer','wrong_motion_binding','not_an_observer','observer_in_wrong_frame',
        'wrong_coordinate_event','missing_frame_field_assignment','wrong_record_id','wrong_record_wave','wrong_record_kind','wrong_record_frame',
        'wrong_record_event','wrong_record_unit','wrong_record_context','wrong_unit_kind','wrong_unit_scale','wrong_unit_context',
        'missing_global_harmonic_condition','missing_global_field_condition','missing_global_region_condition')
    rows={}
    for side in (False,True):
        for label in scenarios:
            results=[evaluate(doc,model_for(doc,side,label)) for doc in docs]
            if results!=[[label=='baseline']]*2:raise ValueError('Wave reading binding differs: '+str((side,label,results)))
            rows[('magnetic:' if side else 'electric:')+label]=results[0]
    return {'cases':rows,'cumulative_and_standalone_agree':True,'global_conditions_are_explicit_fixture_oracles':True,
        'nonharmonic_profile_used_only_to_test_argument_wiring':True,'finite_samples_do_not_prove_full_field_equality':True,
        'physical_measurement_occurrence_verified':False}


def global_refusals(text):
    rows={}
    for name in sorted(GLOBAL):
        doc=query_document(text,GLOBAL-{name});model=model_for(doc)
        try:evaluate(doc,model)
        except ValueError as exc:
            if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
            rows[name]=str(exc)
        else:raise ValueError('Full real condition was certified by sampling: '+name)
    return rows


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Snapshot differs')
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0197')
    excerpt='die Amplitude der elektrischen oder magnetischen Kraft im ruhenden bez. im bewegten System gemessen'
    start=unit['text'].index(excerpt)
    return {'segments':[{'unit':unit['id'],'unit_sha256':unit['text_sha256'],'start':start,'end':start+len(excerpt),
        'source':excerpt,'definitions':['sean','seao','seap','seaq'],'status':'partial_explicit_reading',
        'review_ja':'二系で測る電気側または磁気側の振幅の部分対応。観測者の帰属・量の種類・単位・領域を明示する構成であり、原文の全意味や実測、光源、遠方近似、探索・命名の談話は未完。'}],
        'semantic_completion':False}


def build_report():
    documents={};sizes={};texts=[]
    for builder,stem in ((source_composed,'einstein-wave-readings'),(core_composed,'wave-readings-core')):
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored wave readings differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Wave reading roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]={'characters':len(text),'statements':len(doc['statements'])}
    source=parse(texts[0]);parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if source['declarations'][:len(parent['declarations'])]!=parent['declarations'] or source['statements']!=parent['statements']:raise ValueError('Parent changed')
    paths=[*documents,PARENT,'data/einstein-wave-readings-basis-v1.json','data/wave-readings-core-basis-v1.json',
        'scripts/compose_wave_readings.py','scripts/check_wave_readings.py','scripts/check_plane_waveforms.py',
        'scripts/check_tau_differential.py','scripts/check_angle_composition.py','scripts/check_parallel_composition.py',
        'noema/extraction.py','noema/finite_semantics.py','noema/discourse.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return json.loads(json.dumps({'status':'partial_frame_bound_amplitude_readings','documents':documents,'sizes':sizes,
        'bindings':binding_checks(texts),'global_refusals':global_refusals(texts[1]),'alignment':alignment(),
        'parent_preserved':True,'roundtrips':True,'new_primitives':0,'new_author_statements':0,
        'verified_full_units':{'kant-1784':0,'einstein-1905':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}},ensure_ascii=False))


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Wave reading report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Wave, frame, observer, kind, unit and record bindings checked')


if __name__=='__main__':main()
