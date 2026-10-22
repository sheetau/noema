"""Validate the composed depiction with native growth, resistance, goal and care bodies."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as F
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_nurtured_germ import ROOT,LIBRARY,BASIS,GOAL,MEANINGS,PRIMITIVES,LIMITS,parent,main_catalog,legacy,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scoped_counts import arithmetic

DOC='docs/nurtured-germ-v1.md';READING='data/nurtured-germ-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v206.json'
FETCH='artifacts/nurtured-germ-v1/fetch.json'
PRIORS=('reports/germ-regime-connection-v1.json','reports/covered-unfolding-v1.json','reports/dispositional-resistance-v1.json','reports/tender-care-v1.json')
DOMAIN=('germ','cover','nature','process','other','power')
SCENES=('reference','other','before','start','middle','end','after','loadone','loadtwo')
HISTORY=('start','middle','end');PLANTS=('germ','other');TESTS=('germ','other')
CONSTANTS=dict(reference='reference',nature='nature',germ='germ',object='germ',cover='cover',process='process',start='start',end='end',point='middle')
GROWTH=('reference','nature','germ','cover','process','start','end')
TARGET='k r6jj[r[k zreference[]]]';ALIAS='r[i[bindings j[a]][b point[k zalias[v bindings v point]]]]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def seq(xs):return SequenceValue(tuple(xs),'"individual"')
def norm(x):return (x.rank,json.dumps(json.loads(x.syntax),sort_keys=True)) if hasattr(x,'syntax') else x
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),capture=True):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if value in DOMAIN else 'd')+'.' for n,value in CONSTANTS.items())
    extra+='r zother[] d.r zalias[j[a] d] c.r zcapture[i[d] i[d] '+GOAL+' '+GOAL+'] c.'
    prefix=parse('p:'+extra)['declarations'];ns={r['name'] for r in prefix}
    d['declarations']=prefix+d['declarations'];d['declarations']=closure(d,(*roots,*ns,*(('r6jj',) if capture else ())))
    if capture:query='q[k zcapture[r[k zreference[]] r[k zother[]] '+TARGET+' '+ALIAS+']].'+query
    return parse(format_graph(d,'compact')+query)

def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};codes=[]
    v.update(arithmetic());v.update({'z'+n:lambda value=value:value for n,value in CONSTANTS.items()})
    def capture(*a):codes[:]=a;return True
    def features(r,o,f):return r=='reference' and ((o=='germ' and f in ('germ','cover')) or(o,f)==('other','cover'))
    def history(r,o,s,e,p):return (r,o,s,e)==('reference','germ','start','end') and p in HISTORY
    def measurements(r,o,test,protocol,force,length,point):
        return (r,o,protocol,force,length)==('reference','cover','nature','process','power') and test in TESTS and point in ('loadone','loadtwo')
    def aims(r,actor,act,goal,bindings,p):
        return (r,actor,act)==('reference','nature','other') and norm(goal)==norm(codes[2]) and bindings.items in (('germ',),('other',)) and p in HISTORY
    v.update(zother=lambda:'other',zcapture=capture,h223h=lambda r:codes[0 if r=='reference' else 1],
      h27ax=lambda body,r:body in PLANTS and r=='reference',h27ay=lambda power,body,r:power=='power' and body in PLANTS and r=='reference',
      h27az=lambda nature,power,r:(nature,power,r)==('nature','power','reference'),
      h225t=lambda plant,p:plant in PLANTS,h27a2=lambda o,r,p:(o,r,p)==('germ','reference','start'),
      h27a3=history,h27a4=lambda r,o,s,e,l,h:history(r,o,s,e,l) and history(r,o,s,e,h) and HISTORY.index(l)<HISTORY.index(h),
      h27a5=lambda *a:a==('reference','process','start','end'),h27a6=lambda *a:a==('reference','process','germ','start','end'),
      h27a7=features,h27ba=lambda r,o,f,p:features(r,o,f) and(o,p)==('germ','start'),
      h27bb=lambda r,o,f,p:features(r,o,f) and o=='germ' and(p=='end' or(f=='cover' and p=='start')),
      h27bc=lambda cover,germ,p:(cover,germ)==('cover','germ') and p in HISTORY,
      h27bd=lambda r,n:seq(PLANTS),h27be=lambda r,n,o:(r,n)==('reference','nature') and o in PLANTS,
      h27bf=aims,h27bg=lambda n,o,p:(n,o)==('nature','germ') and p in HISTORY,
      h27bh=lambda n,o,p:n=='nature' and o in PLANTS and p in HISTORY,
      h27bi=lambda n,o,p:F(3 if o=='germ' else 2),hzzb=lambda power,p:(power,p)==('power','middle'),
      h27bj=lambda *a:a==('power','process','germ','start','end'),
      dg=lambda act,p:(act,p)==('process','end') or(act=='other' and p in HISTORY),
      df=lambda actor,act,p:actor=='nature' and ((act,p)==('process','end') or(act=='other' and p in HISTORY)),
      h27bk=lambda r,o:seq(TESTS),h27bl=lambda r,o,t:(r,o)==('reference','cover') and t in TESTS,
      h27bm=lambda r,o:'nature',h27bn=lambda r,o:'process',h27bo=lambda r,o:'power',h27bp=lambda r,o:F(5),h27bq=lambda r,o:F(1,2),
      h27br=measurements,h27bs=lambda *a:F(6) if measurements(*a) else F(0),h27bt=lambda *a:F(1,2) if measurements(*a) else F(0),
      h27bu=lambda r,o,t,m,f,l,anchor,candidate:anchor in HISTORY and measurements(r,o,t,m,f,l,candidate))
    return v,codes
def run(d,v,memo=True):return evaluate(d,v,DOMAIN,SCENES,memo)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def nature_checks():
    d=fixture(('r6jf',),'q[k r6jf['+args(('nature','reference'))+']].',capture=False);base,_=model(d);count=0
    bodies=('germ','other');powers=('power','cover');edges=tuple(product(powers,bodies))
    for relation in product((False,True),repeat=4):
        actual={edge for edge,chosen in zip(edges,relation) if chosen};expected={p for p,b in actual}
        for flags in product((False,True),repeat=2):
            membership={p for p,chosen in zip(powers,flags) if chosen};v=dict(base)
            v['h27ay']=lambda p,b,r:r=='reference' and(p,b) in actual
            v['h27az']=lambda n,p,r:(n,r)==('nature','reference') and p in membership
            assert run(d,v)==[bool(expected) and membership==expected];count+=1
    return dict(two_bodies_two_powers_all_relations_and_memberships=count,nonempty_exact_natural_power_aggregate=True)

@lru_cache(None)
def resistance_checks():
    d=fixture(('r6jk',),'q[k r6jk['+args(('reference','cover','point'))+']].',capture=False);v,_=model(d)
    assert run(d,v)==[True];cases={}
    for name in ('empty_tests','omitted_test','duplicate_test','missing_prospects','missing_one_test_prospects','unassessed',
      'bad_one_response','negative_deformation','weak_load','nonpositive_minimum','negative_maximum','wrong_protocol','wrong_forceunit','wrong_lengthunit','wrong_reference','wrong_cover'):
        w=dict(v)
        if name=='empty_tests':w['h27bk']=lambda *a:seq(())
        if name=='omitted_test':w['h27bk']=lambda *a:seq(('germ',))
        if name=='duplicate_test':w['h27bk']=lambda *a:seq(('germ','germ','other'))
        if name=='missing_prospects':w['h27bu']=lambda *a:False
        if name=='missing_one_test_prospects':w['h27bu']=lambda *a:a[2]!='other' and v['h27bu'](*a)
        if name=='unassessed':w['h27br']=lambda *a:a[2]!='other' and v['h27br'](*a)
        if name=='bad_one_response':w['h27bt']=lambda *a:F(1) if(a[2],a[-1])==('other','loadtwo') else v['h27bt'](*a)
        if name=='negative_deformation':w['h27bt']=lambda *a:F(-1)
        if name=='weak_load':w['h27bs']=lambda *a:F(4)
        if name=='nonpositive_minimum':w['h27bp']=lambda *a:F(0)
        if name=='negative_maximum':w['h27bq']=lambda *a:F(-1)
        if name=='wrong_protocol':w['h27bm']=lambda *a:'germ'
        if name=='wrong_forceunit':w['h27bn']=lambda *a:'germ'
        if name=='wrong_lengthunit':w['h27bo']=lambda *a:'germ'
        if name=='wrong_reference':w['zreference']=lambda:'other'
        if name=='wrong_cover':w['zcover']=lambda:'other'
        assert run(d,w)==[False],name;cases[name]=False
    assert not v['h27br']('reference','cover','germ','nature','process','power','middle')
    for n in ('h27bk','h27bl','h27bu','h27br','h27bs','h27bt'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=cases,native_ryu_rys_rcm=True,actual_anchor_not_loaded_or_assessed=True,unknown_rejected=True)

@lru_cache(None)
def care_checks():
    q='q[k r6jl['+args(('reference','nature','object','point'))+']].'
    d=fixture(('r6jl',),q);v,cs=model(d);assert run(d,v)==[True,True];cases={}
    # Goal execution is absent from care; even a completely unmet goal can be cared for.
    v['h27bb']=unknown;assert run(d,v)==[True,True]
    for name in ('unclassified','unclassified_comparator','negative_degree','comparator_greater','no_affection','no_act','reversed_actor_act',
      'wrong_goal','wrong_bindings','uncared_comparator','bad_reference_name','empty_scope_list','missing_comparator','duplicate_comparator','not_plant','empty_feature_scope'):
        w=dict(v)
        if name=='unclassified':w['h27bh']=lambda *a:False
        if name=='unclassified_comparator':w['h27bh']=lambda *a:a[1]!='other' and v['h27bh'](*a)
        if name=='negative_degree':w['h27bi']=lambda *a:F(-1)
        if name=='comparator_greater':w['h27bi']=lambda n,o,p:F(2 if o=='germ' else 3)
        if name=='no_affection':w['h27bg']=lambda *a:False
        if name=='no_act':w['dg']=lambda *a:False
        if name=='reversed_actor_act':w['df']=lambda actor,act,p:v['df'](act,actor,p)
        if name=='wrong_goal':w['h27bf']=lambda r,n,a,g,b,p:norm(g)==norm(cs[3])
        if name=='wrong_bindings':w['h27bf']=lambda r,n,a,g,b,p:b.items==('cover',)
        if name=='uncared_comparator':w['h27bf']=lambda r,n,a,g,b,p:b.items!=('other',) and v['h27bf'](r,n,a,g,b,p)
        if name=='bad_reference_name':w['h223h']=lambda *a:cs[1]
        if name=='empty_scope_list':w['h27bd']=lambda *a:seq(())
        if name=='missing_comparator':w['h27bd']=lambda *a:seq(('germ',))
        if name=='duplicate_comparator':w['h27bd']=lambda *a:seq(('germ','other','other'))
        if name=='not_plant':w['h225t']=lambda *a:False
        if name=='empty_feature_scope':w['h27a7']=lambda *a:False
        assert run(d,w)==[True,False],name;cases[name]=False
    for n in ('h27bf','df','dg','h27bg','h27bh','h27bi'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    w=dict(v);w['h27bi']=lambda *a:F(3);assert run(d,w)==[True,True]
    q=''.join('q[t[c[s['+TARGET+']][l[a]['+objects+']]][k zend[]]].' for objects in ('k zgerm[]','k zgerm[] k zcover[]',''))
    d=fixture(('r6jj',),q);v,cs=model(d);assert run(d,v)==[True,True,False,False]
    v['h27bb']=lambda *a:False;assert run(d,v)==[True,False,False,False]
    return dict(cases=cases,native_ryl_ryk_ryj_and_closed_composed_goal=True,ties_allowed=True,
      actor_first_df_adapter_required=True,unknown_rejected=True,goal_not_executed_by_care=True,goal_exact_singleton_and_full_feature_scope=True)

@lru_cache(None)
def growth_checks():
    d=fixture(('r6jm',),'q[k r6jm['+args(GROWTH)+']].');v,cs=model(d);assert run(d,v)==[True,True];cases={}
    for name in ('not_initial_plant','not_plant','empty_features','missing_latent','already_all_manifest','one_final_missing','wrong_transition',
      'wrong_affected','reverse_history','missing_middle_order','same_cover_germ','missing_middle_cover','middle_not_resistant','middle_not_cared',
      'missing_intrinsic_power','power_not_active','no_actual_contribution','other_process_contribution','no_growth_action','reversed_growth_actor'):
        w=dict(v)
        if name=='not_initial_plant':w['h27a2']=lambda *a:False
        if name=='not_plant':w['h225t']=lambda *a:False
        if name=='empty_features':w['h27a7']=lambda *a:False
        if name=='missing_latent':w['h27ba']=lambda *a:a[2]!='cover' and v['h27ba'](*a)
        if name=='already_all_manifest':w['h27bb']=lambda r,o,f,p:v['h27bb'](r,o,f,p) or(o,p)==('germ','start')
        if name=='one_final_missing':w['h27bb']=lambda *a:not (a[2]=='germ' and a[-1]=='end') and v['h27bb'](*a)
        if name=='wrong_transition':w['h27a5']=lambda *a:a==('reference','other','start','end')
        if name=='wrong_affected':w['h27a6']=lambda *a:a==('reference','process','other','start','end')
        if name=='reverse_history':w['h27a4']=lambda *a:v['h27a4'](*a[:-2],a[-1],a[-2])
        if name=='missing_middle_order':w['h27a4']=lambda *a:'middle' not in a[-2:] and v['h27a4'](*a)
        if name=='same_cover_germ':w['zcover']=lambda:'germ'
        if name=='missing_middle_cover':w['h27bc']=lambda *a:a[-1]!='middle' and v['h27bc'](*a)
        if name=='middle_not_resistant':w['h27bu']=lambda *a:a[-2]!='middle' and v['h27bu'](*a)
        if name=='middle_not_cared':w['h27bf']=lambda *a:a[-1]!='middle' and v['h27bf'](*a)
        if name=='missing_intrinsic_power':w['h27ay']=lambda power,body,r:body!='germ' and v['h27ay'](power,body,r)
        if name=='power_not_active':w['hzzb']=lambda *a:False
        if name=='no_actual_contribution':w['h27bj']=lambda *a:False
        if name=='other_process_contribution':w['h27bj']=lambda *a:a==('power','other','germ','start','end')
        if name=='no_growth_action':w['dg']=lambda *a:a!=('process','end') and v['dg'](*a)
        if name=='reversed_growth_actor':w['df']=lambda n,a,p:(n,a,p)==('process','nature','end') or a=='other' and v['df'](n,a,p)
        assert run(d,w)==[True,False],name;cases[name]=False
    # Both features initially latent, but one may already manifest; no rupture required.
    assert v['h27bb']('reference','germ','cover','start') and v['h27bc']('cover','germ','end')
    w=dict(v);hist=('before',*HISTORY,'after')
    w['h27a3']=lambda r,o,s,e,p:(r,o,s,e)==('reference','germ','start','end') and p in hist
    w['h27a4']=lambda r,o,s,e,l,h:(r,o,s,e)==('reference','germ','start','end') and l in hist and h in hist and hist.index(l)<hist.index(h)
    assert run(d,w)==[True,True]
    for n in ('h27a2','h27a3','h27a4','h27a5','h27a6','h27a7','h27ba','h27bb','h27bc','hzzb','h27bj'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=cases,native_whole_growth_nature_resistance_and_care=True,initial_partial_manifest_allowed=True,
      same_cover_still_at_end=True,care_and_resistance_required_at_all_interval_points_only=True,unknown_rejected=True)

@lru_cache(None)
def binding_checks():
    d=fixture(('r6jm',),'q[k r6jm['+args(GROWTH)+']].',('r6jf','r6jg','rw5','r6jh','r6jl','r6jk'),capture=False)
    base,_=model(d);calls=[]
    for n in ('r6jf','r6jg','r6jh','r6jl','h27az','h27ay','hzzb','h27bj','dg'):base[n]=lambda *a:True
    for n in ('h27a3','h27a4','h27a5','h27a6','h27a7','h27ba','h27bb','r6jk','df'):
        def f(*a,n=n):calls.append((n,a));return True
        base[n]=f
    def growth(o,proc,start,end,hist,before,transitions,affected,features,latent,manifest,cover,surrounds,resistant):
        calls.append(('rw5',(o,proc,start,end,cover)))
        hist('other');before('other','after');transitions('other','before','after');affected('other','cover','before','after')
        features('other');latent('other','cover','before');manifest('other','cover','after');resistant('other','after');return True
    base['rw5']=growth
    for changed in (None,*GROWTH):
        c=dict(CONSTANTS);v=dict(base)
        if changed:c[changed]='other';v['z'+changed]=lambda:c[changed]
        calls.clear();assert run(d,v,False)==[True]
        r=c['reference'];scope=(r,c['germ'],c['start'],c['end'])
        assert calls==[('rw5',(c['germ'],c['process'],c['start'],c['end'],c['cover'])),
          ('h27a3',(*scope,'other')),('h27a4',(*scope,'other','after')),('h27a5',(r,'other','before','after')),
          ('h27a6',(r,'other','cover','before','after')),('h27a7',(r,c['germ'],'other')),
          ('h27ba',(r,'other','cover','before')),('h27bb',(r,'other','cover','after')),('r6jk',(r,'other','after')),
          ('df',(c['nature'],c['process'],c['end']))],(changed,calls)
    q='q[t[k r6jn['+args(('reference','nature','germ','cover','start'))+']]['+z('end')+']].q[t[k r6jo['+args(('reference','nature','germ','cover'))+']]['+z('end')+']].'
    d=fixture(('r6jn','r6jo'),q,('r6jm',),capture=False);base,_=model(d);exact=tuple(CONSTANTS[n] for n in GROWTH)
    for slot in (None,*range(7)):
        v=dict(base);target=list(exact)
        if slot is not None:target[slot]='__mismatch__'
        v['r6jm']=lambda *a:a==tuple(target);assert run(d,v)==[slot is None]*2
    return dict(all_seven_growth_slots_and_generic_callbacks_bound=True,actor_first_growth_call=True,both_endpoint_content_wrappers=True,
      boundary='Only call-recording tests replace the named bodies. The preceding whole-depiction test executes native rw5, ry u/s and ry l/k/j.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
    artifacts=[p for row in read(FETCH) for p in (row['artifact'],row['text_artifact'])]
    return dict(status='natural_power_germ_resistance_and_tender_care_depiction_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[716,807],text=u['text'][716:807],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        dict(unit=u['id'],range=[853,871],text=u['text'][853:871],definitions=['r6jm','r6jn','r6jo'],status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,lexical_sources=read(FETCH),
      lexical_observations=['Naturは物体の内的構成に基づく変化力、及びそれらを一つと見た全体を含み、独立した存在として描く用法を区別している。今回その読みを採用する。',
        'Keimは植物の初期の始まりと比喩的な最初の始まりを区別する。植物側と二性向側を分ける根拠とするが、原文の特定の植物種や発芽経路は追加しない。'],
      legacy_adapter_issue=dict(generic='ryj performs(act,actor,point)',current='df(actor,act,point)',
        preserved_candidates=['scripts/compose_tender_care.py: iawcare performs=p df','scripts/compose_covered_unfolding.py: iagdepiction df(process,qb,anchor)'],
        replacement='r6jl passes lambda(act,actor,context):df(actor,act,context); r6jm calls df(nature,process,end).'),
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      unresolved=['同じ低い制度・二性向と描写側の覆い・芽の対応','全体の条件と人口・時間への量化','反作用・行為能力・政府・尊厳・著者注参照'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,FETCH,*artifacts,*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for old in (parent(),main_catalog()):
        for n,e in old.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    ds,ms,_=legacy()
    for d in ds:assert c.entries[d['name']]['declaration']==d
    for n,(m,p) in ms.items():assert c.entries[n]['meaning_ja']==m
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    for row in read(FETCH):
        assert digest((ROOT/row['artifact']).read_bytes())==row['sha256']
        assert digest((ROOT/row['text_artifact']).read_bytes())==row['text_sha256']
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:1 if n in ('r6jl','r6jm','r6jn','r6jo') else 0 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,
      inherited_bodies_and_meanings_unchanged=True,roundtrips=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('nature',nature_checks),('resistance',resistance_checks),('care',care_checks),('growth',growth_checks),('bindings',binding_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,FETCH,INDEX,*PRIORS,
      'scripts/compose_nurtured_germ.py','scripts/check_nurtured_germ.py','tests/test_nurtured_germ.py',
      'scripts/compose_covered_unfolding.py','scripts/compose_dispositional_resistance.py','scripts/compose_tender_care.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py'}
    paths.update(p for row in read(FETCH) for p in (row['artifact'],row['text_artifact']))
    return dict(status='nurtured_germ_depiction_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
