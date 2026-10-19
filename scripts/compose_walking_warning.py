"""Compose a bodily warning from existing trial, risk and conditional relations."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT='examples/v016/kant-guardian-reading.noema'
PARENT_BASIS='data/guardian-reading-basis-v1.json'
FULL='examples/v016/kant-walking-warning.noema'
CORE='examples/v016/walking-warning-core.noema'
LIBRARY='examples/v016/conditional-activity-risk.noema'
BASIS='data/walking-warning-basis-v1.json'
ANNOTATIONS='data/walking-warning-identifiers-v1.json'
MEANINGS={
 'rqy3':'同じ本人と基準文脈について指定する非空の仮定範囲で、試みの目標を試みるなら、危険評価の目標へ向かう場合の可能な結果に本人への不利益があるという条件内容。二つの目標記述は独立に指定し、本人・候補状況・結果を結ぶ。実際の試み・成功・危険の発生、許可・勇気・高い危険度は要求しない。',
 'rqy4':'既存zalの補助なしの脚による身体移動を、試みと危険評価の双方の目標に指定したrqy3。仮定範囲は同じ人物・提示文脈のf4を対応する事例の索引として用いる。各事例の身体側と知的側の試みや危険の真理値は独立である。歩行の運動学全体や一歩の最小単位をこの定義で説明したとはしない。',
 'rqy5':'同じ複文hzsqの著者wa・提示文脈whで、知的活動の条件付き危険euを、同じ人物の身体移動の条件付き危険rqy4で非字義的に描写する。引用された条件内容は実行評価せず、現実の危険・転倒・歩行の成功や二内容の真理値一致を主張しない。',
}
LIMITS=[
 'allein zu gehenを、他者や装置による身体支持なしに脚で移動する描写として読む候補。単に同行者がいないこととは区別する。',
 'f4は描写の両側で対応する仮定事例の索引として共有する。現実の同一出来事や知的活動と身体活動の因果的同一性は含意しない。一般形では範囲関数を任意に渡せる。',
 '脚の移動zalの歩行と走行の境界、一歩もという最小単位と許容の範囲、ruhigenの描写、jaの強調は未完。原文一文全体の意味確認を増やさない。',
 '原刊の読みと公開した基本関係の下での部分記述であり、意味一致の自動証明でも独立査読でもない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();doc=deepcopy(old.document);assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    text='''
d rqy3[person a trialgoal i[h[a] e] riskgoal i[h[a] e] cases h[a d d] c tries h[a i[h[a] e] d] c outcomes h[a i[h[a] e] d d] c adverse h[a d] c] e[
 b scene[k rc[v person
  i[subject a][b point[c[v tries][v subject v trialgoal v point]]]
  i[subject a][b point[k rl[v subject v riskgoal v point v outcomes v adverse]]]
  i[point d][c[v cases][v person v scene v point]]
 ]]
].
d rqy4[person a] e[k rqy3[v person r[p zal] r[p zal] p f4 p ei p uq p ur]].
d rqy5[] c[k qh[k hzsq[] k wa[] r[p eu] r[p rqy4] k wh[]]].
s[k rqy5[]].
'''
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements+doc['statements']
    core=deepcopy(doc);core['statements']=[doc['statements'][i] for i in (9,35,36,46)]
    core['declarations']=closure(doc,_references(core['statements']))
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['rqy3']),statements=[])
    basis=dict(status='conditional_bodily_warning_composed_without_new_primitives',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/guardian-reading-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',
        BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for path,text in build().items():write_exact(ROOT/path,text)
    print('Bodily conditional warning composed with three definitions and no new primitives',flush=True)


if __name__=='__main__':main()
