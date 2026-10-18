"""Evaluate dissemination only inside explicitly permission-conditioned cases."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-dissemination-reason.noema'
PARENT_BASIS='data/dissemination-reason-basis-v1.json'
FULL='examples/v016/kant-conditional-dissemination.noema'
CORE='examples/v016/conditional-dissemination-core.noema'
LIBRARY='examples/v016/conditioned-contents.noema'
BASIS='data/conditional-dissemination-basis-v1.json'
FIELDS=[('audience','a'),('reference','d'),('source','a'),('frame','a'),('origins','h[d] d'),('cases','h[d] c'),('contents','h[d] e')]
MEANINGS={
 'rqtn':'指定候補のうち条件を満たすものを内部で選び、その範囲が非空であり、全てについて同じ候補の内容を同じ候補の基準点で評価する。条件や結果を現実の評価点へ移さない。指定範囲での例外なしの読みであり、空の条件範囲を真とする一般の含意や、ほぼ必然の程度評価とは区別する。',
 'hzp7':'全指定候補の経過をhzneで検査し、同じ公衆・参照文脈・出所・期間枠と各候補の基準点による許可継続hznfをrqtnの条件にする。内容もその同じ候補と基準点で評価する。不正な候補が自由の条件を満たさないことを理由に検査から消さない。',
 'hzpa':'hzp7の条件付き判断を閉じた引用に置ける内容として構成する。明示した候補・基準点・内容族を共用する。内容を評価する場所を仮定内の基準点として代入せず、現実での自由や伝播を主張しない。',
}
LIMITS=[
 '自由を公的な理性使用への許可が継続することとして扱う既存hznfの読みを引き継ぐ。物理的な機会や妨害の不在までこの規範条件から導かない。',
 '条件を満たす指定候補で例外なく予測が成立するという読みを構成する。全可能世界の必然性、頻度確率、先頭文のほぼ不可避性を同じものとしない。',
 'contentsは候補を受けて内容を返すNoema関数である。候補ごとの人物・履歴・経路の条件をその関数内で明示できる。関数を不透明な「翻訳済み」の基本関係として実装しない。',
 '現在の伝播候補は行為と経路の供給関数を引数に持つ。原文の不定な行為・経路を存在として記述する接続は別途必要であり、任意の供給関数を原文の唯一の指定だとはしない。',
 '同じ理由側箇所hzp5へ閉じた内容をhzonで帰属できることを検査するが、未確定の解釈引数を埋めた新しい無条件の本文主張は加えない。既存33文と七単位の確認を保つ。',
 '未知の入力は偽で補わない。大きな具体例の評価は短絡診断を明記し、通常評価や無限の候補範囲を尽くす検証とは扱わない。',
]


def definitions():
    selected='w[c[v cases][v branch]][c[v condition][v branch]]'
    text='d rqtn[cases h[d] c condition h[d] c origins h[d] d contents h[d] e] c['
    text+='w[g branch d['+selected+']][f branch d[y['+selected+'][t[c[v contents][v branch]][c[v origins][v branch]]]]]].'
    fields=' '.join(n+' '+t for n,t in FIELDS)
    text+='d hzp7['+fields+'] c[w[f branch d[y[c[v cases][v branch]][k hzne[v frame c[v origins][v branch] v branch]]]]['
    text+='k rqtn[v cases i[branch d][k hznf[v audience v reference v source v frame c[v origins][v branch] v branch]] v origins v contents]]].'
    text+='d hzpa['+fields+'] e[b evaluation[k hzp7['+' '.join('v '+n for n,t in FIELDS)+']]].'
    return text


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[]
    core['declarations']=closure(doc,['hzpa','hzoy','hzny','rqsx','hzon','hzp5','hzp3','wa','hzhb'])
    library=deepcopy(core);library['declarations']=closure(doc,['rqtn'])
    basis=dict(status='permission_conditioned_candidate_contents_with_shared_origins',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        LIBRARY:format_graph(library,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Conditional candidate contents share permission and evaluation origins',flush=True)


if __name__=='__main__':main()
