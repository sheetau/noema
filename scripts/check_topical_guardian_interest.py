"""Check directed subject scope, quoted interest and the ninth-paragraph source."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import html,json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_topical_guardian_interest import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/topical-guardian-interest-v1.md';READING='data/topical-guardian-interest-reading-v1.json'
INDEX='data/semantic-review-index-v201.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
SOURCE='data/ninth-paragraph-source-reading-v1.json'
IMAGE='artifacts/eighth-paragraph-source-v1/page-492.jpg';AA='artifacts/eighth-paragraph-source-v1/kant-aa08-041.html'
PRIORS=('reports/monarchical-religion-sentence-v1.json','reports/eighth-paragraph-v1.json')
DOMAIN=('ruler','subject','other','activity','group','arts','sciences','matter','othermatter','community')
SCENES=('reference','now','future')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def codeid(c):return c.rank,json.loads(c.syntax)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def unit():return next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0016')
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(query,boundaries=()):
    d=deepcopy(catalog().document)
    for row in d['declarations']:
        if row['name'] in boundaries:
            row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for n in DOMAIN)+'] i[a].'
    extra+='r zrefpick[d '+' '.join('i[d]' for n in SCENES)+'] i[d].'
    extra+='d h223g[person a] i[a][k znamepick[v person '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zsavearts[i[e]] c.r zsavesciences[i[e]] c.'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']}
    d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    prefix=''.join('q[k zsave'+topic+'[r[c[p r6bk]['+args(('ruler','group',topic,'reference'))+']]]].' for topic in ('arts','sciences'))
    d['statements']=[]
    return parse(format_graph(d,'compact')+prefix+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)[2:]
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted as lack of interest')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    for topic in ('arts','sciences'):v['zsave'+topic]=lambda c,topic=topic:saved.update({topic:codeid(c)}) is None
    v.update(znamepick=lambda p,*cs:cs[DOMAIN.index(p)],zrefpick=lambda p,*cs:cs[SCENES.index(p)],
        aa=lambda p:p in ('ruler','subject','other'),h246c=lambda g,p,r:g=='group' and p in ('subject','other') and r=='reference',
        dg=lambda a,t:(a,t)==('activity','now'),df=lambda p,a,t:(p,a,t)==('ruler','activity','now'),
        ob=lambda a,p,w,t:(a,p,w,t)==('activity','ruler','subject','now'),
        h255i=lambda m,t,r:(m,t,r)==('matter','arts','reference'),
        h26r7=lambda a,p,w,m,r,t:(a,p,w,m,r,t)==('activity','ruler','subject','matter','reference','now'),
        h26r5=lambda t,r:(t,r)==('arts','reference'),h26r6=lambda t,r:(t,r)==('sciences','reference'),h26sa=lambda *a:False)
    return v,saved

@lru_cache(None)
def activity_checks():
    q='q[k r6bj['+args(('ruler','activity','subject','arts','reference','now'))+']].'
    d=fixture(q);v,_=model(d);assert run(d,v)==[True];rows={}
    for case in ('not_human','same_person','not_occurring','not_participating','no_undertaking','different_activity','different_target','different_matter','different_topic','different_reference','different_point'):
        w=dict(v)
        if case=='not_human':w['aa']=lambda p:p!='subject'
        if case=='same_person':w['zsubject']=lambda:'ruler';w['ob']=lambda *a:True;w['h26r7']=lambda *a:True
        if case=='not_occurring':w['dg']=lambda *a:False
        if case=='not_participating':w['df']=lambda *a:False
        if case=='no_undertaking':w['ob']=lambda *a:False
        if case in ('different_activity','different_target','different_matter','different_reference','different_point'):
            i={'different_activity':0,'different_target':2,'different_matter':3,'different_reference':4,'different_point':5}[case]
            expected=['activity','ruler','subject','matter','reference','now'];expected[i]='future' if i>=4 else 'othermatter'
            w['h26r7']=lambda *a,expected=tuple(expected):a==expected
        if case=='different_topic':w['h255i']=lambda m,t,r:(m,t,r)==('matter','sciences','reference')
        got=run(d,w);assert got==[False],(case,got);rows[case]=got[0]
    for n in ('aa','dg','df','ob','h255i','h26r7'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,same_activity_actor_target_matter_and_topic=True,no_legal_guardianship_or_obedience_premise=True,unknown_rejected=True)

@lru_cache(None)
def quotation_checks():
    codes=' '.join('r['+z(n)+']' for n in ('ruler','group','arts','reference'))
    literal='r[c[p r6bk]['+args(('ruler','group','arts','reference'))+']]'
    d=fixture('q[e[k r6bl['+codes+']]['+literal+']].');v,_=model(d)
    for n in ('aa','dg','df','ob','h26r7','h255i','h246c'):v[n]=unknown
    assert run(d,v)==[True]
    for i in range(4):
        ns=['ruler','group','arts','reference'];ns[i]='future' if i==3 else 'other'
        changed='r[c[p r6bk]['+args(ns)+']]'
        p=fixture('q[e[k r6bl['+codes+']]['+changed+']].');w,_=model(p);assert run(p,w)==[False]
    return dict(all_four_closed_arguments_checked=True,quote_matches_independent_literal=True,activity_content_not_executed=True)

@lru_cache(None)
def interest_checks():
    content='t[k r6bk['+args(('ruler','group','arts','reference'))+']]['+z('now')+']'
    absent='k r6bm['+args(('ruler','group','arts','reference','now'))+']'
    d=fixture('q['+content+'].q['+absent+'].');rows=[]
    for occurring,interested in product((False,True),repeat=2):
        v,saved=model(d);v['dg']=lambda a,t:occurring and (a,t)==('activity','now')
        v['h26sa']=lambda p,c,r,t:interested and (p,r,t)==('ruler','reference','now') and codeid(c)==saved['arts']
        got=run(d,v);assert got==[occurring,not interested],got
        rows.append(dict(actual_guardianship=occurring,interest=interested,result=got))
    p=fixture('q['+absent+'].');v,_=model(p)
    for n in ('dg','df','ob','h26r7','h255i'):v[n]=unknown
    assert run(p,v)==[True]
    cases={}
    for case in ('actor_name','group_name','topic_name','reference_name','empty_group','nonhuman_group'):
        w=dict(v)
        if case.endswith('_name') and case!='reference_name':
            item={'actor_name':'ruler','group_name':'group','topic_name':'arts'}[case]
            w['znamepick']=lambda p,*cs,item=item:cs[DOMAIN.index('other' if p==item else p)]
        if case=='reference_name':w['zrefpick']=lambda p,*cs:cs[-1]
        if case=='empty_group':w['h246c']=lambda *a:False
        if case=='nonhuman_group':w['aa']=lambda p:p=='ruler'
        got=run(p,w);assert got==[False],(case,got);cases[case]=got[0]
    for n in ('h26sa','znamepick','zrefpick','h246c'):
        w=dict(v);w[n]=unknown;rejects(p,w)
    # Capture the delivered interest arguments against independent quoted content.
    v,saved=model(p);seen=[]
    def interest(person,code,reference,point):
        seen.append((person,codeid(code),reference,point));return False
    v['h26sa']=interest;assert run(p,v)==[True]
    assert seen==[('ruler',saved['arts'],'reference','now')]
    return dict(truth_table=rows,cases=cases,exact_interest_target_and_reference=True,
        future_activity_can_be_unknown=True,no_execution_equivalence_assumed=True,unknown_interest_rejected=True)

@lru_cache(None)
def dual_domain_checks():
    q='q[k r6bn['+args(('ruler','group','arts','sciences','reference','now'))+']].'
    d=fixture(q);rows=[]
    for arts,sciences in product((False,True),repeat=2):
        v,saved=model(d)
        v['h26sa']=lambda p,c,r,t:(p,r,t)==('ruler','reference','now') and (arts and codeid(c)==saved['arts'] or sciences and codeid(c)==saved['sciences'])
        got=run(d,v);assert got==[not arts and not sciences];rows.append(dict(arts_interest=arts,sciences_interest=sciences,value=got[0]))
    v,saved=model(d);v['h26sa']=lambda p,c,r,t:codeid(c) not in (saved['arts'],saved['sciences']);assert run(d,v)==[True]
    for n in ('h26r5','h26r6'):
        w=dict(v);w[n]=lambda *a:False;assert run(d,w)==[False]
        w[n]=unknown;rejects(d,w)
    return dict(two_domain_truth_table=rows,interest_in_other_content_not_excluded=True,both_domain_classifications_required=True)

@lru_cache(None)
def subject_checks():
    q='q[k r6bp['+args(('ruler','community','group','arts','sciences','reference','now'))+']].'
    d=fixture(q,('r2uj','r5ni'));v,saved=model(d);seen=[]
    v['r2uj']=lambda *a:a==('ruler','community','reference')
    def subject(ruler,target,community,reference):
        seen.append((ruler,target,community,reference))
        return ruler=='ruler' and target in ('subject','other') and community=='community' and reference=='reference'
    v['r5ni']=subject;assert run(d,v)==[True]
    assert set(seen)=={('ruler',p,'community','reference') for p in DOMAIN}
    cases={}
    for case in ('missing_subject','extra_subject','other_ruler','other_community','other_reference','not_ruler','arts_interest','sciences_interest'):
        w=dict(v)
        if case=='missing_subject':w['h246c']=lambda g,p,r:(g,p,r)==('group','subject','reference')
        if case=='extra_subject':w['h246c']=lambda g,p,r:g=='group' and p in ('subject','other','ruler') and r=='reference'
        if case in ('other_ruler','other_community','other_reference'):
            i={'other_ruler':0,'other_community':2,'other_reference':3}[case]
            w['r5ni']=lambda *a,i=i:subject(*(a[:i]+('future' if i==3 else 'othermatter',)+a[i+1:]))
        if case=='not_ruler':w['r2uj']=lambda *a:False
        if case in ('arts_interest','sciences_interest'):
            topic=case.removesuffix('_interest');w['h26sa']=lambda p,c,r,t,topic=topic:codeid(c)==saved[topic]
        got=run(d,w);assert got==[False],(case,got);cases[case]=got[0]
    for n in ('r5ni','r2uj'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=cases,all_subjects_exactly_matched=True,same_ruler_community_and_fixed_reference=True,unknown_rejected=True,
        boundary='r2uj/r5ni are existing monarchical-role boundaries with prior evidence. Complete membership equality, nonempty human group, both topical contents, closed references and interest absence execute natively.')

def source_record():
    u=unit();text=html.unescape((ROOT/AA).read_text(encoding='utf-8'))
    assert 'Ich habe den Hauptpunkt der Aufklärung, d. i. des Ausganges der' in text
    assert u['text'].startswith('Ich habe den Hauptpunkt der Aufklärung, die des Ausganges der')
    return dict(status='ninth_paragraph_first_sentence_visual_collation',source_unit=u['id'],unit_sha256=u['text_sha256'],
        first_sentence=dict(range=[0,389],text=u['text'][:389],nonblank_characters=336),
        facsimile=dict(path=IMAGE,page=492,visual_reading='die des Ausganges',
            observation='492頁の第九段落冒頭を拡大して再読すると、Aufklärungの後の語はdieと読める。固定転記のdieを保存する。分綴を除いて第一文末のistまで対応する。'),
        alternate_edition=dict(path=AA,location='AA VIII 41, lines 10–15',reading='d. i. des Ausganges'),
        adopted_interpretation='離脱の句を啓蒙の説明として接続する。AAのd. i.はこの説明の読みを明示するが、固定原文の文字を書き換えない。原刊の誤植かAAの編集かといった成立事情は断定しない。',
        limits=['これは原文照合と読解の選択の記録であり、全文の意味一致判断ではない。','第二文の493頁への続きはこの局所照合の対象外。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,IMAGE,AA)})
def reading_record():
    u=unit()
    return dict(status='topical_guardian_interest_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[155,287],text=u['text'][155:287]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['主眼を宗教に置いた著者の回顧と啓蒙の説明','unsere Beherrscherの同じ全対象への量化と本文参照','有害さと不名誉の二つの最上級・追加理由','weil/überdem/so wie/also auchと全文帰属・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,SOURCE,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert not c.document['statements'] and len(old.document['statements'])==117
    for n,e in c.entries.items():
        if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    assert read(SOURCE)==source_record() and read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for name in MEANINGS:
        for rank,label in enumerate(('','b','c')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert ranks=={n:int(n in ('r6bm','r6bn','r6bp')) for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_preserved=True,
        roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0,source_variant_recorded_without_editing_inventory=True)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,encoded(source_record()))
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('activity',activity_checks),('quotation',quotation_checks),('interest',interest_checks),('domains',dual_domain_checks),('subjects',subject_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,SOURCE,*PRIORS,IMAGE,AA,
        'scripts/compose_topical_guardian_interest.py','scripts/check_topical_guardian_interest.py','tests/test_topical_guardian_interest.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='topical_guardianship_and_interest_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
