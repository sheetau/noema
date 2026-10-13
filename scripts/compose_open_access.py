"""Separate admission, usable access methods and actual receipt."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, quant, call, definition
from scripts.compose_contextual_ability import generic_composed as ability

PARENT = 'examples/v014/kant-message-relays.noema'
MESSAGE = 'i[h[a] f]'
RULE = 'h[a a a a a ' + MESSAGE + ' d] c'
BASE = [('authority', 'a'), ('person', 'a'), ('channel', 'a'), ('subject', 'a'),
    ('description', MESSAGE), ('start', 'd'), ('grants', RULE), ('forbids', RULE)]
METHODS = [('available', 'h[a a d] c'), ('outcomes', 'h[a a d d] c'), ('selected', 'h[a a d d] c')]


def params(items):
    return ' '.join(name + ' ' + kind for name, kind in items)


def definitions():
    ruleargs = [v(n) for n in ('authority', 'person', 'plan', 'channel', 'subject', 'description', 'start')]
    text = definition('rdg', params(BASE + [('plan', 'a')]), both(app(v('grants'), *ruleargs), op('u', app(v('forbids'), *ruleargs))))
    text += definition('rdh', params(BASE), quant('g', 'plan', 'a', call('rdg', *(v(n) for n, _ in BASE), v('plan'))))
    scoped = [('audience', 'h[a] c')] + [(n, t) for n, t in BASE if n != 'person']
    audience = app(v('audience'), v('person'))
    text += definition('rdi', params(scoped), both(quant('g', 'person', 'a', audience),
        quant('f', 'person', 'a', op('y', audience, call('rdh', *(v(n) for n, _ in BASE))))))
    allowed = 'i[actor a method a scene d][' + both(app(v('available'), v('actor'), v('method'), v('scene')),
        call('rdg', v('authority'), v('actor'), v('channel'), v('subject'), v('description'), v('scene'),
            v('grants'), v('forbids'), v('method'))) + ']'
    text += definition('rdj', params(BASE + [('goal', 'e')] + METHODS), call('xd', v('person'), v('goal'),
        v('start'), allowed, v('outcomes'), v('selected')))
    text += definition('rdk', params(scoped + [('goals', 'h[a] e')] + METHODS), both(quant('g', 'person', 'a', audience),
        quant('f', 'person', 'a', op('y', audience, call('rdj', *(v(n) for n, _ in BASE),
            app(v('goals'), v('person')), *(v(n) for n, _ in METHODS))))))
    return text


MEANINGS = {
    'rdg': '同じ規範の出所・人・方法・経路・対象・発話記述・開始状況について積極的な許可があり、同じ出所の禁止がない。禁止がないだけでは成立しない。',
    'rdh': '指定人物にrdgの許可された方法がある。実行可能性や受領済みであることを要求しない。',
    'rdi': '独立に指定した非空の受け手範囲の各人にrdhの方法がある。方法は人ごとに異なってよい。実際に読んだ人の集合から対象範囲を決めない。',
    'rdj': '実行でき、同じ出所によってrdgが成立する同一の方法があり、その方法の非空で妥当な評価結果の全てで指定した取得目標が成立する。許可だけ・手段だけ・異なる方法同士の寄せ集めでは成立しない。',
    'rdk': '非空の指定受け手範囲の全員に、それぞれの取得目標についてrdjの方法がある。現に利用した人数と分けた実効的取得機会の部分条件。',
}
LIMITS = [
    '対象範囲は読者・利用資格等の独立した文脈から与える。許可された人や実際の読者だけに範囲を縮めることは、公開性の説明にならない。範囲の正当性は形式だけでは証明しない。',
    '規範の出所を固定し、その出所の許可と禁止を区別する。別の出所との競合や法体系全体での適法性、権利の保障は判定しない。',
    '許可の広さと各人の取得手段の有無は異なる。実効的な取得を全員に保証しないことだけで、公的な発言ではないとは結論しない。',
    '選択した結果の全てで成功するという明示的な評価基準である。全ての可能な偶発事象での保証ではなく、評価基準の代表性・負担・費用・障害への対応は別途必要。',
]


def generic_composed():
    parent_text, parent_basis = ability()
    doc = parse(parent_text)
    doc['declarations'] = [row for row in doc['declarations'] if row['name'] in ('xa', 'xd')]
    doc = parse(format_graph(doc, 'compact') + definitions())
    basis = {'version': 'open-access-basis-v1', 'document': 'examples/v014/open-access.noema', 'primitives': [],
        'definitions': {**{n: parent_basis['definitions'][n] for n in ('xa', 'xd')}, **MEANINGS}, 'unresolved': LIMITS}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = 'r h6k[a a d] c.r h6l[a a a a a ' + MESSAGE + ' d] c.r h6m[a a a a a ' + MESSAGE + ' d] c.r h6n[a d] c.\n'
    extra += '''d h6o[person a channel a subject a description i[h[a] f]] e[b scene[g act a[
 w[k dg[v act v scene]][w[k h6k[v act v channel v scene]][k h6e[v act v person v subject v description v scene]]]
]]].
'''
    inputs = [(n, t) for n, t in BASE if n not in ('grants', 'forbids')]
    args = [v(n) for n, _ in inputs] + ['p h6l', 'p h6m']
    extra += definition('h6p', params(inputs), call('rdh', *args))
    scope = 'i[person a][w[k aa[v person]][k h6n[v person v start]]]'
    scoped = [(n, t) for n, t in inputs if n != 'person']
    group_args = [scope] + [v(n) for n, _ in scoped] + ['p h6l', 'p h6m']
    extra += definition('h6q', params(scoped), call('rdi', *group_args))
    goals = 'i[person a][k h6o[v person v channel v subject v description]]'
    extra += definition('h6r', params(scoped), call('rdk', *group_args, goals, 'p ae', 'p af', 'p ap'))
    extra += definition('h6s', params([(n, t) for n, t in inputs if n != 'authority']),
        op('t', call('h6o', v('person'), v('channel'), v('subject'), v('description')), v('start')))
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-message-relays-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-open-access-basis-v1', document='examples/v014/kant-open-access.noema')
    decls = {row['name']: row for row in doc['declarations']}
    for name, args, meaning in (
        ('h6k', ['act', 'channel', 'context'], 'この取得・提示行為が、この提供経路を使って行われる。別の経路で同じ内容を取得しただけでは成立しない。媒体や経路の個体化は未完。'),
        ('h6l', ['authority', 'person', 'method', 'channel', 'subject', 'message_description', 'context'], '指定した規範の出所が、この人に、この対象の発話記述をこの経路から取得する同じ方法を積極的に許可する。許可の内容を列挙し、実行可能性や実行事実とは分ける。'),
        ('h6m', ['authority', 'person', 'method', 'channel', 'subject', 'message_description', 'context'], '同じ規範の出所が、この人に、この対象の発話記述をこの経路から取得する同じ方法を禁止する。許可の単なる不在とは分ける。'),
        ('h6n', ['person', 'context'], 'この文脈で読者世界として検討する対象者の範囲。今回許可された人、招待された人、既に読んだ人の範囲とは独立に与える。読者世界の歴史的・社会的な一般定義は未完。')):
        row = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': row['parameters'], 'result': row['result'], 'arguments': args, 'meaning_ja': meaning})
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'h6o': '同じ人が、指定した提供経路を使う生起した行為で、同じ対象・発話記述を受領する内容。別経路での取得や意味の理解は混ぜない。',
        'h6p': 'その人物に、同じ出所・経路・対象・発話記述について許可された取得方法がある。',
        'h6q': '同じ基準文脈の非空の読者範囲の全員にh6pが成立する。許可が現実の受領へ結び付いたことは要求しない。',
        'h6r': 'h6qと同じ読者範囲について、各人に、許可され実行可能な同じ方法によるh6oの取得機会がある。評価結果は非空かつ想定結果に含まれる。',
        'h6s': '指定本人が同じ提供経路・対象・発話記述を基準状況で現に受領した。許可の有無や、他の人々の取得機会を含まない。'})
    basis['unresolved'] += LIMITS + [
        'ganzen Publikum der Leserweltへ向けることの開放性を調べる部分構成。h6q/h6rを公衆または公的使用の必要十分条件とはしない。実際の公衆、学識者の立場、発言内容、討議への参加・応答は未接続。',
        '旧0.11のceによる公衆分類は変更していない。旧記号の名前の衝突を避け、現在の提示・受領と文脈的能力へ新しい構成を接続した。全文で両草案を統合する作業は残る。',
        '第一段落の能力評価用のae/af/apを、今回は取得目標h6oへ渡す。原文が特定の取得方法・読者の一覧・規範の出所・評価候補を指定したとは主張しない。本文への実際の成立主張は追加しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'open-access'), (source_composed, 'kant-open-access')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored access conditions differ')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Admission, usable access and actual receipt separated')


if __name__ == '__main__':
    main()
