"""Verify strong impossibility, same-act conscience and non-executed exit duty."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_conscientious_service_exit import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

DOC='docs/conscientious-service-exit-v1.md'
REPORT='reports/conscientious-service-exit-v1.json'
EVIDENCE='data/conscientious-service-exit-evidence-v1.json'
PRIORS=tuple('reports/'+n+'-v1.json' for n in ('clerical-practical-benefit','perceived-doctrinal-conflict','conscientious-office'))
DOMAIN=('person','role','activity','alternate','source','plan','other','bundle','religion')
SCENES=('reference','actual','good','bad','end','other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r z'+n+'[] d.' for n in SCENES if n!='other')
EXTRA+='r zavailable[a a d] c.r zoutcomes[a a d d] c.r zshown[i c[c]] c.'
EXTRA+='r zfoundrecord[i[e]] c.r zpremiserecord[i[h[d] c]] c.'
ARGS='k zperson[] k zrole[] k zreference[] k zactual[]'
ACTION='k zperson[] k zrole[] k zactivity[] k zreference[] k zgood[]'
SEQ='l[a][k zperson[] k zrole[]]'
EXIT='t[k r43x[k zperson[] k zrole[] k zactivity[]]][k zactual[]]'
TARGET='t[k r43y['+SEQ+' k zreference[]]][k zactual[]]'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(query=None,boundary=False):
    doc=deepcopy(catalog().document);doc['statements']=[];seen={d['name'] for d in doc['declarations']}
    doc['declarations'] += [d for d in closure(parent().document,['xg']) if d['name'] not in seen]
    if boundary:
        d=next(d for d in doc['declarations'] if d['name']=='r43x')
        d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    if query is None:query=''.join('q[k '+name+'['+ARGS+']].' for name in ('r43v','r43w','r43z','r432'))
    return parse(format_graph(doc,'compact')+EXTRA+query)


def model(doc,selected=('good','bad'),performed=('good','bad'),allowed=(),exit=True,duty=True,variant='baseline'):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES) if n!='other'});v['zother']=lambda:'other'
    seen=dict(service=[],conscience=[],cases=[],demands=[],termination=[])
    def match(actual,wanted,category,fields):
        wanted=list(wanted)
        for i,name in enumerate(fields):
            if variant==category+'_'+name:wanted[i]='other'
        return tuple(actual)==tuple(wanted)
    def holding(person,role,point):
        return match((person,role),('person','role'),'holding',('person','role')) and point!='end' and not (variant=='not_in_office' and point=='actual') or (
            variant=='still_holds_at_end' and (person,role,point)==('person','role','end'))
    v['cf']=holding
    v['cb']=lambda person,act,role,point:match((person,act,role),('person','activity','role'),'position',('person','activity','role'))
    def classification(role,act,ref):
        seen['service'].append((role,act,ref))
        return match((role,act,ref),('role','activity','reference'),'classification',('role','activity','reference'))
    v['h2522']=classification
    v['cg']=lambda person,act,point:match((person,act),('person','activity'),'performance',('person','activity')) and point in performed
    def conscience(person,act,ref,point):
        seen['conscience'].append((person,act,ref,point))
        expected='alternate' if variant=='split_activity' else 'activity'
        return point in allowed and match((person,act,ref),('person',expected,'reference'),'conscience',('person','activity','reference'))
    v['h252j']=conscience
    def candidate(person,role,ref,actual,point):
        seen['cases'].append((person,role,ref,actual,point))
        return point in selected and match((person,role,ref,actual),('person','role','reference','actual'),
            'selection',('person','role','reference','actual'))
    v['h2523']=candidate
    v['ia']=lambda person,anchor,point:person=='person' and point in (('actual','end') if anchor=='actual' else (anchor,))
    v['ic']=lambda earlier,later,anchor:(earlier,later,anchor)==('actual','end','actual') and variant!='reversed_time'
    v['ag']=lambda act,earlier,later:exit and match((act,earlier,later),('activity','actual','end'),'change',('activity','earlier','later'))
    v['la']=lambda person,act,earlier,later:match((person,act,earlier,later),('person','activity','actual','end'),'affected',('person','activity','earlier','later'))
    v['df']=lambda person,act,point:match((person,act,point),('person','activity','end'),'actor',('person','activity','point'))
    def terminates(act,role,person,earlier,later):
        seen['termination'].append((act,role,person,earlier,later))
        return variant!='dismissal_only' and match((act,role,person,earlier,later),('activity','role','person','actual','end'),
            'termination',('activity','role','person','earlier','later'))
    v['h2524']=terminates
    v['h2525']=lambda person,role,ref:'source' if match((person,role,ref),('person','role','reference'),'source',('person','role','reference')) else 'other'
    def demand(source,person,role,code,bindings,ref,positive,point):
        seen['demands'].append((source,person,role,symbol(code),code.rank,tuple(bindings.items),ref,positive,point))
        expected=['source','person','role','r43y',1,('person','role'),'reference',True,'actual']
        fields=('source','person','role','code','rank','bindings','reference','polarity','point')
        if variant.startswith('demand_'):
            field=variant[7:];i=fields.index(field)
            expected[i]=False if field=='polarity' else 0 if field=='rank' else ('role','person') if field=='bindings' else 'other'
        return duty and seen['demands'][-1]==tuple(expected)
    v['h237z']=demand
    v['zavailable']=lambda person,plan,point:(person,plan,point)==('person','plan','actual')
    v['zoutcomes']=lambda person,plan,start,end:(person,plan,start)==('person','plan','actual') and end in ('good','bad')
    return v,seen


def run(doc,pair,domain=DOMAIN,scenes=SCENES):return evaluate(doc,pair[0],domain,scenes,True)


@lru_cache(None)
def service_checks():
    d=fixture('q[k r43s['+ACTION+']].q[k r43t['+ACTION+']].q[t[k r43u[k zperson[] k zrole[] k zreference[]]][k zgood[]]].')
    rows={}
    variants=('baseline','holding_person','holding_role','position_person','position_activity','position_role',
        'classification_role','classification_activity','classification_reference','performance_person','performance_activity',
        'conscience_person','conscience_activity','conscience_reference','split_activity')
    for variant in variants:
        result=run(d,model(d,allowed=('good',),variant=variant))
        expected=[True,True,True] if variant=='baseline' else [True,False,False] if variant.startswith('conscience_') or variant=='split_activity' else [False,False,False]
        assert result==expected,(variant,result);rows[variant]=result
    assert run(d,model(d,allowed=('good',),performed=('bad',)))==[False,False,False]
    for name in ('cf','cb','cg','h2522','h252j'):
        pair=model(d,allowed=('good',));pair[0][name]=unknown
        try:run(d,pair)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,same_activity_for_service_and_conscience=True,unknown_refused=True)


@lru_cache(None)
def possibility_checks():
    d=fixture();rows=[]
    for bits in product((False,True),repeat=6):
        selected=tuple(p for p,b in zip(('good','bad'),bits[:2]) if b)
        performed=tuple(p for p,b in zip(('good','bad'),bits[2:4]) if b)
        allowed=tuple(p for p,b in zip(('good','bad'),bits[4:]) if b)
        possible=bool(set(selected)&set(performed)&set(allowed));impossible=bool(selected) and not possible
        result=run(d,model(d,selected=selected,performed=performed,allowed=allowed))
        assert result==[possible,impossible,True,impossible],(bits,result)
        rows.append([*bits,*result])
    for variant in ('selection_person','selection_role','selection_reference','selection_actual','not_in_office'):
        result=run(d,model(d,variant=variant));assert result[:2]==[False,False],(variant,result)
    # One possible good outcome defeats impossibility even when no available
    # method guarantees success in all assessed outcomes (the old xg criterion).
    compare=fixture('q[k xg[k zperson[] k r43u[k zperson[] k zrole[] k zreference[]] k zactual[] p zavailable p zoutcomes p zoutcomes]].'
        +'q[k r43v['+ARGS+']].q[k r43w['+ARGS+']].')
    result=run(compare,model(compare,allowed=('good',)));assert result==[True,True,False],result
    pair=model(d);pair[0]['h2523']=unknown
    try:run(d,pair)
    except ValueError as error:assert 'Unknown' in str(error),str(error)
    else:raise AssertionError('Unknown candidate range')
    return dict(selection_service_conscience_table=rows,empty_not_impossible=True,any_possible_good_service_defeats_impossibility=True,
        no_guaranteed_method_distinguished_from_no_possible_service=result,unknown_range_refused=True)


@lru_cache(None)
def departure_checks():
    d=fixture('q['+EXIT+'].');rows={}
    for variant in ('baseline','holding_person','holding_role','not_in_office','still_holds_at_end','reversed_time',
        'change_activity','change_earlier','change_later','affected_person','affected_activity','affected_earlier','affected_later',
        'actor_person','actor_activity','actor_point','termination_activity','termination_role','termination_person',
        'termination_earlier','termination_later','dismissal_only'):
        result=run(d,model(d,variant=variant));assert result==[variant=='baseline'],(variant,result);rows[variant]=result
    assert run(d,model(d,exit=False))==[False]
    # Evaluate the complete target natively once in the focused history model.
    # The binder has a separate typed-boundary check, avoiding repeated full
    # history evaluation for every unrelated person/role/activity combination.
    focused_people=('person','role','activity');focused_scenes=('actual','end')
    target=fixture('q['+TARGET+'].');focused=model(target);focused[0]['zreference']=lambda:'actual'
    assert run(target,focused,focused_people,focused_scenes)==[True]
    for seq in (SEQ,'l[a][]','l[a][k zperson[]]','l[a][k zrole[] k zperson[]]','l[a][k zperson[] k zrole[] k zactivity[]]'):
        q=fixture('q[t[k r43y['+seq+' k zreference[]]][k zactual[]]].',True);pair=model(q)
        pair[0]['zreference']=lambda:'actual'
        pair[0]['r43x']=lambda person,role,act:Content(focused_scenes,((person,role,act)==('person','role','activity'),False))
        assert run(q,pair,focused_people,focused_scenes)==[seq==SEQ],seq
    for name in ('cf','ia','ic','ag','la','df','h2524'):
        pair=model(d);pair[0][name]=unknown
        try:run(d,pair)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,native_hzby_rhd_rhc_rcf_evaluated=True,same_future_self_termination=True,
        duty_target_binding_order_and_lengths_checked=True,binder_boundary='r43x',
        full_target_native_focused_history=True,unknown_refused=True)


@lru_cache(None)
def duty_checks():
    d=fixture('q[k r43z['+ARGS+']].');rows={}
    for variant in ('baseline','source_person','source_role','source_reference','demand_source','demand_person','demand_role',
        'demand_code','demand_rank','demand_bindings','demand_reference','demand_polarity','demand_point','not_in_office'):
        result=run(d,model(d,exit=False,variant=variant));assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
    for departure,duty in product((False,True),repeat=2):
        pair=model(d,exit=departure,duty=duty)
        assert run(d,pair)==[duty] and not pair[1]['termination']
    pair=model(d)
    for name in ('ia','ic','ag','la','df','h2524','h2522','h2523','h252j','cg','cb'):pair[0][name]=unknown
    assert run(d,pair)==[True]
    for name in ('cf','h2525','h237z'):
        pair=model(d);pair[0][name]=unknown
        try:run(d,pair)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    q=fixture('q[k zshown[r c[k r432['+ARGS+']]]].');pair=model(q)
    for name in pair[0]:pair[0][name]=unknown
    pair[0]['zshown']=lambda code:code.rank==2 and json.loads(code.syntax)['symbol']=='r432'
    assert run(q,pair)==[True]
    return dict(contrasts=rows,normative_content_not_executed=True,actual_departure_independent_of_duty=True,
        exact_rank_one_positive_demand=True,complete_consequent_can_be_quoted_at_rank_two=True,unknown_refused=True)


@lru_cache(None)
def conditional_checks():
    names='r[k zperson[]] r[k zbundle[]] r[k zreligion[]] r[k zreference[]]'
    args='k zperson[] k zrole[] k zbundle[] k zreligion[] k zreference[] '+names+' k zactual[]'
    saved='q[k zfoundrecord[k r43o['+names+']]].q[k zpremiserecord[k r43q['+names+']]].'
    d=fixture(saved+'q[k r433['+args+']].');rows={}
    for variant in ('baseline','empty_hypotheses','missing_first_belief','missing_second_belief',
        'missing_first_duty','missing_second_duty','possible_first_service','possible_second_service','wrong_person','wrong_role','wrong_reference','wrong_actual'):
        pair=model(d,performed=('reference','other'));v,seen=pair;records={}
        def save(name,code):records[name]=code;return code.rank==0
        v['zfoundrecord']=lambda c:save('found',c);v['zpremiserecord']=lambda c:save('premise',c)
        v['h233c']=lambda person,code,point:person=='person' and code.syntax==records['found'].syntax and point in (
            ('bad',) if variant=='missing_first_belief' else ('good',) if variant=='missing_second_belief' else ('good','bad'))
        v['hzko']=lambda person,code,actual,point:variant!='empty_hypotheses' and person=='person' and actual==('other' if variant=='wrong_actual' else 'actual') and code.syntax==records['premise'].syntax and point in ('good','bad')
        def candidates(person,role,ref,actual,point):
            seen['cases'].append((person,role,ref,actual,point))
            return (person,role,ref)==('other' if variant=='wrong_person' else 'person','other' if variant=='wrong_role' else 'role',
                'other' if variant=='wrong_reference' else 'reference') and (actual,point) in (('good','reference'),('bad','other'))
        v['h2523']=candidates
        v['h252j']=lambda person,act,ref,point:(person,act,ref)==('person','activity','reference') and (
            (variant,point) in (('possible_first_service','reference'),('possible_second_service','other')))
        def demand(source,person,role,code,bindings,ref,positive,point):
            seen['demands'].append((source,person,role,symbol(code),code.rank,tuple(bindings.items),ref,positive,point))
            return (source,person,role,symbol(code),code.rank,tuple(bindings.items),ref,positive)==('source','person','role','r43y',1,('person','role'),'reference',True) and point in (
                ('bad',) if variant=='missing_first_duty' else ('good',) if variant=='missing_second_duty' else ('good','bad'))
        v['h237z']=demand
        result=run(d,pair);assert result==[True,True,variant=='baseline'],(variant,result);rows[variant]=result[-1]
        assert not seen['termination']
        if variant=='baseline':
            assert {'good','bad'} <= {r[3] for r in seen['cases']}
            assert {'good','bad'} <= {r[-1] for r in seen['demands']}
    return dict(contrasts=rows,native_r43r_and_complete_consequent_connected=True,
        practical_candidates_start_from_each_hypothetical_case=True,belief_and_duties_not_required_at_actual=True,
        actual_departure_not_executed=True)


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();prior_entries=old.entries|dependency().entries
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==prior_entries[n]['declaration'] and e['meaning_ja']==prior_entries[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for path in PRIORS:validate_hashes(ROOT,read(path)['source_sha256'])
    for p in read(EVIDENCE)['pages']:assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        no_source_sentence_added=True,primary_evidence_pinned=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    results={}
    for name,fn in [('service',service_checks),('possibility',possibility_checks),('departure',departure_checks),('duty',duty_checks),('conditional',conditional_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,EVIDENCE,*[p['path'] for p in read(EVIDENCE)['pages']],
        'scripts/compose_conscientious_service_exit.py','scripts/check_conscientious_service_exit.py','tests/test_conscientious_service_exit.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_protected_remarks.py',
        'scripts/compose_perceived_doctrinal_conflict.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='conscientious_service_impossibility_and_required_self_departure',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
