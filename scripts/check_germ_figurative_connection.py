"""Check nonfactive figurative presentation and fixed cover/person/property bindings."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_germ_figurative_connection import ROOT,LIBRARY,BASIS,OLD,OLD_BASIS,HIGH,MEANINGS,PRIMITIVES,LIMITS,parent,main_catalog,legacy,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/germ-figurative-connection-v1.md';READING='data/germ-figurative-connection-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v206.json'
PRIORS=('reports/nurtured-germ-v1.json','reports/germ-regime-connection-v1.json','reports/civic-spirit-sentence-v1.json')
DOMAIN=('a','b');SCENES=('reference','other','prior','presentation','physical','start','end')
CONSTANTS=dict(community='b',lowerorder='a',higherorder='b',person='a',point='end')
SCOPE=('community','lowerorder','higherorder')
NAMES='r[k zb[]] r[k za[]] r[k zb[]]'
TARGET='k r6jr['+NAMES+']';DEPICTION='k r6js['+NAMES+']'
BUNDLE='k r6jb[r[k zb[]] r[k zref[]]]';PREVIOUS='r f[k r6ik[]]'
ALIAS='r b[i[person a][k r6jd[k zb[] k za[] k zb[] v person]]]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def norm(x):return (x.rank,json.dumps(json.loads(x.syntax),sort_keys=True)) if hasattr(x,'syntax') else x
def content(f):return Content(SCENES,tuple(f(p) for p in SCENES))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),capture=True):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra='r za[] a.r zb[] a.r zref[] d.r zother[] d.'
    extra+=''.join('r z'+n+'[] '+('d' if n=='point' else 'a')+'.' for n in CONSTANTS)
    extra+='r zcapture[i[a] i[a] i[d] i[d] '+HIGH+' '+HIGH+' '+HIGH+' i f[e] '+HIGH+'] c.'
    prefix=parse('p:'+extra)['declarations'];ns={r['name'] for r in prefix}
    d['declarations']=prefix+d['declarations']
    d['declarations']=closure(d,(*roots,*ns,*(('r6jr','r6js','r6jb','r6ik') if capture else ())))
    if capture:query='q[k zcapture[r[k za[]] r[k zb[]] r[k zref[]] r[k zother[]] '+TARGET+' '+DEPICTION+' '+BUNDLE+' '+PREVIOUS+' '+ALIAS+']].'+query
    return parse(format_graph(d,'compact')+query)

def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};codes=[]
    def capture(*a):codes[:]=a;return True
    v.update({'z'+n:lambda value=value:value for n,value in CONSTANTS.items()})
    v.update(za=lambda:'a',zb=lambda:'b',zref=lambda:'reference',zother=lambda:'other',zcapture=capture,
      h223g=lambda a:codes[DOMAIN.index(a)],h223h=lambda p:codes[2 if p=='reference' else 3],
      h26zj=lambda:'reference',h26zk=lambda:'prior',h27aw=lambda:'presentation',wa=lambda:'a',h27av=lambda:'b',
      h26zs=lambda:'a',h27b3=lambda:'b',h27at=lambda:'a',h27au=lambda:'b',
      aa=lambda a:a in DOMAIN,h237c=lambda p,c,r:p in DOMAIN and(c,r)==('b','reference'),
      h26zi=lambda *a:a==('b','a','b','reference'),
      h27bx=lambda *a:'a',h27bw=lambda c,l,h,p,ctx:'b' if p=='a' else 'a',
      ue=lambda *a:a==('a','b','presentation'),h27as=lambda *a:a==('a','b','a','b','presentation'))
    v['h27bz']=lambda n,a,t,p,c:(n,a,c)==('b','a','presentation') and norm(t)==norm(codes[4]) and norm(p)==norm(codes[5])
    v['h26ub']=lambda n,a,t,c:(n,a,c)==('a','a','prior') and norm(t)==norm(codes[7])
    v['h27b2']=lambda *a:a==('b','a','a','a','b','a','b','reference','presentation')
    v['h27b4']=lambda n,a,p,g,code,s,c:(n,a,s,c)==('a','a','b','presentation') and g==('b' if p=='a' else 'a') and norm(code)==norm(codes[6])
    v['h27ar']=lambda n,a,code,s,c:n in DOMAIN and(a,s,c)==('a','b','presentation') and norm(code)==norm(codes[6])
    return v,codes
def run(d,v,memo=True):return evaluate(d,v,DOMAIN,SCENES,memo)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def family_checks():
    q=''.join('q[t[c[k '+n+'['+args(SCOPE)+']]['+z('person')+']]['+z('point')+']].' for n in ('r6jp','r6jq'))
    d=fixture(('r6jp','r6jq'),q,('r6jd','r6jo'),capture=False);base,_=model(d);calls=[]
    def target(c,l,h,p):calls.append(('target',(c,l,h,p)));return content(lambda t:t=='end')
    def depiction(r,n,g,c):calls.append(('depiction',(r,n,g,c)));return content(lambda t:t=='end')
    base.update(r6jd=target,r6jo=depiction,h27bv=lambda *a:'b',h27by=lambda *a:'physical')
    for symbol in ('h27bv','h27bw','h27bx','h27by'):
        old=base[symbol]
        def f(*a,symbol=symbol,old=old):calls.append((symbol,a));return old(*a)
        base[symbol]=f
    rows=[]
    for c,l,h,p in product(DOMAIN,repeat=4):
        v=dict(base);values=(c,l,h,p)
        for n,value in zip((*SCOPE,'person'),values):v['z'+n]=lambda value=value:value
        calls.clear();selected=(c,l,h)==('b','a','b');assert run(d,v,False)==[True,selected]
        assert [a for n,a in calls if n=='target']==[values]
        for n in ('h27bv','h27bx','h27by'):assert {a for name,a in calls if name==n}=={(c,l,h,'presentation')}
        assert {a for n,a in calls if n=='h27bw'}=={(c,l,h,p,'presentation')}
        assert {a for n,a in calls if n=='depiction'}=={('physical','b','b' if p=='a' else 'a','a')}
        rows.append(dict(scope=values,depiction_selected=selected))
    v=dict(base);v['aa']=lambda *a:False;assert run(d,v)==[True,False]
    # Same closed functions, evaluated only when an explicit unquotation is requested.
    q=''.join('q[t[c[s['+code+']]['+z('person')+']]['+z('point')+']].' for code in (TARGET,DEPICTION))
    d=fixture(('r6jr','r6js'),q,('r6jd','r6jo'));v,cs=model(d)
    v.update(r6jd=target,r6jo=depiction,h27bv=lambda *a:'b',h27by=lambda *a:'physical')
    assert run(d,v)==[True,True,True]
    v['r6jd']=lambda *a:content(lambda t:False);assert run(d,v)==[True,False,True]
    v['r6jo']=lambda *a:content(lambda t:False);assert run(d,v)==[True,False,False]
    return dict(all_sixteen_comparison_person_bindings=rows,selectors_use_presentation_not_result_point=True,
      closed_functions_execute_independently_only_on_explicit_unquotation=True,
      boundary='Only r6jd/r6jo are content boundaries here. Their unmodified native bodies are pinned by germ-regime-connection and nurtured-germ reports.')

@lru_cache(None)
def presentation_checks():
    d=fixture(('r6jt',),'q[k r6jt['+args(SCOPE)+']].');v,cs=model(d);assert run(d,v)==[True,True];cases={}
    for n in ('h27ad','h27ah','h27bf','h27bb','h27bv','h27by','h7a','h7b','h26y3'):
        assert v.get(n,unknown) is unknown
    for name in ('no_presentation','swapped_descriptions','extensionally_same_alias','wrong_author','wrong_node','wrong_context','bad_community_name','bad_lower_name','bad_higher_name','bad_reference_name'):
        w=dict(v)
        if name=='no_presentation':w['h27bz']=lambda *a:False
        if name=='swapped_descriptions':w['h27bz']=lambda n,a,t,p,c:norm(t)==norm(cs[5]) and norm(p)==norm(cs[4])
        if name=='extensionally_same_alias':w['h27bz']=lambda n,a,t,p,c:norm(t)==norm(cs[8])
        if name=='wrong_author':w['wa']=lambda:'b'
        if name=='wrong_node':w['h27av']=lambda:'a'
        if name=='wrong_context':w['h27aw']=lambda:'other'
        if name=='bad_community_name':w['h223g']=lambda a:cs[0]
        if name=='bad_lower_name':w['h223g']=lambda a:cs[1]
        if name=='bad_higher_name':w['zhigherorder']=lambda:'a';w['h223g']=lambda a:cs[1]
        if name=='bad_reference_name':w['h223h']=lambda p:cs[3]
        assert run(d,w)==[True,False],name;cases[name]=False
    for n in ('h27bz','h223g','h223h'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    q='q[k rw7[k h27av[] k wa[] '+TARGET+' '+TARGET+' k h27aw[] p h27bz]].'
    d=fixture(('rw7','r6jr','h27av','wa','h27aw','h27bz'),q);v,cs=model(d);v['h27bz']=lambda *a:True;assert run(d,v)==[True,False]
    return dict(cases=cases,native_rw7_requires_distinct_closed_descriptions=True,no_target_or_depiction_truth_evaluated=True,unknown_rejected=True)

@lru_cache(None)
def cover_checks():
    d=fixture(('r6ju',),'q[k r6ju['+args(SCOPE)+']].');v,cs=model(d);assert run(d,v)==[True,True];cases={}
    for name in ('same_nodes','prior_not_attributed','wrong_prior_content','wrong_prior_context','no_forward_order','reverse_order','other_cover','wrong_low_order','wrong_community','wrong_reference','no_mapping'):
        w=dict(v)
        if name=='same_nodes':w['h27b3']=lambda:'a'
        if name=='prior_not_attributed':w['h26ub']=lambda *a:False
        if name=='wrong_prior_content':w['h26ub']=lambda n,a,t,c:norm(t)!=norm(cs[7])
        if name=='wrong_prior_context':w['h26zk']=lambda:'presentation'
        if name=='no_forward_order':w['ue']=lambda *a:False
        if name=='reverse_order':w['ue']=lambda *a:a in (('a','b','presentation'),('b','a','presentation'))
        if name=='other_cover':w['h27bx']=lambda *a:'b'
        if name=='wrong_low_order':w['zlowerorder']=lambda:'b'
        if name=='wrong_community':w['zcommunity']=lambda:'a'
        if name=='wrong_reference':w['h26zj']=lambda:'other'
        if name=='no_mapping':w['h27b2']=lambda *a:False
        assert run(d,w)==[True,False],name;cases[name]=False
    # Every primitive mapping position must carry the actual bound value.
    expected=('b','a','a','a','b','a','b','reference','presentation')
    for slot in range(9):
        w=dict(v);bad=list(expected);bad[slot]='__mismatch__';w['h27b2']=lambda *a:a==tuple(bad)
        assert run(d,w)==[True,False],slot
    for n in ('h26ub','h27bx','h27b2','ue'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=cases,all_nine_mapping_slots_checked=True,exact_prior_lower_side_content_and_context=True,
      prior_content_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def germ_checks():
    d=fixture(('r6jv','r6je'),'q[k r6jv['+args(SCOPE)+']].q[k r6je['+z('community')+']].');v,cs=model(d)
    assert run(d,v)==[True,True,True];rows=[]
    for first,second in product((False,True),repeat=2):
        w=dict(v);w['h27b4']=lambda n,a,p,g,code,s,c:(first if p=='a' else second) and v['h27b4'](n,a,p,g,code,s,c)
        assert run(d,w)==[True,first and second,True];rows.append((first,second))
    for name in ('other_germ','wrong_person_property','wrong_scope','wrong_context','wrong_author','bad_reference_name'):
        w=dict(v)
        if name=='other_germ':w['h27bw']=lambda c,l,h,p,ctx:p
        if name=='wrong_person_property':w['h27b4']=lambda n,a,p,g,code,s,c:norm(code)==norm(cs[4])
        if name=='wrong_scope':w['h27av']=lambda:'a'
        if name=='wrong_context':w['h27aw']=lambda:'other'
        if name=='wrong_author':w['wa']=lambda:'b'
        if name=='bad_reference_name':w['h223h']=lambda p:cs[3]
        assert run(d,w)[1] is False,name
    v,cs=model(d);v['h237c']=lambda p,c,r:p=='a' and(c,r)==('b','reference')
    v['h27b4']=lambda n,a,p,g,code,s,c:p=='a' and norm(code)==norm(cs[6]);assert run(d,v)==[True,True,True]
    for n in ('h27b4','h27bw'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(all_member_mapping_rows=rows,nonmember_not_required=True,same_two_disposition_property_as_apposition=True,
      no_disposition_or_growth_truth_evaluated=True,unknown_rejected=True)

@lru_cache(None)
def whole_checks():
    d=fixture(('r6jw',),'q[k r6jw[]].');v,cs=model(d);assert run(d,v)==[True,True]
    for n in ('h27bz','h26ub','h27b2','h27b4','h27ar','h27as'):
        w=dict(v);w[n]=lambda *a:False;assert run(d,w)==[True,False],n
    w=dict(v);w['h26zi']=lambda *a:False;assert run(d,w)==[True,False]
    # Independent Boolean oracle for the four conjuncts on two selected comparison cases.
    d=fixture(('r6jw',),'q[k r6jw[]].',('r6jt','r6ju','r6jv','r6je'),capture=False);base,_=model(d)
    cases=(('a','a','b'),('b','a','b'));count=0
    base['h26zi']=lambda c,l,h,r:(c,l,h) in cases and r=='reference'
    for bits in product((False,True),repeat=8):
        v=dict(base)
        for i,n in enumerate(('r6jt','r6ju','r6jv')):v[n]=lambda c,l,h,i=i:bits[cases.index((c,l,h))*4+i] if(c,l,h) in cases else True
        v['r6je']=lambda c:bits[DOMAIN.index(c)*4+3]
        assert run(d,v)==[all(bits)];count+=1
    return dict(native_whole_requires_presentation_cover_germ_and_apposition=True,empty_comparison_rejected=True,
      independent_two_comparison_four_conjunct_assignments=count,
      boundary='Only the Boolean oracle replaces the four local conjuncts; native r6jw and native local relations execute above.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
    return dict(status='same_comparison_germ_and_cover_figurative_connection_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[716,871],text=u['text'][716:871],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      unresolved=['条件全体と人口・時点への量化','漸次の反作用・行為能力・政府原則','自己利益判断・機械以上の人間・尊厳・著者注参照'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS,
        'data/nurtured-germ-reading-v1.json','data/germ-regime-connection-reading-v1.json','data/cover-reference-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for old in (parent(),main_catalog()):
        for n,e in old.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    ds,m=legacy();assert c.entries['rw7']['declaration']==ds[0] and c.entries['rw7']['meaning_ja']==m
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d','e','f')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    # The prior-content quote in r6ju remains opaque; unlike the other adapters,
    # r6ju never decodes a name or applies a dynamically constructed description.
    assert ranks=={n:0 if n=='r6ju' else 1 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,
      imported_bodies_and_meanings_unchanged=True,roundtrips=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('families',family_checks),('presentation',presentation_checks),('cover',cover_checks),('germ',germ_checks),('whole',whole_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,OLD,OLD_BASIS,*PRIORS,
      'scripts/compose_germ_figurative_connection.py','scripts/check_germ_figurative_connection.py','tests/test_germ_figurative_connection.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='germ_cover_nature_figurative_connection_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
