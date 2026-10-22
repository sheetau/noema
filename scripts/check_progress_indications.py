"""Check fixed actual claims, comparable scenarios and fallible indications."""
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
from scripts.compose_progress_indications import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,FIELDS,SCORE,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

DOC='docs/progress-indications-v1.md';READING='data/progress-indications-reading-v1.json';REPORT='reports/progress-indications-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/departure-hindrance-trend-v1.json','reports/qualified-pursuit-opening-v1.json','reports/religious-collective-assessment-v1.json','reports/clear-indications-v1.json','reports/sixth-paragraph-v1.json')
SOURCES=('artifacts/judgment-performance-quality-v1/kant-aa08-040.html','artifacts/royal-writing-oversight-v1/page-491.jpg')
CASES=('actual','positiveone','positivetwo','negativeone','negativetwo')
SCENES=(*CASES,*(c+t for c in CASES for t in ('past','now')),'reference')
PEOPLE=('alice','bob');ITEMS=('signone','signtwo');DOMAIN=(*PEOPLE,*ITEMS,'group','epoch','topic','work','process','obstacle','frame','factor')
EXTRA=''.join('r z'+n+'[] '+t+'.' for n,t in FIELDS)
EXTRA+=''.join('r z'+n+'[] d.' for n in SCENES if n not in {f for f,_ in FIELDS})+'r zitem[] a.r zobserver[] a.r zcontext[] d.'
EXTRA+=''.join('r z'+n+'[] '+t+'.' for n,t in SCORE)
CODES=' '.join('r[k z'+n+'[]]' for n,_ in FIELDS)
VALUES=' '.join('k z'+n+'[]' for n,_ in FIELDS)
FAMILY='k r5um['+CODES+']';ACTUAL='r[k zactual[]]';SCORES=' '.join('k z'+n+'[]' for n,_ in SCORE)
SOURCE=CODES+' '+ACTUAL+' '+SCORES
ITEM=FAMILY+' '+ACTUAL+' k zobserver[] k zcontext[] k zitem[] '+SCORES
BOUNDARIES=('r5ui','r5tp','r5tw','r5ue')

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=BOUNDARIES,native_name=False):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    text=format_graph(d,'compact');extra=EXTRA
    if native_name:
        old='r h223h[d] i[d].';assert old in text
        text=text.replace(old,'d h223h[point d] i[d][r[k zactualnow[]]].')
        text=text.replace('p:','p:r zactualnow[] d.',1);extra=extra.replace('r zactualnow[] d.','')
    return parse(text+extra+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v,runner=run):
    try:runner(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def content(points):return Content(SCENES,tuple(s in points for s in SCENES))
def constant(value):return lambda:value
def fv(parameters,result,body):return FunctionValue(tuple(parameters),result,body)
STATE={'kind':'function','parameters':['individual'],'result':'truth'}
EQUATION={'kind':'function','parameters':['individual',STATE],'result':'truth'}
SEQUENCE={'kind':'sequence','element':'individual'}

def model(d,hypothesis=(False,True,True,False,False),signal=(True,True,True,False,False),variant='baseline',scale=1):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+s:constant(s) for s in SCENES})
    v.update(ha=lambda a,b:a+b,hb=lambda a,b:a*b,hc=lambda a,b:a<b,hd=lambda t:Fraction(int(t)),pa=lambda a,b:a/b if b else Fraction(0))
    case=lambda c:c if c in CASES else 'actual'
    functions={
        'candidates':fv(('situation',),'situation',case),
        'points':fv(('situation',),'situation',lambda c:case(c)+'now'),
        'firsts':fv(('situation',),'situation',lambda c:case(c)+'past'),
        'processes':fv(('situation','individual','individual'),'individual',lambda c,p,w:'process'),
        'scope':fv(('individual',),'truth',lambda o:o=='obstacle'),
        'variables':fv(('individual',),SEQUENCE,lambda o:SequenceValue(('obstacle','factor'),'"individual"')),
        'equations':fv(('individual','situation'),EQUATION,lambda o,t:fv(('individual',STATE),'truth',lambda var,s:False)),
        'factors':fv(('individual',),'individual',lambda o:o),
        'worlds':fv(('individual','situation',STATE),'situation',lambda o,t,s:t),
        'matches':fv(('individual','situation',STATE,STATE),'truth',lambda o,t,on,off:True),
        'frames':fv(('situation',),'individual',lambda t:'frame')}
    constants=dict(speaker='alice',group='group',epoch='epoch',reference='reference',topic='topic',bound=Fraction(1),obstacles=SequenceValue(('obstacle',),'"individual"'))
    v.update({'z'+n:constant(value) for n,value in (constants|functions).items()})
    v.update(aa=lambda p:p in PEOPLE,mp=lambda g:SequenceValue(PEOPLE if g=='group' else (),'"individual"'),
        h246c=lambda g,p,r:(g,r)==('group','reference') and p in PEOPLE,
        h257z=lambda r,c,t:r=='reference' and c in CASES and t in (c+'past',c+'now'),
        ic=lambda a,b,c:c in CASES and (a,b)==(c+'past',c+'now'),
        h26aa=lambda e,r:(e,r)==('epoch','reference'),h26ab=lambda e,r,c,t:(e,r)==('epoch','reference') and c in CASES and t in (c+'past',c+'now'),
        h256o=lambda p,c,t:p in PEOPLE and c in CASES and t in (c+'past',c+'now'),
        r5tp=lambda p,w,t,a:p in PEOPLE and (w,t)==('work','topic'),
        r5tw=lambda p,w,t,a,s:p in PEOPLE and (w,t)==('work','topic') and a.endswith('now') and s in (a[:-3]+'past',a) and not(variant=='unassessed_opening' and a=='negativeonenow'),
        r5ue=lambda *a:fv(('individual','situation'),'truth',lambda o,t:(a[0],a[1])==('group','reference') and not(variant=='unassessed_obstacle' and t=='negativeonepast')))
    def progress(s,g,e,r,c,p,topic,first,processes,obstacles,scope,bound,variables,equations,factors,worlds,matches,frames):
        correct=(s,g,e,r,topic)==('alice','group','epoch','reference','topic') and c in CASES and (p,first)==(c+'now',c+'past')
        correct=correct and processes('alice','work')=='process' and normalized(obstacles)==('obstacle',) and scope('obstacle') and bound==1 and factors('obstacle')=='obstacle'
        return correct and hypothesis[CASES.index(c)]
    v['r5ui']=progress
    selected=tuple(CASES if variant not in ('actual_omitted','missing_case') else CASES[1:])
    listed=selected if variant!='duplicate_case' else (*CASES,'actual')
    if variant=='missing_case':selected=CASES;listed=CASES[:-1]
    v.update(zitem=constant('signone'),zobserver=constant('alice'),zcontext=constant('actualnow'),
        zcases=constant(SequenceValue(listed,'"situation"')),
        zselected=constant(fv(('situation',),'truth',lambda c:c in selected)),
        zweight=constant(fv(('situation',),'number',lambda c:Fraction(0 if variant=='zero_weight' and c=='negativeone' else scale))),
        zthreshold=constant(Fraction(1 if variant=='bad_threshold' else 2)),
        zclassified=constant(fv(('individual','situation'),'truth',lambda item,c:not(variant=='unclassified' and (item,c)==('signtwo','negativeone')))),
        zcontents=constant(fv(('individual',),'content',lambda item:content({c for c,b in zip(CASES,signal) if b} if item in ITEMS else set()))),
        zaccessible=constant(fv(('individual','individual','situation'),'truth',lambda p,item,point:(p,point)==('alice','actualnow') and item in (ITEMS[:1] if variant=='single' else ITEMS))))
    targets=[]
    def linked(item,target,point):
        targets.append((target.rank,json.loads(target.syntax)))
        return variant!='wrong_target' and item in ITEMS and point=='actualnow' and target.rank==3
    # The callback is a boundary for epistemic correspondence. Exact native
    # quotation identity is checked against an independently constructed target.
    ds={x['name']:x for x in d['declarations']}
    linked_type=ds['zlinked']['result'];v['zlinked']=constant(fv(linked_type['parameters'],linked_type['result'],linked))
    v['_targets']=targets
    return v

@lru_cache(None)
def family_checks():
    fixed='k r5uo['+FAMILY+' k zactual[]]';hyp='k r5uq['+FAMILY+']'
    q=''.join('q[t['+fixed+'][k z'+c+'[]]].' for c in CASES)+''.join('q[t['+hyp+'][k z'+c+'[]]].' for c in CASES)
    q+='q[e[k r5up['+FAMILY+' '+ACTUAL+']][o a[r d[p r5uo]][o r['+FAMILY+'] '+ACTUAL+']]].'
    d=fixture(('r5uo','r5up','r5uq','r5um'),q);rows={}
    for profile in ((False,True,True,False,False),(True,False,True,False,False)):
        got=run(d,model(d,profile));assert got==[profile[0]]*5+list(profile)+[True],got;rows[str(profile)]=got
    for variant in ('other_population','other_topic','other_current','other_first','other_process'):
        v=model(d)
        if variant in ('other_population','other_topic'):v[{'other_population':'zgroup','other_topic':'ztopic'}[variant]]=constant('work')
        if variant in ('other_current','other_first'):
            v[{'other_current':'zpoints','other_first':'zfirsts'}[variant]]=constant(fv(('situation',),'situation',lambda c:'reference'))
        if variant=='other_process':v['zprocesses']=constant(fv(('situation','individual','individual'),'individual',lambda *a:'work'))
        got=run(d,v);assert got==[False]*10+[True],(variant,got);rows[variant]=got
    v=model(d);v['r5ui']=unknown;rejects(d,v)
    return dict(cases=rows,native_family_construction_and_actual_reference=True,quoted_actual_target_identity=True,boundaries=['r5ui'],unknown_rejected=True)

@lru_cache(None)
def indication_checks():
    # Exhaust the diagnostic and plurality in a small generic model. Actual
    # source settings and their validation are checked separately below.
    small_domain=('alice',*ITEMS)
    small_run=lambda d,v:evaluate(d,v,small_domain,CASES,True)
    family='r c[p zfamily]';target=family+' r[k zactual[]] k zobserver[] k zcontext[]'
    q='q[k r5ur['+target+' k zitem[] '+SCORES+']].q[k r5us['+target+' '+SCORES+']].q[t[k r5uo['+family+' k zactual[]]][k zactual[]]].'
    base=deepcopy(catalog().document);base.update(declarations=closure(base,['r5ur','r5us','r5uo']),statements=[])
    extra='r zfamily[d] e.r zactual[] d.r zitem[] a.r zobserver[] a.r zcontext[] d.'+''.join('r z'+n+'[] '+t+'.' for n,t in SCORE)
    d=parse(format_graph(base,'compact')+extra+q);count=0
    def small_model(doc,profile=(False,True,True,False,False),signal=(True,True,True,False,False),variant='baseline',scale=1):
        v=model(doc,profile,signal,variant,scale)
        v.update(zfamily=lambda case:Content(CASES,(profile[CASES.index(case)],)*len(CASES)),zcontext=constant('actual'))
        v['zcontents']=constant(fv(('individual',),'content',lambda item:Content(CASES,tuple(b and item in ITEMS for b in signal))))
        v['zaccessible']=constant(fv(('individual','individual','situation'),'truth',lambda p,item,point:(p,point)==('alice','actual') and item in (ITEMS[:1] if variant=='single' else ITEMS)))
        def linked(item,code,point):
            v['_targets'].append((code.rank,json.loads(code.syntax)))
            return variant!='wrong_target' and item in ITEMS and point=='actual' and code.rank==3
        typ=next(x['result'] for x in doc['declarations'] if x['name']=='zlinked')
        v['zlinked']=constant(fv(typ['parameters'],typ['result'],linked))
        return v
    for signal in product((False,True),repeat=5):
        want=signal[0] and 3*sum(signal[1:3])>4*(signal[0]+sum(signal[3:]))
        v=small_model(d,signal=signal);got=small_run(d,v);assert got==[want,want,False],(signal,got);count+=1
        targets=v['_targets'];assert targets and all(t==targets[0] for t in targets)
    rows={}
    for variant in ('baseline','single','wrong_target','unclassified','duplicate_case','missing_case','actual_omitted','zero_weight','bad_threshold'):
        got=small_run(d,small_model(d,variant=variant));want=[variant not in ('wrong_target','duplicate_case','missing_case','actual_omitted','zero_weight','bad_threshold'),variant=='baseline',False]
        assert got==want,(variant,got,want);rows[variant]=got
    assert small_run(d,small_model(d,scale=7))==[True,True,False]
    # A constant actual claim cannot replace the comparison hypothesis: it
    # lacks one of the two required truth groups, whether actually false/true.
    text='q[k rmb[c[k zcontents[]][k zitem[]] k r5uo['+family+' k zactual[]] k zcases[] k zselected[] i[c d][e[v c][v c]] k zweight[] k zthreshold[]]].'
    old=parse(format_graph(base,'compact')+extra+text)
    for truth in (False,True):assert small_run(old,small_model(old,(truth,True,True,False,False)))==[False]
    for name in ('zclassified','zcontents','zlinked','zaccessible','zfamily'):
        v=small_model(d);v[name]=unknown;rejects(d,v,small_run)
    return dict(diagnostic_profiles=count,cases=rows,actual_false_with_clear_signs=True,constant_actual_hypothesis_rejected=True,positive_weight_rescaling_invariant=True,boundaries=['zfamily: explicitly supplied generic progress family'],unknown_rejected=True)

@lru_cache(None)
def source_checks():
    q='q[k r5ut['+SOURCE+']].'+''.join('q[t[k r5uu['+SOURCE+']][k z'+c+'[]]].' for c in ('actual','positiveone'))
    d=fixture(('r5ut','r5uu'),q,('r5uk','r5ur'));rows={}
    for variant in ('baseline','unassessed_case','unavailable_sign','foreign_observer','foreign_actual','foreign_context'):
        v=model(d);seen=[]
        def checked(*a):
            valid=a[:5]==('alice','group','epoch','reference','topic')
            valid=valid and a[5]('actual')=='actual' and a[6]('actual')=='actualnow' and a[7]('actual')=='actualpast'
            return fv(('situation',),'truth',lambda case:valid and not(variant=='unassessed_case' and case=='negativeone'))
        def indication(family,actual,observer,context,item,*a):
            syntax=json.loads(family.syntax);seen.append((syntax,normalized(actual),observer,context))
            # Every closed setting is retained in its original position.
            expected=dict(kind='apply',function=dict(kind='function_ref',symbol='r5ul'),arguments=[dict(kind='call',symbol='z'+n,arguments=[]) for n,_ in FIELDS])
            valid=family.rank==2 and syntax==expected
            valid=valid and normalized(actual)==('zpositiveone' if variant=='foreign_actual' else 'zactual',0)
            valid=valid and (observer,context)==('bob' if variant=='foreign_observer' else 'alice','positiveonenow' if variant=='foreign_context' else 'actualnow')
            return valid and item in (ITEMS[:1] if variant=='unavailable_sign' else ITEMS)
        v.update(r5uk=checked,r5ur=indication)
        got=run(d,v);assert got==[variant=='baseline']*3,(variant,got);rows[variant]=got
        assert seen and all(x==seen[0] for x in seen)
    return dict(cases=rows,native_closed_family_reference_and_all_case_guard=True,boundaries=['r5uk','r5ur'],outer_point_does_not_rebind_actual=True)

@lru_cache(None)
def assessment_checks():
    q=''.join('q[c[k r5uk['+VALUES+']][k z'+c+'[]]].' for c in CASES)
    d=fixture(('r5uk',),q);rows={}
    for variant in ('baseline','unassessed_opening','unassessed_obstacle','wrong_population','wrong_epoch','bad_bound','duplicate_obstacles'):
        v=model(d,variant=variant);want=[True]*5
        if variant in ('unassessed_opening','unassessed_obstacle'):want[3]=False
        if variant=='wrong_population':v['h246c']=lambda g,p,r:p=='alice';want=[False]*5
        if variant=='wrong_epoch':v['h26aa']=lambda *a:False;want=[False]*5
        if variant=='bad_bound':v['zbound']=constant(Fraction(0));want=[False]*5
        if variant=='duplicate_obstacles':v['zobstacles']=constant(SequenceValue(('obstacle','obstacle'),'"individual"'));want=[False]*5
        got=run(d,v);assert got==want,(variant,got,want);rows[variant]=got
    return dict(cases=rows,native_current_frame_and_all_interval_checks=True,boundaries=['r5tp','r5tw','r5ue'])

@lru_cache(None)
def dialogue_checks():
    q='l[k r5uv['+CODES+' '+ACTUAL+']].l[k r5uw['+CODES+' '+ACTUAL+']].'
    d=fixture(('r5uv','r5uw'),q,BOUNDARIES+('r5ta','r5tb'),True);rows=[]
    for attained,checked,progress in product((False,True),repeat=3):
        v=model(d,(progress,True,True,False,False))
        v['h26kc']=lambda g,r:Fraction(1,2)
        def ability(topic,anchor,code,truth):
            valid=(topic,anchor,normalized(code))==('topic','actualnow',('zactualnow',0))
            return fv(('individual',),'content',lambda p:content({'actualnow'} if valid and p in PEOPLE and truth else set()))
        v['r5ta']=lambda *a:ability(*a,checked);v['r5tb']=lambda *a:ability(*a,attained)
        got=run(d,v);question,answer=got
        assert isinstance(question,Message) and question.force=='ask' and answer.force=='assert'
        assert question.content.values==(checked and attained,)*len(SCENES)
        assert answer.content.values==(checked and not attained and progress,)*len(SCENES)
        rows.append(dict(attained=attained,checked=checked,progress=progress,question=question.content.values[0],answer=answer.content.values[0]))
    return dict(cases=rows,native_population_ratio_and_question_answer=True,same_actual_setting_and_progress_family=True,boundaries=['r5ta','r5tb','r5ui'])

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0014');start=u['text'].index('Allein,');end=u['text'].index(' In diesem Betracht')
    return dict(status='progress_indications_and_answer_content_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),interpretation=LIMITS,
        references=[dict(url='https://korpora.org/kant/aa08/040.html',path=SOURCES[0],observation_ja='第三文のdavonは同じ機会開放と障害漸減を受ける。徴候の存在を対象の無謬な保証へ強めず、第一文の回答の進行内容と対象を共有する。')],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['第三文の場の比喩・現在進行・doch・Allein・oderの提示','第一文の条件付き問答・denn/nun・Nein/aber wohl・著者帰属','第二文の甚だしい不足と支援可能性','後続文と段落通読'],
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
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=108,roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('family',family_checks),('indication',indication_checks),('source',source_checks),('assessment',assessment_checks),('dialogue',dialogue_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,*PRIORS,*SOURCES,
        'scripts/compose_progress_indications.py','scripts/check_progress_indications.py','tests/test_progress_indications.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_situated_criticism.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='progress_indications_dependency_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
