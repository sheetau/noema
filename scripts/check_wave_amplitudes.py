"""Verify transverse amplitude algebra with a pinned facsimile correction."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json
import xml.etree.ElementTree as ET

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup, evaluate, OPS, expected_values
from scripts.check_real_products import MEANINGS, assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, op, both, v
from scripts.compose_wave_amplitudes import ROOT, PARENT, CUT, VECTOR_ARGS, generic_composed, source_composed, core_composed

REPORT=ROOT/'reports/wave-amplitudes-v1.json'
LEDGER=ROOT/'data/wave-amplitudes-facsimile-v1.json'
NS='{http://www.w3.org/1998/Math/MathML}'


def reviewed_formula(raw,correction):
    if hashlib.sha256(raw.encode('utf-8')).hexdigest()!=correction['snapshot_math_sha256']:raise ValueError('Snapshot math hash differs')
    if correction['operation']!='remove_single_outer_denominator_square_root' or correction['review_status']!='token_checked_against_facsimile':raise ValueError('Unreviewed correction')
    tree=ET.fromstring(raw);fraction=next(tree.iter(NS+'mfrac'))
    roots=list(fraction[1].iter(NS+'msqrt'))
    if len(roots)!=1 or len(roots[0])!=1:raise ValueError('Ambiguous denominator square root')
    target=roots[0]
    if ''.join(target.itertext())!='1−(vV)2':raise ValueError('Square root is not the reviewed expression')
    parent=next(node for node in fraction[1].iter() if target in list(node))
    index=list(parent).index(target);parent.remove(target);parent.insert(index,target[0])
    return ET.tostring(tree,encoding='unicode')


def facsimile_check():
    meta=json.loads(LEDGER.read_text(encoding='utf-8'))
    for path,key in ((meta['path'],'sha256'),(meta['image'],'image_sha256')):
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=meta[key]:raise ValueError('Reviewed facsimile differs')
    source=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    item=next(m for m in source['math'] if m['id']=='M0345')
    corrected=reviewed_formula(item['mathml'],meta['correction'])
    return {'snapshot_mathml':item['mathml'],'reviewed_mathml':corrected,
        'snapshot_math_sha256':item['sha256'],'reviewed_math_sha256':hashlib.sha256(corrected.encode('utf-8')).hexdigest(),
        'printed_page':912,'source_snapshot_modified':False,'whole_page_semantics_verified':False}


def polynomial_checks():
    a,b,c,ex,ey,ez,hx,hy,hz=map(v,VECTOR_ARGS.split())
    beta,r=map(v,('beta','ratio'));zero,one=literal(0),literal(1)
    add=lambda x,y:k('ab',x,y);mul=lambda x,y:k('ad',x,y);sub=lambda x,y:add(x,k('ac',y));sq=lambda x:mul(x,x)
    norm=lambda vec:k('seaa',*vec)
    cross=(k('seac',b,c,ey,ez),k('seac',c,a,ez,ex),k('seac',a,b,ex,ey))
    E=(ex,ey,ez);H=(hx,hy,hz);n=(a,b,c)
    ep=(ex,k('s6b',beta,r,ey,hz),k('s6c',beta,r,ez,hy))
    hp=(hx,k('s6c',beta,r,hy,ez),k('s6b',beta,r,hz,ey))
    ep_cross=(ex,k('s6b',beta,r,ey,cross[2]),k('s6c',beta,r,ez,cross[1]))
    d=sub(one,mul(a,r));dot=k('seab',*n,*E)
    normalization=op('e',mul(sq(beta),sub(one,sq(r))),one)
    transverse=k('sead',*n,*E,*H)
    scaled=mul(mul(sq(beta),sq(d)),norm(E))
    residual=add(mul(sq(ex),sub(one,mul(sq(beta),sub(one,sq(r))))),
        add(mul(mul(mul(sq(beta),sq(r)),sq(ex)),sub(norm(n),one)),
            mul(mul(mul(mul(literal(2),sq(beta)),d),r),mul(ex,dot))))
    claims={
        'cross_product_norm_identity':assertion('ax ay az ex ey ez',op('e',norm(cross),sub(mul(norm(n),norm(E)),sq(dot)))),
        'cross_product_transverse_to_direction':assertion('ax ay az ex ey ez',op('e',k('seab',*n,*cross),zero)),
        'cross_product_transverse_to_electric':assertion('ax ay az ex ey ez',op('e',k('seab',*E,*cross),zero)),
        'electric_norm_residual_identity':assertion('beta ratio ax ay az ex ey ez',op('e',sub(norm(ep_cross),scaled),residual)),
        'electric_magnetic_difference_residual':assertion('beta ratio ex ey ez hx hy hz',op('e',
            sub(sub(norm(ep),norm(hp)),sub(norm(E),norm(H))),
            mul(sub(mul(sq(beta),sub(one,sq(r))),one),sub(add(sq(ey),sq(ez)),add(sq(hy),sq(hz)))))),
        'transverse_fields_have_equal_norm':assertion(VECTOR_ARGS,op('y',transverse,op('e',norm(E),norm(H)))),
        'transverse_electric_amplitude_factor':assertion('beta ratio '+VECTOR_ARGS,op('y',both(normalization,transverse),op('e',norm(ep),scaled))),
        'transverse_magnetic_amplitude_factor':assertion('beta ratio '+VECTOR_ARGS,op('y',both(normalization,transverse),op('e',norm(hp),scaled))),
        'parallel_amplitude_square':assertion('light speed power newpower',op('y',k('seae',v('light'),v('speed'),one,v('power'),v('newpower')),
            op('e',mul(add(v('light'),v('speed')),v('newpower')),mul(sub(v('light'),v('speed')),v('power'))))),
        'reviewed_transverse_value':assertion('',k('seae',*(literal(x) for x in (5,3,0,1,F(25,16))))),
        'snapshot_square_root_value':assertion('',k('seae',*(literal(x) for x in (5,3,0,1,F(5,4))))),
        'longitudinal_electric_field_is_not_a_transverse_wave':assertion('',k('sead',*(literal(x) for x in (1,0,0,1,0,0,0,0,0)))),
    }
    rows={};base=generic_composed()[0]
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),MEANINGS,timeout_ms=20000)[0]
        expected='invalid' if name in ('snapshot_square_root_value','longitudinal_electric_field_is_not_a_transverse_wave') else 'valid'
        if result['status']!=expected:raise ValueError('Amplitude algebra differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'rational_polynomial_proofs_only':True,'all_real_cut_laws_proved':False}


def cross(left,right):
    return tuple(left[(i+1)%3]*right[(i+2)%3]-left[(i+2)%3]*right[(i+1)%3] for i in range(3))


def amplitude_cases(texts):
    names=tuple('j'+n for n in 'abcdefghijklmnopqrs')
    decls=''.join('r '+n+'[] '+CUT+'.' for n in names)
    square=lambda value:k('shv',value,value)
    query='q['+k('seam',*map(k,names))+'].'
    query+='q['+k('seak',k('ja'),k('jb'),k('jc'),square(k('jr')),square(k('js')))+'].'
    docs=[abstract(candidate(text,decls+query),OPS) for text in texts]
    fixtures=(
        ((1,0,0),(0,3,4),5),((-1,0,0),(0,3,4),5),((0,1,0),(3,0,4),5),
        ((F(3,5),F(4,5),0),(F(-4,5),F(3,5),0),1),
        ((F(1,3),F(2,3),F(2,3)),(F(2,3),F(1,3),F(-2,3)),1),
    )
    cases={}
    for speed,scale,(direction,electric,magnitude) in product((-3,0,3),(0,-2,1),fixtures):
        n=tuple(map(F,direction));E=tuple(F(scale)*x for x in electric);H=cross(n,E)
        outputs=expected_values((5,speed,2,*n,*E,*H),(0,0,0,0),lambda phase:F(1))
        beta=F(5,4) if speed else F(1)
        A=abs(scale)*magnitude;newA=A*beta*(1-n[0]*F(speed,5))
        cases['valid_'+str(len(cases))]=((5,speed,*n,*E,*H,*outputs,A,newA),[True,True])
    # Nonzero oblique wave with unit amplitude.
    n=(F(3,5),F(4,5),0);E=(F(-4,5),F(3,5),0);H=cross(n,E)
    out=expected_values((5,3,2,*n,*E,*H),(0,0,0,0),lambda phase:F(1))
    base=list(map(F,(5,3,*n,*E,*H,*out,1,F(4,5))))
    for name,index,value,expected in (
        ('negative_old_amplitude',17,-1,[False,True]),
        ('negative_new_amplitude',18,F(-4,5),[False,True]),
        ('wrong_old_amplitude',17,2,[False,False]),
        ('wrong_new_amplitude',18,2,[False,False]),
        ('nonunit_direction',3,0,[False,True]),
        ('longitudinal_electric_component',5,1,[False,True]),
        ('reversed_magnetic_orientation',10,-1,[False,True]),
        ('different_magnetic_magnitude',10,2,[False,True]),
        ('light_speed_boundary',1,5,[False,False]),
        ('negative_light',0,-5,[False,False]),
    ):
        args=base.copy();args[index]=F(value);cases[name]=(args,expected)
    for index in range(6):
        args=base.copy();args[11+index]+=1;cases['changed_transformed_'+str(index)]=(args,[False,True])
    rows={}
    for name,(args,expected) in cases.items():
        checked=[]
        for doc in docs:
            fixture,model=setup(doc)
            for symbol,value in zip(names,args):model[symbol]=lambda value=value:fixture.make(value)
            result=evaluate(doc,model)
            if result!=expected:raise ValueError('Amplitude magnitude binding differs: '+name+repr(result))
            checked.append(result)
        if checked[0]!=checked[1]:raise ValueError('Standalone amplitude differs')
        rows[name]=checked[0]
    return {'cases':rows,'cumulative_and_standalone_agree':True,'zero_and_negative_field_scaling_tested':True,
        'negative_magnitude_is_not_recovered_from_square':True,'rational_cut_oracles_not_general_real_proof':True}


def ratio_cases(text):
    names=tuple('j'+n for n in 'abcde')
    doc=abstract(candidate(text,''.join('r '+n+'[] '+CUT+'.' for n in names)+'q['+k('seak',*map(k,names))+'].'),OPS)
    cases={
        'reviewed_oblique':((5,3,F(3,5),1,F(16,25)),True),
        'reviewed_transverse':((5,3,0,1,F(25,16)),True),
        'snapshot_transverse':((5,3,0,1,F(5,4)),False),
        'parallel_forward':((5,3,1,1,F(1,4)),True),
        'parallel_reverse':((5,-3,1,1,4),True),
        'zero_wave':((5,3,0,0,0),True),
        'zero_wave_nonzero_output':((5,3,0,0,1),False),
        'negative_old_square':((5,3,0,-1,F(-25,16)),False),
        'negative_new_square':((5,3,0,1,F(-25,16)),False),
        'cosine_out_of_range':((5,3,2,1,F(1,16)),False),
        'zero_light':((0,0,0,1,1),False),
        'superluminal':((5,6,0,1,1),False),
    };rows={}
    for name,(args,expected) in cases.items():
        fixture,model=setup(doc)
        for symbol,value in zip(names,args):model[symbol]=lambda value=value:fixture.make(value)
        result=evaluate(doc,model)
        if result!=[expected]:raise ValueError('Squared amplitude ratio differs: '+name+repr(result))
        rows[name]=result
    return rows


def finite_refusal(text):
    query='q['+k('seaj',*(k('bb',literal(n)) for n in (1,0,0,0,1,0,0,0,1)))+'].'
    doc=candidate(text,query);fixture,model=setup(doc)
    # Retain the original four rational primitives and actual cut definitions.
    model.update(aa=lambda a,b:a<b,ab=lambda a,b:a+b,ac=lambda a:-a,ad=lambda a,b:a*b)
    try:evaluate(doc,model)
    except ValueError as exc:
        if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
        return {'refused':True,'reason':str(exc)}
    raise ValueError('Unbounded real cuts were certified by finite interpretation')


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Snapshot differs')
    rows=[]
    for mid in ('M0345','M0347'):
        item=next(m for m in source['math'] if m['id']==mid);unit=next(u for u in source['units'] if mid in u['math_ids'])
        if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('MathML differs')
        rows.append({'unit':unit['id'],'unit_sha256':unit['text_sha256'],'math_id':mid,'math_sha256':item['sha256'],
            'definitions':['seae','seak','seal','seam'],'status':'partial',
            'review_ja':'原刊912頁を照合した二乗振幅比への部分対応。M0345は電子テキストの分母の根号を別記録で除いた形を使う。測定・観測者・光源・導出の談話と全文の意味一致は未完。'})
    return {'segments':rows,'semantic_completion':False,'new_source_ranges':False}


def build_report():
    documents={};sizes={};texts=[]
    for builder,stem in ((generic_composed,'wave-amplitudes'),(source_composed,'einstein-wave-amplitudes'),(core_composed,'wave-amplitudes-core')):
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored amplitudes differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Amplitude roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]={'characters':len(text),'statements':len(doc['statements'])}
    source=parse(texts[1]);parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if source['declarations'][:len(parent['declarations'])]!=parent['declarations'] or source['statements']!=parent['statements']:raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+s+'-basis-v1.json' for s in ('wave-amplitudes','einstein-wave-amplitudes','wave-amplitudes-core')],
        'data/wave-amplitudes-facsimile-v1.json','scripts/compose_wave_amplitudes.py','scripts/check_wave_amplitudes.py',
        'scripts/check_plane_waveforms.py','scripts/check_tau_differential.py','scripts/check_angle_composition.py','scripts/check_transverse_time.py',
        'noema/extraction.py','noema/polynomial_proofs.py','noema/finite_semantics.py','noema/discourse.py',
        'artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf','artifacts/written-facsimiles-v1/einstein-1905-unlp-p912-0.jpg',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return json.loads(json.dumps({'status':'partial_transverse_amplitudes_and_reviewed_square_ratio','documents':documents,'sizes':sizes,
        'facsimile':facsimile_check(),'polynomial':polynomial_checks(),'amplitudes':amplitude_cases(texts[1:]),
        'ratios':ratio_cases(texts[2]),'finite_refusal':finite_refusal(texts[2]),'alignment':alignment(),
        'parent_preserved':True,'roundtrips':True,'new_primitives':0,'new_author_statements':0,
        'verified_full_units':{'kant-1784':0,'einstein-1905':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}},ensure_ascii=False))


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Wave amplitude report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Transverse amplitude vectors and reviewed squared ratio checked')


if __name__=='__main__':main()
