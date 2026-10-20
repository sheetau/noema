"""Check first-person binding without executing ascribed membership claims."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import FunctionValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_scholarly_self_ascription import (
    ROOT, LIBRARY, BASIS, MEANINGS, PRIMITIVES, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

REPORT = 'reports/scholarly-self-ascription-v1.json'
DOC = 'docs/scholarly-self-ascription-v1.md'
PRIOR = ('reports/office-obedience-v1.json', 'reports/use-definitions-v1.json')
DOMAIN = ('person', 'otherperson', 'community', 'world', 'judgment', 'otherjudgment',
          'office', 'work', 'mechanism', 'activity', 'scholar', 'writing', 'audience',
          'record', 'carrier', 'other')
SCENES = ('reference', 'other')
EXTRA = ''.join('r z' + n + '[] a.' for n in (
    'person', 'community', 'world', 'office', 'work', 'activity', 'scholar', 'writing', 'audience', 'other')) + 'r zref[] d.'
CONTEXT_ARGS = ' '.join('k z' + n + '[]' for n in (
    'person', 'office', 'work', 'community', 'world', 'activity', 'scholar', 'writing', 'audience')) + ' k zref[]'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind, sequence=('person', 'community', 'world')):
    doc = deepcopy(catalog().document)
    roots = {'membership': ['r3p', 'r3q'], 'self': ['r3r'], 'writing': ['r3s'], 'context': ['r3t']}[kind]
    doc.update(declarations=closure(doc, roots), statements=[])
    if kind == 'membership':
        seq = 'l[a][' + ' '.join('k z' + n + '[]' for n in sequence) + ']'
        query = ''.join('q[t[k ' + n + '[' + seq + ']][k zref[]]].' for n in roots)
    elif kind == 'self':
        query = 'q[k r3r[k zperson[] k zcommunity[] k zworld[] k zref[]]].'
    elif kind == 'writing':
        query = 'q[k r3s[k zperson[] k zactivity[] k zscholar[] k zwriting[] k zaudience[] k zref[]]].'
    else:
        query = 'q[k r3t[' + CONTEXT_ARGS + ']].'
    return parse(format_graph(doc, 'compact') + EXTRA + query)


def base(doc):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    for name in ('person', 'community', 'world', 'office', 'work', 'activity', 'scholar', 'writing', 'audience', 'other'):
        v['z' + name] = lambda name=name: name
    v['zref'] = lambda: 'reference'
    return v


@lru_cache(None)
def membership_checks():
    doc, rows = fixture('membership'), []
    for civic, worldwide, member in product((False, True), repeat=3):
        v = base(doc)
        v.update(h237c=lambda p, c, r: civic and (p, c, r) == ('person', 'community', 'reference'),
                 h242e=lambda w, r: worldwide and (w, r) == ('world', 'reference'),
                 h242f=lambda p, w, r: member and (p, w, r) == ('person', 'world', 'reference'))
        actual = evaluate(doc, v, DOMAIN[:6] + ('other',), SCENES, True)
        assert actual == [civic, worldwide and member], (civic, worldwide, member, actual)
        rows.append(dict(flags=[civic, worldwide, member], values=actual))
    adapters = {}
    for seq in ((), ('person',), ('person', 'community'), ('person', 'community', 'world'),
                ('person', 'world', 'community'), ('person', 'community', 'world', 'other')):
        doc = fixture('membership', seq); v = base(doc)
        v.update(h237c=lambda p, c, r: (p, c, r) == ('person', 'community', 'reference'),
                 h242e=lambda w, r: (w, r) == ('world', 'reference'),
                 h242f=lambda p, w, r: (p, w, r) == ('person', 'world', 'reference'))
        actual = evaluate(doc, v, DOMAIN[:6] + ('other',), SCENES, True)
        assert actual == [seq == ('person', 'community', 'world')] * 2
        adapters[','.join(seq)] = actual
    return dict(combinations=rows, exact_bindings=adapters, membership_kinds_not_conflated=True)


def self_model(doc, flags=(True, True, True, True), variant='baseline'):
    actor, first_person, political, cosmopolitan = flags
    v = base(doc)
    v.update(fa=lambda p, j, r: actor and (p, j, r) == (
        'otherperson' if variant == 'other_judge' else 'person', 'judgment', 'reference'),
        h242h=lambda j, p, r: first_person and (j, p, r) == (
            'judgment', 'otherperson' if variant == 'third_person_identification' else 'person', 'reference'))
    def ascribes(j, code, bindings, sign, ref):
        which = symbol(code)
        wanted = ('otherperson' if variant == 'other_ascribed_person' else 'person',
                  'other' if variant == 'other_ascribed_community' else 'community',
                  'other' if variant == 'other_ascribed_world' else 'world')
        expected_judgment = 'otherjudgment' if variant == 'split_judgments' and which == 'r3q' else 'judgment'
        return (political if which == 'r3p' else cosmopolitan if which == 'r3q' else False) and (
            j, tuple(bindings.items), sign, ref) == (expected_judgment, wanted,
            False if variant == 'negative_ascription' else True,
            'other' if variant == 'other_ascription_reference' else 'reference')
    v['h242d'] = ascribes
    return v


@lru_cache(None)
def self_checks():
    doc, rows = fixture('self'), []
    for flags in product((False, True), repeat=4):
        actual = evaluate(doc, self_model(doc, flags), DOMAIN, SCENES, True)
        assert actual == [all(flags)], (flags, actual)
        rows.append(dict(flags=list(flags), value=actual[0]))
    contrasts = {}
    for variant in ('other_judge', 'third_person_identification', 'other_ascribed_person',
                    'other_ascribed_community', 'other_ascribed_world', 'split_judgments',
                    'negative_ascription', 'other_ascription_reference'):
        actual = evaluate(doc, self_model(doc, variant=variant), DOMAIN, SCENES, True)
        assert actual == [False], (variant, actual)
        contrasts[variant] = actual[0]
    for name in ('fa', 'h242h', 'h242d'):
        v = self_model(doc); v[name] = unknown
        try:
            evaluate(doc, v, DOMAIN, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    v = self_model(doc)
    assert all(v[n] is unknown for n in ('h237c', 'h242e', 'h242f'))
    assert evaluate(doc, v, DOMAIN, SCENES, True) == [True]
    return dict(combinations=rows, contrasts=contrasts, unknown_inputs_refused=3,
                ascribed_memberships_not_executed=True, first_person_mode_required=True)


def writing_model(doc, variant='baseline'):
    v = base(doc)
    v.update(aa=lambda p: p == 'person' and variant != 'not_human',
        ca=lambda p, act, r: variant != 'not_own_reason' and (p, act, r) == ('person', 'activity', 'reference'),
        cb=lambda p, act, role, r: (p, act, role, r) == ('person', 'activity',
            'office' if variant == 'office_role_only' else 'scholar', 'reference'),
        cd=lambda role, r: (role, r) == ('scholar', 'reference'),
        cc=lambda act, aud, r: (act, aud, r) == ('activity',
            'other' if variant == 'other_addressed_audience' else 'audience', 'reference'),
        ce=lambda aud, r: variant != 'local_audience_only' and (aud, r) == ('audience', 'reference'),
        sc=lambda writing, r: variant != 'not_written_work' and (writing, r) == ('writing', 'reference'),
        hzwr=lambda record, writing, r: (record, writing, r) == ('record', 'writing', 'reference'),
        hzws=lambda record, carrier, r: (record, carrier, r) == (
            'other' if variant == 'split_record' else 'record', 'carrier', 'reference'),
        hzwt=lambda record, r: variant != 'unreadable_record' and (record, r) == ('record', 'reference'),
        h242g=lambda act, writing, aud, r: (act, writing, aud, r) == (
            'other' if variant == 'other_transmission_activity' else 'activity',
            'other' if variant == 'other_transmitted_work' else 'writing',
            'other' if variant == 'other_transmission_audience' else 'audience',
            'other' if variant == 'other_transmission_reference' else 'reference'))
    return v


@lru_cache(None)
def writing_checks():
    doc, rows = fixture('writing'), {}
    for variant in ('baseline', 'not_human', 'not_own_reason', 'office_role_only',
                    'other_addressed_audience', 'local_audience_only', 'not_written_work',
                    'split_record', 'unreadable_record', 'other_transmission_activity',
                    'other_transmitted_work', 'other_transmission_audience', 'other_transmission_reference'):
        actual = evaluate(doc, writing_model(doc, variant), DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual[0]
    for name in ('hzwr', 'hzws', 'hzwt', 'h242g'):
        v = writing_model(doc); v[name] = unknown
        try:
            evaluate(doc, v, DOMAIN, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, native_public_use_and_record_chain=True, unknown_inputs_refused=4,
                sending_receiving_understanding_not_required=True)


@lru_cache(None)
def context_checks():
    doc, rows = fixture('context'), {}
    for variant in ('baseline', 'other_appointed_person', 'other_appointed_office', 'other_job',
                    'other_community', 'missing_self_mode', 'other_writer'):
        v = writing_model(doc)
        sv = self_model(doc, variant='third_person_identification' if variant == 'missing_self_mode' else 'baseline')
        for n in ('fa', 'h242h', 'h242d'):
            v[n] = sv[n]
        v.update(h237y=lambda work, r: (work, r) == ('work', 'reference'),
            h237h=lambda work, r: 'mechanism', h237i=lambda work, r: 'other' if variant == 'other_community' else 'community',
            h237d=lambda m, w, r: FunctionValue(('individual',), 'truth', lambda p: p == 'person'),
            h237c=lambda p, c, r: (p, c, r) == ('person', 'community', 'reference'),
            h237e=lambda p, m, w, r: 'office',
            h237f=lambda p, role, m, w, r: (p, role, m, w, r) == (
                'otherperson' if variant == 'other_appointed_person' else 'person',
                'other' if variant == 'other_appointed_office' else 'office', 'mechanism',
                'other' if variant == 'other_job' else 'work', 'reference'))
        if variant == 'other_writer':
            v['ca'] = lambda p, act, r: (p, act, r) == ('otherperson', 'activity', 'reference')
        actual = evaluate(doc, v, DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual[0]
    return dict(contrasts=rows, native_office_scope_reused=True,
                same_person_different_role_arguments=True, cosmopolitan_membership_not_executed=True)


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert not new.document['statements']
    for n, entry in new.entries.items():
        if n not in MEANINGS and n not in PRIMITIVES:
            assert entry['declaration'] == old.entries[n]['declaration']
            assert entry['meaning_ja'] == old.entries[n]['meaning_ja']
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(new_definitions=5, new_primitives=5, unchanged_active_manuscript=True,
                new_semantic_reviews=0, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)


def build_report():
    results = {}
    for name, fn in [('membership', membership_checks), ('self_ascription', self_checks),
                     ('written_address', writing_checks), ('context', context_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(parent().source_sha256) | {
        DOC, *PRIOR, 'scripts/compose_scholarly_self_ascription.py',
        'scripts/check_scholarly_self_ascription.py', 'tests/test_scholarly_self_ascription.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='scholarly_self_ascription_and_written_address_dependency_group',
                document=LIBRARY, **results, whole_sentence_semantically_verified=False,
                whole_unit_semantically_verified=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
