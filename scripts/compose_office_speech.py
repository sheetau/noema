"""Bind an entrusted task and a separate public activity to the same person."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, call, both, op, definition

PARENT = 'examples/v014/kant-capacity-changes.noema'
PARAMS = ('person a duty a office a issuer a speech a scholar a audience a channel a '
          'subject a description i[h[a] f] authority a context d')
NAMES = ('person', 'duty', 'office', 'issuer', 'speech', 'scholar', 'audience',
         'channel', 'subject', 'description', 'authority', 'context')
TRUE = 'e[n p a b][n p a b]'


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT / 'data/kant-capacity-changes-basis-v1.json').read_text(encoding='utf-8')))
    roles = basis['role_linkage']['symbols']['roles']
    statements, doc['statements'] = doc['statements'], []
    duty = call('hzn', *(v(n) for n in ('person', 'duty', 'office', 'issuer', 'context')))
    extra = definition('hzn', 'person a duty a office a issuer a context d', both(
        call(roles['cf'], v('person'), v('office'), v('context')),
        call(roles['cb'], v('person'), v('duty'), v('office'), v('context')),
        call('h7a', v('issuer'), v('person'), v('office'), v('duty'),
             'r[p ' + roles['dc'] + ']', TRUE, v('context'))))
    extra += definition('hzo', PARAMS, both(duty,
        op('u', op('e', v('duty'), v('speech'))),
        call('h7c', *(v(n) for n in ('person', 'speech', 'scholar', 'audience', 'channel',
                                   'subject', 'description', 'context', 'authority')))))
    extra += definition('hzp', 'person a duty a office a issuer a context d', both(duty,
        op('u', op('t', call(roles['dc'], v('person'), v('duty')), v('context')))))
    doc = parse(format_graph(doc, 'compact') + extra)
    doc['statements'] = statements
    basis.update(version='kant-office-speech-basis-v1', document='examples/v014/kant-office-speech.noema')
    basis['definitions'].update({
        'hzn': '同じ本人に職務が委ねられ、指定行為がその職務での活動とされ、指定出所から同じ行為の実行が要求される。要求の存在であり、正当性、上官という関係、指示の受領や実行は別である。理性使用の活動だけに限定しない。',
        'hzo': 'hznの職務上の要求と、同じ本人による別行為の公的使用へのh7cの許可が、同じ文脈で併存する。職務と学識者としての活動、要求元と許可元をそれぞれ保持する。活動は異なるが、役割や出所が異なることは強制しない。',
        'hzp': 'hznの職務上の実行要求があり、同じ本人・行為の実行が現在の文脈で不成立である。未履行であり、公的発言の有無、責任、故意、制裁は含まない。',
    })
    basis['unresolved'] += [
        '軍人の例への部分的接続であり、軍人・軍務・上官の概念、指示の発出と受領、命令の合目的性・有用性を職務中に声高に論じる条件とその害は未記述。命令が出た事実から要求の正当性を導かない。',
        'hzoは本人の公的活動への積極的な許可がある状態を表す。原文の「正当に禁じることはできない」という上位の規範・正当性と同一ではない。軍務の欠陥についての注記、その公衆の判断への提出という内容・目的の説明も残る。',
        '職務上の要求はhznで保持するが、相反する要求が存在しないことまでは要求しない。hzoの発言許可は同じ許可元による禁止と衝突しない条件であり、あらゆる出所間の規範衝突を解決しない。',
        'hzoは同じ本人に二つの活動が位置付く条件を保持する。職業があるだけで全発言を職務に帰属させず、二つの行為の真偽が一致するだけで対象を交換しない。実際の二つの行為の実行状態は独立に検査する。',
        '既存15件の本文主張は保存し、この部分的な条件式を完成訳または著者の追加主張として登録しない。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = source_composed()
    for name, body in ((basis['document'], text), ('data/kant-office-speech-basis-v1.json',
            json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored office/speech composition differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Same-person office requirement and separate public permission composed')


if __name__ == '__main__':
    main()
