"""Check determined extensions and a non-factive introduction explanation relation."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from noema.finite_semantics import Content
from noema.first_order_proofs import verify
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, guarded
from scripts.check_total_differential import setup, OPERATIONS
from scripts.check_force_wordings import cross
from scripts.check_real_products import assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, op, both
from scripts.compose_auxiliary_terms import ROOT, PARENT, CUT, POINT, CONSTRUCTION, composed, generic_composed

REPORT=ROOT/'reports/auxiliary-terms-v1.json'
DOMAIN=('first','second','x','y')


def finite_extensions():
    doc=parse(generic_composed()[0]+'r ja[a] c.r jb[a a] c.q[k scz2[p ja p jb]].q[k sda2[p ja p jb]].');rows={}
    cases={
        'baseline':({'first','second'},{('first','x'),('second','y')},[True,True]),
        'missing_base_state':({'first','second'},{('first','x')},[False,False]),
        'extra_freedom':({'first','second'},{('first','x'),('first','y'),('second','y')},[True,False]),
        'leaks_forbidden_state':({'first','second'},{('first','x'),('second','y'),('x','x')},[False,False]),
        'different_states_same_value':({'first','second'},{('first','x'),('second','x')},[True,True]),
        'empty_theory':(set(),set(),[True,True]),
        'empty_theory_with_extension':(set(),{('first','x')},[False,False]),
        'changed_values_but_still_determined':({'first','second'},{('first','y'),('second','x')},[True,True]),
    }
    for name,(base,extended,expected) in cases.items():
        model=guarded(doc);model.update(ja=lambda s:s in base,jb=lambda s,x:(s,x) in extended)
        actual=values(doc,model,DOMAIN)
        if actual!=expected:raise ValueError('Extension preserves wrong states or freedoms: '+name)
        rows[name]=actual
    return {'cases':rows,'conservativity_does_not_prove_consistency':True,'unique_values_do_not_identify_the_intended_formula':True}


def defined_graphs():
    doc=parse(generic_composed()[0]+'r ja[a] c.r jb[a] a.q[k sdc2[p ja p jb]].');rows={}
    maps=(('identity',lambda s:s),('constant',lambda s:'x'),('rotation',lambda s:DOMAIN[(DOMAIN.index(s)+1)%len(DOMAIN)]))
    for mask in range(16):
        allowed={s for i,s in enumerate(DOMAIN) if mask&(1<<i)}
        for name,calculate in maps:
            model=guarded(doc);model.update(ja=lambda s:s in allowed,jb=calculate);actual=values(doc,model,DOMAIN)
            if actual!=[True]:raise ValueError('Graph of a total function added a restriction')
            rows[str(mask)+':'+name]=actual
    return {'cases':rows,'all_subsets_of_the_supplied_four_object_domain':True,'finite_examples_supplement_the_general_proof':True}


def first_order_checks():
    doc=parse(generic_composed()[0]);doc['declarations']=[d for d in doc['declarations'] if d['name'] in ('scz2','sda2','sdb2','sdc2')];doc['statements']=[]
    text=format_graph(doc,'compact')+'r ja[a] c.r jb[a] a.r jc[a a] c.'
    result=verify(parse(text+'s[k sdc2[p ja p jb]].s[y[k sda2[p ja p jc]][k scz2[p ja p jc]]].'))
    if [r['status'] for r in result]!=['valid','valid']:raise ValueError('First-order extension law failed')
    return {'claims':dict(zip(('defined_graph_is_conservative_and_determined','determined_extension_preserves_base_states'),result)),
        'actual_noema_definitions_expanded':True,'arbitrary_nonempty_individual_domains':True,'does_not_prove_real_vector_closure':True}


def vector_checks():
    text=generic_composed()[0]+'r ja[] '+CUT+'.r jb[] '+POINT+'.r jc[] '+POINT+'.r jd[] '+POINT+'.q[k sdd2[k ja[] k jb[] k jc[] k jd[]]].'
    doc=abstract(parse(text),OPERATIONS);rows={};domain=('x','y','z','t','other')
    cases=(('general',5,(1,2,3),(3,-2,1)),('zero',5,(0,0,0),(3,-2,1)),
        ('parallel',2,(1,2,3),(2,4,6)),('negative',5,(-1,-2,-3),(3,-2,1)))
    for name,V,u,h in cases:
        computed=tuple(F(x,V) for x in cross(u,h))
        for kind in ('correct','different_other_components','wrong_x','wrong_y','wrong_z'):
            result=list(computed)
            if kind.startswith('wrong_'):result[domain.index(kind[-1])]+=1
            fixture,model=setup(doc)
            callbacks(doc,model,{symbol:lambda axis,vec=vec,symbol=symbol:fixture.make(vec[domain.index(axis)] if axis in domain[:3] else 99 if symbol=='jd' and kind=='different_other_components' else 0) for symbol,vec in (('jb',u),('jc',h),('jd',result))})
            model['ja']=lambda:fixture.make(V);actual=values(doc,model,domain)
            if actual!=[not kind.startswith('wrong_')]:raise ValueError('Derived vector relation differs')
            rows[name+':'+kind]=actual
    return {'cases':rows,'uniqueness_is_spatial_component_equality_not_function_identity':True}


def rational_uniqueness():
    V,a,b,c,i=('v '+n for n in ('light','first','second','cross','inverse'));zero=literal(0);one=literal(1)
    mul=lambda a,b:k('ad',a,b);eq=lambda a,b:op('e',a,b)
    claims={
        'nonzero_divisor_gives_unique_added_component':assertion('light first second cross',op('y',both(op('u',eq(V,zero)),eq(mul(V,a),c),eq(mul(V,b),c)),eq(a,b))),
        'reciprocal_constructs_added_component':assertion('light cross inverse',op('y',eq(mul(V,i),one),eq(mul(V,mul(i,c)),c))),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse('n:r ad[b b] b.'+claim),{'ad':'multiply'},timeout_ms=20000)[0]
        if result['status']!='valid':raise ValueError('Rational extension lemma failed')
        rows[name]=result
    return {'claims':rows,'rational_polynomial_only':True}


def explanation_checks():
    doc=abstract(candidate(composed()[0],'q[t[k sdg2[]][k ri[]]].'),{'sdf2','scx2'});rows=[]
    for determined in (False,True):
        for dependence in (False,True):
            for adopted in (False,True):
                model=guarded(doc);model.update(ri=lambda:'text',rd=lambda:'author',zno=lambda:'scope',
                    sdf2=lambda:Content(('motion','text','other'),(False,determined,False)),
                    scx2=lambda:Content(('motion','text','other'),(False,dependence,False)),
                    zpu=lambda author,reason,construction,scope,ctx:adopted and (author,json.loads(reason.syntax)['symbol'],json.loads(construction.syntax)['symbol'],scope,ctx)==('author','scx2','sci2','scope','text'))
                actual=values(doc,model,('author','scope','other'))
                if actual!=[determined and dependence and adopted]:raise ValueError('Truth was confused with an explanation')
                rows.append(dict(determined=determined,dependence=dependence,adopted=adopted,result=actual))
    return rows


def explanation_identity():
    alias='d ja[light '+CUT+' velocity '+POINT+' magnetic '+POINT+'] '+POINT+'[k sci2[v light v velocity v magnetic]].'
    doc=candidate(composed()[0],alias+'q[k zpu[k rd[] r[k scx2[]] r[p sci2] k zno[] k ri[]]].q[k zpu[k rd[] r[k scx2[]] r[p ja] k zno[] k ri[]]].');rows={}
    for wrong in ('none','author','reason','construction','scope','context'):
        model=guarded(doc);model.update(rd=lambda:'author',zno=lambda:'scope',ri=lambda:'text')
        expected=['author','scx2','sci2','scope','text']
        if wrong!='none':expected[('author','reason','construction','scope','context').index(wrong)]='other'
        model['zpu']=lambda author,reason,construction,scope,ctx:[author,json.loads(reason.syntax)['symbol'],json.loads(construction.syntax)['symbol'],scope,ctx]==expected
        actual=values(doc,model,('author','scope','other'))
        if actual!=[wrong=='none',False]:raise ValueError('Explanation description or scope changed')
        rows[wrong]=actual
    return {'cases':rows,'definitionally_equal_alias_not_automatically_substituted_inside_description':True,'construction_not_executed':True}


def finite_refusal():
    doc=abstract(candidate(composed()[0],'q[t[k sdf2[]][k ri[]]].'),OPERATIONS);fixture,model=setup(doc);model['ri']=lambda:'text'
    try:values(doc,model,('x','y','z','other'))
    except ValueError as exc:
        if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
        return {'refused':True,'reason':str(exc)}
    raise ValueError('Finite domain certified real-vector closure')


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for wrong in ('none','author','role','explanation','scope','context'):
        model=guarded(doc)
        for name,value in {'zpv':'role','zpw':'explanation','rd':'author','zno':'scope','ri':'text'}.items():model[name]=lambda value=value:value
        def claim(node,author,content,scope,ctx):
            return node in ('role','explanation') and [author,json.loads(content.syntax)['symbol'],scope,ctx]==['other' if wrong=='author' else 'author','other' if wrong==node else 'sdf2' if node=='role' else 'sdg2','other' if wrong=='scope' else 'scope','other' if wrong=='context' else 'text']
        model['uh']=claim;actual=values(doc,model,('role','explanation','author','scope','other'))
        if actual!=[wrong not in ('author','role','scope','context'),wrong not in ('author','explanation','scope','context')]:raise ValueError('Auxiliary role attribution differs')
        rows[wrong]=actual
    return {'cases':rows,'quoted_contents_not_executed':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'));inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Source inventory changed')
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0176')
    if hashlib.sha256(unit['text'].encode()).hexdigest()!=unit['text_sha256']:raise ValueError('Auxiliary source changed')
    start=unit['text'].index('daß in der entwickelten Theorie');end=unit['text'].index(', daß die elektrischen')
    return {'segments':[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=start,end=end,source=unit['text'][start:end],
        definitions=['scz2','sda2','sdb2','sdd2','sde2','sdf2','sdg2'],status='partial_explicit_reading',full_semantic_equivalence=False)],
        'conservative_determined_extension_is_a_partial_role_reading':True,'obviousness_and_full_theoretical_role_unfinished':True,'verified_full_units':0}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'auxiliary-terms'),(composed,'einstein-auxiliary-terms')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored auxiliary terms differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Auxiliary roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['statements'][:-2]!=parent['statements'] or doc['declarations'][:len(parent['declarations'])]!=parent['declarations']:raise ValueError('Auxiliary parent changed')
    paths=list(documents)+['data/auxiliary-terms-basis-v1.json','data/einstein-auxiliary-terms-basis-v1.json',PARENT,
        'scripts/compose_auxiliary_terms.py','scripts/check_auxiliary_terms.py','scripts/check_total_differential.py','scripts/check_force_wordings.py',
        'noema/first_order_proofs.py','noema/polynomial_proofs.py','noema/discourse.py','noema/finite_semantics.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'partial_auxiliary_construction_and_introduction_explanation','documents':documents,'extensions':finite_extensions(),
        'defined_graphs':defined_graphs(),'first_order':first_order_checks(),'vectors':vector_checks(),'rational':rational_uniqueness(),
        'explanation':explanation_checks(),'description_identity':explanation_identity(),'finite_refusal':finite_refusal(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,'parent_preserved':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/PARENT).read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Auxiliary report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Conservative extension laws, vector construction and introduction explanation checked')


if __name__=='__main__':main()
