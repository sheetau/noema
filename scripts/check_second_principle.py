"""Check one-way rates, emission states and the retained section-one clock rule."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import DescriptionValue,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_vacuum_light_postulate import setup as prior_setup,DOMAIN as PRIOR_DOMAIN
from scripts.compose_second_principle import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDICES,build
from scripts.review_second_principle import SOURCE,INVENTORY,DOC,READING,PRIORS,source_record

POINTS=('context','other');DOMAIN=PRIOR_DOMAIN+('displaystart','displayend','emitterrest','emittermoving','paper','author','intro','first','second','explanation','scope','lightname','durationname','section')
NUM={'ba','bb','bc','bf','sah','sca'}

def forbidden(*args):raise ValueError('Unknown second-principle input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows


@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    if mode!='full_real':abstract(doc,NUM|{'qo'}|({'eifw','eior'} if mode=='scope' else set()))
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jspc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jspccontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jspccontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def run(name,args,m,mode='native'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jspccontext':lambda:'context'}|{n:(lambda x=x:x) for n,x in zip(slots,args)})


def reject_unknown(check,m,symbols):
    for n in symbols:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown second-principle' in str(e)
        else:raise AssertionError(('Unknown input accepted',n))


def setup(path=6,start=1,end=3,second_path=None):
    cuts,m,rows=prior_setup(path,start,end);c=cuts.make;r=cuts.read
    second_path=path if second_path is None else second_path
    normalized=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    rows['eisb6']={(s,'ray','emitterrest' if s=='s' else 'emittermoving','emission','start','end','frame','lengthunit','timeunit','context') for s in ('s','t')}
    rows['eiscb']={(s,'ray','start','end','frame','lengthunit',Q(path if s=='s' else second_path),'context') for s in ('s','t')}
    rows|={'wb':{('emitterrest',),('emittermoving',)},'wc':{('ray',e,'emission','frame','context') for e in ('emitterrest','emittermoving')},'wd':{('emitterrest','frame','emission','context')},'we':{('emittermoving','frame','emission','context')},'zbd':{(x,) for x in ('start','end','displaystart','displayend')},'eisgm':{('start','displaystart','clockstart','frame','context'),('end','displayend','clockend','frame','context')}}
    rows['cb']|={('displaystart','placestart','frame'),('displayend','placeend','frame')}
    rows['ce']|={('clockstart','displaystart','frame','timeunit',Q(start)),('clockend','displayend','frame','timeunit',Q(end))}
    m|={n:(lambda *xs,rs=rs:normalized(xs) in rs) for n,rs in rows.items()}
    def selector(table):
        def get(x):
            if x not in table:raise ValueError('Unknown second-principle input')
            return table[x]
        return get
    # Explicit finite extensions for known non-segment individuals allow the
    # eager evaluator to inspect a false selection antecedent without guessing.
    for n in ('wf','wg','wh','wi','wj','wk','wl','wm','wn','wo','wp','wq'):
        table={s:m[n](s) for s in DOMAIN}
        if n=='wg':table={s:('emittermoving' if s=='t' else 'emitterrest') for s in DOMAIN}
        if n=='wq':table={s:c(Q(second_path if s=='t' else path)) for s in DOMAIN}
        m[n]=selector(table)
    m|={'ra':lambda:'frame','rc':lambda:'reference','tc':lambda:c(Q(3))}
    return cuts,m,rows


@lru_cache(None)
def numeric_checks():
    cuts,m,_=setup();count=0
    for path,duration,speed in product((Q(-1),Q(0),Q(1),Q(6)),(Q(0),Q(2),Q(3)),(Q(0),Q(1,2),Q(2),Q(3))):
        expected=path>0 and duration>0 and speed>0 and path==speed*duration
        assert run('eiov',[cuts.make(x) for x in (path,duration,speed)],m)==expected
        if path>0 and duration>0 and speed>0:assert expected==(speed==path/duration)
        count+=1
    for speed in (Q(3,2),Q(3),Q(6)):
        assert run('eiov',[cuts.make(x) for x in (Q(6),Q(2),speed)],m)==(speed==3);count+=1
    reject_unknown(lambda x:run('eiov',[cuts.make(Q(y)) for y in (6,2,3)],x),m,('ba','bf','sah','bc'))
    try:run('eiov',[cuts.make(Q(x)) for x in (6,2,3)],m,'full_real')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e)
    else:raise AssertionError('Unbounded real arithmetic finitely enumerated')
    unknown=FunctionValue(('number',),'truth',lambda x:x<6)
    try:run('eiov',[unknown,cuts.make(Q(2)),cuts.make(Q(3))],m)
    except ValueError:pass
    else:raise AssertionError('Unknown cut decoded')
    return dict(cases=count,positive_quotient_matches_native_sax=True,no_roundtrip_factor=True,constructed_cut_oracle_not_sampling=True,unbounded_and_unknown_values_refused=True)


@lru_cache(None)
def time_checks():
    count=0
    for start,end,duration,expected in ((1,3,2,True),(-7,-5,2,True),(11,13,2,True),(1,3,1,False),(3,1,-2,False),(1,1,0,False)):
        cuts,m,_=setup(start=start,end=end)
        assert run('eiou',['s',cuts.make(Q(duration)),'context'],m)==expected;count+=1
    cuts,m,rows=setup();args=['s',cuts.make(Q(2)),'context'];check=lambda x:run('eiou',args,x)
    for symbol in ('zbd','eisgm','cb','cc','ce','qo'):
        assert not check(m|{symbol:lambda *xs:False});count+=1
    # Either endpoint's simultaneous display is essential, not merely its value.
    for row in rows['eisgm']:
        for i in range(len(row)):
            bad=tuple('other' if j==i else x for j,x in enumerate(row))
            assert not check(m|{'eisgm':relation((rows['eisgm']-{row})|{bad})});count+=1
    for clock,display,val in (('clockstart','displaystart',Q(1)),('clockend','displayend',Q(3))):
        selected=(clock,display,'frame','timeunit',val)
        bad=(clock,display,'frame','timeunit',val+1)
        def ce(*xs,rs=(rows['ce']-{selected})|{bad}):return tuple(cuts.read(x) if isinstance(x,FunctionValue) else x for x in xs) in rs
        assert not check(m|{'ce':ce});count+=1
    assert not check(m|{'rc':lambda:'other'});count+=1
    reject_unknown(check,m,('eisgm','ce','qo','wo','wp','rc'))
    return dict(cases=count,same_section_one_event_time_rule=True,both_local_simultaneous_displays_required=True,same_reference_and_positive_end_minus_start=True,common_origin_shift_preserved=True,unknown_inputs_rejected=6)


@lru_cache(None)
def emission_checks():
    cuts,m,rows=setup();count=0
    for segment,emitter in (('s','emitterrest'),('t','emittermoving')):
        for rest,moving in product((False,True),repeat=2):
            wd={('emitterrest','frame','emission','context'),('emittermoving','frame','emission','context')} if rest else set()
            we={('emitterrest','frame','emission','context'),('emittermoving','frame','emission','context')} if moving else set()
            assert run('eior',[segment,'context'],m|{'wd':relation(wd),'we':relation(we)})==(rest!=moving);count+=1
    for symbol in ('wb','wc','wd'):
        row=next(row for row in rows[symbol] if 'emitterrest' in row)
        for i in range(len(row)):
            bad=tuple('other' if j==i else x for j,x in enumerate(row))
            assert not run('eior',['s','context'],m|{symbol:relation((rows[symbol]-{row})|{bad})});count+=1
    reject_unknown(lambda x:run('eior',['s','context'],x),m,('wb','wc','wd','we','wg','wh'))
    return dict(cases=count,rest_or_motion_exclusive_not_missing_information=True,same_ray_body_emission_and_frame=True,unknown_inputs_rejected=6)


@lru_cache(None)
def physical_checks():
    cuts,m,rows=setup();args=['s',cuts.make(Q(2)),cuts.make(Q(3)),'context'];count=0
    assert run('eiow',args,m);count+=1
    for symbol in ('eisb5','eisb6','eisca','eiscb','eisb7','eiscc'):
        assert not run('eiow',args,m|{symbol:lambda *xs:False});count+=1
        target=next(row for row in rows[symbol] if symbol not in ('eisb6','eiscb') or row[0]=='s')
        for i in range(len(target)):
            bad=tuple(('other' if isinstance(x,str) else x+1) if j==i else x for j,x in enumerate(target))
            rs=(rows[symbol]-{target})|{bad}
            def rel(*xs,rs=rs):return tuple(cuts.read(x) if isinstance(x,FunctionValue) else x for x in xs) in rs
            assert not run('eiow',args,m|{symbol:rel});count+=1
    # Formula does not require the particular universal value V: a different
    # valid local rate can satisfy the definition while refuting the law.
    cuts,m,_=setup(second_path=7)
    assert run('eiow',['t',cuts.make(Q(2)),cuts.make(Q(7,2)),'context'],m);count+=1
    assert not run('eiot',[],m);count+=1
    cuts,m,_=setup();args=['s',cuts.make(Q(2)),cuts.make(Q(3)),'context']
    assert run('eiow',args,m|{'tc':forbidden,'th':forbidden});count+=1
    reject_unknown(lambda x:run('eiow',args,x),m,('eisb6','eiscb','eisb7','eiscc','wq'))
    return dict(cases=count,physical_path_and_time_bound_to_displayed_ratio=True,arc_length_not_endpoint_distance=True,general_speed_definition_distinct_from_constant_law=True,unknown_inputs_rejected=5)


@lru_cache(None)
def scope_checks():
    count=0
    for valid_s,valid_t,complete in product((False,True),repeat=3):
        cuts,m,rows=setup();valid={s for s,on in (('s',valid_s),('t',valid_t)) if on}
        m['eifw']=lambda s,f,r,x,c:(f,r,c)==('frame','reference','context') and s in valid and cuts.read(x)==3
        m['eior']=lambda s,c:s in ('s','t') and c=='context'
        m['eisce']=relation(rows['eisce'] if complete else set())
        assert run('eiot',[],m,'scope')==(valid_s and valid_t and complete);count+=1
    cuts,m,rows=setup();assert run('eiot',[],m);count+=1
    for symbol in ('eiscd','eisce'):
        assert not run('eiot',[],m|{symbol:lambda *xs:False});count+=1
    assert not run('eiot',[],m|{'zbh':lambda *xs:'clockstart'});count+=1
    for symbol in ('wd','we'):
        assert not run('eiot',[],m|{symbol:lambda *xs:False});count+=1
    m['eifw']=lambda *xs:True;m['eior']=lambda s,c:s!='t'
    assert not run('eiot',[],m,'scope');count+=1
    m['eior']=lambda *xs:True
    assert not run('eiot',[],m|{'rc':lambda:'other'},'scope');count+=1
    reject_unknown(lambda x:run('eiot',[],x,'scope'),m,('eifw','eior','eisce','eiscd','zbh','tc'))
    return dict(cases=count,all_selected_segments_and_emission_states_share_one_V=True,nonempty_complete_scope=True,same_reference_clock_identity=True,unknown_inputs_rejected=6)


def perturb(check,m,rows):
    count=1;assert check(m)
    for symbol,rs in rows.items():
        row=next(iter(rs))
        assert not check(m|{symbol:relation(set())});count+=1
        for i in range(len(row)):
            bad=tuple('other' if j==i else x for j,x in enumerate(row))
            assert not check(m|{symbol:relation({bad})});count+=1
    reject_unknown(check,m,tuple(rows));return count


@lru_cache(None)
def presentation_checks():
    base={n:lambda x=x:x for n,x in {'wt':'second','vk':'first','wu':'intro','eisll':'explanation','rd':'author','eirf':'paper','wv':'scope','eisk4':'lightname','eisln':'durationname','eisdy':'section','ri':'context'}.items()};count=0
    rows={'vl':{('second','author','eiot','scope','context')},'eislh':{('second','author','lightname','eify','eiot','paper','context')}}
    m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda x:run('eio2',[],x),m,rows)
    rows={'eislm':{('explanation','author','eiov','eiow','paper','context')},'eislo':{('durationname','eiou','paper','context')},'eislp':{('explanation','author','section','eing','paper','context')}}
    m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda x:run('eioz',[],x),m,rows)
    assert run('eioz',[],m|{n:forbidden for n in ('ce','qo','eisb6','eisce','tc')});count+=1
    for path in (CORE,FULL):
        original=parse(read(path))
        for which in (0,1):
            doc=dict(original,statements=[original['statements'][-2+which]])
            if which==0:rows={'eir3':{('second','author','paper','eio3','context')},'eislk':{('second','intro',Q(2),'paper','context')},'ue':{('first','second','context')}}
            else:rows={'eir3':{('explanation','author','paper','eio5','context')},'eisa5':{('explanation','author','eiot','eioz','context')},'ue':{('second','explanation','context')}}
            m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda x:evaluate(doc,x),m,rows)
            assert evaluate(doc,m|{n:forbidden for n in ('vl','eislm','eislo','eislp','eisce','tc','ce')});count+=1
    return dict(cases=count,second_numbered_principle_and_following_explanation=True,exact_quantity_rules_and_section_reference=True,quote_does_not_execute_physics_or_unbounded_arithmetic=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==252
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,indices in zip(PRIORS,([249],[243,244],[248])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert prior['selection']==selection_binding(new,indices)
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    entries=json.loads(read(ANNOTATIONS))['entries'];assert entries[:-1]==json.loads(read('data/first-principle-identifiers-v1.json'))['entries']
    assert entries[-1]['symbol']=='eisln' and entries[-1]['forms'][0]['text']=='Zeitdauer'
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert {'eifx','saz','sax','saf','sae','eing','qu','qo'}<=set(ds)
    def calls(node):
        if isinstance(node,dict):
            if node.get('kind')=='call':yield node
            for child in node.values():yield from calls(child)
        elif isinstance(node,list):
            for child in node:yield from calls(child)
    bound=[c for c in calls(ds['eiot']['body']) if c['symbol']=='eios'];assert len(bound)==1
    assert bound[0]['arguments'][0]==dict(kind='call',symbol='tc',arguments=[])
    formula=ds['eiov'];assert formula['body']['kind']=='call' and formula['body']['symbol']=='sax'
    for parameter,slot in ((0,0),(1,2),(2,3)):
        assert formula['body']['arguments'][slot]==dict(kind='variable',name=formula['parameters'][parameter]['name'])
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256']);assert sum(s['nonblank_characters'] for s in source['segments'])==253
    rec=json.loads(read(READING));validate_hashes(ROOT,rec['source_sha256']);assert rec['selection']==selection_binding(new,list(INDICES))
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=250,prior_principle_and_clock_judgments_preserved=True,printed_math_roles_and_first_section_reference_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_second_principle import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('numeric',numeric_checks),('time',time_checks),('emission',emission_checks),('physical',physical_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record()
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,*PRIORS,'scripts/compose_second_principle.py','scripts/check_second_principle.py','scripts/review_second_principle.py','tests/test_second_principle.py','scripts/check_vacuum_light_postulate.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='second_principle_and_one_way_speed_time_definition_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['三原文単位の全体判断登録、u0029以降'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
