"""Check negative directive content, same-event hearing and fixed social quarters."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_heard_prohibition import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, LIMITS, CONTEXT_MAPPING,
    parent, corrected, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts import check_enlightenment_requirement as previous

INDEX = 'data/semantic-review-index-v147.json'
REPORT = 'reports/heard-prohibition-v1.json'
AUDIT = 'data/heard-prohibition-reading-v1.json'
DOC = 'docs/heard-prohibition-v1.md'
INVENTORY = previous.INVENTORY
IMAGE = previous.IMAGE
FIRST = previous.AUDIT
PRIOR = [previous.REPORT, 'reports/freedom-comparison-v1.json']
PEOPLE = ('author', 'speaker', 'otherspeaker', 'call', 'othercall', 'first', 'second', 'quarter', 'otherquarter')
SCENES = ('now', 'elsewhere')
EXTRA = 'r zp[] a.r zs[] a.r zo[] a.r zcall[] a.r zr[] d.r zt[] d.'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    if kind == 'sides':
        d = next(d for d in doc['declarations'] if d['name'] == 'r2tc')
        d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']]); d.pop('body')
    roots = dict(command=['r2tb'], hearing=['r2tc'], sides=['r2td'], discourse=['r2sz', 'r2tf'])[kind]
    doc.update(declarations=closure(doc, roots), statements=[])
    query = {
        'command': ('q[t[o[c[k r2tb[k zr[]]][k zp[]]]][k zt[]]].'
                    'q[u[e[c[k r2tb[k zr[]]][k zp[]]][j s[c[k r2ta[k zr[]]][k zp[]]]]]].'),
        'hearing': 'q[k r2tc[k zs[] k zcall[] k zo[] r[k zr[]] k zt[]]].',
        'sides': 'q[k r2td[k zo[] r[k zr[]] k zt[]]].',
        'discourse': 'q[k r2sz[]].q[k r2tf[]].',
    }[kind]
    return parse(format_graph(doc, 'compact') + (EXTRA if kind != 'discourse' else '') + query)


def base(doc):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(zp=lambda: 'first', zs=lambda: 'speaker', zo=lambda: 'author',
             zcall=lambda: 'call', zr=lambda: 'now', zt=lambda: 'now')
    return v


@lru_cache(None)
def command_checks():
    doc = fixture('command')
    rows = {}
    for variant in ('none_done', 'target_done', 'other_person_done', 'nonargument_done',
                    'second_target_done', 'empty_scope'):
        v = base(doc)
        v.update(ca=lambda p, a, r: r == 'now' and p in ('first', 'second')
                     and a in ('call', 'othercall', 'quarter') and variant != 'empty_scope',
                 h232p=lambda a, r: r == 'now' and a in ('call', 'othercall'),
                 cg=lambda p, a, t: t == 'now' and (
                     variant == 'target_done' and (p, a) == ('first', 'call') or
                     variant == 'other_person_done' and (p, a) == ('second', 'call') or
                     variant == 'nonargument_done' and (p, a) == ('first', 'quarter') or
                     variant == 'second_target_done' and (p, a) == ('first', 'othercall')))
        actual = evaluate(doc, v, PEOPLE, SCENES, True)
        assert actual == [variant in ('none_done', 'other_person_done', 'nonargument_done'), True], (variant, actual)
        rows[variant] = actual
    for missing in ('ca', 'h232p', 'cg'):
        w = dict(v); w[missing] = unknown
        try:
            evaluate(doc, w, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, native_negative_directive=True, directive_distinct_from_assertion=True,
                scope_fixed_before_execution=True, unknown_inputs_refused=3)


def described(desc, name='r2tb'):
    return desc.rank == 0 and json.loads(desc.syntax) == dict(
        kind='apply', function=dict(kind='function_ref', symbol=name),
        arguments=[dict(kind='call', symbol='zr', arguments=[])])


def hearing_model(doc, variant='baseline'):
    v = base(doc)
    calls = ('call', 'othercall')
    humans = ('author', 'speaker', 'otherspeaker', 'first', 'second')
    def message(call, receiver, subject, desc, point, receipt=False):
        expected_observer = 'first' if variant == 'receipt_wrong_observer' else 'author'
        expected_subject = 'first' if variant == 'second_subject_switched' else subject
        return point == 'now' and call in calls and (
            receiver == expected_observer if receipt else receiver in ('first', 'second')) and (
            subject in ('first', 'second') and subject == expected_subject and
            described(desc, 'r2ta' if variant == 'wrong_message' else 'r2tb')) and not (
                variant == 'only_first_addressed' and not receipt and receiver == 'second' or
                variant == 'missing_receipt' and receipt)
    v.update(
        aa=lambda p: p in humans and not (variant == 'nonhuman_recipient' and p == 'second'),
        dg=lambda a, t: t == 'now' and a in calls and variant != 'not_occurring',
        f3=lambda p, a, t: t == 'now' and (p, a) in {('speaker', 'call'), ('otherspeaker', 'othercall')}
            and variant != 'wrong_presenter',
        h232r=lambda a, t: t == 'now' and a in calls and variant != 'not_a_call',
        h232q=lambda p, a, t: (p, t) == ('author', 'now') and a in (
            ('othercall',) if variant == 'heard_other_event' else calls) and variant != 'only_read',
        h232u=lambda a, r, p: r == 'now' and a in calls and p in (
            () if variant == 'empty_audience' else ('first',) if variant == 'singular_audience' else ('first', 'second')),
        f2=lambda *args: message(*args),
        h6e=lambda *args: message(*args, receipt=True),
        h6g=lambda p, subject, desc, t: (p, t) == ('author', 'now') and
            subject in ('first', 'second') and described(desc) and variant != 'not_understood')
    return v


@lru_cache(None)
def hearing_checks():
    doc = fixture('hearing')
    rows = {}
    for variant in ('baseline', 'not_occurring', 'wrong_presenter', 'not_a_call', 'heard_other_event',
                    'only_read', 'empty_audience', 'singular_audience', 'nonhuman_recipient',
                    'only_first_addressed', 'missing_receipt', 'receipt_wrong_observer',
                    'second_subject_switched', 'wrong_message', 'not_understood'):
        actual = evaluate(doc, hearing_model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    v = hearing_model(doc); v.update(zs=lambda: 'otherspeaker', zcall=lambda: 'othercall')
    assert evaluate(doc, v, PEOPLE, SCENES, True) == [True]
    for missing in ('h232q', 'h232r', 'h232u', 'f2', 'h6e', 'h6g'):
        v = hearing_model(doc); v[missing] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, same_speaker_event_listener_message_and_point=True,
                observer_need_not_be_addressee=True, plural_addressees_not_filtered_by_receipt=True,
                quoted_execution_and_norm_inputs_unknown=True, native_r2tc=True,
                second_quarter_witness_also_natively_checked=True, unknown_inputs_refused=6)


@lru_cache(None)
def sides_checks():
    doc = fixture('sides')
    rows = {}
    for variant in ('baseline', 'empty_sides', 'one_side', 'missing_other_call', 'wrong_quarter',
                    'wrong_observer', 'wrong_reference', 'wrong_point'):
        v = base(doc)
        v.update(
            h232s=lambda o, r, q: (o, r) == ('author', 'now') and q in (
                () if variant == 'empty_sides' else ('quarter',) if variant == 'one_side' else ('quarter', 'otherquarter')),
            h232t=lambda q, s, r: r == 'now' and (q, s) in (
                {('quarter', 'speaker')} if variant == 'wrong_quarter' else
                {('quarter', 'speaker'), ('otherquarter', 'otherspeaker')}),
            r2tc=lambda s, call, o, ref, t: (o, t) == (
                'first' if variant == 'wrong_observer' else 'author',
                'elsewhere' if variant == 'wrong_point' else 'now') and
                json.loads(ref.syntax) == dict(kind='call', symbol='zt' if variant == 'wrong_reference' else 'zr', arguments=[]) and
                (s, call) in ({('speaker', 'call')} if variant == 'missing_other_call' else
                             {('speaker', 'call'), ('otherspeaker', 'othercall')}))
        actual = evaluate(doc, v, PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    v['zt'] = lambda: 'elsewhere'
    assert evaluate(doc, v, PEOPLE, SCENES, True) == [False]
    return dict(contrasts=rows, each_fixed_quarter_requires_its_own_witness=True,
                same_closed_reference_and_observer=True, current_point_matches_reference=True,
                semantic_boundaries=['r2tc: separate native hearing checks cover both witnesses'])


@lru_cache(None)
def discourse_checks():
    doc = fixture('discourse')
    people = (*previous.NODES.values(), 'heard')
    rows = {}
    for variant in ('baseline', 'old_paragraph_context', 'wrong_observer_claim',
                    'reverse_contrast', 'missing_second_claim', 'reverse_text_order'):
        v = previous.discourse_model(doc)
        old_attribution, old_order, old_contrast = v['hzon'], v['ue'], v['h222q']
        v.update(h232o=lambda: 'elsewhere' if variant == 'old_paragraph_context' else 'context',
                 hzp3=unknown, h232w=lambda: 'heard',
                 hzon=lambda n, a, c, x: (
                     (n, a, x) == ('heard', 'author', 'context') and
                     previous.quoted_call(c, 'r2ss' if variant == 'wrong_observer_claim' else 'r2te')
                     and variant != 'missing_second_claim'
                     if n == 'heard' else old_attribution(n, a, c, x)),
                 ue=lambda f, s, x: (
                     x == 'context' and (f, s) == (('heard', 'sentence') if variant == 'reverse_text_order'
                                                 else ('sentence', 'heard'))
                     if 'heard' in (f, s) else old_order(f, s, x)),
                 h222q=lambda n, a, f, c1, s, c2, axis, x: (
                     (n, a, f, s, x) == ('heard', 'author',
                         'heard' if variant == 'reverse_contrast' else 'sentence',
                         'sentence' if variant == 'reverse_contrast' else 'heard', 'context')
                     and previous.quoted_call(c1, 'r2ss') and previous.quoted_call(c2, 'r2te')
                     if n == 'heard' else old_contrast(n, a, f, c1, s, c2, axis, x)))
        actual = evaluate(doc, v, people, ('context', 'elsewhere'), True)
        assert actual == ([False, False] if variant == 'old_paragraph_context' else
                          [True, variant == 'baseline']), (variant, actual)
        rows[variant] = actual
    # Verify the entire correction, including its context, independently of names.
    expected = deepcopy(parent().document)
    expected['declarations'] += [
        d for d in catalog().document['declarations'] if d['name'] in PRIMITIVES]
    expected['declarations'].extend(corrected())
    expected = parse(format_graph(expected, 'compact'))
    for d in expected['declarations'][-3:]:
        assert d == catalog().entries[d['name']]['declaration']
    return dict(contrasts=rows, first_sentence_content_preserved_with_correct_context=True,
                old_paragraph_context_not_used=True, quoted_hearing_and_commands_not_executed=True,
                semantic_boundaries=[])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    text = unit['text'][215:273]
    pieces = [
        ('Nun ', ['h232v', 'r2td', 'r2te'], '叙述上の現在の場面への転換。'),
        ('höre ich ', ['wa', 'h232q', 'h6e', 'h6g', 'r2tc'], '著者を観察者とし、同じ声を聴覚で捉え内容を取得・理解する。'),
        ('aber ', ['r2tf', 'h222q'], '先の自由の要件の提示と禁止の声を対比する。'),
        ('von allen Seiten ', ['h232s', 'h232t', 'r2td'], '固定した全ての社会的方面に、そこからの呼び声を要求する。'),
        ('rufen: ', ['dg', 'f3', 'h232r', 'r2tc'], '話者が実際に生じる同じ呼び声の提示者となる。'),
        ('räsonnirt nicht!', ['ca', 'h232p', 'r2ta', 'r2tb', 'h232u'], '複数の宛先に、本人の理性による言語的検討を行わないよう命ずる。'),
    ]
    clauses, start = [], 215
    for phrase, definitions, interpretation in pieces:
        assert unit['text'][start:start + len(phrase)] == phrase
        clauses.append(dict(range=[start, start + len(phrase)], text=phrase,
                            definitions=definitions, reading=interpretation))
        start += len(phrase)
    assert start == 273
    count = sum(not c.isspace() for c in text)
    first = read(FIRST)
    paths = {FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, IMAGE, FIRST, *PRIOR}
    return dict(status='heard_prohibition_sentence_reviewed_under_explicit_reading', reviewer='assistant_review',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[215, 273], text=text),
                clauses=clauses, selection=selection_binding(catalog(), [64]),
                interpretation=LIMITS, unresolved=[], decision='equivalent_under_stated_reading_for_this_sentence',
                first_sentence_recheck=dict(original_record=FIRST, source=first['source'],
                    selection=selection_binding(catalog(), [63]), source_nonblank_characters=183,
                    replaced_selection=first['selection'], change=CONTEXT_MAPPING,
                    decision='equivalent_under_stated_reading_with_corrected_paragraph_context',
                    reason='原刊の段落境界と旧hzp3の意味規約を確認し、u0012の提示をh232oへ訂正した。元の全句対応・採用解釈は保持し、実行検査で前段落の文脈の混入を拒否する。原記録は更新せず、訂正後の選択を新たに確認した。'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                source_nonblank_characters=count, newly_reviewed_sentence_characters=count,
                paragraph_reviewed_sentence_characters=183 + count,
                semantic_equivalence_automatically_proved=False,
                original_page=dict(path=IMAGE, page=484, visually_inspected=True),
                references=[dict(url='https://korpora.org/Kant/aa08/036.html', accessed='2026-10-21',
                                 use='当文と先行する自由の要件の対比。'),
                            dict(url='https://korpora.org/Kant/aa08/037.html', accessed='2026-10-21',
                                 use='後続の社会的諸方面の例と公的・私的使用の区別。'),
                            dict(url='https://www.duden.de/rechtschreibung/raesonieren', accessed='2026-10-21',
                                 use='古い語義の理性的に述べ推論する用法。カントの読解の独立証明とはしない。')],
                remaining_unit_work='[274,5190)の各方面の具体的な命令、一人の君主の対照、問いと公私使用の定義・例。',
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:63] == old.document['statements'][:63]
    assert new.document['statements'][63]['body']['symbol'] == 'r2sz'
    assert len(new.document['statements']) == 65
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path in [*PRIOR, FIRST]:
        validate_hashes(ROOT, read(path)['source_sha256'])
    assert read(FIRST)['selection'] != selection_binding(new, [63])
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_whole_unit_reviews=len(reviews), added_definitions=len(MEANINGS),
                added_basic_relations=6, added_source_references=3, preserved_statements=63,
                corrected_first_sentence_index=63, added_statement_index=64, authored_statements=65,
                old_definitions_and_evidence_unchanged=True, first_sentence_rechecked=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('command', command_checks), ('hearing', hearing_checks), ('sides', sides_checks),
                     ('discourse', discourse_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, IMAGE, FIRST, *PRIOR, 'scripts/compose_heard_prohibition.py',
        'scripts/check_heard_prohibition.py', 'tests/test_heard_prohibition.py',
        'scripts/compose_public_first_sentence.py', 'scripts/check_enlightenment_requirement.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='heard_prohibition_sentence_reviewed_under_explicit_reading', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                newly_reviewed_sentence_characters=read(AUDIT)['source_nonblank_characters'],
                corrected_first_sentence_characters=183,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
