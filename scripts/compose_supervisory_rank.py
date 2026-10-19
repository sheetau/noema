"""Describe highest supervisory position without inventing a lower tier."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-guardian-purpose.noema'
PARENT_BASIS = 'data/guardian-purpose-basis-v1.json'
FULL = 'examples/v016/kant-supervisory-rank.noema'
CORE = 'examples/v016/supervisory-rank-core.noema'
LIBRARY = 'examples/v016/greatest-preorder.noema'
BASIS = 'data/supervisory-rank-basis-v1.json'
ANNOTATIONS = 'data/supervisory-rank-identifiers-v1.json'
PRIMITIVES = {
    'hzxn': (['first', 'second', 'target', 'context'], '同じ対象について同じ状況で実際に監督の立場を持つ二主体の比較において、第一主体の監督上の位置が第二主体以上である。両方向の成立は同順位を許し、両方向の不成立は比較不能として扱う。本人の価値・能力・合法性を比較せず、別対象での上下を流用しない。比較範囲上の反射性と推移性はrqyiで検査する。'),
    'hzxo': (['act', 'actor', 'target', 'position_description', 'context'], 'この行為によって、この主体が同じ対象について記述された立場・責務を実際に引き受ける。記述は主体と対象から内容への閉じた関数であり、二位置をその順に適用する意味規約を持つ。自己申告だけ、無関係な地位の取得、単なる結果の共存とは分ける。任命儀礼・正当な権利・自発的な発意は含めない。'),
}
MEANINGS = {
    'rqyi': '指定範囲内にある候補が、範囲上で反射的かつ推移的な弱い比較において、全ての範囲内対象以上である。単に上位が見つからない極大とは分ける。同順位の複数の最高位、候補一つだけの範囲を許し、下位者の存在や比較範囲全体の全比較可能性は要求しない。',
    'rqyj': '同じ対象・状況に監督の立場dcを持つ全主体の範囲で、指定主体がhzxnの比較による最高位rqyiにあるという内容。中間の監督者や下位者を補わず、全対象を通じた世界唯一の最高者とも解さない。',
    'rqyk': '前版diを保存する。異なる人間である主体と対象について、現在の総括的監督dcと、それより前の同じ引受け行為de・dvを要求する。監督の最高位や、その特定の立場を引き受けたという記述の結合は要求しない。',
    'di': '異なる人間である主体と対象について、現在は最高位の監督rqyjにあり、現在とは異なる先行状況で同じ主体が同じ対象への監督を実際に引き受けた一つの行為がある。その同じ行為はrqyjとして記述された立場の引受けhzxoでもあり、同じ引受け状況でもrqyjが実際に成立する。現在だけ最高位になった場合と、別行為で別の立場を引き受けた場合を混ぜない。二時点の間の連続保持、正当性、自発的発意は別である。',
}


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not ({'rqyi', 'rqyj', 'rqyk'} | set(PRIMITIVES)) & set(old.entries)
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'di')
    prefix = deepcopy(doc); prefix.update(declarations=doc['declarations'][:at], statements=[])
    saved = deepcopy(old.entries['di']['declaration']); saved['name'] = 'rqyk'; prefix['declarations'].append(saved)
    text = '''
r hzxn[a a a d] c.r hzxo[a a a i[h[a a] e] d] c.
d rqyi[candidate a scope h[a] c order h[a a] c] c[
 w[c[v scope][v candidate]][w[
 f first a[y[c[v scope][v first]][c[v order][v first v first]]]
 ][w[
 f first a[f second a[f third a[y[w[c[v scope][v first]][w[c[v scope][v second]][c[v scope][v third]]]][
 y[w[c[v order][v first v second]][c[v order][v second v third]]][c[v order][v first v third]]
 ]]]]
 ][f other a[y[c[v scope][v other]][c[v order][v candidate v other]]]]]]
].
d rqyj[actor a target a] e[b scene[k rqyi[v actor
 i[other a][k dc[v other v target v scene]]
 i[first a second a][k hzxn[v first v second v target v scene]]
]]].
d di[actor a target a] e[b scene[w[k aa[v actor]][w[k aa[v target]][w[u[e[v actor][v target]]][
 w[t[k rqyj[v actor v target]][v scene]][g prior d[w[u[e[v prior][v scene]]][w[k dd[v prior v scene]][
 g act a[w[k de[v actor v act v prior]][w[k dv[v act v actor v target v prior]][
 w[k hzxo[v act v actor v target r[p rqyj] v prior]][t[k rqyj[v actor v target]][v prior]]
 ]]]]]]
 ]]]]]].
'''
    parsed = parse(format_graph(prefix, 'compact') + text)
    doc['declarations'] = parsed['declarations'] + doc['declarations'][at+1:]
    doc = parse(format_graph(doc, 'compact'))
    basis = dict(status='highest_scoped_supervision_and_same_position_assumption', document=FULL,
        revises_document=PARENT, revises_meaning_basis=PARENT_BASIS, primitives={}, definitions={},
        predecessor_source_sha256=old.source_sha256,
        limitations=['Oberaufsichtを同じ対象について最高位にある監督と読む。唯一の監督者、中間担当者、下位者の存在を補わない。',
            '監督dcの実践的内容と順位hzxnの根拠は解釈に残る。現実の制度や資格の正当性を認定しない。',
            '特定の立場の引受けhzxoを一般化した基本関係として明示する。その心理・制度的な成立機構の説明は未完。',
            '集団目的の読み、gütigst・schon・auchと当該文全体の意味確認は未完。'],
        unresolved=[dict(basis=r['basis'], historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'primitive':
            args, meaning = PRIMITIVES[n] if n in PRIMITIVES else (old.entries[n]['arguments'], old.entries[n]['meaning_ja'])
            basis['primitives'][n] = dict(parameters=d['parameters'], result=d['result'], arguments=args, meaning_ja=meaning)
        else: basis['definitions'][n] = MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    core = deepcopy(doc); core['statements'] = [doc['statements'][7]]
    core['declarations'] = closure(doc, _references(core['statements']))
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['rqyi']), statements=[])
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/guardian-purpose-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(lib, 'compact') + '\n', BASIS: enc(basis), ANNOTATIONS: enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for p, s in build().items(): write_exact(ROOT / p, s)
    print('Scoped highest supervision and its assumption composed', flush=True)


if __name__ == '__main__': main()
