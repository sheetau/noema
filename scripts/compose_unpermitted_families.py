"""Quantify missing permission over a specified family of described proposals."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_falling_depiction import ROOT,closure

PARENT='examples/v016/kant-walking-warning.noema'
PARENT_BASIS='data/walking-warning-basis-v1.json'
FULL='examples/v016/kant-unpermitted-families.noema'
CORE='examples/v016/unpermitted-families-core.noema'
LIBRARY='examples/v016/unpermitted-families.noema'
BASIS='data/unpermitted-families-basis-v1.json'
MEANINGS={
 'rqy6':'指定範囲の全候補について、候補ごとの内容記述と引数列が適合し、同じ出所・名宛人・役割・極性・文脈で積極的な許容がない。範囲が空なら全称条件は真だが、候補や実行可能性の存在を主張しない。不正な引数や未知の許容を許容欠如へ補わない。',
 'rqy7':'指定範囲に、適合する内容記述・引数列を持ち、同じ出所・名宛人・役割・極性・文脈で積極的に許容された候補が少なくとも一つある。範囲外への許容、別候補の引数や別文脈は流用しない。許容された内容の実行や成功は要求しない。',
 'rqza':'指定した候補範囲の全てについて、候補に対応する閉じた目標を同じ本人が勇気を伴って試みる内容への許容がない。各候補のhztcを全称化する。単一の包括的な目標のhztcとは異なり、一候補だけの許容も区別する。候補範囲の完全性や身体的な一歩の構成は呼出側で指定する。',
}
LIMITS=[
 '個別に許容された候補を落とさないための一般構成。指定された範囲が現実の全候補を尽くすことは、量化の形式だけでは保証しない。',
 '規範の基本関係には内容の含意に沿った自動的な閉包を仮定しない。包括的活動への許容欠如から個別活動への許容欠如を推論しない。',
 '無許容と禁止、実行不能、勇気不足、不実行は別である。空範囲では候補の存在を補わず、適合しない候補のある範囲では無許容の全称条件を認定しない。',
 '身体的な一歩と装置外の目標の全範囲、および本文の先行時点との結合が未確定のため、この比較候補を原文の主張には採用しない。現行47文と既存の意味確認を保持する。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();doc=deepcopy(old.document);assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    text='''
d rqy6[source a person a role a members h[a] c descriptions h[a] i[h[j[a]] e] arguments h[a] j[a] polarity c scene d valid h[j[a]] c demands h[a a a i[h[j[a]] e] j[a] c d] c permits h[a a a i[h[j[a]] e] j[a] c d] c] c[
 f item a[y[c[v members][v item]][k rjp[v source v person v role c[v descriptions][v item] c[v arguments][v item] v polarity v scene v valid v demands v permits]]]
].
d rqy7[source a person a role a members h[a] c descriptions h[a] i[h[j[a]] e] arguments h[a] j[a] polarity c scene d valid h[j[a]] c demands h[a a a i[h[j[a]] e] j[a] c d] c permits h[a a a i[h[j[a]] e] j[a] c d] c] c[
 g item a[w[c[v members][v item]][k rdt[v source v person v role c[v descriptions][v item] c[v arguments][v item] v polarity v scene v valid v demands v permits]]]
].
d rqza[source a person a role a members h[a] c goals h[a] i[h[a] e]] e[
 b scene[f item a[y[c[v members][v item]][t[k hztc[v source v person v role c[v goals][v item]]][v scene]]]]
].
'''
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    core=deepcopy(doc);core.update(declarations=closure(doc,['rqza']),statements=[])
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['rqy6','rqy7']),statements=[])
    basis=dict(status='quantified_permission_comparison_not_adopted_source_claim',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    from scripts.audit_opening_scope import write_exact
    for path,text in build().items():write_exact(ROOT/path,text)
    print('Quantified permission comparison composed; active manuscript unchanged',flush=True)


if __name__=='__main__':main()
