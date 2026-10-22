"""Check religious task binding, exact population ratios and fixed dialogue."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,Message
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_religious_collective_assessment import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts import check_present_epoch_assessment as epoch
from scripts import check_judgment_performance_quality as quality

DOC='docs/religious-collective-assessment-v1.md'
READING='data/religious-collective-assessment-reading-v1.json'
REPORT='reports/religious-collective-assessment-v1.json'
INVENTORY=epoch.INVENTORY
PRIORS=('reports/judgment-performance-quality-v1.json','reports/present-epoch-assessment-v1.json','reports/general-resistance-v1.json','reports/sixth-paragraph-v1.json')
SOURCES=('artifacts/judgment-performance-quality-v1/kant-aa08-040.html','artifacts/religious-collective-assessment-v1/kant-aa08-041.html','artifacts/royal-writing-oversight-v1/page-491.jpg')
PEOPLE=epoch.PEOPLE;DOMAIN=epoch.DOMAIN;SCENES=epoch.SCENES
EXTRA=epoch.EXTRA+'r zpeople[a] c.r zreached[a] c.'
FRAME=epoch.FRAME;SOURCE=FRAME+' k ztopic[] r[k znow[]]'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=EXTRA,native_names=False):
    d=deepcopy(catalog().document)
    if native_names:
        ds=[]
        for x in d['declarations']:
            if x['name']=='h26kb':
                text='r zone[] a.r ztwo[] a.r zchoose[a i[a] i[a]] i[a].d h26kb[matter a reference d] i[a][k zchoose[v matter r[k zone[]] r[k ztwo[]]]].'
                ds.extend(parse(format_graph(dict(d,declarations=ds,statements=[]),'compact')+text)['declarations'][len(ds):])
            else:ds.append(x)
        d['declarations']=ds
        for declaration in ('r zone[] a.','r ztwo[] a.','r zchoose[a i[a] i[a]] i[a].'):extra=extra.replace(declaration,'')
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+extra+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')
def base(d,capability=(True,True,False),assessment=(True,True,True),progress=True,threshold=Fraction(2,3)):
    v=epoch.base(d,capability,assessment,progress)
    v.update(mp=lambda g:SequenceValue(PEOPLE if g=='group' else (),'"individual"'),
        h26kc=lambda g,r:threshold if (g,r)==('group','reference') else Fraction(0),
        ha=lambda a,b:a+b,hb=lambda a,b:a*b,hc=lambda a,b:a<b,hd=lambda t:Fraction(int(t)),pa=lambda a,b:a/b if b else Fraction(0),
        zpeople=lambda p:p in PEOPLE,zreached=lambda p:p in PEOPLE and capability[PEOPLE.index(p)],
        h26j7=lambda t,r:(t,r)==('topic','now'),h26ka=lambda p,t,m,r:p in PEOPLE and (t,m,r)==('topic','matter','now'))
    def activity(t,anchor,code,capable=False):
        valid=(t,anchor)==('topic','now') and json.loads(code.syntax)=={'kind':'call','symbol':'znow','arguments':[]}
        return FunctionValue(('individual',),'content',lambda p:epoch.content({'now'} if valid and p in PEOPLE and (capability if capable else assessment)[PEOPLE.index(p)] else set()))
    v.update(r5ta=activity,r5tb=lambda *a:activity(*a,capable=True))
    return v

@lru_cache(None)
def scope_checks():
    q='q[k r5s6[k zalice[] k ztopic[] k zmatter[] k znow[]]].'
    d=fixture(('r5s6',),q);rows={}
    for variant in ('baseline','nonreligious','nonperson','other_person_scope','other_topic','other_matter','other_reference'):
        v=base(d)
        if variant=='nonreligious':v['h26j7']=lambda *a:False
        if variant=='nonperson':v['aa']=lambda *a:False
        if variant=='other_person_scope':v['h26ka']=lambda p,t,m,r:p=='bob'
        if variant in ('other_topic','other_matter','other_reference'):v[{'other_topic':'ztopic','other_matter':'zmatter','other_reference':'znow'}[variant]]=lambda:'outside' if variant=='other_reference' else 'outsider'
        result=run(d,v);assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
    for n in ('aa','h26j7','h26ka'):
        v=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,scope_not_selected_by_success_or_belief=True,unknown_rejected=True)

@lru_cache(None)
def native_ability_checks():
    prior=quality.prior
    extra=prior.prior.EXTRA+prior.REFERENCES
    args='k ztopic[] k zanchor[] r[k zqualitycontext[]]'
    q=''.join('q[t[c[k '+n+'['+args+']][k zperson[]]][k zcontext[]]].' for n in ('r5ta','r5tb'))
    d=fixture(('r5ta','r5tb'),q,extra=extra,native_names=True);rows={}
    for variant,want in (('baseline',[True,True]),('quality_failure',[True,False]),('nonreligious',[False,False]),('wrong_reference',[False,False])):
        v=quality.ability_model(d,variant)
        v.update(h26j7=lambda topic,r:variant!='nonreligious' and (topic,r)==('one','now'),h26ka=v['ztopics'])
        result=run(d,v,prior.DOMAIN,prior.SCENES);assert result==want,(variant,result);rows[variant]=result
    return dict(cases=rows,native_scope_names_quality_and_current_ability_executed=True,closed_names_supplied_by_native_noema_definition=True,
        support_body_binding_checked_structurally=True,support_implementation_previously_executed=PRIORS[0])

@lru_cache(None)
def ratio_checks():
    args='k zgroup[] k zreference[] p zpeople p zreached k znow[]'
    d=fixture(('r5tg',),'q[k r5tg['+args+']].');rows={};count=0
    for threshold in (Fraction(1,3),Fraction(2,3),Fraction(1)):
        results={}
        for bits in product((False,True),repeat=3):
            got=run(d,base(d,bits,threshold=threshold))[0];assert got==(Fraction(sum(bits),3)>=threshold)
            results[bits]=got;count+=1
        for a,b in product(results,repeat=2):
            if sum(a)==sum(b):assert results[a]==results[b]
            if all(not x or y for x,y in zip(a,b,strict=True)):assert not results[a] or results[b]
        rows[str(threshold)]={''.join(str(int(x)) for x in bits):v for bits,v in results.items()}
    cases={}
    for variant in ('reordered','missing','extra','duplicate','empty','nonhuman','wrong_group','wrong_reference','mismatched_people','outsider_success','zero','negative','above_one'):
        v=base(d);want=variant=='reordered'
        listed={'reordered':tuple(reversed(PEOPLE)),'missing':PEOPLE[:2],'extra':(*PEOPLE,'outsider'),'duplicate':(*PEOPLE,'alice'),'empty':()}
        if variant in listed:v['mp']=lambda g:SequenceValue(listed[variant],'"individual"')
        if variant=='empty':v['h246c']=lambda *a:False;v['zpeople']=lambda *a:False
        if variant=='nonhuman':v['aa']=lambda p:p in PEOPLE[:2]
        if variant=='wrong_group':v['zgroup']=lambda:'outsider'
        if variant=='wrong_reference':v['zreference']=lambda:'outside'
        if variant=='mismatched_people':v['zpeople']=lambda p:p in PEOPLE[:2]
        if variant=='outsider_success':v['zreached']=lambda p:p in ('alice','outsider')
        if variant in ('zero','negative','above_one'):v['h26kc']=lambda *a:{'zero':Fraction(0),'negative':Fraction(-1),'above_one':Fraction(4,3)}[variant]
        got=run(d,v);assert got==[want],(variant,got);cases[variant]=got[0]
    # The criterion ignores an unrelated evaluation point, retaining fixed inputs.
    d2=fixture(('r5tg',),'q[k r5tg['+args.replace('k znow[]','k zfuture[]')+']].')
    assert run(d2,base(d2))==[True]
    for n in ('mp','h246c','h26kc','hc','pa','zreached'):
        v=base(d);v[n]=unknown;rejects(d,v)
    return dict(distributions=count,thresholds=rows,contrasts=cases,anonymous_and_monotone=True,fixed_reference_across_evaluation_points=True,unknown_rejected=True,native_exact_fraction=True)

@lru_cache(None)
def dialogue_checks():
    roots=('r5ti','r5tj','r5tk','r5tl','r5tm','r5tn')
    q=''.join('q[k '+n+'['+SOURCE+(' k zprogress[]' if n=='r5tk' else '')+']].' for n in roots[:4])
    q+='l[k r5tm['+SOURCE+']].l[k r5tn['+SOURCE+' k zprogress[]]].'
    d=fixture(roots,q,('r5ta','r5tb'));count=0
    for bits in product((False,True),repeat=3):
        for checked,progress in product((False,True),repeat=2):
            v=base(d,bits,(checked,)*3,progress);got=run(d,v);attained=checked and sum(bits)>=2;contrast=checked and not attained and progress
            assert got[:4]==[checked,attained,contrast,checked and not attained]
            question,answer=got[4:];assert isinstance(question,Message) and isinstance(answer,Message)
            assert question.force=='ask' and answer.force=='assert'
            assert question.content.values==(attained,)*len(SCENES) and answer.content.values==(contrast,)*len(SCENES)
            count+=1
    cases={}
    for variant in ('unassessed_member','missing_current_person','wrong_topic','wrong_threshold_reference','wrong_present','invalid_threshold'):
        v=base(d)
        if variant=='unassessed_member':v=base(d,assessment=(True,True,False))
        if variant=='missing_current_person':v['h246c']=lambda g,p,r:(g,r)==('group','reference') and p in PEOPLE[:2]
        if variant=='wrong_topic':v['ztopic']=lambda:'matter'
        if variant=='wrong_threshold_reference':v['h26kc']=lambda g,r:Fraction(0) if r=='reference' else Fraction(2,3)
        if variant=='wrong_present':v['znow']=lambda:'outside'
        if variant=='invalid_threshold':v['h26kc']=lambda *a:Fraction(0)
        got=run(d,v);assert got[:4]==[False]*4,(variant,got[:4]);cases[variant]=got[:4]
    v=base(d);v['r5ta']=unknown;rejects(d,v)
    return dict(combinations=count,counterexamples=cases,native_population_epoch_ratio_and_fixed_dialogue=True,boundaries=['r5ta','r5tb'],
        activity_boundary_independently_checked_by='native_ability_checks',unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0014')
    return dict(status='religious_collective_assessment_dependency_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,412],text=u['text'][:412]),interpretation=LIMITS,
        references=[dict(url='https://korpora.org/kant/aa08/040.html',path=SOURCES[0],observation_ja='同じ段落の時代判断と宗教的事項、前後の個人の救済・良心と宗教上の自由を照合。'),dict(url='https://korpora.org/kant/aa08/041.html',path=SOURCES[1],observation_ja='後段の著者の説明が宗教上の問題を主眼に置くことを確認。')],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['同じ現在人口の具体的な進行内容','条件付きの問い・denn/nun・Nein/aber wohl・著者帰属','第二文の甚だしい不足と支援可能性の集団評価','後続文と第七段落全文の通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,*SOURCES)})
@lru_cache(None)
def structure_checks():
    c=catalog()
    for old in parents():
        for n,e in old.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    assert not c.document['statements'] and len(parents()[2].document['statements'])==108
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for n,target in (('r5tc','r5s2'),('r5td','r5s3')):
        declaration=c.entries[n]['declaration'];body=declaration['body'];assert body['symbol']==target
        a=body['arguments'];assert a[2]=={'kind':'function_ref','symbol':'r5s6'} and a[3]['symbol']=='r5s7'
        assert a[-3:]==[{'kind':'variable','name':p['name']} for p in declaration['parameters'][-3:]]
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=108,roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('scope',scope_checks),('native_ability',native_ability_checks),('ratio',ratio_checks),('dialogue',dialogue_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,*PRIORS,*SOURCES,
        'scripts/compose_religious_collective_assessment.py','scripts/check_religious_collective_assessment.py','tests/test_religious_collective_assessment.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_present_epoch_assessment.py','scripts/compose_collective_attainment.py','scripts/compose_topical_standing.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_present_epoch_assessment.py','scripts/check_judgment_performance_quality.py','scripts/check_qualified_judgment.py','scripts/check_topical_standing.py'}
    return dict(status='religious_collective_assessment_dependency_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
