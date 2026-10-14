"""Keep alternative attributions distinct from attributing a disjunctive content."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_situated_criticism import params, args
from scripts.compose_bound_revision import ROOTS as POLICY_ROOTS
from scripts.compose_policy_norms import TRUE

PARENT = 'examples/v014/kant-bound-revision.noema'
CLAIMS = 'h[a a i[e] d] c'
CHOICES = [('node', 'a'), ('author', 'a'), ('candidates', 'j[i[e]]'), ('context', 'd'), ('claims', CLAIMS)]
CHOSEN = CHOICES + [('selected', 'i[e]')]
SOURCE = [(n, t) for n, t in CHOICES if n != 'claims']
SOURCE_CHOSEN = SOURCE + [('selected', 'i[e]')]
ROOTS = ['rj4', 'rj5', 'rj6']


def definitions():
    claim = app(v('claims'), v('node'), v('author'), v('candidate'), v('context'))
    nonempty = op('u', op('e', 'd[v candidates]', 'n p a b'))
    text = ''
    for name, connective, initial in (('rj4', 'x', op('u', TRUE)), ('rj5', 'w', TRUE)):
        folded = 'q[v candidates][' + initial + '][i[state c candidate i[e]][' + op(connective, v('state'), claim) + ']]'
        text += definition(name, params(CHOICES), both(nonempty, folded))
    member = 'q[v candidates][' + op('u', TRUE) + '][i[state c candidate i[e]][' + op('x', v('state'), op('e', v('candidate'), v('selected'))) + ']]'
    text += definition('rj6', params(CHOSEN), both(member, app(v('claims'), v('node'), v('author'), v('selected'), v('context'))))
    return text


MEANINGS = {
    'rj4': '明示した非空の内容記述の候補列のうち、少なくとも一つについて同じ箇所・著者・文脈への主張帰属が成立する。どれか一つの候補を勝手に採用せず、内容内部の選言を主張したこととも区別する。候補が全ての可能な解釈を尽くすとはしない。',
    'rj5': '明示した非空の候補列の全てについて、同じ箇所・著者・文脈への主張帰属が成立する。rj4の帰属候補から各候補への賛同を導かず、空列を全候補の帰属成功にしない。',
    'rj6': '明示的に選んだ内容記述が候補列に含まれ、その同じ記述について同じ箇所・著者・文脈への主張帰属が成立する。単なる列の成員であることを帰属の根拠にしない。同値な別記述への自動移送もしない。',
    'hzdy': 'rj4を既存ucの著者主張の帰属関係へ接続する。複数の読解に対応する帰属の選択肢を表せるが、どの読解が原文と一致するかを自動判定しない。',
    'hzdz': 'rj5を既存ucへ接続する。候補全ての著者帰属という強い条件であり、候補が複数あるだけでは成立しない。',
    'hzd2': 'rj6を既存ucへ接続する。採用した記述を候補と照合した上で、同じ著者主張の帰属を要求する。内容の真理・制度的妥当性・実行・達成は認定しない。',
}
LIMITS = [
    'これらは帰属に関する命題であり、読解候補を生成・順位付けする翻訳器ではない。候補と採用する記述は人が明示する。未知の帰属関係を偽へ補わない。',
    '候補列には順序と重複があるが、今回の論理条件は重複の件数を信頼度や多数決へ変えない。別名の記述は同じ内容値であっても別候補である。',
    '少なくとも一つの候補に帰属するという条件は、それぞれの候補への帰属とも、候補内容を選言で結んだ一つの内容への帰属とも異なる。有限候補の外の解釈を排除する条件は追加しない。',
    '原文への接続例は、既存の改善不能の目的全体を含む政策への禁止と許可欠如を別の内容記述として渡す。原文の唯一の読みを確定したり、二つとも著者が断言したという主張を追加したりしない。',
    '原文における主張の同定と記述の適合は解釈上の証拠を必要とする。今回の有限モデルは帰属条件の区別を検査するもので、原文の歴史的解釈や内容の真理を証明しない。',
    '権能の欠如を含めた他の読解、代表資格、規範の根拠、知識・因果の基礎概念、啓蒙全体の進展と原文全体の帰属確定は残る。既存の著者・文脈の局所参照を別段落へ無断で転用しない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()
    for name, target, fields, generic in (('hzdy', 'rj4', SOURCE, CHOICES), ('hzdz', 'rj5', SOURCE, CHOICES), ('hzd2', 'rj6', SOURCE_CHOSEN, CHOSEN)):
        text += definition(name, params(fields), k(target, *args(generic, claims='p uc')))
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-bound-revision-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-attribution-choices-basis-v1', document='examples/v014/kant-attribution-choices.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'attribution-choices')
def core_composed(): return projected(ROOTS + ['hzdy', 'hzdz', 'hzd2'] + POLICY_ROOTS, 'attribution-choices-core')
BUILDERS = ((generic_composed, 'attribution-choices'), (source_composed, 'kant-attribution-choices'), (core_composed, 'attribution-choices-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored attribution choices differ: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
