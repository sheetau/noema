"""Separate scoped classification, shared reference and personal epoch labels."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_enlightening_epoch import PROGRESS

PARENT = 'examples/v014/kant-opening-opportunities.noema'
PROPERTY = 'i[h[a] e]'
PRESENTS = 'h[a a ' + PROPERTY + ' ' + PROPERTY + ' d] c'
OFFICE = [('office', 'a'), ('firstyear', 'b'), ('lastyear', 'b'), ('eligible', 'h[a] c'), ('tenures', 'h[a a b b d] c')]
IDENTITY = [('subject', 'a'), ('scope', 'h[a] c'), ('profile', 'h[a] e'), ('context', 'd')]
EPONYM = [('person', 'a'), ('office', 'a'), ('history', 'h[d] c'), ('before', 'h[d d] c'),
    ('periods', 'h[a d] c'), ('eligible', 'h[a] c'), ('holds', 'h[a a d] c')]
LABELS = [('node', 'a'), ('author', 'a'), ('referent', PROPERTY), ('aspect', PROPERTY), ('label', PROPERTY),
    ('context', 'd'), ('presents', PRESENTS)]
REFERENCED = LABELS + [('subject', 'a'), ('scope', 'h[a] c')]
ASPECT = [(n, t) for n, t in PROGRESS if n not in ('epoch', 'context')]
SOURCE_EPONYM = [(n, t) for n, t in EPONYM if n != 'eligible']
SOURCE_OFFICE = [('office', 'a'), ('tenures', 'h[a a b b d] c')]
SOURCE_IDENTITY = [('person', 'a'), ('scope', 'h[a] c'), ('context', 'd')] + SOURCE_OFFICE
ROOTS = ['rmu', 'rmv', 'rmw', 'rmx', 'rmy', 'rmz']


def definitions():
    profile = both(app(v('eligible'), v('person')), app(v('tenures'), v('person'), v('office'), v('firstyear'), v('lastyear'), v('context')))
    text = definition('rmu', params(OFFICE), 'i[person a][b context[' + profile + ']]', 'h[a] e')
    matches = lambda name: both(app(v('scope'), v(name)), op('t', app(v('profile'), v(name)), v('context')))
    text += definition('rmv', params(IDENTITY), both(matches('subject'),
        quant('f', 'other', 'a', op('y', matches('other'), op('e', v('other'), v('subject'))))))
    overlap = quant('g', 'point', 'd', both(app(v('periods'), v('epoch'), v('point')),
        app(v('holds'), v('person'), v('office'), v('point'))))
    text += definition('rmw', params(EPONYM), 'i[epoch a][b context[' + both(
        app(v('eligible'), v('person')), k('rjc', v('epoch'), v('history'), v('before'), v('periods')), overlap) + ']]', 'h[a] e')
    naming = lambda label: k('rq', v('node'), v('author'), v('referent'), v(label), v('context'), v('presents'))
    text += definition('rmx', params(LABELS), both(op('u', op('e', v('aspect'), v('label'))), naming('aspect'), naming('label')))
    identity = k('rmv', *args(IDENTITY, profile='s[v referent]'))
    text += definition('rmy', params(REFERENCED), both(k('rmx', *args(LABELS)), identity))
    text += definition('rmz', params(REFERENCED), both(k('rmy', *args(REFERENCED)),
        op('t', app('s[v aspect]', v('subject')), v('context'))))
    return text


MEANINGS = {
    'rmu': '明示した役職と始年・終年に対する在職記録を、同じ候補者の識別用の性質へ接続する。記録の意味と年の暦・粒度は入力規約に従う。',
    'rmv': '同じ評価文脈で、明示した候補範囲のうち指定性質に当てはまる者が、指定対象ただ一つである。名前の綴りや同じ呼称だけでは同定しない。',
    'rmw': '指定人物が指定役職を持つ時点と重なる非空の時代区間という描写。時代と在職期間の同一性、百年の長さ、その人物による因果や功績の独占は含めない。',
    'rmx': '同じ著者・箇所・文脈が、同じ対象記述に、観点となる性質記述と別の呼称記述を用いる。記述の内容を実行せず、二描写を一般的な同義語や排他的選択肢とはしない。',
    'rmy': 'rmxに加え、同じ候補範囲で対象記述が指定対象を一意に指す。観点と呼称の内容が実際に真であることは要求しない。',
    'rmz': 'rmyに加え、指定対象について同じ観点の性質が現在実際に成立する。呼称の内容の真理や、他の観点での分類までは追加しない。',
    'hzfj': '同じ履歴・時代範囲・人々・生存関係・進行内容を固定し、時代ごとにrmkの現在の進行条件を返す。到達条件rmjや全観点での評価へ置き換えない。',
    'hzfk': 'rmwの人物候補を人aaへ結ぶ。人物の在職と重なる時代という呼称用の描写であり、歴史的な人物・役職の同定は別に行う。',
    'hzfl': '人aaであり、指定した役職の始年1740・終年1786という在職記録を持つ候補を返す。フリードリヒ二世の参照確認に使う編集上の年単位プロフィールで、原文に年を補って著者の主張にしない。',
    'hzfm': 'hzflのプロフィールを同じ候補範囲と文脈でrmvへ渡し、指定人物が唯一の該当者であることを確認する。役職の歴史的同定と記録の信頼性を代用しない。',
}
LIMITS = [
    'この観点を、閉じた性質記述hzfjへの参照で保持する。他の観点を列挙したり、他の観点では必ず偽だとしたり、啓蒙された状態への到達を補ったりしない。',
    '原文のoderを同じ対象への別の描写として読む候補である。二つの描写の一般的同義性・論理的同値や排他的な二者択一を主張しない。',
    '人物に結ぶ時代の描写には在職時点との重なりを使う。原文のJahrhundertを厳密な百年区間とする読み、称賛の強さ、歴史的な時代区分の境界は確定しない。',
    '在職プロフィールと候補範囲は人物参照を検査するための編集上の情報であり、原文の意味へ歴史的な年の主張を追加するものではない。未知・複数候補・不在は一意な人物へ補完しない。',
    'プロイセンの王位という役職そのものの制度的説明、年の暦や精度、記録の真実性、フリードリヒという綴りの社会的な命名過程は入力規約として残る。',
    '単なる呼称の使用は描写の真理を保証しない。本文末を進行の主張と接続する場合はrmzと同じ進行内容を別に確認する。著者帰属と段落全体の意味確認は未完である。',
    '呼称提示の関係は一般の対象を扱うpresents引数で明示する。既存duの人々に対する呼称の意味規約を、時代へ暗黙に拡張しない。具体的な著者の提示を確定するには別途記録が必要である。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    text += definition('hzfj', params(ASPECT), 'i[epoch a][b context[' + k('rmk', *args(PROGRESS)) + ']]', 'h[a] e')
    text += definition('hzfk', params(SOURCE_EPONYM), k('rmw', *args(EPONYM, eligible='p aa')), 'h[a] e')
    text += definition('hzfl', params(SOURCE_OFFICE), k('rmu', *args(OFFICE,
        eligible='p aa', firstyear='n p ' + number_word(1740) + ' b', lastyear='n p ' + number_word(1786) + ' b')), 'h[a] e')
    text += definition('hzfm', params(SOURCE_IDENTITY), k('rmv', *args(IDENTITY,
        subject=v('person'), profile=k('hzfl', *args(SOURCE_OFFICE)))))
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-opening-opportunities-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-named-epochs-basis-v1', document='examples/v014/kant-named-epochs.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'named-epochs')
def core_composed():
    from scripts.compose_opening_opportunities import ROOTS as OPENING
    return projected(ROOTS + OPENING + ['hzfj', 'hzfk', 'hzfl', 'hzfm', 'hzff', 'hzfg', 'hzfh', 'hzfi',
        'hzfa', 'hzey', 'hzez', 'hzcu', 'rmd', 'rme', 'rmf', 'rmg', 'rmh', 'rmi', 'rmj', 'rmk', 'rml', 'hzfb', 'hzfc', 'hzfd', 'hzfe'], 'named-epochs-core')
BUILDERS = ((generic_composed, 'named-epochs'), (source_composed, 'kant-named-epochs'), (core_composed, 'named-epochs-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored named epochs differ: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
