"""Connect existing use standards to one judgment, keeping two clocks distinct."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_qualified_judgment import ROOT, closure, QUALITY, QCODE, both

PARENT = 'examples/v016/kant-qualified-judgment.noema'
PARENT_BASIS = 'data/qualified-judgment-basis-v1.json'
FULL = 'examples/v016/kant-judgment-standards.noema'
CORE = 'examples/v016/judgment-standards-core.noema'
LIBRARY = 'examples/v016/judgment-standards.noema'
BASIS = 'data/judgment-standards-basis-v1.json'
APPLICABLE = 'h[a a a a d d] c'
EVIDENCE = 'h[a a a a c d d] c'
STANDARDS = [('standard', 'a'), ('adopted', 'h[a d] c'), ('member', 'h[a a d] c'),
             ('applicable', APPLICABLE), ('evidence', EVIDENCE)]
TARGETS = {'rqwx': 'rbi', 'rqwy': 'rbj', 'rqwz': 'rbk', 'rqw2': 'rbl', 'rqw3': 'rbm'}
MEANINGS = {
    'rqwx': '採用基準とその全適用項目を基準文脈に固定し、別に指定した実行時点の同じ人・資源・行為をrbiで評価する。全項目に肯定・否定の証拠のちょうど一方がある評価充足性であり、適合そのものではない。',
    'rqwy': 'rqwxと同じ基準文脈・実行時点・使用を保持するrbjの証拠に基づく適合。非空の全適用項目に肯定だけの証拠が必要で、無証拠や衝突を成功にしない。実際の正しさや基準の正当性の証明とは別である。',
    'rqwz': '同じ二時点の設定でrbkの違反根拠を述べる。全項目に衝突がなく、少なくとも一項目に否定の証拠がある。他項目の資料不足と両立する。',
    'rqw2': '同じ二時点の設定でrblの証拠衝突を述べる。同じ適用項目で肯定と否定が共存する場合であり、別項目の異なる評定だけでは衝突としない。',
    'rqw3': '同じ二時点の設定でrbmの資料不足を述べる。衝突がなく、少なくとも一項目に肯定・否定の証拠がどちらもない。実際の不適合へ読み替えない。',
    'hzvx': '同じ本人の同じ事柄に関する判断と、その判断で実際に使う本人所有の一つの能力について、rqwyの全項目の適合があるという五引数の基準を返す。項目ごとに異なる能力の評価を寄せ集めない。',
    'hzvy': '基準・採用・項目範囲・適用条件・証拠の閉じた記述をhzvxへ適用し、質の引数へ渡せる閉じた基準記述を組み立てる。構築だけではこれらの参照や証拠を実行評価しない。',
}
LIMITS = [
    '既存rbhからrbmの評価制度を再利用する接続であり、目的達成rbnから適切さを導かない。個人の任意の目的の達成を原文のgutへ採用する変更ではない。',
    '基準の採用・項目の範囲はcontext、実際の使用はpointで評価する。適用条件と証拠は両方を受け取り、過去の基準に照らして後の遂行を評価できる。証拠を知った日時や評価者の知識はこれら二時点から補わない。',
    '証拠の存在と項目の事実的充足は別である。hzvxは証拠に基づく適合という基準候補であって、適切な遂行一般やsicher und gutの必要十分条件ではない。基準の正当性・証拠の信頼性と網羅性は未確定である。',
    'hzvxを能力の目標に指定すると、評価対象は証拠に基づく適合を伴う遂行になる。資料不足によるこの目標の不成立から、実際の判断能力の欠如を結論しない。rqwx・rqwz・rqw2・rqw3で評価状態を別に記述できる。',
    '本人所有の同じ能力と同じ判断について全項目を照合するが、複数能力を使う判断でその全能力の適合を求める構成ではない。対象事柄との関係は保持し、他の事柄の判断を証人にしない。',
    '宗教的対象範囲、質の語義の採用、不足の程度、集団基準、問答・進行・徴候と著者帰属の統合は未完。現行41文と十単位604文字の意味判断を保持し、対応文字数を増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def parameters(fields):
    return ' '.join(n + ' ' + t for n, t in fields)


def definitions():
    fields = 'standard a person a resource a act a context d point d adopted h[a d] c member h[a a d] c applicable ' + APPLICABLE + ' use h[a a a d] c evidence ' + EVIDENCE
    # rbi..rbm read the standard at context; the adapters explicitly select point
    # for performance and retain BOTH clocks for applicability and evidence.
    applicable = 'i[q a p a r a j a c d][c[v applicable][v q v p v r v j v c v point]]'
    use = 'i[p a r a j a c d][c[v use][v p v r v j v point]]'
    evidence = 'i[q a p a r a j a sign c c d][c[v evidence][v q v p v r v j v sign v c v point]]'
    args = 'v standard v person v resource v act v context v adopted v member ' + applicable + ' ' + use + ' ' + evidence
    text = ''.join('d ' + n + '[' + fields + '] c[k ' + t + '[' + args + ']].' for n, t in TARGETS.items())
    judgment = both('k fa[v person v judgment v point]', 'k fb[v judgment v matter v point]')
    conformity = 'k rqwy[v standard v person v resource v judgment v context v point v adopted v member v applicable p ac v evidence]'
    witness = 'g resource a[' + both('k ab[v resource v person v point]', conformity) + ']'
    text += 'd hzvx[' + parameters(STANDARDS) + '] ' + QUALITY + '[i[person a matter a judgment a context d point d][' + both(judgment, witness) + ']].'
    codes = [(n, 'i[' + t + ']') for n, t in STANDARDS]
    text += 'd hzvy[' + parameters(codes) + '] ' + QCODE + '[o a[r[p hzvx]][' + ' '.join('v ' + n for n, _ in STANDARDS) + ']].'
    return text


def build():
    old = parent()
    d = deepcopy(old.document)
    statements, d['statements'] = d['statements'], []
    size = len(d['declarations'])
    assert not set(MEANINGS) & set(old.entries)
    d = parse(format_graph(d, 'compact') + definitions())
    d['statements'] = statements
    lib = deepcopy(d)
    lib['declarations'] = closure(d, list(TARGETS))
    lib['statements'] = []
    core = deepcopy(d)
    core['declarations'] = closure(d, list(MEANINGS) + ['hzvq', 'hzvr', 'hzvs', 'hzvg'])
    core['statements'] = []
    basis = dict(status='judgment_use_standards_with_fixed_reference_and_performance_contexts', document=FULL,
        library=LIBRARY, parent=PARENT, inherited_meaning_basis=PARENT_BASIS, primitives={}, definitions=MEANINGS,
        new_signatures={x['name']: {k: x[k] for k in ('parameters', 'result')} for x in d['declarations'][size:]}, limitations=LIMITS)
    return {FULL: format_graph(d, 'compact') + '\n', CORE: format_graph(core, 'compact') + '\n',
        LIBRARY: format_graph(lib, 'compact') + '\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}


def main():
    for name, text in build().items():
        path = ROOT / name
        if path.exists():
            assert path.read_text(encoding='utf-8') == text, name
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
    print('Existing standards connected to the same judgment and resource', flush=True)


if __name__ == '__main__':
    main()
