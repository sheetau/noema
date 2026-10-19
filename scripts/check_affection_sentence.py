"""Check shared-person binding, focused expectations and scoped attribution."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_affection_sentence import ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, REFERENCES, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_attributed_focus import unwrap

INDEX = 'data/semantic-review-index-v96.json'
AUDIT = 'data/affection-sentence-reading-v1.json'
REPORT = 'reports/affection-sentence-v1.json'
DOC = 'docs/affection-sentence-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
FIRST = 'data/nature-sentence-reading-v1.json'
COMPONENTS = {'acquired-affection': ['r2ck'], 'current-deprivation': ['r2cf', 'r2cg'],
              'expected-focus': ['rqts'], 'attributed-focus': ['rqtv'], 'nature-sentence': ['r2eb']}
PEOPLE = ('first', 'second', 'outsider', 'node', 'author')
SCENES = ('now', 'elsewhere')


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(roots, suffix):
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, roots.split()), statements=[])
    return parse(format_graph(doc, 'compact') + suffix)


@lru_cache(None)
def boundary_document():
    suffix = 'q[t[k r2eg[]][k wh[]]].q[t[k r2eh[]][k wh[]]].'
    for package in ('k r2ek[]', 'k rsw[k r2ek[]]'):
        for name in ('rsx', 'rsy'): suffix += 'q[k ' + name + '[' + package + ' k wh[]]].'
    doc = fixture('r2eg r2eh r2ek rsx rsy rsw wh', suffix)
    probes = parse('p:' + ''.join('r z' + n + '[a d] c.' for n in ('attachment', 'deprivation', 'nature')) + ''.join(
        'd ' + name + '[person a] e[b point[k z' + pred + '[v person v point]]].'
        for name, pred in [('r2ck', 'attachment'), ('r2cg', 'deprivation'), ('r2eb', 'nature')]))
    replacements = {d['name']: d for d in probes['declarations'][3:]}
    doc = deepcopy(doc)
    doc['declarations'] = probes['declarations'][:3] + [deepcopy(replacements.get(d['name'], d)) for d in doc['declarations']]
    doc['declarations'] = closure(doc, ['r2eg', 'r2eh', 'r2ek', 'rsx', 'rsy', 'rsw', 'wh'])
    return parse(format_graph(doc, 'compact'))


def world_values(doc, attachment, deprivation, nature, relation=(True, False, True, True), scope=PEOPLE[:2], humans=PEOPLE[:3]):
    names = ('r2eg', 'r2eh')
    edges = {pair for pair, flag in zip(product(names, repeat=2), relation) if flag}
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(wh=lambda: 'now', wa=lambda: 'author', hzzq=lambda: 'node', aa=lambda p: p in humans,
        hzzn=lambda node, p, point: (node, point) == ('node', 'now') and p in scope,
        zattachment=lambda p, point: p in attachment and point == 'now',
        zdeprivation=lambda p, point: p in deprivation and point == 'now',
        znature=lambda p, point: p in nature and point == 'now',
        hzpt=lambda observer, left, right, point: (observer, point) == ('author', 'now') and (
            json.loads(left.syntax)['symbol'], json.loads(right.syntax)['symbol']) in edges)
    return values


@lru_cache(None)
def scope_checks():
    doc = boundary_document(); rows = []
    for bits in product((False, True), repeat=6):
        groups = [{p for p, flag in zip(PEOPLE[:2], bits[i:i+2]) if flag} for i in (0, 2, 4)]
        a, d, n = (all(bits[i:i+2]) for i in (0, 2, 4)); fg = a and d
        actual = evaluate(doc, world_values(doc, *groups), PEOPLE, SCENES, True)
        assert actual == [a, n, fg, True, not fg, True], (bits, actual)
        rows.append(dict(bits=bits, values=actual))
    contrasts = {}
    for name, a, d, n, scope, humans, expected in [
        ('empty_scope', (), (), (), (), PEOPLE[:3], [False, False, False, True, True, True]),
        ('split_people', ('first',), ('second',), PEOPLE[:2], PEOPLE[:2], PEOPLE[:3], [False, True, False, True, True, True]),
        ('unqualified_outsider', ('first',), ('first',), (), ('first',), PEOPLE[:3], [True, False, True, True, False, True]),
        ('nonhuman_member', PEOPLE, PEOPLE, PEOPLE, ('first', 'node'), PEOPLE[:3], [False, False, False, True, True, True])]:
        actual = evaluate(doc, world_values(doc, a, d, n, scope=scope, humans=humans), PEOPLE, SCENES, True)
        assert actual == expected, (name, actual)
        contrasts[name] = actual
    probe = deepcopy(doc); probe['statements'] = [doc['statements'][2]]
    for name in ('hzzn', 'aa', 'zattachment', 'zdeprivation'):
        values = world_values(doc, PEOPLE[:2], PEOPLE[:2], PEOPLE[:2]); values[name] = unknown
        try: evaluate(probe, values, PEOPLE, SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=rows, contrasts=contrasts, unknown_inputs_refused=4,
        same_people_and_scene_for_both_conjuncts=True, component_boundary_isolated=True,
        not_a_native_full_sentence_world_test=True)


@lru_cache(None)
def focus_checks():
    doc = boundary_document(); count = 0
    for relation in product((False, True), repeat=4):
        for attachment, deprivation, nature in product((False, True), repeat=3):
            values = world_values(doc, *(PEOPLE[:2] if x else () for x in (attachment, deprivation, nature)), relation=relation)
            actual = evaluate(doc, values, PEOPLE, SCENES, True)
            background = relation[0] and not relation[1] and relation[2] and relation[3]
            fg = attachment and deprivation
            assert actual == [attachment, nature, fg, background, not fg, background], (relation, actual)
            count += 1
    probe = deepcopy(doc); probe['statements'] = [doc['statements'][3]]
    values = world_values(doc, (), (), ())
    for name in ('hzzn', 'aa', 'zattachment', 'zdeprivation', 'znature'): values[name] = unknown
    assert evaluate(probe, values, PEOPLE, SCENES, True) == [True]
    values['hzpt'] = unknown
    try: evaluate(probe, values, PEOPLE, SCENES, True)
    except ValueError as error: assert 'Unknown' in str(error)
    else: raise AssertionError('Unknown expectation filled')
    return dict(combinations=count, background_independent_of_world_truth=True,
        negation_preserves_background=True, unknown_comparison_refused=True,
        ties_incomparability_reversal_and_missing_reflexivity_rejected=True)


@lru_cache(None)
def expected_background():
    # Specify the expected quotation independently of the package constructor.
    doc = fixture('rqts r2eg r2eh wa wh hzpt', '''q[t[k rqts[r b[k r2eg[]]
        l[i b[e]][r b[k r2eh[]]] k wa[] k wh[] p hzpt]][k wh[]]].''')
    call = doc['statements'][0]['body']['content']
    return dict(kind='apply', function=dict(kind='function_ref', symbol='rqts'), arguments=call['arguments'])


@lru_cache(None)
def discourse_checks():
    doc = fixture('r2el r2em', 'q[k r2el[]].q[k r2em[]].')
    expected_fg = dict(kind='call', symbol='r2ei', arguments=[]); expected_bg = expected_background()
    people = ('firstnode', 'secondnode', 'author', 'whole', 'focus', 'other')
    def model(bits=(True, True, True), variant='baseline'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(hzzq=lambda: 'firstnode', hzzr=lambda: 'secondnode', wa=lambda: 'author',
                      hzzs=lambda: 'whole', hzzt=lambda: 'focus', wh=lambda: 'now')
        if variant in ('other_author', 'other_node', 'other_context', 'other_foreground_scope', 'other_background_scope'):
            name = dict(other_author='wa', other_node='hzzr', other_context='wh', other_foreground_scope='hzzs', other_background_scope='hzzt')[variant]
            values[name] = (lambda: 'elsewhere') if name == 'wh' else (lambda: 'other')
        fg = dict(expected_fg, symbol='r2eg') if variant == 'only_attachment_foreground' else expected_fg
        bg = deepcopy(expected_bg)
        if variant == 'whole_sentence_focus': bg['arguments'][0]['body']['symbol'] = 'r2ei'
        if variant == 'wrong_comparison': bg['arguments'][1]['items'][0]['body']['symbol'] = 'r2ei'
        values.update(
            hznreport=lambda node, author, content, scope, point: bits[0] and (
                node, author, scope, point) == ('secondnode', 'author', 'whole', 'now') and unwrap(content) == fg,
            hzrbgreport=lambda node, author, foreground, background, fs, bs, point: bits[1] and (
                node, author, fs, bs, point) == ('secondnode', 'author', 'whole', 'focus', 'now') and unwrap(foreground) == fg and unwrap(background) == bg,
            ue=lambda first, last, point: bits[2] and (first, last, point) == (
                ('secondnode', 'firstnode', 'now') if variant == 'reversed_order' else ('firstnode', 'secondnode', 'now')))
        return values
    for bits in product((False, True), repeat=3):
        actual = evaluate(doc, model(bits), people, SCENES, True)
        assert actual == [bits[0] and bits[1], bits[2]], (bits, actual)
    contrasts = {}
    for name in ('baseline', 'other_author', 'other_node', 'other_context', 'other_foreground_scope', 'other_background_scope',
                 'only_attachment_foreground', 'whole_sentence_focus', 'wrong_comparison', 'reversed_order'):
        actual = evaluate(doc, model(variant=name), people, SCENES, True)
        wanted = [name in ('baseline', 'reversed_order'), name not in ('other_node', 'other_context', 'reversed_order')]
        assert actual == wanted, (name, actual, wanted)
        contrasts[name] = actual
    for name, position in [('hznreport', 0), ('hzrbgreport', 0), ('ue', 1)]:
        probe = deepcopy(doc); probe['statements'] = [doc['statements'][position]]
        values = model(); values[name] = unknown
        try: evaluate(probe, values, people, SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=8, contrasts=contrasts, unknown_inputs_refused=3,
        attribution_and_text_order_separate=True, world_contents_and_expectation_comparison_unknown=True,
        foreground_and_focus_scope_preserved=True)


@lru_cache(None)
def reused_checks():
    current = catalog(); rows = {}
    for name, roots in COMPONENTS.items():
        path = 'reports/' + name + '-v1.json'; report = read(path); validate_hashes(ROOT, report['source_sha256'])
        old = parse((ROOT / report['document']).read_text(encoding='utf-8'))
        assert closure(old, roots) == closure(current.document, roots)
        dependencies = {d['name'] for d in closure(current.document, roots)}
        rebound = [n for n in dependencies if current.entries[n]['meaning_basis'] not in report['source_sha256']]
        historical = load_catalog(ROOT, 'data/' + name + '-basis-v1.json') if rebound else None
        if historical:
            assert historical.document == old
            assert all(report['source_sha256'][p] == h for p, h in historical.source_sha256.items())
        for n in dependencies:
            basis = current.entries[n]['meaning_basis']
            if n in rebound:
                # A later complete catalog reissued these exact conventions.
                # Compare meaning, argument labels and declaration, not just syntax.
                assert historical.entries[n].keys() == current.entries[n].keys()
                provenance = {'meaning_basis', 'declaration_document'}
                before = {k: v for k, v in historical.entries[n].items() if k not in provenance}
                after = {k: v for k, v in current.entries[n].items() if k not in provenance}
                assert before == after, (path, n)
            else:
                assert report['source_sha256'][basis] == current.source_sha256[basis], (path, n)
        rows[path] = dict(roots=roots, dependency_count=len(dependencies), declarations_and_meaning_conventions_unchanged=True,
                         identical_conventions_reissued_under_new_basis=sorted(rebound))
    first = read(FIRST); validate_hashes(ROOT, first['source_sha256'])
    assert first['decision'] == 'equivalent_under_stated_reading_for_this_sentence'
    assert first['selection'] == selection_binding(current, [51])
    return dict(reports=rows, finite_evidence_reused_without_claiming_new_execution=True,
                first_sentence_review_preserved=True, first_sentence_nonblank_characters=108)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, FIRST}
    paths.update('reports/' + name + '-v1.json' for name in COMPONENTS)
    return dict(status='second_sentence_candidate_with_scoped_attachment_focus', reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[126, 292], text=unit['text'][126:292]),
        selection=selection_binding(catalog(), [11, 12]),
        decision='愛着と不能・原因の内容を同じ各人へ接続し、愛着だけの期待比較を背景として分ける。原文一文としての意味確認は未完。',
        references=[dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036', accessed='2026-10-20',
                         use='第一文に続くErとsie、愛着・現在の不能・weil節を照合。一般化の人物範囲と強調の比較内容は明示した読解候補。'),
                    dict(url='https://grammis.ids-mannheim.de/systematische-grammatik/408', title='IDS grammis Fokuspartikel', accessed='2026-10-20',
                         use='期待に対する尺度上の位置づけと、焦点になり得る範囲の説明。愛着を焦点にし内的定着を比較候補とする今回の選択の唯一性は証明しない。')],
        interpretation_limits=LIMITS, revised_statement_indices=[11, 12], whole_sentence_semantically_verified=False,
        whole_unit_semantically_verified=False, new_verified_sentence_characters=0,
        preserved_first_sentence_characters=108, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-12] == old.document['declarations']
    assert len(new.document['statements']) == len(old.document['statements']) == 52
    changed = [i for i, (a, b) in enumerate(zip(old.document['statements'], new.document['statements'])) if a != b]
    assert changed == [11, 12]
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert set(new.entries) - set(old.entries) == set(MEANINGS) | set(REFERENCES)
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        review = read(path); validate_hashes(ROOT, review['source_sha256'])
        ids = [s['index'] for s in review['selection']['statements']]
        assert not set(ids) & {11, 12} and review['selection'] == selection_binding(old, ids) == selection_binding(new, ids)
    assert len(read(INDEX)['works']['kant-1784']['reviews']) == 12
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(doc, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    assert reading() == read(AUDIT); validate_hashes(ROOT, read(AUDIT)['source_sha256'])
    return dict(new_definitions=9, new_local_references=3, new_general_relations=0, preserved_statements=50,
        revised_statement_indices=[11, 12], authored_statements=52, preserved_review_selections=12,
        reviewed_nonblank_characters=2212, preserved_first_sentence_characters=108, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('scope', scope_checks), ('focus', focus_checks), ('discourse', discourse_checks), ('reused', reused_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    record = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(record['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_affection_sentence.py', 'scripts/check_affection_sentence.py', 'scripts/register_affection_sentence.py',
        'tests/test_affection_sentence.py', 'scripts/compose_scalar_backgrounds.py', 'scripts/compose_grounded_step.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/check_attributed_focus.py',
        'noema/constructed.py', 'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    for name in COMPONENTS: paths.update(read('reports/' + name + '-v1.json')['source_sha256'])
    return dict(status='second_sentence_attachment_focus_candidate_checked', document=FULL, **results,
        alignment=dict(**record['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, preserved_first_sentence_characters=108, new_covered_characters=5,
        new_coverage_explanation='The conjunction and punctuation at positions 156, 158, 159, 160, 291 now join the two formerly separate ranges.',
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
