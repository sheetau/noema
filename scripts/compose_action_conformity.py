"""Conformity of a specified action, with an explicit completeness condition."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, definition, v, call as k, app, op, both, quant
from scripts.compose_assessed_payments import ALL, PAY_NAMES
from scripts.compose_described_norms import DESCRIPTION, RULE, TRUE

PARENT = 'examples/v014/kant-assessed-payments.noema'
DESCRIPTIONS = 'j[' + DESCRIPTION + ']'
SCOPE = 'sources h[a] c descriptions ' + DESCRIPTIONS
FIELDS = 'person a role a action a context d'
BASE = FIELDS + ' required ' + RULE
FIELDS_NAMES = ('person', 'role', 'action', 'context')
SCOPED = SCOPE + ' ' + BASE
FALSE = op('u', TRUE)


def definitions():
    source, description = v('source'), v('description')
    args = [v(n) for n in FIELDS_NAMES] + [v('required')]
    requirement = lambda sign: app(v('required'), source, v('person'), v('role'), v('action'), description, sign, v('context'))
    actual = op('t', app('s['+description+']', v('person'), v('action')), v('context'))
    text = definition('rfe', 'source a description '+DESCRIPTION+' '+BASE, both(
        op('y', requirement(TRUE), actual), op('y', requirement(FALSE), op('u', actual))))
    fold = 'q[v descriptions]['+TRUE+'][i[ok c description '+DESCRIPTION+']['+both(v('ok'), k('rfe', source, description, *args))+']]'
    text += definition('rff', SCOPED, quant('f', 'source', 'a', op('y', app(v('sources'), source), fold)))
    text += definition('rfg', BASE, quant('f', 'source', 'a', quant('f', 'description', DESCRIPTION,
        k('rfe', source, description, *args))))
    listed = 'q[v descriptions]['+FALSE+'][i[found c entry '+DESCRIPTION+']['+op('x', v('found'), op('e', v('entry'), description))+']]'
    covered = op('y', op('x', requirement(TRUE), requirement(FALSE)), both(app(v('sources'), source), listed))
    text += definition('rfh', SCOPED, quant('f', 'source', 'a', quant('f', 'description', DESCRIPTION, covered)))
    scoped_args = [v('sources'), v('descriptions'), *args]
    text += definition('rfi', SCOPED, both(k('rfh', *scoped_args), k('rff', *scoped_args)))
    return text


MEANINGS = {
    'rfe': '同じ出所・本人・役割・行為・記述・文脈にある成立要求と不成立要求をそれぞれ検査する。実際の内容が全ての該当要求を満たす条件。要求がなければ真だが、実行許可を意味しない。相反する要求があれば内容の真偽にかかわらず偽。',
    'rff': '指定した出所範囲と記述の有限列の全組合せでrfeを要求する。範囲内での不違反であり、範囲外の要求を否定しない。空範囲や空列なら真。',
    'rfg': '同じ本人・役割・行為・文脈について、全出所・全ての型に合う記述にわたりrfeを要求する。有限の既知の記述だけを全領域として代用しない。',
    'rfh': '同じ本人・役割・行為・文脈への成立要求または不成立要求があれば、その出所と対象記述が指定範囲に含まれることを全称量化する。記述の同一性を保持し、意味の似た別名で代用しない。要求の内容を実行評価しない。',
    'rfi': '要求を取りこぼさないrfhと、範囲内での不違反rffをともに要求する。既知の一覧に違反がないだけでは、全要求に対する不違反とはしない。',
}
LIMITS = [
    '行為を指定した要求への適合であり、本人の別の行為や生活全体の遵守を意味しない。義務の制度的な正当性、責任、故意、能力、制裁、因果的な違反帰属は別である。',
    'rfe・rff・rfg・rfiは内容の脱引用を含むため、そのまま引用内に入れられない。rfhは対象記述を実行評価せず、引用できる。',
    'rfgとrfhは式記述の全領域へ量化する。有限検査器はこれを列挙せず拒否する。既知の記述列は表現上の検討範囲として渡せるが、全域の代用にはしない。',
]


def generic_composed():
    doc = parse('n:' + definitions())
    basis = dict(version='action-conformity-basis-v1', document='examples/v014/action-conformity.noema',
                 primitives=[], definitions=MEANINGS, unresolved=LIMITS)
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def source_composed():
    doc = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT/'data/kant-assessed-payments-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    text = definitions(); args = [v(n) for n in FIELDS_NAMES]
    for name, generic in (('hzam', 'rff'), ('hzao', 'rfi')):
        text += definition(name, FIELDS+' '+SCOPE, k(generic, v('sources'), v('descriptions'), *args, 'p h7a'))
    text += definition('hzan', FIELDS, k('rfg', *args, 'p h7a'))
    all_names = (*PAY_NAMES, 'speech', 'scholar', 'audience', 'channel', 'subject', 'criticism', 'authority')
    actual = k('hzak', *(v(n) for n in all_names))
    conforms = k('hzao', v('person'), v('role'), v('speech'), v('context'), v('sources'), v('descriptions'))
    text += definition('hzap', ALL+' '+SCOPE, both(actual, conforms))
    text += definition('hzaq', ALL+' '+SCOPE, op('y', actual, conforms))
    doc = parse(format_graph(doc, 'compact')+text); doc['statements'] = statements
    basis.update(version='kant-action-conformity-basis-v1', document='examples/v014/kant-action-conformity.noema')
    basis['definitions'].update(MEANINGS | {
        'hzam': '指定した範囲で、同じ本人・役割・行為へのh7aの全要求を満たす。許可の有無や別行為の未履行とは独立。',
        'hzan': 'h7aで同じ本人・役割・行為・文脈へ課される全ての記述上の要求に違反しない。記述全域への量化を保つ。',
        'hzao': '指定した出所と記述列がh7aの該当要求を尽くし、その全要求に違反しない。有限検査の入力一覧が網羅的だとは自動認定しない。',
        'hzap': '納付要求を持つ同じ本人が、学識者として同じ内容の公的発言を行い、その発言に市民側の役割で課される全要求に違反しない。納付行為への未履行とは分ける。',
        'hzaq': 'hzakで指定した同じ本人の公的発言が行われるなら、その発言への市民側の役割での全要求に違反しないという条件文。前件が偽の場合にも成立し、実際の発言や許可の存在を補わない。',
    })
    basis['unresolved'] += LIMITS + [
        'u0012の「市民の義務に反しない」を、同じ発言行為に市民側の役割で課される全要求への適合という操作的な読みへ部分接続する。該当要求の現実への対応、役割の制度的説明、要求間の優先順位や免除、原文の唯一の解釈は未確定。',
        '発言によって別の義務の履行を妨げるなどの因果的な評価は、行為に直接課された要求との適合とは別である。rfiをあらゆる意味の道徳的無過失と同一視しない。',
        '処罰可能性、抵抗を誘発しうるという先行文との対比、demohngeachtetの談話的な譲歩は未完。新しい本文主張は追加せず、既存15件を保持する。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def core_composed():
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=['hzah', 'hzaj', 'hzal', 'hzan', 'hzap', 'hzaq', 'rfd'], statement_indices=[])
    projected = extract_basis(doc, basis, selected, version='action-conformity-core-basis-v1',
        document_path='examples/v014/action-conformity-core.noema')
    return format_graph(selected.document, 'compact')+'\n', projected


BUILDERS = ((generic_composed, 'action-conformity'), (source_composed, 'kant-action-conformity'),
            (core_composed, 'action-conformity-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/'+stem+'-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2)+'\n')):
            path = ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored action conformity differs: '+name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__':
    main()
