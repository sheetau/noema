"""Check exact equation answers, excess solutions and nonfactive task attribution."""
import argparse
import hashlib
import json

from noema.finite_semantics import FunctionValue, SequenceValue
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.semantics import SemanticError
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded, callbacks
from scripts.check_tau_differential import ARITHMETIC, ConstructedCuts
from scripts.check_transverse_time import square_root
from scripts.check_moving_light_trip import literal
from scripts.compose_motion_question import ROOT, CUT, SYSTEM, generic_composed, source_composed

REPORT=ROOT/'reports/motion-question-v1.json'


def selector_checks():
    text=generic_composed()[0]+'r ja[] '+CUT+'.r jb[] '+CUT+'.'
    rows={}
    for side in (False,True):
        for bound in (-3,-2,0,3,4):
            truth='e[n p a b][n p a b]';choice=truth if side else 'u['+truth+']'
            doc=parse(text+'q[c[k szi['+choice+' k ja[] k jb[]]]['+literal(bound)+']].')
            fixture=ConstructedCuts();model=guarded(doc);model.update(ja=lambda:fixture.make(-2),jb=lambda:fixture.make(3))
            actual=values(doc,model,('object',));expected=bound<(-2 if side else 3)
            if actual!=[expected]:raise ValueError('Equation side selection differs')
            rows[str(side)+':'+str(bound)]=actual
    return {'cases':rows,'selected_predicate_membership_only':True}


def generic_checks():
    text=generic_composed()[0]+'''r ja[a] c.r jb[a] c.r jc[] h[h[b] c] c.r jd[] h[h[b] c h[b] c] c.'''
    text+='r je[] '+SYSTEM+'.q[k szb[k je[] p ja p jb k jc[] k jd[]]].q[h[k szh[p ja p jb k jc[] k jd[]]][k je[]]].'
    doc=parse(text);element=next(d['result']['element'] for d in doc['declarations'] if d['name']=='je')
    domain=('small','large','alias','wrong','outside');coords={'small':(2,3,6),'large':(4,5,20),'alias':(2,3,6),'wrong':(2,3,7),'outside':(9,9,0)}
    rows={}
    for label in ('exact_area','reordered','duplicate','empty_equations','extra_solution','excluded_target','invalid_side','empty_scope','empty_target','missing_target','outside_scope_irrelevant'):
        fixture=ConstructedCuts();model=guarded(doc);indices=[0,1]
        if label=='reordered':indices.reverse()
        if label=='duplicate':indices.append(0)
        if label=='empty_equations':indices=[]
        def term(index,first,second,left):
            if first!=second:raise ValueError('One-record equation received different records')
            a,b,area=coords[first]
            if label=='invalid_side' and not left:return fixture.make(100001)
            if label=='extra_solution':return fixture.make(0)
            if label=='excluded_target' and first=='large':return fixture.make(int(left))
            if index==0:return fixture.make(a*b if left else area)
            return fixture.make(0)  # An additional redundant equation.
        items=tuple(FunctionValue(tuple(element['parameters']),element['result'],lambda a,b,left,index=index:term(index,a,b,left)) for index in indices)
        sequence=SequenceValue(items,json.dumps(element,sort_keys=True,separators=(',',':')))
        model.update(ja=lambda record:record!='outside' and label!='empty_scope',
            jb=lambda record:record in ('small','large','alias') and label!='empty_target' and not(label=='missing_target' and record=='large') or (label=='outside_scope_irrelevant' and record=='outside'),je=lambda:sequence)
        callbacks(doc,model,{'jc':lambda cut:abs(fixture.read(cut))<100000,'jd':lambda a,b:fixture.read(a)==fixture.read(b)})
        actual=values(doc,model,domain);expected=label in ('exact_area','reordered','duplicate','outside_scope_irrelevant')
        if actual!=[expected]*2:raise ValueError('Equation-description question differs: '+label+repr(actual))
        rows[label]=actual
    try:
        values(parse(generic_composed()[0]+'r ja[a] c.r jb[a] c.r jc[] h[h[b] c] c.r jd[] h[h[b] c h[b] c] c.q[k szh[p ja p jb k jc[] k jd[]]].'),
            {k:v for k,v in model.items() if k!='je'},domain)
    except SemanticError as error:
        if 'unbounded sequence domain' not in str(error):raise
    else:raise ValueError('Unbounded equation answers were enumerated')
    return {'cases':rows,'separate_topic':'rectangle area records','explicit_finite_scope':True,'unbounded_answer_enumeration_rejected':True}


def source_checks():
    query='r ja[] a.q[k szd[k szf[]]].q[h[k sze[]][k szf[]]].q[t[k szg[]][k ri[]]].q[t[k syz[]][k ri[]]].q[k szc[k zkb[] k ra[] k zke[] k ja[]]].'
    doc=abstract(candidate(source_composed()[0],query),ARITHMETIC|{'sky','shd','szi'});rows={}
    coords={'r0':(0,0,0,0),'r1':(25,10,0,7),'r2':(50,20,0,14),'alias':(25,10,0,7),
        'badx':(26,10,0,7),'bady':(25,11,0,7),'badz':(25,10,1,7)}
    domain=tuple(coords)+('e0','e1','e2','point','otherpoint','rest','moving','x','y','z','t','scope','author','question')
    for label in ('baseline','value_alias','excess_solution','missing_record','invalid_record','off_curve_event',
        'wrong_point','wrong_frame','wrong_setting','empty_history','incorrect_component','unselected_event'):
        fixture=ConstructedCuts();c=fixture.make;n=fixture.read;model=guarded(doc);fixture.arithmetic(model)
        model['ba']=lambda cut:abs(n(cut))<100000
        charts={'e0':'r0','e1':'r1','e2':'badx' if label=='off_curve_event' else 'r2'}
        if label=='missing_record':del charts['e2']
        for symbol,value in {'zkb':'point','zke':'motion','ra':'moving' if label=='wrong_frame' else 'rest','zbm':'moving','yn':'x','yo':'y','yp':'z','zc7':'t','ri':'text','ja':'alias' if label=='value_alias' else 'r1'}.items():model[symbol]=lambda value=value:value
        model.update(tc=lambda:c(5),zb7=lambda:c(3),zkc=lambda:c(2 if label=='incorrect_component' else 1),zkd=lambda:c(2),
            sky=lambda cut:square_root(fixture,cut),szi=lambda choice,left,right:left if choice else right,
            zka=lambda point,event,setting:point==('otherpoint' if label=='wrong_point' else 'point') and setting==('other' if label=='wrong_setting' else 'motion') and event in ('e0','e1','e2') and label!='empty_history' and not(label=='excess_solution' and event=='e2'),
            zc4=lambda event:event in ('e0','e1','e2') and not(label=='unselected_event' and event=='e2'),
            zc5=lambda record:record in coords and not(label=='invalid_record' and record=='r2'),
            zc6=lambda record,role:c(coords.get(record,(0,0,0,0))[('x','y','z','t').index(role)] if role in ('x','y','z','t') else 0),
            shd=lambda event,record,frame,setting:(frame,setting)==('rest','motion') and charts.get(event)==record)
        actual=values(doc,model,domain)
        exact=label in ('baseline','value_alias')
        subset=label in ('baseline','value_alias','excess_solution')
        membership=label not in ('wrong_point','wrong_frame','wrong_setting','empty_history')
        expected=[exact,exact,exact,subset,membership]
        if actual!=expected:raise ValueError('Motion answer differs: '+label+repr(actual)+' expected '+repr(expected))
        rows[label]=actual
    return {'cases':rows,'candidate_equations_evaluated_from_noema':True,'selector_and_arithmetic_are_explicit_oracles':True,
        'subset_does_not_imply_exact_answer':True,'finite_coordinate_scope_only':True,'all_real_times_covered':False}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-1:];rows={}
    for label in ('baseline','wrong_author','wrong_question','wrong_scope','wrong_context'):
        model=guarded(doc)
        for symbol,value in {'zki':'question','rd':'author','zkf':'scope','ri':'text'}.items():model[symbol]=lambda value=value:value
        model['zdc']=lambda node,author,question,scope,context:(node,author,json.loads(question.syntax)['symbol'],scope,context)==('question','other' if label=='wrong_author' else 'author','shk' if label=='wrong_question' else 'sze','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        actual=values(doc,model,('question','author','scope','other'))
        if actual!=[label=='baseline']:raise ValueError('Motion question attribution differs')
        rows[label]=actual
    return {'cases':rows,'question_and_candidate_not_executed_by_attribution':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';artifact=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Pinned motion question source differs')
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0133');end=unit['text'].index(' Führt man')
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Motion question text differs')
    item=next(m for m in artifact['math'] if m['id']=='M0249')
    if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Motion question frame differs')
    common=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=['szc','szj','szd','sze'],status='partial_explicit_reading',full_semantic_equivalence=False)
    return {'segments':[dict(common,start=0,end=end,source=unit['text'][:end]),dict(common,math_id=item['id'],math_sha256=item['sha256'])],
        'facsimile_checked':False,'verified_full_units':0,'question_added_without_claiming_it_solved':True}


def build_report():
    documents={}
    for compose,basispath in ((generic_composed,'data/equation-description-basis-v1.json'),(source_composed,'data/motion-question-basis-v1.json')):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored question differs')
        if json.loads((ROOT/basispath).read_text(encoding='utf-8'))!=basis:raise ValueError('Question basis differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Question roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/equation-description-basis-v1.json','data/motion-question-basis-v1.json',
        'examples/v014/einstein-velocity-components.noema','scripts/compose_motion_question.py','scripts/check_motion_question.py',
        'scripts/compose_coordinate_correspondence.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'noema/discourse.py','noema/finite_semantics.py','reports/written-units-v1.json','artifacts/written-units-v1/einstein-1905.json']
    text=source_composed()[0]
    return {'status':'partial_motion_question_and_exact_equation_answers','documents':documents,'selector':selector_checks(),
        'generic_equations':generic_checks(),'motion_answers':source_checks(),'attribution':attribution_checks(),'alignment':alignment(),
        'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/'examples/v014/einstein-velocity-components.noema').read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Motion question report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Exact equation answers, excess solutions and open motion question checked')


if __name__=='__main__':main()
