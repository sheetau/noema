"""Required value transfers and separate public criticism of their assessment."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import definition
from scripts.compose_limits import ROOT, call as k, v, app, both, op
from scripts.compose_public_assessment import generic_composed as criteria_composed

PARENT = 'examples/v014/kant-role-hierarchy.noema'
TRUE = 'e[n p a b][n p a b]'
TRANSFER = 'moves h[a a a a d] c accepted h[a d] c'
PAYMENT = 'person a action a role a issuer a payment i[h[a a] e] context d'
PAY_NAMES = ('person', 'action', 'role', 'issuer', 'payment', 'context')
PUBLIC = 'speech a scholar a audience a channel a subject a criticism i[h[a] f] authority a'
ALL = PAYMENT + ' ' + PUBLIC


def definitions():
    text = definition('rfa', 'payer a receiver a transfer a medium a context d ' + TRANSFER, both(
        op('u', op('e', v('payer'), v('receiver'))),
        app(v('moves'), *(v(n) for n in ('transfer', 'payer', 'receiver', 'medium', 'context'))),
        app(v('accepted'), v('medium'), v('context'))))
    text += definition('rfb', 'receiver a medium a ' + TRANSFER,
        'i[payer a transfer a][b context[' + k('rfa', *(v(n) for n in
        ('payer', 'receiver', 'transfer', 'medium', 'context', 'moves', 'accepted'))) + ']]', 'h[a a] e')
    text += definition('rfc', 'subject a suitable j[h[a] e] just j[h[a] e]', 'b context[' + op('x',
        op('t', k('ret', v('subject'), v('suitable')), v('context')),
        op('t', k('ret', v('subject'), v('just')), v('context'))) + ']', 'e')
    text += definition('rfd', 'suitable j[h[a] e] just j[h[a] e]',
        'i[subject a][j s[' + k('rfc', v('subject'), v('suitable'), v('just')) + ']]', 'h[a] f')
    return text


MEANINGS = {
    'rfa': '同じ移転について、本人とは別の受け手への価値媒体の移転があり、その媒体が支払いに受け入れられる。仕事の対価という条件を付けないため、公的な納付、贈与、返済などにも使える。要求や正当性は含まない。',
    'rfb': '受け手・媒体・移転と受容の関係を固定し、本人と行為からrfaの成立内容を返す関数を構成する。受け手への移転という特定の内容を規範の対象記述にできる。',
    'rfc': '同じ対象について、指定された適切さの条件列か公正さの条件列の少なくとも一方に不充足があるという内容。二種類の評価を別の列として保持する。基準の正当性や網羅性は含めない。',
    'rfd': 'rfcの内容を述べる主張の発話を対象から作る。発話の作成と、その内容が真であること、話者が信じていること、実際の発言は別である。',
}
LIMITS = [
    'rfaは価値移転の共通条件であり、これだけで税・贈与・対価・返済を分類しない。受け手、媒体、移転の数量や制度上の根拠は必要に応じ別条件で指定する。',
    '適切さと公正さの基準はNoemaの関数の列で与える。基準自体を正当だと認定したり、批判の内容の真理を発話から推定したりしない。空の両列では不充足の内容は偽となる。',
]


def generic_composed():
    text, basis = criteria_composed(); basis = deepcopy(basis)
    doc = parse(text + definitions())
    basis.update(version='assessed-payments-basis-v1', document='examples/v014/assessed-payments.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT / 'data/kant-role-hierarchy-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()
    text += definition('hzah', 'receiver a medium a', k('rfb', v('receiver'), v('medium'), 'p ti', 'p tj'), 'h[a a] e')
    fields = [v(n) for n in ('issuer', 'person', 'role', 'action', 'payment')]
    text += definition('hzai', PAYMENT, k('h7a', *fields, TRUE, v('context')))
    text += definition('hzaj', PAYMENT, k('rdq', *fields, TRUE, v('context'), 'p h7a', 'p h7b'))
    duty = k('hzai', *(v(n) for n in PAY_NAMES))
    distinct = op('u', op('e', v('action'), v('speech')))
    public_args = [v(n) for n in ('person', 'speech', 'scholar', 'audience', 'channel', 'subject', 'criticism', 'context')]
    text += definition('hzak', ALL, both(duty, distinct, k('h6v', *public_args),
        k('cg', v('person'), v('speech'), v('context'))))
    text += definition('hzal', ALL, both(duty, distinct, k('h7c', *public_args, v('authority'))))
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis.update(version='kant-assessed-payments-basis-v1', document='examples/v014/kant-assessed-payments.noema')
    basis['definitions'].update(MEANINGS | {
        'hzah': '受け手と価値媒体を固定したrfbを既存の移転ti・媒体の受容tjへ接続する。仕事への対価tkは要求しない。',
        'hzai': '指定した出所が、同じ本人・役割・行為について、支払いの実行記述の成立を要求する。支払いの記述にはhzahの閉じた適用を渡す。任意のpaymentを渡した式まで納付義務とは扱わない。',
        'hzaj': 'hzaiと同じ規範の対象記述を本人と行為へ適用し、それが指定文脈で不成立である。未履行の条件であり、故意の拒否・支払不能・期限超過・制裁を含めない。脱引用するため引用内では使えない。',
        'hzak': 'hzaiの要求がある同じ本人が、別の活動で、指定内容・受け手群・経路を持つ公的使用を実際に行う。公的発言から納付済みや要求の消滅を推定しない。',
        'hzal': 'hzaiの要求と、同じ本人の別の公的活動への積極的な実行許可が併存する。許可側の同じ出所による禁止がないことを既存h7cで要求する。本人の実際の納付や発言は要求しない。',
    })
    basis['unresolved'] += LIMITS + [
        'u0012のauferlegten Abgabenへの部分接続。対価でない納付の内容と役割に対する要求を構成したが、市民・共同体・課税の制度、賦課の正当性、金額と期限は未完。市民を職務を委ねられた官吏と同一視せず、cfによる職務委託を条件に追加しない。',
        'kann sich nicht weigernを納付の要求という規範的な読みへ部分接続する。拒否する行為と未払い、支払不能の区別は維持し、拒否の意思を未払いから補わない。',
        'UnschiklichkeitとUngerechtigkeitを別々の基準の不充足として述べる批判の作例を接続する。基準の全説明、本人の思考・信念・議論の語用論は未完。',
        'hzalは義務と許可の併存モデルであり、原文の「市民の義務に反しない」の全意味と同一にはしない。批判のそれ自体への規範的評価、納付時の批判の処罰可能性と抵抗を誘発しうるという条件は未記述。',
        '既存15件の著者主張を保持し、この条件式を追加の著者主張へ昇格しない。原文の全文意味一致は未確認。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def core_composed():
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=['hzah', 'hzai', 'hzaj', 'hzak', 'hzal', 'rfd'], statement_indices=[])
    projected = extract_basis(doc, basis, selected, version='assessed-payments-core-basis-v1',
        document_path='examples/v014/assessed-payments-core.noema')
    return format_graph(selected.document, 'compact') + '\n', projected


BUILDERS = ((generic_composed, 'assessed-payments'), (source_composed, 'kant-assessed-payments'),
            (core_composed, 'assessed-payments-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/'+stem+'-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2)+'\n')):
            path = ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored assessed payments differ: '+name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__':
    main()
