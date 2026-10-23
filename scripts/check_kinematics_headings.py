"""Check numbered heading roles, topic composition and the simultaneity reference."""
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
from scripts.check_material_relative_frame import arithmetic
from scripts.compose_kinematics_headings import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDICES,build

DOC='docs/kinematics-headings-v1.md';SOURCE='data/einstein-kinematics-headings-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=('data/electrodynamics-title-review-v1.json','data/einstein-author-credit-review-v1.json','data/einstein-opening-paragraph-review-v1.json','data/einstein-principles-paragraph-review-v1.json','data/einstein-kinematics-paragraph-review-v1.json')
DOMAIN=('a','b','paper','part','section','partnode','sectionnode','preceding','frame','unit','clock')
def forbidden(*args):raise ValueError('Unknown kinematics-heading input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    if mode=='assigned':abstract(doc,{'seh','sca'})
    if mode=='unbounded':abstract(doc,{'seg','sca'})
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jkh'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def evaluate(doc,model):
    return evaluate_document(doc,individuals=DOMAIN,situations=('a','b'),
        primitives={d['name']:model.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,
        memoize_definitions=True,memoize_expressions=True)[0]['value']
def run(name,values,model,mode='native'):
    doc,slots=fixture(name,mode);assert len(values)==len(slots)
    return evaluate(doc,model|{n:(lambda x=x:x) for n,x in zip(slots,values)})

def clock_model(first=Q(2),second=Q(2),available=('a','b')):
    cuts,m=arithmetic();times={'a':cuts.make(first),'b':cuts.make(second)}
    rows={'va':{('frame',)},'zbd':{('a',),('b',)},'eisb7':{('frame','clock','unit','a')}}
    def stamp(event,frame,unit,context):
        if (frame,unit,context)!=('frame','unit','a') or event not in times:raise ValueError('Unknown kinematics-heading time')
        return times[event]
    m.update({n:relation(rs) for n,rs in rows.items()})
    m.update(zbe=stamp,zbh=lambda f,c:'clock',seh=lambda e,f,u,c,*args:(e,f,u,c) in {(e,'frame','unit','a') for e in available},seg=lambda *xs:True)
    return m,rows

@lru_cache(None)
def simultaneity_checks():
    count=0
    for first,second,availability in product((Q(-1),Q(0),Q(3)),(Q(-1),Q(0),Q(3)),product((False,True),repeat=2)):
        m,_=clock_model(first,second,tuple(e for e,on in zip(('a','b'),availability) if on))
        assert run('eihm',['a','b','frame','unit','a'],m,'assigned')==(first==second and all(availability));count+=1
    m,rows=clock_model()
    assert run('eihm',['a','a','frame','unit','a'],m,'assigned');count+=1
    for name,rs in rows.items():
        for row in rs:
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                assert not run('eihm',['a','b','frame','unit','a'],m|{name:relation((rs-{row})|{bad})},'assigned');count+=1
    for slot in range(4):
        m,_=clock_model()
        m['seh']=lambda e,f,u,c,*args,s=slot: (e,f,u,c)[s]=='wrong'
        assert not run('eihm',['a','b','frame','unit','a'],m,'assigned');count+=1
    m,_=clock_model()
    for name in ('seh','sca','zbe','eisb7'):
        try:run('eihm',['a','b','frame','unit','a'],m|{name:forbidden},'assigned')
        except ValueError as e:assert 'Unknown kinematics-heading' in str(e)
        else:raise AssertionError('Unknown time assignment accepted')
    # Restore native all-value uniqueness; do not enumerate a rational sample as all real values.
    try:run('eihm',['a','b','frame','unit','a'],m,'unbounded')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Unbounded time uniqueness finitely enumerated')
    ds={d['name']:d for d in parse(read(CORE))['declarations']}
    def calls(node):
        if isinstance(node,dict):
            if node.get('kind')=='call':yield node
            for x in node.values():yield from calls(x)
        elif isinstance(node,list):
            for x in node:yield from calls(x)
    bound=[c for c in calls(ds['eihm']['body']) if c['symbol']=='seh'];assert len(bound)==2
    assert all(c['arguments'][-3:]==[dict(kind='function_ref',symbol=n) for n in ('qo','ba','sca')] for c in bound)
    return dict(cases=count,valid_unique_assignments_before_time_comparison=True,same_frame_unit_and_context=True,unbounded_uniqueness_refused=True,unknown_inputs_rejected=4)

@lru_cache(None)
def topic_checks():
    count=0
    rows={'eisdh':{('a','eigy','a')},'eisdt':{('a','eihm','a')},'eisdu':{('a','a')}}
    m={n:relation(rs) for n,rs in rows.items()}
    assert run('eihn',['a','a'],m);assert run('eihp',['a','a'],m);count+=2
    for subject,definition in product((False,True),repeat=2):
        assert run('eihp',['a','a'],m|{'eisdt':relation(rows['eisdt'] if subject else set()),'eisdu':relation(rows['eisdu'] if definition else set())})==(subject and definition);count+=1
    for name,rs in rows.items():
        target='eihn' if name=='eisdh' else 'eihp';row=next(iter(rs))
        for slot in range(len(row)):
            bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not run(target,['a','a'],m|{name:relation({bad})});count+=1
        try:run(target,['a','a'],m|{name:forbidden})
        except ValueError as e:assert 'Unknown kinematics-heading' in str(e)
        else:raise AssertionError('Unknown topic accepted')
    return dict(cases=count,kinematics_and_definition_subject_composed=True,physical_schemas_not_executed=True,unknown_inputs_rejected=3)

def heading_model(which):
    m=dict(eirf=lambda:'paper',ri=lambda:'a',eisdx=lambda:'part',eisdy=lambda:'section',eisdz=lambda:'partnode',eisd2=lambda:'sectionnode',eisds=lambda:'preceding')
    if which==0:node,division,parent,level,topic,before='partnode','part','paper',Q(1),'eihn','preceding'
    else:node,division,parent,level,topic,before='sectionnode','section','part',Q(2),'eihp','partnode'
    rows={'eisdv':{(node,division,parent,'paper',level,Q(1),'a')},'eisdw':{(node,division,topic,'a')},'ue':{(before,node,'a')}}
    return m|{n:relation(rs) for n,rs in rows.items()},rows

@lru_cache(None)
def presentation_checks():
    count=0
    for path in (CORE,FULL):
        original=parse(read(path))
        for which in (0,1):
            doc=dict(original,statements=[original['statements'][-2+which]])
            m,rows=heading_model(which)
            for bits in product((False,True),repeat=3):
                assert evaluate(doc,m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)})==all(bits);count+=1
            for name,rs in rows.items():
                row=next(iter(rs))
                for slot in range(len(row)):
                    bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not evaluate(doc,m|{name:relation({bad})});count+=1
                try:evaluate(doc,m|{name:forbidden})
                except ValueError as e:assert 'Unknown kinematics-heading' in str(e)
                else:raise AssertionError('Unknown heading structure accepted')
            # True external relations cannot erase the distinction between heading, division and parent.
            yes={n:lambda *xs:True for n in rows}
            if which==0:collisions={'eisdz':'part','eisdx':'paper','eisds':'partnode'}
            else:collisions={'eisd2':'section','eisdy':'part','eisdz':'sectionnode'}
            for name,val in collisions.items():
                assert not evaluate(doc,m|yes|{name:lambda x=val:x});count+=1
    return dict(cases=count,part_one_and_section_one_different_levels=True,same_document_and_parent_division=True,distinct_nodes_and_text_order=True,headings_not_physical_assertions=True,unknown_inputs_rejected=12)

def source_record():
    inv=json.loads(read(INVENTORY));units=inv['units'];selected=[units[i] for i in (5,6)]
    assert [u['text'] for u in selected]==['I. Kinematischer Teil.','§ 1. Definition der Gleichzeitigkeit.']
    assert units[22]['text'].startswith('§ 2.') and units[150]['text']=='II. Elektrodynamischer Teil.'
    paths={INVENTORY,DOC,'scripts/check_kinematics_headings.py','artifacts/einstein-principles-v1/retrieval.json'}
    for row in json.loads(read('artifacts/einstein-principles-v1/retrieval.json'))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-kinematics-headings-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['892'],images=['artifacts/einstein-principles-v1/page-892.jpg'],source_units=[dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],source_nonblank_characters=sum(not c.isspace() for c in u['text'])) for u in selected],divisions=[dict(unit='einstein-1905:u0006',level=1,displayed_number='I',ordinal=1,scope_first='einstein-1905:u0006',scope_last='einstein-1905:u0150',next_boundary='einstein-1905:u0151'),dict(unit='einstein-1905:u0007',level=2,displayed_number='1',ordinal=1,parent='einstein-1905:u0006',scope_first='einstein-1905:u0007',scope_last='einstein-1905:u0022',next_boundary='einstein-1905:u0023')],observations=['原刊892頁で導入第三段落の直後に部見出しと節見出しが続くこと、両番号と句点及び語句を視認した。','部は大きく、節はその下に独立した行で置かれる。字の大きさと中央配置は階層の視認に使い、追加の物理的意味にはしない。','全固定転記の次の同階層見出しから区分の終端を同定した。本文各単位の意味確認が済んだという判断ではない。'],math=[],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==221
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213,214,215,216],[217,218])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert not {'eir3','eisba','eisbb'}&set(ds)
    assert {'eigy','eisdh','seh','saf','qo','ba','sca','eisb7'}<=set(ds)
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record();validate_hashes(ROOT,json.loads(read(SOURCE))['source_sha256'])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=219,prior_reviews_preserved=True,two_numbered_heading_units=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results=dict(simultaneity=simultaneity_checks(),topics=topic_checks(),presentation=presentation_checks(),structure=structure_checks())
    units=json.loads(read(INVENTORY))['units'][5:7]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,'scripts/compose_kinematics_headings.py','scripts/check_kinematics_headings.py','tests/test_kinematics_headings.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','scripts/compose_kinematic_difficulties.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    return dict(status='kinematics_and_simultaneity_headings_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],source=u['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for u in units]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
