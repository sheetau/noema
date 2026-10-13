"""Check unit-aware outcomes and a shared hypothetical calibration trial."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_field_transform import setup, OPS
from scripts.compose_charge_calibration import ROOT, PARENT, CUT, composed, generic_composed

REPORT=ROOT/'reports/charge-calibration-v1.json'


def conversion_checks():
    doc=abstract(parse(generic_composed()[0]+'r ja[] a.r jb[] a.r jc[] b.r jd[] b.r je[] '+CUT+'.r jf[] '+CUT+'.q[k sbv2[k ja[] k jb[] k jc[] k jd[] k je[] k jf[]]].'),OPS)
    rows={};cases={
        'same_unit':('quantity','quantity',1,1,1,1,True),
        'different_unit_same_quantity':('quantity','quantity',2,1,F(1,2),1,True),
        'same_numbers_different_units':('quantity','quantity',2,1,1,1,False),
        'different_kind':('quantity','other',1,1,1,1,False),
        'zero_scale':('quantity','quantity',0,1,1,0,False),
        'negative_scale':('quantity','quantity',-1,1,-1,1,False),
        'opposite_values':('quantity','quantity',1,1,-1,1,False),
        'signed_quantity':('quantity','quantity',2,1,F(-1,2),-1,True),
    }
    for name,(leftkind,rightkind,leftscale,rightscale,left,right,expected) in cases.items():
        fixture,model=setup(doc);names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'};model={n:f for n,f in model.items() if n in names}
        model.update(ja=lambda:leftkind,jb=lambda:rightkind,jc=lambda:F(leftscale),jd=lambda:F(rightscale),je=lambda:fixture.make(left),jf=lambda:fixture.make(right))
        actual=values(doc,model,('quantity','other'))
        if actual!=[expected]:raise ValueError('Typed unit conversion differs: '+name)
        rows[name]=actual
    return {'cases':rows,'positive_multiplicative_scales_only':True,'quantity_kind_not_inferred_from_number':True}


CONSTANTS={'ra':'rest','zol':'first','zom':'second','zon':'trial','zoo':'event','zop':'length','zoq':'force','zor':'charge',
    'zos':'cm','zot':'dyn','zou':'charge-unit','zov':'distance-record','zow':'force-record','zox':'charge-record'}
DOMAIN=tuple(CONSTANTS.values())+('other',)


def source_checks():
    doc=abstract(candidate(composed()[0],'q[t[k sby2[]][k ri[]]].q[t[k sbz2[]][k ri[]]].q[t[k sca2[]][k ri[]]].'),OPS)
    base={
        'pairs':{('trial','first','second','rest','event','text')},'equal':{('first','second','rest','event','text')},
        'rest':{('first','rest','text')},'point':{('first','text')},
        'profiles':{('cm','length',F(1),'text'),('dyn','force',F(1),'text'),('charge-unit','charge',F(1),'text')},
        'readings':{('distance-record','trial','length','rest','event','cm',F(1),'text'),
            ('force-record','trial','force','rest','event','dyn',F(1),'text'),('charge-record','first','charge','rest','event','charge-unit',F(1),'text')},
    }
    cases={'baseline':(deepcopy(base),True,True)}
    for label,key in (('missing_pair','pairs'),('unequal_amounts','equal'),('first_not_at_rest','rest'),('not_pointlike','point')):
        changed=deepcopy(base);changed[key]=set();cases[label]=(changed,False,True)
    for label,key,index,value in (
        ('reversed_force_pair','pairs',1,'second'),('different_trial_event','pairs',4,'other'),('equal_amount_wrong_frame','equal',2,'other'),
        ('rest_in_other_frame','rest',1,'other'),('wrong_pair_context','pairs',5,'other')):
        changed=deepcopy(base);row=list(next(iter(changed[key])));row[index]=value;changed[key]={tuple(row)};cases[label]=(changed,False,True)
    for label,record,index,value in (
        ('distance_wrong_target','distance-record',1,'other'),('distance_wrong_event','distance-record',4,'other'),('distance_two','distance-record',6,F(2)),
        ('force_wrong_record','force-record',0,'other'),('force_wrong_target','force-record',1,'second'),('force_wrong_event','force-record',4,'other'),
        ('force_wrong_unit','force-record',5,'cm'),('force_wrong_kind','force-record',2,'length'),('force_two','force-record',6,F(2)),
        ('charge_wrong_body','charge-record',1,'second'),('charge_wrong_event','charge-record',4,'other'),('charge_two','charge-record',6,F(2)),
        ('charge_wrong_context','charge-record',7,'other')):
        changed=deepcopy(base);row=next(r for r in changed['readings'] if r[0]==record);changed['readings'].remove(row);replacement=list(row);replacement[index]=value;changed['readings'].add(tuple(replacement))
        cases[label]=(changed,record=='charge-record',record!='charge-record')
    for label,unit,index,value in (('distance_unit_wrong_kind','cm',1,'force'),('force_unit_wrong_scale','dyn',2,F(2)),('charge_unit_wrong_scale','charge-unit',2,F(2))):
        changed=deepcopy(base);row=next(r for r in changed['profiles'] if r[0]==unit);changed['profiles'].remove(row);replacement=list(row);replacement[index]=value;changed['profiles'].add(tuple(replacement))
        cases[label]=(changed,unit=='charge-unit',unit!='charge-unit')
    rows={}
    for label,(facts,calibration,unit) in cases.items():
        fixture,model=setup(doc)
        for name,value in CONSTANTS.items():model[name]=lambda value=value:value
        model.update(ri=lambda:'text',va=lambda frame:frame=='rest',zof=lambda *args:args in facts['profiles'],
            zog=lambda record,target,kind,frame,event,unit,value,ctx:(record,target,kind,frame,event,unit,fixture.read(value),ctx) in facts['readings'],
            zoh=lambda *args:args in facts['pairs'],zoi=lambda *args:args in facts['equal'],xm=lambda *args:args in facts['rest'],zok=lambda *args:args in facts['point'])
        actual=values(doc,model,DOMAIN)
        if actual!=[calibration,unit,calibration and unit]:raise ValueError('Calibration binding differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'all_outcomes_are_hypothetical_fixture_relations':True,'no_second_body_rest_requirement_added':True,
        'force_charge_and_pointlike_physical_meanings_not_verified':True}


def distinct_target_check():
    # The result relations deliberately allow the self-pair; sbx2 must reject it.
    doc=abstract(candidate(composed()[0],'q[t[k sby2[]][k ri[]]].'),OPS);fixture,model=setup(doc)
    for name,value in CONSTANTS.items():model[name]=lambda value=value:value
    model.update(zom=lambda:'first',ri=lambda:'text',va=lambda *a:True,zof=lambda *a:True,zog=lambda *a:True,
        zoh=lambda *a:True,zoi=lambda *a:True,xm=lambda *a:True,zok=lambda *a:True)
    actual=values(doc,model,DOMAIN)
    if actual!=[False]:raise ValueError('Same amount was confused with same object')
    return {'self_pair_rejected':True,'same_quantity_not_object_identity':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-1:];rows={}
    for index in range(-1,5):
        model=guarded(doc)
        for name,value in {'zoy':'node','rd':'author','zno':'scope','ri':'text'}.items():model[name]=lambda value=value:value
        expected=['node','author','sca2','scope','text']
        if index>=0:expected[index]='other'
        model['ug']=lambda node,who,content,scope,ctx:[node,who,json.loads(content.syntax)['symbol'],scope,ctx]==expected
        actual=values(doc,model,('node','author','scope','other'))
        if actual!=[index==-1]:raise ValueError('Hypothetical calibration attribution differs')
        rows[str(index)]=actual
    return {'cases':rows,'assumption_not_actual_observation':True,'quoted_measurement_contents_not_executed':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Calibration source inventory changed')
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0173')
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Calibration source changed')
    start=unit['text'].index('welche im ruhenden System');end=unit['text'].index(' Nach dem Relativitätsprinzip')
    base=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=['sbv2','sbw2','sbx2','sby2','sbz2','sca2'],status='partial_explicit_reading',full_semantic_equivalence=False)
    rows=[dict(base,start=start,end=end,source=unit['text'][start:end])]
    m=next(m for m in source['math'] if m['id']=='M0315')
    if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=m['sha256']:raise ValueError('Calibration frame reference changed')
    rows.append(dict(base,math_id=m['id'],math_sha256=m['sha256']))
    return {'segments':rows,'pointlike_noun_phrase_excluded_from_explicit_range':True,'physical_concept_gaps_remain_within_partial_range':True,
        'moving_frame_and_force_vector_identification_unwritten':True,'facsimile_scope':'u0173 is visible on stored printed p909; no whole-unit semantic verification','verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'charge-calibration'),(composed,'einstein-charge-calibration')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored calibration differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Calibration roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['statements'][:-1]!=parent['statements'] or doc['declarations'][:len(parent['declarations'])]!=parent['declarations']:raise ValueError('Parent calibration source changed')
    paths=list(documents)+['data/charge-calibration-basis-v1.json','data/einstein-charge-calibration-basis-v1.json',PARENT,
        'scripts/compose_charge_calibration.py','scripts/check_charge_calibration.py','scripts/check_field_transform.py','docs/quantities-v1.md',
        'data/field-scale-inverse-facsimile-v1.json','artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json','noema/discourse.py','noema/finite_semantics.py']
    return {'status':'partial_unit_charge_calibration_with_hypothetical_outcomes','documents':documents,
        'conversion':conversion_checks(),'source':source_checks(),'distinct_targets':distinct_target_check(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'parent_preserved':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Calibration report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Typed quantities, common calibration trial and hypothetical attribution checked')


if __name__=='__main__':main()
