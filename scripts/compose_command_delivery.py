"""Bind the requested actor/action while separating delivery, receipt and duty."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, call, v, both, op, definition

PARENT = 'examples/v014/kant-public-assessment.noema'
DIRECT = 'issuer a person a notice a action a description i[h[a] f] context d'
FIELDS = ('issuer', 'person', 'notice', 'action', 'description', 'context')
DUTY = 'person a action a office a issuer a notice a description i[h[a] f] context d'
DUTY_FIELDS = ('person', 'action', 'office', 'issuer', 'notice', 'description', 'context')


def definitions():
    return 'd rew[person a execution h[a a] e] h[a] f[i[action a][j m[c[v execution][v person v action]]]].\n'


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'directed-action-basis-v1', 'document': 'examples/v014/directed-action.noema',
        'primitives': [], 'definitions': {'rew': '同じ本人・対象行為について、指定した実行条件を満たすよう求める発話を作る。本人と実行条件を固定し、行為から発話への関数を返す。要求の発話の記述であり、現実の発出、受領、職務上の義務、実行を主張しない。'},
        'unresolved': ['指示の発話を型付きの内容から構成する。社会的な正当性、命令権、慣習上の間接的な言い方、制裁や実現能力は、この発話の働きだけからは導かない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT / 'data/kant-public-assessment-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    extra = definitions() + 'd hzz[person a] h[a] f[k rew[v person p zzq]].\n'
    args = [v(n) for n in FIELDS]
    extra += definition('hzaa', DIRECT, call('rdb', *args, 'p dg', 'p f3', 'p f2'))
    extra += definition('hzab', DIRECT, call('rdc', *args, 'p dg', 'p f3', 'p f2', 'p h6e'))
    extra += definition('hzac', DUTY, both(
        call('hzn', *(v(n) for n in ('person', 'action', 'office', 'issuer', 'context'))), call('hzaa', *args)))
    extra += definition('hzad', DUTY, both(call('hzac', *(v(n) for n in DUTY_FIELDS)),
        op('u', op('t', call('zzq', v('person'), v('action')), v('context')))))
    doc = parse(format_graph(doc, 'compact') + extra)
    doc['statements'] = statements
    basis.update(version='kant-command-delivery-basis-v1', document='examples/v014/kant-command-delivery.noema')
    basis['definitions'].update(generic_composed()[1]['definitions'])
    basis['definitions'].update({
        'hzz': 'rewの実行条件を既存zzqへ固定し、指定本人に対象行為の実行を求める発話を作る関数を返す。同じ本人を閉じた式で渡した引用を提示の記述として使う。',
        'hzaa': '実際に生起する同じ提示行為で、指定発出者が、その本人へ、同じ対象行為について指定発話を示す。hzzを使う作例では命令内容を構成するが、任意の発話記述を渡した呼出まで命令とは扱わない。受領は別。',
        'hzab': 'hzaaの提示があり、同じ提示行為・本人・対象行為・発話記述・状況で、その本人が受け取っている。理解・同意・義務・実行は要求しない。',
        'hzac': 'hzaaの提示と、同じ本人・対象行為・出所について職務上の実行要求hznが成立する。提示から義務を導く規則ではなく、別の二条件を対応させる。受領を必須にしない。',
        'hzad': 'hzacが成立し、同じ本人による同じ対象行為は現在実行されていない。未履行であり、命令を知っていたこと、故意、責任、制裁を推定しない。',
    })
    basis['unresolved'] += generic_composed()[1]['unresolved'] + [
        '原文のanbefohlen wirdへの部分的接続では、発出・提示と受領を区別する。受け取ったという条件を原文へ自動追加しない。明示的な受領を必要とする別の文にもhzabを使える。',
        'hzzの本人を、提示の受け手と職務要求の本人へ対応させ、対象行為を発話の引数と規範対象に共通して渡す。任意の発話記述が自動的にこの構成へ一致するわけではなく、作例で式を明示的に固定する。',
        '元の軍人の例について、上官という役割関係、軍務の概念、命令の有用性・合目的性を職務中に論じることの害は未記述。発出者が正当な権限を持つことは発話の発出だけから導かない。',
        '提示と受領は同じ粗い文脈で扱う。実行要求の期限、伝達の遅延、発出後に撤回・変更された命令、異なる時点の履行は今回接続しない。',
        '既存15件の本文主張を保持し、原文の実際の出来事や追加の著者主張を補わない。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def core_composed():
    text, basis = source_composed()
    doc = parse(text)
    extracted = extract_document(doc, roots=['hzz', 'hzaa', 'hzab', 'hzac', 'hzad'], statement_indices=[])
    projected = extract_basis(doc, basis, extracted, version='command-delivery-core-basis-v1',
        document_path='examples/v014/command-delivery-core.noema')
    return format_graph(extracted.document, 'compact') + '\n', projected


def main():
    for builder, stem in ((generic_composed, 'directed-action'), (source_composed, 'kant-command-delivery'),
                          (core_composed, 'command-delivery-core')):
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored command delivery differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__':
    main()
