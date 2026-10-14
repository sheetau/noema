"""Explicit periodization and overlapping human cohorts, tied to undertaking acts."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_solemn_undertakings import SOURCE_PURPOSE
from scripts.compose_mutual_undertakings import FORM

PARENT = 'examples/v014/kant-blocked-revision.noema'
FRAME = [('history', 'h[d] c'), ('before', 'h[d d] c'), ('periods', 'h[a d] c')]
PERIOD = [('epoch', 'a')] + FRAME
PAIR = [('earlier', 'a'), ('later', 'a')] + FRAME
CATALOG = [('epochs', 'h[a] c')] + FRAME
NEXT = [('earlier', 'a'), ('later', 'a')] + CATALOG
MEMBERSHIP = [('context', 'd'), ('population', 'h[a] c'), ('human', 'h[a] c'), ('present', 'h[a d] c'), ('belongs', 'h[a a d] c')]
COHORT = [('group', 'a'), ('epoch', 'a')] + MEMBERSHIP + FRAME
SUCCESSION = [('firstgroup', 'a'), ('nextgroup', 'a')] + NEXT + MEMBERSHIP
SOURCE = [(n, t) for n, t in SUCCESSION if n not in ('human', 'before')]
UNDERTAKING = SOURCE + [(n, t) for n, t in SOURCE_PURPOSE if n not in dict(SOURCE)]
ROOTS = ['rjc', 'rjd', 'rje', 'rjf', 'rjg', 'rjh']


def definitions():
    scope = 'i[point d][' + app(v('periods'), v('epoch'), v('point')) + ']'
    text = definition('rjc', params(PERIOD), k('tb', v('history'), scope, v('before')))
    ordered = quant('f', 'first', 'd', quant('f', 'second', 'd', op('y', both(
        app(v('periods'), v('earlier'), v('first')), app(v('periods'), v('later'), v('second'))), app(v('before'), v('first'), v('second')))))
    text += definition('rjd', params(PAIR), both(op('u', op('e', v('earlier'), v('later'))),
        k('rjc', *args(PERIOD, epoch=v('earlier'))), k('rjc', *args(PERIOD, epoch=v('later'))), ordered))
    selected = lambda name: app(v('epochs'), v(name))
    catalog = both(quant('g', 'epoch', 'a', selected('epoch')),
        quant('f', 'epoch', 'a', op('y', selected('epoch'), k('rjc', *args(PERIOD)))),
        quant('f', 'left', 'a', quant('f', 'right', 'a', op('y', both(selected('left'), selected('right'), op('u', op('e', v('left'), v('right')))),
            op('x', k('rjd', *args(PAIR, earlier=v('left'), later=v('right'))), k('rjd', *args(PAIR, earlier=v('right'), later=v('left'))))))))
    text += definition('rje', params(CATALOG), catalog)
    middle = quant('g', 'middle', 'a', both(selected('middle'),
        k('rjd', *args(PAIR, later=v('middle'))), k('rjd', *args(PAIR, earlier=v('middle')))))
    text += definition('rjf', params(NEXT), both(k('rje', *args(CATALOG)), selected('earlier'), selected('later'), k('rjd', *args(PAIR)), op('u', middle)))
    member = app(v('belongs'), v('group'), v('person'), v('context'))
    qualifies = both(app(v('population'), v('person')), app(v('human'), v('person')),
        quant('g', 'point', 'd', both(app(v('periods'), v('epoch'), v('point')), app(v('present'), v('person'), v('point')))))
    text += definition('rjg', params(COHORT), both(k('rjc', *args(PERIOD)),
        quant('g', 'person', 'a', member), quant('f', 'person', 'a', op('z', member, qualifies))))
    text += definition('rjh', params(SUCCESSION), both(op('u', op('e', v('firstgroup'), v('nextgroup'))),
        k('rjf', *args(NEXT)), k('rjg', *args(COHORT, group=v('firstgroup'), epoch=v('earlier'))),
        k('rjg', *args(COHORT, group=v('nextgroup'), epoch=v('later')))))
    return text


MEANINGS = {
    'rjc': '同じ厳密な全順序の履歴内で、時代に割り当てた状況範囲が空でなく、間の抜けない区間である。',
    'rjd': '異なる二時代がともにrjcを満たし、前の時代の全状況が後の時代の全状況に先行する。区間の一部だけの前後や重なりを先後としない。',
    'rje': '明示した非空の時代区分に含まれる全時代がrjcを満たし、異なる二時代はrjdで一方向に順序付けられる。重複区間を持つ別名の時代を並列に入れない。',
    'rjf': 'rjeの同じ時代区分で、指定二時代が選ばれ、rjdで前後し、その間に別の選択時代がない。区分に相対的な直後であり、全時間の連続被覆を含めない。',
    'rjg': '同じ基準文脈で集団の所属が、指定母集団内の人間で同じ時代区間の少なくとも一状況に生存する人とちょうど一致し、集団が空でない。時代をまたぐ人を排除せず、血縁や一斉の交代は仮定しない。',
    'rjh': '異なる二集団を同じ文脈・母集団・生存関係でそれぞれの時代にrjgで結び、時代間にrjfの直後関係がある。時代の順序を個人間の親子関係へ置換しない。',
    'hzde': 'rjhの人間を既存aa、時間順序を同じcontextでのicへ接続する。時代区分・母集団・生存・所属を引数で明示する部分解釈。',
    'hzdf': 'hzdeを満たし、基準状況が先行時代にあり、hzcwの目的付き宣誓の全当事者が同じ先行集団に所属する。各当事者の引受け・宣誓・目的の同じ行為の状況も先行時代に制限する。後続集団を全当事者に混ぜず、先行集団の全員が当事者とも仮定しない。',
}
LIMITS = [
    'periodsは時代に状況範囲を割り当て、epochsはこの読みで採る時代区分を選ぶ。歴史的な区分の妥当性、期間の尺度、現実への対応は別途説明する。間に未選択の時代や時間の空白がないことをrjfからは導かない。',
    'presentは本人がその状況で生存するという関係で、場所に居合わせることや所属とは別。生と死の一般的な定義は未完。populationは時代の前後で固定し、文化・社会の対象範囲を黙って変えない。',
    'belongsは同じ文脈で集団と人を結ぶ所属関係。rjgでは母集団・生存・時代から所属の範囲を照合するが、集団の同一性や制度を集合の外延だけで決定しない。二集団の構成員が重なってもよい。',
    '時代をその時代の人々で読む明示的な候補であり、Zeitalterを生物学的世代の厳密な区切りや全人類の一斉交代へ翻訳しない。時代区分を細かくすれば直後関係が変わる。',
    'hzdfは当事者の範囲と行為時点を同じ先行時代へ結ぶ。集団全体を代表する資格、全員の共同意図や制度上の規範的効力をそれだけでは与えない。',
    'hzdfのgoalは閉じた内容記述。検査例では後続集団をhzddのholderへ固定し、先行する当事者がその状態を生じさせる閉じたhzcqを目的に渡す。型だけでは任意の目的の対象が後続集団であることを保証しない。',
    'カントのkann nichtの規範的読解、verschwörenの否定的・共謀的含意、mussの必然性、知識・啓蒙の一般的定義、著者の主張への帰属は未完。実際の契約や妨害の発生を追加しない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    before = 'i[first d second d][' + k('ic', v('first'), v('second'), v('context')) + ']'
    text = definitions() + definition('hzde', params(SOURCE), k('rjh', *args(SUCCESSION, human='p aa', before=before)))
    fields = [('person', 'a'), ('act', 'a'), ('agreement', 'a'), ('terms', dict(FORM)['terms']), ('bindings', 'j[a]'), ('scene', 'd')]
    declares = 'i[' + params(fields) + '][' + both(app(v('declares'), *args(fields)), app(v('periods'), v('earlier'), v('scene'))) + ']'
    parties = quant('f', 'person', 'a', op('y', app(v('parties'), v('person'), v('context')), app(v('belongs'), v('firstgroup'), v('person'), v('context'))))
    body = both(k('hzde', *args(SOURCE)), app(v('periods'), v('earlier'), v('context')), parties,
        k('hzcw', *args(SOURCE_PURPOSE, declares=declares)))
    text += definition('hzdf', params(UNDERTAKING), body)
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-blocked-revision-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-successive-cohorts-basis-v1', document='examples/v014/kant-successive-cohorts.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis); return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'successive-cohorts')
def core_composed(): return projected(ROOTS + ['hzde', 'hzdf', 'hzdd', 'hzcq', 'rin'], 'successive-cohorts-core')
BUILDERS = ((generic_composed, 'successive-cohorts'), (source_composed, 'kant-successive-cohorts'), (core_composed, 'successive-cohorts-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored successive cohort differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
