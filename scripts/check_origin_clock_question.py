"""Check local clock capabilities, current origin placement and an open rate question."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from xml.etree import ElementTree as ET
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,QuestionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused
from scripts.compose_origin_clock_question import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,build

DOC='docs/origin-clock-question-v1.md';SOURCE='data/einstein-origin-clock-question-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-reciprocal-shape-u0117-review-v1.json'
DEPENDENCIES=('reports/reciprocal-shape-results-v1.json','reports/clock-site-time-v1.json','reports/event-coordinate-task-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisn5':'section','zib':'previous','zif':'setup','zig':'question','zie':'clock','ri':'discourse','eism5':'tname','eisnl':'tauname'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'event','display','record','observed','origin','other','a','b')))
POINTS=('context','trialK','trialk','discourse','other')
BOUNDS={'ejij':{'eit2'},'ejik':{'eiyw'},'ejil':{'sb'},'ejim':{'ejik','ejil'},'ejin':{'ejij','ejik','ejil','ejim'},'ejio':{'ejin'},'ejja':{'eixu'},'ejip':{'ejin','ejja','ejik'},'ejiq':{'ejik','ejil','eiyx','sb'},'ejjb':{'ejiq'},'ejir':{'se','ejjb'},'ejit':{'ejiq'},'ejiu':{'ejip','ejir','ejit'},'ejiv':{'ejiu'},'ejiw':{'ejio','ejip'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'zzbb','zzbd'}|BOUNDS.get(name,set()));doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'},only_sort=RS))==1
    slots=[]
    def slot(sort):
        n='jocq'+number_word(len(slots));slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=sort));return dict(kind='call',symbol=n,arguments=[])
    expr=dict(kind='call',symbol=name,arguments=[slot(p['sort']) for p in d['parameters']])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jocqpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jocqpoint',arguments=[]))
    if name=='ejiv':
        doc['declarations'].append(dict(kind='primitive',name='jocqcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jocqcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jocqpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def numeric():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    m|={'zzbb':c,'zzbd':lambda a,b:c(r(a)+r(b)),'zzbg':lambda a,b:r(a)<r(b)}
    return cuts,m,norm_factory(cuts,(0,1,2))

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

def physical():
    cuts,m,norm=numeric();c=cuts.make;r=cuts.read
    fs={a:FunctionValue((RS,),RS,lambda t,i=i:c(Q(i))) for i,a in enumerate(('x','y','z'))}
    def track(cl,fr,lu,tu,a,ctx):
        if (cl,lu,tu)!=('clock','length','duration') or fr not in ('K','k') or ctx not in POINTS or a not in fs:forbidden()
        return fs[a]
    coords={'record':[0,1,2,1],'observed':[0,1,2,1]}
    def coordinate(rec,axis):
        if rec not in coords or axis not in ('x','y','z','time'):forbidden()
        return c(Q(coords[rec][('x','y','z','time').index(axis)]))
    m|={'eismh':track,'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2)),'zc6':coordinate}
    return cuts,m,norm,fs,coords

@lru_cache(None)
def local_checks():
    cuts,m,norm,fs,coords=physical();c=cuts.make;count=0
    history=['clock','k','context','length','duration',c(Q(0)),c(Q(2)),*fs.values()]
    rows={'ca':{('clock',)},'va':{('k',)},'ci':{('duration',)},'eisdf':{('clock','context')},'eit2':{norm(history)}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejij',['clock','k','context'],mm),mm,rows,norm)
    unknowns(lambda mm:run('ejij',['clock','k','context'],mm),mm,('eismh','eisls','eislt'))
    args=['clock','event','display','record','origin','k','context']
    rows={'eiyw':{('event','record','origin','k','context')},'zab':{('clock','event','origin','k','context')},'zbd':{('display',)},'cb':{('display','origin','k')},'eisgm':{('event','display','clock','k','context')}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejik',args,mm),mm,rows,norm)
    assert run('ejik',args,mm|{'ce':forbidden});count+=1
    for t in (-1,3):
        coords['record'][3]=t;assert not run('ejik',args,mm);count+=1
    coords['record'][3]=1
    rows={'sb':{norm(['clock','event','k','context','length','duration',c(Q(1)),*[c(Q(n)) for n in (0,1,2)]])},'ce':{norm(['clock',e,'k','duration',c(Q(1))]) for e in ('event','display')}}
    mm=relations(m,rows,norm);check=lambda mm:run('ejil',args+[c(Q(1))],mm,'instance')
    count+=perturb(check,mm,rows,norm)
    for axis in range(3):
        coords['record'][axis]+=1;assert not check(mm);coords['record'][axis]-=1;count+=1
    for e in ('event','display'):
        bad=rows['ce']|{norm(['clock',e,'k','duration',c(Q(7))])}
        assert not run('ejil',args+[c(Q(7))],mm|{'ce':lambda *xs:norm(xs) in bad},'instance');count+=1
    assert run('ejil',args+[c(Q(7))],mm,'instance');count+=1
    refused(lambda:run('ejil',args,mm))
    unknowns(check,mm,('zc6','eismh'))
    return dict(cases=count,representative_rest_and_independent_local_candidates=True,all_display_readings_match_current_coordinates=True,native_all_readings_quantifier_retained=True)

@lru_cache(None)
def binding_checks():
    cuts,m,norm=numeric();c=cuts.make;count=0;domain=('a','b')
    def coord(rec,axis):
        if rec not in domain or axis!='a':forbidden()
        return c(Q(domain.index(rec)))
    m|={'rb':lambda:'b','ra':lambda:'a','zc7':lambda:'a','zc6':coord,'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(1))}
    for ev,di,rec,pl in product(domain,repeat=4):
        row=('a',ev,di,rec,pl,'b','context');rows={n:{row} for n in ('ejik','ejil')};mm=relations(m,rows,norm)
        args=['a','b',c(Q(domain.index(rec))),'context']
        count+=perturb(lambda mm:run('ejim',args,mm,domain=domain),mm,rows,norm)
        # Disjoint candidate/calibration witnesses cannot be independently chosen.
        other=('a',ev,di,rec,'a' if pl=='b' else 'b','b','context')
        assert not run('ejim',args,mm|{'ejil':relation({other})},domain=domain);count+=1
    for ev,di,rec,pl,obs in product(domain,repeat=5):
        row=('a',ev,di,rec,pl,obs,'context');rows={'ejiq':{row}};mm=relations(m,rows,norm)
        args=['a',c(Q(domain.index(obs))),'context']
        count+=perturb(lambda mm:run('ejjb',args,mm,domain=domain),mm,rows,norm)
    for ev,di,pl in product(domain,repeat=3):
        rows={'ejiq':{('a',ev,di,'b',pl,'a','context')}};mm=relations(m,rows,norm)
        count+=perturb(lambda mm:run('ejit',['a','b','a','context'],mm,domain=domain),mm,rows,norm)
    return dict(cases=count,shared_four_and_five_witnesses_every_slot=True,actual_event_display_place_and_both_records_bound=True)

@lru_cache(None)
def capability_checks():
    cuts,m,norm=numeric();c=cuts.make;count=0;domain=('a','b')
    m|={'rb':lambda:'b','eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(1))}
    good=('a','a','b','a','b','b','context');bad=('a','b','a','b','a','b','context')
    rows={'ejij':{('a','b','context')},'ejik':{good},'ejil':{good},'ejim':{norm(['a','b',c(Q(1)),'context'])}}
    mm=relations(m,rows,norm);check=lambda mm:run('ejin',['a','b','context',c(Q(1))],mm,'instance',domain)
    assert check(mm);count+=1
    for n in ('ejij','ejil','ejim'):assert not check(mm|{n:lambda *xs:False});count+=1
    assert not check(mm|{'ejik':relation({good,bad})});count+=1
    assert check(mm|{'ejik':lambda *xs:False});count+=1 # Universal restriction alone; time existence remains separately required.
    refused(lambda:run('ejin',['a','b','context'],mm,domain=domain))
    rows={'ca':{('clock',)},'zid':{('clock','K','context','trialK'),('clock','k','context','trialk')},'ejin':{('clock','K','trialK'),('clock','k','trialk')}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejio',['clock','context'],mm),mm,rows,norm)
    assert run('ejio',['clock','context'],mm|{'cc':forbidden,'x4':forbidden});count+=1
    assert not run('ejio',['clock','context'],mm|{'zbm':lambda:'K'});count+=1
    return dict(cases=count,all_candidates_and_every_own_time_required=True,separate_permitted_frame_capabilities_not_simultaneous_actual_rest=True)

@lru_cache(None)
def origin_checks():
    cuts,m,norm,fs,coords=physical();c=cuts.make;count=0
    for a in fs:fs[a]=FunctionValue((RS,),RS,lambda t:c(Q(0)))
    m['zbn']=lambda f,ctx:'origin' if (f,ctx)==('k','context') else forbidden()
    rows={'zbv':{('k','origin','context')},'cb':{('clock','origin','k')},'eixu':{norm(['origin','k',a,c(Q(0)),'context']) for a in ('x','y','z')}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejja',['clock','context',c(Q(1))],mm),mm,rows,norm)
    for a in fs:
        old=fs[a];fs[a]=FunctionValue((RS,),RS,lambda t:c(Q(1)));assert not run('ejja',['clock','context',c(Q(1))],mm);fs[a]=old;count+=1
    for t in (-1,3):assert not run('ejja',['clock','context',c(Q(t))],mm);count+=1
    rows={'ejin':{('a','a','context')},'ejja':{norm(['a','context',c(Q(1))])},'ejik':{('a','a','b','a','b','a','context')}}
    mm=relations(m,rows,norm)|{'rb':lambda:'b','zbm':lambda:'a','zbn':lambda *xs:'b'}
    check=lambda mm:run('ejip',['a','context',c(Q(1))],mm,'instance',('a','b'))
    assert check(mm);count+=1
    for n in ('ejin','ejja'):assert not check(mm|{n:lambda *xs:False});count+=1
    assert not check(mm|{'ejik':relation(rows['ejik']|{('a','b','a','b','a','a','context')})});count+=1
    refused(lambda:run('ejip',['a','context'],mm,domain=('a','b')))
    return dict(cases=count,three_measured_origin_coordinates_and_whole_clock_history=True,all_local_candidates_at_same_origin=True)

@lru_cache(None)
def comparison_checks():
    cuts,m,norm,fs,coords=physical();c=cuts.make;count=0
    args=['clock','event','display','record','origin','observed','context']
    local=('clock','event','display','record','origin','k','context')
    rows={'ejik':{local},'ejil':{local},'eiyx':{('event','observed','K','context')},'sb':{norm(['clock','event','K','context','length','duration',c(Q(1)),*[c(Q(n)) for n in (0,1,2)]])}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejiq',args,mm),mm,rows,norm)
    for i in range(3):
        coords['observed'][i]+=1;assert not run('ejiq',args,mm);coords['observed'][i]-=1;count+=1
    for t in (-1,3):
        coords['observed'][3]=t;assert not run('ejiq',args,mm|{'sb':lambda *xs:True});count+=1
    coords['observed'][3]=1
    history=['clock','K','context','length','duration',c(Q(0)),c(Q(2)),*fs.values()]
    rows={'se':{norm(history)},'eisdd':{('K','length','duration','context')},'ejjb':{norm(['clock',c(Q(1)),'context'])}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejir',['clock','context',c(Q(1))],mm,'instance'),mm,rows,norm)
    assert run('ejir',['clock','context',c(Q(1))],mm|{'eit2':forbidden,'cc':forbidden},'instance');count+=1
    assert not run('ejir',['clock','context',c(Q(1))],mm|{'eislt':lambda *xs:c(Q(0)),'se':lambda *xs:True},'instance');count+=1
    refused(lambda:run('ejir',['clock','context'],mm))
    return dict(cases=count,same_actual_event_current_coordinates_and_representative_path=True,all_lab_times_nonzero_interval_without_lab_rest=True)

@lru_cache(None)
def rate_checks():
    cuts,m,norm=numeric();c=cuts.make;count=0
    for rate,start,end,offset in product((Q(1,2),Q(4,5),Q(2)),(-2,1),(3,5),(-7,0,9)):
        args=[c(Q(n)) for n in (rate,start,end,offset+rate*start,offset+rate*end)]
        assert run('ejis',args,m);count+=1
        for slot in range(5):
            bad=args[:];bad[slot]=c(cuts.read(bad[slot])+Q(1,7));assert not run('ejis',bad,m);count+=1
    for vals in ((0,0,1,0,0),(-1,0,1,0,-1),(1,1,1,2,2),(1,2,1,2,1)):
        assert not run('ejis',[c(Q(n)) for n in vals],m);count+=1
    # Four record individuals suffice for two distinct times with unequal t and tau.
    domain=('a','b','c','d');times={'a':Q(0),'b':Q(4),'c':Q(0),'d':Q(5)}
    def coordinate(rec,axis):
        if rec not in times or axis!='a':forbidden()
        return c(times[rec])
    rows={'ejip':{('a','context')},'ejir':{('a','context')},'ejit':{('a','a','c','context'),('a','b','d','context')}}
    mm=relations(m,rows,norm)|{'zc7':lambda:'a','zc6':coordinate}
    count+=perturb(lambda mm:run('ejiu',['a',c(Q(4,5)),'context'],mm,domain=domain),mm,rows,norm)
    for rate in (0,-1,1):assert not run('ejiu',['a',c(Q(rate)),'context'],mm,domain=domain);count+=1
    # A third point distinguishes the all-pairs rule from selecting one good pair.
    times.update(e=Q(2),f=Q(5,2));three=mm|{'ejit':relation(rows['ejit']|{('a','e','f','context')})};six=(*domain,'e','f')
    assert run('ejiu',['a',c(Q(4,5)),'context'],three,domain=six);count+=1
    times['e']=Q(3);assert not run('ejiu',['a',c(Q(4,5)),'context'],three,domain=six);count+=1
    return dict(cases=count,positive_rate_actual_difference_and_ordered_nonzero_time=True,all_record_pairs_not_one_selected_pair=True)

@lru_cache(None)
def presentation_checks():
    count=0;cuts,m,norm=numeric();c=cuts.make
    got=[]
    def capture(q):assert isinstance(q,QuestionValue);got.append(q);return True
    assert run('ejiv',[],m|{'ejiu':forbidden,'jocqcapture':capture});count+=1
    # Constructing the question never checks an answer or requires one to exist.
    for accepted in (set(),{Q(4,5)},{Q(2)}, {Q(1,2),Q(2)}):
        got.clear();calls=[]
        def candidate(cl,rate,ctx):calls.append((cl,cuts.read(rate),ctx));return cl=='clock' and ctx=='context' and cuts.read(rate) in accepted
        assert run('ejiv',[],m|{'ejiu':candidate,'jocqcapture':capture}) and not calls;count+=1
        for rate in (Q(1,2),Q(4,5),Q(2)):
            assert got[0].function(c(rate))==(rate in accepted);assert calls[-1]==('clock',rate,'context');count+=1
    rows={'ejio':{('clock','context')},'ejip':{('clock','context')}};mm=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejiw',[],mm),mm,rows,norm)
    for name,rows in (
        ('ejix',{'ug':{('setup','author','ejiw','section','discourse')},'zao':{('previous','setup','section','discourse')},'eislo':{('tname','eiwt','paper','discourse'),('tauname','eiym','paper','discourse')}}),
        ('ejiz',{'eir3':{('setup','author','paper','ejiy','discourse')},'ue':{('previous','setup','discourse')}}),
        ('eji2',{'zih':{('question','author','ejiv','section','discourse')}}),
        ('eji4',{'eir3':{('question','author','paper','eji3','discourse')},'ue':{('setup','question','discourse')}})):
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),mm,rows)
    return dict(cases=count,question_has_no_preset_rate_or_existence_claim=True,same_clock_author_thought_setup_addition_and_question_order=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][117];assert u['id']=='einstein-1905:u0118'
    table={x['id']:x for x in inv['math']};math=[]
    for n,flat in zip(range(207,211),('t','τ','k','τ')):
        e=table[f'M{n:04d}'];assert re.sub(r'\s','',''.join(ET.fromstring(e['mathml']).itertext()))==flat
        math.append(dict(id=e['id'],sha256=e['sha256'],mathml_flat=flat))
    paths={INVENTORY,DOC}
    for retrieval in ('artifacts/einstein-sphere-setting-v1/retrieval.json','artifacts/einstein-origin-clock-setting-v1/retrieval.json'):
        rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']});paths|={retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-origin-clock-question-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['903','904'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=math)],observations=['原刊903頁末のWir denken uns fernerから904頁冒頭のangibt.までを改頁をまたいで照合し、続くWie schnellの問いも再読した。','Kに静止した場合のtとkに静止した場合のτの表示能力を持つ同じ時計を、今回はkの原点に置きτを示すようにする。二系への同時の静止ではない。','Wie schnellは同じ時計をKから比較する進み率の問いである。後続のτの変換式とx=vt、平方根の答えはここでは断言しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==339
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[336])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core();ds={d['name']:d for d in doc['declarations']}
    assert ds['ejiy']['body']['force']==ds['eji3']['body']['force']=='assert'
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    names={d['name'] for d in extract_document(doc,roots=['ejiw'],statement_indices=[]).document['declarations']}
    assert {'zid','eit2','eiyw','eisgm','zab','sb','ce','ejja'}<=names and not {'zac','shd','x4'}&names
    qnames={d['name'] for d in extract_document(doc,roots=['ejiv'],statement_indices=[]).document['declarations']}
    assert not {'srd','sky','sre','sti'}&qnames
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=337,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('local',local_checks),('binding',binding_checks),('capability',capability_checks),('origin',origin_checks),('comparison',comparison_checks),('rate',rate_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_moving_trip_geometry','check_clock_site_time','check_material_relative_frame','check_translated_light_trial','check_transverse_segment','check_rod_methods','compose_reciprocal_shape_results','compose_solid_sphere_geometry','compose_rod_methods','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_origin_clock_question.py','scripts/check_origin_clock_question.py','tests/test_origin_clock_question.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=list(INDICES),definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='origin_clock_capabilities_actual_local_readings_and_open_rate_question_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0118全体の通読判断と登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
