"""Check owning-axis positive order without guessing it from shared directions."""
import argparse,hashlib,json,subprocess,sys
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as F
from itertools import product
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.integration_audit import dependency_path
from noema.script import transcribe
from scripts.compose_positive_axis_calibration import ROOT,PARENT,FULL,CORE,LIBRARY,REVIEW,INDEX,FIELDS,MEANINGS,build,CUT,COORDS
from scripts.compose_limits import call as k,app,op,v
from scripts.check_direction_measurements import evaluate,source_model as displacement_model,POINTS
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_real_products import MEANINGS as RATIONAL,assertion
from scripts.check_moving_light_trip import literal

REPORT=ROOT/'reports/positive-axis-calibration-v1.json'


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


@lru_cache(None)
def numeric_checks():
    extra=''.join('r j'+n+'[] '+CUT+'.' for n in COORDS)+'r jrole[] a.r jx[] a.r jy[] a.r jz[] a.'
    doc=abstract(candidate(text(LIBRARY),extra+'q['+k('sexq',k('jrole'),k('jx'),k('jy'),k('jz'),*[k('j'+n) for n in COORDS])+'].'),OPS)
    cases={
        'x_increasing':('x',(0,0,0,1,0,0),True),
        'y_increasing':('y',(0,0,0,0,2,0),True),
        'z_increasing':('z',(0,0,0,0,0,F(1,2)),True),
        'negative_coordinate_values_increase':('x',(-3,0,0,-1,0,0),True),
        'positive_coordinate_values_decrease':('x',(3,0,0,1,0,0),False),
        'equal_coordinates':('y',(0,1,0,0,1,0),False),
        'wrong_role':('x',(0,0,0,0,1,0),False),
        'unknown_role':('other',(0,0,0,1,0,0),False),
        'parallel_offset_line':('x',(0,2,0,1,2,0),False),
        'head_off_axis':('x',(0,0,0,1,1,0),False),
        'tail_off_axis':('z',(1,0,0,0,0,1),False),
        'both_endpoints_on_negative_half':('y',(0,-4,0,0,-2,0),True),
    };rows={}
    for name,(role,coords,wanted) in cases.items():
        cuts,model=setup(doc)
        for n,value in zip(COORDS,coords):model['j'+n]=lambda value=value:cuts.make(value)
        for n,value in dict(jrole=role,jx='x',jy='y',jz='z').items():model[n]=lambda value=value:value
        actual=evaluate(doc,model);assert actual==[wanted],(name,actual);rows[name]=actual[0]
    model['jz']=lambda:'y';assert evaluate(doc,model)==[False]
    model['jz']=lambda:'z';model['ba']=lambda value:cuts.read(value)!=-4;assert evaluate(doc,model)==[False]
    return dict(cases=rows,duplicate_roles_rejected=True,invalid_component_rejected=True,domain='constructed rational cuts only')


@lru_cache(None)
def polynomial_checks():
    doc=extract_document(parse(text(LIBRARY)),roots=['sexo'],statement_indices=[]).document
    source=parse(text(FULL));names={d['name'] for d in doc['declarations']}
    doc['declarations']=[d for d in source['declarations'] if d['name'] in ('ab','ad') and d['name'] not in names]+doc['declarations']
    base=format_graph(doc,'compact');a,b,s,t=map(v,('tail','head','scale','offset'))
    affine=lambda x:k('ab',k('ad',s,x),t)
    claims={
        'positive_affine_coordinate_change_preserves_order':assertion('tail head scale offset',op('y',k('aa',literal(0),s),op('z',k('sexo',a,b),k('sexo',affine(a),affine(b))))),
        'reverse_order_cannot_also_increase':assertion('tail head',op('y',k('sexo',a,b),op('u',k('sexo',b,a)))),
        'negative_coordinate_values_can_increase':assertion('',k('sexo',literal(-3),literal(-1))),
        'positive_values_imply_positive_order':assertion('',k('sexo',literal(3),literal(1))),
    };rows={};model={d['name']:RATIONAL[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),model,timeout_ms=20000)[0]
        assert result['status']==('invalid' if name=='positive_values_imply_positive_order' else 'valid'),(name,result)
        rows[name]=result
    return dict(claims=rows,real_cut_field_laws_proved=False)


@lru_cache(None)
def source_fixture(path=CORE):
    extra='r jafirst[] a.r jasecond[] a.r javalue[] '+CUT+'.r jacontext[] d.'
    values=[k('ja'+n) for n in ('first','second','value','context')]
    return abstract(candidate(text(path),extra+''.join('q['+app(k(n),*values)+'].' for n in ('sexn','sext'))),OPS)


def source_model(doc,variant):
    parent=variant if variant in ('different_origins','extra_consistent_record','missing_configuration','wrong_frame','wrong_speed','head_mismatch','empty_axis_records') else 'baseline'
    model,_=displacement_model(doc,parent);common_coordinate=model['ym'];common_available=model['zce'];component=model['zsb'];calls=[]
    model['va']=lambda frame:frame=='old' or (frame=='new' and variant!='invalid_own_frame')
    if variant=='common_reversed_y':
        model['zsb']=lambda record,role:model['bb'](-1) if record in ('ry1','ry2') and role=='y' else component(record,role)
    def coordinate(point,moment,frame,unit,role,scene):
        if frame!='new':
            if variant=='common_reversed_y' and point in ('heady1','heady2') and role=='y':return model['bb'](-1)
            return common_coordinate(point,moment,frame,unit,role,scene)
        if variant=='unknown_own_coordinate' and point=='heady2':raise ValueError('missing own-frame coordinate')
        value=F(0)
        if point.startswith('head') and point[4:5]==role:value=F(1)
        if point=='aliashead' and role=='y':value=F(2)
        if variant=='own_positive_scale':value*=2
        if variant in ('own_reversed_x','own_reversed_y','own_reversed_z') and role==variant[-1]:value=-value
        if variant=='own_zero_y' and point=='heady2' and role=='y':value=F(0)
        if variant=='own_head_off_axis' and point=='heady2' and role=='x':value=F(1)
        if variant=='own_offset_axes' and role=='x':value+=5
        if variant=='own_swapped_roles' and point in ('headx2','heady2'):
            value=F(1 if role==('y' if point=='headx2' else 'x') else 0)
        return model['bb'](value)
    def available(point,moment,frame,unit,scene):
        calls.append((point,moment,frame,unit,scene))
        if frame!='new':return common_available(point,moment,frame,unit,scene)
        if variant=='unknown_own_availability':raise ValueError('missing own-frame availability')
        if variant in ('missing_own_coordinates','own_wrong_unit','own_wrong_context','own_wrong_time') and point=='heady2':
            expected={'own_wrong_unit':('moment','other','text'),'own_wrong_context':('moment','unit','other'),
                'own_wrong_time':('later','unit','text')}.get(variant)
            return expected is not None and (moment,unit,scene)==expected
        return point in POINTS and moment=='moment' and unit=='unit' and scene=='text'
    model.update(ym=coordinate,zce=available)
    return model,calls


@lru_cache(None)
def source_checks():
    good=('baseline','different_origins','extra_consistent_record','own_positive_scale')
    bad=('own_reversed_x','own_reversed_y','own_reversed_z','own_zero_y','own_head_off_axis','own_offset_axes',
        'own_swapped_roles','common_reversed_y','missing_own_coordinates','own_wrong_unit','own_wrong_context',
        'own_wrong_time','invalid_own_frame')
    cases={n:[True,True] for n in good};cases.update({n:[True,False] for n in bad})
    cases.update({n:[False,False] for n in ('missing_configuration','wrong_frame','wrong_speed','head_mismatch','empty_axis_records')})
    full_cases=('baseline','own_reversed_y','common_reversed_y','missing_own_coordinates','invalid_own_frame','missing_configuration')
    rows={}
    for path in (CORE,FULL):
        doc=source_fixture(path);rows[path]={}
        selected=cases if path==CORE else {n:cases[n] for n in full_cases}
        for name,wanted in selected.items():
            model,calls=source_model(doc,name);actual=evaluate(doc,model)
            assert actual==wanted,(path,name,actual)
            assert calls and all(c[1]=='moment' and c[2] in ('old','new','third') and c[3:] == ('unit','text') for c in calls)
            if name=='baseline':assert {'old','new'} <= {c[2] for c in calls}
            rows[path][name]=actual
    refused=[];doc=source_fixture()
    for name in ('unknown_own_coordinate','unknown_own_availability'):
        model,_=source_model(doc,name)
        try:evaluate(doc,model)
        except ValueError as exc:assert 'missing' in str(exc);refused.append(name)
        else:raise AssertionError(name)
    return dict(cases=rows,unknown_inputs_refused=refused,own_and_common_frames_distinguished=True,
        original_endpoints_and_record_scope_preserved=True,clock_reading_equality_required=False,physical_metrology_proved=False)


def structure_and_attribution():
    old=parse(text(PARENT));doc=parse(text(FULL));assert len(doc['statements'])==len(old['statements'])==206
    assert doc['declarations'][:len(old['declarations'])]==old['declarations']
    added=doc['declarations'][len(old['declarations']):]
    assert all(d['kind']=='definition' for d in added) and {d['name'] for d in added}==set(MEANINGS)
    original=old['statements'][INDEX]['body']['arguments'][-1]['body'];revised=doc['statements'][INDEX]['body']['arguments'][-1]['body']
    assert original['symbol']==revised['symbol']=='seoz'
    assert [n for (n,_),a,b in zip(FIELDS,original['arguments'],revised['arguments'],strict=True) if a!=b]==['frames']
    restored=deepcopy(doc['statements']);restored[INDEX]=old['statements'][INDEX];assert restored==old['statements']
    paths={n:dependency_path(doc,INDEX,n) for n in ('sext','sexs','sexr','sexq','sexp','sexn','zsa','zsc','zsd','zce','ym','zbw','zcc','zqf','ra','zbm','zb7','ta','rb')};assert all(paths.values())
    quoted=extract_document(doc,statement_indices=[INDEX]).document
    assert quoted==parse(text(CORE))
    rows=[]
    for present,explain,order in product((False,True),repeat=3):
        model=guarded(quoted)
        for name,value in dict(rd='author',zqa='earlier',zqb='node',zqc='scope',ri='text').items():model[name]=lambda value=value:value
        model.update(uh=lambda node,author,content,scope,context:present and json.loads(content.syntax)==revised,
            uf=lambda *args:explain,ue=lambda *args:order)
        actual=evaluate(quoted,model);assert actual==[present and explain and order];rows.append(actual[0])
    prior=extract_document(old,statement_indices=[INDEX]).document;previous=guarded(prior);previous.update(model);assert evaluate(prior,previous)==[False]
    return dict(changed_arguments=['frames'],new_definitions=6,new_primitives=0,other_205_statements_unchanged=True,
        extracted_core_equals_actual_full_statement_dependencies=True,dependency_paths=paths,attribution_cases=rows,
        quoted_calibration_not_executed=True,old_quote_not_substituted=True)


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    for p in (FULL,CORE,LIBRARY):
        doc=parse(text(p));basis=next(json.loads(x) for q,x in files.items() if q.endswith('-basis-v1.json') and json.loads(x)['document']==p)
        audits[p]={k:v for k,v in audit_basis(doc,basis).items() if k!='definition_dependencies'}
        for notation in ('full','compact'):
            formatted=format_graph(doc,notation);assert parse(formatted)==parse(transcribe(formatted,alphabet='v2'))==doc
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==doc
    paths=set(files)|{PARENT,'data/einstein-direction-measurements-basis-v1.json','data/density-formula-review-v9.json',
        'artifacts/written-units-v1/einstein-1905.json','tests/test_positive_axis_calibration.py','docs/positive-axis-calibration-v1.md'}
    paths.update('scripts/'+n+'.py' for n in ('compose_positive_axis_calibration','check_positive_axis_calibration',
        'compose_direction_measurements','check_direction_measurements','compose_axis_orientation',
        'compose_density_frame_binding','compose_density_units','compose_density_boost','compose_origin_clock','compose_limits','compose_situated_criticism',
        'check_axis_orientation','check_coordinate_correspondence','check_described_appraisals','check_rod_setup','check_plane_waveforms','check_field_equations',
        'check_tau_differential','check_angle_composition','check_real_products','check_moving_light_trip','check_rod_measurements'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','integration_audit','polynomial_proofs'))
    source=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));unit=next(x for x in source['units'] if x['id']=='einstein-1905:u0236');math=next(x for x in source['math'] if x['id']=='M0390')
    return dict(status='partial_density_formula_with_own_axis_positive_calibration',document=FULL,basis_audits=audits,
        numeric=numeric_checks(),polynomial=polynomial_checks(),source=source_checks(),structure=structure_and_attribution(),
        roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id='M0390',math_sha256=math['sha256'],
            status='partial_density_formula_with_own_axis_positive_calibration',definitions=['sext','sexs','sexq','seoz'])]),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Owning-frame positive order, preserved record scope and quotation checked',flush=True)


if __name__=='__main__':main()
