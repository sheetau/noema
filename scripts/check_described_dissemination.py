"""Keep closed claim construction, author attribution and truth evaluation separate."""
import argparse
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts import check_thinking_disseminators as prior
from scripts.compose_described_dissemination import ROOT,PARENT,PARENT_BASIS,FULL,CORE,BASIS,MEANINGS,PRIMITIVES,PER_PERSON,PER_RECIPIENT,BINDINGS,GROUP,FIELDS,build

REPORT=ROOT/'reports/described-dissemination-v1.json'


def provider_text():
    text=''
    for name,type_ in BINDINGS:
        if name in PER_PERSON:
            body='r[p zmessage]' if name=='message' else 'k z'+name+'[]'
            result=type_.removeprefix('h[a d] ')
            text+='d zbind'+name+'[person a initial d] '+result+'['+body+'].'
        elif name in PER_RECIPIENT:
            body={'firsts':'k zfirstfor[v person]','tails':'l[a][]','ends':'k zendfor[v person]'}.get(name,'k z'+name+'[v target]')
            result=type_.removeprefix('h[a d a] ')
            text+='d zbind'+name+'[person a initial d target a] '+result+'['+body+'].'
    return text


def arguments(alternate=False):
    values=dict(history='p zsurveyhistory',before='p zbefore',members='p zmembers',governed='k zgoverned[]',
        appoints='p zappointed',guardianrole='p zguardian')
    for name,type_ in BINDINGS:
        values[name]=prior.profiles.STATE if name=='state' else 'p zbind'+name if name in PER_PERSON|PER_RECIPIENT else 'p z'+name
    values.update(scope='p zrelation',extent='p rqsx')
    if alternate:values['state']=values['state'].replace('zcriterion','zothercriterion')
    described=['k hzoq[']
    described+=[' '+(values[n] if n=='state' else 'r['+values[n]+']') for n,t in FIELDS]
    return values,''.join(described)+']'


@lru_cache(maxsize=6)
def document(kind='attribution',alternate=False):
    fixture=prior.profiles.relay.FIXTURE+prior.profiles.ADDITIONS+prior.departure.EXTRA+prior.GROUP_FIXTURE+prior.NATIVE_FIXTURE
    fixture+='r znode[] a.r zauthor[] a.r zcontext[] d.r zrelation[a a d] c.'+provider_text()
    values,claim=arguments(alternate)
    described=' '.join(values[n] if n=='state' else 'r['+values[n]+']' for n,t in FIELDS)
    attribution='k hzor[k znode[] k zauthor[] k zcontext[] '+described+']'
    if kind=='attribution':query='q['+attribution+'].'
    elif kind=='both':query='q['+attribution+'].q[t[s['+claim+']][k zcontext[]]].'
    else:
        assert kind=='person'
        query='q[k hzoo[k zorigin[] k zinitial[] '+' '.join(values[n] for n,t in BINDINGS)+']].'
    return parse((ROOT/CORE).read_text(encoding='utf-8')+fixture+query)


def claim_is_bound(description):
    body=json.loads(description.syntax)
    assert description.rank==1 and description.result_type=='"content"'
    assert body['kind']=='apply' and body['function']==dict(kind='function_ref',symbol='hzop')
    assert len(body['arguments'])==len(FIELDS)
    state=body['arguments'][[n for n,t in FIELDS].index('state')]
    return state==dict(kind='quote',body=prior.profiles.described_state())


def attribution_model(doc,attributed=True,seen=None):
    values={d['name']:prior.unknown for d in doc['declarations'] if d['kind']=='primitive'}
    def reports(node,author,description,context):
        if seen is not None:seen.append((node,author,description,context))
        return attributed and (node,author,context)==('topic','authority','before') and claim_is_bound(description)
    values.update(znode=lambda:'topic',zauthor=lambda:'authority',zcontext=lambda:'before',hzon=reports)
    return values


def attribution_checks():
    doc=document();seen=[]
    assert prior.evaluate(doc,attribution_model(doc,seen=seen))==[True]
    assert len(seen)==1 and claim_is_bound(seen[0][2])
    assert prior.evaluate(doc,attribution_model(doc,False))==[False]
    rows={}
    for name,value in (('znode','reader'),('zauthor','reader'),('zcontext','now')):
        values=attribution_model(doc);values[name]=lambda value=value:value
        actual=prior.evaluate(doc,values);assert actual==[False];rows[name]=actual
    other=document(alternate=True);other_seen=[]
    assert prior.evaluate(other,attribution_model(other,seen=other_seen))==[False]
    assert seen[0][2].syntax!=other_seen[0][2].syntax
    assert len(other_seen)==1
    return dict(attribution_values=[True,False],metadata_contrasts=rows,
        all_world_facts_unknown_but_attribution_evaluated=True,closed_content_rank=1,
        different_property_description_preserved=True,content_is_fully_applied_not_an_unfilled_template=True,
        quoted_argument_count=len(FIELDS),eager=True)


def native_model(doc,variant='baseline',attributed=True):
    values=prior.native_model(doc,'no_sender_thinking' if variant=='split_people' else 'baseline')
    values.update({k:v for k,v in attribution_model(doc,attributed).items() if k in ('znode','zauthor','zcontext','hzon')})
    values['zrelation']=lambda origin,target,point:origin in (('sender',) if variant=='one_scope' else ('sender','relay')) and (target,point)==('reader','before')
    if variant=='borrowed_route':values['zfirstfor']=lambda origin:'stepone'
    if variant=='missing_appointment':
        old=values['zappointed'];values['zappointed']=lambda event,issuer,person,role,point:person=='sender' and old(event,issuer,person,role,point)
    return values


def content_checks():
    doc=document('both');rows={}
    for attributed in (False,True):
        for variant in ('baseline','borrowed_route'):
            actual=prior.evaluate(doc,native_model(doc,variant,attributed),diagnostic=True)
            assert actual==[attributed,variant=='baseline'],(attributed,variant,actual)
            rows[str(attributed)+'_'+variant]=actual
    for variant in ('one_scope','missing_appointment','split_people'):
        actual=prior.evaluate(doc,native_model(doc,variant),diagnostic=True)
        assert actual==[True,False],(variant,actual);rows[variant]=actual
    person=document('person')
    assert prior.evaluate(person,native_model(person))==[True]
    return dict(attribution_and_content_contrasts=rows,one_native_person_evaluated_without_lowering=True,
        quoted_future_content_uses_short_circuit_diagnostics=True,
        appointment_thinking_departure_and_relative_transmission_bodies_executed=True,
        source_semantic_definitions_not_replaced_by_opaque_interpretations=True)


def binding_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'))
    row=next(d for d in doc['declarations'] if d['name']=='hzoo')
    names={n:p['name'] for (n,t),p in zip([('origin','a'),('initial','d')]+BINDINGS,row['parameters'],strict=True)}
    body=row['body'];assert body['kind']=='call' and body['symbol']=='hzol'
    from scripts.compose_relative_dissemination import SCOPED
    checked=0
    for (name,type_),argument in zip(SCOPED+prior.THINKING,body['arguments'],strict=True):
        if name in PER_PERSON|PER_RECIPIENT:
            target=None
            if name in PER_RECIPIENT:
                assert argument['kind']=='lambda';target=argument['parameters'][0]['name'];argument=argument['body']
            assert argument['kind']=='apply' and argument['function']==dict(kind='variable',name=names[name])
            expected=[names['origin'],names['initial']]+([target] if target else [])
            assert argument['arguments']==[dict(kind='variable',name=n) for n in expected]
            checked+=1
        else:assert argument==dict(kind='variable',name=names[name])
    assert checked==len(PER_PERSON|PER_RECIPIENT)
    return dict(person_and_opportunity_provider_bindings=checked,recipient_bound_to_its_own_route=True)


def rank_and_unknown_checks():
    text=(ROOT/CORE).read_text(encoding='utf-8');refused=0
    for extra in ('q[e[r[p hzop]][r[p hzop]]].',
        'r znode[] a.r zauthor[] a.r zcontext[] d.q[k hzon[k znode[] k zauthor[] r[b scene[e[n p a b][n p a b]]] k zcontext[]]].'):
        try:parse(text+extra)
        except ValueError:refused+=1
        else:raise AssertionError('Unsafe rank accepted')
    doc=document();values=attribution_model(doc);values['hzon']=prior.unknown
    try:prior.evaluate(doc,values)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown attribution accepted')
    # Attribution does not supply the missing interpretation when the content
    # is deliberately evaluated later.
    both=document('both')
    try:prior.evaluate(both,attribution_model(both),diagnostic=True)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown content made true by attribution')
    return dict(invalid_rank_uses_refused=refused,unknown_attribution_and_evaluated_content_refused=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==32
    assert new.document['declarations'][:-5]==old.document['declarations']
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    return dict(new_definitions=4,new_primitive_signatures=1,existing_statements=32,seven_review_bindings_preserved=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/relative-dissemination-v1.json').read_text(encoding='utf-8'))
    for path,sha in previous['source_sha256'].items():assert digest((ROOT/path).read_bytes())==sha,path
    thinking=json.loads((ROOT/'reports/thinking-disseminators-v1.json').read_text(encoding='utf-8'))
    alignment={'segments':deepcopy(thinking['alignment']['segments'])+[deepcopy(previous['alignment'])]}
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0011')
    for row in alignment['segments']:
        assert digest(unit['text'].encode('utf-8'))==row['unit_sha256']
        assert unit['text'][row['start']:row['end']]==row['source']
        row.update(definitions=list(MEANINGS),status='partial_closed_ranked_dissemination_claim',
            remaining=['source-appropriate interpretation parameters','scalar and causal discourse, metaphor and modality','actual author attribution and whole-unit meaning'])
    paths=set(load_catalog(ROOT,BASIS).source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        'reports/relative-dissemination-v1.json','scripts/compose_described_dissemination.py',
        'scripts/check_described_dissemination.py','tests/test_described_dissemination.py','docs/described-dissemination-v1.md'}
    return dict(status='closed_ranked_content_and_nonfactive_attribution_partial_connection',document=FULL,
        attribution=attribution_checks(),content=content_checks(),bindings=binding_checks(),ranks=rank_and_unknown_checks(),structure=structure(),
        roundtrips=True,alignment=alignment,new_source_assertions=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Closed ranked claims checked independently from attribution and truth',flush=True)


if __name__=='__main__':main()
