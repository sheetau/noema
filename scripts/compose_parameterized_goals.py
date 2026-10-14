"""Bind goal templates to explicit individuals without constructing runtime quotes."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_mutual_undertakings import ACT, FORM
from scripts.compose_solemn_undertakings import APPEAL, strengthened
from scripts.compose_successive_cohorts import UNDERTAKING, SOURCE as COHORT
from scripts.compose_policy_norms import DESCRIPTION, RULE, TRUE

PARENT = 'examples/v014/kant-normative-denials.noema'
AIMS = 'h[a a ' + DESCRIPTION + ' j[a] d] c'
PRODUCES = 'h[a ' + DESCRIPTION + ' j[a] d] c'
GOAL = [('goal', DESCRIPTION), ('goalbindings', 'j[a]'), ('goalvalid', 'h[j[a]] c'), ('aims', AIMS)]
PURPOSE = FORM + [('proponents', 'h[a d] c')] + GOAL
SOLEMN = PURPOSE + APPEAL
CAUSE = [('agents', 'h[a] c'), ('act', 'a'), ('result', DESCRIPTION), ('bindings', 'j[a]'), ('valid', 'h[j[a]] c'),
    ('context', 'd'), ('occurs', 'h[a d] c'), ('participates', 'h[a a d] c'), ('produces', PRODUCES)]
CAUSAL_CONTENT = [(n, t) for n, t in CAUSE if n not in ('act', 'context')]
CAUSAL_SOURCE = [(n, t) for n, t in CAUSAL_CONTENT if n not in ('occurs', 'participates')]
CASE = [('firstgroup', 'a'), ('nextgroup', 'a'), ('earlier', 'a'), ('later', 'a'), ('agreement', 'a')]
ELIGIBLE = 'h[a a a a a d] c'
UNIVERSAL = [('source', 'a'), ('role', 'a'), ('description', DESCRIPTION), ('context', 'd'),
    ('eligible', ELIGIBLE), ('required', RULE), ('allowed', RULE)]
UNIVERSAL_SOURCE = [(n, t) for n, t in UNIVERSAL if n not in ('context', 'required', 'allowed')]
SOURCE = [(n, t) for n, t in UNDERTAKING if n != 'goal'] + [('goal', DESCRIPTION), ('aims', AIMS)]
ROOTS = ['rjt', 'rju', 'rjv', 'rjw', 'rjx', 'rjy', 'rjz', 'rj2']


def case_bindings(): return 'l[a][' + ' '.join(args(CASE)) + ']'
def case_shape(): return 'i[bindings j[a]][' + k('rdr', v('bindings'), 'n p f b') + ']'


def quantify(kind, body):
    for name, sort in reversed(CASE): body = quant(kind, name, sort, body)
    return body


def definitions():
    aim = app(v('aims'), v('person'), v('act'), v('goal'), v('goalbindings'), v('scene'))
    text = definition('rjt', params(ACT + GOAL), both(k('rhx', *args(ACT)), app(v('goalvalid'), v('goalbindings')), aim))
    proponent = lambda person: app(v('proponents'), v(person), v('context'))
    fields = [('person', 'a'), ('act', 'a'), ('agreement', 'a'), ('terms', DESCRIPTION), ('bindings', 'j[a]'), ('scene', 'd')]
    adapted = 'i[' + params(fields) + '][' + both(app(v('declares'), *args(fields)), op('y', proponent('person'), aim)) + ']'
    body = both(app(v('goalvalid'), v('goalbindings')), quant('g', 'person', 'a', proponent('person')),
        quant('f', 'person', 'a', op('y', proponent('person'), app(v('parties'), v('person'), v('context')))),
        k('rhz', *args(FORM, declares=adapted)))
    text += definition('rju', params(PURPOSE), body)
    text += definition('rjv', params(SOLEMN), k('rju', *args(PURPOSE, declares=strengthened())))
    actual = op('t', app('s[v result]', v('bindings')), v('context'))
    body = both(app(v('valid'), v('bindings')), quant('g', 'person', 'a', app(v('agents'), v('person'))),
        app(v('occurs'), v('act'), v('context')),
        quant('f', 'person', 'a', op('y', app(v('agents'), v('person')), app(v('participates'), v('person'), v('act'), v('context')))),
        app(v('produces'), v('act'), v('result'), v('bindings'), v('context')), actual)
    text += definition('rjw', params(CAUSE), body)
    text += definition('rjx', params(CAUSAL_CONTENT), 'b context[' + quant('g', 'act', 'a', k('rjw', *args(CAUSE))) + ']', 'e')
    eligible = app(v('eligible'), *args(CASE), v('context'))
    for name, target in (('rjy', 'rjq'), ('rjz', 'rjp')):
        norm = k(target, v('source'), v('firstgroup'), v('role'), v('description'), case_bindings(), TRUE,
            v('context'), case_shape(), v('required'), v('allowed'))
        text += definition(name, params(UNIVERSAL), quantify('f', op('y', eligible, norm)))
    text += definition('rj2', 'context d eligible ' + ELIGIBLE, quantify('g', eligible))
    return text


MEANINGS = {
    'rjt': '同じ引受け行為で、目的の関数記述・順序付き対象列への目的志向があり、対象列がその目的の規約に適合する。目的の内容・達成・実現可能性は実行評価しない。',
    'rju': '非空の目的主体が同じ相互引受けの当事者に含まれ、各目的主体の引受けと、同じ目的記述・対象列への志向が同じ行為で成立する。条項の個人別引数と、全員が指す目的の対象列は分ける。',
    'rjv': 'rjuの同じ行為・人物・時点に、既存の厳粛な表明と権威への呼びかけを結ぶ。目的の対象列を、宣誓の個人別引数列へ勝手に交換しない。',
    'rjw': '非空の行為者群の同じ行為が、同じ結果の関数記述と適合する対象列を用いて指定される結果を生じさせ、その同じ適用内容も成立する。因果への引数と実際に評価する引数を一致させる。',
    'rjx': 'rjwを満たす行為があるという内容。記述を既知の関数へ静的に特殊化すれば、対象列を変数のまま保った通常のNoemaとして引用できる。実行時に値を引用文字列へ変換しない。',
    'rjy': '先行集団・後続集団・前後の時代・契約という五個体の全組合せについて、指定適用条件を満たすなら、同じ先行集団に同じ五個体列の政策を禁止する反対要求がある。実際に契約が形成された場合だけへ範囲を縮めない。',
    'rjz': 'rjyと同じ全組合せについて、適用条件を満たす対象への積極的許可がない。禁止との違いを保持し、一部の具体例の許可欠如を全称へ昇格させない。',
    'rj2': '指定した五個体の適用条件を満たす組合せが少なくとも一つある。rjy・rjzの普遍条件と別で、契約が実際に形成されたことを意味しない。',
    'hzdq': '同じ時代区分と集団のhzdeに、先行時代内の目的付き宣誓rjvを結ぶ。目的の対象列を先行集団・後続集団・前時代・後時代・同じ契約の五個体へ固定する。全当事者の所属と同じ行為の時点を保つ。',
    'hzdr': 'rjxの行為者を既存aaの人間、行為の生起をdg、参加をdfへ接続する。結果の関数記述と順序付き対象列は保持し、因果関係を引数で明示する。',
    'hzds': 'rjyの普遍的禁止条件を、既存h7k・h7lと同じ出所・役割・対象記述へ接続した内容。適用条件と政策記述は明示的に渡し、原文の全該当事例を自動認定しない。',
    'hzdt': '同じ設定でrjzの普遍的な許可欠如を述べる内容。hzdsの禁止とは別の読解候補であり、存在や著者の賛同を追加しない。',
}
LIMITS = [
    '目的と結果は、閉じた関数記述と明示的な個体列の組で表す。記述の同一性と列の同一性をともに保持する。値が同じ別名の記述や、順序の違う列へ自動移送しない。',
    'aimsは本人・行為・目的関数記述・対象列・状況の目的志向、producesは行為・結果関数記述・対象列・状況の因果関係を意味する。既存hzu等の閉じた内容一個への関係を、引数を増やして再解釈しない。新しい形の関係は明示した引数で受け取る。',
    'この構成は個体列による対象の束縛である。数・状況・関数を個体へ偽装しない。それらは既存の型付き閉じた記述内に保持できるが、今回それらの値全てを個体列で量化したとはしない。',
    'rjw・rjx・hzdrは動的な脱引用を含む。既知の結果関数記述を固定して静的に特殊化する場合だけ、通常の引用へ展開する。未指定の記述を推測したり、実行時の対象を新しい引用記号へ変換したりしない。',
    '普遍条件の適用範囲はeligibleで明示する。該当例がない場合もrjy・rjzは真になるため、rj2を別に用意する。有限検査の全個体を、現実の全時代・集団・契約の網羅性の証明とはしない。',
    'hzdqの目的列の五位置は固定するが、型だけで任意の関数記述がその規約を意味的に満たすとは保証しない。前版の改善不能・必然性を含む因果目的全体を五個体で再利用する構成と、制度的代表資格は未完。',
    'hzds・hzdtは量化された否認の骨格であり、hzdqを対象政策に含む原文全体の普遍命題、kann nichtの一意の読み、理由付け・著者帰属は未完。既存の特定契約の記述を捨てたり、語句を文字列へ格納して表現済みと数えたりしない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    before = 'i[first d second d][' + k('ic', v('first'), v('second'), v('context')) + ']'
    fields = [('person', 'a'), ('act', 'a'), ('agreement', 'a'), ('terms', DESCRIPTION), ('bindings', 'j[a]'), ('scene', 'd')]
    declares = 'i[' + params(fields) + '][' + both(app(v('declares'), *args(fields)), app(v('periods'), v('earlier'), v('scene'))) + ']'
    body = both(k('hzde', *args(COHORT)), app(v('periods'), v('earlier'), v('context')),
        quant('f', 'person', 'a', op('y', app(v('parties'), v('person'), v('context')), app(v('belongs'), v('firstgroup'), v('person'), v('context')))),
        k('rjv', *args(SOLEMN, eligible='p aa', before=before, occurs='p dg', performs='p f3', declares=declares,
            goalbindings=case_bindings(), goalvalid=case_shape())))
    text += definition('hzdq', params(SOURCE), body)
    humans = quant('f', 'person', 'a', op('y', app(v('agents'), v('person')), k('aa', v('person'))))
    text += definition('hzdr', params(CAUSAL_SOURCE), 'b context[' + both(humans,
        op('t', k('rjx', *args(CAUSAL_CONTENT, occurs='p dg', participates='p df')), v('context'))) + ']', 'e')
    for name, target in (('hzds', 'rjy'), ('hzdt', 'rjz')):
        text += definition(name, params(UNIVERSAL_SOURCE), 'b context[' + k(target, *args(UNIVERSAL, required='p h7k', allowed='p h7l')) + ']', 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-normative-denials-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-parameterized-goals-basis-v1', document='examples/v014/kant-parameterized-goals.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis); return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS + ['rin'], 'parameterized-goals')
def core_composed(): return projected(ROOTS + ['hzdq', 'hzdr', 'hzds', 'hzdt', 'rin'], 'parameterized-goals-core')
BUILDERS = ((generic_composed, 'parameterized-goals'), (source_composed, 'kant-parameterized-goals'), (core_composed, 'parameterized-goals-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored parameterized goal differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
