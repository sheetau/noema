"""Bind one continuing configuration to agreement, intention and protection."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, FunctionValue, evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.specialization import specialize_definition
from scripts.check_assessed_payments import description
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_observed_protection as observed
from scripts import check_public_deliberation as deliberation
from scripts.compose_limits import call as k
from scripts.compose_institutional_choices import ROOT, PARENT, BUILDERS, ITEM, DIFFERENCE, CHANGE, WISH, PRESERVE, SOURCE_CHANGE, SOURCE_WISH, CONFIG

REPORT = ROOT / 'reports/institutional-choices-v1.json'
DOMAIN = ('alice', 'bob', 'alpha', 'beta', 'old', 'new', 'pact', 'firstact', 'secondact', 'plan', 'p', 't', 's')
SCENES = ('past', 'now', 'later', 'alternative')
EXTRA = '''r jnperson[] a.r jncommunity[] a.r jnolder[] a.r jnnewer[] a.r jnagreement[] a.r jncontext[] d.
r jnstate[a a d] c.d jnconfig[community a institution a] e[b point[k jnstate[v community v institution v point]]].
r jnhistories[d] h[d] c.r jnbefore[d d] c.r jnparties[a d] c.r jnproponents[a d] c.r jneligible[a] c.
r jnassigned[a i[h[j[a]] e] d] c.r jnoccurs[a d] c.r jnperforms[a a d] c.
r jndeclares[a a a i[h[j[a]] e] j[a] d] c.r jnmembers[a a d] c.r jnattributed[a a d] c.r jncomparisons[d] c.
r jnaims[a a i[h[j[a]] e] j[a] d] c.
r jnolders[a] a.r jnnewers[a] a.r jnagreements[a] a.r jnpartiesby[a] h[a d] c.r jnproponentsby[a] h[a d] c.
r jnchangegoals[a] h[h[a] c] c.r jnstaygoals[a] h[h[a] c] c.'''
REFS = {n: 'k jn' + n + '[]' for n in ('person', 'community', 'older', 'newer', 'agreement', 'context')}
REFS.update({n: 'p jn' + n for n in ('histories', 'before', 'parties', 'proponents', 'eligible', 'assigned', 'occurs',
    'performs', 'declares', 'members', 'attributed', 'comparisons', 'aims', 'olders', 'newers', 'agreements', 'changegoals', 'staygoals')})
REFS.update(institution=REFS['older'], history='c[p jnhistories][k jncontext[]]', persons=REFS['proponents'], anchor=REFS['context'])


def assemble(text):
    doc = candidate(text, EXTRA)
    base_text = k('rle', 'p jnconfig')
    specialized = specialize_definition(doc, 'rld', 'jncontinue', {0: description(doc, base_text)})
    doc = specialized.document
    terms_text = k('jncontinue', 'p jnhistories', 'p jnbefore')
    terms = description(doc, terms_text)
    doc = parse(format_graph(doc, 'compact') + 'd jnalias[] h[j[a]] e[' + terms_text + '].')
    return dict(document=doc, terms=terms, terms_text=terms_text, terms_syntax=syntax(terms), base_text=base_text,
        disquotations_removed=specialized.disquotations_removed)


def setup(text, source=False, only_wish=False):
    data = assemble(text); refs = dict(REFS, terms='r[' + data['terms_text'] + ']')
    calls = [('hzel', SOURCE_CHANGE), ('hzem', SOURCE_WISH)] if source else [('rlb', CHANGE), ('rlc', WISH)]
    if only_wish: calls = calls[1:]
    queries = []
    for name, fields in calls:
        expr = k(name, *(refs[n] for n, _ in fields))
        if source: expr = 't[' + expr + '][k jncontext[]]'
        queries.append('q[' + expr + '].')
    data['document'] = parse(format_graph(data['document'], 'compact') + ''.join(queries))
    return data


def model_for(data, bits=(True,) * 4, variant='baseline', scenes=SCENES):
    doc = data['document']; model = guarded(doc)
    assigned, first, second, aim = bits; expected = data['terms_syntax']
    order = tuple(point for point in ('past', 'selection', 'now', 'actual', 'later') if point in scenes)
    def history(point):
        selected = order if point in order else (point,)
        return FunctionValue(('situation',), 'truth', lambda p: p in selected)
    def state(community, institution, point):
        if community not in ('alpha', 'beta'): return False
        if variant == 'mere_alias': return institution in ('old', 'new') and point in order
        if variant == 'later_failure' and point == 'later': return False
        return institution == ('new' if point == 'alternative' else 'old')
    def party(person, point):
        return person in (('alice',) if variant == 'single_party' else ('alice', 'bob')) and point in ('now', 'selection')
    def assigned_terms(agreement, desc, point):
        return assigned and agreement == 'pact' and desc.syntax == expected and point in ('now', 'selection')
    def declared(person, act, agreement, desc, bindings, point):
        owner = 'bob' if variant == 'wrong_owner' and person == 'alice' else person
        target = 'old' if variant == 'wrong_institution' else 'new'
        community = 'beta' if variant == 'wrong_community' else 'alpha'
        permitted = first if person == 'alice' else second if person == 'bob' else False
        return permitted and agreement == 'pact' and desc.syntax == expected and bindings.items == (owner, community, target) and (
            (person, act, point) in (('alice', 'firstact', 'past'), ('bob', 'secondact', 'past')))
    def attributed(community, obj, point):
        return variant != 'unattributed' and community == 'alpha' and obj in ('pact', 'plan') and point in ('now', 'selection')
    def aims(person, act, desc, bindings, point):
        if not aim or person not in ('alice', 'bob'): return False
        target_act = ('firstact' if person == 'alice' else 'secondact') if variant == 'split_plans' else 'plan'
        institution = 'new' if variant == 'wrong_wish' else 'old'
        return act == target_act and desc.syntax == expected and bindings.items == (person, 'alpha', institution) and point in ('now', 'selection')
    model.update(jnperson=lambda: 'alice', jncommunity=lambda: 'alpha', jnolder=lambda: 'old', jnnewer=lambda: 'new',
        jnagreement=lambda: 'pact', jncontext=lambda: 'now', jnstate=state, jnhistories=history,
        jnbefore=lambda a, b: a in order and b in order and order.index(a) < order.index(b),
        jnparties=party, jnproponents=lambda person, point: person in ('alice', 'bob') and point in ('now', 'selection') and variant != 'empty_wish',
        jneligible=lambda person: person in ('alice', 'bob'), jnassigned=assigned_terms,
        jnoccurs=lambda act, point: act in ('firstact', 'secondact') and point == 'past',
        jnperforms=lambda person, act, point: (person, act, point) in (('alice', 'firstact', 'past'), ('bob', 'secondact', 'past')),
        jndeclares=declared, jnmembers=lambda community, person, point: community == 'alpha' and person in ('alice', 'bob') and not (variant == 'nonmember' and person == 'bob'),
        jnattributed=attributed, jncomparisons=lambda point: point in scenes and variant != 'empty_comparisons', jnaims=aims)
    for name, other in (('aa', 'jneligible'), ('dg', 'jnoccurs'), ('f3', 'jnperforms')):
        if name in model: model[name] = model[other]
    if 'ic' in model: model['ic'] = lambda first, last, context: model['jnbefore'](first, last)
    return model


def choices_checks(texts):
    data = [setup(texts[0]), *[setup(t, True) for t in texts[1:]]]; cases = []
    for bits in product((False, True), repeat=4):
        expected = [all(bits[:3]), bits[3]]
        rows = [values(d['document'], model_for(d, bits), DOMAIN, SCENES) for d in data]
        if rows != [expected] * len(data): raise ValueError('Agreement and intention conflated: ' + repr((bits, rows)))
        cases.append(dict(bits=list(bits), results=expected))
    contrasts = {}
    for variant in ('mere_alias', 'single_party', 'wrong_owner', 'wrong_institution', 'wrong_community', 'unattributed',
                    'split_plans', 'wrong_wish', 'empty_wish', 'nonmember', 'empty_comparisons'):
        expected = [False, False] if variant in ('unattributed', 'nonmember') else [True, False] if variant in ('split_plans', 'wrong_wish', 'empty_wish') else [False, True]
        rows = [values(d['document'], model_for(d, variant=variant), DOMAIN, SCENES) for d in data]
        if rows != [expected] * len(data): raise ValueError('Choice contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = expected
    for text in texts[1:]:
        d = setup(text, True, True); model = model_for(d)
        for name in ('jnstate', 'dg', 'f3', 'jnoccurs', 'jnperforms'): model[name] = guarded(d['document'])[name]
        if values(d['document'], model, DOMAIN, SCENES) != [True]: raise ValueError('Wanting continuity executed its goal or plan')
    return dict(cases=cases, contrasts=contrasts, unimplemented_new_institution_can_be_agreed=True,
        wish_does_not_execute_plan_or_goal=True, same_terms_and_ordered_bindings=True)


def continuity_checks(texts):
    rows = []
    for text in texts:
        d = assemble(text); refs = dict(REFS, terms='r[' + d['terms_text'] + ']')
        base = 'c[' + d['base_text'] + '][l[a][k jnperson[] k jncommunity[] k jnolder[]]]'
        continued = k('rk7', *(refs[n] for n, _ in ITEM))
        doc = parse(format_graph(d['document'], 'compact') + 'q[t[' + base + '][k jncontext[]]].q[t[' + continued + '][k jncontext[]]].')
        d['document'] = doc
        for variant, expected in (('baseline', [True, True]), ('later_failure', [True, False])):
            actual = values(doc, model_for(d, variant=variant), DOMAIN, SCENES)
            if actual != expected: raise ValueError('Continuation reduced to current configuration')
            rows.append(actual)
    return dict(results=rows, later_failure_matters=True, static_binding_executed_no_primitives=True)


def policy_setup(text, continuing=True):
    d = assemble(text)
    if not continuing:
        d['terms_text'] = d['base_text']
        d['terms'] = description(d['document'], d['terms_text'])
        d['terms_syntax'] = syntax(d['terms'])
    doc = parse(format_graph(d['document'], 'compact') + observed.EXTRA)
    position = next(i for i, (n, _) in enumerate(CONFIG) if n == 'terms')
    bound = specialize_definition(doc, 'hzen', 'jnpolicy', {position: d['terms']})
    refs = {**observed.REFS, **REFS, 'anchor': 'k jvanchor[]', 'parties': 'p jnpartiesby', 'proponents': 'p jnproponentsby'}
    fields = [(n, t) for n, t in CONFIG if n != 'terms']
    target = k('jnpolicy', *(refs[n] for n, _ in fields))
    doc = parse(format_graph(bound.document, 'compact') + 'q[t[' + target + '][k jvcontext[]]].')
    return dict(d, document=doc, policy_text=target, policy_description=description(doc, target),
        policy_disquotations_removed=bound.disquotations_removed)


def policy_model(d, variant='baseline'):
    # The causal fixture needs its eight assignments and two distinct ordinary
    # points. Declaration and selection may coincide; continuation to actual
    # remains nontrivial. Longer temporal contrasts are checked separately.
    scenes = observed.SCENES
    model = model_for(d, scenes=scenes)
    causal = observed.model_for(d['document'])
    for name in causal:
        if name.startswith(('jv', 'jo')): model[name] = causal[name]
    # Extend contents to this interpretation's full situation domain.
    model['jvpolicytruth'] = lambda point: point == 'actual' or point.startswith('w') and point[1] == '1'
    model['jvthreats'] = lambda community: Content(scenes, tuple(point.startswith('w') and point[2] == '1' for point in scenes))
    def config(community, institution, point):
        if community not in ('alpha', 'beta'): return False
        if point.startswith('w'):
            desired = point[3] == '1'
            return desired if institution == ('new' if community == 'alpha' else 'old') else not desired
        return institution == ('new' if community == 'alpha' and point in ('actual', 'later') else 'old')
    if variant == 'wrong_activity':
        original = config
        config = lambda community, institution, point: not original(community, institution, point) if community == 'alpha' and point.startswith('w') else original(community, institution, point)
    model['jnstate'] = config
    model['jncontext'] = lambda: 'selection'
    model['jnoccurs'] = lambda act, point: act in ('firstact', 'secondact') and point == 'selection'
    model['jnperforms'] = lambda person, act, point: point == 'selection' and (person, act) in (('alice', 'firstact'), ('bob', 'secondact'))
    model['jndeclares'] = lambda person, act, agreement, desc, bindings, point: (
        model['jnperforms'](person, act, point) and agreement == 'pact' and desc.syntax == d['terms_syntax']
        and bindings.items == (person, 'alpha', 'new'))
    model['dg'] = model['jnoccurs']; model['f3'] = model['jnperforms']
    party = model['jnparties']; proponent = model['jnproponents']
    model['jnolders'] = lambda community: 'old'; model['jnnewers'] = lambda community: 'new'; model['jnagreements'] = lambda community: 'pact'
    model['jnpartiesby'] = lambda community: FunctionValue(('individual', 'situation'), 'truth', lambda person, point: community == 'alpha' and party(person, point))
    model['jnproponentsby'] = lambda community: FunctionValue(('individual', 'situation'), 'truth', lambda person, point: community == 'beta' and proponent(person, point))
    model['jnmembers'] = lambda community, person, point: community in ('alpha', 'beta') and person in ('alice', 'bob')
    model['jnattributed'] = lambda community, obj, point: (community, obj) in (('alpha', 'pact'), ('beta', 'plan')) and point in ('now', 'selection')
    model['jnaims'] = lambda person, act, desc, bindings, point: person in ('alice', 'bob') and act == 'plan' and desc.syntax == d['terms_syntax'] and bindings.items == (person, 'beta', 'old') and point in ('now', 'selection')
    model['jnchangegoals'] = model['jvgoals']; model['jnstaygoals'] = model['jvgoals']
    if variant == 'inactive_policy': model['jvpolicytruth'] = lambda point: point.startswith('w') and point[1] == '1'
    return model, scenes


def policy_checks(texts):
    rows = []; removed = []
    for text in texts:
        d = policy_setup(text, continuing=False); removed.append(d['policy_disquotations_removed'])
        for variant, expected in (('baseline', [True]), ('wrong_activity', [False]), ('inactive_policy', [False])):
            print('Checking institutional policy', len(text), variant, flush=True)
            model, scenes = policy_model(d, variant)
            results = evaluate_document(d['document'], primitives=model, individuals=DOMAIN, situations=scenes,
                max_steps=64_000_000, memoize_definitions=True, memoize_expressions=True)
            actual = [r['value'] for r in results]
            if actual != expected: raise ValueError('Chosen institution/protected activity differs: ' + repr((variant, actual)))
            rows.append(dict(variant=variant, results=actual))
    return dict(cases=rows, disquotations_removed=removed, same_terms_select_and_define_activity=True,
        terms='configuration via rle; persistence rld checked separately',
        continuing_policy_direct_evaluation=dict(status='step_budget_exceeded', max_steps=64_000_000,
            fixture='core baseline, 13 individuals and 10 situations; not a semantic counterexample'))


def proposal_checks(texts):
    rows = []
    for text in texts:
        d = policy_setup(text); base = d['document']; base['statements'] = []
        doc = parse(format_graph(base, 'compact') + deliberation.EXTRA)
        refs = dict(deliberation.REFS, proposal='r[' + d['policy_text'] + ']')
        query = 't[' + k('hzef', *(refs[n] for n, _ in deliberation.SOURCE)) + '][k jxafter[]]'
        doc = parse(format_graph(doc, 'compact') + 'q[' + query + '].')
        model = deliberation.model_for(doc); expected = syntax(d['policy_description']); participation = model['jxparticipates']
        model['jxproposes'] = lambda person, act, desc, point: participation(person, act, point) and desc.syntax == expected
        actual = values(doc, model, deliberation.DOMAIN, deliberation.SCENES)
        if actual != [True]: raise ValueError('Proposed institutional choice executed unknown policies')
        rows.append(actual)
    return dict(results=rows, unknown_choices_policy_and_observations_not_executed=True, static_specialization=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored institutional choices differ')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Institutional choices roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    segments = []
    for phrase in ('zu einer veränderten Religionseinrichtung geeinigt hätten', 'die es beim Alten wollten bewenden lassen'):
        if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source range')
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)],
            text=phrase, definitions=['rk7', 'rla', 'rlb', 'rlc', 'rld', 'rle', 'rlf', 'hzel', 'hzem', 'hzen']))
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_institutional_choices.py', 'scripts/check_institutional_choices.py', 'scripts/check_observed_protection.py',
        'scripts/check_public_deliberation.py', 'scripts/check_assessed_payments.py', 'scripts/check_conditional_release.py',
        'scripts/check_described_appraisals.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/finite_semantics.py', 'noema/specialization.py', 'noema/extraction.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_institutional_choice_and_continuation', documents=documents, sizes=sizes,
        choices=choices_checks(texts), continuity=continuity_checks([texts[0], texts[2]]), policy=policy_checks(texts[1:]), proposals=proposal_checks(texts[1:]),
        alignment=dict(segments=segments, semantic_completion=False), new_definitions=10, new_primitives=0, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Institutional choices report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Institutional agreement, explicit continuation aims and the protected activity checked')


if __name__ == '__main__': main()
