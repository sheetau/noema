"""Exercise the source's actual protection call and its explicit remaining scope."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from unittest.mock import patch
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,FunctionValue
from noema.script import transcribe
from scripts import check_commanded_protection as previous
from scripts.compose_origin_clock import definition
from scripts.compose_protective_qualification import ROOT,PARENT,PROTECTION,SOURCE,CORE,BASIS,PROVIDERS,QUALIFICATION,build,basis
from scripts.compose_qualified_utterance import closure
from scripts.check_interpreted_depiction import UNITS

REPORT=ROOT/'reports/protective-qualification-v1.json'
PROFILE={'community','citizens','activities','possessions','holds','tasks','methods','taskoutcomes','taskselected'}
COMMANDS={'commandrolescope','commanditems','commandroles','commandactions','commandcodes','commandsigns','orders','criterion'}


def original(name):return ('jc' if name in PROFILE else 'jn' if name in COMMANDS else 'jg')+name


@lru_cache(maxsize=3)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=2)
def setup(restricted=True):
    doc=deepcopy(previous.setup(restricted));doc['statements']=[]
    names={d['name'] for d in doc['declarations']}
    for decl in closure(document(SOURCE),['hzxremaining']):
        if decl['name'] not in names:doc['declarations'].append(decl);names.add(decl['name'])
    # Two providers return existing Noema functions, so their descriptions stay
    # owned by this interpreter. No externally fabricated description values.
    for name in ('tasks','commandcodes'):
        target=next(d for d in doc['declarations'] if d['name']=='hzx'+name)
        ref=next(d for d in doc['declarations'] if d['name']==original(name))
        sort={'kind':'function','parameters':[p['sort'] for p in ref['parameters']],'result':ref['result']}
        target.clear();target.update(kind='definition',name='hzx'+name,
            parameters=[dict(name='actor',sort='individual'),dict(name='group',sort='individual'),dict(name='anchor',sort='situation')],
            result=sort,body=dict(kind='function_ref',symbol=original(name)))
    text=format_graph(doc,'compact')+'r jmactor[] a.r jmgroup[] a.r jmanchor[] d.r jmqualification[a a a d] c.'
    bound='k hzxgroup[k jmactor[] k jmgroup[] k jmanchor[]]'
    residual='k hzxremaining[p jmqualification k jmactor[] k jmanchor[]]'
    text+='q['+bound+'].q['+residual+'].q[e[r b['+residual+']][r b['+residual+']]].'
    text+='q[k jmqualification[k jmactor[] k jmgroup[] k hzxcommunity[k jmactor[] k jmgroup[] k jmanchor[]] k jmanchor[]]].'
    return parse(text)


def values(variant='baseline',*,indices=(0,),restricted=True,threshold=1,flags=(True,True,True)):
    doc=setup(restricted)
    source_variant=variant if variant in ('other_actor','other_group','other_anchor','wrong_community','wrong_residual_actor',
        'wrong_residual_group','wrong_residual_community','wrong_residual_anchor','residual_false','unknown_residual','unknown_provider') else 'baseline'
    old_variant='baseline' if source_variant!='baseline' else variant
    actor='other' if variant=='other_actor' else 'chief'
    group='other' if variant=='other_group' else 'group'
    anchor='w111' if variant=='other_anchor' else 'anchor'
    def evaluate(current,**kwargs):
        model=kwargs['primitives'];lookup={d['name']:d for d in current['declarations']}
        def provider(name):
            old=original(name);decl=lookup[old]
            def select(who,cohort,start):
                assert who==actor and start==anchor,'Provider lost candidate or anchor'
                if variant=='unknown_provider':raise ValueError('Unknown protective model')
                if name=='community' and variant=='wrong_community':return 'other'
                if decl['parameters']:
                    return FunctionValue(tuple(decl['parameters']),decl['result'],model[old])
                return model[old]()
            return select
        for name,sort in PROVIDERS:
            if name not in ('tasks','commandcodes'):model['hzx'+name]=provider(name)
        def qualification(who,cohort,community,start):
            if variant=='unknown_residual':raise ValueError('Unknown residual qualification')
            expected=('other' if variant=='wrong_residual_actor' else 'chief',
                'other' if variant=='wrong_residual_group' else 'group',
                'other' if variant=='wrong_residual_community' else 'people',
                'w111' if variant=='wrong_residual_anchor' else 'anchor')
            return variant!='residual_false' and (who,cohort,community,start)==expected
        model.update(jmactor=lambda:actor,jmgroup=lambda:group,jmanchor=lambda:anchor,jmqualification=qualification)
        # Same finite domain; put the successful witness first, without removing
        # the alternatives needed to falsify an existential claim.
        kwargs['individuals']=('group',)+tuple(x for x in kwargs['individuals'] if x!='group')
        return evaluate_document(current,**kwargs)
    with patch.object(previous,'setup',return_value=doc),patch.object(previous,'evaluate_document',side_effect=evaluate):
        return previous.values(flags,variant=old_variant,indices=indices,restricted=restricted,threshold=threshold)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    def forbidden(*args):raise AssertionError('Qualification evaluated during attribution')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def annotation(node,author,code,scope,context):
        return (node,author,scope,context)==('node','author','scope','context') and code.rank==2 and json.loads(code.syntax)==dict(kind='function_ref',symbol='hzxonly')
    model.update(hztnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        hztscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'other' if variant=='context' else 'context',hzxannotation=annotation)
    return [r['value'] for r in evaluate_document(doc,individuals=('node','author','scope','other'),situations=('context','other'),primitives=model)]


def full_domain_refused():
    try:values(restricted=False)
    except ValueError as error:assert 'description domain' in str(error),str(error)
    else:raise AssertionError('Full command description domain silently restricted')
    assert values(indices=(2,),restricted=False)==[True]
    return True


def binding_structure():
    doc=document(SOURCE);lookup={d['name']:d for d in doc['declarations']}
    call=lookup['hzxgroup']['body'];assert call['kind']=='call' and call['symbol']=='rvh'
    bound={name:p['name'] for name,p in zip(('actor','group','anchor'),lookup['hzxgroup']['parameters'],strict=True)}
    from scripts.compose_commanded_protection import READY
    for (name,sort),arg in zip(READY,call['arguments'],strict=True):
        if name in ('planner','group','anchor'):
            assert arg==dict(kind='variable',name=bound['actor' if name=='planner' else name])
        else:
            assert arg==dict(kind='call',symbol='hzx'+name,arguments=[dict(kind='variable',name=bound[n]) for n in ('actor','group','anchor')])
    outer=lookup['hzxonly']['body'];assert outer['kind']=='call' and outer['symbol']=='hzwonly'
    forwarded=outer['arguments'][0]
    qualification,anchor=(p['name'] for p in lookup['hzxonly']['parameters'])
    actor,point=(p['name'] for p in forwarded['parameters'])
    assert forwarded['kind']=='lambda' and forwarded['body']==dict(kind='call',symbol='hzxremaining',
        arguments=[dict(kind='variable',name=n) for n in (qualification,actor,point)])
    assert outer['arguments'][1]==dict(kind='variable',name=anchor)
    residual=lookup['hzxremaining'];existential=residual['body'];assert existential['kind']=='exists'
    qualification,actor,anchor=(p['name'] for p in residual['parameters']);group=existential['variable']
    condition,protected=existential['body']['arguments']
    assert condition==dict(kind='apply',function=dict(kind='variable',name=qualification),arguments=[
        dict(kind='variable',name=actor),dict(kind='variable',name=group),
        dict(kind='call',symbol='hzxcommunity',arguments=[dict(kind='variable',name=n) for n in (actor,group,anchor)]),
        dict(kind='variable',name=anchor)])
    assert protected==dict(kind='call',symbol='hzxgroup',arguments=[dict(kind='variable',name=n) for n in (actor,group,anchor)])
    return True


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    text='ein wohldisciplinirtes zahlreiches Heer zum Bürgen der öffentlichen Ruhe zur Hand hat'
    start=unit['text'].index(text)
    return dict(work='kant-1784',unit=unit['id'],text_sha256=unit['text_sha256'],segments=[dict(start=start,end=start+len(text),text=text)],
        definitions=['hzxgroup','hzxremaining','hzxonly','hzxattribution'],status='explicit_interpretive_annotation',
        semantic_completion=False,residual_qualification_open=True)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    cases={}
    for variant in ('baseline','other_actor','other_group','other_anchor','wrong_community','wrong_source','wrong_plan','wrong_person','other_plan_failed','empty_commands'):
        result=values(variant);assert result==[variant=='baseline'],(variant,result);cases[variant]=result
    assert values(threshold=2)==[False]
    assert values(flags=(True,True,False))==[False]
    assert values(indices=(1,3))==[True,True]
    for variant in ('wrong_residual_actor','wrong_residual_group','wrong_residual_community','wrong_residual_anchor','residual_false'):
        assert values(variant,indices=(3,))==[False]
    for variant in ('unknown_provider','unknown_residual'):
        assert values(variant,indices=(2,))==[True]
        try:values(variant,indices=(0 if variant=='unknown_provider' else 3,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError('Unknown input was completed')
    for path in (SOURCE,CORE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    paths=[PARENT,PROTECTION,SOURCE,CORE,BASIS,UNITS,'scripts/compose_protective_qualification.py','scripts/check_protective_qualification.py',
        'tests/test_protective_qualification.py','scripts/check_commanded_protection.py','noema/constructed.py',
        'noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    return json.loads(json.dumps(dict(status='partial_protection_candidate_with_residual_qualification',documents=documents,cases=cases,
        binding_structure=binding_structure(),roundtrips=True,full_domain_refused=full_domain_refused(),full_domain_verified=False,
        outer_ability_verified_here=False,outer_ability_evidence='reports/supported-apprehension-v1.json',
        source_alignment=alignment(),verified_full_units={'kant-1784':0,'einstein-1905':0},unresolved=basis()['unresolved'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Same-candidate protective qualification, source binding and explicit residual scope verified')


if __name__=='__main__':main()
