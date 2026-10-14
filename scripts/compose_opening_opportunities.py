"""Describe newly available pursuits without inferring effort or achieved ability."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_declining_hindrances import TIME, SOURCE as DECLINE
from scripts.compose_clear_indications import SOURCE as PRIOR_PROGRESS
from scripts.compose_described_norms import DESCRIPTION

PARENT = 'examples/v014/kant-enlightening-epoch.noema'
FRAME = TIME + [('people', 'h[a] c'), ('activities', 'h[a a] c'), ('assessed', 'h[a a d] c')]
FAMILY = FRAME + [('opportunities', 'h[a a] e')]
PAIR = [('person', 'a'), ('activity', 'a'), ('assessed', 'h[a a d] c'), ('opportunities', 'h[a a] e'), ('start', 'd'), ('end', 'd')]
WITNESS = [('processes', 'h[a a] a'), ('transitions', 'h[a d d] c'), ('affected', 'h[a a d d] c'), ('occurs', 'h[a d] c')]
PROCESS = FAMILY + WITNESS
OPPORTUNITIES = [('authority', 'a'), ('roles', 'h[a] a'), ('execution', DESCRIPTION)]
SOURCE = FRAME + OPPORTUNITIES
SOURCE_PROCESS = SOURCE + WITNESS[:1]
COMBINED = PRIOR_PROGRESS + [('activities', 'h[a a] c'), ('assessed', 'h[a a d] c'), ('processes', 'h[a a] a')]
ROOTS = ['rmo', 'rmp', 'rmq', 'rmr', 'rms', 'rmt']


def definitions():
    person = app(v('people'), v('person')); activity = app(v('activities'), v('person'), v('activity'))
    selected = both(person, activity)
    at = lambda point: op('t', app(v('opportunities'), v('person'), v('activity')), v(point))
    checked = both(app(v('assessed'), v('person'), v('activity'), v('start')),
        app(v('assessed'), v('person'), v('activity'), v('end')))
    text = definition('rmo', params(FRAME), both(k('ta', v('history'), v('before')),
        app(v('history'), v('start')), app(v('history'), v('end')), app(v('before'), v('start'), v('end')),
        quant('g', 'person', 'a', person), quant('f', 'person', 'a', op('y', person, quant('g', 'activity', 'a', activity))),
        quant('f', 'person', 'a', quant('f', 'activity', 'a', op('y', selected, checked)))))
    text += definition('rmp', params(PAIR), both(checked, op('u', at('start')), at('end')))
    gained = k('rmp', *args(PAIR))
    each_gains = quant('f', 'person', 'a', op('y', person, quant('g', 'activity', 'a', both(activity, gained))))
    text += definition('rmq', params(FAMILY), both(k('rmo', *args(FRAME)), each_gains))
    retained = quant('f', 'person', 'a', quant('f', 'activity', 'a', op('y', both(selected, at('start')), at('end'))))
    some_gain = quant('g', 'person', 'a', quant('g', 'activity', 'a', both(selected, gained)))
    text += definition('rmr', params(FAMILY), both(k('rmo', *args(FRAME)), retained, some_gain))
    text += definition('rms', params(FAMILY), both(k('rmq', *args(FAMILY)), k('rmr', *args(FAMILY))))
    process = app(v('processes'), v('person'), v('activity'))
    witness = both(activity, gained, k('tg', v('history'), v('before'), process, v('start'), v('end'), v('transitions')),
        app(v('affected'), v('person'), process, v('start'), v('end')), app(v('occurs'), process, v('end')))
    text += definition('rmt', params(PROCESS), both(k('rmq', *args(FAMILY)),
        quant('f', 'person', 'a', op('y', person, quant('g', 'activity', 'a', witness)))))
    return text


MEANINGS = {
    'rmo': '同じ順序付き履歴内で始点と終点が前後し、明示した人々が非空で、各人に固定した候補活動が一つ以上あり、その全候補の前後評価が済んでいる。',
    'rmp': '同じ本人・活動の機会について前後の評価が済み、前では機会がなく後ではある。順序・対象範囲は呼出側rmoで検査する。',
    'rmq': 'rmoの同じ対象者全員に、固定した候補内で新しく生じる機会が一つ以上ある。以前に他の機会がなかったことや、その保持は要求しない。',
    'rmr': 'rmoの同じ対象者・候補について、前にあった機会が全て後にもあり、少なくとも一人・一活動に新しい機会がある。他の人にも新しい機会が生じるとは限らない。',
    'rms': 'rmqとrmrがともに成立する。全員に新しい機会があり、同じ固定候補内で以前の機会を失わないという強い比較条件。',
    'rmt': 'rmqの各人に、同じ活動の新しい機会と、同じ前後を結ぶ指定過程があり、その本人が変化を受ける対象で、過程が後端で生起する。過程と状態差の接続であり、因果機構の証明ではない。',
    'hzff': '同じ規範源・各人の役割・実行記述を固定し、本人と活動にhze3の自由な取り組みの機会内容を対応させる。',
    'hzfg': 'hzffの機会内容をrmqへ接続し、同じ人々の各人に取り組みの機会が前後で新しく生じることを述べる。',
    'hzfh': 'hzffの機会内容をrmtへ接続し、変化過程をag、変化を受ける本人をla、後端の生起をdgへ結ぶ。機会がある状態だけとは区別する。',
    'hzfi': '評価文脈を後端として、同じ人々へのhzfhの機会の成立過程と、hze7の能力を尺度にする障害の漸減を連言する。自己作業の実行や能力の獲得は補わない。',
}
LIMITS = [
    '固定した人々と候補活動の両端比較である。候補が途中で追加されたことだけを機会の新規成立に数えない。候補が現実の全選択肢を網羅しているかは明示的な評価範囲の問題として残る。',
    'assessedは候補ごとの機会の前後評価が適切であるという入力条件。未評価の前状態を機会の不在と扱わないが、評価条件自体の信頼性をこの定義だけで証明しない。',
    'rmqと原文接続は旧機会の喪失を禁止しない。保持を要求するrmr・rmsは強い比較条件として分離する。区間内部での単調増加、連続性、変化速度は要求しない。',
    '変化過程ag・laと同じ前後状態を結ぶ。どの機構が機会を生じさせたか、その過程が唯一の原因か、過程が現在より後にも続くかは導かない。受動表現から特定の行為者を補わない。',
    'hzfiはhzfaの現在の機会だけという条件に、前後評価・新規成立・過程の証拠を加える候補である。原文の現在進行の全アスペクトや、場の比喩の空間的イメージを尽くすものではない。',
    '実行記述には同じ本人の目標に向かうhzezを閉じて渡す。許可の強い読み、方法と活動を同じ粒度で扱うこと、障害件数による漸減など既存の限界を保持する。著者帰属と全文の意味確認は未完である。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    opportunity = k('hze3', v('authority'), v('person'), app(v('roles'), v('person')), v('activity'), v('execution'), v('point'))
    text += definition('hzff', params(OPPORTUNITIES), 'i[person a activity a][b point[' + opportunity + ']]', 'h[a a] e')
    replacement = dict(opportunities=k('hzff', *args(OPPORTUNITIES)), transitions='p ag', affected='p la', occurs='p dg')
    text += definition('hzfg', params(SOURCE), k('rmq', *args(FAMILY, **replacement)))
    text += definition('hzfh', params(SOURCE_PROCESS), k('rmt', *args(PROCESS, **replacement)))
    opening = k('hzfh', *args(SOURCE_PROCESS, end=v('context')))
    decline = k('hze7', *args(DECLINE, end=v('context')))
    text += definition('hzfi', params(COMBINED), 'b context[' + both(opening, decline) + ']', 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-enlightening-epoch-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-opening-opportunities-basis-v1', document='examples/v014/kant-opening-opportunities.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'opening-opportunities')
def core_composed(): return projected(ROOTS + ['hzff', 'hzfg', 'hzfh', 'hzfi', 'hzfa', 'hzey', 'hzez', 'hzcu', 'rmd', 'rme', 'rmf', 'rmg', 'rmh', 'rmi', 'rmj', 'rmk', 'rml', 'hzfb', 'hzfc', 'hzfd', 'hzfe'], 'opening-opportunities-core')
BUILDERS = ((generic_composed, 'opening-opportunities'), (source_composed, 'kant-opening-opportunities'), (core_composed, 'opening-opportunities-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored opening opportunities differ: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
