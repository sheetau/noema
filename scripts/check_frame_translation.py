"""Check shared translation without freezing the internal mechanism of a clock."""
import argparse
from functools import lru_cache
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks, embedding, guarded, pair_condition
from scripts.check_rod_measurements import ARITHMETIC, cut
from scripts.compose_frame_translation import ROOT, generic_composed, source_composed

REPORT=ROOT/'reports/frame-translation-v1.json'


def values(doc,model,domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=('initial','motion','text','other'),
        primitives=model,max_steps=20_000_000,memoize_definitions=True,memoize_expressions=True)]


def coverage_checks():
    doc=parse(generic_composed()[0]+'''
r ja[] a.r jb[a] c.r jc[a a] c.r jd[a] c.r je[a a] c.r jf[a a a] c.r jg[a a] c.
q[k sfh[k ja[] p jb p jc p jd p je p jf p jg]].''')
    domain=('origin','objecta','objectb','pointa','pointb','first','middle','last')
    times={'first':0,'middle':1,'last':2};rows=[]
    for a,b,pa,pb,available,bad_middle in product((False,True),repeat=6):
        objects={obj for obj,selected in (('objecta',a),('objectb',b)) if selected}
        placed={pair for pair,selected in ((('pointa','objecta'),pa),(('pointb','objectb'),pb)) if selected}
        model={**ARITHMETIC,'ja':lambda:'origin','jb':lambda obj:obj in objects,'jc':lambda p,o:(p,o) in placed,
            'jd':lambda m:m in times,'je':lambda first,last:times.get(first,0)<times.get(last,0),
            'jf':lambda point,first,last:not(bad_middle and (point,first,last)==('pointb','first','middle')),
            'jg':lambda point,moment:available or (point,moment)!=('origin','middle')}
        actual=values(doc,model,domain)[0]
        expected=(a or b) and (not a or pa) and (not b or pb) and available and not(b and pb and bad_middle)
        if actual!=expected:raise ValueError('Placement coverage differs')
        rows.append({'selected_objects':[a,b],'placements':[pa,pb],'origin_available':available,
            'bad_middle_for_second_point':bad_middle,'result':actual})
    return rows


def source_checks(names=None):
    doc=candidate(source_composed()[0],'''
r ja[] d.r jb[] h[h[b] c h[b] c] c.
r jc[] h[h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c] c.
r jd[] h[h[b] c h[b] c] c.r je[] h[h[b] c] c.
q[k sfj[k ja[]]].q[k sfl[k ja[] k jb[] k jc[] k jd[] k je[]]].''')
    all_names=('baseline','origin_wrong_speed','axis_middle_deviation','ruler_transverse_motion','one_clock_wrong_speed',
        'moving_internal_clock_hand','missing_origin_position','missing_clock_position','missing_time_assignment',
        'empty_clock_placement','incomplete_domain','single_time','wrong_time_order','relative_speed_mismatch',
        'replaced_origin','replaced_axis','replaced_ruler','dropped_clock','added_clock','missing_object_transfer',
        'missing_frame_transfer','same_initial_context','wrong_length_unit','wrong_time_frame')
    names=all_names if names is None else names
    axes={'xrole':'xaxis','yrole':'yaxis','zrole':'zaxis'}
    placements={'xaxis':('px','pxend'),'yaxis':('py','pyend'),'zaxis':('pz','pzend'),
        'ruler':('pr','prend'),'clocka':('pa',),'clockb':('pb',)}
    pointnames=['origin',*(p for points in placements.values() for p in points)]
    times={'first':0,'middle':1,'last':2}
    domain=('frame','rest','lengthunit','timeunit','speedunit',*axes,*placements,*pointnames,*times,'hand','other')
    embeddings={i:cut(i) for i in range(-2,40)};rows={}
    for name in names:
        model=guarded(doc)
        constants={'ja':'initial' if name=='same_initial_context' else 'motion','zb4':'initial','zb6':'motion',
            'zbm':'frame','ra':'rest','ta':'other' if name=='wrong_length_unit' else 'lengthunit','rb':'timeunit',
            'tb':'speedunit','yn':'xrole','yo':'yrole','yp':'zrole'}
        for key,val in constants.items():model[key]=lambda val=val:val
        def origin(frame,ctx):return 'other' if name=='replaced_origin' and ctx=='motion' else 'origin'
        def axis(frame,role,ctx):return 'other' if name=='replaced_axis' and ctx=='motion' and role=='xrole' else axes.get(role,'other')
        def ruler(frame,ctx):return 'other' if name=='replaced_ruler' and ctx=='motion' else 'ruler'
        def clocks(frame,clock,ctx):
            selected={'clocka','clockb'}
            if ctx=='motion' and name=='dropped_clock':selected.remove('clockb')
            if ctx=='motion' and name=='added_clock':selected.add('other')
            return frame=='frame' and ctx in ('initial','motion') and clock in selected
        def time(moment,frame,unit,ctx):
            if frame!='rest' or unit!='timeunit' or ctx!='motion' or name=='wrong_time_frame':return embeddings[0]
            return embeddings[times.get(moment,0)]
        def coordinate(point,moment,frame,unit,role,ctx):
            t=times.get(moment,0)
            if frame!='rest' or unit!='lengthunit' or ctx!='motion':return embeddings[0]
            start=pointnames.index(point) if point in pointnames else 0
            if role=='xrole':
                speed=3 if (name=='origin_wrong_speed' and point=='origin' or name=='one_clock_wrong_speed' and point=='pb') else 2
                value=start+speed*t
                if name=='axis_middle_deviation' and (point,moment)==('pxend','middle'):value+=1
                if name=='moving_internal_clock_hand' and point=='hand':value=start+7*t
            elif role=='yrole':value=1+(t if name=='ruler_transverse_motion' and point=='prend' else 0)
            else:value=2
            return embeddings[value]
        model.update(zbn=origin,zbo=axis,zby=ruler,zbz=clocks,
            zbv=lambda frame,o,ctx:(frame,o,ctx)==('frame','origin','motion'),
            zbw=lambda frame,line,role,ctx:(frame,ctx)==('frame','motion') and axes.get(role)==line,
            zbx=lambda frame,ruler,ctx:(frame,ruler,ctx)==('frame','ruler','motion'),
            zca=lambda *args:name!='missing_frame_transfer' and args==('frame','initial','motion'),
            zcb=lambda obj,first,last:(first,last)==('initial','motion') and obj in ('origin',*placements) and not(name=='missing_object_transfer' and obj=='clockb'),
            zcc=lambda point,obj,ctx:ctx=='motion' and point in placements.get(obj,()) and not(name=='empty_clock_placement' and obj=='clockb'),
            zcd=lambda *args:name!='incomplete_domain' and args==('frame','rest','motion'),
            zce=lambda point,moment,frame,unit,ctx:(frame,unit,ctx)==('rest','lengthunit','motion') and point in pointnames and moment in times and not(
                name=='missing_origin_position' and point=='origin' or name=='missing_clock_position' and (point,moment)==('pb','middle')),
            zcf=lambda moment,frame,unit,ctx:(frame,unit,ctx)==('rest','timeunit','motion') and moment in times and not(name=='missing_time_assignment' and moment=='middle'),
            ys=lambda moment,ctx:ctx=='motion' and moment in (('first',) if name=='single_time' else times),
            yl=time,ym=coordinate,zb7=lambda:embeddings[2],
            zbi=lambda *args:embeddings[3 if name=='relative_speed_mismatch' else 2],
            ci=lambda unit:unit=='timeunit',ti=lambda unit:unit=='lengthunit',
            tj=lambda *args:args==('lengthunit','timeunit','speedunit'))
        # Only supplied immutable integer embeddings enter these fixture
        # callbacks. Cache their decoding by identity, not sampled equality.
        integer=lru_cache(maxsize=None)(embedding)
        pair=lru_cache(maxsize=None)(lambda *args:pair_condition(*(integer(x) for x in args)))
        callbacks(doc,model,{
            'jb':lambda first,last:integer(first)>integer(last) if name=='wrong_time_order' else integer(first)<integer(last),
            'jc':pair,'jd':lambda a,b:integer(a)==integer(b),'je':lambda value:True})
        actual=values(doc,model,domain)
        stage_bad={'replaced_origin','replaced_axis','replaced_ruler','dropped_clock','added_clock','missing_object_transfer','missing_frame_transfer','same_initial_context'}
        expected=[name not in stage_bad,name in ('baseline','moving_internal_clock_hand')]
        if actual!=expected:raise ValueError('Frame translation differs: '+name+' '+repr(actual)+' '+repr(expected))
        rows[name]=actual
    return {'cases':rows,'clock_reading_primitive_executed':False,'placement_points_are_not_all_internal_material_points':True,
        'complete_continuous_time_motion_proved':False,'full_real_pair_condition_evaluated':False,
        'integer_embedding_oracles_for_time_order_and_pair_relation':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-1:]
    rows={}
    for name in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_motion','wrong_initial_setup','missing_extension'):
        model=guarded(doc)
        for k,v in {'zcg':'motionnode','zb5':'initialnode','rd':'author','rh':'scope','ri':'text'}.items():model[k]=lambda v=v:v
        model['ug']=lambda node,author,desc,scope,ctx:(node,author,scope,ctx)==('motionnode',
            'other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope',
            'other' if name=='wrong_context' else 'text') and json.loads(desc.syntax)['symbol']==('sfe' if name=='wrong_motion' else 'sfn')
        model['zao']=lambda first,last,scope,ctx:name!='missing_extension' and (first,last,scope,ctx)==(
            'other' if name=='wrong_initial_setup' else 'initialnode','motionnode','scope','text')
        actual=values(doc,model,('motionnode','initialnode','author','scope','other'))[0]
        if actual!=(name=='baseline'):raise ValueError('Frame motion attribution differs')
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0044')
    digest='ac47cdbc668ed13b37de8f87f8e35303185a24899f06aa94af78d1768b8a5ae5'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Frame motion source changed')
    end=unit['text'].index('Jeder Zeit')
    while unit['text'][end-1].isspace():end-=1
    return {'segments':[{'unit':unit['id'],'unit_sha256':digest,'start':0,'end':end,'source':unit['text'][:end],
        'definitions':['sfi','sfj','sfk','sfl','sfm','sfn'],'status':'partial_explicit_reading','full_semantic_equivalence':False}],
        'verified_full_units':0,'facsimile_checked':False,'later_symmetry_and_parallel_configuration_not_yet_composed':True}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored frame motion differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Frame motion roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/frame-translation-basis-v1.json','data/einstein-frame-translation-basis-v1.json',
        'examples/v014/einstein-coordinate-frames.noema','scripts/compose_frame_translation.py','scripts/check_frame_translation.py',
        'noema/discourse.py','noema/finite_semantics.py']
    current=source_composed()[0];previous=(ROOT/'examples/v014/einstein-coordinate-frames.noema').read_text(encoding='utf-8')
    return {'status':'partial_common_frame_translation_with_preserved_instruments','documents':documents,
        'coverage':coverage_checks(),'source_adapter':source_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'added_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Frame translation report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Shared translation, placement coverage, object identity and assumption extension checked')


if __name__=='__main__':main()
