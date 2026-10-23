"""Check institutional adoption, semantic aliases and fixed complete scope."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_government_principle_profile import ROOT,LIBRARY,BASIS,CODE,MEANINGS,PRIMITIVES,LIMITS,parent,legacy,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scoped_counts import arithmetic

DOC='docs/government-principle-profile-v1.md';READING='data/government-principle-profile-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v206.json'
PRIORS=('reports/governing-principles-v1.json','reports/government-release-v1.json')
ARTIFACTS=tuple('artifacts/government-principle-profile-v1/'+n for n in ('fetch.json','grundsatz.html','grundsatz.txt'))
DOMAIN=('a','b');SCENES=('reference','start','end','probeone','probetwo','other');PROBES=('probeone','probetwo')
CONSTANTS=dict(government='a',community='b',reference='reference',rule='a',candidate='a',first='a',second='b',point='start',start='start',end='end')
ARGS='k zgovernment[] k zcommunity[] k zreference[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def seq(xs):return SequenceValue(tuple(xs),'"individual"')
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for r in d['declarations']:
        if r['name'] in boundaries:r.update(kind='primitive',parameters=[p['sort'] for p in r['parameters']]);r.pop('body')
    d['declarations']=closure(d,roots)
    extra=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    extra+='r zfirstvalue[d] c.r zsecondvalue[d] c.r zcapture['+CODE+' '+CODE+'] c.'
    extra+='d zpolicyfirst[bindings j[a]] e[b at[w[e[d[v bindings]][n p a b]][k zfirstvalue[v at]]]].'
    extra+='d zpolicysecond[bindings j[a]] e[b at[w[e[d[v bindings]][n p a b]][k zsecondvalue[v at]]]].'
    return parse(format_graph(d,'compact')+extra+'q[k zcapture[r[p zpolicyfirst] r[p zpolicysecond]]].'+query)

def good(g,c,r):return(g,c,r)==('a','b','reference')
def model(d,first=1,second=2,old=1,new=2):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};v.update(arithmetic());codes=[];calls=[]
    v.update({'z'+n:lambda x=x:x for n,x in CONSTANTS.items()})
    def capture(*xs):codes[:]=xs;return True
    def selected(g,c,r,rule):return good(g,c,r) and rule in DOMAIN
    def required(source,actor,office,code,bindings,sign,point):
        calls.append((source,actor,office,code,bindings,sign,point))
        mask=old if point=='start' else new if point=='end' else 0
        return (source,actor,office)==('a','a','b') and bindings.items==() and sign and any(code==codes[i] and bool(mask&(1<<i)) for i in range(2))
    def value(mask,t):return bool(mask&(1<<PROBES.index(t))) if t in PROBES else False
    v.update(zcapture=capture,zfirstvalue=lambda t:value(first,t),zsecondvalue=lambda t:value(second,t),
      h237n=good,h256s=good,h27c6=lambda c,r:'a',h27c7=lambda *a:'b',h27df=lambda g,o,c,r:good(g,c,r) and o=='b',
      h27da=lambda *a:seq(DOMAIN if good(*a) else ()),h27db=selected,
      h27dc=lambda g,c,r,rule:codes[DOMAIN.index(rule)],h27dd=lambda g,c,r,rule,t:selected(g,c,r,rule) and t in ('start','end'),
      h27de=lambda g,c,r,t:good(g,c,r) and t in PROBES,h7k=required)
    return v,codes,calls
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)[1:]
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def adoption_checks():
    d=fixture(('r6k3','r6k4'),'q[k r6k3['+ARGS+']].q[k r6k4['+ARGS+' k zrule[] k zpoint[]]].')
    v,codes,calls=model(d);assert run(d,v)==[True,True]
    assert calls and all(row[:3]==('a','a','b') and row[3]==codes[0] and row[4].items==() and row[5] for row in calls)
    w=dict(v);w['zfirstvalue']=unknown;assert run(d,w)==[True,True]
    # Even identical contents do not transfer a norm to its other description.
    w,codes,calls=model(d,first=1,second=1);w['zrule']=lambda:'b';assert run(d,w)==[True,False]
    cases={}
    for label in ('wrong_government','wrong_community','wrong_reference','no_directing_position','no_jurisdiction','unassigned_office','wrong_office','not_selected'):
        w,_,_=model(d)
        if label=='wrong_government':w['zgovernment']=lambda:'b'
        if label=='wrong_community':w['zcommunity']=lambda:'a'
        if label=='wrong_reference':w['zreference']=lambda:'other'
        if label=='no_directing_position':w['h237n']=lambda *a:False
        if label=='no_jurisdiction':w['h256s']=lambda *a:False
        if label=='unassigned_office':w['h27df']=lambda *a:False
        if label=='wrong_office':w['h27c7']=lambda *a:'a'
        if label=='not_selected':w['h27db']=lambda *a:False
        result=run(d,w);assert not all(result),(label,result);cases[label]=result
    for n in ('h7k','h27dc','h27df','h237n','h256s'):
        w,_,_=model(d);w[n]=unknown;rejects(d,w)
    return dict(native_institution_and_normative_adoption=True,exact_source_addressee_office_code_empty_arguments_and_sign=True,
      actual_rule_content_not_executed=True,identical_alias_does_not_inherit_norm=True,contrasts=cases,unknown_rejected=True)

@lru_cache(None)
def profile_checks():
    d=fixture(('r6k5','r6k6','r6la'),'q[k r6k5['+ARGS+' k zfirst[] k zsecond[]]].q[k r6k6['+ARGS+' k zcandidate[] k zpoint[]]].q[k r6la['+ARGS+' k zstart[] k zend[]]].')
    rows=0
    for first,second,old,new in product(range(4),repeat=4):
        v,_,_=model(d,first,second,old,new)
        # Independent observation of the set of adopted truth tables. Names
        # remain distinct in h7k, but do not distinguish a content class.
        tables=(first,second)
        before={tables[i] for i in range(2) if old&(1<<i)}
        after={tables[i] for i in range(2) if new&(1<<i)}
        expected=[first==second,first in before,before!=after]
        assert run(d,v)==expected,(first,second,old,new,expected);rows+=1
    v,_,_=model(d,first=1,second=1,old=1,new=2);assert run(d,v)==[True,True,False]
    for old,new in ((0,1),(1,0),(1,3),(3,1)):
        v,_,_=model(d,old=old,new=new);assert run(d,v)[-1] is True,(old,new)
    for old,new in ((0,0),(1,1),(3,3)):
        v,_,_=model(d,old=old,new=new);assert run(d,v)[-1] is False
    v,_,_=model(d,first=1,second=3,old=1,new=2)
    v['h27de']=lambda g,c,r,t:good(g,c,r) and t=='probeone'
    assert run(d,v)==[True,True,False] # explicitly relative to the selected probes
    for n in ('zfirstvalue','zsecondvalue','h27de','h7k'):
        w,_,_=model(d);w[n]=unknown;rejects(d,w)
    return dict(all_256_native_content_and_adoption_rows=rows,rename_only_rejected=True,addition_or_withdrawal_without_replacement_allowed=True,
      unchanged_adoption_rejected=True,equivalence_explicitly_relative_to_full_fixed_probes=True,unknown_rejected=True)

@lru_cache(None)
def scope_checks():
    d=fixture(('r6k7','r6la'),'q[k r6k7['+ARGS+' k zpoint[]]].q[k r6la['+ARGS+' k zstart[] k zend[]]].')
    v,_,_=model(d);assert run(d,v)==[True,True];cases={}
    for label in ('empty_candidates','omitted_candidate','duplicate_candidate','empty_probes','missing_first_assessment','missing_last_assessment','same_point'):
        w,_,_=model(d)
        if label=='empty_candidates':w['h27da']=lambda *a:seq(());w['h27db']=lambda *a:False
        if label=='omitted_candidate':w['h27da']=lambda *a:seq(('a',))
        if label=='duplicate_candidate':w['h27da']=lambda *a:seq(('a','b','b'))
        if label=='empty_probes':w['h27de']=lambda *a:False
        if label=='missing_first_assessment':w['h27dd']=lambda g,c,r,rule,t:rule!='b' or t!='start'
        if label=='missing_last_assessment':w['h27dd']=lambda g,c,r,rule,t:rule!='b' or t!='end'
        if label=='same_point':w['zend']=lambda:'start'
        result=run(d,w);assert result[-1] is False,(label,result);cases[label]=result
    for n in ('h27da','h27db','h27dd'):
        w,_,_=model(d);w[n]=unknown;rejects(d,w)
    return dict(native_complete_inventory_and_both_assessments=True,contrasts=cases,unknown_rejected=True)

@lru_cache(None)
def wrapper_checks():
    d=fixture(('r6lb',),'q[t[k r6lb['+ARGS+' k zstart[]]][k zpoint[]]].',('r6la',));v,_,_=model(d);calls=[]
    def body(*a):calls.append(a);return a==('a','b','reference','start','end')
    v['r6la']=body;rows=0
    for g,c,r,s,e in product(DOMAIN,DOMAIN,('reference','other'),('start','end'),('start','end')):
        w=dict(v)
        for n,x in zip(('government','community','reference','start','point'),(g,c,r,s,e)):w['z'+n]=lambda x=x:x
        calls.clear();assert run(d,w)==[(g,c,r,s,e)==('a','b','reference','start','end')]
        assert(g,c,r,s,e)in calls;rows+=1
    return dict(all_32_bindings=rows,boundary='Only r6la is replaced; its native body is checked separately.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
    return dict(status='government_practical_rule_content_profile_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[1026,1057],text=u['text'][1026:1057],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      unresolved=['原則への因果的作用、endlichとauch/sogar','具体的な尊厳規則、機械以上の人間、政府自身の利益判断','Wenn/soの全体量化と全文帰属・通読判断'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS,*ARTIFACTS)})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for n,e in parent().entries.items():
        if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    ds,means=legacy()
    for d in ds:assert c.entries[d['name']]['declaration']==d and c.entries[d['name']]['meaning_ja']==means[d['name']]
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert(ROOT/p).read_text(encoding='utf-8')==b,p
    fetch=read(ARTIFACTS[0]);assert digest((ROOT/ARTIFACTS[1]).read_bytes())==fetch['raw_sha256'];assert digest((ROOT/ARTIFACTS[2]).read_bytes())==fetch['text_sha256']
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};text=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d','e')):
            try:parse(text+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:1 if n in ('r6k5','r6k6','r6la','r6lb') else 0 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,
      imported_bodies_and_meanings_unchanged=True,roundtrips=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('adoption',adoption_checks),('profile',profile_checks),('scope',scope_checks),('wrapper',wrapper_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,*ARTIFACTS,
      'scripts/compose_government_principle_profile.py','scripts/check_government_principle_profile.py','tests/test_government_principle_profile.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py'}
    return dict(status='government_practical_rule_content_profile_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
