"""Check nonfactive dispositions, normal alternatives and valid two-feature growth."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_thinking_impulse_development import ROOT,LIBRARY,BASIS,OLD,OLD_BASIS,CODE,TRUE,FALSE,MEANINGS,PRIMITIVES,LIMITS,parent,legacy,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/thinking-impulse-development-v1.md';READING='data/thinking-impulse-development-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v206.json'
LEXICAL='data/thinking-disposition-reading-review-v1.json'
PRIORS=('reports/thinking-disposition-v1.json','reports/covered-unfolding-v1.json','reports/civic-intellectual-options-v1.json','reports/acquired-affection-v1.json')
DOMAIN=('a','b');SCENES=('reference','other','start','middle','end','oldnormal','normal','peer','exception')
CONSTANTS=dict(community='b',person='a',reference='reference',anchor='end',point='end',process='b',start='start',end='end',feature='a')
SCOPE=('community','person','reference');GROWTH=(*SCOPE,'process','start','end')
PREFIX='r za[] a.r zb[] a.r zref[] d.r zother[] d.'
TARGET='k r6is[r[k zb[]] r[k zref[]]]';ALTERNATIVE='r[i[person a][b point[k aa[v person]]]]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def norm(x):return (x.rank,json.dumps(json.loads(x.syntax),sort_keys=True)) if hasattr(x,'syntax') else x
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),capture=True):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=PREFIX+''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    extra+='r zcapture[i[a] i[a] i[d] i[d] '+CODE+' '+CODE+'] c.'
    prefix=parse('p:'+extra)['declarations'];ns={r['name'] for r in prefix}
    d['declarations']=prefix+d['declarations'];d['declarations']=closure(d,(*roots,*ns,*(('r6is',) if capture else ())))
    if capture:query='q[k zcapture[r[k za[]] r[k zb[]] r[k zref[]] r[k zother[]] '+TARGET+' '+ALTERNATIVE+']].'+query
    return parse(format_graph(d,'compact')+query)

def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};codes=[]
    def capture(*xs):codes[:]=xs;return True
    v.update({'z'+n:lambda v=v:v for n,v in CONSTANTS.items()})
    v.update(za=lambda:'a',zb=lambda:'b',zref=lambda:'reference',zother=lambda:'other',zcapture=capture,
      h223g=lambda n:codes[DOMAIN.index(n)],h223h=lambda n:codes[2 if n=='reference' else 3],
      aa=lambda p:p=='a',h237c=lambda p,c,r:(p,c,r)==('a','b','reference'),
      h26ys=lambda c,p,t,r:(c,p,t,r)==('b','a','b','reference'),h26yt=lambda t,m,r:t=='b' and r=='reference' and m in DOMAIN)
    def correct(c,r,p,target):return (c,r,p)==('b','reference','a') and norm(target)==norm(codes[4])
    def scope(c,r,p,t,anchor,impulse,s):return correct(c,r,p,t) and s in (('oldnormal',) if anchor=='start' else ('normal','peer','exception') if anchor=='end' else ())
    v['h27ad']=scope;v['h27ae']=v['h27aj']=scope
    v['h27af']=lambda c,r,p,t,s:correct(c,r,p,t) and s in ('oldnormal','normal','peer','exception')
    v['h27ag']=lambda c,r,p,t,a,i,l,h:scope(c,r,p,t,a,i,l) and scope(c,r,p,t,a,i,h) and l in ('normal','peer') and h=='exception'
    v['h27ah']=lambda c,r,p,t,s:correct(c,r,p,t) and s in ('normal','peer')
    v['h27ai']=lambda c,r,p,t,s:correct(c,r,p,t) and s in ('oldnormal','normal','peer')
    v.update(h27ak=lambda r:'a',h27al=lambda r:'b')
    def history(c,p,r,s,e,t):return (c,p,r,s,e)==('b','a','reference','start','end') and t in ('start','middle','end')
    v['h27am']=history
    v['h27an']=lambda c,p,r,s,e,l,h:history(c,p,r,s,e,l) and history(c,p,r,s,e,h) and ('start','middle','end').index(l)<('start','middle','end').index(h)
    v['h27ao']=lambda *a:a==('b','a','reference','b','start','end')
    v['h27ap']=lambda *a:a==('b','reference','b','a','start','end')
    v['h27aq']=lambda c,r,p,f,t:(c,r,p,t)==('b','reference','a','start') and f in DOMAIN
    return v,codes
def run(d,v,memo=True):return evaluate(d,v,DOMAIN,SCENES,memo)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def target_checks():
    q='q[t[c[s['+TARGET+']]['+z('person')+']]['+z('point')+']].'
    d=fixture(('r6is',),q);v,cs=model(d)
    v.update(ab=lambda f,p,t:(f,p,t)==('b','a','end'),ac=lambda p,f,j,t:(p,f,t)==('a','b','end'),
      fa=lambda p,j,t:(p,t)==('a','end'),fb=lambda j,m,t:j==m and t=='end',fc=lambda j,r,t:(r,t)==('a','end'),
      fd=lambda r,j,t:(r,t)==('a','end'),ad=lambda *a:False,
      h26yu=lambda p,task,j,r,t:(p,task,r,t)==('a','b','reference','end'))
    assert run(d,v)==[True,True];cases={}
    for name in ('no_task','empty_matters','other_member','other_owner','unsupported','one_missing_matter','guided','no_judgment'):
        w=dict(v)
        if name=='no_task':w['h26ys']=lambda *a:False
        if name=='empty_matters':w['h26yt']=lambda *a:False
        if name=='other_member':w['h237c']=lambda p,c,r:p=='b'
        if name=='other_owner':w['ab']=lambda f,p,t:p=='b'
        if name=='unsupported':w['fd']=lambda *a:False
        if name=='one_missing_matter':w['h26yu']=lambda p,t,j,r,s:j=='a'
        if name=='guided':w['ad']=lambda l,p,j,t:l!=p
        if name=='no_judgment':w['fa']=lambda *a:False
        assert run(d,w)==[True,False],name;cases[name]=False
    q='q[k r6iv['+args(SCOPE)+' '+z('anchor')+' '+FALSE+']].'
    d=fixture(('r6iv',),q);v,cs=model(d);assert run(d,v)==[True,True]
    assert all(v[n] is unknown for n in ('ab','ac','fa','fb','fc','fd','ad','h26yu'))
    for name in ('bad_community_name','bad_reference_name','wrong_target','nonmember','empty_task_scope','empty_task_matters'):
        w=dict(v)
        if name=='bad_community_name':w['h223g']=lambda n:cs[0]
        if name=='bad_reference_name':w['h223h']=lambda n:cs[3]
        if name=='wrong_target':w['h27ah']=lambda c,r,p,t,s:norm(t)==norm(cs[5])
        if name=='nonmember':w['h237c']=lambda *a:False
        if name=='empty_task_scope':w['h26ys']=lambda *a:False
        if name=='empty_task_matters':w['h26yt']=lambda *a:False
        assert run(d,w)==[True,False],name
    return dict(cases=cases,real_closed_same_thinking_property=True,native_r6hh_and_rcr_target=True,
      wrong_names_or_target_rejected=True,attitude_does_not_execute_or_require_thinking=True)

@lru_cache(None)
def normality_checks():
    q=''.join('q[k '+n+'['+args(SCOPE)+' '+z('anchor')+' '+flag+']].' for flag in (FALSE,TRUE) for n in ('r6iu','r6iv'))
    d=fixture(('r6iu','r6iv'),q);base,cs=model(d);nodes=('normal','peer');rows=[]
    for mask in range(16):
        edges={(a,b) for i,(a,b) in enumerate(product(nodes,repeat=2)) if mask&(1<<i)}
        valid=not any(a==b for a,b in edges) and not {('normal','peer'),('peer','normal')}<=edges
        minima={b for b in nodes if not any((a,b) in edges for a in nodes)}
        for response in product((False,True),repeat=2):
            v=dict(base);v['h27ad']=lambda c,r,p,t,a,i,s:(c,r,p,a)==('b','reference','a','end') and s in nodes
            v['h27ae']=v['h27aj']=v['h27ad'];v['h27ag']=lambda *a:(a[-2],a[-1]) in edges
            v['h27ah']=lambda *a:a[-1] in nodes and response[nodes.index(a[-1])]
            v['h27ai']=lambda *a:a[-1] in nodes and not response[nodes.index(a[-1])]
            favorable=valid and bool(minima) and all(response[nodes.index(x)] for x in minima)
            impulse=valid and bool(minima) and all(not response[nodes.index(x)] for x in minima)
            expected=[True,valid,favorable,valid,impulse];assert run(d,v)==expected,(mask,response)
            rows.append(dict(edges=sorted(edges),response=response,valid=valid,favorable=favorable,impulse=impulse))
    v,cs=model(d);assert run(d,v)==[True]*5 # nonresponding exception is properly dominated
    for name in ('empty','unpreserved_exception','unelicited_exception','unassessed_exception','missing_normal_response','invalid_transitivity','cycle','wrong_person','wrong_reference'):
        w=dict(v)
        if name=='empty':w['h27ad']=lambda *a:False
        if name=='unpreserved_exception':w['h27ae']=lambda *a:a[-1]!='exception' and v['h27ae'](*a)
        if name=='unelicited_exception':w['h27af']=lambda *a:a[-1]!='exception' and v['h27af'](*a)
        if name=='unassessed_exception':w['h27aj']=lambda *a:a[-1]!='exception' and v['h27aj'](*a)
        if name=='missing_normal_response':w['h27ah']=w['h27ai']=lambda *a:a[-1]=='normal'
        if name=='invalid_transitivity':w['h27ag']=lambda *a:a[-2:] in (('normal','peer'),('peer','exception'))
        if name=='cycle':w['h27ag']=lambda *a:a[-2:] in (('normal','peer'),('peer','normal'))
        if name=='wrong_person':w['zperson']=lambda:'b'
        if name=='wrong_reference':w['zreference']=lambda:'other'
        expected=[True,True,False,True,False] if name=='missing_normal_response' else [True,False,False,False,False]
        assert run(d,w)==expected,(name,run(d,w))
    for n in ('h27ad','h27ae','h27af','h27ag','h27ah','h27ai','h27aj'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(independent_two_candidate_order_response_cases=rows,native_rqt4_irreflexive_transitive_minima=True,
      dominated_exception_allowed_but_peer_failure_not_ignored=True,all_candidates_preserved_elicited_and_assessed=True,unknown_rejected=True)

@lru_cache(None)
def pair_checks():
    q='q[t[k r6iw['+args(SCOPE)+']]['+z('point')+']].'+''.join('q[k r6ix['+args(SCOPE)+' k '+n+'[k zreference[]] '+z('point')+']].' for n in ('h27ak','h27al'))
    d=fixture(('r6iw','r6ix'),q);base,cs=model(d);rows=[]
    for favorable,impulse in product((False,True),repeat=2):
        v=dict(base);v['h27ah']=lambda *a:favorable and a[-1] in ('normal','peer');v['h27ai']=lambda *a:impulse and a[-1] in ('normal','peer')
        assert run(d,v)==[True,favorable and impulse,favorable,impulse];rows.append(dict(favorable=favorable,impulse=impulse))
    v,cs=model(d);v['zpoint']=lambda:'start';assert run(d,v)==[True,False,False,True]
    return dict(independent_two_dispositions=rows,same_person_and_point_for_conjunction=True,initially_one_manifest_feature_allowed=True)

@lru_cache(None)
def development_checks():
    q='q[k r6iy['+args(GROWTH)+']].';d=fixture(('r6iy',),q);v,cs=model(d);assert run(d,v)==[True,True];cases={}
    for name in ('same_features','already_both_manifest','neither_manifest_at_end','only_one_manifest_at_end','unassessed_start','empty_start_candidates','invalid_start_order','missing_latent','wrong_person_affected','wrong_process','missing_transition','empty_history','missing_middle_order','reverse_time','same_endpoints','wrong_reference'):
        w=dict(v)
        if name=='same_features':w['h27al']=lambda r:'a'
        if name=='already_both_manifest':w['h27ah']=lambda *a:a[-1] in ('oldnormal','normal','peer')
        if name=='neither_manifest_at_end':w['h27ah']=w['h27ai']=lambda *a:False
        if name=='only_one_manifest_at_end':w['h27ah']=lambda *a:False
        if name=='unassessed_start':w['h27aj']=lambda *a:a[-3]!='start' and v['h27aj'](*a)
        if name=='empty_start_candidates':w['h27ad']=lambda *a:a[-3]!='start' and v['h27ad'](*a)
        if name=='invalid_start_order':w['h27ag']=lambda *a:a[-2:]==('oldnormal','oldnormal') or v['h27ag'](*a)
        if name=='missing_latent':w['h27aq']=lambda *a:a[-2]=='b' and v['h27aq'](*a)
        if name=='wrong_person_affected':w['h27ap']=lambda *a:a==('b','reference','b','b','start','end')
        if name=='wrong_process':w['zprocess']=lambda:'a'
        if name=='missing_transition':w['h27ao']=lambda *a:False
        if name=='empty_history':w['h27am']=lambda *a:False
        if name=='missing_middle_order':w['h27an']=lambda *a:'middle' not in a[-2:] and v['h27an'](*a)
        if name=='reverse_time':w['h27an']=lambda *a:v['h27an'](*a[:-2],a[-1],a[-2])
        if name=='same_endpoints':w['zstart']=lambda:'end'
        if name=='wrong_reference':w['zreference']=lambda:'other'
        assert run(d,w)==[True,False],name;cases[name]=False
    w=dict(v);w['h27ai']=lambda *a:a[-1] in ('normal','peer');assert run(d,w)==[True,True]
    for n in ('h27am','h27an','h27ao','h27ap','h27aq'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Same process/body under the endpoint content, then under a fixed end.
    q='q[t[k r6iz['+args(SCOPE)+' '+z('start')+']]['+z('end')+']].q[t[k r6i2['+args(SCOPE)+']]['+z('end')+']].'
    d=fixture(('r6iz','r6i2'),q);v,cs=model(d);assert run(d,v)==[True,True,True]
    v['h27ap']=lambda *a:False;assert run(d,v)==[True,False,False]
    return dict(cases=cases,native_rw4_tg_and_dispositions=True,initial_one_or_neither_manifest_allowed=True,
      both_latent_and_both_final_manifest_required=True,invalid_baseline_not_counted_as_growth=True,
      process_history_same_person_and_endpoint_content_bound=True)

@lru_cache(None)
def adapter_checks():
    q='q[k r6iy['+args(GROWTH)+']].';d=fixture(('r6iy',),q,('r6iu','r6ix','rw4'));base,cs=model(d);calls=[]
    base['r6iu']=lambda *a:True
    def record(n):
        def f(*a):calls.append((n,a));return True
        return f
    for n in ('h27am','h27an','h27ao','h27ap','h27aq','r6ix'):base[n]=record(n)
    def growth(person,process,start,end,history,before,transitions,affected,features,latent,manifest):
        calls.append(('rw4',(person,process,start,end)))
        history('middle');before('middle','other');transitions('a','middle','other');affected('a','b','middle','other')
        assert features('a') and features('b');latent('b','a','other');manifest('b','a','other');return True
    base['rw4']=growth
    def expected(c):
        fixed=(c['community'],c['person'],c['reference']);cr=(c['community'],c['reference'])
        return [('rw4',(c['person'],c['process'],c['start'],c['end'])),
          ('h27am',(*fixed,c['start'],c['end'],'middle')),('h27an',(*fixed,c['start'],c['end'],'middle','other')),
          ('h27ao',(*fixed,'a','middle','other')),('h27ap',(*cr,'a','b','middle','other')),
          ('h27aq',(*cr,'b','a','other')),('r6ix',(c['community'],'b',c['reference'],'a','other'))]
    for changed in (None,*GROWTH):
        c=dict(CONSTANTS);v=dict(base)
        if changed:c[changed]='other' if changed in ('reference','start','end') else ('b' if c[changed]=='a' else 'a');v['z'+changed]=lambda changed=changed:c[changed]
        calls.clear();run(d,v,False);assert calls==expected(c),(changed,calls)
    # Record every comparison-provider slot against the exact closed target.
    q='q[k r6iv['+args(SCOPE)+' '+z('anchor')+' '+TRUE+']].'
    d=fixture(('r6iv',),q,('r6iu','rqt4'));v,cs=model(d);calls.clear();v['r6iu']=lambda *a:True
    for n in ('h27ad','h27ag','h27ah','h27ai'):
        def f(*a,n=n):calls.append((n,tuple(norm(x) for x in a)));return True
        v[n]=f
    def normal(cases,preferred,response):cases('other');preferred('other','middle');response('other');return True
    v['rqt4']=normal;assert run(d,v,False)==[True,True]
    ctx=('b','reference','a',norm(cs[4]));assert calls==[
      ('h27ad',(*ctx,'end',True,'other')),('h27ag',(*ctx,'end',True,'other','middle')),
      ('h27ah',(*ctx,'other')),('h27ai',(*ctx,'other'))],calls
    return dict(all_six_growth_arguments_and_callback_objects_forwarded=True,comparison_same_target_and_mode_bound=True,
      boundary='r6iu/r6ix/rw4 or r6iu/rqt4 only for call recording; native bodies execute in the preceding tests.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');phrase='nämlich den Hang und Beruf zum freien Denken, ausgewikkelt hat;';a=u['text'].index(phrase)
    return dict(status='chosen_inner_impulse_reading_and_two_feature_development_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,selected_beruf_reading='inner_impulse_toward_free_thinking',alternative_preserved_in='data/thinking-disposition-basis-v1.json',
      choice_reason='同じ芽から内側の働きが展開するという前件を、肯定的な傾きと内的な促しという二性向の発達として採る。外部の任命・義務付与をこの句へ追加しない。自然の作用と世話は別の描写対応で保持する予定であり、選択の正しさを辞書又は検査が証明したとはしない。',
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      unresolved=['自然・芽・覆いと第三文の制度の対応','nämlichの同格と条件文前件の人口への適用','世話・反作用・行為能力・政府・尊厳・全文帰属'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,LEXICAL,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements'];p=parent()
    for n,e in p.entries.items():
        if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    ds,means=legacy()
    for row in ds:assert c.entries[row['name']]['declaration']==row
    assert c.entries['rw4']['meaning_ja']==means['rw4']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    for row in read(LEXICAL)['sources']:assert digest((ROOT/row['artifact']).read_bytes())==row['artifact_sha256']
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
    assert ranks=={n:0 if n in ('r6iq','r6ir','r6is') else 1 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,
      inherited_bodies_and_meanings_unchanged=True,roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('target',target_checks),('normality',normality_checks),('pair',pair_checks),('development',development_checks),('adapters',adapter_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,LEXICAL,OLD,OLD_BASIS,*PRIORS,
      'scripts/compose_thinking_impulse_development.py','scripts/check_thinking_impulse_development.py','tests/test_thinking_impulse_development.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    paths.update(row['artifact'] for row in read(LEXICAL)['sources'])
    return dict(status='two_thinking_dispositions_and_latent_development_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
