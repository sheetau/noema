"""Check authority/topic bindings in the actual scoped policy and attitude."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_topic_scopes import ROOT, PARENT, SOURCE, CORE, BASIS, SCOPE, build, basis
from scripts.compose_public_permission_risk import FIELD_SYMBOLS, INPUTS
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k
from scripts.check_policy_recognition import source_setup as parent_setup
from scripts.check_public_permission_risk import DOMAIN, SCENES

REPORT = ROOT / 'reports/topic-scopes-v1.json'
PEOPLE = ('person','other')
TOPICS = ('topic','topic2')


@lru_cache(maxsize=1)
def setup():
    parent = parent_setup(); doc = deepcopy(parent['document']); doc['statements'] = []
    existing = {d['name'] for d in doc['declarations']}
    core = parse((ROOT/CORE).read_text(encoding='utf-8'))
    doc['declarations'] += [d for d in core['declarations'] if d['name'] not in existing]
    # A pure fixture selector returns one of two locally issued descriptions.
    # No mutable captures or descriptions from another evaluator are needed.
    fixture = parse('p:r jdchoose[a i[a] i[a]] i[a].r jdsubjectone[] a.r jdsubjecttwo[] a.' +
        definition(FIELD_SYMBOLS['subject'], 'person a activity a anchor d',
            'k jdchoose[v person r[k jdsubjectone[]] r[k jdsubjecttwo[]]]', 'i[a]'))
    replacement = fixture['declarations'][-1]
    doc['declarations'] = fixture['declarations'][:-1] + [
        replacement if d['name'] == replacement['name'] else d for d in doc['declarations']]
    refs = dict(ruler=k('hzmruler'), anchor=k('wh'), people='p hzmpeople', activities='p hzmactivities',
        subject='p ' + FIELD_SYMBOLS['subject'], domains='p hzodomains')
    queries = [k('rrr', *(refs[n] for n,_ in SCOPE)), 't[s[k hzopolicy[]]][k wh[]]',
        't[s[k hzmpolicy[]]][k wh[]]', 't[s[r c[k hzosafety[]]]][k wh[]]',
        't[s[r d[k hzoinsight[]]]][k wh[]]']
    doc = parse(format_graph(doc,'compact') + ''.join('q['+q+'].' for q in queries))
    call = next(d['body'] for d in doc['declarations'] if d['name']=='hzopolicy')
    policy = dict(kind='apply', function=dict(kind='function_ref',symbol='rrs'), arguments=[a['body'] for a in call['arguments']])
    targets = []
    for symbol in ('jdsubjectone','jdsubjecttwo'):
        target = deepcopy(parent['target_syntax'])
        target['arguments'][[n for n,_ in INPUTS].index('subject')] = dict(kind='call',symbol=symbol,arguments=[])
        targets.append(target)
    return dict(document=doc, policy=policy, targets=targets, old_policy=parent['policy_syntax'], old_target=parent['target_syntax'])


def values(selected=PEOPLE, members=(True,True), grants=(True,True), aware=True, actual_safe=True,
           variant='baseline', indices=None, memoize=True, rename=False):
    data = setup(); doc = deepcopy(data['document'])
    if indices is not None: doc['statements'] = [doc['statements'][i] for i in indices]
    def forbidden(*args): raise AssertionError('Scope policy executed speech or an unspecified interpretation')
    model = {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def people(person, point):
        return person in (selected if point=='anchor' else (('person',) if variant=='late_population' else ()))
    def domains(ruler, topic, context):
        if variant=='unknown_domains': raise ValueError('Unknown topic scope')
        return ((ruler,context)==('other' if variant=='wrong_authority' else 'ruler',
            'safe' if variant=='outcome_scope' else 'anchor') and topic in TOPICS and members[TOPICS.index(topic)])
    def allowed(ruler,person,role,act,code,sign,point):
        if (ruler,role,act,sign)!=('ruler','role','act',True) or person not in PEOPLE: return False
        i = PEOPLE.index(person)
        target = data['old_target'] if variant=='wrong_norm_target' else data['targets'][i]
        return grants[i] and json.loads(code.syntax)==target
    def prospects(policy,context,outcome):
        expected = data['old_policy'] if variant=='old_policy_prospects' else data['policy']
        chosen = 'bad' if context=='bad' or (context=='anchor' and not actual_safe) else 'safe'
        return policy.rank==1 and json.loads(policy.syntax)==expected and outcome==chosen
    def awareness(person,code,context):
        symbol = 'hzmsafety' if variant=='old_safety_awareness' else 'hzosafety'
        return aware and (person,context)==('ruler','anchor') and json.loads(code.syntax)==dict(kind='call',symbol=symbol,arguments=[])
    model.update(jdchoose=lambda person,left,right: left if person=='person' else right,
        jdsubjectone=lambda: 'channel' if variant=='wrong_subject' else 'topic', jdsubjecttwo=lambda:'topic2',
        jdrole=lambda:'role', jdsubject=lambda:'topic', jdrecipient=lambda:'world', jdchannel=lambda:'channel',
        hzmruler=lambda:'ruler', wh=lambda:'anchor', hzmpeople=people,
        hzmactivities=lambda person,act,point: act=='act' and point=='anchor',
        hzodomains=domains, h7a=lambda *args: False, h7b=allowed,
        hzmprospects=prospects, hzmadverse=lambda point:point=='bad', hznawareness=awareness,
        hznalternatives=lambda person,code,context,candidate: (person,context,candidate)==('ruler','anchor','safe')
            and json.loads(code.syntax)==dict(kind='call',symbol='hzosafety',arguments=[]))
    domain = DOMAIN + ('topic2',)
    if rename:
        mapping = dict(zip(domain, ('chair','member','guest','discussion','speaker','public','policy-a','forum','audience','capacity','policy-b'),strict=True))
        inverse = {value:key for key,value in mapping.items()}
        def wrap(function):
            def renamed(*args):
                result = function(*(inverse.get(a,a) if isinstance(a,str) else a for a in args))
                return mapping.get(result,result) if isinstance(result,str) else result
            return renamed
        model = {name:wrap(fn) for name,fn in model.items()}
        domain = tuple(mapping[p] for p in domain)
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=SCENES,primitives=model,
        max_steps=100_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


def attribution(doc):
    doc = deepcopy(doc); doc['statements'] = doc['statements'][-1:]
    rows = []
    for attributed in (False,True):
        def forbidden(*args): raise AssertionError('Attribution executed scoped content')
        def report(node,author,code,scope,context):
            assert (node,author,scope,context)==('node','author','scope','context')
            assert code.rank==3 and json.loads(code.syntax)==dict(kind='call',symbol='hzoinsight',arguments=[])
            return attributed
        model = {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        model.update(hznreport=report,hzonode=lambda:'node',hzoscope=lambda:'scope',wa=lambda:'author',wh=lambda:'context')
        result = evaluate_document(doc,individuals=('node','scope','author'),situations=('context',),primitives=model)
        assert result==[dict(kind='assert',value=attributed)]; rows.append(result)
    return rows


def build_report():
    documents = {}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc = parse(text)
        for notation in ('full','compact'):
            formatted = format_graph(doc,notation)
            assert parse(formatted)==doc and parse(transcribe(formatted,alphabet='v2'))==doc
        documents[path] = dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text),attribution=attribution(doc))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    parent,source = [parse((ROOT/p).read_text(encoding='utf-8')) for p in (PARENT,SOURCE)]
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert source['statements'][:-1]==parent['statements'][:-1]
    matrix = []
    for first,second,member1,member2,grant1,grant2 in product((False,True),repeat=6):
        selected = tuple(p for p,b in zip(PEOPLE,(first,second),strict=True) if b)
        scoped = (not first or member1) and (not second or member2)
        permitted = (not first or grant1) and (not second or grant2)
        result = values(selected,(member1,member2),(grant1,grant2))
        assert result==[scoped,scoped and permitted,permitted,scoped and permitted,scoped and permitted]
        matrix.append(dict(selected=selected,members=[member1,member2],grants=[grant1,grant2],result=result))
    contrasts = {}
    for variant,expected in (
        ('wrong_authority',[False,False,True,False,False]), ('outcome_scope',[False,False,True,False,False]),
        ('wrong_subject',[False,False,True,False,False]), ('wrong_norm_target',[True,False,False,False,False]),
        ('old_policy_prospects',[True,True,True,False,False]), ('old_safety_awareness',[True,True,True,True,False])):
        contrasts[variant] = values(variant=variant); assert contrasts[variant]==expected
    uncached = values(members=(True,False),indices=(0,1,2),memoize=False)
    assert uncached==values(members=(True,False),indices=(0,1,2))==[False,False,True]
    unit = next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0016')
    phrases = ('sieht ein','in Ansehung seiner Gesetzgebung',
        'es ohne Gefahr sei, seinen Unterthanen zu erlauben, von ihrer eigenen Vernunft öffentlichen Gebrauch zu machen')
    segments = []
    for phrase in phrases:
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase,
            status='explicit_interpretive_annotation',definitions=['rrr','rrs','rrt','hzopolicy','hzosafety','hzoinsight','hzoattribution']))
    paths = [PARENT,SOURCE,CORE,BASIS,'examples/v016/policy-recognition-core.noema',
        'examples/v016/public-permission-risk-core.noema','scripts/compose_topic_scopes.py','scripts/check_topic_scopes.py',
        'tests/test_topic_scopes.py','scripts/check_policy_recognition.py','scripts/check_public_permission_risk.py',
        'scripts/compose_public_permission_risk.py','noema/constructed.py','noema/constructed_discourse.py',
        'noema/constructed_semantics.py','noema/guarded_ranked_semantics.py','artifacts/written-units-v1/kant-1784.json']
    result = dict(status='partial_authority_topic_scope_source_connection',documents=documents,
        parent_declarations_and_first_16_statements_preserved=True,revised_fragment_attributions=1,roundtrips=True,
        finite_interpretation=dict(matrix=matrix,contrasts=contrasts,uncached_scope_and_policy_comparison=uncached),
        alignment=dict(semantic_completion=False,segments=segments),limitations=basis()['unresolved'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    return json.loads(json.dumps(result))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result = build_report()
    if args.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream: json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Authority-bound topics, scoped permissions and recognition verified')


if __name__=='__main__': main()
