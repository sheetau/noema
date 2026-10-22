"""Check same-issue doctrine comparison and its exact offered-action binding."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.review_registry import load_reviews
from noema.script import transcribe
from scripts.compose_confessional_divergence import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,NAMES,parents,build,closure
from scripts import check_offered_judgments as prior
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/confessional-divergence-v1.md';READING='data/confessional-divergence-reading-v1.json'
INDEX=prior.INDEX;INVENTORY=prior.INVENTORY
PRIORS=('reports/offered-judgments-v1.json','reports/prince-sentence-v1.json','reports/doctrinal-statutes-v1.json','reports/irrevisable-confession-v1.json')
SOURCES=prior.SOURCES
DOMAIN=(*prior.DOMAIN,'church','creed','subject','issue','part','standard')
SCENES=prior.SCENES;z=prior.z;ns=prior.ns;codeid=prior.codeid
STANDARD='o a[r[p r5cc]][r['+z('standard')+'] r['+z('reference')+']]'
WHOLE='r[b point[w[t[k r5cc['+ns(('standard','reference'))+']][v point]][t[k r5cc['+ns(('other','reference'))+']][v point]]]]'
SAVE=prior.SAVE+'q[k zsavestandard['+STANDARD+']].q[k zsavecreed['+WHOLE+']].'
POINT='i[point d][x[e[v point]['+z('now')+']][e[v point]['+z('later')+']]]'
FRAME=('church','creed','subject','item','issue','part','standard','reference')
COMPARE='k r532['+ns(FRAME)+' '+POINT+']'
J='l[a]['+z('item')+']';I='l[a]['+z('second')+']'
PAIR=J+' '+I
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document)
    for row in d['declarations']:
        if row['name'] in boundaries:
            row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r ztruth[a d d] c.d h26ae[item a reference d] e[b point[k ztruth[v item v reference v point]]].'
    extra+='r h26ag[a d] a.d r5cc[item a reference d] e[k h26ae[k h26ag[v item v reference] v reference]].'
    extra+='r zdocpick[a d i[e] i[e]] i[e].d h246e[form a reference d] i[e][k zdocpick[v form v reference '+WHOLE+' '+STANDARD+']].'
    extra+='r zsavemessage[i[h[a] f]] c.r zsaveitem[i[e]] c.r zsavesecond[i[e]] c.r zsavestandard[i[e]] c.r zsavecreed[i[e]] c.'
    extra+='r zcases[a d] c.'
    provider=parse('p:'+extra);replaced={x['name'] for x in provider['declarations']}
    d['declarations']=provider['declarations']+[x for x in d['declarations'] if x['name'] not in replaced]
    helpers=[x['name'] for x in provider['declarations'] if x['name'].startswith('z')]
    d.update(declarations=closure(d,(*roots,'r53m','r53p','r5cc',*helpers)),statements=[])
    return parse(format_graph(d,'compact')+query)

def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

def model(d):
    v,saved=prior.model(d)
    v.update({'z'+n:lambda n=n:n for n in DOMAIN})
    v['znamepick']=lambda p,*cs:cs[DOMAIN.index(p)]
    for n in ('standard','creed'):v['zsave'+n]=lambda c,n=n:saved.update({n:codeid(c)}) is None
    v['zdocpick']=lambda f,r,whole,part:whole if f=='creed' else part
    v['h26ad']=lambda i,r:i in ('item','second','alias','standard','other') and r=='reference'
    v['ztruth']=lambda i,r,t:r=='reference' and (i in ('item','second') or i=='standard' and t!='later')
    v['h246d']=lambda c,r:(c,r)==('church','reference')
    v['h245z']=lambda s,r:(s,r)==('subject','reference')
    v['h246f']=lambda c,s,r:(c,s,r)==('creed','subject','reference')
    v['h246g']=lambda c,f,code,r:(c,f,r)==('church','creed','reference') and codeid(code)==saved['creed']
    v['h246h']=lambda c,code,r:(c,r)==('church','reference') and codeid(code)==(0,dict(kind='function_ref',symbol='hzxi'))
    v['h252f']=lambda c,p,r:(c,p,r)==('creed','part','reference')
    v['hzlh']=lambda p,i,s,r:(p,i,s,r)==('part','issue','standard','reference')
    v['h26o3']=lambda item,i,r:item in ('item','second','standard') and(i,r)==('issue','reference')
    v['h254w']=lambda p,left,right,r:(p,r)==('part','reference') and codeid(left)==codeid(right)==saved['standard']
    v['zcases']=lambda i,t:i in ('item','second') and t in ('now','later')
    return v,saved

@lru_cache(None)
def part_checks():
    d=fixture(('r53x',),SAVE+'q[k r53x['+ns(('creed','part','standard','issue','reference'))+']].');rows={}
    for missing in (None,'h26ad','h26o3','h252f','hzlh','h254w'):
        v,_=model(d);v['ztruth']=unknown
        if missing:v[missing]=lambda *a:False
        got=run(d,v);assert got==[True]*5+[missing is None],(missing,got);rows[missing or 'baseline']=got[-1]
    for n in ('h26ad','h26o3','h252f','hzlh','h254w','zdocpick'):
        v,_=model(d);v[n]=unknown;rejects(d,v)
    for n in ('hzlh','h254w'):
        v,_=model(d);old=v[n];v[n]=lambda p,*a,old=old:old('creed',*a)
        assert run(d,v)==[True]*5+[False]
    return dict(cases=rows,positive_containment_required=True,same_issue_and_same_part_content_required=True,
        neither_creed_truth_nor_personal_truth_evaluated=True,unknown_rejected=True)

@lru_cache(None)
def comparison_checks():
    d=fixture(('r532',),SAVE+'q['+COMPARE+'].');rows={}
    for case in ('baseline','all_agree','empty_cases','outside_only','same_now','wrong_own_issue','wrong_standard_issue','wrong_part_content','no_adoption','wrong_adopted_content','wrong_own_name','wrong_issue_name','false_own_now'):
        v,saved=model(d)
        if case=='all_agree':v['ztruth']=lambda i,r,t:r=='reference' and i in ('item','second','standard')
        if case in ('empty_cases','outside_only'):
            # The direct caller supplies the complete comparison range.
            q=COMPARE.replace(POINT,'i[point d]['+('u[e[v point][v point]]' if case=='empty_cases' else 'e[v point]['+z('reference')+']')+']')
            current=fixture(('r532',),SAVE+'q['+q+'].')
        else:current=d
        if case=='same_now':v['ztruth']=lambda i,r,t:r=='reference' and (i in ('item','second') or i=='standard' and t=='now')
        if case in ('wrong_own_issue','wrong_standard_issue'):
            old=v['h26o3'];bad='item' if case=='wrong_own_issue' else 'standard'
            v['h26o3']=lambda i,s,r,old=old,bad=bad:old(i,s,r) and i!=bad
        if case=='wrong_part_content':v['zdocpick']=lambda f,r,whole,part:whole
        if case=='no_adoption':v['h246g']=lambda *a:False
        if case=='wrong_adopted_content':v['h246g']=lambda c,f,code,r:(c,f,r)==('church','creed','reference') and codeid(code)==saved['standard']
        if case in ('wrong_own_name','wrong_issue_name'):
            old=v['znamepick'];bad='item' if case=='wrong_own_name' else 'issue'
            v['znamepick']=lambda p,*cs,old=old,bad=bad:old('other' if p==bad else p,*cs)
        if case=='false_own_now':v['ztruth']=lambda i,r,t:r=='reference' and (i in ('item','second') and t=='later' or i=='standard' and t=='now')
        expected=case in ('baseline','same_now','false_own_now');got=run(current,v)
        assert got==[True]*5+[expected],(case,got);rows[case]=got[-1]
    for n in ('ztruth','h246g','h26o3','h252f','hzlh','h254w'):
        v,_=model(d);v[n]=unknown;rejects(d,v)
    # Real conjunction of a further doctrine is not compared in place of the part.
    v,_=model(d);v['ztruth']=lambda i,r,t:r=='reference' and i in ('item','second','standard')
    assert run(d,v)==[True]*5+[False]
    v,_=model(d);v['zitem']=lambda:'alias';assert run(d,v)==[True]*6
    return dict(cases=rows,real_same_issue_propositions_compared=True,not_teaching_rule_compliance=True,
        whole_creed_extra_doctrine_not_mistaken_for_difference=True,canonical_alias=True,unknown_rejected=True,
        boundary='All semantic definitions, including adopted church confession and rpb, execute natively; content, names and formulation-code providers are explicit fixture functions.')

@lru_cache(None)
def collection_checks():
    q='q[k r533['+ns(('church','creed','subject'))+' '+PAIR+' '+z('reference')+' p zcases]].'
    d=fixture(('r533',),q,('r532',));domain=('item','second','church','creed','subject','issue','part','standard')
    def small(case):
        v,_=model(d)
        def compare(c,cr,s,item,issue,part,std,ref,cases):
            common=(c,cr,s,issue,part,std,ref)==('church','creed','subject','issue','part','standard','reference')
            scope=tuple(t for t in SCENES if cases(t))==('now','later')
            wanted=('item','second') if case=='both' else ('second',) if case=='second' else () if case=='none' else ('item',)
            return common and scope and item in wanted
        v['r532']=compare
        if case=='outside_item':v['r532']=lambda c,cr,s,i,*a:i=='standard'
        if case=='wrong_case_scope':v['zcases']=lambda i,t:i=='standard'
        return v
    rows={}
    for case in ('first','second','both','none','outside_item','wrong_case_scope'):
        got=run(d,small(case),domain);assert got==[case in ('first','second','both')],(case,got);rows[case]=got[0]
    empty=fixture(('r533',),q.replace(PAIR,'l[a][] l[a][]'),('r532',))
    assert run(empty,small('first'),domain)==[False]
    return dict(cases=rows,some_but_not_every_selected_item_required=True,empty_rejected=True,
        boundary='Only r532 is a typed boundary; collection folds and same-item comparison selector execute natively. r532 has separate complete native comparison tests.')

@lru_cache(None)
def integration_checks():
    prefix=ns(NAMES);q=SAVE+'q[k r534['+prefix+' '+PAIR+' '+z('reference')+' p zcases '+z('now')+']].'
    d=fixture(('r534',),q,('r533',))
    def joined():
        v,_=model(d)
        v['r533']=lambda c,cr,s,j,i,r,cases:(c,cr,s,tuple(j.items),tuple(i.items),r)==('church','creed','subject',('item',),('second',),'reference') and cases('item','later') is True
        return v
    assert run(d,joined())==[True]*6
    for n in ('r533','h26ai','f2','hzu'):
        v=joined();v[n]=lambda *a:False;assert run(d,v)==[True]*5+[False],n
    # The native offered-action tree is preserved exactly; the seven binders
    # are checked separately at a scalar boundary on two individuals.
    bindings='l[a]['+prefix+']';target='k r536[r['+J+'] r['+I+'] r[p zcases]]'
    q='q[t[k r535['+PAIR+' p zcases '+bindings+' '+z('reference')+']]['+z('now')+']].'
    q+='q[t[c[s['+target+']]['+bindings+' '+z('reference')+']]['+z('now')+']].'
    b=fixture(('r535','r536'),q,('r534',))
    def bound():
        v,_=model(b);v.update({'z'+n:lambda n=n:'left' if n in ('person','scholar','church','subject','item') else 'right' for n in DOMAIN})
        v['zcases']=lambda i,t:(i,t)==('left','later')
        v['r534']=lambda p,a,s,u,c,cr,su,j,i,r,cases,t:(p,a,s,u,c,cr,su,tuple(j.items),tuple(i.items),r,t)==('left','right','left','right','left','right','left',('left',),('right',),'reference','now') and cases('left','later') is True and cases('right','later') is False
        return v
    assert run(b,bound(),('left','right'))==[True,True]
    for n in NAMES:
        v=bound();value=v['z'+n]();v['z'+n]=lambda value=value:'right' if value=='left' else 'left'
        assert run(b,v,('left','right'))==[False,False],n
    for wrong in ('l[a][]','l[a]['+ns(NAMES[:-1])+']','l[a]['+ns((*NAMES,'other'))+']'):
        bad=fixture(('r535','r536'),q.replace(bindings,wrong),('r534',))
        assert run(bad,bound(),('left','right'))==[False,False]
    return dict(offered_action_and_same_collection_difference_both_required=True,
        native_and_dequoted_target_equal=True,all_seven_bindings_exact=True,
        boundary='r533 only for integration, r534 only for seven-binder adapter. Native presentation preserved and tested in the prior report; native comparison and collection are tested separately here.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='adopted_confession_divergence_dependency_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[574,889],text=u['text'][574:889]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['同じ君主への照応と聖職者の敬意評価','同じ実行対象への自由と職務義務保持','無制約の他者とnoch mehr','全文の帰属と通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*SOURCES,*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog()
    for source in parents():
        for n,e in c.entries.items():
            if n in source.entries:assert e['declaration']==source.entries[n]['declaration'] and e['meaning_ja']==source.entries[n]['meaning_ja']
    old=parents()[1];assert len(old.document['statements'])==113 and not c.document['statements']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==17
    for row in reviews:assert row['selection']==selection_binding(old,[s['index'] for s in row['selection']['statements']])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        text=format_graph(c.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==c.document
    text=format_graph(c.document,'compact')
    try:parse(text+'q[e[r[p r535]][r[p r535]]].')
    except ValueError as e:assert 'Quoted evaluation' in str(e)
    else:raise AssertionError('Rank zero quotation accepted')
    parse(text+'q[e[r b[p r535]][r b[p r535]]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),main_statements_preserved=113,
        whole_unit_reviews_preserved=17,new_verified_characters=0,rank_one_target_required=True,roundtrips=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in (('part',part_checks),('comparison',comparison_checks),('collection',collection_checks),('integration',integration_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,*SOURCES,
        'scripts/compose_confessional_divergence.py','scripts/check_confessional_divergence.py','tests/test_confessional_divergence.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_offered_judgments.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='same_issue_adopted_confession_and_offered_divergence_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
