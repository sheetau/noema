"""Check four anchored demands, excluded personal choices and universal scope."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_everywhere_restriction import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_command_alternatives as commands

INDEX = 'data/semantic-review-index-v152.json'
REPORT = 'reports/everywhere-restriction-v1.json'
AUDIT = 'data/everywhere-restriction-reading-v1.json'
DOC = 'docs/everywhere-restriction-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/public-reversal-reading-v1/page-484.jpg'
PRIOR = 'reports/single-ruler-v1.json'
SENTENCES = 'data/single-ruler-reading-v1.json'
THREE = 'data/role-commands-reading-v1.json'
FIRST = 'data/heard-prohibition-reading-v1.json'
CASES = ('military', 'fiscal', 'clergy', 'royal')
NODES = ('h233m', 'h233n', 'h233o', 'h234i')
EXTRA = 'r zp[] a.r zcase[] a.r zcall[] a.r zr[] d.r zt[] d.'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    boundaries = {
        'anchors': ('r2to', 'r2tp', 'sp', 'r2tq', 'r2uk', 'r2ul'),
        'restriction': ('r2ux',),
        'all_cases': ('r2uv', 'r2uy'),
    }.get(kind, ())
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    if kind == 'contents':
        old = commands.fixture('combined')
        extra = [d for d in old['declarations'] if d['name'].startswith('z')]
        code = next(d for d in old['declarations'] if d['name'] == 'h233b')
        replacement = parse('p:r zobey[a a d d] c.'
                            'd r2ud[source a person a reference d] e['
                            'b point[k zobey[v source v person v reference v point]]].')
        lookup = {d['name']: d for d in replacement['declarations']}
        lookup['h233b'] = code
        doc['declarations'] = extra + [replacement['declarations'][0]] + [
            lookup.get(d['name'], d) for d in doc['declarations']]
        roots = ['r2ux', *[d['name'] for d in extra]]
        doc.update(declarations=closure(doc, roots), statements=[])
        query = ''.join('q[k r2ux[k ' + n + '[] k zs[] k zp[] k zr[] k zt[]]].' for n in NODES)
        return parse(format_graph(doc, 'compact') + query)
    roots = {'anchors': ['r2uv'], 'restriction': ['r2uy'],
             'all_cases': ['r2uz'], 'discourse': ['r2va']}[kind]
    doc.update(declarations=closure(doc, roots), statements=[])
    query = {
        'anchors': 'q[k r2uv[k zcase[] k zp[] k zcall[] r[k zr[]] k zt[]]].',
        'restriction': 'q[k r2uy[k zcase[] k zp[] k zcall[] k zr[] k zt[]]].',
        'all_cases': 'q[t[k r2uz[]][k zt[]]].',
        'discourse': 'q[k r2va[]].',
    }[kind]
    return parse(format_graph(doc, 'compact') + EXTRA + query)


def base(doc, case='military'):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(zp=lambda: 'source', zcase=lambda: case, zcall=lambda: 'call',
             zr=lambda: 'reference', zt=lambda: 'reference', wa=lambda: 'author')
    v.update({n: (lambda value=value: value) for n, value in zip(NODES, CASES)})
    return v


@lru_cache(None)
def anchor_checks():
    doc = fixture('anchors')
    people = (*CASES, 'source', 'other', 'author', 'call', 'army', 'treasury', 'church')
    rows = {}
    for i, case in enumerate(CASES):
        rows[case] = {}
        for variant in ('baseline', 'wrong_role', 'wrong_quarter', 'wrong_speaker', 'wrong_call',
                        'wrong_reference', 'wrong_command', 'wrong_positive', 'not_a_world_ruler'):
            v = base(doc, case)
            quarters = ('army', 'treasury', 'church')
            v.update({n: (lambda value=value: value) for n, value in zip(('h233i', 'h233j', 'h233k'), quarters)})
            v.update(
                h232s=lambda author, ref, quarter: (author, ref) == ('author', 'reference') and quarter in quarters,
                h232t=lambda quarter, p, ref: (p, ref) == ('source', 'reference')
                    and i < 3 and quarter == quarters[(i + (variant == 'wrong_quarter')) % 3],
                r2tq=lambda speaker, call, observer, ref, positive, command, point: i < 3 and
                    (speaker, call, observer, symbol(ref), symbol(positive), symbol(command), point) == (
                        'other' if variant == 'wrong_speaker' else 'source',
                        'other' if variant == 'wrong_call' else 'call', 'author',
                        'zt' if variant == 'wrong_reference' else 'zr',
                        ('r2tg', 'r2th', 'r2ti')[(i + (variant == 'wrong_positive')) % 3],
                        commands.COMMANDS[(i + (variant == 'wrong_command')) % 3], 'reference'),
                r2uk=lambda p, ref, point: (p, ref, point) == ('source', 'reference', 'reference')
                    and i == 3 and variant != 'not_a_world_ruler',
                r2ul=lambda p, call, ref, point: (p, call, symbol(ref), point) == (
                    'other' if variant == 'wrong_speaker' else 'source',
                    'other' if variant == 'wrong_call' else 'call',
                    'zt' if variant == 'wrong_reference' else 'zr', 'reference') and i == 3)
            for j, name in enumerate(('r2to', 'r2tp', 'sp')):
                v[name] = lambda p, point, j=j: (p, point) == ('source', 'reference') and (
                    j == ((i + 1) % 3 if variant == 'wrong_role' else i))
            actual = evaluate(doc, v, people, ('reference', 'later'), True)
            irrelevant = (i == 3 and variant in ('wrong_role', 'wrong_quarter', 'wrong_command', 'wrong_positive')
                          or i < 3 and variant == 'not_a_world_ruler')
            assert actual == [variant == 'baseline' or irrelevant], (case, variant, actual)
            rows[case][variant] = actual
    return dict(contrasts=rows, same_preceding_case_speaker_event_and_command=True,
                semantic_boundaries=['r2to/r2tp/sp/r2tq: unchanged prior role and command constructions',
                                     'r2uk/r2ul: prior single-ruler role and native ranked speech checks'])


@lru_cache(None)
def content_checks():
    doc = fixture('contents')
    people = (*commands.PEOPLE, *CASES)
    rows = []
    for bits in product((False, True), repeat=5):
        reasons, drill, payment, belief, obeys = bits
        v = commands.model(doc, flags=bits[:4])
        v.update({n: (lambda value=value: value) for n, value in zip(NODES, CASES)})
        v['zobey'] = lambda source, p, ref, point: obeys and (
            source, p, ref, point) == ('second', 'first', 'reference', 'later')
        actual = evaluate(doc, v, people, commands.SCENES, True)
        assert actual == [not reasons and drill, not reasons and payment, not reasons and belief, obeys], (bits, actual)
        rows.append(dict(choices_and_obedience=bits, result=actual))
    v = commands.model(doc)
    v.update({n: (lambda value=value: value) for n, value in zip(NODES, CASES)})
    v['zobey'] = lambda source, p, ref, point: (source, p, ref, point) == ('first', 'first', 'reference', 'later')
    assert evaluate(doc, v, people, commands.SCENES, True) == [True, True, True, False]
    return dict(matrix=rows, ruler_permission_not_turned_into_prohibition=True, same_obedience_source=True,
                semantic_boundaries=['r2ud: native content wrapper around zobey for selection checks; full-description coverage and finite diagnostic preserved in free-choice-obedience report'])


@lru_cache(None)
def restriction_checks():
    doc = fixture('restriction')
    people = (*CASES, 'source', 'other', 'recipient', 'outsider', 'call', 'othercall')
    scenes = ('reference', 'candidate', 'unavailable')
    rows = {}
    for case in CASES:
        rows[case] = {}
        for variant in ('baseline', 'all_choices_comply', 'no_free_candidate', 'only_other_person_violates',
                        'only_unavailable_choice_violates', 'outsider_choice', 'wrong_baseline', 'wrong_source'):
            v = base(doc, case)
            v.update(
                h232u=lambda call, ref, p: (call, ref) == ('call', 'reference') and p in ('recipient', 'other'),
                h233p=lambda source, ref, p: (source, ref) == ('source', 'reference') and p in ('recipient', 'other'),
                h234n=lambda c, p, ref, baseline, alternative: (c, p, ref, baseline, alternative) == (
                    case, 'outsider' if variant == 'outsider_choice' else 'recipient', 'reference',
                    'candidate' if variant == 'wrong_baseline' else 'reference', 'candidate')
                    and variant != 'no_free_candidate',
                r2ux=lambda c, source, p, ref, point: not (
                    variant != 'all_choices_comply' and (c, source, p, ref, point) == (
                        case, 'other' if variant == 'wrong_source' else 'source',
                        'other' if variant == 'only_other_person_violates' else 'recipient', 'reference',
                        'unavailable' if variant == 'only_unavailable_choice_violates' else 'candidate')))
            actual = evaluate(doc, v, people, scenes, True)
            assert actual == [variant == 'baseline'], (case, variant, actual)
            rows[case][variant] = actual
    return dict(contrasts=rows, genuinely_excluded_same_person_choice_required=True,
                actual_violation_or_total_loss_not_required=True,
                semantic_boundaries=['r2ux: separately checked content selection, with its prior r2ud coverage limitation'])


@lru_cache(None)
def universal_checks():
    doc = fixture('all_cases')
    people = (*CASES, 'source', 'other', 'call', 'othercall', 'outside')
    rows = []
    def values(bits, variant='baseline'):
        v = base(doc)
        v.update(
            ha=lambda a, b: a + b, hc=lambda a, b: a < b, hd=lambda truth: Fraction(int(truth)),
            h232v=lambda: 'reference',
            h234l=lambda c, ref: 'other' if variant == 'wrong_speaker' and c == 'royal' else 'source',
            h234m=lambda c, ref: 'othercall' if variant == 'wrong_call' and c == 'royal' else 'call',
            r2uv=lambda c, p, call, ref, point: c in CASES and (p, call, symbol(ref), point) == (
                'source', 'call', 'h232v', 'reference') and not (variant == 'unmatched_case' and c == 'royal'),
            r2uy=lambda c, p, call, ref, point: c in CASES and bits[CASES.index(c)]
                and (p, call, ref, point) == ('source', 'call', 'reference', 'reference'),
            zt=lambda: 'later' if variant == 'wrong_point' else 'reference')
        if variant == 'duplicate_case':
            v['h233n'] = lambda: 'military'
        return v
    for bits in product((False, True), repeat=4):
        actual = evaluate(doc, values(bits), people, ('reference', 'later'), True)
        assert actual == [all(bits)], (bits, actual)
        rows.append(dict(restrictions=bits, result=actual))
    contrasts = {}
    for variant in ('wrong_speaker', 'wrong_call', 'unmatched_case', 'wrong_point', 'duplicate_case'):
        actual = evaluate(doc, values((True,) * 4, variant), people, ('reference', 'later'), True)
        assert actual == [False], (variant, actual)
        contrasts[variant] = actual
    return dict(matrix=rows, contrasts=contrasts, all_four_distinct_cases_required=True,
                outside_world_not_universally_restricted=True,
                semantic_boundaries=['r2uv/r2uy: separate anchor and excluded-choice checks'])


@lru_cache(None)
def discourse_checks():
    doc = fixture('discourse')
    people = (*CASES, 'sentence', 'author')
    rows = {}
    for variant in ('baseline', 'missing_claim', 'wrong_content', 'wrong_context',
                    'only_three_antecedents', 'different_antecedent_order', 'wrong_predecessor'):
        v = base(doc)
        v.update(
            h234o=lambda: 'sentence', h232o=lambda: 'context',
            hzon=lambda node, author, content, ctx: (node, author, ctx) == (
                'sentence', 'author', 'other' if variant == 'wrong_context' else 'context')
                and content.rank == 1 and symbol(content) == ('r2uo' if variant == 'wrong_content' else 'r2uz')
                and variant != 'missing_claim',
            h234p=lambda node, author, antecedents, ctx: (node, author, ctx) == ('sentence', 'author', 'context')
                and tuple(antecedents.items) == (CASES[:3] if variant == 'only_three_antecedents' else
                                           tuple(reversed(CASES)) if variant == 'different_antecedent_order' else CASES),
            ue=lambda first, second, ctx: (first, second, ctx) == (
                'clergy' if variant == 'wrong_predecessor' else 'royal', 'sentence', 'context'))
        actual = evaluate(doc, v, people, ('context', 'other'), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, attributed_deictic_scope_and_order=True,
                world_and_alternative_contents_not_executed=True, semantic_boundaries=[])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    pieces = [
        ('Hier ', ['r2us', 'h234p', 'r2va'], '直前の四つの事例を同じ順序と範囲で指す。'),
        ('ist ', ['r2uz', 'r2va'], '叙述上の現在での制限を著者へ帰属する。'),
        ('überall ', ['r2ut', 'r2uz', 'hh'], '異なる四事例の全てに量化する。'),
        ('Einschränkung der Freiheit.', ['r2uv', 'r2uw', 'r2ux', 'r2uy', 'h234n'],
         '同じ指示の宛先の選択肢に、要求が適合するものとして残さない候補がある。')]
    clauses, cursor = [], 537
    for phrase, names, interpretation in pieces:
        assert unit['text'][cursor:cursor + len(phrase)] == phrase
        clauses.append(dict(range=[cursor, cursor + len(phrase)], text=phrase, definitions=names, reading=interpretation))
        cursor += len(phrase)
    assert cursor == 581
    text = unit['text'][537:581]
    count = sum(not c.isspace() for c in text)
    assert count == 39
    paths = (FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, IMAGE, PRIOR, SENTENCES, THREE, FIRST)
    return dict(status='everywhere_restriction_sentence_reviewed_under_explicit_reading', reviewer='assistant_review',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[537, 581], text=text),
                clauses=clauses, selection=selection_binding(catalog(), [69]), interpretation=LIMITS,
                unresolved=[], decision='equivalent_under_stated_reading_for_this_sentence',
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                source_nonblank_characters=count, newly_reviewed_sentence_characters=count,
                preserved_reviewed_sentence_characters=457, paragraph_reviewed_sentence_characters=496,
                semantic_equivalence_automatically_proved=False,
                original_page=dict(path=IMAGE, page=484, visually_inspected=True),
                references=['https://korpora.org/Kant/aa08/037.html'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert old.document['statements'] == new.document['statements'][:69]
    assert len(new.document['statements']) == 70
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in ((SENTENCES, [68]), (THREE, [65, 66, 67]), (FIRST, [64])):
        assert read(path)['selection'] == selection_binding(new, indices)
    assert read(FIRST)['first_sentence_recheck']['selection'] == selection_binding(new, [63])
    for path in (PRIOR, SENTENCES, THREE, FIRST):
        validate_hashes(ROOT, read(path)['source_sha256'])
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_whole_unit_reviews=len(reviews), preserved_statements=69, added_statements=1,
                preserved_reviewed_sentence_characters=457, new_reviewed_sentence_characters=39,
                old_meanings_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('anchors', anchor_checks), ('contents', content_checks), ('restriction', restriction_checks),
                     ('universal', universal_checks), ('discourse', discourse_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, IMAGE, PRIOR, SENTENCES, THREE, FIRST,
        'reports/free-choice-obedience-v1.json', 'reports/command-alternatives-v1.json',
        'scripts/compose_everywhere_restriction.py', 'scripts/check_everywhere_restriction.py',
        'tests/test_everywhere_restriction.py', 'scripts/check_command_alternatives.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='everywhere_restriction_under_explicit_reading', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], statements=[69], status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
