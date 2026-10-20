"""Check assessed unreliability, native judgment, and conditional content binding."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, canonical_digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_uncertain_judgment import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v107.json'
REPORT = 'reports/uncertain-judgment-v1.json'
AUDIT = 'data/uncertain-judgment-reading-v1.json'
DOC = 'docs/uncertain-judgment-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ['reports/abandoned-reliance-v1.json', 'reports/depicted-referents-v1.json', 'reports/fetters-sentence-v1.json']
SENTENCES = [('data/nature-sentence-reading-v1.json', [51]), ('data/confirmed-incapacity-reading-v1.json', [11, 12]),
             ('data/fetters-sentence-reading-v1.json', [10, 52])]

PEOPLE = ('person', 'act', 'copy', 'topic', 'other', 'reason', 'faculty')
SCENES = ('anchor', 'one', 'two', 'outside')


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
    doc = fixture(['r2gu', 'r2gv', 'r2gw'], '''r zc[d] c.r zh[d] c.r zo[d] c.r zp[d d] c.r zr[d] c.
q[k r2gu[p zc p zh p zo p zp]].q[k r2gv[p zc p zh p zo p zp p zr]].q[k r2gw[p zc p zh p zo p zp p zr]].''')
    scenes = ('one', 'two')
    for bits in product((False, True), repeat=6):
        response, held, opportunity = bits[:2], bits[2:4], bits[4:]
        values = dict(zc=lambda s: True, zp=lambda a, b: False, zh=lambda s: held[scenes.index(s)],
            zo=lambda s: opportunity[scenes.index(s)], zr=lambda s: response[scenes.index(s)])
        valid = all(held + opportunity)
        assert evaluate(doc, values, ('person',), scenes, True) == [valid, valid and all(response), valid and not all(response)], bits
    values = dict(zc=lambda s: True, zh=lambda s: True, zo=lambda s: True, zp=lambda a, b: False, zr=lambda s: s == 'one')
    rows = {}
    for name, expected in [('mixed', [True, False, True]), ('first_preferred', [True, True, False]),
                           ('second_preferred', [True, False, True]), ('cycle', [False, False, False]),
                           ('empty', [False, False, False]), ('invalid_nonpreferred', [False, False, False])]:
        v = dict(values)
        if name in ('first_preferred', 'invalid_nonpreferred'): v['zp'] = lambda a, b: (a, b) == ('one', 'two')
        if name == 'second_preferred': v['zp'] = lambda a, b: (a, b) == ('two', 'one')
        if name == 'cycle': v['zp'] = lambda a, b: a != b
        if name == 'empty': v['zc'] = lambda s: False
        if name == 'invalid_nonpreferred': v['zh'] = lambda s: s == 'one'
        actual = evaluate(doc, v, ('person',), scenes, True); assert actual == expected, (name, actual); rows[name] = actual
    refuse(doc, values, ('zc', 'zh', 'zo', 'zp', 'zr'), ('person',), scenes)
    return dict(combinations=64, cases=rows, unknown_inputs_refused=5, invalid_is_not_unreliable=True,
        mixed_normal_responses_are_unreliable=True)


def source_values(doc, variant='baseline', actual_support=True, responses=(True, False)):
    values = unknowns(doc)
    def performed(p, j, s):
        return ((p, j, s) == ('person', 'act', 'anchor') and variant != 'no_actual' or
                (p, j) == ('person', 'copy') and s in ('one', 'two') and not (variant == 'missed_response' and s == 'two'))
    def support(r, j, s):
        return r == 'reason' and ((j, s) == ('act', 'anchor') and actual_support or
            j == 'copy' and s in ('one', 'two') and responses[('one', 'two').index(s)])
    values.update(zperson=lambda: 'person', zact=lambda: 'act', ztopic=lambda: 'topic', zanchor=lambda: 'anchor',
        wh=lambda: 'anchor', hzzzz=lambda p, sc: 'topic' if (p, sc) == ('person', 'anchor') else 'other',
        fa=performed, dg=lambda j, s: performed('person', j, s),
        fb=lambda j, t, s: j in ('act', 'copy') and t == ('other' if variant == 'wrong_actual_topic' and (j, s) == ('act', 'anchor') else 'topic'),
        ab=lambda f, p, s: (f, p) == ('faculty', 'person'),
        ac=lambda p, f, j, s: (p, f) == ('person', 'faculty') and j in ('act', 'copy') and not (variant == 'wrong_actual_faculty' and (j, s) == ('act', 'anchor')),
        ad=lambda o, p, j, s: variant == 'guided_actual' and (o, p, j, s) == ('other', 'person', 'act', 'anchor'),
        fc=lambda j, r, s: j in ('act', 'copy') and r == 'reason', fd=support,
        hzzzt=lambda p, j, t, a, s: variant != 'empty_profile' and (p, j, t, a) == ('person', 'act', 'topic', 'anchor') and s in ('one', 'two'),
        hzzzu=lambda p, j, t, a, s: not (variant == 'changed_basis' and s == 'two'),
        hzzzv=lambda p, t, s: (p, t) == ('person', 'topic') and not (variant == 'no_opportunity' and s == 'two'),
        hzzzw=lambda p, j, t, a, f, l: variant == 'cycle' and f != l or variant in ('prefer_supported', 'invalid_nonpreferred') and (f, l) == ('one', 'two'),
        hzzzx=lambda p, j, t, a, s, c: (p, j, t, a) == ('person', 'act', 'topic', 'anchor') and s in ('one', 'two') and c == 'copy' and not (variant == 'missing_counterpart' and s == 'two'))
    if variant == 'invalid_nonpreferred': values['hzzzu'] = lambda p, j, t, a, s: s != 'two'
    if variant == 'support_for_other_judgment': values['fd'] = lambda r, j, s: (r, j) == ('reason', 'other')
    if variant == 'wrong_counterpart_topic': values['fb'] = lambda j, t, s: t == ('other' if j == 'copy' else 'topic')
    return values


@lru_cache(None)
def judgment_checks():
    suffix = 'r zperson[] a.r zact[] a.r ztopic[] a.r zanchor[] d.'
    suffix += ''.join('q[k '+n+'[k zperson[] k zact[] k ztopic[] k zanchor[]]].' for n in ('r2gx', 'r2gy', 'r2gz', 'r2ha'))
    doc = fixture(['r2ha', 'r2gy'], suffix)
    for actual, first, second in product((False, True), repeat=3):
        v = source_values(doc, actual_support=actual, responses=(first, second))
        wanted = [True, actual, not (first and second), not (first and second)]
        assert evaluate(doc, v, PEOPLE, SCENES, True) == wanted
    rows = {}
    variants = {
        'baseline': [True, True, True, True], 'no_actual': [False, False, True, False],
        'wrong_actual_topic': [False, False, True, False], 'wrong_actual_faculty': [False, False, True, False],
        'guided_actual': [False, False, True, False], 'support_for_other_judgment': [True, False, True, True],
        'wrong_counterpart_topic': [True, True, True, True],
        **{name: [True, True, False, False] for name in ('empty_profile', 'changed_basis', 'no_opportunity', 'cycle', 'missing_counterpart', 'prefer_supported', 'invalid_nonpreferred')},
    }
    for name, wanted in variants.items():
        actual = evaluate(doc, source_values(doc, name), PEOPLE, SCENES, True)
        assert actual == wanted, (name, actual); rows[name] = actual
    missed = evaluate(doc, source_values(doc, 'missed_response', responses=(True, True)), PEOPLE, SCENES, True)
    assert missed == [True, True, True, True]; rows['missed_response'] = missed
    names = ('hzzzt', 'hzzzu', 'hzzzv', 'hzzzw', 'hzzzx', 'fa', 'fb', 'ab', 'ac', 'ad', 'fc', 'fd', 'dg')
    refuse(doc, source_values(doc), names)
    # Execute the real existential consequence, including a fixed topic.
    native = fixture(['r2hb'], 'r zperson[] a.r zanchor[] d.q[t[k r2hb[k zperson[]]][k zanchor[]]].')
    native_rows = {}
    for name, responses, expected in [('baseline', (True, False), True), ('reliable', (True, True), False), ('no_actual', (True, False), False)]:
        actual = evaluate(native, source_values(native, name, responses=responses), PEOPLE, SCENES, True)
        assert actual == [expected], (name, actual); native_rows[name] = actual
    refuse(native, source_values(native), ('hzzzz', 'wh'))
    return dict(combinations=8, cases=rows, unknown_inputs_refused=15, native_consequence=native_rows,
        current_supported_judgment_can_be_unreliable=True, native_reasoned_judgment_executed=True,
        absent_counterparts_not_counted_as_failure=True)


@lru_cache(None)
def conditional_checks():
    # Isolate the content boundary: native antecedent and consequent are checked
    # separately. This tests their binding and conditional logic, not joint execution.
    doc = fixture(['r2hd'], '''r zante[a d] c.r zcons[a d] c.r zperson[] a.r zanchor[] d.
d zbefore[person a] e[b point[k zante[v person v point]]].
d zafter[person a] e[b point[k zcons[v person v point]]].
q[t[k r2hd[k zperson[]]][k zanchor[]]].''')
    lookup = {d['name']: d for d in doc['declarations']}
    for name, target in [('r2gt', 'zbefore'), ('r2hb', 'zafter')]:
        lookup[name]['body'] = deepcopy(lookup[target]['body']); lookup[name]['parameters'] = deepcopy(lookup[target]['parameters'])
    doc['declarations'] = closure(doc, ['r2hd', 'zperson', 'zanchor'])
    doc['declarations'].sort(key=lambda d: d['kind'] != 'primitive')
    doc = parse(format_graph(doc, 'compact'))
    scenes = ('scope', 'one', 'two'); people = ('person', 'other')
    def model(bits=(True, False, True, False)):
        return dict(wh=lambda: 'scope', zanchor=lambda: 'scope', zperson=lambda: 'person',
            hzzzy=lambda p, sc, s: (p, sc) == ('person', 'scope') and s in ('one', 'two'),
            zante=lambda p, s: p == 'person' and s in ('one', 'two') and bits[('one', 'two').index(s)],
            zcons=lambda p, s: p == 'person' and s in ('one', 'two') and bits[2+('one', 'two').index(s)])
    for bits in product((False, True), repeat=4):
        wanted = any(bits[:2]) and all(not bits[i] or bits[i+2] for i in range(2))
        assert evaluate(doc, model(bits), people, scenes, True) == [wanted], bits
    rows = {}
    for name in ('baseline', 'empty', 'other_person_consequence', 'other_scope', 'wrong_anchor'):
        v = model()
        if name == 'empty': v['hzzzy'] = lambda *args: False
        if name == 'other_person_consequence': v['zcons'] = lambda p, s: p == 'other'
        if name == 'other_scope': v['hzzzy'] = lambda p, sc, s: sc == 'one'
        if name == 'wrong_anchor': v['zanchor'] = lambda: 'one'
        actual = evaluate(doc, v, people, scenes, True); assert actual == [name == 'baseline']; rows[name] = actual
    refuse(doc, model(), ('hzzzy', 'zante', 'zcons', 'wh'), people, scenes)
    return dict(combinations=16, cases=rows, unknown_inputs_refused=4, same_person_and_scope=True,
        content_boundary_test=True, native_antecedent_and_consequence_joint_execution=False)


@lru_cache(None)
def native_conditional_checks():
    doc = fixture(['r2hd'], 'r zperson[] a.r zanchor[] d.q[t[k r2hd[k zperson[]]][k zanchor[]]].')
    people = PEOPLE + ('process', 'source', 'author')
    scenes = ('before', 'anchor', 'one', 'two')
    rows = {}
    for variant in ('baseline', 'reliable', 'no_departure', 'no_actual'):
        values = source_values(doc, variant, responses=(True, variant == 'reliable'))
        actual_occurs = values['dg']
        values.update(h2d=lambda: 'source', wa=lambda: 'author',
            hzzzm=lambda n, a, d, p, o, s: (n, a, symbol(d), p, o, s) == ('source', 'author', 'r2fh', 'person', 'topic', 'anchor'),
            hzzzo=lambda sc, o, p, a, s: (sc, o, p) == ('anchor', 'topic', 'person') and (a, s) in (('before', 'one'), ('anchor', 'two')),
            hzzzp=lambda *args: True, hzzzq=lambda *args: True, hzzzr=lambda *args: False,
            hx2=lambda p, o, act, s: (p, o, act, s) == ('person', 'topic', 'act', 'one'), hz2=lambda *args: False,
            dg=lambda act, s: actual_occurs(act, s) or (act, s) == ('act', 'one') or variant != 'no_departure' and (act, s) == ('process', 'anchor'),
            hzzzs=lambda p, end, t: (p, end) == ('person', 'anchor') and t in ('before', 'anchor'),
            ic=lambda a, b, s: (a, b, s) == ('before', 'anchor', 'anchor'),
            ag=lambda proc, a, b: (proc, a, b) == ('process', 'before', 'anchor'),
            la=lambda p, proc, a, b: (p, proc, a, b) == ('person', 'process', 'before', 'anchor'),
            df=lambda p, proc, s: (p, proc, s) == ('person', 'process', 'anchor'),
            hzid=lambda p, proc, old, new, a, b: (p, proc, symbol(old), symbol(new), a, b) == ('person', 'process', 'r2gp', 'r2gq', 'before', 'anchor'),
            g3=lambda proc, p, d, s: (proc, p, symbol(d), s) == ('process', 'person', 'r2gq', 'anchor'),
            hzzzy=lambda p, sc, s: (p, sc, s) == ('person', 'anchor', 'anchor'))
        actual = evaluate(doc, values, people, scenes, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(cases=rows, native_antecedent_and_consequence_joint_execution=True,
        shared_person_topic_and_comparison_world=True)


@lru_cache(None)
def quotation_checks():
    doc = fixture(['r2hd'], 'q[e[r[p r2hd]][r[p r2hd]]].')
    assert evaluate(doc, unknowns(doc), PEOPLE, SCENES, True) == [True]
    return dict(closed_conditional_quotable_without_world_evaluation=True)

def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    start = unit['text'].index('unsicheren', 474); end = start + len('unsicheren Sprung thun')
    current = catalog(); dependencies = [d['name'] for d in closure(current.document, ['r2hd'])]
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, *PRIOR, *(p for p, _ in SENTENCES)}
    return dict(status='unasserted_uncertain_judgment_and_conditional_candidate', reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, end], text=unit['text'][start:end]),
        candidate_definitions=list(MEANINGS), candidate_dependency_sha256=canonical_digest([current.entries[n] for n in dependencies]),
        candidate_dependencies=dependencies, preserved_authored_selection=selection_binding(current, [13, 53]),
        decision='同じ課題への判断は実行するが、通常比較全体に理由ある自己遂行を確保できない後件候補を構成し、前版の離脱と同じ本人の条件骨格へ結ぶ。尺度・限定・不慣れの理由と著者帰属への採用は未完。',
        interpretation_limits=LIMITS, revised_statement_indices=[],
        references=[dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036', accessed='2026-10-20',
            use='依存を離れても不確かな跳躍をするという描写を照合。理由ある独立判断の非確実性は対象側の読解候補であり、原文の唯一の語義ではない。')],
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=408,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-17] == old.document['declarations']
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
    return dict(added_definitions=10, added_primitives=7, authored_statements=54, preserved_statements=54,
        revised_statement_indices=[], preserved_review_selections=12, reviewed_nonblank_characters=2212,
        preserved_reviewed_sentence_characters=408, candidate_not_asserted=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items(): write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('profile', profile_checks), ('judgment', judgment_checks), ('conditional', conditional_checks), ('native', native_conditional_checks),
                     ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    record = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(record['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_uncertain_judgment.py', 'scripts/check_uncertain_judgment.py',
        'scripts/register_uncertain_judgment.py', 'tests/test_uncertain_judgment.py',
        'scripts/check_abandoned_reliance.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    for path in PRIOR: paths.update(read(path)['source_sha256'])
    paths.update(read(INDEX)['works']['kant-1784']['reviews'])
    return dict(status='uncertain_judgment_and_conditional_candidate_checked', document=FULL, **results,
        alignment=dict(**record['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_covered_characters=0, new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=408,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
