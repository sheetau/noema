"""Check explicit error bounds independently of contextual sufficiency."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup, OPS
from scripts.check_field_transform import affine_callback, field_values
from scripts.check_parallel_composition import transform
from scripts.check_rod_setup import callbacks
from scripts.check_real_products import MEANINGS, assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, app, op, both, v
from scripts.compose_wave_approximation import ROOT, PARENT, CUT, POINT, FIELD, REGION, ROLES, SUFFICIENT, generic_composed, source_composed, core_composed

REPORT=ROOT/'reports/wave-approximation-v1.json'
ARITHMETIC=OPS|{'shu'}
DOMAIN=('x','y','z','t','wave','frame','electric-kind','magnetic-kind','purpose','other')


def model_setup(doc):
    fixture,model=setup(doc)
    model['shu']=lambda x:fixture.make(abs(fixture.read(x)))
    return fixture,model


def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return values(doc,{n:f for n,f in model.items() if n in names},DOMAIN)


def polynomial_checks():
    beta,r,a,e,h,eb,hb=map(v,('beta','ratio','absolute','electricerror','magneticerror','electricbound','magneticbound'))
    z,o=literal(0),literal(1);sq=lambda x:k('ad',x,x)
    normalized=both(k('aa',z,beta),op('e',k('ad',sq(beta),k('ab',o,k('ac',sq(r)))),o))
    allowed=both(op('u',k('aa',beta,o)),k('sebc',r,a),k('seba',e,eb),k('seba',h,hb))
    bound=k('sebb',beta,a,eb,hb)
    args='beta ratio absolute electricerror magneticerror electricbound magneticbound'
    claims={
        'positive_normalized_beta_is_at_least_one':assertion('beta ratio',op('y',normalized,op('u',k('aa',beta,o)))),
        'minus_mix_error_bound':assertion(args,op('y',allowed,k('seba',k('s6b',beta,r,e,h),bound))),
        'plus_mix_error_bound':assertion(args,op('y',allowed,k('seba',k('s6c',beta,r,e,h),bound))),
        'longitudinal_error_also_fits':assertion(args,op('y',allowed,k('seba',e,bound))),
        'zero_bound_requires_exact_value':assertion('electricerror',op('z',k('seba',e,z),op('e',e,z))),
        'bound_is_monotone':assertion('electricerror electricbound magneticbound',op('y',both(k('seba',e,eb),op('u',k('aa',hb,eb))),k('seba',e,hb))),
        'same_bound_not_preserved_by_mixing':assertion('',k('seba',k('s6c',*(literal(x) for x in (F(5,4),F(3,5),1,1))),literal(1))),
        'missing_other_field_error_is_not_safe':assertion('',k('seba',k('s6c',*(literal(x) for x in (F(5,4),F(3,5),0,1))),literal(0))),
        'negative_bound_is_not_an_error_budget':assertion('',k('seba',literal(0),literal(-1))),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=20000)[0]
        rejected={'same_bound_not_preserved_by_mixing','missing_other_field_error_is_not_safe','negative_bound_is_not_an_error_budget'}
        if result['status']!=('invalid' if name in rejected else 'valid'):raise ValueError('Error bound algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_component_proofs_only':True,'global_real_field_transport_proved':False}


def point_checks(texts):
    fields=('ja','jb','jc','jd');bounds=('je','jf');points=('jg','jh')
    decls=''.join('r '+n+'[] '+FIELD+'.' for n in fields)+''.join('r '+n+'[] '+CUT+'.' for n in (*bounds,'ji','jj'))
    decls+=''.join('r '+n+'[] '+POINT+'.' for n in points)
    V,s=k('ji'),k('jj');eps=list(map(k,bounds))
    transformed=[k(name,V,s,k(e),k(h)) for e,h in (('ja','jb'),('jc','jd')) for name in ('s6k','s6l')]
    neweps=[k(name,V,s,*eps) for name in ('seau','seav')]
    query='q['+k('seas',*map(k,fields),*eps,k('jg'))+'].'
    query+='q['+k('seas',*transformed,*neweps,k('jh'))+'].'
    query+='q['+k('seas',*transformed,*eps,k('jh'))+'].'
    docs=[abstract(candidate(text,decls+query),ARITHMETIC) for text in texts]
    E=((1,2,0,1,0),(0,1,1,0,1),(2,0,1,-1,2))
    H=((0,1,0,1,2),(1,0,2,0,-1),(-1,2,0,1,1))
    rows={}
    for speed,(eb,hb),x in product((-3,0,3),((0,0),(1,0),(0,1),(1,1),(1,2)),(F(-1),F(0),F(1,2),F(1))):
        actualE=[list(row) for row in E];actualH=[list(row) for row in H]
        for row in actualE:row[0]+=eb
        for row in actualH:row[0]-=hb
        point=(x,F(1,3),F(-1,2),F(1,4));newpoint=transform(point,F(speed),F(5))
        ae,ah=field_values(actualE,actualH,newpoint,F(speed));pe,ph=field_values(E,H,newpoint,F(speed))
        same=all(abs(a-b)<=limit for aa,bb,limit in ((ae,pe,eb),(ah,ph,hb)) for a,b in zip(aa,bb))
        expected=[True,True,same]
        for doc in docs:
            fixture,model=model_setup(doc)
            entries={n:affine_callback(doc,fixture,n,matrix) for n,matrix in zip(fields,(actualE,actualH,E,H))}
            for n,p in zip(points,(point,newpoint)):entries[n]=lambda axis,p=p:fixture.make(p[('x','y','z','t').index(axis)] if axis in ('x','y','z','t') else 0)
            callbacks(doc,model,entries)
            for n,val in zip((*bounds,'ji','jj'),(eb,hb,5,speed)):model[n]=lambda val=val:fixture.make(val)
            actual=evaluate(doc,model)
            if actual!=expected:raise ValueError('Pointwise error transport differs: '+str((speed,eb,hb,x,actual)))
        rows[str((speed,eb,hb,x))]=expected
    return {'cases':rows,'cumulative_and_standalone_agree':True,
        'same_untransformed_bound_has_counterexamples':any(not row[2] for row in rows.values()),
        'affine_test_errors_not_general_field_proof':True}


def scalar_checks(text):
    decls=''.join('r j'+n+'[] '+CUT+'.' for n in 'abc')
    doc=abstract(candidate(text,decls+'q[k sear[k ja[] k jb[] k jc[]]].'),ARITHMETIC)
    cases={'exact':(2,2,0,True),'positive_boundary':(3,2,1,True),'negative_boundary':(1,2,1,True),
        'beyond_bound':(F(301,100),2,1,False),'negative_bound':(2,2,-1,False),'zero_bound_nonzero_error':(3,2,0,False)}
    rows={}
    for name,(value,approx,bound,expected) in cases.items():
        fixture,model=model_setup(doc)
        for n,val in zip('abc',(value,approx,bound)):model['j'+n]=lambda val=val:fixture.make(val)
        actual=evaluate(doc,model)
        if actual!=[expected]:raise ValueError('Scalar approximation differs')
        rows[name]=actual
    return rows


def transport_condition_checks(text):
    fields=('ja','jb','jc','jd')
    decls=''.join('r '+n+'[] '+FIELD+'.' for n in fields)
    decls+=''.join('r j'+n+'[] '+CUT+'.' for n in 'efgh')+'r ji[] '+REGION+'.'
    query='q['+k('seaz',*map(k,fields),k('je'),k('jf'),k('ji'),k('jg'),k('jh'))+'].'
    doc=abstract(candidate(text,decls+query),ARITHMETIC|{'seat'})
    E=tuple((0,0,0,0,x) for x in (1,1,1));H=tuple((0,0,0,0,x) for x in (-2,-2,-2));Z=((0,0,0,0,0),)*3
    rows={};samples=((-1,0,0,0),(1,0,0,0),(-1,0,0,1))
    for speed,premise,conclusion in product((-3,3),(False,True),(False,True)):
        fixture,model=model_setup(doc);make,read=fixture.make,fixture.read
        entries={n:affine_callback(doc,fixture,n,matrix) for n,matrix in zip(fields,(E,H,Z,Z))}
        entries['ji']=lambda x,y,z,t:read(x)>0;callbacks(doc,model,entries)
        for name,value in zip('efgh',(1,2,5,speed)):model['j'+name]=lambda value=value:make(value)
        shiftedE,shiftedH=field_values(E,H,(0,0,0,0),F(speed))
        def bounded(e,h,pe,ph,eb,hb,region):
            actual=tuple(read(field(axis)(*(make(0) for _ in range(4)))) for field in (e,h,pe,ph) for axis in ('x','y','z'))
            domain=tuple(region(*(make(x) for x in p)) for p in samples)
            if actual==(1,1,1,-2,-2,-2,0,0,0,0,0,0) and (read(eb),read(hb))==(1,2) and domain==(False,True,False):return premise
            target=tuple(shiftedE+shiftedH+[F(0)]*6)
            expected_domain=tuple(transform(p,F(-speed),F(5))[0]>0 for p in samples)
            return conclusion and actual==target and (read(eb),read(hb))==(F(11,4),F(13,4)) and domain==expected_domain
        model['seat']=bounded
        actual=evaluate(doc,model);expected=[not premise or conclusion]
        if actual!=expected:raise ValueError('Transport conditional differs')
        rows[str((speed,premise,conclusion))]=actual
    fixture,model=model_setup(doc)
    callbacks(doc,model,{**{n:affine_callback(doc,fixture,n,Z) for n in fields},'ji':lambda *xs:True})
    for name,value in zip('efgh',(1,2,5,5)):model['j'+name]=lambda value=value:fixture.make(value)
    model['seat']=lambda *args:True
    if evaluate(doc,model)!=[False]:raise ValueError('Light-speed boundary accepted by conditional')
    return {'cases':rows,'light_speed_boundary_rejected':True,
        'global_bounds_supplied_only_for_conditional_wiring':True,'false_premise_is_not_evidence_of_an_approximation':True}


def source_query(text,global_approximation=True):
    decls=''.join('r j'+n+'[] '+t+'.' for n,t in SUFFICIENT)
    query='q['+k('seax',*(k('j'+n) for n,t in SUFFICIENT))+'].'
    return abstract(candidate(text,decls+query),ARITHMETIC|{'sdv2'}|({'seat'} if global_approximation else set()))


def source_model(doc,label):
    fixture,model=model_setup(doc);make,read=fixture.make,fixture.read
    ids={'wave':'wave','frame':'frame','electrickind':'electric-kind','magnetickind':'magnetic-kind','scope':'purpose'}
    for n,val in ids.items():model['j'+n]=lambda val=val:val
    vals={'light':5,'rate':2,'ax':1,'ay':0,'az':0,'ex':0,'ey':1,'ez':0,'hx':0,'hy':0,'hz':1,
          'electricbound':F(1,10),'magneticbound':F(1,5),'time':F(1,2)}
    if label=='zero_error_exact':vals.update(electricbound=0,magneticbound=0)
    if label=='loose_but_not_sufficient':vals['electricbound']=10
    if label=='too_small_bound':vals['electricbound']=F(1,20)
    if label=='negative_bound':vals['electricbound']=-1
    if label=='zero_bound_nonzero_error':vals['electricbound']=0
    if label=='origin_wrong_time':vals['time']=2
    for n,val in vals.items():model['j'+n]=lambda val=val:make(val)
    model['jcontext']=lambda:'other' if label=='wrong_context' else 'text'
    samples=((0,0,0,F(1,2)),(1,0,0,F(1,2)),(F(-1),1,0,F(1,2)))
    def in_region(*xs):
        x,y,z,t=map(read,xs)
        return label!='empty_region' and (F(1,2) if label=='origin_excluded' else -1)<=x<=1 and 0<=t<=1
    entries={'jsine':lambda x:x,'jcosine':lambda x:make(1),'jregion':in_region}
    for name,axis,delta in (('jelectric','y',F(1,10)),('jmagnetic','z',F(1,5))):
        scalar=next(d['result']['result'] for d in doc['declarations'] if d['name']==name)
        def component(role,axis=axis,delta=delta,scalar=scalar):
            def at(x,y,z,t):
                phase=2*(read(t)-read(x)/5)
                perturbation=0 if label=='zero_error_exact' else delta
                if label=='error_at_second_point' and read(x)==1:perturbation*=2
                return make(phase+perturbation if role==axis else 0)
            return FunctionValue(tuple(scalar['parameters']),scalar['result'],at)
        entries[name]=component
    entries['jassigned']=lambda wave,frame,e,h,region,ek,hk,ctx:(wave,frame,ek,hk,ctx)==('wave','frame','electric-kind','magnetic-kind','text')
    def adequate(wave,frame,scope,eb,hb,ctx):
        return label!='not_sufficient' and (wave,frame,scope,ctx)==('wave','frame','other' if label=='wrong_purpose' else 'purpose','text') and 0<=read(eb)<=F(1,10) and 0<=read(hb)<=F(1,5)
    entries['jadequate']=adequate;callbacks(doc,model,entries)
    model.update(va=lambda x:x=='frame',cf=lambda x:x=='wave',znn=lambda frame,e,h,region,ctx:(frame,ctx)==('frame','text'))
    model['sdv2']=lambda S,C:label!='missing_harmonic_condition'
    def bounded(e,h,pe,ph,eb,hb,region):
        points=[p for p in samples if region(*(make(x) for x in p))]
        return label!='missing_global_bound' and bool(points) and read(eb)>=0 and read(hb)>=0 and all(
            abs(read(actual(role)(*(make(x) for x in p)))-read(approx(role)(*(make(x) for x in p))))<=read(bound)
            for p in points for actual,approx,bound in ((e,pe,eb),(h,ph,hb)) for role in ('x','y','z'))
    model['seat']=bounded
    return model


def sufficiency_checks(texts):
    docs=[source_query(text) for text in texts]
    labels=('baseline','zero_error_exact','loose_but_not_sufficient','too_small_bound','negative_bound','zero_bound_nonzero_error',
        'origin_wrong_time','empty_region','origin_excluded','error_at_second_point','not_sufficient','wrong_purpose','wrong_context',
        'missing_harmonic_condition','missing_global_bound')
    rows={}
    for name in labels:
        expected=[name in ('baseline','zero_error_exact')]
        results=[evaluate(doc,source_model(doc,name)) for doc in docs]
        if results!=[expected,expected]:raise ValueError('Approximation sufficiency differs: '+name+repr(results))
        rows[name]=expected
    raw=source_query(texts[1],False)
    try:evaluate(raw,source_model(raw,'baseline'))
    except ValueError as exc:
        if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
        refusal=str(exc)
    else:raise ValueError('Uniform real bound was certified by finite samples')
    return {'cases':rows,'cumulative_and_standalone_agree':True,'global_bound_refused_without_oracle':refusal,
        'global_bound_and_harmonic_conditions_are_fixture_oracles':True,
        'nonharmonic_profile_only_tests_argument_wiring':True,'source_does_not_specify_a_unique_error_norm':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Snapshot differs')
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0179')
    excerpt='in einem den Koordinatenursprung enthaltenden Raumteil mit genügender Annäherung durch die Gleichungen dargestellt sei'
    start=unit['text'].index(excerpt)
    return {'segments':[{'unit':unit['id'],'unit_sha256':unit['text_sha256'],'start':start,'end':start+len(excerpt),
        'source':excerpt,'definitions':['seaw','seax'],'status':'partial_explicit_reading',
        'review_ja':'原点を含む領域での十分な近似へ、固定した二つの成分誤差上限と用途の十分性関係による一つの実現を対応させる。原文が誤差尺度を一意に指定したとはしない。遠方光源・空間領域の持続・想定の談話は未完。'}],
        'semantic_completion':False,'chosen_operational_realization_not_unique_source_definition':True}


def build_report():
    documents={};sizes={};texts=[]
    for builder,stem in ((generic_composed,'wave-approximation'),(source_composed,'einstein-wave-approximation'),(core_composed,'wave-approximation-core')):
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored wave approximation differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Approximation roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]={'characters':len(text),'statements':len(doc['statements'])}
    source=parse(texts[1]);parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if source['declarations'][:len(parent['declarations'])]!=parent['declarations'] or source['statements']!=parent['statements']:raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+s+'-basis-v1.json' for s in ('wave-approximation','einstein-wave-approximation','wave-approximation-core')],
        'scripts/compose_wave_approximation.py','scripts/check_wave_approximation.py','scripts/compose_wave_readings.py',
        'scripts/check_plane_waveforms.py','scripts/check_field_transform.py','scripts/check_parallel_composition.py',
        'noema/extraction.py','noema/polynomial_proofs.py','noema/finite_semantics.py','noema/discourse.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return json.loads(json.dumps({'status':'partial_uniform_wave_approximation_and_sufficiency','documents':documents,'sizes':sizes,
        'polynomial':polynomial_checks(),'points':point_checks(texts[1:]),'scalars':scalar_checks(texts[2]),
        'sufficiency':sufficiency_checks(texts[1:]),'transport_condition':transport_condition_checks(texts[2]),'alignment':alignment(),
        'parent_preserved':True,'roundtrips':True,'new_primitives':0,'new_author_statements':0,
        'verified_full_units':{'kant-1784':0,'einstein-1905':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}},ensure_ascii=False))


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Wave approximation report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Fixed component bounds, transformed error budgets and contextual sufficiency checked')


if __name__=='__main__':main()
