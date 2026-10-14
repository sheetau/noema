"""Choose communities from shared undertakings and explicit continuation aims."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_mutual_undertakings import FORM, ASSIGNED, DECLARES
from scripts.compose_policy_norms import DESCRIPTION, TRUE
from scripts.compose_parameterized_goals import AIMS
from scripts.compose_observed_protection import SOURCE as POLICY_SOURCE
from scripts.compose_community_protection import GOAL, FALSE

PARENT = 'examples/v014/kant-observed-protection.noema'
ITEM = [('terms', DESCRIPTION), ('person', 'a'), ('community', 'a'), ('institution', 'a')]
DIFFERENCE = [('terms', DESCRIPTION), ('person', 'a'), ('community', 'a'), ('older', 'a'), ('newer', 'a'), ('comparisons', 'h[d] c')]
CHANGE = [('community', 'a'), ('older', 'a'), ('newer', 'a')] + [(n, t) for n, t in FORM if n != 'arguments'] + [
    ('members', 'h[a a d] c'), ('attributed', 'h[a a d] c'), ('comparisons', 'h[d] c')]
WISH = [('community', 'a'), ('institution', 'a'), ('terms', DESCRIPTION), ('context', 'd'),
    ('proponents', 'h[a d] c'), ('eligible', 'h[a] c'), ('members', 'h[a a d] c'), ('attributed', 'h[a a d] c'), ('aims', AIMS)]
PRESERVE = [('terms', DESCRIPTION), ('community', 'a'), ('institution', 'a'), ('persons', 'h[a d] c'), ('anchor', 'd')]
SOURCE_CHANGE = [(n, t) for n, t in CHANGE if n not in ('context', 'eligible', 'history', 'before', 'occurs', 'performs')] + [('histories', 'h[d] h[d] c')]
SOURCE_WISH = [(n, t) for n, t in WISH if n not in ('context', 'eligible')]
CONFIG = [(n, t) for n, t in POLICY_SOURCE if n not in ('changeconditions', 'stayconditions', 'activities', 'goals')] + [
    ('terms', DESCRIPTION), ('olders', 'h[a] a'), ('newers', 'h[a] a'), ('agreements', 'h[a] a'),
    ('parties', 'h[a] h[a d] c'), ('proponents', 'h[a] h[a d] c'), ('histories', 'h[d] h[d] c'),
    ('assigned', ASSIGNED), ('declares', DECLARES), ('members', 'h[a a d] c'), ('attributed', 'h[a a d] c'),
    ('comparisons', 'h[d] c'), ('aims', AIMS), ('changegoals', 'h[a] ' + GOAL), ('staygoals', 'h[a] ' + GOAL)]
ROOTS = ['rk7', 'rla', 'rlb', 'rlc', 'rld', 'rle', 'rlf']


def bindings(institution='institution'):
    return 'l[a][' + ' '.join(v(n) for n in ('person', 'community', institution)) + ']'


def definitions():
    text = definition('rk7', params(ITEM), app('s[v terms]', bindings()), 'e')
    content = lambda institution: op('t', k('rk7', *args(ITEM, institution=v(institution))), v('point'))
    text += definition('rla', params(DIFFERENCE), quant('g', 'point', 'd', both(app(v('comparisons'), v('point')),
        op('u', op('z', content('older'), content('newer'))))))
    eligible = 'i[person a][' + both(app(v('eligible'), v('person')), app(v('members'), v('community'), v('person'), v('context'))) + ']'
    formed = k('rhz', *args(FORM, arguments='i[person a][' + bindings('newer') + ']', eligible=eligible))
    changed = quant('g', 'person', 'a', both(app(v('parties'), v('person'), v('context')), k('rla', *args(DIFFERENCE))))
    text += definition('rlb', params(CHANGE), both(app(v('attributed'), v('community'), v('agreement'), v('context')), formed, changed))
    proponent = app(v('proponents'), v('person'), v('context'))
    shared = quant('f', 'person', 'a', op('y', proponent, both(app(v('eligible'), v('person')),
        app(v('members'), v('community'), v('person'), v('context')),
        app(v('aims'), v('person'), v('act'), v('terms'), bindings(), v('context')))))
    text += definition('rlc', params(WISH), both(quant('g', 'person', 'a', proponent),
        quant('g', 'act', 'a', both(app(v('attributed'), v('community'), v('act'), v('context')), shared))))
    holds = 'i[point d][' + op('t', app('s[v terms]', v('bindings')), v('point')) + ']'
    persisted = k('rca', app(v('histories'), v('start')), v('before'), v('start'), holds)
    text += definition('rld', 'terms ' + DESCRIPTION + ' histories h[d] h[d] c before h[d d] c',
        'i[bindings j[a]][b start[' + both(k('rdr', v('bindings'), 'n p d b'), persisted) + ']]', 'h[j[a]] e')
    slots = [('person', 'a'), ('community', 'a'), ('institution', 'a')]
    three = 'h[a a a] e'
    initial = 'i[' + params(slots) + '][' + app(v('configurations'), v('community'), v('institution')) + ']'
    shifted = 'i[' + params(slots) + '][' + app(v('state'), v('item'), v('person'), v('community')) + ']'
    step = 'i[state ' + three + ' item a][' + shifted + ']'
    folded = 'q[v bindings][' + initial + '][' + step + ']'
    result = op('t', app(folded, v('seed'), v('seed'), v('seed')), v('context'))
    text += definition('rle', 'configurations h[a a] e', 'i[bindings j[a]][b context[' + both(
        k('rdr', v('bindings'), 'n p d b'), quant('g', 'seed', 'a', result)) + ']]', 'h[j[a]] e')
    person = app(v('persons'), v('person'), v('anchor'))
    text += definition('rlf', params(PRESERVE), 'b context[' + both(quant('g', 'person', 'a', person),
        quant('f', 'person', 'a', op('y', person, op('t', k('rk7', *args(ITEM)), v('context'))))) + ']', 'e')
    return text


MEANINGS = {
    'rk7': '同じ条項関数の記述を、本人・共同体・制度という順序付き三個体へ適用して内容を得る。合意、目的、実現する活動でこの同じ引数規約を共有する。',
    'rla': '同じ条項記述・本人・共同体に旧制度と新制度をそれぞれ渡し、明示した比較状況のどこかで内容が異なる。単なる識別子や記述の別名の違いを制度変更と数えない。',
    'rlb': '同じ共同体に帰属する合意について、選んだ二者以上の適格な成員全員が同じ条項記述と同じ新制度への引受けを表明し、少なくとも一人の条項内容が旧制度と異なる。実施済みや全成員の全員一致は要求しない。',
    'rlc': '空でない目的主体が同じ共同体の適格な成員であり、同じ共同体に帰属する一つの計画・活動で、同じ条項記述と本人・共同体・制度への束縛を目指す。目的の実現・実行や、別の制度への反対を条件にしない。',
    'rld': '三個体列の条項内容が、同じ履歴の基準点以降で持続するという条項関数を作る。旧制度を今望むだけでなく、明示した期間で続ける目的を構成する。',
    'rle': '共同体・制度から内容への関数を、本人・共同体・制度という順序付き三個体列の条項関数へ接続する。本人は引受けや目的の帰属に使い、構成する制度状態自体は共同体と制度に依存する。',
    'rlf': '基準点で固定した非空の対象者全員について、同じ条項記述・共同体・制度の内容が成立するという活動内容。合意・目的の記述を、保護する活動と異なる内容へ交換しない。',
    'hzel': 'rlbの引受けを、人aa、実際の行為dg、本人の実行f3、同じ文脈の時間順序icへ接続する変更側の条件内容。',
    'hzem': 'rlcの目的主体を人aaとする維持側の条件内容。目的の活動を実行したことや維持状態の真理は補わない。',
    'hzen': 'hzelで新制度を選ぶ側とhzemで旧制度を望む側を、観測整合性付きのhzekへ接続する。保護する活動は同じ条項のrlfから構成し、変更側と維持側の目標を分け、政策・共同体・選択基準点・モデル・観測を共有する。',
}
LIMITS = [
    'termsは本人・共同体・制度という三個体列から内容への閉じた条項記述である。rleで制度状態を接続し、rldで継続内容を構成する。同じ条項記述を合意・目的・活動へ渡す。任意の同型の関数を宗教制度の定義済みの内容と認定しない。',
    'rlaの内容差は明示した比較範囲に相対的である。範囲外の違い、組織名・儀礼・制度史など内容値に含めなかった側面の変更は判定しない。比較範囲が適切・網羅的であることは別の課題。',
    '当事者や目的主体の範囲は共同体の全成員と同一とは限らない。共同体への帰属attributedと所属membersを明示するが、代表資格・正当な意思決定手続を構成し終えたとはしない。',
    'rlcは共同体へ帰属する同じ計画・活動での目的という、継続を望むことの一つの強い読みである。個人の願望、選好、発言だけから集団の意思を推定しない。目的形成・団結・意思の強さの一般理論は残る。',
    'rldは指定履歴の基準点以降の持続を使う。有限の履歴を現実の永続としない。rleは三位置の順次束縛であり、順序・重複を保持し、長さが三でない列を拒否する。',
    '条項の内容比較・実現を含む定義には脱引用がある。提案内容として引用する前に、同じ既知の閉じた条項記述へ静的に特殊化する。実行時の引用生成、未知の値の補完、生成モデルによる翻訳は行わない。',
    '宗教制度の具体的な内容、よりよい理解についての当事者の判断、etwaや接続法の不確定性、君主の位置、原文への著者帰属と全文の意味確認は未完。新しい原始記号・著者主張は追加しない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    before = 'i[first d second d][' + k('ic', v('first'), v('second'), v('context')) + ']'
    text = definitions() + definition('hzel', params(SOURCE_CHANGE), 'b context[' + k('rlb', *args(CHANGE,
        eligible='p aa', history=app(v('histories'), v('context')), before=before, occurs='p dg', performs='p f3')) + ']', 'e')
    text += definition('hzem', params(SOURCE_WISH), 'b context[' + k('rlc', *args(WISH, eligible='p aa')) + ']', 'e')
    changes = k('hzel', *args(SOURCE_CHANGE, older=app(v('olders'), v('community')), newer=app(v('newers'), v('community')),
        agreement=app(v('agreements'), v('community')), parties=app(v('parties'), v('community'))))
    stays = k('hzem', *args(SOURCE_WISH, institution=app(v('olders'), v('community')), proponents=app(v('proponents'), v('community'))))
    no_condition = 'i[community a][b point[' + FALSE + ']]'
    policies = []
    for changed in (True, False):
        activity = k('rlf', *args(PRESERVE, institution=app(v('newers' if changed else 'olders'), v('community')),
            persons=app(v('parties' if changed else 'proponents'), v('community'))))
        policy = k('hzek', *args(POLICY_SOURCE,
            changeconditions='i[community a][' + changes + ']' if changed else no_condition,
            stayconditions=no_condition if changed else 'i[community a][' + stays + ']',
            activities='i[community a][' + activity + ']', goals=v('changegoals' if changed else 'staygoals')))
        policies.append(op('t', policy, v('context')))
    text += definition('hzen', params(CONFIG), 'b context[' + both(*policies) + ']', 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-observed-protection-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-institutional-choices-basis-v1', document='examples/v014/kant-institutional-choices.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'institutional-choices')
def core_composed(): return projected(ROOTS + ['hzel', 'hzem', 'hzen', 'hzef'], 'institutional-choices-core')
BUILDERS = ((generic_composed, 'institutional-choices'), (source_composed, 'kant-institutional-choices'), (core_composed, 'institutional-choices-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored institutional choices differ: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
