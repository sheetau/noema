"""Check contact phases, exterior landing, ordered goal binding and quoted norms."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_grounded_step import ROOT,FULL,CORE,LIBRARY,BASIS,PARENT,PARENT_BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.fetch_grounded_step_evidence import PATH as EVIDENCE,validate

INDEX='data/semantic-review-index-v69.json'
REPORT='reports/grounded-step-v1.json'
READING='data/grounded-step-reading-v1.json'
DOC='docs/grounded-step-v1.md'
DOMAIN=('body','foot','otherfoot','frame','act','origin','destination')
TIMES=('start','middle','end','elsewhere')


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+suffix)


@lru_cache(None)
def generic():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jp[] a.r jo[] a.r jd[] a.r js[] d.r je[] d.r jhistory[d] c.r jphase[d] c.
r jbefore[d d] c.r jposition[a d] a.r jcontact[a a d] c.
q[k rqzb[k jp[] k jo[] k jd[] k js[] k je[] p jhistory p jphase p jbefore p jposition p jcontact]].
''')


def generic_values(bits=(True,True,False,True,True),variant='baseline'):
    first,last,middle,changed,complete=bits
    return dict(jp=lambda:'foot',jo=lambda:'origin',jd=lambda:'destination',js=lambda:'start',je=lambda:'end',
        jhistory=lambda s:s in TIMES[:3],jphase=lambda s:s in TIMES[:3] and (s!='middle' or complete),
        jbefore=lambda a,b:a in TIMES[:3] and b in TIMES[:3] and (
            a==b or TIMES.index(a)<TIMES.index(b) if variant=='reflexive' else TIMES.index(a)>TIMES.index(b) if variant=='reverse' else TIMES.index(a)<TIMES.index(b)),
        jposition=lambda p,s:'destination' if s=='end' and changed else 'origin',
        jcontact=lambda p,l,s:p=='foot' and ((s,l)==('start','origin') and first or
            (s,l)==('end','destination') and last or s=='middle' and l=='origin' and middle))


def generic_checks():
    rows=[]
    for bits in product((False,True),repeat=5):
        actual=evaluate(generic(),generic_values(bits),DOMAIN,TIMES)
        assert actual==[bits[0] and bits[1] and not bits[2] and bits[3] and bits[4]],(bits,actual)
        rows.append(dict(bits=bits,value=actual[0]))
    contrasts={}
    for name in ('reflexive','reverse'):
        actual=evaluate(generic(),generic_values(variant=name),DOMAIN,TIMES);assert actual==[False];contrasts[name]=actual
    for name in ('jhistory','jphase','jbefore','jposition','jcontact'):
        v=generic_values();v[name]=unknown
        try:evaluate(generic(),v,DOMAIN,TIMES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(combinations=rows,order_contrasts=contrasts,unknown_inputs_refused=5,
        intermediate_recontact_and_gapped_phase_rejected=True,ordinary_evaluation=True)


PARAMS='r jbody[] a.r jfoot[] a.r jact[] a.r jcarrier[] a.r jstart[] d.r jend[] d.'


def source_values(doc,variant='baseline'):
    v={x['name']:unknown for x in doc['declarations'] if x['kind']=='primitive'}
    v.update(jbody=lambda:'body',jfoot=lambda:'foot',jact=lambda:'act',jcarrier=lambda:'frame',jstart=lambda:'start',jend=lambda:'end',
        ia=lambda p,anchor,s:(p,anchor)==('body','end') and s in TIMES[:3],
        ic=lambda a,b,anchor:anchor=='end' and a in TIMES[:3] and b in TIMES[:3] and TIMES.index(a)<TIMES.index(b),
        h4x=lambda a,anchor,s:(a,anchor)==('act','end') and s in TIMES[:3] and not(variant=='gapped_phase' and s=='middle'),
        qw=lambda p,s:'destination' if p=='foot' and s=='end' and variant!='same_position' else 'origin',
        hzxw=lambda part,body,s:body=='body' and part in ('foot','otherfoot') and s in TIMES[:3] and
            not(variant=='foreign_moving_foot' and part=='foot') and not(variant=='lost_membership_middle' and part=='foot' and s=='middle') and
            not(variant=='foreign_supporting_foot' and part=='otherfoot'),
        hzxx=lambda part,place,s:(part,place,s)==('foot','origin','start') and variant!='no_initial_contact' or
            (part,place,s)==('foot','destination','end') and variant!='no_landing_contact' or
            part=='otherfoot' and place=='origin' and s in TIMES[:3] and not(variant=='flight_middle' and s=='middle') or
            variant=='dragging' and (part,place,s)==('foot','origin','middle'),
        zai=lambda p,a,s:variant!='no_body_motion' and (p,a,s)==('body','act','start'),
        dg=lambda a,s:variant!='no_event' and (a,s)==('act','start'),
        ag=lambda a,s,e:variant!='no_transition' and (a,s,e)==('act','start','end'),
        la=lambda p,a,s,e:(p,a,s,e) in (('body','act','start','end'),('foot','act','start','end')) and
            not(variant=='unaffected_body' and p=='body') and not(variant=='unaffected_foot' and p=='foot') and variant!='other_process',
        hzxy=lambda p,a,s,e:variant!='coincident_relocation' and (p,a,s,e)==(
            'body' if variant=='other_relocated_part' else 'foot','act','start',
            'middle' if variant=='other_relocation_time' else 'end'),
        qv=lambda carrier,place,s:variant!='boundary_only' and (carrier,place,s)==(
            'origin' if variant=='other_carrier' else 'frame','origin' if variant=='body_location_only' else 'destination',
            'start' if variant=='other_exterior_time' else 'end'))
    return v


@lru_cache(None)
def step_questions():
    return fixture(['rqzd','rqze'],PARAMS+
        'q[k rqzd[k jbody[] k jfoot[] k jact[] k jstart[] k jend[]]].'+
        'q[k rqze[k jbody[] k jcarrier[] k jfoot[] k jact[] k jstart[] k jend[]]].')


def source_checks():
    d=step_questions();rows={}
    variants=('baseline','no_initial_contact','no_landing_contact','same_position','gapped_phase','foreign_moving_foot',
        'lost_membership_middle','foreign_supporting_foot','flight_middle','dragging','no_body_motion','no_event','no_transition',
        'unaffected_body','unaffected_foot','other_process','boundary_only','other_carrier','body_location_only','other_exterior_time',
        'coincident_relocation','other_relocated_part','other_relocation_time')
    exterior_only={'boundary_only','other_carrier','body_location_only','other_exterior_time'}
    for name in variants:
        actual=evaluate(d,source_values(d,name),DOMAIN,TIMES,True)
        expected=[name=='baseline' or name in exterior_only,name=='baseline']
        assert actual==expected,(name,actual,expected);rows[name]=actual
    assert evaluate(d,source_values(d),DOMAIN,TIMES)==[True,True]
    return dict(contrasts=rows,ordinary_baseline_agrees=True,pure_memoization_for_contrasts=True,
        boundary_not_outside=True,same_foot_body_process_and_landing_time=True,
        body_center_outside_not_required=True,source_adoption=False)


def binding_checks():
    d=fixture(['rqzg','rqzf'],PARAMS+'r jbindings[] j[a].q[k rqzf[k jbindings[]]].q[t[k rqzg[k jbindings[]]][k jend[]]].')
    rows={};base=('body','frame','foot','act')
    variants={'baseline':base,'empty':(),'short':base[:3],'extra':base+('origin',),
        'swapped_person_and_foot':('foot','frame','body','act'),'swapped_carrier_and_process':('body','act','foot','frame')}
    for name,bindings in variants.items():
        v=source_values(d);v['jbindings']=lambda:SequenceValue(bindings,'"individual"')
        actual=evaluate(d,v,DOMAIN,TIMES,True)
        assert actual==[len(bindings)==4,name=='baseline'],(name,actual);rows[name]=actual
    return dict(contrasts=rows,ordered_fold_executes_actual_goal=True,no_domain_search_for_four_argument_values=True,
        malformed_bindings_not_silently_truncated=True,pure_memoization=True)


def norm_checks():
    d=fixture(['rqzh'],PARAMS+'''
r jsource[] a.r jrole[] a.r jmembers[a] c.r jarguments[a] j[a].r jscene[] d.
q[k rqzh[k jsource[] k jbody[] k jrole[] k jcarrier[] p jmembers p jarguments k jscene[]]].
''');rows=[]
    for first,second in product((False,True),repeat=2):
        for malformed in (False,True):
            v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
            v.update(jbody=lambda:'body',jcarrier=lambda:'frame',jsource=lambda:'source',jrole=lambda:'role',jscene=lambda:'end',
                jfoot=lambda:'foot',jact=lambda:'act',jstart=lambda:'start',jend=lambda:'end',
                jmembers=lambda item:item in ('first','second'),
                jarguments=lambda item:SequenceValue(('otherbody' if malformed and item=='second' else 'body','frame',
                    'foot','actone' if item=='first' else 'acttwo'),'"individual"'),
                h7l=lambda source,person,role,desc,args,polarity,scene:
                    (source,person,role,symbol(desc),polarity,scene)==('source','body','role','rqzg',True,'end') and
                    args.items in ([('body','frame','foot','actone')] if first else [])+([('body','frame','foot','acttwo')] if second else []))
            actual=evaluate(d,v,('first','second','body','frame','foot','actone','acttwo','source','role','otherbody'),TIMES)
            assert actual==[not malformed and not first and not second],(first,second,malformed,actual)
            rows.append(dict(first_allowed=first,second_allowed=second,wrong_body_binding=malformed,values=actual))
    return dict(combinations=rows,all_physical_relations_unknown=True,goal_content_not_executed=True,
        same_body_and_carrier_enforced=True,ordinary_evaluation=True)


def reading():
    previous=json.loads((ROOT/'data/unpermitted-families-reading-v1.json').read_text(encoding='utf-8'))
    paths=(PARENT,PARENT_BASIS,INDEX,'data/unpermitted-families-reading-v1.json',EVIDENCE,
        'artifacts/written-units-v1/kant-1784.json','artifacts/first-cause-reading-v1/page-482.jpg')
    return dict(status='bodily_step_and_exterior_landing_goal_composed_not_yet_source_adopted',reviewer='assistant_review',
        document=FULL,source=previous['source'],source_adoption=False,
        findings=['足の所属と地面側接触を分け、位置差だけで一歩とせず、同じ足の離地・再接地と同じ身体の移動過程を結ぶ。',
            '外部は同じ足の着地点について積極的なqvを要求する。内部でないだけの境界位置や身体の中心位置を代用しない。',
            '四引数の閉じた目標関数を候補別の引数列で指定し、現実の身体関係が未知でも許容の対象として扱える。'],
        interpretation_limits=LIMITS,whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,
        next_required=['原文での候補範囲の指定','勇気を伴う試みを許容の対象とする結合','同じ先行時点の阻止と非字義的な描写',
            'ruhigenとja、一文全体の確認'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def structure():
    old,new=parent(),catalog()
    assert old.document['statements']==new.document['statements'] and len(new.document['statements'])==47
    assert new.document['declarations'][:-10]==old.document['declarations']
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert set(new.entries)-set(old.entries)==set(MEANINGS)|set(PRIMITIVES)
    idx=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    active=load_catalog(ROOT,idx['works']['kant-1784']['meaning_basis'])
    assert selection_binding(active,list(range(47)))==selection_binding(new,list(range(47)))
    for p in idx['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/p).read_text(encoding='utf-8'));ids=[x['index'] for x in r['selection']['statements']]
        assert r['selection']==selection_binding(new,ids)
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('full','compact'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    r=reading();assert r==json.loads((ROOT/READING).read_text(encoding='utf-8'));validate_hashes(ROOT,r['source_sha256'])
    validate(json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8')))
    return dict(active_manuscript_unchanged=True,preserved_statements=47,new_definitions=7,new_primitives=3,
        preserved_review_selections=11,general_library_has_no_primitives=True,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('generic',generic_checks),('source',source_checks),('bindings',binding_checks),('norms',norm_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{READING,DOC,
        'scripts/compose_grounded_step.py','scripts/check_grounded_step.py','scripts/register_grounded_step.py',
        'scripts/fetch_grounded_step_evidence.py','scripts/fetch_pastoral_role_evidence.py','tests/test_grounded_step.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','noema/constructed.py','noema/constructed_semantics.py',
        'noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='grounded_step_goal_and_quoted_family_permission_comparison',document=FULL,**results,
        alignment=dict(**r['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
