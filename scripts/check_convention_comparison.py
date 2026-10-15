"""Check scoped counterfactual comparisons without inferring universal changes."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import transcribe
from scripts.compose_convention_comparison import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,HYPOTHETICAL,ROLES,build
from scripts.compose_limits import call as k,app,op,both,v
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_real_products import assertion,MEANINGS
from scripts.check_phi_normalization import number

REPORT=ROOT/'reports/convention-comparison-v1.json'
SYMBOLS={n:'jqs'+number_word(i) for i,(n,_) in enumerate(HYPOTHETICAL)}
DOMAIN=('x','y','z','first','second','excluded','other')
SCENES=('actual','alternative','unselected')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def fv(sort,callback):return FunctionValue(tuple(sort['parameters']),sort['result'],callback)


def fixture(path,source=False):
    declarations=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in HYPOTHETICAL if n!='candidates')
    declarations+='r '+SYMBOLS['candidates']+'[e d d] c.r jqscontext[] d.r jqsalternative[] d.'
    shared=[k(SYMBOLS[n]) for n,_ in HYPOTHETICAL[:-1]]+['p '+SYMBOLS['candidates']]
    def comparison(scene):return k('seqg',*shared[:5],*(app(k(SYMBOLS['other'+n]),scene) for n in ('force','acceleration','coefficient')))
    queries='q['+comparison(k('jqsalternative'))+'].q['+k('seqh',*shared,k('jqscontext'))+'].q['+comparison(k('jqscontext'))+'].'
    if source:queries='q[t[k seqj[]][k jqscontext[]]].'
    return abstract(candidate(text(path),declarations+queries),OPS)


class ComparisonModel:
    def __init__(self,doc,variant='baseline'):
        self.doc=doc;self.variant=variant;self.cuts,self.model=setup(doc)
        self.declarations={d['name']:d for d in doc['declarations']}
        make=self.cuts.make
        coefficient=lambda axis:F(4 if axis=='x' else 2)
        def acceleration(axis,case):return F(0 if variant=='all_zero' else 2 if case=='second' else 1)
        def force(axis,case):return coefficient(axis)*acceleration(axis,case)*(3 if variant=='invalid_base' else 1)
        def active(scene):return scene==('actual' if variant=='actual_only' else 'alternative')
        def changed_axis(axis):return axis=='y' if variant=='one_direction' else True
        def other_accel(scene,axis,case):
            if active(scene) and variant=='state_permutation':return acceleration(axis,'first' if case=='second' else 'second')
            return acceleration(axis,case)*(2 if active(scene) and variant=='proportional_change' else 1)
        def other_force(scene,axis,case):
            changed=active(scene) and changed_axis(axis) and variant!='identical_values'
            if variant=='outside_cases_only':changed=active(scene) and case=='excluded'
            return force(axis,case)*(2 if changed else 1)
        def other_coefficient(scene,axis):
            changed=active(scene) and changed_axis(axis) and variant not in ('proportional_change','identical_values','outside_cases_only')
            return coefficient(axis)*(3 if changed and variant=='wrong_coefficient' else 2 if changed else 1)
        entries={
            'cases':lambda case:variant!='empty_cases' and case in ('first','second'),
            'axes':lambda axis:variant!='empty_axes' and axis in ('x','y','z'),
            'basecoefficient':lambda axis:make(coefficient(axis)),
        }
        for name,fn in (('baseforce',force),('baseacceleration',acceleration)):
            sort=self.declarations[SYMBOLS[name]]['result']['result']
            entries[name]=lambda axis,fn=fn,sort=sort:fv(sort,lambda case:make(fn(axis,case)))
        for name,fn in (('otherforce',other_force),('otheracceleration',other_accel)):
            vector=self.declarations[SYMBOLS[name]]['result']['result'];value=vector['result']
            entries[name]=lambda scene,fn=fn,vector=vector,value=value:fv(vector,lambda axis:fv(value,lambda case:make(fn(scene,axis,case))))
        sort=self.declarations[SYMBOLS['othercoefficient']]['result']['result']
        entries['othercoefficient']=lambda scene:fv(sort,lambda axis:make(other_coefficient(scene,axis)))
        callbacks(doc,self.model,{SYMBOLS[n]:fn for n,fn in entries.items()})
        def candidates(content,context,scene):
            if variant=='unknown_candidates':raise ValueError('Counterfactual candidate selection missing')
            selected=() if variant=='empty_candidates' else ('alternative','unselected') if variant=='mixed_candidates' else ('alternative',)
            return context=='actual' and scene in selected
        self.model[SYMBOLS['candidates']]=candidates
        self.model.update(jqscontext=lambda:'unselected' if variant=='wrong_context' else 'actual',jqsalternative=lambda:'alternative')
        for name,field in {'zrbcases':'cases','zrbforce':'baseforce','zrbacceleration':'baseacceleration',
            'zrbalternateforce':'otherforce','zrbalternateacceleration':'otheracceleration','zrbalternatemass':'othercoefficient'}.items():
            self.model[name]=self.model[SYMBOLS[field]]
        self.model.update(zrbcandidates=candidates,zralongitudinal=lambda:make(4),zratransverse=lambda:make(2))
        for name,axis in zip(ROLES[:3],('x','y','z')):self.model[name]=lambda axis=axis:axis

    def evaluate(self):
        return [r['value'] for r in evaluate_document(self.doc,individuals=DOMAIN,situations=SCENES,
            primitives={d['name']:self.model[d['name']] for d in self.doc['declarations'] if d['kind']=='primitive'},max_steps=5_000_000)]


EXPECTED={
    'baseline':[True,True,False],'one_direction':[True,True,False],
    'proportional_change':[False,False,False],'identical_values':[False,False,False],
    'outside_cases_only':[False,False,False],'wrong_coefficient':[False,False,False],
    'invalid_base':[False,False,False],'state_permutation':[False,False,False],
    'all_zero':[False,False,False],'empty_cases':[False,False,False],
    'empty_axes':[False,False,False],'empty_candidates':[True,False,False],
    'mixed_candidates':[True,False,False],'actual_only':[False,False,True],
    'wrong_context':[True,False,False],
}


def comparison_checks():
    rows={}
    for path,source in ((LIBRARY,False),(CORE,True),(SOURCE,True)):
        doc=fixture(path,source);results={}
        for variant,expected in EXPECTED.items():
            if source and variant=='empty_axes':continue # Source selects its three axes explicitly.
            actual=ComparisonModel(doc,variant).evaluate();wanted=[expected[1]] if source else expected
            assert actual==wanted,(path,variant,actual,wanted);results[variant]=actual
        try:ComparisonModel(doc,'unknown_candidates').evaluate()
        except ValueError as exc:assert 'missing' in str(exc)
        else:raise AssertionError('Unknown counterfactual selection invented')
        rows[path]=results
    return {'cases':rows,'actual_and_selected_contexts_distinguished':True,
        'specified_finite_case_models_only':True,'physical_domain_completeness_proved':False}


def polynomial_checks():
    base='n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'
    a,f,g,c,d,r=map(v,('acceleration','force','otherforce','coefficient','othercoefficient','ratio'))
    eq=lambda x,y:op('e',x,y);mul=lambda x,y:k('ad',x,y);nonzero=lambda x:op('u',eq(x,number(0)))
    fit=eq(f,mul(c,a));otherfit=eq(g,mul(d,a))
    claims={
        'nonzero_input_identifies_coefficient':assertion('acceleration force coefficient othercoefficient',op('y',
            both(nonzero(a),fit,eq(f,mul(d,a))),eq(c,d))),
        'proportional_force_and_acceleration_keep_coefficient':assertion('acceleration force coefficient ratio',op('y',
            fit,eq(mul(r,f),mul(c,mul(r,a))))),
        'different_force_same_acceleration_requires_different_coefficient':assertion('acceleration force otherforce coefficient othercoefficient',op('y',
            both(nonzero(a),fit,otherfit,op('u',eq(f,g))),op('u',eq(c,d)))),
        'changing_both_evaluations_always_changes_coefficient':assertion('acceleration force coefficient ratio',op('y',
            both(nonzero(a),fit,k('aa',number(1),r)),op('u',eq(mul(r,f),mul(c,mul(r,a)))))),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),MEANINGS,timeout_ms=15000)[0]
        assert result['status']==('invalid' if name.startswith('changing_both') else 'valid'),(name,result)
        rows[name]=result
    return rows


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc)
    for name,value in {'zrbnode':'node','rd':'author','zrbscope':'scope','ri':'actual'}.items():model[name]=lambda value=value:value
    model['uh']=lambda node,author,content,scope,context:(node,author,scope,context)==('node','author','scope','actual') and json.loads(content.syntax)['symbol']=='seqj'
    result=evaluate_document(doc,individuals=('node','author','scope'),situations=('actual',),primitives=model)
    assert result[0]['value'] is True
    return {'quoted_content':'seqj','evaluations_or_counterfactuals_executed':False}


def alignment():
    source=json.loads(text('artifacts/written-units-v1/einstein-1905.json'))
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0259')
    start=unit['text'].index('würde man');end=unit['text'].index(';')
    return {'segments':[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],
        text=unit['text'][start:end],status='partial',definitions=['seqe','seqf','seqg','seqh','seqi','seqj'])]}


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));current=parse(text(SOURCE))
    assert current['statements'][:-1]==old['statements'] and len(old['statements'])==176
    assert current['declarations'][:len(old['declarations'])]==old['declarations']
    for p in (SOURCE,LIBRARY,CORE):
        doc=parse(text(p))
        for notation in ('full','compact'):
            rendered=format_graph(doc,notation);assert parse(rendered)==parse(transcribe(rendered,alphabet='v2'))==doc
        basis=next(json.loads(body) for q,body in files.items() if q.endswith('.json') and json.loads(body)['document']==p)
        audits[p]={k:v for k,v in audit_basis(doc,basis).items() if k!='definition_dependencies'}
        output=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(output.stdout)==doc
    reading=json.loads(text(READING));assert hashlib.sha256((ROOT/reading['facsimile_path']).read_bytes()).hexdigest()==reading['facsimile_sha256']
    for name in ('unit','unit_sha256','range','text'):assert reading[name]==alignment()['segments'][0][name]
    paths=set(files)|{PARENT,READING,reading['facsimile_path'],'data/einstein-force-mass-units-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'scripts/compose_convention_comparison.py','scripts/check_convention_comparison.py','tests/test_convention_comparison.py','docs/convention-comparison-v1.md',
        'scripts/compose_force_mass_units.py','scripts/compose_origin_clock.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/compose_field_equations.py','scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py',
        'scripts/check_plane_waveforms.py','scripts/check_rod_setup.py','scripts/check_real_products.py','scripts/check_phi_normalization.py',
        'scripts/check_angle_composition.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py'}
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','polynomial_proofs','rational_proofs','extraction','meaning_basis','script'))
    return dict(status='partial_counterfactual_convention_comparison',document=SOURCE,basis_audits=audits,
        comparisons=comparison_checks(),polynomial_checks=polynomial_checks(),attribution=attribution_check(),
        statements_preserved=176,new_author_attributions=1,roundtrips=True,cli_parse=True,alignment=alignment(),
        all_alternative_definitions_claimed_to_change_coefficients=False,comparison_caution_completed=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args()
    report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Scoped alternative conventions checked; universal change and full source meaning are not claimed',flush=True)


if __name__=='__main__':main()
