"""Check past adoption, constructed criticism and the extended source policy."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_prior_criticism import ROOT, PARENT, SOURCE, CORE, BASIS, DISCLOSURES, LAW_CODES, LAW_SYMBOLS, build, basis
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k
from scripts.compose_public_permission_risk import FIELD_SYMBOLS, ACTION
from scripts.compose_comparative_speech import DETAILS, DETAIL_SYMBOLS, CCODE
from scripts.compose_candid_assessments import CRITERION
from scripts.compose_disclosure_actions import FIELDS
from scripts.compose_described_norms import TRUE
from scripts.check_disclosure_actions import explicit_target, REFS

REPORT = ROOT / 'reports/prior-criticism-v1.json'
INDIVIDUALS = ('person', 'act', 'topic', 'other', 'role', 'world', 'reader', 'channel',
               'ruler', 'adopter', 'legalrole', 'first', 'second', 'faculty')
SCENES = ('prior', 'anchor', 'candidate', 'outcome', 'later', 'elsewhere')


@lru_cache(maxsize=1)
def setup():
    doc = parse((ROOT / CORE).read_text(encoding='utf-8'))
    doc['statements'] = []
    text = ''.join('r jd' + name + '[] a.' for name in ('first', 'second', 'person', 'act', 'subject', 'role', 'recipient', 'channel', 'adopter', 'legalrole'))
    text += 'r jdscope[a d] c.r jdaudience[a] c.r jdvoices[a a a a a i[h[a] f] d] c.'
    text += 'r jdmetone[a d] c.r jdmettwo[a d] c.r jdhistory[d] c.r jdbefore[d d] c.r jdoldvalid[d] c.'
    text += 'r jdselectcriterion[i[a] ' + CRITERION + ' ' + CRITERION + '] ' + CRITERION + '.'
    text += 'r jdselectpolarity[i[a] i[c] i[c]] i[c].'
    for name, primitive in (('jdstandardone', 'jdmetone'), ('jdstandardtwo', 'jdmettwo')):
        text += definition(name, 'subject a', 'b point[' + k(primitive, 'v subject', 'v point') + ']', 'e')
    text += definition('jdcondition', 'person a', 'b point[' + TRUE + ']', 'e')
    text += definition('jdgoal', 'person a', 'b point[' + TRUE + ']', 'e')
    text += definition('jdoldpolicy', '', 'b point[k jdoldvalid[v point]]', 'e')
    text += 'r jdolder[] a.r jdnewer[] a.r jdforms[a a d] c.r jdcomparelinked[a ' + CCODE + ' a a a d] c.'
    text += 'r jdcomparecandidates[a d d] c.r jdbetter[a a a d] c.'
    text += definition('jdcompare', 'subject a older a newer a', 'b point[k jdbetter[v subject v older v newer v point]]', 'e')
    # Abstract only the already tested old policy, retaining the actual new source definitions.
    replacements = definition('hzppolicy', '', 'r b[k jdoldpolicy[]]', 'i b[e]')
    for name in ('role', 'audience', 'subject', 'recipient', 'channel', 'voices'):
        field_type = dict(FIELDS)[name]
        replacements += definition(FIELD_SYMBOLS[name], 'person a activity a anchor d', 'r[' + REFS[name] + ']', field_type)
    replacements += definition('hzqrecords', 'person a activity a anchor d', 'l[i[a]][r[k jdfirst[]] r[k jdsecond[]]]', 'j[i[a]]')
    replacements += definition('hzqscope', 'person a activity a anchor d', 'r[p jdscope]', 'i[h[a d] c]')
    replacements += definition('hzqcriteria', 'person a activity a anchor d record i[a]',
        'k jdselectcriterion[v record r[p jdstandardone] r[p jdstandardtwo]]', CRITERION)
    replacements += definition('hzqpolarities', 'person a activity a anchor d record i[a]',
        'k jdselectpolarity[v record r[' + TRUE + '] r[u[' + TRUE + ']]]', 'i[c]')
    codes = dict(adopter='r[k jdadopter[]]', lawrole='r[k jdlegalrole[]]', condition='r[p jdcondition]',
                 goal='r[p jdgoal]', positive='r[' + TRUE + ']', history='r[p jdhistory]', before='r[p jdbefore]')
    for name, type_ in LAW_CODES:
        replacements += definition(LAW_SYMBOLS[name], 'person a activity a anchor d', codes[name], type_)
    comparison = dict(criterion='r[p jdcompare]', older='r[k jdolder[]]', newer='r[k jdnewer[]]',
        forms='r[p jdforms]', linked='r[p jdcomparelinked]', candidates='r[p jdcomparecandidates]')
    for name, type_ in DETAILS:
        replacements += definition(DETAIL_SYMBOLS[name], 'person a activity a anchor d', comparison[name], type_)
    fixture = parse('p:' + text + replacements)
    lookup = {d['name']: d for d in fixture['declarations']}
    doc['declarations'] = [d for d in fixture['declarations'] if d['name'].startswith('jd')] + [lookup.get(d['name'], d) for d in doc['declarations']]
    target_text = explicit_target(('first', 'second'), (True, False), True)
    for old, new in (('p jdjudgments', 'p fa'), ('p jdmatters', 'p fb'),
                     ('p jdlinked', 'p hzqlinked'), ('p jdcandidates', 'p hzqcandidates')):
        target_text = target_text.replace(old, new)
    message = 'c[i[comparison h[a a a] e older a newer a][i[subject a][j s[c[v comparison][v subject v older v newer]]]]][p jdcompare k jdolder[] k jdnewer[]]'
    comparative = 'c[p rrv][p jdcompare r[p jdcompare] k jdolder[] k jdnewer[] p jdforms p jdcomparelinked p jdcomparecandidates '
    comparative += ' '.join('r[' + message + ']' if name == 'message' else REFS[name] for name, _ in ACTION) + ']'
    target_text = 'c[p rsj][' + comparative + ' ' + target_text + ']'
    queries = ['e[k hzqtarget[k jdperson[] k jdact[] k wh[]]][r[' + target_text + ']]',
        't[s[k hzqcritical[]]][k wh[]]', 't[s[k hzqpolicy[]]][k wh[]]',
        't[k hzqsafety[]][k wh[]]', 't[k hzqinsight[]][k wh[]]']
    doc = parse(format_graph(doc, 'compact') + ''.join('q[' + q + '].' for q in queries))
    source = {d['name']: d for d in doc['declarations']}
    critical = dict(kind='apply', function=dict(kind='function_ref', symbol='rsr'),
                    arguments=[a['body'] for a in source['hzqcritical']['body']['arguments']])
    old_policy = dict(kind='call', symbol='jdoldpolicy', arguments=[])
    joint = dict(kind='apply', function=source['rrz']['body']['function']['body'], arguments=[old_policy, critical])
    return dict(document=doc, target=doc['statements'][0]['body']['arguments'][1]['body'], joint=joint, old_policy=old_policy)


def values(past=True, permission=True, old_now=True, old_future=True, adverse=False, aware=True,
           current_adoption=False, selected=True, variant='baseline', indices=None, memoize=True, parts=False):
    data = setup()
    doc = deepcopy(data['document'])
    if parts:
        refs = [dict(kind='call', symbol=name, arguments=[]) for name in ('hzmruler', 'jdperson', 'jdrole', 'jdact')]
        true = parse('p:q[' + TRUE + '].')['statements'][0]['body']
        for part in data['target']['arguments']:
            doc['statements'].append(dict(kind='ask', body=dict(kind='call', symbol='h7b', arguments=refs + [
                dict(kind='quote', body=part), true, dict(kind='call', symbol='wh', arguments=[])])))
        doc = parse(format_graph(doc, 'compact'))
    if indices is not None:
        doc['statements'] = [doc['statements'][i] for i in indices]
    def forbidden(*args):
        raise AssertionError('Policy executed an unknown criticism or unrelated primitive')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    def match(code, node):
        return json.loads(code.syntax) == node
    def order(first, last):
        if variant == 'unknown_history':
            raise ValueError('Unknown temporal order')
        if variant == 'cycle':
            return (first, last) in (('prior', 'anchor'), ('anchor', 'prior'))
        rank = {'prior': 0, 'anchor': 1, 'later': 2}
        if variant == 'reversed_time':
            rank = {'anchor': 0, 'prior': 1, 'later': 2}
        return first in rank and last in rank and rank[first] < rank[last]
    def history(point):
        if variant == 'missing_anchor':
            return point == 'prior'
        return point in ('prior', 'anchor', 'later')
    def adopted(law, adopter, role, condition, goal, positive, point):
        if variant == 'unknown_adoption':
            raise ValueError('Unknown prescription adoption')
        desired = 'later' if variant == 'future_only' else 'elsewhere' if variant == 'other_history' else 'prior'
        exists = past and point == desired or current_adoption and point == 'anchor'
        expected = ('other' if variant == 'other_law' else 'topic',
                    'other' if variant == 'other_adopter' else 'adopter',
                    'role' if variant == 'wrong_law_role' else 'legalrole', variant != 'wrong_law_polarity')
        return exists and (law, adopter, role, positive) == expected and match(condition, dict(kind='function_ref',
            symbol='jdgoal' if variant == 'wrong_condition' else 'jdcondition')) and match(goal, dict(kind='function_ref',
            symbol='jdcondition' if variant == 'wrong_goal' else 'jdgoal'))
    def choose(code, left, right):
        if variant == 'unknown_selector':
            raise ValueError('Unknown assessment selector')
        return left if match(code, dict(kind='call', symbol='jdfirst', arguments=[])) else right
    def allowed(ruler, person, role, act, code, sign, point):
        targets = [data['target']]
        if variant == 'wrong_target':
            targets = [data['target']['arguments'][0]]
        elif variant == 'separate_permissions':
            targets = data['target']['arguments']
        return permission and (ruler, person, role, act, sign) == (
            'ruler', 'person', 'other' if variant == 'wrong_public_role' else 'role', 'act', True) and any(match(code, target) for target in targets)
    def prospects(code, anchor, outcome):
        expected = data['old_policy'] if variant == 'old_policy_prospects' else data['joint']
        return outcome == 'outcome' and match(code, expected)
    def awareness(person, code, context):
        symbol = 'hzpsafety' if variant == 'old_safety_awareness' else 'hzqsafety'
        return aware and person == 'ruler' and match(code, dict(kind='call', symbol=symbol, arguments=[]))
    model.update(jdfirst=lambda: 'first', jdsecond=lambda: 'second', jdperson=lambda: 'person', jdact=lambda: 'act',
        jdsubject=lambda: 'topic', jdrole=lambda: 'role', jdrecipient=lambda: 'world', jdchannel=lambda: 'channel',
        jdadopter=lambda: 'adopter', jdlegalrole=lambda: 'legalrole', wh=lambda: 'anchor', hzmruler=lambda: 'ruler',
        jdselectcriterion=choose, jdselectpolarity=choose, jdhistory=history, jdbefore=order, rba=adopted,
        jdoldvalid=lambda point: old_future if point == 'outcome' else old_now,
        hzmpeople=lambda person, anchor: (person, anchor) == ('person', 'anchor'),
        hzqactivities=lambda person, act, anchor: selected and (person, act, anchor) == ('person', 'act', 'anchor'),
        hzodomains=lambda ruler, subject, anchor: variant != 'wrong_domain' and (ruler, subject, anchor) == ('ruler', 'topic', 'anchor'),
        h7a=lambda *args: False, h7b=allowed, hzmprospects=prospects, hzmadverse=lambda outcome: adverse and outcome == 'outcome',
        hznalternatives=lambda person, code, context, candidate: person == 'ruler' and candidate == 'candidate' and match(code, dict(kind='call', symbol='hzqsafety', arguments=[])),
        hznawareness=awareness)
    return [r['value'] for r in evaluate_document(doc, individuals=INDIVIDUALS, situations=SCENES, primitives=model,
        max_steps=100_000_000, memoize_definitions=memoize, memoize_expressions=memoize)]


def joint_action(comparison=True, criticism=True, variant='baseline'):
    doc = parse((ROOT / CORE).read_text(encoding='utf-8'))
    doc['statements'] = []
    text = 'r jdperson[] a.r jdact[] a.r jdpoint[] d.r jdcomparison[a a d] c.r jdcriticism[a a d] c.'
    text += 'q[t[c[k rsj[i[person a activity a][b point[k jdcomparison[v person v activity v point]]] i[person a activity a][b point[k jdcriticism[v person v activity v point]]]]][k jdperson[] k jdact[]]][k jdpoint[]]].'
    doc = parse(format_graph(doc, 'compact') + text)
    def forbidden(*args):
        raise AssertionError('Unexpected primitive in joint presentation')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update(jdperson=lambda: 'person', jdact=lambda: 'act', jdpoint=lambda: 'anchor',
        jdcomparison=lambda person, act, point: comparison and (person, act, point) == ('person', 'act', 'anchor'),
        jdcriticism=lambda person, act, point: criticism and (person, act, point) == (
            'other' if variant == 'other_person' else 'person', 'other' if variant == 'other_act' else 'act',
            'elsewhere' if variant == 'other_context' else 'anchor'))
    return evaluate_document(doc, individuals=INDIVIDUALS, situations=SCENES, primitives=model)[0]['value']


def attribution(doc):
    doc = deepcopy(doc)
    doc['statements'] = doc['statements'][-1:]
    result = []
    for attributed in (False, True):
        def forbidden(*args):
            raise AssertionError('Attribution executed the quoted criticism policy')
        def report(node, author, code, scope, point):
            assert (node, author, scope, point) == ('node', 'author', 'scope', 'point')
            assert code.rank == 3 and json.loads(code.syntax) == dict(kind='call', symbol='hzqinsight', arguments=[])
            return attributed
        model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
        model.update(hznreport=report, hzqnode=lambda: 'node', wa=lambda: 'author', hzqrange=lambda: 'scope', wh=lambda: 'point')
        row = evaluate_document(doc, individuals=('node', 'author', 'scope'), situations=('point',), primitives=model)
        assert row == [dict(kind='assert', value=attributed)]
        result.append(row)
    return result


def build_report():
    documents = {}
    for path, text in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == text
        doc = parse(text)
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == doc and parse(transcribe(form, alphabet='v2')) == doc
        documents[path] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']), characters=len(text), attribution=attribution(doc))
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    parent, source = [parse((ROOT / p).read_text(encoding='utf-8')) for p in (PARENT, SOURCE)]
    assert source['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert source['statements'][:-1] == parent['statements'][:-1]
    matrix = []
    for past, permission, old_now, old_future, adverse, aware in product((False, True), repeat=6):
        critical = past and permission
        safety = critical and old_future and not adverse
        result = values(past, permission, old_now, old_future, adverse, aware)
        assert result == [True, critical, critical and old_now, safety, safety and aware]
        matrix.append(dict(past=past, permission=permission, old_now=old_now, old_future=old_future, adverse=adverse, aware=aware, result=result))
    contrasts = {}
    for variant in ('future_only', 'other_history', 'missing_anchor', 'cycle', 'reversed_time', 'other_law', 'other_adopter',
                    'wrong_law_role', 'wrong_law_polarity', 'wrong_condition', 'wrong_goal', 'wrong_domain', 'wrong_target', 'wrong_public_role', 'separate_permissions'):
        result = values(variant=variant)
        assert result == [True, False, False, False, False]
        contrasts[variant] = result
    separate = values(variant='separate_permissions', parts=True)
    assert separate == [True, False, False, False, False, True, True]
    for variant, expected in (('old_policy_prospects', [True, True, True, False, False]),
                              ('old_safety_awareness', [True, True, True, True, False])):
        result = values(variant=variant)
        assert result == expected
        contrasts[variant] = result
    uncached = values(indices=(0, 1, 2), memoize=False)
    assert uncached == values(indices=(0, 1, 2)) == [True] * 3
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0016')
    phrases = ('sieht ein', 'in Ansehung seiner Gesetzgebung',
        'es ohne Gefahr sei, seinen Unterthanen zu erlauben, von ihrer eigenen Vernunft öffentlichen Gebrauch zu machen',
        'und ihre Gedanken über eine bessere Abfassung derselben', 'mit', 'Kritik der schon gegebenen', 'der Welt öffentlich vorzulegen')
    segments = []
    for phrase in phrases:
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start + len(phrase)], text=phrase,
            status='explicit_interpretive_annotation', definitions=['rsp', 'rsq', 'rsr', 'rss', 'rsk', 'hzqtarget', 'hzqcritical', 'hzqpolicy', 'hzqsafety', 'hzqinsight', 'hzqattribution']))
    paths = [PARENT, SOURCE, CORE, BASIS, DISCLOSURES, 'scripts/compose_prior_criticism.py', 'scripts/check_prior_criticism.py',
        'tests/test_prior_criticism.py', 'scripts/check_disclosure_actions.py', 'scripts/compose_disclosure_actions.py',
        'scripts/compose_candid_assessments.py', 'scripts/compose_comparative_speech.py', 'scripts/compose_public_permission_risk.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py', 'noema/guarded_ranked_semantics.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_prior_criticism_source_connection', documents=documents,
        parent_declarations_and_first_16_statements_preserved=True, roundtrips=True,
        finite_interpretation=dict(matrix=matrix, contrasts=contrasts, separate_permissions=separate, uncached=uncached,
            scope='Actual new source definitions; the previously tested old combined policy is abstracted to an independent content. Criticism target identity is checked without executing judgments or public speech.'),
        alignment=dict(semantic_completion=False, segments=segments), limitations=basis()['unresolved'],
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    result = build_report()
    if args.verify_only:
        assert json.loads(REPORT.read_text(encoding='utf-8')) == result
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Past adoption, criticism target and extended policy verified')


if __name__ == '__main__':
    main()
