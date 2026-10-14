"""Check period-relative succession, overlapping cohorts and same-era solemn acts."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.specialization import specialize_definition
from scripts.check_assessed_payments import description
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_solemn_undertakings as solemn
from scripts import check_blocked_revision as blocked
from scripts.compose_limits import call as k
from scripts.compose_successive_cohorts import ROOT, PARENT, BUILDERS, PAIR, CATALOG, NEXT, SUCCESSION, SOURCE, UNDERTAKING
from scripts.compose_blocked_revision import SOURCE as REVISION

REPORT = ROOT / 'reports/successive-cohorts-v1.json'
EXTRA = '''r jearly[] a.r jlate[] a.r jfirstgroup[] a.r jnextgroup[] a.r jcontext[] d.
r jepochs[a] c.r jhistory[d] c.r jorder[d d] c.r jperiods[a d] c.
r jpopulation[a] c.r jhuman[a] c.r jpresent[a d] c.r jbelongs[a a d] c.'''
REFS = dict(earlier='k jearly[]', later='k jlate[]', firstgroup='k jfirstgroup[]', nextgroup='k jnextgroup[]',
    context='k jcontext[]', epochs='p jepochs', history='p jhistory', before='p jorder', periods='p jperiods',
    population='p jpopulation', human='p jhuman', present='p jpresent', belongs='p jbelongs')
EPOCHS = ('early', 'late', 'middle')
POINTS = ('one', 'two', 'three')


def period_setup(text):
    return candidate(text, EXTRA + ''.join('q[' + k(name, *(REFS[n] for n, _ in fields)) + '].' for name, fields in (('rjd', PAIR), ('rje', CATALOG), ('rjf', NEXT))))


def period_checks(texts):
    docs = [period_setup(t) for t in texts]
    subsets = [set(i for i in range(3) if mask & (1 << i)) for mask in range(8)]
    count = 0
    for first, last, selected_middle in product(subsets, subsets, (False, True)):
        spans = {'early': first, 'late': last, 'middle': {1}}
        selected = ('early', 'late', 'middle') if selected_middle else ('early', 'late')
        valid = lambda s: bool(s) and s == set(range(min(s), max(s) + 1))
        ordered = lambda a, b: a != b and valid(spans[a]) and valid(spans[b]) and max(spans[a]) < min(spans[b])
        frame = all(valid(spans[a]) for a in selected) and all(a == b or ordered(a, b) or ordered(b, a) for a in selected for b in selected)
        pair = ordered('early', 'late')
        following = frame and pair and not any(ordered('early', m) and ordered(m, 'late') for m in selected)
        want = [pair, frame, following]
        for doc in docs:
            model = guarded(doc)
            model.update(jearly=lambda: 'early', jlate=lambda: 'late', jepochs=lambda a: a in selected,
                jhistory=lambda s: s in POINTS, jorder=lambda a, b: POINTS.index(a) < POINTS.index(b),
                jperiods=lambda a, s: s in POINTS and POINTS.index(s) in spans.get(a, set()))
            if values(doc, model, EPOCHS, POINTS) != want: raise ValueError('Periodization differs from interval/set oracle')
        count += 1
    return dict(models=count, independent_interval_oracle=True, standalone_agrees=True,
        changing_catalog_can_change_successor=True, gaps_not_assumed_filled=True)


DOMAIN = (*solemn.mutual.PEOPLE, *EPOCHS, 'oldgroup', 'newgroup')
SCENES = solemn.mutual.SCENES


def cohort_setup(text):
    return candidate(text, EXTRA + 'q[' + k('rjh', *(REFS[n] for n, _ in SUCCESSION)) + '].')


def cohort_model(doc, variant='baseline'):
    model = guarded(doc)
    order = ('first', 'second', 'now', 'future')
    spans = {'early': {'first', 'second', 'now'}, 'late': {'future'}, 'middle': {'now'}}
    selected = ('early', 'late')
    if variant == 'intervening': spans['early'] = {'first', 'second'}; selected = EPOCHS
    if variant == 'overlap': spans['late'] = {'now', 'future'}
    if variant == 'gap_inside': spans['early'] = {'first', 'now'}
    if variant == 'outside_history': spans['late'] = {'elsewhere'}
    if variant == 'act_outside': spans['early'] = {'second', 'now'}
    if variant == 'late_context': spans['early'] = {'first', 'second'}; spans['late'] = {'now', 'future'}
    if variant == 'no_selected_later': selected = ('early',)
    humans = ('alpha', 'beta', 'other')
    first_members = {'alpha', 'beta', 'other'}
    next_members = {'beta', 'other'}
    if variant == 'party_outside': first_members.remove('beta')
    if variant == 'disjoint_members': next_members = {'other'}; first_members = {'alpha', 'beta'}
    if variant == 'same_members': next_members = set(first_members)
    if variant == 'empty_next': next_members = set()
    def present(person, scene):
        return person in first_members and scene in spans['early'] or person in next_members and scene in spans['late']
    def belongs(group, person, context):
        if context != 'now': return False
        if variant == 'missing_member' and (group, person) == ('oldgroup', 'alpha'): return False
        if variant == 'nonhuman_member' and (group, person) == ('oldgroup', 'acta'): return True
        if variant == 'extra_member' and (group, person) == ('newgroup', 'alpha'): return True
        return person in (first_members if group == 'oldgroup' else next_members if group == 'newgroup' else set())
    def before(a, b):
        if variant == 'cyclic' and (a, b) == ('now', 'first'): return True
        return a in order and b in order and order.index(a) < order.index(b)
    model.update(jearly=lambda: 'late' if variant == 'reverse' else 'early', jlate=lambda: 'early' if variant == 'reverse' else 'late',
        jfirstgroup=lambda: 'oldgroup', jnextgroup=lambda: 'oldgroup' if variant == 'same_group' else 'newgroup',
        jcontext=lambda: 'now', jepochs=lambda a: a in selected, jhistory=lambda s: s in order, jorder=before,
        jperiods=lambda a, s: s in spans.get(a, set()), jpopulation=lambda a: a in humans and not (variant == 'population_changed' and a == 'other'),
        jhuman=lambda a: a in humans, jpresent=present, jbelongs=belongs)
    return model


def cohort_checks(texts):
    docs = [cohort_setup(t) for t in texts]; cases = {}
    positive = ('baseline', 'disjoint_members', 'same_members', 'act_outside', 'party_outside', 'late_context')
    negative = ('intervening', 'overlap', 'gap_inside', 'outside_history', 'no_selected_later', 'empty_next',
        'missing_member', 'nonhuman_member', 'extra_member', 'cyclic', 'reverse', 'same_group', 'population_changed')
    for variant in positive + negative:
        want = [variant in positive]
        rows = [values(d, cohort_model(d, variant), DOMAIN, SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Cohort contrast ' + variant + ': ' + repr(rows))
        cases[variant] = want
    for d in docs:
        for name in ('jepochs', 'jperiods', 'jpopulation', 'jpresent', 'jbelongs'):
            model = cohort_model(d); model[name] = guarded(d)[name]
            try: values(d, model, DOMAIN, SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown cohort relation guessed')
    return dict(contrasts=cases, standalone_agrees=True, overlapping_members_allowed=True,
        unknown_relations_refused=True, biological_parenthood_not_assumed=True)


def source_setup(text):
    doc = candidate(text, EXTRA + solemn.EXTRA + blocked.EXTRA)
    # Same later collective is the epistemic holder, in its own future period.
    revision_refs = blocked.REFS | dict(holder='k jnextgroup[]')
    unavailable = k('hzdd', *(revision_refs[n] for n, _ in REVISION))
    effect_text = 'b anchor[g point d[w[k jperiods[k jlate[] v point]][t[' + unavailable + '][v point]]]]'
    effect = description(doc, effect_text)
    specialized = specialize_definition(doc, 'hzcq', 'jcohortcause', {1: effect}); doc = specialized.document
    agents = 'i[person a][k jg[v person k je[]]]'
    goal_text = k('jcohortcause', agents, 'p jlcause')
    goal = description(doc, goal_text)
    refs = solemn.REFS | REFS | dict(context='k je[]', history='p jj', goal='r[' + goal_text + ']')
    queries = 'q[' + k('hzde', *(refs[n] for n, _ in SOURCE)) + '].q[' + k('hzdf', *(refs[n] for n, _ in UNDERTAKING)) + '].'
    doc = parse(format_graph(doc, 'compact') + queries)
    return doc, goal, effect, dict(bound_positions=specialized.bound_positions,
        expanded_definitions=specialized.expanded_definitions, disquotations_removed=specialized.disquotations_removed)


def source_model(setup, aimed=True, solemnity=True, variant='baseline'):
    doc, goal, _, _ = setup
    model = solemn.model_for(doc, bits=(solemnity,) * 4, aimed=aimed)
    cohorts = cohort_model(doc, variant)
    model.update({n: value for n, value in cohorts.items() if n.startswith(('jearly', 'jlate', 'jfirstgroup', 'jnextgroup', 'jcontext', 'jepochs', 'jhistory', 'jorder', 'jperiods', 'jpopulation', 'jhuman', 'jpresent', 'jbelongs'))})
    model['jj'] = cohorts['jhistory']
    model['ic'] = lambda a, b, c: c == 'now' and cohorts['jorder'](a, b)
    model['aa'] = cohorts['jhuman']
    expected = syntax(goal)
    model['hzu'] = lambda p, act, content, scene: aimed and (p, act, scene) == ('alpha', 'acta', 'first') and content.syntax == expected
    if variant == 'wrong_goal':
        expected = syntax(description(doc, 'k jwother[]'))
        model['hzu'] = lambda p, act, content, scene: (p, act, scene) == ('alpha', 'acta', 'first') and content.syntax == expected
    return model


def achieved_checks(setups):
    cases = []
    domain = tuple(dict.fromkeys((*DOMAIN, *blocked.DOMAIN)))
    scenes = tuple(dict.fromkeys((*SCENES, *blocked.SCENES)))
    for caused, unavailable in product((False, True), repeat=2):
        for setup in setups:
            doc, goal, effect, _ = setup
            trial = deepcopy(doc)
            trial['statements'] = [dict(kind='ask', body=dict(kind='evaluate', content=deepcopy(goal['body']),
                situation=dict(kind='call', symbol='je', arguments=[])))]
            model = source_model(setup)
            epistemic = blocked.source_model(doc, gain=not unavailable, decrease=not unavailable)
            person = lambda a: 'holder' if a == 'newgroup' else a
            stage = lambda s: 'before' if s == 'future' else s
            for name in ('jkassessment', 'jkscope', 'jktruth', 'jkcomparisons'):
                model[name] = epistemic[name]
            model['jkcorpus'] = lambda a, c, s: epistemic['jkcorpus'](person(a), c, stage(s))
            model['jksupported'] = lambda a, c, s: epistemic['jksupported'](person(a), c, stage(s))
            model['jlavailable'] = lambda a, p, s: a == 'newgroup' and s == 'future' and epistemic['jlavailable'](person(a), p, stage(s))
            model['jloutcomes'] = lambda a, p, s, e: a == 'newgroup' and s == 'future' and epistemic['jloutcomes'](person(a), p, stage(s), e)
            previous = model['dg']
            model['dg'] = lambda a, s: previous(a, s) or (a, s) == ('other', 'now')
            model['df'] = lambda p, a, s: p in ('alpha', 'beta') and (a, s) == ('other', 'now')
            expected = syntax(effect)
            model['jlcause'] = lambda a, content, s: caused and (a, s) == ('other', 'now') and content.syntax == expected
            if values(trial, model, domain, scenes) != [caused and unavailable]:
                raise ValueError('Causal goal confused current inability with later-cohort outcome')
        cases.append(dict(caused=caused, later_unavailable=unavailable, result=caused and unavailable))
    return cases


def source_checks(texts):
    setups = [source_setup(t) for t in texts]; cases = []
    for aimed, solemnity in product((False, True), repeat=2):
        want = [True, aimed and solemnity]
        rows = [values(s[0], source_model(s, aimed, solemnity), DOMAIN, SCENES) for s in setups]
        if rows != [want] * len(setups): raise ValueError('Successor identity inferred undertaking or purpose')
        cases.append(dict(aimed=aimed, solemnity=solemnity, results=want))
    contrasts = {}
    for variant in ('act_outside', 'party_outside', 'late_context', 'wrong_goal', 'same_members', 'disjoint_members'):
        want = [True, variant in ('same_members', 'disjoint_members')]
        rows = [values(s[0], source_model(s, variant=variant), DOMAIN, SCENES) for s in setups]
        if rows != [want] * len(setups): raise ValueError('Wrong-era undertaking contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = want
    for s in setups:
        doc = s[0]; model = source_model(s)
        for name in ('jlcause', 'jlavailable', 'jloutcomes', 'jkcorpus', 'jksupported', 'jktruth'):
            model[name] = guarded(doc)[name]
        if values(doc, model, DOMAIN, SCENES) != [True, True]: raise ValueError('Undertaking executed its unrealized later-cohort goal')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Cohort undertaking roundtrip changed')
    return dict(cases=cases, contrasts=contrasts, achieved_cases=achieved_checks(setups), specialization=[s[3] for s in setups],
        later_holder_and_period_fixed_in_goal=True, earlier_parties_are_causal_agents=True,
        unknown_achievement_not_evaluated=True, closed_roundtrips=True, standalone_agrees=True,
        collective_representation_not_proven=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored successive cohort differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Successive cohort roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    segments = []
    for phrase, symbols in (('Ein Zeitalter', ['rjg', 'rjh', 'hzde']), ('sich nicht verbünden und darauf verschwören', ['hzdf']), ('das folgende', ['rjf', 'rjh', 'hzde'])):
        if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source phrase')
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=symbols))
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_successive_cohorts.py', 'scripts/check_successive_cohorts.py', 'scripts/check_solemn_undertakings.py',
        'scripts/check_blocked_revision.py', 'scripts/check_assessed_payments.py', 'scripts/check_conditional_release.py',
        'scripts/check_described_appraisals.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'noema/specialization.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_successive_cohorts_and_undertaking', documents=documents, sizes=sizes,
        periods=period_checks([texts[0], texts[2]]), cohorts=cohort_checks([texts[0], texts[2]]), source=source_checks(texts[1:]),
        alignment=dict(segments=segments, semantic_completion=False), new_definitions=8, new_primitives=0, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Successive cohort report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Period-relative succession, cohort membership and earlier-era solemn undertaking checked')


if __name__ == '__main__': main()
