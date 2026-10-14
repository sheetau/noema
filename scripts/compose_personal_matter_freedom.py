"""Bind each person's normative freedom to that person's matters and action descriptions."""
from copy import deepcopy
import json
from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_topical_enablement import JUDGMENT
from scripts.compose_described_norms import DESCRIPTION, RULE, TRUE

PARENT = 'examples/v014/kant-reasoned-responses.noema'
FRAME = [('people', 'h[a] c'), ('topics', 'h[a a] c'), ('activities', 'h[a a a] c'),
    ('assessed', 'h[a a a d] c'), ('eligible', 'h[a] c'), ('context', 'd')]
FIELD = [('source', 'a'), ('roles', 'h[a] a'), ('descriptions', 'h[a a a] ' + DESCRIPTION)] + FRAME + [('required', RULE), ('allowed', RULE)]
SOURCE_FIELD = [(n, t) for n, t in FIELD if n not in ('eligible', 'required', 'allowed')]
CLASSIFIER = [('cases', 'h[d] c'), ('judgments', 'h[a a d] c'), ('matters', 'h[a a d] c'), ('selfassessment', 'h[a a d] c')]
ROOTS = ['rox', 'roy', 'roz', 'rp2']


def definitions():
    text = definition('rox', params([('matter', 'a')] + JUDGMENT), 'i[person a activity a][b point[' + both(
        k('rcr', v('person'), v('activity'), v('point'), *args(JUDGMENT)), app(v('matters'), v('activity'), v('matter'), v('point'))) + ']]', 'h[a a] e')
    person = app(v('people'), v('person')); topic = app(v('topics'), v('person'), v('matter'))
    activity = app(v('activities'), v('person'), v('matter'), v('activity'))
    checked = both(quant('g', 'activity', 'a', activity), quant('f', 'activity', 'a', op('y', activity,
        app(v('assessed'), v('person'), v('matter'), v('activity'), v('context')))))
    valid = both(quant('g', 'person', 'a', person), quant('f', 'person', 'a', op('y', person, both(
        app(v('eligible'), v('person')), quant('g', 'matter', 'a', topic), quant('f', 'matter', 'a', op('y', topic, checked))))))
    text += definition('roy', params(FRAME), valid)
    fields = [v('source'), v('person'), app(v('roles'), v('person')), v('activity'), app(v('descriptions'), v('person'), v('matter'), v('activity'))]
    permissions = both(*(k('rdm', *fields, sign, v('context'), v('required'), v('allowed')) for sign in (TRUE, op('u', TRUE))))
    universal = quant('f', 'person', 'a', quant('f', 'matter', 'a', quant('f', 'activity', 'a', op('y', both(person, topic, activity), permissions))))
    text += definition('roz', params(FIELD), both(k('roy', *args(FRAME)), universal))
    example = both(app(v('cases'), v('point')), app(v('judgments'), v('person'), v('judgment'), v('point')),
        app(v('matters'), v('judgment'), v('matter'), v('point')), app(v('selfassessment'), v('judgment'), v('person'), v('point')))
    text += definition('rp2', params(CLASSIFIER), 'i[person a matter a][' + quant('g', 'point', 'd', quant('g', 'judgment', 'a', example)) + ']', 'h[a a] c')
    return text


MEANINGS = {
    'rox': '本人が同じ判断行為で自分の理解力を使い、用いた理由による支持と他者の指導の不在があり、その判断が同じ指定事柄についてである。rcrの行為と判断対象を固定した内容関数。',
    'roy': '選んだ人々が非空で全員が適格であり、各人の事柄が非空、その各事柄の対象活動が非空で全活動が同じ評価文脈で確認されている。ある人の事柄や活動で別人の不足を埋めない。',
    'roz': 'royの同じ人物・事柄・活動・記述について、同じ出所が実行と不実行の双方を積極的に許し、反対要求がない。各人に一つだけ許可された事柄があればよいという意味ではない。',
    'rp2': '指定した分類用の状況のいずれかに、同じ本人が同じ事柄について判断し、その判断が本人自身の行為を評価するという例がある。本人・判断・事柄・状況を保持する。現在の実行や達成能力を要求しない。',
    'hzgo': 'roxの所有・使用・判断・対象・理由・支持・指導をab・ac・fa・fb・fc・fd・adへ接続する。本人の理性使用への一つの明示的な活動記述であり、許可とは別の条件。',
    'hzgp': 'rozの適格性と規範をaa・h7a・h7bへ接続する。人ごとの事柄、事柄ごとの活動・実行記述を保持し、実行や能力を推定しない。',
    'hzgq': 'rp2の判断主体・対象・自己評価をfa・fb・seへ接続する。指定分類例において、本人の行為を道徳的要求に照らして判断する事柄という、良心に関わる事柄の部分分類。',
}
LIMITS = [
    '各人の事柄を別々の範囲として保持する。他人の事柄を全員へ一律に配ること、各人に少なくとも一つの許可があること、全ての事柄で全員が実際に判断したことと区別する。',
    '規範上の選択は一つの出所・役割・時点と明示した範囲に相対的である。実際の能力、無妨害、法的権利、全規範源の自由を保証しない。',
    'descriptionsは人物・事柄・活動を受けて閉じた実行記述を返す。原文接続例では事柄を固定したhzgoを引用する。型だけで任意の記述がその事柄を表すと認定せず、同じ真偽の別記述へ規範を移さない。',
    'hzgqのcasesは分類のための明示的な例の状況であり、現在の実行履歴や実行可能な未来の一覧ではない。その中の判断が現在実行済みであることや本人に可能であることは推定しない。分類の網羅性や原文の良心の語義全体は別途検討が必要である。',
    'seは本人の行為を道徳的要求に照らす既存の関係である。道徳的要求の内容・正当性、宗教的信念・感情・葛藤としての良心全体をこの分類だけで説明し終えない。',
    'hzgoは用いた理由の支持と他者の指導の不在を含む、理性使用の強い操作的な読みである。自分で行った誤った推論の全てを排除する語義だと主張しない。',
    '原文のfrei ließを、その出所に相対的な自由が成立する条件へ部分接続する。以前からの自由を保持した時間経過、政府の全制度、本文全体の意味一致は未完。原始記号と著者主張は追加しない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions() + definition('hzgo', 'matter a', k('rox', v('matter'), *['p ' + n for n in ('ab', 'ac', 'fa', 'fb', 'fc', 'fd', 'ad')]), 'h[a a] e')
    text += definition('hzgp', params(SOURCE_FIELD), k('roz', *args(FIELD, eligible='p aa', required='p h7a', allowed='p h7b')))
    text += definition('hzgq', 'cases h[d] c', k('rp2', v('cases'), 'p fa', 'p fb', 'p se'), 'h[a a] c')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-reasoned-responses-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-personal-matter-freedom-basis-v1', document='examples/v014/kant-personal-matter-freedom.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS; audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text); selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'personal-matter-freedom')
def core_composed(): return projected(ROOTS + ['hzgo', 'hzgp', 'hzgq'], 'personal-matter-freedom-core')
BUILDERS = ((generic_composed, 'personal-matter-freedom'), (source_composed, 'kant-personal-matter-freedom'), (core_composed, 'personal-matter-freedom-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored personal matter freedom differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
