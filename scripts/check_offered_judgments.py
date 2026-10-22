"""Check actual content, quoted review purpose and exact plural-action binding."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import FORCES
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.review_registry import load_reviews
from noema.script import transcribe
from scripts.compose_offered_judgments import ROOT,LIBRARY,BASIS,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/offered-judgments-v1.md';READING='data/offered-judgments-reading-v1.json'
INDEX='data/semantic-review-index-v197.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/prince-sentence-v1.json','reports/cognitive-acquisition-v1.json','reports/scholarly-own-voice-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v1.json',)
DOMAIN=('person','activity','scholar','audience','item','second','alias','judgment','secondjudgment','reason','reader','review','other')
SCENES=('reference','now','later')
def z(n):return 'k z'+n+'[]'
def ns(names):return ' '.join(z(n) for n in names)
def codeid(c):return c.rank,json.loads(c.syntax)
MESSAGE='o a[r[p r53m]][r['+z('reference')+']]'
def goal(item):return 'o a[r[p r53p]][r['+z('audience')+'] r['+z(item)+'] r['+z('reference')+']]'
SAVE='q[k zsavemessage['+MESSAGE+']].'+''.join('q[k zsave'+n+'['+goal(n)+']].' for n in ('item','second'))
PREFIX=('person','activity','scholar','audience')
def call(name,item='item'):return 'k '+name+'['+ns((*PREFIX,item,'reference','now'))+']'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,boundary=False):
    d=deepcopy(catalog().document)
    if boundary:
        row=next(x for x in d['declarations'] if x['name']=='r53u')
        row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r ztruth[a d d] c.d h26ae[item a reference d] e[b point[k ztruth[v item v reference v point]]].'
    extra+='r zsavemessage[i[h[a] f]] c.r zsaveitem[i[e]] c.r zsavesecond[i[e]] c.r zinspect[f] c.'
    provider=parse('p:'+extra);replaced={x['name'] for x in provider['declarations']}
    d['declarations']=provider['declarations']+[x for x in d['declarations'] if x['name'] not in replaced]
    helpers=[x['name'] for x in provider['declarations'] if x['name'].startswith('z')]
    d.update(declarations=closure(d,(*roots,*helpers)),statements=[])
    return parse(format_graph(d,'compact')+query)

def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

def model(d):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(znamepick=lambda p,*cs:cs[DOMAIN.index(p)],zrefpick=lambda p,*cs:cs[SCENES.index(p)])
    for n in ('message','item','second'):v['zsave'+n]=lambda c,n=n:saved.update({n:codeid(c)}) is None
    v['aa']=lambda p:p in ('person','reader')
    v['h26ad']=lambda i,r:i in ('item','second','alias') and r=='reference'
    v['h26ag']=lambda i,r:'item' if i=='alias' else i
    v['h26af']=lambda p,i,r,t:(p,r,t)==('person','reference','now') and i in ('item','second')
    v['h26ai']=lambda p,j,r,t:(p,r,t)==('person','reference','now') and j in ('judgment','secondjudgment')
    v['h245q']=lambda j,i,c,r,s,t:(r,s,t)==('reference',True,'now') and (j,i) in (('judgment','item'),('secondjudgment','second')) and codeid(c)==(0,dict(kind='function_ref',symbol='h26ae'))
    v['h26ah']=lambda p,i,r,t:(p,r,t)==('person','reference','now') and i in ('item','second')
    v['fc']=lambda j,r,t:j in ('judgment','secondjudgment') and(r,t)==('reason','now')
    v['fd']=lambda r,j,t:j in ('judgment','secondjudgment') and(r,t)==('reason','now')
    v['h26aj']=lambda r,j,ref,t:j in ('judgment','secondjudgment') and(r,ref,t)==('reason','reference','now')
    v['ca']=lambda p,a,r:(p,a,r)==('person','activity','reference')
    v['cb']=lambda p,a,s,r:(p,a,s,r)==('person','activity','scholar','reference')
    v['cd']=lambda s,r:(s,r)==('scholar','reference')
    v['cc']=lambda a,b,r:(a,b,r)==('activity','audience','reference')
    v['ce']=lambda a,r:(a,r)==('audience','reference')
    v['h6t']=lambda a,p,r:(a,p,r)==('audience','reader','reference')
    v['dg']=lambda a,t:(a,t)==('activity','now')
    v['f3']=lambda p,a,t:(p,a,t)==('person','activity','now')
    v['f2']=lambda a,p,i,c,t:(a,p,t)==('activity','reader','now') and i in ('item','second') and codeid(c)==saved['message']
    v['h253l']=lambda p,a,principal,role,i,c,t:(p,a,principal,role,t)==('person','activity','person','scholar','now') and i in ('item','second') and codeid(c)==saved['message']
    v['hzu']=lambda p,a,c,t:(p,a,t)==('person','activity','now') and codeid(c) in (saved['item'],saved['second'])
    v['fa']=lambda p,j,t:(p,j,t)==('reader','review','later')
    v['fb']=lambda j,i,t:(j,i,t)==('review','item','later')
    v['hzv']=lambda j,i,c,t:(j,i,t)==('review','item','later') and codeid(c)==saved['message']
    return v,saved

@lru_cache(None)
def holding_checks():
    args=ns(('person','judgment','item','reference','now'))
    d=fixture(('r53n','r53o'),'q[k r53n['+args+']].q[k r53o['+args+']].');rows={}
    base=('aa','h26ad','h26af','h26ai','h245q');extra=('h26ah','fc','fd','h26aj')
    for missing in (None,*base,*extra):
        v,_=model(d)
        if missing:v[missing]=lambda *a:False
        expected=[missing not in base,missing is None]
        assert run(d,v)==expected,(missing,expected);rows[missing or 'baseline']=expected
    for n in (*base,*extra):v,_=model(d);v[n]=unknown;rejects(d,v)
    v,_=model(d);v['zitem']=lambda:'alias';assert run(d,v)==[True,True]
    for n in ('h26ai','h245q','fc','fd','h26aj'):
        v,_=model(d);old=v[n]
        v[n]=lambda *a,old=old:old(*tuple('other' if x in ('judgment','secondjudgment') else x for x in a))
        assert run(d,v)[1] is False,n
    return dict(cases=rows,held_not_necessarily_currently_performed_judgment=True,same_judgment_grounds=True,
        canonical_alias=True,proposition_truth_never_evaluated=True,unknown_rejected=True)

@lru_cache(None)
def purpose_checks():
    q=SAVE+'q[t[k r53p['+ns(('audience','item','reference'))+']]['+z('later')+']].'
    d=fixture(('r53p','r53m'),q);rows={}
    for missing in (None,'aa','h6t','ce','fa','fb','hzv'):
        v,_=model(d)
        if missing:v[missing]=lambda *a:False
        got=run(d,v);assert got==[True]*3+[missing is None];rows[missing or 'baseline']=got[-1]
    for n in ('fa','fb','hzv'):
        v,_=model(d);old=v[n]
        for position in range({'fa':3,'fb':3,'hzv':4}[n]):
            def altered(*a,old=old,position=position):
                a=list(a);a[position]='other'
                try:return old(*a)
                except AttributeError:return False
            v[n]=altered
            assert run(d,v)==[True]*3+[False],(n,position)
    for n in ('aa','h6t','ce','fa','fb','hzv'):
        v,_=model(d);v[n]=unknown;rejects(d,v)
    native=fixture(('r53m',),''.join('q[k zinspect[c[s['+MESSAGE+']]['+z(n)+']]].' for n in ('item','alias','second')))
    v,_=model(native);seen=[]
    v['ztruth']=lambda i,r,t:r=='reference' and (i,t) in (('item','now'),('second','later'))
    v['zinspect']=lambda m:seen.append((m.force,m.content.values)) is None
    assert run(native,v)==[True]*3
    assert seen==[(FORCES['s'],(False,True,False)),(FORCES['s'],(False,True,False)),(FORCES['s'],(False,False,True))]
    return dict(cases=rows,same_representative_and_message=True,scope_fixed_at_reference=True,
        native_message_payload_and_alias_checked=True,only_one_human_reviewer_required=True,
        truth_agreement_or_positive_outcome_not_required=True,unknown_rejected=True)

@lru_cache(None)
def presentation_checks():
    q=SAVE+''.join('q['+call(n)+'].' for n in ('r53r','r53s','r53t'))
    d=fixture(('r53r','r53s','r53t','r53m'),q);rows={}
    essential=('ca','cb','cd','cc','ce','h6t','dg','f3','f2','h253l','hzu')
    for missing in (None,*essential):
        v,_=model(d)
        if missing:v[missing]=lambda *a:False
        got=run(d,v);assert got==[True]*3+[missing is None]*3,(missing,got);rows[missing or 'baseline']=got[-3:]
    v,_=model(d)
    for n in ('fa','fb','hzv','ztruth'):v[n]=unknown
    assert run(d,v)==[True]*6
    v,_=model(d);old=v['aa'];v['aa']=lambda p:p=='person';assert run(d,v)==[True]*3+[False]*3
    v,_=model(d);v['h26ai']=lambda *a:False;assert run(d,v)==[True]*3+[True,False,False]
    mismatches=0
    for n,length in (('f2',5),('h253l',7),('hzu',4)):
        for pos in range(length):
            v,_=model(d);old=v[n]
            def altered(*a,old=old,pos=pos):
                a=list(a);a[pos]='other' if pos!=length-2 else None
                # A malformed code is rejected here as a nonmatch, not passed to the evaluator.
                if any(x is None for x in a):return False
                try:return old(*a)
                except AttributeError:return False
            v[n]=altered;assert run(d,v)==[True]*3+[False]*3,(n,pos);mismatches+=1
    for n in essential:v,_=model(d);v[n]=unknown;rejects(d,v)
    v,_=model(d);old=v['znamepick'];v['znamepick']=lambda p,*cs:old('other' if p=='item' else p,*cs)
    assert run(d,v)==[True]*3+[False]*3
    v,_=model(d);old=v['zrefpick'];v['zrefpick']=lambda p,*cs:old('later' if p=='reference' else p,*cs)
    assert run(d,v)==[True]*3+[False]*3
    return dict(cases=rows,argument_mismatches=mismatches,name_mismatch_rejected=True,
        purpose_and_asserted_proposition_not_executed=True,human_audience_required=True,unknown_rejected=True,
        boundaries='No semantic definitions replaced; only name providers and proposition content have native fixture implementations.')

@lru_cache(None)
def plural_checks():
    q=SAVE+'q[k r53u['+ns(PREFIX)+' l[a]['+z('item')+'] l[a]['+z('second')+'] '+ns(('reference','now'))+']].'
    d=fixture(('r53u','r53m'),q);v,_=model(d);assert run(d,v)==[True]*4
    v,_=model(d);old=v['h26ah'];v['h26ah']=lambda p,i,r,t:old(p,i,r,t) and i!='second';assert run(d,v)==[True]*3+[False]
    v,_=model(d);v['f2']=lambda a,p,i,c,t:(a,p,t)==('activity','reader','now') and i=='item';assert run(d,v)==[True]*3+[False]
    # Same composite execution remains one activity, including each review purpose.
    v,saved=model(d);v['hzu']=lambda p,a,c,t:(p,a,t)==('person','activity','now') and codeid(c)==saved['item'];assert run(d,v)==[True]*3+[False]
    empty=fixture(('r53u',),'q[k r53u['+ns(PREFIX)+' l[a][] l[a][] '+ns(('reference','now'))+']].')
    v,_=model(empty);assert run(empty,v)==[False]
    # Exact adapter tested over two individuals with a declared boundary, avoiding
    # a 13**4 re-evaluation of the already tested entire speech model.
    lists='l[a]['+z('item')+'] l[a]['+z('second')+']';bindings='l[a]['+ns(PREFIX)+']'
    target='k r53w[r[l[a]['+z('item')+']] r[l[a]['+z('second')+']]]'
    q='q[t[k r53v['+lists+' '+bindings+' '+z('reference')+']]['+z('now')+']].'
    q+='q[t[c[s['+target+']]['+bindings+' '+z('reference')+']]['+z('now')+']].'
    b=fixture(('r53v','r53w'),q,True)
    def bound_model():
        v,_=model(b);v.update({'z'+n:lambda n=n:'left' if n in ('person','scholar','item') else 'right' for n in DOMAIN})
        v['r53u']=lambda p,a,s,u,j,i,r,t:(p,a,s,u,tuple(j.items),tuple(i.items),r,t)==('left','right','left','right',('left',),('right',),'reference','now')
        return v
    assert run(b,bound_model(),('left','right'))==[True,True]
    for name in PREFIX:
        v=bound_model();old=v['z'+name];value=old();v['z'+name]=lambda value=value:'right' if value=='left' else 'left'
        assert run(b,v,('left','right'))==[False,False],name
    for wrong in ('l[a][]','l[a]['+ns(PREFIX[:3])+']','l[a]['+ns((*PREFIX,'other'))+']'):
        bad=fixture(('r53v','r53w'),q.replace(bindings,wrong),True)
        assert run(bad,bound_model(),('left','right'))==[False,False]
    return dict(native_two_item_presentation=True,every_item_and_purpose_required=True,empty_union_rejected=True,
        native_and_dequoted_adapter_equal=True,exact_four_bindings=True,
        boundary='Only r53u is replaced for the four-binder adapter test; r53u and all its dependencies execute natively in the two-item test.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='public_presentation_dependency_reading_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[574,889],text=u['text'][574:889]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['採用信条との相違とhier oder da','同じ君主への照応と聖職者の敬意評価','職務義務を保つ自由と無制約の他者','noch mehrの提示と全文の帰属・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*SOURCES,*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();old=parent()
    assert len(old.document['statements'])==113 and not c.document['statements']
    for n,e in c.entries.items():
        if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==17
    for row in reviews:assert row['selection']==selection_binding(old,[s['index'] for s in row['selection']['statements']])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        text=format_graph(c.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==c.document
    text=format_graph(c.document,'compact')
    try:parse(text+'q[e[r[p r53v]][r[p r53v]]].')
    except ValueError as e:assert 'Quoted evaluation' in str(e)
    else:raise AssertionError('Rank zero quotation accepted')
    parse(text+'q[e[r b[p r53v]][r b[p r53v]]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=0,new_statements=0,main_statements_preserved=113,
        whole_unit_reviews_preserved=17,new_verified_characters=0,rank_one_target_required=True,roundtrips=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in (('holding',holding_checks),('purpose',purpose_checks),('presentation',presentation_checks),('plural',plural_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,*SOURCES,
        'scripts/compose_offered_judgments.py','scripts/check_offered_judgments.py','tests/test_offered_judgments.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='personal_judgment_and_insight_presentation_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
