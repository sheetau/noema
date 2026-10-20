"""Verify the whole answer and preserve its normative and causal scopes."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content, SequenceValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_answer_discourse import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_private_choice_frequency as private
from scripts import check_qualified_private_influence as qualified

INDEX = 'data/semantic-review-index-v160.json'
REPORT = 'reports/answer-discourse-v1.json'
AUDIT = 'data/answer-discourse-reading-v1.json'
DOC = 'docs/answer-discourse-v1.md'
EVIDENCE = 'data/answer-discourse-evidence-v1.json'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGES = ('artifacts/public-reversal-reading-v1/page-484.jpg', 'artifacts/answer-discourse-v1/page-485.jpg')
PRIOR = ('reports/public-freedom-duty-v1.json', 'reports/public-enlightenment-route-v1.json',
         'reports/private-policy-permission-v1.json', 'reports/qualified-private-influence-v1.json')
PEOPLE = ('author', 'answer', 'intro', 'duty', 'route', 'private', 'questionone', 'questiontwo', 'other')
SCENES = ('presentation', 'reference', 'first', 'second')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    roots = {'split': ['r2yy', 'r2z7', 'r2za'], 'content': ['r2zf'],
             'discourse': ['r2zh'], 'scope': ['r2zd', 'r2zg']}[kind]
    boundaries = {'split': ('r2ys', 'r2yv', 'r2yu'), 'content': ('r2yh', 'r2ym', 'r2z5'),
                  'discourse': (), 'scope': ()}[kind]
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    if kind == 'split':
        extra = private.EXTRA + qualified.MODEL_EXTRA.replace('r zreference[] d.', '') + '''
r zbranchdegrees[d d] b.r zbranchpoints[d] j[d].r zbranchweight[d d] b.r zbranchfrequency[d] b.r zbranch[] d.
'''
        args = qualified.BOUND_ARGS
        query = ('q[t[k r2yy[' + args + ']][k zbranch[]]].'
                 'q[w[t[k r2z7[' + args + ']][k zbranch[]]][t[k r2za[' + args + ']][k zbranch[]]]].')
    elif kind == 'content':
        extra, query = 'r zevaluation[] d.', 'q[t[k r2zf[]][k zevaluation[]]].'
    elif kind == 'scope':
        extra = 'r zp[] a.r zr[] a.r zcase[] a.r zpublic[] a.r zevaluation[] d.'
        query = ('q[k r2zd[k zpublic[] k zp[] k zr[] k zcase[]]].'
                 'q[t[k r2zg[k zp[]]][k zevaluation[]]].')
    else:
        extra, query = '', 'q[k r2zh[]].'
    return parse(format_graph(doc, 'compact') + extra + query)


@lru_cache(None)
def split_checks():
    doc, rows = fixture('split'), []
    people = (*private.PEOPLE, 'factor', 'outcome', 'public')
    for aligned, frequent, bridge, bounded in product((False, True), repeat=4):
        v = private.model(doc)
        v.update(zvariables=lambda: SequenceValue(('factor', 'outcome'), '"individual"'),
                 zequation=lambda var, state: var == 'outcome' and state('factor'),
                 zfactor=lambda: 'factor', zworld=lambda state: 'first' if state('factor') else 'last',
                 zmatch=lambda on, off: on('factor') and not off('factor'),
                 zpublic=lambda: 'public', ztolerance=lambda: Fraction(1, 4), zbranch=lambda: 'first',
                 zbranchdegrees=lambda branch, point: Fraction(3, 4),
                 zbranchpoints=lambda branch: SequenceValue(private.TIMES, '"situation"'),
                 zbranchweight=lambda branch, point: Fraction(1),
                 zbranchfrequency=lambda branch: Fraction(1, 2),
                 h222g=lambda public, reference: 'frame' if aligned else 'role',
                 r2ys=lambda *args: frequent, r2yv=lambda *args: bridge, r2yu=lambda *args: bounded)
        actual = evaluate(doc, v, people, private.SCENES, True)
        assert actual == [aligned and frequent and bridge and bounded] * 2
        rows.append(dict(frame=aligned, frequency=frequent, intervention=bridge, bound=bounded,
                         original_and_split=actual))
    # Compare the wrappers' full argument trees, not just fixture truth values.
    entries = catalog().entries
    original = entries['r2yz']['declaration']['body']['arguments']
    for n in ('r2zb', 'r2zc'):
        assert entries[n]['declaration']['body']['arguments'] == original
    return dict(combinations=rows, same_source_argument_trees=True,
                semantic_boundaries=['r2ys/r2yv/r2yu varied independently; native temporal release r2yx retained; prior native checks pinned'])


@lru_cache(None)
def content_checks():
    doc, rows = fixture('content'), []
    for flags in product((False, True), repeat=3):
        v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        v['zevaluation'] = lambda: 'first'
        for name, flag in zip(('r2yh', 'r2ym', 'r2z5'), flags):
            v[name] = lambda flag=flag: Content(SCENES, tuple(flag if s == 'first' else not flag for s in SCENES))
        actual = evaluate(doc, v, PEOPLE, SCENES, True)[0]
        assert actual == all(flags)
        rows.append(dict(parts=list(flags), whole=actual))
    scope = fixture('scope')
    scope_rows = []
    for public, pair, case in product((False, True), repeat=3):
        v = {d['name']: unknown for d in scope['declarations'] if d['kind'] == 'primitive'}
        v.update(zp=lambda: 'author', zr=lambda: 'other', zcase=lambda: 'private', zpublic=lambda: 'answer',
                 zevaluation=lambda: 'first', h232v=lambda: 'reference',
                 h222e=lambda p, ref: public and (p, ref) == ('answer', 'reference'),
                 h236h=lambda p, ref, person, role: pair and (p, ref, person, role) == ('answer', 'reference', 'author', 'other'),
                 h235v=lambda p, person, role, ref, c: case and (p, person, role, ref, c) ==
                    ('answer', 'author', 'other', 'reference', 'private'),
                 aa=lambda person: person == 'author',
                 ca=lambda person, act, ref: (person, act, ref) == ('author', 'other', 'reference'))
        actual = evaluate(scope, v, PEOPLE, SCENES, True)
        assert actual == [public and pair and case, True]
        scope_rows.append(dict(public=public, person_role=pair, candidate=case, result=actual[0]))
    return dict(content_combinations=rows, domain_combinations=scope_rows,
                same_evaluation_and_fixed_reference=True,
                semantic_boundaries=['whole conjunction uses typed contents for the three previously checked clauses'])


def discourse_model(doc, variant='baseline'):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(wa=lambda: 'author', h232o=lambda: 'presentation', h235p=lambda: 'answer',
             h236n=lambda: 'intro', h235s=lambda: 'duty', h235t=lambda: 'route',
             h236j=lambda: 'duty' if variant == 'collapsed_clause_nodes' else 'private',
             h235n=lambda: 'questionone', h235o=lambda: 'questiontwo')
    def code(value):
        return symbol(value), value.rank
    def attributed(node, author, content, context):
        return (node, author, code(content), context) == (
            'answer', 'other' if variant == 'wrong_author' else 'author',
            ('r2z5' if variant == 'wrong_whole_content' else 'r2zf', 3),
            'reference' if variant == 'wrong_context' else 'presentation')
    def contrast(node, author, first, left, second, right, dimension, context):
        return variant != 'missing_contrast' and (node, author, first, code(left), second, code(right), code(dimension), context) == (
            'answer', 'author', 'duty', ('r2ym' if variant == 'wrong_public_content' else 'r2yh', 3),
            'private', ('r2zf' if variant == 'wrong_private_content' else 'r2z5', 3),
            ('h4l' if variant == 'wrong_dimension' else 'r2zg', 0), 'presentation')
    def qualification(node, author, outer, domain, premise, retained, combined, context):
        return variant != 'missing_qualification' and (
            node, author, code(outer), code(domain), code(premise), code(retained), code(combined), context) == (
            'private', 'author', ('r2zf' if variant == 'outside_permission_scope' else 'r2z5', 3),
            ('r2xq' if variant == 'wrong_domain' else 'r2zd', 0),
            ('r2zc' if variant == 'swapped_causal_direction' else 'r2zb', 2),
            ('r2zb' if variant == 'swapped_causal_direction' else 'r2zc', 2),
            ('r2zb' if variant == 'lost_bound' else 'r2yz', 2), 'presentation')
    def self_present(intro, author, question, response, content, context):
        return variant != 'missing_self_presentation' and (
            intro, author, response, code(content), context) == (
            'intro', 'author', 'other' if variant == 'other_response' else 'answer',
            ('r2z5' if variant == 'partial_self_response' else 'r2zf', 3), 'presentation'
        ) and question in (('questionone',) if variant == 'second_question_missing' else ('questionone', 'questiontwo'))
    order = {('questionone', 'intro'), ('questiontwo', 'intro'), ('intro', 'duty'),
             ('duty', 'route'), ('route', 'private')}
    if variant == 'wrong_clause_order':
        order.remove(('route', 'private')); order.add(('private', 'route'))
    v.update(h236i=attributed, h236k=contrast, h236l=qualification, h236m=self_present,
             hzcs=lambda author, question, response, context: variant != 'not_answering' and
                 (author, response, context) == ('author', 'answer', 'presentation') and question in ('questionone', 'questiontwo'),
             ue=lambda first, last, context: context == 'presentation' and (first, last) in order)
    return v


@lru_cache(None)
def discourse_checks():
    doc, rows = fixture('discourse'), {}
    for variant in ('baseline', 'wrong_author', 'wrong_whole_content', 'wrong_context',
                    'missing_contrast', 'wrong_public_content', 'wrong_private_content', 'wrong_dimension',
                    'missing_qualification', 'outside_permission_scope', 'wrong_domain', 'swapped_causal_direction',
                    'lost_bound', 'missing_self_presentation', 'other_response', 'partial_self_response',
                    'second_question_missing', 'wrong_clause_order', 'not_answering', 'collapsed_clause_nodes'):
        actual = evaluate(doc, discourse_model(doc, variant), PEOPLE, SCENES, True)[0]
        assert actual == (variant == 'baseline'), (variant, actual)
        rows[variant] = actual
    for name in ('h236i', 'h236k', 'h236l', 'h236m', 'hzcs', 'ue'):
        v = discourse_model(doc); v[name] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    text = format_graph(doc, 'compact')
    for before, after in (('r d[k r2zf[]]', 'r c[k r2zf[]]'), ('r c[p r2zb]', 'r b[p r2zb]'),
                          ('r c[p r2zc]', 'r b[p r2zc]')):
        assert before in text
        try:
            parse(text.replace(before, after))
        except ValueError:
            pass
        else:
            raise AssertionError('lower rank accepted: ' + before)
    return dict(contrasts=rows, unknown_discourse_evidence_refused=6, lower_ranks_refused=3,
                world_contents_and_permission_unknown_and_unexecuted=True, semantic_boundaries=[])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    parts = [
        ('Ich antworte: ', ['h236m', 'r2zf', 'r2zh'], '同じ著者が先行二問への自分の回答として全文を提示する。'),
        ('der öffentliche Gebrauch seiner Vernunft ', ['zzo', 'r2ye', 'r2yh'], '各人自身の理性の公的使用。後続の定義と同じ学識者として読者世界へ向ける使用。'),
        ('muß jederzeit frei sein', ['r2ye', 'r2yf', 'r2yg', 'h235q'], '全関連時機で同じ公的活動の自由を求める規範。実際の活動実行ではない。'),
        (', und ', ['r2ze'], '公的自由の要求と唯一の可能な実現経路を連言で追加する。'),
        ('der allein kann ', ['r2yj', 'r2yk', 'r2yl'], '実現可能な経路があり、同じ啓蒙が実現する経路では公的使用の生産的関与を欠かない。'),
        ('Aufklärung unter Menschen zu Stande bringen', ['r2ln', 'r2xc', 'r2yl', 'r2ym'], '同じ公衆の人間の自立的能力変化が集団に広がる啓蒙の実現。'),
        ('; der Privatgebrauch derselben ', ['zzp', 'r2yp', 'r2yz', 'r2z5'], '同じ本人の理性の、委ねられた市民的職務での使用。公的使用の単なる否定ではない。'),
        ('aber ', ['h236k', 'r2zg', 'r2zh'], '理性使用の扱いについて公的自由の要求と私的制限への許可を対照する。'),
        ('darf ', ['h235u', 'r2z2', 'r2z3', 'r2z4'], '条件を満たす方針案の存在を内容の内側に置いた積極的許可。現実の実施は導かない。'),
        ('öfters sehr enge eingeschränkt sein', ['r2yo', 'r2yq', 'r2yr', 'r2ys', 'r2zb'], '同じ私的選択肢の強い排除が全関連時機でどの程度の頻度を持つか。程度と頻度の基準を分ける。'),
        (', ohne doch darum ', ['h236l', 'r2yv', 'r2zc', 'r2zh'], 'この強い制限によって次の留保が失われるという見通しを退ける。効果は同じ方針の適用と全解除で比較する。'),
        ('den Fortschritt der Aufklärung ', ['r2xc', 'r2xf', 'r2yu'], '先行する同じ啓蒙の進行尺度・公衆・基準・期間。別過程の変化を合算しない。'),
        ('sonderlich zu hindern.', ['r2yt', 'r2yu', 'h236g', 'r2yz'], '対応する全結果間で、広がりの低下が固定した許容上限を超えない。完全な無影響へ強めない。'),
    ]
    clauses, cursor = [], 690
    for text, names, interpretation in parts:
        assert unit['text'][cursor:cursor + len(text)] == text, (cursor, text)
        clauses.append(dict(range=[cursor, cursor + len(text)], text=text, definitions=names, reading=interpretation))
        assert all(n in catalog().entries for n in names)
        cursor += len(text)
    assert cursor == 980
    text = unit['text'][690:980]
    assert sum(not ch.isspace() for ch in text) == 250
    assert unit['text'][687:690] == ' – '
    evidence = read(EVIDENCE)
    validate_hashes(ROOT, evidence['source_sha256'])
    paths = (FULL, BASIS, ANNOTATIONS, DOC, EVIDENCE, INVENTORY, *IMAGES, *PRIOR)
    return dict(status='answer_sentence_reviewed_under_explicit_reading', reviewer='assistant_review',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[690, 980], text=text),
                sentence_ranges=[[690, 980]], clauses=clauses,
                preceding_separator=dict(range=[687, 690], text=' – ', reading='二問から明示的な自己回答への区切り。順序と自己提示へ接続し、新規文文字数には含めない。'),
                selection=selection_binding(catalog(), [72, 73, 74, 75]),
                interpretation=LIMITS, unresolved=[], decision='equivalent_under_stated_reading_for_the_answer_sentence',
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                source_nonblank_characters=250, newly_reviewed_sentence_characters=250,
                preserved_reviewed_sentence_characters=588, paragraph_reviewed_sentence_characters=838,
                semantic_equivalence_automatically_proved=False,
                holistic_review=[
                    '公的使用の全時機への要求と、私的使用の頻度を含む許可を区別した。話者の自己提示・規範的許可・許可対象の現実の成立という三層を混同しない。',
                    'alleinは公的使用を欠いた生産的経路の不在とし、公的使用だけで全ての条件が足りるという強化を避ける。kannの可能性と実現済みの主張を区別した。',
                    'derselben、darum、同じ啓蒙への照応はそれぞれ本人の理性、同じ制限方針、同じr2ln/r2xcの尺度へ束縛した。程度・頻度・因果比較で参照を動かしていない。',
                    '全回答の各語句と否定・様相・作用域を連続した原文範囲へ対応付けた。記述段階を保ち、未評価や許可の存在を実際の無害性へ補っていない。',
                    '原刊の頁境界はzu / Standeの間であり内容上の区切りではない。ダッシュ、コロン、und、セミコロン、aber、ohne doch darumの役割を保持した。',
                ],
                original_pages=[dict(path=p, page=n, visually_inspected=True) for p, n in zip(IMAGES, (484, 485))],
                references=[evidence['source']['url'], *[row['url'] for row in evidence['facsimiles']]],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:75] == old.document['statements']
    assert len(new.document['statements']) == 76
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in (('data/question-discourse-reading-v1.json', [70, 71]),
                          ('data/public-freedom-duty-reading-v1.json', [72]),
                          ('data/public-enlightenment-route-reading-v1.json', [73]),
                          ('data/private-policy-permission-reading-v1.json', [74])):
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
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
    return dict(preserved_statements=75, added_statements=1, preserved_whole_unit_reviews=len(reviews),
                preserved_reviewed_sentence_characters=588, new_reviewed_sentence_characters=250,
                old_meanings_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('split', split_checks), ('contents', content_checks),
                     ('discourse', discourse_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, EVIDENCE, INVENTORY, *IMAGES, *PRIOR,
        'scripts/compose_answer_discourse.py', 'scripts/check_answer_discourse.py',
        'scripts/compose_private_policy_permission.py', 'scripts/compose_qualified_private_influence.py',
        'scripts/compose_private_choice_frequency.py', 'scripts/compose_grounded_step.py',
        'scripts/check_private_choice_frequency.py', 'scripts/check_qualified_private_influence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'tests/test_answer_discourse.py',
        'data/question-discourse-reading-v1.json', 'data/public-freedom-duty-reading-v1.json',
        'data/public-enlightenment-route-reading-v1.json', 'data/private-policy-permission-reading-v1.json'}
    return dict(status='answer_sentence_under_explicit_reading', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], statements=[72, 73, 74, 75], status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
