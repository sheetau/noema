"""Check two connected calculation paths and genuinely general comparison."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from itertools import product
from noema.finite_semantics import Content
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded, callbacks
from scripts.check_calculation_discourse import sequence, symbol
from scripts.check_field_transform import setup, OPS, affine_callback, field_values, E, H
from scripts.check_moving_light_trip import literal
from scripts.check_real_products import assertion
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import POINT, ROLES
from scripts.compose_origin_clock import definition
from scripts.compose_inverse_methods import ROOT, PARENT, CUT, FIELD, STEPS, generic_composed, composed

REPORT=ROOT/'reports/inverse-methods-v1.json'
DOMAIN=('x','y','z','t','other')


def path_checks():
    prefix=generic_composed()[0]+'r ja[] e.r jb[] e.r jc[] e.r jd[] e.r je[i[e] i[e]] c.'
    cases={
        'baseline':([('ja','jb')],[('ja','jc')],'jc',True),
        'intermediate_steps':([('ja','jd'),('jd','jb')],[('ja','jc')],'jc',True),
        'empty_first':([],[('ja','jc')],'jc',False),
        'empty_second':([('ja','jb')],[],'jc',False),
        'same_description':([('ja','jb')],[('ja','jb')],'jb',False),
        'swapped_results':([('ja','jc')],[('ja','jb')],'jc',False),
        'wrong_premise':([('jd','jb')],[('ja','jc')],'jc',False),
        'broken_first':([('ja','jd'),('ja','jb')],[('ja','jc')],'jc',False),
        'unapproved_second_step':([('ja','jb')],[('ja','jd'),('jd','jc')],'jc',False),
    };rows={}
    for name,(first,second,target,expected) in cases.items():
        doc=parse(prefix+'q[k sbs2['+sequence(first)+' '+sequence(second)+' r[k ja[]] r[k jb[]] r[k '+target+'[]] p je]].')
        model=guarded(doc);model.update(aa=lambda a,b:a<b,ab=lambda a,b:a+b,je=lambda before,after:(symbol(before),symbol(after)) in {('ja','jb'),('ja','jc'),('ja','jd'),('jd','jb')})
        actual=values(doc,model,DOMAIN)
        if actual!=[expected]:raise ValueError('Two calculation paths differ: '+name)
        rows[name]=actual
    return {'cases':rows,'quoted_formula_contents_not_executed':True,'allowed_transform_soundness_not_claimed':True}


def scalar_checks():
    doc=abstract(candidate(composed()[0],'r ja[] '+CUT+'.r jb[] '+CUT+'.r jc[] '+CUT+'.q[k sbi2[k ja[] k jb[]]].q[k sbn2[k ja[] k jb[] k jc[]]].'),OPS);rows={}
    for name,a,b,value in (('positive',2,F(1,2),3),('negative',-2,F(-1,2),3),('mismatch',2,3,1),('zero_masks_mismatch',2,3,0)):
        fixture,model=setup(doc);c=fixture.make;model.update(ja=lambda:c(a),jb=lambda:c(b),jc=lambda:c(value))
        actual=values(doc,model,DOMAIN)
        if actual!=[True,value/a==b*value]:raise ValueError('Inverse coefficient comparison differs')
        rows[name]=actual
    valid=abstract(candidate(composed()[0],'r ja[] '+CUT+'.r jb[] '+CUT+'.q[k sbi2[k ja[] k jb[]]].'),OPS)
    fixture,model=setup(valid);model.update(ja=lambda:fixture.make(0),jb=lambda:fixture.make(1))
    rows['zero_divisor']=values(valid,model,DOMAIN)
    if rows['zero_divisor']!=[False]:raise ValueError('Zero inverse coefficient accepted')
    a,b,inv,x=('v '+name for name in ('first','second','inverse','input'));mul=lambda a,b:k('ad',a,b);eq=lambda a,b:op('e',a,b)
    claim=assertion('first second inverse input',op('y',both(eq(mul(a,inv),literal(1)),op('u',eq(x,literal(0))),eq(mul(inv,x),mul(b,x))),eq(mul(a,b),literal(1))))
    proof=verify_universal(parse('n:r ad[b b] b.'+claim),{'ad':'multiply'},timeout_ms=20000)[0]
    if proof['status']!='valid':raise ValueError('Nonzero witness cancellation failed')
    return {'cases':rows,'nonzero_witness_algebra':proof,'zero_witness_does_not_compare_maps':True}


def field_checks():
    decls='r ja[] '+FIELD+'.r jb[] '+FIELD+'.r jc[] '+CUT+'.r jd[] '+CUT+'.r je[] '+CUT+'.r jf[] h['+CUT+'] '+CUT+'.r jg[] '+POINT+'.'
    coords=[app('k jg[]',k(role)) for role in ROLES];query=''
    for solved,reversed in (('sbj2','sbl2'),('sbk2','sbm2')):
        first=k(solved,'k jc[]','k jd[]','k je[]','k ja[]','k jb[]');second=k(reversed,'k jc[]','k jd[]','k jf[]','k ja[]','k jb[]')
        for role in ROLES[:3]:query+='q['+k('sca',app(app(first,k(role)),*coords),app(app(second,k(role)),*coords))+'].'
    doc=abstract(candidate(composed()[0],decls+query),OPS);rows={}
    for speed in (F(0),F(3),F(-3)):
        for label,a,b,zero in (('positive',F(2),F(1,2),False),('negative',F(-2),F(-1,2),False),('mismatch',F(2),F(3),False),('zero_fields_mask_mismatch',F(2),F(3),True)):
            fixture,model=setup(doc);c,n=fixture.make,fixture.read
            matrices=([(0,0,0,0,0)]*3,)*2 if zero else (E,H)
            seen=[]
            def factor(value):seen.append(n(value));return c(b if n(value)==-speed else 99)
            callbacks(doc,model,{'ja':affine_callback(doc,fixture,'ja',matrices[0]),'jb':affine_callback(doc,fixture,'jb',matrices[1]),'jf':factor,'jg':lambda role:c(1 if role in ('x','t') else 0)})
            model.update(jc=lambda:c(5),jd=lambda:c(speed),je=lambda:c(a));actual=values(doc,model,DOMAIN)
            if all(actual)!=(zero or a*b==1) or set(seen)!={-speed}:raise ValueError('Two field inverses differ: '+str((speed,label,actual)))
            rows[str(speed)+':'+label]=actual
    return {'cases':rows,'coefficient_function_evaluated_at_opposite_speed':True,'zero_field_agreement_not_general_operator_agreement':True}


def source_binding_checks():
    doc=abstract(candidate(composed()[0],'q[t[k sbp2[]][k ri[]]].q[t[k sbq2[]][k ri[]]].'),OPS|{'saj2','sai2'});rows={}
    oldE=[(0,0,0,0,a) for a in (1,2,3)];oldH=[(0,0,0,0,a) for a in (5,7,11)]
    for label,a,b in (('positive',F(2),F(1,2)),('negative',F(-2),F(-1,2)),('different_rule_scale',F(2),F(3)),('wrong_context',F(2),F(1,2)),('different_domains',F(2),F(1,2))):
        fixture,model=setup(doc);c,n=fixture.make,fixture.read;e,h=field_values(oldE,oldH,(0,0,0,0),F(3))
        callbacks(doc,model,{'znl':affine_callback(doc,fixture,'znl',oldE),'znm':affine_callback(doc,fixture,'znm',oldH),
            'znr':affine_callback(doc,fixture,'znr',[(0,0,0,0,a*x) for x in e]),'zns':affine_callback(doc,fixture,'zns',[(0,0,0,0,a*x) for x in h]),
            'znk':lambda *xs:True,'znt':lambda *xs:True,'znz':lambda value:c(a if n(value)==3 else b)})
        model.update(tc=lambda:c(5),zb7=lambda:c(3),ra=lambda:'rest',zbm=lambda:'moving',ri=lambda:'text',
            znn=lambda frame,e,h,region,ctx:ctx==('other' if label=='wrong_context' else 'text') and frame in ('rest','moving'),saj2=lambda a,b:label!='different_domains')
        def equal_fields(scale,e,h,recoveredE,recoveredH,region):
            point=[c(x) for x in (1,0,0,1)]
            return n(scale)==1 and region(*point) and all(n(left(role)(*point))==n(right(role)(*point)) for left,right in ((e,recoveredE),(h,recoveredH)) for role in DOMAIN[:3])
        model['sai2']=equal_fields;actual=values(doc,model,(*DOMAIN,'rest','moving'))
        expected=[label not in ('wrong_context','different_domains'),label in ('positive','negative')]
        if actual!=expected:raise ValueError('Source inverse binding differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'global_field_equality_and_domain_equality_are_explicit_fixture_oracles':True}


def source_paths():
    text=composed()[0];rows={}
    for label in ('baseline','empty_first','swapped_methods','wrong_context','disallowed_reversal'):
        doc=parse(text);doc['statements']=[]
        first=[] if label=='empty_first' else [('sak2','sbq2' if label=='swapped_methods' else 'sbp2')]
        second=[('sak2','sbp2' if label=='swapped_methods' else 'sbq2')]
        for name,pairs in (('zoc',first),('zod',second)):
            index=next(i for i,d in enumerate(doc['declarations']) if d['name']==name)
            prefix=dict(doc,declarations=doc['declarations'][:index])
            doc['declarations'][index]=parse(format_graph(prefix,'compact')+definition(name,'',sequence(pairs),STEPS))['declarations'][-1]
        doc=parse(format_graph(doc,'compact')+'q[t[k sbt2[]][k ri[]]].');model=guarded(doc)
        model.update(ri=lambda:'text',zla=lambda before,after,ctx:ctx==('other' if label=='wrong_context' else 'text') and (symbol(before),symbol(after)) in ({('sak2','sbp2')} if label=='disallowed_reversal' else {('sak2','sbp2'),('sak2','sbq2')}))
        actual=values(doc,model,DOMAIN)
        if actual!=[label=='baseline']:raise ValueError('Source calculation paths differ: '+label)
        rows[label]=actual
    return {'cases':rows,'steps_constructed_in_noema':True,'quoted_source_formulas_not_executed':True}


def finite_refusal():
    doc=abstract(candidate(composed()[0],'r ja[] '+CUT+'.r jb[] '+CUT+'.q[k sbo2[k ja[] k jb[]]].'),OPS)
    fixture,model=setup(doc);model.update(ja=lambda:fixture.make(2),jb=lambda:fixture.make(F(1,2)))
    try:values(doc,model,DOMAIN)
    except ValueError as error:
        if 'Cannot finitely quantify the rational number domain' not in str(error):raise
        return {'refused':True,'reason':str(error)}
    raise ValueError('Finite inputs replaced full operator comparison')


def premise_checks():
    doc=abstract(candidate(composed()[0],'q[t[k sbu2[]][k ri[]]].'),{'sbt2','sak2','sbr2'});rows=[]
    for paths,forward,agreement in product((False,True),repeat=3):
        model=guarded(doc);model['ri']=lambda:'text'
        for name,truth in (('sbt2',paths),('sak2',forward),('sbr2',agreement)):
            model[name]=lambda truth=truth:Content(('motion','text','other'),(False,truth,False))
        actual=values(doc,model,DOMAIN)
        if actual!=[paths and forward and agreement]:raise ValueError('Method connection was substituted for formula truth')
        rows.append(dict(paths=paths,forward_formula=forward,general_agreement=agreement,result=actual))
    return rows


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-1:];rows={}
    for index in range(-1,6):
        model=guarded(doc)
        for name,value in {'zoe':'node','rd':'author','zno':'scope','ri':'text'}.items():model[name]=lambda value=value:value
        expected=['node','author','sbu2','saq2','scope','text']
        if index>=0:expected[index]='other'
        model['zc']=lambda node,author,premise,conclusion,scope,ctx:[node,author,symbol(premise),symbol(conclusion),scope,ctx]==expected
        actual=values(doc,model,('node','author','scope','other'))
        if actual!=[index==-1]:raise ValueError('Inverse comparison attribution differs')
        rows[str(index)]=actual
    return rows


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'));rows=[]
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Inverse methods source changed')
    for index in (165,166):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Inverse methods text changed')
        base=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=['sbj2','sbk2','sbl2','sbm2','sbo2','sbp2','sbq2','sbr2','sbs2','sbt2','sbu2'],status='partial_explicit_reading',full_semantic_equivalence=False)
        if index==165:rows.append(dict(base,start=0,end=len(unit['text']),source=unit['text']))
        for mid in unit['math_ids']:
            m=next(m for m in source['math'] if m['id']==mid)
            if hashlib.sha256(m['mathml'].encode('utf-8')).hexdigest()!=m['sha256']:raise ValueError('Inverse methods math changed')
            rows.append(dict(base,math_id=mid,math_sha256=m['sha256']))
    return {'segments':rows,'method_soundness_and_modal_force_unfinished':True,
        'facsimile_scope':'u0165 and M0311 previously displayed on stored printed p909; no whole-page semantic certification',
        'verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'inverse-methods'),(composed,'einstein-inverse-methods')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored inverse methods differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Inverse methods roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['statements'][:-1]!=parent['statements'] or doc['declarations'][:len(parent['declarations'])]!=parent['declarations']:raise ValueError('Parent inverse methods source changed')
    paths=list(documents)+['data/inverse-methods-basis-v1.json','data/einstein-inverse-methods-basis-v1.json',PARENT,
        'scripts/compose_inverse_methods.py','scripts/check_inverse_methods.py','scripts/check_calculation_discourse.py','scripts/check_field_transform.py',
        'data/field-scale-inverse-facsimile-v1.json','artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json','noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    return {'status':'partial_two_inverse_methods_and_general_comparison','documents':documents,
        'paths':path_checks(),'scalars':scalar_checks(),'fields':field_checks(),'source_binding':source_binding_checks(),'source_paths':source_paths(),
        'premise':premise_checks(),'finite_refusal':finite_refusal(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,'parent_preserved':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Inverse methods report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Two inverse methods, linked descriptions and full comparison checked')


if __name__=='__main__':main()
