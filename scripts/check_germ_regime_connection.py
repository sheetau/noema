"""Check fixed regime throughout growth, and nonfactive same-property apposition."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_germ_regime_connection import ROOT,LIBRARY,BASIS,OLD,OLD_BASIS,HIGH,MEANINGS,PRIMITIVES,LIMITS,parent,main_catalog,legacy,build,closure
from scripts.check_thinking_impulse_development import model as thinking_model,norm,CODE,TARGET,ALTERNATIVE,PREFIX
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/germ-regime-connection-v1.md';READING='data/germ-regime-connection-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v206.json'
PRIORS=('reports/thinking-impulse-development-v1.json','reports/civic-spirit-sentence-v1.json','reports/civic-intellectual-options-v1.json')
DOMAIN=('a','b');SCENES=('reference','other','lower','higher','before','start','middle','end','after','oldnormal','normal','peer','exception')
CONSTANTS=dict(community='b',person='a',reference='reference',view='reference',lowerorder='a',higherorder='b',
  baseline='lower',point='end',process='b',start='start',end='end')
SCOPE=('community','lowerorder','higherorder','person','reference','view');GROWTH=(*SCOPE,'process','start','end')
BUNDLE='k r6jb[r[k zb[]] r[k zref[]]]'
OTHER_BUNDLE='r b[i[person a][k r6iw[k zb[] v person k zref[]]]]'
ACTION='r[i[actor a activity a][b point[w[k dg[v activity v point]][k df[v activity v actor v point]]]]]'
ACTION_TYPE='i[h[a a] e]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),capture=True):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=PREFIX+'r dg[a d] c.r df[a a d] c.'+''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    extra+='r zcapture[i[a] i[a] i[d] i[d] '+CODE+' '+CODE+' '+HIGH+' '+ACTION_TYPE+' '+HIGH+'] c.'
    prefix=parse('p:'+extra)['declarations'];ns={r['name'] for r in prefix}
    d['declarations']=prefix+[r for r in d['declarations'] if r['name'] not in ns]
    d['declarations']=closure(d,(*roots,*ns,*(('r6is','r6jb') if capture else ())))
    if capture:query='q[k zcapture[r[k za[]] r[k zb[]] r[k zref[]] r[k zother[]] '+TARGET+' '+ALTERNATIVE+' '+BUNDLE+' '+ACTION+' '+OTHER_BUNDLE+']].'+query
    return parse(format_graph(d,'compact')+query)

def model(d):
    v,cs=thinking_model(d);v.update({'z'+n:lambda v=v:v for n,v in CONSTANTS.items()})
    v.update(aa=lambda p:p in DOMAIN,h237c=lambda p,c,r:p in DOMAIN and(c,r)==('b','reference'),
      h26yo=lambda c,p,a,r:(c,r)==('b','reference') and p in DOMAIN and a in DOMAIN,
      h26yp=lambda o,c,r,t:o,h26yq=lambda c,p,r:p,h26yr=lambda a,r:cs[7],h7a=lambda *a:False,
      h26zi=lambda *a:a==('b','a','b','reference'),
      h26yy=lambda *a:'lower' if a==('b','reference','reference') else 'other',
      h26yz=lambda *a:'higher' if a==('b','reference','reference') else 'other',
      r6fr=lambda c,o,r,t:(c,r)==('b','reference') and ((o=='a' and t in ('lower','start','middle','end')) or(o,t)==('b','higher')),
      h26zj=lambda:'reference',h26km=lambda:'other',h26kn=lambda case:'reference' if case=='other' else 'end',
      h27at=lambda:'a',h27au=lambda:'b',wa=lambda:'a',h27av=lambda:'b',h27aw=lambda:'other',
      ue=lambda *a:a==('a','b','other'),h27as=lambda *a:a==('a','b','a','b','other'))
    def allowed(o,p,role,a,code,sign,t):
        valid=p in DOMAIN and a in DOMAIN and role==p and norm(code)==norm(cs[7]) and sign
        return valid and ((o=='a' and t in ('lower','start','middle','end') and a=='a') or(o,t)==('b','higher') and(a=='a' or p=='a'))
    v['h7b']=allowed
    v['h27ar']=lambda node,author,code,scope,ctx:node in DOMAIN and(author,scope,ctx)==('a','b','other') and norm(code)==norm(cs[6])
    return v,cs
def run(d,v,memo=True):return evaluate(d,v,DOMAIN,SCENES,memo)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def regime_checks():
    q='q[k r6i5['+args(GROWTH)+']].';d=fixture(('r6i5',),q,('r6fr',));v,cs=model(d)
    assert run(d,v)==[True,True];cases={}
    for name in ('unselected_comparison','equal_civic_freedom','swapped_baselines','wrong_lower_order','wrong_reference','other_developing_person',
      'wrong_process','missing_psychological_growth','missing_initial_latent','lost_middle_permission','gained_middle_permission',
      'opposed_middle_requirement','nonoperating_start','nonoperating_middle','nonoperating_end'):
        w=dict(v)
        if name=='unselected_comparison':w['h26zi']=lambda *a:False
        if name=='equal_civic_freedom':w['h7b']=lambda *a:v['h7b'](*a) and a[3]=='a'
        if name=='swapped_baselines':w.update(h26yy=v['h26yz'],h26yz=v['h26yy'])
        if name=='wrong_lower_order':w['zlowerorder']=lambda:'b'
        if name=='wrong_reference':w['zreference']=lambda:'other'
        if name=='other_developing_person':w['zperson']=lambda:'b'
        if name=='wrong_process':w['zprocess']=lambda:'a'
        if name=='missing_psychological_growth':w['h27ah']=lambda *a:False
        if name=='missing_initial_latent':w['h27aq']=lambda *a:False
        if name=='lost_middle_permission':w['h7b']=lambda *a:v['h7b'](*a) and not (a[1]=='b' and a[-1]=='middle')
        if name=='gained_middle_permission':w['h7b']=lambda *a:v['h7b'](*a) or(a[0],a[1],a[2],a[3],a[-1])==('a','b','b','b','middle')
        if name=='opposed_middle_requirement':w['h7a']=lambda *a:(a[0],a[1],a[2],a[3],a[-2],a[-1])==('a','b','b','a',False,'middle')
        if name.startswith('nonoperating_'):w['r6fr']=lambda *a,point=name.removeprefix('nonoperating_'):a[-1]!=point and v['r6fr'](*a)
        assert run(d,w)==[True,False],name;cases[name]=False
    # The same full history can include points before/after the actual growth interval.
    history=('before','start','middle','end','after');w=dict(v)
    w['h27am']=lambda *a:a[:-1]==('b','a','reference','start','end') and a[-1] in history
    w['h27an']=lambda *a:a[:-2]==('b','a','reference','start','end') and a[-2] in history and a[-1] in history and history.index(a[-2])<history.index(a[-1])
    assert run(d,w)==[True,True]
    for n in ('h26zi','h26yy','h26yz','h7a','h7b','h27am','h27an','h27ah','h27aq'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=cases,native_two_dispositions_growth_r6iy_and_norms_r6hf_rdm=True,
      all_citizens_and_both_permission_directions_checked=True,actual_lower_baseline_distinct_from_growth_start=True,
      interval_endpoints_included_and_external_history_excluded=True,unknown_rejected=True,
      boundary='Only r6fr is replaced by a public-order relation; its unchanged definition and previous validation are pinned.')

@lru_cache(None)
def interval_checks():
    ns=('community','person','reference','start','end','point')
    d=fixture(('r6i4',),'q[k r6i4['+args(ns)+']].',capture=False);v,_=model(d)
    history=('before','start','middle','end','after')
    v['h27am']=lambda *a:a[:-1]==('b','a','reference','start','end') and a[-1] in history
    v['h27an']=lambda *a:a[:-2]==('b','a','reference','start','end') and a[-2] in history and a[-1] in history and history.index(a[-2])<history.index(a[-1])
    rows=[]
    for point in SCENES:
        w=dict(v);w['zpoint']=lambda:point;want=point in ('start','middle','end');assert run(d,w)==[want]
        rows.append(dict(point=point,in_interval=want))
    for name in ('community','person','reference','start','end'):
        w=dict(v);w['z'+name]=lambda:'b' if name=='person' else 'a' if name=='community' else 'other'
        assert run(d,w)==[False],name
    return dict(interval_rows=rows,history_context_and_both_endpoints_bound=True)

@lru_cache(None)
def endpoint_checks():
    q='q[t[k r6i6['+args(SCOPE)+' '+z('start')+']]['+z('end')+']].q[t[k r6i7['+args(SCOPE)+']]['+z('end')+']].'
    d=fixture(('r6i6','r6i7'),q,('r6i5',),capture=False);base,_=model(d);cases=[]
    exact=tuple(CONSTANTS[n] for n in GROWTH)
    for slot in (None,*range(len(GROWTH))):
        v=dict(base);wanted=list(exact)
        # Every free argument must bind; existential process/start may select any real candidate.
        if slot is not None:wanted[slot]='__mismatch__'
        v['r6i5']=lambda *a:a==tuple(wanted)
        want=slot is None;assert run(d,v)==[want,want],slot;cases.append(slot)
    # Exact fixed source baseline and comparison view, under r6jd, are separately observed.
    q='q[t[k r6jd['+args(SCOPE[:4])+']]['+z('end')+']].';d=fixture(('r6jd',),q,('r6i7',),capture=False)
    from noema.constructed_semantics import Content
    v,_=model(d);calls=[]
    def result(*a):calls.append(a);return Content(SCENES,tuple(t=='end' for t in SCENES))
    v['r6i7']=result;assert run(d,v,False)==[True];assert calls==[('b','a','b','a','reference','reference')]
    return dict(all_nine_growth_slots_checked=cases,fixed_third_sentence_reference_and_view=True,
      boundary='r6i5/r6i7 are call boundaries for existential and source-constant wiring. Native r6i5 is checked in regime_checks.')

@lru_cache(None)
def apposition_checks():
    q='q[k r6jc['+args(('community','reference'))+']].q[k r6je['+z('community')+']].'
    d=fixture(('r6jc','r6je'),q);v,cs=model(d);assert run(d,v)==[True,True,True]
    # No attitude or thinking predicate is evaluated while pointing to the property.
    for n in ('h27ad','h27ae','h27af','h27ag','h27ah','h27ai','h27aj','aa','h237c','h26ys','h26yt','ab','ac','fa','fb','fc','fd','ad'):
        v[n]=unknown
    assert run(d,v)==[True,True,True];cases={}
    for name in ('same_mentions','first_not_denoting','second_not_denoting','reverse_order','no_order','no_explanation',
      'wrong_property','bad_community_name','bad_reference_name','wrong_author','wrong_scope','wrong_presentation'):
        w=dict(v)
        if name=='same_mentions':w['h27au']=lambda:'a'
        if name=='first_not_denoting':w['h27ar']=lambda *a:a[0]!='a' and v['h27ar'](*a)
        if name=='second_not_denoting':w['h27ar']=lambda *a:a[0]!='b' and v['h27ar'](*a)
        if name=='reverse_order':w['ue']=lambda *a:a in (('a','b','other'),('b','a','other'))
        if name=='no_order':w['ue']=lambda *a:False
        if name=='no_explanation':w['h27as']=lambda *a:False
        if name=='wrong_property':w['h27ar']=lambda n,a,c,s,t:norm(c)==norm(cs[8])
        if name=='bad_community_name':w['h223g']=lambda *a:cs[0]
        if name=='bad_reference_name':w['h223h']=lambda *a:cs[3]
        if name=='wrong_author':w['wa']=lambda:'b'
        if name=='wrong_scope':w['h27av']=lambda:'a'
        if name=='wrong_presentation':w['h27aw']=lambda:'reference'
        assert run(d,w)==[True,False,False],name;cases[name]=False
    for n in ('h27ar','h27as','ue','h223g','h223h'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Decode the same quotation only here, and compare to the native two dispositions.
    q='q[t[c[s['+BUNDLE+']]['+z('person')+']]['+z('point')+']].q[t[k r6iw['+args(('community','person','reference'))+']]['+z('point')+']].'
    d=fixture(('r6jb','r6iw'),q);base,cs=model(d);rows=[]
    for favorable,impulse in product((False,True),repeat=2):
        w=dict(base);w['h27ah']=lambda *a:favorable and a[-1] in ('normal','peer');w['h27ai']=lambda *a:impulse and a[-1] in ('normal','peer')
        want=favorable and impulse;assert run(d,w)==[True,want,want]
        rows.append(dict(favorable=favorable,impulse=impulse,value=want))
    return dict(cases=cases,property_rows=rows,native_ryt_and_exact_rank_one_composed_property=True,
      same_community_reference_and_third_sentence_fixed_adapter=True,no_referent_execution_during_apposition=True,unknown_rejected=True)

@lru_cache(None)
def binding_checks():
    q='q[k r6i5['+args(GROWTH)+']].'
    d=fixture(('r6i5',),q,('r6hg','r6iy','r6i4','r6i3'),capture=False);base,_=model(d);calls=[]
    for name in ('h26zi','r6hg','r6iy','r6i4','r6i3'):
        def f(*a,name=name):calls.append((name,a));return True
        base[name]=f
    base.update(h26yy=lambda *a:'lower',h26yz=lambda *a:'higher')
    for changed in (None,*GROWTH):
        c=dict(CONSTANTS);v=dict(base)
        if changed:c[changed]='other' if c[changed] not in DOMAIN else ('b' if c[changed]=='a' else 'a');v['z'+changed]=lambda:c[changed]
        calls.clear();assert run(d,v,False)==[True]
        expected=[('h26zi',tuple(c[n] for n in ('community','lowerorder','higherorder','reference'))),
          ('r6hg',tuple(c[n] for n in ('community','lowerorder','higherorder','reference'))+('lower','higher')),
          ('r6iy',tuple(c[n] for n in ('community','person','reference','process','start','end')))]
        for point in SCENES:expected.extend([
          ('r6i4',tuple(c[n] for n in ('community','person','reference','start','end'))+(point,)),
          ('r6i3',tuple(c[n] for n in ('community','lowerorder','reference'))+('lower',point))])
        assert calls==expected,(changed,calls)
    return dict(all_nine_scalar_arguments_and_every_history_point_bound=True,
      boundary='r6hg/r6iy/r6i4/r6i3 replaced only to observe exact call arguments; native bodies except r6fr are exercised above.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
    return dict(status='same_lower_regime_and_namely_property_connection_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[a,b],text=u['text'][a:b],definitions=roots,status='explicit_interpretive_annotation')
        for a,b,roots in ((736,772,['r6i3','r6i4','r6i5']),(807,871,['r6i6','r6i7','r6ja','r6jb','r6jc','r6jd','r6je']))]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      prior_readings=['data/cover-reference-reading-v1.json','data/property-apposition-reading-v1.json','data/thinking-impulse-development-reading-v1.json'],
      evidence_note='保存済み原刊照合と先行読解を使用。今回新たな辞書取得又は原刊再照合は行わない。',
      unresolved=['自然と擬人化、描写側の植物・覆い・世話','Wenn/so全体と人口・時点への量化','反作用・行為能力・政府・尊厳・著者注参照'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS,
        'data/cover-reference-reading-v1.json','data/property-apposition-reading-v1.json','data/thinking-impulse-development-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for old in (parent(),main_catalog()):
        for n,e in old.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    ds,m=legacy();assert c.entries['ryt']['declaration']==ds[0] and c.entries['ryt']['meaning_ja']==m
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
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
    assert ranks=={n:0 if n in ('r6i3','r6i4') else 1 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,
      imported_bodies_and_meanings_unchanged=True,roundtrips=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('regime',regime_checks),('interval',interval_checks),('endpoints',endpoint_checks),('apposition',apposition_checks),('bindings',binding_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,OLD,OLD_BASIS,*PRIORS,
      'scripts/compose_germ_regime_connection.py','scripts/check_germ_regime_connection.py','tests/test_germ_regime_connection.py',
      'scripts/check_thinking_impulse_development.py','scripts/compose_civic_spirit_sentence.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='same_lower_regime_development_and_property_apposition_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
