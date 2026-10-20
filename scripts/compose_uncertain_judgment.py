"""Compose unreliable independent judgment and a target-side conditional candidate."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-abandoned-reliance.noema'
PARENT_BASIS = 'data/abandoned-reliance-basis-v1.json'
FULL = 'examples/v016/kant-uncertain-judgment.noema'
CORE = 'examples/v016/uncertain-judgment-core.noema'
LIBRARY = 'examples/v016/assessed-unreliability.noema'
BASIS = 'data/uncertain-judgment-basis-v1.json'
ANNOTATIONS = 'data/uncertain-judgment-identifiers-v1.json'
MEANINGS = {
    'r2gu': '比較場面の全候補に保持条件と外的機会があり、通常性の順序と非空の通常候補が有効である。応答そのものを常に真とするr2glで、応答の成否から独立した評価条件を取り出す。',
    'r2gv': '有効な同じ比較で、全ての通常場面に指定した応答がある。前版r2glの肯定極性を再利用する。現在の成功や、全種類の能力を要求しない。',
    'r2gw': 'r2guの有効な評価条件の下でr2gvが成立しない。少なくとも一つの通常場面に応答がないという非確実性であり、全通常場面で応答がない負極性の傾向とは異なる。空や不正な比較を不確かさと数えない。',
    'r2gx': '本人が同じ対象について同じ判断活動を行い、同じ本人の理解力をその判断で使い、その判断活動が生起する。本人と異なる者による同じ判断への指導はない。理由の支持・真理・成功は別条件である。',
    'r2gy': 'r2gxの同じ判断について、既存h5cの自分の理解力・理由・支持・他者の指導不在を要求する。別の判断への支持や別の話題を借りない。',
    'r2gz': '同じ本人・判断活動・課題・基準に対応する比較で、各候補の対応活動が非空であり、基盤保持と外的機会が全候補で有効である。その通常候補で、全対応活動がr2gyを満たすとは限らない。対応活動の欠落と、存在する対応活動での応答不成立を区別する。',
    'r2ha': '同じ基準で実際の独立した判断r2gxがあり、その同じ活動・課題の比較にr2gzの非確実性がある。実際の判断が理由に支持されることも許し、実際の誤りや判断不能を補わない。',
    'r2hb': '提示文脈whで本人について固定した課題に、r2haを満たす判断活動がある。比較の結果ごとに課題を交換しない。課題の最小の難しさや、他の活動を全て排除する限定はまだ含まない。',
    'r2hc': '同じ本人・非空の仮定集合で、前版r2gtの依存離脱ならr2hbの不確かな独立判断が成立し、離脱を満たす仮定も存在する。rcとreを再利用し、現在の離脱や判断を断定しない。',
    'r2hd': '固定した提示文脈whで、その本人の知的活動側の仮定集合へr2hcを適用する、第四文の対象側の条件骨格候補。著者帰属・身体的描写との対応・理由節・譲歩と尺度限定は未接続である。',
}
PRIMITIVES = {
    'hzzzt': ('a a a d d', ['person', 'judgment', 'topic', 'anchor', 'candidate'], '同じ本人・判断活動・課題・基準について、その活動の遂行の確かさを比較する場面。応答の成否によらず選ぶ。全種類の活動能力や生涯全体を評価する集合ではない。'),
    'hzzzu': ('a a a d d', ['person', 'judgment', 'topic', 'anchor', 'candidate'], '比較場面で本人の関連する基盤と課題・取り組み方を保つ。新たな訓練や別の容易な課題への交換を除くが、応答や理由支持の真偽は固定しない。'),
    'hzzzv': ('a a d', ['person', 'topic', 'candidate'], 'その同じ課題について本人が判断に取り組む外的機会がある。判断の実行、能力、理由の支持を機会そのものの条件にしない。'),
    'hzzzw': ('a a a d d d', ['person', 'judgment', 'topic', 'anchor', 'preferred', 'other'], '同じ活動の比較で、背景条件から先の場面を通常とする厳密な優先関係。成功や理由の有無を優先根拠にしない。'),
    'hzzzx': ('a a a d d a', ['person', 'judgment', 'topic', 'anchor', 'candidate', 'counterpart'], '同じ本人の同じ課題へのこの取り組みを比較場面で評価するための対応活動。実際に判断を遂行できるかは別条件であり、未遂の対応活動も指定できる。対応する活動を全て指定し、応答に失敗する活動を除外しない。'),
    'hzzzy': ('a d d', ['person', 'scope', 'candidate'], '同じ本人と提示文脈について、依存離脱を仮定する対象側の条件文の比較場面。描写側の身体的な履歴や、個別判断の確かさを評価する比較集合とは区別する。'),
    'hzzzz': ('a d', ['person', 'scope'], '同じ本人について、この提示文脈で判断対象として指す課題。比較の結果から選び直さない。最も小さい困難の課題という尺度条件は別途必要である。'),
}
LIMITS = [
    '不確かな跳躍の対象側を、独立した判断の実行はあるが、同じ基盤と課題で理由ある自己遂行を通常比較全体に確保できないという読みから構成する。unsicherの唯一の語義や、全ての不安定な知的活動の必要十分条件ではない。',
    '比較場面と対応活動は総解釈で与える。未知を偽と扱わず、空の対応を判断の失敗と数えない。有限モデルの検査は現実の全比較を尽くした証明ではない。',
    '理由の支持は既存h5cの意味規約を継承する。本人の主観的確信、結論の真理、正答率、身体の安全、全方法にわたる能力と同一視しない。現在の理由ある判断と不確かさは両立する。',
    '固定課題への一つの判断活動を記述する。最小の困難の尺度、einen nurの限定、auchとdennochの期待対比、全過程の安定の時間構造は未完である。',
    '条件骨格は前版のr2gtを同じ本人へ渡す。条件だけを記録し、不慣れの活動記述・理由の採用、身体的な比喩との対応、本文の二帰属はまだ置き換えない。',
    '新しい意味確認済み分量と原文対応文字数は加えない。既存54文、十二全単位と先頭三文408文字の判断を保持する。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def additions():
    text = ''.join('r '+n+'['+signature+'] '+('a' if n == 'hzzzz' else 'c')+'.' for n, (signature, _, _) in PRIMITIVES.items())
    return text + '''
d r2gu[cases h[d] c held h[d] c opportunity h[d] c preferred h[d d] c] c[
 k r2gl[v cases v held v opportunity v preferred i[point d][e[v point][v point]] e[n p a b][n p a b]]].
d r2gv[cases h[d] c held h[d] c opportunity h[d] c preferred h[d d] c response h[d] c] c[
 k r2gl[v cases v held v opportunity v preferred v response e[n p a b][n p a b]]].
d r2gw[cases h[d] c held h[d] c opportunity h[d] c preferred h[d d] c response h[d] c] c[
 w[k r2gu[v cases v held v opportunity v preferred]][u[k r2gv[v cases v held v opportunity v preferred v response]]]].
d r2gx[person a judgment a topic a point d] c[
 w[k dg[v judgment v point]][w[k fa[v person v judgment v point]][w[k fb[v judgment v topic v point]][
 w[g faculty a[w[k ab[v faculty v person v point]][k ac[v person v faculty v judgment v point]]]][
 u[g other a[w[u[e[v other][v person]]][k ad[v other v person v judgment v point]]]]]]]]].
d r2gy[person a judgment a topic a point d] c[w[k r2gx[v person v judgment v topic v point]][k h5c[v person v judgment v point]]].
d r2gz[person a judgment a topic a anchor d] c[k r2gw[
 i[scene d][k hzzzt[v person v judgment v topic v anchor v scene]]
 i[scene d][w[k hzzzu[v person v judgment v topic v anchor v scene]][g counterpart a[k hzzzx[v person v judgment v topic v anchor v scene v counterpart]]]]
 i[scene d][k hzzzv[v person v topic v scene]]
 i[first d last d][k hzzzw[v person v judgment v topic v anchor v first v last]]
 i[scene d][f counterpart a[y[k hzzzx[v person v judgment v topic v anchor v scene v counterpart]][k r2gy[v person v counterpart v topic v scene]]]]
]].
d r2ha[person a judgment a topic a anchor d] c[w[k r2gx[v person v judgment v topic v anchor]][k r2gz[v person v judgment v topic v anchor]]].
d r2hb[person a] e[b anchor[g judgment a[k r2ha[v person v judgment k hzzzz[v person k wh[]] v anchor]]]].
d r2hc[person a cases h[d] c] c[w[k rc[v person p r2gt p r2hb v cases]][k re[v person p r2gt v cases]]].
d r2hd[person a] e[b anchor[w[e[v anchor][k wh[]]][k r2hc[v person i[scene d][k hzzzy[v person v anchor v scene]]]]]].
'''


def build():
    old = parent(); doc = deepcopy(old.document); statements = doc['statements']; doc['statements'] = []
    assert not (set(MEANINGS) | set(PRIMITIVES)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + additions()); doc['statements'] = statements
    core = deepcopy(doc); core.update(declarations=closure(doc, ['r2hd']), statements=[])
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['r2gu', 'r2gv', 'r2gw']), statements=[])
    added = doc['declarations'][len(old.document['declarations']):]; assert len(added) == 17
    decls = {d['name']: d for d in added}
    basis = dict(status='unasserted_uncertain_judgment_and_conditional_candidate', document=FULL, parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
        primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'], arguments=args, meaning_ja=meaning)
            for n, (_, args, meaning) in PRIMITIVES.items()},
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/abandoned-reliance-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact')+'\n', LIBRARY: format_graph(lib, 'compact')+'\n',
        BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Uncertain judgment and conditional candidate composed; 54 statements preserved', flush=True)
