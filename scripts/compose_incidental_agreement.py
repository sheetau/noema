"""Replace the opaque chance predicate with a contextual outcome construction."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.semantic_reviews import digest
from noema.meaning_catalog import load_catalog
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-designation-order.noema'
PARENT_BASIS = 'data/designation-order-basis-v1.json'
FULL = 'examples/v016/kant-incidental-agreement.noema'
CORE = 'examples/v016/incidental-agreement-core.noema'
LIBRARY = 'examples/v016/contingent-outcome.noema'
BASIS = 'data/incidental-agreement-basis-v1.json'
ANNOTATIONS = 'data/incidental-agreement-identifiers-v1.json'
PRIMITIVES = {
    'hzwi': (['process', 'actor', 'activity', 'context'], '指定過程の構成部分として、その人物がその行為の計画・遂行を担う。文脈と過程を固定し、別過程の計画や単なる傍観者を混ぜない。該当行為の範囲は結果を見て都合よく除外しない。自然過程のように該当人物がいない場合もある。'),
    'hzwj': (['process', 'anchor', 'alternative'], '当該過程について文脈で採る説明上の条件を保つ比較状況。結果を固定する条件は、結果を必然扱いする根拠がある場合にだけ含める。実際の全微視的履歴や全物理法則を固定する意味ではなく、無知や主観的驚きだけでも選ばない。比較範囲は一致を調べる前に固定し、基準状況自身を含む。具体的な条件の選択は解釈の責任であり、この関係から全宇宙の非決定性を主張しない。'),
}
MEANINGS = {
    'rqw6': '同じ基準状況で結果が成立し、その基準状況自身を含む比較範囲に、結果が成立しない状況がある。結果の成立と比較条件に対する非必然性を分ける。空範囲、単なる未評価、驚きの強さや低確率では代用しない。',
    'rqw7': '同じ過程の構成行為を担う全人物について、その行為で指定記述と同じ順序の引数が表す結果を目標にしていない。別過程・別行為の目標は流用しない。目標内容を実行せず、目標への未知の評価を否定に変えない。該当する構成行為がなければこの条件だけは満たす。',
    'hzwk': 'ちょうど三個の順序付き引数を第一文献・第二文献・一致範囲として受け、同じ状況での既存hzkvによる内容対応を返す。長さの違いを黙って切り捨てない。原文にない確率や尺度を加えない。',
    'hzwl': '同じ二文献と範囲の一致について、過程ごとの説明上の比較条件ではその一致が必然でなく、その過程の構成行為ではその一致を目的にしていない。共通の問題や背景原因を排除せず、思想の真実性や一致一般への驚きを要求しない。意図の対象は引用の字面でなく同じ引数を適用した目標内容である。',
    'hzlc': '現在の論説と先の回答の指定範囲の一致に寄与する同じ生起過程があり、その結果がhzwlの文脈的に非必然・非目的的な成立条件を満たす。Zufallをこの著者注における計画された一致でない符合として具体化する読み。偶然一般の唯一の定義ではない。現実の一致は主張せず、hzldの可能な状況内の条件となる。',
}


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def additions():
    return '''
r hzwi[a a a d] c.
r hzwj[a d d] c.
d rqw6[outcome e anchor d alternatives h[d d] c] c[
 w[t[v outcome][v anchor]][w[c[v alternatives][v anchor v anchor]][
  g other d[w[c[v alternatives][v anchor v other]][u[t[v outcome][v other]]]]
 ]]
].
d rqw7[process a goal i[h[j[a]] e] bindings j[a] anchor d component h[a a a d] c aims h[a a i[h[j[a]] e] j[a] d] c] c[
 f actor a[f activity a[y[c[v component][v process v actor v activity v anchor]][
  u[c[v aims][v actor v activity v goal v bindings v anchor]]
 ]]]
].
d hzwk[bindings j[a]] e[b scene[
 w[e[d[v bindings]][n p d b]][g first a[g second a[g extent a[
  w[a[v bindings][n p a b][v first]][w[a[v bindings][n p b b][v second]][
   w[a[v bindings][n p c b][v extent]][k hzkv[v first v second v extent v scene]]
  ]]
 ]]]]
]].
d hzwl[process a first a second a extent a scene d] c[
 w[k rqw6[k hzwk[l[a][v first v second v extent]] v scene
  i[anchor d other d][k hzwj[v process v anchor v other]]
 ]][k rqw7[v process r[p hzwk] l[a][v first v second v extent] v scene p hzwi p hztl]]
].
d hzlc[extent a context d] c[g process a[
 w[k dg[v process v context]][w[k hzkx[v process k hzik[] k hzjn[] v extent v context]][
  k hzwl[v process k hzik[] k hzjn[] v extent v context]
 ]]
]].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    assert not ((set(PRIMITIVES) | set(MEANINGS)) - {'hzlc'}) & set(old.entries)
    # Insert before hzlc, moving only the existing primitive needed there.
    aims = next(d for d in doc['declarations'] if d['name'] == 'hztl')
    doc['declarations'].remove(aims)
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'hzlc')
    prefix = deepcopy(doc)
    prefix.update(declarations=doc['declarations'][:at] + [aims], statements=[])
    parsed = parse(format_graph(prefix, 'compact') + additions())
    doc['declarations'] = parsed['declarations'] + doc['declarations'][at + 1:]
    doc = parse(format_graph(doc, 'compact'))
    primitives, definitions = {}, {}
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'primitive':
            args, meaning = PRIMITIVES[n] if n in PRIMITIVES else (old.entries[n]['arguments'], old.entries[n]['meaning_ja'])
            primitives[n] = dict(parameters=d['parameters'], result=d['result'], arguments=args, meaning_ja=meaning)
        else:
            definitions[n] = MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    basis = dict(status='contextual_incidental_agreement_reading', document=FULL,
        revises_document=PARENT, revises_meaning_basis=PARENT_BASIS,
        primitives=primitives, definitions=definitions, predecessor_source_sha256=old.source_sha256,
        limitations=[
            '意図されないことと比較条件に対する非必然性を合わせる文脈的な読み。全てのZufallの語義をこの条件に還元しない。',
            '過程・比較範囲・目標の解釈を指定せずに自然言語から確定する仕組みではない。通常の合理的な真理探究や共通背景を、他の論説への一致を目標にした調整と自動同一視しない。',
            '結果を目指さないことは、全ての原因が不明、因果なし、確率的独立、あらゆる一致が予想外であることを意味しない。',
            '定義展開は内容対応の十分な証拠の一つであり、hzliの全対応を判定する手続きではない。',
            '本文42文の構文と既存十単位の意味判断を保持する。著者注全体の再読と、残る内容対応規約の確認は別途必要。'],
        unresolved=[dict(basis=r['basis'], historical_caveats=r['caveats']) for r in old.lineage])
    core = deepcopy(doc)
    core['declarations'] = closure(doc, ['hzle'])
    core['statements'] = [doc['statements'][22]]
    library = deepcopy(doc)
    library['declarations'] = closure(doc, ['rqw6', 'rqw7'])
    library['statements'] = []
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/designation-order-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda obj: json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
        LIBRARY: format_graph(library, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(ann)}


def main():
    for name, body in build().items():
        path = ROOT / name
        if path.exists():
            assert path.read_text(encoding='utf-8') == body, name
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Contextual incidental outcome connected to the source question', flush=True)


if __name__ == '__main__':
    main()
