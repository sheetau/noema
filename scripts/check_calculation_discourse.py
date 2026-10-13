"""Check linked descriptions, same-chain workload and non-factive appraisals."""
import argparse
from fractions import Fraction as F
import hashlib
import json

from noema.finite_semantics import FunctionValue
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from noema.semantics import SemanticError
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_real_products import MEANINGS as ARITHMETIC_MEANINGS, assertion
from scripts.check_moving_light_trip import literal
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_angle_composition import model_arithmetic
from scripts.compose_calculation_discourse import (
    ROOT, CUT, STEP, STEPS, RULE, COST, LEFT, RIGHT, TRUE, generic_composed, composed, step, k, v, op, both,
)

REPORT=ROOT/'reports/calculation-discourse-v1.json'


def symbol(description):
    return json.loads(description.syntax)['symbol']


def pair(value):
    selector=parse('n:r ja['+STEP+'] c.')['declarations'][0]['parameters'][0]['parameters'][0]
    return tuple(symbol(value(FunctionValue(tuple(selector['parameters']),selector['result'],
        lambda left,right,index=index:(left,right)[index]))) for index in (0,1))


def sequence(pairs):
    return 'l['+STEP+']['+' '.join(step('r[k '+a+'[]]','r[k '+b+'[]]') for a,b in pairs)+']'


def chain_checks():
    prefix=generic_composed()[0]+'r ja[] e.r jb[] e.r jc[] e.r jd[] e.r je[i[e] i[e]] c.r jf['+STEP+'] b.r jg[b] c.'
    cases={
        'baseline':([('ja','jb'),('jb','jc')],3,{},True,True),
        'empty':([],3,{},False,False),
        'reversed_order':([('jb','jc'),('ja','jb')],3,{},False,False),
        'broken_chain':([('ja','jb'),('jd','jc')],3,{},False,False),
        'wrong_start':([('jd','jb'),('jb','jc')],3,{},False,False),
        'wrong_end':([('ja','jb'),('jb','jd')],3,{},False,False),
        'unapproved_transition':([('ja','jc')],3,{},False,False),
        'expensive_valid_chain':([('ja','jb'),('jb','jc')],2,{},True,False),
        'negative_cost':([('ja','jb'),('jb','jc')],3,{('ja','jb'):-1},True,False),
        'repeated_loop_is_counted':([('ja','jb'),('jb','jb'),('jb','jb'),('jb','jc')],3,{},True,False),
        'same_loop_with_larger_budget':([('ja','jb'),('jb','jb'),('jb','jb'),('jb','jc')],5,{},True,True),
        'cheap_other_chain_cannot_replace_cost':([('ja','jb'),('jb','jc')],0,{('jd','jc'):0},True,False),
        'twenty_repeated_steps':([('ja','jb')]+[('jb','jb')]*20+[('jb','jc')],23,{},True,True),
    }
    rows={};allowed={('ja','jb'),('jb','jc'),('jb','jb'),('jd','jc')}
    for label,(pairs,budget,changed,linked,easy) in cases.items():
        seq=sequence(pairs);arguments=seq+' r[k ja[]] r[k jc[]] p je'
        costs={('ja','jb'):1,('jb','jc'):2,('jb','jb'):1,('jd','jc'):1}|changed
        total=F(sum(costs.get(p,1) for p in pairs))
        doc=parse(prefix+'q[k s2w['+arguments+']].q[k s2y['+arguments+' p jf p jg]].q[e[k s2x['+seq+' p jf]]['+literal(total)+']].')
        model=guarded(doc)
        model.update(aa=lambda a,b:a<b,ab=lambda a,b:a+b,je=lambda a,b:(symbol(a),symbol(b)) in allowed,
            jf=lambda item:F(costs.get(pair(item),1)),jg=lambda cost:cost<=budget)
        actual=values(doc,model,('object',))
        expected=[linked,easy,True]
        if actual!=expected:raise ValueError('Chain or burden differs: '+label+repr(actual))
        rows[label]={'linked':actual[0],'low_burden':actual[1],'cost_equals_independent_sum':actual[2],'cost':str(total)}
    return {'cases':rows,'steps_built_in_noema_without_new_pair_primitive':True,
        'quoted_contents_never_evaluated':True,'allowed_rewrite_soundness_not_assumed':True}


def appraisal_checks():
    prefix=generic_composed()[0]+'''r ja[] e.r jb[] e.r jc[] d.r jd[i[e] d] b.r je[b d] c.
q[k s2z[r[k ja[]] k jc[] p jd p je]].q[k s2z[r[k jb[]] k jc[] p jd p je]].'''
    doc=parse(prefix);rows={}
    for label in ('baseline','changed_description','wrong_context','low_value','different_standard'):
        model=guarded(doc)
        model.update(aa=lambda a,b:a<b,ab=lambda a,b:a+b,jc=lambda:'text',
            jd=lambda subject,context:F(8 if symbol(subject)==('jb' if label=='changed_description' else 'ja') and
                context==('other' if label=='wrong_context' else 'text') and label!='low_value' else 2),
            je=lambda degree,context:degree>=5 and context==('other' if label=='different_standard' else 'text'))
        actual=values(doc,model,('object',));expected=[label=='baseline',label=='changed_description']
        if actual!=expected:raise ValueError('Description-sensitive appraisal differs')
        rows[label]=actual
    return {'cases':rows,'truth_and_actual_attention_not_inferred':True}


def source_chain_checks():
    text=composed()[0];rows={}
    for label in ('baseline','wrong_premise','wrong_conclusion','wrong_transition','high_burden','wrong_cost_context','wrong_standard_context'):
        doc=candidate(text,'q[t[k s3d[]][k ri[]]].')
        before='s2v' if label=='wrong_premise' else 's3c';after='s3b' if label=='wrong_conclusion' else 's2v'
        replacement=parse('n:r s3c[] e.r s2v[] e.r s3b[] e.d zkz[] '+STEPS+'['+sequence([(before,after)])+'].')['declarations'][-1]
        doc['declarations']=[d for d in doc['declarations'] if d['name']!='zkz']
        position=next(i for i,d in enumerate(doc['declarations']) if d['name']=='s3d')
        doc['declarations'].insert(position,replacement)
        model=guarded(doc);model.update(aa=lambda a,b:a<b,ab=lambda a,b:a+b,ri=lambda:'text',
            zla=lambda a,b,context:(symbol(a),symbol(b),context)==('s3c','s3b' if label=='wrong_transition' else 's2v','text'),
            zlb=lambda item,context:F(8 if label=='high_burden' else 2),
            zlc=lambda cost,context:cost<=3 and context==('other' if label=='wrong_standard_context' else 'text'))
        if label=='wrong_cost_context':model['zlb']=lambda item,context:F(2 if context=='other' else 8)
        actual=values(doc,model,('object',))
        if actual!=[label=='baseline']:raise ValueError('Source calculation assessment differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'one_step_fixture_not_attributed_as_historical_procedure':True,
        'physical_premise_and_result_contents_not_evaluated':True}


def source_appraisal_checks():
    doc=candidate(composed()[0],'q[t[k s3e[]][k ri[]]].');rows={}
    for label in ('baseline','formula_instead_of_symmetry','wrong_context','low_value','high_standard'):
        model=guarded(doc);model.update(ri=lambda:'text',
            zld=lambda subject,context:F(8 if (symbol(subject),context)==('s2v' if label=='formula_instead_of_symmetry' else 's3b',
                'other' if label=='wrong_context' else 'text') and label!='low_value' else 2),
            zle=lambda value,context:value>=(9 if label=='high_standard' else 5) and context=='text')
        actual=values(doc,model,('object',))
        if actual!=[label=='baseline']:raise ValueError('Source attention assessment differs')
        rows[label]=actual
    return {'cases':rows,'actual_symmetry_and_attention_not_evaluated':True}


def symmetry_checks():
    text=composed()[0];V,s,W,c,h,r,U=map(v,('light','speed','moving','cosine','sine','radical','result'))
    zero=literal(0);claim=assertion('light speed moving cosine sine radical result',op('y',
        both(op('u',k('aa',s,zero)),op('u',k('aa',W,zero))),
        op('z',k('s2o',V,s,W,c,h,r,U),k('s2o',V,W,s,c,h,r,U))))
    doc=candidate(text,claim);doc['declarations']=[d for d in doc['declarations'] if d['name'] in {'aa','ab','ac','ad','szw','s2n','s2o'}]
    algebra=verify_universal(doc,ARITHMETIC_MEANINGS,timeout_ms=20000)[0]
    if algebra['status']!='valid':raise ValueError('Symmetric quotient algebra differs')
    query='q[t[k s3b[]][k ri[]]].';base=candidate(text,query)
    doc=abstract(base,ARITHMETIC|{'sjt','sky','s3a'});angle_type=next(d['result'] for d in doc['declarations'] if d['name']=='zkt')
    rows={}
    for label in ('baseline','opposite_direction','zero_light','negative_light'):
        fixture=ConstructedCuts();make=fixture.make;n=fixture.read;model=guarded(doc);model_arithmetic(fixture,model)
        light=0 if label=='zero_light' else -5 if label=='negative_light' else 5;cosine=-1 if label=='opposite_direction' else 1
        def sampled(relation,domain):
            for a,b in ((3,1),(1,3),(0,3),(-1,3),(3,-1),(128,1)):
                if domain(make(a),make(b))!=(0<=a<128 and 0<=b<128):raise ValueError('Symmetry domain changed')
            if light<=0:return True  # Separate source guards must reject it.
            for a,b in ((3,1),(1,3),(0,3),(3,3)):
                answer=F(abs(a+cosine*b),1)/(1+F(a*b*cosine,light*light))
                for result in (answer,answer+1):
                    expected=result==answer
                    if relation(make(a),make(b),make(result))!=expected or relation(make(b),make(a),make(result))!=expected:
                        raise ValueError('Source symmetry relation bindings differ')
            return True
        model.update(tc=lambda:make(light),ri=lambda:'text',s3a=sampled,
            zkt=lambda:FunctionValue(tuple(angle_type['parameters']),angle_type['result'],lambda choose:make(cosine if choose else 0)))
        actual=values(doc,model,('object',))
        if actual!=[light>0]:raise ValueError('Symmetry source guard differs')
        rows[label]=actual
    # The universal real-cut domain must not be replaced by sampled pairs.
    unbounded=abstract(candidate(text,query),ARITHMETIC|{'sjt','sky'})
    finite_model=guarded(unbounded);model_arithmetic(fixture,finite_model)
    finite_model.update(tc=lambda:make(5),ri=lambda:'text',zkt=lambda:FunctionValue(tuple(angle_type['parameters']),angle_type['result'],lambda choose:make(1 if choose else 0)))
    try:values(unbounded,finite_model,('object',))
    except SemanticError as error:
        if str(error)!='Cannot finitely quantify the rational number domain':raise
    else:raise ValueError('All-real symmetry was finitely enumerated')
    return {'rational_algebra':algebra,'finite_binding_cases':rows,
        'sampled_relation_callback_is_not_a_universal_proof':True,'unbounded_real_domain_enumeration_rejected':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-4:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','reversed_derivation','swapped_appraisals'):
        model=guarded(doc)
        for symbol_,value in {'zkx':'calculation','zky':'symmetry','rd':'author','zkf':'scope','ri':'text'}.items():model[symbol_]=lambda value=value:value
        def setting(author,scope,context):
            return (author,scope,context)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        def follows(node,author,before,after,scope,context):
            return setting(author,scope,context) and node=='calculation' and (symbol(before),symbol(after))==(('s2v','s3c') if label=='reversed_derivation' else ('s3c','s2v'))
        def claims(node,author,content,scope,context):
            accepted={'calculation':{'s3e'} if label=='swapped_appraisals' else {'s3d'},'symmetry':{'s3b','s3d'} if label=='swapped_appraisals' else {'s3b','s3e'}}
            return setting(author,scope,context) and symbol(content) in accepted[node]
        model.update(zc=follows,uh=claims);actual=values(doc,model,('calculation','symmetry','author','scope','other'))
        expected=[False]*4 if label.startswith('wrong_') else [label!='reversed_derivation',label!='swapped_appraisals',True,label!='swapped_appraisals']
        if actual!=expected:raise ValueError('Calculation attribution differs')
        rows[label]=actual
    return {'cases':rows,'quoted_derivation_and_appraisal_contents_not_evaluated':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Source inventory differs')
    rows=[]
    for index,defs in ((139,['s2w','s2y','s3c','s3d']),(141,['s2z','s3a','s3b','s3e'])):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Source text differs')
        start=unit['text'].index('Nach einfacher Rechnung') if index==139 else 0
        end=len(unit['text']) if index==139 else unit['text'].index(' Hat auch')
        common=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=defs,status='partial_explicit_reading',full_semantic_equivalence=False)
        rows.append(dict(common,start=start,end=end,source=unit['text'][start:end]))
        if index==141:
            for mid in ('M0258','M0259'):
                item=next(m for m in source['math'] if m['id']==mid)
                if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Source math differs')
                rows.append(dict(common,math_id=mid,math_sha256=item['sha256']))
    return {'segments':rows,'verified_full_units':0,'facsimile_checked':False,
        'low_burden_and_attention_value_are_explicit_partial_readings':True,
        'specific_calculation_steps_and_numeric_appraisals_not_supplied_by_source':True,
        'following_parallel_motion_clause_unwritten':True}


def build_report():
    documents={};paths=[];sizes={}
    for builder,name in ((generic_composed,'calculation-assessments'),(composed,'calculation-discourse')):
        text,basis=builder();doc=parse(text);basispath='data/'+name+'-basis-v1.json'
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/basispath).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored calculation artifacts differ')
        documents[basis['document']]=audit_basis(doc,basis);paths += [basis['document'],basispath];sizes[basis['document']]=len(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Calculation roundtrip differs')
    paths += ['scripts/compose_calculation_discourse.py','scripts/check_calculation_discourse.py','examples/v014/einstein-angle-composition.noema',
        'scripts/check_angle_composition.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'partial_linked_calculation_and_description_sensitive_symmetry_appraisal','documents':documents,
        'chains':chain_checks(),'appraisal':appraisal_checks(),'source_chains':source_chain_checks(),
        'source_appraisal':source_appraisal_checks(),'symmetry':symmetry_checks(),'attribution':attribution_checks(),'alignment':alignment(),
        'notation_size':{'documents':sizes,'source_added_characters':sizes['examples/v014/einstein-calculation-discourse.noema']-len((ROOT/'examples/v014/einstein-angle-composition.noema').read_text(encoding='utf-8'))},
        'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Calculation discourse report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Calculation chains, burden, symmetry and description-sensitive appraisal checked')


if __name__=='__main__':main()
