"""Check the full selected wave and attributed compatibility proof status."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.compose_wave_compatibility_conclusion import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,GROUPS,build

DOC='docs/wave-compatibility-conclusion-v1.md';SOURCE='data/einstein-wave-compatibility-conclusion-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-spherical-equation-rewrite-u0090-review-v1.json'
DEPENDENCIES=('reports/spherical-equation-rewrite-v1.json','reports/rest-spherical-wave-v1.json','reports/frame-light-law-v1.json','reports/two-postulates-v1.json','reports/light-proof-task-v1.json','reports/spherical-wave-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zge':'previous','zgf':'wave_node','zgg':'proof_node','ra':'rest','zbm':'moving','zfu':'wave','zfv':'emission','zb6':'context','ta':'length','rb':'time'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'a','b','other')));POINTS=('context','discourse','other')

@lru_cache(None)
def core_document():return parse(read(CORE))

@lru_cache(None)
def fixture(name):
    doc=extract_document(core_document(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'ei73','ei44','ei75','eifj','eify'}
    if name=='ejam':bounds.add('ejal')
    if name=='ejan':bounds.add('ejam')
    if name=='ejao':bounds|={'ejag','ejaf'}
    if name=='ejap':bounds|={'ejao','ejan'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jwcc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jwccpoint',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jwccpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def run(name,args,m,domain=DOMAIN,point='discourse'):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}|{'jwccpoint':lambda:point}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def propagation_model():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    rows={'zft':{('a','a','other'),('a','b','other')},'eiscd':{('a','a','a','b','other'),('b','a','a','b','other')},
        'ei73':{('a','a','b','a','a','a','other'),('a','b','b','b','b','a','other')},
        'ei44':{('a','a','b','a',Q(10),'a',Q(5),'other'),('b','b','a','b',Q(15),'a',Q(5),'other')}}
    m|={'ta':lambda:'a','rb':lambda:'b','tc':lambda:c(Q(5)),'wf':lambda s:s,'wh':lambda s:'b','wi':lambda s:'b' if s=='a' else 'a','wj':lambda s:s,'wq':lambda s:c(Q(10 if s=='a' else 15))}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    return cuts,m,rows,norm


@lru_cache(None)
def propagation_checks():
    cuts,m,rows,norm=propagation_model();args=['a','b','a','other']
    # Selection and membership are ranges, not positive conjuncts: removing a
    # selected segment can shrink a supplied range. Vary the required bodies.
    required={n:rows[n] for n in ('ei73','ei44')}
    count=perturb(lambda mm:run('ejal',args,mm,domain=('a','b')),m,required,norm)
    for n,bad in (('wh',lambda s:'a'),('wi',lambda s:s),('wj',lambda s:'a' if s=='b' else 'b'),('wf',lambda s:'b' if s=='a' else 'a'),('wq',lambda s:cuts.make(Q(20))),('tc',lambda:cuts.make(Q(6)))):
        assert not run('ejal',args,m|{n:bad},domain=('a','b'));count+=1
    assert not run('ejal',args,m|{'zft':lambda *xs:False},domain=('a','b'));count+=1
    # A bad interval belonging only to another wave is outside this sentence.
    outside=m|{'zft':relation({('a','a','other')}),'ei44':lambda *xs:norm(xs) in {('a','a','b','a',Q(10),'a',Q(5),'other')}}
    assert run('ejal',args,outside,domain=('a','b'));count+=1
    # The same interval becomes mandatory when its ray joins the target wave.
    assert not run('ejal',args,outside|{'zft':m['zft']},domain=('a','b'));count+=1
    unknowns(lambda mm:run('ejal',args,mm,domain=('a','b')),m,('zft','eiscd','ei73','ei44','wf','wh','wi','wj','wq','tc'))
    return dict(cases=count,nonempty_all_constituent_rays_have_current_origin_paths=True,all_selected_wave_intervals_require_same_emission_and_measured_V=True,interior_interval_start_not_forced_to_emission=True,unrelated_wave_not_promoted_to_universal_light_law=True,two_value_witness_domain_and_pinned_native_measurement_bodies=True)


@lru_cache(None)
def wave_checks():
    count=0
    for name,args,rows in (
        ('ejam',['wave','emission','moving','other'],{'ejal':{('wave','emission','moving','other')},'ei75':{('wave','emission','moving','other')}}),
        ('ejan',[],{'ei75':{('wave','emission','rest','context')},'ejam':{('wave','emission','moving','context')}})):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,args,mm),m,rows)
    return dict(cases=count,both_full_wave_front_and_measured_propagation_required=True,same_wave_emission_both_frames_and_fixed_physical_setting=True)


@lru_cache(None)
def argument_checks():
    count=0
    for name,parts in (('ejao',('ejag','ejaf')),('ejap',('ejao','ejan'))):
        for first,second in product((False,True),repeat=2):
            m={n:lambda on=on:Content(POINTS,(True,on,False)) for n,on in zip(parts,(first,second))}
            assert run(name,[],m)==(first and second);count+=1
        m={parts[0]:lambda:Content(POINTS,(True,False,True)),parts[1]:lambda:Content(POINTS,(False,True,False))}
        assert not run(name,[],m);count+=1
        unknowns(lambda mm:run(name,[],mm),m,parts)
    return dict(cases=count,same_setting_and_equation_and_wave_conclusion_bound=True,no_mixing_truth_at_different_discourse_points=True)


@lru_cache(None)
def compatibility_checks():
    count=0
    cases=(('shared',{'other'},{'other'},{'other'},True),('different',{'context','other'},{'context'},{'other'},False),('empty',set(),{'other'},{'other'},False),('excluded',{'context'},{'other'},{'other'},False),('not_every',{'context','other'},{'other'},{'context','other'},True),('first_false',{'other'},set(),{'other'},False),('second_false',{'other'},{'other'},set(),False))
    for label,allowed,first,second,expected in cases:
        m={'eifj':lambda:Content(POINTS,tuple(s in first for s in POINTS)),'eify':lambda:Content(POINTS,tuple(s in second for s in POINTS)),
           'eiscj':relation({('eifj','eify','discourse',s) for s in allowed})}
        assert run('eif5',[],m)==expected,label;count+=1
    m={'eifj':lambda:Content(POINTS,(False,False,True)),'eify':lambda:Content(POINTS,(False,False,True)),'eiscj':relation({('eifj','eify','discourse','other')})}
    count+=perturb(lambda mm:run('eif5',[],mm),m,{'eiscj':{('eifj','eify','discourse','other')}})
    unknowns(lambda mm:run('eif5',[],mm),m,('eifj','eify','eiscj'))
    return dict(cases=count,current_two_principles_native_shared_admissible_setting=True,separate_worlds_and_empty_scope_rejected=True,truth_at_reference_not_required=True)


@lru_cache(None)
def presentation_checks():
    count=0
    rows=[('ejaq',{'zc':{('wave_node','author','ejao','ejan','section','discourse')}}),
        ('ejar',{'zc':{('proof_node','author','ejap','eif5','section','discourse')},'ui':{('author','proof_node','discourse')}})]
    for body,message,author,node,previous in GROUPS:
        rows.append((author,{'eir3':{(CONSTANTS[node],'author','paper',message,'discourse')},'ue':{(CONSTANTS[previous],CONSTANTS[node],'discourse')}}))
    for name,rs in rows:
        m={n:relation(r) for n,r in rs.items()};count+=perturb(lambda mm:run(name,[],mm),m,rs)
        assert run(name,[],m|{n:forbidden for n in ('ejao','ejan','ejap','eif5','eifj','eify','ei75','ei44')});count+=1
    # Even a false target can be presented as proved; nonfactive attribution is
    # necessary to describe source assertions without verifying their truth.
    rows={'zc':{('proof_node','author','ejap','eif5','section','discourse')},'ui':{('author','proof_node','discourse')}}
    m={n:relation(r) for n,r in rows.items()}|{'eif5':lambda:Content(POINTS,(False,False,False))}
    assert run('ejar',[],m);count+=1
    assert not run('ejar',[],m|{'ui':lambda *xs:False});count+=1
    assert not run('ejar',[],m|{'ui':relation({('author','wave_node','discourse')})});count+=1
    return dict(cases=count,thus_and_hereby_reasons_targets_preserved=True,proof_status_attached_to_same_compatibility_node=True,source_claim_not_validator_proof_certification=True,quotes_not_executed_and_author_section_paper_order_preserved=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][90];math={m['id']:m for m in inv['math']}
    assert u['id']=='einstein-1905:u0091' and u['text_sha256']=='7586e175815928fff932ecfa340d4646ba175f85e1d2e7b0ba320db8faadafe1'
    assert ''.join(ET.fromstring(math['M0147']['mathml']).itertext())=='V'
    segment=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id='M0147',sha256=math['M0147']['sha256'],reading='V')])
    retrieval='artifacts/einstein-light-proof-task-v1/retrieval.json';retrieved=json.loads(read(retrieval));validate_hashes(ROOT,{r['path']:r['sha256'] for r in retrieved['sources']});paths={INVENTORY,DOC,retrieval,*(r['path'] for r in retrieved['sources'])}
    return dict(version='einstein-wave-compatibility-conclusion-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['901'],segments=[segment],observations=['原刊901頁で直前のk二乗式からDie betrachtete Welle ...、Hiermit ist gezeigt ...の二文全体と、次の未知φを決める課題の境界を視認・通読した。','Die betrachtete Welleは同じ検討中の波であり、auchは先行Kでの球面性を受けてkでも同じVの球面波とする帰結。','Hiermitはこの同じ波の設定と変換・結論による議論を指す。unsere beiden Grundprinzipienは既出の相対性と真空光速度の二原理。','ist gezeigtはこの論述段階で著者が示されたとする位置付けであり、以前にまだ証明が提示されていなかった段階を消去しない。','二乗式から未来側の全波面への論理的十分性をこの翻訳で補修しない。結論内容と著者の帰結・証明済みの提示を明示する。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==309
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[306])==prior['selection']
    earlier=json.loads(read('data/einstein-light-proof-task-u0086-review-v1.json'));validate_hashes(ROOT,earlier['source_sha256']);assert selection_binding(new,[304])==earlier['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core_document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[m]['body']['force']=='assert' for _,m,_,_,_ in GROUPS)
    assert not set(ds)&{'shd','smk','sqn','sqv','sqw','sqz','spk'}
    assert {'ei73','ei74','ei75','ei44','eif5','eifj','eify','eiscj','sqh','ui'}<=set(ds)
    # First sentence's target is this wave, not a universal k light-law claim.
    target=extract_document(doc,roots=['ejan'],statement_indices=[])
    assert 'ei43' not in target.retained_symbols and 'eifx' not in target.retained_symbols
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,prior_equation_and_earlier_unproved_stage_preserved=True,whole_current_wave_and_compatibility_not_old_oracles=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('propagation',propagation_checks),('wave',wave_checks),('argument',argument_checks),('compatibility',compatibility_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'data/einstein-light-proof-task-u0086-review-v1.json','docs/semantic-review-v1.md','scripts/compose_wave_compatibility_conclusion.py','scripts/check_wave_compatibility_conclusion.py','tests/test_wave_compatibility_conclusion.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX,INDEX+1],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='same_wave_and_attributed_compatibility_conclusion_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,remaining=['u0091の全文通読判断登録','u0092以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
