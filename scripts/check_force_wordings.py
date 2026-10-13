"""Check cross-product orientation, second-order remainder and comoving evaluation."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from noema.finite_semantics import Content, FunctionValue
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, guarded
from scripts.check_total_differential import setup, OPERATIONS
from scripts.check_field_transform import affine_callback, field_values
from scripts.check_parallel_composition import transform
from scripts.check_real_products import assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_force_wordings import ROOT, PARENT, CUT, POINT, ROLES, composed, generic_composed

REPORT=ROOT/'reports/force-wordings-v1.json'
DOMAIN=('x','y','z','t','rest','moving','body','event','charge','unit','record','vector-force','dyn','new-force','other')
AXES=DOMAIN[:4]


def cross(a,b):return tuple(a[j]*b[l]-a[l]*b[j] for j,l in ((1,2),(2,0),(0,1)))


def vector_checks():
    decl='r ja[] '+POINT+'.r jb[] '+POINT+'.r jc[] '+POINT+'.r jd[] '+POINT+'.r je[] '+CUT+'.'
    query='q[k sch2[k ja[] k jb[]]].q[k sck2[k je[] k ja[] k jc[] k jb[]]].'
    for role in ROLES[:3]:query+='q[k sca['+app(k('scj2',k('je'),k('ja'),k('jc'),k('jb')),k(role))+' '+app(k('jd'),k(role))+']].'
    doc=abstract(parse(generic_composed()[0]+decl+query),OPERATIONS);rows={}
    cases=[('xyz',(1,0,0),(0,1,0),(2,3,4),1),('reversed',(0,1,0),(1,0,0),(2,3,4),1),
        ('general',(1,2,3),(3,-2,1),(1,0,-1),5),('parallel',(1,2,3),(2,4,6),(2,3,4),2),
        ('zero',(0,0,0),(3,-2,1),(2,3,4),3),('negative_velocity',(-1,0,0),(0,0,2),(1,2,3),2)]
    for label,u,h,e,V in cases:
        for wrong in (False,True):
            fixture,model=setup(doc);extra=cross(u,h);expected=tuple(F(x)+F(y,V) for x,y in zip(e,extra))
            output=list(expected)
            if wrong:output[1]+=1
            callbacks(doc,model,{name:lambda axis,vec=vec:fixture.make(vec[AXES.index(axis)] if axis in AXES[:3] else 0) for name,vec in (('ja',u),('jb',h),('jc',e),('jd',output))})
            model['je']=lambda:fixture.make(V);actual=values(doc,model,DOMAIN)
            if actual!=[True,True,True,not wrong,True]:raise ValueError('Cross product or additive term differs')
            rows[label+(':wrong_y' if wrong else '')]=actual
    return {'cases':rows,'zero_and_parallel_vectors_allowed':True,'right_handed_ordered_components':True}


def response_checks():
    decl='r ja[] '+POINT+'.r jb[] '+POINT+'.r jc[] '+CUT+'.r jd[] '+POINT+'.'
    queries=''.join('q[k sca['+app(k('scl2',k('jc'),k('ja'),k('jb')),k(role))+' '+app(k('jd'),k(role))+']].' for role in ROLES[:3])
    doc=abstract(parse(generic_composed()[0]+decl+queries),OPERATIONS);rows={}
    e=(2,3,-1);h=(1,-2,4)
    for r,beta in ((F(0),F(1)),(F(5,13),F(13,12)),(F(-5,13),F(13,12)),(F(3,5),F(5,4)),(F(-3,5),F(5,4))):
        linear=(F(e[0]),e[1]-r*h[2],e[2]+r*h[1]);exact=(linear[0],beta*linear[1],beta*linear[2])
        for approximation in (False,True):
            fixture,model=setup(doc);out=linear if approximation else exact
            callbacks(doc,model,{name:lambda axis,vec=vec:fixture.make(vec[AXES.index(axis)] if axis in AXES[:3] else 0) for name,vec in (('ja',e),('jb',h),('jd',out))})
            model['jc']=lambda:fixture.make(r);actual=values(doc,model,DOMAIN)
            expected=[True,not approximation or r==0,not approximation or r==0]
            if actual!=expected:raise ValueError('Exact response was replaced by first order')
            rows[str(r)+(':linear' if approximation else ':exact')]=actual
    return {'cases':rows,'nonzero_speed_first_order_is_not_exact':True,'rational_cut_fixtures_only':True}


def domain_checks():
    doc=abstract(parse(generic_composed()[0]+'r ja[] '+POINT+'.r jb[] '+CUT+'.q[k sck2[k jb[] k ja[] k ja[] k ja[]]].'),OPERATIONS);rows={}
    for light in (-1,0,1):
        for alias in (False,True):
            fixture,model=setup(doc);callbacks(doc,model,{'ja':lambda a:fixture.make(0)})
            model['jb']=lambda:fixture.make(light)
            if alias:model['yo']=lambda:'x'
            actual=values(doc,model,DOMAIN)
            if actual!=[light>0 and not alias]:raise ValueError('Light/axis guard differs')
            rows[f'{light}:alias={alias}']=actual
    return {'cases':rows,'invalid_divisions_are_not_evaluated':True}


def premise_checks():
    doc=abstract(candidate(composed()[0],'q[t[k scn2[]][k ri[]]].'),OPERATIONS);rows={}
    base=['record','body','charge','rest','event','unit',F(1),'text']
    labels=('baseline','not_pointlike','not_moving','wrong_profile',*(f'wrong_{n}' for n in ('record','body','kind','frame','event','unit','value','context')))
    for label in labels:
        fixture,model=setup(doc);expected=list(base)
        for index,name in enumerate(('record','body','kind','frame','event','unit','value','context')):
            if label=='wrong_'+name:expected[index]=F(2) if name=='value' else 'other'
        for name,value in {'zpp':'record','zol':'body','zor':'charge','ra':'rest','zpo':'event','zou':'unit','ri':'text'}.items():model[name]=lambda value=value:value
        model.update(zok=lambda body,ctx:(body,ctx)==('body','text') and label!='not_pointlike',
            xm=lambda body,frame,ctx:(body,frame,ctx)==('body','rest','text') and label!='not_moving',
            zof=lambda *a:a==('unit','charge',F(1),'text') and label!='wrong_profile',
            zog=lambda record,body,kind,frame,event,unit,value,ctx:[record,body,kind,frame,event,unit,fixture.read(value),ctx]==expected)
        actual=values(doc,model,DOMAIN)
        if actual!=[label=='baseline']:raise ValueError('Moving unit-point premise differs')
        rows[label]=actual
    return {'cases':rows,'motion_uses_the_existing_xm_contract':True}


def remainder_checks():
    text='n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'
    mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b);sub=lambda a,b:add(a,k('ac',b));sq=lambda a:mul(a,a)
    eq=lambda a,b:op('e',a,b);le=lambda a,b:op('u',k('aa',b,a));zero=literal(0);one=literal(1);two=literal(2)
    b,r,e,h,A,B=('v '+n for n in ('beta','ratio','electric','magnetic','bounde','boundh'))
    normalized=eq(mul(sq(b),sub(one,sq(r))),one)
    linear=sub(e,mul(r,h));error=sub(mul(b,linear),linear)
    base=both(normalized,le(one,b),le(sq(r),literal(F(1,4))))
    bounds=both(le(zero,A),le(zero,B),le(k('ac',A),e),le(e,A),le(k('ac',B),h),le(h,B))
    upper=mul(mul(two,add(A,B)),sq(r))
    claims={
        'remainder_factors':assertion('beta ratio electric magnetic',eq(error,mul(sub(b,one),linear))),
        'beta_excess_identity':assertion('beta ratio',op('y',normalized,eq(mul(sub(b,one),add(b,one)),mul(sq(b),sq(r))))),
        'bounded_ratio_bounds_beta':assertion('beta ratio',op('y',base,le(b,two))),
        'beta_excess_is_second_order':assertion('beta ratio',op('y',base,both(le(zero,sub(b,one)),le(sub(b,one),mul(two,sq(r)))))),
        'fixed_field_remainder_bound':assertion('beta ratio electric magnetic bounde boundh',op('y',both(base,bounds),both(le(k('ac',upper),error),le(error,upper)))),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(text+claim),{'aa':'less','ab':'add','ac':'negate','ad':'multiply'},timeout_ms=20000)[0]
        if result['status']!='valid':raise ValueError('Rational remainder lemma differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'fixed_field_bounds_not_uniform_over_all_fields':True,'full_real_cut_asymptotic_proof':False}


def finite_refusal():
    doc=abstract(parse(generic_composed()[0]+'r ja[] '+POINT+'.r jb[] '+POINT+'.q[k scm2[k ja[] k jb[]]].'),OPERATIONS)
    fixture,model=setup(doc);callbacks(doc,model,{n:lambda axis:fixture.make(1) for n in ('ja','jb')})
    try:values(doc,model,DOMAIN)
    except ValueError as exc:
        if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
        return {'refused':True,'reason':str(exc)}
    raise ValueError('Finite examples certified an asymptotic statement')


def source_checks():
    doc=abstract(candidate(composed()[0],'q[t[k sco2[]][k ri[]]].q[t[k scp2[]][k ri[]]].'),OPERATIONS|{'scn2','scm2'})
    e=((1,0,0,0,1),(0,1,0,0,1),(0,0,1,0,2));h=((0,0,0,0,2),(0,0,0,0,1),(0,0,0,0,3))
    oldpoint=(F(1),F(2),F(-1),F(1));newpoint=tuple(transform(oldpoint,F(3),F(5)));expected=field_values(e,h,newpoint,F(3))[0];rows={}
    labels=('baseline','wrong_old_body','wrong_event','wrong_context','outside_old','wrong_old_field','bad_asymptotic',
        'wrong_new_point','outside_new','wrong_new_body','wrong_unit','wrong_record','wrong_force_x','wrong_force_y','wrong_force_z',
        'untransformed_force','not_moving_wrong_force','not_comoving_wrong_force')
    for label in labels:
        fixture,model=setup(doc);cut,read=fixture.make,fixture.read
        point=tuple(x+(1 if i==0 and label=='wrong_new_point' else 0) for i,x in enumerate(newpoint))
        force=list(expected)
        if 'wrong_force' in label:
            axis=label[-1] if label[-1] in AXES[:3] else 'y';force[AXES.index(axis)]+=1
        if label=='untransformed_force':force=[2,3,1]
        callbacks(doc,model,{'znl':affine_callback(doc,fixture,'znl',e),'znm':affine_callback(doc,fixture,'znm',h),
            'zpj':lambda a:cut(oldpoint[AXES.index(a)] if a in AXES else 0),'zpk':lambda a:cut(point[AXES.index(a)] if a in AXES else 0),
            'zpm':lambda a:cut(force[AXES.index(a)] if a in AXES[:3] else 0),
            'znk':lambda *xs:label!='outside_old','znt':lambda *xs:label!='outside_new'})
        for name,index in (('znr',0),('zns',1)):
            sort=next(d['result']['result'] for d in doc['declarations'] if d['name']==name)
            def component(axis,index=index,sort=sort):
                return FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs:cut(field_values(e,h,tuple(read(x) for x in xs),F(3))[index][AXES.index(axis)] if axis in AXES[:3] else 0))
            callbacks(doc,model,{name:component})
        for name,value in {'ra':'rest','zbm':'moving','zol':'body','zpo':'event','zpn':'vector-force','zot':'dyn','zpf':'new-force'}.items():model[name]=lambda value=value:value
        def located(body,frame,event,p,ctx):
            wanted='other' if (frame=='rest' and label=='wrong_old_body') or (frame=='moving' and label=='wrong_new_body') else 'body'
            return body==wanted and event==('other' if label=='wrong_event' else 'event') and ctx==('other' if label=='wrong_context' else 'text') and frame in ('rest','moving') and tuple(read(p(a)) for a in AXES)==(oldpoint if frame=='rest' else newpoint)
        def assigned(frame,E,H,region,ctx):return frame in ('rest','moving') and ctx=='text' and not(frame=='rest' and label=='wrong_old_field')
        model.update(ri=lambda:'text',tc=lambda:cut(5),zb7=lambda:cut(3),va=lambda f:f in ('rest','moving'),zpb=located,znn=assigned,
            scn2=lambda:Content(('motion','text','other'),(False,label!='not_moving_wrong_force',False)),
            scm2=lambda E,H:label!='bad_asymptotic' and tuple(read(E(a)) for a in AXES[:3])==(2,3,1) and tuple(read(H(a)) for a in AXES[:3])==(2,1,3),
            zpa=lambda body,frame,event,ctx:(body,frame,event,ctx)==('body','moving','event','text') and label!='not_comoving_wrong_force',
            zof=lambda *a:a==('dyn','vector-force',F(1),'text'),
            zpc=lambda record,body,kind,frame,event,unit,vec,ctx:(record,body,kind,frame,event,unit,ctx)==('other' if label=='wrong_record' else 'new-force','body','vector-force','moving','event','other' if label=='wrong_unit' else 'dyn','text'))
        actual=values(doc,model,DOMAIN)
        common=label in ('wrong_old_body','wrong_event','wrong_context','outside_old','wrong_old_field')
        old=not common and label!='bad_asymptotic'
        new=not common and label not in ('wrong_new_point','outside_new','wrong_new_body','wrong_unit','wrong_record','wrong_force_x','wrong_force_y','wrong_force_z','untransformed_force')
        if label in ('not_moving_wrong_force','not_comoving_wrong_force'):new=True
        if actual!=[old,new]:raise ValueError('Force wording source differs: '+label+repr(actual)+repr([old,new]))
        rows[label]=actual
    return {'cases':rows,'asymptotic_condition_is_an_explicit_oracle_for_source_wiring':True,
        'actual_normalized_transform_and_inverse_coordinates_evaluated':True,'whole_physical_model_not_verified':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for wrong in ('none','author','old','new','scope','context'):
        model=guarded(doc)
        for name,value in {'zpq':'old','zpr':'new','rd':'author','zno':'scope','ri':'text'}.items():model[name]=lambda value=value:value
        def claim(node,author,content,scope,ctx):
            return node in ('old','new') and [author,json.loads(content.syntax)['symbol'],scope,ctx]==['other' if wrong=='author' else 'author','other' if node==wrong else 'sco2' if node=='old' else 'scp2','other' if wrong=='scope' else 'scope','other' if wrong=='context' else 'text']
        model['uh']=claim;actual=values(doc,model,('old','new','author','scope','other'))
        if actual!=[wrong not in ('author','old','scope','context'),wrong not in ('author','new','scope','context')]:raise ValueError('Wording attribution differs')
        rows[wrong]=actual
    return {'cases':rows,'quoted_contents_not_executed':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'));inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Source inventory changed')
    rows=[]
    for uid,names in (('u0174',['scg2','sci2','scj2','scm2','scn2','sco2']),('u0175',['scn2','scp2'])):
        unit=next(u for u in source['units'] if u['id']=='einstein-1905:'+uid)
        if hashlib.sha256(unit['text'].encode()).hexdigest()!=unit['text_sha256']:raise ValueError('Wording text changed')
        start=unit['text'].index('Ist ein');end=unit['text'].index(' (')
        base=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=names,status='partial_explicit_reading',full_semantic_equivalence=False)
        rows.append(dict(base,start=start,end=end,source=unit['text'][start:end]))
        if uid=='u0174':
            m=next(m for m in source['math'] if m['id']=='M0318')
            if hashlib.sha256(m['mathml'].encode()).hexdigest()!=m['sha256']:raise ValueError('Speed-ratio source changed')
            rows.append(dict(base,math_id=m['id'],math_sha256=m['sha256']))
    return {'segments':rows,'old_wording_is_standard_axis_fixed_field_partial_reading':True,'old_new_register_labels_and_intro_unwritten':True,'verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'force-wordings'),(composed,'einstein-force-wordings')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored wording differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Wording roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['statements'][:-2]!=parent['statements'] or doc['declarations'][:len(parent['declarations'])]!=parent['declarations']:raise ValueError('Wording parent changed')
    paths=list(documents)+['data/force-wordings-basis-v1.json','data/einstein-force-wordings-basis-v1.json',PARENT,
        'scripts/compose_force_wordings.py','scripts/check_force_wordings.py','scripts/check_field_transform.py','scripts/check_total_differential.py',
        'noema/discourse.py','noema/finite_semantics.py','artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'partial_cross_product_approximation_and_comoving_force','documents':documents,'vectors':vector_checks(),
        'response':response_checks(),'domain':domain_checks(),'premise':premise_checks(),
        'remainder':remainder_checks(),'finite_refusal':finite_refusal(),'source':source_checks(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,'parent_preserved':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Wording report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Cross product, bounded rational remainder and comoving-force wording checked')


if __name__=='__main__':main()
