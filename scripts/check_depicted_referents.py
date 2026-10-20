"""Check total paired reference ranges and their use by both fourth-sentence parts."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_depicted_referents import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_generic_fetters import presentation_values

INDEX = 'data/semantic-review-index-v105.json'
REPORT = 'reports/depicted-referents-v1.json'
AUDIT = 'data/depicted-referents-reading-v1.json'
DOC = 'docs/depicted-referents-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
SENTENCES = [('data/nature-sentence-reading-v1.json', [51]),
             ('data/confirmed-incapacity-reading-v1.json', [11, 12]),
             ('data/fetters-sentence-reading-v1.json', [10, 52])]
PRIOR = ['reports/fetters-sentence-v1.json', 'reports/occasional-continuation-v1.json']
PEOPLE = ('person', 'other', 'shackle', 'shackle2', 'rule', 'form', 'first', 'third', 'fourth', 'author')
PRESENTATION = PEOPLE + ('reason', 'second', 'subject', 'apposition', 'correction')
SCENES = ('scope', 'before', 'case')


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
def range_checks():
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8') + '''
r zs[a] c.r zt[a] c.r zm[a a] c.q[k r2gf[p zs p zt p zm]].''')
    domain = ('s1', 's2', 't1', 't2')
    possible = list(product(domain[:2], domain[2:]))
    for bits in product((False, True), repeat=8):
        sources = {s for s, b in zip(domain[:2], bits[:2]) if b}
        targets = {t for t, b in zip(domain[2:], bits[2:4]) if b}
        edges = {e for e, b in zip(possible, bits[4:]) if b}
        expected = bool(sources and targets) and {s for s, _ in edges} == sources and {t for _, t in edges} == targets
        values = dict(zs=lambda s: s in sources, zt=lambda t: t in targets, zm=lambda s, t: (s, t) in edges)
        assert evaluate(doc, values, domain, ('scope',), True) == [expected], bits
    cases = {}
    for name, edges, wanted in [
        ('one_to_one', {('s1', 't1'), ('s2', 't2')}, True),
        ('many_to_many', set(possible), True),
        ('unmatched_source', {('s1', 't1'), ('s1', 't2')}, False),
        ('unmatched_target', {('s1', 't1'), ('s2', 't1')}, False),
        ('outside_edge', set(possible) | {('t1', 's1')}, False),
    ]:
        values = dict(zs=lambda s: s in domain[:2], zt=lambda t: t in domain[2:], zm=lambda s, t: (s, t) in edges)
        actual = evaluate(doc, values, domain, ('scope',), True)
        assert actual == [wanted], (name, actual); cases[name] = actual
    values = dict(zs=lambda s: s in domain[:2], zt=lambda t: t in domain[2:], zm=lambda s, t: (s, t) in possible)
    refuse(doc, values, ('zs', 'zt', 'zm'), domain, ('scope',))
    return dict(combinations=256, cases=cases, unknown_inputs_refused=3,
        two_sided_coverage_and_edge_endpoints_checked=True, physical_identity_not_required=True)


@lru_cache(None)
def person_checks():
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8') + '''
r zp[a] c.r zs[a a] c.r zt[a a] c.r zm[a a a] c.q[k r2gg[p zp p zs p zt p zm]].''')
    domain = ('p1', 'p2', 'source', 'target')
    for bits in product((False, True), repeat=6):
        people = {p for p, b in zip(domain[:2], bits[:2]) if b}
        sources = {p for p, b in zip(domain[:2], bits[2:4]) if b}
        targets = {p for p, b in zip(domain[:2], bits[4:]) if b}
        values = dict(zp=lambda p: p in people, zs=lambda o, p: o == 'source' and p in sources,
            zt=lambda o, p: o == 'target' and p in targets,
            zm=lambda s, t, p: (s, t) == ('source', 'target') and p in sources & targets)
        assert evaluate(doc, values, domain, ('scope',), True) == [bool(people) and sources == targets == people], bits
    values = dict(zp=lambda p: p == 'p1', zs=lambda o, p: (o, p) == ('source', 'p1'),
        zt=lambda o, p: (o, p) == ('target', 'p1'), zm=lambda s, t, p: (s, t, p) == ('source', 'target', 'p1'))
    cases = {}
    for name in ('baseline', 'other_person_only', 'outside_person_edge', 'missing_second_person'):
        changed = dict(values)
        if name == 'other_person_only': changed['zm'] = lambda s, t, p: (s, t, p) == ('source', 'target', 'p2')
        if name == 'outside_person_edge': changed['zm'] = lambda s, t, p: (s, t) == ('source', 'target') and p in domain[:2]
        if name == 'missing_second_person': changed['zp'] = lambda p: p in domain[:2]
        actual = evaluate(doc, changed, domain, ('scope',), True)
        assert actual == [name == 'baseline'], (name, actual); cases[name] = actual
    refuse(doc, values, ('zp', 'zs', 'zt', 'zm'), domain, ('scope',))
    return dict(combinations=64, cases=cases, unknown_inputs_refused=4, no_cross_person_borrowing=True)


def source_values(doc, variant='baseline'):
    values = unknowns(doc)
    values.update(wh=lambda: 'scope', hzzq=lambda: 'first', h2d=lambda: 'third', h3a=lambda: 'fourth', wa=lambda: 'author',
        aa=lambda p: p in ('person', 'other'),
        hzzn=lambda n, p, s: (n, p, s) == ('first', 'person', 'scope'),
        h2s=lambda o, p, s: o in ('shackle', 'shackle2') and (p, s) == ('person', 'scope'))
    targets = {'rule', 'form'}
    edges = {('shackle', 'rule'), ('shackle2', 'form')}
    if variant == 'many_to_one': targets = {'rule'}; edges = {('shackle', 'rule'), ('shackle2', 'rule')}
    if variant == 'one_to_many': edges = {('shackle', 'rule'), ('shackle', 'form'), ('shackle2', 'form')}
    if variant == 'missing_target': targets = {'rule'}
    if variant == 'missing_source_edge': edges = {('shackle', 'rule'), ('shackle', 'form')}
    if variant == 'outside_edge': edges.add(('other', 'rule'))
    if variant == 'empty_targets': targets = set()
    def selected(n, a, kind, p, o, s):
        expected = ('first' if variant == 'wrong_antecedent' else 'third',
                    'other' if variant == 'wrong_author' else 'author',
                    'other' if variant == 'wrong_person' else 'person',
                    'case' if variant == 'depiction_time' else 'scope')
        return (n, a, p, s) == expected and o in targets and kind.rank == 1 and symbol(kind) == ('hd2' if variant == 'wrong_kind' else 'r2fh')
    def mapping(n, prior, a, p, left, right, s):
        return (n, prior, a, p, s) == (
            'third' if variant == 'wrong_current_node' else 'fourth',
            'first' if variant == 'wrong_mapping_antecedent' else 'third', 'author',
            'other' if variant == 'other_person_mapping' else 'person', 'scope') and (left, right) in edges
    values.update(hzzzm=selected, hzzzn=mapping)
    if variant == 'outside_person_selection':
        before = values['h2s']; values['h2s'] = lambda o, p, s: before(o, p, s) or (o, p, s) == ('shackle', 'other', 'scope')
    if variant == 'empty_people': values['hzzn'] = lambda *args: False
    if variant == 'nonhuman': values['aa'] = lambda p: False
    return values


@lru_cache(None)
def binding_checks():
    doc = fixture(['r2gh', 'wh'], 'q[k r2gh[k wh[]]].')
    cases = {}
    for name in ('baseline', 'many_to_one', 'one_to_many', 'missing_target', 'missing_source_edge', 'outside_edge',
                 'empty_targets', 'wrong_antecedent', 'wrong_author', 'wrong_person', 'depiction_time', 'wrong_kind',
                 'wrong_current_node', 'wrong_mapping_antecedent', 'other_person_mapping', 'outside_person_selection', 'empty_people', 'nonhuman'):
        actual = evaluate(doc, source_values(doc, name), PEOPLE, SCENES, True)
        assert actual == [name in ('baseline', 'many_to_one', 'one_to_many')], (name, actual)
        cases[name] = actual
    refuse(doc, source_values(doc), ('aa', 'hzzn', 'h2s', 'hzzzm', 'hzzzn'))
    return dict(cases=cases, unknown_inputs_refused=5, kind_description_not_executed=True,
        different_depicted_and_target_individuals=True, discourse_scope_fixed=True)


@lru_cache(None)
def native_checks():
    doc = fixture(['r2gh', 'h2w', 'wh'], '''r zperson[] a.r zcase[] d.
q[k r2gh[k wh[]]].q[t[k h2w[k zperson[] k wh[]]][k zcase[]]].''')
    domain = PEOPLE + ('release', 'limb', 'movement')
    rows = {}
    for name in ('baseline', 'missing_source_edge', 'still_bound', 'no_termination'):
        values = source_values(doc, name)
        values.update(zperson=lambda: 'person', zcase=lambda: 'case',
            h2r=lambda p, c, t: (p, c) == ('person', 'case') and t in ('before', 'case'),
            ic=lambda a, b, c: (a, b, c) == ('before', 'case', 'case'),
            ag=lambda e, a, b: (e, a, b) == ('release', 'before', 'case'),
            la=lambda p, e, a, b: (p, e, a, b) == ('person', 'release', 'before', 'case'),
            df=lambda p, e, t: (p, e, t) == ('person', 'release', 'case'),
            h2q=lambda e, o, p, a, b: name != 'no_termination' and o in ('shackle', 'shackle2') and (e, p, a, b) == ('release', 'person', 'before', 'case'),
            h2e=lambda o, limb, p, t: o in ('shackle', 'shackle2') and (limb, p) == ('limb', 'person') and (t == 'before' or name == 'still_bound' and o == 'shackle2' and t == 'case'),
            h2f=lambda limb, p, t: (limb, p) == ('limb', 'person'),
            h2g=lambda p, act, t: (p, act) == ('person', 'movement'),
            h2h=lambda o, limb, p, act, t: o in ('shackle', 'shackle2') and (limb, p, act) == ('limb', 'person', 'movement'))
        actual = evaluate(doc, values, domain, SCENES, True)
        wanted = [name != 'missing_source_edge', name not in ('still_bound', 'no_termination')]
        assert actual == wanted, (name, actual); rows[name] = actual
    return dict(cases=rows, native_removal_and_same_selected_objects_executed=True,
        reference_mapping_does_not_imply_release=True, physical_release_does_not_imply_complete_reference=True)


def presentation_model(doc, bits=(True, True, True, True), variant='baseline'):
    prior, conditional, reason, mapped = bits
    values = presentation_values(doc)
    # This fixture evaluates attribution and reference, never the quoted world contents.
    values.update(source_values(doc, 'missing_source_edge' if not mapped else variant))
    values.update(hzzr=lambda: 'second', hzzzj=lambda: 'subject', hzzzk=lambda: 'apposition',
        hk2=lambda: 'correction', h3s=lambda: 'reason',
        uc=lambda n, a, d, s: (a, s) == ('author', 'scope') and (
            prior and n == 'third' and symbol(d) == 'r2gc' or
            conditional and n == 'fourth' and symbol(d) == 'h2z' or
            reason and n == 'reason' and symbol(d) == 'h4e'),
        rbt=lambda n, a, t, d, s: (n, a, symbol(t), symbol(d), s) == ('third', 'author', 'r2gd', 'h2b', 'scope'),
        rbf=lambda n, a, f, t, s: (n, a, symbol(f), symbol(t), s) == ('correction', 'author', 'hm2', 'hn2', 'scope'),
        ibbdenotes=lambda n, a, d, sc, s: n in ('subject', 'apposition') and (a, symbol(d), d.rank, sc, s) == ('author', 'r2fh', 1, 'third', 'scope'),
        ibbclarifies=lambda f, l, a, sc, s: (f, l, a, sc, s) == ('subject', 'apposition', 'author', 'third', 'scope'))
    order = {('subject', 'apposition'), ('second', 'third'), ('third', 'fourth'), ('fourth', 'reason')}
    if variant == 'reverse_order': order.add(('fourth', 'third'))
    if variant == 'missing_previous_order': order.remove(('third', 'fourth'))
    if variant == 'missing_reason_order': order.remove(('fourth', 'reason'))
    values['ue'] = lambda f, l, s: s == 'scope' and (f, l) in order
    return values


@lru_cache(None)
def presentation_checks():
    doc = fixture(['r2gj', 'r2gk'], 'q[k r2gj[]].q[k r2gk[]].')
    for bits in product((False, True), repeat=4):
        actual = evaluate(doc, presentation_model(doc, bits), PRESENTATION, SCENES, True)
        assert actual == [bits[0] and bits[1] and bits[3], bits[0] and bits[2] and bits[3]], (bits, actual)
    rows = {}
    for name, expected in [('baseline', [True, True]), ('reverse_order', [False, False]),
                           ('missing_previous_order', [False, False]), ('missing_reason_order', [True, False]),
                           ('wrong_mapping_antecedent', [False, False])]:
        actual = evaluate(doc, presentation_model(doc, variant=name), PRESENTATION, SCENES, True)
        assert actual == expected, (name, actual); rows[name] = actual
    refuse(doc, presentation_model(doc), ('uc', 'rbt', 'ue', 'hzzzm', 'hzzzn'), PRESENTATION, SCENES)
    return dict(combinations=16, cases=rows, unknown_inputs_refused=5,
        both_attributions_require_same_reference=True, quoted_world_contents_not_executed=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, *PRIOR, *(p for p, _ in SENTENCES)}
    return dict(status='fourth_sentence_depicted_referents_candidate', reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[474, 481], text=unit['text'][474:481]),
        selection=selection_binding(catalog(), [13, 53]),
        decision='先行する比喩を受ける描写側と指示対象側を、同じ人物・提示文脈で両側とも網羅する。第四文の対象側の条件内容と全体判断は未完。',
        interpretation_limits=LIMITS, revised_statement_indices=[13, 53],
        references=[dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036', accessed='2026-10-20',
            use='第三文の足枷と、第四文冒頭のそれを捨てる仮定、後続の跳躍と不慣れを照合。指示対象側の全内容は未完。')],
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=408,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-8] == old.document['declarations']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    assert len(old.document['statements']) == len(new.document['statements']) == 54
    assert [i for i, (a, b) in enumerate(zip(old.document['statements'], new.document['statements'])) if a != b] == [13, 53]
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        row = read(path); validate_hashes(ROOT, row['source_sha256'])
        ids = [s['index'] for s in row['selection']['statements']]
        assert row['selection'] == selection_binding(old, ids) == selection_binding(new, ids)
    for path, ids in SENTENCES:
        row = read(path); validate_hashes(ROOT, row['source_sha256'])
        assert row['selection'] == selection_binding(new, ids)
    for path in PRIOR: validate_hashes(ROOT, read(path)['source_sha256'])
    assert closure(old.document, ['h3b', 'h4f', 'r2ge']) == closure(new.document, ['h3b', 'h4f', 'r2ge'])
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE, LIBRARY):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(doc, style); assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    assert read(AUDIT) == reading()
    return dict(added_definitions=6, added_primitives=2, authored_statements=54, preserved_statements=52,
        revised_statement_indices=[13, 53], preserved_review_selections=12, reviewed_nonblank_characters=2212,
        preserved_reviewed_sentence_characters=408, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items(): write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('ranges', range_checks), ('people', person_checks), ('binding', binding_checks),
                     ('native', native_checks), ('presentation', presentation_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    record = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(record['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_depicted_referents.py', 'scripts/check_depicted_referents.py',
        'scripts/register_depicted_referents.py', 'tests/test_depicted_referents.py',
        'scripts/check_generic_fetters.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    for path in PRIOR: paths.update(read(path)['source_sha256'])
    paths.update(read(INDEX)['works']['kant-1784']['reviews'])
    return dict(status='fourth_sentence_reference_correspondence_checked', document=FULL, **results,
        alignment=dict(**record['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_covered_characters=0, new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=408,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
