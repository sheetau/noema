"""Check worthy regard without actual regard and shared ruler/clerical scope."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_revered_clerical_scope import ROOT,LIBRARY,BASIS,GROUND,RESPONSE,STANDARD,MEANINGS,PRIMITIVES,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/revered-clerical-scope-v1.md';READING='data/revered-clerical-scope-reading-v1.json'
INDEX='data/semantic-review-index-v197.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/clerical-duty-scope-v1.json','reports/prince-sentence-v1.json','reports/grateful-regard-v1.json','reports/personal-salvation-judgment-v1.json')
DOMAIN=('person','holder','office','church','ruler','rulingoffice','community','creed','subject','scholar','other')
SCENES=('reference','now','otherpoint','sourcepoint')
def z(n):return 'k z'+n+'[]'
def ns(names):return ' '.join(z(n) for n in names)
def codeid(c):return c.rank,json.loads(c.syntax)
G='k r54r[r['+z('office')+'] r['+z('church')+'] r['+z('reference')+']]'
R='k r54t[o r['+G+']]'
SAVE='q[k zsaveground['+G+']].q[k zsaveresponse['+R+']].'
LIST='l['+STANDARD+'][p zfirst p zsecond]'
CONCRETE=ns(('person','office','church','reference','now'))
SCOPE=ns(('ruler','rulingoffice','community','person','office','church','creed','subject','scholar','reference'))

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query):
    d=deepcopy(catalog().document)
    # Existing deep classifications are exact argument boundaries, not new meanings.
    for row in d['declarations']:
        if row['name'] in ('r35m','r35r','r5xh'):
            row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zsaveground['+GROUND+'] c.r zsaveresponse['+RESPONSE+'] c.'
    for name in ('first','second'):
        extra+='r z'+name+'fit[a '+RESPONSE+' '+GROUND+' d] c.d z'+name+'[person a response '+RESPONSE+' ground '+GROUND+'] e[b point[k z'+name+'fit[v person v response v ground v point]]].'
    extra+='r zchoose[a '+RESPONSE+' '+GROUND+' d j['+STANDARD+'] j['+STANDARD+']] j['+STANDARD+'].'
    extra+='d h26o5[person a response '+RESPONSE+' ground '+GROUND+' reference d] j['+STANDARD+'][k zchoose[v person v response v ground v reference '+LIST+' l['+STANDARD+'][]]].'
    extra+='r zqualified[a a a d] c.d r53b[] h[a a a] e[i[ruler a rulingoffice a community a][b point[k zqualified[v ruler v rulingoffice v community v point]]]].'
    prefix=parse('p:'+extra);replaced={row['name'] for row in prefix['declarations']}
    d['declarations']=prefix['declarations']+[row for row in d['declarations'] if row['name'] not in replaced]
    d.update(declarations=closure(d,(*roots,'r54r',*replaced)),statements=[])
    return parse(format_graph(d,'compact')+query)

def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')

def model(d):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(znamepick=lambda p,*codes:codes[DOMAIN.index(p)],zrefpick=lambda p,*codes:codes[SCENES.index(p)],
        zsaveground=lambda c:saved.update(ground=codeid(c)) is None,zsaveresponse=lambda c:saved.update(response=codeid(c)) is None,
        aa=lambda p:p in ('person','holder','ruler'))
    v['r35m']=lambda p,o,c,r:(p,o,c,r)==('person','office','church','reference')
    v['r35r']=lambda c,cr,s,r:(c,cr,s,r)==('church','creed','subject','reference')
    v['cf']=lambda p,o,t:(p,o,t)==('person','office','now')
    v['h246k']=lambda p,c,o,t:(p,c,o,t)==('person','church','office','now')
    v['h247d']=lambda p,r:'scholar' if (p,r)==('person','reference') else 'other'
    v['r5xh']=lambda p,o,c,t:(p,o,c,t)==('ruler','rulingoffice','community','now')
    v['h26hi']=lambda p,o,c,t:(p,o,c,t)==('person','rulingoffice','community','now')
    v['zqualified']=lambda p,o,c,t:(p,o,c,t)==('ruler','rulingoffice','community','now')
    v['h26km']=lambda:'sourcepoint';v['h26kn']=lambda p:'now' if p=='sourcepoint' else 'otherpoint'
    def same(p,r,g,t):return (p,t)==('person','now') and codeid(r)==saved['response'] and codeid(g)==saved['ground']
    v['zfirstfit']=same;v['zsecondfit']=same
    v['zchoose']=lambda p,r,g,ref,full,empty:full if ref=='reference' and same(p,r,g,'now') else empty
    return v,saved

@lru_cache(None)
def attitude_checks():
    q=SAVE+''.join('q[t[c['+f+']['+ns(('holder','person'))+']]['+z('now')+']].' for f in ('k r54s['+G+']','s['+R+']'))
    d=fixture(('r54s','r54t'),q);rows={}
    for case in ('baseline','no_regard','wrong_holder','wrong_subject','wrong_aspect','nonhuman'):
        v,saved=model(d)
        def regard(h,p,g,t):return (h,p,t)==('holder','person','now') and codeid(g)==saved['ground']
        v['h26nu']=regard
        if case=='no_regard':v['h26nu']=lambda *a:False
        if case=='wrong_holder':v['h26nu']=lambda h,p,g,t:regard('other',p,g,t)
        if case=='wrong_subject':v['h26nu']=lambda h,p,g,t:regard(h,'other',g,t)
        if case=='wrong_aspect':v['h26nu']=lambda *a:False
        if case=='nonhuman':v['aa']=lambda *a:False
        # Attitude and its quote do not evaluate whether the clerical ground is true.
        v['r35m']=unknown
        got=run(d,v);assert got==[True,True,case=='baseline',case=='baseline'],(case,got);rows[case]=got[2:]
    v,_=model(d);v['h26nu']=unknown;rejects(d,v)
    return dict(cases=rows,direct_and_dequoted_attitude_match=True,ground_not_executed_in_attitude=True,unknown_rejected=True)

@lru_cache(None)
def worthiness_checks():
    q=SAVE+'q[k r54u['+z('person')+' '+R+' '+G+' '+LIST+' '+z('now')+']].'
    d=fixture(('r54u','r54t'),q);rows=[]
    for ground,first,second in product((False,True),repeat=3):
        v,_=model(d)
        if not ground:v['r35m']=lambda *a:False
        if not first:v['zfirstfit']=lambda *a:False
        if not second:v['zsecondfit']=lambda *a:False
        assert v['h26nu'] is unknown
        got=run(d,v);assert got==[True,True,ground and first and second]
        rows.append(dict(ground=ground,first=first,second=second,worthy=got[-1]))
    empty=fixture(('r54u','r54t'),q.replace(LIST,'l['+STANDARD+'][]'));v,_=model(empty);assert run(empty,v)==[True,True,False]
    for name in ('r35m','zfirstfit','zsecondfit'):
        v,_=model(d);v[name]=unknown;rejects(d,v)
    # Equal truth at these points does not license substituting another code.
    alternative='r b[i[person a][b point[e[v person]['+z('person')+']]]]'
    changed=fixture(('r54u','r54t'),q.replace(' '+G+' '+LIST,' '+alternative+' '+LIST))
    v,_=model(changed);assert run(changed,v)==[True,True,False]
    return dict(eight_cases=rows,empty_criteria_rejected=True,no_actual_regard_or_response_execution=True,
        coextensive_ground_is_not_the_same_description=True,unknown_rejected=True)

@lru_cache(None)
def bound_worthiness_checks():
    d=fixture(('r54v',),SAVE+'q[k r54v['+CONCRETE+']].');rows={}
    for case in ('baseline','false_clerical_ground','empty_criteria','failed_second','wrong_office_name','wrong_church_name','wrong_reference_name','wrong_criterion_subject','wrong_criterion_point'):
        v,_=model(d)
        if case=='false_clerical_ground':v['r35m']=lambda *a:False
        if case=='empty_criteria':v['zchoose']=lambda p,r,g,ref,full,empty:empty
        if case=='failed_second':v['zsecondfit']=lambda *a:False
        if case in ('wrong_office_name','wrong_church_name'):
            item='office' if case=='wrong_office_name' else 'church';v['znamepick']=lambda p,*codes:codes[DOMAIN.index('other' if p==item else p)]
        if case=='wrong_reference_name':v['zrefpick']=lambda p,*codes:codes[SCENES.index('otherpoint')]
        if case=='wrong_criterion_subject':
            old=v['zfirstfit'];v['zfirstfit']=lambda p,*a:old('other',*a)
        if case=='wrong_criterion_point':
            old=v['zfirstfit'];v['zfirstfit']=lambda p,r,g,t:old(p,r,g,'otherpoint')
        got=run(d,v);assert got==[True,True,case=='baseline'],(case,got);rows[case]=got[-1]
    for name in ('zchoose','znamepick','zrefpick'):
        v,_=model(d);v[name]=unknown;rejects(d,v)
    return dict(cases=rows,three_names_validated=True,same_ground_response_and_person_for_all_criteria=True,
        boundary='r35m is an exact person/office/church/reference boundary backed by its prior native tests. Criteria check exact code bindings and two independent fit conditions; this does not prove the substantive adequacy of a normative standard.')

@lru_cache(None)
def ruler_checks():
    names=('ruler','rulingoffice','community','person')
    q='q[k r54w['+ns(names)+ ' '+z('now')+']].q[k r54x['+ns(names)+']].';d=fixture(('r54w','r54x'),q);rows={}
    for case in ('baseline','unqualified_ruler','other_rulingoffice','other_community','other_subject','other_ruler','other_anchor','nonhuman_subject'):
        v,_=model(d)
        if case=='unqualified_ruler':v['zqualified']=lambda *a:False
        if case in ('other_rulingoffice','other_community','other_subject'):
            old=v['h26hi'];pos={'other_subject':0,'other_rulingoffice':1,'other_community':2}[case]
            def wrong(*a):
                a=list(a);a[pos]='other';return old(*a)
            v['h26hi']=wrong
        if case=='other_ruler':
            old=v['r5xh'];v['r5xh']=lambda p,*a:old('other',*a)
        if case=='other_anchor':v['h26kn']=lambda *a:'otherpoint'
        if case=='nonhuman_subject':v['aa']=lambda *a:False
        got=run(d,v);expected=[case in ('baseline','unqualified_ruler','other_anchor'),case=='baseline'];assert got==expected,(case,got);rows[case]=got
    for name in ('h26hi','zqualified','r5xh'):
        v,_=model(d);v[name]=unknown;rejects(d,v)
    return dict(cases=rows,same_qualified_ruler_office_community_and_anchor=True,
        boundary='r5xh and the full r53b antecedent are exact shared-argument boundaries with prior native evidence. h26hi and the new composition execute natively; no obedience, policy performance or permission primitive is needed.')

@lru_cache(None)
def scope_checks():
    d=fixture(('r54z',),SAVE+'q[k r54z['+SCOPE+']].');rows={}
    for case in ('baseline','no_current_office','no_service','other_scholar','other_adopted_creed','not_worthy','not_under_ruler','not_qualified_ruler'):
        v,_=model(d)
        changed={'no_current_office':'cf','no_service':'h246k','other_adopted_creed':'r35r','not_worthy':'zfirstfit','not_under_ruler':'h26hi','not_qualified_ruler':'zqualified'}.get(case)
        if changed:v[changed]=lambda *a:False
        if case=='other_scholar':v['h247d']=lambda *a:'other'
        got=run(d,v);assert got==[True,True,case=='baseline'],(case,got);rows[case]=got[-1]
    return dict(cases=rows,same_clerical_and_political_roles_kept_distinct=True,no_actual_respect_obedience_or_publication_required=True,
        boundary='Same previously declared classification and qualification boundaries; r54n and all new scope/valuation definitions execute without a truth-value replacement of the combined condition.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='qualified_ruler_and_worthy_clergy_scope_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[574,889],text=u['text'][574:889]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['同じ対象範囲への全発表候補の自由','全職務の制限を受けない他者とnoch mehr','全文帰属と通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    c=catalog()
    for parent in parents():
        for n,e in c.entries.items():
            if n in parent.entries:assert e['declaration']==parent.entries[n]['declaration'] and e['meaning_ja']==parent.entries[n]['meaning_ja']
    assert not c.document['statements'] and len(parents()[1].document['statements'])==113
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact')
    for name,low,valid in (('r54v','b','c'),('r54z','b','c')):
        try:parse(t+'q[e[r '+low+'[p '+name+']][r '+low+'[p '+name+']]].')
        except ValueError as e:assert 'Quoted evaluation' in str(e)
        else:raise AssertionError('Low-rank quote accepted: '+name)
        parse(t+'q[e[r '+valid+'[p '+name+']][r '+valid+'[p '+name+']]].')
    parse(t+'q[e[r h[p r54z]][r h[p r54z]]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),main_statements_preserved=113,new_verified_characters=0,
        inherited_meanings_preserved=True,roundtrips=True,worthy_quote_rank=2,qualified_scope_minimum_quote_rank=2,rank_seven_presentation_available=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in (('attitude',attitude_checks),('worthiness',worthiness_checks),('bound_worthiness',bound_worthiness_checks),('ruler',ruler_checks),('scope',scope_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json',
        'scripts/compose_revered_clerical_scope.py','scripts/check_revered_clerical_scope.py','tests/test_revered_clerical_scope.py',
        'scripts/compose_prince_sentence.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='same_qualified_ruler_and_worthy_clergy_scope_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
