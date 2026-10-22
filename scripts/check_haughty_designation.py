"""Check asymmetric respect, adopted naming and nonvacuous scoped appraisal."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_haughty_designation import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure,USE_CODE
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts import check_designation_rejection as prior

INDEX=prior.INDEX;INVENTORY=prior.INVENTORY;REPORT='reports/haughty-designation-v1.json'
READING='data/haughty-designation-reading-v1.json';DOC='docs/haughty-designation-v1.md'
LEXICAL='artifacts/haughty-designation-v1/dwb-hochmut.html'
SOURCES=(*prior.SOURCES,LEXICAL);PRIORS=('reports/designation-rejection-v1.json','reports/self-report-dignity-v1.json')
DOMAIN=prior.DOMAIN;SCENES=prior.SCENES;z=prior.z;FARGS=prior.FARGS;CODE=prior.CODE
ACTOR=z('actor');LABEL=z('work');REF=z('reference');NOW=z('now');POINT=z('otherpoint')
RESPECT='k r5xa[r['+REF+']]';TRIPLE='l[a]['+ACTOR+' '+z('person')+' '+z('community')+']'
PAIR=' '.join(z(n) for n in ('actor','person','event','source','role','community','reference','otherpoint'))
SAVE='q[k zsavepattern['+CODE+']].q[k zsaverespect['+RESPECT+']].'
APPRAISAL='k r5xg['+LABEL+' '+FARGS+' '+z('other')+' p zcases]'
identity=prior.identity
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    prefix=parse('p:'+prior.prior.EXTRA+prior.prior.PROVIDERS+'r zsavepattern['+prior.PATTERN+'] c.r zsaverespect['+USE_CODE+'] c.r zcases[d] c.')
    replacements={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h','h246e')}
    d['declarations']=[x for x in prefix['declarations'] if x['name'] not in replacements]+[replacements.get(x['name'],x) for x in d['declarations']]
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def base(d):
    v,saved=prior.base(d)
    v.update(zsaverespect=lambda code:saved.update(respect=identity(code)) is None,
        h246c=lambda group,p,r:r=='reference' and ((group=='group' and p in ('person','otherperson')) or (group=='other' and p=='actor')),
        dg=lambda event,point:(event,point)==('event','otherpoint'),
        f3=lambda p,event,point:(p,event,point)==('actor','event','otherpoint'),
        hzih=lambda event,label,p,point:(event,label,p,point)==('event','work','actor','otherpoint'),
        h26nm=lambda p,event,label,code,c,r,point:(p,event,label,identity(code),c,r,point)==('actor','event','work',saved['pattern'],'community','reference','otherpoint'),
        h244j=lambda p,event,code,b,sign,point:(p,event,identity(code),point)==('actor','event',saved['respect'],'otherpoint') and normalized(b)==(('person','actor','community') if sign else ('actor','person','community')),
        h7k=lambda source,p,office,code,b,sign,point:(source,p,office,identity(code),normalized(b),sign,point)==('source','actor','role',saved['respect'],('actor','person','community'),True,'otherpoint'),
        zcases=lambda point:point=='otherpoint')
    return v,saved

@lru_cache(None)
def reciprocity_checks():
    q='q[k zsaverespect['+RESPECT+']].q[k r5xb['+PAIR+']].q[k r5xc['+PAIR+']].'
    d=fixture(('r5xa','r5xb','r5xc'),q);rows=[]
    for expects,denies,required in product((False,True),repeat=3):
        v,saved=base(d);stance=v['h244j'];norm=v['h7k']
        v['h244j']=lambda *a:stance(*a) and (expects if a[-2] else denies);v['h7k']=lambda *a:norm(*a) and required
        got=run(d,v);assert got==[True,expects and denies,expects and denies and required]
        assert v['h26nl'] is unknown
        rows.append(dict(expects_respect=expects,denies_respect=denies,required=required,result=got[1:]))
    for pos in range(6):
        v,saved=base(d)
        def wrong(p,event,code,b,sign,point):
            want=['actor','event',saved['respect'],('person','actor','community') if sign else ('actor','person','community'),sign,'otherpoint'];want[pos]='other'
            return (p,event,identity(code),normalized(b),sign,point)==tuple(want)
        v['h244j']=wrong;assert run(d,v)==[True,False,False],pos
    for pos in range(7):
        v,saved=base(d)
        def wrongnorm(s,p,o,code,b,sign,point):
            want=['source','actor','role',saved['respect'],('actor','person','community'),True,'otherpoint'];want[pos]='other'
            return (s,p,o,identity(code),normalized(b),sign,point)==tuple(want)
        v['h7k']=wrongnorm;assert run(d,v)==[True,True,False],pos
    for name in ('h244j','h7k','aa','zrefpick'):
        v,_=base(d);v[name]=unknown;rejects(d,v)
    return dict(eight_stance_and_requirement_combinations=rows,same_reciprocal_content_with_reversed_bindings=True,
        all_stance_and_norm_arguments_fixed=True,actual_treatment_not_evaluated=True,unknown_rejected=True)

@lru_cache(None)
def content_checks():
    q='q[t[c[s['+RESPECT+']]['+TRIPLE+']]['+POINT+']].q[k h26nl['+ACTOR+' '+z('person')+' '+z('community')+' '+REF+' '+POINT+']].'
    d=fixture(('r5xa','h26nl'),q)
    for actual in (False,True):
        v,_=base(d);v['h26nl']=lambda *a:actual and a==('actor','person','community','reference','otherpoint');assert run(d,v)==[actual,actual]
    d=fixture(('r5w7',),'q[t[c[k r5w7['+REF+']][k zbindings[]]]['+POINT+']].')
    for pos in range(3):
        b=tuple('other' if i==pos else 'person' for i in range(3));v,_=base(d);v['h26nl']=lambda *a:a==(*b,'reference','otherpoint')
        v['zbindings']=lambda:SequenceValue(b,'"individual"');assert run(d,v,('person','other'))==[True]
        for bad in (('person',)*3,b[:-1],(*b,'person')):
            v['zbindings']=lambda:SequenceValue(bad,'"individual"');assert run(d,v,('person','other'))==[False],(pos,bad)
    v,_=base(d);v['zbindings']=lambda:SequenceValue(('person','other','person'),'"individual"');v['h26nl']=unknown;rejects(d,v)
    return dict(native_content_and_dequotation_agree=True,three_binding_positions_lengths_and_direction_checked=True,unknown_rejected=True)

@lru_cache(None)
def adoption_checks():
    q=SAVE+'q[k r5xd['+ACTOR+' '+z('event')+' '+LABEL+' '+FARGS+' '+POINT+']].'
    d=fixture(('r5wu','r5xa','r5xd'),q);rows={}
    for variant in ('baseline','unheld_meaning','no_occurrence','other_presenter','other_subject','mere_quotation','other_activity','other_label','other_pattern','other_community','other_reference','other_point'):
        v,saved=base(d)
        if variant=='unheld_meaning':v['h26nk']=lambda *a:False
        if variant=='no_occurrence':v['dg']=lambda *a:False
        if variant=='other_presenter':v['f3']=lambda *a:a==('person','event','otherpoint')
        if variant=='other_subject':v['hzih']=lambda *a:a==('event','work','person','otherpoint')
        if variant=='mere_quotation':v['h26nm']=lambda *a:False
        if variant in ('other_activity','other_label','other_pattern','other_community','other_reference','other_point'):
            at={'other_activity':1,'other_label':2,'other_pattern':3,'other_community':4,'other_reference':5,'other_point':6}[variant]
            def wrong(p,event,label,code,c,r,point):
                want=['actor','event','work',saved['pattern'],'community','reference','otherpoint'];want[at]='other'
                return (p,event,label,identity(code),c,r,point)==tuple(want)
            v['h26nm']=wrong
        got=run(d,v);assert got==[True,True,variant=='baseline'],(variant,got);rows[variant]=got[-1]
    for name in prior.FNAMES:
        v,_=base(d)
        if name=='reference':v['zrefpick']=lambda point,*codes:codes[2] if point=='reference' else codes[SCENES.index(point)]
        else:v['znamepick']=lambda item,*codes:codes[DOMAIN.index('other' if item==name else item)]
        assert run(d,v)==[True,True,False],name
    for n in ('h26nm','h26nk','dg','f3','hzih','znamepick'):
        v,_=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,all_six_pattern_references_fixed=True,own_adoption_distinct_from_naming_and_quoted_truth=True,unknown_rejected=True)

@lru_cache(None)
def appraisal_checks():
    q=SAVE+'q['+APPRAISAL+'].q[k r5xd['+ACTOR+' '+z('event')+' '+LABEL+' '+FARGS+' '+NOW+']].'
    d=fixture(('r5wu','r5xa','r5xg','r5xd'),q);rows={}
    for variant in ('baseline','empty_candidates','empty_cases','no_adopted_use','no_recipient','self_recipient','no_negative_stance','no_due_respect','other_use_disrespect'):
        v,saved=base(d)
        if variant in ('empty_candidates','no_recipient','self_recipient'):
            member=v['h246c']
            v['h246c']=lambda g,p,r:member(g,p,r) and g!=('other' if variant=='empty_candidates' else 'group') or variant=='self_recipient' and (g,p,r)==('group','actor','reference')
        if variant=='empty_cases':v['zcases']=lambda *a:False
        if variant=='no_adopted_use':v['h26nm']=lambda *a:False
        if variant=='no_negative_stance':
            stance=v['h244j'];v['h244j']=lambda *a:stance(*a) and a[-2]
        if variant=='no_due_respect':v['h7k']=lambda *a:False
        if variant=='other_use_disrespect':
            stance=v['h244j'];v['h244j']=lambda p,event,*a:stance(p,'event',*a) and event=='otherwork'
        got=run(d,v);assert got==[True,True,variant=='baseline',False],(variant,got);rows[variant]=got[2:]
    # A second selected adopted use lacks the negative stance. Keeping it
    # outside the fixed cases must not affect the first case; including it must.
    for selected in (False,True):
        v,saved=base(d);second=('otherwork','reference')
        v['dg']=lambda event,point:(event,point) in (('event','otherpoint'),second)
        v['f3']=lambda p,event,point:p=='actor' and v['dg'](event,point)
        v['hzih']=lambda event,label,p,point:(label,p)==('work','actor') and v['dg'](event,point)
        v['h26nm']=lambda p,event,label,code,c,r,point:(p,label,identity(code),c,r)==('actor','work',saved['pattern'],'community','reference') and v['dg'](event,point)
        v['zcases']=lambda point:point=='otherpoint' or selected and point=='reference'
        got=run(d,v);assert got==[True,True,not selected,False],(selected,got)
        rows['second_use_'+str(selected)]=got[2:]
    for n in ('h244j','h7k','h246c','zcases','h26nm'):
        v,_=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,nonempty_people_cases_and_adopted_use_required=True,all_selected_uses_checked=True,
        counterexample_rejected=True,current_use_not_required=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');start=u['text'].index('den hoch');end=u['text'].index(' von sich');last=u['text'].index('. ')+1
    return dict(status='haughty_designation_appraisal_dependency_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        sentence_context=dict(range=[0,last],text=u['text'][:last]),interpretation=LIMITS,
        evidence=[dict(path=SOURCES[0],url='https://korpora.org/kant/aa08/040.html',observation='hochmüthigenは名称を修飾し、本人はその名称を拒否する。'),
            dict(path=SOURCES[1],observation='原刊491頁の関係節の同じ修飾と拒否の対象。'),
            dict(path=SOURCES[3],url='https://www.dwds.de/wb/dwb/toleranz',observation='前回の寛容という呼称の文脈的読みを保持する。'),
            dict(path=SOURCES[4],url='https://korpora.org/Kant/aa06/465.html',observation='相手に自己を低く扱うよう求め、相手には同じ尊重を与えないという後年の説明を補助にする。'),
            dict(path=LEXICAL,url='https://www.dwds.de/wb/dwb/hochmut',observation='第二義は自己を上に置く傲慢な誇り。第一義の喜ばしい高揚や植物名とは区別する。')],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['名前・人物範囲・仮定場面・規範源と本文の固定','名称評価の著者帰属を一般的な君主の条件と区別','selbstとalso、自己報告と品位、啓蒙・称賛・解放・良心事項','491–492頁の一文全体と後続の通読'],
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
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=112,
        preserved_whole_unit_reviews=17,new_verified_characters=0,compact_full_v2_roundtrips=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('reciprocity',reciprocity_checks),('content',content_checks),('adoption',adoption_checks),('appraisal',appraisal_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,*SOURCES,*PRIORS,
        'scripts/compose_haughty_designation.py','scripts/check_haughty_designation.py','tests/test_haughty_designation.py',
        'scripts/compose_designation_rejection.py','scripts/check_designation_rejection.py','scripts/compose_self_report_dignity.py',
        'scripts/check_religious_freedom_policy.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/compose_protected_remarks.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='haughty_designation_through_scoped_asymmetric_respect_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
