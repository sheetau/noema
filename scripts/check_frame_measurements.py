"""Check frame-bound instruments, complete coordinate tuples and local time scope."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, guarded, embedding
from scripts.check_rod_measurements import cut
from scripts.compose_frame_measurements import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/frame-measurements-v1.json'


def values(doc,model,domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,
        situations=('initial','motion','text','other'),primitives=model,max_steps=3_000_000,
        memoize_definitions=True,memoize_expressions=True)]


def coverage_checks():
    doc=parse(generic_composed()[0]+'''
r ja[a] c.r jb[a] c.r jc[a a] c.
q[k sgf[p ja p jb p jc]].''')
    pairs=list(product(('p','q'),('x','y','z')));rows=[]
    for bits in product((False,True),repeat=6):
        available={pair for pair,yes in zip(pairs,bits) if yes}
        model={'ja':lambda p:p in ('p','q'),'jb':lambda c:c in ('x','y','z'),'jc':lambda p,c:(p,c) in available}
        actual=values(doc,model,('p','q','x','y','z'))[0]
        if actual!=all(bits):raise ValueError('Coordinate coverage differs')
        rows.append({'six_coordinates':list(bits),'result':actual})
    for empty in ('places','channels'):
        model={'ja':lambda p:empty!='places' and p=='p','jb':lambda c:empty!='channels' and c=='x','jc':lambda *a:True}
        if values(doc,model,('p','x'))!=[False]:raise ValueError('Empty spatial scope accepted')
    return rows


def clock_scope_checks():
    doc=parse(generic_composed()[0]+'''
r ja[a] c.r jb[a] c.r jc[a a] c.r jd[a] c.r je[a a] c.r jf[] a.
r jg[a] c.r jh[a a] c.r ji[a a] c.
q[k sgg[p ja p jb p jc p jd p je k jf[]]].
q[k sgi[p ja p jb p jc p jg p jh p ji]].''')
    names=('baseline','empty_clock_set','reference_not_deployed','clock_unusable','clock_has_no_place',
        'clock_outside_space','clock_unsynchronized','event_time_missing','event_at_empty_place',
        'unselected_event','second_clock_at_empty_place','second_event_at_clock_place')
    rows={};domain=('clock','reference','extra','p','q','empty','outside','event','second','other')
    for name in names:
        clocks={'clock','reference'}
        if name=='empty_clock_set':clocks=set()
        if name=='reference_not_deployed':clocks.remove('reference')
        if name=='second_clock_at_empty_place':clocks.add('extra')
        located={('clock','p'),('reference','q'),('extra','empty')}
        if name=='clock_has_no_place':located.remove(('clock','p'))
        if name=='clock_outside_space':located.add(('clock','outside'))
        events={'event'} if name!='unselected_event' else set()
        if name=='second_event_at_clock_place':events.add('second')
        eventplace={('event','empty' if name in ('event_at_empty_place','second_clock_at_empty_place') else 'p'),('second','p')}
        model={'ja':lambda p:p in ('p','q','empty'),'jb':lambda c:c in clocks,'jc':lambda c,p:(c,p) in located,
            'jd':lambda c:name!='clock_unusable' or c!='clock',
            'je':lambda c,r:r=='reference' and (name!='clock_unsynchronized' or c!='clock'),'jf':lambda:'reference',
            'jg':lambda e:e in events,'jh':lambda e,p:(e,p) in eventplace,
            'ji':lambda e,p:(e,p)==('event','p') and name!='event_time_missing'}
        actual=values(doc,model,domain)
        expected=[name not in {'empty_clock_set','reference_not_deployed','clock_unusable','clock_has_no_place','clock_outside_space','clock_unsynchronized'},
            name not in {'event_time_missing','second_clock_at_empty_place','second_event_at_clock_place'}]
        if actual!=expected:raise ValueError('Clock-place scope differs: '+name+repr(actual))
        rows[name]=actual
    return rows


def carrier_document(roots,query,abstract=()):
    """Project only the relevant definitions; real cuts become a finite value carrier."""
    source=parse(source_composed()[0]);decls={d['name']:deepcopy(d) for d in source['declarations']}
    for name in abstract:
        d=decls[name];decls[name]={'kind':'primitive','name':name,'parameters':[p['sort'] for p in d['parameters']],'result':d['result']}
    def refs(value):
        if isinstance(value,dict):
            result={value['symbol']} if 'symbol' in value else set()
            for child in value.values():result |= refs(child)
            return result
        if isinstance(value,list):return set().union(*(refs(v) for v in value))
        return set()
    selected=set(roots)
    while True:
        expanded=selected|set().union(*(refs(decls[n]) for n in selected))
        if expanded==selected:break
        selected=expanded
    real_sort={'kind':'function','parameters':['number'],'result':'truth'}
    def project(value):
        if value==real_sort:return 'individual'
        if isinstance(value,dict):return {k:project(v) for k,v in value.items()}
        if isinstance(value,list):return [project(v) for v in value]
        return value
    doc={**source,'declarations':project([decls[d['name']] for d in source['declarations'] if d['name'] in selected]),'statements':[]}
    return parse(format_graph(doc,'compact')+query)


def spatial_checks():
    doc=carrier_document({'sgl'},'''
r ja[] h[a] c.r jb[] h[a a] c.r jc[] a.r jd[] a.r je[] d.
q[k sgl[k jc[] k je[] k ja[] k jb[]]].q[k sgl[k jd[] k je[] k ja[] k jb[]]].''',abstract=('sfb',))
    names=('baseline','same_value_alias','conflicting_value','missing_z','missing_second_place',
        'wrong_ruler','ruler_not_stationary','ruler_not_rigid','ruler_not_deployed','ruler_replaced',
        'origin_replaced','axis_replaced','wrong_projection','wrong_axis','wrong_frame','wrong_unit',
        'wrong_context','invalid_value','geometry_invalid','empty_space')
    rows={};frameplaces={'A':('p','q'),'B':('r','s')};roles=('x','y','z')
    domain=('A','B','p','q','r','s',*roles,'minus','zero','plus','alias','conflict','invalid','other',
        'Aruler','Bruler','Aorigin','Borigin','Ax','Ay','Az','Bx','By','Bz','replaced','length','badunit',
        'projected:p','projected:q','projected:r','projected:s')
    for name in names:
        model=guarded(doc)
        model.update(jc=lambda:'A',jd=lambda:'B',je=lambda:'other' if name=='wrong_context' else 'motion',
            ta=lambda:'badunit' if name=='wrong_unit' else 'length',zb4=lambda:'initial',yn=lambda:'x',yo=lambda:'y',yp=lambda:'z')
        def coord(p,f,role,u,ctx):
            if name=='invalid_value' and (p,f,role)==('p','A','x'):return 'invalid'
            return ('minus','zero','plus')[roles.index(role)] if role in roles else 'invalid'
        def ruler(f,ctx):return ('replaced' if name=='ruler_replaced' and f=='A' and ctx=='motion' else f+'ruler')
        def origin(f,ctx):return 'replaced' if name=='origin_replaced' and f=='A' and ctx=='motion' else f+'origin'
        def axis(f,role,ctx):return 'replaced' if name=='axis_replaced' and f=='A' and role=='x' and ctx=='motion' else f+role if role in roles else 'other'
        def measures(r,o,p,f,a,u,v,ctx):
            if (u,ctx)!=('length','motion') or f not in frameplaces:return False
            if name=='wrong_ruler' and f=='A':return r=='Bruler'
            if name=='wrong_frame' and f=='A':return False
            if r!=f+'ruler' or o!=f+'origin':return False
            choices={(place,f+role):('minus','zero','plus')[i] for place in frameplaces[f] for i,role in enumerate(roles)}
            key=(p.removeprefix('projected:'),a);expected=choices.get(key)
            if name=='missing_z' and f=='A' and a=='Az':return False
            if name=='missing_second_place' and f=='A' and p=='projected:q':return False
            if name=='wrong_axis' and f=='A':return False
            return expected is not None and (v==expected or name=='same_value_alias' and v=='alias' and expected=='minus' or name=='conflicting_value' and v=='conflict' and f=='A' and key==('p','Ax'))
        model.update(sfb=lambda f,ctx:f in frameplaces and ctx=='motion' and (name!='geometry_invalid' or f!='A'),
            ti=lambda u:u=='length',xc=lambda r:r in ('Aruler','Bruler'),zby=ruler,zbn=origin,zbo=axis,
            zbx=lambda f,r,ctx:r==f+'ruler' and (name!='ruler_not_deployed' or f!='A'),
            zbq=lambda r,ctx:name!='ruler_not_rigid' or r!='Aruler',
            x4=lambda r,f,ctx:r==f+'ruler' and (name!='ruler_not_stationary' or f!='A'),
            zcu=lambda p,f,ctx:p in frameplaces.get(f,()) and (name!='empty_space' or f!='A'),
            zcv=lambda p,f,role,ctx:'projected:'+p if p in ('p','q','r','s') else 'other',
            zcw=lambda p,proj,f,a,ctx:p in frameplaces.get(f,()) and proj=='projected:'+p and a in {f+r for r in roles} and (name!='wrong_projection' or f!='A'),
            zcx=measures,zcy=coord)
        numeric={'minus':-1,'zero':0,'plus':1,'alias':-1,'conflict':9}
        callbacks(doc,model,{'ja':lambda v:v in numeric,'jb':lambda a,b:numeric.get(a,a)==numeric.get(b,b)})
        actual=values(doc,model,domain)
        expected=[name in {'baseline','same_value_alias'},name not in {'wrong_unit','wrong_context'}]
        if actual!=expected:raise ValueError('Spatial measurement differs: '+name+repr(actual))
        rows[name]=actual
    return {'cases':rows,'real_cut_carrier_substitution':True,'frame_geometry_given_as_oracle':True,'full_real_uniqueness_proved':False}


def temporal_checks():
    doc=carrier_document({'sgq'},'''
r ja[] h[a a a a d] c.r jb[] h[a] c.r jc[] h[a a] c.r jd[] a.r je[] a.r jf[] d.
q[k sgq[k jd[] k jf[] k ja[] k jb[] k jc[]]].q[k sgq[k je[] k jf[] k ja[] k jb[] k jc[]]].''',abstract=('sgp',))
    local=carrier_document({'sgp'},'''
r ja[] h[a a a a d] c.r jb[] h[a] c.r jc[] h[a a] c.r jd[] a.r je[] a.r jf[] d.
r jg[] a.r jh[] a.r ji[] a.r jj[] a.r rb[] a.
q[k sgp[k jg[] k jh[] k jd[] k rb[] k jf[] k ja[] k jb[] k jc[]]].
q[k sgp[k ji[] k jj[] k je[] k rb[] k jf[] k ja[] k jb[] k jc[]]].''')
    names=('baseline','same_value_alias','conflicting_local_reading','missing_reading',
        'clock_not_stationary','reference_not_stationary','reference_from_other_frame','clock_not_typed','clock_unlocated',
        'clock_outside_space','clock_added','clock_dropped','sync_scope_mismatch','not_synchronized',
        'wrong_unit','wrong_context','invalid_reading','event_at_unclocked_place','second_event_unread','wrong_event_place')
    clocks={'A':('ac','ar'),'B':('bc','br')};places={'A':('ap','aq','empty'),'B':('bp','bq')}
    located={('ac','ap','A'),('ar','aq','A'),('bc','bp','B'),('br','bq','B')}
    domain=('A','B','ac','ar','bc','br','extra','ap','aq','bp','bq','empty','outside','ae','be','extraevent','one','two','alias','bad','invalid','other','time','badunit')
    rows={};local_rows={}
    for name in names:
        model={**guarded(doc),**guarded(local)}
        model.update(jd=lambda:'A',je=lambda:'B',jf=lambda:'other' if name=='wrong_context' else 'motion',
            zb4=lambda:'initial',rb=lambda:'badunit' if name=='wrong_unit' else 'time',
            jg=lambda:'ae',jh=lambda:'ap',ji=lambda:'be',jj=lambda:'bp')
        def deployed(f,c,ctx):
            if name=='clock_added' and ctx=='motion' and (f,c)==('A','extra'):return True
            if name=='clock_dropped' and ctx=='motion' and (f,c)==('A','ac'):return False
            return c in clocks.get(f,())
        def location(obj,p,f):
            if name=='clock_unlocated' and obj=='ac':return False
            if name=='clock_outside_space' and (obj,p,f)==('ac','outside','A'):return True
            if (obj,p,f) in located:return True
            return (obj,p,f) in {('ae','empty' if name=='event_at_unclocked_place' else 'aq' if name=='wrong_event_place' else 'ap','A'),('be','bp','B'),('extraevent','ap','A')}
        def reading(c,e,f,u,v):
            if u!='time':return False
            if (c,e,f)==('bc','be','B'):return v=='two'
            if (c,e,f)!=('ac','ae','A') or name=='missing_reading':return False
            return v=='one' or name=='same_value_alias' and v=='alias' or name=='conflicting_local_reading' and v=='bad'
        model.update(va=lambda f:f in clocks,ci=lambda u:u=='time',zbz=deployed,
            qa=lambda c,f,ctx:deployed(f,c,ctx) and (name!='sync_scope_mismatch' or c!='ac'),
            zcu=lambda p,f,ctx:p in places.get(f,()),cb=location,
            ca=lambda c:c in ('ac','ar','bc','br') and (name!='clock_not_typed' or c!='ac'),
            cc=lambda c,f:c in clocks.get(f,()) and not(name=='clock_not_stationary' and c=='ac' or name=='reference_not_stationary' and c=='ar'),
            zbh=lambda f,ctx:'br' if name=='reference_from_other_frame' and f=='A' else 'ar' if f=='A' else 'br',
            zcz=lambda e,f,ctx:(e,f) in {('ae','A'),('be','B')} or name=='second_event_unread' and (e,f)==('extraevent','A'),
            zbe=lambda e,f,u,ctx:'invalid' if name=='invalid_reading' and f=='A' else 'one' if f=='A' else 'two',ce=reading)
        def sync(c,r,f,u,ctx):
            return c in clocks.get(f,()) and r==('ar' if f=='A' else 'br') and (u,ctx)==('time','motion') and (name!='not_synchronized' or c!='ac')
        numbers={'one':1,'two':2,'alias':1,'bad':9}
        callbacks(doc,model,{'ja':sync,'jb':lambda v:v in numbers,'jc':lambda a,b:numbers.get(a,a)==numbers.get(b,b)})
        subset=lambda target:{d['name']:model[d['name']] for d in target['declarations'] if d['kind']=='primitive'}
        local_results=values(local,subset(local),domain)
        local_expected=[name not in {'conflicting_local_reading','missing_reading','clock_not_stationary','reference_not_stationary',
            'reference_from_other_frame','clock_not_typed','clock_unlocated','clock_dropped','not_synchronized','wrong_unit',
            'wrong_context','invalid_reading','event_at_unclocked_place','wrong_event_place'},name not in {'wrong_unit','wrong_context'}]
        if local_results!=local_expected:raise ValueError('Local time uniqueness differs: '+name+repr(local_results))
        # Evaluate the real sgp body above, then tabulate those two supplied
        # event/place fixtures for the outer coverage test. Every other event
        # has no supplied reading. This avoids repeated full-carrier scans in
        # eager implication evaluation; it is not a real-number proof.
        table={('ae','ap','A'):local_results[0],('be','bp','B'):local_results[1]}
        model['sgp']=lambda e,p,f,u,ctx,sync,valid,same:(u,ctx)==('time','motion') and table.get((e,p,f),False)
        actual=values(doc,subset(doc),domain)
        expected=[name in {'baseline','same_value_alias','event_at_unclocked_place'},name not in {'wrong_unit','wrong_context'}]
        if actual!=expected:raise ValueError('Temporal measurement differs: '+name+repr(actual))
        rows[name]=actual
        local_rows[name]=local_results
    return {'cases':rows,'local_readings':local_rows,'real_cut_carrier_substitution':True,
        'outer_scope_uses_tabulated_local_fixtures':True,'synchrony_given_as_oracle':True,'full_real_uniqueness_proved':False}


def actual_cut_checks():
    doc=candidate(source_composed()[0],'''
r ja[] a.r jb[] a.r jc[] a.r jd[] a.r je[] h[b] c.r jf[] d.r jg[] h[h[b] c] c.
q[k sgj[k ja[] k jb[] k jc[] k jd[] k je[] k jf[] k jg[]]].''')
    rows={}
    for value in (-2,0,3):
        for mismatch in (False,True):
            model=guarded(doc)
            model.update(ja=lambda:'place',jb=lambda:'frame',jc=lambda:'x',jd=lambda:'unit',je=lambda:cut(value),jf=lambda:'motion',
                yn=lambda:'x',yo=lambda:'y',yp=lambda:'z',zcu=lambda p,f,c:(p,f,c)==('place','frame','motion'),
                zcv=lambda *a:'projection',zby=lambda *a:'ruler',zbn=lambda *a:'origin',zbo=lambda *a:'axis',
                zcw=lambda *a:a==('place','projection','frame','axis','motion'),
                zcx=lambda r,o,p,f,a,u,v,c:(r,o,p,f,a,u,c)==('ruler','origin','projection','frame','axis','unit','motion') and embedding(v)==value+int(mismatch))
            callbacks(doc,model,{'jg':lambda v:embedding(v) in (-2,0,3)})
            actual=values(doc,model,('place','frame','x','y','z','unit','projection','ruler','origin','axis'))[0]
            if actual==mismatch:raise ValueError('Actual integer-cut coordinate binding differs')
            rows[str(value)+('_wrong' if mismatch else '')]=actual
    return {'cases':rows,'integer_embedding_oracles':True,'arbitrary_real_cuts_evaluated':False}


def wrapper_checks():
    doc=candidate(source_composed()[0],'q[t[k sgn[]][k ri[]]].q[t[k sgs[]][k ri[]]].')
    for i,d in enumerate(doc['declarations']):
        if d['name'] in ('sgl','sgq','ba','sca','qo'):
            doc['declarations'][i]={'kind':'primitive','name':d['name'],
                'parameters':[p['sort'] for p in d['parameters']],'result':d['result']}
    rows={}
    for name in ('baseline','rest_space_invalid','moving_space_invalid','rest_time_invalid','moving_time_invalid','wrong_context'):
        model=guarded(doc)
        model.update(ra=lambda:'rest',zbm=lambda:'moving',zb6=lambda:'other' if name=='wrong_context' else 'motion',ri=lambda:'text',
            ba=lambda value:embedding(value)==1,sca=lambda a,b:embedding(a)==embedding(b),
            qo=lambda c,r,f,u,ctx:(c,r,u,ctx)==('clock','reference','time','motion') and f in ('rest','moving'))
        def numeric(valid,same):return valid(cut(1)) and not valid(cut(2)) and same(cut(1),cut(1)) and not same(cut(1),cut(2))
        def space(f,ctx,valid,same):return f in ('rest','moving') and ctx=='motion' and numeric(valid,same) and name!=f+'_space_invalid'
        def time(f,ctx,sync,valid,same):return (
            f in ('rest','moving') and ctx=='motion' and numeric(valid,same) and sync('clock','reference',f,'time',ctx) and name!=f+'_time_invalid')
        model.update(sgl=space,sgq=time)
        actual=values(doc,model,('rest','moving','clock','reference','time'))
        expected=[name not in {'rest_space_invalid','moving_space_invalid','wrong_context'},name not in {'rest_time_invalid','moving_time_invalid','wrong_context'}]
        if actual!=expected:raise ValueError('Frame measurement wrapper binding differs')
        rows[name]=actual
    return {'cases':rows,'numerical_and_physical_predicates_are_fixture_oracles':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for name in ('baseline','wrong_author','wrong_scope','wrong_context','swapped_content','wrong_prior_setting'):
        model=guarded(doc)
        for key,value in {'zc2':'spatial','zc3':'temporal','zcp':'parallel','rd':'author','rh':'scope','ri':'text'}.items():model[key]=lambda value=value:value
        def adopted(node,author,desc,scope,ctx):
            expected={'spatial':'sgs' if name=='swapped_content' else 'sgn','temporal':'sgn' if name=='swapped_content' else 'sgs'}
            return (author,scope,ctx)==('other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope','other' if name=='wrong_context' else 'text') and json.loads(desc.syntax)['symbol']==expected.get(node)
        model.update(ug=adopted,zao=lambda a,b,s,c:name!='wrong_prior_setting' and (a,b) in {('parallel','spatial'),('spatial','temporal')} and (s,c)==('scope','text'))
        actual=values(doc,model,('spatial','temporal','parallel','author','scope'))
        if actual!=[name=='baseline']*2:raise ValueError('Measurement attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0045')
    digest='adc4984541a1599e358dba1ca4d46bf1d15b67c29cd10e4dc17fbb9f8985c31d'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Measurement source changed')
    return {'segments':[{'unit':unit['id'],'unit_sha256':digest,'start':0,'end':len(unit['text']),'source':unit['text'],
        'definitions':['sgj','sgk','sgl','sgn','sgo','sgp','sgq','sgs'],'status':'partial_operational_reading','full_semantic_equivalence':False}],
        'facsimile_checked':False,'projection_procedure_is_explicit_interpretation':True,'verified_full_units':0}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored measurement differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Measurement roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/frame-measurements-basis-v1.json','data/einstein-frame-measurements-basis-v1.json',
        'examples/v014/einstein-parallel-histories.noema','scripts/compose_frame_measurements.py','scripts/check_frame_measurements.py',
        'noema/discourse.py','noema/finite_semantics.py']
    current=source_composed()[0];previous=(ROOT/'examples/v014/einstein-parallel-histories.noema').read_text(encoding='utf-8')
    return {'status':'partial_frame_local_space_and_time_measurements','documents':documents,
        'spatial_coverage':coverage_checks(),'clock_scope':clock_scope_checks(),'spatial_bindings':spatial_checks(),
        'temporal_bindings':temporal_checks(),'integer_cut_coordinates':actual_cut_checks(),'wrapper_bindings':wrapper_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'added_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Measurement report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Frame-local coordinates, clock coverage and attributed measurement checked')


if __name__=='__main__':main()
