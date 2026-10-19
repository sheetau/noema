"""Compose subject-bound episode absence without lexical quietness primitives."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_grounded_step import ROOT,closure

PARENT='examples/v016/kant-step-depiction.noema'
PARENT_BASIS='data/step-depiction-basis-v1.json'
FULL='examples/v016/kant-scoped-quiet.noema'
CORE='examples/v016/scoped-episode-absence.noema'
BASIS='data/scoped-quiet-basis-v1.json'
MEANINGS={
 'rqzz':'同じ本人・出来事・状況について、本人との関係、出来事の生起、指定された性質が全て成立する。別々の出来事や時点の証拠を合わせない。本人との関係と性質は引数で与え、行為者・経験者、外面の動き・内面の状態を固定しない。',
 'rqz2':'指定した履歴内の空でなく間の抜けない範囲をtbで検査し、その範囲のどの時点にもrqzzを満たす出来事がない。範囲外の出来事、別人の出来事、未生起の候補、別の性質をこの不在へ混ぜない。未知の情報を不在と扱わない。',
 'rqz3':'rqz2と同じ範囲整合条件の下で、少なくとも一つの選択時点にrqzzを満たす出来事がある。整合した範囲ではrqz2の反対側だが、空・欠落・履歴外など不整合な範囲では両方偽になり、単なるrqz2の否定とは異なる。',
 'rqz4':'rqz2の本人と出来事の関係を既存の行為参加df、生起をdgに固定する。指定した性質を持つ本人の実際の行為が選択範囲にない。他の性質の行為は許し、全活動の停止・服従・無感情・勇気不足を含意しない。',
}
LIMITS=[
 '落ち着いた外面を、文脈で顕著な乱れを持つ活動の不在として説明するための比較構成。性質の指定だけでruhigの語義を説明し終えたとはしない。どの性質が顕著な乱れかという基準と、この用例の読解は未確定。',
 '同じ一般構成に行為参加と経験主体の別関係を渡せるが、二つを自動的に同一化しない。身体が動かないこと、他者への負担、内面の平静、非抵抗、服従を同義にしない。',
 '指定する履歴と範囲は完全な意味上の範囲。有限観測で乱れが見えなかったことから全期間の不在を導かない。tbは引数の完全性そのものや現実の観測網羅性を証明しない。',
 '全称・連言は通常評価器では選択外を含む総関数を要求する場合がある。未知入力を偽として補う規則は追加しない。',
 '本文の48文と既存十一単位の判断を保持する。ruhigenの描写への採用、一文全体、二作品全文の意味確認は増やさない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();doc=deepcopy(old.document);assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    text='''
d rqzz[person a episode a point d subject h[a a d] c occurs h[a d] c marked h[a d] c] c[
 w[c[v subject][v person v episode v point]][w[c[v occurs][v episode v point]][c[v marked][v episode v point]]]
].
d rqz2[person a history h[d] c phase h[d] c before h[d d] c subject h[a a d] c occurs h[a d] c marked h[a d] c] c[
 w[k tb[v history v phase v before]][f point d[y[c[v phase][v point]][u[g episode a[k rqzz[v person v episode v point v subject v occurs v marked]]]]]]
].
d rqz3[person a history h[d] c phase h[d] c before h[d d] c subject h[a a d] c occurs h[a d] c marked h[a d] c] c[
 w[k tb[v history v phase v before]][g point d[w[c[v phase][v point]][g episode a[k rqzz[v person v episode v point v subject v occurs v marked]]]]]
].
d rqz4[person a history h[d] c phase h[d] c before h[d d] c marked h[a d] c] c[
 k rqz2[v person v history v phase v before p df p dg v marked]
].
'''
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[])
    basis=dict(status='scoped_episode_absence_comparison_not_source_adopted',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    from scripts.audit_opening_scope import write_exact
    for path,text in build().items():write_exact(ROOT/path,text)
    print('Four definitions composed; no new primitives or source assertions',flush=True)


if __name__=='__main__':main()
