"""Exact finite scope enumeration and context-dependent upper counts."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT
from scripts.compose_proportions import generic_composed as proportions

PARENT = 'examples/v014/kant-referenced-kinds.noema'


def definitions():
    return '''
d rcm[population j[a] scope h[a] c] c[
 w[k he[]][w[k hi[v population v scope]][w[k hc[n p a b d[v population]]][
  f person a[z[c[v scope][v person]][k hg[v population v person]]]
 ]]]
].
d rcn[population j[a] scope h[a] c property h[a] c upper b] c[
 w[k rcm[v population v scope]][w[k hc[n p a b v upper]][k hc[k hf[v population v property] v upper]]]
].
d rco[population j[a] scope h[a] c property h[a] c upper b] c[
 w[k rcn[v population v scope v property v upper]][k hc[n p a b k hf[v population v property]]]
].
'''


def generic_composed():
    text, basis = proportions()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='scoped-counts-basis-v1', document='examples/v014/scoped-counts.noema')
    basis['definitions'].update({
        'rcm': '指示関数の規約を満たし、列が非空・重複なしで、指定範囲に属する個体の全てを過不足なく列挙する。適格な個体だけを含むhiに、範囲全体との同値を加える。',
        'rcn': 'rcmの全列挙について、指定性質を持つ人数が、与えた正の上限より厳密に少ない。該当者0人も許す。上限と等しい人数は許さない。',
        'rco': 'rcnに加え、指定性質を持つ人が少なくとも一人いる。全対象が0人の場合と、非空の対象のうち該当者が0人の場合を区別する。'})
    basis['unresolved'] += [
        '完全性は指定範囲との一致である。その範囲が現実の評価対象を過不足なく表すか、有限モデルが現実の全個体を含むかは別途確認する。標本から未知の人々を推定する統計ではない。',
        '上限は正の有理数で与えるが、数える人数は通常の指示関数と加算の規約の下で非負整数になる。上限を固定した言葉の辞書や、少ないという語の普遍的な閾値ではない。',
        '人数の上限と、母集団内の比率の上限は別の指定である。上限を母集団の半数に固定せず、母集団が小さいときは全員でも絶対人数として少ない評価を許す。',
        '性質の真偽と範囲の所属は完全な解釈として与える。未知の性質を偽にして人数を少なくすることは認めない。無限の対象範囲は有限列で完全に列挙できない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = '''r h4h[b d] b.r h4i[a d] c.
d h4j[population j[a] property h[a] e context d] c[
 k rcn[v population i[person a][w[k aa[v person]][k h4i[v person v context]]]
  i[person a][t[c[v property][v person]][v context]] k h4h[d[v population] v context]]
].
d h4k[population j[a] property h[a] e context d] c[
 k rco[v population i[person a][w[k aa[v person]][k h4i[v person v context]]]
  i[person a][t[c[v property][v person]][v context]] k h4h[d[v population] v context]]
].
'''
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-referenced-kinds-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-scoped-counts-basis-v1', document='examples/v014/kant-scoped-counts.noema')
    generic = generic_composed()[1]
    basis['definitions'].update({name: generic['definitions'][name] for name in ('rcm', 'rcn', 'rco')})
    decls = {d['name']: d for d in doc['declarations']}
    for name, arguments, meaning in (
        ('h4h', ['population_size', 'context'], 'この母集団の全人数と基準文脈で、少ないという数量評価に採る正の上限候補。原文の具体的な数値とはしない。総人数への依存を明示し、絶対人数基準や比率から得た人数基準を区別して設定できる。上限の適切さは別の解釈上の前提。'),
        ('h4i', ['person', 'context'], 'この基準文脈で、段落末の少数者を数える対象範囲に入る個体。人であることはaaで別に要求し、成功者だけを選んだ標本や、仮定ごとに入れ替わる対象集合とはしない。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
            'arguments': arguments, 'meaning_ja': meaning})
    basis['definitions'].update({
        'h4j': 'この文脈の対象となる人を全て重複なく列挙し、指定した性質を同じ文脈で満たす人数がh4hの上限より少ない。ゼロ人を許す上限条件の候補。性質はまだ引数として保持する。',
        'h4k': 'h4jの人数が少なくとも一人でもあるという、存在を伴う少数者の候補。原文の最終的な存在含意の読みを、この候補だけで確定しない。'})
    basis['unresolved'] += generic['unresolved'][-4:] + [
        'nur Wenigeの数量部分の二つの候補であり、原文の具体的な人数・閾値・存在含意を確定しない。nurの期待との対比・焦点、Daherの推論は未記述。',
        '成功した自立・自分の精神への働きかけ・確かな歩みを性質引数へ接続する作業は残る。この数量候補を新しい本文主張としては実行しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'scoped-counts'), (source_composed, 'kant-scoped-counts')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored scoped counts differ')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Complete finite scopes and distinct zero-permitting/existential upper counts composed')


if __name__ == '__main__':
    main()
