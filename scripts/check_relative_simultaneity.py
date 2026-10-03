"""Check unavailable times, frame dependence, uniqueness and time-mixing limits."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_moving_light_trip import literal
from scripts.check_real_products import MEANINGS, ZERO, call, op, conjunction, assertion
from scripts.check_rod_comparison import callbacks, guarded
from scripts.check_rod_measurements import ARITHMETIC, cut, fingerprint
from scripts.compose_relative_simultaneity import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/relative-simultaneity-v1.json'


def values(doc,model,domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('comparison','text','other'),
        primitives=model,max_steps=3_000_000,memoize_definitions=True,memoize_expressions=True)]


def logical_checks():
    doc=parse(generic_composed()[0]+'''
r ja[a] c.r jb[a] c.r jc[a a a a d] c.r jd[a a d] c.r je[a a a d] c.r jf[] d.
q[k sea[k jf[] p ja p jb p jc p jd p je]].q[k seb[k jf[] p ja p jb p jc p jd p je]].
q[k sec[k jf[] p ja p jb p jc p jd p je]].q[k sed[k jf[] p ja p jb p jc p jd p je]].''')
    rows=[];domain=('eventa','eventb','framea','frameb')
    for mask in product((False,True),repeat=7):
        available=set(pair for pair,yes in zip(product(domain[:2],domain[2:]),mask[:4]) if yes)
        first,second,comparable=mask[4:]
        model={**ARITHMETIC,'ja':lambda e:e in domain[:2],'jb':lambda f:f in domain[2:],
            'jc':lambda a,b,f,g,ctx:comparable and (a,b,f,g,ctx)==(*domain,'comparison'),
            'jd':lambda e,f,ctx:ctx=='comparison' and (e,f) in available,
            'je':lambda a,b,f,ctx:first if f=='framea' else second,'jf':lambda:'comparison'}
        actual=values(doc,model,domain)
        valid=all(mask[:4]) and comparable
        expected=[not valid or first==second,valid and first and not second,valid and first!=second,not valid or not first or not second]
        if actual!=expected:raise ValueError('Frame-dependence logical kernel differs')
        rows.append({'bits':list(mask),'results':actual})
    # One pair changes while another simultaneous pair remains simultaneous.
    domain=('eventa','eventb','eventc','framea','frameb')
    model={**ARITHMETIC,'ja':lambda e:e in domain[:3],'jb':lambda f:f in domain[3:],
        'jc':lambda a,b,f,g,ctx:a=='eventa' and b in ('eventb','eventc') and (f,g,ctx)==('framea','frameb','comparison'),
        'jd':lambda e,f,ctx:e in domain[:3] and f in domain[3:] and ctx=='comparison',
        'je':lambda a,b,f,ctx:f=='framea' or b=='eventc','jf':lambda:'comparison'}
    mixed=values(doc,model,domain)
    if mixed!=[False,True,True,False]:raise ValueError('Existence incorrectly implies all-pair change')
    return {'cases':rows,'changing_and_preserved_pairs_together':mixed,
        'invariance_iff_no_disagreement_checked':all(r['results'][0]!=r['results'][2] for r in rows),
        'missing_readings_are_not_nonsimultaneity':True}


def numeric_checks():
    cases={
        'longitudinal_separation':((3,5,Fraction(5,4),0,2,0,Fraction(5,2),2,5,Fraction(7,4)),True),
        'same_longitudinal_coordinate':((3,5,Fraction(5,4),0,2,0,Fraction(5,2),2,0,Fraction(5,2)),True),
        'zero_relative_speed':((0,5,1,0,2,0,2,2,5,2),True),
        'negative_relative_speed':((-3,5,Fraction(5,4),0,2,0,Fraction(5,2),2,5,Fraction(13,4)),True),
        'common_time_origin':((3,5,Fraction(5,4),7,2,0,Fraction(19,2),2,5,Fraction(35,4)),True),
        'nonunit_scale':((3,5,Fraction(5,2),0,2,0,5,2,5,Fraction(7,2)),True),
        'simultaneous_only_in_target':((3,5,Fraction(5,4),0,2,0,Fraction(5,2),Fraction(13,5),5,Fraction(5,2)),True),
        'wrong_mixing_sign':((3,5,Fraction(5,4),0,2,0,Fraction(5,2),2,5,Fraction(13,4)),False),
        'different_output_origin':((3,5,Fraction(5,4),0,2,0,Fraction(5,2),2,5,Fraction(11,4)),False),
        'zero_scale':((3,5,0,0,2,0,0,2,5,0),False),
        'zero_light_speed':((0,0,1,0,2,0,2,2,5,2),False),
        'light_speed_boundary':((5,5,1,0,2,0,2,2,5,1),False),
    }
    rows={}
    for name,(args,expected) in cases.items():
        doc=parse(generic_composed()[0]+'q['+call('sef',*(literal(x) for x in args))+'].')
        actual=values(doc,ARITHMETIC,('object',))[0]
        if actual!=expected:raise ValueError('Time-mixing numeric condition differs: '+name)
        rows[name]={'relation':actual,'source_simultaneous':args[4]==args[7],'target_simultaneous':args[6]==args[9]}
    return rows


def polynomial_checks():
    v,c,k,o,t,x,a,s,y,b=('v '+name for name in ('speed','light','scale','origin','first','firstx','firstout','second','secondx','secondout'))
    mul=lambda p,q:call('ad',p,q)
    sub=lambda p,q:call('ab',p,call('ac',q))
    base=call('sef',v,c,k,o,t,x,a,s,y,b)
    equal=op('e',t,s);outequal=op('e',a,b)
    names='speed light scale origin first firstx firstout second secondx secondout'
    claims={
        'common_origin_cancels_in_time_difference':assertion(names,op('y',base,
            op('e',mul(mul(c,c),sub(b,a)),mul(k,sub(mul(mul(c,c),sub(s,t)),mul(v,sub(y,x))))))),
        'simultaneity_preserved_iff_velocity_times_position_gap_zero':assertion(names,
            op('y',conjunction(base,equal),op('z',outequal,op('e',mul(v,sub(y,x)),ZERO)))),
        'nonzero_motion_and_longitudinal_gap_change_simultaneity':assertion(names,
            op('y',conjunction(base,equal,op('u',op('e',v,ZERO)),op('u',op('e',x,y))),op('u',outequal))),
        'equal_longitudinal_position_preserves_simultaneity':assertion(names,
            op('y',conjunction(base,equal,op('e',x,y)),outequal)),
        'all_nonzero_motion_destroys_every_simultaneous_pair':assertion(names,
            op('y',conjunction(base,equal,op('u',op('e',v,ZERO))),op('u',outequal))),
        'all_simultaneous_pairs_stay_simultaneous':assertion(names,op('y',conjunction(base,equal),outequal)),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(generic_composed()[0]+claim),MEANINGS,timeout_ms=15000)[0]
        expected='invalid' if name.startswith('all_') else 'valid'
        if result['status']!=expected:raise ValueError('Simultaneity proof differs: '+name+' '+result['status'])
        rows[name]=result
    # Connect the auxiliary relation to the frozen, previously composed four
    # coordinate equations; avoid silently substituting a new transformation.
    coordinate=parse((ROOT/'examples/v011/einstein-coordinates.noema').read_text(encoding='utf-8'))
    bridge=parse(generic_composed()[0])
    bridge['declarations'] += [deepcopy(d) for d in coordinate['declarations'] if d['name'] in ('cm','ea')]
    beta,phi=('v '+n for n in ('beta','phi'))
    four=call('ea',v,c,beta,phi,t,x,'v y','v z',a,'v xi','v eta','v zeta')
    claim=assertion('speed light beta phi first firstx y z firstout xi eta zeta',
        op('y',conjunction(four,op('u',op('e',phi,ZERO))),call('see',v,c,mul(phi,beta),ZERO,t,x,a)))
    result=verify_universal(parse(format_graph(bridge,'compact')+claim),MEANINGS,timeout_ms=15000)[0]
    if result['status']!='valid':raise ValueError('Existing coordinate equation bridge differs')
    rows['existing_four_coordinate_equations_imply_time_component']=result
    return rows


def local_time_checks():
    doc=candidate(source_composed()[0],'''
r ja[] a.r jb[] a.r jc[] a.r jd[] d.r je[] h[a a a a d] c.r jf[] h[h[b] c] c.
q[k sei[k ja[] k jb[] k jc[] k jd[] k je[] k jf[]]].''')
    domain=('event','reception','clock','reference','place','remote','frame','otherframe','unit','other')
    names=('baseline','wrong_event','wrong_frame','wrong_unit','wrong_context','missing_reading','wrong_reading',
        'clock_not_stationary','reference_not_stationary','missing_clock_type','missing_reference_type',
        'remote_clock','missing_event_location','unsynced','different_reference','invalid_value')
    rows={}
    for name in names:
        model=guarded(doc)
        model.update(ja=lambda:'reception' if name=='wrong_event' else 'event',
            jb=lambda:'otherframe' if name=='wrong_frame' else 'frame',jc=lambda:'other' if name=='wrong_unit' else 'unit',
            jd=lambda:'other' if name=='wrong_context' else 'comparison',
            zbe=lambda *args:cut(9 if name=='wrong_reading' else 7),zbh=lambda frame,ctx:'reference',
            ca=lambda clock:clock in ('clock','reference') and not(name=='missing_clock_type' and clock=='clock' or name=='missing_reference_type' and clock=='reference'),
            cc=lambda clock,frame:frame=='frame' and clock in ('clock','reference') and not(name=='clock_not_stationary' and clock=='clock' or name=='reference_not_stationary' and clock=='reference'),
            ci=lambda unit:unit=='unit',
            cb=lambda obj,place,frame:frame=='frame' and ((obj=='clock' and place==('remote' if name=='remote_clock' else 'place')) or (obj=='event' and place=='place' and name!='missing_event_location')),
            ce=lambda clock,event,frame,unit,value:name!='missing_reading' and (clock,event,frame,unit)==('clock','event','frame','unit') and fingerprint(value)==fingerprint(cut(7)))
        callbacks(doc,model,{'je':lambda clock,ref,frame,unit,ctx:name!='unsynced' and (clock,ref,frame,unit,ctx)==('clock','other' if name=='different_reference' else 'reference','frame','unit','comparison'),
            'jf':lambda value:name!='invalid_value'})
        actual=values(doc,model,domain)[0]
        if actual!=(name=='baseline'):raise ValueError('General frame local time differs: '+name)
        rows[name]=actual
    return {'cases':rows,'full_real_uniqueness_evaluated':False,'only_selected_reading_adapter_evaluated':True}


def projected_uniqueness():
    original=parse(source_composed()[0])
    cut_sort={'kind':'function','parameters':['number'],'result':'truth'}
    def replace(value):
        if value==cut_sort:return 'individual'
        if isinstance(value,dict):return {k:replace(v) for k,v in value.items()}
        if isinstance(value,list):return [replace(v) for v in value]
        return value
    names={'ca','cb','cc','ci','ce','zbe','zbh','sae','saf','seg','seh','sei'}
    doc={**original,'declarations':replace([deepcopy(d) for d in original['declarations'] if d['name'] in names]),'statements':[]}
    doc=parse(format_graph(doc,'compact')+'''
r ja[] a.r jb[] a.r jc[] a.r jd[] d.r je[] h[a a a a d] c.r jf[] h[a] c.r jg[] h[a a] c.
q[k seh[k ja[] k jb[] k jc[] k jd[] k je[] k jf[] k jg[]]].
q[k sei[k ja[] k jb[] k jc[] k jd[] k je[] k jf[]]].''')
    domain=('event','clock','reference','place','frame','unit','seven','alias','nine','other')
    rows=[]
    for bits in product((False,True),repeat=3):
        selected={x for x,yes in zip(('seven','alias','nine'),bits) if yes}
        model={'ja':lambda:'event','jb':lambda:'frame','jc':lambda:'unit','jd':lambda:'comparison',
            'zbe':lambda *args:'seven','zbh':lambda *args:'reference','ca':lambda c:c in ('clock','reference'),
            'cb':lambda obj,place,frame:obj in ('clock','event') and (place,frame)==('place','frame'),
            'cc':lambda c,f:c in ('clock','reference') and f=='frame','ci':lambda u:u=='unit',
            'ce':lambda c,e,f,u,v:(c,e,f,u)==('clock','event','frame','unit') and v in selected}
        callbacks(doc,model,{'je':lambda *args:args==('clock','reference','frame','unit','comparison'),
            'jf':lambda value:value in ('seven','alias','nine'),
            'jg':lambda a,b:({'seven':7,'alias':7,'nine':9}.get(a,a)=={'seven':7,'alias':7,'nine':9}.get(b,b))})
        actual=values(doc,model,domain)
        expected=['seven' in selected and 'nine' not in selected,'seven' in selected]
        if actual!=expected:raise ValueError('Finite carrier uniqueness projection differs')
        rows.append({'selected':sorted(selected),'results':actual})
    return {'cases':rows,'carrier_substitution_only':True,'real_cut_uniqueness_proved':False}


def comparison_scope_checks():
    doc=candidate(source_composed()[0],'''
r ja[] a.r jb[] a.r jc[] a.r jd[] a.r je[] d.
q[k sel[k ja[] k jb[] k jc[] k jd[] k je[]]].
q[k sem[k ja[] k jb[] k jc[] k jd[] k je[]]].''')
    # Replace only the cut-validity/equality checks with explicit fixture oracles.
    # These are tests of the source bindings, not evaluations over all real cuts.
    for i,d in enumerate(doc['declarations']):
        if d['name'] in ('ba','sca'):
            doc['declarations'][i]={'kind':'primitive','name':d['name'],
                'parameters':[p['sort'] for p in d['parameters']],'result':d['result']}
    probes=tuple(Fraction(n) for n in range(-5,13))
    key=lambda value:tuple(value(q) for q in probes)
    valid={key(cut(n)) for n in (-3,0,3,5)}
    names=('baseline','negative_speed','zero_speed','same_longitudinal_position','same_frame','reversed_frames',
        'axes_not_parallel','velocity_not_constant','invalid_speed','invalid_position','wrong_unit','wrong_context')
    rows={}
    for name in names:
        model=guarded(doc)
        constants={'ja':'eventa','jb':'eventb','jc':'frameb' if name=='reversed_frames' else 'framea',
            'jd':'framea' if name in ('same_frame','reversed_frames') else 'frameb',
            'je':'other' if name=='wrong_context' else 'comparison','ta':'lengthunit',
            'rb':'other' if name=='wrong_unit' else 'timeunit'}
        for k,v in constants.items():model[k]=lambda v=v:v
        speed=-3 if name=='negative_speed' else 0 if name=='zero_speed' else 99 if name=='invalid_speed' else 3
        def position(event,frame,unit,ctx):
            if frame!='framea' or unit!='lengthunit' or ctx!='comparison' or name=='invalid_position':return cut(99)
            return cut(0 if event=='eventa' or name=='same_longitudinal_position' else 5)
        model.update(aa=lambda a,b:a<b,ba=lambda value:key(value) in valid,sca=lambda a,b:key(a)==key(b),
            va=lambda f:f in ('framea','frameb'),
            vb=lambda *args:name!='axes_not_parallel' and args==('framea','frameb','comparison'),
            vc=lambda *args:name!='velocity_not_constant' and args==('framea','frameb','comparison'),
            zbi=lambda *args:cut(speed if args==('framea','frameb','lengthunit','timeunit','comparison') else 99),zbl=position)
        actual=values(doc,model,('eventa','eventb','framea','frameb','lengthunit','timeunit','other'))
        broad=name in ('baseline','negative_speed','same_longitudinal_position','invalid_position')
        narrow=name in ('baseline','negative_speed')
        if actual!=[broad,narrow]:raise ValueError('Comparison scope differs: '+name+' '+repr(actual))
        rows[name]=actual
    return {'cases':rows,'validity_and_equality_replaced_with_finite_integer_oracles':True,
        'full_real_scope_evaluated':False}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-2:]
    rows={}
    for name in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_premise','wrong_conclusion','reversed_contrast'):
        model=guarded(doc)
        for key,val in {'zbk':'node','rd':'author','rh':'principle_scope','ri':'text'}.items():model[key]=lambda val=val:val
        symbol=lambda desc:json.loads(desc.syntax)['symbol']
        def common(node,author,scope,ctx):
            return (node,author,scope,ctx)==('node','other' if name=='wrong_author' else 'author',
                'other' if name=='wrong_scope' else 'principle_scope','other' if name=='wrong_context' else 'text')
        model['zc']=lambda node,author,premise,conclusion,scope,ctx:common(node,author,scope,ctx) and (symbol(premise),symbol(conclusion))==(
            'sdj' if name=='wrong_premise' else 'sdt','sen' if name=='wrong_conclusion' else 'seq')
        model['zbc']=lambda node,author,a,b,scope,ctx:common(node,author,scope,ctx) and (symbol(a),symbol(b))==(('ses','ser') if name=='reversed_contrast' else ('ser','ses'))
        actual=values(doc,model,('node','author','principle_scope','other'))
        bad={'wrong_author','wrong_scope','wrong_context'}
        expected=[name not in bad|{'wrong_premise','wrong_conclusion'},name not in bad|{'reversed_contrast'}]
        if actual!=expected:raise ValueError('Relative simultaneity attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0041')
    digest='d7a76cee5507db3a7dd6a62b48c3fb46a44db5279c62f8e52aa5f1b427b5ffaf'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Relative simultaneity source changed')
    return {'segments':[{'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],
        'definitions':['sen','seo','sep','seq','ser','ses'],'status':'partial_explicit_reading','full_semantic_equivalence':False}],
        'verified_full_units':0,'facsimile_checked':False,'longitudinal_scope_is_explicit_interpretive_addition':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored simultaneity differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Simultaneity roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/relative-simultaneity-basis-v1.json','data/einstein-relative-simultaneity-basis-v1.json',
        'examples/v014/einstein-observer-judgments.noema','examples/v011/einstein-coordinates.noema',
        'scripts/compose_relative_simultaneity.py','scripts/check_relative_simultaneity.py',
        'noema/discourse.py','noema/finite_semantics.py','noema/polynomial_proofs.py']
    current=source_composed()[0];previous=(ROOT/'examples/v014/einstein-observer-judgments.noema').read_text(encoding='utf-8')
    return {'status':'partial_frame_relative_simultaneity_with_explicit_interpretive_scope','documents':documents,
        'logical':logical_checks(),'numeric':numeric_checks(),'polynomial':polynomial_checks(),
        'local_time_adapter':local_time_checks(),'uniqueness_projection':projected_uniqueness(),
        'comparison_scope_adapter':comparison_scope_checks(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'added_declarations_and_statements_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Relative simultaneity report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Frame dependence, reading availability, uniqueness projection and time-mixing limits checked')


if __name__=='__main__':main()
