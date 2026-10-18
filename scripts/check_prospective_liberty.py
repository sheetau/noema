"""Check sustained permission and future completion without past-result reuse."""
import argparse
from copy import deepcopy
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.grammar import number_word
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_audience_liberty as prior
from scripts.check_described_explanations import symbol
from scripts.compose_prospective_liberty import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,MEANINGS,build

REPORT=ROOT/'reports/prospective-liberty-v1.json'
SCENES=(*prior.SCENES,'actual')


def generic_document(query):
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zhistory[d] c.r zbefore[d d] c.r zinitial[] d.r zcondition[d] c.r zchange[a d d] c.
'''+query)


def generic_checks():
    points=('past','now','middle','later');people=('process','other')
    permission=generic_document('q[k rqtc[p zhistory p zbefore k zinitial[] p zcondition]].')
    event=generic_document('q[k rqtd[p zhistory p zbefore k zinitial[] p zchange]].')
    def model(initial='now',allowed=points,start='now',end='later',present=True,history=None):
        history=set(points if history is None else history)
        return dict(zhistory=lambda p:p in history,zbefore=lambda a,b:points.index(a)<points.index(b),
            zinitial=lambda:initial,zcondition=lambda p:p in allowed,
            zchange=lambda process,first,last:present and (process,first,last)==('process',start,end))
    permissions=0;events=0
    for initial,flags in product(points,product((False,True),repeat=4)):
        allowed={p for p,flag in zip(points,flags) if flag}
        future={p for p in points if points.index(p)>points.index(initial)}
        actual=prior.prior.evaluate(permission,model(initial,allowed),people,points)
        assert actual==[bool(future) and {initial,*future}<=allowed]
        permissions+=1
    for initial,start,end,present in product(points,points,points,(False,True)):
        actual=prior.prior.evaluate(event,model(initial,start=start,end=end,present=present),people,points)
        assert actual==[present and points.index(start)<points.index(end) and points.index(initial)<points.index(end)]
        events+=1
    contrasts={}
    for label,history,initial in (('empty',(), 'now'),('missing_initial',('past','later'),'now'),
        ('no_future',('past','now'),'now'),('valid_future',points,'now')):
        values=model(initial,history=history)
        actual=prior.prior.evaluate(permission,values,people,points)
        assert actual==[label=='valid_future'];contrasts[label]=actual
    values=model();values['zbefore']=lambda a,b:a!=b
    assert prior.prior.evaluate(permission,values,people,points)==[False]
    for name,doc in (('zhistory',permission),('zbefore',permission),('zcondition',permission),('zchange',event)):
        values=model();values[name]=prior.prior.unknown
        try:prior.prior.evaluate(doc,values,people,points)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(permission_time_combinations=permissions,event_time_combinations=events,history_contrasts=contrasts,
        cyclic_order_refused=True,already_underway_event_allowed=True,completed_at_or_before_initial_refused=True,
        unknown_inputs_refused=4,semantic_evaluation_uncached=True)


def joint_document():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));doc['statements']=[]
    text=format_graph(doc,'compact')+'''
r zaudience[] a.r zreference[] d.r zsource[] a.r zwithdrawn[] a.r zframe[] a.r zinitial[] d.r zlate[] d.r zbranch[] d.
r zactual[] d.r zactualsource[] a.r zorigins[d] d.r zlateorigins[d] d.r zactualorigins[d] d.
r zextent[h[a] c h[a] c] c.r zcases[d] c.r zinvalidcases[d] c.
r zscale[a] c.r zless[a a] c.r znear[a] c.r zlow[] a.r zhigh[] a.r zdegree[] a.
r zcheckpoint[b c] c.
'''
    fixed='k zaudience[] k zreference[] '
    condition=lambda source,branch:'k hznf['+fixed+'k '+source+'[] k zframe[] k zinitial[] '+branch+']'
    goal=lambda initial,branch:'k hzng['+fixed+'k zframe[] '+initial+' v extent '+branch+']'
    modal=lambda source,cases,origins='zorigins':'k hznh['+fixed+'k '+source+'[] k zframe[] p '+origins+' v extent p '+cases+' p zscale p zless p znear k zlow[] k zhigh[] k zdegree[]]'
    expressions=['k hzne[k zframe[] k zinitial[] k zreference[]]',condition('zsource','k zreference[]'),
        condition('zwithdrawn','k zreference[]'),goal('k zinitial[]','k zreference[]'),
        goal('k zlate[]','k zreference[]'),goal('k zinitial[]','k zbranch[]'),
        modal('zsource','zcases'),modal('zwithdrawn','zcases'),modal('zsource','zinvalidcases')]
    # Without the independent history-validity guard, the invalid candidate
    # disappears through a false condition and the modal judgment stays true.
    expressions.append('k rqsu[p zinvalidcases i[branch d]['+condition('zsource','v branch')+'] '
        'i[branch d]['+goal('k zinitial[]','v branch')+'] p zscale p zless p znear k zlow[] k zhigh[] k zdegree[]]')
    expressions += [modal('zsource','zcases','zlateorigins'),
        'k hzna['+fixed+'k zsource[] k zactual[]]',
        'k hzna['+fixed+'k zactualsource[] k zactual[]]',
        modal('zactualsource','zcases'),'k hzne[k zframe[] k zactual[] k zreference[]]']
    expected=[True,True,False,True,False,False,True,False,False,True,False,False,True,True,False]
    expressions=['k zcheckpoint[n p '+number_word(i)+' b '+expression+']' for i,expression in enumerate(expressions,1)]
    truth='e[k zaudience[]][k zaudience[]]'
    wanted='l[c]['+' '.join(truth if v else 'u['+truth+']' for v in expected)+']'
    text+='q[e[c[i[extent h[h[a] c h[a] c] c][l[c]['+' '.join(expressions)+']]][p zextent]]['+wanted+']].'
    return parse(text),expected


def model(doc,observed=None,progress=None):
    values=prior.model(doc,'actual_permission')
    # The actual scene is separate from all hypothetical histories. Complete
    # negative facts there extend the finite fixture, not the language rules.
    # Actual execution remains unavailable: normative tests must not run it.
    for declaration in doc['declarations']:
        if declaration['kind']!='primitive' or declaration['result']!='truth' or declaration['name']=='cg':continue
        positions=[i for i,sort in enumerate(declaration['parameters']) if sort=='situation']
        if not positions:continue
        original=values[declaration['name']]
        values[declaration['name']]=lambda *args,_positions=positions,_original=original:False if any(args[i]=='actual' for i in _positions) else _original(*args)
    values.update(zwithdrawn=lambda:'other',zframe=lambda:'group',zinitial=lambda:'before',zlate=lambda:'end',
        zbranch=lambda:'end',zinvalidcases=lambda point:point in prior.SCENES,
        zactual=lambda:'actual',zactualsource=lambda:'faculty',zactualorigins=lambda branch:'actual')
    def origin(branch,late=False):
        point='end' if late and branch=='anchor' else 'before'
        if observed is not None:observed.add(('origin',branch,point))
        return point
    values['zorigins']=origin;values['zlateorigins']=lambda branch:origin(branch,True)
    def checkpoint(index,value):
        if progress:progress('Native contrast '+str(int(index))+' evaluated: '+str(value))
        return value
    values['zcheckpoint']=checkpoint
    def history(frame,branch,point):
        if observed is not None:observed.add(('history',frame,branch))
        return frame=='group' and point in prior.SCENES and branch in prior.SCENES and prior.SCENES.index(point)<=prior.SCENES.index(branch)
    values['h7q']=history
    def allowed(source,person,role,act,description,sign,point):
        match=(person,act,role) in {('person','process','faculty'),('other','part','plan')}
        permit=(source=='faculty') if point=='actual' else (source in ('group','faculty') or source=='other' and point!='end')
        return match and symbol(description)=='zzq' and sign and permit
    values['h7b']=allowed;values['h7a']=lambda *args:False
    for name in ('h6t','cb'):
        original=values[name]
        def tracked(*args,_name=name,_original=original):
            if observed is not None:observed.add((_name,args[-1]))
            return _original(*args)
        values[name]=tracked
    return values


def native_checks(progress=None):
    doc,expected=joint_document();seen=set();values=model(doc,seen,progress)
    filtered={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    result=[r['value'] for r in evaluate_document(doc,individuals=prior.DOMAIN,situations=SCENES,
        primitives=filtered,max_steps=360000000,memoize_definitions=True,memoize_expressions=True)]
    assert result==[True],(expected,result)
    assert all(row[1]=='anchor' for row in seen if row[0] in ('h6t','cb'))
    assert {row[1] for row in seen if row[0]=='history'}=={'group'}
    assert ('origin','anchor','end') in seen and ('origin','end','before') in seen
    return dict(verified_result_vector=expected,
        vector_order=['valid_history','sustained_permission','withdrawn_permission','later_completed_change',
            'already_completed_change','different_candidate_change','conditional_future_change',
            'withdrawn_policy_conditional','invalid_candidate_guarded','invalid_candidate_without_guard',
            'candidate_specific_late_boundary','actual_permission_absent','actual_permission_present',
            'same_hypothetical_policy_actual_permission_present','actual_point_outside_candidate_history'],
        population_and_activity_reference_fixed=True,same_frame_for_all_candidates=True,
        candidate_origins_used_by_validity_condition_and_goal=True,actual_permission_not_inferred=True,
        native_capacity_and_causation_definitions_preserved=True,source_definitions_not_replaced_or_lowered=True,
        memoized=True,max_steps=360000000)


def unknown_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));doc['statements']=[]
    text=format_graph(doc,'compact')+'r zaudience[] a.r zreference[] d.r zsource[] a.r zframe[] a.r zinitial[] d.'
    doc=parse(text+'q[k hznf[k zaudience[] k zreference[] k zsource[] k zframe[] k zinitial[] k zreference[]]].')
    for name in ('h7q','h7b'):
        values=model(doc);values[name]=prior.prior.unknown
        try:prior.prior.evaluate(doc,values,prior.DOMAIN,SCENES,memoize=True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    mapped,_=joint_document();mapped['statements']=[]
    mapped=parse(format_graph(mapped,'compact')+'q[k hznh[k zaudience[] k zreference[] k zsource[] k zframe[] p zorigins p zextent p zcases p zscale p zless p znear k zlow[] k zhigh[] k zdegree[]]].')
    values=model(mapped);values['zorigins']=prior.prior.unknown
    try:prior.prior.evaluate(mapped,values,prior.DOMAIN,SCENES,memoize=True)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('unknown candidate origin')
    return dict(unknown_history_and_permission_refused=True,unknown_candidate_origin_refused=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==32
    assert new.document['declarations'][:-7]==old.document['declarations']
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    core=load_catalog(ROOT,BASIS,document_path=CORE)
    assert {'ta','h7q','ic','hzna','hzmy','rqsu'}<=set(core.entries)
    assert not {'mp','h6e','h6g','h6n'}&set(core.entries)
    modal=new.entries['hznh']['declaration'];origin=modal['parameters'][4]
    assert origin['sort']=={'kind':'function','parameters':['situation'],'result':'situation'}
    bindings=[]
    def inspect(node):
        if isinstance(node,dict):
            if node.get('kind')=='call' and node.get('symbol') in ('hzne','hznf','hzng'):
                position={'hzne':1,'hznf':4,'hzng':3}[node['symbol']]
                mapped=node['arguments'][position]
                assert mapped=={'kind':'apply','function':{'kind':'variable','name':origin['name']},'arguments':[node['arguments'][-1]]}
                bindings.append(node['symbol'])
            for value in node.values():inspect(value)
        elif isinstance(node,list):
            for value in node:inspect(value)
    inspect(modal['body']);assert sorted(bindings)==['hzne','hznf','hzng']
    return dict(new_definitions=7,new_primitives=0,existing_statements=32,seven_review_bindings_preserved=True,
        same_candidate_origin_bound_in_validity_condition_and_goal=True,
        generic_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report(progress=None):
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    cat=load_catalog(ROOT,BASIS)
    previous=json.loads((ROOT/'reports/audience-liberty-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,previous['source_sha256'])
    alignment=deepcopy(previous['alignment']);alignment.update(definitions=list(MEANINGS),remaining=[
        'social liberty beyond the sustained normative reading and complete candidate histories',
        'public self-enlightenment including discourse and attitude dissemination',
        'source-appropriate extent, comparison baseline, reinforcement and author attribution'])
    paths=set(cat.source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        'reports/audience-liberty-v1.json','scripts/compose_prospective_liberty.py','scripts/check_prospective_liberty.py',
        'tests/test_prospective_liberty.py','docs/prospective-liberty-v1.md','docs/temporal-norms-v1.md','docs/necessary-futures-v1.md'}
    return dict(status='sustained_normative_permission_with_later_native_change_partial_reading',document=FULL,
        generic=generic_checks(),native=native_checks(progress),unknowns=unknown_checks(),structure=structure(),roundtrips=True,
        alignment=alignment,new_source_assertions=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        active_review_index_unchanged='data/semantic-review-index-v22.json',source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report(lambda message:print(message,flush=True))
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Sustained permission, future completion and candidate validity checked')


if __name__=='__main__':main()
