"""Check institutional sources, universal candidates and the shared policy quote."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_shared_liberty_policy import ROOT,LIBRARY,BASIS,CONTENT,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_all_offered_freedoms import bounded_lists

DOC='docs/shared-liberty-policy-v1.md';READING='data/shared-liberty-policy-reading-v1.json'
INDEX='data/semantic-review-index-v198.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/freedom-ethos-v1.json','reports/government-release-v1.json','reports/all-offered-freedoms-v1.json','reports/clerical-duty-scope-v1.json')
DOMAIN=('a','b');SCENES=('reference','now','later')
CODE='i b[h[j[a] d] e]'
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def codeid(c):return c.rank,json.loads(c.syntax)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,boundaries=(),limited=False,extra=''):
    d=deepcopy(catalog().document)
    for row in d['declarations']:
        if row['name'] in boundaries:
            assert row['result']=='truth'
            row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
        elif limited and row['name'] in ('r56d','r56f'):bounded_lists(row)
    constants=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    constants+='r zone[] a.r ztwo[] a.r znamepick[a i[a] i[a]] i[a].r zrefpick[d i[d] i[d] i[d]] i[d].'
    constants+='d h223g[item a] i[a][k znamepick[v item r['+z('a')+'] r['+z('b')+']]].'
    constants+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    constants+='r zsave['+CONTENT+'] c.r zsavetarget['+CODE+'] c.r zcompare[a d] c.'
    prefix=parse('p:'+constants+extra);ns={r['name'] for r in prefix['declarations']}
    d['declarations']=prefix['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d.update(declarations=closure(d,(*roots,*ns)),statements=[])
    return parse(format_graph(d,'compact')+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v,message='Unknown'):
    try:run(d,v)
    except ValueError as e:assert message in str(e),str(e)
    else:raise AssertionError('Unsupported or unknown accepted')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(zone=lambda:'a',ztwo=lambda:'b',znamepick=lambda p,*cs:cs[DOMAIN.index(p)],zrefpick=lambda p,*cs:cs[SCENES.index(p)],
        zsave=lambda c:saved.update(content=codeid(c)) is None,zsavetarget=lambda c:saved.update(target=codeid(c)) is None,
        aa=lambda p:p=='b')
    return v,saved

@lru_cache(None)
def government_checks():
    choice=args(('a','b','a','a','a','reference'))
    q='q[k r556['+choice+' '+args(('a','now'))+']].q[k r557['+choice+' '+z('now')+']].'
    d=fixture(('r556','r557'),q,('r5vw',));out={}
    for case in ('institutional_intervention','no_intervention','private_activity','other_government','wrong_person','wrong_target','no_permission','prohibited'):
        v,_=model(d)
        v['r5vw']=lambda *a:a==('b','a','a','reference')
        v['h26hn']=lambda *a:'b'
        v['dg']=lambda a,t:(a,t)==('a','now');v['df']=lambda p,a,t:(p,a,t)==('b','a','now')
        v['h26n2']=lambda p,a,g,t:(p,a,g,t)==('b','a','a','now')
        v['h26ho']=lambda a,p,c,b,r,t:(a,p,tuple(b.items),r,t)==('a','b',('b','a','a','a','b'),'reference','now') and codeid(c)==(1,{'kind':'function_ref','symbol':'r5vy'})
        v['h245c']=lambda s,p,role,c,b,r,sign,t:(s,p,role,tuple(b.items),r,sign,t)==('a','b','b',('b','a','a'),'reference',sign,'now') and codeid(c)==(1,{'kind':'function_ref','symbol':'r5vx'})
        v['h237z']=lambda *a:False
        if case in ('no_intervention','no_permission','prohibited'):v['h26ho']=lambda *a:False
        if case=='private_activity':v['h26n2']=lambda *a:False
        if case=='other_government':v['h26n2']=lambda p,a,g,t:g=='b'
        if case=='wrong_person':v['h26ho']=lambda a,p,*rest:p=='a'
        if case=='wrong_target':v['h26ho']=lambda a,p,c,*rest:codeid(c)==(1,{'kind':'function_ref','symbol':'r5vx'})
        if case=='no_permission':v['h245c']=lambda *a:False
        if case=='prohibited':v['h237z']=lambda *a:True
        got=run(d,v);assert got==[case=='institutional_intervention',case not in ('institutional_intervention','no_permission','prohibited')],(case,got);out[case]=got
    v,_=model(d);v.update(r5vw=lambda *a:True,h26hn=lambda *a:'b',dg=lambda *a:True,df=lambda *a:True,h26n2=lambda *a:True,h26ho=unknown,h245c=lambda *a:True,h237z=lambda *a:False);rejects(d,v)
    # Government qualification and exact population run natively; a government is not a person.
    scope=fixture(('r56b','r56i'),'q[k r56b['+args(('a','b','a','b','reference','now'))+']].q[k r56i['+args(('a','b','a','b','a','reference'))+']].')
    v,_=model(scope);v.update(h237n=lambda *a:a[0]=='a',h256s=lambda *a:a[0]=='a',h256p=lambda o,g,t:(o,g)==('b','a'),
        h246c=lambda g,p,r:(g,p,r)==('b','b','reference'),h26hi=lambda p,o,c,t:(p,o,c)==('b','b','a'),h26j7=lambda t,r:(t,r)==('a','reference'))
    assert run(scope,v)==[True,True]
    for n in ('h237n','h256s','h256p','h246c','h26hi','h26j7'):
        changed=dict(v);changed[n]=lambda *a:False;got=run(scope,changed);assert got==([True,False] if n=='h26j7' else [False,False]),(n,got)
    extra=dict(v);extra['h246c']=lambda *a:True;assert run(scope,extra)==[False,False]
    return dict(cases=out,public_human_agent_and_nonhuman_government_separated=True,exact_population_and_qualification=True,
        boundary='Only r5vw is an existing choice-classification boundary. r5zk, r5v2, r5zj, r5ty, scope and native norms execute; quoted religious act content remains unevaluated.')

@lru_cache(None)
def religious_all_checks():
    d=fixture(('r56a',),'q[t[k r56a['+args(('a','b','a','a','reference'))+']]['+z('now')+']].',('r5v5','r5vw','r557'));out={}
    for case in ('all','second_choice_denied','no_evaluation','outside_group','wrong_government'):
        v,_=model(d);v.update(r5v5=lambda *a:a==('a','b','a','a','reference','now'),h246c=lambda g,p,r:p=='b',r5vw=lambda p,u,t,r:p=='b',r557=lambda *a:a[0]=='a' and a[-1]=='now')
        if case=='second_choice_denied':v['r557']=lambda g,p,c,u,t,r,at:u!='b'
        if case=='no_evaluation':v['r5v5']=lambda *a:False
        if case=='outside_group':v['r557']=lambda g,p,*rest:p=='b'
        if case=='wrong_government':v['r557']=lambda g,*rest:g=='b'
        got=run(d,v);assert got==[case in ('all','outside_group')],(case,got);out[case]=got[0]
    return dict(cases=out,native_all_people_and_choices=True,boundary='r5v5 and r5vw preserve prior assessment/candidate evidence; r557 is the checked per-choice boundary above.')

@lru_cache(None)
def clerical_binding_checks():
    ns=('b','a','b','a','b','a','b');j='l[a]['+z('a')+']';i='l[a][]';comp='r[p zcompare]'
    q='q[k r56c['+z('a')+' '+args(ns)+' '+z('b')+' '+j+' '+i+' '+args(('reference','now'))+' '+comp+']].'
    d=fixture(('r56c',),q,('r54n','r54m'));out={}
    for case in ('same','different_source','different_office','different_reference','different_candidate_range','not_same_cleric'):
        v,_=model(d)
        v['r54n']=lambda *a:a==('b','b','b','a','b','b','reference','now')
        v['h26o4']=lambda p,t,b,r,anchor,at:(p,tuple(b.items),r,anchor,at)==('b',ns,'reference','now','later')
        def duty(*a):
            assert a[:7]==ns
            return a[7:11]==('a','b','reference','now') and codeid(a[13])==(0,{'kind':'function_ref','symbol':'zcompare'}) and tuple(t for t in SCENES if a[14](t))==('later',)
        v['r54m']=duty
        if case=='different_source':v['r54m']=lambda *a:a[7]=='b'
        if case=='different_office':v['r54m']=lambda *a:a[8]=='a'
        if case=='different_reference':v['r54m']=lambda *a:a[9]=='later'
        if case=='different_candidate_range':v['h26o4']=lambda *a:False
        if case=='not_same_cleric':v['r54n']=lambda *a:False
        got=run(d,v);assert got==[case=='same'],(case,got);out[case]=got[0]
    return dict(cases=out,explicit_government_source=True,duty_sources_not_restricted=True,
        boundary='r54n/r54m are previously checked boundaries; source, seven bindings, office, reference, constructed list names, comparison and full h26o4 case selector are connected natively.')

@lru_cache(None)
def all_offers_checks():
    ns=('b','a','b','a','b','b');local=args(('a',*ns,'reference','now'))+' r[p zcompare]'
    query='q[k zsavetarget[k r53w[k r543[l[a]['+z('b')+']] k r543[l[a][]]]]].'
    query+='q[k r56d['+local+']].q[k r56f['+args(('a','b','b','reference','now'))+']].'
    boundary=('r55a','r55e','r56c')
    full=fixture(('r56d','r56f'),query,boundary)
    v,_=model(full);rejects(full,v,'Cannot finitely quantify the unbounded sequence domain')
    d=fixture(('r56d','r56f'),query,boundary,True);out={}
    for case in ('all','second_clerical_denied','second_public_denied','other_government_only','prohibited','no_candidates'):
        v,saved=model(d)
        def public(p,a,s,au,j,i,r,t):return p=='b' and s=='b' and a=='a' and au=='a' and tuple(j.items) in (('a',),('b',)) and not i.items and (r,t)==('reference','now')
        v['r55e']=public
        v['r55a']=lambda p,a,s,au,ch,cr,su,j,i,r,t,comp:public(p,a,s,au,j,i,r,t)
        v['r56c']=lambda *a:a[0]=='a'
        v['h245c']=lambda src,p,role,c,b,r,sign,t:(src,p,role,r,sign,t)==('a','b','b','reference',True,'now') and tuple(b.items)==('b','a','b','a')
        v['h237z']=lambda *a:False
        if case=='second_clerical_denied':v['r56c']=lambda *a:tuple(a[9].items)!=('b',)
        if case=='second_public_denied':
            v['h245c']=lambda src,p,role,c,b,r,sign,t:codeid(c)!=saved['target']
        if case=='other_government_only':v['h245c']=lambda src,*a:src=='b'
        if case=='prohibited':v['h237z']=lambda *a:True
        if case=='no_candidates':v['r55a']=lambda *a:False;v['r55e']=lambda *a:False
        got=run(d,v);expected=[case not in ('second_clerical_denied','no_candidates'),case not in ('second_public_denied','other_government_only','prohibited','no_candidates')]
        assert got==[True,*expected],(case,got);out[case]=got[1:]
    return dict(full_sequence_domain_rejected=True,diagnostic_cases=out,native_all_activity_audience=True,
        boundary='Only sequence quantifiers use empty/singleton-a/singleton-b diagnostics; r55a/r55e and r56c are separate deep boundaries. The public r37c norm body and target construction execute natively, with no policy-content execution.')

@lru_cache(None)
def scope_quantifier_checks():
    d=fixture(('r56e','r56g'),'q[k r56e['+args(('a','b','a','reference','now'))+']].q[k r56g['+args(('a','b','a','reference','now'))+']].',('r54y','r56d','r55j','r55h','r56f'));out={}
    def base():
        v,_=model(d);v.update(aa=lambda p:True,h26hi=lambda p,o,c,t:(o,c,t)==('b','a','now'),r54y=lambda *a:True,
            r56d=lambda *a:a[0]=='a' and a[7:9]==('reference','now'),r55j=lambda *a:False,r55h=lambda *a:True,
            h247d=lambda p,r:'b' if p=='a' else 'a',r56f=lambda g,p,s,r,t:g=='a' and (r,t)==('reference','now') and s==('b' if p=='a' else 'a'))
        return v
    v=base();seen=[];v['r56d']=lambda *a:seen.append(a[1:7]) is None;assert run(d,v)==[True,True];assert len(set(seen))==64
    for i in range(6):
        v=base();v['r56d']=lambda *a:a[i+1]!='b';assert run(d,v)==[False,True]
    for case in ('second_denied','second_restricted','second_clerical','wrong_government','wrong_name'):
        v=base()
        if case.startswith('second_'):
            v['r56f']=lambda g,p,*rest:p=='a'
            if case=='second_restricted':v['r55h']=lambda p,*a:p=='a'
            if case=='second_clerical':v['r55j']=lambda p,*a:p=='b'
        if case=='wrong_government':v['r56d']=lambda g,*a:g=='b';v['r56f']=lambda g,*a:g=='b'
        if case=='wrong_name':v['znamepick']=lambda p,a,b:b if p=='a' else a
        got=run(d,v);assert got==[case not in ('wrong_government','wrong_name'),case not in ('second_denied','wrong_government')],(case,got);out[case]=got
    return dict(cases=out,native_clerical_combinations=64,all_other_people_quantified=True,
        boundary='Deep clergy classification, all-offer result and person-wide restriction have separate evidence; native six-place and one-person quantifiers preserve roles, exclusion, reference and point.')

@lru_cache(None)
def shared_content_checks():
    policy_extra='r zreligion[a a a a d d] c.d r56a[government a group a community a topic a reference d] e[b point[k zreligion[v government v group v community v topic v reference v point]]].'
    whole=fixture(('r56h',),'q[t[k r56h['+args(('a','b','a','b','a','reference'))+']]['+z('now')+']].',
        ('r56b','r56e','r56g'),extra=policy_extra)
    w,_=model(whole)
    w.update(r56b=lambda *a:a==('a','b','a','b','reference','now'),
        r56e=lambda *a:a==('a','b','a','reference','now'),r56g=lambda *a:a==('a','b','a','reference','now'),
        zreligion=lambda *a:a==('a','b','a','a','reference','now'))
    assert run(whole,w)==[True]
    for name in ('r56b','r56e','r56g','zreligion'):
        changed=dict(w);changed[name]=lambda *a:False;assert run(whole,changed)==[False]
        changed=dict(w);changed[name]=unknown;rejects(whole,changed)
    extra='r zpolicy[a a a a a d d] c.d r56h[government a rulingoffice a community a group a topic a reference d] e[b point[k zpolicy[v government v rulingoffice v community v group v topic v reference v point]]].'
    d=fixture(('r56j','r56l'),'q[t[k r56j['+z('reference')+']]['+z('now')+']].q[k r56l['+z('reference')+']].',('r56i',),extra=extra);out={}
    for case in ('all','second_policy_denied','second_excluded','no_settings','wrong_reference','wrong_point'):
        v,_=model(d);v['r56i']=lambda *a:a[-1]=='reference';v['zpolicy']=lambda *a:a[-2:]==('reference','now')
        if case=='second_policy_denied':v['zpolicy']=lambda g,*a:g=='a'
        if case=='second_excluded':v['zpolicy']=lambda g,*a:g=='a';v['r56i']=lambda g,*a:g=='a'
        if case=='no_settings':v['r56i']=lambda *a:False;v['zpolicy']=lambda *a:False
        if case=='wrong_reference':v['zpolicy']=lambda *a:a[-2]=='later'
        if case=='wrong_point':v['zpolicy']=lambda *a:a[-1]=='later'
        got=run(d,v);assert got==[case in ('all','second_excluded','no_settings'),case!='no_settings'],(case,got);out[case]=got
    q='q[k zsave[k r56k[r['+z('reference')+']]]].q[k r56m['+args(('a','reference','now'))+']].q[t[c[k r56n['+z('reference')+']]['+z('b')+']]['+z('later')+']].'
    attitude=fixture(('r56k','r56m','r56n'),q,('r56i',));v,saved=model(attitude)
    v.update(aa=lambda *a:True,r56i=lambda *a:True,h26pg=lambda p,c,t:codeid(c)==saved['content'])
    assert run(attitude,v)==[True,True,True]
    # No policy realization primitive is supplied; both holders share exactly one code.
    for case in ('empty_scope','wrong_reference_name','wrong_content','unknown'):
        changed=dict(v)
        if case=='empty_scope':changed['r56i']=lambda *a:False
        if case=='wrong_reference_name':changed['zrefpick']=lambda p,*cs:cs[2]
        if case=='wrong_content':changed['h26pg']=lambda p,c,t:False
        if case=='unknown':changed['h26pg']=unknown;rejects(attitude,changed);continue
        assert run(attitude,changed)==[True,False,False]
    return dict(cases=out,whole_policy_four_same_context_conjuncts_checked=True,nonempty_scope_separate_from_policy_truth=True,two_people_two_points_same_content=True,
        policy_truth_remains_unknown_for_support=True,boundary='Five native setting quantifiers execute against separate frame/policy boundaries. The actual common quote r56k and supporting property r56n are constructed without executing r56j.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='shared_government_liberty_policy_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[890,1049],text=u['text'][890:1049]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['本文の先行自由例と共通方針の照応','異なる統治圏での同じ態度の取得・影響・広がり','外的障害と格闘の必要、政府の自己誤解','auch/selbstと全文帰属・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements'];assert len(parents()[1].document['statements'])==114
    for old in parents():
        for n,e in c.entries.items():
            if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact');ranks={}
    active={row['name'] for row in closure(c.document,['r56n'])}
    assert not {'h247b','r5xh','h234f','r53b'}&active
    for name in ('r56h','r56j','r56n'):
        for rank,label in enumerate(('','b','c','d','e')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert ranks['r56j']==2
    return dict(new_definitions=len(MEANINGS),new_primitives=0,unchanged_manuscript_statements=114,
        inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0,
        no_monarchical_qualification_or_unbound_public_norm_source=True)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('government',government_checks),('religious_all',religious_all_checks),('clerical_binding',clerical_binding_checks),('all_offers',all_offers_checks),('scope_quantifiers',scope_quantifier_checks),('shared_content',shared_content_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json',
        'scripts/compose_shared_liberty_policy.py','scripts/check_shared_liberty_policy.py','tests/test_shared_liberty_policy.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_clerical_duty_scope.py','scripts/compose_all_offered_freedoms.py',
        'scripts/check_all_offered_freedoms.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='common_institutional_liberty_and_shared_support_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
