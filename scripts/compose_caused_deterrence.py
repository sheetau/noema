"""Use actual causal contribution, not adopted explanation, for deterrence."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_reasoned_concession import ROOT,closure
from scripts.compose_courageous_undertaking import replace_symbols

PARENT='examples/v016/kant-reasoned-concession.noema'
PARENT_BASIS='data/reasoned-concession-basis-v1.json'
FULL='examples/v016/kant-caused-deterrence.noema'
CORE='examples/v016/caused-deterrence-core.noema'
BASIS='data/caused-deterrence-basis-v1.json'
ANNOTATIONS='data/caused-deterrence-identifiers-v1.json'
MAPPING={'gs':'hzua','gu':'hzub','gv':'hzuc','gx':'hzud','gy':'hzue','hztv':'hzuf','hztw':'hzug','hztx':'hzuh'}
MEANINGS={
 'hzua':'同じ事例の対象者に、同じ活動bbへ向かう十分な勇気がなく、少なくとも一つの後続する試みへの害の恐れがある。勇気の目標は閉じた性質記述で指定し、目標の実現やその真偽の同一性で別の活動を代用しない。',
 'hzub':'同じ事例で、認識された先行例grと萎縮hzuaが実際に成立し、前者が後者へ因果的に寄与する。両内容の共存や説明への採用eaだけでは満たさない。rqquの固定した二記述への特殊化であり、引用可能性を保つ。',
 'hzuc':'同じ事例で、認識された先行例grと、後続する試みの全範囲を恐れにより避けるgtが実際に成立し、前者が後者へ因果的に寄与する。本人が恐れを回避理由とするmeと、実際の因果hzieを区別する。',
 'hzud':'旧gxの非空・重複なし・適格性・範囲の網羅性と通常性の条件を保持し、萎縮と回避に実際の因果条件hzub・hzucを使う。回避しない例外を同じ範囲に残す。',
 'hzue':'更新したhzudを著者に帰属させ、学習の見込みの後という本文順を保持する。引用した因果条件を実行評価しない。',
 'hzuf':'既存hztvの期待背景に用いるQをhzudへ更新し、同じPと質的比較、視点と状況を保つ。',
 'hzug':'同じ更新後のhzudとhzufを主張・期待背景の組として保持する。旧gxだけを主張側へ残さない。',
 'hzuh':'理由付けftと本文順を保持し、更新後の萎縮・回避の主張と期待背景を同じ著者・範囲・文脈へ帰属する。',
}
LIMITS=[
 '原文のmacht ... schüchternとschrekt ... abを、単に説明に採用したという意味ではなく、例の認識が反応へ実際に寄与する主張として読む。原著者の因果主張を実証したわけではない。',
 'hzieは既存の意味規約を持つ基本関係である。唯一・必要・十分な原因、反事実の全状況、認知機構や測定方法を追加しない。',
 'grは同じ事例の対象者が認識した先行する不成功経験を記述する。経験者と対象者は別でもよい。架空の例、身体的な転倒との比喩対応、認識から反応までの詳細な時間構造は残る。',
 '勇気は既存hzioにより、同じ本人についてのbbの閉じた記述へ結ぶ。勇気の程度基準、schüchternの語義全体、以前より恐れが増えたという変化は今回確定しない。',
 'gtの恐れ・回避・本人が恐れを理由とする関係を保持する。因果の条件を追加しただけで、本人の理由認識と原因が一般に同じになるとはしない。',
 '通常性の有限事例・等重み・過半数と文脈基準、全称的な試みの範囲、期待背景の操作化は前版のまま。第二段落全体と両作品の全文の意味確認は未完。',
 '本文の末尾一文を更新し、他の37文と既存九単位の意味判断を保持する。新しい意味の基本関係と原文対応文字数は増やさない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    assert not set(MEANINGS)&set(old.entries)
    doc=parse(format_graph(doc,'compact')+'''
d hzua[case a] e[b scene[w[u[k hzio[k gd[v case] r[p bb] v scene]]][
 g act a[w[k gq[k gd[v case] v act v scene]][k mc[k gd[v case] v act v scene]]]
]]].
d hzub[case a] e[b scene[w[t[k gr[v case]][v scene]][w[t[k hzua[v case]][v scene]][
 k hzie[v case r[p gr] v case r[p hzua] v scene]
]]]].
d hzuc[case a] e[b scene[w[t[k gr[v case]][v scene]][w[t[k gt[v case]][v scene]][
 k hzie[v case r[p gr] v case r[p gt] v scene]
]]]].
''')
    lookup={d['name']:d for d in old.document['declarations']}
    for name in ('gx','gy','hztv','hztw','hztx'):
        row=replace_symbols(deepcopy(lookup[name]),MAPPING);row['name']=MAPPING[name];doc['declarations'].append(row)
    doc['statements']=deepcopy(statements);doc['statements'][37]=replace_symbols(doc['statements'][37],MAPPING)
    doc=parse(format_graph(doc,'compact'));core=deepcopy(doc);core['declarations']=closure(doc,['hzuh']);core['statements']=doc['statements'][-1:]
    added=doc['declarations'][size:]
    basis=dict(status='actual_causal_contribution_in_example_deterrence',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={},definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/reasoned-concession-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Actual causal contribution connected to deterrence',flush=True)


if __name__=='__main__':main()
