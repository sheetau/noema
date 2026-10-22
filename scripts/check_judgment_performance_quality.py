"""Check actual task conditions and stable own-understanding performances."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_judgment_performance_quality import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts import check_qualified_judgment as prior

DOC='docs/judgment-performance-quality-v1.md'
READING='data/judgment-performance-quality-reading-v1.json'
REPORT='reports/judgment-performance-quality-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/present-epoch-assessment-v1.json','reports/qualified-judgment-v1.json','reports/judgment-standards-v1.json','reports/cognitive-acquisition-v1.json','reports/sixth-paragraph-v1.json')
EVIDENCE=('adelung-sicher.html','adelung-wohl.html','kant-aa08-040.html','kant-aa04-331.html')
SOURCES=tuple('artifacts/judgment-performance-quality-v1/'+p for p in EVIDENCE)+('artifacts/royal-writing-oversight-v1/page-491.jpg',)
DOMAIN=('person','matter','judgment','counterpart','faculty','reason','ground','support','weakreason')
SCENES=('reference','actual','normal')
EXTRA=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
ARGS='k zperson[] k zmatter[] k zjudgment[] k zreference[] k zactual[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,concrete=False,extra=EXTRA):
    d=deepcopy(catalog().document)
    if concrete:
        # Move the two native example requirements ahead of the content adapter.
        examples=[x for x in d['declarations'] if x['name'] in ('r5s4','r5s5')]
        ds=[]
        for x in d['declarations']:
            if x['name'] in ('r5s4','r5s5'):continue
            if x['name']=='h26j4':
                ds.extend(examples)
                text='r zground[] a.r zsupport[] a.d h26j4[criterion a person a matter a judgment a reference d] e[b point[w[x[e[v criterion][k zground[]]][k r5s4[v person v matter v judgment v reference v point]]][x[e[v criterion][k zsupport[]]][k r5s5[v person v matter v judgment v reference v point]]]]].'
                ds.extend(parse(format_graph(dict(d,declarations=ds,statements=[]),'compact')+text)['declarations'][len(ds):])
            else:ds.append(x)
        d['declarations']=ds
        extra=extra.replace('r zground[] a.','').replace('r zsupport[] a.','')
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+extra+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown input accepted')
def model(d,actual=True,normal=True):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    def act(j,s):return (j,s) in (('judgment','actual'),('counterpart','normal'))
    v.update(aa=lambda p:p=='person',ab=lambda f,p,s:(f,p)==('faculty','person'),
        ac=lambda p,f,j,s:(p,f)==('person','faculty') and act(j,s),
        fa=lambda p,j,s:p=='person' and act(j,s),fb=lambda j,m,s:m=='matter' and act(j,s),
        fc=lambda j,r,s:r=='reason' and act(j,s),fd=lambda r,j,s:r=='reason' and act(j,s),ad=lambda *a:False,
        h26aj=lambda r,j,c,s:r=='reason' and c=='reference' and act(j,s),
        h26j3=lambda c,p,m,r:c in ('ground','support') and (p,m,r)==('person','matter','reference'),
        h26j4=lambda c,p,m,j,r:Content(SCENES,tuple(c in ('ground','support') and (p,m,r)==('person','matter','reference') and act(j,s) and (actual if s=='actual' else normal) for s in SCENES)),
        h26j5=lambda p,m,j,r,s,t:(p,m,j,r,s)==('person','matter','judgment','reference','actual') and t in ('actual','normal'),
        h26j6=lambda p,m,j,r,s,t:'counterpart' if t=='normal' else j)
    return v

@lru_cache(None)
def performance_checks():
    d=fixture(('r5ss','r5sv'),''.join('q[k '+n+'['+ARGS+']].' for n in ('r5ss','r5sv')))
    rows={}
    for actual,normal in product((False,True),repeat=2):
        result=run(d,model(d,actual,normal));assert result==[actual,actual and normal];rows[str((actual,normal))]=result
    cases={}
    for variant in ('empty_conditions','one_failed_condition','empty_comparison','missing_actual','wrong_actual_counterpart','wrong_person','wrong_matter','wrong_reference','missing_counterpart','guided_counterpart','unsupported_counterpart','unowned_faculty'):
        v=model(d);want=[True,False]
        if variant=='empty_conditions':v['h26j3']=lambda *a:False;want=[False,False]
        if variant=='one_failed_condition':
            old=v['h26j4'];v['h26j4']=lambda c,*a:Content(SCENES,(False,)*3) if c=='support' else old(c,*a);want=[False,False]
        if variant=='empty_comparison':v['h26j5']=lambda *a:False
        if variant=='missing_actual':v['h26j5']=lambda *a:a[-1]=='normal'
        if variant=='wrong_actual_counterpart':v['h26j6']=lambda *a:'counterpart'
        if variant in ('wrong_person','wrong_matter','wrong_reference'):
            v[{'wrong_person':'zperson','wrong_matter':'zmatter','wrong_reference':'zreference'}[variant]]=lambda:'reason' if variant!='wrong_reference' else 'normal';want=[False,False]
        if variant=='missing_counterpart':v['fa']=lambda p,j,s:(p,j,s)==('person','judgment','actual')
        if variant=='guided_counterpart':v['ad']=lambda o,p,j,s:(o,p,j,s)==('faculty','person','counterpart','normal')
        if variant=='unsupported_counterpart':v['fd']=lambda r,j,s:(r,j,s)==('reason','judgment','actual')
        if variant=='unowned_faculty':v['ab']=lambda *a:False
        result=run(d,v);assert result==want,(variant,result);cases[variant]=result
    for n in ('h26j3','h26j4','h26j5','h26j6','fa','fb','ab','ac','fc','fd','ad'):
        v=model(d);v[n]=unknown;rejects(d,v)
    return dict(actual_and_normal_combinations=rows,counterexamples=cases,unknown_rejected=True,native_own_understanding_executed=True)

@lru_cache(None)
def concrete_checks():
    d=fixture(('r5ss','r5sv'),''.join('q[k '+n+'['+ARGS+']].' for n in ('r5ss','r5sv')),True)
    rows={}
    for variant,want in (('baseline',[True,True]),('insufficient_ground',[False,False]),('unsupported_used_reason',[False,False]),('normal_insufficient',[True,False])):
        v=model(d)
        if variant=='insufficient_ground':v['h26aj']=lambda *a:False
        if variant=='normal_insufficient':v['h26aj']=lambda r,j,c,s:(r,j,c,s)==('reason','judgment','reference','actual')
        if variant=='unsupported_used_reason':
            old=v['fc'];v['fc']=lambda j,r,s:old(j,r,s) or (j,r,s)==('judgment','weakreason','actual')
        result=run(d,v);assert result==want,(variant,result);rows[variant]=result
    v=model(d);v['h26aj']=unknown;rejects(d,v)
    return dict(cases=rows,content_adapter_is_native_noema_definition=True,sufficient_ground_and_all_used_reasons_executed=True,examples_not_exhaustive_task_standards=True)

def quality_task(code):
    n=json.loads(code.syntax)
    if n.get('kind')!='apply' or n.get('function')!={'kind':'function_ref','symbol':'hzvp'}:return None
    a=n.get('arguments',[])
    if len(a)!=4 or a[1:]!=[{'kind':'call','symbol':'zqualitycontext','arguments':[]},{'kind':'function_ref','symbol':'r5sv'},{'kind':'function_ref','symbol':'r5ss'}]:return None
    return {'zone':'one','ztwo':'two'}.get(a[0].get('symbol'))

@lru_cache(None)
def construction_checks():
    extra='r zone[] a.r zqualitycontext[] d.r zinspect[i[h[a] e]] c.'
    d=fixture(('r5sx',),'q[k zinspect[k r5sx[r[k zone[]] r[k zqualitycontext[]]]]].',extra=extra)
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'};v['zinspect']=lambda c:c.rank==0 and quality_task(c)=='one'
    assert run(d,v)==[True]
    code='k r5sx[r[k zmatter[]] r[k zreference[]]]'
    q='q[t[c[k r5sw[k zmatter[] k zreference[]]][k zperson[]]][k zactual[]]].q[t[c[s['+code+']][k zperson[]]][k zactual[]]].'
    d=fixture(('r5sw','r5sx'),q);rows=[]
    for good in (False,True):
        result=run(d,model(d,True,good));assert result==[good,good];rows.append(result)
    v=model(d);v['h26j4']=unknown;rejects(d,v)
    return dict(construction_does_not_execute_references=True,exact_qualified_task_syntax=True,native_and_dequoted_execution=rows,unknown_rejected_on_execution=True)

@lru_cache(None)
def ability_doc(support=False):
    roots=('r5s2','r5s3') if support else ('r5sy','r5sz')
    args=prior.prior.TOPIC+' r[k zqualitycontext[]]'+(' p zagents p zenabling p zeffects' if support else '')
    query=''.join('q[t[c[k '+n+'['+args+']][k zperson[]]][k zcontext[]]].' for n in roots)
    return fixture(roots,query,extra=prior.prior.EXTRA+prior.REFERENCES)
def ability_model(d,variant='baseline'):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'};v.update(prior.model(variant))
    def matching(p,g):return p=='person' and quality_task(g) in ('one','two') and variant!='unqualified_profile'
    v.update(hzuq=lambda p,g,a,s:matching(p,g) and (a,s) in (('now','pretrial'),('after','posttrial')),
        hzur=lambda p,g,a,s:matching(p,g),hzus=lambda p,g,s:matching(p,g) and s in ('pretrial','posttrial'),hzut=lambda *a:False,
        hzuu=lambda p,g,m,a,s:matching(p,g) and m==('methodone' if quality_task(g)=='one' else 'methodtwo'),hzuv=lambda p,g,m,a,s:matching(p,g),
        h26j3=lambda c,p,m,r:c=='reason' and p=='person' and m in ('one','two') and r=='now',
        h26j4=lambda c,p,m,j,r:Content(prior.SCENES,tuple(c=='reason' and (p,r,s)==('person','now','good') and (m,j) in (('one','actone'),('two','acttwo')) and variant!='quality_failure' for s in prior.SCENES)),
        h26j5=lambda p,m,j,r,s,t:s==t,h26j6=lambda p,m,j,r,s,t:j)
    return v
@lru_cache(None)
def ability_checks():
    rows={}
    for support,variants in ((False,('baseline','quality_failure','wrong_standard_context','unqualified_profile')),(True,('baseline','quality_failure','unassessed_after'))):
        d=ability_doc(support)
        for variant in variants:
            want=[True,True] if variant=='baseline' else [True,False] if variant=='quality_failure' else [False,False]
            result=run(d,ability_model(d,variant),prior.DOMAIN,prior.SCENES);assert result==want,(support,variant,result)
            rows[('support_' if support else 'current_')+variant]=result
    return dict(cases=rows,native_quality_and_ability_and_support_executed=True,quality_profile_identity_preserved=True,single_point_comparison_fixture=True,multi_point_stability_checked_separately=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0014')
    urls=('https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_2_0_590','https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_6_2_2635','https://korpora.org/kant/aa08/040.html','https://korpora.org/kant/aa04/331.html')
    observations=('Sicherの誤りを避ける用法と熟練した手の例。主観的自信だけへ限定しない。','Wohlの事柄の性質にふさわしい仕方という用法。道徳的善さへ限定しない。','原文のin Religionsdingenからsicher und gutまでを同じ理解力の使用に結ぶ。','数学と自然科学で細かな演繹なしにも同じ二語を使う対照例。唯一の語義の証明とはしない。')
    return dict(status='judgment_performance_quality_dependency_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[148,412],text=u['text'][148:412]),interpretation=LIMITS,
        references=[dict(url=url,path=path,observation_ja=note) for url,path,note in zip(urls,SOURCES[:4],observations,strict=True)],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['宗教的な対象事項と課題別の全適用条件の採用','固定された集団到達基準','同じ人々への進行内容','条件付き問答・談話と著者帰属','第七段落全文の通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,*SOURCES)})
@lru_cache(None)
def structure_checks():
    c=catalog()
    for old in parents():
        for n,e in old.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    assert not c.document['statements'] and len(parents()[1].document['statements'])==108
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=108,roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('performance',performance_checks),('concrete',concrete_checks),('construction',construction_checks),('ability',ability_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,*PRIORS,*SOURCES,
        'scripts/compose_judgment_performance_quality.py','scripts/check_judgment_performance_quality.py','tests/test_judgment_performance_quality.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_topical_standing.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_qualified_judgment.py','scripts/check_topical_standing.py'}
    return dict(status='judgment_performance_quality_dependency_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
