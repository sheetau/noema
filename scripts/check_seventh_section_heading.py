"""Check separate physical settings/accounts and the seventh heading's scope."""
from functools import lru_cache
from fractions import Fraction as Q
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_resting_charge_force import retag
from scripts.check_aberration_line import setup
from scripts.check_material_relative_frame import NUM
from scripts.compose_seventh_section_heading import *

DOC='docs/seventh-section-heading-v1.md';SOURCE='data/einstein-seventh-section-heading-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg'
DEPENDENCIES=('reports/observed-intensity-v1.json','reports/doppler-specialization-v1.json','reports/aberration-presentation-v1.json','reports/aberration-specialization-v1.json','reports/sixth-section-heading-v1.json')
CONSTANTS={'ra':'frame','eisrx':'section','ri':'case','eisss':'dopplername','eiss3':'aberrationname','eisti':'heading','eispb':'part','eirf':'paper','eisrs':'previous','eisry':'following'}
DOMAIN=tuple(dict.fromkeys([*CONSTANTS.values(),'inquiry','other','a','b','body']))

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|({'ekev','eket'} if name=='ekkp' else {'ekgy'} if name=='ekkq' else {'ekkp','ekkq','eke2','ekhc'})
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode.startswith('slot:'):
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) and s.get('kind')=='function' else s for s in d['parameters']]
                if isinstance(d['result'],dict) and d['result'].get('kind')=='function':d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict) and p['sort'].get('kind')=='function':p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==name);body=d['body']['body'];pivot=int(mode.split(':')[1]);retained=None
        fields=DOPPLER_VARIABLES if name=='ekkp' else ABERRATION_VARIABLES
        for i in range(len(fields)):
            assert body['kind']=='exists'
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        d['body']['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jssh7'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for (n,s),x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=200000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def setting_checks():
    cases=0
    for name,fields,variables,bound in [('ekkp',DOPPLER,DOPPLER_VARIABLES,'eket'),('ekkq',ABERRATION,ABERRATION_VARIABLES,'ekgy')]:
        for pivot,(var,sort) in enumerate(variables):
            mode=f'slot:{pivot}';values={n:('a' if i%2==0 else 'b') for i,(n,t) in enumerate(variables)}
            args=[values[n] for i,(n,t) in enumerate(variables) if i!=pivot]
            for target in ('a','b','unavailable'):
                expected=values|{var:target,'frame':'a','light':'a','scope':'b','context':'case'};row=tuple(expected[n] for n,t in fields)
                m={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b',bound:lambda *xs,row=row:xs==row,'ekev':lambda light,speed,expected=expected:(light,speed)==('a',expected['speed'])}
                assert run(name,args,m,mode,('a','b'))==(target!='unavailable'),(name,var,target);cases+=1
            unknowns(lambda mm:run(name,args,mm,mode,('a','b')),m,(bound,))
        try:run(name,[],{bound:lambda *xs:True,'ekev':lambda *xs:True,'tc':lambda:'a'})
        except ValueError as e:assert 'Finite function domain' in str(e) or 'rational number domain' in str(e),str(e)
        else:raise AssertionError('Infinite settings silently enumerated')
        cases+=1
    cuts,m=setup();c=cuts.make
    for light,speed,expected in [(5,3,True),(5,0,False),(5,-1,False),(5,5,False),(5,6,False),(0,1,False),(-5,1,False)]:
        assert run('ekev',[c(light),c(speed)],m)==expected;cases+=1
    return dict(cases=cases,all_56_and_61_witness_slots_checked=True,infinite_settings_refused=True,native_speed_boundary_checked=True,lower_physical_bodies_reused_from_pinned_reports=True)

@lru_cache(None)
def heading_checks():
    topic={'eisch':{('dopplername','eke2','section','case'),('aberrationname','ekhc','section','case')},'eisth':{('inquiry','ekkp','eke2','case'),('inquiry','ekkq','ekhc','case')}}
    m={n:relation(rs) for n,rs in topic.items()}
    cases=perturb(lambda mm:run('ekkt',['inquiry','case'],mm),m,topic)
    for name in ('ekkr','ekks'):assert run(name,['inquiry','case'],m);cases+=1
    for n,rows in [('eisth',{('inquiry','ekkp','ekhc','case'),('inquiry','ekkq','eke2','case')}),('eisth',{('inquiry','ekkp','eke2','case'),('other','ekkq','ekhc','case')}),('eisth',{('inquiry','ekkp','eke2','case'),('inquiry','ekkq','ekhc','other')})]:
        assert not run('ekkt',['inquiry','case'],m|{n:relation(rows)});cases+=1
    rows={'eisdv':{('heading','section','part','paper',Q(2),Q(7),'case')},'eisdw':{('heading','section','ekkt','case')},'ue':{('previous','heading','case'),('heading','following','case')}}
    cases+=perturb(lambda mm:run('ekku',[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    for name,value in [('eisti','section'),('eisrx','part'),('eisti','previous'),('eisti','following')]:
        assert not run('ekku',[],{n:lambda *xs:True for n in rows}|{name:lambda value=value:value});cases+=1
    return dict(cases=cases,same_inquiry_and_context_for_both_subjects=True,settings_and_accounts_distinct=True,quoted_physics_not_executed=True,section_seven_hierarchy_and_both_order_edges=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][177]
    assert u['id']=='einstein-1905:u0178' and u['kind']=='heading' and not u['math_ids']
    assert digest(u['text'].encode())==u['text_sha256'] and inv['units'][201]['text'].startswith('§ 8.')
    s=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=[],source_nonblank_characters=len(re.sub(r'\s','',u['text'])))
    return dict(version='einstein-seventh-section-heading-reading-v1',reviewer='assistant_visual_and_text_review',pages=['910'],segments=[s],division=dict(level=2,ordinal=7,parent='eispb',first=u['id'],last='einstein-1905:u0201',next_boundary='einstein-1905:u0202'),observations=['原刊910頁で第六節の末尾と次の波の仮定の間にある見出しを照合した。Theorieは両主題へ掛かると読む。','Doppelerschen Prinzipsの印字と属格を保持し、本文の同じ呼称への別表記とする。研究主題の案内は引用した物理設定や法則の断言ではない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,FACSIMILE)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==385 and new.document['statements'][:INDEX]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    oldann=json.loads(read('data/observed-intensity-identifiers-v1.json'));newann=json.loads(read(ANNOTATIONS))
    assert newann['entries'][:-1]==oldann['entries'] and newann['entries'][-1]['forms'][0]['text']=='Doppelerschen Prinzips'
    names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'eihq','eisdv','eisdw','eisth','eket','ekgy','eke2','ekhc','eisch','eisss','eiss3','eisrx'}<=names
    assert not names&{'eir3'}
    d={d['name']:d for d in new.document['declarations']}
    assert d['ekkv']['body']==dict(kind='call',symbol='eisss',arguments=[])
    for name,bound in [('ekkp','eket'),('ekkq','ekgy')]:
        isolated=extract_document(new.document,roots=[name],statement_indices=[]).document
        ns={d['name'] for d in isolated['declarations']};assert bound in ns and not {'eke2','ekhc','ekgo'}&ns
    c=core()
    for style in ('compact','full'):
        body=format_graph(c,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==c
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_reference_individuals=1,previous_384_statements_and_meanings_preserved=True,old_identifier_forms_preserved=True,physical_settings_do_not_assume_printed_laws=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('settings',setting_checks),('heading',heading_checks),('structure',structure_checks)]}
    helpers=('compose_observed_intensity','compose_doppler_specialization','compose_aberration_presentation','compose_doppler_infinity','compose_relativity_conjecture','compose_two_postulates','compose_material_relative_frame','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_resting_charge_force','check_aberration_line','check_material_relative_frame','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_seventh_section_heading.py','scripts/check_seventh_section_heading.py','tests/test_seventh_section_heading.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record()['segments'][0]
    return dict(status='seventh_section_theoretical_subjects_connected',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0178の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
