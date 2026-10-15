"""Check spatial curvature, derivative bindings and the source's signed branch."""
import argparse
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import transcribe
from scripts.compose_magnetic_curvature import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,CUT,GEOMETRY,NUMERIC,AT,build
from scripts.compose_limits import call as k,both,op,v
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_real_products import MEANINGS,assertion
from scripts.check_material_acceleration import PolynomialModel,SYMBOLS,LAW,ABSTRACT,PEOPLE,unwrap

REPORT=ROOT/'reports/magnetic-curvature-v1.json'


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=PEOPLE,situations=('text','other'),primitives={n:model[n] for n in names},
        max_steps=5_000_000,memoize_definitions=True,memoize_expressions=True)]


def numeric_checks():
    geometry={
        'normal':((3,0,0,0,F(-12,5),0,F(15,4)),True),
        'tangential_added':((3,0,0,100,F(-12,5),0,F(15,4)),True),
        'rotated':((0,3,0,F(12,5),100,0,F(15,4)),True),
        'space_curve':((1,1,0,0,0,1,2),True),
        'rest':((0,0,0,1,1,1,2),False),
        'straight_accelerating':((3,0,0,2,0,0,4),False),
        'negative_radius':((3,0,0,0,F(-12,5),0,F(-15,4)),False),
        'wrong_radius':((3,0,0,0,F(-12,5),0,4),False),
    };rows={}
    rational=format_graph(extract_document(parse(text(LIBRARY)),roots=['sevb','seve','sevg','sevi'],statement_indices=[]).document,'compact')
    for name,(values,wanted) in geometry.items():
        actual=evaluate(parse(rational+'q['+k('sevb',*map(number,values))+'].'),ARITHMETIC)
        for path in (LIBRARY,CORE):
            doc=abstract(candidate(text(path),'q['+k('sevc',*(k('bb',number(x)) for x in values))+'].'),OPS)
            _,model=setup(doc);model.update(ARITHMETIC);actual+=evaluate(doc,model)
        assert actual==[wanted]*3,(name,actual);rows[name]=actual
    physics={
        'printed_orientation':((5,3,F(5,4),2,2,5,F(-12,5),F(15,4)),[True]*3),
        'negative_charge':((5,3,F(5,4),2,-2,5,F(12,5),F(15,4)),[False,False,True]),
        'negative_field':((5,3,F(5,4),2,2,-5,F(12,5),F(15,4)),[False,False,True]),
        'both_negative':((5,3,F(5,4),2,-2,-5,F(-12,5),F(15,4)),[True]*3),
        'zero_field':((5,3,F(5,4),2,2,0,0,1),[False]*3),
        'rest':((5,0,1,2,2,5,0,1),[False]*3),
        'zero_charge':((5,3,F(5,4),2,0,5,0,1),[False]*3),
        'wrong_acceleration':((5,3,F(5,4),2,2,5,F(-11,5),F(15,4)),[False,True,False]),
    };results={}
    for name,(values,wanted) in physics.items():
        actual=[]
        for path,real in ((None,False),(LIBRARY,True),(CORE,True)):
            nums=[k('bb',number(x)) if real else number(x) for x in values]
            names=('sevf','sevh','sevj') if real else ('seve','sevg','sevi')
            q=''.join('q['+k(n,*(nums if i!=1 else nums[:6]+nums[7:]))+'].' for i,n in enumerate(names))
            if real:
                doc=abstract(candidate(text(path),q),OPS);_,model=setup(doc);model.update(ARITHMETIC)
            else:doc=parse(rational+q);model=ARITHMETIC
            actual+=evaluate(doc,model)
        assert actual==wanted*3,(name,actual);results[name]=actual
    return dict(geometry=rows,magnetic=results)


def polynomial_checks():
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['sevb','seve','sevg','sevi'],statement_indices=[]).document,'compact')
    eq=lambda a,b:op('e',a,b);mul=lambda a,b:k('ad',a,b);sq=lambda a:mul(a,a);add=lambda a,b:k('ab',a,b)
    zero=number(0);terms=list(map(v,NUMERIC.split()));V,s,b,m,q,N,a,R=terms
    law=k('setj',V,s,b,m,q,zero,N,a);chain=k('seve',*terms);formula=k('sevg',*terms[:6],R)
    geo=list(map(v,GEOMETRY.split()));shift=v('shift')
    moved=geo[:3]+[add(geo[i+3],mul(shift,geo[i])) for i in range(3)]+geo[6:]
    claims={
        'tangential_acceleration_preserves_radius':assertion(GEOMETRY+' shift',op('z',k('sevb',*geo),k('sevb',*moved))),
        'quarter_turn_preserves_radius':assertion(GEOMETRY,op('z',k('sevb',*geo),k('sevb',k('ac',geo[1]),geo[0],geo[2],k('ac',geo[4]),geo[3],geo[5],geo[6]))),
        'geometry_and_oriented_magnetic_law_imply_printed_chain':assertion(NUMERIC+' tangent',op('y',both(law,k('aa',zero,mul(q,N)),
            k('sevb',s,zero,zero,v('tangent'),a,zero,R)),chain)),
        'printed_forms_are_equivalent_under_motion_law':assertion(NUMERIC,op('y',law,op('z',chain,formula))),
        'direction_independent_radius_keeps_squared_magnetic_product':assertion(NUMERIC,op('y',k('sevi',*terms),eq(sq(mul(R,mul(q,N))),sq(mul(mul(m,b),mul(V,s)))))),
        'same_radius_requires_same_bending_direction':assertion('',op('y',both(
            k('sevi',*map(number,(5,3,F(5,4),2,2,5,F(-12,5),F(15,4)))),
            k('sevi',*map(number,(5,3,F(5,4),2,-2,5,F(12,5),F(15,4))))),eq(number(F(-12,5)),number(F(12,5))))),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),MEANINGS,timeout_ms=20000)[0]
        assert result['status']==('invalid' if name.startswith('same_radius') else 'valid'),(name,result);rows[name]=result
    return rows


def trajectory_fixture(path,source=False,abstracted=ABSTRACT):
    declarations=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in LAW)+'r jcurvradius[] '+CUT+'.'
    if source:
        q=''.join('q[t[k '+n+'[]][k ri[]]].' for n in ('sevl','sevm','sevn','sevo'))
        q+='q['+k('sevj',k('tc'),k('zb7'),k('soy',k('tc'),k('zb7')),k('zramu'),k('zrgcharge'),k('zromagnetic'),k('zroay'),k('zroradius'))+'].'
    else:q='q['+k('sevd',*[k(SYMBOLS[n]) for n,_ in AT],k('jcurvradius'))+'].'
    return abstract(candidate(text(path),declarations+q),abstracted)


class CurvatureModel(PolynomialModel):
    def __init__(self,doc,variant='baseline'):
        charge=F(-2 if variant in ('reversed_charge','both_negative') else 0 if variant=='zero_charge' else 2)
        magnetic=F(-5 if variant=='both_negative' else 0 if variant=='zero_field' else 5)
        speed=F(0 if variant=='rest' else 3);beta=F(1 if speed==0 else F(5,4))
        ay=-charge*speed*magnetic/(2*beta*5)
        if variant=='wrong_bending_direction':ay=-ay
        tangent=F(4 if variant=='tangential_acceleration' else 0)
        super().__init__(doc,variant,quadratic=(tangent/2,ay/2,0),velocity=(speed,0,0))
        self.model.update(ARITHMETIC);make=self.cuts.make;read=self.cuts.read
        radius=F(4 if variant=='wrong_radius' else F(15,4));self.model['jcurvradius']=lambda:make(radius)
        if 'sevl' not in self.declarations:return
        for name,val in {'tc':5,'zb7':speed,'zramu':2,'zrgcharge':charge,'zromagnetic':magnetic,'zroradius':radius}.items():self.model[name]=lambda val=val:make(val)
        for n in ('domain','curve','event','point','velocityx','velocityy','velocityz','ax','ay'):
            self.model['zro'+n]=self.model[SYMBOLS[n]]
        if variant=='wrong_source_event':self.model['zroevent']=lambda:'other'
        field_sort=self.declarations['zroelectricfield']['result']['result']
        def electric(axis):
            def value(*coordinates):
                if tuple(map(read,coordinates))!=(1,2,3,0):raise ValueError('Field evaluated at a different event')
                return make(F(125,16) if axis=='x' and tangent else 1 if axis=='y' and variant=='transverse_electric' else 0)
            return FunctionValue(tuple(field_sort['parameters']),field_sort['result'],value)
        def field(axis):
            def value(*coordinates):
                if tuple(map(read,coordinates))!=(1,2,3,0):raise ValueError('Field evaluated at a different event')
                return make(magnetic+(variant=='wrong_magnetic_value') if axis=='z' else 0)
            return FunctionValue(tuple(field_sort['parameters']),field_sort['result'],value)
        def region(*coordinates):return variant!='outside_field_region' and tuple(map(read,coordinates))==(1,2,3,0)
        def only(matter,frame,event,magneticfield,context):
            if variant=='unknown_only':raise ValueError('Other deflection causes unknown')
            return variant!='other_deflection' and (matter,frame,event,context)==('matter','frame','event','text') and unwrap(magneticfield).implementation is field
        def assigned(frame,electricfield,magneticfield,area,context):
            return variant!='wrong_field_frame' and (frame,context)==('frame','text') and unwrap(electricfield).implementation is electric and unwrap(magneticfield).implementation is field and unwrap(area).implementation is region
        callbacks(doc,self.model,{'zroelectricfield':electric,'zromagneticfield':field,'zroregion':region,'zroonly':only})
        self.model['znn']=assigned


def trajectory_checks():
    variants=('baseline','tangential_acceleration','reversed_charge','both_negative','fake_velocity_field','wrong_acceleration','sample_alias_field',
        'missing_history','isolated','one_sided','wrong_matter','wrong_frame','wrong_event','wrong_context','wrong_radius','zero_field','rest','zero_charge')
    rows={}
    for path in (LIBRARY,CORE):
        doc=trajectory_fixture(path);output={}
        for name in variants:
            actual=evaluate(doc,CurvatureModel(doc,name).model);wanted=name in ('baseline','tangential_acceleration','reversed_charge','both_negative')
            assert actual==[wanted],(path,name,actual);output[name]=actual[0]
        rows[path]=output
    doc=trajectory_fixture(LIBRARY,abstracted=OPS|{'sjs'})
    try:evaluate(doc,CurvatureModel(doc).model)
    except ValueError as exc:assert any(w in str(exc).lower() for w in ('domain','enumerat','quantif','function','rational')),str(exc)
    else:raise AssertionError('Unrestricted history silently sampled')
    return dict(cases=rows,all_cut_history_and_derivative_fields_refused=True,registered_polynomial_derivatives=True)


def source_checks():
    cases={'baseline':[True]*5,'tangential_acceleration':[True]*5,'both_negative':[True]*5,'reversed_charge':[True,False,False,False,True],
        'wrong_bending_direction':[True,False,True,False,False],
        **{n:[False]*5 for n in ('zero_field','zero_charge','rest','wrong_radius')},
        **{n:[False,False,False,False,True] for n in ('other_deflection','transverse_electric','wrong_magnetic_value','wrong_field_frame','outside_field_region','missing_history','fake_velocity_field','wrong_source_event')}}
    rows={}
    for path in (CORE,SOURCE):
        doc=trajectory_fixture(path,True);output={}
        for name,wanted in cases.items():
            actual=evaluate(doc,CurvatureModel(doc,name).model);assert actual==wanted,(path,name,actual,wanted);output[name]=actual
        rows[path]=output
    doc=trajectory_fixture(CORE,True)
    try:evaluate(doc,CurvatureModel(doc,'unknown_only').model)
    except ValueError as exc:assert 'unknown' in str(exc),str(exc)
    else:raise AssertionError('Other force causes silently excluded')
    return dict(cases=rows,unknown_exclusivity_refused=True)


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc);seen=[]
    labels={'zrochainnode':'chain','zroradiusnode':'radius','zroreasonnode':'reason','zroreformnode':'reform','rd':'author','zroscope':'scope','ri':'text'}
    for n,value in labels.items():model[n]=lambda value=value:value
    symbol=lambda x:json.loads(x.syntax)['symbol']
    def claim(node,author,content,scope,context):
        seen.append(['claim',symbol(content)])
        return (node,symbol(content)) in [('chain','sevm'),('radius','sevn')] and (author,scope,context)==('author','scope','text')
    def reason(node,author,premise,conclusion,scope,context):
        seen.append(['reason',symbol(premise),symbol(conclusion)])
        return (node,symbol(premise),symbol(conclusion)) in [('reason','sevo','sevm'),('reform','sevm','sevn')] and (author,scope,context)==('author','scope','text')
    model.update(uh=claim,zc=reason)
    result=evaluate_document(doc,individuals=tuple(labels.values())[:-1],situations=('text',),primitives=model)
    assert [r['value'] for r in result]==[True]*4
    return dict(quoted_targets=seen,trajectories_and_fields_executed=False)


def alignment():
    work=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));rows=[]
    for u in work['units']:
        if u['id'].split(':')[1] not in ('u0271','u0272','u0273','u0274'):continue
        base=dict(unit=u['id'],unit_sha256=u['text_sha256'],status='partial_local_magnetic_curvature_and_printed_orientation',definitions=['sevd','sevk','sevm','sevn','sevo'])
        if u['kind']=='body':rows.append(dict(base,range=[0,len(u['text'])],text=u['text']))
        rows.extend(dict(base,math_id=mid) for mid in u['math_ids'])
    return dict(segments=rows)


def printed_equations():
    work=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));rows={};ns='{http://www.w3.org/1998/Math/MathML}'
    leaves=lambda x:[(e.text or '').strip() for e in x.iter() if not len(e) and (e.text or '').strip()]
    for mid in ('M0441','M0442'):
        item=next(m for m in work['math'] if m['id']==mid);root=ET.fromstring(item['mathml'])
        fractions=[[leaves(child) for child in f] for f in root.iter(ns+'mfrac')]
        assert len(list(root.iter(ns+'msqrt')))==1
        if mid=='M0441':
            assert leaves(root)[0]=='−'
            assert fractions[:4]==[[['d','2','y'],['d','t','2']],[['v','2'],['R']],[['ϵ'],['μ']],[['v'],['V']]]
        else:
            assert leaves(root)[:4]==['R','=','V','2']
            assert fractions[0]==[['μ'],['ϵ']] and fractions[-1]==[['1'],['N']]
        rows[mid]=dict(math_sha256=item['sha256'],fractions=fractions,leaf_sequence=leaves(root))
    return rows


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));doc=parse(text(SOURCE));assert len(old['statements'])==199 and doc['statements'][:-4]==old['statements']
    assert doc['declarations'][:len(old['declarations'])]==old['declarations']
    for p in (SOURCE,LIBRARY,CORE):
        document=parse(text(p));basis=next(json.loads(x) for q,x in files.items() if q.endswith('.json') and json.loads(x)['document']==p)
        audits[p]={k:v for k,v in audit_basis(document,basis).items() if k!='definition_dependencies'}
        for notation in ('full','compact'):
            output=format_graph(document,notation);assert parse(output)==parse(transcribe(output,alphabet='v2'))==document
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8');assert json.loads(result.stdout)==document
    reading=json.loads(text(READING));assert reading['segments']==alignment()['segments']
    assert hashlib.sha256((ROOT/reading['facsimile_path']).read_bytes()).hexdigest()==reading['facsimile_sha256']
    paths=set(files)|{PARENT,READING,reading['facsimile_path'],'data/einstein-potential-speed-basis-v1.json','artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json','tests/test_magnetic_curvature.py','docs/magnetic-curvature-v1.md'}
    paths.update('scripts/'+n+'.py' for n in ('compose_magnetic_curvature','check_magnetic_curvature','compose_convention_comparison','compose_origin_clock','compose_limits','compose_situated_criticism','compose_material_acceleration','compose_material_velocity','compose_field_equations','check_coordinate_correspondence','check_described_appraisals','check_plane_waveforms','check_rod_setup','check_phi_normalization','check_quantities','check_real_products','check_material_acceleration','check_tau_differential','check_angle_composition'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','polynomial_proofs'))
    return dict(status='partial_local_magnetic_curvature_and_printed_orientation',document=SOURCE,basis_audits=audits,numeric=numeric_checks(),
        polynomial=polynomial_checks(),trajectory=trajectory_checks(),source=source_checks(),attribution=attribution_check(),printed_equations=printed_equations(),
        statements_preserved=199,new_author_attributions=4,roundtrips=True,cli_parse=True,alignment=alignment(),verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();r=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==r
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print('Local curvature and magnetic orientation checked',flush=True)


if __name__=='__main__':main()
