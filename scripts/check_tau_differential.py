"""Check derivative argument bindings without finitely replacing real limits."""
import argparse
from fractions import Fraction
import hashlib
import json

from noema.grammar import parse, format_graph
from noema.finite_semantics import FunctionValue
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, guarded
from scripts.check_rod_measurements import cut
from scripts.check_real_products import MEANINGS, call, op, assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_tau_differential import ROOT, CUT, TAU, generic_composed, limit_declarations, source_composed

REPORT=ROOT/'reports/tau-differential-v1.json'
ARITHMETIC={'ba','bb','bc','bg','bd','bf','shv','bj','sjd','sca'}


class ConstructedCuts:
    """Exact oracle on retained, constructed rational cuts; no sampled decoding."""
    def __init__(self):self.table={}

    def make(self,value):
        value=Fraction(value);result=cut(value);self.table[result.implementation]=value
        return result

    def read(self,value):
        # The finite evaluator wraps FunctionValue in a typed invoke(raw, args)
        # closure. Follow only that wrapper to a retained fixture implementation;
        # never infer a rational value by probing an arbitrary predicate.
        while isinstance(value,FunctionValue):
            implementation=value.implementation
            if implementation in self.table:return self.table[implementation]
            code=getattr(implementation,'__code__',None)
            if code is None:break
            free=dict(zip(code.co_freevars,
                (cell.cell_contents for cell in (getattr(implementation,'__closure__',None) or ()))))
            value=free.get('raw')
        raise ValueError('Cut was not constructed by this finite fixture')

    def arithmetic(self,model):
        n=self.read;c=self.make
        model.update(aa=lambda a,b:a<b,bb=c,ba=lambda x:abs(n(x))<128,bc=lambda a,b:n(a)<=n(b),
            bg=lambda a,b:n(a)<n(b),sca=lambda a,b:n(a)==n(b),bd=lambda a,b:c(n(a)+n(b)),
            bf=lambda a,b:c(n(a)-n(b)),shv=lambda a,b:c(n(a)*n(b)),bj=lambda s,x:c(s*n(x)),
            sjd=lambda x:c(1/n(x) if n(x)>0 else 0))


def polynomial_checks():
    V,v,a,b,o,r=('v '+n for n in ('light','speed','space','time','outward','returning'))
    add=lambda x,y:call('ab',x,y);mul=lambda x,y:call('ad',x,y);sub=lambda x,y:add(x,call('ac',y))
    inverses=call('sjb',literal(1),V,v,o,r)
    first=call('ska',V,v,a,b,o,r);second=call('skb',V,v,a,b)
    x,t,h,k,c=('v '+n for n in ('position','moment','dx','dt','offset'))
    function=lambda x,t:call('sjc',a,b,c,x,t)
    residual=sub(sub(function(add(x,h),add(t,k)),function(x,t)),add(mul(a,h),mul(b,k)))
    claims={
        'inverse_sum_form_iff_rearranged_coefficient_equation':assertion('light speed space time outward returning',op('y',inverses,op('z',first,second))),
        'affine_candidate_has_zero_two_variable_linear_remainder':assertion('space time offset position moment dx dt',op('e',residual,literal(0))),
        'swapping_partial_roles_preserves_the_equation':assertion('light speed space time',op('y',second,call('skb',V,v,b,a))),
        'wrong_sign_on_speed_term_is_equivalent':assertion('light speed space time',op('y',second,op('e',sub(mul(sub(mul(V,V),mul(v,v)),a),mul(v,b)),literal(0)))),
        # For F(x,t)=xt/(|x|+|t|), F(h,h)=h/2 when h>0.
        # Its coordinate-axis partials at zero vanish, but the proposed zero
        # linear map fails the epsilon=1/8 remainder bound at every h>0.
        'diagonal_counterexample_value_satisfies_its_quotient':assertion('dx',op('y',call('aa',literal(0),h),op('e',mul(add(h,h),mul(literal(Fraction(1,2)),h)),mul(h,h)))),
        'diagonal_counterexample_defeats_zero_linear_map':assertion('dx',op('y',call('aa',literal(0),h),call('aa',mul(literal(Fraction(1,8)),add(h,h)),mul(literal(Fraction(1,2)),h)))),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        expected='invalid' if name in ('swapping_partial_roles_preserves_the_equation','wrong_sign_on_speed_term_is_equivalent') else 'valid'
        if result['status']!=expected:raise ValueError('Differential algebra differs: '+name)
        rows[name]=result
    return {'claims':rows,'rational_polynomial_lemmas_only':True,'general_chain_rule_proved':False,
        'separate_partials_counterexample':'F(x,t)=xt/(|x|+|t|), F(0,0)=0; both axis partials vanish, while F(h,h)=h/2 for h>0'}


def reuse_checks():
    doc=parse(source_composed()[0]);decls={d['name']:d for d in doc['declarations']}
    for d in limit_declarations():
        if d!=decls[d['name']]:raise ValueError('Renamed limit or derivative changed')
    old=parse((ROOT/'examples/v011/real-products.noema').read_text(encoding='utf-8'))
    d=next(d for d in old['declarations'] if d['name']=='cg')
    def replace(node):
        if isinstance(node,list):return [replace(x) for x in node]
        if not isinstance(node,dict):return node
        result={k:replace(v) for k,v in node.items()}
        if result.get('symbol') in ('ca','cf'):result['symbol']={'ca':'sju','cf':'sjd'}[result['symbol']]
        if result.get('name')=='cg':result['name']='sjt'
        return result
    if replace(d)!=decls['sjt']:raise ValueError('Signed reciprocal differs from the preserved definition')
    return {'five_limit_and_derivative_definitions_reused':True,'signed_reciprocal_reused':True}


def equation_checks():
    doc=abstract(candidate(source_composed()[0],'''
r ja[] h[b] c.r jb[] h[b] c.r jc[] h[b] c.r jd[] h[b] c.
q[k sjx[k ja[] k jb[] k jc[] k jd[]]].q[k sjy[k ja[] k jb[] k jc[] k jd[]]].'''),ARITHMETIC)
    rows={}
    for name,(args,expected) in {
        'baseline':((3,1,-1,8),True),'scaled_partials':((3,1,Fraction(-1,4),2),True),
        'zero_speed':((3,0,0,8),True),'wrong_space_partial':((3,1,1,8),False),
        'wrong_time_partial':((3,1,-1,4),False),'swapped_partials':((3,1,8,-1),False),
        'light_speed_boundary':((1,1,-1,8),False),'above_light_speed':((1,2,-1,8),False),
        'negative_speed':((3,-1,-1,8),False),'invalid_partial':((3,1,128,8),False),
    }.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        for symbol,value in zip(('ja','jb','jc','jd'),args):model[symbol]=lambda value=value:fixture.make(value)
        actual=values(doc,model,('object',))
        if actual!=[expected,expected]:raise ValueError('Real-cut differential expression differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'exact_constructed_rational_cut_oracles':True,'no_real_cut_sampling':True}


def slice_checks():
    doc=abstract(candidate(source_composed()[0],'''
r ja[] '''+TAU+'''.r jb[] h[b] c.r jc[] h[b] c.r jd[] h[b] c.r je[] h[b] c.r jf[] h[b] c.r jg[] h[b] c.
q[k sjw[k ja[] k jb[] k jc[] k jd[] k je[] k jf[] k jg[]]].'''),ARITHMETIC|{'sjs'})
    rows={}
    for name in ('baseline','wrong_x_point','wrong_y_point','wrong_z_point','wrong_time_point','wrong_space_partial','wrong_time_partial','swapped_partials','missing_derivative'):
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model);observed=[]
        params=[1,2,1,3,-1,8]
        for i,key in enumerate(('x','y','z','time')):
            if name=='wrong_'+key+'_point':params[i]+=1
        if name=='wrong_space_partial':params[4]=1
        if name=='wrong_time_partial':params[5]=7
        if name=='swapped_partials':params[4:]=[8,-1]
        for symbol,value in zip(('jb','jc','jd','je','jf','jg'),params):model[symbol]=lambda value=value:c(value)
        def function(x,y,z,t):
            args=tuple(n(v) for v in (x,y,z,t));observed.append(args)
            return c(-args[0]+4*args[1]+5*args[2]+8*args[3])
        def derivative(domain,fn,point,value):
            p=n(point);result=n(value)
            return name!='missing_derivative' and domain(point) and n(fn(point))==36 and result in (-1,8) and all(
                n(fn(c(p+step)))-n(fn(point))==result*step for step in (-1,1,2))
        callbacks(doc,model,{'ja':function});model['sjs']=derivative
        actual=values(doc,model,('object',))[0]
        if actual!=(name=='baseline'):raise ValueError('Partial derivative slice differs: '+name+repr(actual))
        if name=='baseline' and not all((y,z)==(2,1) and (x==1 or t==3) for x,y,z,t in observed):raise ValueError('Unvaried coordinates were changed')
        rows[name]=actual
    return {'cases':rows,'derivative_oracle_only_checks_supplied_affine_fixture':True,'other_coordinates_fixed':True}


def source_checks():
    doc=abstract(candidate(source_composed()[0],'q[k skd[k zb6[]]].'),ARITHMETIC|{'sjl','skc','sjv','sjw'})
    rows={}
    for name in ('baseline','missing_prior_binding','no_neighborhood','single_trial_only','zero_radius','wrong_time',
        'wrong_function','wrong_space_partial','wrong_time_partial','no_total_derivative','no_partial_derivatives','wrong_context'):
        fixture=ConstructedCuts();n=fixture.read;c=fixture.make;model=guarded(doc);fixture.arithmetic(model)
        for key,value in {'zb6':'other' if name=='wrong_context' else 'motion','zdq':'trial','ra':'rest','zc7':'time'}.items():model[key]=lambda value=value:value
        model.update(qe=lambda tr:'depart',zdz=lambda e,f,ctx:'tuple',zc6=lambda tup,r:c(3 if name=='wrong_time' else 2),
            tc=lambda:c(3),zb7=lambda:c(1),zd5=lambda:c(0 if name=='zero_radius' else 1),
            zd6=lambda:c(1 if name=='wrong_space_partial' else -1),zd7=lambda:c(7 if name=='wrong_time_partial' else 8),
            sjl=lambda ctx:ctx=='motion' and name!='missing_prior_binding')
        def function(x,y,z,t):return c((-1 if name!='wrong_function' else 1)*n(x)+8*n(t))
        callbacks(doc,model,{'zd4':function})
        def matching(fn):return n(fn(c(1),c(0),c(0),c(2)))==15
        model['skc']=lambda f,V,v,t,r:matching(f) and tuple(n(x) for x in (V,v,t,r))==(3,1,2,1) and name not in ('no_neighborhood','single_trial_only')
        for symbol,bad in (('sjv','no_total_derivative'),('sjw','no_partial_derivatives')):
            model[symbol]=lambda f,x,y,z,t,px,pt,bad=bad:matching(f) and tuple(n(a) for a in (x,y,z,t,px,pt))==(0,0,0,2,-1,8) and name!=bad
        actual=values(doc,model,('trial','rest','time','depart','tuple'))[0]
        if actual!=(name=='baseline'):raise ValueError('Local differential premise differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'prior_binding_neighborhood_and_differentiability_are_oracles':True,'origin_and_same_time_preserved':True}


def finite_refusals():
    rows={}
    queries={
        'full_real_neighborhood':'k skc[k ja[] k jb[] k jc[] k jd[] k je[]]',
        'two_variable_linear_approximation':'k sjv[k ja[] k jd[] k jd[] k jd[] k jd[] k jc[] k jb[]]',
        'partial_derivative_limit':'k sjw[k ja[] k jd[] k jd[] k jd[] k jd[] k jc[] k jb[]]',
    }
    for name,query in queries.items():
        doc=abstract(candidate(source_composed()[0],'r ja[] '+TAU+'.r jb[] '+CUT+'.r jc[] '+CUT+'.r jd[] '+CUT+'.r je[] '+CUT+'.q['+query+'].'),ARITHMETIC)
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model)
        model.update(jb=lambda:fixture.make(3),jc=lambda:fixture.make(1),jd=lambda:fixture.make(0),je=lambda:fixture.make(1))
        callbacks(doc,model,{'ja':lambda x,y,z,t:fixture.make(fixture.read(x)+3*fixture.read(t))})
        try:values(doc,model,('object',))
        except ValueError as error:
            if 'Cannot finitely quantify the rational number domain' not in str(error):raise
            rows[name]={'refused':True,'reason':str(error)}
        else:raise ValueError('Finite sampling accepted a real limit or neighborhood')
    return rows


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for name in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_limit_premise','wrong_first_equation','wrong_rewrite_premise','wrong_rewrite_before','wrong_rewrite_after'):
        model=guarded(doc)
        for k,v in {'zea':'limit','zeb':'rewrite','rd':'author','rh':'scope','ri':'text'}.items():model[k]=lambda v=v:v
        symbol=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','other' if name=='wrong_context' else 'text')
        model.update(zc=lambda node,a,p,q,s,c:common(a,s,c) and (node,symbol(p),symbol(q))==('limit','sjm' if name=='wrong_limit_premise' else 'ske','skg' if name=='wrong_first_equation' else 'skf'),
            zd3=lambda node,a,p,b,d,s,c:common(a,s,c) and (node,symbol(p),symbol(b),symbol(d))==('rewrite','sjm' if name=='wrong_rewrite_premise' else 'ske','siz' if name=='wrong_rewrite_before' else 'skf','skf' if name=='wrong_rewrite_after' else 'skg'))
        actual=values(doc,model,('limit','rewrite','author','scope'));bad={'wrong_author','wrong_scope','wrong_context'}
        if actual!=[name not in bad|{'wrong_limit_premise','wrong_first_equation'},name not in bad|{'wrong_rewrite_premise','wrong_rewrite_before','wrong_rewrite_after'}]:raise ValueError('Differential inference attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'));rows=[]
    for uid,digest,mid,mdigest,defs in (
        ('einstein-1905:u0054','23dc1f9497cbbc5500b805b1fa49801366e7766329281646ae02fea01c746e18','M0102','5789f9fd8ca6ee1a7ad7b9d6fdd7d9d84bd2ac37e2e0869db607ee20d6aa8e62',['sjv','sjw','skc','skd','ske']),
        ('einstein-1905:u0055','c09c543a3988aaa674b35503b21575be8d9327b1c2629eb2412f2c3c52caa631','M0103','e8a9ec8a5a4da9e1ca4e05c63fb88d2aa8301da17001e921c94c3579aa31301d',['sjx','skf']),
        ('einstein-1905:u0056','b81d9593a3f6c4f7d125fd1da37c9b1fb180574cfb728f3db3c70eda3053e079',None,None,['skf','skg']),
        ('einstein-1905:u0057','f826093e5e1fa23cd15456ed32cfaff71f22a8dc3a5029a3e393d57b30fc45d7','M0104','88911ee9357b4f1be52655797918ef155797ffaf3fd12c0c1607f281b4efbeb1',['sjy','skg'])):
        unit=next(u for u in artifact['units'] if u['id']==uid)
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Differential source changed')
        rows.append({'unit':uid,'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],'definitions':defs,'status':'partial_explicit_reading','full_semantic_equivalence':False})
        if mid:
            math=next(m for m in artifact['math'] if m['id']==mid)
            if hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest()!=mdigest:raise ValueError('Differential equation changed')
            rows.append({'unit':uid,'unit_sha256':digest,'math_id':mid,'math_sha256':mdigest,'definitions':defs,'status':'partial','full_semantic_equivalence':False})
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'explicit_sufficient_regularity_added':True,'arbitrary_starting_point_not_yet_generalized':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored differential differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Differential roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/tau-differential-basis-v1.json','data/einstein-tau-differential-basis-v1.json',
        'examples/v014/einstein-light-time-arguments.noema','examples/v011/limits.noema','examples/v011/real-products.noema',
        'scripts/compose_tau_differential.py','scripts/check_tau_differential.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-light-time-arguments.noema').read_text(encoding='utf-8')
    return {'status':'partial_local_differentiability_and_tau_differential_equations','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'reused_definitions':reuse_checks(),'equations':equation_checks(),
        'partial_slices':slice_checks(),'source_premise':source_checks(),'finite_refusals':finite_refusals(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Differential report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Differential equations, fixed-coordinate slices and real-limit refusals checked')


if __name__=='__main__':main()
