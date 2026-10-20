"""Check three positive contents, same-person conjunction and nonfactive quotation."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_command_alternatives import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v148.json'
REPORT = 'reports/command-alternatives-v1.json'
AUDIT = 'data/command-alternatives-reading-v1.json'
DOC = 'docs/command-alternatives-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = 'reports/heard-prohibition-v1.json'
SENTENCES = 'data/heard-prohibition-reading-v1.json'
PEOPLE = ('first', 'second', 'act', 'pattern', 'receiver', 'medium', 'one', 'two')
SCENES = ('reference', 'later')
EXTRA = '''r zp[] a.r zs[] a.r zr[] d.r zt[] d.
r zpick[a d i[e] i[e]] i[e].r ztruth[d] c.
d zfirst[] e[b point[k ztruth[v point]]].
d zsecond[] e[b point[u[k ztruth[v point]]]].
'''
COMMANDS = ('r2tk', 'r2tl', 'r2tm')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    extras = parse('p:' + EXTRA)['declarations']
    replacement = parse('p:' + EXTRA + '''d h233b[item a reference d] i[e][
 k zpick[v item v reference r[k zfirst[]] r[k zsecond[]]]].''')['declarations'][-1]
    doc['declarations'] = extras + [replacement if d['name'] == 'h233b' else d for d in doc['declarations']]
    roots = {'drill': ['r2tg'], 'payment': ['r2th'], 'belief': ['r2ti'],
             'combined': list(COMMANDS), 'quoted': [*COMMANDS, 'f2']}[kind]
    doc.update(declarations=closure(doc, [*roots, *[d['name'] for d in extras]]), statements=[])
    if kind in ('drill', 'payment', 'belief'):
        query = 'q[t[c[k ' + roots[0] + '[k zr[]]][k zp[]]][k zt[]]].'
    elif kind == 'combined':
        query = ''.join('q[t[o[c[k ' + n + '[k zr[]]][k zp[]]]][k zt[]]].' for n in COMMANDS)
        query += ''.join('q[u[e[c[k ' + n + '[k zr[]]][k zp[]]][j s[o[c[k ' + n +
                         '[k zr[]]][k zp[]]]]]]].' for n in COMMANDS)
    else:
        query = ''.join('q[k f2[k zs[] k zp[] k zp[] o a[r[p ' + n +
                         ']][r[k zr[]]] k zt[]]].' for n in COMMANDS)
    return parse(format_graph(doc, 'compact') + query)


def model(doc, variant='baseline', flags=(False, True, True, True)):
    reasons, drill, payment, belief = flags
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(
        zp=lambda: 'first', zs=lambda: 'second', zr=lambda: 'reference', zt=lambda: 'later',
        ca=lambda p, a, r: (p, a, r) == ('first', 'act', 'reference'),
        h232p=lambda a, r: (a, r) == ('act', 'reference'),
        cg=lambda p, a, t: reasons and (p, a, t) == ('first', 'act', 'later'),
        dg=lambda a, t: drill and (a, t) == ('act', 'later') and variant != 'practice_not_occurring',
        df=lambda p, a, t: (p, a, t) == (
            'second' if variant == 'other_person_practices' else 'first', 'act', 'later'),
        h232x=lambda a, pattern, t: (a, pattern, t) == ('act',
            'one' if variant == 'different_pattern' else 'pattern', 'later') and variant != 'not_practice',
        h232y=lambda pattern, r: (pattern, r) == ('pattern',
            'later' if variant == 'pattern_at_wrong_reference' else 'reference') and variant != 'nonmilitary_pattern',
        h232z=lambda r, p, a: (r, p, a) == ('reference', 'first',
            'one' if variant == 'unrelated_payment' else 'act'),
        ti=lambda a, p, receiver, medium, t: payment and (a, p, receiver, medium, t) == (
            'act', 'second' if variant == 'other_payer' else 'first',
            'first' if variant == 'self_transfer' else 'receiver', 'medium',
            'reference' if variant == 'transfer_at_wrong_point' else 'later'),
        tj=lambda medium, t: (medium, t) == (
            'one' if variant == 'different_medium_accepted' else 'medium', 'later') and variant != 'unaccepted_medium',
        h233a=lambda r, teaching: r == 'reference' and teaching in ('one', 'two') and variant != 'empty_teachings',
        zpick=lambda item, r, first, second: (
            second if variant == 'wrong_teaching_content' else first) if item == 'one' else second,
        h233c=lambda p, content, t: belief and (p, t) == (
            'second' if variant == 'other_believer' else 'first', 'later')
            and symbol(content) in (
                ('zfirst',) if variant in ('one_teaching_rejected', 'wrong_teaching_content')
                else ('zfirst', 'zsecond')))
    return v


@lru_cache(None)
def drill_checks():
    doc = fixture('drill')
    rows = {}
    for variant in ('baseline', 'practice_not_occurring', 'other_person_practices', 'not_practice',
                    'different_pattern', 'nonmilitary_pattern', 'pattern_at_wrong_reference'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, same_person_practice_and_military_pattern=True, native_content=True)


@lru_cache(None)
def payment_checks():
    doc = fixture('payment')
    rows = {}
    for variant in ('baseline', 'unrelated_payment', 'other_payer', 'self_transfer',
                    'transfer_at_wrong_point', 'different_medium_accepted', 'unaccepted_medium'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, native_rfa_ti_tj=True, unrelated_transfer_cannot_pay_the_named_transaction=True)


@lru_cache(None)
def belief_checks():
    doc = fixture('belief')
    rows = {}
    for variant in ('baseline', 'empty_teachings', 'other_believer', 'one_teaching_rejected', 'wrong_teaching_content'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for truth in (True, False):
        v = model(doc); v['ztruth'] = lambda *args, truth=truth: truth
        assert evaluate(doc, v, PEOPLE, SCENES, True) == [True]
    for missing in ('h233a', 'h233c', 'zpick'):
        v = model(doc); v[missing] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, same_nonempty_teaching_scope=True, doctrine_truth_not_required=True,
                native_quote_provider=True, unknown_inputs_refused=3)


@lru_cache(None)
def combination_checks():
    doc = fixture('combined')
    rows = {}
    for flags in product((False, True), repeat=4):
        actual = evaluate(doc, model(doc, flags=flags), PEOPLE, SCENES, True)
        assert actual == [not flags[0] and p for p in flags[1:]] + [True] * 3, (flags, actual)
        rows[str(flags)] = actual[:3]
    quoted = fixture('quoted')
    v = {d['name']: unknown for d in quoted['declarations'] if d['kind'] == 'primitive'}
    seen = []
    def conveys(call, person, subject, desc, point):
        node = json.loads(desc.syntax)
        seen.append(node['function']['symbol'])
        return (call, person, subject, point) == ('second', 'first', 'first', 'later') and desc.rank == 0 and (
            node['kind'] == 'apply' and node['function']['symbol'] in COMMANDS and
            node['arguments'] == [dict(kind='call', symbol='zr', arguments=[])])
    v.update(zp=lambda: 'first', zs=lambda: 'second', zr=unknown, zt=lambda: 'later', f2=conveys)
    assert evaluate(quoted, v, PEOPLE, SCENES, True) == [True] * 3
    assert seen == list(COMMANDS)
    return dict(contrasts=rows, native_all_three_contents_and_prohibition=True,
                positive_and_negative_parts_both_required=True, directive_distinct_from_assertion=True,
                quoted_reference_execution_and_belief_unknown=True, semantic_boundaries=[])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    return dict(status='three_command_contents_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[274, 426], text=unit['text'][274:426]),
                interpretation=LIMITS, definitions=list(MEANINGS),
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                authored_statements_added=0, preserved_reviewed_sentence_characters=232,
                references=['https://korpora.org/Kant/aa08/037.html',
                            'https://www.duden.de/rechtschreibung/exerzieren',
                            'https://fwb.sub.uni-goettingen.de/lemma/glauben.h1.3v'],
                unresolved=['三つの発信者の役割', '発話・命令の対応とsagtの省略',
                            'sondernの代替提示', '前文の諸方面との対応', '三文全体の帰属と通読'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in
                               (FULL, BASIS, DOC, INVENTORY, PRIOR, SENTENCES)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'] == old.document['statements']
    assert len(new.document['statements']) == 65
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    sentences = read(SENTENCES)
    assert sentences['selection'] == selection_binding(new, [64])
    assert sentences['first_sentence_recheck']['selection'] == selection_binding(new, [63])
    for path in (PRIOR, SENTENCES):
        validate_hashes(ROOT, read(path)['source_sha256'])
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_whole_unit_reviews=len(reviews), added_definitions=len(MEANINGS),
                added_basic_relations=len(PRIMITIVES), preserved_statements=65, added_statements=0,
                preserved_reviewed_sentence_characters=232, old_definitions_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('drill', drill_checks), ('payment', payment_checks), ('belief', belief_checks),
                     ('combination', combination_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR, SENTENCES, 'scripts/compose_command_alternatives.py',
        'scripts/check_command_alternatives.py', 'tests/test_command_alternatives.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='three_command_contents_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_three_negative_and_positive_command_contents'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
