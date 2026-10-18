"""Join the active explanatory title, answer bridge and all footnote assertions."""
from copy import deepcopy
from functools import lru_cache
import argparse
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts import check_projected_classification as footnote
from scripts.check_explanatory_question import query_syntax, ref
from scripts.compose_falling_depiction import ROOT, closure

INDEX = 'data/semantic-review-index-v35.json'
DOCUMENT = 'examples/v016/kant-explanatory-question.noema'
BASIS = 'data/explanatory-question-basis-v1.json'
AUDIT = 'data/footnote-audit-v2.json'
REPORT = 'reports/current-footnote-v1.json'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
SELECTION = [0, *range(18, 27), 40]
SYMBOLS = ['hzva', 'hzjt', 'hzju', 'hzkk', 'hzkt', 'hzle', 'hzlr', 'hzlt', 'hzlz', 'hzmd', 'hzvb']
DOMAIN = (*footnote.previous.DOMAIN, 'opening')
SCENES = (*footnote.previous.previous.previous.SCENES, 'text')


def unknown(*args):
    raise ValueError('Unknown current-footnote interpretation')


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def document():
    doc = deepcopy(catalog().document)
    doc['statements'] = [doc['statements'][i] for i in SELECTION]
    assert [s['body']['symbol'] for s in doc['statements']] == SYMBOLS
    doc['declarations'] = closure(doc, SYMBOLS)
    return doc


def model(variant='baseline', seen=None):
    doc = document()
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(footnote.model(footnote.document(True)))
    assert values['wa']() == 'author' and values['hzia']() == 'question'
    expected = query_syntax('bf' if variant == 'other_title_concept' else 'bi', 'wh', 'hzv6')

    def title(node, author, code, scene):
        if variant == 'unknown_title':
            return unknown()
        if seen is not None:
            seen.setdefault('title_codes', []).append(json.loads(code.syntax))
        return variant != 'no_title' and (node, author, scene) == ('question', 'author', 'text') and code.rank == 1 and json.loads(code.syntax) == expected

    values.update(wb=lambda: 'opening', wh=lambda: 'text', hzib=title,
        ua=lambda node, author, code, scene: (node, author, scene) == ('opening', 'author', 'text') and ref(code, 'bi'),
        ue=lambda first, second, scene: (first, second, scene) == ('question', 'opening', 'text'),
        hzcs=lambda author, question, answer, scene: (author, question, answer, scene) == (
            ('author', 'opening', 'question', 'text') if variant == 'reverse_response' else ('author', 'question', 'opening', 'text')))
    answers = values['hzjj']

    def answer_reference(mention, work, question, scene):
        if seen is not None:
            seen.setdefault('answer_references', []).append([mention, work, question, scene])
        if variant == 'unknown_current_reference' and mention == 'selfmention':
            return unknown()
        if variant == 'other_current_question' and mention == 'selfmention':
            return (work, question, scene) == ('document', 'other', 'note')
        if variant == 'other_prior_question' and mention == 'citation':
            return (work, question, scene) == ('answer', 'other', 'note')
        if variant == 'prior_citation_only' and mention == 'selfmention':
            return False
        return answers(mention, work, question, scene)

    values['hzjj'] = answer_reference
    if variant == 'no_note_link':
        values['hzly'] = lambda *args: False
    if variant == 'no_projected_classification':
        values['du'] = lambda *args: False
    if variant == 'no_courtesy':
        values['hzlq'] = lambda *args: False
    if variant == 'other_trial_question':
        values['hzky'] = lambda role, code, scene: (role, scene) == ('trial', 'note') and json.loads(code.syntax) == {
            'kind': 'call', 'symbol': 'hzll', 'arguments': []}
    if variant == 'actual_receipt':
        received = values['hzji']
        values['hzji'] = lambda p, w, t, s: received(p, w, t, s) or (p, w, t, s) == ('author', 'answer', 'past', 'note')
    if variant == 'unknown_branch_receipt':
        received = values['hzji']
        values['hzji'] = lambda p, w, t, s: unknown() if s == 'branch' else received(p, w, t, s)
    # Neither the answer to the title nor the answer to the trial question is
    # needed to report their presentation. No finite substitutes are supplied.
    for symbol in ('hzv6', 'aa', 'hzma', 'hzku', 'hzkw', 'hzkx', 'hzlf', 'hzlg', 'hzlh', 'hzli'):
        values[symbol] = unknown
    return {d['name']: values[d['name']] for d in doc['declarations'] if d['kind'] == 'primitive'}


def evaluate(values):
    return [r['value'] for r in evaluate_document(document(), individuals=DOMAIN, situations=SCENES,
        primitives=values, max_steps=3000000, memoize_definitions=False, memoize_expressions=False)]


EXPECTED_FALSE = {
    'baseline': (), 'no_title': (0, 10), 'other_title_concept': (0, 10), 'reverse_response': (10,),
    'other_current_question': (7,), 'other_prior_question': (1,), 'prior_citation_only': (7,),
    'no_note_link': (8,), 'no_projected_classification': (9,), 'no_courtesy': (6, 9),
    'other_trial_question': (5,), 'actual_receipt': (2, 4),
}


def joint_checks():
    rows, seen = {}, {}
    for variant, false in EXPECTED_FALSE.items():
        actual = evaluate(model(variant, seen))
        assert actual == [i not in false for i in range(11)], (variant, actual)
        rows[variant] = actual
    assert seen['title_codes'] and all(code == query_syntax('bi', 'wh', 'hzv6') for code in seen['title_codes'])
    assert ['citation', 'answer', 'question', 'note'] in seen['answer_references']
    assert ['selfmention', 'document', 'question', 'note'] in seen['answer_references']
    for variant in ('unknown_title', 'unknown_current_reference', 'unknown_branch_receipt'):
        try:
            evaluate(model(variant))
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(variant)
    return dict(cases=rows, unknown_inputs_refused=3, selected_statements=SELECTION,
        title_and_both_answer_references_share_one_question=True,
        current_document_prior_work_and_opening_node_are_distinct=True,
        title_and_footnote_contexts_are_distinct=True,
        answer_truth_and_actual_gender_classification_remain_unknown=True,
        stored_graph_without_lowering=True, memoization=False)


def scope_checks():
    doc = document()
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    validate_hashes(ROOT, index['source_sha256'])
    active = index['works']['kant-1784']
    assert active['document'] == DOCUMENT and active['meaning_basis'] == BASIS
    assert len(active['reviews']) == 10
    for path in active['reviews']:
        review = json.loads((ROOT / path).read_text(encoding='utf-8'))
        indices = [s['index'] for s in review['selection']['statements']]
        assert selection_binding(catalog(), indices) == review['selection']
    assert len(catalog().document['statements']) == 41
    return dict(active_index=INDEX, active_document=DOCUMENT, preserved_review_selections=10,
        manuscript_statements=41, selected_graph_roundtrips=True, new_definitions=0, new_primitives=0)


def audit():
    old = json.loads((ROOT / 'data/footnote-audit-v1.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT, old['source_sha256'])
    result = deepcopy(old)
    result.update(document=DOCUMENT, meaning_basis=BASIS, supersedes='data/footnote-audit-v1.json',
        selection=selection_binding(catalog(), list(range(18, 27))),
        context_selection=selection_binding(catalog(), [0, 40]))
    result.pop('direct_reference_users')
    changes = {
        'clause-1': ('represented_under_reading', ['hzlz', 'rqsm'], '現行の注・本文末尾の標識・同じ文書・著者表示をhzlzで接続する。原刊494頁の二標識を再確認した。直前の命題への論理的な説明を補わない。'),
        'clause-5': ('represented_under_reading', ['hzjt', 'hzlr', 'hzmd', 'hzva'], '案内中の先の回答と、表題に提示された同じ問いを結ぶ。脚注自身の敬称使用には丁寧さと男性向け分類の描写を接続するという読みを採用する。Adelungの第三の語義を補助資料とし、具体的身分・権限・内心の敬意や本人の実際の属性は補わない。'),
        'clause-7': ('represented_under_reading', ['hzkt', 'hzkr', 'hzks', 'hzlt', 'hzva', 'hzvb'], '先の回答を受領していたならその影響で現在の論説を差し控えたという読み。現在の論説への言及hzltと先の回答の紹介hzjtが、表題の同じ問いhziaを指すことを同時に検査する。冒頭の回答箇所wbと文献hzikは別個体とし、差し控える段階は限定しない。'),
        'clause-8': ('represented_under_reading', ['hzle', 'hzlb', 'hzky', 'rqrw', 'hzlz'], '原刊のmagをここでの提示を容認する態度、nurを同じ問いを検討する試みという種類への限定として採用する。比較対象の位置付けは同じ著者・文書・文脈に限定する。試みの成功や問いの答え、文献の全価値の限定を加えない。'),
    }
    for clause in result['clauses']:
        if clause['id'] in changes:
            clause['assessment'], clause['symbols'], clause['reason'] = changes[clause['id']]
    result['closed_items'] = [
        dict(id='current-answer-question', evidence=['hzlt', 'hzva', 'hzvb'], status='connected_and_jointly_checked'),
        dict(id='note-attachment', evidence=['rqsm', 'hzlz'], status='connected_and_jointly_checked'),
        dict(id='honorific-convention', evidence=['rqsl', 'hzlr', 'hzmd'], status='represented_under_stated_contextual_reading'),
        dict(id='trial-limitation-and-tolerated-presentation', evidence=['rqrw', 'hzle'], status='represented_under_stated_contextual_reading'),
    ]
    result['open_items'] = [
        dict(id='periodical-description', source_ranges=[[3, 72]], symbols=['hzkd', 'hzke', 'hzkk'],
            next_action='Büschingへの帰属と週刊という説明を、固有呼称の使用と区別して記述する。人名を含む名称個体だけで説明済みにせず、実際の全刊行日時の規則性も要求しない。',
            completion_evidence='名称から独立した人物・系列・周期の記述、原文における提示範囲の選択、別系列・別周期・欠刊の対照を伴う接続。'),
        dict(id='chance-and-agreement-criterion', source_ranges=[[394, 462]], symbols=['hzkw', 'hzkx', 'hzkv', 'hzli', 'hzld'],
            next_action='この文脈での偶発性と内容対応を明示する。構文同一性rqrzだけへ一致を狭めず、hzllを使う場合は原文に適した比較基準を指定する。実際の二文献の全思想抽出や答えの計算は前提にしない。',
            completion_evidence='未読の別回答との意図的調整を補わない偶発性の読み、同義の別構文と同じ真偽だけの異内容を区別する対応規約、同じ問いへの非事実的な接続。'),
    ]
    result['sources_revisited'] = [
        dict(path='artifacts/author-signature-facsimile-v1/page-494.jpg', visually_inspected=True, page=494),
        dict(url='https://korpora.org/Kant/aa08/042.html', use='著者注の電子本文と原刊との対照。'),
        dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009132_3_1_1987',
            use='第三語義の男性向け敬称と丁寧な言及を参照する。後年の辞書を1784年の全慣習と同一視しない。'),
    ]
    result['limits'] = [
        '九つの脚注主張と表題・冒頭回答接続の同時解釈を検査する。二つの未解決項目があり、脚注全体の意味一致は未確認である。',
        '句ごとのrepresented_under_readingは採用した読みについてのアシスタント判断であり、独立査読や自動的な意味証明ではない。',
        '本文・文法・意味規約・文字体系・対応範囲・意味確認済み全文単位数を変更しない。',
    ]
    paths = set(catalog().source_sha256) | {INDEX, INVENTORY, 'data/footnote-audit-v1.json',
        'artifacts/author-signature-facsimile-v1/page-494.jpg', 'reports/current-answer-v1.json',
        'reports/attached-note-v1.json', 'reports/projected-classification-v1.json', 'reports/explanatory-question-v1.json'}
    result['source_sha256'] = {p: digest((ROOT / p).read_bytes()) for p in sorted(paths)}
    return result


def audit_checks():
    result = audit()
    assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == result
    unit = next(u for u in json.loads((ROOT / INVENTORY).read_text(encoding='utf-8'))['units'] if u['id'] == result['unit'])
    assert result['text'] == unit['text'] and result['unit_sha256'] == unit['text_sha256']
    cursor = 0
    for clause in result['clauses']:
        start, end = clause['range']
        assert start == cursor < end and clause['source'] == unit['text'][start:end]
        assert all(s in catalog().entries for s in clause['symbols'])
        cursor = end
    assert cursor == len(unit['text']) and result['decision'] == 'incomplete'
    assert {c['id'] for c in result['clauses'] if c['assessment'] == 'open'} == {'clause-2', 'clause-9'}
    return dict(source_partition_complete=True, clauses=9, open_clauses=2, closed_followup_items=4,
        whole_unit_decision='incomplete', full_unit_review_added=False)


def build_report():
    checks = joint_checks()
    print('Eleven connected assertions checked in twelve models', flush=True)
    scope, audit_result = scope_checks(), audit_checks()
    paths = set(audit()['source_sha256']) | {AUDIT, 'scripts/check_current_footnote.py',
        'tests/test_current_footnote.py', 'docs/footnote-audit-v2.md',
        'scripts/check_projected_classification.py', 'scripts/check_attached_note.py',
        'scripts/check_current_answer.py', 'scripts/check_footnote_joint.py',
        'scripts/check_announced_answer.py', 'scripts/check_courteous_reference.py',
        'scripts/check_explanatory_question.py', 'scripts/compose_falling_depiction.py',
        'noema/constructed.py', 'noema/constructed_semantics.py', 'noema/meaning_catalog.py',
        'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='current_title_and_footnote_joint_models_with_incomplete_source_audit',
        document=DOCUMENT, selection=selection_binding(catalog(), SELECTION), checks=checks, scope=scope,
        audit=audit_result, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit()))
    report = build_report()
    if args.verify_only:
        assert json.loads((ROOT / REPORT).read_text(encoding='utf-8')) == report
    else:
        write_exact(ROOT / REPORT, encoded(report))
    print('Active title and footnote checked; two source gaps remain explicit', flush=True)


if __name__ == '__main__':
    main()
