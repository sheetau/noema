"""Verify quoted question attribution, focus scope and the bounded reading."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_question_discourse import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.compose_demand_candidates import CASES

INDEX = 'data/semantic-review-index-v155.json'
REPORT = 'reports/question-discourse-v1.json'
AUDIT = 'data/question-discourse-reading-v1.json'
DOC = 'docs/question-discourse-v1.md'
EVIDENCE = 'data/question-discourse-evidence-v1.json'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/public-reversal-reading-v1/page-484.jpg'
PRIOR = 'reports/restriction-questions-v1.json'
PREVIOUS = 'data/everywhere-restriction-reading-v1.json'
PEOPLE = ('author', 'previous', 'first', 'second', 'answer', 'other')
SCENES = ('presentation', 'other')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    boundaries = ('r2xs', 'r2xt', 'r2xu') if kind in ('properties', 'questions') else ()
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    roots = {'properties': ['r2xx', 'r2xy', 'r2xz'], 'questions': ['r2ya', 'r2yb'],
             'discourse': ['r2yc', 'r2yd']}[kind]
    doc.update(declarations=closure(doc, roots), statements=[])
    extra = ''
    if kind == 'properties':
        extra = 'r zcase[] a.r zpoint[] d.'
        queries = ''.join('q[t[k ' + n + '[k zcase[]]][k zpoint[]]].' for n in roots)
    elif kind == 'questions':
        queries = ''.join('q[k ' + n + '[]].' for n in roots)
    else:
        queries = 'q[k r2yc[]].q[k r2yd[]].'
    return parse(format_graph(doc, 'compact') + extra + queries)


@lru_cache(None)
def content_checks():
    properties = fixture('properties')
    rows = {}
    effects = {'harm': (True, False, False), 'neutral': (False, True, False),
               'help': (False, True, True), 'mixed': (True, False, False)}
    for case, flags in effects.items():
        v = {d['name']: unknown for d in properties['declarations'] if d['kind'] == 'primitive'}
        v.update(h232o=lambda: 'presentation', zcase=lambda: case)
        for n, result in zip(('r2xs', 'r2xt', 'r2xu'), flags):
            v[n] = lambda context, item, result=result: context == 'presentation' and item == case and result
        for point in SCENES:
            v['zpoint'] = lambda: point
            actual = evaluate(properties, v, tuple(effects), SCENES, True)
            assert actual == list(flags), (case, point, actual)
        rows[case] = actual
    questions = fixture('questions')
    people = ('military', 'fiscal', 'clergy', 'royal', 'extra', 'outside')
    v = {d['name']: unknown for d in questions['declarations'] if d['kind'] == 'primitive'}
    v.update({n: (lambda value=value: value) for n, value in zip(CASES, people[:4])})
    v.update(h232o=lambda: 'presentation',
             h234u=lambda context, item: context == 'presentation' and item != 'outside',
             r2xs=lambda context, item: context == 'presentation' and item in ('military', 'clergy', 'outside'),
             r2xu=lambda context, item: context == 'presentation' and item in ('royal', 'extra', 'outside'),
             ha=lambda a, b: a + b, hc=lambda a, b: a < b, hd=lambda truth: Fraction(int(truth)))
    def answers():
        result = evaluate_document(questions, individuals=people, situations=SCENES, primitives=v,
                                   memoize_definitions=True, memoize_expressions=True)
        return [[x[0] for x in q['answers']] for q in result]
    actual = answers()
    assert actual == [['military', 'clergy'], ['royal', 'extra']]
    v['r2xs'] = v['r2xu'] = lambda *args: False
    assert answers() == [[], []]
    return dict(properties=rows, closed_question_answers=actual, empty_answers_allowed=True,
                same_fixed_context_for_properties_and_questions=True,
                semantic_boundaries=['r2xs/r2xt/r2xu: same-candidate requirement, intervention and scale checked by restriction-questions-v1'])


def discourse_model(doc, variant='baseline'):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(wa=lambda: 'other' if variant == 'wrong_author' else 'author',
             h232o=lambda: 'other' if variant == 'wrong_context' else 'presentation',
             h234o=lambda: 'previous', h235n=lambda: 'first',
             h235o=lambda: 'first' if variant == 'collapsed_nodes' else 'second', h235p=lambda: 'answer')

    def question(node, author, code, context):
        name = ('r2yb' if variant == 'wrong_first_question' else 'r2ya') if node == 'first' else (
            'r2ya' if variant == 'wrong_second_question' else 'r2yb')
        return node in ('first', 'second') and (author, code.rank, symbol(code), context) == ('author', 2, name, 'presentation')

    def contrast(node, author, antecedent, content, code, context):
        return (node, author, antecedent, content.rank, symbol(content), code.rank, symbol(code), context) == (
            'first', 'author', 'other' if variant == 'wrong_antecedent' else 'previous', 1,
            'r2xx' if variant == 'wrong_antecedent_content' else 'r2uz', 2, 'r2ya', 'presentation')

    def replacement(node, author, rejected, positive, code, context):
        return (node, author, rejected.rank, symbol(rejected), positive.rank, symbol(positive), code.rank,
                symbol(code), context) == ('second', 'author', 2,
            'r2xy' if variant == 'wrong_rejected_property' else 'r2xx', 2,
            'r2xx' if variant == 'wrong_replacement_property' else 'r2xz', 2, 'r2yb', 'presentation')

    def conjecture(node, author, focus, code, context):
        return variant != 'missing_conjecture' and (
            node, author, focus.rank, symbol(focus), code.rank, symbol(code), context) == (
                'second', 'author', 2, 'r2xy' if variant == 'wrong_conjecture_scope' else 'r2xz', 2, 'r2yb', 'presentation')

    def emphasis(node, author, baseline, focus, code, context):
        return variant != 'missing_emphasis' and (
            node, author, baseline.rank, symbol(baseline), focus.rank, symbol(focus), code.rank, symbol(code), context) == (
                'second', 'author', 2, 'r2xx' if variant == 'wrong_baseline' else 'r2xy', 2,
                'r2xy' if variant == 'wrong_emphasis_scope' else 'r2xz', 2, 'r2yb', 'presentation')

    def order(first, second, context):
        allowed = {('previous', 'first'), ('first', 'second'), ('second', 'answer')}
        if variant == 'missing_first_order':
            allowed.remove(('previous', 'first'))
        if variant == 'reversed_second_order':
            allowed.remove(('first', 'second'))
            allowed.add(('second', 'first'))
        return context == 'presentation' and (first, second) in allowed

    v.update(h235i=question, h235j=contrast, h235k=replacement, h235l=conjecture, h235m=emphasis,
             ue=order, hzcs=lambda author, question, response, context: (
                 author, response, context) == (
                     'author', 'other' if variant == 'wrong_response' else 'answer', 'presentation') and
                 question in ('first', 'second'))
    return v


@lru_cache(None)
def discourse_checks():
    doc = fixture('discourse')
    rows = {}
    first_only = {'wrong_first_question', 'wrong_antecedent', 'wrong_antecedent_content', 'missing_first_order'}
    both_wrong = {'wrong_author', 'wrong_context', 'wrong_response'}
    variants = ('baseline', *sorted(first_only), *sorted(both_wrong), 'wrong_second_question',
                'wrong_rejected_property', 'wrong_replacement_property', 'missing_conjecture',
                'wrong_conjecture_scope', 'missing_emphasis', 'wrong_baseline', 'wrong_emphasis_scope',
                'reversed_second_order', 'collapsed_nodes')
    for variant in variants:
        actual = evaluate(doc, discourse_model(doc, variant), PEOPLE, SCENES, True)
        wanted = [True, True] if variant == 'baseline' else [False, True] if variant in first_only else (
            [False, False] if variant in both_wrong else [True, False])
        assert actual == wanted, (variant, actual)
        rows[variant] = actual
    for name in ('h235i', 'h235j', 'h235k', 'h235l', 'h235m', 'hzcs'):
        v = discourse_model(doc)
        v[name] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError('Missing discourse evidence was accepted: ' + name)
    return dict(contrasts=rows, unknown_discourse_evidence_refused=6,
                questions_and_world_contents_not_executed=True, conjecture_and_focus_scopes_preserved=True,
                same_author_context_and_response=True, semantic_boundaries=[])


@lru_cache(None)
def quotation_checks():
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, ['r2ya', 'r2yb', 'r2xx', 'r2xy', 'r2xz']), statements=[])
    prefix = format_graph(doc, 'compact')
    for n in ('r2ya', 'r2yb'):
        parse(prefix + 'd zquote[] i c[g[a]][r c[k ' + n + '[]]].')
        try:
            parse(prefix + 'd zquote[] i b[g[a]][r b[k ' + n + '[]]].')
        except ValueError as error:
            assert 'strictly lower ranks' in str(error)
        else:
            raise AssertionError(n)
    for n in ('r2xx', 'r2xy', 'r2xz'):
        parse(prefix + 'd zquote[] i c[h[a] e][r c[p ' + n + ']].')
    return dict(question_and_focus_descriptions_rank_two=True, lower_question_rank_refused=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    pieces = [
        (582, [
            ('Welche Einschränkung ', ['r2xq', 'r2xv', 'r2ya'], '先行四事例を含み追加候補も許す同じ制限範囲について問う。'),
            ('aber ', ['h235j', 'r2yc'], '直前の制限の存在を受け、その効果を問い分ける対照。先行叙述は否定しない。'),
            ('ist der Aufklärung ', ['r2ln', 'r2xf', 'r2xg', 'h234t', 'h232v'], '同じ啓蒙・対象公衆・基準への効果。'),
            ('hinderlich?', ['r2xs', 'r2xx', 'r2ya', 'h235i'], '対応する背景で進行を妨げうる候補を、著者が問いとして提示する。')]),
        (639, [
            ('welche ', ['r2xw', 'r2yb'], '省略された制限を同じ候補範囲から受ける。'),
            ('nicht, ', ['r2xt', 'r2xu', 'r2xy', 'r2yb'], '同じ候補について先行する阻害を否定する。未評価を非阻害へ補わない。'),
            ('sondern ', ['h235k', 'r2yd'], '同じ回答対象の阻害を否定側、促進を肯定側に置く対置。'),
            ('ihr ', ['r2ln', 'r2xf', 'r2xg', 'r2yb'], '第一問と同じ啓蒙を指す。'),
            ('wohl ', ['h235l', 'r2xz', 'r2yd'], '促進側の見込みを推量的に提出する留保。'),
            ('gar ', ['h235m', 'r2xy', 'r2xz', 'r2yd'], '単なる非阻害を越える促進を取り立てる強調。'),
            ('beförderlich?', ['r2xu', 'r2xz', 'r2yb', 'h235i'], '同じ候補の非阻害かつ促進を問い、答えの存在や真理は断言しない。')])]
    clauses = []
    for start, parts in pieces:
        cursor = start
        for text, names, interpretation in parts:
            assert unit['text'][cursor:cursor + len(text)] == text
            clauses.append(dict(range=[cursor, cursor + len(text)], text=text, definitions=names, reading=interpretation))
            cursor += len(text)
        assert cursor == (638 if start == 582 else 687)
    text = unit['text'][582:687]
    assert sum(not ch.isspace() for ch in text) == 92
    assert unit['text'][690:980].startswith('Ich antworte:') and unit['text'][690:980].endswith('hindern.')
    paths = (FULL, BASIS, ANNOTATIONS, DOC, EVIDENCE, INVENTORY, IMAGE, PRIOR, PREVIOUS)
    return dict(status='restriction_question_pair_reviewed_under_explicit_reading', reviewer='assistant_review',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[582, 687], text=text),
                sentence_ranges=[[582, 638], [639, 687]], clauses=clauses,
                selection=selection_binding(catalog(), [70, 71]), interpretation=LIMITS, unresolved=[],
                response_reference=dict(range=[690, 980], node='h235p', content_reviewed_here=False),
                decision='equivalent_under_stated_reading_for_the_two_questions',
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                source_nonblank_characters=92, newly_reviewed_sentence_characters=92,
                preserved_reviewed_sentence_characters=496, paragraph_reviewed_sentence_characters=588,
                semantic_equivalence_automatically_proved=False,
                original_page=dict(path=IMAGE, page=484, visually_inspected=True),
                references=[read(EVIDENCE)['source']['url'], *[r['url'] for r in read(EVIDENCE)['lexical_evidence']]],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:70] == old.document['statements']
    assert len(new.document['statements']) == 72
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in ((PREVIOUS, [69]), ('data/single-ruler-reading-v1.json', [68]),
                          ('data/role-commands-reading-v1.json', [65, 66, 67]),
                          ('data/heard-prohibition-reading-v1.json', [64])):
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
    first = read('data/heard-prohibition-reading-v1.json')['first_sentence_recheck']
    assert first['selection'] == selection_binding(new, [63])
    validate_hashes(ROOT, read(PRIOR)['source_sha256'])
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_statements=70, added_statements=2, preserved_whole_unit_reviews=len(reviews),
                preserved_reviewed_sentence_characters=496, new_reviewed_sentence_characters=92,
                old_meanings_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('contents', content_checks), ('discourse', discourse_checks),
                     ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, EVIDENCE, INVENTORY, IMAGE, PRIOR, PREVIOUS,
        'scripts/compose_question_discourse.py', 'scripts/check_question_discourse.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/compose_demand_candidates.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'tests/test_question_discourse.py', 'data/single-ruler-reading-v1.json',
        'data/role-commands-reading-v1.json', 'data/heard-prohibition-reading-v1.json'}
    return dict(status='restriction_question_pair_under_explicit_reading', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], statements=[70, 71], status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
