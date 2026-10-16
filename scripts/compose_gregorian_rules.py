"""Describe Gregorian date validity with checked natural-number certificates."""
from copy import deepcopy
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_calendar_dateline import conjunction,num

PARENT='examples/v016/kant-labeled-dates.noema'
PARENT_BASIS='data/labeled-dates-basis-v1.json'
FULL='examples/v016/kant-gregorian-rules.noema'
LIBRARY='examples/v016/gregorian-rules.noema'
BASIS='data/gregorian-rules-basis-v1.json'
ANNOTATIONS='data/gregorian-rules-identifiers-v1.json'
FIELDS=('year','qfour','rfour','qhundred','rhundred','qfourhundred','rfourhundred')
PARAMS=' '.join(n+' j[b]' for n in FIELDS)
ARGS=' '.join('v '+n for n in FIELDS)
MEANINGS={
 'rqse':'非空の有限数字列の全要素が0から31の整数であることを、有限列の位置検査で要求する。先頭の0は許す。空列・負・分数・32以上の桁は拒否する。',
 'rqsf':'数字列を左から読み、蓄積値を32倍して次の桁を足す。数字列の妥当性はrqseで別に要求する。',
 'rqsg':'被除数・除数・商・余りを有効な32進自然数列で与え、除数が正、被除数=除数×商+余り、余り<除数を要求する。整数性を外部判定へ任せず、不正な証拠を拒否する。',
 'rqsh':'正の年番号と、その同じ年を4・100・400で割った商・余りの証拠が全て有効である。異なる年の証拠や0年を混ぜない。',
 'rqsi':'rqshを満たし、4での余りが0、かつ100での余りが非0または400での余りが0である。正の年番号についてのグレゴリオ閏年規則。',
 'rqsj':'rqshで年の証拠を検査し、月番号と日番号がグレゴリオ暦の月長規則を満たす。2月29日はrqsiを必要とし、無効な年証拠を平年として受理しない。月日番号の非整数・0・負・範囲外も拒否する。',
 'rqsk':'同じ年番号の証拠でrqsjによる月日有効性とrqsdによる暦内の一意な年・月・日割当を結ぶ。暦の歴史的な同定や絶対時刻をこの条件だけで主張しない。',
 'hzlo':'日付行と脚注が共有する年番号1784・月番号9・日番号13と30について、同じ32進の商余り証拠を使い、各文脈の期間割当とグレゴリオ規則上の有効性を結ぶ追加条件。原文の暦全体がグレゴリオ暦であるという同定ではなく、既存本文の主張としては追加しない。',
}


def digits(value):
    assert type(value) is int and value>=0
    result=[]
    while value:result.append(value%32);value//=32
    return list(reversed(result or [0]))


def seq(values):return 'l[b]['+' '.join(num(v) for v in values)+']'


def certificate(year):
    result=[digits(year)]
    for divisor in (4,100,400):result.extend(map(digits,divmod(year,divisor)))
    return result


def additions():
    zero=num(0);one=num(1);truth='e['+zero+']['+zero+']'
    text='d rqse[digits j[b]] c['+conjunction(['u[e[d[v digits]]['+zero+']]',
        'q[v digits]['+truth+'][i[valid c digit b][w[v valid][a['+seq(range(32))+'][v digit][v digit]]]]'])+'].'
    text+='d rqsf[digits j[b]] b[q[v digits]['+zero+'][i[value b digit b][k ha[k hb[v value '+num(32)+'] v digit]]]].'
    text+='d rqsg[value j[b] divisor j[b] quotient j[b] remainder j[b]] c['+conjunction([
        'k rqse[v '+n+']' for n in ('value','divisor','quotient','remainder')]+[
        'k hc['+zero+' k rqsf[v divisor]]',
        'e[k rqsf[v value]][k ha[k hb[k rqsf[v divisor] k rqsf[v quotient]] k rqsf[v remainder]]]',
        'k hc[k rqsf[v remainder] k rqsf[v divisor]]'])+'].'
    text+='d rqsh['+PARAMS+'] c['+conjunction([
        'k hc['+zero+' k rqsf[v year]]',
        *('k rqsg[v year '+seq(digits(divisor))+' v '+q+' v '+r+']' for divisor,q,r in (
            (4,'qfour','rfour'),(100,'qhundred','rhundred'),(400,'qfourhundred','rfourhundred')))])+'].'
    leap='w[e[k rqsf[v rfour]]['+zero+']][x[u[e[k rqsf[v rhundred]]['+zero+']]][e[k rqsf[v rfourhundred]]['+zero+']]]'
    text+='d rqsi['+PARAMS+'] c[w[k rqsh['+ARGS+']]['+leap+']].'
    def member(values,item):
        return 'q['+seq(values)+'][u['+truth+']][i[found c number b][x[v found][e[v number][v '+item+']]]]'
    short='w['+member((4,6,9,11),'month')+'][k hc[v day '+num(31)+']]'
    feb='w[e[v month]['+num(2)+']][x[k hc[v day '+num(29)+']][w[e[v day]['+num(29)+']][k rqsi['+ARGS+']]]]'
    text+='d rqsj['+PARAMS+' month b day b] c['+conjunction([
        'k rqsh['+ARGS+']',
        'k rqse[l[b][v day]]','k hc['+zero+' v day]',
        'x['+member((1,3,5,7,8,10,12),'month')+'][x['+short+']['+feb+']]'])+'].'
    text+='d rqsk[calendar a yearperiod a monthperiod a dayperiod a yearlabel b monthlabel b daylabel b context d years h[a a b d] c months h[a a a b d] c days h[a a a b d] c '+PARAMS+'] c['+conjunction([
        'e[v yearlabel][k rqsf[v year]]','k rqsj['+ARGS+' v monthlabel v daylabel]',
        'k rqsd[v calendar v yearperiod v monthperiod v dayperiod v yearlabel v monthlabel v daylabel v context v years v months v days]'])+'].'
    proof=' '.join(seq(ds) for ds in certificate(1784))
    calls=[]
    for day,period,context in ((30,'hzjh','hziz'),(13,'hzki','hzjl'),(30,'hzjh','hzjl')):
        calls.append('k rqsk[k hzix[] k hzjf[] k hzjg[] k '+period+'[] '+num(1784)+' '+num(9)+' '+num(day)+' k '+context+'[] p hzir p hzlm p hzln '+proof+']')
    text+='d hzlo[] c['+conjunction(calls)+'].'
    return text


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document);assert not set(MEANINGS)&set(cat.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+additions());doc['statements']=statements
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqse','rqsf','rqsg','rqsh','rqsi','rqsj','rqsk'])
    basis=dict(status='checked_gregorian_numeric_rules_not_historical_identification',document=FULL,library=LIBRARY,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},
        limitations=[
            '既存の有理加算ha・乗算hb・比較hcと有限列演算を使用する。整数・剰余・閏年を返す新しい基本関係を追加しない。',
            '自然数を32進数字列として与え、その全桁と商余りの等式をNoemaで検査する。証拠の生成と検査は別であり、生成器の誤りを無条件には信用しない。',
            '正の年番号にグレゴリオ規則を適用する。0年・紀元前年の表記規約、改暦時の欠番、地方ごとの導入日、天文学的時刻への換算は含まない。',
            '数値上有効な年月日であっても、その場所で歴史上使用された暦と同定したことにはならない。原文の暦についての未確認事項は継承する。',
            'rqskは月日の有効性と期間への割当の整合条件である。与えられた割当の網羅性・時間順序・物理的な日境界まで定義しない。',
            '既存23文と全宣言・意味規約を保存する。hzloを新たな原文主張として追加せず、原文対応範囲と意味確認済み単位は増やさない。',
        ])
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/labeled-dates-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Gregorian numeric rules composed with checked base-32 certificates')


if __name__=='__main__':main()
