"""Compare personal judgments with an adopted criterion on the same issue."""
from copy import deepcopy
import json
from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_personal_criteria import APPRAISAL, JUDGING
from scripts.compose_policy_norms import DESCRIPTION

PARENT = 'examples/v014/kant-retained-duties.noema'
COMPARE = [('owncriterion', DESCRIPTION), ('standardcriterion', DESCRIPTION), ('bindings', 'j[a]'), ('cases', 'h[d] c')]
POINT = [('person', 'a'), ('judgment', 'a'), ('subject', 'a'), ('owncriterion', DESCRIPTION), ('standardcriterion', DESCRIPTION), ('context', 'd')] + JUDGING + [('cases', 'h[d] c')]
COLLECTION = [('person', 'a'), ('organization', 'a'), ('issues', 'h[a] c'), ('judgmentfor', 'h[a] a'),
    ('owncriterion', DESCRIPTION), ('standardcriterion', DESCRIPTION), ('context', 'd')] + JUDGING + [
    ('comparisons', 'h[a d] c'), ('adopted', 'h[a ' + DESCRIPTION + ' d] c')]
SOURCE = [(n, t) for n, t in COLLECTION if n not in ('judgments', 'matters')]
ROOTS = ['rpb', 'rpc', 'rpd', 'rpe', 'rpf', 'rpg', 'rph']


def definitions():
    chosen = app(v('cases'), v('point'))
    left = op('t', app('s[v owncriterion]', v('bindings')), v('point'))
    right = op('t', app('s[v standardcriterion]', v('bindings')), v('point'))
    equal = op('e', left, right)
    text = definition('rpb', params(COMPARE), quant('g', 'point', 'd', both(chosen, op('u', equal))))
    text += definition('rpc', params(COMPARE), both(quant('g', 'point', 'd', chosen), quant('f', 'point', 'd', op('y', chosen, equal))))
    text += definition('rpd', params(COMPARE), both(quant('g', 'point', 'd', both(chosen, left)),
        quant('g', 'point', 'd', both(chosen, right)), op('u', quant('g', 'point', 'd', both(chosen, left, right)))))
    judged = k('rlg', *args(APPRAISAL, criterion=v('owncriterion'), bindings='l[a][v subject]'))
    text += definition('rpe', params(POINT), both(judged, k('rpb', *args(COMPARE, bindings='l[a][v subject]'))))
    point = dict(judgment=app(v('judgmentfor'), v('subject')), cases='i[point d][' + app(v('comparisons'), v('subject'), v('point')) + ']')
    divergence = k('rpe', *args(POINT, **point))
    member = app(v('issues'), v('subject'))
    adoption = app(v('adopted'), v('organization'), v('standardcriterion'), v('context'))
    text += definition('rpf', params(COLLECTION), both(adoption, quant('g', 'subject', 'a', both(member, divergence))))
    text += definition('rpg', params(COLLECTION), both(adoption, quant('g', 'subject', 'a', member), quant('f', 'subject', 'a', op('y', member, divergence))))
    agreement = both(k('rlg', *args(APPRAISAL, judgment=point['judgment'], criterion=v('owncriterion'), bindings='l[a][v subject]')),
        k('rpc', *args(COMPARE, bindings='l[a][v subject]', cases=point['cases'])))
    text += definition('rph', params(COLLECTION), both(k('rpf', *args(COLLECTION)), quant('g', 'subject', 'a', both(member, agreement))))
    return text


MEANINGS = {
    'rpb': '同じ順序付き引数列について、指定比較状況の少なくとも一つで二つの基準内容の真偽が異なる。式の綴りの相違や、比較外での違いだけでは成立しない。',
    'rpc': '比較範囲が非空で、同じ引数列について全比較状況で二つの基準内容が一致する。その範囲での一致であり、全状況での同義性とはしない。',
    'rpd': '比較範囲で二つの内容がそれぞれ充足可能だが、共に真になる比較状況がない。単なる内容差rpbより強い、範囲を限定した両立不能。',
    'rpe': '同じ人・判断・論点・文脈についてrlgの個人的判断が成立し、その論点を唯一の引数とする本人の基準と標準基準の内容にrpbの差がある。判断候補と比較範囲は分離する。',
    'rpf': '組織が同じ標準基準の閉じた記述を採用し、選択論点の少なくとも一つで本人のrpeの判断がその基準と異なる。他の論点について一致も不一致も主張しない。',
    'rpg': '組織が同じ標準基準を採用し、選択論点が非空で、その全てでrpeの差がある。選択範囲を教理全体とみなさず、全体の否認や論理的矛盾を導かない。',
    'rph': 'rpfに加え、同じ選択範囲に本人の判断が成立し標準とrpcの一致を示す論点がある。一致と相違が混在する、rpfより強い条件。',
    'hzgv': 'rpfの判断者と判断対象を既存fa・fbへ結ぶ。組織による基準の採用と個人の判断を別関係として保持する。',
    'hzgw': 'rphをfa・fbへ結ぶ。一部の相違と別の論点での一致がともに確認された読みであり、原文からこの強い読みを自動採用しない。',
}
LIMITS = [
    'hier oder daは少なくとも一つの指定論点での差という弱い読みで部分記述する。相違点が厳密に少数であること、全体の何割か、他の全論点での一致は未指定。rphの混在条件を原文の必須条件にしない。',
    'standardcriterionは引数列から内容を作る同じ閉じた記述であり、採用関係にも比較にも同じ値を使う。組織の採用から本人の賛同・基準の真理・権威の正当性を導かない。',
    '比較は同じ論点の単一要素の引数列に固定する。比較状況の選び方・網羅性・現実への接続は別途必要であり、有限検査を全可能状況の意味同一性判定にしない。',
    '本人の判断はrlgの非空候補による非事実的な認識モデルである。判断候補で本人の基準が成立しても、現在の真理や知識・洞察の正当性は認定しない。Einsichtenの認識上の含意は未完。',
    '両立不能rpdでは両側の充足可能性を要求する。異なる内容、自己矛盾、全教理の否認、全論点の不一致を混同しない。',
    '二つの基準を引用対象にする際は、同じ閉じた記述へ静的特殊化して動的な脱引用を除く。引用だけでは判断や採用の真偽を評価しない。',
    'adoptedは既存の個体・基準記述・文脈の採用関係と同じ型を取る明示入力である。教会・教理・宗教・聖職者という名詞の一般的説明、制度的採用の成立過程は未完。',
    '許可、職務義務の保存、学者としての公的な提示、世界による吟味への統合は未完。原文への部分注記であり、新たな著者主張や全文の意味確認を追加しない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    for name, target in (('hzgv', 'rpf'), ('hzgw', 'rph')):
        text += definition(name, params(SOURCE), k(target, *args(COLLECTION, judgments='p fa', matters='p fb')))
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-retained-duties-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-partial-divergence-basis-v1', document='examples/v014/kant-partial-divergence.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS; audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text); selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'partial-divergence')
def core_composed(): return projected(ROOTS + ['hzgv', 'hzgw'], 'partial-divergence-core')
BUILDERS = ((generic_composed, 'partial-divergence'), (source_composed, 'kant-partial-divergence'), (core_composed, 'partial-divergence-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored partial divergence differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
