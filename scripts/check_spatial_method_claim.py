"""Check the same spatial candidate, native calculation chain and author roles."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_calculation_discourse import sequence,pair,symbol
from scripts.check_origin_light_ray import RS
from scripts.compose_spatial_method_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,GROUPS,STEPS,build

DOC='docs/spatial-method-claim-v1.md';SOURCE='data/einstein-spatial-method-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-affine-time-u0064-review-v1.json'
DEPENDENCIES=('reports/origin-light-ray-v1.json','reports/frame-light-law-v1.json','reports/event-coordinate-task-v1.json','reports/calculation-discourse-v1.json','reports/affine-time-claim-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zb6':'context','ra':'frame','zbm':'moving','zev':'origin','ze7':'methodnode','ze2':'principles','ze3':'equation','ze4':'rewrite','zez':'restrecord','zey':'movingrecord','yn':'x','yo':'y','yp':'z','zc7':'time','zdb':'task','eisnn':'method'}
DOMAIN=tuple(dict.fromkeys(CONSTANTS.values()))+('first','second','other')
POINTS=('context','discourse','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eion','eios','eiok','ei3c','ei43','ei5a','smn'}
    if name=='ei5c':boundaries.add('eiy4')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if name=='ei5i':
        # A finite chain is constructed inside this interpretation so that its
        # quotations have the interpreter's own identities, not forged objects.
        pairs=json.loads(mode)
        helper=parse('n:r jsmcprogram[a d '+STEPS+'] '+STEPS+'.')['declarations'][0]
        replacement=parse('n:r ei5g[] e.r ei5f[] e.r ei5c[] e.r snp[] e.r smn[] e.r jsmcprogram[a d '+STEPS+'] '+STEPS+'.d zlx[method a stage d] '+STEPS+'[k jsmcprogram[v method v stage '+sequence(pairs)+']].')['declarations'][-1]
        doc['declarations']=[d for d in doc['declarations'] if d['name']!='zlx']
        missing={n for p in pairs for n in p}-{d['name'] for d in doc['declarations']}
        at=next(i for i,d in enumerate(doc['declarations']) if d['name']=='ei5i')
        doc['declarations'][at:at]=[dict(kind='primitive',name=n,parameters=[],result='content') for n in sorted(missing)]+[helper,replacement]
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jsmc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jsmcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jsmcpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jsmcpoint',lambda:'discourse')
    mm.setdefault('jsmcprogram',lambda method,stage,seq:seq if (method,stage)==('method','discourse') else SequenceValue((),seq.element_type))
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def target_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;count=0
    coords={'first':[7,11,13,2],'second':[17,19,23,29]}
    m['zc6']=lambda tup,axis:c(Q(coords.get(tup,[31]*4)[('x','y','z','time').index(axis)])) if axis in ('x','y','z','time') else forbidden()
    m['zb7']=lambda:c(Q(3))
    # A distinguishing tau function tests all four arguments and x'=x-vt.
    m['zd4']=lambda:FunctionValue((RS,RS,RS,RS),RS,lambda x,y,z,t:c(r(x)+2*r(y)+3*r(z)+5*r(t)))
    def candidate(method,stage):
        offset=0 if (method,stage)==('method','discourse') else 100
        return FunctionValue(('individual','individual'),RS,lambda tup,axis:c(Q(({'x':2,'y':3,'z':5}.get(axis,7))+(0 if tup=='first' else 50)+offset)))
    m['eisno']=candidate
    wanted=[[17,2],[19,3],[23,5],[29,72]] # 1+2*11+3*13+5*2
    def signature(seq):
        return tuple(tuple(tuple(bool(eq('first','second',left)(Q(t))) for t in (0,1,2,3,4,5,17,19,23,29,71,72,73,100)) for left in (True,False)) for eq in seq.items)
    expected=tuple(tuple(tuple(Q(t)<Q(x) for t in (0,1,2,3,4,5,17,19,23,29,71,72,73,100)) for x in values) for values in wanted)
    m['eiy4']=lambda seq:signature(seq)==expected
    assert run('ei5c',[],m);count+=1
    for field,other in (('eisnn','other'),('jsmcpoint','other')):
        assert not run('ei5c',[],m|{field:lambda other=other:other});count+=1
    for tup in ('first','second'):
        for i in range(4):
            coords[tup][i]+=1
            # Spatial outputs are independently supplied candidates; changes
            # in K inputs are detected by the retained native time expression.
            assert not run('ei5c',[],m),(tup,i)
            coords[tup][i]-=1;count+=1
    assert not run('ei5c',[],m|{'zb7':lambda:c(Q(4))});count+=1
    assert not run('ei5c',[],m|{'eiy4':lambda seq:False});count+=1
    unknowns(lambda mm:run('ei5c',[],mm),m,('eisno','eiy4','zd4','zc6','zb7'))
    return dict(cases=count,all_four_native_equations_and_tau_input_roles_distinguished=True,same_method_stage_candidate_and_current_equation_question_bound=True,finite_cut_fingerprints_not_general_real_equality=True)

@lru_cache(None)
def chain_checks():
    good=[('ei5g','ei5f'),('ei5f','ei5c')]
    rows={}
    cases={
      'baseline':(good,2,{},True),
      'empty':([],2,{},False),
      'reversed':(list(reversed(good)),2,{},False),
      'wrong_start':([('smn','ei5f'),good[1]],2,{},False),
      'wrong_end':([good[0],('ei5f','snp')],2,{},False),
      'broken':([good[0],('snp','ei5c')],2,{},False),
      'omitted_light_equations':([('ei5g','ei5c')],2,{},False),
      'old_light_equations':([('ei5g','snp'),('snp','ei5c')],2,{},False),
      'expensive_same_method':(good,1,{},False),
      'negative_cost':(good,2,{good[0]:-1},False),
      'repeated_cost_counted':([good[0],('ei5f','ei5f'),good[1]],2,{},False),
      'longer_valid':([good[0],('ei5f','ei5f'),good[1]],3,{},True),
      'cheap_unrelated_step':(good,0,{('snp','ei5c'):0},False),
    }
    for name,(pairs,budget,changed,expected) in cases.items():
        m={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'zlw':lambda a,p,s:(a,p,s)==('author','method','discourse'),'zla':lambda a,b,s:s=='discourse','zlb':lambda step,s:Q(changed.get(pair(step),1)),'zlc':lambda n,s:s=='discourse' and n<=budget}
        mode=json.dumps(pairs);actual=run('ei5i',[],m,mode);assert actual==expected,(name,actual);rows[name]=actual
    m={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'zlw':lambda a,p,s:(a,p,s)==('author','method','discourse'),'zla':lambda a,b,s:s=='discourse' and (symbol(a),symbol(b)) in good,'zlb':lambda step,s:Q(1 if s=='discourse' else 10),'zlc':lambda n,s:s=='discourse' and n<=2}
    mode=json.dumps(good)
    for name,extra in (
      ('unavailable',{'zlw':lambda *xs:False}),('wrong_actor',{'rd':lambda:'other'}),('wrong_method',{'eisnn':lambda:'other'}),('wrong_context',{'jsmcpoint':lambda:'other'}),('forbidden_transition',{'zla':lambda a,b,s:(symbol(a),symbol(b))==good[0]}),('cost_context',{'zlb':lambda step,s:Q(1 if s=='other' else 10)}),('criterion_context',{'zlc':lambda n,s:s=='other' and n<=2}),('program_other_method',{'jsmcprogram':lambda p,s,seq:seq if p=='other' else SequenceValue((),seq.element_type)}),('program_other_stage',{'jsmcprogram':lambda p,s,seq:seq if s=='other' else SequenceValue((),seq.element_type)})):
        assert not run('ei5i',[],m|extra,mode);rows[name]=False
    unknowns(lambda mm:run('ei5i',[],mm,mode),m,('zlw','zla','zlb','zlc'))
    assert run('ei5i',[],m|{n:forbidden for n in ('ei5c','ei5f','ei5g','eisno','eiy4')},mode)
    return dict(cases=rows,native_chain_fold_nonnegative_total_and_same_method_used=True,light_equations_must_occur_in_connected_chain=True,quoted_goal_and_physical_truth_not_executed=True)

@lru_cache(None)
def premise_checks():
    cuts,m=numbers();c=cuts.make
    tau=FunctionValue((RS,RS,RS,RS),RS,lambda *xs:c(Q(0)))
    m|={'tc':lambda:c(Q(5)),'zd4':lambda:tau,'eion':lambda:Content(POINTS,(True,False,False)),'eios':lambda light,ctx:cuts.read(light)==5 and ctx=='context','eiok':lambda a,b,ctx:(a,b,ctx)==('frame','moving','context'),'ei3c':lambda f,ctx:cuts.read(f(*[c(Q(0))]*4))==0 and ctx=='context'}
    assert run('ei5d',[],m);count=1
    for n in ('eion','eios','eiok','ei3c'):
        bad=(lambda:Content(POINTS,(False,False,False))) if n=='eion' else lambda *xs:False
        assert not run('ei5d',[],m|{n:bad});count+=1
    for n in ('ra','zbm','zb6'):
        assert not run('ei5d',[],m|{n:lambda:'other'});count+=1
    assert not run('ei5d',[],m|{'tc':lambda:c(Q(6))});count+=1
    unknowns(lambda mm:run('ei5d',[],mm),m,('eion','eios','eiok','ei3c','tc','zd4'))
    m|={'ei43':lambda frame,light,ctx:frame=='moving' and cuts.read(light)==5 and ctx=='context','ei5a':lambda a,b,ctx:(a,b,ctx)==('restrecord','movingrecord','context'),'smn':lambda:Content(POINTS,(True,True,True))}
    for name,boundary in (('ei5e','ei43'),('ei5l','ei5a'),('ei5f','ei43'),('ei5g','eios')):
        assert run(name,[],m);assert not run(name,[],m|{boundary:lambda *xs:False});count+=2
    for name in ('ei5f','ei5g'):
        assert not run(name,[],m|{'smn':lambda:Content(POINTS,(False,False,False))});count+=1
    return dict(cases=count,same_two_principles_frames_V_context_and_tau_preserved=True,method_premise_keeps_prior_result_and_current_light_equations=True)

@lru_cache(None)
def presentation_checks():
    rows=[('ei5j',{'zf2':{('methodnode','author','smn',('x','y','z'),'task','section','discourse')},'uh':{('methodnode','author','ei5i','section','discourse')}}),('ei5k',{'zc':{('principles','author','ei5d','ei5e','section','discourse')}}),('ei5m',{'zc':{('equation','author','ei5l','snr','section','discourse')}}),('ei5n',{'zd3':{('rewrite','author','ei5l','snr','sns','section','discourse')}})]
    for body,message,author,node,previous in GROUPS:
        rows.append((author,{'eir3':{(CONSTANTS[node],'author','paper',message,'discourse')},'ue':{(CONSTANTS[previous],CONSTANTS[node],'discourse')}}))
    count=0
    for name,relations in rows:
        m={n:relation(rs) for n,rs in relations.items()};count+=perturb(lambda mm:run(name,[],mm),m,relations)
        assert run(name,[],m|{n:forbidden for n in ('ei5i','ei5d','ei5e','ei5l','smn','snr','sns')});count+=1
    return dict(cases=count,method_principle_inference_and_equivalent_rewrite_distinct=True,same_author_section_paper_source_order_and_three_roles_preserved=True,quoted_contents_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    hashes=('7a64a854f5f0e9b0ccc0f77a9a1f274fa96c5cdad236e9d700ea042b90a7fdc3','aa94bd3e0f6b1c6eeed2e6645daa5551af64e457da38517e9d3a5f3e5516c265','b81d9593a3f6c4f7d125fd1da37c9b1fb180574cfb728f3db3c70eda3053e079','2b5131095a90e9fcac122c4f7f1ada4febfe8d4a4f965255a6a05ef40abd0c86')
    readings=dict(zip((f'M{n:04d}' for n in range(118,124)),('ξ,η,ζ','V','τ=0','ξ','ξ=Vτ','ξ=aV(t−v*x′/(V²−v²))')))
    for n,flat in zip(readings,('ξ,η,ζ','V','τ=0','ξ','ξ=Vτ','ξ=aV(t−vV2−v2x′)')):assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==flat
    root=ET.fromstring(math['M0123']['mathml']);assert len(root.findall('.//{*}mfrac'))==1
    assert [''.join(e.itertext()) for e in root.findall('.//{*}msup')]==['V2','v2','x′']
    for i,u in enumerate(inv['units'][64:68]):
        assert u['id']==f'einstein-1905:u{65+i:04d}' and u['text_sha256']==hashes[i]
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n],mathml_flat=''.join(ET.fromstring(math[n]['mathml']).itertext())) for n in u['math_ids']]))
    prior='data/einstein-affine-time-source-reading-v1.json';validate_hashes(ROOT,json.loads(read(prior))['source_sha256'])
    paths={INVENTORY,DOC,prior,'artifacts/einstein-differential-step-v1/page-899.html','artifacts/einstein-differential-step-v1/page-899.jpg','artifacts/einstein-differential-step-v1/retrieval.json'}
    return dict(version='einstein-spatial-method-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['899'],segments=segments,observations=['原刊899頁を先行τの式からMit Hilfe dieses Resultates、二原理の括弧書き、正のξ方向への光線、二つの表示式とoderまで視認した。','ξ,η,ζは求める三空間座標。先行結果は同じτの具体式であり、同じ光速Vを運動系でも測るという等式を用いる方法を述べる。','括弧内のverlangtは光速度不変と相対性の両原理による要請として帰属する。','放出はτ=0、方向はξの増大方向。原点放出は前後とξ=Vτに合わせた明示的な読みである。','二式はξ=Vτ、ξ=aV(t−v*x′/(V²−v²))。oderは同じ条件の下での別表示。a,V、括弧、負号、分母の二乗とx′を保持する。','容易さは文脈上の低負担計算として読む。原文にない手順数や閾値を補わず、u0069以降のV−vとtの消去を混ぜない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-4]==old.document['statements'] and len(new.document['statements'])==293
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[286,287,288])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert all(ds[m]['body']['force']=='assert' for _,m,_,_,_ in GROUPS)
    for n in ('ei5c','ei5d','ei5e','ei5f','ei5g','ei5i','ei5l'):
        extracted=extract_document(doc,roots=[n],statement_indices=[])
        assert not set(extracted.retained_symbols)&{'snq','snk','snc','shd','smk','sfm','sbc'},n
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=2,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,obsolete_ray_and_coordinate_dependencies_not_reintroduced=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('target',target_checks),('chain',chain_checks),('premise',premise_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_spatial_method_claim.py','scripts/check_spatial_method_claim.py','tests/test_spatial_method_claim.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_calculation_discourse.py','scripts/check_rod_methods.py','scripts/check_origin_light_ray.py','scripts/compose_coordinate_correspondence.py','scripts/compose_calculation_discourse.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX,INDEX+1,INDEX+2] if i==0 else [INDEX+2] if i==1 else [INDEX+2,INDEX+3],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='spatial_method_and_two_longitudinal_equations_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,remaining=['u0065–u0068の全文通読判断登録','u0069以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
