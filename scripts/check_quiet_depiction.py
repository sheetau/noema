"""Verify local motor absence and attribution without inferring inner states."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_quiet_depiction import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_step_depiction import attribution_values as previous_attribution
from scripts.fetch_scoped_quiet_evidence import PATH as EVIDENCE,validate

INDEX='data/semantic-review-index-v74.json'
REPORT='reports/quiet-depiction-v1.json'
AUDIT='data/quiet-depiction-reading-v1.json'
DOC='docs/quiet-depiction-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
SELECTION=[9,35,36,46,47,48]
DOMAIN=('body','other','one','two','guard','guards')
TIMES=('early','prior','anchor','elsewhere')


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+suffix)


@lru_cache(None)
def local_fixture():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jp[] a.r jt[] d.r jsubject[a a d] c.r joccurs[a d] c.r jmarked[a d] c.
q[k rqz5[k jp[] k jt[] p jsubject p joccurs p jmarked]].
''')


def local_checks():
    rows=[]
    for bits in product((False,True),repeat=6):
        subjects,occurs,marked=[{e for e,b in zip(('one','two'),bits[i:i+2]) if b} for i in (0,2,4)]
        v=dict(jp=lambda:'body',jt=lambda:'prior',jsubject=lambda p,e,t:p=='body' and e in subjects and t=='prior',
            joccurs=lambda e,t:e in occurs and t=='prior',jmarked=lambda e,t:e in marked and t=='prior')
        actual=evaluate(local_fixture(),v,DOMAIN,TIMES)
        assert actual==[not bool(subjects&occurs&marked)],(bits,actual)
        rows.append(dict(subject_occurrence_pattern=bits,local_absence=actual[0]))
    # An agitated episode at a different point does not falsify this local
    # statement; it is a counterexample to a persistent-character inference.
    v=dict(jp=lambda:'body',jt=lambda:'prior',jsubject=lambda p,e,t:(p,e,t)==('body','one','early'),
        joccurs=lambda e,t:(e,t)==('one','early'),jmarked=lambda e,t:(e,t)==('one','early'))
    assert evaluate(local_fixture(),v,DOMAIN,TIMES)==[True]
    v['jt']=lambda:'early';assert evaluate(local_fixture(),v,DOMAIN,TIMES)==[False]
    for name in ('jsubject','joccurs','jmarked'):
        w=dict(v);w[name]=unknown
        try:evaluate(local_fixture(),w,DOMAIN,TIMES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(combinations=rows,local_absence_not_persistent_disposition=True,unknown_inputs_refused=3,ordinary_evaluation=True)


PARAMS='r jp[] a.r jprior[] d.r janchor[] d.'


def motor_values(d,bits=(True,True,False),variant='baseline'):
    moves,occurs,agitated=bits
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update(jp=lambda:'body',jprior=lambda:'prior',janchor=lambda:'anchor',
        hzyc=lambda b,e,t:moves and (b,e,t)==('other' if variant=='other_body' else 'body','one',
            'early' if variant=='other_motion_point' else 'prior'),
        dg=lambda e,t:occurs and (e,t)==('two' if variant=='other_episode' else 'one','prior'),
        hzyd=lambda b,e,r,t:agitated and (b,e,r,t)==('other' if variant=='other_pattern_body' else 'body',
            'two' if variant=='other_pattern_episode' else 'one','early' if variant=='other_reference' else 'anchor',
            'early' if variant=='other_pattern_point' else 'prior'))
    return v


def motor_checks():
    d=fixture(['rqz6'],PARAMS+'q[k rqz6[k jp[] k jprior[] k janchor[]]].');rows=[]
    for bits in product((False,True),repeat=3):
        actual=evaluate(d,motor_values(d,bits),DOMAIN,TIMES)
        assert actual==[not all(bits)];rows.append(dict(motion_occurrence_agitation=bits,quiet=actual[0]))
    contrasts={}
    for name in ('other_body','other_motion_point','other_episode','other_pattern_body','other_pattern_episode','other_reference','other_pattern_point'):
        actual=evaluate(d,motor_values(d,(True,True,True),name),DOMAIN,TIMES)
        assert actual==[True],(name,actual);contrasts[name]=actual
    for name in ('hzyc','dg','hzyd'):
        v=motor_values(d);v[name]=unknown
        try:evaluate(d,v,DOMAIN,TIMES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    primitives={x['name'] for x in d['declarations'] if x['kind']=='primitive'}
    assert primitives=={'jp','jprior','janchor','hzyc','dg','hzyd'}
    return dict(combinations=rows,contrasts=contrasts,unknown_inputs_refused=3,
        no_human_agency_emotion_permission_or_courage_inputs=True,ordinary_evaluation=True)


def source_values(d,variant='baseline'):
    v=motor_values(d,(True,True,variant=='agitated'))
    v.update(db=lambda:'guards',mp=lambda group:SequenceValue(('guard',) if group=='guards' else (), '"individual"'),
        aa=lambda p:p=='guard' or p=='body' and variant=='human',qd=lambda p:p=='body' and variant!='not_animal',
        qn=lambda owner,b,t:variant!='unowned' and (owner,b,t)==('guards','body','anchor'),
        qr=lambda b,a,t:(b,a)==('body','anchor') and t in TIMES[:3],
        qo=lambda b,a,t:(b,a)==('body','anchor') and t in (
            ('early','anchor') if variant=='gapped_husbandry' else TIMES[:3]),
        dd=lambda a,b:a in TIMES[:3] and b in TIMES[:3] and TIMES.index(a)<TIMES.index(b))
    for name in ('qe','ql','qm'):
        v[name]=lambda keeper,b,t,n=name:(keeper,b)==('guard','body') and t in TIMES[:3] and variant!='missing_'+n
    if variant=='other_subject':v['jp']=lambda:'other'
    if variant=='other_anchor':v['janchor']=lambda:'elsewhere'
    if variant=='no_prior_order':
        v['jprior']=lambda:'anchor'
    if variant=='quiet_but_inactive':v['hzyc']=lambda *args:False
    if variant=='involuntary_agitation':
        v['hzyd']=lambda b,e,r,t:(b,e,r,t)==('body','one','anchor','prior')
    return v


def source_checks():
    d=fixture(['rqz7'],PARAMS+'q[k rqz7[k jp[] k jprior[] k janchor[]]].');rows={}
    for name in ('baseline','agitated','human','not_animal','unowned','gapped_husbandry','missing_qe','missing_ql','missing_qm',
            'other_subject','other_anchor','no_prior_order','quiet_but_inactive','involuntary_agitation'):
        actual=evaluate(d,source_values(d,name),DOMAIN,TIMES)
        assert actual==[name in ('baseline','quiet_but_inactive')],(name,actual);rows[name]=actual
    # Distinguish the same body's simultaneous calm/agitated local points.
    pair=fixture(['rqz7'],PARAMS+'r jearly[] d.q[k rqz7[k jp[] k jprior[] k janchor[]]].q[k rqz7[k jp[] k jearly[] k janchor[]]].')
    v=source_values(pair);v['jearly']=lambda:'early'
    v.update(hzyc=lambda b,e,t:(b,e)==('body','one') and t in ('prior','early'),
        dg=lambda e,t:e=='one' and t in ('prior','early'),hzyd=lambda b,e,r,t:(b,e,r,t)==('body','one','anchor','early'))
    assert evaluate(pair,v,DOMAIN,TIMES)==[True,False]
    return dict(contrasts=rows,same_body_different_points=[True,False],actual_husbandry_definition_evaluated=True,
        human_action_relation_not_required_for_animal_motion=True,ordinary_evaluation=True)


def attribution_values(d,variant='baseline'):
    v=previous_attribution(d);old=v['hzyb']
    def match(n,a,c,t,b,s):
        wanted=dict(kind='call',symbol='hztr',arguments=[dict(kind='call',symbol='db',arguments=[])])
        if variant=='other_claim':wanted['symbol']='hztf'
        if variant=='other_group':wanted['arguments'][0]['symbol']='mv'
        return (variant!='missing' and (n,a,s)==('relative' if variant=='other_node' else 'clause',
            'other' if variant=='other_author' else 'author','elsewhere' if variant=='other_context' else 'context')
            and json.loads(c.syntax)==wanted and symbol(t)==('rqz7' if variant=='reversed' else 'rqzw')
            and symbol(b)==('rqzw' if variant=='reversed' else 'rqzx' if variant=='other_depiction' else 'rqz7'))
    v['hzyb']=lambda *args:old(*args) or match(*args)
    return v


def attribution_checks():
    d=fixture(['r2aa'],'q[k r2aa[]].');domain=('clause','relative','livestock','previous','author','other');times=('context','elsewhere');rows={}
    for name in ('baseline','missing','other_claim','other_group','other_node','other_author','other_context','reversed','other_depiction'):
        actual=evaluate(d,attribution_values(d,name),domain,times)
        assert actual==[name=='baseline'],(name,actual);rows[name]=actual
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    assert evaluate(core,attribution_values(core),domain,times)==[True]*6
    v=attribution_values(d);v['hzyb']=unknown
    try:evaluate(d,v,domain,times)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown presentation became true')
    return dict(contrasts=rows,six_excerpt_statements_evaluated=True,world_contents_all_unknown=True,
        unknown_alignment_refused=True,old_bodily_permission_alignment_retained=True,ordinary_evaluation=True)


def reading():
    validate(json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8')))
    old=json.loads((ROOT/'data/step-depiction-reading-v1.json').read_text(encoding='utf-8'));clauses=deepcopy(old['clauses'])
    c=next(c for c in clauses if c['id']=='quiet_creatures')
    c.update(status='partial',definitions=['qk','rqzw','rqz5','rqz6','rqz7','r2aa'],
        interpretation_ja='先行する家畜像の同じ対象を再指示し、阻止と許容欠如の同じ先行局面に、外から目立つ身体的な動揺がない描写を結ぶ。内面の平静・非抵抗・従順な性格までは含めない。')
    paths=(INDEX,PARENT,PARENT_BASIS,FULL,BASIS,ANNOTATIONS,INVENTORY,EVIDENCE,
        'data/step-depiction-reading-v1.json','data/scoped-quiet-reading-v1.json','reports/step-depiction-v1.json',
        'artifacts/first-cause-reading-v1/page-482.jpg')
    return dict(status='external_quiet_depiction_connected_to_same_prior_stage',reviewer='assistant_review',
        decision='partial_source_depiction_adopted_whole_sentence_not_verified',document=FULL,meaning_basis=BASIS,
        source=old['source'],clauses=clauses,selection=selection_binding(catalog(),SELECTION),
        interpretation_limits=LIMITS,source_review=old['source_review'],
        remaining=['jaの強調','局面上のruhigenと家畜・歩行の語義範囲を含む一文全体','第二段落末尾と段落全体','二作品全文'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def structure():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-6]==old.document['declarations']
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==49
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert set(new.entries)-set(old.entries)==set(MEANINGS)|set(PRIMITIVES)
    idx=json.loads((ROOT/INDEX).read_text(encoding='utf-8'));active=load_catalog(ROOT,idx['works']['kant-1784']['meaning_basis'])
    assert selection_binding(active,list(range(48)))==selection_binding(new,list(range(48)))
    for path in idx['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/path).read_text(encoding='utf-8'));ids=[s['index'] for s in r['selection']['statements']]
        assert 48 not in ids and r['selection']==selection_binding(new,ids)
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('full','compact'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    r=reading();assert r==json.loads((ROOT/AUDIT).read_text(encoding='utf-8'));validate_hashes(ROOT,r['source_sha256'])
    assert ''.join(c['text'] for c in r['clauses'])==r['source']['text']
    assert [c['id'] for c in r['clauses'] if c['status']=='unresolved']==['emphasis']
    return dict(preserved_statements=48,new_statements=[48],new_definitions=4,new_primitives=2,
        preserved_review_selections=11,roundtrips=True,whole_sentence_verified=False)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('local',local_checks),('motor',motor_checks),('source',source_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']==r['source']['unit'])
    span=[1008,1032]
    paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_quiet_depiction.py','scripts/check_quiet_depiction.py','scripts/register_quiet_depiction.py','tests/test_quiet_depiction.py',
        'scripts/compose_grounded_step.py','scripts/compose_falling_depiction.py','scripts/check_step_depiction.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/fetch_scoped_quiet_evidence.py',
        'scripts/fetch_pastoral_role_evidence.py','noema/constructed.py','noema/constructed_semantics.py',
        'noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='partial_external_quiet_livestock_depiction_at_same_prior_stage',document=FULL,**results,
        alignment=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=span,text=unit['text'][span[0]:span[1]],
            definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
