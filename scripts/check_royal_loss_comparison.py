"""Check shared counterfactual baselines, strict wide gaps and all matched pairs."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_royal_loss_comparison import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,NAMES,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/royal-loss-comparison-v1.md';READING='data/royal-loss-comparison-reading-v1.json';REPORT='reports/royal-loss-comparison-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/royal-dignity-loss-v1.json','reports/royal-insight-reproof-v1.json','reports/royal-despotic-support-v1.json','reports/monarchical-religion-sentence-v1.json')
READINGS=('data/royal-dignity-loss-reading-v1.json','data/royal-insight-reproof-reading-v1.json','data/royal-despotic-support-reading-v1.json')
DOMAIN=('alpha','beta','gamma');SCENES=('reference','assessment','first','second','baseline','alternative','unpaired')
EXTRA=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))+'r zbindings[] j[a].'
A='k zalpha[]';B='k zbeta[]';C='k zgamma[]';R='k zreference[]';T='k zassessment[]';F='k zfirst[]';S='k zsecond[]'
TEN=('alpha','beta','gamma','beta','alpha','gamma','alpha','beta','gamma','beta')
TERMS=(A,B,C,B,A,C,A,B,C,B)

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(root,terms,boundaries=(),query=None):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,[root]),statements=[])
    return parse(format_graph(d,'compact')+EXTRA+(query or 'q[k '+root+'['+' '.join(terms)+']].'))
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def base(d,bindings=('alpha',)*10):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['zbindings']=lambda:SequenceValue(bindings,'"individual"')
    v['h26ip']=lambda a,r,l:(a,r)==('alpha','reference') and l in DOMAIN
    v['h26iq']=lambda a,r,h,l:(a,r)==('alpha','reference') and DOMAIN.index(h)>=DOMAIN.index(l)
    degrees={'first':'beta','second':'alpha','baseline':'gamma','alternative':'gamma','reference':'gamma','assessment':'gamma','unpaired':'beta'}
    v['h26ir']=lambda a,r,p,l:(a,r)==('alpha','reference') and l==degrees[p]
    v['h26is']=lambda act,a,r,p,b:(act,p) in (('beta','first'),('gamma','second')) and (a,r)==('alpha','reference') and b in ('baseline','alternative')
    v['h26it']=v['h26is']
    v['dg']=lambda act,p:(act,p) in (('beta','first'),('gamma','second'))
    v['h26jb']=lambda *a:a==('alpha','reference','beta','alpha')
    v['h26jc']=lambda *a:a==('beta','gamma','alpha','reference','assessment','first','second')
    v['h26io']=lambda *a:'alpha' if a==('alpha','beta','gamma','reference') else 'beta'
    v['h234f']=lambda o,c,p:(o,c)==('beta','gamma') and p in ('first','second')
    v['r2ui']=lambda a,o,c,p:(a,o,c)==('alpha','beta','gamma') and p in ('first','second')
    v['r5pc']=lambda *a:a[:7]==('alpha','gamma','beta','alpha','gamma','alpha','reference') and a[7] in ('first','second')
    v['r5pd']=lambda a,o,c,act,w,r,p:(a,o,c,w,r)==('alpha','beta','gamma','gamma','reference') and (act,p) in (('beta','first'),('gamma','second'))
    v['h26in']=lambda act,project,r,p:(project,r)==('alpha','reference') and (act,p) in (('beta','first'),('gamma','second'))
    v['r5pr']=lambda *a:a==('alpha','beta','alpha','reference','first')
    v['r5p5']=lambda *a:a==('alpha','gamma','beta','beta','reference')
    v['r5qb']=lambda *a:a==('alpha','beta','gamma','gamma','reference','second')
    v['r5qf']=lambda *a:a==('beta','alpha','gamma','beta','alpha','gamma','reference','second')
    v['r5qm']=lambda *a:a==(*TEN[:7],'beta','reference','first')
    v['r5qn']=lambda *a:a==(*TEN[:7],'gamma','beta','reference','second')
    v['r5ql']=lambda *a:a==('alpha','beta','gamma','beta','gamma','reference','assessment','first','second')
    return v
def unknown_rejected(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')
def mismatches(d,lengths,model=base):
    rows={}
    for name,length in lengths:
        for pos in range(length):
            v=model(d);old=v[name]
            def changed(*a,pos=pos,old=old):
                a=list(a);a[pos]='mismatch';return old(*a)
            v[name]=changed;actual=run(d,v);assert actual==[False],(name,pos,actual);rows[name+'_'+str(pos)]=False
    return rows

@lru_cache(None)
def baseline_checks():
    d=fixture('r5qi',(B,C,A,R,F,S));rows={}
    for variant in ('baseline','empty','first_only','second_only','one_shared_only','different_sets','wrong_aspect','wrong_reference','wrong_activity','wrong_point','unknown'):
        v=base(d);sets={'first':('baseline','alternative'),'second':('baseline','alternative')}
        if variant=='empty':sets={'first':(),'second':()}
        if variant=='first_only':sets['second']=()
        if variant=='second_only':sets['first']=()
        if variant=='one_shared_only':sets['second']=('baseline',)
        if variant=='different_sets':sets['second']=('assessment','unpaired')
        v['h26is']=lambda act,a,r,p,b:(act,p) in (('beta','first'),('gamma','second')) and (a,r)==('alpha','reference') and b in sets.get(p,())
        if variant=='wrong_aspect':v['zalpha']=lambda:'beta'
        if variant=='wrong_reference':v['zreference']=lambda:'unpaired'
        if variant=='wrong_activity':v['zgamma']=lambda:'alpha'
        if variant=='wrong_point':v['zsecond']=lambda:'unpaired'
        if variant=='unknown':v['h26is']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(native_nonempty_equal_full_counterfactual_ranges=rows,unknown_rejected=True)

@lru_cache(None)
def magnitude_checks():
    d=fixture('r5qj',(A,R,F,S));rows={}
    for variant in ('baseline','small_gap','same_degree','opposite_order','wide_claim_without_order','ambiguous_first','ambiguous_second','no_first_measurement','no_second_measurement','outside_scale','incomparable','other_aspect','other_reference','unknown'):
        v=base(d)
        if variant=='small_gap':v['h26jb']=lambda *a:False
        if variant in ('same_degree','opposite_order','wide_claim_without_order'):
            v['h26jb']=lambda *a:True
            v['h26ir']=lambda a,r,p,l:(a,r)==('alpha','reference') and l==('beta' if variant=='same_degree' else 'alpha' if p=='first' else 'gamma')
        if variant in ('ambiguous_first','ambiguous_second'):
            original=v['h26ir'];at='first' if variant=='ambiguous_first' else 'second'
            v['h26ir']=lambda a,r,p,l:original(a,r,p,l) or p==at and l=='gamma'
        if variant in ('no_first_measurement','no_second_measurement'):
            original=v['h26ir'];at='first' if variant=='no_first_measurement' else 'second';v['h26ir']=lambda a,r,p,l:p!=at and original(a,r,p,l)
        if variant=='outside_scale':v['h26ip']=lambda a,r,l:l!='alpha'
        if variant=='incomparable':v['h26iq']=lambda a,r,h,l:h==l
        if variant=='other_aspect':v['zalpha']=lambda:'beta'
        if variant=='other_reference':v['zreference']=lambda:'unpaired'
        if variant=='unknown':v['h26jb']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    contrasts=mismatches(d,(('h26jb',4),))
    return dict(native_unique_measurements_strict_order_and_wide_gap=rows,same_gap_values=contrasts,unknown_rejected=True)

@lru_cache(None)
def causal_comparison_checks():
    d=fixture('r5qk',(B,C,A,R,T,F,S));rows={}
    for variant in ('baseline','first_not_active','second_not_active','first_no_cause','second_no_cause','first_not_harmed','lower_endpoint_different_baseline','one_baseline_not_lower','not_registered','wrong_assessment','unknown'):
        v=base(d)
        if variant in ('first_not_active','second_not_active'):
            missing='first' if variant=='first_not_active' else 'second';v['dg']=lambda act,p:p!=missing and (act,p) in (('beta','first'),('gamma','second'))
        if variant in ('first_no_cause','second_no_cause'):
            missing='first' if variant=='first_no_cause' else 'second';old=v['h26it'];v['h26it']=lambda act,a,r,p,b:p!=missing and old(act,a,r,p,b)
        if variant=='first_not_harmed':
            v['h26jb']=lambda *a:True;v['h26ir']=lambda a,r,p,l:(a,r)==('alpha','reference') and l==('alpha' if p=='second' else 'gamma')
        if variant=='lower_endpoint_different_baseline':
            v['h26is']=lambda act,a,r,p,b:(a,r)==('alpha','reference') and ((act,p,b)==('beta','first','baseline') or (act,p,b)==('gamma','second','alternative'));v['h26it']=v['h26is']
            v['h26ir']=lambda a,r,p,l:(a,r)==('alpha','reference') and l==('gamma' if p=='baseline' else 'alpha' if p=='second' else 'beta')
        if variant=='one_baseline_not_lower':
            v['h26ir']=lambda a,r,p,l:(a,r)==('alpha','reference') and l==('beta' if p=='first' else 'alpha' if p in ('second','alternative') else 'gamma')
        if variant=='not_registered':v['h26jc']=lambda *a:False
        if variant=='wrong_assessment':v['zassessment']=lambda:'unpaired'
        if variant=='unknown':v['h26it']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(native_both_causal_losses_shared_baseline_and_greater_loss=rows,lower_endpoint_alone_insufficient=True,unknown_rejected=True)

def owned(d):
    v=base(d);v['r5qk']=lambda *a:a==('beta','gamma','alpha','reference','assessment','first','second');return v

@lru_cache(None)
def owner_checks():
    d=fixture('r5ql',(A,B,C,B,C,R,T,F,S),('r5qk','r2ui'));rows={}
    for variant in ('baseline','not_highest_first','not_highest_second','not_held_first','not_held_second','other_owner','other_office','other_community','other_reference','unknown'):
        v=owned(d)
        if variant in ('not_highest_first','not_highest_second'):
            p='first' if variant=='not_highest_first' else 'second';old=v['h234f'];v['h234f']=lambda *a:a[-1]!=p and old(*a)
        if variant in ('not_held_first','not_held_second'):
            p='first' if variant=='not_held_first' else 'second';old=v['r2ui'];v['r2ui']=lambda *a:a[-1]!=p and old(*a)
        if variant in ('other_owner','other_office','other_community','other_reference'):
            wanted=['alpha','beta','gamma','reference'];i={'other_owner':0,'other_office':1,'other_community':2,'other_reference':3}[variant];wanted[i]='unpaired' if i==3 else 'gamma' if i==0 else 'alpha'
            v['h26io']=lambda *a:'alpha' if a==tuple(wanted) else 'beta'
        if variant=='unknown':v['h26io']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    contrasts=mismatches(d,(('r5qk',7),),owned)
    return dict(same_person_held_office_community_aspect_in_both_cases=rows,exact_comparison_arguments=contrasts,boundaries=['r5qk','r2ui'],unknown_rejected=True)

@lru_cache(None)
def branch_checks():
    rows={};contrasts={}
    specs=(('r5qm',(*TERMS[:7],B,R,F),('r5pc','r5pd','r5pr'),(('r5pc',8),('r5pd',7),('r5pr',5),('h26in',4))),
        ('r5qn',(*TERMS[:7],C,B,R,S),('r5pc','r5pd','r5p5','r5qb','r5qf'),(('r5pc',8),('r5pd',7),('r5p5',5),('r5qb',6),('r5qf',8),('h26in',4))))
    for root,terms,boundaries,relations in specs:
        d=fixture(root,terms,boundaries)
        for missing in (None,*(n for n,length in relations)):
            v=base(d)
            if missing:v[missing]=lambda *a:False
            actual=run(d,v);assert actual==[missing is None],(root,missing,actual);rows[root+'_'+str(missing)]=actual[0]
        contrasts[root]=mismatches(d,relations)
        v=base(d);v[relations[-1][0]]=unknown;unknown_rejected(d,v)
    return dict(same_office_versions_of_existing_intervention_branches=rows,exact_participants_work_field_activity_and_point=contrasts,
        boundaries=['r5pc','r5pd','r5pr','r5p5','r5qb','r5qf'],reproof_not_a_selection_condition=True,unknown_rejected=True)

@lru_cache(None)
def profile_checks():
    d=fixture('r5qp',(*TERMS,R,T,F,S),('r5qm','r5qn','r5ql'));rows={}
    for missing in (None,'r5qm','r5qn','r5ql','h26jc'):
        v=base(d)
        if missing:v[missing]=lambda *a:False
        actual=run(d,v);assert actual==[missing is None];rows[missing or 'baseline']=actual[0]
    contrasts=mismatches(d,(('r5qm',10),('r5qn',11),('r5ql',9),('h26jc',7)))
    d=fixture('r5qq',(*TERMS,R,T),('r5qm','r5qn','r5ql'));profiles={}
    for variant in ('baseline','two_pairs','empty','one_wrong_branch','one_missing_loss','invalid_registered_pair','wrong_assessment','unknown'):
        v=base(d)
        if variant=='empty':v['h26jc']=lambda *a:False
        if variant in ('two_pairs','one_wrong_branch','one_missing_loss'):
            v['h26jc']=lambda *a:a[:6]==('beta','gamma','alpha','reference','assessment','first') and a[6] in ('second','alternative')
            if variant!='one_wrong_branch':v['r5qn']=lambda *a:a[:10]==(*TEN[:7],'gamma','beta','reference') and a[10] in ('second','alternative')
            if variant!='one_missing_loss':v['r5ql']=lambda *a:a[:8]==('alpha','beta','gamma','beta','gamma','reference','assessment','first') and a[8] in ('second','alternative')
        if variant=='invalid_registered_pair':
            v['h26jc']=lambda *a:a[:5]==('beta','gamma','alpha','reference','assessment') and a[5:] in (('first','second'),('unpaired','second'))
        if variant=='wrong_assessment':v['zassessment']=lambda:'unpaired'
        if variant=='unknown':v['r5ql']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant in ('baseline','two_pairs')],(variant,actual);profiles[variant]=actual[0]
    return dict(both_branches_and_same_comparison=rows,exact_arguments=contrasts,all_nonempty_registered_pairs=profiles,
        boundaries=['r5qm','r5qn','r5ql'],invalid_pairs_not_filtered_away=True,unknown_rejected=True)

@lru_cache(None)
def adapter_checks():
    d=fixture('r5qr',(),('r5qq',),query='q[t[k r5qr[k zbindings[] '+R+']]['+T+']].');positions=[]
    for pos in range(10):
        b=tuple('beta' if i==pos else 'alpha' for i in range(10));v=base(d,b);v['r5qq']=lambda *a:a==(*b,'reference','assessment')
        assert run(d,v,DOMAIN[:2])==[True];v['zbindings']=lambda:SequenceValue(('alpha',)*10,'"individual"');assert run(d,v,DOMAIN[:2])==[False];positions.append(pos)
    for variant in ('short','long','wrong_reference','wrong_assessment','unknown'):
        v=base(d);v['r5qq']=lambda *a:a==(*('alpha',)*10,'reference','assessment')
        if variant in ('short','long'):v['zbindings']=lambda:SequenceValue(('alpha',)*(9 if variant=='short' else 11),'"individual"')
        if variant=='wrong_reference':v['zreference']=lambda:'unpaired'
        if variant=='wrong_assessment':v['zassessment']=lambda:'unpaired'
        if variant=='unknown':v['r5qq']=unknown;unknown_rejected(d,v)
        else:assert run(d,v,DOMAIN[:2])==[False]
    return dict(all_ten_binding_positions=positions,wrong_lengths_reference_and_assessment_rejected=True,boundaries=['r5qq'],unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013');start=u['text'].index('sowohl wenn',3645);end=4155
    previous=read(READINGS[0])
    return dict(status='matched_royal_interventions_and_greater_dignity_loss_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        interpretation=LIMITS,primary_pages=previous['primary_pages'],new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/040.html',observation='同じ威厳への損傷についてsowohl/als auchが二側を結び、noch weit mehrが第二側を大きくする。両活動の現実の発生ではなく一般的な条件の叙述として読む。')],
        unresolved=['全仮定範囲と条件・帰結の接続','sowohl/als auch/noch/weitの談話提示','格言引用文言の提示と著者帰属','selbstの取り立て・würdigtの皮肉・so weitの程度提示','全文通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,*READINGS,*(x['path'] for x in previous['primary_pages']))})

@lru_cache(None)
def structure_checks():
    new=catalog();old={n:e for c in parents() for n,e in c.entries.items()}
    for n,e in new.entries.items():
        if n not in MEANINGS and n not in PRIMITIVES:assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja']
    assert len(parents()[3].document['statements'])==107 and not new.document['statements']
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
    for name,fn in (('baseline',baseline_checks),('magnitude',magnitude_checks),('causal_comparison',causal_comparison_checks),('owner',owner_checks),('branches',branch_checks),('profile',profile_checks),('adapter',adapter_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{READING,DOC,INVENTORY,*PRIORS,*READINGS,*(p['path'] for p in read(READING)['primary_pages']),
        'scripts/compose_royal_loss_comparison.py','scripts/check_royal_loss_comparison.py','tests/test_royal_loss_comparison.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='matched_royal_interventions_and_greater_dignity_loss_partial',**results,
        alignment=dict(**read(READING)['source'],document=LIBRARY,definitions=list(MEANINGS),status='partial_semantic_dependency'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
