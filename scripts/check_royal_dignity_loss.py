"""Check strict loss, causal baselines and shared office without false credit."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_royal_dignity_loss import ROOT,LIBRARY,BASIS,PARENTS,PRIMITIVES,MEANINGS,LIMITS,NAMES,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/royal-dignity-loss-v1.md';READING='data/royal-dignity-loss-reading-v1.json';REPORT='reports/royal-dignity-loss-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
LEXICAL=('artifacts/royal-dignity-loss-v1/adelung-abbruch.html','artifacts/royal-dignity-loss-v1/adelung-majestaet.html')
PRIORS=('reports/royal-writing-oversight-v1.json','reports/monarchical-religion-sentence-v1.json')
DOMAIN=('alpha','beta','gamma');SCENES=('reference','candidate','comparison','alternative','past')
EXTRA=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))+'r zbindings[] j[a].'
A='k zalpha[]';B='k zbeta[]';R='k zreference[]';P='k zcandidate[]'

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
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def base(d,bindings=('alpha',)*7):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['zbindings']=lambda:SequenceValue(bindings,'"individual"')
    v['h26ip']=lambda a,r,l:(a,r)==('alpha','reference') and l in DOMAIN
    v['h26iq']=lambda a,r,l,h:(a,r)==('alpha','reference') and DOMAIN.index(l)>=DOMAIN.index(h)
    values={'reference':'beta','candidate':'alpha','comparison':'beta','alternative':'gamma','past':'alpha'}
    v['h26ir']=lambda a,r,p,l:(a,r)==('alpha','reference') and values[p]==l
    v['h26is']=lambda act,a,r,p,c:(act,a,r,p)==('beta','alpha','reference','candidate') and c in ('comparison','alternative')
    v['h26it']=lambda act,a,r,p,c:(act,a,r,p)==('beta','alpha','reference','candidate') and c in ('comparison','alternative')
    v['dg']=lambda a,p:(a,p)==('beta','candidate')
    return v
def unknown_rejected(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def scale_checks():
    d=fixture(('r5pg',),'q[k r5pg['+A+' '+R+']].');rows={}
    for variant in ('baseline','empty','nonreflexive','incomparable','cycle','ties','other_aspect','other_reference','unknown'):
        v=base(d)
        if variant=='empty':v['h26ip']=lambda *a:False
        if variant=='nonreflexive':v['h26iq']=lambda a,r,l,h:DOMAIN.index(l)>DOMAIN.index(h)
        if variant=='incomparable':v['h26iq']=lambda a,r,l,h:l==h
        if variant=='cycle':v['h26iq']=lambda a,r,l,h:l==h or (l,h) in {('alpha','beta'),('beta','gamma'),('gamma','alpha')}
        if variant=='ties':v['h26iq']=lambda *a:True
        if variant=='other_aspect':v['zalpha']=lambda:'beta'
        if variant=='other_reference':v['zreference']=lambda:'past'
        if variant=='unknown':v['h26iq']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant in ('baseline','ties')],(variant,actual);rows[variant]=actual[0]
    return dict(native_nonempty_total_preorder=rows,unknown_rejected=True)

@lru_cache(None)
def measurement_checks():
    d=fixture(('r5pi',),'q[k r5pi['+A+' '+R+' '+P+' k zcomparison[]]].');rows={}
    for variant in ('baseline','same_degree','higher_actual','no_actual_measurement','no_comparison_measurement','ambiguous_actual','ambiguous_comparison','outside_scale','tied_distinct_values','other_aspect','other_reference','other_point','unknown'):
        v=base(d);values={'reference':'beta','candidate':'alpha','comparison':'beta','alternative':'gamma','past':'alpha'}
        if variant=='same_degree':values['candidate']='beta'
        if variant=='higher_actual':values['candidate']='gamma'
        if variant in ('no_actual_measurement','no_comparison_measurement'):values['candidate' if variant=='no_actual_measurement' else 'comparison']=None
        v['h26ir']=lambda a,r,p,l:(a,r)==('alpha','reference') and (l==values[p] or (variant=='ambiguous_actual' and p=='candidate' and l=='beta') or (variant=='ambiguous_comparison' and p=='comparison' and l=='gamma'))
        if variant=='outside_scale':v['h26ip']=lambda a,r,l:(a,r)==('alpha','reference') and l in ('alpha','gamma')
        if variant=='tied_distinct_values':v['h26iq']=lambda *a:True
        if variant=='other_aspect':v['zalpha']=lambda:'beta'
        if variant=='other_reference':v['zreference']=lambda:'past'
        if variant=='other_point':v['zcandidate']=lambda:'alternative'
        if variant=='unknown':v['h26ir']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(native_unique_measurement_and_strict_decrease=rows,native_r2cl=True,unknown_rejected=True)

@lru_cache(None)
def causal_checks():
    d=fixture(('r5pj',),'q[k r5pj['+B+' '+A+' '+R+' '+P+']].');rows={}
    for variant in ('baseline','no_activity','empty_comparisons','one_comparison_not_lower','one_causal_link_missing','mere_cooccurrence','other_activity','other_aspect','other_reference','other_point','other_comparison','rise_from_past_but_loss_against_baseline','unknown'):
        v=base(d)
        if variant=='no_activity':v['dg']=lambda *a:False
        if variant=='empty_comparisons':v['h26is']=lambda *a:False
        if variant=='one_comparison_not_lower':
            v['h26ir']=lambda a,r,p,l:(a,r)==('alpha','reference') and l==('beta' if p=='comparison' else 'alpha')
        if variant=='one_causal_link_missing':v['h26it']=lambda act,a,r,p,c:(act,a,r,p,c)==('beta','alpha','reference','candidate','comparison')
        if variant=='mere_cooccurrence':v['h26it']=lambda *a:False
        changes={'other_activity':(0,'alpha'),'other_aspect':(1,'beta'),'other_reference':(2,'past'),'other_point':(3,'past')}
        if variant in changes:
            wanted=['beta','alpha','reference','candidate'];i,value=changes[variant];wanted[i]=value
            v['h26it']=lambda *a:a[:4]==tuple(wanted) and a[4] in ('comparison','alternative')
        if variant=='other_comparison':v['h26it']=lambda *a:a==('beta','alpha','reference','candidate','past')
        if variant=='rise_from_past_but_loss_against_baseline':
            v['h26ir']=lambda a,r,p,l:(a,r)==('alpha','reference') and l==('alpha' if p=='past' else 'beta' if p=='candidate' else 'gamma')
        if variant=='unknown':v['h26it']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant in ('baseline','rise_from_past_but_loss_against_baseline')],(variant,actual);rows[variant]=actual[0]
    return dict(all_fixed_comparisons_and_same_causal_contribution=rows,past_decline_not_required=True,unknown_rejected=True)

@lru_cache(None)
def owner_checks():
    d=fixture(('r5pk',),'q[k r5pk['+' '.join((A,B,A,B,R,P))+']].',('r2ui','r5pj'));rows={}
    for variant in ('baseline','not_highest_office','different_holder','different_community','different_point','wrong_owner_aspect','wrong_office_aspect','wrong_community_aspect','wrong_aspect_reference','wrong_causal_activity','unknown'):
        v=base(d);v['h234f']=lambda *a:variant!='not_highest_office' and a==('beta','alpha','candidate')
        holder=['alpha','beta','alpha','candidate']
        changes={'different_holder':(0,'beta'),'different_community':(2,'beta'),'different_point':(3,'past')}
        if variant in changes:i,value=changes[variant];holder[i]=value
        v['r2ui']=lambda *a:a==tuple(holder)
        wanted=['alpha','beta','alpha','reference'];changes={'wrong_owner_aspect':(0,'beta'),'wrong_office_aspect':(1,'alpha'),'wrong_community_aspect':(2,'beta'),'wrong_aspect_reference':(3,'past')}
        if variant in changes:i,value=changes[variant];wanted[i]=value
        v['h26io']=lambda *a:'alpha' if a==tuple(wanted) else 'beta'
        v['r5pj']=lambda *a:a==('alpha' if variant=='wrong_causal_activity' else 'beta','alpha','reference','candidate')
        if variant=='unknown':v['h26io']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(same_ruler_office_community_aspect_and_activity=rows,boundaries=['r2ui','r5pj'],unknown_rejected=True)

@lru_cache(None)
def joining_checks():
    d=fixture(('r5pl',),'q[k r5pl['+' '.join((A,A,B,A,B,A,B,R,P))+']].',('r5pc','r5pd','r5pk'));rows={}
    for variant in ('baseline','separate_offices','other_work','other_project','other_regulation','other_person','other_reference','other_point','unknown'):
        v=base(d)
        v['r5pc']=lambda *a:a==('alpha','alpha','alpha' if variant=='other_person' else 'beta','alpha','beta','alpha','reference','candidate')
        v['r5pd']=lambda *a:a==('alpha','gamma','alpha','beta','alpha' if variant=='other_work' else 'beta','reference','candidate')
        wanted=['alpha','beta' if variant=='separate_offices' else 'gamma','alpha','beta','reference','candidate']
        if variant=='other_regulation':wanted[3]='alpha'
        if variant=='other_reference':wanted[4]='past'
        if variant=='other_point':wanted[5]='past'
        v['r5pk']=lambda *a:a==tuple(wanted)
        v['h26in']=lambda *a:a==('beta','beta' if variant=='other_project' else 'alpha','reference','candidate')
        if variant=='unknown':v['r5pk']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    d=fixture(('r5pm',),'q[t[k r5pm[k zbindings[] '+R+']]['+P+']].',('r5pl',));positions=[]
    for i in range(7):
        b=tuple('beta' if i==j else 'alpha' for j in range(7));v=base(d,b);v['r5pl']=lambda *a:a==(*b,'reference','candidate')
        assert run(d,v,DOMAIN[:2])==[True];v['zbindings']=lambda:SequenceValue(('alpha',)*7,'"individual"');assert run(d,v,DOMAIN[:2])==[False];positions.append(i)
    for variant in ('short','long','other_reference','other_point','unknown'):
        v=base(d);v['r5pl']=lambda *a:a==(*('alpha',)*7,'reference','candidate')
        if variant in ('short','long'):v['zbindings']=lambda:SequenceValue(('alpha',)*(6 if variant=='short' else 8),'"individual"')
        if variant=='other_reference':v['zreference']=lambda:'past'
        if variant=='other_point':v['zcandidate']=lambda:'past'
        if variant=='unknown':v['r5pl']=unknown;unknown_rejected(d,v)
        else:assert run(d,v,DOMAIN[:2])==[False]
    return dict(shared_office_oversight_and_loss=rows,all_seven_adapter_positions=positions,boundaries=['r5pc','r5pd','r5pk','r5pl'],unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013')
    fragment='Es thut selbst seiner Majestät Abbruch';start=u['text'].index(fragment,3645);end=start+len(fragment)
    previous=read('data/royal-writing-oversight-reading-v1.json')
    return dict(status='same_ruler_public_dignity_causal_loss_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=fragment),
        interpretation=LIMITS,primary_pages=previous['primary_pages'],new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/040.html',lines='9–16',observation='威厳への損傷を、直後の同じ君主の著作監督に結び、二種類の介入比較へ備える。'),
          dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009131_3_0_116',path=LEXICAL[0],observation='名望・権利・威厳等の減損という比喩用法を確認。全喪失や永久性にしない。'),
          dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009133_1_0_180',path=LEXICAL[1],observation='最高の権力と地位、外に示される威厳、人物の敬称を区別して読む。ここでは最高職の公的な威厳を採る。')],
        unresolved=['selbstの取り立て','würdigtの皮肉的な描写','自己の最高の見識に基づく介入と批判への曝露','Caesar non est supra Grammaticosの引用と内容','最高権力を一部の聖職者の専制支援へ落とす場合と残余臣民','同じ比較基準での二側とnoch weit mehr','全仮定範囲と条件・手段説明・著者帰属・全文通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*LEXICAL,*PRIORS,'data/royal-writing-oversight-reading-v1.json',*(x['path'] for x in previous['primary_pages']))})

@lru_cache(None)
def structure_checks():
    new=catalog();old={n:e for c in parents() for n,e in c.entries.items()}
    for n,e in new.entries.items():
        if n not in MEANINGS and n not in PRIMITIVES:assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja']
    assert len(parents()[1].document['statements'])==107 and not new.document['statements']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        s=format_graph(new.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==new.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_unchanged=True,main_statements_unchanged=107,roundtrips=True,verified_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('scale',scale_checks),('measurement',measurement_checks),('causal',causal_checks),('owner',owner_checks),('joining',joining_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{READING,DOC,INVENTORY,*LEXICAL,*PRIORS,*(p['path'] for p in read(READING)['primary_pages']),
        'data/royal-writing-oversight-reading-v1.json','scripts/compose_royal_dignity_loss.py','scripts/check_royal_dignity_loss.py','tests/test_royal_dignity_loss.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='same_ruler_public_dignity_causal_loss_partial',**results,
        alignment=dict(**read(READING)['source'],document=LIBRARY,definitions=list(MEANINGS),status='partial_semantic_dependency'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
