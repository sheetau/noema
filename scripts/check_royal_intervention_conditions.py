"""Check independent conditionals, exact case binding and universal scope."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_royal_intervention_conditions import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,NAMES,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

DOC='docs/royal-intervention-conditions-v1.md';READING='data/royal-intervention-conditions-reading-v1.json';REPORT='reports/royal-intervention-conditions-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/royal-loss-comparison-v1.json','reports/royal-insight-reproof-v1.json','reports/royal-dignity-loss-v1.json','reports/monarchical-religion-sentence-v1.json')
DOMAIN=('alpha','beta');SCENES=('reference','case','first','second','outside')
TEN=('alpha','beta','alpha','beta','alpha','beta','alpha','beta','alpha','beta')
EXTRA=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))+'r zbindings[] j[a].'
A='k zalpha[]';B='k zbeta[]';R='k zreference[]';P='k zcase[]';TERMS=(A,B,A,B,A,B,A,B,A,B)
BOUNDARIES=('r5qt','r5qm','r5qn','r5pk','r5py','r5qq')

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
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def base(d,bindings=TEN):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['zbindings']=lambda:SequenceValue(bindings,'"individual"')
    v['h26jd']=lambda b,r,c:normalized((b,r,c))==(TEN,'reference','case')
    v['r2uj']=lambda *a:a==('alpha','alpha','case')
    v['h234f']=lambda *a:a==('beta','alpha','case')
    v['r2ui']=lambda *a:a==('alpha','beta','alpha','case')
    v['r5pc']=lambda *a:a==('alpha','alpha','beta','alpha','beta','alpha','case','case')
    v['r5pd']=lambda *a:a==('alpha','beta','alpha','beta','beta','case','case')
    v['h26in']=lambda *a:a==('beta','alpha','case','case')
    v['r5qt']=lambda *a:a==(*TEN[:7],'beta','case','case')
    v['r5qm']=v['r5qt']
    v['r5qn']=lambda *a:a==(*TEN[:7],'alpha','beta','case','case')
    v['r5pk']=lambda a,o,c,act,r,p:(a,o,c,r,p)==('alpha','beta','alpha','case','case') and act in DOMAIN
    v['r5py']=lambda *a:a==('alpha','alpha','alpha','beta','case','case')
    v['h26io']=lambda *a:'alpha' if a==('alpha','beta','alpha','case') else 'beta'
    v['h26jc']=lambda *a:a==('beta','alpha','alpha','case','case','first','second')
    v['r5qq']=lambda *a:a==(*TEN,'case','case')
    v['r5qy']=lambda *a:a==(*TEN,'reference','case')
    v['r5qs']=v['r5qy']
    return v
def unknown_rejected(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def scope_checks():
    d=fixture('r5qs',(*TERMS,R,P),('r2uj','r2ui'));rows={}
    for missing in (None,'h26jd','r2uj','h234f','r2ui'):
        v=base(d)
        if missing:v[missing]=lambda *a:False
        actual=run(d,v);assert actual==[missing is None];rows[missing or 'baseline']=actual[0]
    for pos in range(10):
        terms=list(TERMS);terms[pos]=B if terms[pos]==A else A
        changed=fixture('r5qs',(*terms,R,P),('r2uj','r2ui'));assert run(changed,base(changed))==[False]
    for n in ('zreference','zcase'):
        v=base(d);v[n]=lambda:'outside';assert run(d,v)==[False]
    v=base(d);v['h26jd']=unknown;unknown_rejected(d,v)
    return dict(unfiltered_hypothetical_frame_and_same_held_office=rows,all_ten_scope_positions=True,
        reference_and_case_separated=True,boundaries=['r2uj','r2ui'],unknown_rejected=True)

@lru_cache(None)
def base_intervention_checks():
    d=fixture('r5qt',(*TERMS[:7],B,P,P),('r5pc','r5pd'));rows={}
    for missing in (None,'r5pc','r5pd','h26in'):
        v=base(d)
        if missing:v[missing]=lambda *a:False
        actual=run(d,v);assert actual==[missing is None];rows[missing or 'baseline']=actual[0]
    contrasts={}
    for name,length in (('r5pc',8),('r5pd',7),('h26in',4)):
        for pos in range(length):
            v=base(d);old=v[name]
            def changed(*a,pos=pos,old=old):
                a=list(a);a[pos]='mismatch';return old(*a)
            v[name]=changed;assert run(d,v)==[False];contrasts[name+'_'+str(pos)]=False
    v=base(d);v['h26in']=unknown;unknown_rejected(d,v)
    return dict(same_work_inquiry_office_and_intervention=rows,exact_arguments=contrasts,boundaries=['r5pc','r5pd'],unknown_rejected=True)

@lru_cache(None)
def conditional_checks():
    results={}
    specs=(('r5qu','r5qt',('r5pk',)),('r5qv','r5qm',('r5pk','r5py')),('r5qw','r5qn',('r5pk',)),('r5qx','h26jc',('r5qq',)))
    for root,antecedent,consequents in specs:
        d=fixture(root,(*TERMS,R,P),BOUNDARIES);rows=[]
        for bits in product((False,True),repeat=1+len(consequents)):
            v=base(d);old=v[antecedent];v[antecedent]=lambda *a:bits[0] and old(*a)
            for i,n in enumerate(consequents,1):
                original=v[n];v[n]=lambda *a,on=bits[i],original=original:on and original(*a)
            actual=run(d,v);expected=not bits[0] or all(bits[1:]);assert actual==[expected],(root,bits,actual)
            rows.append(dict(bits=bits,value=actual[0]))
        v=base(d);v[consequents[-1]]=unknown;unknown_rejected(d,v)
        results[root]=rows
    # Record the actual arguments crossing independently checked boundaries.
    d=fixture('r5qy',(*TERMS,R,P),BOUNDARIES);v=base(d);calls={}
    for n in (*BOUNDARIES,'h26jc','h26io'):
        if n not in {x['name'] for x in d['declarations'] if x['kind']=='primitive'}:continue
        original=v[n];calls[n]=set()
        def record(*a,n=n,original=original):calls[n].add(a);return original(*a)
        v[n]=record
    assert run(d,v)==[True]
    expected={'r5qt':{(*TEN[:7],'beta','case','case')},'r5qm':{(*TEN[:7],'beta','case','case')},
        'r5qn':{(*TEN[:7],'alpha','beta','case','case')},
        'r5pk':{('alpha','beta','alpha',act,'case','case') for act in DOMAIN},
        'r5py':{('alpha','alpha','alpha','beta','case','case')},'r5qq':{(*TEN,'case','case')},
        'h26io':{('alpha','beta','alpha','case')}}
    for n,values in expected.items():assert calls[n]==values,(n,calls[n],values)
    assert calls['h26jc'] and all(a[:5]==('beta','alpha','alpha','case','case') for a in calls['h26jc'])
    return dict(truth_tables=results,exact_inner_case_calls={n:[list(a) for a in sorted(values)] for n,values in expected.items()},
        comparison_range_uses_same_case_and_assessment=True,boundaries=list(BOUNDARIES),unknown_rejected=True)

@lru_cache(None)
def independent_consequences_checks():
    d=fixture('r5qy',(*TERMS,R,P),BOUNDARIES);rows={}
    for variant in ('all','none','basic_only','basic_only_no_loss','own_without_reproof','support_only','support_only_no_loss','comparison_only','comparison_without_result'):
        v=base(d)
        if variant=='none':
            for n in (*BOUNDARIES,'h26jc'):v[n]=lambda *a:False
        if variant in ('basic_only','basic_only_no_loss'):
            for n in ('r5qm','r5qn','h26jc','r5py','r5qq'):v[n]=lambda *a:False
            if variant=='basic_only_no_loss':v['r5pk']=lambda *a:False
        if variant=='own_without_reproof':v['r5py']=lambda *a:False
        if variant in ('support_only','support_only_no_loss'):
            for n in ('r5qt','r5qm','h26jc','r5py','r5qq'):v[n]=lambda *a:False
            if variant=='support_only_no_loss':v['r5pk']=lambda *a:False
        if variant in ('comparison_only','comparison_without_result'):
            for n in ('r5qt','r5qm','r5qn','r5pk','r5py'):v[n]=lambda *a:False
            if variant=='comparison_without_result':v['r5qq']=lambda *a:False
        actual=run(d,v);assert actual==[variant in ('all','none','basic_only','support_only','comparison_only')],(variant,actual);rows[variant]=actual[0]
    return dict(independent_antecedents_and_consequences=rows,empty_comparison_does_not_assert_greater_loss=True,
        no_false_disjunction_of_only_two_intervention_types=True,boundaries=list(BOUNDARIES))

@lru_cache(None)
def universal_checks():
    d=fixture('r5qz',(),('r5qs','r5qy'),query='q[t[k r5qz['+R+']]['+P+']].');rows={}
    v=base(d);assert run(d,v)==[True]
    for pos in range(10):
        other=list(TEN);other[pos]='beta' if other[pos]=='alpha' else 'alpha';other=tuple(other)
        v=base(d);v['r5qs']=lambda *a:a in ((*TEN,'reference','case'),(*other,'reference','case'))
        assert run(d,v)==[False];rows[str(pos)]=False
    for variant in ('second_case','empty_scope','outside_scope_failure'):
        v=base(d)
        if variant=='second_case':v['r5qs']=lambda *a:a in ((*TEN,'reference','case'),(*TEN,'reference','outside'))
        if variant=='empty_scope':v['r5qs']=lambda *a:False;v['r5qy']=lambda *a:False
        actual=run(d,v);assert actual==[variant!='second_case'];rows[variant]=actual[0]
    for root,target in (('r5ra','r5qu'),('r5rb','r5qv'),('r5rc','r5qw'),('r5rd','r5qx')):
        segment=fixture(root,(),('r5qs',target),query='q[t[k '+root+'['+R+']]['+P+']].');v=base(segment)
        v[target]=lambda *a:a==(*TEN,'reference','case');assert run(segment,v)==[True]
        v[target]=lambda *a:False;assert run(segment,v)==[False]
    return dict(all_ten_objects_and_all_cases=rows,separate_conditional_contents_checked=True,
        actual_occurrence_not_asserted=True,boundaries=['r5qs','r5qy','r5qu','r5qv','r5qw','r5qx'])

@lru_cache(None)
def adapter_checks():
    rows={}
    for root in ('r5re','r5rf','r5rg','r5rh','r5ri','r5rj','r5rk','r5rl','r5rm','r5rn'):
        d=fixture(root,(),(*BOUNDARIES,'r5qs','r5qy'),query='q[t[k '+root+'[k zbindings[] '+R+']]['+P+']].')
        v=base(d);assert run(d,v)==[True],root
        for length in (9,11):
            v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False],(root,length)
        rows[root]=dict(correct_binding=True,wrong_lengths_rejected=True)
    d=fixture('r5rn',(),('r5qy',),query='q[t[k r5rn[k zbindings[] '+R+']]['+P+']].');positions=[]
    for pos in range(10):
        b=tuple('beta' if i==pos else 'alpha' for i in range(10));v=base(d,b);v['r5qy']=lambda *a:a==(*b,'reference','case')
        assert run(d,v)==[True];v['zbindings']=lambda:SequenceValue(('alpha',)*10,'"individual"');assert run(d,v)==[False];positions.append(pos)
    v=base(d);v['r5qy']=unknown;unknown_rejected(d,v)
    return dict(content_family_adapters=rows,all_ten_binding_positions=positions,
        general_reference_only_selects_scope_inner_reference_is_case=True,boundaries=[*BOUNDARIES,'r5qs','r5qy'],unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013');previous=read('data/royal-loss-comparison-reading-v1.json')
    return dict(status='royal_intervention_full_conditional_nucleus_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[3645,4155],text=u['text'][3645:4155]),
        interpretation=LIMITS,primary_pages=previous['primary_pages'],new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/040.html',observation='基本のwenn、見識側と専制支援側、批判可能性と二側の損傷比較を別の条件範囲に保持する。現実の前件成立を断言しない。')],
        unresolved=['並列・追加・程度の提示','indemの手段説明','格言文言・内容・文脈的適用の引用提示','selbstの取り立て・würdigtの皮肉','著者帰属・本文統合・全文通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,'data/royal-loss-comparison-reading-v1.json',*(x['path'] for x in previous['primary_pages']))})

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
    for name,fn in (('scope',scope_checks),('base_intervention',base_intervention_checks),('conditional',conditional_checks),('independent_consequences',independent_consequences_checks),('universal',universal_checks),('adapter',adapter_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{READING,DOC,INVENTORY,*PRIORS,*(p['path'] for p in read(READING)['primary_pages']),
        'data/royal-loss-comparison-reading-v1.json','scripts/compose_royal_intervention_conditions.py','scripts/check_royal_intervention_conditions.py','tests/test_royal_intervention_conditions.py',
        'scripts/compose_royal_loss_comparison.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='royal_intervention_full_conditional_nucleus_partial',**results,
        alignment=dict(**read(READING)['source'],document=LIBRARY,definitions=list(MEANINGS),status='partial_semantic_dependency'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
