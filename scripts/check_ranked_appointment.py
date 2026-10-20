"""Check same-witness history, ranked target identity and independent demands."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_ranked_appointment import (
    ROOT, LIBRARY, BASIS, CODE, NAMES, BIND_NAMES, PRIMITIVES, MEANINGS, parents, build, closure)
from scripts.compose_qualitative_influence import TRUE, FALSE
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

REPORT = 'reports/ranked-appointment-v1.json'
DOC = 'docs/ranked-appointment-v1.md'
PRIOR = 'reports/confessional-teaching-v1.json'
DOMAIN = (*BIND_NAMES, 'event', 'other')
SCENES = ('past', 'middle', 'now', 'future', 'reference')
EXTRA = ''.join('r z' + n + '[] a.' for n in DOMAIN)
EXTRA += 'r zpast[] d.r zpoint[] d.r zref[] d.'
EXTRA += 'd zalias[bindings j[a] reference d] e[k r35w[v bindings v reference]].'
TARGET = 'r b[p r35w]'
BINDINGS = 'l[a][' + ' '.join('k z' + n + '[]' for n in BIND_NAMES) + ']'
OPEN = 'k zchurch[] k zperson[] k zrole[] ' + TARGET + ' ' + BINDINGS + ' k zref[] {sign} k zpoint[]'


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind='generic', positive=True, bindings=()):
    doc = deepcopy(catalog().document); doc['statements'] = []
    if kind == 'binding':
        doc['declarations'] = closure(doc, ['r35w'])
        d = next(d for d in doc['declarations'] if d['name'] == 'r35v')
        doc['declarations'] = [dict(kind='primitive', name=d['name'], parameters=[p['sort'] for p in d['parameters']], result=d['result'])
            if x['name'] == 'r35v' else x for x in doc['declarations']]
        seq = 'l[a][' + ' '.join('k z' + n + '[]' for n in bindings) + ']'
        queries = 'q[t[k r35w[' + seq + ' k zref[]]][k zpoint[]]].'
    elif kind == 'generic':
        fields = OPEN.format(sign=TRUE if positive else FALSE)
        queries = 'q[k r35x[k zevent[] k zpast[] ' + fields + ']].'
        queries += ''.join('q[k ' + n + '[' + fields + ']].' for n in ('r35y', 'r35z', 'h237z'))
    else:
        fields = ' '.join('k z' + n + '[]' for n in NAMES) + ' k zref[] k zactivity[]'
        queries = ''.join('q[t[k ' + n + '[' + fields + ']][k zpoint[]]].' for n in ('r352', 'r353', 'r354'))
    return parse(format_graph(doc, 'compact') + EXTRA + queries)


def base(doc):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    for n in DOMAIN: v['z' + n] = lambda n=n: n
    v.update(zpast=lambda: 'past', zpoint=lambda: 'now', zref=lambda: 'reference')
    return v


def model(doc, variant='baseline', bits=(True, True, True, True, True), positive=True):
    occurred, entrusted, appointed, terms, required = bits
    v = base(doc)
    when = 'now' if variant == 'present_only' else 'future' if variant == 'future_only' else 'past'
    def matches(actual, expected, prefix, fields):
        return actual == tuple('other' if variant == prefix + '_' + f else x for f, x in zip(fields, expected))
    def history(person, anchor, at):
        return matches((person, anchor), ('person', 'now'), 'history', ('person', 'anchor')) and at in (
            ('now',) if variant == 'foreign_history' else ('past', 'middle', 'now', 'future'))
    def order(first, last, anchor):
        times = ('past', 'middle', 'now', 'future')
        if anchor != 'now': return False
        if variant == 'cyclic' and (first, last) == ('now', 'past'): return True
        if variant == 'reflexive' and first == last == 'past': return True
        if variant == 'incomparable' and {first, last} == {'middle', 'now'}: return False
        if variant == 'nontransitive' and (first, last) == ('past', 'now'): return False
        return first in times and last in times and times.index(first) < times.index(last)
    def appointment(event, issuer, person, role, at):
        events = ('event', 'other') if variant == 'two_appointments' else ('event',)
        return appointed and any(matches((event, issuer, person, role, at), (e, 'church', 'person', 'role', when),
            'appointment', ('event', 'issuer', 'person', 'role', 'point')) for e in events)
    def correct_target(code, bindings, ref, sign, prefix):
        target = 'zalias' if variant == prefix + '_description' else 'r35w'
        items = tuple('other' if variant == prefix + '_binding_' + n else n for n in BIND_NAMES)
        if variant == prefix + '_short': items = items[:-1]
        if variant == prefix + '_long': items += ('other',)
        if variant == prefix + '_reordered': items = items[1:] + items[:1]
        return (symbol(code), code.rank, tuple(bindings.items), ref, sign) == (
            target, 1, items, 'past' if variant == prefix + '_reference' else 'reference',
            not positive if variant == prefix + '_sign' else positive)
    def condition(event, code, bindings, ref, sign, at):
        events = ('event', 'other') if variant == 'two_appointments' else ('other',) if variant == 'split_event' else ('event',)
        time = 'middle' if variant == 'split_time' else when
        return terms and event in events and at == time and correct_target(code, bindings, ref, sign, 'terms')
    def norm(issuer, person, role, code, bindings, ref, sign, at):
        return required and matches((issuer, person, role, at), ('church', 'person', 'role', 'now'),
            'norm', ('issuer', 'person', 'role', 'point')) and correct_target(code, bindings, ref, sign, 'norm')
    v.update(ia=history, ic=order, h223k=appointment, h246m=condition, h237z=norm,
        dg=lambda event, at: occurred and event in ('event', 'other') and at in (when, 'middle'),
        cf=lambda person, role, at: entrusted and (person, role) == ('person', 'role') and at in (when, 'middle'))
    return v


@lru_cache(None)
def independent_checks():
    doc, cases = fixture(), []
    for bits in product((False, True), repeat=5):
        past, norm = all(bits[:4]), bits[4]
        expected = [past, past, past and norm, norm]
        actual = evaluate(doc, model(doc, bits=bits), DOMAIN, SCENES, True)
        assert actual == expected, (bits, actual); cases.append(dict(inputs=bits, results=actual))
    return dict(cases=cases, present_duty_not_inferred_from_past_appointment=True,
        appointment_not_inferred_from_duty=True, teaching_and_creed_truth_not_executed=True)


@lru_cache(None)
def witness_checks():
    doc, rows = fixture(), {}
    variants = ('baseline', 'appointment_event', 'appointment_issuer', 'appointment_person', 'appointment_role',
        'appointment_point', 'history_person', 'history_anchor', 'foreign_history', 'split_event', 'split_time',
        'present_only', 'future_only', 'cyclic', 'reflexive', 'incomparable', 'nontransitive', 'two_appointments')
    for variant in variants:
        expected = [True] * 4 if variant in ('baseline', 'two_appointments') else [False, False, False, True]
        actual = evaluate(doc, model(doc, variant), DOMAIN, SCENES, True)
        assert actual == expected, (variant, actual); rows[variant] = actual
    v = model(doc); v['zevent'] = lambda: 'other'
    assert evaluate(doc, v, DOMAIN, SCENES, True) == [False, True, True, True]
    return dict(contrasts=rows, same_event_and_past_point=True, named_witness_distinct_from_existential=True,
        original_ta_ia_ic_h223k_dg_cf_evaluated=True)


@lru_cache(None)
def identity_checks():
    doc, rows = fixture(), {}
    fields = ('description', 'reference', 'sign', 'short', 'long', 'reordered', *('binding_' + n for n in BIND_NAMES))
    for prefix in ('terms', 'norm'):
        for field in fields + (('issuer', 'person', 'role', 'point') if prefix == 'norm' else ()):
            variant = prefix + '_' + field
            actual = evaluate(doc, model(doc, variant), DOMAIN, SCENES, True)
            expected = [False, False, False, True] if prefix == 'terms' else [True, True, False, False]
            assert actual == expected, (variant, actual); rows[variant] = actual
    negative = fixture(positive=False)
    assert evaluate(negative, model(negative, positive=False), DOMAIN, SCENES, True) == [True] * 4
    return dict(contrasts=rows, negative_terms_and_demand_supported=True, extensionally_equal_alias_not_substituted=True,
        target_reference_distinct_from_past_appointment_and_current_duty_points=True)


@lru_cache(None)
def concrete_checks():
    doc, rows = fixture('concrete'), {}
    for variant, bits in [('baseline', (True,) * 5), ('absent_duty', (True, True, True, True, False)),
        ('absent_appointment', (True, True, False, True, True)), ('terms_binding_church', (True,) * 5),
        ('norm_binding_standard', (True,) * 5), ('terms_reference', (True,) * 5), ('norm_sign', (True,) * 5)]:
        v = model(doc, variant, bits)
        assert all(v[n] is unknown for n in ('h246e', 'h246j', 'h246l', 'f2', 'h246g'))
        expected = [True] * 3 if variant == 'baseline' else [False, True, False] if variant.startswith('norm_') or variant == 'absent_duty' else [True, False, False]
        actual = evaluate(doc, v, DOMAIN, SCENES, True)
        assert actual == expected, (variant, actual); rows[variant] = actual
    return dict(contrasts=rows, native_teaching_target_in_both_records=True,
        no_teaching_execution_or_belief_truth_from_appointment_or_demand=True)


@lru_cache(None)
def binding_checks():
    for position in range(len(BIND_NAMES)):
        names = tuple('person' if i == position else 'other' for i in range(len(BIND_NAMES)))
        expected = tuple('x' if i == position else 'y' for i in range(len(BIND_NAMES)))
        doc = fixture('binding', bindings=names); v = base(doc)
        v.update(zperson=lambda: 'x', zother=lambda: 'y')
        # r35v puts the reference before the final activity argument.
        args = (*expected[:-1], 'reference', expected[-1])
        v['r35v'] = lambda *given: Content(SCENES, tuple(given == args for _ in SCENES))
        assert evaluate(doc, v, ('x', 'y'), SCENES, True) == [True], position
    for length in (0, 9, 11):
        doc = fixture('binding', bindings=('person',) * length); v = base(doc)
        v['zperson'] = lambda: 'x'; v['r35v'] = lambda *args: Content(SCENES, (True,) * len(SCENES))
        assert evaluate(doc, v, ('x', 'y'), SCENES, True) == [False], length
    return dict(independently_checked_positions=len(BIND_NAMES), wrong_lengths_refused=[0, 9, 11],
        boundaries=['r35v is a typed boundary here; confessional-teaching evaluates the native individual-message teaching definition.'])


@lru_cache(None)
def unknown_rank_checks():
    doc = fixture(); rows = []
    for name in ('ia', 'ic', 'dg', 'cf', 'h223k', 'h246m', 'h237z'):
        v = model(doc); v[name] = unknown
        try: evaluate(doc, v, DOMAIN, SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error), str(error)
        else: raise AssertionError(name)
        rows.append(name)
    doc = deepcopy(catalog().document); doc['statements'] = []
    quoted = parse(format_graph(doc, 'compact') + 'q[e[r b[p r35w]][r b[p r35w]]].')
    assert evaluate(quoted, base(quoted), DOMAIN, SCENES, True) == [True]
    try: parse(format_graph(doc, 'compact') + 'q[e[r[p r35w]][r[p r35w]]].')
    except ValueError as error: rank_error = str(error)
    else: raise AssertionError('Insufficient quote rank accepted')
    return dict(unknown_relations_refused=rows, ranked_target_quoted_without_execution=True, insufficient_rank_rejected=rank_error)


@lru_cache(None)
def structure_checks():
    new = catalog(); old = {n: e for p in parents() for n, e in p.entries.items()}
    assert not new.document['statements']
    for n, e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration'] == old[n]['declaration'] and e['meaning_ja'] == old[n]['meaning_ja'], n
    validate_hashes(ROOT, read(PRIOR)['source_sha256'])
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation); assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(new_primitives=len(PRIMITIVES), new_definitions=len(MEANINGS), inherited_meanings_preserved=True,
        roundtrips=True, new_semantic_reviews=0, active_manuscript_unchanged=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)


def build_report():
    results = {}
    for name, fn in [('independence', independent_checks), ('witness', witness_checks), ('identity', identity_checks),
        ('concrete', concrete_checks), ('binding', binding_checks), ('unknown_rank', unknown_rank_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set().union(*(set(p.source_sha256) for p in parents())) | {DOC, PRIOR,
        'scripts/compose_ranked_appointment.py', 'scripts/check_ranked_appointment.py', 'tests/test_ranked_appointment.py',
        'scripts/compose_confessional_teaching.py', 'scripts/compose_protected_remarks.py', 'scripts/compose_appointment_terms.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='ranked_same_appointment_terms_and_independent_duty', document=LIBRARY, **results,
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
