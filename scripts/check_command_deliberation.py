"""Check appraisal criteria separately from nonfactive intended discussion."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_command_deliberation import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_officer_command_binding import model as officer_model,EXTRA as OFFICER_EXTRA,DOMAIN as OFFICER_DOMAIN

REPORT='reports/command-deliberation-v1.json'
DOC='docs/command-deliberation-v1.md'
PRIOR=('reports/officer-command-binding-v1.json','reports/qualitative-influence-v1.json')
STATES=tuple(product((False,True),repeat=2))
POINTS=('offlow','offhigh','onlow','onhigh')
SCENES=('reference',*POINTS)
DOMAIN=('person','action','notice','institution','factor','result','other')
EXTRA=OFFICER_EXTRA+'r zdiscussion[] a.r zvariables[] j[a].r zequations[a h[a] c] c.r zfactor[] a.r zview[h[a] c] d.r zchecked[h[a] c] c.r zatleast[h[a] c h[a] c] c.'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(kind,sign=True):
    roots={'profile':['r32p'],'appraisals':['r32q','r32r'],'questions':['r32s','r32t'],'discussion':['r32u'],'bound':['r32v']}[kind]
    doc=deepcopy(catalog().document)
    if kind in ('appraisals','questions'):
        # Supply an actual closed quotation to the goal provider. Its content
        # remains unknown, so reading that content would make the checks fail.
        replacement=parse('p:r ztruth[d] c.d zgoal[] e[b point[k ztruth[v point]]].'
                          'd h242y[notice a reference d] i[e][r[k zgoal[]]].')['declarations']
        index=next(i for i,d in enumerate(doc['declarations']) if d['name']=='h242y')
        doc['declarations'][index:index+1]=replacement
    doc.update(declarations=closure(doc,roots),statements=[])
    polarity='e[k zperson[]][k zperson[]]' if sign else 'u[e[k zperson[]][k zperson[]]]'
    if kind=='profile':
        query='q[k r32p[k zperson[] k zaction[] '+polarity+' k zvariables[] p zequations k zfactor[] p zchecked p zatleast p zview]].'
    elif kind in ('appraisals','questions'):
        args='k zperson[] k zaction[] k znotice[] k zinstitution[] '+polarity+' k zref[]'
        query=''.join(('l[k '+n+'['+args+']].' if kind=='questions' else 'q[t[k '+n+'['+args+']][k zref[]]].') for n in roots)
    elif kind=='discussion':
        query='q[k r32u[k zperson[] k zoffice[] k zinstitution[] k znotice[] k zaction[] '+polarity+' k zdiscussion[] k zref[]]].'
    else:
        query='q[k r32v[k zperson[] k zoffice[] k zinstitution[] k zissuer[] k zhigher[] k znotice[] k zaction[] '+polarity+' k zdiscussion[] k zref[]]].'
    return parse(format_graph(doc,'compact')+EXTRA+query)


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    for n in ('person','issuer','office','higher','institution','notice','action','discussion','other'):
        v['z'+n]=lambda n=n:n
    v['zref']=lambda:'reference'
    return v


def key(state):return bool(state('factor')),bool(state('result'))


def profile_model(doc,sign=True,table=(False,False,False,False),grades=(1,1,2,2),variant='baseline'):
    v=base(doc)
    v.update(zvariables=lambda:SequenceValue(('factor','result'),'"individual"'),zfactor=lambda:'factor',
        zequations=lambda item,state:table[STATES.index(key(state))] if item=='result' else False,
        zview=lambda state:POINTS[STATES.index(key(state))],
        zchecked=lambda state:not (variant=='unassessed' and key(state)==(True,False)),
        zatleast=lambda left,right:grades[STATES.index(key(left))]>=grades[STATES.index(key(right))],
        cg=lambda p,a,s:(p,a)==('person','other' if variant=='other_action' else 'action') and s in POINTS and (
            STATES[POINTS.index(s)][0] if sign or variant=='wrong_negative_direction' else not STATES[POINTS.index(s)][0]))
    return v


@lru_cache(None)
def profile_checks():
    rows={}
    for sign in (False,True):
        doc=fixture('profile',sign)
        for name,table,grades,expected in (
            ('improves',(False,)*4,(1,1,2,2),True),
            ('equal_only',(False,)*4,(1,1,1,1),False),
            ('worse',(False,)*4,(2,2,1,1),False),
            ('mixed',(False,True,False,True),(1,3,2,2),False),
            ('gain_with_ties',(False,True,False,True),(1,1,1,2),True),
            ('no_on_solution',(False,False,True,False),(1,1,2,2),False)):
            actual=evaluate(doc,profile_model(doc,sign,table,grades),DOMAIN,SCENES,True)
            assert actual==[expected],(sign,name,actual)
            rows[str((sign,name))]=actual[0]
        for variant in ('unassessed','other_action')+(() if sign else ('wrong_negative_direction',)):
            actual=evaluate(doc,profile_model(doc,sign,variant=variant),DOMAIN,SCENES,True)
            assert actual==[False],(sign,variant,actual)
            rows[str((sign,variant))]=actual[0]
    return dict(contrasts=rows,native_signed_content_alignment_and_improvement=True,
                negative_command_content_is_nonexecution=True)


def appraisal_model(doc,goal_better=True,benefit_better=True,variant='baseline'):
    v=profile_model(doc)
    v.update(h242z=lambda notice,point:v['zvariables'](),
        h243a=lambda notice,point,item,state:v['zequations'](item,state),
        h243b=lambda notice,point:'factor',h243c=lambda notice,point,state:v['zview'](state),
        h243d=lambda goal,ref,point:(symbol(goal),ref)==('zgoal','reference') and point in POINTS,
        h243e=lambda goal,ref,left,right:(symbol(goal),ref)==('zgoal','reference') and (
            (left in ('onlow','onhigh'))>=(right in ('onlow','onhigh')) if goal_better else True),
        h243f=lambda institution,ref,point:(institution,ref)==(
            'other' if variant=='other_beneficiary' else 'institution','reference') and point in POINTS,
        h243g=lambda institution,ref,left,right:(institution,ref)==('institution','reference') and (
            (left in ('onlow','onhigh'))>=(right in ('onlow','onhigh')) if benefit_better else True))
    return v


@lru_cache(None)
def appraisal_checks():
    doc,rows=fixture('appraisals'),[]
    for goal,benefit in product((False,True),repeat=2):
        v=appraisal_model(doc,goal,benefit)
        assert v['ztruth'] is unknown
        seen={n:set() for n in ('h242z','h243a','h243b','h243c')}
        for name in seen:
            original=v[name]
            def provider(*args,name=name,original=original):
                seen[name].add(args[:2]);return original(*args)
            v[name]=provider
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[goal,benefit],(goal,benefit,actual)
        assert all(values and all(n=='notice' and p in SCENES for n,p in values) for values in seen.values())
        rows.append(dict(goal=goal,benefit=benefit,values=actual))
    assert evaluate(doc,appraisal_model(doc,variant='other_beneficiary'),DOMAIN,SCENES,True)==[True,False]
    questions=fixture('questions')
    actual=evaluate(questions,appraisal_model(questions,True,False),DOMAIN,SCENES,True)
    assert [m.force for m in actual]==['ask','ask']
    assert all(actual[0].content.values) and not any(actual[1].content.values)
    return dict(independent_criteria=rows,same_command_model=True,other_beneficiary_refused=True,
                goal_truth_not_executed=True,native_questions_constructed=True)


def discussion_model(doc,flags=(True,True,True),variant='baseline',sign=True):
    purpose,utility,intent=flags
    v=officer_model(doc,'baseline',sign);v['zdiscussion']=lambda:'discussion'
    v.update(ca=lambda p,a,r:(p,a,r)==('person','discussion','reference'),
        h232p=lambda a,r:variant!='not_reasoning' and (a,r)==('discussion','reference'),
        cb=lambda p,a,role,r:(p,a,role,r)==('person','discussion','office','reference'),
        h243i=lambda p,a,r:intent and (p,a,r)==('other' if variant=='other_intending_person' else 'person','discussion','reference'),
        h243j=lambda p,a,role,i,r:(p,a,role,i,r)==('person','discussion',
            'other' if variant=='outside_office' else 'office','institution','reference'),
        h243k=lambda a,r:variant!='silent_only' and (a,r)==('discussion','reference'))
    def topic(discussion,person,action,notice,institution,polarity,code,ref):
        which=symbol(code)
        selected=purpose if which=='r32s' else utility if which=='r32t' else False
        return selected and (discussion,person,action,notice,institution,polarity,code.rank,ref)==(
            'discussion','person','other' if variant=='other_discussed_action' else 'action',
            'other' if variant=='other_discussed_notice' else 'notice','institution',
            not sign if variant=='other_discussed_polarity' else sign,0,'reference')
    v['h243h']=topic
    return v


@lru_cache(None)
def discussion_checks():
    doc,rows=fixture('discussion'),[]
    for flags in product((False,True),repeat=3):
        v=discussion_model(doc,flags)
        actual=evaluate(doc,v,OFFICER_DOMAIN+('discussion',),SCENES,True)
        assert actual==[(flags[0] or flags[1]) and flags[2]],(flags,actual)
        assert all(v[n] is unknown for n in ('h242y','h242z','h243a','h243d','h243g','cg'))
        rows.append(dict(flags=list(flags),value=actual[0]))
    contrasts={}
    for variant in ('not_reasoning','other_intending_person','outside_office','silent_only','other_discussed_action','other_discussed_notice','other_discussed_polarity'):
        actual=evaluate(doc,discussion_model(doc,variant=variant),OFFICER_DOMAIN+('discussion',),SCENES,True)
        assert actual==[False],(variant,actual);contrasts[variant]=actual[0]
    return dict(combinations=rows,contrasts=contrasts,inclusive_alternative_topics=True,
                appraisals_and_execution_not_evaluated=True)


@lru_cache(None)
def bound_checks():
    rows={}
    for sign in (False,True):
        doc=fixture('bound',sign)
        for variant in ('baseline','other_discussed_notice','other_discussed_action','other_discussed_polarity','outside_office','silent_only'):
            v=discussion_model(doc,variant=variant,sign=sign)
            assert not v['dg']('discussion','reference')
            actual=evaluate(doc,v,OFFICER_DOMAIN+('discussion',),SCENES,True)
            assert actual==[variant=='baseline'],(sign,variant,actual)
            rows[str((sign,variant))]=actual[0]
    return dict(contrasts=rows,native_same_officer_and_command=True,discussion_occurrence_not_required=True)


@lru_cache(None)
def unknown_checks():
    doc=fixture('discussion')
    names=('h243h','h243i','h243j','h243k')
    for name in names:
        v=discussion_model(doc);v[name]=unknown
        try:evaluate(doc,v,OFFICER_DOMAIN+('discussion',),SCENES,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(unknown_inputs_refused=list(names))


@lru_cache(None)
def structure_checks():
    new=catalog();old={n:e for c in parents() for n,e in c.entries.items()}
    assert not new.document['statements']
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for p in PRIOR:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,s in build().items():assert (ROOT/p).read_text(encoding='utf-8')==s,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    return dict(new_definitions=8,new_primitives=13,new_semantic_reviews=0,unchanged_active_manuscript=True,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,s in build().items():write_exact(ROOT/p,s)


def build_report():
    results={}
    for name,fn in [('profile',profile_checks),('appraisals',appraisal_checks),('discussion',discussion_checks),
                    ('bound',bound_checks),('unknown',unknown_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set().union(*(set(c.source_sha256) for c in parents()))|{
        DOC,*PRIOR,'scripts/compose_command_deliberation.py','scripts/check_command_deliberation.py','tests/test_command_deliberation.py',
        'scripts/check_officer_command_binding.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='intended_in_service_deliberation_about_signed_command_appraisals',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
