"""Check same-event pairing, complete tuples and exact equation solution sets."""
import argparse
import hashlib
import json

from noema.finite_semantics import FunctionValue, SequenceValue, evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, guarded, embedding
from scripts.check_rod_measurements import cut
from scripts.compose_coordinate_correspondence import ROOT, SIDE, SYSTEM, generic_composed, source_composed

REPORT=ROOT/'reports/coordinate-correspondence-v1.json'


def values(doc,model,domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,
        situations=('initial','motion','text','other'),primitives=model,max_steps=3_000_000,
        memoize_definitions=True,memoize_expressions=True)]


def abstract(doc,names):
    for i,d in enumerate(doc['declarations']):
        if d['name'] in names:
            doc['declarations'][i]={'kind':'primitive','name':d['name'],
                'parameters':[p['sort'] for p in d['parameters']],'result':d['result']}
    return doc


def chart_checks(source=False):
    if source:
        doc=abstract(candidate(source_composed()[0],'q[t[k shi[]][k ri[]]].'),{'shd','shh'})
    else:
        doc=parse(generic_composed()[0]+'''
r ja[a] c.r jb[a a] c.r jc[a a] c.r jd[a a] c.r je[a] c.r jf[a] c.r jg[a a] c.
r jh[] a.r ji[] a.r jj[] a.
q[k sgv[p ja p jb p jc p jd]].q[k sgw[p je p jf p jg p jd]].
q[k sgu[p ja p jb p jc k jh[] k ji[]]].q[k sgu[p ja p jb p jc k jh[] k jj[]]].''')
    domain=('event1','event2','a','b','c','d','alias','other');rows={}
    names=('baseline','empty_events','missing_source','missing_target','two_source_values',
        'two_target_values','equivalent_target_alias','same_input_different_output','coincident_events','swapped_event_targets',
        'equivalent_source_different_output','equivalent_source_same_output')
    for name in names:
        events=set() if name=='empty_events' else {'event1','event2'}
        left={('event1','a'),('event2','b')};right={('event1','c'),('event2','d')}
        if name=='missing_source':left.remove(('event2','b'))
        if name=='missing_target':right.remove(('event2','d'))
        if name=='two_source_values':left.add(('event1','b'))
        if name=='two_target_values':right.add(('event1','d'))
        if name=='equivalent_target_alias':right.add(('event1','alias'))
        if name in ('same_input_different_output','coincident_events'):left={('event1','a'),('event2','a')}
        if name=='coincident_events':right={('event1','c'),('event2','c')}
        if name=='equivalent_source_same_output':right={('event1','c'),('event2','c')}
        if name=='swapped_event_targets':right={('event1','d'),('event2','c')}
        def key(value):return 'c' if value=='alias' else 'a' if value=='b' and name.startswith('equivalent_source_') else value
        equal=lambda a,b:key(a)==key(b)
        relation=lambda a,b:any((e,a) in left and (e,b) in right for e in events)
        if source:
            model=guarded(doc)
            model.update(zc4=lambda e:e in events,ra=lambda:'a',zbm=lambda:'b',zb6=lambda:'motion',ri=lambda:'text',shh=equal,
                shd=lambda e,t,f,ctx:ctx=='motion' and (e,t) in (left if f=='a' else right if f=='b' else set()))
        else:
            model={'ja':lambda e:e in events,'jb':lambda e,t:(e,t) in left,'jc':lambda e,t:(e,t) in right,'jd':equal,
                'je':lambda t:any((e,t) in left for e in events),'jf':lambda t:any((e,t) in right for e in events),
                'jg':relation,'jh':lambda:'a','ji':lambda:'c','jj':lambda:'d'}
        # Independent finite set checks distinguish coverage, value uniqueness,
        # and a function of source coordinates (not of event identifiers).
        complete=bool(events) and all(
            all(vals and all(equal(a,b) for a in vals for b in vals) for vals in
                ({t for e,t in left if e==event},{t for e,t in right if e==event})) for event in events)
        firsts={t for e,t in left if e in events};seconds={t for e,t in right if e in events}
        functional=bool(firsts) and all(any(relation(a,b) for b in seconds) for a in firsts) and all(
            equal(b,d) for a in firsts for c in firsts for b in seconds for d in seconds if equal(a,c) and relation(a,b) and relation(c,d))
        expected=[complete and functional] if source else [complete,functional,relation('a','c'),relation('a','d')]
        actual=values(doc,model,domain)
        if actual!=expected:raise ValueError('Coordinate chart correspondence differs: '+name+repr(actual))
        rows[name]=actual
    return rows


def tuple_binding_checks():
    doc=abstract(candidate(source_composed()[0],'''
r ja[] a.r jb[] a.r jc[] a.r jd[] d.r je[] h[a a a a d] c.r jf[] h[h[b] c] c.r jg[] h[h[b] c h[b] c] c.
q[k shc[k ja[] k jb[] k jc[] k jd[] k je[] k jf[] k jg[]]].'''),{'sgk','sgp'})
    rows={};roles=('x','y','z','time');coords={'left':(-1,0,1,2),'right':(3,4,5,6)}
    domain=('event','other_event','left','right','alias','rest','moving','restplace','movingplace','ambiguous_place','other',*roles,'lengthunit','timeunit')
    names=('baseline','moving_frame','tuple_alias','wrong_event','event_outside_scope','event_unselected_in_frame',
        'wrong_place','missing_x_measurement','missing_y_measurement','missing_z_measurement','missing_time_assignment',
        'wrong_x_value','wrong_y_value','wrong_z_value','wrong_time_value','invalid_component','untyped_tuple',
        'time_role_equals_x','wrong_length_unit','wrong_time_unit','wrong_context','frame_untyped','ambiguous_location')
    for name in names:
        frame='moving' if name=='moving_frame' else 'rest';which='right' if name=='moving_frame' else 'alias' if name=='tuple_alias' else 'left'
        def component(t,r):
            vector=coords.get(t,coords['left']);index=roles.index(r) if r in roles else 0
            value=vector[index]
            if name=='invalid_component' and r=='z':value=30
            if name=='wrong_'+r+'_value':value+=1
            return cut(value)
        model=guarded(doc)
        model.update(ja=lambda:'other_event' if name=='wrong_event' else 'event',jb=lambda:which,
            jc=lambda:frame,jd=lambda:'other' if name=='wrong_context' else 'motion',
            zc4=lambda e:e=='event' and name!='event_outside_scope',
            zcz=lambda e,f,ctx:e=='event' and f in ('rest','moving') and ctx=='motion' and name!='event_unselected_in_frame',
            va=lambda f:f in ('rest','moving') and name!='frame_untyped',
            zc5=lambda t:t in ('left','right','alias') and name!='untyped_tuple',zc6=component,
            yn=lambda:'x',yo=lambda:'y',yp=lambda:'z',zc7=lambda:'x' if name=='time_role_equals_x' else 'time',
            ta=lambda:'timeunit' if name=='wrong_length_unit' else 'lengthunit',
            rb=lambda:'lengthunit' if name=='wrong_time_unit' else 'timeunit',
            ti=lambda u:u=='lengthunit',ci=lambda u:u=='timeunit',
            zcu=lambda p,f,ctx:ctx=='motion' and (p==f+'place' or name=='ambiguous_location' and (p,f)==('ambiguous_place','rest')),
            cb=lambda e,p,f:e=='event' and p==f+'place' and name!='wrong_place',
            zbe=lambda e,f,u,ctx:cut(coords['left' if f=='rest' else 'right'][3]),
            zcy=lambda p,f,r,u,ctx:cut(coords['left' if f=='rest' else 'right'][roles.index(r)]))
        def measured(p,f,r,u,ctx,valid,same):
            return (u,ctx)==('lengthunit','motion') and (p==f+'place' or name=='ambiguous_location' and (p,f)==('ambiguous_place','rest')) and name!='missing_'+r+'_measurement' and valid(cut(1)) and same(cut(1),cut(1)) and not same(cut(1),cut(2))
        def assigned(e,p,f,u,ctx,sync,valid,same):
            return (e,p,u,ctx)==('event',f+'place','timeunit','motion') and name!='missing_time_assignment' and sync('event','event',f,u,ctx) and valid(cut(1)) and same(cut(1),cut(1))
        model.update(sgk=measured,sgp=assigned)
        callbacks(doc,model,{'je':lambda a,b,f,u,ctx:f in ('rest','moving') and (u,ctx)==('timeunit','motion'),
            'jf':lambda v:-1<=embedding(v)<=6,'jg':lambda a,b:embedding(a)==embedding(b)})
        actual=values(doc,model,domain)[0]
        expected=name in ('baseline','moving_frame','tuple_alias')
        if actual!=expected:raise ValueError('Same-event tuple measurement binding differs: '+name)
        rows[name]=actual
    return {'cases':rows,'measurement_predicates_replaced_with_oracles':True,'integer_embedding_oracles':True,'full_measurement_model_evaluated':False}


def equation_checks(source=False):
    if source:
        doc=abstract(candidate(source_composed()[0],
            'r jg[] '+SYSTEM+'.q[k shj[k jg[]]].q[h[k shk[]][k jg[]]].'),{'shf','shg','she','shh','ba','sca'})
    else:
        doc=parse(generic_composed()[0]+'''
r ja[a] c.r jb[a] c.r jc[a a] c.r jd[a a] c.r je[] h[h[b] c] c.r jf[] h[h[b] c h[b] c] c.
'''+ 'r jg[] '+SYSTEM+'.q[k sgy[k jg[] p ja p jb p jc p jd k je[] k jf[]]].q[h[k sgz[p ja p jb p jc p jd k je[] k jf[]]][k jg[]]].')
    sequence_sort=next(d['result'] for d in doc['declarations'] if d['name']=='jg');element=sequence_sort['element']
    domain=('a','b','c','d','extra')
    coordinates={'a':(0,0,0,0),'b':(1,0,0,0),'c':(2,0,0,0),'d':(3,0,0,0),'extra':(2,1,0,0)}
    rows={}
    for name in ('exact','reordered','duplicate_equation','empty','missing_x','missing_y','too_restrictive','invalid_side','no_source_domain','missing_correspondence','nonfunctional_correspondence'):
        indices=[0,1,2,3]
        if name=='reordered':indices.reverse()
        if name=='duplicate_equation':indices.append(0)
        if name=='empty':indices=[]
        if name=='missing_x':indices.remove(0)
        if name=='missing_y':indices.remove(1)
        def term(index,a,b,left):
            if name=='invalid_side' and index==3 and not left:return cut(31)
            value=coordinates[a][index]+(2 if index==0 else 0) if left else coordinates[b][index]
            if name=='too_restrictive' and index==1 and left:value+=1
            return cut(value)
        equations=tuple(FunctionValue(tuple(element['parameters']),element['result'],lambda a,b,left,index=index:term(index,a,b,left)) for index in indices)
        sequence=SequenceValue(equations,json.dumps(element,sort_keys=True,separators=(',',':')))
        pairs={('a','c'),('b','d')}
        if name=='missing_correspondence':pairs.remove(('b','d'))
        if name=='nonfunctional_correspondence':pairs.add(('a','d'))
        model=guarded(doc)
        entries={'shf' if source else 'ja':lambda t:t in ('a','b') and name!='no_source_domain',
            'shg' if source else 'jb':lambda t:t in ('c','d','extra'),
            'she' if source else 'jc':lambda a,b:(a,b) in pairs,
            'shh' if source else 'jd':lambda a,b:coordinates[a]==coordinates[b],'jg':lambda:sequence}
        model.update(entries)
        valid=lambda v:0<=embedding(v)<10
        same=lambda a,b:embedding(a)==embedding(b)
        if source:model.update(ba=valid,sca=same)
        else:callbacks(doc,model,{'je':valid,'jf':same})
        actual=values(doc,model,domain)
        expected=name in ('exact','reordered','duplicate_equation')
        if actual!=[expected]*2:raise ValueError('Equation solution set or question match differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'fixed_finite_coordinate_domain':True,'integer_embedding_oracles':True,'general_transformation_derived':False}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for name in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_claim','wrong_question','wrong_prior_setting'):
        model=guarded(doc)
        for key,value in {'zda':'claim','zdb':'task','zc3':'measurement','rd':'author','rh':'scope','ri':'text'}.items():model[key]=lambda value=value:value
        def shared(author,scope,ctx):return (author,scope,ctx)==('other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','other' if name=='wrong_context' else 'text')
        model.update(uh=lambda node,author,desc,scope,ctx:shared(author,scope,ctx) and (node,json.loads(desc.syntax)['symbol'])==('claim','shk' if name=='wrong_claim' else 'shi'),
            zdc=lambda node,author,desc,scope,ctx:shared(author,scope,ctx) and (node,json.loads(desc.syntax)['symbol'])==('task','shi' if name=='wrong_question' else 'shk'),
            zao=lambda a,b,s,c:(a,b,s,c)==('other' if name=='wrong_prior_setting' else 'measurement','claim','scope','text'))
        actual=values(doc,model,('claim','task','measurement','author','scope'))
        bad={'wrong_author','wrong_scope','wrong_context'}
        expected=[name not in bad|{'wrong_claim','wrong_prior_setting'},name not in bad|{'wrong_question'}]
        if actual!=expected:raise ValueError('Coordinate task attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0046')
    digest='a1b68714d870d447a894ad5f6bb147fae6384314d5523e95faff5a3864888e86'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Coordinate correspondence source changed')
    return {'segments':[{'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],
        'definitions':['shc','she','shi','shj','shk'],'status':'partial_explicit_reading','full_semantic_equivalence':False}],
        'facsimile_checked':False,'coordinate_chart_completeness_not_proved':True,'verified_full_units':0}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored correspondence differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Correspondence roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/coordinate-correspondence-basis-v1.json','data/einstein-coordinate-correspondence-basis-v1.json',
        'examples/v014/einstein-frame-measurements.noema','scripts/compose_coordinate_correspondence.py','scripts/check_coordinate_correspondence.py',
        'noema/discourse.py','noema/finite_semantics.py']
    current=source_composed()[0];previous=(ROOT/'examples/v014/einstein-frame-measurements.noema').read_text(encoding='utf-8')
    return {'status':'partial_same_event_correspondence_and_equation_task','documents':documents,
        'generic_charts':chart_checks(),'source_charts':chart_checks(True),'measurement_bindings':tuple_binding_checks(),
        'generic_equations':equation_checks(),'source_equations':equation_checks(True),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'added_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Correspondence report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Same-event tuples, exact equation answers and task attribution checked')


if __name__=='__main__':main()
