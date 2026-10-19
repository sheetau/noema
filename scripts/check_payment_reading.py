"""Review payment, restricted sufficiency and assured future undertaking."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_payment_reading import ROOT, PARENT, PARENT_BASIS, FULL, CORE, BASIS, ANNOTATIONS, parent, build, closure
from scripts.check_sufficient_payment import questions as previous_questions, source_values, PEOPLE, SCENES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_designation_order import substantive
from scripts.fetch_payment_reading_evidence import PATH as EVIDENCE, validate

INDEX = 'data/semantic-review-index-v60.json'
REPORT = 'reports/payment-reading-v1.json'
AUDIT = 'data/payment-reading-v1.json'
DOC = 'docs/payment-reading-v1.md'


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def generic_checks():
    d = deepcopy(catalog().document); d.update(declarations=closure(d, ['s4', 'hzxl']), statements=[])
    d = parse(format_graph(d, 'compact') + '''r jn[] a.r ja[] a.r js[] d.r jp[] c.r jq[] c.
d jeligible[person a] e[b scene[k jp[]]].
d jaccess[person a] e[b scene[k jq[]]].
d jrule[person a] e[b scene[y[k jp[]][k jq[]]]].
q[w[k s4[k jn[] k ja[] r[p jrule] k js[]]][k hzxl[k jn[] k ja[] r[p jeligible] r[p jaccess] k js[]]]].
q[k jp[]].q[k jq[]].''')
    rows = []
    for presented, restricted, eligible, access in product((False, True), repeat=4):
        v = dict(jn=lambda: 'node', ja=lambda: 'presenter', js=lambda: 'context', jp=lambda: eligible, jq=lambda: access,
            s4=lambda n, a, d, s: presented and (n, a, symbol(d), s) == ('node', 'presenter', 'jrule', 'context'),
            hzxl=lambda n, a, p, q, s: restricted and (n, a, symbol(p), symbol(q), s) ==
                ('node', 'presenter', 'jeligible', 'jaccess', 'context'))
        actual = evaluate(d, v, ('node', 'presenter'), ('context',))
        assert actual == [presented and restricted, eligible, access]
        rows.append(dict(presented=presented, restricted=restricted, eligible=eligible, access=access, values=actual))
    return dict(independent_combinations=rows, nonpayment_eligibility_fixture=True,
        marker_not_equivalent_to_actual_sufficiency=True)


def presentation_values(variant='baseline'):
    d = parse((ROOT / CORE).read_text(encoding='utf-8'))
    v = {x['name']: unknown for x in d['declarations'] if x['kind'] == 'primitive'}
    v.update(t4=lambda: 'payment', s3=lambda: 'examples', wa=lambda: 'author', wh=lambda: 'text',
        s4=lambda n, a, d, s: variant != 'no_presentation' and (n, a, symbol(d), s) ==
            ('payment', 'author', 'tr' if variant == 'wrong_conditional' else 't3', 'text'),
        ue=lambda a, b, s: (a, b, s) == (('payment', 'examples', 'text') if variant == 'reverse_order' else ('examples', 'payment', 'text')),
        hzxl=lambda n, a, p, q, s: variant != 'no_marker' and (n, a, symbol(p), symbol(q), s) == (
            'examples' if variant == 'other_node' else 'payment', 'other' if variant == 'other_author' else 'author',
            'tq' if variant == 'reversed_scope' else 'to' if variant == 'other_premise' else 'tp',
            'tp' if variant == 'reversed_scope' else 't2' if variant == 'other_conclusion' else 'tq',
            'case' if variant == 'other_context' else 'text'))
    return v


def scope_checks():
    d = parse((ROOT / CORE).read_text(encoding='utf-8')); rows = {}
    for variant in ('baseline', 'no_presentation', 'no_marker', 'wrong_conditional', 'other_node', 'other_author',
            'other_premise', 'other_conclusion', 'reversed_scope', 'other_context', 'reverse_order'):
        actual = evaluate(d, presentation_values(variant), ('payment', 'examples', 'author', 'other'), ('text', 'case'))
        expected = [variant not in ('no_presentation', 'wrong_conditional', 'reverse_order'), variant in ('baseline', 'reverse_order')]
        assert actual == expected; rows[variant] = actual
    for name in ('s4', 'hzxl', 'ue'):
        v = presentation_values(); v[name] = unknown
        try: evaluate(d, v, ('payment', 'examples', 'author'), ('text',))
        except ValueError as e: assert 'Unknown' in str(e)
        else: raise AssertionError(name)
    return dict(contrasts=rows, unknown_inputs_refused=3, all_payment_thinking_and_forecast_facts_unknown=True)


@lru_cache(None)
def questions():
    d = deepcopy(catalog().document); d.update(declarations=closure(d, ['tp', 'tq', 't2', 't3', 'wh']), statements=[])
    return parse(format_graph(d, 'compact') + 'r jperson[] a.' + ''.join(
        'q[t[k ' + n + '[k jperson[]]][k wh[]]].' for n in ('tp', 'tq', 't2', 't3')))


def source_checks():
    assert questions() == previous_questions()
    report = json.loads((ROOT / 'reports/sufficient-payment-v1.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT, report['source_sha256'])
    assert report['source']['current_definitions_executed'] and len(report['source']['contrasts']) == 34
    rows = []
    for variant, marked in product(('baseline', 'thinking_required', 'empty_forecast', 'partial_no_forecast'), (False, True)):
        actual = evaluate(questions(), source_values(variant), PEOPLE, SCENES, True)
        assert actual == report['source']['contrasts'][variant]
        presented = evaluate(parse((ROOT / CORE).read_text(encoding='utf-8')),
            presentation_values('baseline' if marked else 'no_marker'), ('payment', 'examples', 'author'), ('text',))
        assert presented == [True, marked]
        rows.append(dict(variant=variant, restricted=marked, source_values=actual, presentation_values=presented))
    assert evaluate(questions(), source_values('thinking_required'), PEOPLE, SCENES) == [True, False, True, False]
    return dict(cases=rows, current_source_definitions_executed=True, ordinary_countermodel_agrees=True,
        prior_34_contrasts_bound_to_identical_query_document=True, actual_conditional_not_inferred_from_presentation=True)


def forecast_checks():
    d = deepcopy(catalog().document); d.update(declarations=closure(d, ['t2', 'tz', 'wh']), statements=[])
    d = parse(format_graph(d, 'compact') + 'r jperson[] a.q[t[k t2[k jperson[]]][k wh[]]].q[t[k tz[k jperson[]]][k wh[]]].')
    variants = ('different_workers', 'same_worker', 'missing_second', 'wrong_work', 'wrong_beneficiary',
        'wrong_forecast_description', 'wrong_viewpoint', 'not_unpleasant', 'empty_forecast', 'nonfuture_candidate',
        'current_as_future', 'current_truth')
    rows = {}
    for variant in variants:
        v = source_values()
        selected = {'now'} if variant == 'current_as_future' else set() if variant == 'empty_forecast' else {'near', 'far'}
        work = 'sm' if variant == 'wrong_work' else 'bm'
        beneficiary = 'other' if variant == 'wrong_beneficiary' else 'person'
        facts = {('worker', beneficiary, work, 'near')}
        if variant != 'missing_second': facts.add(('worker' if variant == 'same_worker' else 'alternate', beneficiary, work, 'far'))
        if variant == 'current_truth': facts.add(('worker', 'person', 'bm', 'now'))
        v.update(aa=lambda p: p in ('person', 'worker', 'alternate'),
            ts=lambda o, p, w, s: (o, p, symbol(w), s) in facts,
            tu=lambda p, w, s: variant != 'not_unpleasant' and (p, symbol(w), s) ==
                ('other' if variant == 'wrong_viewpoint' else 'person', 'bm', 'now'),
            tw=lambda p, w, c, s: (p, symbol(w), c) ==
                ('person', 'bm' if variant == 'wrong_forecast_description' else 'tz', 'now') and s in selected,
            tx=lambda c, s: c == 'now' and s in selected and not (variant == 'nonfuture_candidate' and s == 'far'))
        actual = evaluate(d, v, ('person', 'worker', 'alternate'), ('now', 'near', 'far', 'other'))
        assert actual == [variant in ('different_workers', 'same_worker', 'current_truth'), variant == 'current_truth'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, actual_current_forecast_definitions=True,
        undertaking_not_performance_or_completion=True, ordinary_evaluation=True)


def reading():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    text = 'Ich habe nicht nöthig zu denken, wenn ich nur bezahlen kann; andere werden das verdrießliche Geschäft schon für mich übernehmen.'
    start = unit['text'].index(text); pos = start; clauses = []
    parts = [
        ('person', 'Ich ', ['s4', 's2'], '前文から続く仮定上の一人称。著者の実生活や全員の事実に固定しない。'),
        ('unnecessary', 'habe nicht nöthig ', ['tq', 'rd', 'sw'], '本人の実用上の用事を、本人の思考が経路に含まれない方法で処理できる。思考不能や単なる不実行とは分ける。'),
        ('thinking', 'zu denken, ', ['tl', 'bm'], 'この文脈で本人が理解力を用いて判断する仕事。全ての心的活動まで不要とはしない。'),
        ('condition', 'wenn ich ', ['t3', 'rqxg'], '同じ本人・非空の仮定範囲で、支払能力を前件として帰結を要求する。'),
        ('restriction', 'nur ', ['hzxl', 'hzxm'], '固定した文脈では支払能力だけで足りるという限定の提示。普通の条件提示とは分け、必要条件や唯一の達成手段にはしない。'),
        ('payment_capacity', 'bezahlen kann; ', ['to', 'tp', 'rqxz'], 'その仕事を賄う必要対価を支払う方法がある。単なる部分払い、現在の支払い済み、所持金とは区別する。'),
        ('others', 'andere ', ['rh', 'tz'], '本人とは別の不特定の人による引受け。全員、固有の一人、固定人数を指定しない。'),
        ('future', 'werden ', ['ri', 'tx', 't2'], '支払える仮定の状況を基準とする将来の見込み。現在や実現の保証へ読み替えない。'),
        ('work_evaluation', 'das verdrießliche Geschäft ', ['bm', 'tu', 't2'], '前の本人の判断の仕事を受け、仮定上の話者がそれを煩わしいと評価する。著者の客観的な認定とはしない。'),
        ('assurance', 'schon ', ['tw', 'ri'], 'その見込みを確かなものとして提示する候補範囲。既に終わったという時間用法、数値確率、全可能世界での保証とはしない。'),
        ('undertaking', 'für mich übernehmen.', ['ts', 'tz'], '同じ本人のために仕事を担当として引き受ける。現在の実行や将来の完了を追加しない。')]
    for name, phrase, definitions, interpretation in parts:
        clauses.append(dict(id=name, range=[pos, pos+len(phrase)], text=phrase,
            definitions=definitions, interpretation_ja=interpretation, status='reviewed_under_stated_reading'))
        pos += len(phrase)
    paths = (inv, PARENT, PARENT_BASIS, FULL, BASIS, INDEX, EVIDENCE,
        'artifacts/first-cause-reading-v1/page-482.jpg', 'data/sufficient-payment-reading-v1.json',
        'data/sufficient-payment-evidence-v1.json', 'reports/sufficient-payment-v1.json',
        'data/conditional-forecast-reading-v1.json', 'data/delegation-context-reading-v1.json')
    return dict(status='payment_sentence_reviewed_with_restricted_sufficiency', reviewer='assistant_review',
        decision='equivalent_under_stated_reading_for_this_sentence', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start+len(text)], text=text,
            nonblank_characters=sum(not ch.isspace() for ch in text)), clauses=clauses,
        selection=selection_binding(catalog(), [5, 43]),
        context=dict(person='仮定上の一人称の位置を前件・帰結・評価・受益者へ共通に通す。',
            purpose='前の代行例と同じ実際上の用事sw。自分で判断することを目的に組み込まない。',
            cases='非空の仮定範囲s2を先に定める。そこで支払能力があるかを、条件文の真偽とは別に確認する。',
            methods='各方法の非空で整合した評価結果を固定する。不足や失敗の結果を後から除いて成功を作らない。',
            prices='同じ取引文脈の尺度で算入額と必要額を比較する。具体的な金額・通貨や必要額の正当性を加えない。',
            forecast='後半を同じ支払い仮定に従属させる既存の読み。未来の基準・見込みの主体を同じ仮定へ結ぶ。',
            alternatives='nurは十分性を限定して提示する読み。支払不能なら必ず思考が必要という逆条件や他の達成手段の排除を加えない。'),
        findings=['原刊482頁の一文全体を十一範囲に分け、現在の内容と提示の構造へ照合した。',
            '通常の条件提示だけでは残らなかった限定をhzxlで区別した。金額の不足と必要額の充足は前版の修正を保持する。',
            '歴史辞典のnurの条件提示とschonの確言の用法を照合し、この文の採用読解を明示した。',
            'この固定版の一文は、公開した基本関係と文脈を用いる採用読解の下で対応すると判断する。'],
        interpretation_limits=['アシスタントによる読解判断であり、独立査読や自動的な意味一致の証明ではない。',
            'nurとschonの全用法を網羅せず、条件提示と確信を伴う見込みというこの用法を採る。',
            '後半を独立した見込みとする別読解もあり、句読点だけで仮定への従属が一意に決まるとはしない。',
            'andereは不特定の他者による引受けとして読む。全候補で同じ人、全員、具体的な人数は要求しない。',
            '数量による対価評価、思考の経路、見込みと引受け、限定の提示は明示した基本関係の解釈を使う。制度・心理の全内部構造は未完成。',
            '原刊の語順や綴りの復元、皮肉の全効果、段落全体の論証の完成をこの一文の判断へ含めない。',
            'この判断を別文脈・後続版・全文へ自動継承しない。'],
        remaining=['後見人の働きかけを含む第二段落全体', '二作品全文', '基本関係の構成的説明の拡充'],
        whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=109, new_whole_unit_reviews=0, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def structure():
    old, new = parent(), catalog()
    assert new.document['statements'][:43] == old.document['statements'] and len(new.document['statements']) == 44
    assert set(new.entries) - set(old.entries) == {'hzxl', 'hzxm'}
    assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in old.entries)
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        review = json.loads((ROOT / path).read_text(encoding='utf-8')); ids = [s['index'] for s in review['selection']['statements']]
        a, b = selection_binding(old, ids), selection_binding(new, ids)
        assert a == review['selection'] and a['statements'] == b['statements'] and a['dependencies'] == b['dependencies']
    r = reading(); assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == r
    validate_hashes(ROOT, r['source_sha256'])
    assert r['source']['range'] == [519, 647] and r['source']['nonblank_characters'] == 109
    assert ''.join(c['text'] for c in r['clauses']) == r['source']['text'] and len(r['clauses']) == 11
    for c in r['clauses']:
        a, b = c['range']; assert c['text'] == r['source']['text'][a-519:b-519]
        assert all(n in new.entries for n in c['definitions'])
    for path, text in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == text
    for path in (FULL, CORE):
        d = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(d, style); assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    validate(json.loads((ROOT / EVIDENCE).read_text(encoding='utf-8')))
    return dict(preserved_statements=43, added_statement=43, changed_definitions=[], new_primitives=1, new_definitions=1,
        preserved_review_meanings=11, current_selection_bound=True, clause_partition=11,
        reviewed_sentence_characters=109, roundtrips=True, semantic_equivalence_automatically_proved=False)


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('scope', scope_checks), ('source', source_checks),
            ('forecast', forecast_checks), ('structure', structure)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    r = reading(); source = r['source']
    paths = set(build()) | set(catalog().source_sha256) | set(r['source_sha256']) | {AUDIT, DOC,
        'scripts/compose_payment_reading.py', 'scripts/check_payment_reading.py', 'scripts/register_payment_reading.py',
        'scripts/fetch_payment_reading_evidence.py', 'tests/test_payment_reading.py', 'scripts/fetch_pastoral_role_evidence.py',
        'scripts/check_sufficient_payment.py', 'scripts/check_conditional_forecast.py', 'scripts/check_payment_expectation.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/check_designation_order.py',
        'scripts/compose_falling_depiction.py', 'noema/constructed.py', 'noema/constructed_discourse.py',
        'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='whole_payment_sentence_reviewed_under_explicit_reading', document=FULL, **results,
        alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'], range=source['range'], source=source['text'],
            definitions=['tp', 'tq', 't2', 't3', 'hzxl', 'hzxm'], status='explicit_interpretive_annotation'),
        review_decision=r['decision'], reviewer='assistant_review', whole_sentence_semantically_verified=True,
        new_verified_sentence_characters=109, semantic_equivalence_automatically_proved=False,
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))


if __name__ == '__main__':
    main()
