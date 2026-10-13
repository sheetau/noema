"""Check rest/motion independently and preserve frame-local conditional forces."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, guarded
from scripts.check_field_transform import setup, OPS, affine_callback
from scripts.check_charge_calibration import CONSTANTS
from scripts.compose_rest_force import ROOT, PARENT, POINT, FIELD, composed, generic_composed, replace_symbol

REPORT=ROOT/'reports/rest-force-v1.json'
DOMAIN=tuple(CONSTANTS.values())+('x','y','z','t','moving','vector-force','moving-charge','old-force','new-force','force-event')
AXES=('x','y','z','t')


def rest_regression():
    rows={}
    for label,text in (('historical',(ROOT/PARENT).read_text(encoding='utf-8')),('corrected',composed()[0])):
        doc=abstract(candidate(text,'q[t[k sby2[]][k ri[]]].'),OPS)
        for resting in (False,True):
            for moving in (False,True):
                fixture,model=setup(doc)
                for name,value in CONSTANTS.items():model[name]=lambda value=value:value
                model.update(ri=lambda:'text',va=lambda *a:True,zof=lambda *a:True,zog=lambda *a:True,
                    zoh=lambda *a:True,zoi=lambda *a:True,zok=lambda *a:True,
                    x4=lambda *a:resting,xm=lambda *a:moving)
                actual=values(doc,model,DOMAIN)
                if actual!=[moving if label=='historical' else resting]:raise ValueError('Rest/motion regression differs')
                rows[f'{label}:rest={resting}:motion={moving}']=actual
    basis=json.loads((ROOT/'data/einstein-rod-setup-basis-v1.json').read_text(encoding='utf-8'))
    meanings={p['symbol']:p['meaning_ja'] for p in basis['primitives']}
    if '動いている' not in meanings['xm'] or '静止している' not in meanings['x4']:raise ValueError('Prior canonical motion/rest contracts changed')
    return {'cases':rows,'canonical_contracts':{n:meanings[n] for n in ('xm','x4')},
        'historical_test_reinterpreted_motion_as_rest':True,'only_sby2_reference_corrected':True}


def generic_checks():
    from noema.finite_semantics import SequenceValue
    text=generic_composed()[0]+'r ja[] '+FIELD+'.r jb[] '+POINT+'.r jc[] '+POINT+'.r jd[] j[a].q[k scb2[k jd[] k ja[] k jb[] k jc[]]].'
    doc=abstract(parse(text),OPS);rows={}
    matrix=((1,0,0,1,1),(0,2,0,0,0),(0,0,-1,0,0));point=(1,2,3,4);expected=(6,4,-3)
    for label in ('baseline','different_function_same_values','wrong_x','wrong_y','wrong_z','wrong_time','empty_axes','duplicate_axes'):
        fixture,model=setup(doc);names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'};model={n:f for n,f in model.items() if n in names}
        output=list(expected);position=list(point)
        if label.startswith('wrong_') and label!='wrong_time':output[AXES.index(label[-1])]+=1
        if label=='wrong_time':position[3]+=1
        axes=() if label=='empty_axes' else ('x','x') if label=='duplicate_axes' else AXES[:3]
        callbacks(doc,model,{'ja':affine_callback(doc,fixture,'ja',matrix),
            'jb':lambda axis:fixture.make(position[AXES.index(axis)] if axis in AXES else 0),
            'jc':lambda axis:fixture.make(output[AXES.index(axis)] if axis in AXES[:3] else 99 if label=='different_function_same_values' else 0)})
        model['jd']=lambda:SequenceValue(axes,'"individual"')
        actual=values(doc,model,AXES+('other',))
        if actual!=[label in ('baseline','different_function_same_values')]:raise ValueError('Pointwise vector comparison differs: '+label)
        rows[label]=actual
    return {'cases':rows,'values_compared_only_on_selected_components':True,'point_time_is_retained':True}


def charge_checks():
    doc=abstract(candidate(composed()[0],'q[t[k scc2[]][k ri[]]].'),OPS);rows={}
    baseline=('moving-charge','first','charge','moving','event','charge-unit',F(1),'text')
    cases={'baseline':baseline}
    for index,name in enumerate(('record','body','kind','frame','event','unit','value','context')):
        row=list(baseline);row[index]=F(2) if index==6 else 'other';cases['wrong_'+name]=tuple(row)
    for label,expected in cases.items():
        fixture,model=setup(doc)
        for name,value in CONSTANTS.items():model[name]=lambda value=value:value
        model.update(ri=lambda:'text',zbm=lambda:'moving',zpd=lambda:'moving-charge',va=lambda frame:frame=='moving',
            zof=lambda *a:a==('charge-unit','charge',F(1),'text'),
            zog=lambda record,body,kind,frame,event,unit,value,ctx:(record,body,kind,frame,event,unit,fixture.read(value),ctx)==expected)
        actual=values(doc,model,DOMAIN)
        if actual!=[label=='baseline']:raise ValueError('Charge frame binding differs: '+label)
        rows[label]=actual
    return {'cases':rows,'moving_record_not_copied_from_old_frame':True,'invariance_not_derived_from_principle_alone':True}


def premise_checks():
    from noema.finite_semantics import Content
    doc=abstract(candidate(composed()[0],'q[t[k scd2[]][k ri[]]].'),{'sca2','saw'});rows=[]
    for calibration in (False,True):
        for principle in (False,True):
            model=guarded(doc);model.update(ri=lambda:'text',
                sca2=lambda:Content(('motion','text','other'),(False,calibration,False)),
                saw=lambda:Content(('motion','text','other'),(False,principle,False)))
            actual=values(doc,model,('other',))
            if actual!=[calibration and principle]:raise ValueError('Charge inference premise differs')
            rows.append(dict(calibration=calibration,principle=principle,result=actual))
    return rows


def force_checks():
    doc=abstract(candidate(composed()[0],'q[t[k sce2[]][k ri[]]].q[t[k scf2[]][k ri[]]].'),OPS);rows={}
    oldpoint=(F(1),F(2),F(-1),F(1));newpoint=(F(-5,2),F(2),F(-1),F(11,10))
    matrices={'rest':((1,0,0,1,1),(0,2,0,0,0),(0,0,-1,0,0)),
        'moving':((0,1,0,0,2),(0,0,1,0,3),(0,0,0,2,0))}
    points={'rest':oldpoint,'moving':newpoint}
    labels=('baseline','neither_rest','only_old_rest','instantaneous_new_rest_without_interval_rest',
        'inactive_new_field','inactive_old_field','neither_rest_missing_fields',
        *(f'{side}_{error}' for side in ('old','new') for error in ('body','event','frame','context','unit','kind','record','point_time','outside','field_assignment','x','y','z')))
    for label in labels:
        fixture,model=setup(doc);cut,read=fixture.make,fixture.read
        pointvalues=dict(points)
        if label.endswith('point_time'):
            side='rest' if label.startswith('old') else 'moving';p=list(pointvalues[side]);p[3]+=1;pointvalues[side]=tuple(p)
        force={side:[F(row[4])+sum(a*b for a,b in zip(row,points[side])) for row in matrix] for side,matrix in matrices.items()}
        for side,prefix in (('rest','old'),('moving','new')):
            for index,axis in enumerate(AXES[:3]):
                if label==prefix+'_'+axis:force[side][index]+=1
        for name,value in {**CONSTANTS,'zbm':'moving','zpn':'vector-force','zpe':'old-force','zpf':'new-force','zpo':'force-event'}.items():model[name]=lambda value=value:value
        callbacks(doc,model,{name:affine_callback(doc,fixture,name,matrices[side]) for name,side in (('znl','rest'),('znr','moving'))})
        callbacks(doc,model,{name:affine_callback(doc,fixture,name,((0,0,0,0,0),)*3) for name in ('znm','zns')})
        for side,prefix,pn,fn,rn in (('rest','old','zpj','zpl','znk'),('moving','new','zpk','zpm','znt')):
            callbacks(doc,model,{pn:lambda axis,side=side:cut(pointvalues[side][AXES.index(axis)] if axis in AXES else 0),
                fn:lambda axis,side=side:cut(force[side][AXES.index(axis)] if axis in AXES[:3] else 0),
                rn:lambda *a,prefix=prefix:label!=prefix+'_outside'})
        def located(body,frame,event,point,ctx):
            return (body,event,ctx)==('first','force-event','text') and frame in points and tuple(read(point(a)) for a in AXES)==points[frame]
        def recorded(record,body,kind,frame,event,unit,vector,ctx):
            if frame not in points:return False
            prefix='old' if frame=='rest' else 'new'
            expected=[prefix+'-force','first','vector-force',frame,'force-event','dyn','text']
            for error,index in (('record',0),('body',1),('kind',2),('frame',3),('event',4),('unit',5),('context',6)):
                if label==prefix+'_'+error:expected[index]='other'
            return [record,body,kind,frame,event,unit,ctx]==expected and tuple(read(vector(a)) for a in AXES[:3])==tuple(force[frame])
        def assignment(frame,e,h,region,ctx):
            if frame not in points or ctx!='text':return False
            prefix='old' if frame=='rest' else 'new'
            sample=tuple(read(e(a)(*(cut(x) for x in points[frame]))) for a in AXES[:3])
            expected=tuple(F(row[4])+sum(a*b for a,b in zip(row,points[frame])) for row in matrices[frame])
            return label not in (prefix+'_field_assignment','inactive_'+prefix+'_field','neither_rest_missing_fields') and sample==expected
        oldrest=label not in ('neither_rest','instantaneous_new_rest_without_interval_rest','inactive_old_field','neither_rest_missing_fields')
        newrest=label not in ('neither_rest','only_old_rest','inactive_new_field','neither_rest_missing_fields')
        model.update(ri=lambda:'text',va=lambda f:f in points,zpb=located,zpc=recorded,znn=assignment,
            zof=lambda *args:args==('dyn','vector-force',F(1),'text'),
            x4=lambda body,frame,ctx:(body,frame,ctx)==('first','rest','text') and oldrest,
            xm=lambda *args:False,
            zpa=lambda body,frame,event,ctx:(body,frame,event,ctx)==('first','moving','force-event','text') and newrest)
        actual=values(doc,model,DOMAIN)
        expected=[not oldrest or not label.startswith('old_'),not newrest or not label.startswith('new_')]
        if actual!=expected:raise ValueError('Frame-local force differs: '+label+repr(actual)+repr(expected))
        rows[label]=actual
    return {'cases':rows,'different_frames_have_different_vector_values':True,
        'force_event_not_identified_with_calibration_event':True,
        'conditionals_do_not_assert_rest':True,'instantaneous_rest_does_not_require_interval_rest':True,
        'rational_affine_fields_and_explicit_relation_fixtures_only':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-3:];rows={}
    for wrong in ('none','author','premise','charge','old','new','scope','context'):
        model=guarded(doc)
        for name,value in {'zpg':'charge-node','zph':'old-node','zpi':'new-node','rd':'author','zno':'scope','ri':'text'}.items():model[name]=lambda value=value:value
        symbol=lambda d:json.loads(d.syntax)['symbol']
        def inference(node,author,premise,conclusion,scope,ctx):
            return [node,author,symbol(premise),symbol(conclusion),scope,ctx]==['charge-node','other' if wrong=='author' else 'author','other' if wrong=='premise' else 'scd2','other' if wrong=='charge' else 'scc2','other' if wrong=='scope' else 'scope','other' if wrong=='context' else 'text']
        def claim(node,author,content,scope,ctx):
            expected={'old-node':'sce2','new-node':'scf2'}
            return node in expected and [author,symbol(content),scope,ctx]==['other' if wrong=='author' else 'author','other' if node==wrong+'-node' else expected[node],'other' if wrong=='scope' else 'scope','other' if wrong=='context' else 'text']
        model.update(zc=inference,uh=claim);actual=values(doc,model,('charge-node','old-node','new-node','author','scope','other'))
        expected=[wrong not in ('author','premise','charge','scope','context'),wrong not in ('author','old','scope','context'),wrong not in ('author','new','scope','context')]
        if actual!=expected:raise ValueError('Force attribution differs')
        rows[wrong]=actual
    return {'cases':rows,'quoted_contents_not_executed':True,'inference_attribution_is_not_a_proof':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Source inventory changed')
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0173')
    if hashlib.sha256(unit['text'].encode()).hexdigest()!=unit['text_sha256']:raise ValueError('Source text changed')
    start=unit['text'].index('Nach dem Relativitätsprinzip');end=unit['text'].index(' Die ersten drei')
    base=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=['scc2','scd2','sce2','scf2'],status='partial_explicit_reading',full_semantic_equivalence=False)
    previous_start=unit['text'].index('welche im ruhenden System')
    previous_end=unit['text'].index(' Nach dem Relativitätsprinzip')
    rows=[dict(base,start=previous_start,end=previous_end,source=unit['text'][previous_start:previous_end],definitions=['sby2','sbz2','sca2'],correction='xm motion replaced by x4 rest'),
        dict(base,start=start,end=end,source=unit['text'][start:end])]
    for mid in ('M0315','M0316','M0317'):
        m=next(m for m in source['math'] if m['id']==mid)
        if hashlib.sha256(m['mathml'].encode()).hexdigest()!=m['sha256']:raise ValueError('Vector source changed')
        rows.append(dict(base,math_id=mid,math_sha256=m['sha256']))
    return {'segments':rows,'definition_based_reason_and_two_wordings_unfinished':True,'verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'rest-force'),(composed,'einstein-rest-force')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored force document differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Force roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    revised=[replace_symbol(d,'xm','x4') if d['name']=='sby2' else d for d in parent['declarations']]
    if doc['statements'][:-3]!=parent['statements'] or doc['declarations'][:len(revised)]!=revised:raise ValueError('Unexpected parent revision')
    paths=list(documents)+['data/rest-force-basis-v1.json','data/einstein-rest-force-basis-v1.json',PARENT,
        'data/einstein-rod-setup-basis-v1.json','scripts/compose_rest_force.py','scripts/check_rest_force.py',
        'scripts/check_field_transform.py','scripts/check_charge_calibration.py','noema/discourse.py','noema/finite_semantics.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'partial_frame_local_force_with_corrected_rest_binding','documents':documents,
        'rest_regression':rest_regression(),'generic':generic_checks(),'charge':charge_checks(),'premise':premise_checks(),'force':force_checks(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'parent_revision':{'definition':'sby2','old_reference':'xm','new_reference':'x4','other_parent_declarations_and_all_statements_preserved':True},
        'supersedes_historical_interpretation':'reports/charge-calibration-v1.json: source rest predicate was wrongly interpreted as motion',
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Rest-force report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Rest/motion correction, charge frame and conditional force vectors checked')


if __name__=='__main__':main()
