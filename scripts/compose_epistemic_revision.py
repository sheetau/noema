"""Compare warranted information and error contents rather than sentence counts."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args

PARENT = 'examples/v014/kant-normative-powers.noema'
RELATIONS = [('corpus', 'h[a a d] c'), ('supported', 'h[a a d] c'), ('contents', 'h[a] e')]
ITEM = [('holder', 'a'), ('claim', 'a'), ('stage', 'd'), ('assessment', 'd')] + RELATIONS
PROFILE = [('holder', 'a'), ('stage', 'd'), ('assessment', 'd'), ('scope', 'h[a] c')] + RELATIONS
CHANGE = [('holder', 'a'), ('before', 'd'), ('after', 'd'), ('assessment', 'd'), ('scope', 'h[a] c')] + RELATIONS + [('comparisons', 'h[d] c')]
SOURCE = [(n, t) for n, t in CHANGE if n != 'assessment']
ROOTS = ['ri2', 'ri3', 'ri4', 'ri5', 'ri6', 'ri7']


def definitions():
    selected = lambda claim: app(v('scope'), v(claim))
    accepted = lambda claim, stage: app(v('corpus'), v('holder'), v(claim), v(stage))
    truth = lambda claim, point: op('t', app(v('contents'), v(claim)), v(point))
    text = definition('ri2', params(ITEM), both(accepted('claim', 'stage'),
        app(v('supported'), v('holder'), v('claim'), v('stage')), truth('claim', 'assessment')))
    filtered = 'i[owner a claim a phase d][' + both(selected('claim'), k('ri2', *args(ITEM, holder=v('owner'), stage=v('phase')))) + ']'
    text += definition('ri3', params(PROFILE), 'b point[' + k('rgq', v('holder'), v('point'), v('stage'), filtered, v('contents')) + ']', 'e')
    profile = lambda stage: op('t', k('ri3', *args(PROFILE, stage=v(stage))), v('point'))
    compared = app(v('comparisons'), v('point'))
    text += definition('ri4', params(CHANGE), both(op('u', op('e', v('before'), v('after'))),
        app(v('comparisons'), v('assessment')),
        quant('f', 'point', 'd', op('y', compared, op('y', profile('after'), profile('before'))))))
    text += definition('ri5', params(CHANGE), both(k('ri4', *args(CHANGE)),
        quant('g', 'point', 'd', both(compared, profile('before'), op('u', profile('after'))))))
    error = lambda claim, stage: both(selected(claim), accepted(claim, stage), op('u', truth(claim, 'assessment')))
    equivalent = quant('f', 'point', 'd', op('y', compared, op('z', truth('old', 'point'), truth('new', 'point'))))
    no_new = quant('f', 'new', 'a', op('y', error('new', 'after'),
        quant('g', 'old', 'a', both(error('old', 'before'), equivalent))))
    removed = quant('g', 'old', 'a', both(error('old', 'before'),
        quant('f', 'new', 'a', op('y', error('new', 'after'), op('u', equivalent)))))
    text += definition('ri6', params(CHANGE), both(k('ri4', *args(CHANGE)), no_new, removed))
    text += definition('ri7', params(CHANGE), both(k('ri6', *args(CHANGE)), quant('f', 'claim', 'a', op('u', error('claim', 'after')))))
    return text


MEANINGS = {
    'ri2': '同じ主体がその段階で受け入れ、根拠による支持があり、同じ評価状況で内容が真となる命題項目。支持の一般理論や知識の十分条件を定義したものではない。',
    'ri3': '固定した命題範囲でri2を満たす全項目の内容を同時に満たす状況を表す内容。既存rgqの連言構成を使い、項目数を知識量にしない。',
    'ri4': '異なる二段階の同じ主体について、比較状況の範囲が評価状況を含み、後段階のri3を満たす比較状況は全て前段階のri3も満たす。比較範囲内で以前の正しく支持された情報を失わない条件。',
    'ri5': 'ri4に加え、前段階のri3を満たすが後段階には満たさない比較状況がある。正しく支持された情報が比較範囲内で厳密に増えるという拡大の候補。',
    'ri6': 'ri4を保ちながら、後段階で受け入れた誤った内容は全て以前にもあり、以前の誤った内容の少なくとも一つが後段階には残らない。比較状況全体で同じ真偽を持つ別名項目へ置き換えただけなら除去と数えない。',
    'ri7': 'ri6を満たし、固定範囲内で後段階に受け入れられた偽の内容が一つも残らない。範囲外の全ての誤りを除いたとはしない。',
}
LIMITS = [
    'corpusは同じ主体がその段階で受け入れている項目の関係であり、単なる引用・検討中の仮説・所持する文書とは区別する。集団を主体にするときの帰属は別途指定し、全構成員が信じていると補わない。',
    'supportedは同じ主体・命題項目・段階で根拠による支持がある関係。証拠の信頼性・認識過程・理解・偶然の正しさの排除は未構成で、ri2を知識一般の完成した定義とはしない。',
    'scope、contents、comparisons、assessmentは二段階の間で固定する。世界や評価基準が変わったことを、主体の認識の改善として数えない。段階の違いは要求するが、実時間の前後や変化過程の因果をこの比較だけで確定しない。',
    '情報の増加と内容の同値は、明示した比較状況の範囲内で判定する。有限例での一致を全ての可能状況での論理的同値に昇格させない。比較範囲の網羅性・適切さは解釈の前提である。',
    'ri5は意味内容による情報増加の候補であり、数学の恒真命題の新しい証明を理解することや、同じ内容を別の仕方で認識できるようになることまで測らない。記述への認識と内容の一致は引き続き別である。',
    'ri6は同値を除いた誤り内容の厳密な減少。残った誤りが弱い内容へ修正された等の全ての部分改善を網羅せず、ri7は選択範囲内の全除去を区別する。支持されていない受容でも、偽なら誤り側には数える。',
    '主体・支持・真偽・所属の未知を空集合や偽で補わない。関数として渡した内容を評価するが、自然言語を自動解釈したり、項目に名前を与えるだけで内容を確定したりしない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()
    for name, target in (('hzc5', 'ri5'), ('hzc6', 'ri6'), ('hzc7', 'ri7')):
        text += definition(name, params(SOURCE), 'b assessment[' + k(target, *args(CHANGE)) + ']', 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-normative-powers-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-epistemic-revision-basis-v1', document='examples/v014/kant-epistemic-revision.noema')
    basis['definitions'].update(MEANINGS | {
        'hzc5': '同じ主体・二段階・命題範囲・支持・内容・比較状況を固定し、評価状況を受け取ってri5の情報拡大を述べる内容。閉じた適用式を未達成の目的として引用できる。',
        'hzc6': 'hzc5と同じ引数から、ri6の誤りの厳密な減少を述べる内容。正しい情報の損失を伴わないという比較上の条件も保持する。',
        'hzc7': '同じ範囲内のri7の誤り全除去を述べる内容。hzc6の部分的な減少と区別する。'})
    basis['unresolved'] += LIMITS + [
        'u0013のErkenntnisse zu erweiternとvon Irrthümern zu reinigenへの部分候補。知識・理解の一般的な成立、特に重要な知識という焦点、啓蒙を進めること全体は未完。',
        '現在と後続の時代の集団の同定、世代交代、前の時代の契約や宣誓が後続世代の活動を不可能にすること、期間・因果・規範的な否認への接続は未完。新しい原始記号・著者主張は追加しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'epistemic-revision')
def core_composed(): return projected(ROOTS + ['hzc5', 'hzc6', 'hzc7'], 'epistemic-revision-core')
BUILDERS = ((generic_composed, 'epistemic-revision'), (source_composed, 'kant-epistemic-revision'), (core_composed, 'epistemic-revision-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored epistemic revision differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
