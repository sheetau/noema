"""Check durations, opposite directions, and nonfactive definitional adoption."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import NUM,arithmetic
from scripts.compose_equal_light_times import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build
from scripts.review_equal_light_times import SOURCE,INVENTORY,DOC,source_record

READING='data/equal-light-times-reading-v1.json'
PRIORS={234:'data/local-clock-valuation-reading-v1.json',235:'data/second-local-clock-reading-v1.json',236:'data/local-times-only-reading-v1.json'}
POINTS=('now','r1','r2','other')
DOMAIN=('time','ray','backray','start','finish','backstart','backfinish','left','right','frame','unit','paper','pair','pair2','proposal','task','localA','localB','clockA','clockB','author','oldstage','stage','prior','node','other')
PLAN=['proposal','task','time','localA','localB','clockA','clockB','left','right','frame','unit','author','oldstage','stage','paper','now']
SCOPE=['time','left','right','frame','unit','paper','now']


def forbidden(*args):raise ValueError('Unknown equal-light-times input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def changed(row,i):return tuple('other' if j==i else x for j,x in enumerate(row))


@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    if mode!='full_real':abstract(doc,NUM|({'eima'} if mode=='scope' else set()))
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jelt'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jeltcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jeltcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def evaluate(doc,m,domain=DOMAIN):
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def run(name,args,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(slots)==len(args)
    return evaluate(doc,m|{'jeltcontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)},domain)


def reject_unknown(name,args,m,symbols,mode='native',domain=DOMAIN):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},mode,domain)
        except ValueError as e:assert 'Unknown equal-light-times' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))


def setup(values=(1,4,3,20,23,3)):
    cuts,m=arithmetic();vals=tuple(map(Q,values));r=cuts.read
    rows={'cf':{('ray',),('backray',)},'zbd':{(e,) for e in ('start','finish','backstart','backfinish')},'cg':{('ray','start','finish','frame'),('backray','backstart','backfinish','frame')},'cb':{('start','left','frame'),('finish','right','frame'),('backstart','right','frame'),('backfinish','left','frame')},'ci':{('unit',)},'va':{('frame',)}}
    m|={n:relation(rs) for n,rs in rows.items()}
    readings={('time',e,p,'frame','unit',x,'now') for e,p,x in zip(('start','finish','backstart','backfinish'),('left','right','right','left'),(vals[0],vals[1],vals[3],vals[4]))}
    m['eisi5']=lambda t,e,p,f,u,x,s:(t,e,p,f,u,r(x),s) in readings
    fields=('ray','start','finish','backray','backstart','backfinish')
    # Total, explicit candidate fixtures for the eager evaluator; membership remains separate.
    def field(pair,slot,context):
        assert pair in DOMAIN and context in POINTS and slot.denominator==1 and 0<=slot<6
        return fields[int(slot)]
    def numeric(pair,slot,t,f,u,s):
        assert pair in DOMAIN and slot.denominator==1 and 0<=slot<6
        if (t,f,u,s)==('time','frame','unit','now'):return cuts.make(vals[int(slot)])
        return cuts.make(Q(0))
    m|={'eisi6':field,'eisi7':numeric,'eisja':relation({('pair',*SCOPE)})}
    return cuts,m,rows,readings,fields,vals


@lru_cache(None)
def duration_checks():
    cuts,m,rows,readings,fields,vals=setup();args=['time','ray','start','finish','left','right','frame','unit','now']+[cuts.make(x) for x in vals[:3]];count=0
    assert run('eil7',args,m);count+=1
    for i in range(9):
        bad=args.copy();bad[i]='other';assert not run('eil7',bad,m);count+=1
    for symbol,rs in rows.items():
        for row in rs:
            if row[0] in ('backray','backstart','backfinish'):continue
            assert not run('eil7',args,m|{symbol:relation(rs-{row})});count+=1
    for first,last,duration in ((1,4,3),(10,13,3),(1,4,4),(4,1,-3),(1,1,0),(Q(1,2),Q(5,2),2)):
        cc,mm,*_=setup((first,last,duration,20,23,3));a=args[:9]+[cc.make(Q(x)) for x in (first,last,duration)]
        assert run('eil7',a,mm)==(last-first==duration and duration>=0);count+=1
    assert not run('eil7',args,m|{'ba':lambda *xs:False});count+=1
    assert run('eil7',args,m|{n:forbidden for n in ('ch','cd','qo','ce')});count+=1
    reject_unknown('eil7',args,m,('cf','zbd','cg','cb','ci','va','eisi5','ba','bc','bf','sca'))
    try:run('eil7',args,m,'full_real')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Full real domain silently sampled')
    return dict(cases=count,elapsed_time_is_nonnegative_difference=True,same_light_endpoints_assignment_and_units=True,no_reflection_or_already_synchronized_clocks_added=True,full_real_domain_not_sampled=True)


@lru_cache(None)
def opposite_checks():
    cuts,m,rows,readings,fields,vals=setup();args=['pair']+SCOPE;count=0
    assert run('eima',args,m);count+=1
    for i in range(6):
        base=m['eisi6']
        mm=m|{'eisi6':lambda p,s,c,i=i:'other' if s==i else base(p,s,c)}
        assert not run('eima',args,mm);count+=1
        numeric=m['eisi7']
        mm=m|{'eisi7':lambda p,s,t,f,u,c,i=i:cuts.make(Q(99)) if s==i else numeric(p,s,t,f,u,c)}
        assert not run('eima',args,mm);count+=1
    for i in range(1,6):
        bad=args.copy();bad[i]='other';assert not run('eima',bad,m);count+=1
    for values,expected in (((1,4,3,20,23,3),True),((1,4,3,1,4,3),True),((1,4,3,20,24,4),False),((1,4,3,2,4,2),False),((4,1,-3,23,20,-3),False),((Q(1,2),Q(5,2),2,10,12,2),True)):
        _,mm,*_=setup(values);assert run('eima',args,mm)==expected;count+=1
    # Reverse the return propagation only, preserving both endpoint values.
    bad=(rows['cg']-{('backray','backstart','backfinish','frame')})|{('backray','backfinish','backstart','frame')}
    assert not run('eima',args,m|{'cg':relation(bad)});count+=1
    assert run('eimb',SCOPE,m);count+=1
    # Every selector uses the same pair/time/frame/unit/context and all six slots.
    seen=[];seenreal=[];field=m['eisi6'];numeric=m['eisi7']
    def record_field(*xs):seen.append(xs);return field(*xs)
    def record_numeric(*xs):seenreal.append(xs);return numeric(*xs)
    assert run('eima',args,m|{'eisi6':record_field,'eisi7':record_numeric});count+=1
    assert set(seen)=={('pair',Q(i),'now') for i in range(6)}
    assert set(seenreal)=={('pair',Q(i),'time','frame','unit','now') for i in range(6)}
    reject_unknown('eima',args,m,('eisi5','eisi6','eisi7','cg','sca'))
    return dict(cases=count,opposite_directions_and_all_record_slots_checked=True,numerical_durations_not_endpoint_times_compared=True,native_pair_body_and_rule_executed=True)


@lru_cache(None)
def scope_checks():
    scope=['a','a','b','a','a','a','now'];count=0
    for membership,success in product(product((False,True),repeat=2),repeat=2):
        rows={(p,*scope) for p,on in zip(('a','b'),membership) if on};good={(p,*scope) for p,on in zip(('a','b'),success) if on}
        m={'eisja':relation(rows),'eima':relation(good)}
        assert run('eimb',scope,m,'scope',('a','b'))==all(not a or b for a,b in zip(membership,success));count+=1
    # Distinct roles show that the domain and criterion receive the same arguments.
    seen=[];criteria=[]
    assert run('eimb',SCOPE,{'eisja':lambda *xs:seen.append(xs) or True,'eima':lambda *xs:criteria.append(xs) or True},'scope');count+=1
    assert seen and criteria and all(xs[1:]==tuple(SCOPE) for xs in seen+criteria)
    reject_unknown('eimb',scope,{'eisja':lambda *xs:True,'eima':lambda *xs:True},('eisja','eima'),'scope',('a','b'))
    return dict(cases=count,all_corresponding_pairs_checked=True,no_actual_light_population_in_definition=True,domain_not_success_filtered=True)


def references():
    names=('eisje','eisjf','eisjd','eisiw','eisix','eisib','eisik','ziq','zir','ra','rb','rd','eisiy','eisjg','eirf')
    return {n:(lambda x=x:x) for n,x in zip(names,PLAN[:-1])}|{'eisjh':lambda:'node','eisiz':lambda:'prior','ri':lambda:'now'}


def adoption_rows():
    return {'eisjc':{tuple(PLAN)},'eisjb':{('proposal','time','left','right','frame','unit','author','stage','paper','eimb','r1')},'eisiq':{('time','author','stage','paper','r1')},'eisir':{('time',p,'frame','unit','paper','r1') for p in ('left','right')},'eisf2':{('proposal','task','paper','now','r1')}}


@lru_cache(None)
def adoption_checks():
    rows=adoption_rows();m=references()|{n:relation(rs) for n,rs in rows.items()};count=0
    assert run('eimc',PLAN+['r1'],m);count+=1
    assert run('eimd',PLAN,m);count+=1
    assert run('eime',[],m);count+=1
    assert not run('eimc',PLAN+['now'],m);count+=1
    for symbol,rs in rows.items():
        for row in rs:
            assert not run('eimd',PLAN,m|{symbol:relation(rs-{row})});count+=1
            for i in range(len(row)):
                assert not run('eimd',PLAN,m|{symbol:relation((rs-{row})|{changed(row,i)})});count+=1
    for candidate,adopted,defined,shared in product((False,True),repeat=4):
        mm=m|{n:relation(rows[n] if on else set()) for n,on in (('eisf2',candidate),('eisjb',adopted),('eisiq',defined),('eisir',shared))}
        assert run('eimd',PLAN,mm)==(candidate and adopted and defined and shared);count+=1
    # Conditions split across possible outcomes cannot witness one successful adoption.
    shifted={r[:-1]+('r2',) for r in rows['eisir']}
    assert not run('eimd',PLAN,m|{'eisir':relation(shifted),'eisf2':relation(rows['eisf2']|{('proposal','task','paper','now','r2')})});count+=1
    # A later successful candidate is found even when the first candidate has failed.
    late={n:relation({r[:-1]+('r2',) for r in rs}) for n,rs in rows.items() if n!='eisjc'}
    assert run('eimd',PLAN,m|late);count+=1
    assert run('eime',[],m|{n:forbidden for n in ('eisi5','eisi6','eisi7','eisja','cf','cg','ba')});count+=1
    reject_unknown('eimd',PLAN,m,tuple(rows))
    return dict(cases=count,same_possible_result_required=True,rule_adopted_as_definition_not_measured_fact=True,old_and_new_stages_local_clocks_and_places_bound=True,actual_adoption_not_required=True)


@lru_cache(None)
def presentation_checks():
    rows={'eir3':{('node','author','paper','eimf','now')},'eisji':{('node','author','prior','eil2','time','left','right','paper','now')},'ue':{('prior','node','now')}};count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:];m=references()|{n:relation(rs) for n,rs in rows.items()}
        assert evaluate(doc,m);count+=1
        for symbol,rs in rows.items():
            row=next(iter(rs))
            for i in range(len(row)):
                assert not evaluate(doc,m|{symbol:relation({changed(row,i)})});count+=1
        assert not evaluate(doc,m|{n:lambda *xs:True for n in rows}|{'eisiz':lambda:'node'});count+=1
        assert evaluate(doc,m|{n:forbidden for n in ('eisf2','eisjb','eisiq','eisi5','cg')});count+=1
    return dict(cases=count,latter_common_time_anaphora_author_and_order_preserved=True,quoted_definition_possibility_is_nonfactive=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==238
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for index,path in PRIORS.items():
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[index])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256']);assert source['segments'][0]['nonblank_characters']==181
    rec=json.loads(read(READING));validate_hashes(ROOT,rec['source_sha256']);assert rec['selection']==selection_binding(new,[INDEX]) and rec['source_nonblank_characters']==181
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=237,three_prior_sentence_bindings_preserved=True,four_direction_symbols_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_equal_light_times import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('duration',duration_checks),('opposite',opposite_checks),('scope',scope_checks),('adoption',adoption_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][12]
    segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[822,1070],source=u['text'][822:1070],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]
    segments.extend(dict(unit=u['id'],unit_sha256=u['text_sha256'],math_id=m['id'],math_sha256=m['sha256'],definitions=['eime','eimg'],status='explicit_interpretive_annotation') for m in source_record()['segments'][0]['math'])
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,*PRIORS.values(),'scripts/compose_equal_light_times.py','scripts/check_equal_light_times.py','scripts/review_equal_light_times.py','tests/test_equal_light_times.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='equal_opposite_light_durations_and_possible_definitional_adoption_checked',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['第五文の具体的な往復光、第六文の同期式、段落全体の判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
