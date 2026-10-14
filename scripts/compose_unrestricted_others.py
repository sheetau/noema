"""Separate nonrestricting office requirements from permission for every other person."""
from copy import deepcopy
import json
from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_described_norms import DESCRIPTION, RULE, TRUE

PARENT = 'examples/v014/kant-public-divergent-judgments.noema'
BASE = [('person', 'a'), ('anchor', 'd'), ('officeroles', 'h[a] c'), ('items', 'h[a] c'), ('issuers', 'h[a] a'), ('offices', 'h[a] a'),
    ('actions', 'h[a] a'), ('descriptions', 'h[a] ' + DESCRIPTION), ('signs', 'h[a] c'), ('required', RULE)]
POINT = BASE + [('point', 'd')]
CASES = BASE + [('trigger', 'e'), ('cases', 'h[d] c')]
SOURCE_CASES = [(n, t) for n, t in CASES if n != 'required']
POPULATION = [('population', 'h[a] c'), ('excluded', 'h[a] c'), ('activities', 'h[a a] c'), ('unrestricted', 'h[a a] c'), ('permitted', 'h[a a] c')]
SOURCE_POPULATION = POPULATION[:-1] + [('authority', 'a'), ('roles', 'h[a] a'), ('target', DESCRIPTION), ('anchor', 'd')]
ROOTS = ['rpl', 'rpm', 'rpn', 'rpo', 'rpp', 'rpq', 'rpr', 'rps']


def definitions():
    selected = app(v('items'), v('item'))
    requirement = app(v('required'), app(v('issuers'), v('item')), v('person'), app(v('offices'), v('item')),
        app(v('actions'), v('item')), app(v('descriptions'), v('item')), app(v('signs'), v('item')), v('anchor'))
    text = definition('rpl', params(BASE), quant('f', 'item', 'a', op('y', selected, both(app(v('officeroles'), app(v('offices'), v('item'))), requirement))))
    actual = op('t', app('s[' + app(v('descriptions'), v('item')) + ']', v('person'), app(v('actions'), v('item'))), v('point'))
    fulfilled = quant('f', 'item', 'a', op('y', selected, op('e', actual, app(v('signs'), v('item')))))
    text += definition('rpm', params(POINT), both(k('rpl', *args(BASE)), fulfilled))
    instance = both(app(v('cases'), v('point')), op('t', v('trigger'), v('point')))
    text += definition('rpn', params(CASES), quant('g', 'point', 'd', both(instance, k('rpm', *args(POINT)))))
    text += definition('rpo', params(CASES), both(k('rpl', *args(BASE)), quant('g', 'point', 'd', instance),
        quant('f', 'point', 'd', op('y', instance, k('rpm', *args(POINT))))))
    requested = app(v('required'), v('issuer'), v('person'), v('office'), v('activity'), v('description'), v('sign'), v('anchor'))
    match = both(selected, *[op('e', app(v(fn), v('item')), v(field)) for fn, field in
        (('issuers', 'issuer'), ('offices', 'office'), ('actions', 'activity'), ('descriptions', 'description'), ('signs', 'sign'))])
    covered = op('y', both(app(v('officeroles'), v('office')), requested), quant('g', 'item', 'a', match))
    for field, sort in reversed([('issuer', 'a'), ('office', 'a'), ('activity', 'a'), ('description', DESCRIPTION), ('sign', 'c')]):
        covered = quant('f', field, sort, covered)
    text += definition('rpp', params(BASE), covered)
    text += definition('rpq', params(CASES), both(k('rpp', *args(BASE)), k('rpo', *args(CASES))))
    eligible = both(app(v('population'), v('person')), op('u', app(v('excluded'), v('person'))),
        app(v('activities'), v('person'), v('activity')), app(v('unrestricted'), v('person'), v('activity')))
    text += definition('rpr', params(POPULATION), quant('f', 'person', 'a', quant('f', 'activity', 'a',
        op('y', eligible, app(v('permitted'), v('person'), v('activity'))))))
    text += definition('rps', params(POPULATION), both(k('rpr', *args(POPULATION)), quant('g', 'person', 'a', quant('g', 'activity', 'a', eligible))))
    return text


MEANINGS = {
    'rpl': '選択した各項目が、指定された職務の役割範囲に属し、同じ本人・基準文脈に対する同じ出所・職務・活動・記述・極性の要求である。空の一覧でも真だが、一覧が全義務を尽くすことは含めない。',
    'rpm': 'rplの全選択要求について、その記述内容が同じ比較状況で各要求の極性に一致する。基準文脈の要求を評価しており、比較状況で要求が新設・免除されたことを条件にしない。',
    'rpn': '対象活動が成立する比較候補があり、その同じ候補でrpmの全選択要求も満たせる。別候補での活動と履行を継ぎ合わせない。',
    'rpo': '対象活動が成立する比較候補が少なくとも一つあり、その全てでrpmが成立する。選択要求がその比較範囲で対象活動の候補を排除しないという、rpnより強い条件。',
    'rpp': '同じ本人・基準文脈について、指定職務の役割範囲に属する全出所・全活動・全実行記述・両極性の要求が、同じ組合せの選択項目として一覧に含まれる。一覧外の義務を無断で不存在にしない。',
    'rpq': '指定職務範囲の全要求の網羅性rppと、選択した活動候補を要求が排除しないrpoをともに要求する。網羅したのは義務の記録であり、比較範囲が全可能状況であるとはしない。',
    'rpr': '指定した人々から既出の対象群を除き、該当活動と無制約条件を満たす全ての本人・活動の組に許可がある。無制約だけから許可を導く規則ではなく、許可があるという独立の普遍内容。',
    'rps': 'rprに加えて、その前件を満たす本人・活動の組が少なくとも一つ存在する。空の対象範囲でも成立する普遍内容と区別する。',
    'hzgz': 'rpoの要求を既存h7aへ結ぶ。指定一覧と比較範囲に限定した、職務要求による候補の排除の不在を表す。',
    'hzg2': 'rpqをh7aへ結び、同じ本人の要求の網羅性も保持する。有限検査器で全実行記述の量化を既知の一覧へ縮めない。',
    'hzg3': 'rprの許可を同じ出所・本人・公的役割・活動・閉じた実行記述・基準文脈に対するrdmへ結ぶ。積極的許可と反対要求の不在をともに要求する。',
    'hzg4': 'rpsをhzg3と同じ許可へ結び、対象となる本人・活動の存在も要求する。',
}
LIMITS = [
    '制約を候補の排除として捉えた限定した読みである。義務が一つもないこと、現在の不違反、実行能力、因果的な無妨害、制度上の正当性を同一視しない。義務が存在しても全活動候補で満たせる場合がある。',
    '空一覧は選択要求の不存在を表すにすぎない。全要求がないことにはrppの網羅性が別に必要であり、未知の一覧を空で補わない。rplとrppを合わせれば、一覧と基準文脈の要求が一致する。',
    'officerolesは同じ本人の基準文脈で職務と数える役割範囲を指定する。職務以外の立場への要求を職務義務に混ぜない。その範囲が本人の実際の全職務を尽くすことや、役割の制度上の成立は別に確認が必要である。',
    'rppは全ての型に合う実行記述へ量化する。有限解釈器はこの全域を列挙せず拒否する。二記述への制限検査を全域の網羅性の証明へ置き換えない。',
    '比較範囲は明示した状況だけである。対象活動の実例が空ならrpn・rpo・rpqは偽であり、活動の不在を無制約の根拠としない。比較状況の現実への接続と十分性は別に必要である。',
    'hzg3・hzg4のunrestrictedへhzgzまたはhzg2を同じ人・活動の実行内容で結ぶ。引数の型が合うだけで任意の条件を無制約と認定しない。検査では同じ閉じたtargetから活動内容を作る。',
    'jeder andereの他者は、指定人口から既出の対象群を除いた範囲として記述する。単なる話者本人以外ではない。聖職者の一般的定義と人口の範囲はまだ別に必要である。',
    'noch mehrを許可の真偽の数値的な大小とみなさない。制約の減少によるなおさらという論証の強調・根拠、前節からの推論、君主への照応は未完。',
    '新たな著者主張は追加しない。部分構成を言語化しており、対象文全体とその原始的な意味規約の完成確認は未了。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    for name, target in (('hzgz', 'rpo'), ('hzg2', 'rpq')):
        text += definition(name, params(SOURCE_CASES), k(target, *args(CASES, required='p h7a')))
    permitted = 'i[person a activity a][' + k('rdm', v('authority'), v('person'), app(v('roles'), v('person')), v('activity'),
        v('target'), TRUE, v('anchor'), 'p h7a', 'p h7b') + ']'
    for name, target in (('hzg3', 'rpr'), ('hzg4', 'rps')):
        text += definition(name, params(SOURCE_POPULATION), k(target, *args(POPULATION, permitted=permitted)))
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-public-divergent-judgments-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-unrestricted-others-basis-v1', document='examples/v014/kant-unrestricted-others.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS; audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text); selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'unrestricted-others')
def core_composed(): return projected(ROOTS + ['hzgz', 'hzg2', 'hzg3', 'hzg4'], 'unrestricted-others-core')
BUILDERS = ((generic_composed, 'unrestricted-others'), (source_composed, 'kant-unrestricted-others'), (core_composed, 'unrestricted-others-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored unrestricted others differ: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
