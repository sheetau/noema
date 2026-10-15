"""Test orientation, record completeness, source binding and quotation boundaries."""
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
from scripts.compose_axis_orientation import ROOT,PARENT,FULL,CORE,LIBRARY,REVIEW,INDEX,FIELDS,BINDINGS,PREVIOUS_BINDINGS,MEANINGS,build,CUT
from scripts.compose_limits import call as k,app,op,both,v
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded,callbacks
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_real_products import MEANINGS as RATIONAL,assertion
from scripts.check_moving_light_trip import literal
from scripts.check_rod_measurements import ARITHMETIC

REPORT=ROOT/'reports/axis-orientation-v1.json'
ROLES=('x','y','z')
AXES=tuple(a+f for f in ('1','2') for a in ROLES)
RECORDS=tuple('r'+a for a in AXES)+('alias','conflict')
DOMAIN=('old','new','third','unit','other',*ROLES,*AXES,*RECORDS,'author','earlier','node','scope')
SCENES=('text','other')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives={n:model[n] for n in names},max_steps=20_000_000,memoize_definitions=True,memoize_expressions=True)]


@lru_cache(None)
def numeric_checks():
    cases={'same':((1,0,0,1,0,0),True),'positive_scale':((1,2,3,2,4,6),True),
        'fractional_scale':((2,4,6,F(1,2),1,F(3,2)),True),'both_negative':((-1,-2,-3,-2,-4,-6),True),
        'antiparallel':((1,2,3,-2,-4,-6),False),'acute_nonparallel':((1,0,0,1,1,0),False),
        'orthogonal':((1,0,0,0,1,0),False),'zero_first':((0,0,0,1,0,0),False),
        'zero_second':((1,0,0,0,0,0),False),'both_zero':((0,0,0,0,0,0),False)}
    rat=extract_document(parse(text(LIBRARY)),roots=['sexa'],statement_indices=[]).document
    base=format_graph(rat,'compact');rows={}
    real=abstract(candidate(text(LIBRARY),''.join('r j'+n+'[] '+CUT+'.' for n in 'abcdef')+
        'q['+k('sexd',*[k('j'+n) for n in 'abcdef'])+'].'),OPS)
    for name,(args,wanted) in cases.items():
        doc=parse(base+'q['+k('sexa',*map(literal,args))+'].');r=evaluate(doc,ARITHMETIC)
        cuts,model=setup(real)
        for n,value in zip('abcdef',args):model['j'+n]=lambda value=value:cuts.make(value)
        s=evaluate(real,model);assert r==s==[wanted],(name,r,s)
        rows[name]=wanted
    cuts,model=setup(real)
    for n,value in zip('abcdef',(1,0,0,2,0,0)):model['j'+n]=lambda value=value:cuts.make(value)
    model['ba']=lambda cut:cuts.read(cut)!=2
    assert evaluate(real,model)==[False]
    return dict(cases=rows,invalid_component_rejected=True,real_cut_test_domain='constructed rational embeddings only')


@lru_cache(None)
def polynomial_checks():
    doc=extract_document(parse(text(LIBRARY)),roots=['sexa'],statement_indices=[]).document;base=format_graph(doc,'compact')
    a=[v(n) for n in ('x','y','z')];b=[v(n) for n in ('u','v','w')];scale=v('scale');zero=literal(0)
    orient=lambda x,y:k('sexa',*x,*y)
    scaled=lambda x:[k('ad',scale,c) for c in x]
    neg=lambda x:[k('ad',literal(-1),c) for c in x]
    claims={
        'symmetric':assertion('x y z u v w',op('z',orient(a,b),orient(b,a))),
        'positive_scale_preserves_orientation':assertion('x y z u v w scale',op('y',k('aa',zero,scale),op('z',orient(a,b),orient(a,scaled(b))))),
        'reverse_both_preserves_orientation':assertion('x y z u v w',op('z',orient(a,b),orient(neg(a),neg(b)))),
        'reverse_one_breaks_orientation':assertion('x y z u v w',op('y',orient(a,b),op('u',orient(a,neg(b))))),
        'orientation_implies_equal_length':assertion('',op('y',orient([literal(1),zero,zero],[literal(2),zero,zero]),op('e',literal(1),literal(4)))),
    }
    rows={}
    for name,claim in claims.items():
        model={d['name']:RATIONAL[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
        result=verify_universal(parse(base+claim),model,timeout_ms=20000)[0]
        assert result['status']==('invalid' if name=='orientation_implies_equal_length' else 'valid'),(name,result['status'])
        rows[name]=result
    return dict(claims=rows,real_cut_field_laws_proved=False)


@lru_cache(None)
def source_fixture(path=CORE):
    extra='r jafirst[] a.r jasecond[] a.r javalue[] '+CUT+'.r jacontext[] d.'
    values=[k('ja'+n) for n in ('first','second','value','context')]
    return abstract(candidate(text(path),extra+''.join('q['+app(k(n),*values)+'].' for n in ('sewz','sexh'))),OPS)


def source_model(doc,variant):
    cuts,model=setup(doc);calls=[]
    constants={'ra':'old','zbm':'new','ta':'unit','yn':'x','yo':'y','yp':'z',
        'jafirst':'old','jasecond':'new','jacontext':'text'}
    if variant=='wrong_frame':constants['jasecond']='third'
    if variant=='wrong_context':constants['jacontext']='other'
    if variant=='duplicate_role':constants['yp']='y'
    for n,val in constants.items():model[n]=lambda val=val:val
    model['zb7']=lambda:cuts.make(3);model['javalue']=lambda:cuts.make(4 if variant=='wrong_speed' else 3)
    axis=lambda frame,role,scene:role+('1' if frame=='old' else '2')
    vectors={a:tuple(F(1 if a[0]==r else 0) for r in ROLES) for a in AXES}
    if variant=='positive_rescale':vectors.update({a:tuple(x*F(3,2) for x in vec) for a,vec in vectors.items() if a.endswith('2')})
    if variant in ('antiparallel_x','antiparallel_y','antiparallel_z'):
        name=variant[-1]+'2';vectors[name]=tuple(-x for x in vectors[name])
    if variant=='acute_nonparallel':vectors['y2']=(F(1),F(1),F(0))
    if variant=='zero_direction':vectors['z2']=(F(0),)*3
    record_vectors={'r'+a:vec for a,vec in vectors.items()}
    record_vectors['alias']=tuple(2*x for x in vectors['y2']);record_vectors['conflict']=(F(0),F(-1),F(0))
    assigned={(record,a,'old','unit','text') for a in AXES for record in ('r'+a,)}
    if variant=='missing_record':assigned={row for row in assigned if row[1]!='z2'}
    if variant=='alias_record':assigned.add(('alias','y2','old','unit','text'))
    if variant=='conflicting_record':assigned.add(('conflict','y2','old','unit','text'))
    if variant in ('wrong_record_chart','wrong_record_unit','wrong_record_context'):
        i={'wrong_record_chart':2,'wrong_record_unit':3,'wrong_record_context':4}[variant]
        assigned={tuple('other' if j==i and row[1]=='y2' else value for j,value in enumerate(row)) for row in assigned}
    if variant=='outside_bad_record':assigned.add(('conflict','y2','other','unit','text'))
    def selected(record,ax,chart,unit,scene):
        if variant=='unknown_assignment':raise ValueError('missing direction assignment')
        calls.append((chart,unit,scene));return (record,ax,chart,unit,scene) in assigned
    def component(record,role):
        if variant=='unknown_component' and record=='ry2':raise ValueError('missing direction component')
        return cuts.make(record_vectors.get(record,(F(0),)*3)[ROLES.index(role)] if role in ROLES else 0)
    model.update(va=lambda f:f=='old',ti=lambda u:u=='unit',zbo=axis,
        zbw=lambda frame,ax,role,scene:frame in ('old','new') and scene=='text' and ax==axis(frame,role,scene)
            and not(variant=='missing_axis_assignment' and (frame,role)==('new','y')),
        zsa=selected,zsb=component)
    callbacks(doc,model,{'zqf':lambda *args:variant!='missing_configuration'})
    return model,calls


@lru_cache(None)
def source_checks():
    success=('baseline','positive_rescale','alias_record','outside_bad_record')
    orientation_failures=('antiparallel_x','antiparallel_y','antiparallel_z','acute_nonparallel','zero_direction',
        'missing_record','conflicting_record','wrong_record_chart','wrong_record_unit','wrong_record_context',
        'missing_axis_assignment','duplicate_role','wrong_context')
    cases={n:[True,True] for n in success};cases.update({n:[True,False] for n in orientation_failures})
    cases.update({n:[False,False] for n in ('missing_configuration','wrong_frame','wrong_speed')})
    rows={}
    for path in (CORE,FULL):
        doc=source_fixture(path);rows[path]={}
        for name,wanted in cases.items():
            model,calls=source_model(doc,name);actual=evaluate(doc,model)
            assert actual==wanted,(path,name,actual)
            assert calls and all(c==('old','unit','other' if name=='wrong_context' else 'text') for c in calls)
            rows[path][name]=actual
    refused=[];doc=source_fixture()
    for name in ('unknown_assignment','unknown_component'):
        model,_=source_model(doc,name)
        try:evaluate(doc,model)
        except ValueError as exc:assert 'missing' in str(exc);refused.append(name)
        else:raise AssertionError(name)
    return dict(cases=rows,unknown_inputs_refused=refused,common_chart_unit_context=True,
        complete_physical_configuration_derived=False,density_law_evaluated=False)


def structure_and_attribution():
    old=parse(text(PARENT));doc=parse(text(FULL));assert len(doc['statements'])==len(old['statements'])==206
    assert doc['declarations'][:len(old['declarations'])]==old['declarations']
    added=doc['declarations'][len(old['declarations']):]
    assert {d['name'] for d in added if d['kind']=='definition'}==set(MEANINGS)
    assert {d['name'] for d in added if d['kind']=='primitive'}=={'zsa','zsb'}
    original=old['statements'][INDEX]['body']['arguments'][-1]['body'];revised=doc['statements'][INDEX]['body']['arguments'][-1]['body']
    assert original['symbol']==revised['symbol']=='seoz'
    assert [n for (n,_),a,b in zip(FIELDS,original['arguments'],revised['arguments'],strict=True) if a!=b]==['frames']
    restored=deepcopy(doc['statements']);restored[INDEX]=old['statements'][INDEX];assert restored==old['statements']
    paths={n:dependency_path(doc,INDEX,n) for n in ('sexh','sexg','sexf','sexe','sexd','sexc','sexb','sewz','zqf','ra','zbm','zb7','ta','rb')};assert all(paths.values())
    quoted=extract_document(doc,statement_indices=[INDEX]).document;rows=[]
    for present,explain,order in product((False,True),repeat=3):
        model=guarded(quoted)
        for name,value in dict(rd='author',zqa='earlier',zqb='node',zqc='scope',ri='text').items():model[name]=lambda value=value:value
        model.update(uh=lambda node,author,content,scope,context:present and json.loads(content.syntax)==revised,
            uf=lambda *args:explain,ue=lambda *args:order)
        actual=evaluate(quoted,model);assert actual==[present and explain and order];rows.append(actual[0])
    prior=extract_document(old,statement_indices=[INDEX]).document;previous=guarded(prior);previous.update(model);assert evaluate(prior,previous)==[False]
    return dict(changed_arguments=['frames'],new_definitions=8,new_primitives=2,other_205_statements_unchanged=True,
        dependency_paths=paths,attribution_cases=rows,quoted_orientation_not_executed=True,old_quote_not_substituted=True)


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
    paths=set(files)|{PARENT,'data/einstein-density-frame-binding-basis-v1.json','data/density-formula-review-v7.json',
        'artifacts/written-units-v1/einstein-1905.json','tests/test_axis_orientation.py','docs/axis-orientation-v1.md'}
    paths.update('scripts/'+n+'.py' for n in ('compose_axis_orientation','check_axis_orientation','compose_density_frame_binding',
        'compose_density_units','compose_density_boost','compose_origin_clock','compose_limits','compose_situated_criticism',
        'check_coordinate_correspondence','check_described_appraisals','check_rod_setup','check_plane_waveforms','check_field_equations',
        'check_tau_differential','check_angle_composition','check_real_products','check_moving_light_trip','check_rod_measurements'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','integration_audit','polynomial_proofs'))
    source=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));unit=next(x for x in source['units'] if x['id']=='einstein-1905:u0236');math=next(x for x in source['math'] if x['id']=='M0390')
    return dict(status='partial_density_formula_with_positive_axis_orientation',document=FULL,basis_audits=audits,
        numeric=numeric_checks(),polynomial=polynomial_checks(),source=source_checks(),structure=structure_and_attribution(),
        roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id='M0390',math_sha256=math['sha256'],
            status='partial_density_formula_with_positive_axis_orientation',definitions=['sexh','sexg','sexd','seoz'])]),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Positive axis orientation, record coverage and source quotation checked',flush=True)


if __name__=='__main__':main()
