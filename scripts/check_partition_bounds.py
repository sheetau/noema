"""Check quadratic error induction against the actual tagged-sum fold."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue,SequenceValue,evaluate_document
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode,decode
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_integrals import cell_value,CELL,ARITHMETIC
from scripts.check_plane_waveforms import setup,evaluate,OPS
from scripts.check_real_products import MEANINGS,assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k,op,both,v
from scripts.compose_partition_bounds import ROOT,PARENT,BUILDERS,CUT,PARTITION,generic_composed,source_composed,core_composed
from scripts.compose_wave_amplitudes import params

REPORT=ROOT/'reports/partition-bounds-v1.json'


def fold_shape_checks(doc):
    declarations={d['name']:d for d in doc['declarations']}
    original=parse((ROOT/'examples/v014/integrals.noema').read_text(encoding='utf-8'))
    for d in original['declarations']:
        if d['name'] in ('ma','mb','mc','md') and d!=declarations[d['name']]:
            raise ValueError('Induction requires the preserved tagged partition and sum fold: '+d['name'])
    geometry=parse((ROOT/'examples/v014/geometric-volumes.noema').read_text(encoding='utf-8'))
    for d in geometry['declarations']:
        if d['name'] in ('seec','seef') and d!=declarations[d['name']]:
            raise ValueError('Induction requires the preserved section polynomial and primitive: '+d['name'])
    # This independent template binds the generic sum to the exact polynomial
    # whose cell and prefix assertions are checked below.
    template='''d seek[partition j[h[b] b] pi b radius b factor b] b[
k md[v partition i[x b][k seec[v pi v radius v factor v x]]]].'''
    stripped={**doc,'declarations':[d for d in doc['declarations'] if d['name']!='seek'],'statements':[]}
    expected=parse(format_graph(stripped,'compact')+template)
    expected=next(d for d in expected['declarations'] if d['name']=='seek')
    if declarations['seek']!=expected:raise ValueError('Quadratic fold does not use the certified profile')
    L,H,B,delta,pi=map(v,('lower','upper','bound','delta','pi'))
    le=lambda a,b:op('u',k('aa',b,a))
    domain=both(le(literal(0),pi),k('aa',literal(0),B),k('aa',literal(0),delta),
        le(k('ac',B),L),le(H,B),k('mb',v('partition'),L,H),k('mc',v('partition'),delta))
    template='d seel[partition j[h[b] b] '+params('pi radius factor lower upper bound delta','b')+'] c['+domain+'].'
    stripped={**doc,'declarations':[d for d in doc['declarations'] if d['name']!='seel'],'statements':[]}
    expected=next(d for d in parse(format_graph(stripped,'compact')+template)['declarations'] if d['name']=='seel')
    if declarations['seel']!=expected:raise ValueError('Partition acceptance omitted a required hypothesis')
    return {'preserved_partition_and_fold_definitions':['ma','mb','mc','md'],
        'sum_uses_certified_profile':True,'acceptance_binds_all_induction_hypotheses':True,
        'section_polynomial_and_primitive_preserved':True,
        'induction_rule':'empty prefix plus one valid connected cell extends the same numeric fold'}


def polynomial_checks(doc=None):
    doc=doc or parse(generic_composed()[0])
    shape=fold_shape_checks(doc)
    base=format_graph({**doc,'statements':[]},'compact')
    mul=lambda a,b:k('ad',a,b)
    add=lambda a,b:k('ab',a,b)
    sub=lambda a,b:add(a,k('ac',b))
    le=lambda a,b:op('u',k('aa',b,a))
    zero,one,two=literal(0),literal(1),literal(2)
    pi,R,D,B,delta,start,left,right,tag,total=map(v,'pi radius factor bound delta start left right tag total'.split())
    K=k('seeg',pi,D,B)
    width=sub(right,left)
    err=k('seeh',pi,R,D,left,right,tag)
    conditions=k('seej',pi,R,D,B,delta,left,right,tag)
    budget=mul(K,mul(delta,width))
    prefix=k('seei',pi,R,D,start,left,B,delta,total)
    nexttotal=add(total,mul(width,k('seec',pi,R,D,tag)))
    epsilon,length,coefficient=map(v,('epsilon','length','coefficient'))
    error,bound,step_error,step_bound=map(v,('error','budget','steperror','stepbudget'))
    claims={
        'error_coefficient_formula':assertion('pi factor bound',op('e',K,mul(two,mul(pi,mul(mul(D,D),B))))),
        'nonnegative_error_coefficient':assertion('pi factor bound',op('y',both(le(zero,pi),le(zero,B)),le(zero,K))),
        'accepted_cell_supplies_step_hypotheses':assertion('pi radius factor bound delta left right tag',op('y',both(
            le(zero,pi),k('aa',zero,B),k('aa',zero,delta),le(k('ac',B),left),k('aa',left,right),le(right,B),
            le(left,tag),le(tag,right),k('aa',width,delta)),conditions)),
        'cell_error_bounded_by_squared_width':assertion('pi radius factor bound delta left right tag',op('y',conditions,
            both(le(k('ac',mul(K,mul(width,width))),err),le(err,mul(K,mul(width,width)))))),
        'cell_error_bounded_by_mesh':assertion('pi radius factor bound delta left right tag',op('y',conditions,
            both(le(k('ac',budget),err),le(err,budget)))),
        'prefix_base_case':assertion('pi radius factor bound delta start',op('y',both(le(zero,pi),k('aa',zero,B),
            k('aa',zero,delta),le(k('ac',B),start),le(start,B)),k('seei',pi,R,D,start,start,B,delta,zero))),
        'error_intervals_add':assertion('error budget steperror stepbudget',op('y',both(le(zero,bound),le(zero,step_bound),
            le(k('ac',bound),error),le(error,bound),le(k('ac',step_bound),step_error),le(step_error,step_bound)),
            both(le(k('ac',add(bound,step_bound)),add(error,step_error)),le(add(error,step_error),add(bound,step_bound))))),
        'prefix_extension':assertion('pi radius factor bound delta start left right tag total',op('y',both(prefix,conditions),
            k('seei',pi,R,D,start,right,B,delta,nexttotal))),
        'prefix_invariant_implies_actual_error_bound':assertion('pi radius factor bound delta start left total',op('y',prefix,
            both(le(k('ac',mul(K,mul(delta,sub(left,start)))),
                sub(total,sub(k('seef',pi,R,D,left),k('seef',pi,R,D,start)))),
                le(sub(total,sub(k('seef',pi,R,D,left),k('seef',pi,R,D,start))),mul(K,mul(delta,sub(left,start))))))),
        'positive_mesh_choice_and_strict_error':assertion('epsilon length coefficient delta',op('y',both(
            k('aa',zero,epsilon),k('aa',zero,length),le(zero,coefficient),
            op('e',mul(two,mul(add(coefficient,one),mul(length,delta))),epsilon)),
            both(k('aa',zero,delta),k('aa',mul(coefficient,mul(length,delta)),epsilon)))),
        'zero_coefficient_still_has_positive_mesh':assertion('',both(k('aa',zero,literal(F(1,8))),
            op('e',mul(two,mul(add(zero,one),mul(literal(4),literal(F(1,8))))),one))),
        'single_tag_exact_integral_counterexample':assertion('',op('e',k('seeh',*(literal(n) for n in (1,1,1,0,1,0))),zero)),
        'missing_factor_in_bound_counterexample':assertion('',le(k('seeh',*(literal(n) for n in (1,1,10,0,1,0))),literal(2))),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),MEANINGS,timeout_ms=30000)[0]
        if result['status']!=('invalid' if name.endswith('counterexample') else 'valid'):
            raise ValueError('Partition induction obligation differs: '+name+repr(result))
        rows[name]=result
    return {'claims':rows,'fold_shape':shape,'finite_sequence_induction':{
        'base_obligation':'prefix_base_case','step_obligation':'prefix_extension',
        'hypothesis_bridge':'accepted_cell_supplies_step_hypotheses','conclusion_bridge':'prefix_invariant_implies_actual_error_bound',
        'endpoint_condition':'mb requires the connected prefix to finish at the requested upper endpoint',
        'conclusion':'For every finite accepted rational tagged partition, |sum - primitive endpoint difference| <= K*delta*(upper-lower).',
        'trusted_rule':'structural induction for the language finite fold and ordered partition semantics',
        'scope':'rational values and arbitrary finite partition length',
        'not_proved':['all Dedekind-cut field laws','existence of a fine real partition','Archimedean property','complete Riemann integral equivalence']}}


def finite_checks():
    text=generic_composed()[0]
    args='k ja[] k jb[] k jc[] k jd[] k je[] k jf[] k jg[]'
    query='''r zp[] j[h[b] b].r ja[] b.r jb[] b.r jc[] b.r jd[] b.r je[] b.r jf[] b.r jg[] b.
q[k seel[k zp[] '''+args+''']].
q[k seei['''+args+''' k seek[k zp[] k ja[] k jb[] k jc[]]]].'''
    doc=parse(text+query)
    def run(cells,pi=F(3),R=F(2),D=F(1),lower=F(-2),upper=F(2),B=F(2),delta=F(5)):
        model={**ARITHMETIC,'zp':lambda:SequenceValue(tuple(cell_value(c) for c in cells),json.dumps(CELL,sort_keys=True,separators=(',',':')))}
        for name,value in zip(('ja','jb','jc','jd','je','jf','jg'),(pi,R,D,lower,upper,B,delta),strict=True):model[name]=lambda value=value:F(value)
        return [row['value'] for row in evaluate_document(doc,individuals=('object',),situations=('now',),primitives=model,max_steps=5_000_000)]
    rows=[]
    for size,tagoffset,pi,D in product((1,2,4,8),(F(0),F(1,2),F(1)),(F(0),F(3)),(F(0),F(1),F(2))):
        width=F(4,size)
        cells=tuple((F(-2)+i*width,F(-2)+(i+1)*width,F(-2)+(i+tagoffset)*width) for i in range(size))
        actual=run(cells,pi=pi,D=D,delta=2*width)
        if actual!=[True,True]:raise ValueError('Finite tagged bound differs')
        rows.append({'cells':size,'tag':str(tagoffset),'pi_coefficient':str(pi),'factor':str(D),'results':actual})
    contrasts={}
    for label,cells,options in (
        ('gap',((-2,-1,-2),(0,2,1)),{}),('overlap',((-2,1,0),(0,2,1)),{}),
        ('reversed',((0,2,1),(-2,0,-1)),{}),('outside_tag',((-2,2,3),),{}),
        ('missing_end',((-2,1,0),),{}),('empty',(),{}),
        ('mesh_equal_width',((-2,2,0),),{'delta':4}),('zero_bound',((-2,2,0),),{'B':0}),
        ('negative_coefficient',((-2,2,0),),{'pi':-3})):
        actual=run(cells,**options)
        if actual[0]:raise ValueError('Invalid partition admitted: '+label)
        contrasts[label]=actual
    return {'cases':rows,'contrasts':contrasts,'samples_supplement_induction_not_replace_it':True}


def real_binding_checks(texts):
    names=tuple('j'+n for n in 'abcdefg')
    query=''.join('r '+n+'[] '+CUT+'.' for n in names)+'q['+k('sedx',*map(k,names))+'].'
    docs=[abstract(candidate(text,query),OPS|{'sedv'}) for text in texts]
    rows=[]
    for pi,D,epsilon,known in product((0,3),(0,1,2),(F(1,10),F(1)),(False,True)):
        numbers=(pi,2,D,-2,2,2,epsilon)
        expected_delta=epsilon/(2*(2*pi*D*D*2+1)*4)
        results=[]
        for doc in docs:
            fixture,model=setup(doc);read,make=fixture.read,fixture.make
            for name,value in zip(names,numbers,strict=True):model[name]=lambda value=value:make(value)
            model['sedv']=lambda *args:known and tuple(read(x) for x in args)==(*map(F,numbers[:6]),expected_delta)
            results.append(evaluate(doc,model))
        if results!=[[known]]*2:raise ValueError('Explicit mesh or global premise binding differs')
        rows.append({'pi_coefficient':pi,'factor':D,'epsilon':str(epsilon),'delta':str(expected_delta),
            'global_bound_assumed':known,'results':results[0]})
    return {'cases':rows,'global_real_partition_bound_is_an_explicit_oracle':True,'standalone_agrees':True}


def real_sum_checks(texts):
    names=tuple('j'+n for n in 'abcdefg')
    query='r jz[] '+PARTITION+'.'+''.join('r '+n+'[] '+CUT+'.' for n in names)+'q['+k('sedu',k('jz'),*map(k,names))+'].'
    docs=[abstract(candidate(text,query),OPS|{'sedb','sedc'}) for text in texts]
    # The sum itself and polynomial stay as Noema definitions. Only concrete
    # record validity/chain/mesh checks use exact registered rational values.
    def run(cells,pi=3,D=1,delta=2):
        observed=[]
        for doc in docs:
            fixture,model=setup(doc);make,read=fixture.make,fixture.read
            zp=next(d for d in doc['declarations'] if d['name']=='jz')['result']
            cell_sort=zp['element'] if 'element' in zp else zp['item']
            record_sort=cell_sort['result']
            def record(values):
                values=tuple(map(F,values))
                return FunctionValue(('number',),record_sort,lambda index:make(values[int(index)] if index in (0,1,2) else 0))
            sequence=SequenceValue(tuple(record(cell) for cell in cells),json.dumps(cell_sort,sort_keys=True,separators=(',',':')))
            model['jz']=lambda:sequence
            for name,value in zip(names,(pi,2,D,-2,2,2,delta),strict=True):model[name]=lambda value=value:make(value)
            def tuples(partition):return [tuple(read(cell(F(i))) for i in (0,1,2)) for cell in partition.items]
            def valid_cell(cell):
                left,right,tag=cell
                return left<right and left<=tag<=right
            def chain(partition,lower,upper):
                rows=tuples(partition)
                return bool(rows) and read(lower)<read(upper) and rows[0][0]==read(lower) and rows[-1][1]==read(upper) and all(
                    valid_cell(row) for row in rows) and all(first[1]==second[0] for first,second in zip(rows,rows[1:]))
            model['sedb']=chain
            model['sedc']=lambda partition,bound:read(bound)>0 and all(valid_cell(row) and row[1]-row[0]<read(bound) for row in tuples(partition))
            observed.append(evaluate(doc,model))
        if observed[0]!=observed[1]:raise ValueError('Real tagged sums differ in standalone library')
        return observed[0]
    rows=[]
    for pi,D,tag in product((0,3),(0,1,2),(F(0),F(1,2),F(1))):
        cells=tuple((i,i+1,F(i)+tag) for i in (-2,-1,0,1))
        actual=run(cells,pi,D)
        if actual!=[True]:raise ValueError('Constructed-cut sum error differs')
        rows.append({'coefficient':pi,'factor':D,'tag':str(tag),'results':actual})
    contrasts={}
    for name,cells,delta in (('empty',(),2),('gap',((-2,-1,-2),(0,2,1)),3),
        ('outside_tag',((-2,2,3),),5),('equal_mesh',((-2,2,0),),4)):
        actual=run(cells,delta=delta)
        if actual!=[False]:raise ValueError('Invalid constructed-cut partition accepted')
        contrasts[name]=actual
    return {'cases':rows,'contrasts':contrasts,'actual_noema_sum_and_polynomial_evaluated':True,
        'partition_validation_uses_exact_registered_rational_cuts':True,'standalone_agrees':True}


def refusals(text):
    doc=candidate(text,'q['+k('sedv',*(k('bb',literal(x)) for x in (3,2,1,-2,2,2,1)))+'].' )
    # Arithmetic is abstracted, but the universal finite-partition quantifier is not.
    doc=abstract(doc,OPS);fixture,model=setup(doc)
    try:evaluate(doc,model)
    except ValueError as exc:
        if 'Cannot finitely quantify' not in str(exc):raise
        return {'refused':True,'reason':str(exc)}
    raise ValueError('All partitions were certified with a finite domain')


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    item=next(m for m in source['math'] if m['id']=='M0362');unit=next(u for u in source['units'] if 'M0362' in u['math_ids'])
    return {'segments':[{'unit':unit['id'],'unit_sha256':unit['text_sha256'],'math_id':'M0362','math_sha256':item['sha256'],
        'definitions':['seds','sedt','sedu','sedv','sedw','sedx'],'status':'partial',
        'review_ja':'体積比を支える断面多項式のタグ付き和に、任意の有限分割の誤差評価と正の細かさの構成を追加した。実切断全域の積分法則・測度・物理的意味の確認は未完。'}],
        'new_source_ranges':False,'semantic_completion':False}


def build_report():
    texts=[];documents={};sizes={}
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored partition bounds differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Partition bound roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]={'characters':len(text),'statements':len(doc['statements'])}
    source,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if source['declarations'][:len(parent['declarations'])]!=parent['declarations'] or source['statements']!=parent['statements']:raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'examples/v014/integrals.noema','scripts/compose_partition_bounds.py','scripts/check_partition_bounds.py',
        'scripts/check_integrals.py','scripts/check_plane_waveforms.py','scripts/check_tau_differential.py',
        'noema/polynomial_proofs.py','noema/finite_semantics.py','noema/extraction.py','artifacts/written-units-v1/einstein-1905.json']
    return json.loads(json.dumps({'status':'partial_partition_error_induction_not_full_real_integral_proof',
        'documents':documents,'sizes':sizes,'induction':polynomial_checks(),'finite':finite_checks(),
        'real_bindings':real_binding_checks(texts[1:]),'real_sums':real_sum_checks(texts[1:]),
        'unbounded_refusal':refusals(texts[2]),'alignment':alignment(),
        'roundtrips':True,'parent_preserved':True,'new_primitives':0,'new_author_statements':0,
        'verified_full_units':{'kant-1784':0,'einstein-1905':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}},ensure_ascii=False))


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Partition bound report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Quadratic cell and prefix induction obligations and explicit mesh checked')


if __name__=='__main__':main()
