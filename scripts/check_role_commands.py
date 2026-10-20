"""Check role identity, same-call delivery, examples and nonfactive attribution."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_role_commands import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_heard_prohibition import described

INDEX = 'data/semantic-review-index-v149.json'
REPORT = 'reports/role-commands-v1.json'
AUDIT = 'data/role-commands-reading-v1.json'
DOC = 'docs/role-commands-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/public-reversal-reading-v1/page-484.jpg'
PRIOR = 'reports/command-alternatives-v1.json'
SENTENCES = 'data/heard-prohibition-reading-v1.json'
COMMANDS = ('r2tk', 'r2tl', 'r2tm')
POSITIVE = ('r2tg', 'r2th', 'r2ti')
CONTENTS = ('r2ts', 'r2tt', 'r2tu')
CLAIMS = ('r2tw', 'r2tx', 'r2ty')
EXTRA = 'r zp[] a.r zs[] a.r zo[] a.r zcall[] a.r zr[] d.r zt[] d.'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind, index=0):
    doc = deepcopy(catalog().document)
    boundaries = ('r2to', 'r2tp', 'sp', 'r2tq') if kind == 'examples' else ()
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    roots = dict(roles=['r2to', 'r2tp'], delivery=['r2tq', POSITIVE[index], COMMANDS[index]],
                 examples=list(CONTENTS), discourse=list(CLAIMS))[kind]
    doc.update(declarations=closure(doc, roots), statements=[])
    query = {
        'roles': 'q[k r2to[k zp[] k zt[]]].q[k r2tp[k zp[] k zt[]]].',
        'delivery': ('q[k r2tq[k zs[] k zcall[] k zo[] r[k zr[]] r[p ' +
                     POSITIVE[index] + '] r[p ' + COMMANDS[index] + '] k zt[]]].'),
        'examples': ''.join('q[t[k ' + n + '[]][k zt[]]].' for n in CONTENTS),
        'discourse': ''.join('q[k ' + n + '[]].' for n in CLAIMS),
    }[kind]
    return parse(format_graph(doc, 'compact') + EXTRA + query)


def base(doc):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(zp=lambda: 'person', zs=lambda: 'speaker', zo=lambda: 'author',
             zcall=lambda: 'call', zr=lambda: 'now', zt=lambda: 'now')
    return v


def refused(doc, v, missing, people, scenes):
    w = dict(v); w[missing] = unknown
    try:
        evaluate(doc, w, people, scenes, True)
    except ValueError as error:
        assert 'Unknown' in str(error), str(error)
    else:
        raise AssertionError('Accepted unknown ' + missing)


@lru_cache(None)
def role_checks():
    doc = fixture('roles')
    people = ('person', 'other', 'role', 'otherrole', 'institution', 'otherinstitution')
    scenes = ('now', 'later')
    rows = {}
    for variant in ('baseline', 'nonhuman', 'no_role', 'not_appointed', 'other_holder',
                    'other_appointed_role', 'other_institution', 'wrong_point',
                    'not_military', 'not_officer_rank', 'not_public_finance', 'not_councillor'):
        v = base(doc)
        v.update(
            aa=lambda p: p == 'person' and variant != 'nonhuman',
            hzwn=lambda p, r, t: (p, r, t) == (
                'other' if variant == 'other_holder' else 'person', 'role', 'now') and variant != 'no_role',
            hzxf=lambda p, r, inst, t: (p, r, inst, t) == (
                'person', 'otherrole' if variant == 'other_appointed_role' else 'role',
                'otherinstitution' if variant == 'other_institution' else 'institution',
                'later' if variant == 'wrong_point' else 'now') and variant != 'not_appointed',
            h233d=lambda inst, t: (inst, t) == ('institution', 'now') and variant != 'not_military',
            h233e=lambda r, inst, t: (r, inst, t) == ('role', 'institution', 'now') and variant != 'not_officer_rank',
            h233f=lambda inst, t: (inst, t) == ('institution', 'now') and variant != 'not_public_finance',
            h233g=lambda r, inst, t: (r, inst, t) == ('role', 'institution', 'now') and variant != 'not_councillor')
        actual = evaluate(doc, v, people, scenes, True)
        expected = ([True, True] if variant == 'baseline' else
                    [False, True] if variant in ('not_military', 'not_officer_rank') else
                    [True, False] if variant in ('not_public_finance', 'not_councillor') else [False, False])
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    # Both roles may belong to one person; no artificial disjointness is imposed.
    return dict(contrasts=rows, same_holder_role_institution_and_point=True,
                current_performance_not_required=True, semantic_boundaries=[])


def delivery_model(doc, index, variant='baseline'):
    v = base(doc)
    command, positive = COMMANDS[index], POSITIVE[index]
    def matches(desc, name):
        return described(desc, name)
    def message(call, receiver, subject, desc, point, receipt=False):
        if matches(desc, 'r2tb'):
            allowed = True
        else:
            allowed = matches(desc, COMMANDS[(index + 1) % 3] if variant == 'wrong_command' else command)
            allowed &= variant != 'missing_combined_command'
            if variant == 'positive_in_other_call':
                return call == 'other' and allowed
        return (allowed and call == 'call' and point == 'now' and subject in ('first', 'second')
                and (receiver == 'author' if receipt else receiver == subject)
                and not (variant == 'second_not_addressed' and not receipt and receiver == 'second'))
    v.update(
        aa=lambda p: p in ('author', 'speaker', 'first', 'second'),
        dg=lambda a, t: (a, t) == ('call', 'now') and variant != 'not_occurring',
        f3=lambda p, a, t: (p, a, t) == (
            'other' if variant == 'different_presenter' else 'speaker', 'call', 'now'),
        h232r=lambda a, t: (a, t) == ('call', 'now'),
        h232q=lambda o, a, t: (o, a, t) == ('author', 'call', 'now') and variant != 'not_heard',
        h232u=lambda a, r, p: (a, r) == ('call', 'now') and p in (
            ('first',) if variant == 'singular_audience' else ('first', 'second')),
        f2=lambda *args: message(*args),
        h6e=lambda *args: message(*args, receipt=True),
        h6g=lambda o, p, d, t: (o, t) == ('author', 'now') and p in ('first', 'second')
            and (matches(d, 'r2tb') or matches(d, command) and variant != 'positive_not_understood'),
        h233h=lambda a, s, p, negative, affirmative, t: (
            a, s, t) == ('call', 'other' if variant == 'other_speaker_replaces' else 'speaker', 'now')
            and p in (('first',) if variant == 'only_first_replacement' else ('first', 'second'))
            and matches(negative, positive if variant == 'reverse_replacement' else 'r2ta')
            and matches(affirmative, POSITIVE[(index + 1) % 3] if variant == 'wrong_positive' else positive)
            and variant != 'mere_juxtaposition')
    return v


@lru_cache(None)
def delivery_checks():
    people = ('author', 'speaker', 'first', 'second', 'call', 'other')
    scenes = ('now', 'later')
    rows = {}
    for index, command in enumerate(COMMANDS):
        doc = fixture('delivery', index)
        rows[command] = {}
        for variant in ('baseline', 'missing_combined_command', 'wrong_command', 'positive_in_other_call',
                        'second_not_addressed', 'not_occurring', 'different_presenter', 'not_heard',
                        'singular_audience', 'positive_not_understood', 'other_speaker_replaces',
                        'only_first_replacement', 'reverse_replacement', 'wrong_positive', 'mere_juxtaposition'):
            actual = evaluate(doc, delivery_model(doc, index, variant), people, scenes, True)
            assert actual == [variant == 'baseline'], (command, variant, actual)
            rows[command][variant] = actual
        for missing in ('h233h', 'h232q', 'f2'):
            refused(doc, delivery_model(doc, index), missing, people, scenes)
    return dict(contrasts=rows, native_same_call_and_plural_audience=True,
                same_speaker_negative_positive_replacement=True, execution_and_belief_inputs_unknown=True,
                unknown_inputs_refused=9, semantic_boundaries=[])


@lru_cache(None)
def example_checks():
    doc = fixture('examples')
    people = ('author', 'officer', 'finance', 'clergy', 'call', 'army', 'treasury', 'church', 'other')
    scenes = ('now', 'later')
    rows = {}
    for variant in ('baseline', 'role_mismatch', 'quarter_mismatch', 'outside_prior_quarters',
                    'speaker_mismatch', 'observer_mismatch', 'positive_mismatch', 'command_mismatch',
                    'reference_mismatch', 'wrong_point'):
        v = base(doc)
        seen = set()
        speakers = ('officer', 'finance', 'clergy')
        quarters = ('army', 'treasury', 'church')
        def delivery(s, call, o, ref, positive, command, point):
            actual = (s, call, o, symbol(ref), symbol(positive), symbol(command), point)
            if s not in speakers:
                return False
            i = speakers.index(s)
            expected = (speakers[(i + 1) % 3] if variant == 'speaker_mismatch' else s, 'call',
                        'other' if variant == 'observer_mismatch' else 'author',
                        'zt' if variant == 'reference_mismatch' else 'h232v',
                        POSITIVE[(i + 1) % 3] if variant == 'positive_mismatch' else POSITIVE[i],
                        COMMANDS[(i + 1) % 3] if variant == 'command_mismatch' else COMMANDS[i], 'now')
            if actual == expected:
                seen.add(actual)
                return True
            return False
        v.update(wa=lambda: 'author', h232v=lambda: 'now',
                 h233i=lambda: 'army', h233j=lambda: 'treasury', h233k=lambda: 'church',
                 zt=lambda: 'later' if variant == 'wrong_point' else 'now',
                 h232s=lambda o, r, q: (o, r) == ('author', 'now') and q in quarters
                     and variant != 'outside_prior_quarters',
                 h232t=lambda q, s, r: r == 'now' and (q, s) in set(zip(
                     quarters, speakers[1:] + speakers[:1] if variant == 'quarter_mismatch' else speakers)),
                 r2tq=delivery)
        for i, name in enumerate(('r2to', 'r2tp', 'sp')):
            v[name] = lambda p, t, i=i: (p, t) == (
                speakers[(i + 1) % 3] if variant == 'role_mismatch' else speakers[i], 'now')
        actual = evaluate(doc, v, people, scenes, True)
        assert actual == [variant == 'baseline'] * 3, (variant, actual)
        if variant == 'baseline':
            assert len(seen) == 3
            bindings = sorted(seen)
        rows[variant] = actual
    return dict(contrasts=rows, paired_roles_quarters_positive_and_commands=bindings,
                same_prior_hearing_scene=True,
                semantic_boundaries=['r2tq: natively checked for all three commands',
                    'r2to/r2tp: natively checked with same-role and same-institution contrasts',
                    'sp: unchanged previously composed clerical role; inherited meaning and definition checked'])


def quoted(desc, name):
    return desc.rank == 1 and json.loads(desc.syntax) == dict(kind='call', symbol=name, arguments=[])


@lru_cache(None)
def discourse_checks():
    doc = fixture('discourse')
    nodes = ('military', 'fiscal', 'religious')
    people = ('author', 'heard', *nodes)
    rows = {}
    for variant in ('baseline', 'missing_attribution', 'wrong_author', 'wrong_context',
                    'wrong_general_content', 'wrong_example_content', 'wrong_general_node', 'reverse_order'):
        v = base(doc)
        def content(n, desc):
            return n in nodes and quoted(desc, CONTENTS[(nodes.index(n) + (variant == 'wrong_example_content')) % 3])
        v.update(wa=lambda: 'author', h232o=lambda: 'context', h232w=lambda: 'heard',
                 h233m=lambda: nodes[0], h233n=lambda: nodes[1], h233o=lambda: nodes[2],
                 hzon=lambda n, a, d, x: (a, x) == (
                     'heard' if variant == 'wrong_author' else 'author',
                     'other' if variant == 'wrong_context' else 'context')
                     and content(n, d) and variant != 'missing_attribution',
                 h233l=lambda n, a, general, first, second, x: (a, general, x) == (
                     'author', nodes[0] if variant == 'wrong_general_node' else 'heard', 'context')
                     and quoted(first, 'r2ss' if variant == 'wrong_general_content' else 'r2te')
                     and content(n, second),
                 ue=lambda first, second, x: x == 'context' and (first, second) in (
                     set(zip(nodes, ('heard', *nodes[:2]))) if variant == 'reverse_order'
                     else set(zip(('heard', *nodes[:2]), nodes))))
        actual = evaluate(doc, v, people, ('context', 'other'), True)
        assert actual == [variant == 'baseline'] * 3, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, native_quotation_without_world_execution=True,
                same_attributed_examples_and_source_order=True, semantic_boundaries=[])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    rows = []
    starts = (274, 328, 378)
    ends = (327, 377, 426)
    role_phrases = ('Der Offizier ', 'Der Finanzrath', 'Der Geistliche')
    role_defs = (['r2tn', 'r2to', 'hzwn', 'hzxf', 'h233d', 'h233e'],
                 ['r2tn', 'r2tp', 'hzwn', 'hzxf', 'h233f', 'h233g'], ['sp'])
    last = ('exercirt!', 'bezahlt!', 'glaubt!')
    for i, (start, end) in enumerate(zip(starts, ends)):
        parts = [
            (role_phrases[i], role_defs[i], '代表的な役職者の例。保持者・任用・当該役割を同じ本人に結ぶ。'),
            ('sagt: ' if i == 0 else ': ', ['r2tr', 'r2tq', 'r2tc', 'f3'],
             '同じ役職者の呼び声として言う。後二文のsagtの省略を同じ関係で補う。'),
            ('räsonnirt nicht, ', ['r2ta', 'r2tb', COMMANDS[i]], '各宛先本人による言語的検討の不実行を求める。'),
            ('sondern ', ['h233h', 'r2tj', 'r2tq'], '禁止される活動に代わる肯定内容を同じ話者が同じ宛先へ提示する。'),
            (last[i], [POSITIVE[i], COMMANDS[i], 'f2', 'h6e', 'h6g'],
             ('本人が軍事教練を行うよう求める。', '指定取引の支払いを行うよう求める。',
              '指定された宗教的教えの内容を信じるよう求める。教えの真理を加えない。')[i]),
        ]
        clauses, cursor = [], start
        for phrase, names, interpretation in parts:
            assert unit['text'][cursor:cursor + len(phrase)] == phrase, (cursor, phrase)
            clauses.append(dict(range=[cursor, cursor + len(phrase)], text=phrase,
                                definitions=names, reading=interpretation))
            cursor += len(phrase)
        assert cursor == end
        text = unit['text'][start:end]
        rows.append(dict(range=[start, end], text=text, clauses=clauses,
                         source_nonblank_characters=sum(not c.isspace() for c in text),
                         selection=selection_binding(catalog(), [65 + i]),
                         context_reading='先行する社会的諸方面の呼び声の具体例として著者へ帰属する。',
                         decision='equivalent_under_stated_reading_for_this_sentence'))
    count = sum(r['source_nonblank_characters'] for r in rows)
    assert count == 134
    paths = (FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, IMAGE, PRIOR, SENTENCES)
    return dict(status='three_role_commands_reviewed_under_explicit_reading', reviewer='assistant_review',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[274, 426], text=unit['text'][274:426]),
                sentences=rows, selection=selection_binding(catalog(), [65, 66, 67]),
                interpretation=LIMITS, unresolved=[],
                decision='equivalent_under_stated_reading_for_these_three_sentences',
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                source_nonblank_characters=count, newly_reviewed_sentence_characters=count,
                preserved_reviewed_sentence_characters=232, paragraph_reviewed_sentence_characters=366,
                semantic_equivalence_automatically_proved=False,
                original_page=dict(path=IMAGE, page=484, visually_inspected=True),
                references=[
                    dict(url='https://korpora.org/Kant/aa08/037.html',
                         use='三つの役職名・命令の反復と後続の軍務・納付の例。'),
                    dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009132_6_0_208',
                         use='Kämmerer第三義。領邦の収入管理とFinanz-Räthe等の呼称。'),
                    dict(url='https://www.duden.de/rechtschreibung/Offizier',
                         use='軍事的な任官階級の保持者という語義の確認。現代の具体的階級表を1784年の制度へ転用しない。')],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:65] == old.document['statements']
    assert len(new.document['statements']) == 68
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
                added_basic_relations=len(PRIMITIVES), preserved_statements=65, added_statements=3,
                preserved_reviewed_sentence_characters=232, new_reviewed_sentence_characters=134,
                old_definitions_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('roles', role_checks), ('delivery', delivery_checks),
                     ('examples', example_checks), ('discourse', discourse_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, IMAGE, PRIOR, SENTENCES, 'scripts/compose_role_commands.py',
        'scripts/check_role_commands.py', 'tests/test_role_commands.py',
        'scripts/check_heard_prohibition.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='role_commands_under_explicit_reading', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], statements=[65, 66, 67],
                               status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
