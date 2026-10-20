"""Check response-profile cessation, agentive change, and retained incapacity."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, canonical_digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_abandoned_reliance import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, LIMITS, parent, build, closure, extend
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_current_deprivation import capacity_values

INDEX = 'data/semantic-review-index-v106.json'
REPORT = 'reports/abandoned-reliance-v1.json'
AUDIT = 'data/abandoned-reliance-reading-v1.json'
DOC = 'docs/abandoned-reliance-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ['reports/depicted-referents-v1.json', 'reports/fetters-sentence-v1.json']
SENTENCES = [('data/nature-sentence-reading-v1.json', [51]), ('data/confirmed-incapacity-reading-v1.json', [11, 12]),
             ('data/fetters-sentence-reading-v1.json', [10, 52])]
PEOPLE = ('person', 'other', 'rule', 'form', 'reaction', 'judgment', 'process', 'author', 'third')
SCENES = ('scope', 'before', 'anchor', 'old1', 'old2', 'new1', 'new2')


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))
@lru_cache(None)
def document(): return parse((ROOT / FULL).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


def fixture(roots, extra):
    doc = deepcopy(document()); doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra)


def unknowns(doc): return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


def refuse(doc, values, names, people=PEOPLE, scenes=SCENES):
    for name in names:
        changed = dict(values); changed[name] = unknown
        try: evaluate(doc, changed, people, scenes, True)
        except ValueError as error: assert 'Unknown' in str(error), (name, str(error))
        else: raise AssertionError(name)


@lru_cache(None)
def profile_checks():
    doc = fixture(['r2gl'], '''r zc[d] c.r zh[d] c.r zo[d] c.r zp[d d] c.r zr[d] c.r zpoint[] d.
q[k r2gl[p zc p zh p zo p zp p zr e[k zpoint[]][k zpoint[]]]].
q[k r2gl[p zc p zh p zo p zp p zr u[e[k zpoint[]][k zpoint[]]]]].''')
    scenes = ('one', 'two')
    for bits in product((False, True), repeat=6):
        response, held, opportunities = bits[:2], bits[2:4], bits[4:]
        values = dict(zpoint=lambda: 'one', zc=lambda s: s in scenes, zp=lambda a, b: False,
            zh=lambda s: held[scenes.index(s)], zo=lambda s: opportunities[scenes.index(s)], zr=lambda s: response[scenes.index(s)])
        wanted = [all(held + opportunities) and all(response), all(held + opportunities) and not any(response)]
        assert evaluate(doc, values, ('person',), scenes, True) == wanted, bits
    values = dict(zpoint=lambda: 'one', zc=lambda s: s in scenes, zh=lambda s: True, zo=lambda s: True,
                  zp=lambda a, b: False, zr=lambda s: s == 'one')
    rows = {}
    for name, expected in [('mixed', [False, False]), ('first_preferred', [True, False]),
                           ('second_preferred', [False, True]), ('cycle', [False, False]),
                           ('empty', [False, False]), ('invalid_nonpreferred', [False, False])]:
        v = dict(values)
        if name in ('first_preferred', 'invalid_nonpreferred'): v['zp'] = lambda a, b: (a, b) == ('one', 'two')
        if name == 'second_preferred': v['zp'] = lambda a, b: (a, b) == ('two', 'one')
        if name == 'cycle': v['zp'] = lambda a, b: a != b
        if name == 'empty': v['zc'] = lambda s: False
        if name == 'invalid_nonpreferred': v['zh'] = lambda s: s == 'one'
        actual = evaluate(doc, v, ('person',), scenes, True); assert actual == expected, (name, actual); rows[name] = actual
    refuse(doc, values, ('zc', 'zh', 'zo', 'zp', 'zr'), ('person',), scenes)
    return dict(combinations=64, cases=rows, unknown_inputs_refused=5,
        negative_profile_not_negation_of_positive=True, all_candidates_validated_before_normality=True)


GENERIC_ARGS = 'p zhistory p zorder k zperson[] k zprocess[] k zstart[] k zend[] r[p zold] r[p znew] p zchanges p zaffected p zagent p zoccurs p ztransition p zproduces'


@lru_cache(None)
def transition_checks():
    doc = fixture(['r2gm'], '''r zperson[] a.r zprocess[] a.r zstart[] d.r zend[] d.
r zhistory[d] c.r zorder[d d] c.r zchanges[a d d] c.r zaffected[a a d d] c.r zagent[a a d] c.r zoccurs[a d] c.
r ztransition[a a i[h[a] e] i[h[a] e] d d] c.r zproduces[a a i[h[a] e] d] c.r zp[a d] c.r zq[a d] c.
d zold[person a] e[b point[k zp[v person v point]]].d znew[person a] e[b point[k zq[v person v point]]].
q[k r2gm[''' + GENERIC_ARGS + ']].')
    domain = ('person', 'process', 'other'); scenes = ('start', 'end', 'outside')
    def model(bits=(True, False, False, True) + (True,) * 6):
        oldstart, newstart, oldend, newend, changes, affected, agent, occurs, transition, produces = bits
        return dict(zperson=lambda: 'person', zprocess=lambda: 'process', zstart=lambda: 'start', zend=lambda: 'end',
            zhistory=lambda s: s in scenes[:2], zorder=lambda a, b: (a, b) == ('start', 'end'),
            zp=lambda p, s: p == 'person' and (oldstart if s == 'start' else oldend if s == 'end' else False),
            zq=lambda p, s: p == 'person' and (newstart if s == 'start' else newend if s == 'end' else False),
            zchanges=lambda p, a, b: changes and (p, a, b) == ('process', 'start', 'end'),
            zaffected=lambda p, r, a, b: affected and (p, r, a, b) == ('person', 'process', 'start', 'end'),
            zagent=lambda p, r, s: agent and (p, r, s) == ('person', 'process', 'end'),
            zoccurs=lambda r, s: occurs and (r, s) == ('process', 'end'),
            ztransition=lambda p, r, f, t, a, b: transition and (p, r, symbol(f), symbol(t), a, b) == ('person', 'process', 'zold', 'znew', 'start', 'end'),
            zproduces=lambda r, p, d, s: produces and (r, p, symbol(d), s) == ('process', 'person', 'znew', 'end'))
    for bits in product((False, True), repeat=10):
        wanted = bits[0] and not bits[1] and not bits[2] and bits[3] and all(bits[4:])
        assert evaluate(doc, model(bits), domain, scenes, True) == [wanted], bits
    rows = {}
    for name in ('baseline', 'missing_endpoint', 'reverse_order', 'other_agent', 'other_affected', 'other_cause', 'old_result', 'other_transition', 'reversed_descriptions'):
        v = model()
        if name == 'missing_endpoint': v['zhistory'] = lambda s: s == 'end'
        if name == 'reverse_order': v['zorder'] = lambda a, b: (a, b) == ('end', 'start')
        if name == 'other_agent': v['zagent'] = lambda p, r, s: (p, r, s) == ('other', 'process', 'end')
        if name == 'other_affected': v['zaffected'] = lambda p, r, a, b: p == 'other'
        if name == 'other_cause': v['zproduces'] = lambda r, p, d, s: r == 'other'
        if name == 'old_result': v['zproduces'] = lambda r, p, d, s: symbol(d) == 'zold'
        if name == 'other_transition': v['ztransition'] = lambda p, r, f, t, a, b: r == 'other'
        if name == 'reversed_descriptions': v['ztransition'] = lambda p, r, f, t, a, b: (symbol(f), symbol(t)) == ('znew', 'zold')
        actual = evaluate(doc, v, domain, scenes, True); assert actual == [name == 'baseline'], (name, actual); rows[name] = actual
    refuse(doc, model(), ('zhistory', 'zorder', 'zp', 'zq', 'zchanges', 'zaffected', 'zagent', 'zoccurs', 'ztransition', 'zproduces'), domain, scenes)
    return dict(combinations=1024, cases=rows, unknown_inputs_refused=10,
        same_descriptions_for_evaluation_transition_and_cause=True)


def source_values(doc, variant='baseline', before=(True, True), after=(False, False)):
    values = unknowns(doc)
    cases = {'before': ('old1', 'old2'), 'anchor': ('new1', 'new2')}
    response = dict(zip(cases['before'], before)) | dict(zip(cases['anchor'], after))
    values.update(wh=lambda: 'scope', h2d=lambda: 'third', wa=lambda: 'author', zperson=lambda: 'person',
        zprocess=lambda: 'process', zstart=lambda: 'before', zend=lambda: 'anchor',
        hzzzm=lambda n, a, d, p, o, s: variant != 'empty_targets' and (n, a, symbol(d), p, s) == ('third', 'author', 'r2fh', 'person', 'scope') and o in ('rule', 'form'),
        hzzzo=lambda sc, o, p, a, s: variant != 'empty_profile' and (sc, p) == ('scope', 'person') and o in ('rule', 'form') and s in cases.get(a, ()),
        hzzzp=lambda sc, o, p, a, s: (sc, p) == ('scope', 'person') and not (variant == 'changed_basis' and a == 'anchor' and s == 'new2'),
        hzzzq=lambda o, p, s: p == 'person' and not (variant == 'missing_opportunity' and s == 'new2'),
        hzzzr=lambda sc, o, p, a, f, l: variant == 'cyclic_normality' and a == 'anchor' and f != l,
        hx2=lambda p, o, act, s: (p, act) == ('person', 'reaction') and o in ('rule', 'form') and (
            response.get(s, False) or variant == 'examined_use_after' and s in cases['anchor'] or
            variant == 'one_target_retained' and o == 'form' and s in cases['anchor']),
        fa=lambda p, j, s: (p, j) == ('person', 'judgment') and variant == 'examined_use_after' and s in cases['anchor'],
        fb=lambda j, o, s: j == 'judgment' and o in ('rule', 'form'),
        hz2=lambda j, act, s: (j, act) == ('judgment', 'reaction'),
        dg=lambda act, s: act == 'reaction' and s in response or (variant != 'no_event' and (act, s) == ('process', 'anchor')),
        hzzzs=lambda p, end, t: (p, end) == ('person', 'anchor') and t in ('before', 'anchor') and not (variant == 'other_history' and t == 'before'),
        ic=lambda a, b, s: (a, b, s) == ('before', 'anchor', 'anchor'),
        ag=lambda proc, a, b: (proc, a, b) == ('process', 'before', 'anchor'),
        la=lambda p, proc, a, b: (p, proc, a, b) == ('person', 'process', 'before', 'anchor'),
        df=lambda p, proc, s: (p, proc, s) == ('other' if variant == 'other_agent' else 'person', 'process', 'anchor'),
        hzid=lambda p, proc, old, new, a, b: variant != 'no_transition' and (p, proc, symbol(old), symbol(new), a, b) == ('person', 'process', 'r2gp', 'r2gq', 'before', 'anchor'),
        g3=lambda proc, p, d, s: variant != 'no_cause' and (proc, p, symbol(d), s) == ('process', 'person', 'r2gp' if variant == 'old_causal_result' else 'r2gq', 'anchor'))
    return values


@lru_cache(None)
def source_fixture():
    return fixture(['r2gm', 'r2gt', 'r2gn', 'wh'], '''r zperson[] a.r zprocess[] a.r zstart[] d.r zend[] d.r zobject[] a.
q[t[k r2gp[k zperson[]]][k zstart[]]].q[t[k r2gq[k zperson[]]][k zstart[]]].
q[t[k r2gp[k zperson[]]][k zend[]]].q[t[k r2gq[k zperson[]]][k zend[]]].
q[k r2gs[k zperson[] k zprocess[] k zstart[] k zend[]]].q[t[k r2gt[k zperson[]]][k zend[]]].
q[k r2gm[i[point d][k hzzzs[k zperson[] k zend[] v point]] i[first d last d][k ic[v first v last k zend[]]]
 k zperson[] k zprocess[] k zstart[] k zend[] r[p r2gp] r[p r2gq] p ag p la p df p dg p hzid p g3]].
q[k r2gn[k zobject[] k zperson[] k zstart[]]].''')


@lru_cache(None)
def source_checks():
    doc = source_fixture()
    for bits in product((False, True), repeat=4):
        v = source_values(doc, before=bits[:2], after=bits[2:]); v['zobject'] = lambda: 'rule'
        positive_before, negative_before, positive_after, negative_after = all(bits[:2]), not any(bits[:2]), all(bits[2:]), not any(bits[2:])
        change = positive_before and negative_after
        wanted = [positive_before, negative_before, positive_after, negative_after, change, change, change, False]
        assert evaluate(doc, v, PEOPLE, SCENES, True) == wanted, bits
    rows = {}
    for name in ('baseline', 'examined_use_after', 'one_target_retained', 'empty_targets', 'empty_profile', 'changed_basis',
                 'missing_opportunity', 'cyclic_normality', 'no_event', 'other_history', 'other_agent', 'no_transition', 'no_cause', 'old_causal_result'):
        v = source_values(doc, name); v['zobject'] = lambda: 'rule'
        actual = evaluate(doc, v, PEOPLE, SCENES, True)
        assert actual[4:7] == [name in ('baseline', 'examined_use_after')] * 3, (name, actual)
        assert actual[-1] is False
        rows[name] = actual
    v = source_values(doc); v['zobject'] = lambda: 'rule'
    refuse(doc, v, ('hzzzm', 'hzzzo', 'hzzzp', 'hzzzq', 'hzzzr', 'hx2', 'fa', 'dg', 'hzzzs', 'hzid', 'g3'))
    return dict(combinations=16, cases=rows, unknown_inputs_refused=11,
        specialized_matches_general=True, current_quiet_point_does_not_remove_disposition=True,
        examined_use_after_abandonment_allowed=True, all_fixed_targets_required=True)


@lru_cache(None)
def capacity_checks():
    # Supply the same concrete witness used by source_checks. The existential
    # r2gt wrapper is executed there; here both native predicates share a world.
    doc = fixture(['r2gs', 'r2cf'], '''r zperson[] a.r zprocess[] a.r zstart[] d.r zend[] d.
q[k r2gs[k zperson[] k zprocess[] k zstart[] k zend[]]].q[t[k r2cf[k zperson[]]][k zend[]]].''')
    domain = tuple(dict.fromkeys(PEOPLE + ('method', 'faculty', 'act')))
    scenes = tuple(dict.fromkeys(SCENES + ('first', 'second', 'success', 'failure')))
    rows = []
    for stops, capable in product((False, True), repeat=2):
        values = capacity_values(doc, passes=(capable, capable), now=False)
        supplied = source_values(doc, after=(not stops, not stops))
        values.update({n: value for n, value in supplied.items() if value is not unknown})
        actual = evaluate(doc, values, domain, scenes, True)
        assert actual == [stops, not capable], (stops, capable, actual)
        rows.append(dict(abandonment=stops, capable=capable, values=actual))
    return dict(cases=rows, native_current_capacity_executed=True, same_world_with_explicit_transition_witness=True,
        existential_wrapper_checked_separately=True, abandonment_does_not_imply_capacity=True)


@lru_cache(None)
def quotation_checks():
    doc = fixture(['r2gt'], 'q[e[r[p r2gt]][r[p r2gt]]].')
    assert evaluate(doc, unknowns(doc), PEOPLE, SCENES, True) == [True]
    try: fixture(['r2gm'], 'q[e[r[p r2gm]][r[p r2gm]]].')
    except ValueError as error: assert 'quot' in str(error).lower(), str(error)
    else: raise AssertionError('Unspecialized dynamic disquotation was quoted')
    _, trace = extend(parent().document)
    assert trace.disquotations_removed == 4 and trace.bound_positions == [6, 7]
    return dict(closed_antecedent_quotable_without_world_evaluation=True,
        unspecialized_dynamic_definition_refused=True, removed_disquotations=4)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    start = unit['text'].index('abwürfe', 474); end = start + len('abwürfe')
    current = catalog(); dependencies = [d['name'] for d in closure(current.document, ['r2gt'])]
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, *PRIOR, *(p for p, _ in SENTENCES)}
    return dict(status='unasserted_abandonment_antecedent_candidate', reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, end], text=unit['text'][start:end]),
        candidate_definitions=list(MEANINGS), candidate_dependency_sha256=canonical_digest([current.entries[n] for n in dependencies]),
        candidate_dependencies=dependencies, preserved_authored_selection=selection_binding(current, [13, 53]),
        decision='吟味のない使用傾向を自らやめる前件候補を構成する。静かな一時点の不使用や能力の獲得とは分ける。第四文の著者帰属への採用と後件接続は未完。',
        interpretation_limits=LIMITS, revised_statement_indices=[],
        references=[dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036', accessed='2026-10-20',
            use='足枷を捨てる仮定と、なお不確かな跳躍しかできないという後続を照合。傾向の交替は対象側の読解候補であり、唯一の語義とはしない。')],
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=408,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-14] == old.document['declarations']
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert len(new.document['statements']) == 54 and old.document['statements'] == new.document['statements']
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        record = read(path); validate_hashes(ROOT, record['source_sha256'])
        indices = [s['index'] for s in record['selection']['statements']]
        assert record['selection'] == selection_binding(old, indices) == selection_binding(new, indices)
    for path, indices in SENTENCES:
        record = read(path); validate_hashes(ROOT, record['source_sha256'])
        assert record['selection'] == selection_binding(new, indices)
    for path in PRIOR: validate_hashes(ROOT, read(path)['source_sha256'])
    assert not set(MEANINGS) & set(selection_binding(new, list(range(54)))['dependencies'])
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE, LIBRARY):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(doc, style); assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    assert read(AUDIT) == reading()
    return dict(added_definitions=9, added_primitives=5, authored_statements=54, preserved_statements=54,
        revised_statement_indices=[], preserved_review_selections=12, reviewed_nonblank_characters=2212,
        preserved_reviewed_sentence_characters=408, candidate_not_asserted=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items(): write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('profile', profile_checks), ('transition', transition_checks), ('source', source_checks),
                     ('capacity', capacity_checks), ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    record = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(record['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_abandoned_reliance.py', 'scripts/check_abandoned_reliance.py',
        'scripts/register_abandoned_reliance.py', 'tests/test_abandoned_reliance.py',
        'noema/constructed_specialization.py', 'scripts/check_current_deprivation.py',
        'scripts/check_exercise_capacity.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    for path in PRIOR: paths.update(read(path)['source_sha256'])
    paths.update(read(INDEX)['works']['kant-1784']['reviews'])
    return dict(status='agentive_abandonment_antecedent_checked', document=FULL, **results,
        alignment=dict(**record['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_covered_characters=0, new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=408,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
