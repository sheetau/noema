"""Check complete example bindings, additional restrictions and shared questions."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import FunctionValue, SequenceValue, evaluate_document
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_restriction_questions import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, SCALE_BASIS, CODE, MEANINGS, LIMITS, parent, scale, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_demand_candidates as prior

INDEX = 'data/semantic-review-index-v154.json'
REPORT = 'reports/restriction-questions-v1.json'
DOC = 'docs/restriction-questions-v1.md'
CONTEXT = 'presentation'
PEOPLE = (*prior.PEOPLE, 'extra-record', 'extra-person', 'extra-role', 'extra-act')
SCENES = (*prior.SCENES, CONTEXT, 'other-context')
KINDS = (*prior.LABELS, 'extra')
EXTRA = ('r zcontext[] d.r zextra[] a.r ztruth[a a d] c.'
         'd zcontent[person a activity a] e[b point[k ztruth[v person v activity v point]]].'
         'r zselect[d a a ' + ' '.join([CODE] * 5) + '] ' + CODE + '.')


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    if kind == 'questions':
        boundaries = ('r2xs', 'r2xu')
        roots = ['r2xv', 'r2xw']
        query = 'q[k r2xv[k zcontext[]]].q[k r2xw[k zcontext[]]].'
    else:
        boundaries = ('r2wa',) + (('r2xh', 'r2xi', 'r2xj', 'r2xk') if kind == 'bindings' else
                                  ('r2wz', 'r2xd') if kind == 'extra' else ())
        roots = ['r2xp'] if kind == 'rows' else ['r2xr', 'r2xs', 'r2xt', 'r2xu']
        cases = ('zextra',) if kind == 'extra' else (*prior.CASES, 'zextra')
        query = ''.join('q[k ' + n + '[k zcontext[] k ' + case + '[]]].'
                        for case in cases for n in roots)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    extra = 'r zcontext[] d.'
    if kind != 'questions':
        # Its native quotes refer to the existing contents, so append the
        # replacement after those declarations rather than before them.
        doc['declarations'] = [d for d in doc['declarations'] if d['name'] != 'h235a']
        position = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'r2xp')
        prefix = deepcopy(doc)
        prefix.update(declarations=prefix['declarations'][:position], statements=[])
        replacement = parse(format_graph(prefix, 'compact') + EXTRA +
            'd h235a[context d case a record a] ' + CODE +
            '[k zselect[v context v case v record ' +
            ' '.join('r b[p ' + n + ']' for n in (*prior.CONTENTS, 'zcontent')) + ']].')
        doc['declarations'][position:position] = replacement['declarations'][position:]
        roots += ['h235a', 'zcontext', 'zextra']
        extra = ''
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra + query)


def model(doc, variant='baseline', seen=None):
    v = prior.model(doc)
    touches = seen if seen is not None else []

    def context(ctx):
        touches.append(ctx)
        if ctx != CONTEXT:
            raise ValueError('Unknown comparison context')

    def records(ctx, case, record):
        context(ctx)
        if case == 'extra':
            return variant != 'empty_extra' and record == 'extra-record'
        selected = set(prior.RECIPIENTS)
        if case == 'military':
            if variant == 'missing_row':
                selected.remove('second')
            if variant == 'extra_row':
                selected.add('extra-record')
        return case in prior.LABELS and record in selected

    def source(ctx, case, record):
        context(ctx)
        if case not in prior.LABELS or variant == 'wrong_source' and case == 'military':
            return 'extra'
        return case + '-source'

    def person(ctx, case, record):
        context(ctx)
        return 'extra-person' if case == 'extra' or variant == 'wrong_person' and case == 'military' else record

    def role(ctx, case, record):
        context(ctx)
        return 'extra-role' if case == 'extra' or variant == 'wrong_role' and case == 'military' else (
            'role-second' if record == 'second' else 'role-recipient')

    def activity(ctx, case, record):
        context(ctx)
        return 'extra-act' if case not in prior.LABELS or variant == 'wrong_activity' and case == 'military' else case + '-plan'

    def select(ctx, case, record, *codes):
        context(ctx)
        return codes[prior.LABELS.index(case)] if case in prior.LABELS and not (
            variant == 'wrong_code' and case == 'military') else codes[-1]

    def sign(ctx, case, record):
        context(ctx)
        return case != 'extra' and not (variant == 'wrong_polarity' and case == 'military')

    def choices(ctx, case, record, point):
        context(ctx)
        if variant == 'wrong_choice' and case == 'military':
            return False
        return (record, point) == ('extra-record' if case == 'extra' else 'recipient', 'choice')

    def projection(ctx, case, value):
        context(ctx)
        return value

    def public(ctx):
        context(ctx)
        return 'public'

    v.update(zcontext=lambda: CONTEXT, zextra=lambda: 'extra',
             h234t=public, h234u=lambda ctx, case: bool(context(ctx) is None) and case in KINDS,
             h234v=records, h234w=source, h234x=person, h234y=role, h234z=activity, zselect=select,
             h235b=sign, h235c=choices,
             h235d=lambda ctx, case: projection(ctx, case, SequenceValue(('factor', 'outcome'), '"individual"')),
             h235e=lambda ctx, case, variable, state: projection(ctx, case, variable == 'outcome' and state('factor')),
             h235f=lambda ctx, case: projection(ctx, case, 'factor'),
             h235g=lambda ctx, case, state: projection(ctx, case, 'on' if state('factor') else 'off'),
             h235h=lambda ctx, case, on, off: projection(ctx, case, on('factor') and not off('factor')),
             h234l=lambda case, reference: case + '-source' if case in prior.LABELS else 'extra',
             h234m=lambda case, reference: case + '-call' if case in prior.LABELS else 'extra',
             h234q=lambda case: case + '-plan' if case in prior.LABELS else 'extra-act',
             r2wa=lambda case, code: case in prior.LABELS and code.rank == 1 and
                 symbol(code) == prior.CONTENTS[prior.LABELS.index(case)],
             ztruth=lambda person, activity, point: (person, activity, point) == ('extra-person', 'extra-act', 'choice'),
             r2wz=lambda public, reference, point: (public, reference) == ('public', 'reference') and point in ('on', 'off'),
             r2xd=lambda public, reference, left, right: (public, reference) == ('public', 'reference') and
                 (2 if left == 'on' else 1) >= (2 if right == 'on' else 1))

    def required(source, person, role, activity, content, sign, point):
        return (source, person, role, activity, content.rank, symbol(content), sign) == (
            'extra', 'extra-person', 'extra-role', 'extra-act', 1, 'zcontent', False) and (
                point == 'on' or variant == 'extra_still_required' and point == 'off')

    v['h234s'] = required
    return v


@lru_cache(None)
def row_checks():
    doc = fixture('rows')
    rows = {}
    for variant in ('baseline', 'missing_row', 'extra_row', 'wrong_source', 'wrong_person',
                    'wrong_role', 'wrong_activity', 'wrong_code', 'wrong_polarity', 'wrong_choice'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == ([True] * 5 if variant == 'baseline' else [False, True, True, True, True]), (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, all_four_original_demands_and_choices_preserved=True,
                additional_cases_not_forced_into_example_shape=True,
                semantic_boundaries=['r2wa: prior demand-candidates-v1 role/speaker/call/content checks'])


@lru_cache(None)
def binding_checks():
    doc = fixture('bindings')
    seen = []
    v = model(doc, seen=seen)
    received = set()

    def inspect(*args, result):
        (records, sources, people, roles, activities, codes, signs, required, variables, equations,
         factor, worlds, choices, matches, public, reference) = args
        selected = [p for p in PEOPLE if records(p)]
        extra = selected == ['extra-record']
        assert selected == (['extra-record'] if extra else list(prior.RECIPIENTS))
        for record in selected:
            case = 'extra' if extra else activities(record)[:-5]
            assert (sources(record), people(record), roles(record), activities(record), codes(record).rank,
                    symbol(codes(record)), signs(record)) == (
                'extra' if extra else case + '-source', 'extra-person' if extra else record,
                'extra-role' if extra else 'role-' + record, 'extra-act' if extra else case + '-plan',
                1, 'zcontent' if extra else prior.CONTENTS[prior.LABELS.index(case)], not extra)
            assert choices(record, 'choice') == (extra or record == 'recipient')
            received.add(case)
        on = FunctionValue(('individual',), 'truth', lambda item: item == 'factor')
        off = FunctionValue(('individual',), 'truth', lambda item: False)
        assert variables.items == ('factor', 'outcome')
        assert (factor, public, reference, worlds(on), worlds(off)) == ('factor', 'public', 'reference', 'on', 'off')
        assert matches(on, off) and not matches(off, on)
        assert equations('outcome', on) and not equations('outcome', off)
        return result

    for n, result in zip(('r2xh', 'r2xi', 'r2xj', 'r2xk'), (True, False, True, True)):
        v[n] = lambda *args, result=result: inspect(*args, result=result)
    actual = evaluate(doc, v, PEOPLE, SCENES, True)
    assert actual == [True, False, True, True] * 5
    assert received == set(KINDS) and set(seen) == {CONTEXT}
    v['zcontext'] = lambda: 'other-context'
    try:
        evaluate(doc, v, PEOPLE, SCENES, True)
    except ValueError as error:
        assert 'Unknown comparison context' in str(error)
    else:
        raise AssertionError('Question silently used another context')
    return dict(shared_public_reference_and_context=True, all_record_and_model_fields_passed=True,
                other_context_refused=True, semantic_boundaries=['r2xh/r2xi/r2xj/r2xk: native extent comparison checked in enlightenment-extent-v1'])


@lru_cache(None)
def extra_checks():
    doc = fixture('extra')
    rows = {}
    for variant in ('baseline', 'empty_extra', 'extra_still_required'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == ([True, False, True, True] if variant == 'baseline' else [False] * 4), (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, additional_negative_requirement_natively_evaluated=True,
                empty_table_and_incomplete_withdrawal_refused=True,
                semantic_boundaries=['r2wz/r2xd: fixed extent scale checked separately; native demand/choice/intervention/matching here'])


@lru_cache(None)
def question_checks():
    doc = fixture('questions')
    people = (*KINDS, 'outside')
    seen = []
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update({n: (lambda value=value: value) for n, value in zip(prior.CASES, prior.LABELS)})
    def predicate(ctx, case, selected):
        seen.append(ctx)
        return ctx == CONTEXT and case in selected
    v.update(zcontext=lambda: CONTEXT, h234u=lambda ctx, case: predicate(ctx, case, KINDS),
             r2xs=lambda ctx, case: predicate(ctx, case, ('military', 'clergy', 'outside')),
             r2xu=lambda ctx, case: predicate(ctx, case, ('royal', 'extra', 'outside')),
             ha=lambda a, b: a + b, hc=lambda a, b: a < b, hd=lambda truth: Fraction(int(truth)))
    def run():
        results = evaluate_document(doc, individuals=people, situations=(CONTEXT,), primitives=v,
                                    memoize_definitions=True, memoize_expressions=True)
        return [[row[0] for row in q['answers']] for q in results]
    answers = run()
    assert answers == [['military', 'clergy'], ['royal', 'extra']]
    v['r2xs'] = v['r2xu'] = lambda ctx, case: False
    assert run() == [[], []]
    v['r2xu'] = lambda ctx, case: True
    v['h234u'] = lambda ctx, case: case in KINDS and case != 'royal'
    assert run() == [[], []]
    assert set(seen) == {CONTEXT}
    return dict(answer_sets=answers, fifth_candidate_can_answer=True, outside_candidate_excluded=True,
                empty_answers_allowed=True, missing_antecedent_scope_refused=True,
                semantic_boundaries=['r2xs/r2xu classifications are independently checked; native questions and scope here'])


@lru_cache(None)
def quotation_checks():
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, ['r2xv', 'r2xw', 'h232o']), statements=[])
    prefix = format_graph(doc, 'compact')
    for question in ('r2xv', 'r2xw'):
        parse(prefix + 'd zquestion[] i c[g[a]][r c[k ' + question + '[k h232o[]]]].')
        try:
            parse(prefix + 'd zquestion[] i b[g[a]][r b[k ' + question + '[k h232o[]]]].')
        except ValueError as error:
            assert 'strictly lower ranks' in str(error)
        else:
            raise AssertionError('Question disquoting rank-one demand accepted a rank-one outer quote')
    return dict(required_outer_quote_rank=2, both_closed_question_descriptions_well_typed=True,
                lower_rank_quote_refused=True, author_attribution_not_yet_added=True)


@lru_cache(None)
def structure_checks():
    old, new, prior_scale = parent(), catalog(), scale()
    assert old.document['statements'] == new.document['statements']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    for n, e in prior_scale.entries.items():
        for k in ('declaration', 'meaning_ja'):
            assert new.entries[n][k] == e[k], (n, k)
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path in ('data/everywhere-restriction-reading-v1.json', 'data/single-ruler-reading-v1.json',
                 'data/role-commands-reading-v1.json', 'data/heard-prohibition-reading-v1.json'):
        row = json.loads((ROOT / path).read_text(encoding='utf-8'))
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
        validate_hashes(ROOT, row['source_sha256'])
    for path in ('reports/enlightenment-extent-v1.json', 'reports/demand-candidates-v1.json'):
        validate_hashes(ROOT, json.loads((ROOT / path).read_text(encoding='utf-8'))['source_sha256'])
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_statements=70, preserved_whole_unit_reviews=len(reviews),
                added_author_statements=0, new_semantically_reviewed_characters=0, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)


def build_report():
    results = {}
    for name, fn in [('rows', row_checks), ('bindings', binding_checks), ('extra', extra_checks),
                     ('questions', question_checks), ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | set(scale().source_sha256) | {
        INDEX, DOC, 'scripts/compose_restriction_questions.py', 'scripts/check_restriction_questions.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/compose_aligned_influence.py', 'scripts/compose_enlightenment_extent.py',
        'scripts/check_demand_candidates.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'tests/test_restriction_questions.py', 'reports/enlightenment-extent-v1.json',
        'reports/demand-candidates-v1.json', 'data/everywhere-restriction-reading-v1.json',
        'data/single-ruler-reading-v1.json', 'data/role-commands-reading-v1.json',
        'data/heard-prohibition-reading-v1.json'}
    return dict(status='partial_open_restriction_question_contents_checked', document=FULL,
                **results, limitations=LIMITS, whole_sentence_semantically_verified=False,
                whole_unit_semantically_verified=False, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
