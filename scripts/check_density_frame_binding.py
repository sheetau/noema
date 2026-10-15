"""Verify ordered source references independently of physical configuration."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph
from noema.finite_semantics import evaluate_document
from noema.extraction import extract_document,_references
from noema.integration_audit import dependency_path
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_density_frame_binding import ROOT,PARENT,FULL,CORE,LIBRARY,REVIEW,INDEX,FIELDS,BOUND,BINDINGS,PREVIOUS_BINDINGS,build,CUT
from scripts.compose_limits import call as k,app
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded,callbacks
from scripts.check_plane_waveforms import setup,OPS

REPORT=ROOT/'reports/density-frame-binding-v1.json'
PEOPLE=('old','new','third','author','earlier','node','scope')
SCENES=('text','other')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=PEOPLE,situations=SCENES,
        primitives={n:model[n] for n in names},max_steps=2_000_000,memoize_definitions=True)]


@lru_cache(None)
def source_fixture(path=CORE):
    extra='r jbfirst[] a.r jbsecond[] a.r jbvalue[] '+CUT+'.r jbcontext[] d.'
    inputs=[k('jb'+n) for n in ('first','second','value','context')]
    return abstract(candidate(text(path),extra+''.join('q['+app(k(n),*inputs)+'].' for n in ('zqf','sewz'))),OPS)


def source_model(doc,variant='baseline'):
    cuts,model=setup(doc);calls=[]
    first,second,value,context='old','new',F(3),'text'
    if variant=='other_first':first='third'
    if variant=='other_second':second='third'
    if variant=='reversed':first,second='new','old'
    if variant=='reversed_and_negated':first,second,value='new','old',F(-3)
    if variant=='wrong_magnitude':value=F(4)
    if variant=='negated_speed':value=F(-3)
    if variant=='other_context':context='other'
    if variant=='same_frame_references':first,second='new','new'
    for n,x in dict(ra='new' if variant=='same_frame_references' else 'old',zbm='new',
        jbfirst=first,jbsecond=second,jbcontext=context).items():model[n]=lambda x=x:x
    expected=F(0) if variant=='zero_velocity' else F(3)
    if variant=='zero_velocity':value=F(0)
    def known_value():
        if variant=='unknown_velocity':raise ValueError('Source velocity missing')
        return cuts.make(expected)
    model['zb7']=known_value;model['jbvalue']=lambda:cuts.make(value)
    def relation(left,right,speed,scene):
        calls.append((left,right,str(cuts.read(speed)),scene))
        if variant=='unknown_configuration':raise ValueError('Configuration missing')
        # Deliberately permits other pairs and speeds, exposing what the new
        # reference guard adds without deriving physical truth from equality.
        return variant!='missing_configuration' and scene=='text'
    callbacks(doc,model,{'zqf':relation})
    return model,calls


@lru_cache(None)
def source_checks():
    cases={'baseline':[True,True],'zero_velocity':[True,True],
        'missing_configuration':[False,False],'other_context':[False,False]}
    for name in ('other_first','other_second','reversed','reversed_and_negated','wrong_magnitude','negated_speed','same_frame_references'):
        cases[name]=[True,False]
    rows={}
    for path in (CORE,FULL):
        doc=source_fixture(path);outputs={}
        for name,expected in cases.items():
            model,calls=source_model(doc,name);actual=evaluate(doc,model)
            assert actual==expected,(path,name,actual)
            assert calls and all(x[-1]==('other' if name=='other_context' else 'text') for x in calls)
            outputs[name]=actual
        rows[path]=outputs
    refused=[];doc=source_fixture()
    for variant in ('unknown_velocity','unknown_configuration'):
        model,_=source_model(doc,variant)
        try:evaluate(doc,model)
        except ValueError as exc:assert 'missing' in str(exc);refused.append(variant)
        else:raise AssertionError('Unknown source input guessed')
    return dict(cases=rows,unknown_inputs_refused=refused,caller_context_preserved=True,
        physical_configuration_derived=False,full_density_law_evaluated=False)


@lru_cache(None)
def generic_fixture():
    extra=''.join('r jg'+n+'[] '+t+'.' for n,t in BOUND)
    return candidate(text(LIBRARY),extra+'q['+k('sewy',*[k('jg'+n) for n,_ in BOUND])+'].')


def generic_checks():
    doc=generic_fixture();rows={}
    cases={'forward':('old','new',F(3),'old','new',F(3),True,True,True),
        'reversed':('old','new',F(3),'new','old',F(-3),True,True,False),
        'explicit_inverse':('new','old',F(-3),'new','old',F(-3),True,True,True),
        'invalid_values':('old','new',F(3),'old','new',F(3),False,True,False),
        'missing_relation':('old','new',F(3),'old','new',F(3),True,False,False),
        'same_reference_allowed_generically':('old','old',F(0),'old','old',F(0),True,True,True),
        'different_numeric_value':('old','new',F(3),'old','new',F(4),True,True,False)}
    for name,(ef,es,ev,first,second,value,valid,present,wanted) in cases.items():
        cuts,model=setup(doc)
        for n,x in dict(expectedfirst=ef,expectedsecond=es,first=first,second=second,context='text').items():model['jg'+n]=lambda x=x:x
        model['jgexpectedvalue']=lambda:cuts.make(ev);model['jgvalue']=lambda:cuts.make(value)
        callbacks(doc,model,{'jgvalid':lambda x:valid,'jgsame':lambda a,b:cuts.read(a)==cuts.read(b),
            'jgrelation':lambda a,b,value,context:present and context=='text'})
        actual=evaluate(doc,model);assert actual==[wanted],(name,actual);rows[name]=actual[0]
    return dict(cases=rows,generic_pair_need_not_be_distinct=True,reverse_relation_requires_explicit_binding=True)


def structural_checks():
    old=parse(text(PARENT));doc=parse(text(FULL))
    assert len(doc['statements'])==len(old['statements'])==206
    assert doc['declarations'][:len(old['declarations'])]==old['declarations']
    assert [x['name'] for x in doc['declarations'][len(old['declarations']):]]==['sewy','sewz']
    original=old['statements'][INDEX]['body']['arguments'][-1]['body']
    revised=doc['statements'][INDEX]['body']['arguments'][-1]['body']
    assert original['symbol']==revised['symbol']=='seoz'
    changed=[]
    for (name,_),a,b in zip(FIELDS,original['arguments'],revised['arguments'],strict=True):
        assert a==dict(kind='call',symbol=PREVIOUS_BINDINGS[name],arguments=[])
        assert b==dict(kind='call',symbol=BINDINGS[name],arguments=[])
        if a!=b:changed.append(name)
    assert changed==['frames']
    restored=deepcopy(doc['statements']);restored[INDEX]=old['statements'][INDEX]
    assert restored==old['statements']
    lookup={d['name']:d for d in doc['declarations']}
    assert {'ra','zbm','zb7','zqf','ba','sca','sewy'}<=_references(lookup['sewz'])
    # The earlier translation actually uses these named frames and velocity;
    # do not infer that connection from their matching numeric model values.
    assert {'ra','zbm','zb7','ta','rb'}<=_references(lookup['sfl'])
    paths={n:dependency_path(doc,INDEX,n) for n in ('sewy','sewz','ra','zbm','zb7','zqf','seoz','seoy','seou','sens')}
    assert all(paths.values())
    assert BINDINGS['lengthunit']=='ta' and BINDINGS['timeunit']=='rb'
    return dict(changed_arguments=changed,dependency_paths=paths,previous_206_statements_retained=True,
        other_205_statements_unchanged=True,new_primitives=0,existing_definitions_unchanged=True,
        physical_configuration_predicate_retained=True,coordinate_unit_fix_preserved=True)


def attribution_checks():
    source=parse(text(FULL));doc=extract_document(source,statement_indices=[INDEX]).document
    expected=doc['statements'][0]['body']['arguments'][-1]['body'];rows=[]
    for present,explain,order in product((False,True),repeat=3):
        model=guarded(doc)
        for name,value in dict(rd='author',zqa='earlier',zqb='node',zqc='scope',ri='text').items():model[name]=lambda value=value:value
        model.update(uh=lambda node,author,content,scope,context:present and json.loads(content.syntax)==expected,
            uf=lambda *args:explain,ue=lambda *args:order)
        result=evaluate(doc,model);assert result==[present and explain and order]
        rows.append(dict(present=present,explain=explain,order=order,value=result[0]))
    old=parse(text(PARENT));old['statements']=[old['statements'][INDEX]]
    previous=guarded(old);previous.update(model)
    assert evaluate(old,previous)==[False]
    return dict(cases=rows,old_quote_not_substituted=True,configuration_and_velocity_not_executed=True)


def alignment():
    source=json.loads(text('artifacts/written-units-v1/einstein-1905.json'))
    unit=next(x for x in source['units'] if x['id']=='einstein-1905:u0236')
    math=next(x for x in source['math'] if x['id']=='M0390')
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id='M0390',math_sha256=math['sha256'],
        status='partial_density_formula_with_ordered_frame_binding',definitions=['sewy','sewz','seoz','sens'])])


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
    paths=set(files)|{PARENT,'data/einstein-density-units-basis-v1.json','data/density-formula-review-v6.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json','tests/test_density_frame_binding.py','docs/density-frame-binding-v1.md'}
    paths.update('scripts/'+n+'.py' for n in ('compose_density_frame_binding','check_density_frame_binding','compose_density_units','compose_density_boost',
        'compose_origin_clock','compose_limits','compose_situated_criticism','compose_frame_translation',
        'check_coordinate_correspondence','check_described_appraisals','check_rod_setup','check_plane_waveforms','check_field_equations','check_tau_differential','check_angle_composition'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','integration_audit'))
    return dict(status='partial_density_formula_with_ordered_frame_binding',document=FULL,basis_audits=audits,
        structure=structural_checks(),source=source_checks(),generic=generic_checks(),attribution=attribution_checks(),
        roundtrips=True,cli_parse=True,alignment=alignment(),verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Ordered frame references, signed velocity and source quotation checked',flush=True)


if __name__=='__main__':main()
