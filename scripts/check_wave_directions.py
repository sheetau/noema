"""Check Doppler/aberration algebra separately from physical interpretation."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.finite_semantics import FunctionValue
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_real_products import MEANINGS, assertion
from scripts.check_moving_light_trip import literal
from scripts.check_tau_differential import ConstructedCuts, ARITHMETIC
from scripts.check_angle_composition import model_arithmetic
from scripts.compose_limits import call as k, op, both, v
from scripts.compose_wave_directions import ROOT, PARENT, CUT, generic_composed, source_composed, core_composed

REPORT=ROOT/'reports/wave-directions-v1.json'


def polynomial_checks():
    r,b,w,a,y,z,wp,ap,bp,cp=map(v,('ratio','beta','rate','ax','ay','az','shifted','dx','dy','dz'))
    mul=lambda x,y:k('ad',x,y)
    add=lambda x,y:k('ab',x,y)
    sub=lambda x,y:add(x,k('ac',y))
    sq=lambda x:mul(x,x)
    zero,one=literal(0),literal(1)
    den=sub(one,mul(a,r))
    names='ratio beta rate ax ay az shifted dx dy dz'
    relation=k('sdi2',r,b,w,a,y,z,wp,ap,bp,cp)
    claims={
        'positive_denominator':assertion('ratio beta ax ay az',op('y',k('sdh2',r,b,a,y,z),k('aa',zero,den))),
        'positive_transformed_frequency':assertion(names,op('y',relation,k('aa',zero,wp))),
        'unit_direction_preserved':assertion(names,op('y',relation,op('e',add(sq(ap),add(sq(bp),sq(cp))),one))),
        'inverse_boost_recovers_input':assertion(names,op('y',relation,k('sdi2',k('ac',r),b,wp,ap,bp,cp,w,a,y,z))),
        'parallel_positive_root':assertion(names,op('y',both(relation,op('e',a,one)),k('sdk2',r,w,wp))),
        'transverse_longitudinal_component':assertion(names,op('y',both(relation,op('e',a,zero)),op('e',ap,k('ac',r)))),
        'positive_frequency_scale_commutes':assertion(names+' scale',op('y',both(relation,k('aa',zero,v('scale'))),
            k('sdi2',r,b,mul(v('scale'),w),a,y,z,mul(v('scale'),wp),ap,bp,cp))),
        'wrong_aberration_sign':assertion('',k('sdi2',*(literal(x) for x in (F(3,5),F(5,4),2,0,1,0,F(5,2),F(3,5),F(4,5),0)))),
    }
    # Coordinates use the same positive V and signed v/V. The coefficient
    # relation is sufficient for phase preservation; no sine or field law is
    # silently assumed by this algebraic check.
    V,t,x,py,pz,phase=map(v,('light','time','x','y','z','phase'))
    tau=mul(b,sub(mul(V,t),mul(r,x)))
    xi=mul(b,sub(x,mul(mul(r,V),t)))
    before=k('sdj2',V,w,a,y,z,t,x,py,pz,phase)
    # Clear V*tau' instead of introducing rational division in the verifier.
    after=op('e',mul(V,phase),mul(wp,sub(tau,add(mul(ap,xi),add(mul(bp,py),mul(cp,pz))))))
    claims['phase_preserved_by_same_boost']=assertion(names+' light time x y z phase',op('y',both(relation,before),after))
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=20000)[0]
        if result['status']!=('invalid' if name=='wrong_aberration_sign' else 'valid'):
            raise ValueError('Wave algebra differs: '+name+' '+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'all_real_cut_field_laws_proved':False}


def transformed(V,s,w,a,b,c):
    from math import isqrt
    square=V*V-s*s
    numerator,denominator=isqrt(square.numerator),isqrt(square.denominator)
    if F(numerator*numerator,denominator*denominator)!=square:raise ValueError('Irrational beta in rational fixture')
    beta=V/F(numerator,denominator)
    den=1-a*s/V
    return (w*beta*den,(a-s/V)/den,b/(beta*den),c/(beta*den))


def expression_checks():
    def evaluate(doc,model):
        names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
        return values(doc,{name:value for name,value in model.items() if name in names},('object',))
    fields='abcdefghij'
    extra=''.join('r j'+n+'[] '+CUT+'.' for n in fields)
    query='q[k sdq2['+' '.join(k('j'+n) for n in fields)+']].'
    docs=[abstract(candidate(builder()[0],extra+query),ARITHMETIC|{'sky'}) for builder in (source_composed,core_composed)]
    cases={}
    directions=((1,0,0),(-1,0,0),(0,1,0),(0,0,-1),(F(3,5),F(4,5),0),(F(-3,5),0,F(4,5)),(F(1,3),F(2,3),F(2,3)))
    for speed,direction in product((F(-3),F(0),F(3)),directions):
        inp=(F(5),speed,F(2),*map(F,direction))
        cases['valid_'+str(len(cases))]=(inp+transformed(*inp),True)
    baseline=tuple(map(F,(5,3,2,0,1,0)))
    out=transformed(*baseline)
    for label,index,value in (('wrong_frequency',0,F(2)),('wrong_ax_sign',1,-out[1]),
                              ('missing_beta_y',2,F(1)),('wrong_z',3,F(1))):
        wrong=list(out);wrong[index]=value
        cases[label]=(baseline+tuple(wrong),False)
    cases.update({
        'zero_light':((0,0,2,0,1,0,2,0,1,0),False),
        'negative_light':((-5,3,2,0,1,0,2,0,1,0),False),
        'light_speed_boundary':((5,5,2,0,1,0,2,0,1,0),False),
        'superluminal_speed':((5,6,2,0,1,0,2,0,1,0),False),
        'negative_frequency':((5,3,-2,0,1,0,-F(5,2),-F(3,5),F(4,5),0),False),
        'zero_frequency':((5,3,0,0,1,0,0,-F(3,5),F(4,5),0),False),
        'nonunit_direction':((5,3,2,0,0,0,F(5,2),-F(3,5),0,0),False),
        'singular_nonunit_direction':((5,3,2,F(5,3),0,0,0,0,0,0),False),
    })
    rows={}
    for name,(args,expected) in cases.items():
        for doc in docs:
            for undefined in (0,17):
                fixture=ConstructedCuts();model=guarded(doc);model_arithmetic(fixture,model,undefined)
                # Positive-only reciprocal is also totalized outside its
                # domain, so acceptance cannot rely on its arbitrary fallback.
                model['sjd']=lambda x:fixture.make(1/fixture.read(x) if fixture.read(x)>0 else undefined)
                for symbol,value in zip(('j'+n for n in fields),args):model[symbol]=lambda value=value:fixture.make(value)
                actual=evaluate(doc,model)
                if actual!=[expected]:raise ValueError('Cut transformation differs: '+name+repr(actual))
        rows[name]=[expected]
    # Phase and the longitudinal root are checked as actual composed cut
    # expressions on exact rational cases, including both velocity signs.
    sample_doc=abstract(candidate(core_composed()[0],extra+
        'q[k sca[k sdr2[k ja[] k jb[] k jc[]] k jd[]]].'
        'q[k sca[k sds2[k ja[] k jc[] k je[] k jf[] k jg[] k jh[] k ji[] k jj[] k jb[]] k jd[]]].'),ARITHMETIC|{'sky'})
    # Separate queries allow unrelated expected values and coordinates.
    specials={}
    for speed in (-3,0,3):
        root=F(2)*F(5-speed,4 if speed else 5)
        # sqrt((1-r)/(1+r)) = (5-s)/sqrt(25-s²).
        root_doc={**sample_doc,'statements':sample_doc['statements'][:1]}
        fixture=ConstructedCuts();model=guarded(root_doc);model_arithmetic(fixture,model)
        for key,val in {'ja':5,'jb':speed,'jc':2,'jd':root}.items():model[key]=lambda val=val:fixture.make(val)
        actual=evaluate(root_doc,model)
        if actual!=[True]:raise ValueError('Longitudinal positive branch differs')
        specials['parallel_'+str(speed)]=actual
    phase_doc={**sample_doc,'statements':sample_doc['statements'][1:]}
    fixture=ConstructedCuts();model=guarded(phase_doc);model_arithmetic(fixture,model)
    vals={'ja':5,'jb':3,'jc':2,'jd':F(46,25),'je':F(3,5),'jf':F(4,5),'jg':0,'jh':2,'ji':5,'jj':3}
    # 2*(2 - ((3/5)*5+(4/5)*3)/5) = 46/25.
    for key,val in vals.items():model[key]=lambda val=val:fixture.make(val)
    actual=evaluate(phase_doc,model)
    if actual!=[True]:raise ValueError('Phase expression differs')
    specials['phase']=actual
    unknown_doc=docs[-1]
    fixture=ConstructedCuts();model=guarded(unknown_doc);model_arithmetic(fixture,model)
    for symbol,value in zip(('j'+n for n in fields),baseline+out):model[symbol]=lambda value=value:fixture.make(value)
    model['ja']=lambda:FunctionValue(('number',),'truth',lambda rational:False)
    try:evaluate(unknown_doc,model)
    except ValueError as exc:
        if 'Cut was not constructed' not in str(exc):raise
    else:raise ValueError('Arbitrary predicate was decoded by finite sampling')
    return {'cases':rows,'specials':specials,'cumulative_and_standalone_agree':True,
        'domain_rejection_independent_of_two_oracle_fallbacks':True,
        'unregistered_predicate_not_decoded_by_sampling':True,
        'constructed_rational_cut_oracles_not_general_real_proof':True}


def finite_refusal():
    args=' '.join(k('bb',literal(n)) for n in (5,3,2,0,1,0))
    doc=candidate(core_composed()[0],'q[k sdl2['+args+']].')
    model={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'ac':lambda a:-a,'ad':lambda a,b:a*b}
    try:values(doc,model,('object',))
    except ValueError as exc:
        if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
        return {'refused':True,'reason':str(exc)}
    raise ValueError('Finite execution certified the cut universe')


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json'
    source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:
        raise ValueError('Source snapshot differs')
    mapping={'M0320':['sds2'],'M0326':['sds2'],'M0327':['sdq2'],
        'M0333':['sdn2'],'M0335':['sdr2'],'M0340':['sdo2'],'M0342':['sdo2']}
    rows=[]
    for math_id,names in mapping.items():
        item=next(m for m in source['math'] if m['id']==math_id)
        unit=next(u for u in source['units'] if math_id in u['math_ids'])
        if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:
            raise ValueError('MathML differs')
        rows.append({'unit':unit['id'],'unit_sha256':unit['text_sha256'],'math_id':math_id,'math_sha256':item['sha256'],
            'definitions':names,'status':'partial','review_ja':'数学的な式の部分対応。M0320は位相部分のみ。光源・観測者・波形・角度の幾何学・定義域の物理的根拠と全文の意味一致は未完。'})
    return {'segments':rows,'new_source_ranges':False,'new_math_associations':True,'semantic_completion':False}


def build_report():
    documents={};sizes={};source_doc=None
    for builder,stem in ((generic_composed,'wave-directions'),(source_composed,'einstein-wave-directions'),(core_composed,'wave-directions-core')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored wave directions differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Wave directions roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
        sizes[stem]={'characters':len(text),'statements':len(doc['statements'])}
        if stem=='einstein-wave-directions':source_doc=doc
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if source_doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or source_doc['statements']!=parent['statements']:
        raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+s+'-basis-v1.json' for s in ('wave-directions','einstein-wave-directions','wave-directions-core')],
        'scripts/compose_wave_directions.py','scripts/check_wave_directions.py','scripts/check_tau_differential.py',
        'scripts/check_angle_composition.py','scripts/check_transverse_time.py','noema/polynomial_proofs.py',
        'noema/extraction.py','noema/finite_semantics.py','noema/discourse.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return json.loads(json.dumps({'status':'partial_wave_phase_frequency_and_direction_equations',
        'documents':documents,'sizes':sizes,'polynomial':polynomial_checks(),'expressions':expression_checks(),
        'finite_refusal':finite_refusal(),
        'alignment':alignment(),'roundtrips':True,'parent_preserved':True,'new_primitives':0,'new_author_statements':0,
        'verified_full_units':{'kant-1784':0,'einstein-1905':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}},ensure_ascii=False))


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Wave directions report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Doppler factor, aberration, phase, inverse and domain conditions checked')


if __name__=='__main__':main()
