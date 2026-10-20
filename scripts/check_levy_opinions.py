"""Check distinct evaluative contents and their own public expression."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_discourse import function_sort
from noema.constructed_semantics import Content, FunctionValue, SequenceValue, Message
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_levy_opinions import ROOT, LIBRARY, BASIS, PRIMITIVES, MEANINGS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

REPORT = 'reports/levy-opinions-v1.json'
DOC = 'docs/levy-opinions-v1.md'
PRIOR = 'reports/civic-example-v1.json'
EVIDENCE = 'data/levy-opinions-lexical-v1.json'
DOMAIN = ('person', 'activity', 'scholar', 'audience', 'levy', 'reader', 'second', 'judgment', 'other')
SCENES = ('reference', 'outcome', 'other')
EXTRA = ''.join('r z' + n + '[] a.' for n in DOMAIN) + 'r zref[] d.r zpoint[] d.'
CRITERION_SORT = json.dumps(function_sort(['individual'], 'content'), sort_keys=True, separators=(',', ':'))


def read(p):
    return json.loads((ROOT / p).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(target):
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, [target]), statements=[])
    names = ('levy',) if target in ('r342', 'r343', 'r344', 'r345') else (
        ('person', 'activity', 'audience', 'levy') if target == 'r346' else
        ('person', 'activity', 'scholar', 'audience', 'levy'))
    args = ' '.join('k z' + n + '[]' for n in names) + ' k zref[]'
    if target == 'r346':
        # Include the closed function families used as arguments.
        doc['declarations'] = closure(catalog().document, [target, 'r344', 'r342'])
        args += ' r[p r344] r[p r342]'
    call = 'k ' + target + '[' + args + ']'
    statement = 'l[' + call + '].' if target in ('r344', 'r345') else 'q[t[' + call + '][k zpoint[]]].'
    return parse(format_graph(doc, 'compact') + EXTRA + statement)


def base(doc):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    for n in DOMAIN:
        v['z' + n] = lambda n=n: n
    v.update(zref=lambda: 'reference', zpoint=lambda: 'outcome')
    return v


def criteria_model(doc, unsuitable=True, unjust=False, variant='baseline'):
    v = base(doc)
    def provider(failed):
        def criteria(subject, reference):
            matched = (subject, reference) == ('other' if variant == 'other_subject' else 'levy',
                'other' if variant == 'other_reference' else 'reference')
            def check(subject):
                if variant == 'unknown_criterion':
                    return unknown()
                return Content(SCENES, tuple(not (failed and matched and
                    subject == ('other' if variant == 'other_evaluated_subject' else 'levy') and
                    point == ('other' if variant == 'other_point' else 'outcome')) for point in SCENES))
            condition = FunctionValue(('individual',), 'content', check)
            passing = FunctionValue(('individual',), 'content', lambda subject: Content(SCENES, (True,) * len(SCENES)))
            items = () if variant == 'empty' else (passing, condition)
            if variant == 'reordered':
                items = (condition, passing)
            if variant == 'duplicate':
                items = (condition, condition)
            return SequenceValue(items, CRITERION_SORT)
        return criteria
    v.update(h245n=provider(unsuitable), h245o=provider(unjust))
    return v


@lru_cache(None)
def content_checks():
    rows = []
    for unsuitable, unjust in product((False, True), repeat=2):
        results = []
        for target in ('r342', 'r343'):
            doc = fixture(target)
            results.extend(evaluate(doc, criteria_model(doc, unsuitable, unjust), DOMAIN, SCENES, True))
        assert results == [unsuitable, unjust]
        rows.append(dict(unsuitable=unsuitable, unjust=unjust, results=results))
    contrasts = {}
    for variant in ('baseline', 'empty', 'other_subject', 'other_reference', 'other_evaluated_subject',
                    'other_point', 'reordered', 'duplicate'):
        results = []
        for target in ('r342', 'r343'):
            doc = fixture(target)
            results.extend(evaluate(doc, criteria_model(doc, True, True, variant), DOMAIN, SCENES, True))
        assert results == [variant in ('baseline', 'reordered', 'duplicate')] * 2, (variant, results)
        contrasts[variant] = results
    return dict(cases=rows, contrasts=contrasts, native_ret=True,
        distinct_condition_families=True, empty_does_not_imply_defect=True)


@lru_cache(None)
def message_checks():
    rows = {}
    for target in ('r344', 'r345'):
        doc = fixture(target)
        for failed in (False, True):
            value = evaluate(doc, criteria_model(doc, failed, failed), DOMAIN, SCENES, True)[0]
            assert isinstance(value, Message) and value.force == 'assert'
            assert value.content == Content(SCENES, (False, failed, False))
            rows[target + ':' + str(failed)] = list(value.content.values)
    return dict(cases=rows, assertion_force_distinct_from_truth=True)


def expression_model(doc, variant='baseline', branches=('unsuitable',)):
    v = base(doc)
    def matches(actual, expected, fields):
        changed = tuple('other' if variant == field else value for value, field in zip(expected, fields))
        return actual == changed
    v.update(
        dg=lambda act, point: variant != 'no_event' and matches((act, point), ('activity', 'outcome'), ('event_activity', 'event_point')),
        f3=lambda person, act, point: matches((person, act, point), ('person', 'activity', 'outcome'),
            ('speaker', 'speaker_activity', 'speaker_point')),
        h6t=lambda audience, recipient, ref: variant != 'empty_audience' and recipient in ('reader', 'second') and
            matches((audience, ref), ('audience', 'reference'), ('recipient_audience', 'recipient_reference')),
        fa=lambda person, judgment, point: variant != 'no_own_judgment' and matches((person, judgment, point),
            ('person', 'judgment', 'outcome'), ('judge', 'judge_judgment', 'judge_point')),
        h245r=lambda act, judgment, point: variant != 'not_expressed' and matches((act, judgment, point),
            ('activity', 'judgment', 'outcome'), ('expression_activity', 'expression_judgment', 'expression_point')),
        h244n=lambda person, act, subject, point: variant != 'neutral_report' and matches((person, act, subject, point),
            ('person', 'activity', 'levy', 'outcome'), ('stance_person', 'stance_activity', 'stance_subject', 'stance_point')))
    def presentation(act, recipient, subject, code, ref, point):
        allowed = {'unsuitable': 'r344', 'unjust': 'r345'}
        return recipient in (('reader',) if variant == 'missing_recipient' else ('reader', 'second')) and any(
            matches((act, subject, symbol(code), code.rank, ref, point),
                ('activity', 'levy', allowed[b], 0, 'reference', 'outcome'),
                ('presentation_activity', 'presentation_subject', 'presentation_family', 'presentation_rank',
                 'presentation_reference', 'presentation_point')) for b in branches)
    def judgment_content(judgment, subject, code, ref, polarity, point):
        allowed = {'unsuitable': 'r342', 'unjust': 'r343'}
        if variant == 'mismatched_content':
            allowed = {'unsuitable': 'r343', 'unjust': 'r342'}
        return polarity == (variant != 'opposite_judgment') and any(matches(
            (judgment, subject, symbol(code), code.rank, ref, point),
            ('judgment', 'levy', allowed[b], 0, 'reference', 'outcome'),
            ('content_judgment', 'content_subject', 'content_family', 'content_rank', 'content_reference', 'content_point'))
            for b in branches)
    v.update(h245p=presentation, h245q=judgment_content,
        aa=lambda p: variant != 'not_person' and p == 'person',
        ca=lambda p, act, ref: variant != 'not_reason_use' and matches((p, act, ref),
            ('person', 'activity', 'reference'), ('reason_person', 'reason_activity', 'reason_reference')),
        cb=lambda p, act, role, ref: matches((p, act, role, ref), ('person', 'activity', 'scholar', 'reference'),
            ('role_person', 'role_activity', 'role_scholar', 'role_reference')),
        cd=lambda role, ref: variant != 'not_scholar' and (role, ref) == ('scholar', 'reference'),
        cc=lambda act, audience, ref: matches((act, audience, ref), ('activity', 'audience', 'reference'),
            ('public_activity', 'public_audience', 'public_reference')),
        ce=lambda audience, ref: variant != 'not_reader_world' and (audience, ref) == ('audience', 'reference'))
    return v


EXPRESSION_CONTRASTS = ('baseline', 'no_event', 'event_activity', 'event_point', 'speaker', 'speaker_activity',
    'speaker_point', 'empty_audience', 'recipient_audience', 'recipient_reference', 'no_own_judgment',
    'judge', 'judge_judgment', 'judge_point', 'not_expressed', 'expression_activity', 'expression_judgment',
    'expression_point', 'neutral_report', 'stance_person', 'stance_activity', 'stance_subject', 'stance_point',
    'missing_recipient', 'presentation_activity', 'presentation_subject', 'presentation_family',
    'presentation_rank', 'presentation_reference', 'presentation_point', 'mismatched_content',
    'opposite_judgment', 'content_judgment', 'content_subject', 'content_family', 'content_rank',
    'content_reference', 'content_point')


@lru_cache(None)
def expression_checks():
    doc, rows = fixture('r346'), {}
    for variant in EXPRESSION_CONTRASTS:
        v = expression_model(doc, variant)
        assert v['h245n'] is unknown
        actual = evaluate(doc, v, DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual[0]
    return dict(contrasts=rows, native_own_judgment_and_expression=True,
        same_fixed_recipients_subject_reference_point=True, quoted_content_not_evaluated=True)


@lru_cache(None)
def public_checks():
    doc, rows = fixture('r347'), {}
    for branches in ((), ('unsuitable',), ('unjust',), ('unsuitable', 'unjust')):
        v = expression_model(doc, branches=branches)
        assert v['h245n'] is unknown and v['h245o'] is unknown
        actual = evaluate(doc, v, DOMAIN, SCENES, True)
        assert actual == [bool(branches)], (branches, actual)
        rows[str(branches)] = actual[0]
    contrasts = {}
    for variant in ('not_person', 'not_reason_use', 'reason_person', 'reason_activity', 'reason_reference',
        'role_person', 'role_activity', 'role_scholar', 'role_reference', 'not_scholar',
        'public_activity', 'public_audience', 'public_reference', 'not_reader_world',
        'no_own_judgment', 'not_expressed', 'mismatched_content'):
        actual = evaluate(doc, expression_model(doc, variant), DOMAIN, SCENES, True)
        assert actual == [False], (variant, actual)
        contrasts[variant] = actual[0]
    return dict(cases=rows, contrasts=contrasts, native_r2zi_and_expression_branches=True,
        either_or_both_opinions=True, truth_receipt_and_written_channel_not_required=True)


@lru_cache(None)
def unknown_checks():
    rows = []
    for name in ('h245p', 'h245q', 'h245r', 'fa', 'h244n', 'ce'):
        doc = fixture('r347'); v = expression_model(doc); v[name] = unknown
        try:
            evaluate(doc, v, DOMAIN, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
        rows.append(name)
    for target in ('r342', 'r343'):
        doc = fixture(target)
        try:
            evaluate(doc, criteria_model(doc, variant='unknown_criterion'), DOMAIN, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(target)
        rows.append(target + ':unknown_criterion')
    return dict(unknown_inputs_refused=rows)


@lru_cache(None)
def structure_checks():
    new, old = catalog(), parent()
    assert not new.document['statements']
    for n, e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration'] == old.entries[n]['declaration'] and e['meaning_ja'] == old.entries[n]['meaning_ja'], n
    validate_hashes(ROOT, read(PRIOR)['source_sha256'])
    for p, s in build().items():
        assert (ROOT / p).read_text(encoding='utf-8') == s, p
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    evidence = read(EVIDENCE)
    validate_hashes(ROOT, {s['raw_archive']: s['raw_sha256'] for s in evidence['sources']})
    return dict(new_definitions=len(MEANINGS), new_primitives=len(PRIMITIVES), new_semantic_reviews=0,
        active_manuscript_unchanged=True, roundtrips=True, archived_lexical_sources_hashes_verified=True,
        lexical_candidate_not_certified_equivalence=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p, s in build().items():
        write_exact(ROOT / p, s)


def build_report():
    results = {}
    for name, fn in [('content', content_checks), ('message', message_checks), ('expression', expression_checks),
                     ('public', public_checks), ('unknown', unknown_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set(parent().source_sha256) | {
        DOC, PRIOR, EVIDENCE, 'scripts/compose_levy_opinions.py', 'scripts/check_levy_opinions.py',
        'tests/test_levy_opinions.py', 'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='own_public_levy_opinions_candidate', document=LIBRARY, **results,
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
