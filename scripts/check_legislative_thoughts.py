"""Check an improvement issue, fallible personal views and their public offering."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_legislative_thoughts import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,FRAME,NAMES,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts import check_offered_judgments as offered

DOC='docs/legislative-thoughts-v1.md';READING='data/legislative-thoughts-reading-v1.json'
INDEX='data/semantic-review-index-v202.json';SOURCE='data/ninth-paragraph-source-reading-v2.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/legislative-formulations-v1.json','reports/offered-judgments-v1.json','reports/religious-emphasis-sentence-v1.json')
DOMAIN=(*offered.DOMAIN,*FRAME,'revision','newform','faculty')
SCENES=offered.SCENES
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def codeid(c):return c.rank,json.loads(c.syntax)
FARGS=args((*FRAME,'reference'));PARGS=args(('person','activity','scholar','audience'))
MESSAGE='o a[r[p r53m]][r['+z('reference')+']]'
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r ztruth[a d d] c.d h26ae[item a reference d] e[b point[k ztruth[v item v reference v point]]].r zsavemessage[i[h[a] f]] c.'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']};d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d['declarations']=closure(d,(*roots,*ns,'r53m'))
    return parse(format_graph(d,'compact')+'q[k zsavemessage['+MESSAGE+']].'+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)[1:]
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def issue_literal():return (0,dict(kind='apply',function=dict(kind='function_ref',symbol='r6cq'),arguments=[dict(kind='call',symbol='z'+n,arguments=[]) for n in (*FRAME,'reference')]))
def model(d):
    v,saved=offered.model(d);v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['znamepick']=lambda p,*cs:cs[DOMAIN.index(p)];v['zrefpick']=lambda p,*cs:cs[SCENES.index(p)]
    v.update(r6cm=lambda *a:a==('ruler','people','community','baseline','oldform','reference'),
        r6cp=lambda *a:a==('ruler','people','community','baseline','revision','oldform','newform','reference'),
        h26tg=lambda s,c,r:(s,c,r)==('standard','community','reference'),
        h26ti=lambda i,p,r,c:i in ('item','second') and codeid(p)==(0,dict(kind='function_ref',symbol='h26ae')) and r=='reference' and codeid(c)==issue_literal(),
        ab=lambda f,p,t:(f,p,t)==('faculty','person','now'),ac=lambda p,f,a,t:(p,f,a,t)==('person','faculty','activity','now'))
    return v

@lru_cache(None)
def comparison_checks():
    q='q[t[c[k r6cq['+FARGS+']]['+args(('revision','newform'))+']]['+z('now')+']].'
    d=fixture(('r6cq',),q,('r6cp',));rows=[]
    pairs=(('baseline','oldform','baseline','oldform'),('revision','newform','revision','newform'),
           ('baseline','oldform','revision','newform'),('revision','newform','baseline','oldform'))
    def relation(bits):
        return lambda s,l,f,r,g,c,ref,t:(s,c,ref)==('standard','community','reference') and (l,f,r,g) in pairs and bits[pairs.index((l,f,r,g))]
    for bits in product((False,True),repeat=4):
        v=model(d);v['h26th']=relation(bits);want=bits[0] and bits[1] and bits[2] and not bits[3]
        assert run(d,v)==[want],bits;rows.append(dict(comparisons=list(bits),strict_improvement=want))
    v=model(d);v['h26th']=relation((True,True,True,False));cases={}
    for name in (*FRAME,'reference','revision','newform'):
        w=dict(v);w['z'+name]=lambda:'later' if name=='reference' else 'other'
        assert run(d,w)==[False],name;cases[name]=False
    for n in ('r6cp','h26tg','h26th'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(all_pair_comparisons=rows,ties_and_missing_reflexivity_rejected=True,reference_mutations=cases,unknown_rejected=True,
        boundary='r6cp is an exact eight-argument boundary; the pinned legislative-formulations report executes the complete formulation and revision construction.')

@lru_cache(None)
def own_public_checks():
    q='q[k r6cu['+args(('person','item'))+' '+FARGS+' '+z('now')+']].q[k r6cv['+PARGS+' '+z('item')+' '+FARGS+' '+z('now')+']].'
    d=fixture(('r6cu','r6cv'),q,('r6cm',));v=model(d);assert run(d,v)==[True,True];rows={}
    for case in ('not_same_issue','different_content_provider','no_own_judgment','no_acceptance','other_persons_judgment','wrong_baseline','wrong_standard','misnamed_ruler','misnamed_reference','not_public_role','wrong_public','not_whole_readership','not_occurring','not_own_voice','different_activity','no_understanding','others_faculty','different_use_activity','no_review_purpose','false_presented_content','no_actual_improvement'):
        w=dict(v);want=[False,False]
        if case=='not_same_issue':w['h26ti']=lambda *a:False
        if case=='different_content_provider':w['h26ti']=lambda i,p,r,c:codeid(p)==(0,dict(kind='function_ref',symbol='r5cc'))
        if case=='no_own_judgment':w['h26ai']=lambda *a:False
        if case=='no_acceptance':w['h26af']=lambda *a:False
        if case=='other_persons_judgment':w['h26ai']=lambda p,j,r,t:p=='other'
        if case=='wrong_baseline':w['r6cm']=lambda r,p,c,b,f,ref:b=='revision'
        if case=='wrong_standard':w['h26tg']=lambda *a:False
        if case=='misnamed_ruler':w['znamepick']=lambda p,*cs:cs[DOMAIN.index('other' if p=='ruler' else p)]
        if case=='misnamed_reference':w['zrefpick']=lambda p,*cs:cs[-1]
        public=('not_public_role','wrong_public','not_whole_readership','not_occurring','not_own_voice','different_activity','no_understanding','others_faculty','different_use_activity')
        if case in public:want=[True,False]
        if case=='not_public_role':w['cb']=lambda *a:False
        if case=='wrong_public':w['cc']=lambda a,b,r:b=='other'
        if case=='not_whole_readership':w['ce']=lambda *a:False
        if case=='not_occurring':w['dg']=lambda *a:False
        if case=='not_own_voice':w['h253l']=lambda p,a,principal,role,i,c,t:principal=='other'
        if case=='different_activity':w['f2']=lambda a,*rest:a=='other'
        if case=='no_understanding':w['ab']=lambda *a:False
        if case=='others_faculty':w['ab']=lambda f,p,t:p=='other'
        if case=='different_use_activity':w['ac']=lambda p,f,a,t:a=='other'
        if case=='no_review_purpose':w['hzu']=lambda *a:False;want=[True,True]
        if case=='false_presented_content':w['ztruth']=lambda *a:False;want=[True,True]
        if case=='no_actual_improvement':w['h26th']=lambda *a:False;want=[True,True]
        got=run(d,w);assert got==want,(case,got,want);rows[case]=got
    for n in ('h26ti','h26tg','h26ai','h245q','ab','ac','f2','h253l'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    assert v['ztruth'] is unknown and v['h26th'] is unknown
    w=dict(v);w['zitem']=lambda:'alias';assert run(d,w)==[True,True]
    return dict(cases=rows,native_own_judgment_and_public_presentation=True,same_person_activity_faculty_and_issue=True,
        false_views_and_unrealized_improvement_permitted=True,review_purpose_not_added=True,unknown_rejected=True,
        boundary='Only r6cm legal baseline frame is a boundary. r53n/r53q/rhe and their judgment, public role and own-voice dependencies execute natively; content truth and comparison truth remain unknown.')

@lru_cache(None)
def plural_checks():
    def case(items):
        seq='l[a]['+args(items)+']';q='q[k r6cw['+PARGS+' '+seq+' '+FARGS+' '+z('now')+']].'
        d=fixture(('r6cw',),q,('r6cm',));return d,model(d)
    rows={}
    for items in ((),('item',),('item','second'),('second','item'),('item','item')):
        d,v=case(items);got=run(d,v);assert got==[bool(items)];rows[str(items)]=got[0]
    d,v=case(('item','second'))
    for case in ('second_not_own','second_elsewhere','second_different_activity','second_unrelated'):
        w=dict(v)
        if case=='second_not_own':w['h26af']=lambda p,i,r,t:i=='item'
        if case=='second_elsewhere':w['h245q']=lambda j,i,c,r,s,t:i=='item' or t=='later'
        if case=='second_different_activity':w['f2']=lambda a,p,i,c,t:i=='item' or a=='other'
        if case=='second_unrelated':w['h26ti']=lambda i,*a:i=='item'
        assert run(d,w)==[False],case;rows[case]=False
    return dict(cases=rows,all_items_share_one_public_activity=True,nonempty_arbitrary_finite_sequence=True)

@lru_cache(None)
def binding_checks():
    seq='l[a]['+args(('item','second'))+']'
    def make(names,quoted,marked=0,expected_mark=0):
        bindings='l[a]['+args(names)+']'
        content=('c[s[k r6cy[r['+seq+']]]]['+bindings+' '+z('reference')+']') if quoted else 'k r6cx['+seq+' '+bindings+' '+z('reference')+']'
        d=fixture(('r6cy' if quoted else 'r6cx',),'q[t['+content+']['+z('now')+']].',('r6cw',));v=model(d)
        # Two distinguishable individuals suffice to test each slot, while
        # the native existential destructuring then has 2**10 cases, not 28**10.
        for n in DOMAIN:v['z'+n]=lambda:'alpha'
        for i,n in enumerate(NAMES):v['z'+n]=lambda i=i:'beta' if i==marked else 'alpha'
        v['zitem']=lambda:'alpha';v['zsecond']=lambda:'beta';v['zother']=lambda:'alpha'
        slots=tuple('beta' if i==expected_mark else 'alpha' for i in range(10))
        expected=(*slots[:4],('alpha','beta'),*slots[4:],'reference','now')
        v['r6cw']=lambda *a:tuple(tuple(x.items) if hasattr(x,'items') else x for x in a)==expected
        return evaluate(d,v,('alpha','beta'),SCENES,True)[1]
    for quoted in (False,True):
        for i in range(10):
            assert make(NAMES,quoted,i,i),(quoted,i)
            assert not make(NAMES,quoted,i,(i+1)%10),(quoted,i)
        assert not make(NAMES[:-1],quoted) and not make((*NAMES,'person'),quoted)
    return dict(direct_and_quoted_targets=True,all_ten_positions_and_wrong_lengths_checked=True,closed_items_preserved=True,
        finite_model='Two distinguishable individuals test ten diagonal and ten displaced slots for each direct/quoted target, plus wrong lengths.',
        boundary='r6cw only; native plural action body checked separately')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0016')
    fragments=('von ihrer eigenen Vernunft öffentlichen Gebrauch zu machen','ihre Gedanken über eine bessere Abfassung derselben','der Welt öffentlich vorzulegen')
    segments=[]
    for f in fragments:
        a=u['text'].index(f,390);segments.append(dict(unit=u['id'],range=[a,a+len(f)],text=f,definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
    return dict(status='legislative_improvement_issue_and_public_thoughts_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],alignment=dict(segments=segments),interpretation=LIMITS,
      unresolved=['同じ既存法についての率直な批判','同じ全臣民と全発表候補への許可','危険・洞察・思考態度・啓蒙への照応と拡張','実例・尊敬する君主の先行者不在・全文提示と通読'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,SOURCE,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();dep=dependency();assert not c.document['statements'] and len(old.document['statements'])==118
    for source in (old,dep):
        for n,e in source.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:int(n not in ('r6cq','r6cr','r6cs')) for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('comparison',comparison_checks),('own_public',own_public_checks),('plural',plural_checks),('binding',binding_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,SOURCE,INVENTORY,*PRIORS,
      'scripts/compose_legislative_thoughts.py','scripts/check_legislative_thoughts.py','tests/test_legislative_thoughts.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_offered_judgments.py'}
    return dict(status='own_public_legislative_thoughts_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
