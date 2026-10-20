"""Validate exclusive requirements, unchanged referents and the whole first sentence."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_enlightenment_requirement import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, FAMILY, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v146.json'
REPORT = 'reports/enlightenment-requirement-v1.json'
AUDIT = 'data/enlightenment-requirement-reading-v1.json'
DOC = 'docs/enlightenment-requirement-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/public-reversal-reading-v1/page-484.jpg'
PRIOR = ['reports/public-topics-v1.json', 'reports/freedom-comparison-v1.json',
         'reports/public-first-sentence-v1.json', 'reports/fourth-paragraph-v1.json']
PEOPLE = ('public', 'otherpublic', 'focus', 'extra', 'outside')
SCENES = ('reference', 'elsewhere')
EXTRA = f'r zpick[a d {FAMILY} {FAMILY}] {FAMILY}.r zg[] a.r zr[] d.'
NODES = dict(h232h='sentence', h232i='freedom', h232j='minimum', h232k='publicuse',
             h232l='oldgoal', h232m='thisgoal', h232n='requirement', h226h='slow',
             h227w='priorend', wa='author')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    if kind == 'discourse':
        doc.update(declarations=closure(doc, ['r2sw']), statements=[])
        return parse(format_graph(doc, 'compact') + 'q[k r2sw[]].')
    extras = parse('p:' + EXTRA)['declarations']
    replacement = parse(format_graph(dict(doc, statements=[]), 'compact') + EXTRA +
                        f'd zprovider[item a reference d] {FAMILY}['
                        'k zpick[v item v reference r b[p r2sl] r b[p r2ln]]'
                        '].')['declarations'][-1]
    replacement['name'] = 'h232f'
    for index, d in enumerate(doc['declarations']):
        if d['name'] == 'h232f':
            doc['declarations'][index] = replacement
        elif d['name'] == 'r2sn':
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc['declarations'] = extras + doc['declarations']
    roots = ['r2sq'] if kind == 'requirement' else ['r2sr', 'r2so', 'r2ss']
    doc.update(declarations=closure(doc, [*roots, *[d['name'] for d in extras]]), statements=[])
    questions = ('q[k r2sq[k zg[] k zr[]]].' if kind == 'requirement' else
                 'q[t[k r2sr[]][k zr[]]].q[t[k r2so[]][k zr[]]].q[t[k r2ss[]][k zr[]]].')
    return parse(format_graph(doc, 'compact') + questions)


def requirement_model(doc, variant='baseline', flags=(True, True)):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    def required(item, goal, public, reference):
        assert goal.rank == 1
        if symbol(goal) != ('r2sl' if variant == 'wrong_goal' else 'r2ln'):
            return False
        expected_reference = 'elsewhere' if variant == 'wrong_reference' else 'reference'
        if reference != expected_reference or public not in ('public', 'otherpublic'):
            return False
        if variant == 'other_public_only' and public != 'otherpublic':
            return False
        if not flags[0] or variant == 'second_public_fails' and public == 'otherpublic':
            return False
        return item in (('extra',) if variant == 'extra_only' else
                        () if variant == 'no_requirements' else
                        ('focus', 'extra') if variant in ('additional_requirement', 'duplicate_content') else
                        ('focus', 'outside') if variant == 'requirement_outside_selected_names' else ('focus',))
    def content(item, reference, focus, extra):
        assert (symbol(focus), symbol(extra), focus.rank, extra.rank) == ('r2sl', 'r2ln', 1, 1)
        if variant == 'wrong_focus_content' and item == 'focus':
            return extra
        return focus if item == 'focus' or variant == 'duplicate_content' and item == 'extra' else extra
    values.update(zg=lambda: 'public', zr=lambda: 'reference',
                  h232e=required, zpick=content,
                  h222e=lambda public, reference: reference == 'reference'
                      and public in ('public', 'otherpublic') and variant != 'empty_publics',
                  r2sn=lambda public, reference: flags[1] and reference == 'reference'
                      and not (variant == 'second_comparison_fails' and public == 'otherpublic'))
    return values


@lru_cache(None)
def requirement_checks():
    doc = fixture('requirement')
    rows = {}
    for variant in ('baseline', 'duplicate_content', 'additional_requirement', 'extra_only',
                    'no_requirements', 'requirement_outside_selected_names', 'wrong_focus_content',
                    'wrong_goal', 'wrong_reference', 'other_public_only'):
        actual = evaluate(doc, requirement_model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant in ('baseline', 'duplicate_content')], (variant, actual)
        rows[variant] = actual
    for missing in ('h232e', 'zpick'):
        values = requirement_model(doc); values[missing] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, native_exclusive_quantification=True,
                no_requirements_and_additional_requirements_rejected=True, unknown_inputs_refused=2,
                goal_and_condition_quoted_without_execution=True)


@lru_cache(None)
def composition_checks():
    doc = fixture('composition')
    rows = {}
    for flags in product((False, True), repeat=2):
        actual = evaluate(doc, requirement_model(doc, flags=flags), PEOPLE, SCENES, True)
        assert actual == [*flags, all(flags)], (flags, actual)
        rows[str(flags)] = actual
    for variant, expected in (
        ('empty_publics', [False, False, False]),
        ('second_public_fails', [False, True, False]),
        ('second_comparison_fails', [True, False, False]),
    ):
        actual = evaluate(doc, requirement_model(doc, variant), PEOPLE, SCENES, True)
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    old, new = parent(), catalog()
    for name in ('r2ln', 'r2sl', 'r2sn', 'r2so', 'h222e'):
        assert old.entries[name] == new.entries[name]
    return dict(contrasts=rows, same_nonempty_scope_for_both_clauses=True,
                previous_goal_and_permission_and_minimum_unchanged=True,
                semantic_boundaries=['r2sn: native minimum and identity tested in reports/freedom-comparison-v1.json'])


def quoted_call(desc, name):
    return desc.rank == 1 and json.loads(desc.syntax) == dict(kind='call', symbol=name, arguments=[])


def discourse_model(doc, variant='baseline'):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    for name, value in NODES.items():
        values[name] = lambda value=value: value
    values['hzp3'] = lambda: 'context'
    if variant == 'same_explanation_nodes':
        values['h232k'] = lambda: 'minimum'
    def denotes(node, author, referent, scope, context):
        expected = 'r2ln' if node in ('oldgoal', 'thisgoal') else 'r2sl'
        if variant == 'different_goal' and node == 'thisgoal':
            expected = 'r2sl'
        if variant == 'different_freedom' and node == 'publicuse':
            expected = 'r2ln'
        return (author, scope, context) == ('author',
            'priorend' if variant == 'wrong_scope' else 'sentence',
            'elsewhere' if variant == 'wrong_context' else 'context') and (
            referent.rank == 1 and symbol(referent) == expected)
    def order(first, second, context):
        edges = {('freedom', 'minimum'), ('minimum', 'publicuse'), ('oldgoal', 'thisgoal'),
                 ('priorend', 'sentence')}
        if variant == 'reverse_explanation':
            edges.remove(('minimum', 'publicuse')); edges.add(('publicuse', 'minimum'))
        if variant == 'cyclic_anaphora':
            edges.add(('thisgoal', 'oldgoal'))
        if variant == 'missing_paragraph_order':
            edges.remove(('priorend', 'sentence'))
        return context == 'context' and (first, second) in edges
    def clarifies(first, second, author, scope, context):
        edges = {('freedom', 'minimum'), ('minimum', 'publicuse')}
        if variant == 'no_restriction_explanation':
            edges.remove(('freedom', 'minimum'))
        if variant == 'no_public_use_explanation':
            edges.remove(('minimum', 'publicuse'))
        return (author, scope, context) == ('author', 'sentence', 'context') and (first, second) in edges
    def attribution(node, author, content, context):
        expected = dict(sentence='r2ss', requirement='r2sr', minimum='r2so')
        return (author, context) == ('author', 'context') and quoted_call(content, expected[node]) and not (
            variant == 'missing_whole_claim' and node == 'sentence' or
            variant == 'missing_requirement_claim' and node == 'requirement' or
            variant == 'missing_minimum_claim' and node == 'minimum')
    def contrast(node, author, first, c1, second, c2, axis, context):
        return (node, author, first, second, context) == ('sentence', 'author',
            'requirement' if variant == 'reverse_contrast' else 'slow',
            'slow' if variant == 'reverse_contrast' else 'requirement', 'context') and (
            quoted_call(c1, 'r2pt') and quoted_call(c2, 'r2sr') and symbol(axis) == 'h4l')
    values.update(h232g=denotes, ue=order, ibbclarifies=clarifies, hzon=attribution, h222q=contrast)
    return values


@lru_cache(None)
def discourse_checks():
    doc = fixture('discourse')
    rows = {}
    for variant in ('baseline', 'different_goal', 'different_freedom', 'wrong_scope', 'wrong_context',
                    'same_explanation_nodes', 'reverse_explanation', 'cyclic_anaphora',
                    'no_restriction_explanation', 'no_public_use_explanation', 'missing_paragraph_order',
                    'missing_whole_claim', 'missing_requirement_claim', 'missing_minimum_claim', 'reverse_contrast'):
        actual = evaluate(doc, discourse_model(doc, variant), tuple(NODES.values()), ('context', 'elsewhere'), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for missing in ('h232g', 'ibbclarifies', 'hzon', 'h222q'):
        values = discourse_model(doc); values[missing] = unknown
        try:
            evaluate(doc, values, tuple(NODES.values()), ('context', 'elsewhere'), True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, same_goal_and_freedom_referents=True, explanation_not_just_word_order=True,
                world_requirement_permission_and_harm_inputs_unknown=True, semantic_boundaries=[],
                unknown_inputs_refused=4)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    text = unit['text'][:214]
    pieces = [
        ('Zu ', ['r2sq', 'h232e'], '同じ啓蒙へ向けて供給する要件の話題設定。'),
        ('dieser Aufklärung ', ['r2sv', 'h232g', 'r2ln'], '前段落と同じ公衆の同じ啓蒙を指す。'),
        ('aber ', ['r2sw', 'h222q', 'r2pt'], '先行する遅い到達の叙述と要件の少なさを対比する。'),
        ('wird nichts erfordert als ', ['r2sp', 'r2sq', 'r2sr'], '焦点の要件があり、他内容の追加供給要件がない。'),
        ('Freiheit; ', ['r2sl', 'r2su', 'r2sq'], '後続句と同じ公的理性使用の自由を要件の内容とする。'),
        ('und zwar ', ['r2su', 'r2st', 'ibbclarifies'], '同じ自由を後句で限定し説明する。'),
        ('die unschädlichste ', ['r2sn', 'r2sm', 'rce', 'h232d'], 'その自由を同じ害の評価で最小とする。同順位を許す。'),
        ('unter allem, was nur Freiheit heißen mag, ', ['h232b', 'h232c', 'r2sm', 'rcd'], '自由と呼びうる全種類を固定した比較範囲として採る。'),
        ('nämlich die: ', ['r2su', 'r2st', 'h232g'], '同じ自由を公的使用の内容によって特定する。'),
        ('von seiner Vernunft ', ['ca', 'zzo'], '同じ本人の自らの理性を使う活動記述。'),
        ('in allen Stükken ', ['r2sj', 'h232a', 'h227z'], '全主題を固定し、各読者と各主題の活動記述を結ぶ。'),
        ('öffentlichen Gebrauch zu machen.', ['zzo', 'cd', 'cc', 'ce', 'r2sl', 'hzna'],
         '学識者として読者世界へ向ける使用。全活動の規範的な許可維持を自由の内容とする。'),
    ]
    clauses, start = [], 0
    for phrase, definitions, interpretation in pieces:
        assert text[start:start + len(phrase)] == phrase, (start, phrase)
        clauses.append(dict(range=[start, start + len(phrase)], text=phrase,
                            definitions=definitions, reading=interpretation))
        start += len(phrase)
    assert start == 214 and sum(not c.isspace() for c in text) == 183
    paths = {FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, IMAGE, *PRIOR}
    return dict(status='enlightenment_requirement_sentence_reviewed_under_explicit_reading',
                reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[0, 214], text=text),
                clauses=clauses, selection=selection_binding(catalog(), [63]),
                interpretation=LIMITS, unresolved=[],
                decision='equivalent_under_stated_reading_for_this_sentence',
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                source_nonblank_characters=183, newly_reviewed_sentence_characters=183,
                paragraph_reviewed_sentence_characters=183, semantic_equivalence_automatically_proved=False,
                original_page=dict(path=IMAGE, page=484, visually_inspected=True),
                references=[dict(url='https://korpora.org/Kant/aa08/036.html', accessed='2026-10-21',
                                 use='前段落の啓蒙・遅さとの接続、当文の要件限定・比較・説明。'),
                            dict(url='https://korpora.org/Kant/aa08/037.html', accessed='2026-10-21',
                                 use='後続する公的使用の著者の定義。')],
                remaining_unit_work='[215,5190)の後続の禁止の声、問い、公私の使用の定義と職務の例を確認する。',
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:-1] == old.document['statements']
    assert len(new.document['statements']) == 64
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path in PRIOR:
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
                added_basic_relations=3, added_source_references=7, preserved_statements=63,
                added_statement_index=63, authored_statements=64, old_definitions_unchanged=True,
                sentence_nonblank_characters=183, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('requirement', requirement_checks), ('composition', composition_checks),
                     ('discourse', discourse_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, IMAGE, *PRIOR, 'scripts/compose_enlightenment_requirement.py',
        'scripts/check_enlightenment_requirement.py', 'tests/test_enlightenment_requirement.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='enlightenment_requirement_sentence_reviewed_under_explicit_reading',
                document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                newly_reviewed_sentence_characters=183, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
