"""Native tests of conscience classification, reasoning and every scoped choice."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_conscience_choice import ROOT,LIBRARY,BASIS,GOAL,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/conscience-choice-v1.md';READING='data/conscience-choice-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';INDEX='data/semantic-review-index-v196.json'
PRIORS=('reports/religious-freedom-policy-v1.json','reports/world-posterity-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v1.json','artifacts/conscience-choice-v1/dwb-gewissenssache.html',
    'artifacts/conscience-choice-v1/dwb-gewissensfreiheit.html')
DOMAIN=('actor','one','two','child','community','group','mone','mtwo','mthree','jone','jother','jtwo','jthree',
    'cone','ctwo','cthree','roleone','roletwo','rolechild','faculty','borrowed','reason','activity','other')
SCENES=('reference','case','now','later')
MATTERS={('one','mone','cone'),('one','mtwo','ctwo'),('two','mthree','cthree')}
CANDIDATES={('one','mone','jone'),('one','mone','jother'),('one','mtwo','jtwo'),('two','mthree','jthree')}
ROLES={'one':'roleone','two':'roletwo','child':'rolechild'}
def z(n):return 'k z'+n+'[]'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def identity(c):return c.rank,json.loads(c.syntax)
CODE='k r5zh['+' '.join('r['+z(n)+']' for n in ('actor','community','reference'))+']'
ONE=' '.join(z(n) for n in ('actor','one','community','mone','jone','reference','now'))
GROUP='q[t[k r5zg['+' '.join(z(n) for n in ('actor','group','community','reference'))+']]['+z('now')+']].'
PERSON='q[t[c[k r5zf['+' '.join(z(n) for n in ('actor','community','reference'))+']]['+z('one')+']]['+z('now')+']].'
DEQUOTED='q[t[c[s['+CODE+']]['+z('one')+']]['+z('now')+']].'
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:
            x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    prefix=parse('p:'+extra);replacements={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h')}
    additions=[x for x in prefix['declarations'] if x['name'] not in replacements]
    d['declarations']=additions+[replacements.get(x['name'],x) for x in d['declarations']]
    d.update(declarations=closure(d,(*roots,*(x['name'] for x in additions))),statements=[])
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def base(d):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(znamepick=lambda a,*cs:cs[DOMAIN.index(a)],zrefpick=lambda p,*cs:cs[SCENES.index(p)],
        aa=lambda a:a in ROLES,h26nw=lambda p,m,r,c:r=='reference' and c=='case',
        fa=lambda p,j,c:c=='case' and any((p,j)==(a,k) for a,m,k in MATTERS),
        fb=lambda j,m,c:c=='case' and any((j,m)==(k,b) for a,b,k in MATTERS),
        se=lambda j,p,c:c=='case' and any((j,p)==(k,a) for a,b,k in MATTERS),
        h26nx=lambda p,m,j,r:r=='reference' and (p,m,j) in CANDIDATES,
        h26ny=lambda p,c,r:ROLES.get(p,'other') if (c,r)==('community','reference') else 'other',
        h246c=lambda g,p,r:(g,r)==('group','reference') and p in ROLES,
        h26nz=lambda a,p,c,m,j,r,t:(a,c,r,t)==('actor','community','reference','now') and (p,m,j) in CANDIDATES,
        h237z=lambda *a:False,h26ho=lambda *a:False,dg=lambda *a:False,df=lambda *a:False,
        r5y3=lambda p,m,r:r=='reference' and any((p,m)==(a,b) for a,b,k in MATTERS))
    def permits(a,p,role,code,bindings,r,pol,t):
        return (a,r,t)==('actor','reference','now') and role==ROLES.get(p) and identity(code)==(1,dict(kind='function_ref',symbol='r5y6')) and bindings.items in tuple((p,m,j) for x,m,j in CANDIDATES if x==p)
    v['h245c']=permits
    return v

@lru_cache(None)
def classification_checks():
    q=''.join('q[k r5y3['+z(p)+' '+z(m)+' '+z('reference')+']].' for p,m in (('one','mone'),('one','mtwo'),('two','mthree'),('two','mone'),('child','mone')))
    d=fixture(('r5y3',),q);v=base(d);assert run(d,v)==[True,True,True,False,False]
    rows={}
    for n in ('aa','fa','fb','se','h26nw'):
        v=base(d);v[n]=lambda *a:False;got=run(d,v);assert got==[False]*5;rows[n]=got
        v=base(d);v[n]=unknown;rejects(d,v)
    # Wrong fixed reference or classification point cannot supply another case's witness.
    for n in ('reference','case'):
        v=base(d)
        if n=='reference':v['zreference']=lambda:'later'
        else:v['h26nw']=lambda p,m,r,c:r=='reference' and c=='now'
        assert run(d,v)==[False]*5
    return dict(native_classification=True,three_person_specific_matters=True,no_actual_current_self_judgment=True,
        missing_components=rows,wrong_person_matter_reference_case_rejected=True,unknown_rejected=True)

def actual(d):
    v=base(d);oldfa,oldfb=v['fa'],v['fb']
    v.update(fa=lambda p,j,c:oldfa(p,j,c) or (p,j,c)==('one','jone','now'),
        fb=lambda j,m,c:oldfb(j,m,c) or (j,m,c)==('jone','mone','now'),
        ab=lambda f,p,c:(f,p,c)==('faculty','one','now'),
        ac=lambda p,f,j,c:(p,f,j,c)==('one','faculty','jone','now'),
        fc=lambda j,r,c:(j,r,c)==('jone','reason','now'),ad=lambda *a:False)
    return v
@lru_cache(None)
def reasoning_checks():
    q='q[t[k r5y4['+' '.join(z(n) for n in ('one','mone','jone'))+']]['+z('now')+']].'
    d=fixture(('r5y4',),q);rows={}
    for case in ('baseline','borrowed_faculty','other_judgment_use','other_matter','other_reason','no_judgment','directed_now','past_instruction','other_judgment_instruction'):
        v=actual(d)
        if case=='borrowed_faculty':v['ab']=lambda f,p,c:(f,p,c)==('borrowed','one','now')
        if case=='other_judgment_use':v['ac']=lambda p,f,j,c:(p,f,j,c)==('one','faculty','jother','now')
        if case=='other_matter':v['fb']=lambda j,m,c:c=='case' and any((j,m)==(k,b) for a,b,k in MATTERS)
        if case=='other_reason':v['fc']=lambda j,r,c:(j,r,c)==('jother','reason','now')
        if case=='no_judgment':v['fa']=base(d)['fa']
        if case=='directed_now':v['ad']=lambda a,p,j,c:(a,p,j,c)==('other','one','jone','now')
        if case=='past_instruction':v['ad']=lambda a,p,j,c:(a,p,j,c)==('other','one','jone','case')
        if case=='other_judgment_instruction':v['ad']=lambda a,p,j,c:(a,p,j,c)==('other','one','jother','now')
        got=run(d,v);expected=case in ('baseline','past_instruction','other_judgment_instruction');assert got==[expected],(case,got);rows[case]=got
    assert 'fd' not in {x['name'] for x in d['declarations']}
    for n in ('ab','ac','fc','ad'):
        v=actual(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,support_and_correctness_not_required=True,same_person_faculty_judgment_matter=True,
        unknown_rejected=True)

@lru_cache(None)
def binding_checks():
    names=('one','community','mone','jone','roleone');domain=(*names,'other')
    rows={}
    for case in ('baseline','missing','extra','person','community','matter','judgment','role'):
        items=list(names)
        if case=='missing':items.pop()
        if case=='extra':items.append('other')
        if case in ('person','community','matter','judgment','role'):items[('person','community','matter','judgment','role').index(case)]='other'
        q='q[t[k r5y7[l[a]['+' '.join(z(n) for n in items)+'] '+z('reference')+']]['+z('now')+']].'
        d=fixture(('r5y7',),q,('r5y4','r5y5'));v=base(d)
        v['r5y5']=lambda p,m,j,r:(p,m,j,r)==('one','mone','jone','reference')
        v['r5y4']=lambda p,m,j:Content(SCENES,tuple((p,m,j,t)==('one','mone','jone','now') for t in SCENES))
        got=run(d,v,domain);assert got==[case=='baseline'],(case,got);rows[case]=got[0]
    return dict(cases=rows,exact_length_order_roles_and_conduct=True,
        boundary='Only the separately evaluated r5y4 conduct and r5y5 scope are scalar/content truth boundaries in this small sequence-binding fixture; both sequence adapters execute natively.')

@lru_cache(None)
def choice_checks():
    d=fixture(('r5zd',),'q[k r5zd['+ONE+']].',('r5y3',));rows=[]
    for positive,negative,allow,abstain,intervene in product((False,True),repeat=5):
        v=base(d);permit=v['h245c']
        v.update(h237z=lambda a,p,role,c,b,r,pol,t:(positive if pol else negative) and (a,p,t)==('actor','one','now'),
            h245c=lambda a,p,role,c,b,r,pol,t:permit(a,p,role,c,b,r,pol,t) and (allow if pol else abstain),
            dg=lambda a,t:intervene and (a,t)==('activity','now'),df=lambda a,x,t:(a,x,t)==('actor','activity','now'),
            h26ho=lambda a,p,c,b,r,t:(a,p,identity(c),b.items,r,t)==('activity','one',(1,dict(kind='function_ref',symbol='r5y7')),
                ('one','community','mone','jone','roleone'),'reference','now'))
        got=run(d,v);assert got==[not positive and not negative and allow and abstain and not intervene]
        rows.append(dict(require=positive,forbid=negative,allow=allow,abstain=abstain,intervene=intervene,result=got[0]))
    for occurred,participated,intervened in product((False,True),repeat=3):
        v=base(d);v.update(dg=lambda a,t:occurred and (a,t)==('activity','now'),
            df=lambda a,x,t:participated and (a,x,t)==('actor','activity','now'),h26ho=lambda a,p,c,b,r,t:intervened and (a,p,t)==('activity','one','now'))
        assert run(d,v)==[not (occurred and participated and intervened)]
    # Every normative binding is checked independently, including polarity and exact code.
    for pos in range(8):
        v=base(d);old=v['h245c']
        def changed(*args):
            if pos in (3,4):return False
            b=list(args);b[pos]=False if pos==6 else 'other'
            if pos==6:return old(*b) and not args[pos] # positive permission missing
            return old(*b)
        v['h245c']=changed;assert run(d,v)==[False],pos
    for n in ('h237z','h245c','h26ho','dg','df','h26ny'):
        v=base(d);v[n]=unknown;rejects(d,v)
    return dict(thirty_two_norm_and_interference_cases=rows,all_three_intervention_parts_required=True,
        all_eight_norm_arguments_checked=True,unknown_rejected=True,
        boundary='The separately tested classification r5y3 is a scalar truth boundary; candidates, permissions and same-event intervention execute natively.')

@lru_cache(None)
def native_policy_checks():
    domain=('actor','one','community','group','mone','jone','cone','roleone','other')
    d=fixture(('r5zf','r5zg','r5zh'),PERSON+DEQUOTED+GROUP);v=base(d)
    v['h246c']=lambda g,p,r:(g,p,r)==('group','one','reference')
    assert run(d,v,domain)==[True]*3
    for n in ('ab','ac','fc','ad'):assert v[n] is unknown
    v['h26nz']=lambda *a:False;assert run(d,v,domain)==[False]*3
    return dict(complete_native_classification_choice_and_group=True,direct_and_dequoted_state_match=True,
        missing_assessment_rejected=True,actual_reasoning_not_executed=True)

@lru_cache(None)
def universal_checks():
    d=fixture(('r5zf','r5zg','r5zh'),PERSON+DEQUOTED+GROUP,('r5y3','r5zd'))
    def model():
        v=base(d)
        v['r5zd']=lambda a,p,c,m,j,r,t:(a,c,r,t)==('actor','community','reference','now') and (p,m,j) in CANDIDATES
        return v
    v=model();assert run(d,v)==[True]*3
    rows={}
    for person,matter,judgment in sorted(CANDIDATES):
        for absent in ('permission','assessment'):
            v=model()
            if absent=='permission':
                old=v['r5zd'];v['r5zd']=lambda a,p,c,m,j,r,t:old(a,p,c,m,j,r,t) and (p,m,j)!=(person,matter,judgment)
            else:
                old=v['h26nz'];v['h26nz']=lambda a,p,c,m,j,r,t:old(a,p,c,m,j,r,t) and (p,m,j)!=(person,matter,judgment)
            got=run(d,v);assert got==[person!='one']*2+[False];rows['/'.join((person,matter,judgment,absent))]=got
    v=model();old=v['h26nx'];v['h26nx']=lambda p,m,j,r:old(p,m,j,r) and m!='mtwo';assert run(d,v)==[False]*3
    v=model();v['h246c']=lambda *a:False;assert run(d,v)==[True,True,False]
    v=model();old=v['h246c'];v['h246c']=lambda g,p,r:old(g,p,r) or (g,p,r)==('group','other','reference');assert run(d,v)==[True,True,False]
    for n in ('h26nx','h26nz','r5y3','r5zd'):
        v=model();v[n]=unknown;rejects(d,v)
    names='q[k r5zi['+' '.join(z(n) for n in ('actor','community','reference'))+']].'
    nd=fixture(('r5zi',),names);assert run(nd,base(nd))==[True]
    for n in ('actor','community','reference'):
        v=base(nd)
        if n=='reference':v['zrefpick']=lambda p,*cs:cs[SCENES.index('later' if p==n else p)]
        else:v['znamepick']=lambda a,*cs:cs[DOMAIN.index('other' if a==n else a)]
        assert run(nd,v)==[False]
    return dict(all_four_candidate_omissions=rows,second_matter_and_second_person_required=True,
        nonempty_candidates_for_each_relevant_matter=True,no_conscience_matter_person_kept_in_population=True,
        empty_or_nonhuman_group_rejected=True,direct_and_dequoted_person_freedom_match=True,
        actual_reasoning_not_executed=True,three_names_checked=True,unknown_rejected=True,
        boundary='Separately evaluated classification r5y3 and single-choice freedom r5zd are scalar truth boundaries. All people, all matters, all judgment candidates and assessment execute natively; a smaller complete native model is checked separately.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');start=u['text'].index('und Jedem');end=u['text'].index('zu bedienen.')+len('zu bedienen.')
    return dict(status='each_person_all_conscience_matters_freedom_dependency',
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        interpretation=LIMITS,evidence=[dict(path=SOURCES[1],url='https://www.dwds.de/wb/dwb/gewissenssache',retrieved='2026-10-23',
            observation='casus conscientiaeとの関係、信仰上の事柄を含む諸例を参照する。宗教にだけ範囲を限定する根拠とはしない。'),
            dict(path=SOURCES[2],url='https://www.dwds.de/wb/dwb/gewissensfreiheit',retrieved='2026-10-23',
            observation='内面の無自責とは異なる、上位の権威に対する良心主体の外的な関係という区別を補助にする。後代の全法理・歴史を1784年の主張へ足さない。')],
        unresolved=['政府側の最初の解放と同じ出来事・受益者への束縛、全人間範囲と政府側の本文設定',
            '功績・恩恵と双方の称揚適合基準への接続、著者帰属・sondern・一文全体と後続'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,*SOURCES)})
@lru_cache(None)
def structure_checks():
    c=catalog()
    for p in parents():
        for n,e in c.entries.items():
            if n in p.entries:assert e['declaration']==p.entries[n]['declaration'] and e['meaning_ja']==p.entries[n]['meaning_ja']
    assert not c.document['statements'] and len(parents()[1].document['statements'])==112
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    assert c.entries['r5zh']['declaration']['result'].get('rank',0)==0
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=112,
        new_verified_characters=0,compact_full_v2_roundtrips=True,parent_meanings_preserved=True,beneficiary_state_quote_rank_zero=True)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('classification',classification_checks),('reasoning',reasoning_checks),('bindings',binding_checks),('choice',choice_checks),('native_policy',native_policy_checks),('universal',universal_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,*SOURCES,*PRIORS,
        'scripts/compose_conscience_choice.py','scripts/check_conscience_choice.py','tests/test_conscience_choice.py',
        'scripts/compose_protected_remarks.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='all_person_specific_conscience_choices_and_noninterference_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
