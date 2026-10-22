"""Check fixed names, regime views and nonfactive comparison candidates."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_advantage_appearance import ROOT,LIBRARY,BASIS,OLD,OLD_BASIS,CODE,MEANINGS,PRIMITIVES,LIMITS,parents,legacy,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/civic-advantage-appearance-v1.md';READING='data/civic-advantage-appearance-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v205.json'
PRIORS=('reports/civic-intellectual-options-v1.json','reports/policy-recognition-v1.json')
DOMAIN=tuple('abcd');SCENES=('reference','anchor','view','other','lzero','hzero','lone','hone','ltwo','htwo')
FIELDS=('community','lowerorder','higherorder','reference');ARGS=' '.join('k z'+n+'[]' for n in FIELDS)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def norm(xs):return tuple((v.rank,json.dumps(json.loads(v.syntax),sort_keys=True)) if hasattr(v,'syntax') else v for v in xs)
def code():return (2,json.dumps(dict(kind='apply',function=dict(kind='function_ref',symbol='r6ho'),arguments=[dict(kind='call',symbol='z'+n,arguments=[]) for n in FIELDS]),sort_keys=True))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(query,boundaries=('r6hg','r6hm')):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra='r zcommunity[] a.r zlowerorder[] a.r zhigherorder[] a.r zobserver[] a.r zreference[] d.r zother[] d.r zanchor[] d.'
    extra+='r znpick[a i[a] i[a] i[a] i[a]] i[a].d h223g[item a] i[a][k znpick[v item r[k zcommunity[]] r[k zlowerorder[]] r[k zhigherorder[]] r[k zobserver[]]]].'
    extra+='r zdpick[d i[d] i[d]] i[d].d h223h[item d] i[d][k zdpick[v item r[k zreference[]] r[k zother[]]]].'
    prefix=parse('p:'+extra)['declarations'];ns={r['name'] for r in prefix}
    d['declarations']=prefix+[r for r in d['declarations'] if r['name'] not in ns];d['declarations']=closure(d,('r6hs','r6ho','r6hq',*ns))
    return parse(format_graph(d,'compact')+query)
def model(d,civil_actual=True,civil_view=True,mental_actual=False,mental_view=True,selected=True):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update(zcommunity=lambda:'a',zlowerorder=lambda:'b',zhigherorder=lambda:'c',zobserver=lambda:'d',zreference=lambda:'reference',zother=lambda:'other',zanchor=lambda:'anchor',
      znpick=lambda x,a,b,c,d:{'a':a,'b':b,'c':c,'d':d}[x],zdpick=lambda x,a,b:a if x=='reference' else b,aa=lambda p:p=='d')
    pairs={'anchor':('lzero','hzero'),'view':('lone','hone')}
    v['h26yy']=lambda c,r,view:pairs.get(view,('ltwo','htwo'))[0]
    v['h26yz']=lambda c,r,view:pairs.get(view,('ltwo','htwo'))[1]
    v['r6hg']=lambda c,lo,hi,r,l,h:(c,lo,hi,r)==('a','b','c','reference') and ((l,h)==('lzero','hzero') and civil_actual or (l,h)==('lone','hone') and civil_view)
    v['r6hm']=lambda c,r,l,h:(c,r)==('a','reference') and ((l,h)==('lzero','hzero') and mental_actual or (l,h)==('lone','hone') and mental_view)
    v['h26y2']=lambda c,r,o,q,t,s:selected and(c,r,o,norm((q,))[0],t,s)==('a','reference','d',code(),'anchor','view')
    return v
def run(d,v,memo=True):return evaluate(d,v,DOMAIN,SCENES,memo)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def appearance_checks():
    q='q[t[k r6hs[k zobserver[] '+ARGS+']][k zanchor[]]].q[t[k r6ho['+ARGS+']][k zanchor[]]].'
    d=fixture(q);rows=[]
    for flags in product((False,True),repeat=5):
        ca,cv,ma,mv,selected=flags;v=model(d,*flags);want=ca and cv and mv and selected
        assert run(d,v)==[want,ca and ma],flags;rows.append(dict(flags=flags,appearance=want,actual_advantage=ca and ma))
    v=model(d);assert run(d,v)==[True,False]
    for name in ('wrong_observer','wrong_content','wrong_reference','wrong_anchor','mixed_candidates','nonhuman','empty_candidates'):
        w=dict(v)
        if name=='wrong_observer':w['h26y2']=lambda c,r,o,q,t,s:o=='a' and s=='view'
        if name=='wrong_content':w['h26y2']=lambda c,r,o,q,t,s:norm((q,))[0]!=(code()) and s=='view'
        if name=='wrong_reference':w['h26y2']=lambda c,r,o,q,t,s:r=='other' and s=='view'
        if name=='wrong_anchor':w['h26y2']=lambda c,r,o,q,t,s:t=='other' and s=='view'
        if name=='mixed_candidates':w['h26y2']=lambda c,r,o,q,t,s:s in ('view','other')
        if name=='nonhuman':w['aa']=lambda *a:False
        if name=='empty_candidates':w['h26y2']=lambda *a:False
        assert run(d,w)==[False,False],name
    for n in ('h26y2','r6hg','r6hm'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(matrix=rows,native_rro_nonempty_all_candidates=True,appearance_can_be_true_when_actual_advantage_false=True,
      actual_advantage_also_allowed=True,actual_civic_degree_required=True,unknown_rejected=True,
      boundaries='r6hg/r6hm for civic and intellectual truth tables; their native bodies and all argument bindings are pinned by civic-intellectual-options-v1.')

@lru_cache(None)
def names_and_points_checks():
    q='q[t[k r6hs[k zobserver[] '+ARGS+']][k zanchor[]]].q[k r6hr['+ARGS+']].'
    d=fixture(q);base=model(d);assert run(d,base)==[True,True]
    for field,wrong in (('community','b'),('lowerorder','c'),('higherorder','a')):
        w=dict(base)
        w['znpick']=lambda x,a,b,c,d,field=field,wrong=wrong:({'a':a,'b':b,'c':c,'d':d}[wrong] if x=={'community':'a','lowerorder':'b','higherorder':'c'}[field] else {'a':a,'b':b,'c':c,'d':d}[x])
        assert run(d,w)==[False,False],field
    w=dict(base);w['zdpick']=lambda x,a,b:b;assert run(d,w)==[False,False]
    for n in ('h26yy','h26yz'):
        w=dict(base);w[n]=lambda *a:'other';assert run(d,w)==[False,True],n
        w=dict(base);w[n]=unknown;rejects(d,w)
    # Each view gets its own pair; source identities and reference stay fixed.
    calls=[];w=dict(base)
    def civil(*a):calls.append(('civil',a));return True
    def mental(*a):calls.append(('mental',a));return True
    w['r6hg']=civil;w['r6hm']=mental;assert run(d,w)==[True,True]
    assert ('civil',('a','b','c','reference','lzero','hzero')) in calls
    assert ('civil',('a','b','c','reference','lone','hone')) in calls
    assert ('mental',('a','reference','lone','hone')) in calls
    assert all(a[:4]==('a','b','c','reference') if n=='civil' else a[:2]==('a','reference') for n,a in calls)
    return dict(all_four_name_bindings_checked=True,actual_and_candidate_regime_pairs_distinct=True,
      community_orders_and_reference_preserved_across_views=True,unknown_rejected=True)

@lru_cache(None)
def quotation_and_adapter_checks():
    codes=' '.join('r[k z'+n+'[]]' for n in FIELDS)
    q='q[e[k r6hq['+codes+']][k r6hq['+codes+']]].q[e[r d[p r6hs]][r d[p r6hs]]].'
    d=fixture(q);assert run(d,{r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'})==[True,True]
    q='q[t[k r6hs[k zobserver[] '+ARGS+']][k zanchor[]]].'
    d=fixture(q,('r6hg','r6hm','rro'));v=model(d);calls=[];anchors=[]
    def selected(*a):calls.append(norm(a));return True
    def attitude(observer,claim,anchor,alternatives):
        assert (observer,norm((claim,))[0])==('d',code())
        anchors.append(anchor)
        alternatives('a',claim,'other','view');return True
    v['h26y2']=selected;v['rro']=attitude;assert run(d,v,False)==[True]
    assert tuple(anchors)==SCENES,anchors
    assert calls==[('a','reference','a',code(),'other','view')]*len(SCENES),calls
    return dict(closed_comparison_quotation_does_not_execute_names_or_content=True,
      alternative_observer_content_anchor_and_candidate_forwarded=True,fixed_community_and_reference=True,
      boundary='rro only in the separate callback test; native rro runs in the appearance matrix.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');phrase='Ein größerer Grad bürgerlicher Freiheit scheint der Freiheit des Geistes des Volks vortheilhaft'
    a=u['text'].index(phrase,467)
    return dict(status='nonfactive_civic_advantage_comparison_dependency',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for p in parents():
        for n,e in p.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    ds,means=legacy()
    for row in ds:assert c.entries[row['name']]['declaration']==row and c.entries[row['name']]['meaning_ja']==means[row['name']]
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:3 if n=='r6hs' else 1 if n=='r6hr' else 0 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,
      inherited_bodies_and_meanings_unchanged=True,roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('appearance',appearance_checks),('names_and_points',names_and_points_checks),('quotation_and_adapters',quotation_and_adapter_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,OLD,OLD_BASIS,*PRIORS,
      'scripts/compose_civic_advantage_appearance.py','scripts/check_civic_advantage_appearance.py','tests/test_civic_advantage_appearance.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='nonfactive_civic_advantage_comparison_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
