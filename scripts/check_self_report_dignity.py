"""Check nested self-report/appraisal without importing the quoted facts."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_self_report_dignity import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,MESSAGE,ACTION,STANDARD,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts import check_religious_freedom_policy as prior

INDEX=prior.INDEX;REPORT='reports/self-report-dignity-v1.json'
READING='data/self-report-dignity-reading-v1.json';DOC='docs/self-report-dignity-v1.md';INVENTORY=prior.INVENTORY
LEXICAL='artifacts/self-report-dignity-v1/dwb-unwuerdig.html';SOURCES=(*prior.SOURCES,LEXICAL)
PRIORS=('reports/religious-freedom-policy-v1.json','reports/seventh-paragraph-v1.json')
DOMAIN=prior.DOMAIN;SCENES=prior.SCENES;z=prior.z
FNAMES=('source','role','group','community','topic','reference')
SNAMES=(*FNAMES[:-1],'other','reference')
ANAMES=('actor',*SNAMES)
FARGS=' '.join(z(n) for n in FNAMES);SARGS=' '.join(z(n) for n in SNAMES);AARGS=' '.join(z(n) for n in ANAMES)
CODE4='k r5wg['+' '.join('r['+z(n)+']' for n in FNAMES)+']'
CODE5='k r5wj['+' '.join('r['+z(n)+']' for n in SNAMES)+']'
CODE6='k r5wn['+' '.join('r['+z(n)+']' for n in ANAMES)+']'
PROVIDERS='r zsavemessage['+MESSAGE+'] c.r zsaveaction['+ACTION+'] c.r zsaveappraisal[i g[e]] c.r zmessage[f] c.'
PROVIDERS+=''.join('r z'+n+'[a '+ACTION+' d] c.' for n in ('firststandard','secondstandard'))
PROVIDERS+='r zstandardpick[a a a d j['+STANDARD+']] j['+STANDARD+'].'
rules=['i[person a action '+ACTION+'][b point[k z'+n+'[v person v action v point]]]' for n in ('firststandard','secondstandard')]
PROVIDERS+='d h26nh[person a office a community a reference d] j['+STANDARD+'][k zstandardpick[v person v office v community v reference l['+STANDARD+']['+' '.join(rules)+']]].'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots),statements=[])
    prefix=parse('p:'+prior.EXTRA+prior.PROVIDERS+PROVIDERS)
    replacements={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h','h246e','h26nh')}
    d['declarations']=[x for x in prefix['declarations'] if x['name'] not in replacements]+[replacements.get(x['name'],x) for x in d['declarations']]
    return parse(format_graph(d,'compact')+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def identity(code):return code.rank,code.syntax
def base(d):
    v=prior.base(d);saved={}
    for key,n in (('duty','zinspect'),('message','zsavemessage'),('action','zsaveaction'),('appraisal','zsaveappraisal')):
        v[n]=lambda code,key=key:saved.update({key:identity(code)}) is None
    v.update(f3=lambda person,event,point:(person,event,point)==('actor','event','now'),
        h246c=lambda group,p,r:(group,r)==('other','reference') and p in ('person','otherperson'),
        zstandardpick=lambda person,office,community,ref,seq:seq if (person,office,community,ref)==('actor','role','community','reference') else SequenceValue((),seq.element_type))
    return v,saved

@lru_cache(None)
def message_checks():
    q='q[k zinspect['+prior.CODE+']].q[k zmessage[c[s['+CODE4+']]['+z('actor')+']]].'
    d=fixture(('r5wc','r5wg'),q);rows=[]
    for belief in (False,True):
        v,saved=base(d);messages=[]
        v['h26nf']=lambda person,code,point:belief and (person,identity(code),point)==('actor',saved['duty'],'now')
        def inspect(msg):
            messages.append((msg.force,msg.content.values));return msg.force=='assert' and msg.content.situations==SCENES
        v['zmessage']=inspect;assert run(d,v)==[True,True]
        assert messages==[('assert',(False,belief,False))],messages;rows.append(dict(inner_belief=belief,message_truth=list(messages[0][1])))
        assert v['h26ne'] is unknown and v['ztruth'] is unknown
    v['h26nf']=unknown;rejects(d,v)
    return dict(cases=rows,native_constructed_message_contains_same_persons_duty_judgment=True,
        actual_duty_policy_and_reporting_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def reporting_checks():
    actual='k r5wh['+z('actor')+' '+z('event')+' '+SARGS+' '+z('now')+']'
    quoted='t[c[s['+CODE5+']]['+z('actor')+' '+z('event')+']]['+z('now')+']'
    q='q[k zsavemessage['+CODE4+']].q['+actual+'].q['+quoted+'].'
    d=fixture(('r5wg','r5wh','r5wj'),q);rows={}
    for variant in ('baseline','no_occurrence','other_presenter','other_activity','empty_audience','second_recipient_missing',
                    'wrong_subject','wrong_content','wrong_point','no_inner_belief'):
        v,saved=base(d)
        def conveys(activity,recipient,subject,code,point):
            expected=('event',recipient,'actor',saved['message'],'now')
            if variant=='wrong_subject':expected=('event',recipient,'otherperson',saved['message'],'now')
            if variant=='wrong_content':expected=('event',recipient,'actor',(0,'different'),'now')
            if variant=='wrong_point':expected=('event',recipient,'actor',saved['message'],'otherpoint')
            return (activity,recipient,subject,identity(code),point)==expected and recipient in ('person','otherperson') and not(variant=='second_recipient_missing' and recipient=='otherperson')
        v['h26ng']=conveys
        if variant=='no_occurrence':v['dg']=lambda *a:False
        if variant=='other_presenter':v['f3']=lambda p,e,s:(p,e,s)==('otherperson','event','now')
        if variant=='other_activity':v['f3']=lambda p,e,s:(p,e,s)==('actor','otherwork','now')
        if variant=='empty_audience':v['h246c']=lambda *a:False
        if variant=='no_inner_belief':v['h26nf']=lambda *a:False
        good=variant in ('baseline','no_inner_belief');got=run(d,v);assert got==[True,good,good],(variant,got);rows[variant]=got[1:]
    for name in ('dg','f3','h246c','h26ng'):
        v,saved=base(d);v['h26ng']=lambda *a:True;v[name]=unknown;rejects(d,v)
    return dict(cases=rows,native_report_and_dequoted_action_agree=True,one_event_all_recipients_same_subject=True,
        report_can_be_false_as_self_report=True,unknown_rejected=True)

@lru_cache(None)
def standard_checks():
    standards='k h26nh['+z('actor')+' '+z('role')+' '+z('community')+' '+z('reference')+']'
    q='q[k zsaveaction['+CODE5+']].'+''.join('q[t[k '+n+'['+z('actor')+' '+CODE5+' '+standards+']]['+z('now')+']].' for n in ('r5wk','r5wl'))
    d=fixture(('r5wj','r5wk','r5wl','h26nh'),q);rows=[]
    for first,second in product((False,True),repeat=2):
        v,saved=base(d)
        v['zfirststandard']=lambda p,c,s:first and (p,identity(c),s)==('actor',saved['action'],'now')
        v['zsecondstandard']=lambda p,c,s:second and (p,identity(c),s)==('actor',saved['action'],'now')
        got=run(d,v);assert got==[True,not(first and second),first and second];rows.append(dict(standards=[first,second],result=got[1:]))
    v,saved=base(d);v['zstandardpick']=lambda p,o,c,r,seq:SequenceValue((),seq.element_type)
    assert run(d,v)==[True,False,False]
    for variant in ('reversed','duplicate','wrong_person','wrong_action','wrong_point'):
        v,saved=base(d)
        v['zfirststandard']=lambda p,c,s:(p,identity(c),s)==('otherperson' if variant=='wrong_person' else 'actor',(0,'wrong') if variant=='wrong_action' else saved['action'],'otherpoint' if variant=='wrong_point' else 'now')
        v['zsecondstandard']=v['zfirststandard']
        if variant in ('reversed','duplicate'):
            v['zstandardpick']=lambda p,o,c,r,seq:SequenceValue(tuple(reversed(seq.items)) if variant=='reversed' else (*seq.items,seq.items[0]),seq.element_type)
        want=variant in ('reversed','duplicate');assert run(d,v)==[True,not want,want],variant
    for n in ('zfirststandard','zsecondstandard'):
        v,saved=base(d);v['zfirststandard']=lambda *a:True;v['zsecondstandard']=lambda *a:True;v[n]=unknown;rejects(d,v)
    return dict(all_minimum_criteria=rows,empty_is_neither_deficient_nor_adequate=True,
        ordering_and_duplicates_do_not_change_adequacy=True,person_action_and_point_fixed=True,unknown_rejected=True)

@lru_cache(None)
def appraisal_checks():
    q='q[k zsaveaction['+CODE5+']].q[k zsaveappraisal['+CODE6+']].q[t[k r5wm['+AARGS+']]['+z('now')+']].q[t[s['+CODE6+']]['+z('now')+']].q[k r5wp['+AARGS+' '+z('now')+']].q[k r5wh['+z('actor')+' '+z('event')+' '+SARGS+' '+z('now')+']].'
    d=fixture(('r5wj','r5wn','r5wm','r5wp','r5wh'),q);rows=[]
    for accepted,adequate,reported in product((False,True),repeat=3):
        v,saved=base(d)
        v['zfirststandard']=lambda p,c,s:adequate and (p,identity(c),s)==('actor',saved['action'],'now')
        v['zsecondstandard']=lambda *a:True
        v['h26ni']=lambda p,c,s:accepted and (p,identity(c),s)==('actor',saved['appraisal'],'now')
        v['h26ng']=lambda *a:reported
        got=run(d,v);assert got==[True,True,adequate,adequate,accepted,reported],(accepted,adequate,reported,got)
        assert v['h26nf'] is unknown and v['h26ne'] is unknown
        rows.append(dict(outer_judgment=accepted,actual_adequacy=adequate,actual_report=reported,result=got[2:]))
    for n in ('h26ni','zstandardpick'):
        v,saved=base(d);v['zfirststandard']=lambda *a:True;v['zsecondstandard']=lambda *a:True;v['h26ni']=lambda *a:True;v['h26ng']=lambda *a:True;v[n]=unknown;rejects(d,v)
    return dict(all_eight_appraisal_adequacy_report_combinations=rows,constructed_appraisal_dequotes_to_same_content=True,
        inner_belief_duty_and_policy_not_imported=True,unknown_rejected=True)

@lru_cache(None)
def reference_checks():
    q='q[k zsaveappraisal['+CODE6+']].q[k r5wo['+AARGS+']].q[k r5wp['+AARGS+' '+z('now')+']].'
    d=fixture(('r5wn','r5wo','r5wp'),q);rows={}
    def values():
        v,saved=base(d);v['h26ni']=lambda p,c,s:(p,identity(c),s)==('actor',saved['appraisal'],'now');return v,saved
    v,saved=values();assert run(d,v)==[True,True,True]
    for obj in ANAMES:
        v,saved=values()
        if obj=='reference':v['zrefpick']=lambda point,*codes:codes[2] if point=='reference' else codes[SCENES.index(point)]
        else:v['znamepick']=lambda item,*codes:codes[DOMAIN.index('work' if item==obj else item)]
        got=run(d,v);assert got==[True,False,False],(obj,got);rows[obj]=True
    for pos in range(3):
        v,saved=values()
        def wrong(person,code,point):
            want=['actor',saved['appraisal'],'now'];want[pos]='other';return (person,identity(code),point)==tuple(want)
        v['h26ni']=wrong;assert run(d,v)==[True,True,False]
    for name in ('znamepick','zrefpick','h26ni'):
        v,saved=values();v[name]=unknown;rejects(d,v)
    return dict(all_eight_references_checked=rows,outer_judgment_person_content_point_distinct=True,
        no_reporting_or_criterion_evaluation_for_outer_judgment=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    start=u['text'].index('der es seiner');end=u['text'].index(', der also');last=u['text'].index('. ')+1
    return dict(status='self_report_and_dignity_appraisal_dependency_partial',
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        sentence_context=dict(range=[0,last],text=u['text'][:last]),interpretation=LIMITS,
        primary_evidence=[dict(path=SOURCES[0],url='https://korpora.org/kant/aa08/040.html',lines='28–31',observation='品位評価の対象はzu sagen以下の自己報告であり、内側に本人の義務判断がある。'),
            dict(path=SOURCES[1],observation='原刊491頁でseiner nicht unwürdig findetと義務判断の発言内容を照合。'),
            dict(path=LEXICAL,url='https://www.dwds.de/wb/dwb/unw%C3%BCrdig',observation='gの個人的品位・道徳的自己意識に反する用法とWielandのseiner nicht unwürdigの例を補助にする。語義の可能性の資料であり、この文の全意味の証明とはしない。')],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['一般的な君主と固定対象集団・共同体・受け手・品位基準の本文接続','sondern/alsoの作用域と名称拒否・高慢評価・自らの強調',
            '本人の啓蒙・世界と後代の称賛・最初の政府側の解放・各人の良心事項の自由','491–492頁の全一文照合・著者帰属・後続文と段落通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*SOURCES,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog()
    for p in parents():
        for n,e in c.entries.items():
            if n in p.entries:assert e['declaration']==p.entries[n]['declaration'] and e['meaning_ja']==p.entries[n]['meaning_ja']
    assert not c.document['statements'] and len(parents()[1].document['statements'])==112
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==17
    for r in reviews:assert r['selection']==selection_binding(parents()[1],[s['index'] for s in r['selection']['statements']])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    source=(ROOT/LIBRARY).read_text(encoding='utf-8')
    for old,new in (('r e[p r5wf]','r d[p r5wf]'),('r f[p r5wi]','r e[p r5wi]'),('r g[p r5wm]','r f[p r5wm]')):
        try:parse(source.replace(old,new))
        except (ValueError,TypeError):pass
        else:raise AssertionError('Insufficient quotation rank: '+old)
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=112,
        preserved_whole_unit_reviews=17,new_verified_characters=0,compact_full_v2_roundtrips=True,rank_four_five_six_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for name,fn in (('message',message_checks),('reporting',reporting_checks),('standards',standard_checks),('appraisal',appraisal_checks),('references',reference_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,*SOURCES,*PRIORS,
        'scripts/compose_self_report_dignity.py','scripts/check_self_report_dignity.py','tests/test_self_report_dignity.py',
        'scripts/compose_religious_freedom_policy.py','scripts/check_religious_freedom_policy.py','scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='self_report_and_dignity_appraisal_dependency_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
