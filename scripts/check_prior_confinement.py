"""Test local confinement, a shared continuing onset, and timed depiction."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.finite_semantics import SequenceValue as LegacySequence
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_prior_confinement import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_confinement import DOMAIN
from scripts.check_insistent_framing import source_values as old_attribution

INDEX='data/semantic-review-index-v77.json'
REPORT='reports/prior-confinement-v1.json'
AUDIT='data/prior-confinement-reading-v1.json'
DOC='docs/prior-confinement-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
EVIDENCE='data/prior-confinement-evidence-v1.json'
SELECTION=[9,35,36,46,47,48,49]
TIMES=('open','closed','prior','released','reclosed','warning')
PEOPLE=DOMAIN+('closing_again',)


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+suffix)


@lru_cache(None)
def generic():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jhistory[d] c.r jbefore[d d] c.r jstage[] d.r jend[] d.r jonset[a d d] c.r jstate[d] c.r jvalid[d] c.
q[k r2ad[p jhistory p jbefore k jstage[] k jstage[] p jonset b point[k jstate[v point]] p jvalid]].
q[k r2ad[p jhistory p jbefore k jstage[] k jend[] p jonset b point[k jstate[v point]] p jvalid]].
''')


def generic_values(bits=(True,True,True,True),variant='baseline'):
    onset,prior,middle,final=bits
    states=dict(open=False,closed=True,prior=prior,released=middle,reclosed=middle,warning=final)
    history=set(TIMES)
    if variant.startswith('missing_'):history.remove(variant.removeprefix('missing_'))
    if variant=='empty_history':history.clear()
    return dict(jhistory=lambda t:t in history,
        jbefore=lambda a,b:TIMES.index(a)>TIMES.index(b) if variant=='reverse_order' else TIMES.index(a)<TIMES.index(b),
        jstage=lambda:'warning' if variant=='stage_after_end' else 'prior',
        jend=lambda:'prior' if variant=='stage_after_end' else 'warning',
        jonset=lambda p,a,b:onset and (p,a,b)==('event','open','closed'),
        jstate=lambda t:True if variant=='no_change' and t=='open' else states[t],
        jvalid=lambda t:not(variant=='invalid_first' and t=='open' or variant=='invalid_middle' and t=='released'))


def generic_checks():
    rows=[]
    for bits in product((False,True),repeat=4):
        actual=evaluate(generic(),generic_values(bits),('event','other'),TIMES,True)
        assert actual==[bits[0] and bits[1],all(bits)],(bits,actual)
        rows.append(dict(onset_prior_middle_final=bits,local_and_continuing=actual))
    variants={'missing_prior':[False,False],'missing_warning':[True,False],'missing_open':[False,False],
        'missing_closed':[False,False],'empty_history':[False,False],'reverse_order':[False,False],
        'stage_after_end':[True,False],'no_change':[False,False],'invalid_first':[False,False],'invalid_middle':[True,False]}
    contrasts={}
    for name,expected in variants.items():
        actual=evaluate(generic(),generic_values(variant=name),('event','other'),TIMES,True)
        assert actual==expected,(name,actual,expected);contrasts[name]=actual
    for name in ('jhistory','jbefore','jonset','jstate','jvalid'):
        v=generic_values();v[name]=unknown
        try:evaluate(generic(),v,('event','other'),TIMES,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(combinations=rows,contrasts=contrasts,unknown_inputs_refused=5,
        same_onset_witness_retained=True,local_state_not_extended_to_later_endpoint=True)


@lru_cache(None)
def native():
    return fixture(['r2ae','zbe','zbb'],'''
r jp[] a.r jf[] a.r jl[] a.r js[] d.r je[] d.
q[k r2ae[k jp[] k jf[] k jl[] k js[] k js[]]].
q[k r2ae[k jp[] k jf[] k jl[] k js[] k je[]]].
q[k zbe[k jp[] k jf[] k jl[] k je[]]].
q[t[k zbb[k jp[] k jf[] k jl[]]][k js[]]].
q[k zbe[k jp[] k jf[] k jl[] k js[]]].
''')


def native_values(d,variant='baseline'):
    from scripts.check_confinement_onset import source_model
    old=source_model(d)
    def adapt(fn):
        def call(*args):
            result=fn(*args)
            return SequenceValue(result.items,result.element_type) if isinstance(result,LegacySequence) else result
        return call
    v={n:adapt(fn) for n,fn in old.items()}
    active=set(TIMES[1:])
    events={'closing':('open','closed')}
    if variant=='late':active={'reclosed','warning'};events={'closing_again':('released','reclosed')}
    if variant=='released_after_prior':active={'closed','prior'}
    if variant=='released_and_reclosed':
        active={'closed','prior','reclosed','warning'};events['closing_again']=('released','reclosed')
    def history(r,p,c,a,t):
        return (r,p,c)==('lock','being','frame') and a in ('prior','warning') and TIMES.index(t)<=TIMES.index(a) \
            and not(variant=='missing_prior_history' and t=='prior')
    v.update(jp=lambda:'being',jf=lambda:'other' if variant=='wrong_carrier' else 'frame',jl=lambda:'lock',
        js=lambda:'prior',je=lambda:'warning',db=lambda:'guards',
        ha=lambda a,b:a+b,hc=lambda a,b:a<b,hd=lambda truth:Fraction(int(truth)),
        dd=lambda a,b:TIMES.index(a)<TIMES.index(b),zba=history,
        ag=lambda p,a,b:events.get(p)==(a,b),
        la=lambda person,p,a,b:person=='being' and events.get(p)==(a,b),
        dg=lambda p,t:variant!='no_actual_event' and p in events and events[p][1]==t,
        df=lambda keeper,p,t:keeper=='guard' and p in events and events[p][1]==t,
        qz=lambda p,r,person,c,t:(r,person,c)==('lock','being','frame') and p in events and events[p][1]==t,
        q7=lambda r,person,c,t:(r,person,c)==('lock','being','frame') and not(variant=='unassessed_prior' and t=='prior'),
        qy=lambda r,person,c,a,b,t:(r,person,c,a,b)==('lock','being','frame','threshold','outside') and t in active)
    return v


def native_checks():
    expected={'baseline':[True,True,True,True,True],'late':[False,False,True,False,False],
        'released_after_prior':[True,False,False,True,True],'released_and_reclosed':[True,False,True,True,True],
        'missing_prior_history':[False,False,True,True,False],'unassessed_prior':[False]*5,
        'wrong_carrier':[False]*5,'no_actual_event':[False,False,False,True,False]}
    rows={}
    for name,wanted in expected.items():
        actual=evaluate(native(),native_values(native(),name),PEOPLE,TIMES,True)
        assert actual==wanted,(name,actual,wanted);rows[name]=actual
        print('native '+name+' checked',flush=True)
    assert all(v[0]==v[4] for v in rows.values())
    r=rows['released_and_reclosed'];assert r[2] and r[3] and not r[1]
    return dict(contrasts=rows,columns=['local_prior','same_onset_through_warning','old_at_warning','state_at_prior','old_at_prior'],
        local_degenerate_interval_agrees_with_old_state_in_all_cases=True,
        endpoint_conjunction_countermodel=True,actual_graph_onset_and_keeper_definitions_executed=True,
        definitions_replaced_by_primitives=False)


@lru_cache(None)
def source_fixture():
    return fixture(['r2af'],'r jp[] a.r js[] d.r je[] d.q[k r2af[k jp[] k js[] k je[]]].')


def source_values(d,variant='baseline'):
    from scripts.check_training_frame import source_model,PARTS
    v=native_values(d,variant)
    frame=source_model(d,'no_training_purpose' if variant=='no_training_purpose' else 'baseline')
    for name in ('zaa','zab','zac','zad','zae','zaf','zag'):
        callback=frame[name]
        def call(*args,callback=callback):
            result=callback(*('now' if a=='warning' else a for a in args))
            return SequenceValue(result.items,result.element_type) if isinstance(result,LegacySequence) else result
        v[name]=call
    v.update(qs=lambda p,a:'other' if variant=='wrong_apparatus' else 'frame',
        mp=lambda group:SequenceValue(('guard',) if group=='guards' else (), '"individual"'),
        aa=lambda p:p=='guard',qd=lambda p:p=='being',
        qn=lambda g,p,a:variant!='unowned' and (g,p,a)==('guards','being','warning'),
        qr=lambda p,a,t:(p,a)==('being','warning') and t in TIMES,
        qo=lambda p,a,t:(p,a)==('being','warning') and t in TIMES)
    for name in ('qe','ql','qm'):
        v[name]=lambda k,p,t:(k,p)==('guard','being') and t in TIMES
    return v


def source_checks():
    from scripts.check_training_frame import PARTS
    d=source_fixture();rows={}
    for name in ('baseline','late','released_after_prior','released_and_reclosed','wrong_apparatus','no_training_purpose','unowned'):
        actual=evaluate(d,source_values(d,name),PEOPLE+PARTS,TIMES,True)
        assert actual==[name in ('baseline','released_after_prior','released_and_reclosed')],(name,actual)
        rows[name]=actual;print('source '+name+' checked',flush=True)
    return dict(contrasts=rows,actual_husbandry_training_apparatus_and_local_confinement_evaluated=True,
        release_after_prior_does_not_rewrite_prior=True,apparatus_selected_at_anchor_held_at_prior=True)


def attribution_values(d,variant='baseline'):
    v=old_attribution(d);old=v['hzyb']
    def match(n,a,c,t,b,s):
        wanted=dict(kind='call',symbol='hztr',arguments=[dict(kind='call',symbol='db',arguments=[])])
        if variant=='other_claim':wanted['symbol']='hztf'
        return variant!='missing' and (n,a,s)==('relative' if variant=='other_node' else 'clause',
            'other' if variant=='other_author' else 'author','elsewhere' if variant=='other_context' else 'context') \
            and json.loads(c.syntax)==wanted and symbol(t)==('r2af' if variant=='reversed' else 'rqzw') \
            and symbol(b)==('rqzw' if variant=='reversed' else 'zbf' if variant=='old_depiction' else 'r2af')
    v['hzyb']=lambda *args:old(*args) or match(*args)
    return v


def attribution_checks():
    d=fixture(['r2ag'],'q[k r2ag[]].');people=('clause','relative','livestock','previous','author','guards','other');times=('context','elsewhere');rows={}
    for name in ('baseline','missing','other_claim','other_node','other_author','other_context','reversed','old_depiction'):
        actual=evaluate(d,attribution_values(d,name),people,times)
        assert actual==[name=='baseline'],(name,actual);rows[name]=actual
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    assert evaluate(core,attribution_values(core),people,times)==[True]*7
    v=attribution_values(d);v['hzyb']=unknown
    try:evaluate(d,v,people,times)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown alignment became true')
    return dict(contrasts=rows,seven_excerpt_statements_evaluated=True,world_contents_unknown=True,
        unknown_alignment_refused=True,ordinary_evaluation=True)


def reading():
    old=json.loads((ROOT/'data/insistent-framing-reading-v1.json').read_text(encoding='utf-8'))
    clauses=deepcopy(old['clauses']);c=next(c for c in clauses if c['id']=='confinement')
    c.update(definitions=['r2ad','r2ae','r2af','r2ag','zbd','zbb'],status='partial',
        interpretation_ja='同じ本人と装置について、阻止・許容欠如の同じ先行局面までに成立し、その局面へ続く閉じ込めを描く。後の警告までの継続は別条件として残し、本文には補わない。')
    paths=(INDEX,PARENT,PARENT_BASIS,FULL,BASIS,ANNOTATIONS,INVENTORY,EVIDENCE,
        'data/insistent-framing-reading-v1.json','reports/guarded-walking-scope-v1.json',
        'artifacts/first-cause-reading-v1/page-482.jpg')
    return dict(status='prior_stage_confinement_adopted_without_later_persistence',reviewer='assistant_review',
        decision='partial_source_depiction_revised_whole_sentence_not_verified',document=FULL,meaning_basis=BASIS,
        source=old['source'],clauses=clauses,selection=selection_binding(catalog(),SELECTION),
        interpretation_limits=LIMITS,source_review=old['source_review'],
        remaining=['歩行と家畜像・局面上の落ち着き・強調を含む複文の通し判断','第二段落末尾と段落全体','二作品全文'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def structure():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-4]==old.document['declarations']
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'],strict=True)) if a!=b]==[36]
    assert len(new.document['statements'])==50 and all(new.entries[n]==e for n,e in old.entries.items())
    assert set(new.entries)-set(old.entries)==set(MEANINGS)
    idx=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for path in idx['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/path).read_text(encoding='utf-8'));ids=[s['index'] for s in r['selection']['statements']]
        assert 36 not in ids and r['selection']==selection_binding(new,ids)
    for path,text in build().items():assert (ROOT/path).read_text(encoding='utf-8')==text,path
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('full','compact'):
            t=format_graph(d,style);assert parse(t)==parse(transcribe(t,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    r=reading();assert r==json.loads((ROOT/AUDIT).read_text(encoding='utf-8'));validate_hashes(ROOT,r['source_sha256'])
    assert ''.join(c['text'] for c in r['clauses'])==r['source']['text']
    return dict(revised_statements=[36],preserved_statements=49,total_statements=50,new_definitions=4,new_primitives=0,
        preserved_review_selections=11,roundtrips=True,whole_sentence_verified=False)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('generic',generic_checks),('native',native_checks),('source',source_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']==r['source']['unit'])
    paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_prior_confinement.py','scripts/check_prior_confinement.py','scripts/register_prior_confinement.py',
        'tests/test_prior_confinement.py','scripts/check_confinement_onset.py','scripts/check_confinement.py',
        'scripts/check_training_frame.py','scripts/check_insistent_framing.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','noema/constructed.py','noema/constructed_semantics.py',
        'noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='confinement_bound_to_same_prior_stage',document=FULL,**results,
        alignment=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[1073,1101],text=unit['text'][1073:1101],
            definitions=list(MEANINGS),status='partial_prior_stage_confinement'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
