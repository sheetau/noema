"""Check plural tyrants, remaining subjects and use of the same supreme office."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_royal_despotic_support import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,NAMES,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/royal-despotic-support-v1.md';READING='data/royal-despotic-support-reading-v1.json';REPORT='reports/royal-despotic-support-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
LEXICAL=('artifacts/royal-despotic-support-v1/adelung-erniedrigen.html','artifacts/royal-despotic-support-v1/adelung-unterstuetzen.html')
PRIORS=('reports/royal-writing-oversight-v1.json','reports/monarchical-religion-sentence-v1.json','reports/political-withdrawal-v1.json')
DOMAIN=('alpha','beta','gamma','delta','epsilon');SCENES=('reference','candidate','other')
EXTRA=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))+'r zbindings[] j[a].'
A='k zalpha[]';B='k zbeta[]';C='k zgamma[]';D='k zdelta[]';E='k zepsilon[]';R='k zreference[]';P='k zcandidate[]'

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
def base(d,bindings=('alpha',)*8):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['zbindings']=lambda:SequenceValue(bindings,'"individual"')
    v['mp']=lambda g:SequenceValue(('alpha','beta') if g=='epsilon' else (),'"individual"')
    v['aa']=lambda x:True
    v['r5ni']=lambda a,t,c,r:(a,c,r)==('epsilon','epsilon','reference') and t in DOMAIN[:4]
    v['h226i']=lambda t,o,p:t==o and o in ('alpha','beta') and p=='candidate'
    v['h226j']=v['h226i']
    v['h26g7']=lambda f,c,r:(f,c,r)==('epsilon','epsilon','reference')
    v['h26i3']=lambda o,f,c,r,p:o in ('alpha','beta') and (f,c,r,p)==('epsilon','epsilon','reference','candidate')
    v['h26i4']=lambda act,o,r,p:o in ('alpha','beta') and (act,r,p)==('epsilon','reference','candidate')
    v['h26i6']=lambda o,t,r,p:(o,t) in (('alpha','gamma'),('beta','delta')) and (r,p)==('reference','candidate')
    v['r2uj']=lambda *a:a==('epsilon','epsilon','candidate')
    v['h234f']=lambda *a:a==('gamma','epsilon','candidate')
    v['r2ui']=lambda *a:a==('epsilon','gamma','epsilon','candidate')
    v['dg']=lambda *a:a==('epsilon','candidate')
    v['df']=lambda *a:a==('epsilon','epsilon','candidate')
    v['h26i5']=lambda *a:a==('epsilon','gamma','reference','candidate')
    v['h26i7']=lambda act,office,o,r,p:o in ('alpha','beta') and (act,office,r,p)==('epsilon','gamma','reference','candidate')
    v['h26ja']=lambda office,o,c,r,p:o in ('alpha','beta') and (office,c,r,p)==('gamma','epsilon','reference','candidate')
    v['r5pc']=lambda *a:a==('epsilon','epsilon','gamma','delta','beta','epsilon','reference','candidate')
    v['r5pd']=lambda *a:a==('epsilon','gamma','epsilon','epsilon','beta','reference','candidate')
    v['h26in']=lambda *a:a==('epsilon','delta','reference','candidate')
    return v
def unknown_rejected(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')
def mismatches(d,lengths):
    rows={}
    for name,length in lengths:
        for pos in range(length):
            v=base(d);old=v[name]
            def changed(*a,pos=pos,old=old):
                a=list(a);a[pos]='mismatch';return old(*a)
            v[name]=changed;actual=run(d,v);assert actual==[False],(name,pos,actual);rows[name+'_'+str(pos)]=False
    return rows

@lru_cache(None)
def population_checks():
    d=fixture('r5p4',(E,E,E,R),('r5ni',));rows={}
    for variant in ('baseline','empty','one','duplicate_one','duplicate_two','three','nonperson','one_outside_subjects','no_remaining','other_ruler','other_community','other_reference','unknown'):
        v=base(d)
        groups={'empty':(),'one':('alpha',),'duplicate_one':('alpha','alpha'),'duplicate_two':('alpha','beta','beta'),'three':('alpha','beta','gamma')}
        if variant in groups:v['mp']=lambda g:SequenceValue(groups[variant],'"individual"')
        if variant=='nonperson':v['aa']=lambda p:p!='beta'
        if variant=='one_outside_subjects':v['r5ni']=lambda a,t,c,r:t in ('alpha','gamma','delta')
        if variant=='no_remaining':v['r5ni']=lambda a,t,c,r:t in ('alpha','beta')
        if variant in ('other_ruler','other_community','other_reference'):
            wanted=['epsilon','epsilon','reference'];wanted[{'other_ruler':0,'other_community':1,'other_reference':2}[variant]]='other' if variant=='other_reference' else 'delta'
            v['r5ni']=lambda a,t,c,r:(a,c,r)==tuple(wanted) and t in DOMAIN[:4]
        if variant=='unknown':v['mp']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant in ('baseline','duplicate_two','three')],(variant,actual);rows[variant]=actual[0]
    d=fixture('r5p5',(E,E,E,C,R),('r5ni',));residual={}
    for target in DOMAIN:
        v=base(d);v['zgamma']=lambda:target;actual=run(d,v);assert actual==[target in ('gamma','delta')];residual[target]=actual[0]
    return dict(plural_subject_subset_and_nonempty_remainder=rows,exact_set_difference=residual,boundaries=['r5ni'],unknown_rejected=True)

@lru_cache(None)
def despotism_checks():
    d=fixture('r5p6',(A,A,E,E,R,P));rows={}
    for missing in (None,'aa','h226i','h226j','h26g7','h26i3'):
        v=base(d)
        if missing:v[missing]=lambda *a:False
        actual=run(d,v);assert actual==[missing is None],(missing,actual);rows[missing or 'baseline']=actual[0]
    contrasts=mismatches(d,(('h226i',3),('h226j',3),('h26g7',3),('h26i3',5)))
    assert 'sp' not in {x['name'] for x in d['declarations']}
    for n in ('h226i','h226j','h26i3'):
        v=base(d);v[n]=unknown;unknown_rejected(d,v)
    return dict(native_arbitrary_personal_control_in_same_religious_domain=rows,exact_arguments=contrasts,
        formal_clerical_appointment_not_added=True,native_r2qa=True,unknown_rejected=True)

@lru_cache(None)
def support_checks():
    d=fixture('r5qa',(E,E,E,E,E,R,P),('r5ni',));rows={}
    for variant in ('baseline','no_support','only_first_supported','second_not_despotic','one_remaining_not_targeted','only_tyrants_targeted','foreign_order','split_control_and_support','same_order','unknown'):
        v=base(d)
        if variant=='no_support':v['h26i4']=lambda *a:False
        if variant=='only_first_supported':v['h26i4']=lambda act,o,r,p:o=='alpha'
        if variant=='second_not_despotic':v['h226j']=lambda t,o,p:t==o=='alpha'
        if variant=='one_remaining_not_targeted':v['h26i6']=lambda o,t,r,p:(o,t)==('alpha','gamma')
        if variant=='only_tyrants_targeted':v['h26i6']=lambda o,t,r,p:t in ('alpha','beta')
        if variant=='foreign_order':v['h26i3']=lambda o,f,c,r,p:c=='delta'
        if variant=='split_control_and_support':v['h26i4']=lambda act,o,r,p:o=='gamma'
        if variant=='same_order':
            v['h226i']=lambda t,o,p:t in ('alpha','beta') and (o,p)==('alpha','candidate');v['h226j']=v['h226i']
            v['h26i6']=lambda o,t,r,p:o=='alpha' and t in ('gamma','delta') and (r,p)==('reference','candidate')
        if variant=='unknown':v['h26i4']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant in ('baseline','same_order')],(variant,actual);rows[variant]=actual[0]
    single=fixture('r5p7',(E,E,E,E,E,A,A,R,P),('r5ni',))
    contrasts=mismatches(single,(('h26i4',4),('h26i6',4)))
    return dict(native_all_tyrants_and_all_remaining_subjects=rows,exact_support_and_target=contrasts,
        different_orders_and_targets_allowed=True,successful_subjection_not_required=True,boundaries=['r5ni'],unknown_rejected=True)

@lru_cache(None)
def power_checks():
    d=fixture('r5qb',(E,C,E,E,R,P),('r2uj','r2ui'));rows={}
    for missing in (None,'r2uj','h234f','r2ui','dg','df','h26i5'):
        v=base(d)
        if missing:v[missing]=lambda *a:False
        actual=run(d,v);assert actual==[missing is None];rows[missing or 'baseline']=actual[0]
    contrasts=mismatches(d,(('h234f',3),('r2ui',4),('df',3),('h26i5',4)))
    v=base(d);v['h26i5']=unknown;unknown_rejected(d,v)
    return dict(same_held_supreme_office_act_and_power_use=rows,exact_arguments=contrasts,boundaries=['r2uj','r2ui'],unknown_rejected=True)

@lru_cache(None)
def degradation_checks():
    d=fixture('r5qd',(C,A,E,E,R,P));rows={}
    for missing in (None,'h26i7','h26ja'):
        v=base(d)
        if missing:v[missing]=lambda *a:False
        actual=run(d,v);assert actual==[missing is None];rows[missing or 'baseline']=actual[0]
    contrasts=mismatches(d,(('h26i7',5),('h26ja',5)))
    d=fixture('r5qf',(C,E,E,E,E,E,R,P),('r5ni',));collective={}
    for variant in ('baseline','one_instrumental_use_missing','one_unworthy_use_missing','other_office','other_activity','other_order','other_community','other_reference','other_point','support_and_degradation_split','unknown'):
        v=base(d)
        if variant=='one_instrumental_use_missing':v['h26i7']=lambda a,o,order,r,p:order=='alpha'
        if variant=='one_unworthy_use_missing':v['h26ja']=lambda o,order,c,r,p:order=='alpha'
        if variant in ('other_office','other_activity','other_order','other_reference','other_point'):
            wanted=['epsilon','gamma',None,'reference','candidate'];i={'other_activity':0,'other_office':1,'other_order':2,'other_reference':3,'other_point':4}[variant]
            wanted[i]='other' if i>=3 else 'delta'
            v['h26i7']=lambda *a:all(y is None or x==y for x,y in zip(a,wanted))
        if variant=='other_community':v['h26ja']=lambda o,order,c,r,p:c=='delta'
        if variant=='support_and_degradation_split':
            v['h26i4']=lambda a,o,r,p:o=='alpha';v['h26i7']=lambda a,o,order,r,p:order=='beta'
        if variant=='unknown':v['h26ja']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);collective[variant]=actual[0]
    return dict(actual_instrumental_use_and_incompatible_public_standing=rows,exact_arguments=contrasts,
        all_same_support_witnesses=collective,boundaries=['r5ni'],no_physical_power_loss_or_legal_transfer_added=True,unknown_rejected=True)

@lru_cache(None)
def joining_checks():
    terms=(E,E,C,D,B,E,E,E,R,P);boundaries=('r5pc','r5pd','r5ni','r2uj','r2ui')
    d=fixture('r5qg',terms,boundaries);rows={}
    for variant in ('baseline','not_remaining_writer','other_work','other_project','other_regulation','other_field','other_reference','other_point','different_offices','appropriate_support','unknown'):
        v=base(d)
        if variant=='not_remaining_writer':
            v['zgamma']=lambda:'alpha';v['r5pc']=lambda *a:a==('epsilon','epsilon','alpha','delta','beta','epsilon','reference','candidate')
        if variant=='other_work':v['r5pd']=lambda *a:a==('epsilon','gamma','epsilon','epsilon','alpha','reference','candidate')
        if variant=='other_project':v['h26in']=lambda *a:a==('epsilon','alpha','reference','candidate')
        if variant=='other_regulation':v['h26in']=lambda *a:a==('alpha','delta','reference','candidate')
        if variant=='other_field':v['h26g7']=lambda *a:a==('delta','epsilon','reference')
        if variant=='other_reference':v['zreference']=lambda:'other'
        if variant=='other_point':v['zcandidate']=lambda:'other'
        if variant=='different_offices':
            v['h234f']=lambda o,c,p:o in ('gamma','delta') and (c,p)==('epsilon','candidate')
            v['r2ui']=lambda a,o,c,p:o in ('gamma','delta') and (a,c,p)==('epsilon','epsilon','candidate')
            v['h26i5']=lambda a,o,r,p:o in ('gamma','delta') and (a,r,p)==('epsilon','reference','candidate')
            v['h26i7']=lambda a,o,order,r,p:order in ('alpha','beta') and (a,o,r,p)==('epsilon','delta','reference','candidate')
            v['h26ja']=lambda o,order,c,r,p:order in ('alpha','beta') and (o,c,r,p)==('delta','epsilon','reference','candidate')
        if variant=='appropriate_support':v['h26ja']=lambda *a:False
        if variant=='unknown':v['h26i7']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    intermediate=fixture('r5qc',terms,boundaries);v=base(intermediate);v['h26ja']=lambda *a:False;assert run(intermediate,v)==[True]
    d=fixture('r5qh',(),('r5qg',),query='q[t[k r5qh[k zbindings[] '+R+']]['+P+']].');positions=[]
    for pos in range(8):
        b=tuple('beta' if i==pos else 'alpha' for i in range(8));v=base(d,b);v['r5qg']=lambda *a:a==(*b,'reference','candidate')
        assert run(d,v,DOMAIN[:2])==[True];v['zbindings']=lambda:SequenceValue(('alpha',)*8,'"individual"');assert run(d,v,DOMAIN[:2])==[False];positions.append(pos)
    for bad in (7,9):
        v['zbindings']=lambda:SequenceValue(('alpha',)*bad,'"individual"');assert run(d,v,DOMAIN[:2])==[False]
    v=base(d);v['r5qg']=unknown;unknown_rejected(d,v)
    return dict(same_writer_project_work_regulation_and_office=rows,appropriate_support_not_degradation=True,
        all_eight_binding_positions=positions,wrong_lengths_rejected=True,boundaries=[*boundaries,'r5qg'],unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013')
    fragment='wenn er seine oberste Gewalt so weit erniedrigt, den geistlichen Despotism einiger Tyrannen in seinem Staate gegen seine übrigen Unterthanen zu unterstützen.'
    start=u['text'].index(fragment,3645);previous=read('data/royal-writing-oversight-reading-v1.json')
    return dict(status='royal_power_used_for_spiritual_despotism_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,start+len(fragment)],text=fragment),
        interpretation=LIMITS,primary_pages=previous['primary_pages'],new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/040.html',observation='geistlichenはDespotismを修飾する。最高権力・国家・残余臣民・支援を同じ君主の介入に結ぶ。'),
          dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009131_7_1_1973',path=LEXICAL[0],observation='erniedrigenの比喩的な品位に反する行為の語義。物理的な力や法的地位の喪失に限定しない。'),
          dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_4_1_1272',path=LEXICAL[1],observation='unterstützenの種々の援助、意図又は作用を促進する語義。特定の手段に限定せず実際の支えを構成する。')],
        unresolved=['二側の同一基準での損傷比較とnoch weit mehr','全仮定範囲と威厳損傷への条件接続','格言引用文言の提示と著者帰属','selbstの取り立て・würdigtの皮肉・so weitの程度提示','全文通読'],
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
    for name,fn in (('population',population_checks),('despotism',despotism_checks),('support',support_checks),('power',power_checks),('degradation',degradation_checks),('joining',joining_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{READING,DOC,INVENTORY,*LEXICAL,*PRIORS,*(p['path'] for p in read(READING)['primary_pages']),
        'data/royal-writing-oversight-reading-v1.json','scripts/compose_royal_despotic_support.py','scripts/check_royal_despotic_support.py','tests/test_royal_despotic_support.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='royal_power_used_for_spiritual_despotism_partial',**results,
        alignment=dict(**read(READING)['source'],document=LIBRARY,definitions=list(MEANINGS),status='partial_semantic_dependency'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
