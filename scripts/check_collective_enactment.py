"""Check shared decisions, constitutive changes and actual enactment separately."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json

from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.script import transcribe
from scripts.compose_collective_enactment import ROOT,PARENT,LIBRARY,EXAMPLE,BASIS,build,basis
from scripts.check_collective_office import interpretation,DOMAIN as OFFICE_DOMAIN

REPORT=ROOT/'reports/collective-enactment-v1.json'
DOMAIN=OFFICE_DOMAIN+('framework','beneficiary','recipientrole','contract')
SCENES=('anchor','after','alternative')
APPROVAL_CONTRASTS=('mandate_framework','mandate_organization','mandate_office','mandate_code','mandate_bindings','mandate_anchor',
    'wrong_exercise_owner','bad_exercise_shape','missing_holder','duplicate_holder','incomparable','dictator')
CHANGE_CONTRASTS=('control_actor','control_code','control_bindings','control_anchor',
    'recognition_framework','recognition_actor','recognition_office','recognition_code','recognition_bindings','recognition_start','split_result',
    'norm_source','norm_person','norm_role','norm_code','norm_bindings','norm_polarity','bad_target_shape')
ACTUAL_CONTRASTS=('cast_person','cast_sign','cast_organization','cast_office','cast_code','cast_bindings','cast_anchor',
    'performed_actor','performed_code','performed_bindings','performed_anchor','split_realization')


@lru_cache(maxsize=2)
def document(path=EXAMPLE):return parse((ROOT/path).read_text(encoding='utf-8'))


def model(*,mandated=True,approved=True,controlled=True,recognized=True,changed=True,
        cast=True,performed=True,realized=True,status=True,polarity=True,variant='baseline'):
    from scripts.check_collective_office import truth_table
    office=interpretation(table=truth_table(3,'first') if variant=='dictator' else None,variant=variant)
    result={('jce'+n[3:] if n.startswith('jda') else n):f for n,f in office.items() if n not in ('jdavoter','jdasecond')}
    args=('outsider','office') if variant=='wrong_exercise_owner' else ('organization','office','outsider') if variant=='bad_exercise_shape' else ('organization','office')
    bindings=('beneficiary','recipientrole','outsider') if variant=='bad_target_shape' else ('beneficiary','recipientrole')
    profile=lambda person:person=='p1' or approved and person=='p2'
    seq=lambda items:SequenceValue(items,json.dumps('individual'))
    def code(value,name):return json.loads(value.syntax)==dict(kind='function_ref',symbol='jce'+name)
    def exact(actual,expected,tag,labels):
        expected=list(expected)
        for i,label in enumerate(labels):
            if variant==tag+'_'+label:
                expected[i]=not expected[i] if isinstance(expected[i],bool) else ('outsider',) if isinstance(expected[i],tuple) else 'outsider'
        return tuple(actual)==tuple(expected)
    def mandates(framework,org,office,description,items,anchor):
        if variant=='unknown_mandate':raise ValueError('Unknown mandate')
        return mandated and exact((framework,org,office,code(description,'exercise'),items.items,anchor),
            ('framework','organization','office',True,args,'anchor'),'mandate',('framework','organization','office','code','bindings','anchor'))
    def control(actor,description,items,anchor):
        if variant=='unknown_control':raise ValueError('Unknown control')
        return controlled and exact((actor,code(description,'exercise'),items.items,anchor),
            ('organization',True,args,'anchor'),'control',('actor','code','bindings','anchor'))
    def recognition(framework,actor,office,description,items,start,end):
        if variant=='unknown_recognition':raise ValueError('Unknown recognition')
        endpoint='alternative' if variant in ('alternative','split_result') else 'after'
        return recognized and exact((framework,actor,office,code(description,'exercise'),items.items,start,end),
            ('framework','organization','office',True,args,'anchor',endpoint),'recognition',
            ('framework','actor','office','code','bindings','start','end'))
    def relation(source,person,role,description,items,sign,scene):
        if variant=='unknown_norm':raise ValueError('Unknown norm')
        matches=exact((source,person,role,code(description,'target'),items.items,sign),
            ('contract','beneficiary','recipientrole',True,bindings,polarity),'norm',('source','person','role','code','bindings','polarity'))
        endpoint='alternative' if variant=='alternative' else 'after'
        return matches and (not status if scene=='anchor' else status if changed and scene==endpoint else not status)
    def ballot(person,sign,org,office,description,items,anchor):
        if variant=='unknown_cast':raise ValueError('Unknown ballot record')
        return cast and exact((person,sign,org,office,code(description,'exercise'),items.items,anchor),
            ('outsider' if variant=='missing_ballot' and person=='p3' else person,profile(person),'organization','office',True,args,'anchor'),
            'cast',('person','sign','organization','office','code','bindings','anchor'))
    def execution(actor,description,items,anchor):
        if variant=='unknown_performed':raise ValueError('Unknown execution')
        return performed and exact((actor,code(description,'exercise'),items.items,anchor),
            ('organization',True,args,'anchor'),'performed',('actor','code','bindings','anchor'))
    def actual(start,end):
        if variant=='unknown_realized':raise ValueError('Unknown realization')
        return realized and (start,end)==('anchor','alternative' if variant in ('alternative','split_realization') else 'after')
    def opaque(*args):raise AssertionError('Policy or exercise truth evaluated')
    result.update(jceframework=lambda:'framework',jceprofile=profile,jceexercisebindings=lambda:seq(args),
        jceexercisevalid=lambda items:len(items.items)==2,jcemandates=mandates,jcesource=lambda:'contract',
        jceperson=lambda:'beneficiary',jcerole=lambda:'recipientrole',jcebindings=lambda:seq(bindings),
        jcepolarity=lambda:polarity,jceend=lambda:'anchor' if variant=='same_state' else 'after',
        jcestatus=lambda:status,jcevalid=lambda items:len(items.items)==2,jcerelation=relation,
        jcecontrolled=control,jcerecognizes=recognition,jcecast=ballot,jceperformed=execution,jcerealized=actual,
        jceexercisetruth=opaque,jcetargettruth=opaque)
    return result


def values(*,indices=None,memoize=True,**options):
    doc=deepcopy(document())
    if indices is not None:doc['statements']=[doc['statements'][i] for i in indices]
    primitives=model(**options)
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    assert not names-set(primitives),names-set(primitives)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives={n:primitives[n] for n in names},max_steps=2_000_000,
        memoize_definitions=memoize,memoize_expressions=memoize)]


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    matrix=[]
    for flags in product((False,True),repeat=5):
        options=dict(zip(('mandated','approved','controlled','recognized','changed'),flags))
        result=values(**options);approval=all(flags[:2]);change=all(flags)
        assert result==[approval,change,change,change,True],(options,result)
        matrix.append(dict(flags=list(flags),result=result))
    actual=[]
    for flags in product((False,True),repeat=3):
        result=values(**dict(zip(('cast','performed','realized'),flags)))
        assert result==[True,True,True,all(flags),True],(flags,result)
        actual.append(dict(flags=list(flags),result=result))
    contrasts={}
    for names,expected in [(APPROVAL_CONTRASTS,[False]*4+[True]),(CHANGE_CONTRASTS,[True,False,False,False,True]),
                           (ACTUAL_CONTRASTS+('missing_ballot',),[True,True,True,False,True])]:
        for name in names:
            result=values(variant=name);assert result==expected,(name,result);contrasts[name]=result
    for name in ('same_state','alternative'):
        assert values(variant=name)==[True,False,True,False,True]
    for status,polarity in product((False,True),repeat=2):assert values(status=status,polarity=polarity)==[True]*5
    for name in ('unknown_mandate','unknown_control','unknown_recognition','unknown_norm','unknown_cast','unknown_performed','unknown_realized'):
        assert values(variant=name,indices=(4,))==[True]
        try:values(variant=name,indices=(3,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    for name in ('unknown_cast','unknown_performed','unknown_realized'):assert values(variant=name,indices=(2,))==[True]
    assert values(memoize=False)==values()
    paths=[PARENT,LIBRARY,EXAMPLE,BASIS,'scripts/compose_collective_enactment.py','scripts/check_collective_enactment.py',
        'tests/test_collective_enactment.py','scripts/check_collective_office.py','scripts/compose_normative_powers.py',
        'noema/constructed.py','noema/constructed_semantics.py','noema/constructed_discourse.py']
    return dict(status='decision_power_and_actual_enactment_separated',documents=documents,new_definitions=4,
        matrix=matrix,actual_matrix=actual,contrasts=contrasts,roundtrips=True,policy_and_exercise_not_executed=True,
        source_alignment_added=False,verified_full_units={'kant-1784':0,'einstein-1905':0},limitations=basis()['limitations'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Collective approval, same normative transition and actual enactment verified')


if __name__=='__main__':main()
