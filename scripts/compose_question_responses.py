"""Keep question framing, answer polarity and textual attribution separate."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_situated_criticism import params, args
from scripts.compose_policy_norms import DESCRIPTION, TRUE

PARENT = 'examples/v014/kant-produced-contents.noema'
SIGNED = [('proposition', 'e'), ('polarity', 'c')]
PAIR = [('first', 'a'), ('second', 'a'), ('author', 'a'), ('context', 'd'),
    ('question', 'i[f]'), ('answer', 'i[e]'), ('asks', 'h[a a i[f] d] c'),
    ('asserts', 'h[a a i[e] d] c'), ('before', 'h[a a d] c'), ('responds', 'h[a a a d] c')]
SOURCE_PAIR = PAIR[:6]
NORM = [('assessor', 'a'), ('holder', 'a'), ('role', 'a'), ('target', DESCRIPTION),
    ('bindings', 'j[a]'), ('valid', 'h[j[a]] c')]
ROOTS = ['rii', 'rij', 'rik', 'ril']


def definitions():
    text = definition('rii', params(SIGNED), 'b scene[' + op('z', op('t', v('proposition'), v('scene')), v('polarity')) + ']', 'e')
    for name, force in (('rij', 'q'), ('rik', 's')):
        text += definition(name, params(SIGNED), 'j ' + force + '[' + k('rii', *args(SIGNED)) + ']', 'f')
    return text + definition('ril', params(PAIR), both(op('u', op('e', v('first'), v('second'))),
        app(v('asks'), v('first'), v('author'), v('question'), v('context')),
        app(v('asserts'), v('second'), v('author'), v('answer'), v('context')),
        app(v('before'), v('first'), v('second'), v('context')),
        app(v('responds'), v('author'), v('first'), v('second'), v('context'))))


MEANINGS = {
    'rii': '命題内容と極性から内容を作る。正極性なら元の内容、負極性ならその否定。質問の文法上の極性と回答の極性には独立に適用する。',
    'rij': 'riiの内容を問う極性質問の発話。否定形の質問を肯定形に消去せず、問いかけと断言を区別する。修辞的な期待や驚きは別に指定する必要がある。',
    'rik': 'riiの内容を主張する発話。質問rijと同じ真偽内容であっても発話の働きは異なる。',
    'ril': '異なる二つの本文箇所で同じ著者が問いと主張を提示し、問いが本文上で先行し、後者を前者への回答として提示する。二つの記述の内容が一致する条件はこの一般関係だけには含めない。',
}
LIMITS = [
    '極性は元の命題に対して指定する。否定疑問に対する元の命題の否認では、質問・回答の双方が負極性となり得る。否定疑問全体をさらに否定して肯定に変える規則はない。',
    'rilは談話関係であり、回答の正しさや命題の真理を要求しない。同じ命題への応答であることは、具体的な閉じた適用記述を同じ命題から構成して検査する。無関係な二つの記述を渡す誤用を型だけでは排除しない。',
    'Noemaの引用は式を実行しない。同じ意味や真理値を持つ別名の記述を自動的に同一視しない。質問の修辞的な含意、否定質問への自然言語のはい・いいえの使い分けはこの定義の外にある。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = definitions() + 'r hzcr[a a i[f] d] c.r hzcs[a a a d] c.'
    norm = k('rdu', v('assessor'), v('holder'), v('role'), v('target'), v('bindings'), TRUE,
        v('scene'), v('valid'), 'p h7k', 'p h7l')
    extra += definition('hzct', params(NORM), 'b scene[' + norm + ']', 'e')
    extra += definition('hzcu', params(SOURCE_PAIR), k('ril', *args(PAIR,
        asks='p hzcr', asserts='p uc', before='p ue', responds='p hzcs')))
    doc = parse(format_graph(doc, 'compact') + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-produced-contents-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-question-responses-basis-v1', document='examples/v014/kant-question-responses.noema')
    for name, names, meaning in (
        ('hzcr', ['node', 'author', 'message_description', 'context'], '著者が指定箇所で、指定した発話記述を質問として提示する。単なる他者の発話の引用ubとは区別する。質問内容の肯定・否定への賛同は含まない。'),
        ('hzcs', ['author', 'question_node', 'response_node', 'context'], '著者が第二の本文箇所を第三の本文箇所で回答するという談話関係。本文で後にあるだけでは成立せず、内容の真理や回答の十分性は含まない。')):
        row = next(d for d in doc['declarations'] if d['name'] == name)
        basis['primitives'].append(dict(symbol=name, parameters=row['parameters'], result=row['result'], arguments=names, meaning_ja=meaning))
    basis['definitions'].update(MEANINGS | {
        'hzct': '指定した評価側の規範において、名宛人がその立場で指定の内容を実現することに、反対要求と衝突しない積極的許可rduがあるという内容。対象記述・引数列・列の適合条件を固定し、現実の実行や成功を主張しない。',
        'hzcu': 'rilを、質問の提示hzcr、著者による内容の主張uc、本文順序ue、回答関係hzcsへ接続する。質問と回答を同じ命題から作った閉じた記述で与えられる。'})
    basis['unresolved'] += LIMITS + [
        'u0013の否定疑問とそれに続く否定判断への部分的な解釈注記。berechtigt seinをhzctの許可として読む候補であり、制度的な権能・正当性・資格の意味全体を確定したものではない。',
        'das ist ganz unmöglichの否定先を資格に取る候補。物理的に永続化できないという命題や、目的内容の否定へ自動変換しない。ganzの程度・強調、sollte nichtの期待・反語、宣誓・組織の特定は残る。',
        '新しい本文主張は追加しない。共通命題を持つ具体例は検査用の閉じた適用記述であり、原文の契約・組織・役割を全て特定した著者帰属の完成形ではない。質問提示と回答関係は意味規約を持つ入力であり、原始関係を増やしただけで説明を完了したとはしない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed()
    doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'question-responses')
def core_composed(): return projected(ROOTS + ['hzct', 'hzcu'], 'question-responses-core')
BUILDERS = ((generic_composed, 'question-responses'), (source_composed, 'kant-question-responses'), (core_composed, 'question-responses-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored question response differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
