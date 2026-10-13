"""Possible causal outcomes and intentional adverse responses, separately licensed."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, call as k, app, both, op, quant
from scripts.compose_origin_clock import definition
from scripts.compose_finite_ratios import generic_composed as ratios

PARENT = 'examples/v014/kant-action-conformity.noema'
DESCRIPTION = 'i[h[a] e]'
PROSPECTS = 'h[a d d] c'
RELATIONS = 'enacts h[a a d] c adverse h[a a d] c intends h[a a a d] c responds h[a a a a '+DESCRIPTION+' d] c'
RESPONSE = 'person a offense a assessment '+DESCRIPTION+' '+RELATIONS
RESPONSE_NAMES = ('person', 'offense', 'assessment', 'enacts', 'adverse', 'intends', 'responds')


def definitions():
    text = definition('rfj', 'activity a context d prospects '+PROSPECTS+' condition h[d] c',
        quant('g', 'outcome', 'd', both(app(v('prospects'), v('activity'), v('context'), v('outcome')),
            app(v('condition'), v('outcome')))))
    actual = op('t', app('s[v effect]', v('group')), v('outcome'))
    text += definition('rfk', 'activity a group a effect '+DESCRIPTION+' context d prospects '+PROSPECTS+
        ' occurs h[a d] c produces h[a a '+DESCRIPTION+' d] c',
        k('rfj', v('activity'), v('context'), v('prospects'), 'i[outcome d]['+both(
            app(v('occurs'), v('activity'), v('outcome')),
            app(v('produces'), v('activity'), v('group'), v('effect'), v('outcome')), actual)+']'))
    text += definition('rfl', 'group a members h[a] j[a] eligible h[a] c property h[a] e criterion h[b] c',
        'b outcome['+k('pd', app(v('members'), v('group')), v('eligible'),
            'i[person a]['+op('t', app(v('property'), v('person')), v('outcome'))+']', v('criterion'))+']', 'e')
    text += definition('rfm', 'authority a measure a '+RESPONSE+' context d', both(
        app(v('enacts'), v('authority'), v('measure'), v('context')),
        app(v('adverse'), v('measure'), v('person'), v('context')),
        app(v('intends'), v('authority'), v('measure'), v('person'), v('context')),
        app(v('responds'), v('authority'), v('measure'), v('person'), v('offense'), v('assessment'), v('context'))))
    text += definition('rfn', RESPONSE, 'i[authority a measure a][b context['+
        k('rfm', v('authority'), v('measure'), *(v(n) for n in RESPONSE_NAMES), v('context'))+']]', 'h[a a] e')
    return text


MEANINGS = {
    'rfj': '同じ活動と評価文脈に対して選ばれた可能結果のうち、指定条件を満たすものが存在する。現実の結果、全候補での成立、規範的な許可を含まない。',
    'rfk': '同じ候補結果で活動が起き、その活動が同じ対象について記述された結果を生じさせ、結果内容も成立する。別々の候補での活動・因果・結果を結合しない。現実の発生を要求しない。',
    'rfl': '指定集団の重複なし・非空の適格な成員列について、指定性質を満たす割合が明示した基準を満たす内容。全員や過半数という閾値を勝手に固定しない。',
    'rfm': '同じ施行者が同じ措置を実行し、その措置が対象者へ不利益を与え、施行者がその不利益を意図し、同じ対象者の対象行為を指定記述で評価したことへの応答として措置を加える。処罰の一つの操作的な構成であり、評価の真理・正当性・許可を含まない。',
    'rfn': '対象者・対象行為・評価記述と関係を固定して、施行者と措置からrfmの成立内容への関数を作る。この閉じた適用を規範の対象記述として利用できる。',
}
LIMITS = [
    '候補選定、因果、意図、不利益、評価に応じた措置という関係の現実への対応と一般的な基礎説明は別である。定義に渡す関係は、検査結果に合わせて選び直さない。',
    'rfmは意図した不利益が実際に生じる応答を扱う。失敗した処罰の試み、象徴的な非難、司法手続、適法性、正当性を全て定義したものではない。',
    '評価記述は応答の根拠として保持するが、その内容を真として実行しない。誤認に基づく措置も表現できる。',
    'rfkは脱引用を含むため、そのまま引用できない。rfnは評価記述を実行しないため、閉じた適用を引用できる。',
]


def generic_composed():
    text, basis = ratios(); basis = deepcopy(basis)
    doc = parse(text+definitions())
    basis.update(version='possible-sanctions-basis-v1', document='examples/v014/possible-sanctions.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def source_composed():
    doc = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT/'data/kant-action-conformity-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()
    text += definition('hzar', 'criticism a group a resistance '+DESCRIPTION+' context d prospects '+PROSPECTS,
        k('rfk', v('criticism'), v('group'), v('resistance'), v('context'), v('prospects'), 'p dg', 'p g3'))
    text += definition('hzas', 'group a resistance h[a] e criterion h[b] c',
        k('rfl', v('group'), 'p mp', 'p aa', v('resistance'), v('criterion')), 'e')
    source_response = 'person a offense a assessment '+DESCRIPTION+' adverse h[a a d] c intends h[a a a d] c responds h[a a a a '+DESCRIPTION+' d] c'
    source_names = ('person', 'offense', 'assessment', 'adverse', 'intends', 'responds')
    text += definition('hzat', source_response, k('rfn', v('person'), v('offense'), v('assessment'),
        'p cg', v('adverse'), v('intends'), v('responds')), 'h[a a] e')
    text += definition('hzau', 'authority a measure a '+source_response+' context d prospects '+PROSPECTS,
        k('rfj', v('measure'), v('context'), v('prospects'), 'i[outcome d]['+op('t',
            app(k('hzat', *(v(n) for n in source_names)), v('authority'), v('measure')), v('outcome'))+']'))
    text += definition('hzav', 'issuer a authority a role a measure a description i[h[a a] e] context d',
        k('rdm', v('issuer'), v('authority'), v('role'), v('measure'), v('description'),
            'e[n p a b][n p a b]', v('context'), 'p h7a', 'p h7b'))
    doc = parse(format_graph(doc, 'compact')+text); doc['statements'] = statements
    basis.update(version='kant-possible-sanctions-basis-v1', document='examples/v014/kant-possible-sanctions.noema')
    basis['definitions'].update(MEANINGS | {
        'hzar': '指定批判の行為について、同じ候補結果で行為が起き、指定集団に抵抗として記述された結果を生じさせ、その内容も成立する可能性。g3の因果関係と単なる共起を区別する。',
        'hzas': '同じ集団の人々について、抵抗として指定した性質が文脈基準の割合に広がる内容。抵抗の性質と広がりの基準は説明した関数として渡す。allgemeineを全員と固定しない有限集団の読み。',
        'hzat': '施行関係cgを使い、対象者・対象行為・評価記述を固定した意図的な不利益の応答内容を作る。閉じた適用を規範へ渡せる。',
        'hzau': '同じ対象者・批判行為・評価記述へのhzatの措置が、同じ候補状況で実行される可能性。現実の処罰、全候補での処罰、許可を含まない。',
        'hzav': '記述された措置について、指定出所が同じ施行者・役割・行為へ積極的な許可を与え、反対の要求がない。可能性hzauとは独立。作例ではhzatの閉じた適用を渡す。',
    })
    basis['unresolved'] += LIMITS + [
        'u0012の誘発可能性と処罰可能性へ部分接続する。vorwitzigの評価、Skandalの説明、抵抗の対象・具体的な性質、広がりの基準、納付すべき時期との接続、sogarとdemohngeachtetの談話は未完。',
        'bestraft werden kannの実行可能性と規範的な許可の二つの読みを別々に記述し、どちらかに自動同一化しない。誘発可能性から許可を導く規則は追加しない。既存15著者主張を保持する。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def core_composed():
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=['hzar', 'hzas', 'hzat', 'hzau', 'hzav'], statement_indices=[])
    projected = extract_basis(doc, basis, selected, version='possible-sanctions-core-basis-v1',
        document_path='examples/v014/possible-sanctions-core.noema')
    return format_graph(selected.document, 'compact')+'\n', projected


BUILDERS = ((generic_composed, 'possible-sanctions'), (source_composed, 'kant-possible-sanctions'),
            (core_composed, 'possible-sanctions-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/'+stem+'-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2)+'\n')):
            path = ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored possible-sanctions document differs: '+name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__':
    main()
