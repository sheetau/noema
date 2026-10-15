"""Check complete office holders, decision influence and source classification."""
import argparse
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import hashlib
from itertools import product
import json

from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,FunctionValue,SequenceValue
from noema.constructed_discourse import sequence_sort
from noema.diagnostic_short_circuit import lower
from noema.script import transcribe
from scripts.compose_collective_office import ROOT,PARENT,LIBRARY,EXAMPLE,SOURCE,CORE,BASIS,REVIEW,build,basis
from scripts.compose_qualified_utterance import closure
from scripts import check_risk_undertaking as risk

REPORT=ROOT/'reports/collective-office-v1.json'
DOMAIN=('organization','office','lower','outsider','p1','p2','p3','third')
SCENES=('anchor','other')
CONTRASTS=('missing_holder','extra_holder','duplicate_holder','nonperson','other_holder_office','other_holder_organization',
           'other_holder_anchor','other_roles_organization','other_order_anchor','incomparable','reflexive','cycle','uncovered_role')


@lru_cache(maxsize=5)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


def participants(count=3,variant='baseline'):
    people=tuple('p'+str(i+1) for i in range(count))
    return {'missing_holder':people[:-1],'extra_holder':people+('outsider',),
        'duplicate_holder':people[:1]+people,'reverse_order':tuple(reversed(people))}.get(variant,people)


def truth_table(count,rule='majority'):
    return sum(1<<bits for bits in range(1<<count) if {
        'majority':bits.bit_count()>count/2,'unanimity':bits==(1<<count)-1,
        'any':bool(bits),'parity':bits.bit_count()%2==1,'first':bool(bits&1),'constant':True}[rule])


def pivotal(count,table):
    return [any(bool(table&(1<<bits))!=bool(table&(1<<(bits^(1<<i)))) for bits in range(1<<count)) for i in range(count)]


def interpretation(count=3,table=None,variant='baseline',*,prefix='jda',organization='organization'):
    people=tuple('p'+str(i+1) for i in range(count));listed=participants(count,variant)
    table=truth_table(count) if table is None else table
    def decision(votes):
        if variant=='unknown_rule':raise ValueError('Unknown decision rule')
        # Total extension outside the declared positional arity. Invalid holder
        # lists still fail completeness; these values are not new participants.
        return len(votes.items)==count and bool(table&(1<<sum(int(bit)<<i for i,bit in enumerate(votes.items))))
    def roles(role,org,anchor):
        return (org,anchor)==('outsider' if variant=='other_roles_organization' else organization,'anchor') and (
            role in ('office','lower') or variant=='uncovered_role' and role=='third')
    def above(first,second,org,anchor):
        if (org,anchor)!=(organization,'other' if variant=='other_order_anchor' else 'anchor'):return False
        if variant=='outside_cycle' and first==second=='outsider':return True
        if variant=='reflexive' and first==second=='office':return True
        if variant=='cycle' and (first,second)==('lower','office'):return True
        return variant!='incomparable' and (first,second)==('office','lower')
    def holders(person,office,org,anchor):
        if variant=='unknown_holders':raise ValueError('Unknown office holders')
        return person in people and (office,org,anchor)==('lower' if variant=='other_holder_office' else 'office',
            'outsider' if variant=='other_holder_organization' else organization,'other' if variant=='other_holder_anchor' else 'anchor')
    values={prefix+n:fn for n,fn in dict(roles=roles,above=above,holders=holders).items()}
    if prefix=='jda':
        values.update(jdaoffice=lambda:'office',jdaorganization=lambda:organization,jdaanchor=lambda:'anchor',
            jdaparticipants=lambda:SequenceValue(listed,json.dumps('individual')),jdarule=decision,
            jdapersons=lambda p:p in people and not (variant=='nonperson' and p=='p3'),jdavoter=lambda:'p1',jdasecond=lambda:'p2',
            ha=lambda a,b:a+b,hc=lambda a,b:a<b,hd=lambda value:Fraction(int(value)))
    else:
        values.update(iaboffice=lambda org,anchor:'office',
            iabparticipants=lambda org,anchor:SequenceValue(listed,json.dumps('individual')),
            iabrule=lambda org,office,anchor:FunctionValue((sequence_sort('truth'),),'truth',decision))
    return values


def values(count=3,table=None,variant='baseline',*,indices=None,memoize=True):
    doc=deepcopy(document(EXAMPLE))
    if indices is not None:doc['statements']=[doc['statements'][i] for i in indices]
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives=interpretation(count,table,variant),max_steps=2_000_000,
        memoize_definitions=memoize,memoize_expressions=memoize)]


def source_fixture(*,table=None,civic=True,allowed=False,qualified=True,variant='baseline'):
    doc,kwargs=risk.source_fixture(combined=True,allowed=allowed,qualified=qualified)
    doc=deepcopy(doc);doc['statements']=[];names={d['name'] for d in doc['declarations']}
    if variant!='wrong_polity_reference':
        # The predecessor fixed this diagnostic reference to one human speaker.
        # Select a separately quoted collective referent while keeping its
        # original human reference (and thus its utterance code) unchanged.
        speaker=next(d for d in doc['declarations'] if d['name']=='jbspeaker')
        speaker['body']=dict(kind='call',symbol='jureference',arguments=[
            dict(kind='variable',name=speaker['parameters'][0]['name']),
            dict(kind='quote',rank=1,body=dict(kind='call',symbol='juperson',arguments=[])),
            dict(kind='quote',rank=1,body=dict(kind='call',symbol='juother',arguments=[]))])
    for d in closure(document(SOURCE),['iabcontrast']):
        if d['name'] not in names:doc['declarations'].append(d);names.add(d['name'])
    text=format_graph(doc,'compact')+'r jsbpolity[] a.r jsbcivic[a d] c.'
    scope='i[organization a anchor d][k iabpolity[p jsbcivic v organization v anchor]]'
    tail='p jrasstandardfor p jrasrolefor p jrascandidates k juanchor[]'
    combined='k iabcontrast[p jiremaining p jsbcivic '+tail+']'
    questions=['k iabsharing[k jsbpolity[] k juanchor[]]','k iabpolity[p jsbcivic k jsbpolity[] k juanchor[]]',
        combined,'e[r c['+combined+']][r c['+combined+']]','k iaadenial['+scope+' '+tail+']']
    doc=parse(text+''.join('q['+q+'].' for q in questions))
    primitives=kwargs['primitives'];primitives.update(interpretation(table=table,variant=variant,prefix='iab',organization='other'))
    previous_person=primitives['aa']
    primitives['aa']=lambda person:person!='other' and (previous_person(person) or person in ('p1','p2','p3')) and not (variant=='nonperson' and person=='p3')
    def civilian(org,anchor):
        if variant=='unknown_civic':raise ValueError('Unknown civic basis')
        return civic and (org,anchor)==('other','anchor')
    primitives.update(jsbpolity=lambda:'other',jsbcivic=civilian,
        jrascandidates=lambda p,a,c:(p,a,c)==('other','trial','anchor'))
    norms=risk.model((True,)*6+(allowed,False),prefix='iaa',person='other',view='left',outcome='right',
        goal='iaautterance',normgoal='iaaundertake',variant='unknown_norm' if variant=='unknown_norm' else 'baseline')
    primitives.update({n:norms[n] for n in ('iaaallowed','iaarequired')})
    required={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    assert not required-set(primitives),required-set(primitives)
    kwargs.update(primitives={n:primitives[n] for n in required},
        individuals=tuple(dict.fromkeys([*kwargs['individuals'],'p1','p2','p3','office','lower','outsider','third'])))
    return doc,kwargs


def source_values(*,indices=(0,1,2,3,4),**options):
    doc,kwargs=source_fixture(**options);doc['statements']=[doc['statements'][i] for i in indices]
    doc,kwargs['primitives']=lower(doc,kwargs['primitives'])
    return [r['value'] for r in evaluate_document(doc,**kwargs)]


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    def forbidden(*args):raise AssertionError('Political classification or speech evaluated during attribution')
    primitives={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def annotation(node,author,code,scope,context):
        return (node,author,scope,context)==('node','author','scope','context') and code.rank==2 and json.loads(code.syntax)==dict(kind='function_ref',symbol='iabcontrast')
    primitives.update(hztnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        hztscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'other' if variant=='context' else 'context',iabannotation=annotation)
    return [r['value'] for r in evaluate_document(doc,individuals=('node','author','scope','other'),situations=('context','other'),primitives=primitives)]


def alignment():
    corpus=json.loads((ROOT/risk.UNITS).read_text(encoding='utf-8'));unit=next(u for u in corpus['units'] if u['id']=='kant-1784:u0017')
    phrase='Freistaat';start=unit['text'].index(phrase)
    return dict(work='kant-1784',unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        segments=[dict(start=start,end=start+len(phrase),text=phrase)],definitions=['iabsharing','iabpolity','iabcontrast','iabattribution'],
        semantic_completion=False,civic_basis_open=True,normative_standard_open=True)


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
    for count in (2,3):
        for table in range(1<<(1<<count)):
            impact=pivotal(count,table);result=values(count,table)
            assert result==[all(impact),impact[0],impact[1],True,True],(count,table,result,impact)
            matrix.append(dict(holders=count,table=table,pivotal=impact,result=result))
    contrasts={v:values(variant=v) for v in CONTRASTS}
    assert all(not result[0] for result in contrasts.values())
    assert values(variant='outside_cycle')==[True]*5
    assert values(count=1,table=truth_table(1,'first'))==[False,True,False,True,True]
    source=[]
    for civic,allowed,qualified in product((False,True),repeat=3):
        result=source_values(civic=civic,allowed=allowed,qualified=qualified)
        denied=not civic or not allowed
        assert result==[True,civic,qualified and denied,True,denied],result
        source.append(dict(civic=civic,allowed=allowed,qualified=qualified,result=result))
    assert source_values(table=truth_table(3,'first'),allowed=True)==[False,False,True,True,True]
    assert source_values(variant='wrong_polity_reference')==[True,True,False,True,False]
    for variant in ('unknown_rule','unknown_holders','unknown_civic','unknown_norm'):
        assert source_values(variant=variant,indices=(3,))==[True]
        try:source_values(variant=variant,indices=(2,))
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError('Unknown political input was filled')
    for path in (SOURCE,CORE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    assert values(memoize=False)==values()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    reading=json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))
    for item in reading['sources']:assert hashlib.sha256((ROOT/item['artifact']).read_bytes()).hexdigest()==item['artifact_sha256']
    paths=[PARENT,LIBRARY,EXAMPLE,SOURCE,CORE,BASIS,REVIEW,risk.UNITS,'scripts/compose_collective_office.py','scripts/check_collective_office.py',
        'scripts/check_risk_undertaking.py','reports/risk-undertaking-v1.json','tests/test_collective_office.py','noema/diagnostic_short_circuit.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py']+[item['artifact'] for item in reading['sources']]
    return dict(status='candidate_plural_governing_office_with_unfilled_civic_basis',documents=documents,matrix=matrix,contrasts=contrasts,
        source_matrix=source,source_scope_can_be_empty=True,combined_description_domains_finite=True,roundtrips=True,
        collective_reference_distinct_from_human=True,wrong_collective_reference_rejected=True,
        source_alignment=alignment(),unresolved=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Plural office holders, non-dummy decisions and explicit civic remainder verified')


if __name__=='__main__':main()
