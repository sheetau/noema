"""Check the magnetic dual and distinguish value changes from zero/nonzero changes."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, guarded
from scripts.check_total_differential import setup, OPERATIONS
from scripts.check_field_transform import affine_callback
from scripts.check_force_wordings import cross
from scripts.check_real_products import assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import FIELD, ROLES
from scripts.compose_field_dependence import ROOT, PARENT, CUT, POINT, AXES, at, composed, generic_composed

REPORT=ROOT/'reports/field-dependence-v1.json'
DOMAIN=('x','y','z','t','rest','body','event','other')


def dual_checks():
    decl='r ja[] '+POINT+'.r jb[] '+POINT+'.r jc[] '+POINT+'.r jd[] '+CUT+'.r je[] '+POINT+'.'
    query=''.join('q[k sca['+app(k('scr2',k('jd'),k('ja'),k('jb'),k('jc')),k(role))+' '+app(k('je'),k(role))+']].' for role in ROLES[:3])
    doc=abstract(parse(generic_composed()[0]+decl+query),OPERATIONS);rows={}
    for label,u,e,h,V in (('x',(1,0,0),(0,0,2),(1,2,3),2),('general',(1,-2,3),(-2,1,2),(1,0,-1),5),
        ('parallel',(1,2,3),(2,4,6),(2,3,4),2),('zero',(0,0,0),(3,2,1),(1,2,3),3),('reversed',(-1,0,0),(0,0,2),(1,2,3),2)):
        extra=cross(u,e)
        for wrong in (False,True):
            expected=[F(x)+F(y,V)*(1 if wrong else -1) for x,y in zip(h,extra)]
            fixture,model=setup(doc)
            callbacks(doc,model,{name:lambda axis,vec=vec:fixture.make(vec[DOMAIN.index(axis)] if axis in DOMAIN[:3] else 0) for name,vec in (('ja',u),('jb',e),('jc',h),('je',expected))})
            model['jd']=lambda:fixture.make(V);actual=values(doc,model,DOMAIN)
            wanted=[not wrong or component==0 for component in extra]
            if actual!=wanted:raise ValueError('Magnetic additional sign differs')
            rows[label+(':wrong_sign' if wrong else ':correct')]=actual
    return {'cases':rows,'minus_cross_product_is_explicit':True,'zero_or_parallel_cases_do_not_detect_sign_errors_alone':True}


def response_checks():
    decl='r ja[] '+POINT+'.r jb[] '+POINT+'.r jc[] '+CUT+'.r jd[] '+POINT+'.'
    query=''.join('q[k sca['+app(k('scs2',k('jc'),k('ja'),k('jb')),k(role))+' '+app(k('jd'),k(role))+']].' for role in ROLES[:3])
    doc=abstract(parse(generic_composed()[0]+decl+query),OPERATIONS);rows={}
    e=(2,3,-1);h=(1,-2,4)
    for r,beta in ((F(0),F(1)),(F(5,13),F(13,12)),(F(-5,13),F(13,12)),(F(3,5),F(5,4)),(F(-3,5),F(5,4))):
        linear=(F(h[0]),h[1]+r*e[2],h[2]-r*e[1]);exact=(linear[0],beta*linear[1],beta*linear[2])
        for approximate in (False,True):
            fixture,model=setup(doc);out=linear if approximate else exact
            callbacks(doc,model,{name:lambda axis,vec=vec:fixture.make(vec[DOMAIN.index(axis)] if axis in DOMAIN[:3] else 0) for name,vec in (('ja',e),('jb',h),('jd',out))})
            model['jc']=lambda:fixture.make(r);actual=values(doc,model,DOMAIN)
            if actual!=[True,not approximate or r==0,not approximate or r==0]:raise ValueError('Magnetic exact/first-order distinction differs')
            rows[str(r)+(':linear' if approximate else ':exact')]=actual
    return {'cases':rows,'nonzero_speed_approximation_is_not_exact':True}


def presence_checks():
    doc=abstract(parse(generic_composed()[0]+'r ja[] '+POINT+'.r jb[] '+POINT+'.q[k scu2[k ja[]]].q[k scu2[k jb[]]].q[k scv2[k ja[] k jb[]]].'),OPERATIONS);rows={}
    for label,a,b in (('both_zero',(0,0,0),(0,0,0)),('appears',(0,0,0),(0,1,0)),('disappears',(0,-1,0),(0,0,0)),
        ('same_nonzero',(1,0,0),(1,0,0)),('value_changes',(1,0,0),(2,0,0)),('sign_changes',(1,0,0),(-1,0,0)),('direction_changes',(1,0,0),(0,1,0))):
        fixture,model=setup(doc)
        callbacks(doc,model,{name:lambda axis,vec=vec:fixture.make(vec[DOMAIN.index(axis)] if axis in DOMAIN[:3] else 0) for name,vec in (('ja',a),('jb',b))})
        actual=values(doc,model,DOMAIN);wanted=[any(a),any(b),bool(any(a))!=bool(any(b))]
        if actual!=wanted:raise ValueError('Numerical presence differs: '+label)
        rows[label]=actual
    return {'cases':rows,'ordinary_value_change_is_not_presence_change':True,'does_not_define_general_existence':True}


def witness_checks():
    doc=abstract(parse(generic_composed()[0]+'r ja[] '+CUT+'.q[k scw2[k ja[]]].'),OPERATIONS);rows={}
    for r in (F(0),F(3,5),F(-3,5),F(5,13),F(-5,13)):
        fixture,model=setup(doc);model['ja']=lambda:fixture.make(r);actual=values(doc,model,DOMAIN)
        if actual!=[r!=0]:raise ValueError('Two presence witnesses differ')
        rows[str(r)]=actual
    # Nonzero longitudinal fields provide a counterexample to the overclaim
    # that every nonzero boost changes every field's zero/nonzero status.
    text=generic_composed()[0]+'r ja[] '+POINT+'.r jb[] '+CUT+'.q[k scv2[k ja[] k scl2[k jb[] k ja[] k ja[]]]].q[k scv2[k ja[] k scs2[k jb[] k ja[] k ja[]]]].'
    unchanged=abstract(parse(text),OPERATIONS);fixture,model=setup(unchanged)
    callbacks(unchanged,model,{'ja':lambda axis:fixture.make(1 if axis=='x' else 0)});model['jb']=lambda:fixture.make(F(3,5))
    counterexample=values(unchanged,model,DOMAIN)
    if counterexample!=[False,False]:raise ValueError('Invariant longitudinal example changed presence')
    return {'cases':rows,'two_witnesses_have_different_input_configurations':True,'nonzero_longitudinal_counterexample':counterexample}


def field_transform_checks():
    decl='r ja[] '+FIELD+'.r jb[] '+FIELD+'.r jc[] '+POINT+'.r jd[] '+CUT+'.r je[] '+CUT+'.'
    newpoint=k('s46',k('jd'),k('je'),k('jc'));field=k('s6l',k('jd'),k('je'),k('ja'),k('jb'))
    response=k('scs2',k('shv',k('je'),k('sjd',k('jd'))),at(k('ja'),k('jc')),at(k('jb'),k('jc')))
    query='q[k sho['+AXES+' '+at(field,newpoint)+' '+response+' p sca]].'
    doc=abstract(candidate(composed()[0],decl+query),OPERATIONS);rows={}
    e=((1,0,0,1,1),(0,1,0,0,1),(0,0,1,-1,2));h=((0,0,0,1,2),(1,0,0,0,1),(0,1,0,0,3))
    for speed in (F(0),F(3),F(-3)):
        for point in ((0,0,0,0),(1,2,-1,1),(-2,1,3,-1)):
            fixture,model=setup(doc)
            callbacks(doc,model,{'ja':affine_callback(doc,fixture,'ja',e),'jb':affine_callback(doc,fixture,'jb',h),
                'jc':lambda axis:fixture.make(point[DOMAIN.index(axis)] if axis in DOMAIN[:4] else 0)})
            model.update(jd=lambda:fixture.make(5),je=lambda:fixture.make(speed));actual=values(doc,model,DOMAIN)
            if actual!=[True]:raise ValueError('Magnetic response differs from established field transform')
            rows[str(speed)+':'+str(point)]=actual
    return {'cases':rows,'same_event_uses_transformed_coordinates':True,'affine_rational_field_fixtures_only':True}


def polynomial_checks():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc['declarations']=[d for d in doc['declarations'] if d['name'] in ('aa','ab','ac','ad','s6b','s6c')];doc['statements']=[];text=format_graph(doc,'compact')
    b,r,h,e=('v '+n for n in ('beta','ratio','magnetic','electric'));zero=literal(0)
    eq=lambda a,b:op('e',a,b);neg=lambda x:k('ac',x);mul=lambda a,b:k('ad',a,b)
    claims={
        'magnetic_plus_is_electric_minus_with_negated_source':assertion('beta ratio magnetic electric',eq(k('s6c',b,r,h,e),k('s6b',b,r,h,neg(e)))),
        'magnetic_minus_is_electric_plus_with_negated_source':assertion('beta ratio magnetic electric',eq(k('s6b',b,r,h,e),k('s6c',b,r,h,neg(e)))),
        'nonzero_motion_and_positive_beta_give_nonzero_cross_response':assertion('beta ratio',op('y',both(k('aa',zero,b),op('u',eq(r,zero))),op('u',eq(mul(b,r),zero)))),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(text+claim),{'aa':'less','ab':'add','ac':'negate','ad':'multiply'},timeout_ms=20000)[0]
        if result['status']!='valid':raise ValueError('Dual rational lemma differs')
        rows[name]=result
    prior=ROOT/'reports/force-wordings-v1.json';record=json.loads(prior.read_text(encoding='utf-8'))
    if not all(v['status']=='valid' for v in record['remainder']['claims'].values()):raise ValueError('Prior remainder evidence changed')
    return {'claims':rows,'rational_polynomial_only':True,'reused_remainder_report':prior.relative_to(ROOT).as_posix(),
        'reused_remainder_sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),'full_real_cut_proof':False}


def finite_refusal():
    rows={}
    for label,text in (('existential_witness',candidate(composed()[0],'q[t[k scx2[]][k ri[]]].')),
        ('magnetic_asymptotic',parse(generic_composed()[0]+'r ja[] '+POINT+'.q[k sct2[k ja[] k ja[]]].'))):
        doc=abstract(text,OPERATIONS);fixture,model=setup(doc)
        if label=='existential_witness':model['ri']=lambda:'text'
        else:callbacks(doc,model,{'ja':lambda axis:fixture.make(1)})
        try:values(doc,model,DOMAIN)
        except ValueError as exc:
            if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
            rows[label]=str(exc);continue
        raise ValueError('Finite domain silently replaced arbitrary real inputs')
    return rows


def source_checks():
    doc=abstract(candidate(composed()[0],'q[t[k scy2[]][k ri[]]].'),OPERATIONS|{'sct2'});rows={}
    e=((1,0,0,0,1),(0,1,0,0,1),(0,0,1,0,2));h=((0,0,0,0,2),(0,0,0,0,1),(0,0,0,0,3));point=(1,2,-1,1)
    for label in ('baseline','wrong_body','wrong_frame','wrong_event','wrong_context','outside','wrong_point','swapped_fields','bad_asymptotic'):
        fixture,model=setup(doc);cut,read=fixture.make,fixture.read
        callbacks(doc,model,{'znl':affine_callback(doc,fixture,'znl',h if label=='swapped_fields' else e),
            'znm':affine_callback(doc,fixture,'znm',e if label=='swapped_fields' else h),
            'zpj':lambda axis:cut(point[DOMAIN.index(axis)]+(1 if label=='wrong_point' and axis=='x' else 0) if axis in DOMAIN[:4] else 0),
            'znk':lambda *xs:label!='outside'})
        for name,value in {'ra':'rest','zol':'body','zpo':'event','ri':'text'}.items():model[name]=lambda value=value:value
        expected=['body','rest','event','text']
        for name,index in (('body',0),('frame',1),('event',2),('context',3)):
            if label=='wrong_'+name:expected[index]='other'
        model.update(va=lambda f:f=='rest',znn=lambda frame,E,H,region,ctx:(frame,ctx)==('rest','text'),
            zpb=lambda body,frame,event,p,ctx:[body,frame,event,ctx]==expected and tuple(read(p(a)) for a in DOMAIN[:4])==point,
            sct2=lambda E,H:label!='bad_asymptotic' and tuple(read(E(a)) for a in DOMAIN[:3])==(2,3,1) and tuple(read(H(a)) for a in DOMAIN[:3])==(2,1,3))
        actual=values(doc,model,DOMAIN)
        if actual!=[label=='baseline']:raise ValueError('Magnetic source binding differs')
        rows[label]=actual
    return {'cases':rows,'asymptotic_truth_is_an_explicit_source_wiring_oracle':True,'no_magnetic_pole_measurement_asserted':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for wrong in ('none','author','dual','dependence','scope','context'):
        model=guarded(doc)
        for name,value in {'zps':'dual','zpt':'dependence','rd':'author','zno':'scope','ri':'text'}.items():model[name]=lambda value=value:value
        def claim(node,author,content,scope,ctx):
            return node in ('dual','dependence') and [author,json.loads(content.syntax)['symbol'],scope,ctx]==['other' if wrong=='author' else 'author','other' if wrong==node else 'scy2' if node=='dual' else 'scx2','other' if wrong=='scope' else 'scope','other' if wrong=='context' else 'text']
        model['uh']=claim;actual=values(doc,model,('dual','dependence','author','scope','other'))
        if actual!=[wrong not in ('author','dual','scope','context'),wrong not in ('author','dependence','scope','context')]:raise ValueError('Dependence attribution differs')
        rows[wrong]=actual
    return {'cases':rows,'quoted_contents_not_executed':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'));inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Source inventory changed')
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0176')
    if hashlib.sha256(unit['text'].encode()).hexdigest()!=unit['text_sha256']:raise ValueError('Dependence source changed')
    rows=[]
    for start,end,names in ((0,unit['text'].index(' Man sieht'),['scq2','scr2','scs2','sct2','scy2']),
        (unit['text'].index('daß die elektrischen'),len(unit['text']),['scu2','scv2','scw2','scx2'])):
        rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=start,end=end,source=unit['text'][start:end],definitions=names,status='partial_explicit_reading',full_semantic_equivalence=False))
    return {'segments':rows,'numerical_presence_is_only_a_partial_reading_of_existence':True,
        'auxiliary_role_and_explanation_of_introduction_unwritten':True,'verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'field-dependence'),(composed,'einstein-field-dependence')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored dependence differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Dependence roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['statements'][:-2]!=parent['statements'] or doc['declarations'][:len(parent['declarations'])]!=parent['declarations']:raise ValueError('Dependence parent changed')
    paths=list(documents)+['data/field-dependence-basis-v1.json','data/einstein-field-dependence-basis-v1.json',PARENT,
        'scripts/compose_field_dependence.py','scripts/check_field_dependence.py','reports/force-wordings-v1.json',
        'scripts/check_field_transform.py','scripts/check_force_wordings.py','scripts/check_total_differential.py',
        'noema/discourse.py','noema/finite_semantics.py','artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'partial_magnetic_dual_and_frame_dependent_presence','documents':documents,'dual':dual_checks(),'response':response_checks(),
        'presence':presence_checks(),'witnesses':witness_checks(),'field_transform':field_transform_checks(),'polynomial':polynomial_checks(),
        'finite_refusal':finite_refusal(),'source':source_checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,'parent_preserved':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Field dependence report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Magnetic dual, presence witnesses and source scope checked')


if __name__=='__main__':main()
