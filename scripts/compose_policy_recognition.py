"""Compose description-sensitive attitudes toward a policy's prospective safety."""
from copy import deepcopy
import json

from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, both, op, quant
from scripts.compose_situated_criticism import params

PARENT = 'examples/v016/kant-public-permission-risk.noema'
SOURCE = 'examples/v016/kant-policy-recognition.noema'
CORE = 'examples/v016/policy-recognition-core.noema'
BASIS = 'data/policy-recognition-basis-v1.json'
CODE = 'i c[e]'
ALTERNATIVES = 'h[a ' + CODE + ' d d] c'
AWARENESS = 'h[a ' + CODE + ' d] c'
JUDGMENT = [('person', 'a'), ('target', CODE), ('context', 'd'), ('alternatives', ALTERNATIVES)]
ATTITUDE = JUDGMENT + [('awareness', AWARENESS)]


def definitions():
    selected = app(v('alternatives'), v('person'), v('target'), v('context'), v('candidate'))
    holds = op('t', 's[v target]', v('candidate'))
    text = definition('rro', params(JUDGMENT), both(
        quant('g', 'candidate', 'd', selected),
        quant('f', 'candidate', 'd', op('y', selected, holds))))
    text += definition('rrp', params(ATTITUDE), both(
        app(v('awareness'), v('person'), v('target'), v('context')),
        k('rro', *(v(n) for n, _ in JUDGMENT))))
    text += definition('rrq', params(ATTITUDE), both(
        k('rrp', *(v(n) for n, _ in ATTITUDE)), op('t', 's[v target]', v('context'))))
    return text


def build():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()
    text += 'r hznalternatives[a ' + CODE + ' d d] c.r hznawareness[a ' + CODE + ' d] c.'
    text += 'r hznnode[] a.r hznscope[] a.r hznreport[a a i d[e] a d] c.'
    args = [k('hzmruler'), 'r c[k hzmsafety[]]', v('context'), 'p hznalternatives', 'p hznawareness']
    text += definition('hzninsight', '', 'b context[' + k('rrq', *args) + ']', 'e')
    text += definition('hznattribution', '', k('hznreport', k('hznnode'), k('wa'),
        'r d[k hzninsight[]]', k('hznscope'), k('wh')))
    doc = parse(format_graph(doc, 'compact') + text + 's[k hznattribution[]].')
    # Replace the previous fragment attribution; do not retain a separate
    # assertion of safety outside the newly expressed attitude.
    doc['statements'] = statements[:-1] + doc['statements']
    lookup = {d['name']: d for d in doc['declarations']}
    pending, retained = _references(doc['statements'][-1:]), set()
    while pending:
        name = pending.pop()
        if name in retained:
            continue
        retained.add(name)
        pending.update(_references(lookup[name]) - retained)
    core = deepcopy(doc)
    core['declarations'] = [d for d in doc['declarations'] if d['name'] in retained]
    core['statements'] = doc['statements'][-1:]
    return {SOURCE: format_graph(doc, 'compact') + '\n', CORE: format_graph(core, 'compact') + '\n'}


def basis():
    return dict(status='partial_description_sensitive_factive_attitude', document=SOURCE, parent=PARENT,
        definitions=dict(
            rro='同じ人・対象記述・判断文脈に属する候補が非空で、その全候補で同じ記述の内容が成立する。',
            rrp='rroに加え、本人が同じ記述を同じ文脈で認識する。実際の真理はまだ要求しない。',
            rrq='rrpに加え、対象内容が判断文脈でも成立する。現在状況を候補集合へ追加する操作ではない。',
            hzninsight='統治者本人について、既存の方針安全性hzmsafetyの記述にrrqを適用する。',
            hznattribution='認識を含む部分内容を同じ著者に帰属する。段階3の引用であり、帰属の評価だけでは認識や安全性を実行しない。'),
        bindings=dict(
            hznalternatives='同じ本人・段階2の対象記述・判断文脈において排除されていない候補状況。危険の想定結果hzmprospectsとは別の関係。',
            hznawareness='本人がこの記述をこの文脈で認識し、判断の対象にする関係。真理、肯定、証明済みを単独では含まない。',
            hznnode='今回の部分的な認識内容の本文位置。', hznscope='この認識と対象内容の非連続な原文対応範囲。',
            hznreport='著者・本文位置・段階3の内容記述・原文範囲・文脈の帰属関係。'),
        unresolved=[
            'sieht einを真なる肯定認識の部分条件として読む。理解の仕方、証拠の妥当性、偶然の正しさの排除、洞察の成立過程まで定義していない。rrqを知識や洞察一般の十分条件にしない。',
            '候補関係と明示的認識は解釈入力であり、認識の心理的・社会的な構成説明は残る。矛盾した信念や論理的全知の一般問題も未解決。',
            '記述の一致は正規化した構文の一致である。同じ真偽を持つ別記述の認識を自動転用しない。候補は人・対象・文脈の全てに依存する。',
            '危険の候補と判断の候補は別階層に保つ。判断候補ごとに同じ方針の安全性を評価するが、方針の対象者・活動は元の基準文脈に固定したまま。',
            'u0016の立法への限定、改善案と率直な批判、啓蒙を支持する統治者という照応、比較・強調・後続実例は未記述。全従属節をこの断片と同一視しない。',
            '元の公的使用・理解力・臣民・政策と危険についての未解決事項を継承する。全段落の意味一致や現実の政策安全性は検証していない。'])


def main():
    files = build() | {BASIS: json.dumps(basis(), ensure_ascii=False, indent=2) + '\n'}
    for name, text in files.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != text:
                raise ValueError('Stored policy recognition differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
        print(name, len(text), 'characters')


if __name__ == '__main__':
    main()
