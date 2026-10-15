"""Check both directions of characterization and the three source projections."""
import argparse
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_law_characterization import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,SCALAR,FIELDS,ROLES,CATALOGUE,build
from scripts.compose_limits import call as k
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_integral_substitution import PolynomialIntegrals

REPORT=ROOT/'reports/law-characterization-v1.json'
PEOPLE=('theory','subject','frame','r1','r2','r3','c0','c1','c2','other')
QUERIES=('sevt','sevr','sevs','sevu','sevv','sevw')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model,people=PEOPLE):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=people,situations=('text','other'),primitives={n:model[n] for n in names},
        max_steps=12_000_000,memoize_definitions=True,memoize_expressions=True)]


def fixture(path=LIBRARY):
    declarations=''.join('r jchar'+n+'[] '+sort+'.' for n,sort in FIELDS)
    values=[k('jchar'+n) for n,_ in FIELDS]
    return candidate(text(path),declarations+''.join('q['+k(n,*values)+'].' for n in QUERIES))


def generic_model(doc,allowed_mask=3,formula_mask=3,variant='baseline'):
    model=guarded(doc)
    for n in ('theory','subject','frame','context'):model['jchar'+n]=lambda n=n:'text' if n=='context' else n
    selected=lambda relation:variant!='no_relations' and relation in ('r1','r2','r3')
    def scope(case,context):return variant!='empty_scope' and context=='text' and case in (('c0','c1','c2') if variant=='expanded_scope' else ('c0','c1'))
    def bound(case,subject,frame,context):return variant!='wrong_binding' and (subject,frame,context)==('subject','frame','text')
    def applicable(relation,case,context):
        if variant=='unknown_applicability':raise ValueError('Applicability missing')
        if variant=='unconstrained_case' and case=='c1':return False
        if variant=='simultaneous' and case=='c0' and relation=='r2':return True
        return (relation,case) in [('r1','c0'),('r2','c1'),('r3','c2')]
    def conditions(relation,case,context):
        if variant=='unknown_conditions':raise ValueError('Condition interpretation missing')
        if variant=='simultaneous' and case=='c0' and relation=='r2':return False
        return case in ('c0','c1') and bool(formula_mask & (1<<int(case[1])))
    def allowed(theory,subject,frame,case,context):
        if variant=='unknown_theory':raise ValueError('Theory interpretation missing')
        return (theory,subject,frame,context)==('theory','subject','frame','text') and (case=='c2' or case in ('c0','c1') and bool(allowed_mask & (1<<int(case[1]))))
    callbacks(doc,model,{'jchar'+n:f for n,f in dict(selected=selected,scope=scope,bound=bound,applicable=applicable,conditions=conditions,allowed=allowed).items()})
    return model


def truth_table_checks():
    rows={}
    for path in (LIBRARY,CORE):
        doc=fixture(path);output={}
        for allowed in range(4):
            for formula in range(4):
                extra=bool(formula & ~allowed);missing=bool(allowed & ~formula)
                wanted=[allowed==formula,not missing,not extra,extra,missing,True]
                actual=evaluate(doc,generic_model(doc,allowed,formula));assert actual==wanted,(path,allowed,formula,actual)
                output[f'{allowed}:{formula}']=actual
        rows[path]=output
    return dict(two_case_masks=rows,scope_is_finite=True,infinite_trajectory_space_proved=False)


def boundary_checks():
    doc=fixture();cases={
        'baseline':[True,True,True,False,False,True],
        'empty_scope':[False,True,True,False,False,True],
        'no_relations':[False,True,True,False,False,False],
        'wrong_binding':[False,True,True,False,False,True],
        'expanded_scope':[False,False,True,False,True,True],
        'unconstrained_case':[True,True,True,False,False,False],
        'simultaneous':[False,False,True,False,True,True],
    };rows={}
    for name,wanted in cases.items():
        actual=evaluate(doc,generic_model(doc,variant=name));assert actual==wanted,(name,actual);rows[name]=actual
    refused=[]
    for name in ('unknown_applicability','unknown_conditions','unknown_theory'):
        try:evaluate(doc,generic_model(doc,variant=name))
        except ValueError as exc:assert 'missing' in str(exc),str(exc);refused.append(name)
        else:raise AssertionError('Missing interpretation filled in')
    return dict(cases=rows,unknown_interpretations_refused=refused,coverage_is_not_equivalence=True)


def source_fixture(path):
    declarations='r jcharprofile[] '+SCALAR+'.r jcharbadprofile[] '+SCALAR+'.'
    values=[k('zrptheory'),k('zramatter'),k('ra'),k('ri'),'p sevx',k('zrpscope'),k('zrpbound'),k('zrpapplicable'),'p sevy',k('zrpallowed')]
    query='q[t[k sewa[]][k ri[]]].'+''.join('q['+k(n,*values)+'].' for n in QUERIES[1:])
    return abstract(candidate(text(path),declarations+query),OPS|{'sede'})


class SourceModel(PolynomialIntegrals):
    def __init__(self,doc,variant='baseline'):
        super().__init__(doc);make=self.cuts.make
        for symbol,value in {'zrptheory':'theory','zramatter':'subject','ra':'frame','ri':'text',**{n:'r'+str(i+1) for i,(n,_,_) in enumerate(CATALOGUE)}}.items():self.model[symbol]=lambda value=value:value
        if variant=='duplicate_relation':self.model[CATALOGUE[2][0]]=lambda:'r1'
        for n in ROLES:self.model['zrp'+n]=lambda n=n:n
        # Explicit constant interpretations on the model's whole individual
        # domain; these are synthetic values, never defaults for absent data.
        baseline=dict(light=5,speed=3,beta=F(5,4),mass=2,charge=2,electricresponse=5,magneticresponse=3,
            drop=F(25,4),magnetic=5,radius=F(15,4),lower=0,upper=5)
        def value(case,role,context):
            if variant=='unknown_value':raise ValueError('Case value missing')
            if case=='c0' and role=='magneticresponse' and variant in ('bad_ratio','theory_agrees_bad_ratio'):return make(4)
            if case=='c1' and role=='drop' and variant=='bad_potential_value':return make(7)
            if case=='c2' and role=='radius' and variant in ('bad_radius','sample_scope'):return make(4)
            return make(baseline[role])
        self.register('jcharprofile',(F(5,4),));self.register('jcharbadprofile',(F(1),))
        def profile(case,context):return self.model['jcharbadprofile' if variant=='bad_potential_field' and case=='c1' else 'jcharprofile']()
        def scope(case,context):return context=='text' and case in (('c0',) if variant=='sample_scope' else ('c0','c1','c2'))
        def bound(case,subject,frame,context):return (subject,frame,context)==('subject','frame','text') and not (variant=='wrong_binding' and case=='c1')
        def applicable(relation,case,context):
            if variant=='unknown_applicability':raise ValueError('Applicability missing')
            return context=='text' and (relation,case) in [('r1','c0'),('r2','c1'),('r3','c2')]
        def allowed(theory,subject,frame,case,context):
            if variant=='unknown_theory':raise ValueError('Theory interpretation missing')
            return (theory,subject,frame,context)==('theory','subject','frame','text') and case in ('c0','c1','c2') and not (variant in ('theory_rejects_ratio','theory_agrees_bad_ratio') and case=='c0')
        callbacks(doc,self.model,{'zrpvalues':value,'zrpprofile':profile,'zrpscope':scope,'zrpbound':bound,'zrpapplicable':applicable,'zrpallowed':allowed})


def source_checks():
    cases={'baseline':[True,True,True,False,False,True],
        **{name:[False,False,True,False,True,True] for name in ('bad_ratio','bad_potential_value','bad_potential_field','bad_radius')},
        'theory_rejects_ratio':[False,True,False,True,False,True],
        'theory_agrees_bad_ratio':[True,True,True,False,False,True],
        'sample_scope':[True,True,True,False,False,True],
        'wrong_binding':[False,True,True,False,False,True],
        'duplicate_relation':[False,True,True,False,False,False]}
    rows={}
    for path in (CORE,SOURCE):
        doc=source_fixture(path);output={}
        for name,wanted in cases.items():
            actual=evaluate(doc,SourceModel(doc,name).model,PEOPLE+tuple(ROLES));assert actual==wanted,(path,name,actual,wanted);output[name]=actual
        rows[path]=output
    refused=[];doc=source_fixture(CORE)
    for name in ('unknown_value','unknown_applicability','unknown_theory'):
        try:evaluate(doc,SourceModel(doc,name).model,PEOPLE+tuple(ROLES))
        except ValueError as exc:assert 'missing' in str(exc),str(exc);refused.append(name)
        else:raise AssertionError('Unknown source data invented')
    return dict(cases=rows,unknown_inputs_refused=refused,synthetic_total_functions=True,actual_electron_theory_characterization_proved=False)


def catalogue_checks():
    doc=parse(text(CORE));lookup={d['name']:d for d in doc['declarations']}
    quoted=lookup['sevz']['body'];assert quoted['kind']=='sequence' and len(quoted['items'])==3
    targets=[x['body']['symbol'] for x in quoted['items']];assert targets==[n for _,n,_ in CATALOGUE]
    def calls(node):
        if isinstance(node,list):return [x for item in node for x in calls(item)]
        if not isinstance(node,dict):return []
        return ([node['symbol']] if node.get('kind')=='call' else [])+[x for item in node.values() for x in calls(item)]
    dependencies=calls(lookup['sevy']['body'])
    for symbol in ('sets','seur','seus','sevh'):assert symbol in dependencies
    for node,_,_ in CATALOGUE:assert node in dependencies
    # Quoting all three source bodies must not run their numerical or physical inputs.
    quoted_doc=candidate(text(CORE),'q[e[k sevz[]][k sevz[]]].')
    assert evaluate(quoted_doc,guarded(quoted_doc))==[True]
    return dict(source_contents=targets,projected_relations=['sets','seur','seus','sevh'],quoted_bodies_executed=False)


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc);seen=[]
    for n,value in {'zrpnode':'claim','rd':'author','zrpdiscussion':'discussion','ri':'text'}.items():model[n]=lambda value=value:value
    def claim(node,author,content,scope,context):
        target=json.loads(content.syntax)['symbol'];seen.append(target)
        return (node,author,target,scope,context)==('claim','author','sewa','discussion','text')
    model['uh']=claim
    r=evaluate_document(doc,individuals=('claim','author','discussion'),situations=('text',),primitives=model)
    assert [x['value'] for x in r]==[True]
    return dict(quoted_targets=seen,completeness_claim_evaluated=False)


def alignment():
    w=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));u=next(x for x in w['units'] if x['id']=='einstein-1905:u0275')
    return dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],
        status='partial_scope_relative_characterization_by_three_relations',definitions=['sevt','sevx','sevy','sevz','sewa'])])


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));doc=parse(text(SOURCE));assert len(old['statements'])==203 and doc['statements'][:-1]==old['statements']
    assert doc['declarations'][:len(old['declarations'])]==old['declarations']
    for p in (SOURCE,LIBRARY,CORE):
        document=parse(text(p));basis=next(json.loads(x) for q,x in files.items() if q.endswith('.json') and json.loads(x)['document']==p)
        audits[p]={k:v for k,v in audit_basis(document,basis).items() if k!='definition_dependencies'}
        for notation in ('full','compact'):
            output=format_graph(document,notation);assert parse(output)==parse(transcribe(output,alphabet='v2'))==document
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8');assert json.loads(result.stdout)==document
    reading=json.loads(text(READING));assert reading['segments']==alignment()['segments']
    assert hashlib.sha256((ROOT/reading['facsimile_path']).read_bytes()).hexdigest()==reading['facsimile_sha256']
    paths=set(files)|{PARENT,READING,reading['facsimile_path'],'data/einstein-magnetic-curvature-basis-v1.json','artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json','tests/test_law_characterization.py','docs/law-characterization-v1.md'}
    paths.update('scripts/'+n+'.py' for n in ('compose_law_characterization','check_law_characterization','compose_convention_comparison','compose_origin_clock','compose_limits','compose_situated_criticism','check_coordinate_correspondence','check_described_appraisals','check_plane_waveforms','check_rod_setup','check_integral_substitution','check_material_acceleration','check_quantities','check_real_products','check_phi_normalization','check_tau_differential','check_angle_composition'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','polynomial_proofs'))
    return dict(status='partial_scope_relative_characterization_by_three_relations',document=SOURCE,basis_audits=audits,
        truth_tables=truth_table_checks(),boundaries=boundary_checks(),source=source_checks(),catalogue=catalogue_checks(),attribution=attribution_check(),
        statements_preserved=203,new_author_attributions=1,roundtrips=True,cli_parse=True,alignment=alignment(),verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();r=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==r
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print('Scope-relative characterization and source projections checked',flush=True)


if __name__=='__main__':main()
