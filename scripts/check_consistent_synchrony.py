"""Check shared candidate assignments and reject finite sampling of all finite families."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,SequenceValue,DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import NUM
from scripts.check_light_roundtrip_definition import setup as prior_setup,DOMAIN as PRIOR_DOMAIN
from scripts.compose_consistent_synchrony import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build
from scripts.review_consistent_synchrony import SOURCE,INVENTORY,DOC,READING,source_record

PRIORS={234:'data/local-clock-valuation-reading-v1.json',235:'data/second-local-clock-reading-v1.json',236:'data/local-times-only-reading-v1.json',237:'data/equal-light-times-reading-v1.json'}
POINTS=('now','other');DOMAIN=PRIOR_DOMAIN+('config','config2','node','firstlaw','secondlaw')


def forbidden(*args):raise ValueError('Unknown consistent-synchrony input')
def value(x):
    if isinstance(x,DescriptionValue):return json.loads(x.syntax)['symbol']
    if isinstance(x,SequenceValue):return tuple(x.items)
    return x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def seq(items):return SequenceValue(tuple(items),json.dumps('individual'))


@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'eild'}|{'family':{'eimw'},'possibility':{'eimx'},'content':{'eim2','qr'}}.get(mode,set()))
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jcs'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jcscontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jcscontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def evaluate(doc,m,domain=DOMAIN):
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)


def run(name,args,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jcscontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)},domain)[0]['value']


def reject_unknown(name,args,m,symbols,mode='native',domain=DOMAIN):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},mode,domain)
        except ValueError as e:assert 'Unknown consistent-synchrony' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))


def setup(middle=2):
    cuts,m,rows,readings,records,values=prior_setup();r=cuts.read
    assignments={('clocka','depart'):Q(0),('clockb','reflect'):Q(middle),('clocka','arrive'):Q(4),('clocka','a2'):Q(5)}
    rows['cb'].add(('a2','placea','frame'));rows['cg']|={('ray2','depart','reflect','frame'),('ray2','reflect','a2','frame')};rows['ch'].add(('ray2','reflect','frame'))
    m|={n:relation(rs) for n,rs in rows.items()}
    m['eisjx']=lambda config,p:'clocka' if p=='placea' else 'clockb'
    m['eisjy']=lambda config,c,e,f,u,s:cuts.make(assignments.get((c,e),Q(0)))
    def history(config,c,f,u,h,s):
        if (config,f,u,s)!=('config','frame','unit','now'):return False
        return all(r(h(e))==x for (clock,e),x in assignments.items() if clock==c)
    m['eisjz']=history
    records={'trial':('placea','placeb','depart','reflect','arrive','ray'),'trial2':('placea','placeb','depart','reflect','a2','ray2')}
    for i,n in enumerate(('qc','qd','qe','qf','qg','qh')):m[n]=lambda t,i=i:records.get(t,records['trial'])[i]
    m['eiska']=relation({('config','placea','placeb','frame','unit','paper','now',t) for t in ('trial','trial2')})
    m['eisjv']=relation({(p,'frame','now') for p in ('placea','placeb')})
    return cuts,m,rows,assignments


@lru_cache(None)
def point_checks():
    domain=('a','b','c','d','e');m={'eisjv':lambda p,f,s:p in domain and (f,s)==('a','now')};count=0
    for items,expected in (((),False),(('a',),True),(('a','a'),False),(('a','b'),True),(domain,True),(('a','b','a'),False)):
        assert run('eimt',[seq(items),'a','now'],m,domain=domain)==expected;count+=1
    assert not run('eimt',[seq(domain),'a','now'],{'eisjv':lambda p,f,s:p!='e'},domain=domain);count+=1
    assert not run('eimt',[seq(('a','b')),'b','now'],m,domain=domain);count+=1
    reject_unknown('eimt',[seq(('a','b')),'a','now'],m,('eisjv',),domain=domain)
    try:run('eimz',['a','a','a','now'],m,domain=domain)
    except ValueError as e:assert 'unbounded sequence domain' in str(e)
    else:raise AssertionError('All finite point families silently sampled')
    return dict(cases=count,nonempty_unique_eligible_points_without_fixed_length=True,all_finite_family_quantification_not_sampled=True)


@lru_cache(None)
def native_trial_checks():
    cuts,m,rows,assignments=setup();pair=['config','placea','placeb','frame','unit','paper','now'];count=0
    assert run('eimv',pair+['trial'],m);count+=1
    assert not run('eimv',pair+['trial2'],m);count+=1
    assert not run('eimw',pair,m);count+=1
    _,other,*_=setup(Q(5,2))
    assert not run('eimv',pair+['trial'],other);count+=1
    assert run('eimv',pair+['trial2'],other);count+=1
    assert not run('eimw',pair,other);count+=1
    # Removing a needed failing trial makes the logical result differ, so completeness is an input contract.
    one={tuple(pair+['trial'])}
    assert run('eimw',pair,m|{'eiska':relation(one)});count+=1
    assert not run('eimw',pair,m|{'eiska':relation(set())});count+=1
    selfpair=pair.copy();selfpair[2]='placea'
    assert run('eimw',selfpair,m|{'eiska':relation(set())});count+=1
    assert not run('eimv',pair+['trial'],m|{'eisjz':lambda *xs:False});count+=1
    for symbol in ('cf','cg','ch','cd','ca','cc','cb','ci','zbd','eild'):
        assert not run('eimv',pair+['trial'],m|{symbol:lambda *xs:False});count+=1
    for i in range(len(pair)):
        bad=pair.copy();bad[i]='other';assert not run('eimv',bad+['trial'],m);count+=1
    # The same clock/event key is used in both trials; no comparison-partner parameter exists.
    seen=[];reading=m['eisjy']
    def record(*xs):seen.append(xs);return reading(*xs)
    assert run('eimv',pair+['trial'],m|{'eisjy':record});count+=1
    assert not run('eimv',pair+['trial2'],m|{'eisjy':record});count+=1
    assert ('config','clockb','reflect','frame','unit','now') in seen
    assert all(len(xs)==6 and xs[0]=='config' and xs[3:]==('frame','unit','now') for xs in seen)
    reject_unknown('eimv',pair+['trial'],m,('eisjx','eisjy','eisjz','qc','qd','qe','qf','qg','qh','cf','cg','ch','eild'))
    return dict(cases=count,native_shared_clock_histories_and_two_conflicting_trials_checked=True,independent_trial_solutions_not_one_shared_solution=True,self_synchrony_and_nonempty_cross_trials_distinguished=True)


@lru_cache(None)
def family_checks():
    points=seq(('a','b'));args=[points,'a','a','a','now','a','now'];count=0
    base={'eisjv':lambda p,f,s:True,'eisjx':lambda config,p:p}
    for bits in product((False,True),repeat=4):
        pairs=dict(zip(product(('a','b'),repeat=2),bits))
        assert run('eimx',args,base|{'eimw':lambda cfg,a,b,f,u,d,s:pairs[a,b]},'family',('a','b'))==all(bits);count+=1
    assert not run('eimx',args,base|{'eimw':lambda *xs:True,'eisjx':lambda *xs:'a'},'family',('a','b'));count+=1
    # Each candidate satisfies a different directed pair; no candidate solves the whole family.
    def pairrule(cfg,a,b,f,u,d,s):return a==b or (cfg=='a' and (a,b)==('a','b')) or (cfg=='b' and (a,b)==('b','a'))
    m=base|{'eimw':pairrule,'eisjw':lambda *xs:True}
    assert not run('eimy',args[:5],m,'family',('a','b'));count+=1
    assert run('eimy',args[:5],m|{'eimw':lambda cfg,*xs:cfg=='b'},'family',('a','b'));count+=1
    seen=[]
    assert run('eimx',args,base|{'eimw':lambda *xs:seen.append(xs) or True},'family',('a','b'));count+=1
    assert set(seen)=={('a',a,b,'a','a','a','now') for a,b in product(('a','b'),repeat=2)}
    reject_unknown('eimx',args,base|{'eimw':lambda *xs:True},('eisjx','eimw','eisjv'),'family',('a','b'))
    return dict(cases=count,all_pairs_share_one_candidate_and_result=True,pairwise_separate_witnesses_rejected=True,distinct_points_have_distinct_clocks=True)


@lru_cache(None)
def possibility_checks():
    points=seq(('a','b'));args=[points,'a','b','a','now'];row=(('a','b'),'a','b','a','now','b','other');count=0
    for candidate,success in product((False,True),repeat=2):
        m={'eisjw':relation({row} if candidate else set()),'eimx':relation({row} if success else set())}
        assert run('eimy',args,m,'possibility',('a','b'))==(candidate and success);count+=1
    for i in range(len(row)):
        bad=tuple((('b',) if i==0 else 'a' if x=='b' else 'b') if j==i else x for j,x in enumerate(row))
        assert not run('eimy',args,{'eisjw':relation({row}),'eimx':relation({bad})},'possibility',('a','b'));count+=1
    reject_unknown('eimy',args,{'eisjw':relation({row}),'eimx':relation({row})},('eisjw','eimx'),'possibility',('a','b'))
    return dict(cases=count,candidate_and_success_share_whole_family_and_scope=True,same_result_required_not_actual_success=True)


def references():
    return {'eiskc':lambda:'node','eiskd':lambda:'firstlaw','eiske':lambda:'secondlaw','eisjs':lambda:'prior','rd':lambda:'author','eirf':lambda:'paper','ra':lambda:'frame','rb':lambda:'unit','ri':lambda:'now'}


@lru_cache(None)
def content_checks():
    count=0;reason=('paper','eim2','qr','now');base=references()
    for possible,laws,explained in product((False,True),repeat=3):
        m=base|{'eim2':lambda p=possible:Content(POINTS,(p,p)),'qr':lambda p=laws:Content(POINTS,(p,p)),'eisdk':relation({reason} if explained else set())}
        assert run('eim3',[],m,'content')==(possible and laws and explained);count+=1
    row=('node','author','eim3','paper','now');m=base|{'ug':relation({row})}
    assert run('eim4',[],m);count+=1
    for i in range(len(row)):
        bad=tuple('other' if i==j else x for j,x in enumerate(row));assert not run('eim4',[],m|{'ug':relation({bad})});count+=1
    assert run('eim4',[],m|{n:forbidden for n in ('eisjw','eisjy','eiska','ca')});count+=1
    return dict(cases=count,possibility_and_laws_are_distinct_assumed_contents=True,also_reason_direction_preserved=True,assumption_does_not_execute_unbounded_quantification=True)


@lru_cache(None)
def presentation_checks():
    rows={'eir3':{('node','author','paper','eim5','now')},'eiskb':{('node','author','prior','eimk','paper','now')},'eiskf':{('node','author','firstlaw','secondlaw','qp','qq','paper','now')},'ue':{('prior','node','now'),('node','firstlaw','now'),('firstlaw','secondlaw','now')}};m=references()|{n:relation(rs) for n,rs in rows.items()};count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:]
        assert evaluate(doc,m)[0]['value'];count+=1
        for symbol,rs in rows.items():
            for row in rs:
                for i in range(len(row)):
                    bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not evaluate(doc,m|{symbol:relation((rs-{row})|{bad})})[0]['value'];count+=1
        assert evaluate(doc,m|{n:forbidden for n in ('ug','eisjw','eisjy','eiska','ca')})[0]['value'];count+=1
    return dict(cases=count,previous_definition_and_ordered_forward_laws_preserved=True,attribution_nonfactive=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==241
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read('data/einstein-local-synchrony-paragraph-review-v1.json'));validate_hashes(ROOT,prior['source_sha256']);assert prior['selection']==selection_binding(new,list(range(234,240)))
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256']);assert source['segments'][0]['nonblank_characters']==149
    rec=json.loads(read(READING));validate_hashes(ROOT,rec['source_sha256']);assert rec['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=240,previous_whole_paragraph_binding_preserved=True,whole_149_character_source_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_consistent_synchrony import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('points',point_checks),('native_trials',native_trial_checks),('family',family_checks),('possibility',possibility_checks),('content',content_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][14]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,'scripts/compose_consistent_synchrony.py','scripts/check_consistent_synchrony.py','scripts/review_consistent_synchrony.py','tests/test_consistent_synchrony.py','scripts/check_light_roundtrip_definition.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py','data/einstein-local-synchrony-paragraph-review-v1.json'}
    return dict(status='shared_consistent_synchrony_for_all_finite_families_assumption_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],source=u['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['全単位判断の登録、u0016/u0017の場所記号と提示の本文接続'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
