"""Check institutional identity, ranked speech, unique speakers and the aside."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_single_ruler import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

INDEX = 'data/semantic-review-index-v151.json'
REPORT = 'reports/single-ruler-v1.json'
AUDIT = 'data/single-ruler-reading-v1.json'
DOC = 'docs/single-ruler-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/public-reversal-reading-v1/page-484.jpg'
PRIOR = 'reports/free-choice-obedience-v1.json'
SENTENCES = 'data/role-commands-reading-v1.json'
FIRST = 'data/heard-prohibition-reading-v1.json'
EXTRA = 'r zp[] a.r zcommunity[] a.r zcall[] a.r zr[] d.r zt[] d.'
SCENES = ('now', 'later')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    boundaries = {'world': ('r2uj',), 'unique': ('r2uk', 'r2ul')}.get(kind, ())
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    roots = {'role': ['r2uj'], 'world': ['r2uk'], 'speech': ['r2ul'],
             'unique': ['r2un'], 'discourse': ['r2ur']}[kind]
    doc.update(declarations=closure(doc, roots), statements=[])
    query = {
        'role': 'q[k r2uj[k zp[] k zcommunity[] k zt[]]].',
        'world': 'q[k r2uk[k zp[] k zr[] k zt[]]].',
        'speech': 'q[k r2ul[k zp[] k zcall[] r[k zr[]] k zt[]]].',
        'unique': 'q[k r2un[r[k zr[]] k zt[]]].',
        'discourse': 'q[k r2ur[]].',
    }[kind]
    return parse(format_graph(doc, 'compact') + EXTRA + query)


def base(doc):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(zp=lambda: 'ruler', zcommunity=lambda: 'state', zcall=lambda: 'call',
             zr=lambda: 'now', zt=lambda: 'now')
    return v


def role_model(doc, variant='baseline'):
    v = base(doc)
    edges = {('top', 'middle'), ('middle', 'lower'), ('top', 'lower')}
    if variant == 'nontransitive':
        edges.remove(('top', 'lower'))
    if variant == 'incomparable_lower_role':
        edges = {('top', 'middle')}
    if variant == 'reflexive_order':
        edges.add(('top', 'top'))
    v.update(
        aa=lambda p: p in ('ruler', 'other') and variant != 'nonhuman',
        cf=lambda p, role, t: (p, role, t) == ('ruler', 'top', 'now') and variant != 'not_entrusted',
        hzwn=lambda p, role, t: t == 'now' and (
            (p, role) == ('ruler', 'middle' if variant == 'holds_another_role' else 'top')
            or variant == 'second_holder' and (p, role) == ('other', 'top')),
        hzxf=lambda p, role, state, t: t == 'now' and state == (
            'otherstate' if variant == 'appointed_elsewhere' else 'state')
            and ((p, role) == ('ruler', 'middle' if variant == 'appointed_to_other_role' else 'top')
                 or variant == 'second_holder' and (p, role) == ('other', 'top'))
            and variant != 'not_appointed',
        h234d=lambda role, state, t: (state, t) == ('state', 'now')
            and role in (('middle', 'lower') if variant == 'highest_outside_scope' else ('top', 'middle', 'lower')),
        h234e=lambda top, lower, state, t: (state, t) == ('state', 'now') and (top, lower) in edges,
        h234f=lambda role, state, t: (role, state, t) == (
            'middle' if variant == 'delegated_department_head' else 'top', 'state', 'now')
            and variant != 'private_owner')
    return v


@lru_cache(None)
def role_checks():
    doc = fixture('role')
    people = ('ruler', 'other', 'top', 'middle', 'lower', 'state', 'otherstate')
    rows = {}
    for variant in ('baseline', 'nonhuman', 'not_entrusted', 'holds_another_role', 'not_appointed',
                    'appointed_elsewhere', 'appointed_to_other_role', 'second_holder',
                    'highest_outside_scope', 'nontransitive', 'incomparable_lower_role', 'reflexive_order',
                    'delegated_department_head', 'private_owner'):
        actual = evaluate(doc, role_model(doc, variant), people, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, native_hzfn_rm2_rex_and_same_institution=True,
                highest_not_merely_maximal=True, semantic_boundaries=[])


@lru_cache(None)
def world_checks():
    doc = fixture('world')
    people = ('ruler', 'state', 'otherstate', 'other')
    rows = {}
    for variant in ('baseline', 'two_communities_one_person', 'outside_world_scope',
                    'other_person_rules', 'other_reference', 'wrong_evaluation_point'):
        v = base(doc)
        v.update(h234c=lambda community, ref: ref == ('later' if variant == 'other_reference' else 'now')
                 and community in ('state', 'otherstate'),
                 r2uj=lambda p, community, t: (p, t) == (
                     'other' if variant == 'other_person_rules' else 'ruler',
                     'later' if variant == 'wrong_evaluation_point' else 'now')
                 and community in (('other',) if variant == 'outside_world_scope' else
                                   ('state', 'otherstate') if variant == 'two_communities_one_person' else ('state',)))
        actual = evaluate(doc, v, people, SCENES, True)
        assert actual == [variant in ('baseline', 'two_communities_one_person')], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, same_person_community_reference_and_point=True,
                semantic_boundaries=['r2uj: separately evaluated with native hzfn/rm2/rex'])


def applied(desc, name, reference='zr'):
    return desc.rank == 1 and json.loads(desc.syntax) == dict(
        kind='apply', function=dict(kind='function_ref', symbol=name),
        arguments=[dict(kind='call', symbol=reference, arguments=[])])


def speech_model(doc, variant='baseline'):
    v = base(doc)
    def presentation(call, recipient, subject, desc, point):
        name = json.loads(desc.syntax)['function']['symbol']
        expected_name = 'r2ug' if variant == 'permission_only' else name
        return (call, subject, point) == (
            'othercall' if variant == 'other_event' and name == 'r2uh' else 'call',
            'first' if variant == 'recipient_used_as_norm_source' else
            'other' if variant == 'other_norm_source' else 'ruler', 'now'
        ) and recipient in (('first',) if variant == 'only_first_addressed' else ('first', 'second')) \
            and applied(desc, expected_name, 'zt' if variant == 'other_reference' else 'zr')
    v.update(
        aa=lambda p: p in ('ruler', 'first', 'second') and not (variant == 'nonhuman_recipient' and p == 'second'),
        dg=lambda call, t: (call, t) == ('call', 'now') and variant != 'not_occurring',
        f3=lambda p, call, t: (p, call, t) == (
            'other' if variant == 'other_presenter' else 'ruler', 'call', 'now'),
        h233p=lambda p, ref, recipient: (p, ref) == ('ruler', 'now') and recipient in (
            () if variant == 'empty_audience' else ('first',) if variant == 'one_recipient' else ('first', 'second')),
        h234g=presentation,
        h234h=lambda call, speaker, recipient, subject, first, second, point: (
            call, speaker, subject, point) == ('call', 'ruler',
                'other' if variant == 'contrast_other_subject' else 'ruler', 'now')
            and recipient in (('first',) if variant == 'contrast_only_first' else ('first', 'second'))
            and applied(first, 'r2uh' if variant == 'reverse_contrast' else 'r2ug')
            and applied(second, 'r2ug' if variant == 'reverse_contrast' else 'r2uh')
            and variant != 'mere_juxtaposition')
    return v


@lru_cache(None)
def speech_checks():
    doc = fixture('speech')
    people = ('ruler', 'first', 'second', 'call', 'other', 'othercall')
    rows = {}
    for variant in ('baseline', 'permission_only', 'other_event', 'recipient_used_as_norm_source',
                    'other_norm_source', 'only_first_addressed', 'other_reference', 'nonhuman_recipient',
                    'not_occurring', 'other_presenter', 'empty_audience', 'one_recipient',
                    'contrast_other_subject', 'contrast_only_first', 'reverse_contrast', 'mere_juxtaposition'):
        actual = evaluate(doc, speech_model(doc, variant), people, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for missing in ('h234g', 'h234h', 'h233p'):
        v = speech_model(doc); v[missing] = unknown
        try:
            evaluate(doc, v, people, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, same_speaker_is_both_norm_sources=True, all_plural_recipients_addressed=True,
                native_rank_one_messages=True, normative_and_execution_inputs_unknown=True,
                unknown_inputs_refused=3, semantic_boundaries=[])


@lru_cache(None)
def uniqueness_checks():
    doc = fixture('unique')
    people = ('ruler', 'other', 'outsider', 'call', 'othercall')
    rows = {}
    for variant in ('one_speaker_two_rulers', 'no_speakers', 'no_rulers', 'two_ruler_speakers',
                    'one_person_two_calls', 'nonruler_also_speaks', 'only_nonruler_speaks',
                    'wrong_point', 'different_reference'):
        v = base(doc)
        qualified = () if variant == 'no_rulers' else ('ruler', 'other')
        calls = {('ruler', 'call')}
        if variant == 'no_speakers':
            calls = set()
        elif variant == 'two_ruler_speakers':
            calls.add(('other', 'othercall'))
        elif variant == 'one_person_two_calls':
            calls.add(('ruler', 'othercall'))
        elif variant == 'nonruler_also_speaks':
            calls.add(('outsider', 'othercall'))
        elif variant == 'only_nonruler_speaks':
            calls = {('outsider', 'othercall')}
        v.update(
            r2uk=lambda p, ref, t: p in qualified and (ref, t) == ('now', 'now'),
            r2ul=lambda p, call, ref, t: (p, call) in calls and t == 'now' and ref.rank == 0
                and json.loads(ref.syntax) == dict(kind='call',
                    symbol='zt' if variant == 'different_reference' else 'zr', arguments=[]),
            zt=lambda: 'later' if variant == 'wrong_point' else 'now')
        actual = evaluate(doc, v, people, SCENES, True)
        expected = variant in ('one_speaker_two_rulers', 'one_person_two_calls', 'nonruler_also_speaks')
        assert actual == [expected], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, exactly_one_qualified_speaker_not_one_ruler_or_one_call=True,
                semantic_boundaries=['r2uk: world binding separately tested; r2uj native role checks',
                                     'r2ul: separately tested native ranked presentation'])


def quoted(desc, name):
    return desc.rank == 1 and json.loads(desc.syntax) == dict(kind='call', symbol=name, arguments=[])


@lru_cache(None)
def discourse_checks():
    doc = fixture('discourse')
    people = ('author', 'aside', 'three', 'clergy')
    rows = {}
    for variant in ('baseline', 'missing_attribution', 'other_author', 'other_context',
                    'wrong_claim', 'reversed_contrast', 'wrong_common_dimension',
                    'not_parenthetical', 'wrong_aside_anchor', 'reversed_text_order'):
        v = base(doc)
        v.update(wa=lambda: 'author', h234i=lambda: 'aside', h234j=lambda: 'three',
                 h233o=lambda: 'clergy', h232o=lambda: 'context',
                 hzon=lambda node, author, content, ctx: (node, author, ctx) == (
                     'aside', 'three' if variant == 'other_author' else 'author',
                     'other' if variant == 'other_context' else 'context')
                     and quoted(content, 'r2up' if variant == 'wrong_claim' else 'r2uo')
                     and variant != 'missing_attribution',
                 h222q=lambda node, author, firstnode, first, secondnode, second, axis, ctx: (
                     node, author, firstnode, secondnode, ctx) == (
                         'aside', 'author', 'aside' if variant == 'reversed_contrast' else 'three',
                         'three' if variant == 'reversed_contrast' else 'aside', 'context')
                     and quoted(first, 'r2up') and quoted(second, 'r2uo')
                     and axis.rank == 0 and json.loads(axis.syntax) == dict(
                         kind='apply', function=dict(kind='function_ref',
                             symbol='r2ta' if variant == 'wrong_common_dimension' else 'r2uq'),
                         arguments=[dict(kind='call', symbol='h232v', arguments=[])]),
                 h234k=lambda node, author, anchor, ctx: (node, author, anchor, ctx) == (
                     'aside', 'author', 'clergy' if variant == 'wrong_aside_anchor' else 'three', 'context')
                     and variant != 'not_parenthetical',
                 ue=lambda first, second, ctx: (first, second, ctx) == (
                     'aside' if variant == 'reversed_text_order' else 'clergy',
                     'clergy' if variant == 'reversed_text_order' else 'aside', 'context'))
        # Even the narrated reference and all world-level predicates remain unknown.
        v['zr'] = unknown
        actual = evaluate(doc, v, people, ('context', 'other'), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, native_attribution_contrast_aside_and_order=True,
                world_and_quoted_reference_not_executed=True, semantic_boundaries=[])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    pieces = [
        ('(', ['h234k', 'r2ur'], '先の三者の声への補足を括弧で挿入する。'),
        ('Nur ein einziger ', ['r2um', 'r2un'], 'この発言をする統治者の存在と唯一性。'),
        ('Herr ', ['r2ui', 'r2uj', 'hzfn', 'h234f'], '同じ共同体の最高位に任用された君主的な統治者。'),
        ('in der Welt ', ['h234c', 'r2uk'], '叙述上の現在の世界全体の政治的共同体を比較範囲とする。'),
        ('sagt: ', ['dg', 'f3', 'r2ul', 'h234g'], '同じ話者が同じ発話で同じ複数宛先へ述べる。'),
        ('räsonnirt, ', ['r2ug', 'r2tz', 'ca', 'h232p'], '本人の理性を用いた言語的検討への容認。'),
        ('so viel ihr wollt, ', ['h233r', 'h233t', 'r2ub', 'rtt', 'rts'], '各宛先本人が望む量・程度での議論を許す。'),
        ('und worüber ihr wollt; ', ['h233q', 'h233s', 'h227z', 'r2ub', 'rtt', 'rts'],
         '望む話題を量と独立に選べる。全組合せと範囲内の全候補を扱う。'),
        ('aber ', ['h234h', 'r2ul'], '容認を撤回せず、服従の制約を対照的な留保として続ける。'),
        ('gehorcht!', ['r2uh', 'r2uf', 'r2ud', 'rtx', 'rtw', 'h234b'],
         '同じ出所の要求を欠かさず、その指示に従って履行するよう求める。'),
        (')', ['h234k', 'r2ur'], '括弧での補足として同じ著者へ帰属する。'),
    ]
    clauses, cursor = [], 427
    for phrase, names, interpretation in pieces:
        assert unit['text'][cursor:cursor + len(phrase)] == phrase, (cursor, phrase)
        clauses.append(dict(range=[cursor, cursor + len(phrase)], text=phrase,
                            definitions=names, reading=interpretation))
        cursor += len(phrase)
    assert cursor == 536
    text = unit['text'][427:536]
    count = sum(not c.isspace() for c in text)
    assert count == 91
    paths = (FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, IMAGE, PRIOR, SENTENCES, FIRST)
    return dict(status='single_ruler_parenthesis_reviewed_under_explicit_reading', reviewer='assistant_review',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[427, 536], text=text),
                clauses=clauses, selection=selection_binding(catalog(), [68]), interpretation=LIMITS,
                unresolved=[], decision='equivalent_under_stated_reading_for_this_sentence',
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                source_nonblank_characters=count, newly_reviewed_sentence_characters=count,
                preserved_reviewed_sentence_characters=366, paragraph_reviewed_sentence_characters=457,
                semantic_equivalence_automatically_proved=False,
                original_page=dict(path=IMAGE, page=484, visually_inspected=True),
                references=[
                    dict(url='https://korpora.org/Kant/aa08/037.html', use='括弧文全体と前後の文脈。'),
                    dict(url='https://korpora.org/Kant/aa08/040.html', use='後続のMonarch・Fürstと政治的な統治の文脈。'),
                    dict(url='https://korpora.org/Kant/aa08/041.html', use='Staatsoberhaupt・Monarchの文脈での同じ発言の再掲。'),
                    dict(url='https://www.duden.de/rechtschreibung/Herr', use='敬称とは異なる支配者・統べる者の語義。')],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:68] == old.document['statements']
    assert len(new.document['statements']) == 69
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    assert read(SENTENCES)['selection'] == selection_binding(new, [65, 66, 67])
    first = read(FIRST)
    assert first['selection'] == selection_binding(new, [64])
    assert first['first_sentence_recheck']['selection'] == selection_binding(new, [63])
    for p in (PRIOR, SENTENCES, FIRST):
        validate_hashes(ROOT, read(p)['source_sha256'])
    assert read(AUDIT) == reading()
    for p, body in build().items():
        assert (ROOT / p).read_text(encoding='utf-8') == body
    for p in (FULL, CORE):
        doc = parse((ROOT / p).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_whole_unit_reviews=len(reviews), preserved_statements=68, added_statements=1,
                old_meanings_unchanged=True, preserved_reviewed_sentence_characters=366,
                new_reviewed_sentence_characters=91, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for p, body in build().items():
        write_exact(ROOT / p, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('role', role_checks), ('world', world_checks), ('speech', speech_checks),
                     ('uniqueness', uniqueness_checks), ('discourse', discourse_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, IMAGE, PRIOR, SENTENCES, FIRST,
        'scripts/compose_single_ruler.py', 'scripts/check_single_ruler.py', 'tests/test_single_ruler.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='single_ruler_parenthesis_under_explicit_reading', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], statements=[68], status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
