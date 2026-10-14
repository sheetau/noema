"""Preserve the same signed office duties when another activity is permitted."""
from copy import deepcopy
import json
from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_described_norms import DESCRIPTION, RULE, TRUE

PARENT = 'examples/v014/kant-personal-matter-freedom.noema'
BASE = [('person', 'a'), ('office', 'a'), ('anchor', 'd'), ('items', 'h[a] c'), ('issuers', 'h[a] a'),
    ('actions', 'h[a] a'), ('descriptions', 'h[a] ' + DESCRIPTION), ('signs', 'h[a] c'), ('required', RULE)]
POINT = BASE + [('point', 'd')]
CASES = BASE + [('trigger', 'e'), ('cases', 'h[d] c')]
SOURCE = [(n, t) for n, t in CASES if n != 'required']
PERMISSION = [(n, t) for n, t in SOURCE if n != 'trigger'] + [
    ('authority', 'a'), ('publicrole', 'a'), ('publicact', 'a'), ('publicdescription', DESCRIPTION)]
ROOTS = ['rp3', 'rp4', 'rp5', 'rp6', 'rp7', 'rpa']


def definitions():
    item = app(v('items'), v('item'))
    required = lambda point: app(v('required'), app(v('issuers'), v('item')), v('person'), v('office'),
        app(v('actions'), v('item')), app(v('descriptions'), v('item')), app(v('signs'), v('item')), v(point))
    text = definition('rp3', params(BASE), both(quant('g', 'item', 'a', item), quant('f', 'item', 'a', op('y', item, required('anchor')))))
    text += definition('rp4', params(POINT), both(k('rp3', *args(BASE)), quant('f', 'item', 'a', op('y', item, required('point')))))
    applicable = both(app(v('cases'), v('point')), op('t', v('trigger'), v('point')))
    preserved = quant('f', 'point', 'd', op('y', applicable, k('rp4', *args(POINT))))
    text += definition('rp5', params(CASES), both(k('rp3', *args(BASE)), quant('g', 'point', 'd', app(v('cases'), v('point'))), preserved))
    text += definition('rp6', params(CASES), both(k('rp5', *args(CASES)), quant('g', 'point', 'd', applicable)))
    actual = op('t', app('s[' + app(v('descriptions'), v('item')) + ']', v('person'), app(v('actions'), v('item'))), v('point'))
    fulfilled = quant('f', 'item', 'a', op('y', item, op('e', actual, app(v('signs'), v('item')))))
    text += definition('rp7', params(POINT), both(k('rp4', *args(POINT)), fulfilled))
    text += definition('rpa', params(CASES), both(k('rp5', *args(CASES)), quant('g', 'point', 'd', both(applicable, k('rp7', *args(POINT))))))
    return text


MEANINGS = {
    'rp3': '非空の選択項目の全てについて、基準文脈で同じ本人・職務・出所・活動・記述・極性の要求がある。要求の存在を履行や正当性と同一視しない。',
    'rp4': 'rp3の同じ選択項目に対する同じ要求が、指定比較文脈でも成立する。別人・別職務・別出所・別記述・逆の極性への要求で保存を代用しない。',
    'rp5': '比較文脈が非空で、指定活動内容が成立する全比較文脈でrp4を満たす。対象活動の実例がない場合も条件自体は成立し得る。',
    'rp6': 'rp5に加え、対象活動内容が成立する比較文脈が少なくとも一つある。実例を持たない条件から分ける。現実での活動や達成能力は要求しない。',
    'rp7': '同じ比較文脈でrp4の要求が残り、選択項目の記述内容がそれぞれの要求極性に一致する。義務の消滅による空虚な履行と区別し、肯定要求と否定要求を保持する。',
    'rpa': 'rp5を満たし、同じ一つの比較文脈で対象活動と全選択義務の履行rp7が共に成立する。別々の候補での成立を継ぎ合わせない。',
    'hzgr': 'rp5の要求をh7aへ接続する。職務義務を免除しない条件の部分的な構成。選択した項目を、その職務の全義務だと無断で認定しない。',
    'hzgs': 'rp6をh7aへ接続し、活動の実例を含む比較範囲で要求が保存される条件を作る。',
    'hzgt': 'rpaをh7aへ接続し、活動と残存する選択義務の同じ候補内での共充足を述べる。実行方法の存在・実際の履行・物理的な無妨害は含めない。',
    'hzgu': '同じ本人の公的役割・活動・閉じた実行記述への基準文脈での積極的許可と、その記述の実行を条件としたhzgrを結ぶ。許可元と職務義務の出所を別に保持する。',
}
LIMITS = [
    'unbeschadet ihrer Amtspflichtのうち、義務を免除しないことと共充足の余地を分けて記述する。職務遂行を因果的に妨げないこと、法的な優先順位、制度上の正当性を保存だけから導かない。',
    'items・issuers・actions・descriptions・signsは基準文脈から比較文脈へ固定する。項目名を同じにしたまま、人物・役割・記述・極性を取り替えない。追加の要求が生じることは排除しない。',
    '選択項目は非空で、全て基準文脈に存在する要求である。職務の全要求を網羅することはこの条件だけで保証しない。一般の記述全域への網羅性は既存rfhなどの別条件であり、有限検査はそれを代用しない。',
    'casesは同じ比較のための状況を選び、現実に到達できる未来を自動で表さない。比較文脈の存在を、本人の能力や現実の発言として扱わない。時間的な前後関係も強制しない。',
    '相反する極性の要求も保存し得る。rp4やrp5から無矛盾性を推定しない。同じ内容への肯定・否定の双方が要求されれば、rp7とrpaの全項目履行は成立しない。',
    'rp7とrpaは閉じた実行記述を評価する。未知記述への脱引用を含むまま引用することはできない。保存条件rp3からrp6は記述を実行せず、閉じた構成を引用できる。',
    'hzguのpublicdescriptionへ未知の記述を渡したまま引用しない。引用対象にする際は同じ閉じた実行記述へ静的特殊化する。型だけで任意の活動が学者としての公的発言であるとは認定しない。',
    '原文への部分注記であり、聖職者の意味・学者という資格・公開性・世界の公衆・吟味という目的・教理との差異・敬意の評価、本文全体の意味一致は残る。新たな著者主張は追加しない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    for name, target in (('hzgr', 'rp5'), ('hzgs', 'rp6'), ('hzgt', 'rpa')):
        text += definition(name, params(SOURCE), k(target, *args(CASES, required='p h7a')))
    trigger = app('s[v publicdescription]', v('person'), v('publicact'))
    permission = k('rdm', v('authority'), v('person'), v('publicrole'), v('publicact'), v('publicdescription'), TRUE, v('anchor'), 'p h7a', 'p h7b')
    text += definition('hzgu', params(PERMISSION), both(permission, k('hzgr', *args(SOURCE, trigger=trigger))))
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-personal-matter-freedom-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-retained-duties-basis-v1', document='examples/v014/kant-retained-duties.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS; audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text); selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'retained-duties')
def core_composed(): return projected(ROOTS + ['hzgr', 'hzgs', 'hzgt', 'hzgu'], 'retained-duties-core')
BUILDERS = ((generic_composed, 'retained-duties'), (source_composed, 'kant-retained-duties'), (core_composed, 'retained-duties-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored retained duties differ: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
