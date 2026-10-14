"""Bundle norm changes and ask a scoped hypothetical self-imposition question."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_policy_norms import DESCRIPTION, RULE, TRUE
from scripts.compose_normative_powers import CONTROL, EDGE, EFFECT

PARENT = 'examples/v014/kant-attribution-choices.noema'
CLAUSE = 'h[a a d d] c'
CLAUSES = 'j[' + CLAUSE + ']'
BINDINGS = 'h[a a] j[a]'
CLAUSE_FIELDS = [('role', 'a'), ('target', DESCRIPTION), ('bindings', BINDINGS), ('polarity', 'c'),
    ('status', 'c'), ('valid', 'h[j[a]] c'), ('relation', RULE)]
PACKAGE = [('law', 'a'), ('people', 'a'), ('start', 'd'), ('end', 'd'), ('clauses', CLAUSES)]
TRANSITION = [('framework', 'a'), ('actor', 'a'), ('capacity', 'a'), ('exercise', DESCRIPTION),
    ('law', 'a'), ('people', 'a'), ('start', 'd'), ('end', 'd'), ('clauses', CLAUSES),
    ('exercisevalid', 'h[j[a]] c'), ('controlled', CONTROL), ('recognizes', EDGE)]
POWER = [(n, t) for n, t in TRANSITION if n != 'end']
SELF = [(n, t) for n, t in POWER if n not in ('actor', 'start', 'clauses')] + [
    ('clauses', 'h[a] ' + CLAUSES), ('assessor', 'a'), ('context', 'd'),
    ('candidates', 'h[a a d d] c'), ('required', RULE), ('allowed', RULE)]
CRITERION = [(n, t) for n, t in SELF if n != 'law'] + [
    ('eligible', 'h[a a a d] c'), ('admissible', 'h[a a a d] c')]
SOURCE_SELF = [(n, t) for n, t in SELF if n not in ('context', 'required', 'allowed')]
SOURCE_CRITERION = [(n, t) for n, t in CRITERION if n not in ('context', 'required', 'allowed')]
ROOTS = ['rj7', 'rka', 'rkb', 'rkc', 'rkd', 'rke', 'rkf', 'rkg', 'rdr']


def exercise_bindings(actor='actor'):
    return 'l[a][' + ' '.join(v(n) for n in (actor, 'people', 'law')) + ']'


def definitions():
    effect = k('riv', *args(EFFECT, source=v('law'), person=v('people'), bindings=app(v('bindings'), v('law'), v('people'))))
    text = definition('rj7', params(CLAUSE_FIELDS), 'i[law a people a start d end d][' + effect + ']', CLAUSE)
    package = 'q[v clauses][' + TRUE + '][i[state c clause ' + CLAUSE + '][' + both(v('state'), app(v('clause'), *args(PACKAGE[:4]))) + ']]'
    text += definition('rka', params(PACKAGE), both(op('u', op('e', v('start'), v('end'))),
        op('u', op('e', 'd[v clauses]', 'n p a b')), package))
    bindings = exercise_bindings()
    text += definition('rkb', params(TRANSITION), both(app(v('exercisevalid'), bindings),
        app(v('controlled'), v('actor'), v('exercise'), bindings, v('start')),
        app(v('recognizes'), v('framework'), v('actor'), v('capacity'), v('exercise'), bindings, v('start'), v('end')),
        k('rka', *args(PACKAGE))))
    text += definition('rkc', params(POWER), quant('g', 'end', 'd', k('rkb', *args(TRANSITION))))
    permission = k('rdu', v('assessor'), v('people'), v('capacity'), v('exercise'), exercise_bindings('people'), TRUE,
        v('branch'), v('exercisevalid'), v('required'), v('allowed'))
    power = k('rkc', *args(POWER, actor=v('people'), start=v('branch'), clauses=app(v('clauses'), v('law'))))
    possible = quant('g', 'branch', 'd', both(app(v('candidates'), v('people'), v('law'), v('context'), v('branch')), permission, power))
    text += definition('rkd', params(SELF), possible)
    for name, connective in (('rke', 'y'), ('rkf', 'z')):
        eligible = app(v('eligible'), v('actor'), v('people'), v('law'), v('context'))
        condition = op(connective, app(v('admissible'), v('actor'), v('people'), v('law'), v('context')), k('rkd', *args(SELF)))
        text += definition(name, params(CRITERION), quant('f', 'actor', 'a', quant('f', 'law', 'a', op('y', eligible, condition))))
    fields = [(n, t) for n, t in SELF if n != 'context']
    text += definition('rkg', params(fields), k('rij', 'b context[' + k('rkd', *args(SELF)) + ']', TRUE), 'f')
    return text


MEANINGS = {
    'rj7': '法を規範の出所、人民を名宛人として、指定した一つの規範の成立または廃止を既存rivで記述する。対象記述・役割・極性を保ち、対象の引数列も同じ法と人民から作る。',
    'rka': '非空の規範変更条件の列が、同じ法・人民・異なる前後状況について全て成立する。一条項ずつ別の結果状況で成立するだけでは足りない。',
    'rkb': '主体・人民・法の三個体を同じ行使の引数列に置き、その行使の適合性、主体の統制、同じ制度的枠組みの認定と、同じ前後状況のrkaを結ぶ。',
    'rkc': '同じ主体の同じ行使から、同じ法の全変更が共同で成立する結果状況が存在する。実際の行使や許可を含まず、列が空なら成立しない。',
    'rkd': '指定した人民・法・基準文脈の候補状況の少なくとも一つで、人民自身を行使主体とし、同じ行使に衝突のない許可rduと規範変更の権能rkcが共にある。別候補の許可と権能を混ぜない。',
    'rke': '全ての指定対象の主体・法について、その人民への立法が指定基準で許容されるなら、同じ人民・法のrkdが成立するという必要条件。対象の実際の採択を要求しない。',
    'rkf': 'rkeと同じ対象範囲で、許容条件とrkdの同値を要求する。必要条件だけを十分条件へ強めない。',
    'rkg': '同じ設定のrkdが成立するかを問う正極性の質問発話。質問の作成だけで肯定回答・現実の許可・実行を補わない。',
    'hzd3': 'rj7の規範関係を既存h7kの要求へ接続した変更条件。',
    'hzd4': 'rj7の規範関係を既存h7lの積極的許可へ接続した変更条件。要求の変更とは区別する。',
    'hzd5': 'rkdの仮定的な自己立法の条件を既存h7k・h7lへ接続した内容。',
    'hzd6': 'hzd5を問う質問発話。同じ人民・法と三個体の行使引数を保持する。',
    'hzd7': 'rkeの必要条件を既存の規範関係で内容化する。',
    'hzea': 'rkfの同値の判断基準を既存の規範関係で内容化する。hzd7との強さの違いを保持する。',
}
LIMITS = [
    '規範変更の列は条項を含む型付き関数の列であり、原語の法律名を意味の代用にしない。ただし任意の同型関数が法的な条項であるとは型だけで保証しない。接続例では要求・許可の変更をrj7で構成する。',
    '同じ人民を共同主体と規範の名宛人へ束縛する。全市民が個別に立法する、全員が現実に同意した、直接投票した、代表者が正当に選ばれたことを補わない。市民個々への配分は別の量化が必要。',
    '規範の変更を生む権能、行使の許可、実際の行使、物理的な実行可能性は別である。rkdは候補状況での許可と権能を組み合わせた操作的な読みであり、原文のkönnteの唯一の語義とはしない。',
    '候補は同じ人民・法・基準文脈に相対的である。実際に起きた状況や現在の制度だけに限定しないが、理性的に可能な同意・正当性を候補関係の名前だけで説明し終えたとはしない。選定根拠と網羅性は残る。',
    'rj7は不在から成立、または成立から不在への指定変更を扱う。既存の法の確認、変更を伴わない採択、全ての法形式をこれだけで網羅したとはしない。条件の全てが同じ結果で成立しても、列外の効果が不変だとは要求しない。',
    '必要条件と同値の判断基準を別に保持する。対象範囲が空でも普遍条件は真となるが、法や立法主体の存在を主張しない。基準として採用することと、現実の制度がその基準を満たすことは別。',
    'u0013の自己立法の問いと判断基準への部分解釈。wohlの含意、人民・法・立法の基礎定義、合理的な共同意思、代表資格、著者帰属、後続の暫定的秩序と君主の議論は未完。新しい著者主張は追加しない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()
    fields = [(n, t) for n, t in CLAUSE_FIELDS if n != 'relation']
    for name, relation in (('hzd3', 'h7k'), ('hzd4', 'h7l')):
        text += definition(name, params(fields), k('rj7', *args(CLAUSE_FIELDS, relation='p ' + relation)), CLAUSE)
    text += definition('hzd5', params(SOURCE_SELF), 'b context[' + k('rkd', *args(SELF, required='p h7k', allowed='p h7l')) + ']', 'e')
    text += definition('hzd6', params(SOURCE_SELF), k('rij', k('hzd5', *args(SOURCE_SELF)), TRUE), 'f')
    for name, target in (('hzd7', 'rke'), ('hzea', 'rkf')):
        text += definition(name, params(SOURCE_CRITERION), 'b context[' + k(target, *args(CRITERION, required='p h7k', allowed='p h7l')) + ']', 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-attribution-choices-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-self-legislation-basis-v1', document='examples/v014/kant-self-legislation.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'self-legislation')
def core_composed(): return projected(ROOTS + ['hzd3', 'hzd4', 'hzd5', 'hzd6', 'hzd7', 'hzea', 'hzcr'], 'self-legislation-core')
BUILDERS = ((generic_composed, 'self-legislation'), (source_composed, 'kant-self-legislation'), (core_composed, 'self-legislation-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored self legislation differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
