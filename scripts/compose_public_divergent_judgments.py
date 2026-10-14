"""Bind divergent judgment, self-attributed presentation and review purpose."""
from copy import deepcopy
import json
from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.specialization import specialize_definition
from scripts.check_assessed_payments import description
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_situated_criticism import params, args, MESSAGE
from scripts.compose_partial_divergence import POINT, DESCRIPTION
from scripts.compose_speech_principals import PUBLIC, VOICE

PARENT = 'examples/v014/kant-partial-divergence.noema'
JUDGMENT = POINT + [('organization', 'a'), ('adopted', 'h[a ' + DESCRIPTION + ' d] c')]
SOURCE_JUDGMENT = [(n, t) for n, t in JUDGMENT if n not in ('judgments', 'matters')]
JOIN = [('qualification', 'h[a d] c'), ('presentation', 'h[a a] e'), ('goal', 'i[e]'), ('aims', 'h[a a i[e] d] c')]
FRAME = [(n, t) for n, t in SOURCE_JUDGMENT if n not in ('person', 'judgment', 'context', 'cases')] + [
    ('judgmentfor', 'h[a d] a'), ('comparisons', 'h[a d] c'), ('role', 'a'), ('audience', 'h[a] c'),
    ('recipient', 'a'), ('channel', 'a'), ('voices', VOICE), ('message', MESSAGE), ('goal', 'i[e]')]
ROOTS = ['rpi', 'rpj', 'rpk']


def definitions():
    text = definition('rpi', 'criterion ' + DESCRIPTION, 'i[subject a][j s[' + app('s[v criterion]', 'l[a][v subject]') + ']]', 'h[a] f')
    text += definition('rpj', params(JUDGMENT), both(k('rpe', *args(POINT)), app(v('adopted'), v('organization'), v('standardcriterion'), v('context'))))
    body = both(app(v('qualification'), v('person'), v('context')), op('t', app(v('presentation'), v('person'), v('activity')), v('context')),
        app(v('aims'), v('person'), v('activity'), v('goal'), v('context')))
    text += definition('rpk', params(JOIN), 'i[person a activity a][b context[' + body + ']]', 'h[a a] e')
    return text


MEANINGS = {
    'rpi': '同じ論点を唯一の引数とした基準内容を述べる主張の発話関数を作る。基準への賛同、内容の真理、実際の伝達とは区別する。',
    'rpj': 'rpeの同じ本人の同じ論点についての判断と、比較に使った同じ基準記述を同じ文脈で組織が採用している条件を結ぶ。別論点での相違を発表対象の相違へ代用しない。',
    'rpk': '同じ人・活動・文脈に、人物の資格条件、実際の提示内容、同じ目的記述への意図を結ぶ実行内容関数。目的の達成は要求せず、目的を持つことだけで実行を推論しない。',
    'hzgx': 'rpjの判断主体・対象を既存fa・fbへ接続する。これから提示する同じ論点の判断を選ぶ条件として使う。',
    'hzgy': '同じ本人・文脈のhzgx、本人を帰属先とする公的提示hzb4、同じ活動での目的hzuをrpkで結ぶ。本人と活動を引数に取る実行内容を作り、許可や義務保存の同一対象にできる。',
}
LIMITS = [
    'FRAMEだけでは任意のmessageとgoalを受け取れる。bind_presentationは本人の基準から主張rpiを作り、その同じ主張・論点・公衆への判断hzxを目的にし、その二つをhzgyへ渡す。内容の取り違えを防ぐこの閉じた構成を検証対象とする。',
    '閉じたNoema式を接続する処理であり、自然言語の推測・モデル生成・対訳辞書は使わない。静的特殊化は未知の脱引用を除き、構成結果は通常のNoema文書として解析・引用できる。',
    'hzgyの内容を引用して同じ人・活動・公的役割へのhzguに渡す。許可、義務が免除されない条件、実際の提示、目的達成を別々に保つ。許可時点での発言・個人的判断の実在は要求しない。',
    '採用基準の記述と論点は固定し、実行候補で同じ基準の採用と本人の判断が成立することを対象行為の条件にする。基準の現実での真理や全状況での採用は保証しない。',
    '一度の提示と一論点を扱う。複数の判断・洞察を同時に示す一般化、教理・聖職者・敬意の評価、学者と世界の社会的意味、君主への照応は未完。個別の教義内容を補わない。',
    '公衆の判断は少なくとも一人が同じ内容を評価する目的として部分記述する。全員の受領・理解・正しい評価・同意・実効的なアクセスをそれだけで認定しない。',
    '本文の許可を特定の人物が実際に行使したとの著者主張へ置き換えない。公的提示と義務保持を結ぶ部分構成であり、全文の意味一致や新たな著者主張の確認ではない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions() + definition('hzgx', params(SOURCE_JUDGMENT), k('rpj', *args(JUDGMENT, judgments='p fa', matters='p fb')))
    qualification = 'i[person a context d][' + k('hzgx', *args(SOURCE_JUDGMENT,
        judgment=app(v('judgmentfor'), v('person'), v('context')),
        cases='i[point d][' + app(v('comparisons'), v('subject'), v('point')) + ']')) + ']'
    presentation = 'i[person a activity a][b context[' + k('hzb4', *args(PUBLIC)) + ']]'
    text += definition('hzgy', params(FRAME), k('rpk', qualification, presentation, v('goal'), 'p hzu'), 'h[a a] e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-partial-divergence-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-public-divergent-judgments-basis-v1', document='examples/v014/kant-public-divergent-judgments.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS; audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def bind_presentation(doc, bindings, message_name='jzmessage', target_name='jztarget'):
    """Bind closed expressions into an ordinary, quotable Noema action description.

    No model is evaluated. Message and purpose are derived here, never accepted
    as independent caller inputs. All externally supplied expressions must be closed.
    """
    expected = {n for n, _ in FRAME} - {'message', 'goal'}
    if set(bindings) != expected: raise ValueError('Presentation bindings must contain exactly: ' + ', '.join(sorted(expected)))
    expressions = {name: description(doc, expr)['body'] for name, expr in bindings.items()}
    for name in ('owncriterion', 'standardcriterion'):
        if expressions[name]['kind'] != 'quote': raise ValueError('Criterion must be an explicit closed quotation: ' + name)
    first = specialize_definition(doc, 'rpi', message_name, {0: expressions['owncriterion']})
    fixed = {i: expressions[n] for i, (n, _) in enumerate(FRAME) if n in ('owncriterion', 'standardcriterion')}
    second = specialize_definition(first.document, 'hzgy', target_name, fixed)
    message = 'r[' + k(message_name) + ']'
    goal = 'r[' + k('hzx', bindings['recipient'], bindings['subject'], message) + ']'
    refs = bindings | dict(message=message, goal=goal)
    action = k(target_name, *(refs[n] for n, _ in FRAME if n not in ('owncriterion', 'standardcriterion')))
    description(second.document, action)  # Enforce closedness and absence of unresolved dequotation.
    return dict(document=second.document, message=message, goal=goal, action=action,
        disquotations_removed=first.disquotations_removed + second.disquotations_removed)


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text); selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'public-divergent-judgments')
def core_composed(): return projected(ROOTS + ['hzgx', 'hzgy', 'hzx', 'hzgu', 'rp6', 'rpa'], 'public-divergent-judgments-core')
BUILDERS = ((generic_composed, 'public-divergent-judgments'), (source_composed, 'kant-public-divergent-judgments'), (core_composed, 'public-divergent-judgments-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored public divergent judgment differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
