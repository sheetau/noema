"""Reuse scientific scoped necessity for nonvacuous conditional future outcomes."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_blocked_revision import SOURCE as REVISION

PARENT = 'examples/v014/kant-successive-cohorts.noema'
MODAL_PARENT = 'examples/v014/derivation-modalities.noema'
MODAL_BASIS = 'data/derivation-modalities-basis-v1.json'
CONDITION = [('subject', 'e'), ('condition', 'e'), ('context', 'd'), ('candidates', 'h[d d] c')]
APPLICABLE = [(n, t) for n, t in CONDITION if n != 'subject']
FUTURE = [('subject', 'e'), ('context', 'd'), ('continuations', 'h[d d d] c')]
SOURCE = REVISION + [('later', 'a'), ('periods', 'h[a d] c'), ('condition', 'e'),
    ('candidates', 'h[d d] c'), ('continuations', 'h[d d d] c')]
ROOTS = ['s5k', 'rjk', 'rjl', 'rjm', 'rjn', 'rjo']
SOURCE_ROOTS = ['hzdh', 'hzdi', 'hzdj', 'hzdf', 'hzcq', 'rin']


def definitions():
    selected = app(v('candidates'), v('context'), v('branch'))
    applicable = both(selected, op('t', v('condition'), v('branch')))
    implication = 'b branch[' + op('y', op('t', v('condition'), v('branch')), op('t', v('subject'), v('branch'))) + ']'
    adapter = 'i[content e anchor d branch d][' + app(v('candidates'), v('anchor'), v('branch')) + ']'
    text = definition('rjk', params(CONDITION), k('s5k', implication, v('context'), adapter))
    text += definition('rjl', params(APPLICABLE), quant('g', 'branch', 'd', applicable))
    text += definition('rjm', params(CONDITION), both(k('rjk', *args(CONDITION)), k('rjl', *args(APPLICABLE))))
    endpoint = app(v('continuations'), v('context'), v('branch'), v('point'))
    truth = op('t', v('subject'), v('point'))
    text += definition('rjn', params(FUTURE), 'b branch[' + quant('g', 'point', 'd', both(endpoint, truth)) + ']', 'e')
    persistent = both(quant('g', 'point', 'd', endpoint), quant('f', 'point', 'd', op('y', endpoint, truth)))
    text += definition('rjo', params(FUTURE), 'b branch[' + persistent + ']', 'e')
    return text


MEANINGS = {
    'rjk': '指定文脈の候補が空でなく、全候補で同じ前件が成立すれば同じ後件も成立する。既存s5kへ条件内容を渡す。前件の実例がない場合の条件成立を許す。',
    'rjl': '指定文脈の候補に、同じ前件が成立するものが少なくとも一つある。後件の成立、現実の前件の成立、規範的な許可は含まない。',
    'rjm': 'rjkの全候補にわたる条件とrjlの適用例の存在を併記する。空候補や前件の実例がない場合を、実例を伴う必然性として認定しない。',
    'rjn': '同じ基準文脈から、その候補に属すると指定した将来の状況の少なくとも一つで対象内容が成立するという候補の性質。別候補の将来を流用しない。',
    'rjo': '同じ基準文脈・候補の将来が空でなく、その全状況で対象内容が成立するという候補の性質。一度の成立と、選択将来全体での成立を分ける。',
    'hzdh': '同じ後続集団を主体とするhzddの改善不能について、指定した後続時代内かつ基準状況より後の継続点にrjnで結び、rjmの条件付き必然性を述べる内容。各適用候補で少なくとも一つの将来点があるという強さ。',
    'hzdi': 'hzdhと同じ設定でrjoを使い、各適用候補の選択された将来全体で改善不能となるという強い内容。原文の唯一の読みや永久性とはしない。',
    'hzdj': 'hzdhのrjmをrjkへ替え、前件の適用例の存在を断定しない条件付き内容を作る。存在を補わない読みと、存在を要求するhzdhを区別して保持する。',
}
LIMITS = [
    's5kは理系の導出様相で使った既存の定義を構文木ごと再利用する。内容・文脈・候補を引数で渡す構造であり、数学的な群やカント固有の語を組み込まない。',
    'candidatesは基準文脈から比較する候補、conditionはその候補を条件に合うものとして扱う内容。選定根拠・網羅性・到達可能性は解釈の前提で、後件が真となる候補だけを選んで必然性を立証したとはしない。',
    'continuationsは基準文脈・候補・その将来点を結ぶ。別候補の結果を混ぜず、原文側では後続時代の範囲と既存icの先後も要求する。候補の履歴全体や現実の経過の一意性を定義し終えたものではない。',
    '現在の真理、実際に起きる将来、条件に適合しない候補での結果、義務や許可は全候補での条件成立と別である。外部でrjlを確認しただけで現実の前件を真にしない。',
    '各候補にいずれかの成立点があることは、全候補で同じ一つの成立点があることを要求しない。また、候補の全ての将来点で成立することや無限時間の持続とは異なる。',
    'hzddの改善不能は指定した方法・結果・知識の比較範囲に相対的である。未知の前件・候補・継続・知識関係を空や偽で補わない。',
    'mussの一つの操作的な読みを追加する。時代区分や因果過程・制度がどの候補を許すか、原文の唯一の歴史的解釈、kann nichtの規範的否認、共謀的含意、著者の帰属は未完。新しい著者主張・原始記号は追加しない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    modal = parse((ROOT / MODAL_PARENT).read_text(encoding='utf-8'))
    shared = next(d for d in modal['declarations'] if d['name'] == 's5k')
    assert not any(d['name'] == 's5k' for d in doc['declarations'])
    doc['declarations'].append(deepcopy(shared))
    text = definitions()
    continuations = 'i[anchor d branch d point d][' + both(app(v('continuations'), v('anchor'), v('branch'), v('point')),
        app(v('periods'), v('later'), v('point')), k('ic', v('anchor'), v('point'), v('anchor'))) + ']'
    for name, future, condition in (('hzdh', 'rjn', 'rjm'), ('hzdi', 'rjo', 'rjm'), ('hzdj', 'rjn', 'rjk')):
        subject = k(future, k('hzdd', *args(REVISION)), v('context'), continuations)
        body = k(condition, *args(CONDITION, subject=subject))
        text += definition(name, params(SOURCE), 'b context[' + body + ']', 'e')
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-successive-cohorts-basis-v1.json').read_text(encoding='utf-8')))
    modal_basis = json.loads((ROOT / MODAL_BASIS).read_text(encoding='utf-8'))
    basis.update(version='kant-necessary-futures-basis-v1', document='examples/v014/kant-necessary-futures.noema')
    basis['definitions'].update(MEANINGS | {'s5k': modal_basis['definitions']['s5k']}); basis['unresolved'] += LIMITS
    audit_basis(doc, basis); return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'necessary-futures')
def core_composed(): return projected(ROOTS + SOURCE_ROOTS, 'necessary-futures-core')
BUILDERS = ((generic_composed, 'necessary-futures'), (source_composed, 'kant-necessary-futures'), (core_composed, 'necessary-futures-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored necessary future differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
