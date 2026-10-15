"""Check fixed-cohort growth without requiring every member to grow twice."""
import argparse
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.script import transcribe
from scripts.compose_cohort_response import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,STATE,FIELDS,build,basis
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_apparent_liberty import UNITS
from scripts import check_reasoned_response as previous
from scripts import check_thinking_disposition as thinking

REPORT=ROOT/'reports/cohort-response-v1.json'
PEOPLE=('person','other')
TOPICS=('topicone','topictwo')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    from scripts.compose_restricted_utterance import primitive
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')
    args=[]
    for name,sort in FIELDS:
        symbol='jc'+name
        text+=primitive(symbol,sort if sort.startswith('h[') else 'h[] '+sort)
        args.append('p '+symbol if sort.startswith('h[') else 'k '+symbol+'[]')
    text+='r jcexpectedstart[] b.r jcexpectedend[] b.'
    text+=''.join('q[k '+name+'['+' '.join(args)+']].' for name in ('rxm','rxn'))
    text+='q[e[k rxl[k jcpopulation[] p jctopics p jcresponse k jcstart[]]][k jcexpectedstart[]]].q[e[k rxl[k jcpopulation[] p jctopics p jcresponse k jcend[]]][k jcexpectedend[]]].'
    return parse(text)


def values(profile=(0,1,3),*,topics=(('topicone',),('topicone',)),bound=1,variant='baseline',indices=(0,1),memoize=True):
    times=('start','middle','finish') if len(profile)==3 else ('start','middle','hold','finish')
    assert len(profile)==len(times) and len(topics)==len(PEOPLE)
    pairs=tuple((person,topic) for person,ts in zip(PEOPLE,topics) for topic in ts)
    population=() if variant=='empty_people' else PEOPLE+('person',) if variant=='duplicate_people' else PEOPLE[:1] if variant=='omitted_person' else PEOPLE+('outsider',) if variant=='extra_person' else PEOPLE
    if variant=='reordered':population=tuple(reversed(population))
    def people(person):
        if variant=='unknown_people':raise ValueError('Unknown cohort membership')
        return variant!='empty_people' and person in PEOPLE
    def selected(person):
        items=topics[PEOPLE.index(person)] if person in PEOPLE else ()
        if person=='other':
            if variant=='empty_topics':items=()
            if variant=='duplicate_topics':items=items+items[:1]
            if variant=='omitted_topic':items=items[:-1]
            if variant=='extra_topic':items=items+('outsider',)
        return SequenceValue(tuple(reversed(items)) if variant=='reordered' else items,'"individual"')
    def scope(person,topic):
        if variant=='unknown_scope':raise ValueError('Unknown personal topic scope')
        return (person,topic) in pairs and not (variant=='empty_topics' and person=='other')
    def history(point):
        if variant=='unknown_history':raise ValueError('Unknown history')
        return point in ((times[0],times[-1]) if variant=='hidden_middle' else times)
    def before(left,right):
        if variant=='unknown_order':raise ValueError('Unknown order')
        if variant=='reflexive' and left==right:return True
        return left in times and right in times and times.index(left)<times.index(right)
    def classified(person,topic,point):
        if variant=='unknown_classification':raise ValueError('Unknown classification')
        return (person,topic) in pairs and point in times and not (variant=='unclassified_other' and person=='other' and point=='middle')
    def response(person,topic,point):
        if variant=='unknown_response':raise ValueError('Unknown response')
        if variant=='outsider_only':return person=='outsider' and point in times and point!='start'
        return (person,topic) in pairs and point in times and bool(profile[times.index(point)]&(1<<pairs.index((person,topic))))
    p=dict(arithmetic(variant=='bad_indicator'),jcpopulation=lambda:SequenceValue(population,'"individual"'),jcpeople=people,
        jctopics=selected,jcscope=scope,jchistory=history,jcbefore=before,jcstart=lambda:times[0],jcend=lambda:times[-1],
        jcbound=lambda:Fraction(bound),jcclassified=classified,jcresponse=response,
        jcexpectedstart=lambda:Fraction(profile[0].bit_count()),jcexpectedend=lambda:Fraction(profile[-1].bit_count()))
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,PEOPLE+TOPICS+('outsider',),times+('outside',),memoize=memoize,budget=8_000_000)


def expected(profile,bound=1):
    """Independent bitset oracle for valid fixed scopes and a finite ordered path."""
    counts=[mask.bit_count() for mask in profile]
    return (bound>0 and all(left&~right==0 for left,right in zip(profile,profile[1:]))
        and all(b-a<=bound for a,b in zip(counts,counts[1:]))
        and any(counts[0]<middle<counts[-1] for middle in counts[1:-1]))


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    from scripts.compose_qualified_utterance import closure
    names={d['name'] for d in doc['declarations']}
    for d in closure(document(SOURCE),['ianreviewed']):
        if d['name'] not in names:doc['declarations'].append(d);names.add(d['name'])
    # Individual iamchange remains available to compare collective growth with
    # the stronger claim that each person undergoes two strict expansions.
    return parse(format_graph(doc,'compact')+f'r jcstate[] {STATE}.'+'''
r jccommunity[] a.r jcperson[] a.r jcother[] a.r jcstart[] d.r jcend[] d.
q[k ianreviewed[k jccommunity[] k jcstart[] k jcend[] k jcstate[]]].
q[k ianchange[k jccommunity[] k jcstart[] k jcend[] k jcstate[]]].
q[k iamchange[k jcperson[] k jcstart[] k jcend[] k jcstate[]]].
q[k iamchange[k jcother[] k jcstart[] k jcend[] k jcstate[]]].
q[t[k iahthinking[k jcperson[]]][k jcstart[]]].
q[k iamreviewed[k jcperson[] k jcstart[] k jcend[] k jcstate[]]].
q[k iamreviewed[k jcother[] k jcstart[] k jcend[] k jcstate[]]].
''')


def source_values(*,variant='baseline',state_bits=(True,True,True),indices=(0,1,2,3,4),calls=None):
    p,domain,scenes=previous.source_model(state_bits=state_bits)
    domain=domain+('community','othercommunity','otherfaculty')
    oldprobe=p['iamprobe']
    def correct(community,anchor):return (community,anchor)==('community','end')
    def members(community,person,anchor):
        if calls is not None:calls.append(('members',community,anchor))
        if variant=='unknown_members':raise ValueError('Unknown cohort membership')
        return correct(community,anchor) and person in PEOPLE
    def population(community,anchor):
        if calls is not None:calls.append(('population',community,anchor))
        selected=PEOPLE[:1] if variant=='drop_departed' else PEOPLE
        return SequenceValue(selected if correct(community,anchor) else (), '"individual"')
    def topics(community,person,anchor):
        if calls is not None:calls.append(('topics',community,anchor))
        return SequenceValue(TOPICS[:1] if correct(community,anchor) and person in PEOPLE else (), '"individual"')
    def probe(community,person,topic,point,state):
        if calls is not None:calls.append(('probe',community,person,topic,*(state(x) for x in previous.VARIABLES)))
        if variant=='unknown_probe':raise ValueError('Unknown probe')
        return oldprobe(person,topic,point,state) if community=='community' else 'outside'
    def presented(person,topic,scene):
        return person in PEOPLE and topic=='topicone' and scene in previous.PROBES
    def classified(person,topic,scene):
        if variant=='unknown_classification' and person=='other':raise ValueError('Unknown member assessment')
        return presented(person,topic,scene) and not (variant=='unclassified_other' and person=='other' and scene=='probe_one')
    def judged(person,judgment,scene):
        if variant=='one_person_only' and person=='other':return False
        if variant=='outsider_only':return person=='norm' and judgment=='judgmentone' and scene=='probe_two'
        return ((person,judgment)==('person','judgmentone') and scene in ('probe_one','probe_two')
            or (person,judgment,scene)==('other','judgmenttwo','probe_two'))
    def owns(faculty,person,scene):
        return (faculty,person) in (('faculty','person'),('otherfaculty','other')) and scene in previous.PROBES and not (variant=='other_owner' and person=='other')
    def uses(person,faculty,judgment,scene):
        return (person,faculty,judgment) in (('person','faculty','judgmentone'),('other','otherfaculty','judgmenttwo')) and scene in previous.PROBES
    p.update(jcstate=p['jrstate'],jccommunity=lambda:'othercommunity' if variant=='wrong_community' else 'community',
        jcperson=lambda:'person',jcother=lambda:'other',jcstart=lambda:'end',jcend=lambda:'after',
        ianpopulation=population,ianmembers=members,iantopics=topics,
        ianscope=lambda community,person,anchor,topic:correct(community,anchor) and person in PEOPLE and topic=='topicone',
        ianbound=lambda community,anchor:Fraction(1 if correct(community,anchor) else 0),ianprobe=probe,
        ianbegin=p['iakbegin'],ianend=p['iakend'],ianhistory=p['iakhistory'],ianbefore=p['iakbefore'],
        iamtopics=lambda person,anchor:topics('community',person,anchor),iamscope=lambda person,anchor,topic:correct('community',anchor) and person in PEOPLE and topic=='topicone',
        iambound=lambda person,anchor:Fraction(1 if person in PEOPLE and anchor=='end' else 0),
        aa=lambda person:person in PEOPLE and not (variant=='nonhuman' and person=='other'),
        iampresented=presented,iamclassified=classified,fa=judged,ab=owns,ac=uses,
        fb=lambda judgment,topic,scene:judgment in previous.JUDGMENTS and topic==('topictwo' if variant=='wrong_topic' else 'topicone') and scene in previous.PROBES,
        fd=lambda reason,judgment,scene:reason=='reason' and judgment in previous.JUDGMENTS and scene in previous.PROBES and not (variant=='unsupported' and judgment=='judgmenttwo'),
        ad=lambda guide,person,judgment,scene:variant=='guided' and (guide,person,judgment)==('norm','other','judgmenttwo') and scene in previous.PROBES)
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    primitives={d['name']:p.get(d['name'],thinking.forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,primitives,domain,scenes,budget=12_000_000)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    p={d['name']:thinking.forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def match(node,author,code,scope,context,name,rank):
        return (node,author,scope,context)==('node','author','scope','end') and thinking.code_is(code,name,rank)
    p.update(iagnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iagscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'outside' if variant=='context' else 'end',
        iamreport=lambda n,a,c,s,t:variant!='missing_individual' and match(n,a,c,s,t,'iamschema',2),
        ianreport=lambda n,a,c,s,t:variant!='missing_cohort' and match(n,a,c,s,t,'ianchange',1))
    return [r['value'] for r in evaluate_document(doc,individuals=thinking.DOMAIN,situations=thinking.SCENES,primitives=p)]


CONTRASTS=('empty_people','duplicate_people','omitted_person','extra_person','empty_topics','duplicate_topics','omitted_topic','extra_topic',
    'hidden_middle','reflexive','unclassified_other','outsider_only','bad_indicator')
UNKNOWNS=('unknown_people','unknown_scope','unknown_history','unknown_order','unknown_classification','unknown_response')
SOURCE_CONTRASTS=('drop_departed','unclassified_other','one_person_only','outsider_only','other_owner','wrong_topic','unsupported','guided','nonhuman','wrong_community')


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        definitions=['ianresponse','ianassessed','ianreviewed','ianchange','ianattribution'],
        adds_new_text_coverage=False,semantic_completion=False,collective_causal_integration=False)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    for profile in product(range(4),repeat=3):assert values(profile)==[True,expected(profile)],profile
    for variant in CONTRASTS:assert values(variant=variant,indices=(1,))==[False],variant
    for variant in UNKNOWNS:
        try:values(variant=variant,indices=(1,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    assert values(memoize=False)==values()
    assert source_values()==[True,True,False,False,False]
    assert source_values(indices=(5,6))==[True,True]
    assert source_values(state_bits=(False,False,False),indices=(0,1))==[True,False]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context','missing_individual','missing_cohort'):assert attribution(path,variant)==[False]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    assert new['statements'][-1]['body']['arguments'][0]==old['statements'][-1]['body']
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,UNITS,'scripts/compose_cohort_response.py','scripts/check_cohort_response.py',
        'tests/test_cohort_response.py','scripts/check_reasoned_response.py','scripts/check_caused_choice.py',
        'noema/constructed.py','noema/constructed_semantics.py','noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py']
    return dict(status='fixed_cohort_response_growth_checked_not_collective_causality',documents=documents,two_member_profile_combinations=64,
        source_alignment=alignment(),roundtrips=True,uncached_generic_baseline_checked=True,source_uses_closure_cache=True,
        limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    r=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==r
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(r,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Fixed-cohort response growth verified; collective causal integration remains incomplete')


if __name__=='__main__':main()
