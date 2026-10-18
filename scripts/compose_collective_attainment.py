"""Parameterize collective attainment without treating it as unanimity."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_falling_depiction import ROOT,closure

PARENT='examples/v016/kant-explanatory-question.noema'
PARENT_BASIS='data/explanatory-question-basis-v1.json'
FULL='examples/v016/kant-collective-attainment.noema'
CORE='examples/v016/collective-attainment-core.noema'
LIBRARY='examples/v016/collective-attainment.noema'
BASIS='data/collective-attainment-basis-v1.json'
FRAME='epoch a context d history h[d] c before h[d d] c periods h[a d] c people h[a] c present h[a d] c'
FARGS='v epoch v context v history v before v periods v people v present'
STANDARD='h[h[a] c h[a] c d] c'
CHECKED=FRAME+' assessed h[a] e standard '+STANDARD
ATTAINED=CHECKED+' capable h[a] e'
AARGS=FARGS+' v assessed v standard v capable'
CONTRAST=ATTAINED+' progress e'
SOURCE='epoch a history h[d] c before h[d d] c periods h[a d] c people h[a] c present h[a d] c standard '+STANDARD
SARGS='v epoch v history v before v periods v people v present v standard'
MEANINGS={
 'rqwg':'同じ集団・評価文脈の肯定的な到達基準が、誰も条件を満たさない分布を拒否し、全員が満たす分布を受け入れることを検査する。中間の分布を一律に全員一致へ置換しない。',
 'rqwh':'同じ時代・非空の集団・現在でrmiの全員の評価が整い、rqwgの基準の両端条件も整う。未評価や不正な基準を未到達の理由にしない。',
 'rqwi':'rqwhが整い、指定集団内で現在能力を持つ人々の分布が、同じ集団・現在の到達基準を満たす。集団外の能力を成功者として渡さない。',
 'rqwj':'同じ時代・集団・現在についてrqwhが整い、rqwiの到達は偽で、rmkの進行内容は真である。到達と進行の二者択一や、進行から未到達への推論ではない。',
 'rqwk':'rqwiの同じ集団と基準による到達内容を問う正極性の質問発話。問いを作ることから内容の真理や実際の質問出来事は導かない。',
 'rqwl':'rqwjの未到達だが進行中という内容を答えとして主張する発話。判断基準を問答の間で変えず、著者による提示と内容の真理は別に評価する。',
 'hzvc':'rqwiの評価・能力を現在のfo・h4lへ接続する時代の到達内容。旧hzfbが固定した全員一致を、明示した集団と到達基準へ置き換える比較候補。',
 'hzvd':'hzvcと同じ現在の評価・能力・集団基準で、未到達と進行を結ぶ内容。進行の内容は同じ明示的な設定から渡す必要がある。',
 'hzve':'hzvcの到達内容を問う発話。時代全体の全時点で全員が能力を持つという内容にはしない。',
 'hzvf':'hzvdの対比内容を主張する発話。質問の発話種別とは区別し、条件付きで質問を提示する原文全体の記述とはまだ分ける。',
}
LIMITS=[
 'im Ganzen genommenを含む段落の到達判断を、全員一致へ固定しないための比較候補。どの集団・分布基準が原文の文脈に適切かを、型や有限テストだけで決めない。',
 '基準は集団・能力を持つ部分集団・評価文脈に結ぶ。数値比率や過半数をNoemaの語義へ固定しない。基準を結果に合わせて後から選び直す読みは採らない。',
 '両端の条件は、空の成功分布を肯定し全員の到達を拒否するような基準を除く。これだけで任意の中間分布について単調性・匿名性・公平さを証明するものではない。原文の採用には基準の意味規約も必要である。',
 '全員の評価が整うことと、全員が能力を持つことは別条件である。未知の個人評価や基準を偽で埋めず、集団外の成功、別の集団や時点の判定を流用しない。',
 '宗教上の理解力使用、sicher und gut、現状から能力を得させうる可能性、隔たりの程度、機会の開放と徴候、条件付きの問答、段落全体の著者帰属は残る。集団基準だけで段落を完成扱いにしない。',
 '既存の文と意味規約を変更せず、新しい引数付き候補を加える。現行登録本文と十単位・604文字の意味判断を保持し、この比較草案を自動的に著者の主張として採用しない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def definitions():
    false='u[e[n p a b][n p a b]]';true='e[n p a b][n p a b]'
    text='d rqwg[people h[a] c context d standard '+STANDARD+'] c[w[u[c[v standard][v people i[person a]['+false+'] v context]]][c[v standard][v people v people v context]]].'
    text+='d rqwh['+CHECKED+'] c[w[k rmi['+FARGS+' v assessed]][k rqwg[v people v context v standard]]].'
    mask='i[person a][w[c[v people][v person]][t[c[v capable][v person]][v context]]]'
    text+='d rqwi['+ATTAINED+'] c[w[k rqwh['+FARGS+' v assessed v standard]][c[v standard][v people '+mask+' v context]]].'
    text+='d rqwj['+CONTRAST+'] c[w[k rqwh['+FARGS+' v assessed v standard]][w[u[k rqwi['+AARGS+']]][k rmk['+FARGS+' v progress]]]].'
    for name,target,fields,extra,force in [('rqwk','rqwi',ATTAINED,'','rij'),('rqwl','rqwj',CONTRAST,' v progress','rik')]:
        text+='d '+name+'['+fields.replace(' context d','')+'] f[k '+force+'[b context[k '+target+'['+AARGS+extra+']] '+true+']].'
    args=FARGS+' p fo v standard p h4l'
    text+='d hzvc['+SOURCE+'] e[b context[k rqwi['+args+']]].'
    text+='d hzvd['+SOURCE+' progress e] e[b context[k rqwj['+args+' v progress]]].'
    text+='d hzve['+SOURCE+'] f[k rij[k hzvc['+SARGS+'] '+true+']].'
    text+='d hzvf['+SOURCE+' progress e] f[k rik[k hzvd['+SARGS+' v progress] '+true+']].'
    return text


def build():
    cat=parent();doc=deepcopy(cat.document);statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    assert not set(MEANINGS)&set(cat.entries)
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    lib=deepcopy(doc);lib['declarations']=closure(doc,['rqwk','rqwl']);lib['statements']=[]
    core=deepcopy(doc);core['declarations']=closure(doc,['hzvc','hzvd','hzve','hzvf','hzfb','hzfc']);core['statements']=[]
    added=doc['declarations'][size:]
    basis=dict(status='contextual_collective_attainment_comparison_not_adopted_claim',document=FULL,library=LIBRARY,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,text in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==text,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
    print('Collective criterion separated from unanimous attainment',flush=True)


if __name__=='__main__':main()
