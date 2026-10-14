"""Keep an order and public criticism together up to a shared milestone."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args, MESSAGE

PARENT = 'examples/v014/kant-self-legislation.noema'
UNTIL = [('history', 'h[d] c'), ('before', 'h[d d] c'), ('start', 'd'), ('maintained', 'e'), ('milestone', 'e')]
WITNESS = UNTIL + [('end', 'd')]
STATE = [('population', 'a'), ('regime', 'a'), ('context', 'd'), ('active', 'h[a d] c'), ('citizens', 'h[a a d] c'),
    ('eligible', 'h[a a a d] c'), ('permitted', 'h[a a a d] c')]
CONFIG = [('population', 'a'), ('regime', 'a'), ('role', 'a'), ('audience', 'a'), ('channel', 'a'), ('criticism', MESSAGE),
    ('authority', 'a'), ('active', 'h[a d] c'), ('citizens', 'h[a a d] c')]
SOURCE = CONFIG + [('histories', 'h[d] h[d] c'), ('milestone', 'e')]
ROOTS = ['rkh', 'rki', 'rkj', 'rkk', 'rkl']


def definitions():
    at_or_after = lambda point: op('x', op('e', v('start'), v(point)), app(v('before'), v('start'), v(point)))
    prior = both(app(v('history'), v('point')), at_or_after('point'), app(v('before'), v('point'), v('end')))
    persistent = both(op('t', v('maintained'), v('point')), op('u', op('t', v('milestone'), v('point'))))
    witness = both(k('ta', v('history'), v('before')), app(v('history'), v('start')), app(v('history'), v('end')),
        at_or_after('end'), op('t', v('milestone'), v('end')), quant('f', 'point', 'd', op('y', prior, persistent)))
    text = definition('rkh', params(WITNESS), witness)
    text += definition('rki', params(UNTIL), quant('g', 'end', 'd', k('rkh', *args(WITNESS))))
    never = 'i[point d][' + persistent + ']'
    text += definition('rkj', params(UNTIL), op('x', k('rki', *args(UNTIL)), k('rca', v('history'), v('before'), v('start'), never)))
    text += definition('rkk', params(UNTIL), quant('g', 'end', 'd', both(k('rkh', *args(WITNESS)), op('t', v('maintained'), v('end')))))
    eligible = app(v('eligible'), v('person'), v('activity'), v('regime'), v('context'))
    freedom = both(quant('g', 'activity', 'a', eligible), quant('f', 'activity', 'a', op('y', eligible,
        app(v('permitted'), v('person'), v('activity'), v('regime'), v('context')))))
    text += definition('rkl', params(STATE), both(app(v('active'), v('regime'), v('context')),
        quant('f', 'person', 'a', op('y', app(v('citizens'), v('population'), v('person'), v('context')), freedom))))
    return text


MEANINGS = {
    'rkh': '同じ非空履歴の厳密な全順序上で、基準点以降の指定終点に到達条件が成立し、それより前の全点で維持内容が成立し、到達条件はまだ成立しない。終点は基準点以降の最初の到達点である。終点以後に維持内容が不成立になるとは要求しない。',
    'rki': 'rkhを満たす最初の到達点が存在する。到達前の維持と、到達条件の実際の成立を共に要求する。',
    'rkj': 'rkiが成立するか、同じ履歴の基準点以降の全点で維持内容が成立し、到達条件が一度も成立しない。後者を排除しない弱い継続条件。選んだ有限履歴での成立を現実の無限持続とはしない。',
    'rkk': 'rkiと同じ最初の到達点まで維持し、その到達点自体でも維持内容が成立する強い境界条件。到達後の廃止を含意しない。',
    'rkl': '同じ制度が同じ時点で存続し、各市民にその制度についての該当活動が少なくとも一つあり、その該当活動全てが許可される。別の市民・制度・時点への許可を流用せず、実際に活動したことは加えない。',
    'hzeb': 'rklの該当活動を同じ立場・公衆・経路・制度・批判記述の公的使用h6v、許可を同じ権限側のh7cへ接続する内容。制度の存続と各市民の批判への許可を同じ時点で保つ。',
    'hzec': 'hzebの状態が、同じ評価文脈で選んだ履歴の最初の到達点より前まで続くrkiの内容。時間順序には同じ評価文脈のicを使い、到達条件は明示的なNoema内容として渡す。',
    'hzed': '同じ設定でrkjの弱い継続を述べる。到達条件が成立しない場合の持続も許す。',
    'hzee': '同じ設定でrkkの到達点も含む継続を述べる。境界での制度存続と批判許可の扱いを明示する。',
}
LIMITS = [
    '最初の到達点を要求する読みを採る。密な時間順序で到達条件の成立点集合に最小点がない場合はrkiが成立しない。後の点を都合よく選んで最初の到達として扱わない。一般の時間的until全ての意味と同一視しない。',
    '維持内容は最初の到達点で偽になる必要はなく、その後も続けられる。rkiとrkkは到達点を含むかどうかだけが異なり、実際の廃止・改正行為を記述したものではない。',
    '一つの固定した履歴を使い、反事実的な別経過の維持と到達を結合しない。有限モデルによる履歴・順序の検査は、現実の時間粒度や無限履歴の網羅性の証明ではない。',
    '市民の所属は各時点で評価する。各市民について該当する公的活動の非空性を要求するが、それは実際の発話・読了・同意・物理的な実行可能性を証明しない。市民集合自体の非空性はこの普遍条件からは主張しない。',
    '批判の記述と対象制度を全時点で保持する。接続例では既存reuに条件列を渡した閉じた不足の指摘を用いる。任意の同型の発話記述が批判であるとは型だけで認定しない。',
    '理解の公的な進展・確認と提案可能性を含む具体的な到達条件、一定の短い期間、改善への期待、特に聖職者という強調、実際の改正・保護・妨害禁止、著者帰属は未完。到達条件を意味未説明の原語で代用して全文対応済みには数えない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()
    public = [v(n) for n in ('person', 'activity', 'role', 'audience', 'channel', 'regime', 'criticism', 'point')]
    eligible = 'i[person a activity a regime a point d][' + k('h6v', *public) + ']'
    permitted = 'i[person a activity a regime a point d][' + k('h7c', *public, v('authority')) + ']'
    text += definition('hzeb', params(CONFIG), 'b context[' + k('rkl', *args(STATE, eligible=eligible, permitted=permitted)) + ']', 'e')
    before = 'i[first d second d][' + k('ic', v('first'), v('second'), v('context')) + ']'
    for name, target in (('hzec', 'rki'), ('hzed', 'rkj'), ('hzee', 'rkk')):
        body = k(target, *args(UNTIL, history=app(v('histories'), v('context')), before=before, start=v('context'), maintained=k('hzeb', *args(CONFIG))))
        text += definition(name, params(SOURCE), 'b context[' + body + ']', 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-self-legislation-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-provisional-order-basis-v1', document='examples/v014/kant-provisional-order.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'provisional-order')
def core_composed(): return projected(ROOTS + ['hzeb', 'hzec', 'hzed', 'hzee', 'reu'], 'provisional-order-core')
BUILDERS = ((generic_composed, 'provisional-order'), (source_composed, 'kant-provisional-order'), (core_composed, 'provisional-order-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored provisional order differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
