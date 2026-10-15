"""Verify rooted delegation and its independent conjunction with conformity."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from unittest.mock import patch
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.script import transcribe
from scripts import check_commanded_protection as previous
from scripts.compose_command_authority import ROOT,LIBRARY,CORE,EXAMPLE,BASIS,PARENT,PARENT_EXAMPLE,build,basis

REPORT=ROOT/'reports/command-authority-v1.json'
CORE_DOMAIN=('root','middle','chief','institution','group','person','role','activity','other')


@lru_cache(maxsize=1)
def core_document():return parse((ROOT/CORE).read_text(encoding='utf-8'))


def core_values(flags=(True,True,True,True,True),variant='baseline',*,indices=(0,1),memoize=True):
    hasroot,canfirst,cansecond,firstedge,secondedge=flags
    doc=deepcopy(core_document());doc['statements']=[doc['statements'][i] for i in indices]
    chain={'empty':(),'direct_root':('chief',),'wrong_end':('root','middle'),'no_root':('middle','chief'),
        'repeat':('root','middle','root','chief'),'cycle':('middle','chief','middle'),
        'reversed':('chief','middle','root'),'longer':('root','middle','other','chief')}.get(variant,('root','middle','chief'))
    edges={('root','middle'):firstedge,('middle','chief'):secondedge}
    if variant=='repeat':edges.update({('middle','root'):True,('root','chief'):True})
    if variant=='cycle':edges.update({('chief','middle'):True})
    if variant=='longer':edges.update({('middle','other'):True,('other','chief'):True})
    def context(institution,group,person,role,activity,code,sign,anchor,scope_variant=None):
        if variant=='unknown_authority':raise ValueError('Unknown authority')
        mode=variant if scope_variant is None else scope_variant
        expected=('other' if mode=='wrong_institution' else 'institution','other' if mode=='wrong_group' else 'group',
            'other' if mode=='wrong_person' else 'person','other' if mode=='wrong_role' else 'role',
            'other' if mode=='wrong_activity' else 'activity',mode!='wrong_sign','later' if mode=='wrong_anchor' else 'anchor')
        return (institution,group,person,role,activity,sign,anchor)==expected and json.loads(code.syntax).get('symbol')==('other' if mode=='wrong_code' else 'jaaction')
    def roots(institution,who,group,person,role,activity,code,sign,anchor):
        return context(institution,group,person,role,activity,code,sign,anchor) and hasroot and who==('chief' if variant=='direct_root' else 'root')
    def delegable(institution,who,group,person,role,activity,code,sign,anchor):
        return context(institution,group,person,role,activity,code,sign,anchor) and {'root':canfirst,'middle':cansecond,'other':True}.get(who,False)
    def delegated(institution,sender,recipient,group,person,role,activity,code,sign,anchor):
        mode=variant.removeprefix('edge_') if variant.startswith('edge_') else variant
        return context(institution,group,person,role,activity,code,sign,anchor,scope_variant=mode) and edges.get((sender,recipient),False)
    def unexecuted(*args):raise AssertionError('Authority must not execute the commanded action')
    model={'jainstitution':lambda:'institution','jacommander':lambda:'chief','jagroup':lambda:'group',
        'japerson':lambda:'person','jarole':lambda:'role','jaactivity':lambda:'activity','jasign':lambda:True,'jaanchor':lambda:'anchor',
        'jachain':lambda:SequenceValue(chain,'"individual"'),'jaroots':roots,'jadelegable':delegable,'jadelegated':delegated,'jaexecuted':unexecuted}
    return [row['value'] for row in evaluate_document(doc,individuals=CORE_DOMAIN,situations=('anchor','later'),primitives=model,
        max_steps=5_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(maxsize=2)
def integration_document(restricted=True):
    doc=parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))
    if restricted:
        # Reuse only the prior finite-description diagnostic. All new authority
        # and protection definitions are evaluated unchanged.
        old=previous.setup(True)
        target=next(d for d in doc['declarations'] if d['name']=='rtx')
        target['body']=deepcopy(next(d for d in old['declarations'] if d['name']=='rtx')['body'])
        doc['declarations'].append(deepcopy(next(d for d in old['declarations'] if d['name']=='jnalias')))
        prefix=[d for d in doc['declarations'] if d['kind']=='primitive' or d['name'] in ('jnact','jnalias')]
        doc['declarations']=prefix+[d for d in doc['declarations'] if d not in prefix]
        doc=parse(format_graph(doc,'compact'))
    return doc


def integration_values(variant='baseline',*,indices=(10,13,14),restricted=True):
    # Fixture injection adds primitive interpretations, never result values or
    # replacement semantic definitions. The real evaluator runs below.
    def evaluate(doc,**kwargs):
        def context(institution,group,person,role,activity,code,sign,anchor):
            if variant=='unknown_authority':raise ValueError('Unknown authority')
            return (institution,group,role,activity,sign,anchor)==('institution','group','role','work',True,'anchor') and \
                person in (('m2',) if variant=='wrong_person' else ('m1','m2')) and json.loads(code.syntax).get('symbol')=='jnact'
        def roots(institution,who,group,person,role,activity,code,sign,anchor):
            return variant!='no_authority' and who=='authority' and context(institution,group,person,role,activity,code,sign,anchor)
        def delegable(institution,who,group,person,role,activity,code,sign,anchor):
            return variant!='no_delegation_power' and who=='authority' and context(institution,group,person,role,activity,code,sign,anchor)
        def delegated(institution,sender,recipient,group,person,role,activity,code,sign,anchor):
            return variant!='missing_delegation' and (sender,recipient)==('authority','chief') and context(institution,group,person,role,activity,code,sign,anchor)
        def paths(planner,group,person,plan,item,anchor):
            if variant=='unknown_path':raise ValueError('Unknown path')
            chain=('authority','chief') if (planner,group,plan,item,anchor)==('chief','group','plan','order','anchor') else ()
            if variant=='wrong_plan_path':chain=() if plan=='plan' else ('authority','chief')
            return SequenceValue(chain,'"individual"')
        kwargs['primitives'].update(jainstitution=lambda:'institution',japaths=paths,jaroots=roots,jadelegable=delegable,jadelegated=delegated)
        kwargs['individuals']=(*kwargs['individuals'],'authority','institution')
        return evaluate_document(doc,**kwargs)
    doc=integration_document(restricted)
    with patch.object(previous,'setup',return_value=doc),patch.object(previous,'evaluate_document',side_effect=evaluate):
        return previous.values(indices=indices,restricted=restricted)


def full_domain_refused():
    try:integration_values(indices=(14,),restricted=False)
    except ValueError as error:assert 'description domain' in str(error)
    else:raise AssertionError('Unbounded descriptions were silently enumerated')
    return True


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
        result=core_values(flags);assert result==[all(flags),True],(flags,result);matrix.append(dict(flags=flags,result=result))
    contrasts={}
    for name in ('empty','wrong_end','no_root','repeat','cycle','reversed','wrong_institution','wrong_group','wrong_person',
                 'wrong_role','wrong_activity','wrong_code','wrong_sign','wrong_anchor'):
        result=core_values(variant=name);assert result==[False,True],(name,result);contrasts[name]=result
    for name in ('direct_root','longer'):
        result=core_values(variant=name);assert result==[True,True];contrasts[name]=result
    for field in ('institution','group','person','role','activity','code','sign','anchor'):
        name='edge_wrong_'+field;result=core_values(variant=name);assert result==[False,True];contrasts[name]=result
    assert core_values((True,False,False,False,False),variant='direct_root')==[True,True]
    assert core_values(variant='unknown_authority',indices=(1,))==[True]
    assert core_values(memoize=False)==[True,True]
    connected={}
    for name in ('baseline','no_authority','no_delegation_power','missing_delegation','wrong_person','wrong_plan_path'):
        result=integration_values(name);assert result==([True]*3 if name=='baseline' else [True,False,False]),(name,result);connected[name]=result
    full={}
    for name in ('baseline','no_authority'):
        result=integration_values(name,indices=(5,15));assert result==[True,name=='baseline'],(name,result);full[name]=result
    for name in ('unknown_authority','unknown_path'):assert integration_values(name,indices=(16,),restricted=False)==[True]
    paths=[LIBRARY,CORE,EXAMPLE,BASIS,PARENT,PARENT_EXAMPLE,'scripts/check_commanded_protection.py',
        'scripts/compose_command_authority.py','scripts/check_command_authority.py','tests/test_command_authority.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    return json.loads(json.dumps(dict(status='rooted_authority_and_conformity_kept_separate',documents=documents,
        matrix=matrix,contrasts=contrasts,member_integration=connected,collective_integration=full,roundtrips=True,
        full_description_domain_refused=full_domain_refused(),full_description_domain_verified=False,limitations=basis()['limitations'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Rooted scoped delegation, command conformity and collective protection verified')


if __name__=='__main__':main()
