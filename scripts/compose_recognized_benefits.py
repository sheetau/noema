"""Bind favorable achieved states to their agents, then distinguish recognition."""
from copy import deepcopy
import json
from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_first_achievers import GOAL, ACHIEVES
from scripts.compose_personal_criteria import JUDGING, APPRAISAL
from scripts.compose_policy_norms import DESCRIPTION

PARENT = 'examples/v014/kant-cohort-responses.noema'
FAVOR = 'h[a ' + GOAL + ' d] c'
EPISODE = [('person', 'a'), ('activity', 'a'), ('target', 'a'), ('goal', GOAL), ('context', 'd'),
    ('history', 'h[d] c'), ('before', 'h[d d] c'), ('achieves', ACHIEVES), ('favor', FAVOR)]
SETTINGS = [('goal', GOAL), ('histories', 'h[d] h[d] c'), ('orders', 'h[d] h[d d] c'), ('achievements', 'h[d] ' + ACHIEVES), ('favor', FAVOR)]
RECOGNITION = [('criterion', DESCRIPTION), ('activity', 'a')] + JUDGING
SOURCE_RECOGNITION = [(n, t) for n, t in RECOGNITION if n not in ('judgments', 'matters')]
ROOTS = ['roo', 'rop', 'roq', 'ror', 'ros']


def definitions():
    completed = both(app(v('history'), v('completion')),
        op('x', op('e', v('completion'), v('context')), app(v('before'), v('completion'), v('context'))),
        app(v('achieves'), v('person'), v('activity'), v('target'), v('goal'), v('completion')))
    body = both(k('ta', v('history'), v('before')), app(v('history'), v('context')),
        quant('g', 'completion', 'd', completed), app(v('favor'), v('target'), v('goal'), v('context')))
    text = definition('roo', params(EPISODE), body)
    fields = args(EPISODE, history=app(v('histories'), v('context')), before=app(v('orders'), v('context')), achieves=app(v('achievements'), v('context')))
    text += definition('rop', params(SETTINGS), 'i[target a person a activity a][b context[' + k('roo', *fields) + ']]', 'h[a a a] e')
    slots = [('target', 'a'), ('person', 'a'), ('activity', 'a')]
    initial = 'i[' + params(slots) + '][' + app(v('relation'), *args(slots)) + ']'
    step = 'i[state h[a a a] e item a][i[' + params(slots) + '][' + app(v('state'), v('item'), v('target'), v('person')) + ']]'
    folded = 'q[v bindings][' + initial + '][' + step + ']'
    result = op('t', app(folded, v('seed'), v('seed'), v('seed')), v('context'))
    text += definition('roq', 'relation h[a a a] e', 'i[bindings j[a]][b context[' + both(k('rdr', v('bindings'), 'n p d b'), quant('g', 'seed', 'a', result)) + ']]', 'h[j[a]] e')
    judgment = k('rlg', *args(APPRAISAL, person=v('target'), subject=v('person'), bindings='l[a][v target v person v activity]'))
    text += definition('ror', params(RECOGNITION), 'i[target a person a][b context[' + quant('g', 'judgment', 'a', judgment) + ']]', 'h[a a] e')
    text += definition('ros', 'recognition h[a a] e response h[a a a] e', 'i[speaker a activity a subject a][b context[' + both(
        op('t', app(v('recognition'), v('speaker'), v('subject')), v('context')),
        op('t', app(v('response'), v('speaker'), v('activity'), v('subject')), v('context'))) + ']]', 'h[a a a] e')
    return text


MEANINGS = {
    'roo': '同じ履歴内の基準時までに、指定行為者の指定行為が同じ受益対象・目標記述について達成し、対象者が基準時にその自分の状態を好ましく受け入れる。未来の達成や別行為・別対象・別の目標で代用しない。',
    'rop': '目標と、評価文脈ごとの履歴・順序・達成関係・受容関係を固定し、受益対象・行為者・行為の三者にrooの内容を割り当てる。現実の履歴と判断候補の履歴を区別できる。',
    'roq': '三引数の内容関数を、受益対象・行為者・行為の順序付き三個体列へ接続する。各位置と重複を保ち、列の長さが三でないときは成立しない。',
    'ror': '受益対象を判断主体、行為者を判断対象とするrlgの判断があり、同じ基準記述と受益対象・行為者・行為の引数列について非空の候補全てで成立すると認めている。基準の現実の真理は要求しない。任意の基準を恩恵とみなす定義ではない。',
    'ros': '同じ時点に、応答者が同じ応答対象について指定認識を持ち、同じ応答行為が成立する。認識だけでも応答だけでも足りない。認識が応答の心理的原因であることは要求しない。',
    'hzgk': 'ropの候補ごとの達成関係を、同じ目標のhzgeによる状態変化・生起・関与・生成へ接続し、好ましい受容をidに結ぶ。roqで同じ三個体列に適用する。',
    'hzgl': 'rorの判断主体と判断対象をfa・fbへ接続する。hzgkの閉じた基準を渡すと、本人が指定行為者から好ましい結果を得たと認める内容になる。恩恵の真理、感謝の情緒、応答の実行を補わない。',
}
LIMITS = [
    '感謝の構成要素として、好ましい結果の受容とその行為者への認識を記述する。これを感謝の必要十分条件とはしない。単に自分の結果を喜びながら相手を嫌う場合を、感謝と認定しない。',
    'idは記述された自分の状態への好ましい受容であり、相手への好意ではない。好ましく受け入れることを、客観的な福利・道徳的な善・自由な同意・害の不在に置き換えない。',
    '同じ受益対象・行為者・行為・目標記述を保持する。行為者による善意や意図、唯一の原因、恩返しの義務、代表資格、現在も結果が続くことは要求しない。',
    'histories・orders・achievementsは評価文脈ごとに明示する。同じ現実の記録を全判断候補へ強制せず、誤認も記述する。候補履歴の選択や現実への接続は有限モデルの真偽だけで保証されない。',
    'rooは過去または同時の達成を扱う。後続者が過去の行為から間接的に得る利益、別人や共同体への恩恵を理由にする感謝、未達成の善意への感謝はこの条件をそのまま当てはめず別の説明が必要である。',
    'hzgkの目標への脱引用、hzglの基準への脱引用は、引用に使う前に同じ閉じた記述へ静的特殊化する。未知の基準を実行時に生成して補完しない。',
    'rosは認識と応答の同時成立であり、感謝を表す発話、真摯さ、心情に基づく動機、敬意、肯定的報告と称賛の違いは未完。原文dankbarenへの構成要素の注記であり、語義全体の翻訳や新たな著者主張ではない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    achievements = 'i[context d][' + k('hzge', app(v('histories'), v('context')), app(v('orders'), v('context')), v('goal')) + ']'
    text = definitions() + definition('hzgk', params(SETTINGS[:3]), k('roq', k('rop', *args(SETTINGS, achievements=achievements, favor='p id'))), 'h[j[a]] e')
    text += definition('hzgl', params(SOURCE_RECOGNITION), k('ror', *args(RECOGNITION, judgments='p fa', matters='p fb')), 'h[a a] e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-cohort-responses-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-recognized-benefits-basis-v1', document='examples/v014/kant-recognized-benefits.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS; audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text); selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'recognized-benefits')
def core_composed(): return projected(ROOTS + ['hzgk', 'hzgl', 'hzgj'], 'recognized-benefits-core')
BUILDERS = ((generic_composed, 'recognized-benefits'), (source_composed, 'kant-recognized-benefits'), (core_composed, 'recognized-benefits-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored recognized benefit differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
