"""Construct self-appraisal and an explicitly normative universal calling."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-communicated-attitudes.noema'
PARENT_BASIS='data/communicated-attitudes-basis-v1.json'
FULL='examples/v016/kant-reasoned-self-appraisal.noema'
CORE='examples/v016/reasoned-self-appraisal-core.noema'
LIBRARY='examples/v016/identified-reasoned-judgment.noema'
BASIS='data/reasoned-self-appraisal-basis-v1.json'
READING='data/self-appraisal-reading-v1.json'
PRIMITIVES={
 'hznm':(['judgment','target','criterion','assessment','context'],
   'この判断が、指定対象の価値・長所を指定した評価基準の下で、この評定として評価している。同じ判断の主体・理由・支持は別の関係で結ぶ。評定は質的な個体として扱え、数値・価格・他者との序列・判断の正しさを自動的に要求しない。基準と評定の解釈は明示する。自分自身だけに限定した語ではない。'),
 'hznn':(['judgment','subject','content_description','polarity','context'],
   'この判断が、指定対象へ同じNoemaの内容記述を適用した内容を、指定極性で認めている。真は肯定、偽は否定である。判断主体はfaで別に結び、検討しただけの場合hzvと区別する。内容の実際の真理や実現、判断の正しさ、対象を実行する意図を含意しない。記述を真偽が同じ別記述へ置き換えない。'),
}
MEANINGS={
 'rqtf':'指定した同じ判断行為について、本人が判断し、同じ事柄を対象とし、その判断で使った理由がその同じ判断を支えることを要求する。別の判断の理由・支持を合算しない。',
 'hzno':'本人が人であり、自分の理解力を用い、用いた理由で支持され、他人の指導によらない判断rcrを行うという内容。既存iahthinkingと同じ本体を使う。思考一般の全ての形態や、実行能力だけを意味しない。',
 'hznp':'一人だけの引数列にhznoを適用する内容。空列・余分な引数・別人の思考では満たさない。要求関係h7kへ渡す対象の記述として使い、要求を述べるだけでは内容を実行しない。',
 'hznq':'指定の規範源と立場について、全ての人に、同じhznpへ本人一人の引数列を渡した内容を正極性で要求する命題を作る。対象引数は命題を扱う話題の位置で、量化する人の範囲をその一人へ狭めない。人が存在しない解釈では通常の全称命題として真になる。',
 'hznr':'人である本人が、自分自身を対象として、同じ基準で価値を評定する理由ある判断を行うという内容。評定と判断は存在量化し、原文にない価格や具体的な価値の高さを固定しない。',
 'hzns':'規範源・立場の閉じた参照記述からhznqの命題関数の記述を組み立てる。人ごとの目標はhznpの本人への適用として固定され、規範の真理や思考の実行は評価しない。',
 'hznt':'同じ人が同じ話題について、同じ内容記述を肯定する理由ある判断を行うという内容。単なる検討・理解、別人の判断、別の内容や否定判断は足りない。肯定した内容の真理を追加しない。',
 'hznu':'同じ本人と状況に、hznrの理由ある自己評価と、全ての人の自己思考への課題を認めるhzntの判断を結ぶ。評価基準と規範の出所・立場は別に保持する。二つの判断は別の行為でもよい。',
 'hznv':'評価基準・話題・規範源・立場の閉じた参照から、hznuの性質記述を構成する。規範の出所と立場は内側の内容記述にもそのまま保持し、別に渡した性質関数との一致を仮定しない。取得を述べる場合はこの同じ記述を既存rqteへ渡せる。',
}
LIMITS=[
 '人の価値を評定することと、価格を決めることは同一にしない。hznmは一般的な価値評価の関係であり、原文の人としての価値に適した基準は解釈で指定する。全ての価値を数値や有用性へ還元しない。',
 'Berufを、全ての人が自分で考えることを課題として要求されるという規範的な読みで具体化する。内的衝動など他の読みを否定せず、神・国家・職業・法的強制を暗黙に補わない。規範源と立場は明示する。',
 '判断が理由に支えられる条件はfc・fdの意味規約を使う。支持の全理論や絶対的な正しさを証明するものではない。rationalという語を任意の理由の存在だけへ弱めない。',
 'hznuは評価と規範承認を行う具体的な状態であり、持続的な精神・性向としてのGeistを一回の判断だけで尽くしたとはしない。取得・伝達・性向・将来の様相への全文接続は残る。',
 '前段hzniの、自分の状態に対する好ましい受容へ置き換えない。全ての人についての規範を認める判断は、本人の自己状態だけを好む態度とは区別する。',
 'hznpで記述する思考は独立した理由ある判断という読みであり、想像・探索・問いなど思考全体を網羅しない。内容の記述と実際の実行は区別する。',
 '既存32文・全意味規約・確認済み七単位を保存する。具体化した読解候補を著者の新しい無条件主張として加えず、既存範囲の補足だけを記録する。',
]


def definitions():
    return '''
r hznm[a a a a d] c.
r hznn[a a i[h[a] e] c d] c.
d rqtf[person a judgment a subject a context d judges h[a a d] c about h[a a d] c
 uses h[a a d] c supports h[a a d] c] c[
 w[c[v judges][v person v judgment v context]][w[c[v about][v judgment v subject v context]][
 g reason a[w[c[v uses][v judgment v reason v context]][c[v supports][v reason v judgment v context]]]]]
].
d hzno[person a] e[b point[w[k aa[v person]][g judgment a[
 k rcr[v person v judgment v point p ab p ac p fa p fb p fc p fd p ad]]]]].
d hznp[arguments j[a]] e[b context[g person a[w[e[v arguments][l[a][v person]]][t[k hzno[v person]][v context]]]]].
d hznq[source a role a] h[a] e[i[subject a][b context[
 f person a[y[k aa[v person]][k h7k[v source v person v role r[p hznp] l[a][v person] e[v person][v person] v context]]]
]]].
d hznr[person a criterion a] e[b context[w[k aa[v person]][g judgment a[g assessment a[
 w[k rqtf[v person v judgment v person v context p fa p fb p fc p fd]][
 k hznm[v judgment v person v criterion v assessment v context]]]]]]].
d hzns[source i[a] role i[a]] i[h[a] e][o a[r[p hznq]][v source v role]].
d hznt[person a subject a claim i[h[a] e]] e[b context[w[k aa[v person]][g judgment a[
 w[k rqtf[v person v judgment v subject v context p fa p fb p fc p fd]][
 k hznn[v judgment v subject v claim e[v person][v person] v context]]]]]].
d hznu[criterion a subject a source i[a] role i[a]] h[a] e[i[person a][b context[
 w[t[k hznr[v person v criterion]][v context]][t[k hznt[v person v subject k hzns[v source v role]]][v context]]
]]].
d hznv[criterion i[a] subject i[a] source i[a] role i[a]] i[h[a] e][
 o a[r[p hznu]][v criterion v subject o r[v source] o r[v role]]
].
'''


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['hznv','hznp','rqte','g3','ag','la','dg','h6a'])
    library=deepcopy(core);library['declarations']=closure(doc,['rqtf'])
    primitives={}
    for d in doc['declarations'][size:]:
        if d['kind']=='primitive':
            args,meaning=PRIMITIVES[d['name']]
            primitives[d['name']]=dict(parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning)
    basis=dict(status='reasoned_self_appraisal_and_universal_calling_explicit_reading',document=FULL,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        LIBRARY:format_graph(library,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Self-appraisal and a universal thinking task composed without factualizing the task')


if __name__=='__main__':main()
