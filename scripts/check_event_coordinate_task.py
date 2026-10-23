"""Check measured tuple bindings, correspondence and exact equation questions."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.compose_event_coordinate_task import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,LIMITS,SYSTEM,COORDINATES,build

DOC='docs/event-coordinate-task-v1.md';SOURCE='data/einstein-event-coordinate-task-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-clock-site-time-review-v1.json'
DEPENDENCIES=('reports/clock-site-time-v1.json','reports/measured-space-sentence-v2.json','reports/spatial-coverage-v1.json')
CONSTANTS={'ra':'frame','zbm':'moving','rb':'unit','ta':'lengthunit','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rd':'author','eirf':'paper','ri':'discourse','eisms':'section','zc3':'clocks','zda':'claim','zdb':'task','zcg':'motion','eisna':'kname','eism5':'tname','eisnl':'tauname'}
CONSTANTS.update({sign:printed+'name' for sign,printed,*_ in COORDINATES})
DOMAIN=tuple(dict.fromkeys(['event','tuple','place','otherplace','other',*[x for n,x in CONSTANTS.items() if n not in ('zb6','ri')]]))
POINTS=('context','discourse','other')

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eixq'}
    if name=='eiyw':boundaries|={'eiyv','eiyi','eiyj'}
    if name=='eiyx':boundaries.add('eiyw')
    if name in ('eiyy','eiyz','eiy2','eiy3'):boundaries|={'eiyx','shh'}
    if name in ('eiy4','eiy5'):boundaries|={'eiyz','eiy2','eiyy','shh'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if name=='eiy5':
        doc=parse(format_graph(doc,'compact')+'r jectseq[] '+SYSTEM+'.q[h[k eiy5[]][k jectseq[]]].')
        return doc,['jectseq']
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='ject'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jectpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jectpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,domain=DOMAIN):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jectpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=1500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def measurement_checks():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,());roles=('x','y','z','time');vals=(-2,0,3,7)
    positions={p:(100+i,200+i,300+i) for i,p in enumerate(DOMAIN)};positions['place']=vals[:3]
    rows={'zc5':{('tuple',)},'zcu':{('place','frame','context')},'eixq':{('place','frame',r,'context') for r in roles[:3]}}
    m|={n:relation(rs) for n,rs in rows.items()};m|={'zc6':lambda t,r:c(Q(vals[roles.index(r)])),'zcy':lambda p,f,r,u,ctx:c(Q(positions[p][roles.index(r)]))}
    args=['tuple','place','frame','context'];count=perturb(lambda mm:run('eiyu',args,mm),m,rows)
    for i,r in enumerate(roles[:3]):
        assert not run('eiyu',args,m|{'zc6':lambda t,a,i=i:c(Q(vals[roles.index(a)]+(1 if roles.index(a)==i else 0)))});count+=1
    assert run('eiyu',args,m|{'zc6':lambda t,r:c(Q(99 if r=='time' else vals[roles.index(r)]))});count+=1
    assert not run('eiyu',args,m|{'ba':lambda val:cuts.read(val)!=7});count+=1
    assert not run('eiyu',args,m|{'zc7':lambda:'x'});count+=1
    unknowns(lambda mm:run('eiyu',args,mm),m,('zc6','zcy','ba','sca'))
    assert run('eiyv',args,m);count+=1
    extended=m|{'zcu':relation(rows['zcu']|{('otherplace','frame','context')}),'eixq':relation(rows['eixq']|{('otherplace','frame',r,'context') for r in roles[:3]})}
    assert run('eiyv',args,extended);count+=1
    ambiguous=extended|{'zcy':lambda p,f,r,u,ctx:c(Q(vals[roles.index(r)] if p in ('place','otherplace') else positions[p][roles.index(r)]))}
    assert not run('eiyv',args,ambiguous);count+=1
    assert not run('eiyv',args,m|{'zcu':lambda *xs:False});count+=1
    # Four-component equality is value equality, including separate records.
    # The evaluator is eager. Non-role members of this explicit finite domain
    # get an irrelevant numeric cell; sgt's role predicate excludes that cell.
    vectors={'tuple':vals,'other':vals};mm={n:m[n] for n in NUM if n in m}|{'zc6':lambda t,r:c(Q(vectors[t][roles.index(r)] if r in roles else -31))}
    assert run('shh',['tuple','other'],mm);count+=1
    for i in range(4):
        changed=list(vals);changed[i]+=1
        assert not run('shh',['tuple','other'],mm|{'zc6':lambda t,r,changed=changed:c(Q((changed if t=='other' else vals)[roles.index(r)] if r in roles else -31))});count+=1
    return dict(cases=count,native_sha_eixu_and_all_location_candidates_checked=True,four_component_value_identity_not_record_identity=True,time_component_not_assigned_by_spatial_measurement_alone=True)

@lru_cache(None)
def binding_checks():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,())
    rows={'zc4':{('event',)},'zcz':{('event','moving','context')},'zbd':{('event',)},'va':{('moving',)},'ti':{('lengthunit',)},'ci':{('unit',)},'eiyv':{('tuple','place','moving','context')},'cb':{('event','place','moving')},'eiyi':{('event','place','moving','context')},'eiyj':{('event','moving','context')}}
    m|={n:relation(rs) for n,rs in rows.items()};m|={'zc6':lambda t,r:c(Q(7)) if (t,r)==('tuple','time') else forbidden(),'zbe':lambda *xs:c(Q(7)) if xs==('event','moving','unit','context') else forbidden()}
    args=['event','tuple','place','moving','context'];check=lambda mm:run('eiyw',args,mm)
    count=perturb(check,m,rows);assert not check(m|{'zbe':lambda *xs:c(Q(8))});count+=1
    unknowns(check,m,('zc6','zbe','sca'))
    small=('a','b')
    for e,t,p,f in product(small,repeat=4):
        row=(e,t,p,f,'context');args=[e,t,f,'context'];mm={'eiyw':relation({row})}
        assert run('eiyx',args,mm,small);count+=1
        for i in range(5):
            bad=list(row);bad[i]='wrong'
            assert not run('eiyx',args,{'eiyw':relation({tuple(bad)})},small);count+=1
    unknowns(lambda mm:run('eiyx',['a','b','a','context'],mm,small),{'eiyw':lambda *xs:True},('eiyw',))
    return dict(cases=count,same_event_place_frame_tuple_time_and_context_bound=True,existential_place_checked_with_two_individuals=True)

@lru_cache(None)
def correspondence_checks():
    domain=('a','b','c','d','alias');count=0;out={}
    names=('baseline','empty_events','missing_source','missing_target','two_source_values','two_target_values','equivalent_target_alias','same_input_different_output','coincident_events','swapped_event_targets','equivalent_source_different_output','equivalent_source_same_output')
    for name in names:
        events=set() if name=='empty_events' else {'a','b'};left={('a','a'),('b','b')};right={('a','c'),('b','d')}
        if name=='missing_source':left.remove(('b','b'))
        if name=='missing_target':right.remove(('b','d'))
        if name=='two_source_values':left.add(('a','b'))
        if name=='two_target_values':right.add(('a','d'))
        if name=='equivalent_target_alias':right.add(('a','alias'))
        if name in ('same_input_different_output','coincident_events'):left={('a','a'),('b','a')}
        if name in ('coincident_events','equivalent_source_same_output'):right={('a','c'),('b','c')}
        if name=='swapped_event_targets':right={('a','d'),('b','c')}
        def key(t):return 'c' if t=='alias' else 'a' if t=='b' and name.startswith('equivalent_source_') else t
        same=lambda a,b:key(a)==key(b)
        relation=lambda a,b:any((e,a) in left and (e,b) in right for e in events)
        m={'ra':lambda:'a','zbm':lambda:'b','zc4':lambda e:e in events,'shh':same,'eiyx':lambda e,t,f,ctx:ctx=='context' and (e,t) in (left if f=='a' else right if f=='b' else set())}
        complete=bool(events) and all(all(vals and all(same(a,b) for a in vals for b in vals) for vals in ({t for e,t in left if e==event},{t for e,t in right if e==event})) for event in events)
        source={t for e,t in left if e in events};target={t for e,t in right if e in events}
        functional=bool(source) and all(any(relation(a,b) for b in target) for a in source) and all(same(b,d) for a,c,b,d in product(source,source,target,target) if same(a,c) and relation(a,b) and relation(c,d))
        actual=run('eiy3',[],m,domain);assert actual==(complete and functional),(name,actual);count+=1;out[name]=actual
        for a,b in (('a','c'),('a','d')):assert run('eiyy',[a,b],m,domain)==relation(a,b);count+=1
    return dict(cases=count,outcomes=out,native_sgu_sgv_sgw_and_modern_side_bindings_checked=True,coincident_events_and_equivalent_records_allowed=True,no_cross_event_pairing=True)

@lru_cache(None)
def equation_checks():
    domain=('a','b','c','d','extra');vectors={'a':(0,0,0,0),'b':(1,0,0,0),'c':(2,0,0,0),'d':(3,0,0,0),'extra':(2,1,0,0)}
    doc,slots=fixture('eiy5');element=next(d['result']['element'] for d in doc['declarations'] if d['name']=='jectseq');count=0;out={}
    for name in ('exact','reordered','duplicate_equation','empty','missing_x','missing_y','too_restrictive','invalid_side','no_source_domain','missing_correspondence','nonfunctional_correspondence'):
        cuts,m=numbers();c=cuts.make;r=cuts.read;indices=[0,1,2,3]
        if name=='reordered':indices.reverse()
        if name=='duplicate_equation':indices.append(0)
        if name=='empty':indices=[]
        if name=='missing_x':indices.remove(0)
        if name=='missing_y':indices.remove(1)
        def term(i,a,b,left):
            if name=='invalid_side' and i==3 and not left:return c(Q(99))
            n=vectors[a][i]+(2 if i==0 else 0) if left else vectors[b][i]
            if name=='too_restrictive' and i==1 and left:n+=1
            return c(Q(n))
        terms=tuple(FunctionValue(tuple(element['parameters']),element['result'],lambda a,b,left,i=i:term(i,a,b,left)) for i in indices)
        seq=SequenceValue(terms,json.dumps(element,sort_keys=True,separators=(',',':')))
        pairs={('a','c'),('b','d')}
        if name=='missing_correspondence':pairs.remove(('b','d'))
        if name=='nonfunctional_correspondence':pairs.add(('a','d'))
        m|={'eiyz':lambda t:t in ('a','b') and name!='no_source_domain','eiy2':lambda t:t in ('c','d','extra'),'eiyy':lambda a,b:(a,b) in pairs,'shh':lambda a,b:vectors[a]==vectors[b],'ba':lambda x:r(x)!=99}
        actual=[run(n,[seq],m,domain) for n in ('eiy4','eiy5')];expected=name in ('exact','reordered','duplicate_equation');assert actual==[expected,expected],(name,actual);count+=2;out[name]=actual
        if name=='exact':unknowns(lambda mm:run('eiy4',[seq],mm,domain),m,('eiyz','eiy2','eiyy','shh','ba','sca'))
    return dict(cases=count,outcomes=out,native_sgx_sgy_sgz_exact_solution_set_and_question_agree=True,empty_missing_extra_and_inconsistent_solutions_rejected=True,finite_example_not_a_physical_transformation_derivation=True)

def notation_rows():
    rows={'eislo':{(printed+'name',rule,'paper','discourse') for _,printed,rule,_,_ in COORDINATES}|{('tname','eiwt','paper','discourse'),('tauname','eiym','paper','discourse')},'eisd4':{('motion','author','kname','moving','paper','discourse')}}
    return rows

@lru_cache(None)
def presentation_checks():
    rows=notation_rows();m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eiy6',[],mm),m,rows)
    rows|={'uh':{('claim','author','eiy3','section','discourse')},'zao':{('clocks','claim','section','discourse')},'zdc':{('task','author','eiy5','section','discourse')},'ue':{('claim','task','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiy7',[],mm),m,rows)
    assert run('eiy7',[],m|{n:forbidden for n in ('eiy3','eiy4','eiy5','eiyx','eixq','eiyi')});count+=1
    rows={'eir3':{('claim','author','paper','eiza','discourse')},'ue':{('clocks','claim','discourse')}};m={n:relation(rs) for n,rs in rows.items()}
    count+=perturb(lambda mm:run('eizb',[],mm),m,rows)
    assert run('eizb',[],m|{n:forbidden for n in ('uh','zdc','eiy7','eiy3','eiy5')});count+=1
    return dict(cases=count,eight_quantities_and_preceding_k_name_bound=True,claim_and_equation_task_order_and_scope_distinguished=True,quoted_question_and_physical_content_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][45];assert u['id']=='einstein-1905:u0046' and len(u['text'])==289
    assert u['text_sha256']=='a1b68714d870d447a894ad5f6bb147fae6384314d5523e95faff5a3864888e86'
    count=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',u['text']));assert count==227
    math={m['id']:m for m in inv['math'] if m['id'] in u['math_ids']};forms=('x,y,z,t','k','ξ,η,ζ,τ');bindings=('eiyx/ra','zbm','eiyx/zbm');entries=[]
    for n,s,b in zip(u['math_ids'],forms,bindings):
        assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==s
        entries.append(dict(id=n,sha256=math[n]['sha256'],reading=s,binding=b))
    paths={INVENTORY,DOC,'artifacts/einstein-frame-coordinates-v1/page-898.jpg','artifacts/einstein-frame-coordinates-v1/page-898.html','artifacts/einstein-frame-coordinates-v1/retrieval.json'}
    previous=json.loads(read('data/einstein-clock-site-time-source-reading-v1.json'));validate_hashes(ROOT,previous['source_sha256'])
    assert all(digest((ROOT/p).read_bytes())==previous['source_sha256'][p] for p in paths if p.startswith('artifacts/'))
    paths.add('data/einstein-clock-site-time-source-reading-v1.json')
    return dict(version='einstein-event-coordinate-task-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['898'],unit=u['id'],unit_sha256=u['text_sha256'],range=[0,289],text=u['text'],source_nonblank_characters=227,math=entries,observations=['原刊898頁のZu jedemからzu findenまでの一文と八つの量を照合した。','Wert Systemという固定本文の分かち書きは原刊Wertsystemと同じ値の組を指す。','jenes Ereignisは前半と同じ出来事を指す。Ort und Zeitの特定と出来事個体の同一性を分ける。','und es ist nun die Aufgabeは同じ対応を結ぶ方程式系の探索課題で、式の答えや線形性は後続に残る。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==273
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[270,271])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/clock-site-time-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert ds['eiza']['body']['force']=='assert'
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=272,all_previous_meanings_and_u0045_review_preserved=True,claim_and_task_not_a_solved_equation=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('measurement',measurement_checks),('binding',binding_checks),('correspondence',correspondence_checks),('equations',equation_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_event_coordinate_task.py','scripts/check_event_coordinate_task.py','tests/test_event_coordinate_task.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/compose_coordinate_correspondence.py','scripts/compose_limits.py','scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py'}
    return dict(status='same_event_coordinates_and_equation_task_connected',document=FULL,**results,alignment=dict(segments=[dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0046の一文全体の通読判断登録','u0047以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
