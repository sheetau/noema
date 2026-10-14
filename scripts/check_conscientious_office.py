"""Check role-bound ability and conditional duties without asserting departure."""
import argparse
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.grammar import parse,format_graph,number_word
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded,callbacks
from scripts.compose_limits import call as k
from scripts.compose_conscientious_office import (ROOT,PARENT,BUILDERS,ABILITY,TRIGGER,CONDITIONAL,
    TRANSITION,SOURCE_TARGET,TERMINATES,TRUE)

REPORT=ROOT/'reports/conscientious-office-v1.json'
FIELDS=[field for field in CONDITIONAL[:-1] if field[0]!='target']+[
    ('context','d'),('later','d'),('terminates',TERMINATES)]
SYMBOLS={name:'jv'+number_word(i) for i,(name,_) in enumerate(FIELDS)}
DOMAIN=('person','role','activity','source','document','standard','claim','plan0','plan1','other')
SCENES=('now','later','case0','case1','end0','end1','out0','out1')


def expression(name):
    if name=='target':return 'r[c[p hzby]['+expression('role')+' '+expression('terminates')+']]'
    return k(SYMBOLS[name])


def setup(text):
    if (set(SYMBOLS.values())|{'jvzz'}) & {d['name'] for d in parse(text)['declarations']}:
        raise ValueError('Office fixture symbols collide')
    extra=''.join('r '+SYMBOLS[name]+'[] '+sort+'.' for name,sort in FIELDS)
    extra+='d jvzz[role a terminates '+TERMINATES+'] h[a a] e[k hzby[v role v terminates]].'
    base=candidate(text,extra)
    target=apply_description(base,quoted('function_ref','hzby'),[quoted('call',SYMBOLS[n]) for n in ('role','terminates')])
    alternate=apply_description(base,quoted('function_ref','jvzz'),[quoted('call',SYMBOLS[n]) for n in ('role','terminates')])
    queries=[]
    for symbol,fields in (('rg4',ABILITY),('rg5',ABILITY),('rg6',ABILITY),('rg7',TRIGGER),
        ('hzbz',CONDITIONAL[:-1]),('hzb2',CONDITIONAL[:-1])):
        queries.append(k(symbol,*(expression(n) for n,_ in fields)))
    queries.append(k('h7a',*(expression(n) for n in ('source','person','role','activity','target')),TRUE,expression('context')))
    queries.append('t[c[s['+expression('target')+']]['+expression('person')+' '+expression('activity')+']]['+expression('context')+']')
    special={
        'earlier':expression('context'),
        'history':'i[point d]['+k('ia',expression('person'),expression('context'),'v point')+']',
        'before':'i[first d second d]['+k('ic','v first','v second',expression('context'))+']',
        'holding':'p cf','changes':'p ag','affected':'p la','agent':'p df',
    }
    queries.append(k('rhc',*(special[n] if n in special else expression(n) for n,_ in TRANSITION)))
    doc=candidate(format_graph(base,'compact'),''.join('q['+q+'].' for q in queries))
    if doc['statements'][6]['body']['arguments'][4]!=target:raise ValueError('Written and constructed departure targets differ')
    return doc,target,alternate


def model_for(doc,target,alternate,*,available=(True,False),selected=(True,True),success=(False,False),
    performs=(True,True),premises=(True,False),duties=(True,False),case_success=(False,False),
    case_valid=(True,True),cases=(True,True),current_premise=False,current_duty=False,
    future=(True,False,True,True,True,False),variant='baseline'):
    model=guarded(doc)
    scalars=dict(source='source',person='person',role='role',document='document',standard='standard',
        activity='activity',anchor='now',context='now',later='later')
    for name,value in scalars.items():model[SYMBOLS[name]]=lambda value=value:value
    def match(actual,expected,category,labels):
        expected=list(expected)
        for i,label in enumerate(labels):
            if variant==category+'_'+label:expected[i]='absent_point' if label in ('context','anchor','earlier','later') else 'other'
        return list(actual)==expected
    def accessible(person,role,plan,start):
        return match((person,role),('person','role'),'available',('person','role')) and start in ('now','case0','case1') and any(
            enabled and plan=='plan'+str(i) for i,enabled in enumerate(available))
    def result(which,person,role,plan,start,end):
        if not match((person,role),('person','role'),which,('person','role')) or plan not in ('plan0','plan1'):return False
        i=int(plan[-1])
        expected='out'+str(i) if start=='now' else 'end'+str(('case0','case1').index(start)) if start in ('case0','case1') else None
        if which=='selected':
            enabled=selected[i] if start=='now' else case_valid[('case0','case1').index(start)] if start in ('case0','case1') else False
            if not enabled:return False
            if variant=='selected_outside_outcomes':expected='later'
        return end==expected
    def goal(person,role,point,conscience):
        if not match((person,role),('person','role'),'conscientious' if conscience else 'performs',('person','role')):return False
        if point in ('out0','out1'):
            return (success if conscience else performs)[('out0','out1').index(point)]
        if point in ('end0','end1'):
            return case_success[('end0','end1').index(point)] if conscience else True
        return False
    def contains(document,claim,anchor):
        expected='case0' if variant=='membership_only_in_case' else 'now'
        return match((document,claim,anchor),('document','claim',expected),'contains',('document','claim','anchor'))
    def clashes(claim,standard,point):
        if not match((claim,standard),('claim','standard'),'clashes',('claim','standard')):return False
        return current_premise if point=='out0' else any(point=='end'+str(i) and flag for i,flag in enumerate(premises))
    def candidates(person,document,standard,anchor,point):
        expected='out0' if anchor=='now' else 'end'+str(('case0','case1').index(anchor)) if anchor in ('case0','case1') else None
        return match((person,document,standard),('person','document','standard'),'candidates',('person','document','standard')) and point==expected
    def hypotheses(person,role,document,standard,anchor,point):
        return match((person,role,document,standard,anchor),('person','role','document','standard','now'),
            'cases',('person','role','document','standard','anchor')) and any(flag and point=='case'+str(i) for i,flag in enumerate(cases))
    callbacks(doc,model,{
        SYMBOLS['performs']:lambda p,r,t:goal(p,r,t,False),SYMBOLS['conscientious']:lambda p,r,t:goal(p,r,t,True),
        SYMBOLS['available']:accessible,SYMBOLS['outcomes']:lambda *x:result('outcomes',*x),SYMBOLS['selected']:lambda *x:result('selected',*x),
        SYMBOLS['contains']:contains,SYMBOLS['clashes']:clashes,SYMBOLS['candidates']:candidates,SYMBOLS['cases']:hypotheses})
    def norm(source,person,role,activity,description,positive,context):
        flag=current_duty if context=='now' else any(context=='case'+str(i) and flag for i,flag in enumerate(duties))
        return flag and positive==(variant!='norm_negative') and match((source,person,role,activity),('source','person','role','activity'),
            'norm',('source','person','role','activity')) and description.syntax==syntax(alternate if variant=='norm_description' else target) and variant!='norm_context'
    model['h7a']=norm
    held,retained,changed,affected,agent,ended=future
    def history(person,anchor,point):
        allowed=('later',) if variant=='history_missing_start' else ('now',) if variant=='history_missing_end' else ('now','later')
        return match((person,anchor),('person','now'),'history',('person','anchor')) and point in allowed
    def before(first,second,anchor):
        if variant=='reflexive_order':return first==second and anchor=='now'
        if variant=='reversed_order':return (first,second,anchor)==('later','now','now')
        return match((first,second,anchor),('now','later','now'),'order',('earlier','later','anchor'))
    def holding(person,role,point):
        return match((person,role),('person','role'),'holding',('person','role')) and ((point=='now' and held) or (point=='later' and retained))
    def termination(activity,role,person,earlier,later):
        return ended and match((activity,role,person,earlier,later),('activity','role','person','now','later'),
            'termination',('activity','role','person','earlier','later'))
    callbacks(doc,model,{SYMBOLS['terminates']:termination})
    model.update(ia=history,ic=before,cf=holding,
        ag=lambda activity,earlier,later:changed and match((activity,earlier,later),('activity','now','later'),'change',('activity','earlier','later')),
        la=lambda person,activity,earlier,later:affected and match((person,activity,earlier,later),('person','activity','now','later'),'affected',('person','activity','earlier','later')),
        df=lambda person,activity,point:agent and match((person,activity,point),('person','activity','later'),'agent',('person','activity','later')))
    return model


def evaluate(doc,model,indices):
    doc={**doc,'statements':[doc['statements'][i] for i in indices]}
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return values(doc,{n:value for n,value in model.items() if n in names},DOMAIN,SCENES)


def finite_checks(texts):
    setups=[setup(text) for text in texts]
    def run(indices,**options):
        rows=[evaluate(doc,model_for(doc,target,alternate,**options),indices) for doc,target,alternate in setups]
        if rows[0]!=rows[1]:raise ValueError('Extracted office conditions differ')
        return rows[0]
    ability=[]
    for available,selected,success in product(product((False,True),repeat=2),repeat=3):
        capable=any(a and s and goal for a,s,goal in zip(available,selected,success))
        valid=all(not a or s for a,s in zip(available,selected))
        row=run(range(3),available=available,selected=selected,success=success)
        if row!=[capable,valid and not capable,valid]:raise ValueError('Unknown or incomplete ability became inability')
        ability.append(dict(available=list(available),selected=list(selected),success=list(success),results=row))
    ability_contrasts={}
    for name,options,expected in (
        ('split_goal',dict(available=(True,True),performs=(True,False),success=(False,True)),[False,True,True]),
        ('one_success_one_unassessed',dict(available=(True,True),selected=(True,False),success=(True,True)),[True,False,False]),
        ('outside_outcomes',dict(variant='selected_outside_outcomes',success=(True,True)),[False,False,False]),
        ('wrong_performer',dict(variant='performs_person',success=(True,True)),[False,True,True]),
        ('wrong_office',dict(variant='conscientious_role',success=(True,True)),[False,True,True]),
    ):
        row=run(range(3),**options)
        if row!=expected:raise ValueError('Role or same-outcome conjunction lost: '+name)
        ability_contrasts[name]=row
    conditions=[]
    for premises,duties,success in product(product((False,True),repeat=2),repeat=3):
        conditional=all(not p or (d and not s) for p,d,s in zip(premises,duties,success))
        row=run((4,5,6),premises=premises,duties=duties,case_success=success)
        if row!=[conditional,conditional and any(premises),False]:raise ValueError('Hypothetical duty became actual or ignored its premise')
        conditions.append(dict(premises=list(premises),duties=list(duties),success=list(success),results=row))
    ranges=[]
    for selected,premises in product(product((False,True),repeat=2),repeat=2):
        row=run((4,5),cases=selected,premises=premises,duties=(True,True))
        expected=[any(selected),any(s and p for s,p in zip(selected,premises))]
        if row!=expected:raise ValueError('Empty or vacuous conditional cases collapsed')
        ranges.append(dict(selected=list(selected),premises=list(premises),results=row))
    invalid=[]
    for valid in product((False,True),repeat=2):
        row=run((4,5),premises=(True,True),duties=(True,True),case_valid=valid)
        if row!=[all(valid)]*2:raise ValueError('Unassessed hypothetical method became inability')
        invalid.append(dict(valid=list(valid),results=row))
    contrasts={}
    specifications={
        **{'norm_'+f:[False,False] for f in ('source','person','role','activity','description','negative','context')},
        **{'cases_'+f:[False,False] for f in ('person','role','document','standard','anchor')},
        **{name:[True,False] for name in ('contains_document','contains_claim','contains_anchor','membership_only_in_case',
            'clashes_claim','clashes_standard','candidates_person','candidates_document','candidates_standard')},
    }
    for variant,expected in specifications.items():
        row=run((4,5),variant=variant)
        if row!=expected:raise ValueError('Conditional/normative referent differs: '+repr((variant,row)))
        contrasts[variant]=row
    departures=[]
    for future in product((False,True),repeat=6):
        expected=future[0] and not future[1] and all(future[2:])
        row=run((7,8),future=future)
        if row!=[expected,expected]:raise ValueError('Prospective departure or role transition replaced')
        departures.append(dict(holding_before=future[0],holding_after=future[1],change=future[2],affected=future[3],agent=future[4],termination=future[5],results=row))
    departure_contrasts={}
    for variant in ('history_missing_start','history_missing_end','history_person','history_anchor','reflexive_order','reversed_order',
        'order_anchor','holding_person','holding_role',
        *('termination_'+f for f in ('activity','role','person','earlier','later')),
        *('change_'+f for f in ('activity','earlier','later')),
        *('affected_'+f for f in ('person','activity','earlier','later')),
        *('agent_'+f for f in ('person','activity','later'))):
        row=run((7,8),future=(True,False,True,True,True,True),variant=variant)
        if row!=[False,False]:raise ValueError('Departure witness binding lost: '+variant)
        departure_contrasts[variant]=row
    independent=[]
    for current_premise,current_duty,departed in product((False,True),repeat=3):
        row=run((3,4,5,6,7),current_premise=current_premise,current_duty=current_duty,future=(True,False,True,True,True,departed))
        if row!=[current_premise,True,True,current_duty,departed]:raise ValueError('Hypothetical statement inferred current events')
        independent.append(dict(current_premise=current_premise,current_duty=current_duty,departure=departed,results=row))
    for doc,target,alternate in setups:
        m=model_for(doc,target,alternate)
        for name in ('ia','ic','cf','ag','la','df',SYMBOLS['terminates']):m[name]=guarded(doc)[name]
        if evaluate(doc,m,(4,5,6))!=[True,True,False]:raise ValueError('Normative target executed during condition evaluation')
        for name,indices in ((SYMBOLS['selected'],(1,)),(SYMBOLS['performs'],(0,)),(SYMBOLS['conscientious'],(0,)),
            (SYMBOLS['candidates'],(3,)),(SYMBOLS['contains'],(3,)),(SYMBOLS['cases'],(4,)),('h7a',(4,)),(SYMBOLS['terminates'],(7,))):
            m=model_for(doc,target,alternate);m[name]=guarded(doc)[name]
            try:evaluate(doc,m,indices)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown office input replaced: '+name)
    return dict(ability_cases=ability,ability_contrasts=ability_contrasts,conditional_cases=conditions,case_ranges=ranges,
        incomplete_assessments=invalid,binding_contrasts=contrasts,departure_cases=departures,departure_contrasts=departure_contrasts,
        independent_actual_cases=independent,standalone_agrees=True,unknown_inputs_refused=True,
        required_target_not_executed=True,written_and_constructed_targets_agree=True,
        conscientiousness_or_normative_validity_proved=False)


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='kant-1784:u0012')
    excerpt='Denn glaubte er das letztere darin zu finden, so würde er sein Amt mit Gewissen nicht verwalten können; er müßte es niederlegen.'
    if unit['text'].count(excerpt)!=1:raise ValueError('Ambiguous conscientious office range')
    start=unit['text'].index(excerpt)
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
        definitions=['rg3','rg4','rg5','rg6','rg7','rha','rhb','rhc','rhd','hzby','hzbz','hzb2'],status='partial',
        review_ja='同じ規定群・基準への判断を前件とし、同じ役職の良心に適う遂行不能と、今後の自己による役職保持の終結への要求を同じ仮定範囲に結ぶ。不能の評価の整合性と閉じた目標記述を保持する。良心の実質、条件選択、辞意表明・受理、denn、規範の出所と全文意味一致は未完。')],semantic_completion=False)


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored conscientious office differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Conscientious office roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:
        raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_conscientious_office.py','scripts/check_conscientious_office.py',
        'scripts/compose_contained_conflict.py','scripts/compose_described_norms.py','scripts/compose_contextual_ability.py',
        'scripts/compose_conditional_release.py','scripts/check_closed_policies.py','scripts/check_conditional_release.py',
        'scripts/check_described_appraisals.py','scripts/check_public_assessment.py','scripts/check_rod_setup.py',
        'noema/description_templates.py','noema/finite_semantics.py','noema/extraction.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_conscientious_office_and_conditional_departure_duty',documents=documents,sizes=sizes,
        finite=finite_checks(texts[1:]),alignment=alignment(),new_definitions=12,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Conscientious office report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Conscientious office ability, conditional duties and prospective departure checked')


if __name__=='__main__':main()
