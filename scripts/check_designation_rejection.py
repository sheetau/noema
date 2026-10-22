"""Check policy discretion, naming and personal rejection as distinct relations."""
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
from scripts.compose_designation_rejection import ROOT,LIBRARY,BASIS,PATTERN,USE_CODE,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts import check_religious_freedom_policy as prior

INDEX=prior.INDEX;INVENTORY=prior.INVENTORY;REPORT='reports/designation-rejection-v1.json'
READING='data/designation-rejection-reading-v1.json';DOC='docs/designation-rejection-v1.md'
SOURCES=(*prior.SOURCES,*(f'artifacts/designation-rejection-v1/{n}' for n in ('dwb-ablehnen.html','dwb-toleranz.html','kant-aa06-465.html')))
PRIORS=('reports/religious-freedom-policy-v1.json','reports/self-report-dignity-v1.json')
DOMAIN=prior.DOMAIN;SCENES=prior.SCENES;z=prior.z
FNAMES=('source','role','group','community','topic','reference');FARGS=' '.join(z(n) for n in FNAMES)
DARGS=prior.DARGS;LABEL=z('work');USERS=z('other');ACTOR=z('actor');NOW=z('now');REF=z('reference')
CODE='k r5wu['+' '.join('r['+z(n)+']' for n in FNAMES)+']'
USE='k r5wz[r['+REF+']]'
TRIPLE='l[a]['+ACTOR+' '+LABEL+' '+USERS+']'
NORM=('source','actor','role',('r5wa',2),('actor','group','community','topic'),'reference')
identity=lambda code:(code.rank,code.syntax)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    prefix=parse('p:'+prior.EXTRA+prior.PROVIDERS+'r zsavepattern['+PATTERN+'] c.r zsaveuse['+USE_CODE+'] c.')
    replacements={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h','h246e')}
    d['declarations']=[x for x in prefix['declarations'] if x['name'] not in replacements]+[replacements.get(x['name'],x) for x in d['declarations']]
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def base(d,used=True,rejected=True,meaning=True):
    v=prior.base(d);saved={}
    v.update(zsavepattern=lambda code:saved.update(pattern=identity(code)) is None,zsaveuse=lambda code:saved.update(use=identity(code)) is None,
        h26ne=lambda *a:False,h26nj=lambda *a:normalized(a[:6])==NORM and a[-1]=='now',
        h26nk=lambda label,code,c,r:meaning and (label,identity(code),c,r)==('work',saved['pattern'],'community','reference'),
        h246c=lambda g,p,r:g in ('group','other') and p in ('person','otherperson') and r=='reference',
        dg=lambda event,point:point=='now' and (event=='event' or event=='otherwork' and used),
        f3=lambda p,event,point:(p,event,point)==('person','otherwork','now'),
        hzih=lambda event,label,subject,point:(event,label,subject,point)==('otherwork','work','actor','now'),
        h244j=lambda person,event,code,b,sign,point:rejected and (person,event,identity(code),normalized(b),sign,point)==('actor','event',saved['use'],('actor','work','other'),False,'now'))
    return v,saved

@lru_cache(None)
def discretion_checks():
    q='q[t[k r5wr['+DARGS+']]['+NOW+']].q[t[k r5w6['+DARGS+']]['+NOW+']].'
    d=fixture(('r5wr','r5w6'),q);rows=[]
    for reqpos,reqneg,allowpos,allowneg in product((False,True),repeat=4):
        v,_=base(d)
        v['h26ne']=lambda *a:normalized(a[:6])==NORM and a[-1]=='now' and (reqpos if a[-2] else reqneg)
        v['h26nj']=lambda *a:normalized(a[:6])==NORM and a[-1]=='now' and (allowpos if a[-2] else allowneg)
        got=run(d,v);assert got==[allowpos and allowneg and not reqpos and not reqneg,True]
        rows.append(dict(requirements=[reqpos,reqneg],permissions=[allowpos,allowneg],result=got))
    for pos in range(8):
        v,_=base(d)
        def mismatch(*a):
            want=[*NORM,a[-2],'now'];want[pos]='other';return normalized(a)==tuple(want)
        v['h26nj']=mismatch;assert run(d,v)==[False,True],pos
    for n in ('h26ne','h26nj'):
        v,_=base(d);v[n]=unknown;rejects(d,v)
    return dict(normative_combinations=rows,all_eight_permission_arguments_fixed=True,duty_excludes_choice_without_inference_to_rejection=True,unknown_rejected=True)

@lru_cache(None)
def pattern_checks():
    q='q[k zsavepattern['+CODE+']].q[t[c[s['+CODE+']]['+ACTOR+']]['+NOW+']].q[t[k r5ws['+DARGS+']]['+NOW+']].q[k r5wv['+LABEL+' '+FARGS+']].'
    d=fixture(('r5wu','r5ws','r5wv'),q);rows=[]
    for discretion,policy,meaning in product((False,True),repeat=3):
        v,_=base(d,meaning=meaning);v['h26nj']=lambda *a:discretion and normalized(a[:6])==NORM and a[-1]=='now';v['h245c']=lambda *a:policy
        got=run(d,v);assert got==[True,discretion and policy,discretion and policy,meaning],(discretion,policy,meaning,got)
        rows.append(dict(discretion=discretion,policy=policy,meaning=meaning,result=got[1:]))
    for n in ('h26nj','h245c','h26nk'):
        v,_=base(d);v[n]=unknown;rejects(d,v)
    return dict(all_eight_meaning_discretion_policy_combinations=rows,native_dequoted_pattern_matches_composition=True,quoted_meaning_is_nonfactive=True,unknown_rejected=True)

@lru_cache(None)
def naming_checks():
    q='q[t[k r5wx['+ACTOR+' '+LABEL+' '+USERS+' '+REF+']]['+NOW+']].'
    d=fixture(('r5wx',),q);rows={}
    for variant in ('baseline','no_occurrence','other_speaker','other_event','other_label','other_subject','other_point','empty_users','excluded_speaker'):
        v,_=base(d)
        if variant=='no_occurrence':v['dg']=lambda *a:False
        if variant=='other_speaker':v['f3']=lambda *a:a==('actor','otherwork','now')
        if variant=='excluded_speaker':v['h246c']=lambda g,p,r:(g,p,r)==('other','otherperson','reference')
        if variant=='empty_users':v['h246c']=lambda *a:False
        if variant in ('other_event','other_label','other_subject','other_point'):
            want=['otherwork','work','actor','now'];want[('other_event','other_label','other_subject','other_point').index(variant)]='other';v['hzih']=lambda *a:a==tuple(want)
        got=run(d,v);assert got==[variant=='baseline'],(variant,got);rows[variant]=got[0]
    for n in ('dg','f3','hzih','h246c'):
        v,_=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,same_use_presenter_label_subject_point=True,unknown_rejected=True)

@lru_cache(None)
def rejection_checks():
    q='q[k zsavepattern['+CODE+']].q[k zsaveuse['+USE+']].q[t[k r5w3['+ACTOR+' '+LABEL+' '+USERS+' '+REF+']]['+NOW+']].'
    q+='q[t[k r5w4['+ACTOR+' '+LABEL+' '+USERS+' '+FARGS+']]['+NOW+']].q[t[k r5wx['+ACTOR+' '+LABEL+' '+USERS+' '+REF+']]['+NOW+']].'
    d=fixture(('r5wu','r5wz','r5w3','r5w4','r5wx'),q);rows=[]
    for rejected,used,meaning in product((False,True),repeat=3):
        v,_=base(d,used,rejected,meaning);v['h26ne']=v['h26nj']=unknown
        got=run(d,v);assert got==[True,True,rejected,rejected and meaning,used],(rejected,used,meaning,got)
        rows.append(dict(rejected=rejected,used=used,meaning=meaning,result=got[2:]))
    # Stance needs an occurring action by this subject, not compliance by callers.
    for n,fn in (('dg',lambda event,point:(event,point)==('otherwork','now')),('df',lambda *a:False),('h246c',lambda *a:False)):
        v,_=base(d);v[n]=fn;got=run(d,v);assert got[2:4]==[False,False],(n,got)
    for pos in range(6):
        v,saved=base(d)
        def wrong(person,event,code,b,sign,point):
            want=['actor','event',saved['use'],('actor','work','other'),False,'now'];want[pos]='other'
            return (person,event,identity(code),normalized(b),sign,point)==tuple(want)
        v['h244j']=wrong;assert run(d,v)[2:4]==[False,False],pos
    for n in ('h244j','df','dg','h246c'):
        v,_=base(d);v[n]=unknown;rejects(d,v)
    return dict(eight_rejection_naming_meaning_combinations=rows,negative_stance_and_own_action_required=True,
        all_six_stance_arguments_fixed=True,no_utterance_or_actual_norm_required=True,unknown_rejected=True)

@lru_cache(None)
def binding_checks():
    q='q[t[c[s['+USE+']]['+TRIPLE+']]['+NOW+']].q[t[k r5wx['+ACTOR+' '+LABEL+' '+USERS+' '+REF+']]['+NOW+']].'
    d=fixture(('r5wz','r5wx'),q)
    for used in (False,True):v,_=base(d,used=used);assert run(d,v)==[used,used]
    # Exhaustive variable binding over two distinguishable values, with the
    # naming content replaced only at this separately tested boundary.
    d=fixture(('r5wy',),'q[t[c[k r5wy['+REF+']][k zbindings[]]]['+NOW+']].',('r5wx',))
    for pos in range(3):
        b=tuple('other' if i==pos else 'person' for i in range(3));v,_=base(d)
        v['r5wx']=lambda *a:Content(SCENES,tuple(a==(*b,'reference') and s=='now' for s in SCENES))
        v['zbindings']=lambda:SequenceValue(b,'"individual"');assert run(d,v,('person','other'))==[True]
        for bad in (('person',)*3,b[:-1],(*b,'person')):
            v['zbindings']=lambda:SequenceValue(bad,'"individual"');assert run(d,v,('person','other'))==[False],(pos,bad)
    q='q[k zsavepattern['+CODE+']].q[k zsaveuse['+USE+']].q[t[k r5w4['+ACTOR+' '+LABEL+' '+USERS+' '+FARGS+']]['+NOW+']].'
    d=fixture(('r5wu','r5wz','r5w4'),q)
    for name in FNAMES:
        v,_=base(d)
        if name=='reference':v['zrefpick']=lambda point,*codes:codes[2] if point=='reference' else codes[SCENES.index(point)]
        else:v['znamepick']=lambda item,*codes:codes[DOMAIN.index('other' if item==name else item)]
        assert run(d,v)==[True,True,False],name
    for n in ('zrefpick','znamepick'):
        v,_=base(d);v[n]=unknown;rejects(d,v)
    return dict(native_dequoted_naming_content=True,all_three_binding_positions_and_lengths=True,six_meaning_references_checked=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');start=u['text'].index('den hoch');end=u['text'].index(': ist selbst');last=u['text'].index('. ')+1
    return dict(status='designation_meaning_and_rejection_dependency_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        sentence_context=dict(range=[0,last],text=u['text'][:last]),interpretation=LIMITS,
        evidence=[dict(path=SOURCES[0],url='https://korpora.org/kant/aa08/040.html',observation='名称の自分への適用拒否と義務判断からのalsoを保持。名称の高慢評価は未接続。'),
            dict(path=SOURCES[1],observation='原刊491頁の同じ関係節。'),
            dict(path=SOURCES[2],url='https://www.dwds.de/wb/dwb/ablehnen',observation='提案・栄誉等を断る用法。発話の依頼という形に限定しない。'),
            dict(path=SOURCES[3],url='https://www.dwds.de/wb/dwb/toleranz',observation='宗教的許容や、寛容と承認との区別の例。今回の裁量的許容という文脈解釈の補助であり唯一の語義とはしない。'),
            dict(path=SOURCES[4],url='https://korpora.org/Kant/aa06/465.html',observation='後年の高慢説明は他者を低く扱う尊重の非対称を含む。旧草案の裁量資格の不足だけでは不足するため次の構成で扱う。')],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['名称・使用者集団・共同体を原文の一般的な君主の範囲へ固定','高慢な名称の評価・自らの強調・alsoの帰結提示','啓蒙・称賛・最初の政府側の解放・良心事項の自由','491–492頁の全一文と後続の通読判断'],
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
    try:parse(source.replace('r d[p r5wt]','r c[p r5wt]'))
    except (ValueError,TypeError):pass
    else:raise AssertionError('Insufficient quotation rank accepted')
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=112,
        preserved_whole_unit_reviews=17,new_verified_characters=0,compact_full_v2_roundtrips=True,quotation_rank_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('discretion',discretion_checks),('pattern',pattern_checks),('naming',naming_checks),('rejection',rejection_checks),('bindings',binding_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,*SOURCES,*PRIORS,
        'scripts/compose_designation_rejection.py','scripts/check_designation_rejection.py','tests/test_designation_rejection.py',
        'scripts/compose_religious_freedom_policy.py','scripts/compose_self_report_dignity.py','scripts/check_religious_freedom_policy.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='designation_meaning_and_practical_rejection_dependency_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
