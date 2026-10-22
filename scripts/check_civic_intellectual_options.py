"""Check fixed civic targets, reasoned task goals and assessed opportunity gains."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_intellectual_options import ROOT,LIBRARY,BASIS,OLD,OLD_BASIS,ACTION,MEANINGS,PRIMITIVES,LIMITS,parent,legacy,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/civic-intellectual-options-v1.md';READING='data/civic-intellectual-options-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v205.json'
PRIORS=('reports/whole-view-sentence-v1.json','reports/republic-polity-v1.json','reports/apparent-liberty-v1.json')
DOMAIN=tuple('abcd');SCENES=('reference','lower','higher','outlow','outhigh','other')
CONSTANTS=dict(community='c',lowerorder='c',higherorder='d',person='a',task='c',reference='reference',point='lower',lower='lower',higher='higher')
TARGET='r[i[actor a activity a][b point[w[k dg[v activity v point]][k df[v activity v actor v point]]]]]'
OTHER='r[i[actor a activity a][b point[k dg[v activity v point]]]]'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def z(n):return 'k z'+n+'[]'
def args(*ns):return ' '.join(z(n) for n in ns)
def norm(xs):return tuple((v.rank,json.dumps(json.loads(v.syntax),sort_keys=True)) if hasattr(v,'syntax') else v for v in xs)
def content(f):return Content(SCENES,tuple(f(t) for t in SCENES))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),capture=False):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    # Closed action quotations are issued by the same evaluation as the queries.
    extra='r dg[a d] c.r df[a a d] c.'+''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    extra+='r zcapture['+ACTION+' '+ACTION+'] c.'
    prefix=parse('p:'+extra)['declarations'];ns={r['name'] for r in prefix}
    d['declarations']=prefix+[r for r in d['declarations'] if r['name'] not in ns];d['declarations']=closure(d,(*roots,*ns))
    if capture:query='q[k zcapture['+TARGET+' '+OTHER+']].'+query
    return parse(format_graph(d,'compact')+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};codes=[]
    def capture(*xs):codes[:]=xs;return True
    v.update({'z'+n:lambda v=v:v for n,v in CONSTANTS.items()})
    v.update(zcapture=capture,aa=lambda p:p in 'ab',h237c=lambda p,c,r:p in 'ab' and(c,r)==('c','reference'),
      h26yo=lambda c,p,a,r:(c,r)==('c','reference') and p in 'ab' and a in 'cd',
      h26yp=lambda o,c,r,t:o,h26yq=lambda c,p,r:'b' if p=='a' else 'a',h26yr=lambda a,r:codes[0],
      h26ys=lambda c,p,a,r:(c,p,r)==('c','a','reference') and a in 'cd',
      h26yt=lambda task,m,r:task in 'cd' and m in 'cd' and r=='reference')
    return v,codes
def rule_row(code,source,person,activity,point,polarity=True):return (source,person,'b' if person=='a' else 'a',activity,norm((code,))[0],polarity,point)

@lru_cache(None)
def civic_norm_checks():
    q='q[k r6hf['+args('community','lowerorder','person','task','reference','point')+']].'
    d=fixture(('r6hf',),q,capture=True);rows=[]
    for allowed,forbidden in product((False,True),repeat=2):
        v,cs=model(d)
        v['h7b']=lambda *a:allowed and norm(a)==rule_row(cs[0],'c','a','c','lower')
        v['h7a']=lambda *a:forbidden and norm(a)==rule_row(cs[0],'c','a','c','lower',False)
        want=allowed and not forbidden;assert run(d,v)==[True,want];rows.append(dict(allowed=allowed,forbidden=forbidden,value=want))
    def setup():
        w,cs=model(d);w['h7b']=lambda *a:norm(a)==rule_row(cs[0],'c','a','c','lower');w['h7a']=lambda *a:False;return w,cs
    for slot in range(7):
        w,cs=setup()
        def mismatch(*a):
            expected=list(rule_row(cs[0],'c','a','c','lower'));expected[slot]='__mismatch__';return norm(a)==tuple(expected)
        w['h7b']=mismatch;assert run(d,w)==[True,False],slot
    for n in ('h26yo','aa','h237c'):
        w,_=setup();w[n]=lambda *a:False;assert run(d,w)==[True,False],n
    w,cs=setup();w['h26yr']=lambda *a:cs[1];assert run(d,w)==[True,False]
    for n in ('h26yp','h26yq','h26yr','h7a','h7b'):
        w,_=setup();w[n]=unknown;rejects(d,w)
    w,_=setup();assert w['dg'] is unknown and w['df'] is unknown and run(d,w)==[True,True]
    return dict(permission_matrix=rows,normative_argument_mutations=7,same_person_activity_role_source_description_and_point=True,
      merely_no_prohibition_insufficient=True,opposed_requirement_cancels_permission=True,quoted_action_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def civic_comparison_checks():
    q='q[k r6hg['+args('community','lowerorder','higherorder','reference','lower','higher')+']].'
    d=fixture(('r6hg',),q,('r6fr',),capture=True);pairs=tuple(product('ab','cd'));count=0;strict=0
    def setup(low,high):
        v,cs=model(d);v['h7a']=lambda *a:False
        def allowed(source,p,role,a,description,sign,point):
            valid=norm((source,p,role,a,description,sign,point))==rule_row(cs[0],source,p,a,point)
            return valid and ((source,point)==('c','lower') and(p,a) in low or (source,point)==('d','higher') and(p,a) in high)
        v['h7b']=allowed
        v['r6fr']=lambda c,o,r,t:(c,r)==('c','reference') and(o,t) in (('c','lower'),('d','higher'))
        return v,cs
    for first in product((False,True),repeat=4):
        low={p for p,b in zip(pairs,first) if b}
        for second in product((False,True),repeat=4):
            high={p for p,b in zip(pairs,second) if b};v,_=setup(low,high);want=low<high
            assert run(d,v)==[True,want],(low,high);count+=1;strict+=want
    low={('a','c')};high={('a','c'),('b','d')}
    for name in ('empty_population','empty_scope','wrong_lower_order','wrong_higher_order','swapped_points','one_order_not_operating','gain_outside_scope','gain_other_person'):
        v,_=setup(low,high)
        if name=='empty_population':v['h237c']=lambda *a:False
        if name=='empty_scope':v['h26yo']=lambda *a:False
        if name=='wrong_lower_order':v['zlowerorder']=lambda:'a'
        if name=='wrong_higher_order':v['zhigherorder']=lambda:'a'
        if name=='swapped_points':v.update(zlower=lambda:'higher',zhigher=lambda:'lower')
        if name=='one_order_not_operating':v['r6fr']=lambda c,o,r,t:t=='lower'
        if name=='gain_outside_scope':v['h26yo']=lambda c,p,a,r:a=='c'
        if name=='gain_other_person':v,_=setup(low,{('b','c'),('b','d')})
        assert run(d,v)==[True,False],name
    v,_=setup(low,high);v['r6fr']=unknown;rejects(d,v)
    return dict(two_people_two_activities_assignments=count,strict_inclusions=strict,same_population_and_activities=True,
      both_operating_public_orders_bound=True,swapping_or_losing_options_not_growth=True,boundary='Only r6fr for paired public-order wiring; its unchanged body and civic meanings are pinned by republic-polity-v1.')

def judgment_model(d):
    v,cs=model(d)
    active=lambda t:t in ('outlow','outhigh')
    v.update(ab=lambda f,p,t:(f,p)==('b','a') and active(t),ac=lambda p,f,j,t:(p,f)==('a','b') and j in 'cd' and active(t),
      fa=lambda p,j,t:p=='a' and j in 'cd' and active(t),fb=lambda j,m,t:j==m and j in 'cd' and active(t),
      fc=lambda j,r,t:j in 'cd' and r=='b' and active(t),fd=lambda r,j,t:r=='b' and j in 'cd' and active(t),ad=lambda *a:False,
      h26yu=lambda p,task,j,r,t:(p,r)==('a','reference') and task in 'cd' and j in 'cd' and active(t))
    return v,cs
@lru_cache(None)
def task_goal_checks():
    q='q[t[k r6hh['+args('person','task','reference')+']][k zpoint[]]].';d=fixture(('r6hh',),q);v,_=judgment_model(d);v['zpoint']=lambda:'outlow';assert run(d,v)==[True];cases={}
    for name in ('no_matters','one_missing_judgment','one_unsupported_judgment','other_person_faculty','other_task','other_matter','one_guided_judgment','nonhuman','wrong_reference','not_actual'):
        w=dict(v)
        if name=='no_matters':w['h26yt']=lambda *a:False
        if name=='one_missing_judgment':w['h26yu']=lambda p,task,j,r,t:j=='c'
        if name=='one_unsupported_judgment':w['fd']=lambda r,j,t:j=='c'
        if name=='other_person_faculty':w['ab']=lambda f,p,t:p=='b'
        if name=='other_task':w['h26yu']=lambda p,task,j,r,t:task=='d'
        if name=='other_matter':w['fb']=lambda j,m,t:m=='b'
        if name=='one_guided_judgment':w['ad']=lambda leader,p,j,t:(leader,p,j)==('b','a','d')
        if name=='nonhuman':w['aa']=lambda *a:False
        if name=='wrong_reference':w['zreference']=lambda:'other'
        if name=='not_actual':w['fa']=lambda *a:False
        assert run(d,w)==[False],name;cases[name]=False
    w=dict(v);w['ad']=lambda leader,p,j,t:leader==p;assert run(d,w)==[True]
    for n in ('ab','ac','fa','fb','fc','fd','ad','h26yt','h26yu'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=cases,native_rcr_and_all_task_matters=True,different_judgments_can_cover_different_matters=True,
      self_guidance_not_other_guidance=True,unknown_rejected=True)

def opportunity_model(d):
    v,cs=judgment_model(d)
    v['fa']=lambda p,j,t:p=='a' and j in 'cd' and t=='outlow'
    v['h26yv']=lambda c,task,r,p,m,t:(c,r,p,m)==('c','reference','a','b') and task in 'cd' and t in ('lower','higher')
    v['h26yw']=lambda c,task,r,p,m,t,o:(c,r,p,m)==('c','reference','a','b') and task in 'cd' and(t,o) in (('lower','outlow'),('higher','outhigh'))
    v['h26yx']=v['h26yw'];return v,cs
@lru_cache(None)
def opportunity_checks():
    q=''.join('q[k '+n+'['+args('community','person','task','reference',side)+']].' for side in ('lower','higher') for n in ('r6hi','r6hj','r6hk'))
    d=fixture(('r6hi','r6hj','r6hk'),q);v,_=opportunity_model(d);assert run(d,v)==[True,True,False,False,True,True];cases={}
    for name in ('unassessed_method','selected_outside_candidates','no_available_method','empty_task','wrong_community','wrong_person','outside_scope'):
        w=dict(v)
        if name=='unassessed_method':w['h26yx']=lambda *a:False;want=[False]*6
        if name=='selected_outside_candidates':w['h26yw']=lambda *a:False;want=[False]*6
        if name=='no_available_method':w['h26yv']=lambda *a:False;want=[False,True,True]*2
        if name=='empty_task':w['h26yt']=lambda *a:False;want=[False]*6
        if name=='wrong_community':w['zcommunity']=lambda:'d';want=[False]*6
        if name=='wrong_person':w['zperson']=lambda:'b';want=[False,True,True]*2
        if name=='outside_scope':w['h26ys']=lambda *a:False;want=[False]*6
        # A person outside the selected mental scope is not an evaluated incapacity.
        if name=='wrong_person':want=[False]*6
        assert run(d,w)==want,(name,run(d,w));cases[name]=want
    for n in ('h26yv','h26yw','h26yx'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=cases,native_goals_xd_xf_xg=True,current_execution_not_required_for_opportunity=True,
      unassessed_not_counted_as_incapacity=True,empty_task_not_vacuously_classified=True,unknown_rejected=True)

@lru_cache(None)
def mental_comparison_checks():
    q='q[k r6hl['+args('community','reference','lower','higher')+']].q[k r6hm['+args('community','reference','lower','higher')+']].'
    d=fixture(('r6hl','r6hm'),q,('r6hh',));rows=[]
    for bits in product((False,True),repeat=4):
        v,_=opportunity_model(d)
        v['r6hh']=lambda p,task,r:content(lambda t:(p,r)==('a','reference') and task in 'cd' and t in ('outlow','outhigh') and bits[('cd'.index(task)*2)+('outlow','outhigh').index(t)])
        low={a for a in 'cd' if bits['cd'.index(a)*2]};high={a for a in 'cd' if bits['cd'.index(a)*2+1]}
        assert run(d,v)==[True,low<high],bits;rows.append(dict(bits=bits,gain=low<high))
    v,_=opportunity_model(d);v['r6hh']=lambda p,task,r:content(lambda t:t=='outhigh')
    assert run(d,v)==[True,True]
    for name in ('unassessed_low_task','empty_scope','empty_matters','gain_from_other_person'):
        w=dict(v)
        if name=='unassessed_low_task':w['h26yx']=lambda c,task,r,p,m,t,o:task!='d' or t!='lower'
        if name=='empty_scope':w['h26ys']=lambda *a:False
        if name=='empty_matters':w['h26yt']=lambda *a:False
        if name=='gain_from_other_person':w['r6hh']=lambda p,task,r:content(lambda t:p=='b' and t=='outhigh')
        assert run(d,w)==([True,False] if name=='gain_from_other_person' else [False,False]),name
    return dict(assignments=rows,native_opportunity_and_assessment_comparison=True,
      one_unassessed_pair_rejects_comparison=True,empty_scope_and_content_rejected=True,
      boundary='r6hh only to distinguish task/outcome truth tables; its native full reasoned-judgment body executes in task_goal and opportunity checks.')

@lru_cache(None)
def adapter_checks():
    q=''.join('q[k '+n+'['+args('community','person','task','reference','point')+']].' for n in ('r6hi','r6hj','r6hk'))
    d=fixture(('r6hi','r6hj','r6hk'),q,('xd','xf','xg','r6hh'));v,_=model(d);calls=[]
    v['r6hh']=lambda p,task,r:content(lambda t:(p,task,r,t)==('a','c','reference','outlow'))
    def primitive(name):
        def rec(*a):calls.append((name,a));return True
        return rec
    for n in ('h26yv','h26yw','h26yx'):v[n]=primitive(n)
    def ability(person,goal,point,available,possible,selected):
        assert (person,point)==('a','lower')
        assert goal==content(lambda t:t=='outlow')
        available('b','d','higher');possible('b','d','higher','other');selected('b','d','higher','other');return True
    for n in ('xd','xf','xg'):v[n]=ability
    assert evaluate(d,v,DOMAIN,SCENES,False)==[True]*3
    assert calls==[(n,('c','c','reference','b','d','higher',*tail)) for _ in range(3) for n,tail in (('h26yv',()),('h26yw',('other',)),('h26yx',('other',)))],calls
    q='q[k r6hn['+args('community','lowerorder','higherorder','reference','lower','higher')+']].'
    d=fixture(('r6hn',),q,('r6hg','r6hm'));base,_=model(d)
    for civil,mental in product((False,True),repeat=2):
        v=dict(base);v['r6hg']=lambda *a:civil and a==('c','c','d','reference','lower','higher');v['r6hm']=lambda *a:mental and a==('c','reference','lower','higher')
        assert run(d,v)==[civil and mental]
    for n in CONSTANTS:
        if n not in ('community','lowerorder','higherorder','reference','lower','higher'):continue
        w=dict(v);w['z'+n]=lambda n=n:'other' if n in ('reference','lower','higher') else 'b';assert run(d,w)==[False],n
    return dict(all_three_ability_adapters_forward_alternative_actor_method_point_and_outcome=True,
      task_community_and_reference_remain_fixed=True,paired_comparison_requires_both=True,all_six_pair_arguments_bound=True,
      boundaries='xd/xf/xg/r6hh only for provider recording; r6hg/r6hm only for conjunction wiring. Native bodies are checked in separate groups.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');segments=[]
    for phrase,ns in (('Ein größerer Grad bürgerlicher Freiheit',['r6hd','r6he','r6hf','r6hg']),('der Freiheit des Geistes des Volks',['r6hh','r6hi','r6hj','r6hm'])):
        a=u['text'].index(phrase,467);segments.append(dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=ns,status='explicit_interpretive_annotation'))
    return dict(status='fixed_civic_and_intellectual_options_dependency',source_unit=u['id'],unit_sha256=u['text_sha256'],alignment=dict(segments=segments),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for n,e in parent().entries.items():
        if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    ds,means=legacy()
    for row in ds:assert c.entries[row['name']]['declaration']==row and c.entries[row['name']]['meaning_ja']==means[row['name']]
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact')
    for n in MEANINGS:parse(t+'q[e[r[p '+n+']][r[p '+n+']]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_bodies_and_meanings_unchanged=True,
      legacy_strict_inclusion_unchanged=True,minimum_quote_ranks={n:0 for n in MEANINGS},roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('civic_norm',civic_norm_checks),('civic_comparison',civic_comparison_checks),('task_goal',task_goal_checks),('opportunity',opportunity_checks),('mental_comparison',mental_comparison_checks),('adapters',adapter_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,OLD,OLD_BASIS,*PRIORS,
      'scripts/compose_civic_intellectual_options.py','scripts/check_civic_intellectual_options.py','tests/test_civic_intellectual_options.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='civic_permissions_and_assessed_intellectual_options_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
