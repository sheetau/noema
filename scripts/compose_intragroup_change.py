"""Describe cross-member participation in one assessed capacity change."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, call, definition
from scripts.compose_transitions import generic_composed as transitions

PARENT = 'examples/v014/kant-count-focus.noema'


def definitions():
    args = ('history h[d] c before h[d d] c members h[a] c actor a target a process a part a start d end d '
        'assessed h[a d] c prior h[a] e goal h[a] e description i[h[a] e] '
        'changes h[a d d] c affected h[a a d d] c occurs h[a d] c participates h[a a d] c '
        'partof h[a a d] c produces h[a a i[h[a] e] d] c')
    invoke = lambda name, *fields: app(v(name), *(v(field) for field in fields))
    state = lambda name, point: op('t', invoke(name, 'target'), v(point))
    return definition('rda', args, both(
        call('tg', *[v(name) for name in ('history', 'before', 'process', 'start', 'end', 'changes')]),
        invoke('members', 'actor'), invoke('members', 'target'), op('u', op('e', v('actor'), v('target'))),
        invoke('assessed', 'target', 'start'), invoke('assessed', 'target', 'end'),
        state('prior', 'start'), op('u', state('prior', 'end')), op('u', state('goal', 'start')), state('goal', 'end'),
        invoke('affected', 'target', 'process', 'start', 'end'), invoke('occurs', 'process', 'end'),
        invoke('partof', 'part', 'process', 'end'), invoke('occurs', 'part', 'end'),
        invoke('participates', 'actor', 'part', 'end'), invoke('produces', 'part', 'target', 'description', 'end')))


MEANING = '同じ集団に属する異なる当事者と対象者がいる。同じ順序付き履歴の変化過程が対象者に作用し、整合した前後評価で前状態から目標状態へ変わる。その過程を構成する同じ活動部分が生起し、当事者が能動的に参加し、同じ対象者に記述された目標をその部分活動が生じさせる。集団への所属や活動の同時発生だけでは認定しない。'
LIMITS = [
    'descriptionは同じ対象者のgoalを記述するという接続規約を持つ。原文側ではh4lの内容とその引用を同じ定義へ固定する。',
    '当事者が参加する同じ部分活動の結果生成を要求するが、当事者単独で十分な原因であることや、外部者の援助の不在は要求しない。全構成員の同時変化や共同意図も導かない。',
    '活動部分は過程を構成する全体または部分として与える。前後二点の粒度で完了側に活動の生起・参加・結果を記録するが、全てが瞬間的な出来事であるとはしない。途中の詳細な時間経過は別途必要である。',
    '一人への内部参加を含む変化は、集団全体の啓蒙・能力・自治の必要十分条件ではない。集団の種類や同一性、公開性、言説の伝播、変化の範囲・程度は別途記述する。',
]


def generic_composed():
    text, parent = transitions()
    doc = parse(text)
    doc['declarations'] = [row for row in doc['declarations'] if row['name'] in ('ta', 'tg')]
    doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions())
    basis = {'version': 'intragroup-change-basis-v1', 'document': 'examples/v014/intragroup-change.noema',
        'primitives': [], 'definitions': {name: parent['definitions'][name] for name in ('ta', 'tg')}, 'unresolved': LIMITS}
    basis['definitions']['rda'] = MEANING
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = '''r h6a[a a d] c.
d h6b[group a actor a target a process a part a start d end d anchor d] c[
 w[k hi[k mp[v group] p aa]][w[k ia[v target v anchor v anchor]][w[
  x[e[v end][v anchor]][k ic[v end v anchor v anchor]]
 ][k rda[i[point d][k ia[v target v anchor v point]] i[first d last d][k ic[v first v last v anchor]]
  i[person a][k hg[k mp[v group] v person]] v actor v target v process v part v start v end
  i[person a point d][t[k fo[v person]][v point]] p bf p h4l r[p h4l] p ag p la p dg p df p h6a p g3]
 ]]]
].
d h6c[group a process a start d end d anchor d] c[g actor a[g target a[g part a[
 k h6b[v group v actor v target v process v part v start v end v anchor]
]]]].
d h6d[group a] e[b anchor[g process a[g start d[g end d[k h6c[v group v process v start v end v anchor]]]]]].
'''
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-count-focus-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-intragroup-change-basis-v1', document='examples/v014/kant-intragroup-change.noema')
    decl = next(row for row in doc['declarations'] if row['name'] == 'h6a')
    basis['primitives'].append({'symbol': 'h6a', 'parameters': decl['parameters'], 'result': decl['result'],
        'arguments': ['part_activity', 'process', 'context'],
        'meaning_ja': 'この評価文脈で、この活動が同じ変化過程を構成する全体または部分である。単なる同時生起や、無関係な過程の部分とは区別する。過程・部分活動の個体化と詳細な構成機構は未完。'})
    basis['definitions'].update({'rda': MEANING,
        'h6b': '同じ集団mpの異なる人を当事者と対象者へ固定し、対象者の同じ基準文脈の履歴でrdaを満たす。前後で能力評価foが整合し、bfからh4lへ変わり、当事者が参加する同じh6aの活動部分がg3によってh4lを生じさせる。未来の完了は含めない。',
        'h6c': '指定した集団・過程・前後・基準文脈について、h6bを満たす異なる内部の二人と活動部分が存在する。過程を固定して各役割を結び、全構成員の成功へ量化を強めない。',
        'h6d': '基準時までにh6cの内部参加を含む変化を持つ集団の内容。公衆であること、集団全体の啓蒙の完成、可能性・比較的容易さや必然性までは含まない。'})
    basis['unresolved'] += LIMITS + [
        'sich selbst aufkläreの集団内の働きかけを記述するための部分構成であり、Publikumの語義、公開の言説・理性的評価の伝播、全体の変化尺度は未完である。人の列を持つだけの任意の集団を、そのまま公衆と認定しない。',
        'mpはこの比較で同一の集団の構成員列を与える。参加・離脱による構成員の変化、世界全体の読者への開かれ方はこの固定範囲の部分構成に含めていない。',
        '援助を受けて能力を得る過程と、得た能力の使用が他者の指導を必要とすることを区別する。h4lは結果側の自立的使用を要求し、発達過程で人から情報や援助を受けたことだけで拒否しない。',
        '実際の結果生成を含むh6dを定義したが、原文は比較的可能であることを述べるため、h6dの現実の成立を本文主張として追加しない。eher möglich、自由の条件とbeinahe unausbleiblich、後続の伝播・抑圧・革命の論述は未接続。',
        '能力の評価・因果・活動部分・集団の基礎概念と原文の意味一致確認は未完。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'intragroup-change'), (source_composed, 'kant-intragroup-change')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored intragroup change differs')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Distinct internal participants and one assessed capacity-change process composed')


if __name__ == '__main__':
    main()
