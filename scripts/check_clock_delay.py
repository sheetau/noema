"""Check calibrated elapsed loss and keep approximation distinct from equality."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.rational_proofs import verify
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_origin_clock import clock_model, DOMAIN as CLOCK_DOMAIN
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_transverse_time import square_root
from scripts.check_real_products import MEANINGS, call as k, op, assertion, conjunction as both
from scripts.check_moving_light_trip import literal
from scripts.compose_clock_delay import ROOT, CUT, generic_composed, source_composed

REPORT=ROOT/'reports/clock-delay-v1.json'
DOMAIN=CLOCK_DOMAIN+('second',)


def polynomial_checks():
    s,f,l,a,e,T,elapsed,lost=map(lambda n:'v '+n,('squaredratio','rate','lag','approximation','error','duration','elapsed','lost'))
    mul=lambda x,y:k('ad',x,y);sq=lambda x:mul(x,x);add=lambda x,y:k('ab',x,y);sub=lambda x,y:add(x,k('ac',y))
    zero=literal(0);one=literal(1);le=lambda x,y:op('u',k('aa',y,x));eq=lambda x,y:op('e',x,y)
    residual=k('svn',s,f,l,a,e)
    names='squaredratio rate lag approximation error'
    claims={
        'residual_is_half_the_squared_exact_lag':assertion(names,op('y',residual,eq(mul(literal(2),e),sq(l)))),
        'rationalized_residual_identity':assertion(names,op('y',residual,eq(mul(mul(literal(2),e),sq(add(one,f))),sq(s)))),
        'fourth_order_lower_and_upper_bounds':assertion(names,op('y',residual,both(le(mul(literal(Fraction(1,8)),sq(s)),e),le(e,mul(literal(Fraction(1,2)),sq(s)))))),
        'nonzero_speed_approximation_strictly_underestimates':assertion(names,op('y',both(residual,k('aa',zero,s)),k('aa',zero,e))),
        'zero_speed_has_zero_lag_approximation_and_error':assertion('rate lag approximation error',op('y',k('svn',zero,f,l,a,e),both(eq(l,zero),eq(a,zero),eq(e,zero)))),
        'elapsed_loss_is_nonnegative_and_below_duration':assertion('duration rate elapsed lost',op('y',k('svo',T,f,elapsed,lost),both(le(zero,lost),k('aa',lost,T)))),
        'elapsed_loss_and_residual_scale_with_duration':assertion(names+' duration elapsed lost',op('y',both(residual,k('svo',T,f,elapsed,lost)),both(eq(lost,mul(T,l)),eq(sub(lost,mul(T,a)),mul(T,e))))),
        'common_second_conversion_preserves_rate':assertion('scale duration rate elapsed lost',op('y',both(k('aa',zero,'v scale'),k('svo',T,f,elapsed,lost)),k('svo',mul('v scale',T),f,mul('v scale',elapsed),mul('v scale',lost)))),
        'second_order_formula_is_exact':assertion('',op('y',k('svn',literal(Fraction(9,25)),literal(Fraction(4,5)),literal(Fraction(1,5)),literal(Fraction(9,50)),literal(Fraction(1,50))),eq(literal(Fraction(1,5)),literal(Fraction(9,50))))),
        'one_second_delay_is_always_total_delay':assertion('',op('y',k('svo',literal(5),literal(Fraction(4,5)),literal(4),one),eq(one,literal(Fraction(1,5))))),
        'fourth_order_bound_implies_small_error_at_any_speed':assertion('',op('y',k('svn',literal(Fraction(576,625)),literal(Fraction(7,25)),literal(Fraction(18,25)),literal(Fraction(288,625)),literal(Fraction(162,625))),k('aa',literal(Fraction(162,625)),literal(Fraction(1,100))))),
    }
    invalid={'second_order_formula_is_exact','one_second_delay_is_always_total_delay','fourth_order_bound_implies_small_error_at_any_speed'}
    rows={}
    for name,claim in claims.items():
        row=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        if row['status']!=('invalid' if name in invalid else 'valid'):raise ValueError('Clock delay algebra differs: '+name+repr(row))
        rows[name]=row
    return {'claims':rows,'rational_lemmas_only':True,'small_speed_needed_for_small_absolute_approximation_error':True}


def approximation_checks():
    query=''.join('r '+n+'[] '+CUT+'.' for n in ('ja','jb','jc','jd','je','jf'))
    args=' '.join('k '+n+'[]' for n in ('ja','jb','jc','jd','je','jf'))
    query+='q[k svq['+args+']].q[k svr['+args+']].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky'});rows={}
    cases={'baseline':(5,3,Fraction(4,5),Fraction(1,5),Fraction(9,50),Fraction(1,50)),
        'negative_speed':(5,-3,Fraction(4,5),Fraction(1,5),Fraction(9,50),Fraction(1,50)),
        'stationary':(5,0,1,0,0,0),'near_light':(5,Fraction(24,5),Fraction(7,25),Fraction(18,25),Fraction(288,625),Fraction(162,625)),
        'zero_error':(5,3,Fraction(4,5),Fraction(1,5),Fraction(9,50),0),
        'approximation_used_as_exact_lag':(5,3,Fraction(4,5),Fraction(9,50),Fraction(9,50),0),
        'negative_rate':(5,3,Fraction(-4,5),Fraction(9,5),Fraction(9,50),Fraction(81,50)),
        'light_boundary':(5,5,0,1,Fraction(1,2),Fraction(1,2))}
    for label,args in cases.items():
        fixture=ConstructedCuts();model=guarded(doc);fixture.arithmetic(model);model['sky']=lambda x:square_root(fixture,x)
        for name,value in zip(('ja','jb','jc','jd','je','jf'),args):model[name]=lambda value=value:fixture.make(value)
        actual=values(doc,model,('object',));expected=label in ('baseline','negative_speed','stationary','near_light')
        if actual!=[expected]*2:raise ValueError('Exact lag and residual differ: '+label)
        rows[label]={'values':list(map(str,args)),'accepted':actual}
    return rows


def interval_checks():
    query='r ja[] a.r jb[] a.'+''.join('r '+n+'[] '+CUT+'.' for n in ('jc','jd','je','jf','jg','jh'))
    query+='q[k swd['+' '.join('k '+n+'[]' for n in ('ja','jb','jc','jd','je','jf','jg','jh'))+' k zb6[]]].q[k swe[k jc[] k zb6[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd'});rows={}
    labels=('baseline','one_second','negative_times','negative_velocity','stationary','wrong_duration','mixed_elapsed_scale','exact_equals_approximation',
        'wrong_conversion','wrong_target_unit','negative_scale','same_record','reversed_records','nonlinear_clock','missing_observer_chart','zero_light_speed')
    for label in labels:
        model,fixture,_=clock_model(doc,'stationary' if label=='zero_light_speed' else label);c=fixture.make;n=fixture.read
        scale=Fraction(1,5) if label in ('one_second','mixed_elapsed_scale') else Fraction(-1) if label=='negative_scale' else Fraction(1)
        rate=Fraction(1) if label in ('stationary','zero_light_speed') else Fraction(4,5)
        duration=5*scale;elapsed=duration*rate;lost=duration-elapsed;estimate=duration*(0 if rate==1 else Fraction(9,50));error=lost-estimate
        if label=='wrong_duration':duration=1
        if label=='mixed_elapsed_scale':elapsed=4
        if label=='exact_equals_approximation':lost=estimate;error=0
        for name,value in zip(('jc','jd','je','jf','jg','jh'),(scale,duration,elapsed,lost,estimate,error)):model[name]=lambda value=value:c(value)
        model.update(ja=lambda:'r1' if label=='reversed_records' else 'r0',jb=lambda:'r0' if label in ('same_record','reversed_records') else 'r1',
            zik=lambda:'length' if label=='wrong_target_unit' else 'second',ci=lambda unit:unit in ('time','second'),
            zil=lambda source,target,s,ctx:(source,target,n(s),ctx)==('time','second',Fraction(2) if label=='wrong_conversion' else scale,'motion'))
        if label=='zero_light_speed':model['tc']=lambda:c(0)
        actual=values(doc,model,DOMAIN)
        first=label in ('baseline','one_second','negative_times','negative_velocity','stationary')
        second=label not in ('wrong_conversion','wrong_target_unit','negative_scale','nonlinear_clock','missing_observer_chart','zero_light_speed')
        if actual!=[first,second]:raise ValueError('Second conversion and elapsed loss differ: '+label+repr(actual))
        rows[label]={'accepted':actual,'duration_seconds':str(duration),'elapsed_seconds':str(elapsed),'lost_seconds':str(lost),'approximate_seconds':str(estimate),'error_seconds':str(error)}
    return {'cases':rows,'one_second_sample_not_required_for_rate_statement':True,'same_scale_applied_to_both_times_and_all_records':True}


def asymptotic_checks():
    source=parse(source_composed()[0]);cut=parse('n:r ja[] '+CUT+'.')['declarations'][0]['result']
    def rationalize(node):
        if node==cut:return 'number'
        if isinstance(node,list):return [rationalize(x) for x in node]
        if isinstance(node,dict):return {key:rationalize(value) for key,value in node.items()}
        return node
    base=parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.d ba[x b] c[e[v x][v x]].d bb[x b] b[v x].d bg[x b y b] c[k aa[v x v y]].d bc[x b y b] c[u[k aa[v y v x]]].d bd[x b y b] b[k ab[v x v y]].d bf[x b y b] b[k ab[v x k ac[v y]]].d shv[x b y b] b[k ad[v x v y]].d sca[x b y b] c[e[v x][v y]].d sbg[x b] c[k aa[n p a b v x]].')
    base['declarations'] += [rationalize(d) for d in source['declarations'] if d['name'] in ('sjo','sjp','sjq','svw','svx','svy')]
    text=format_graph(base,'compact');domain='i[x b][w[k aa[n p a b v x]][k aa[v x n p b b]]]'
    identity='i[x b][v x]';constant=lambda n:'i[x b]['+literal(n)+']'
    cases={
        'bounded_error_big_o_one':('svy',[domain,constant(7),constant(0),constant(1),literal(0)],True),
        'exact_function_zero_scale':('svy',[domain,identity,identity,constant(0),literal(0)],True),
        'nonzero_error_zero_scale':('svy',[domain,identity,constant(0),constant(0),literal(0)],False),
        'negative_comparison_scale':('svy',[domain,identity,identity,constant(-1),literal(0)],False),
        'empty_domain_not_accumulation':('svy',['i[x b][u[e[v x][v x]]]',identity,identity,constant(1),literal(0)],False),
        'linear_error_fixed_constant':('svx',[domain,'i[x b][k ad[n p d b v x]]','i[x b][k ad[n p c b v x]]',identity,literal(0),literal(1),literal(1)],True),
        'negative_error_two_sided':('svx',[domain,identity,'i[x b][k ad[n p c b v x]]',identity,literal(0),literal(1),literal(1)],True),
        'constant_too_small':('svx',[domain,'i[x b][k ad[n p d b v x]]','i[x b][k ad[n p c b v x]]',identity,literal(0),literal(Fraction(1,2)),literal(1)],False),
    }
    rows={}
    for name,(symbol,args,expected) in cases.items():
        row=verify(parse(text+'s['+k(symbol,*args)+'].'),MEANINGS,timeout_ms=15000)[0]
        if row['status']!=('valid' if expected else 'invalid'):raise ValueError('Asymptotic quantification differs: '+name+repr(row))
        rows[name]=row
    full=abstract(candidate(source_composed()[0],'q[k swc[]].'),ARITHMETIC|{'sky'})
    fixture=ConstructedCuts();model=guarded(full);fixture.arithmetic(model)
    try:values(full,model,('object',))
    except ValueError as error:
        if 'rational number domain' not in str(error):raise
    else:raise ValueError('Full asymptotic condition was finitely sampled')
    return {'cases':rows,'actual_definitions_specialized_to_rationals':True,'full_cut_condition_refuses_finite_sampling':True,'real_cut_big_o_not_machine_proved':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-3:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_exact','wrong_approximation','wrong_supplement'):
        model=guarded(doc);constants={'zim':'exact','zin':'approximation','zio':'supplement','rd':'author','rh':'scope','ri':'text'}
        for name,value in constants.items():model[name]=lambda value=value:value
        sym=lambda d:json.loads(d.syntax)['symbol']
        common=lambda a,s,c:(a,s,c)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        model.update(zc=lambda node,a,p,d,s,c:common(a,s,c) and (node,sym(p),sym(d))==('exact','swi','swg' if label=='wrong_exact' else 'swf'),
            uh=lambda node,a,d,s,c:common(a,s,c) and (node,sym(d))==('approximation','swh' if label=='wrong_approximation' else 'swg'),
            zfl=lambda node,a,p,d,s,c:common(a,s,c) and (node,sym(p),sym(d))==('supplement','swf','swg' if label=='wrong_supplement' else 'swh'))
        actual=values(doc,model,tuple(v for k,v in constants.items() if k!='ri'))
        expected=[label not in ('wrong_author','wrong_scope','wrong_context',bad) for bad in ('wrong_exact','wrong_approximation','wrong_supplement')]
        if actual!=expected:raise ValueError('Clock delay attribution differs: '+label)
        rows[label]=actual
    return rows


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned delay source differs')
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0125');names=['svq','svp','swd','swf','svy','swc','swg']
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Clock delay unit differs')
    rows=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=0,end=len(unit['text']),source=unit['text'],definitions=names,status='partial_explicit_reading',full_semantic_equivalence=False)]
    for mid in unit['math_ids']:
        item=next(m for m in artifact['math'] if m['id']==mid)
        if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Clock delay math differs')
        rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id=mid,math_sha256=item['sha256'],definitions=names,status='partial',full_semantic_equivalence=False))
    return {'segments':rows,'facsimile_checked':False,'verified_full_units':0,'explicit_remainder_constants_are_supplement':True,'seconds_realization_unfinished':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored clock delay differs')
        if json.loads((ROOT/('data/'+basis['document'].split('/')[-1].replace('.noema','-basis-v1.json'))).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored delay basis differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Clock delay roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/clock-delay-basis-v1.json','data/einstein-clock-delay-basis-v1.json',
        'examples/v014/origin-clock.noema','examples/v014/einstein-origin-clock.noema','scripts/check_origin_clock.py',
        'scripts/compose_clock_delay.py','scripts/check_clock_delay.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'reports/written-units-v1.json','artifacts/written-units-v1/einstein-1905.json',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py','noema/rational_proofs.py']
    text=source_composed()[0];previous=(ROOT/'examples/v014/einstein-origin-clock.noema').read_text(encoding='utf-8')
    return {'status':'partial_clock_delay_seconds_and_fourth_order_approximation','documents':documents,
        'polynomial_lemmas':polynomial_checks(),'approximation':approximation_checks(),'intervals':interval_checks(),
        'asymptotics':asymptotic_checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Clock delay report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Clock delay seconds, interval readings and quantified approximation checked')


if __name__=='__main__':main()
