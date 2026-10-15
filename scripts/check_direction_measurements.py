"""Verify that all selected direction records agree with their observed endpoints."""
import argparse,hashlib,json,subprocess,sys
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as F
from itertools import product
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.meaning_basis import audit_basis
from noema.finite_semantics import evaluate_document
from noema.polynomial_proofs import verify_universal
from noema.integration_audit import dependency_path
from noema.script import transcribe
from scripts.compose_direction_measurements import ROOT,PARENT,FULL,CORE,LIBRARY,REVIEW,INDEX,FIELDS,MEANINGS,build,CUT
from scripts.compose_limits import call as k,app,op,v
from scripts.check_axis_orientation import source_model as orientation_model,DOMAIN as PRIOR_DOMAIN,ROLES,AXES
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_real_products import MEANINGS as RATIONAL,assertion
from scripts.check_moving_light_trip import literal

REPORT=ROOT/'reports/direction-measurements-v1.json'
POINTS=('tail1','tail2',*('head'+a for a in AXES),'aliashead')
DOMAIN=PRIOR_DOMAIN+POINTS+('moment','later')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=('text','other'),
        primitives={n:model[n] for n in names},max_steps=30_000_000,memoize_definitions=True,memoize_expressions=True)]


@lru_cache(None)
def polynomial_checks():
    doc=extract_document(parse(text(LIBRARY)),roots=['sexi'],statement_indices=[]).document;base=format_graph(doc,'compact')
    a,b,d,t=map(v,('tail','head','delta','offset'));add=lambda x,y:k('ab',x,y);neg=lambda x:k('ac',x)
    claims={
        'common_origin_change_preserves_displacement':assertion('tail head delta offset',op('z',k('sexi',a,b,d),k('sexi',add(a,t),add(b,t),d))),
        'swapping_endpoints_reverses_displacement':assertion('tail head delta',op('z',k('sexi',a,b,d),k('sexi',b,a,neg(d)))),
        'change_only_head_preserves_displacement':assertion('',op('y',k('sexi',literal(1),literal(3),literal(2)),k('sexi',literal(1),literal(4),literal(2)))),
        'unsigned_difference_is_sufficient':assertion('',k('sexi',literal(3),literal(1),literal(2))),
    };rows={}
    model={d['name']:RATIONAL[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),model,timeout_ms=20000)[0]
        assert result['status']==('valid' if name.startswith(('common','swapping')) else 'invalid'),(name,result)
        rows[name]=result
    return dict(claims=rows,real_cut_field_laws_proved=False)


@lru_cache(None)
def numeric_checks():
    doc=abstract(candidate(text(LIBRARY),'r ja[] '+CUT+'.r jb[] '+CUT+'.r jc[] '+CUT+'.q[k sexj[k ja[] k jb[] k jc[]]].'),OPS)
    cases={'positive':(1,3,2,True),'negative':(3,1,-2,True),'zero':(3,3,0,True),
        'fractional':(F(1,2),F(5,6),F(1,3),True),'wrong_sign':(3,1,2,False),'wrong_magnitude':(1,3,3,False)};rows={}
    for name,(a,b,c,wanted) in cases.items():
        cuts,model=setup(doc)
        for key,value in zip(('ja','jb','jc'),(a,b,c)):model[key]=lambda value=value:cuts.make(value)
        actual=evaluate(doc,model);assert actual==[wanted];rows[name]=actual[0]
    cuts,model=setup(doc)
    for key,value in zip(('ja','jb','jc'),(1,3,2)):model[key]=lambda value=value:cuts.make(value)
    model['ba']=lambda value:cuts.read(value)!=3;assert evaluate(doc,model)==[False]
    return dict(cases=rows,invalid_position_rejected=True,domain='constructed rational cuts only')


@lru_cache(None)
def source_fixture(path=CORE):
    extra='r jafirst[] a.r jasecond[] a.r javalue[] '+CUT+'.r jacontext[] d.'
    values=[k('ja'+n) for n in ('first','second','value','context')]
    return abstract(candidate(text(path),extra+''.join('q['+app(k(n),*values)+'].' for n in ('sexh','sexn'))),OPS)


def source_model(doc,variant):
    parent={'consistent_scale':'positive_rescale','forged_scale':'positive_rescale',
        'extra_consistent_record':'alias_record','extra_inconsistent_record':'alias_record',
        'empty_axis_records':'missing_record'}.get(variant,variant if variant in ('missing_configuration','wrong_frame','wrong_speed') else 'baseline')
    model,_=orientation_model(doc,parent);calls=[]
    axes={**{'r'+a:a for a in AXES},'alias':'y2'}
    moment='later' if variant=='later_observation' else 'moment'
    def fields(record):
        ax=axes.get(record,'x1');tail='tail'+ax[-1];head='head'+ax
        if record=='alias' and variant=='extra_consistent_record':head='aliashead'
        if record=='ry2' and variant=='same_endpoints':head=tail
        if record=='ry2' and variant=='swapped_endpoints':tail,head=head,tail
        return tail,head,moment
    def field(record,index):
        if record=='ry2' and variant=='unknown_field':raise ValueError('missing endpoint field')
        return fields(record)[int(index)] if index in (0,1,2) else 'other'
    def linked(record,tail,head,t,scene):
        expected=fields(record)
        if record=='ry2' and variant=='wrong_linked_order':expected=(expected[1],expected[0],expected[2])
        return record in axes and (tail,head,t)==expected and scene=='text' and not(record=='ry2' and variant=='missing_link')
    def placed(point,axis,scene):
        return scene=='text' and axis in AXES and (point in ('tail'+axis[-1],'head'+axis) or (point=='aliashead' and axis=='y2')) and not(point=='heady2' and variant=='point_outside_axis')
    def available(point,t,chart,unit,scene):
        calls.append((t,chart,unit,scene))
        valid=point in POINTS and t in ('moment','later') and chart=='old' and unit=='unit' and scene=='text'
        if point=='heady2' and variant in ('missing_coordinates','wrong_position_chart','wrong_position_unit','wrong_position_context','head_at_other_time'):
            wanted={'wrong_position_chart':(t,'third',unit,scene),'wrong_position_unit':(t,chart,'other',scene),
                'wrong_position_context':(t,chart,unit,'other'),'head_at_other_time':('later',chart,unit,scene)}.get(variant)
            return wanted is not None and (t,chart,unit,scene)==wanted
        return valid
    def coordinate(point,t,chart,unit,role,scene):
        if variant=='unknown_position' and point=='heady2':raise ValueError('missing position coordinate')
        idx=ROLES.index(role) if role in ROLES else 0
        frame='2' if point in ('tail2','headx2','heady2','headz2','aliashead') else '1'
        base=(10,-4,2) if variant=='different_origins' and frame=='2' else (0,0,0)
        result=F(base[idx])
        if variant=='common_origin_shift':result+=(7,-5,3)[idx]
        if t=='later':result+=(9,2,-3)[idx]
        if point.startswith('head'):
            ax=point[4:];scale=F(3,2) if variant=='consistent_scale' and ax.endswith('2') else F(1)
            if ax[0]==role:result+=scale
        if point=='aliashead' and role=='y':result+=2
        if point=='heady2' and role=='y' and variant=='head_mismatch':result+=1
        if point=='tail1' and role=='x' and variant=='tail_mismatch':result+=1
        return model['bb'](result)
    model.update(zsc=field,zsd=linked,zcc=placed,zce=available,ym=coordinate)
    return model,calls


@lru_cache(None)
def source_checks():
    good=('baseline','consistent_scale','common_origin_shift','different_origins','later_observation','extra_consistent_record')
    bad=('forged_scale','extra_inconsistent_record','head_mismatch','tail_mismatch','missing_link','wrong_linked_order',
        'point_outside_axis','missing_coordinates','wrong_position_chart','wrong_position_unit','wrong_position_context',
        'head_at_other_time','same_endpoints','swapped_endpoints')
    cases={n:[True,True] for n in good};cases.update({n:[True,False] for n in bad})
    cases.update({n:[False,False] for n in ('empty_axis_records','missing_configuration','wrong_frame','wrong_speed')})
    rows={}
    for path in (CORE,FULL):
        doc=source_fixture(path);rows[path]={}
        for name,wanted in cases.items():
            model,calls=source_model(doc,name);actual=evaluate(doc,model)
            assert actual==wanted,(path,name,actual)
            assert calls and all(c==('later' if name=='later_observation' else 'moment','old','unit','text') for c in calls)
            rows[path][name]=actual
    refused=[];doc=source_fixture()
    for name in ('unknown_field','unknown_position'):
        model,_=source_model(doc,name)
        try:evaluate(doc,model)
        except ValueError as exc:assert 'missing' in str(exc);refused.append(name)
        else:raise AssertionError(name)
    return dict(cases=rows,unknown_inputs_refused=refused,same_moment_chart_unit_context=True,
        original_record_set_preserved=True,physical_measurement_derived=False,density_law_evaluated=False)


def structure_and_attribution():
    old=parse(text(PARENT));doc=parse(text(FULL));assert len(doc['statements'])==len(old['statements'])==206
    assert doc['declarations'][:len(old['declarations'])]==old['declarations']
    added=doc['declarations'][len(old['declarations']):]
    assert {d['name'] for d in added if d['kind']=='definition'}==set(MEANINGS)
    assert {d['name'] for d in added if d['kind']=='primitive'}=={'zsc','zsd'}
    original=old['statements'][INDEX]['body']['arguments'][-1]['body'];revised=doc['statements'][INDEX]['body']['arguments'][-1]['body']
    assert original['symbol']==revised['symbol']=='seoz'
    assert [n for (n,_),a,b in zip(FIELDS,original['arguments'],revised['arguments'],strict=True) if a!=b]==['frames']
    restored=deepcopy(doc['statements']);restored[INDEX]=old['statements'][INDEX];assert restored==old['statements']
    paths={n:dependency_path(doc,INDEX,n) for n in ('sexn','sexm','sexl','sexk','sexj','sexh','zsa','zsb','zsc','zsd','zce','ym','zcc','zqf','ra','zbm','zb7','ta','rb')};assert all(paths.values())
    quoted=extract_document(doc,statement_indices=[INDEX]).document;rows=[]
    for present,explain,order in product((False,True),repeat=3):
        model=guarded(quoted)
        for name,value in dict(rd='author',zqa='earlier',zqb='node',zqc='scope',ri='text').items():model[name]=lambda value=value:value
        model.update(uh=lambda node,author,content,scope,context:present and json.loads(content.syntax)==revised,
            uf=lambda *args:explain,ue=lambda *args:order)
        actual=evaluate(quoted,model);assert actual==[present and explain and order];rows.append(actual[0])
    prior=extract_document(old,statement_indices=[INDEX]).document;previous=guarded(prior);previous.update(model);assert evaluate(prior,previous)==[False]
    return dict(changed_arguments=['frames'],new_definitions=6,new_primitives=2,other_205_statements_unchanged=True,
        dependency_paths=paths,attribution_cases=rows,quoted_measurements_not_executed=True,old_quote_not_substituted=True)


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
    paths=set(files)|{PARENT,'data/einstein-axis-orientation-basis-v1.json','data/density-formula-review-v8.json',
        'artifacts/written-units-v1/einstein-1905.json','tests/test_direction_measurements.py','docs/direction-measurements-v1.md'}
    paths.update('scripts/'+n+'.py' for n in ('compose_direction_measurements','check_direction_measurements','compose_axis_orientation',
        'compose_density_frame_binding','compose_density_units','compose_density_boost','compose_origin_clock','compose_limits','compose_situated_criticism',
        'check_axis_orientation','check_coordinate_correspondence','check_described_appraisals','check_rod_setup','check_plane_waveforms','check_field_equations',
        'check_tau_differential','check_angle_composition','check_real_products','check_moving_light_trip','check_rod_measurements'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','integration_audit','polynomial_proofs'))
    source=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));unit=next(x for x in source['units'] if x['id']=='einstein-1905:u0236');math=next(x for x in source['math'] if x['id']=='M0390')
    return dict(status='partial_density_formula_with_recorded_endpoint_displacements',document=FULL,basis_audits=audits,
        numeric=numeric_checks(),polynomial=polynomial_checks(),source=source_checks(),structure=structure_and_attribution(),
        roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id='M0390',math_sha256=math['sha256'],
            status='partial_density_formula_with_recorded_endpoint_displacements',definitions=['sexn','sexm','sexk','seoz'])]),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Endpoint provenance, shared coordinates and all selected direction records checked',flush=True)


if __name__=='__main__':main()
