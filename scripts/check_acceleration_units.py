"""Verify time-squared unit conversion and its coordinate-record bindings."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import transcribe
from scripts.compose_acceleration_units import ROOT,PARENT,SOURCE,LIBRARY,CORE,ALL,LAW,META,READINGS,INPUTS,TRACK,basis,build
from scripts.compose_limits import call as k,app,op,both,v
from scripts.check_material_acceleration import PolynomialModel,SYMBOLS as OLD_SYMBOLS,PEOPLE,ABSTRACT,unwrap
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,evaluate,OPS
from scripts.check_rod_setup import callbacks
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_real_products import MEANINGS,assertion

REPORT=ROOT/'reports/acceleration-units-v1.json'
SYMBOLS={**OLD_SYMBOLS,**{n:'jqu'+number_word(i) for i,(n,_) in enumerate(META+READINGS)}}
DOMAIN=PEOPLE+('lengthunit','timeunit','lengthaxis','timeaxis')
WORLD=basis()['source_symbols']['worldlines']


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def numerical_checks():
    cases={'scaled':((2,3,5,9,F(2,5)),True),'negative_acceleration':((2,3,5,-9,F(-2,5)),True),
        'zero':((2,3,5,0,0),True),'coherent_units':((18,3,2,7,7),True),
        'time_not_squared':((2,3,5,9,F(6,5)),False),'inverse_scale_direction':((2,3,5,9,F(405,2)),False),
        'raw_coordinate_used_as_reading':((2,3,5,9,9),False),'lost_sign':((2,3,5,-9,F(2,5)),False),
        'zero_length_at_zero_input':((0,3,5,0,0),False),'zero_time_at_zero_input':((2,0,5,0,0),False),
        'negative_time':((2,-3,5,9,F(2,5)),False),'negative_acceleration_unit':((2,3,-5,9,F(-2,5)),False)}
    rational=extract_document(parse(text(LIBRARY)),roots=['seps'],statement_indices=[]).document
    base=format_graph(rational,'compact');rows={}
    for label,(args,expected) in cases.items():
        doc=parse(base+'q['+k('seps',*map(number,args))+'].')
        rational_value=evaluate_document(doc,individuals=('object',),situations=('text',),
            primitives={n:ARITHMETIC[n] for n in ('aa','ad')})[0]['value']
        results=[rational_value]
        for path in (LIBRARY,CORE):
            doc=abstract(candidate(text(path),'q['+k('sept',*(k('bb',number(a)) for a in args))+'].'),OPS)
            _,model=setup(doc);results.append(evaluate(doc,model)[0])
        assert results==[expected]*3,(label,results)
        rows[label]=results
    return rows


def polynomial_checks():
    doc=extract_document(parse(text(LIBRARY)),roots=['seps'],statement_indices=[]).document
    base=format_graph(doc,'compact');L,T,A,x,y,z=map(v,'length time unit x y z'.split())
    relation=lambda x,y:k('seps',L,T,A,x,y);mul=lambda x,y:k('ad',x,y);zero=number(0)
    L2,T2,A2=map(v,('secondlength','secondtime','secondunit'))
    claims={
        'converted_reading_is_unique':assertion('length time unit x y z',op('y',both(relation(x,y),relation(x,z)),op('e',y,z))),
        'zero_preserved_in_both_directions':assertion('length time unit x y',op('y',relation(x,y),op('z',op('e',x,zero),op('e',y,zero)))),
        'positive_reading_preserves_orientation':assertion('length time unit x y',op('y',relation(x,y),op('z',k('aa',zero,x),k('aa',zero,y)))),
        'coherent_scale_recovers_same_number':assertion('length time unit x y',op('y',both(relation(x,y),op('e',L,mul(A,mul(T,T)))),op('e',x,y))),
        'consecutive_conversions_compose':assertion('length time unit secondlength secondtime secondunit x y z',op('y',
            both(relation(x,y),k('seps',L2,T2,A2,y,z)),k('seps',mul(L,L2),mul(T,T2),mul(A,A2),x,z))),
        'one_power_of_time_would_suffice':assertion('length time unit x y',op('y',relation(x,y),op('e',mul(mul(y,A),T),mul(x,L)))),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),{n:MEANINGS[n] for n in ('aa','ad')},timeout_ms=20000)[0]
        assert result['status']==('invalid' if name.startswith('one_power') else 'valid'),(name,result)
        rows[name]=result
    return rows


class UnitModel(PolynomialModel):
    def __init__(self,doc,variant='baseline'):
        super().__init__(doc,variant)
        self.model.update(ARITHMETIC)
        make,read=self.cuts.make,self.cuts.read
        self.scales=(F(2),F(0 if variant=='zero_time_scale' else 3),F(5))
        factor=F(45,2);self.converted=(F(4,45),F(-4,45),F(8,45))
        if variant=='unconverted_reading':self.converted=(F(2),F(-2),F(4))
        if variant=='linear_time_scale':self.converted=(F(4,15),F(-4,15),F(8,15))
        for (name,_),value in zip(READINGS,self.converted):self.model[SYMBOLS[name]]=lambda value=value:make(value)
        for name,value in {'longitudinal':F(125,16)*factor,'transverse':F(25,4)*factor+(1 if variant=='wrong_coefficient' else 0)}.items():
            self.model[SYMBOLS[name]]=lambda value=value:make(value)
        self.model['zralongitudinal']=self.model[SYMBOLS['longitudinal']];self.model['zratransverse']=self.model[SYMBOLS['transverse']]
        self.model['zramu']=lambda:make(4*factor)
        for name in ('lengthunit','timeunit','lengthaxis','timeaxis'):
            value='lengthaxis' if name=='timeaxis' and variant=='same_dimension_axes' else name
            self.model[SYMBOLS[name]]=lambda value=value,name=name:'other' if variant=='wrong_'+name else value
        for (name,_),scale in zip(META[7:10],self.scales):self.model[SYMBOLS[name]]=lambda scale=scale:make(scale)
        self.dimensions={
            'lengthdim':lambda axis:F(axis=='lengthaxis'),
            'timedim':lambda axis:F(axis=='timeaxis'),
            'accelerationdim':lambda axis:F(axis=='lengthaxis')-F(1 if variant=='velocity_dimension' else 2)*F(axis=='timeaxis')}
        entries={SYMBOLS[name]:fn for name,fn in self.dimensions.items()}
        def units(unit,dimension,scale,context):
            if variant=='unknown_units':raise ValueError('Unit calibration interpretation missing')
            rows={'lengthunit':('lengthdim',self.scales[0]),'timeunit':('timedim',self.scales[1]),
                'accelerationunit':('accelerationdim',self.scales[2])}
            if unit not in rows or context!='text':return False
            dim,expected=rows[unit]
            if variant=='wrong_scale_record' and unit=='lengthunit':expected+=1
            return read(scale)==expected and all(dimension(a)==self.dimensions[dim](a) for a in DOMAIN)
        entries[SYMBOLS['units']]=units;callbacks(doc,self.model,entries)
        def bridge(matter,frame,context,domain,curve,lengthunit,timeunit):
            if variant=='unknown_bridge':raise ValueError('Whole-history unit bridge interpretation missing')
            return variant!='missing_bridge' and (matter,frame,context,lengthunit,timeunit)==('matter','frame','text','lengthunit','timeunit') and unwrap(curve).implementation in self.curves
        self.model['sepw']=bridge
        self.model[WORLD['tg']]=lambda *a:a==('matter','event','text')
        def coordinates(event,frame,context,lengthunit,timeunit,time,x,y,z):
            return variant!='missing_unit_coordinates' and (event,frame,context,lengthunit,timeunit)==('event','frame','text','lengthunit','timeunit') and tuple(map(read,(time,x,y,z)))==(0,1,2,3)
        self.model[WORLD['tf']]=coordinates
        self.model[WORLD['tl']]=lambda unit,dimension,scale:unit=='lengthunit' and scale==2 and all(dimension(a)==self.dimensions['lengthdim'](a) for a in DOMAIN)

    def evaluate(self):
        return [r['value'] for r in evaluate_document(self.doc,individuals=DOMAIN,situations=('text','other'),
            primitives={d['name']:self.model[d['name']] for d in self.doc['declarations'] if d['kind']=='primitive'},max_steps=5_000_000)]


def fixture(path,source=False,abstracted=ABSTRACT|{'sepw'}):
    declarations=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in ALL)
    body=k('sepx',*(k(SYMBOLS[n]) for n,_ in ALL))
    if source:body='t['+k('sepy',*(k(SYMBOLS[n]) for n,_ in INPUTS))+']['+k(SYMBOLS['context'])+']'
    return abstract(candidate(text(path),declarations+'q['+body+'].'),abstracted)


def physical_checks():
    rows={}
    variants=('baseline','unconverted_reading','linear_time_scale','zero_time_scale','velocity_dimension','same_dimension_axes',
        'wrong_lengthunit','wrong_timeunit','wrong_scale_record','missing_bridge','wrong_coefficient','wrong_forceunit',
        'wrong_accelerationunit','wrong_frame','wrong_event','force_record_mismatch','fake_velocity_field')
    for path,source in ((CORE,False),(CORE,True),(SOURCE,True)):
        doc=fixture(path,source);results={}
        for variant in variants:
            actual=UnitModel(doc,variant).evaluate()
            assert actual==[variant=='baseline'],(path,source,variant,actual)
            results[variant]=actual[0]
        if rows:assert results==next(iter(rows.values()))
        rows[path+':'+str(source)]=results
    return {'cases':rows,'whole_history_bridge_is_explicit_premise':True,
        'registered_rational_scales_and_readings_only':True,'real_chain_rule_proved':False}


def bridge_probes():
    doc=fixture(CORE,abstracted=ABSTRACT);ds={d['name']:d for d in doc['declarations']}
    quantifier=ds['sepw']['body'];body=quantifier['body']
    helper=dict(kind='definition',name='jquprobe',parameters=deepcopy(ds['sepw']['parameters'])+[
        dict(name=quantifier['variable'],sort=quantifier['sort'])],result='truth',body=deepcopy(body))
    doc['declarations'].append(helper);doc['statements']=[]
    args=[k(SYMBOLS[n]) for n,_ in TRACK]+[k(SYMBOLS[n]) for n in ('lengthunit','timeunit')]+[k('bb',number(0))]
    doc=parse(format_graph(doc,'compact')+'q['+k('jquprobe',*args)+'].');rows={}
    for variant in ('baseline','missing_unit_coordinates','wrong_lengthunit','wrong_timeunit'):
        actual=UnitModel(doc,variant).evaluate();assert actual==[variant=='baseline'],(variant,actual)
        rows[variant]=actual[0]
    return {'actual_bridge_body_at_one_time':rows,'whole_history_not_certified':True}


def adapter_checks():
    doc=fixture(CORE);ds={d['name']:d for d in doc['declarations']};quantifier=ds['sepv']['body']
    helper=dict(kind='definition',name='jquadapter',parameters=deepcopy(ds['sepv']['parameters'])+[
        dict(name=quantifier['variable'],sort=quantifier['sort'])],result='truth',body=deepcopy(quantifier['body']))
    doc['declarations'].append(helper);doc['statements']=[];base=format_graph(doc,'compact');rows={}
    for rational,scale,expected in ((2,2,True),(3,3,False),(2,3,False),(-2,-2,False)):
        query=k('jquadapter',k(SYMBOLS['lengthunit']),k(SYMBOLS['lengthdim']),k('bb',number(scale)),k(SYMBOLS['context']),number(rational))
        actual=UnitModel(parse(base+'q['+query+'].')).evaluate();assert actual==[expected]
        rows[str((rational,scale))]=actual[0]
    return rows


def refusal_checks():
    rows={}
    doc=fixture(CORE,abstracted=ABSTRACT)
    try:UnitModel(doc).evaluate()
    except ValueError as exc:
        assert 'Cannot finitely quantify the rational number domain' in str(exc);rows['whole_history']=str(exc)
    else:raise AssertionError('Whole-history bridge inferred by sampling')
    doc=fixture(CORE)
    for variant in ('unknown_units','unknown_bridge'):
        try:UnitModel(doc,variant).evaluate()
        except ValueError as exc:
            assert 'missing' in str(exc);rows[variant]=str(exc)
        else:raise AssertionError('Missing calibration or bridge invented')
    doc['statements']=[]
    query=k('sepv',k(SYMBOLS['lengthunit']),k(SYMBOLS['lengthdim']),k('bb',number(2)),k(SYMBOLS['context']))
    doc=parse(format_graph(doc,'compact')+'q['+query+'].')
    try:UnitModel(doc).evaluate()
    except ValueError as exc:
        assert 'Cannot finitely quantify the rational number domain' in str(exc);rows['adapter_rational_witness_search']=str(exc)
    else:raise AssertionError('All-rational witness search silently bounded')
    return rows


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));current=parse(text(SOURCE))
    assert current['statements']==old['statements'] and len(current['statements'])==176
    assert current['declarations'][:len(old['declarations'])]==old['declarations']
    assert all(d['kind']=='definition' for d in current['declarations'][len(old['declarations']):])
    for p in (SOURCE,LIBRARY,CORE):
        doc=parse(text(p))
        for notation in ('full','compact'):
            rendered=format_graph(doc,notation);assert parse(rendered)==parse(transcribe(rendered,alphabet='v2'))==doc
        meanings=next(json.loads(body) for q,body in files.items() if q.endswith('.json') and json.loads(body)['document']==p)
        audits[p]={k:v for k,v in audit_basis(doc,meanings).items() if k!='definition_dependencies'}
        completed=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(completed.stdout)==doc
    previous=json.loads(text('reports/material-acceleration-v1.json'))
    segment=deepcopy(previous['alignment']['segments'][0]);segment['definitions']=['seps','sept','sepu','sepw','sepx','sepy']
    paths=set(files)|{PARENT,'data/einstein-material-acceleration-basis-v1.json','reports/material-acceleration-v1.json',
        'scripts/compose_acceleration_units.py','scripts/check_acceleration_units.py','tests/test_acceleration_units.py','docs/acceleration-units-v1.md',
        'scripts/compose_material_acceleration.py','scripts/check_material_acceleration.py','scripts/compose_origin_clock.py',
        'scripts/compose_limits.py','scripts/compose_situated_criticism.py','scripts/check_coordinate_correspondence.py',
        'scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_phi_normalization.py','scripts/check_quantities.py','scripts/check_real_products.py',
        'scripts/check_angle_composition.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py','reports/written-units-v1.json'}
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','polynomial_proofs','rational_proofs','extraction','meaning_basis','script'))
    return dict(status='partial_acceleration_unit_and_record_binding',document=SOURCE,basis_audits=audits,
        numerical_checks=numerical_checks(),polynomial_checks=polynomial_checks(),physical_checks=physical_checks(),
        bridge_probes=bridge_probes(),rational_adapter_witnesses=adapter_checks(),refusals=refusal_checks(),
        statements_preserved=176,new_primitives=0,roundtrips=True,cli_parse=True,
        alignment={'segments':[segment]},adds_new_text_coverage=False,unit_calibration_constructed=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args()
    report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Acceleration scale, dimensions and unit-record bindings checked; full semantic review remains open',flush=True)


if __name__=='__main__':main()
