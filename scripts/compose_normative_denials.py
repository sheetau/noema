"""Guard normative negation and bind the same collective undertaking as its target."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_policy_norms import DESCRIPTION, RULE, TRUE
from scripts.compose_normative_powers import POWER, SOURCE as POWER_SOURCE
from scripts.compose_successive_cohorts import UNDERTAKING

PARENT = 'examples/v014/kant-necessary-futures.noema'
NORM = [('source', 'a'), ('person', 'a'), ('role', 'a'), ('description', DESCRIPTION), ('bindings', 'j[a]'),
    ('polarity', 'c'), ('context', 'd'), ('valid', 'h[j[a]] c'), ('required', RULE), ('allowed', RULE)]
SOURCE = [(n, t) for n, t in NORM if n not in ('polarity', 'context', 'required', 'allowed')]
ADAPTER = [(n, t) for n, t in UNDERTAKING if n not in ('firstgroup', 'context')]
ROOTS = ['rjp', 'rjq', 'rjr', 'rjs']
SOURCE_ROOTS = ['hzdk', 'hzdl', 'hzdm', 'hzdn', 'hzdo', 'hzdp', 'hzc2', 'hzc3', 'hzdh', 'hzdi', 'hzdj', 'hzcq', 'rin']


def definitions():
    text = definition('rjp', params(NORM), both(app(v('valid'), v('bindings')), op('u', k('rdt', *args(NORM)))))
    text += definition('rjq', params(NORM), k('rds', *args(NORM, polarity=op('u', v('polarity')))))
    text += definition('rjr', params(NORM), both(app(v('valid'), v('bindings')), op('u', k('rdu', *args(NORM)))))
    valid = both(app(v('exercisevalid'), v('exercisebindings')), 'a[v exercisebindings][n p a b][v actor]', app(v('valid'), v('bindings')))
    text += definition('rjs', params(POWER), both(valid, op('u', k('rix', *args(POWER)))))
    return text


MEANINGS = {
    'rjp': '対象の引数が適合し、同じ出所・名宛人・役割・記述・引数列・極性・文脈への積極的な許可がない。反対要求や禁止をそれだけで補わない。',
    'rjq': '同じ適合する対象について反対極性が要求される。対象内容を実行せよという正極性を渡した場合、その不成立への要求を表す。許可と衝突する場合も要求の存在を消さない。',
    'rjr': '対象の引数が適合し、反対要求と衝突しない許可rduがない。積極的許可がない場合と、許可はあるが反対要求もある場合を含む。rjpやrjqと同一ではない。',
    'rjs': '行使と規範対象の引数が適合し、行使引数列の先頭が同じ主体である上で、指定した規範変更を生む権能rixがない。不正な引数や別主体への入力を権能の否認として認定しない。',
    'hzdk': '一個体だけの引数列から先行集団を取り、固定した後続集団・時代区分・合意・条項・宣誓・目的についてhzdfの成立内容を返す関数。集団を引数先頭に置き、同じ行使を規範と権能の両方の対象として記述できる。',
    'hzdl': '同じ指定対象について、既存h7k・h7lに関する正極性のrjpの許可欠如を、評価文脈ごとの内容にする。対象の実行や能力を評価しない。',
    'hzdm': '同じ指定対象の不成立を要求するrjqを内容にする。許可の欠如とは別の、禁止の読解候補。',
    'hzdn': '同じ指定対象への衝突のない許可がないrjrを内容にする。許可と反対要求が併存する場合を、許可そのものがない場合と分ける。',
    'hzdo': '同じ行使によって指定した要求h7kを成立・廃止させる権能がないというrjsの内容。対象・行使の適合条件を保ち、物理的な行為不能や規範的禁止とは分ける。',
    'hzdp': '同じ行使によって指定した積極的許可h7lを成立・廃止させる権能がないというrjsの内容。要求を変更する権能の不在から自動推定しない。',
}
LIMITS = [
    '否定される関係の未知を偽に補わない。引数が適合したことは、規範・制度的効果・許可の情報が完全に判明したことを意味しない。有限解釈は指定関係の全値を入力した検査例である。',
    '許可の欠如、禁止、衝突のない許可の欠如、特定の規範を変える権能の欠如は独立に指定する。禁止されても制度上の効果を生む権能が残る場合を表せる。',
    'hzdkは一個体列を取り、その個体を先行集団へ束縛する。既存の空列専用の閉じた政策を、一個体列へ暗黙に変更しない。残る引数は通常の型付き引用として記述内に保持する。',
    '集団を規範の名宛人・行使主体にする解釈は、集団の代表資格や共同意思の理論の完成を意味しない。hzdfが要求する当事者の所属・同じ時代内の行為・目的を保持するが、外側の規範からそれらの実際の成立を推定しない。',
    'rjsは指定した一つの規範変更についての権能の不在。要求・許可・権能・免責を含む全制度効果の不存在や、契約全体の一般的な無効性へ広げない。',
    '原文への具体例は、同じ閉じたhzdkの記述を行使と規範の対象へ渡す。任意の型が合う記述への否認を、全てこの契約についての否認として扱わない。規範の出所・役割・制度は原文から自動確定しない。',
    'u0013のkann nichtについて、規範的な読解候補を複数保持する。どれが原文の否認に当たるかを一意に確定せず、全てを著者の主張へ追加しない。著者帰属、権利・人間本性からの理由付け、普遍量化は未完。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    body = both(k('rdr', v('bindings'), 'n p b b'), quant('g', 'firstgroup', 'a', both(
        'a[v bindings][n p a b][v firstgroup]', k('hzdf', *args(UNDERTAKING)))))
    text += definition('hzdk', params(ADAPTER), 'i[bindings j[a]][b context[' + body + ']]', 'h[j[a]] e')
    for name, target in (('hzdl', 'rjp'), ('hzdm', 'rjq'), ('hzdn', 'rjr')):
        text += definition(name, params(SOURCE), 'b context[' + k(target, *args(NORM, polarity=TRUE, required='p h7k', allowed='p h7l')) + ']', 'e')
    for name, relation in (('hzdo', 'h7k'), ('hzdp', 'h7l')):
        text += definition(name, params(POWER_SOURCE), 'b start[' + k('rjs', *args(POWER, relation='p ' + relation)) + ']', 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-necessary-futures-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-normative-denials-basis-v1', document='examples/v014/kant-normative-denials.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis); return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'normative-denials')
def core_composed(): return projected(ROOTS + SOURCE_ROOTS, 'normative-denials-core')
BUILDERS = ((generic_composed, 'normative-denials'), (source_composed, 'kant-normative-denials'), (core_composed, 'normative-denials-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored normative denial differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
