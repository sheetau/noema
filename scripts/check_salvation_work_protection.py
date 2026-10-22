"""Check effort limits, distinct goals, violent hindrance and preventive remit."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_salvation_work_protection import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build
from scripts.check_civic_compatibility import PROVIDERS,base,run,content,DOMAIN,EXTRA
from scripts.check_covenant_nullity import normalized
from scripts.check_motive_causes import unknown

DOC='docs/salvation-work-protection-v1.md'
READING='data/salvation-work-protection-reading-v1.json'
REPORT='reports/salvation-work-protection-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
LEXICAL='artifacts/salvation-work-protection-v1/adelung-gewaltthaetig.html'
PRIORS=('reports/personal-religious-remit-v1.json','reports/civic-oversight-v1.json','reports/monarchical-sentence-v1.json')
A='k zalpha[]';B='k zbeta[]';R='k zreference[]';P='k zcandidate[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    prefix=parse('p:'+EXTRA+PROVIDERS)
    providers={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h','h246e')}
    d['declarations']=[x for x in prefix['declarations'] if x['name'] not in providers]+[providers.get(x['name'],x) for x in d['declarations']]
    return parse(format_graph(d,'compact')+query)

def effort(d):
    v=base(d)
    v['h26hr']=lambda p,g,r,l:(p,g,r)==('alpha','alpha','reference') and l in DOMAIN
    v['h26hs']=lambda p,g,r,l,h:(p,g,r)==('alpha','alpha','reference') and (l,h) in {('alpha','alpha'),('beta','beta'),('beta','alpha')}
    v['h26ht']=lambda *a:a==('alpha','beta','alpha','reference','candidate','beta')
    return v

@lru_cache(None)
def capacity_checks():
    d=fixture('q[k r5n7['+' '.join((A,B,A,R,P))+']].');rows={}
    for variant in ('full','below_capacity','empty_capacity','missing_measurement','ambiguous_measurement','outside_capacity','nonreflexive','incomparable','other_person','other_work','other_goal','other_reference','other_point','unknown'):
        v=effort(d)
        if variant=='below_capacity':v['h26ht']=lambda *a:a==('alpha','beta','alpha','reference','candidate','alpha')
        if variant=='empty_capacity':v['h26hr']=lambda *a:False
        if variant=='missing_measurement':v['h26ht']=lambda *a:False
        if variant=='ambiguous_measurement':v['h26ht']=lambda *a:a[:-1]==('alpha','beta','alpha','reference','candidate')
        if variant=='outside_capacity':v['h26hr']=lambda p,g,r,l:(p,g,r,l)==('alpha','alpha','reference','alpha')
        if variant=='nonreflexive':v['h26hs']=lambda p,g,r,l,h:l!=h
        if variant=='incomparable':v['h26hs']=lambda p,g,r,l,h:l==h
        wanted=['alpha','beta','alpha','reference','candidate','beta']
        changes={'other_person':(0,'beta'),'other_work':(1,'alpha'),'other_goal':(2,'beta'),'other_reference':(3,'assessment'),'other_point':(4,'end')}
        if variant in changes:
            i,val=changes[variant];wanted[i]=val;v['h26ht']=lambda *a:a==tuple(wanted)
        if variant=='unknown':
            v['h26ht']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown effort')
            continue
        actual=run(d,v);assert actual==[variant=='full'],(variant,actual);rows[variant]=actual[0]
    d=fixture('q[k r5n6['+A+' '+A+' '+R+']].');v=base(d)
    levels=(*DOMAIN,'third');v['h26hr']=lambda p,g,r,l:(p,g,r)==('alpha','alpha','reference') and l in levels
    # Reflexive and pairwise comparable but cyclic: transitivity must fail.
    v['h26hs']=lambda p,g,r,l,h:l==h or (l,h) in {('alpha','beta'),('beta','third'),('third','alpha')}
    assert run(d,v,levels)==[False]
    return dict(native_full_capacity=rows,nontransitive_comparison_rejected=True,unique_measurement_uses_native_r2cl=True,unknown_rejected=True)

@lru_cache(None)
def work_checks():
    d=fixture('q[k r5oa['+' '.join((A,B,A,R,P))+']].');rows={}
    for variant in ('baseline','no_activity','no_participation','no_determining_aim','no_promoting_aim','wrong_goal','wrong_person','wrong_reference','wrong_point','not_own_salvation','underused_capacity','unknown'):
        v=effort(d);v['h26hj']=lambda *a:a==('alpha','alpha','reference') and variant!='not_own_salvation'
        v['dg']=lambda *a:a==('beta','candidate') and variant!='no_activity'
        v['df']=lambda *a:a==('alpha','beta','candidate') and variant!='no_participation'
        def aims(p,w,code,b,r,at):
            codes={('r5n4',1),('r5n3',1)}
            if variant=='no_determining_aim':codes.remove(('r5n4',1))
            if variant=='no_promoting_aim':codes.remove(('r5n3',1))
            wanted=('beta' if variant=='wrong_person' else 'alpha','beta',('alpha','beta') if variant=='wrong_goal' else ('alpha','alpha'),
                'assessment' if variant=='wrong_reference' else 'reference','end' if variant=='wrong_point' else 'candidate')
            return normalized((p,w,b,r,at))==wanted and normalized((code,))[0] in codes
        v['h26hf']=aims
        if variant=='underused_capacity':v['h26ht']=lambda *a:a==('alpha','beta','alpha','reference','candidate','alpha')
        if variant=='unknown':
            v['h26hf']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown aim')
            continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert v['h26hq'] is unknown and v['ztruth'] is unknown
    # The two targets can differ in truth value; neither entails the other.
    query=''.join('q[t[k '+n+'[l[a]['+A+' '+B+'] '+R+']]['+P+']].' for n in ('r5n3','r5n4'))
    d=fixture(query);v=base(d);v['h26hj']=lambda *a:a==('beta','alpha','reference')
    v['ztruth']=lambda *a:False;v['h26hq']=lambda *a:a==('alpha','beta','reference','candidate')
    assert run(d,v)==[False,True]
    v['ztruth']=lambda *a:a==('beta','candidate');v['h26hq']=lambda *a:False;assert run(d,v)==[True,False]
    return dict(native_full_capacity_work=rows,distinct_determination_and_salvation_targets=True,work_does_not_require_either_success=True,unknown_rejected=True)

@lru_cache(None)
def candidate_checks():
    d=fixture('q[k r5oc['+A+' '+B+' '+A+' '+R+']].');rows={}
    for variant in ('baseline','missing_determination','missing_promotion','other_person','other_work','other_goal','other_reference','unknown'):
        v=base(d);v['h26hj']=lambda *a:a==('alpha','alpha','reference')
        def selected(p,w,code,b,r):
            expected=('beta' if variant=='other_person' else 'alpha','alpha' if variant=='other_work' else 'beta',
                ('alpha','beta') if variant=='other_goal' else ('alpha','alpha'),'assessment' if variant=='other_reference' else 'reference')
            allowed={('r5n3',1),('r5n4',1)}
            if variant=='missing_determination':allowed.remove(('r5n4',1))
            if variant=='missing_promotion':allowed.remove(('r5n3',1))
            return normalized((p,w,b,r))==expected and normalized((code,))[0] in allowed
        v['h26hu']=selected
        if variant=='unknown':
            v['h26hu']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown candidate')
            continue
        actual=run(d,v);assert actual==[variant=='baseline'];rows[variant]=actual[0]
        assert v['h26hf'] is unknown and v['h26ht'] is unknown and v['h26hq'] is unknown and v['ztruth'] is unknown
    d=fixture('q[k r5oe['+' '.join((A,B,A,B,A,B,R))+']].',('r5ni','r5oc'));identities={}
    for variant in ('baseline','agent_outside','victim_outside','other_work','same_person','wrong_reference'):
        v=base(d)
        v['r5ni']=lambda actor,p,c,at:(actor,c,at)==('alpha','beta','assessment' if variant=='wrong_reference' else 'reference') and not(variant=='agent_outside' and p=='alpha') and not(variant=='victim_outside' and p=='beta')
        v['r5oc']=lambda *a:a==('beta','beta' if variant=='other_work' else 'alpha','beta','reference')
        if variant=='same_person':v['zbeta']=lambda:'alpha';v['r5ni']=lambda *a:True;v['r5oc']=lambda *a:True
        actual=run(d,v);assert actual==[variant=='baseline'];identities[variant]=actual[0]
    return dict(native_candidate_without_success_or_necessity_belief=rows,same_polity_distinct_subjects=identities,case_boundaries=['r5ni','r5oc'],unknown_rejected=True)

@lru_cache(None)
def violence_checks():
    args=' '.join((A,B,A,B,B,R,P));query='q[k r5od['+args+']].';d=fixture(query);rows={}
    for variant in ('baseline','no_activity','no_participation','no_force','justified_force','no_causal_hindrance','other_agent','other_victim','other_intrusion','other_work','other_goal','other_reference','other_point','other_target','same_person','unknown','unknown_authority'):
        v=base(d);v['dg']=lambda *a:a==('beta','candidate') and variant!='no_activity'
        v['df']=lambda *a:a==('beta' if variant=='other_agent' else 'alpha','beta','candidate') and variant!='no_participation'
        v['h26hv']=lambda *a:a==('beta','beta','candidate') and variant!='no_force'
        v['h26hx']=lambda *a:variant=='justified_force' and a==('beta','beta','reference','candidate')
        wanted=['beta','beta',('r5ob',1),('beta','alpha','beta'),'reference','candidate']
        changes={'other_victim':(1,'alpha'),'other_intrusion':(0,'alpha'),'other_work':(3,('beta','beta','beta')),
            'other_goal':(3,('beta','alpha','alpha')),'other_reference':(4,'assessment'),'other_point':(5,'end'),'other_target':(2,('r5n3',1))}
        if variant in changes:i,val=changes[variant];wanted[i]=val
        v['h26hw']=lambda *a:normalized(a)==tuple(wanted) and variant!='no_causal_hindrance'
        if variant=='same_person':v['zbeta']=lambda:'alpha'
        if variant in ('unknown','unknown_authority'):
            v['h26hw' if variant=='unknown' else 'h26hx']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown hindrance')
            continue
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    # Same hindrance can coexist with compensated work or completely blocked work.
    d=fixture(query+'q[t[k r5ob[l[a]['+B+' '+A+' '+B+'] '+R+']]['+P+']].',('r5oa',));counterexamples=[]
    for succeeds in (False,True):
        v=base(d);v['dg']=lambda *a:a==('beta','candidate');v['df']=lambda *a:a==('alpha','beta','candidate')
        v['h26hv']=lambda *a:a==('beta','beta','candidate')
        v['h26hx']=lambda *a:False
        v['h26hw']=lambda *a:normalized(a)==('beta','beta',('r5ob',1),('beta','alpha','beta'),'reference','candidate')
        v['r5oa']=lambda *a:succeeds and a==('beta','alpha','beta','reference','candidate')
        actual=run(d,v);assert actual==[True,succeeds];counterexamples.append(actual)
    return dict(native_violent_hindrance=rows,hindrance_then_actual_target=counterexamples,boundary_for_independent_target_only='r5oa',unknown_rejected=True)

@lru_cache(None)
def universal_checks():
    d=fixture('q[t[k r5of['+A+' '+B+' '+R+']]['+P+']].',('r5oe','r5od'));rows={}
    for variant in ('no_hindrance','second_victim_hindered','first_victim_hindered','other_goal','other_point','other_reference','empty_scope','unknown'):
        v=base(d)
        v['r5oe']=lambda actor,c,agent,victim,w,g,r:(actor,c,w,g,r)==('alpha','beta','alpha','beta','reference') and agent!=victim and variant!='empty_scope'
        wanted=('beta','alpha','alpha','alpha' if variant=='other_goal' else 'beta','alpha',
            'assessment' if variant=='other_reference' else 'reference','end' if variant=='other_point' else 'candidate')
        if variant=='second_victim_hindered':wanted=('alpha','beta','alpha','beta','alpha','reference','candidate')
        v['r5od']=lambda *a:variant!='no_hindrance' and a==wanted
        if variant=='unknown':
            v['r5od']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown violence treated as absent')
            continue
        actual=run(d,v);assert actual==[variant not in ('first_victim_hindered','second_victim_hindered')];rows[variant]=actual[0]
    return dict(every_distinct_subject_pair_and_candidate=rows,boundaries=['r5oe','r5od'],actual_threat_not_required=True,unknown_rejected=True)

@lru_cache(None)
def prevention_checks():
    d=fixture('q[k r5oh['+' '.join((A,B,B,R,P))+']].',('r2uj','r5of'));rows={}
    for variant in ('baseline','no_ruler','no_activity','no_participation','no_goal','no_contribution','no_result','other_goal','other_bindings','other_reference','other_point','unknown'):
        v=base(d);v['r2uj']=lambda *a:a==('alpha','beta','candidate') and variant!='no_ruler'
        v['dg']=lambda *a:a==('beta','candidate') and variant!='no_activity'
        v['df']=lambda *a:a==('alpha','beta','candidate') and variant!='no_participation'
        wanted=['alpha','beta',('r5of',1) if variant=='other_goal' else ('r5og',1),('alpha','alpha') if variant=='other_bindings' else ('alpha','beta'),
            'assessment' if variant=='other_reference' else 'reference','end' if variant=='other_point' else 'candidate']
        v['h26hf']=lambda *a:normalized(a)==tuple(wanted) and variant!='no_goal'
        v['h26hh']=lambda *a:normalized(a)==('beta',('r5og',1),('alpha','beta'),'reference','candidate') and variant!='no_contribution'
        v['r5of']=lambda *a:content({'candidate'}) if a==('alpha','beta','reference') and variant!='no_result' else content(set())
        if variant=='unknown':
            v['h26hh']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown preventive contribution')
            continue
        actual=run(d,v);assert actual==[variant=='baseline'];rows[variant]=actual[0]
    d=fixture('q[k r5oj['+' '.join((B,A,B,R,P))+']].',('r2uj','r2ui'));duties={}
    for variant in ('baseline','no_ruler','no_office','no_holder','no_remit','no_requirement','wrong_source','wrong_office','wrong_content','wrong_bindings','wrong_reference','wrong_point','negative_requirement','unknown'):
        v=base(d);v['r2uj']=lambda *a:a==('alpha','beta','candidate') and variant!='no_ruler'
        v['h234f']=lambda *a:a==('beta','beta','candidate') and variant!='no_office'
        v['r2ui']=lambda *a:a==('alpha','beta','beta','candidate') and variant!='no_holder'
        v['h26hp']=lambda *a:normalized(a)==('beta','beta',('r5oi',1),('alpha','beta'),'reference','candidate') and variant!='no_remit'
        wanted=['beta','alpha','beta',('r5oi',1),('alpha','beta'),'reference',True,'candidate']
        changes={'wrong_source':(0,'alpha'),'wrong_office':(2,'alpha'),'wrong_content':(3,('r5og',1)),
            'wrong_bindings':(4,('alpha','alpha')),'wrong_reference':(5,'assessment'),'negative_requirement':(6,False),'wrong_point':(7,'end')}
        if variant in changes:i,val=changes[variant];wanted[i]=val
        v['h237z']=lambda *a:normalized(a)==tuple(wanted) and variant!='no_requirement'
        if variant=='unknown':
            v['h237z']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown obligation')
            continue
        actual=run(d,v);assert actual==[variant=='baseline'];duties[variant]=actual[0]
        assert v['dg'] is unknown and v['h26hf'] is unknown and v['h26hh'] is unknown and v['h26hw'] is unknown
    return dict(effective_prevention=rows,same_office_remit_and_positive_requirement=duties,duty_does_not_execute_prevention=True,boundaries=['r2uj','r2ui','r5of'],unknown_rejected=True)

@lru_cache(None)
def adapter_checks():
    rows={}
    for root,target,length in (('r5ob','r5oa',3),('r5og','r5of',2),('r5oi','r5oh',2)):
        d=fixture('q[t[k '+root+'[k zbindings[] '+R+']]['+P+']].',(target,));positions=[]
        for i in range(length):
            b=tuple('beta' if i==j else 'alpha' for j in range(length));v=base(d,b)
            if root=='r5ob':v[target]=lambda *a:a==(*b,'reference','candidate')
            elif root=='r5og':v[target]=lambda *a:content({'candidate'}) if a==(*b,'reference') else content(set())
            else:v[target]=lambda actor,c,act,r,p:(actor,c,r,p)==(*b,'reference','candidate') and act=='beta'
            assert run(d,v)==[True];v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False];positions.append(i)
        for size in (length-1,length+1):v['zbindings']=lambda:SequenceValue(('alpha',)*size,'"individual"');assert run(d,v)==[False]
        rows[root]=positions
    source=(ROOT/LIBRARY).read_text(encoding='utf-8')
    for target in ('r5n3','r5n4','r5ob','r5og','r5oi'):
        try:parse(source.replace('r b[p '+target+']','r[p '+target+']'))
        except (ValueError,TypeError):pass
        else:raise AssertionError('Rank-zero accepted: '+target)
    return dict(exact_adapters=rows,rank_zero_targets_rejected=True,boundaries=['r5oa','r5of','r5oh'])

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013')
    pages=[p for p in read('data/personal-enlightenment-choice-reading-v1.json')['primary_pages'] if 'page-490' in p['path']]
    return dict(status='partial_salvation_work_and_preventive_official_duty',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[3489,3644],text=u['text'][3489:3644]),
        interpretation=LIMITS,new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,primary_pages=pages,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/040.html',lines='7–9',observation='君主の職責の対照に続き、一人が他人の救済の決定・促進への全力の営みを暴力的に妨げないよう防ぐ部分。営み・妨害・予防の内容と、その所管・要求を分けて接続。'),
          dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009132_2_1_1899',path=LEXICAL,entry='Gewaltthätig, F–L巻653–654頁',observation='優越的な力の権限なき行使を語義とし、単なるgewaltsamへの置換とも区別する。身体的実力だけの草案を改め、強制力と正当な根拠の不在を分ける。')],
        unresolved=['前半のkann/nur/übrigensと監督のWenn条件','同じ君主の所管外と積極的所管のwohl aberによる対照','職責を評価する規範源の固定','全文の照応・提示・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,LEXICAL,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();sources=parents()
    for n in read(BASIS)['imported_symbols']:
        old=next(s.entries[n] for s in sources if n in s.entries)
        assert c.entries[n]['declaration']==old['declaration'] and c.entries[n]['meaning_ja']==old['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    assert read(READING)==reading_record() and len(sources[2].document['statements'])==106
    assert 'unbefugter Anwendung' in (ROOT/LEXICAL).read_text(encoding='utf-8')
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,preserved_main_statements=106,semantic_review_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('capacity',capacity_checks),('work',work_checks),('candidates',candidate_checks),('violence',violence_checks),('universal',universal_checks),('prevention',prevention_checks),('adapters',adapter_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INVENTORY,LEXICAL,*PRIORS,*(x['path'] for x in read(READING)['primary_pages']),
        'scripts/compose_salvation_work_protection.py','scripts/check_salvation_work_protection.py','tests/test_salvation_work_protection.py',
        'scripts/check_civic_compatibility.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/compose_protected_remarks.py','scripts/check_persistent_compact_progress.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='full_capacity_salvation_work_violent_hindrance_and_preventive_duty',document=LIBRARY,**results,
        alignment=dict(**reading_record()['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
