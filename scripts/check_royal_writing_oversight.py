"""Check all clarity requirements, actual attempts and same-work regulation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_royal_writing_oversight import ROOT,LIBRARY,BASIS,PARENT,PRIMITIVES,MEANINGS,LIMITS,NAMES,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

DOC='docs/royal-writing-oversight-v1.md'
READING='data/royal-writing-oversight-reading-v1.json'
REPORT='reports/royal-writing-oversight-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
LEXICAL='artifacts/royal-writing-oversight-v1/adelung-rein.html'
PAGE='artifacts/royal-writing-oversight-v1/page-491.jpg'
PRIORS=('reports/monarchical-religion-sentence-v1.json','reports/cognitive-acquisition-v1.json','reports/written-carriers-v1.json')
DOMAIN=('alpha','beta','gamma','delta');SCENES=('reference','candidate','other')
EXTRA=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))+'r zbindings[] j[a].'
A='k zalpha[]';B='k zbeta[]';C='k zgamma[]';D='k zdelta[]';R='k zreference[]';P='k zcandidate[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+EXTRA+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def content(points):return Content(SCENES,tuple(p in points for p in SCENES))
def base(d,bindings=('alpha','gamma','delta')):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(zbindings=lambda:SequenceValue(bindings,'"individual"'),aa=lambda p:p in DOMAIN)
    v['h26ih']=lambda p,w,i,r:(p,w,r)==('alpha','gamma','reference') and i in ('alpha','beta')
    v['h26ad']=lambda i,r:i in ('alpha','beta') and r=='reference'
    v['h26ag']=lambda i,r:i
    v['h26c5']=lambda i,f,r:i in ('alpha','beta') and (f,r)==('delta','reference')
    v['h26ii']=lambda p,w,c,r:(p,w,r)==('alpha','gamma','reference') and c in ('alpha','beta')
    v['h26ah']=lambda p,i,r,t:(p,r,t)==('alpha','reference','candidate') and i in ('alpha','beta')
    v['h26ij']=lambda c,p,w,r:content({'candidate'} if (p,w,r)==('alpha','gamma','reference') and c in ('alpha','beta') else set())
    return v
def unknown_rejected(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def clarity_checks():
    d=fixture(('r5o7',),'q[t[k r5o7[k zbindings[] '+R+']]['+P+']].');rows={}
    for variant in ('baseline','empty_items','empty_criteria','second_item_outside_catalog','second_item_wrong_field','second_item_ungrasped','second_condition_unsatisfied','other_person','other_work','other_field','other_reference','other_point','unknown'):
        v=base(d)
        if variant=='empty_items':v['h26ih']=lambda *a:False
        if variant=='empty_criteria':v['h26ii']=lambda *a:False
        if variant=='second_item_outside_catalog':v['h26ad']=lambda i,r:i=='alpha' and r=='reference'
        if variant=='second_item_wrong_field':v['h26c5']=lambda i,f,r:(i,f,r)==('alpha','delta','reference')
        if variant=='second_item_ungrasped':v['h26ah']=lambda p,i,r,t:(p,i,r,t)==('alpha','alpha','reference','candidate')
        if variant=='second_condition_unsatisfied':v['h26ij']=lambda c,p,w,r:content({'candidate'} if (c,p,w,r)==('alpha','alpha','gamma','reference') else set())
        changes={'other_person':('beta','gamma','delta'),'other_work':('alpha','delta','delta'),'other_field':('alpha','gamma','gamma')}
        if variant in changes:v['zbindings']=lambda:SequenceValue(changes[variant],'"individual"')
        if variant=='other_reference':v['zreference']=lambda:'other'
        if variant=='other_point':v['zcandidate']=lambda:'other'
        if variant=='unknown':v['h26ij']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    # A different item name still requires grasp of its fixed representative.
    v=base(d);v['h26ag']=lambda i,r:'alpha' if i=='beta' else i
    v['h26ah']=lambda p,i,r,t:(p,i,r,t)==('alpha','alpha','reference','candidate')
    assert run(d,v)==[True]
    v['h26ah']=lambda p,i,r,t:(p,i,r,t)==('alpha','beta','reference','candidate');assert run(d,v)==[False]
    return dict(all_items_and_all_explicit_conditions=rows,canonical_item_not_its_alias_required=True,unknown_rejected=True)

def attempt_values(d):
    v=base(d);v['dg']=lambda a,p:(a,p)==('beta','candidate');v['df']=lambda p,a,t:(p,a,t)==('alpha','beta','candidate')
    v['sc']=lambda w,t:(w,t)==('gamma','candidate')
    v['hzwr']=lambda rec,w,t:(rec,w,t)==('delta','gamma','candidate')
    v['hzws']=lambda rec,carrier,t:(rec,carrier,t)==('delta','alpha','candidate')
    v['hzwt']=lambda rec,t:(rec,t)==('delta','candidate')
    v['h26ik']=lambda *a:a==('alpha','beta','gamma','reference','candidate')
    v['h26hf']=lambda *a:normalized(a)==('alpha','beta',('r5o7',1),('alpha','gamma','delta'),'reference','candidate')
    return v

@lru_cache(None)
def attempt_checks():
    d=fixture(('r5pb',),'q[k r5pb['+' '.join((A,B,C,D,R,P))+']].');rows={}
    for variant in ('baseline','no_activity','no_person_participation','not_written_work','no_external_record','unreadable_record','different_record','no_instrumental_use','no_goal','wrong_goal_person','wrong_goal_work','wrong_goal_field','wrong_goal_reference','wrong_goal_point','unknown'):
        v=attempt_values(d)
        # Goal state and truth are deliberately unavailable in an actual attempt.
        v['h26ah']=unknown;v['h26ij']=unknown
        targets={'no_activity':'dg','no_person_participation':'df','not_written_work':'sc','no_external_record':'hzws','unreadable_record':'hzwt','no_instrumental_use':'h26ik','no_goal':'h26hf'}
        if variant in targets:v[targets[variant]]=lambda *a:False
        if variant=='different_record':v['hzws']=lambda rec,carrier,t:(rec,carrier,t)==('beta','alpha','candidate')
        if variant.startswith('wrong_goal_'):
            wanted=['alpha','beta',('r5o7',1),('alpha','gamma','delta'),'reference','candidate']
            if variant=='wrong_goal_person':wanted[3]=('beta','gamma','delta')
            if variant=='wrong_goal_work':wanted[3]=('alpha','beta','delta')
            if variant=='wrong_goal_field':wanted[3]=('alpha','gamma','beta')
            if variant=='wrong_goal_reference':wanted[4]='other'
            if variant=='wrong_goal_point':wanted[5]='other'
            v['h26hf']=lambda *a:normalized(a)==tuple(wanted)
        if variant=='unknown':v['h26ik']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(native_actual_attempt_and_shared_record=rows,unachieved_and_unknown_goal_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def supervision_checks():
    d=fixture(('r5pd',),'q[k r5pd['+' '.join((A,B,C,D,C,R,P))+']].',('r2ui',));rows={}
    for variant in ('baseline','not_highest_office','not_holder','no_activity','no_participation','private_reading_only','no_worthiness_treatment','wrong_office','wrong_work','wrong_reference','wrong_point','unknown'):
        v=base(d);v['h234f']=lambda *a:a==('beta','gamma','candidate');v['r2ui']=lambda *a:a==('alpha','beta','gamma','candidate')
        v['dg']=lambda *a:a==('delta','candidate');v['df']=lambda *a:a==('alpha','delta','candidate')
        wanted=['delta','beta','gamma','reference','candidate']
        changes={'wrong_office':(1,'alpha'),'wrong_work':(2,'beta'),'wrong_reference':(3,'other'),'wrong_point':(4,'other')}
        if variant in changes:i,value=changes[variant];wanted[i]=value
        v['h26il']=lambda *a:a==tuple(wanted)
        v['h26im']=lambda *a:a==('alpha','delta','gamma','reference','candidate')
        targets={'not_highest_office':'h234f','not_holder':'r2ui','no_activity':'dg','no_participation':'df','private_reading_only':'h26il','no_worthiness_treatment':'h26im'}
        if variant in targets:v[targets[variant]]=lambda *a:False
        if variant=='unknown':v['h26il']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(office_activity_and_same_work=rows,no_ban_or_success_required=True,boundaries=['r2ui: same office holding'],unknown_rejected=True)

@lru_cache(None)
def binding_checks():
    d=fixture(('r5pc',),'q[k r5pc['+' '.join((B,C,A,B,C,D,R,P))+']].',('r5ni','r5pb'));rows={}
    for variant in ('baseline','other_monarch','other_subject','other_community','other_religious_field','other_attempt','other_reference','unknown'):
        v=base(d);wanted=['beta','alpha','gamma','reference']
        changes={'other_monarch':(0,'alpha'),'other_subject':(1,'beta'),'other_community':(2,'delta'),'other_reference':(3,'other')}
        if variant in changes:i,value=changes[variant];wanted[i]=value
        v['r5ni']=lambda *a:a==tuple(wanted)
        v['h26g7']=lambda *a:a==('gamma' if variant=='other_religious_field' else 'delta','gamma','reference')
        v['r5pb']=lambda *a:a==('alpha','alpha' if variant=='other_attempt' else 'beta','gamma','delta','reference','candidate')
        if variant=='unknown':v['r5ni']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'];rows[variant]=actual[0]
    d=fixture(('r5pe',),'q[k r5pe['+' '.join((A,C,B,A,C,D,D,R,P))+']].',('r5pc','r5pd'));joined={}
    for variant in ('baseline','different_work','different_subject_project','different_monarch','different_intervention','unknown'):
        v=base(d);v['r5pc']=lambda *a:a==('alpha','gamma','beta','alpha','gamma','delta','reference','candidate')
        v['r5pd']=lambda *a:a==('beta' if variant=='different_monarch' else 'alpha','beta','gamma','delta','alpha' if variant=='different_work' else 'gamma','reference','candidate')
        v['h26in']=lambda *a:a==('beta' if variant=='different_intervention' else 'delta','beta' if variant=='different_subject_project' else 'alpha','reference','candidate')
        if variant=='unknown':v['h26in']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'];joined[variant]=actual[0]
    return dict(subject_religious_scope=rows,same_work_and_intervention=joined,boundaries=['r5ni','r5pb','r5pc','r5pd'])

@lru_cache(None)
def adapter_checks():
    d=fixture(('r5pf',),'q[t[k r5pf[k zbindings[] '+R+']]['+P+']].',('r5pe',));positions=[]
    for i in range(7):
        b=tuple('beta' if j==i else 'alpha' for j in range(7));v=base(d,b);v['r5pe']=lambda *a:a==(*b,'reference','candidate')
        assert run(d,v)==[True]
        v['zbindings']=lambda:SequenceValue(('alpha',)*7,'"individual"');assert run(d,v)==[False];positions.append(i)
    for variant in ('short','long','other_reference','other_point','unknown'):
        v=base(d,('alpha',)*7);v['r5pe']=lambda *a:a==(*('alpha',)*7,'reference','candidate')
        if variant in ('short','long'):v['zbindings']=lambda:SequenceValue(('alpha',)*(6 if variant=='short' else 8),'"individual"')
        if variant=='other_reference':v['zreference']=lambda:'other'
        if variant=='other_point':v['zcandidate']=lambda:'other'
        if variant=='unknown':v['r5pe']=unknown;unknown_rejected(d,v)
        else:assert run(d,v)==[False]
    return dict(all_seven_positions=positions,exact_length_reference_point_and_unknown_checked=True,boundaries=['r5pe'])

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013')
    fragment='wenn er sich hierin mischt, indem er die Schriften, wodurch seine Unterthanen ihre Einsichten ins Reine zu bringen suchen, seiner Regierungsaufsicht würdigt'
    start=u['text'].index(fragment,3645);end=start+len(fragment)
    prior=read('data/personal-enlightenment-choice-reading-v1.json')
    pages=[p for p in prior['primary_pages'] if '490' in p['path']]+[dict(path=PAGE,url='https://api.digitale-sammlungen.de/iiif/image/v2/bsb10926843_00531/full/full/0/default.jpg',sha256=digest((ROOT/PAGE).read_bytes()),visually_inspected=True)]
    return dict(status='written_clarification_and_royal_oversight_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=fragment),
        interpretation=LIMITS,new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        primary_pages=pages,primary_evidence=[
          dict(url='https://korpora.org/kant/aa08/040.html',lines='9–16',observation='原刊490–491頁を表示して最終文と次段落の境を確認。知的内容への監督を前文の秩序保持から区別する。'),
          dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009133_6_1_1007',path=LEXICAL,observation='Reinの見出しは清書と、比喩的な整理・確定を区別する。ここでは後者を理解内容の明確化へ適用し、目的と成功を分ける。'),
          dict(url='https://woerterbuchnetz.de/?lemid=W02928&sigle=Adelung',observation='Würdigenの対象を値すると取り扱う語義を参照。著者の賛同又は統治の正当性とはしない。')],
        unresolved=['威厳への損傷とその比較基準','selbstとwürdigtの皮肉の提示','自分の最高の見識に基づく介入と批判への曝露','Caesar non est supra Grammaticosの引用と意味','最高権力を聖職者の専制へ従属させる介入と残余臣民','sowohl/als auch/noch weit mehrの二側と程度比較','条件・手段説明・全候補量化・著者帰属・全文通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,LEXICAL,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    for n,e in new.entries.items():
        if n not in MEANINGS and n not in PRIMITIVES:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    assert len(old.document['statements'])==107 and new.document['statements']==[]
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    assert read(READING)==reading_record()
    doc=new.document
    for notation in ('compact','full'):
        s=format_graph(doc,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==doc
    assert read(READING)['new_verified_characters']==0
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_unchanged=True,main_statements_unchanged=107,roundtrips=True,verified_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('clarity',clarity_checks),('attempt',attempt_checks),('supervision',supervision_checks),('binding',binding_checks),('adapters',adapter_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{READING,DOC,INVENTORY,LEXICAL,*PRIORS,*(p['path'] for p in read(READING)['primary_pages']),
        'data/personal-enlightenment-choice-reading-v1.json','scripts/compose_royal_writing_oversight.py','scripts/check_royal_writing_oversight.py','tests/test_royal_writing_oversight.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='written_clarification_and_royal_oversight_partial',**results,
        alignment=dict(**read(READING)['source'],document=LIBRARY,definitions=list(MEANINGS),status='partial_semantic_dependency'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
