"""Give a document a provisional role directed at a modal extent question."""
from copy import deepcopy
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_calendar_dateline import conjunction

PARENT='examples/v016/kant-counterfactual-withholding.noema'
PARENT_BASIS='data/counterfactual-withholding-basis-v1.json'
FULL='examples/v016/kant-exploratory-question.noema'
LIBRARY='examples/v016/exploratory-question.noema'
BASIS='data/exploratory-question-basis-v1.json'
ANNOTATIONS='data/exploratory-question-identifiers-v1.json'
PRIMITIVES={
 'hzku':('[d d] c',['評価文脈','可能性を検討する状況'],'この文脈で可能性を検討するために採る状況。実際に起きた状況、話者が信じる状況、確率標本と同一視しない。許容する可能性の種類と範囲は文脈の意味契約である。'),
 'hzkv':('[a a a d] c',['第一文献','第二文献','一致の範囲・程度','評価状況'],'二文献の思想・論旨の内容が、この範囲・程度で一致する。字面の一致、文献の同一性、真理や価値への評価とは区別する。範囲・程度は個体として指定し、数値尺度・最大値・一致率を補わない。比較基準の構成は未完。'),
 'hzkw':('[a d] c',['成立過程','評価状況'],'この文脈でその成立過程が偶発的と捉えられる。単なる原因の不明、確率的独立、意図ある人格としての偶然とは同一視しない。意図的な調整や必然的な一致と区別するための偶発性の基準は意味契約として残る。'),
 'hzkx':('[a a a a d] c',['成立過程','第一文献','第二文献','一致の範囲・程度','評価状況'],'この過程が、二文献の内容の指定範囲・程度の一致を生じさせることに因果的に寄与する。同じ過程・文献・一致範囲を結び、単なる共存と区別する。唯一原因性や一般的な認知機構は補わない。'),
 'hzky':('[a i[g[a]] d] c',['提示上の位置付け','範囲・程度を答えとする問いの記述','評価文脈'],'この位置付けは、記述された問いを検討するための試みとしての提示である。問いの解決、候補答えの存在・唯一性、実験の成功や結果の真理は含意しない。'),
 'hzkz':('[a a a d] c',['提示者','文献','提示上の位置付け','評価文脈'],'この提示者が、この箇所・文脈で当該文献に与える提示上の位置付け。文献のあらゆる用途や価値、他の人が与える位置付けまで列挙する関係ではない。'),
 'hzla':('[] a',[],'この脚注で現在の回答に与える提示上の位置付けの局所参照。その内容は本文でhzkyと問いの記述へ結ぶ。'),
 'hzlb':('[a a d d] c',['提示者','文献','基準時点','評価文脈'],'この人物が、この基準時点の文脈で当該文献をここに提示したものとして置いておくことを容認する態度を表す。法的な許可、実際の刊行、成功、文献内容への確信とは区別する。'),
}
MEANINGS={
 'rqrt':'指定文脈から検討可能な状況のいずれかで指定条件を満たす範囲・程度を、候補答えとして求める質問を構成する。候補の存在・最大値・唯一性や現実での条件成立を主張しない。',
 'rqru':'同じ状況に成立する過程が偶発的とされ、その過程が同じ二文献の指定範囲・程度の一致に因果的に寄与し、その一致も同じ状況で成立する。異なる過程・状況・文献・範囲の関係を組み合わせない。',
 'rqrv':'提示者がこの文脈で当該文献に指定の位置付けを与え、与えている全ての位置付けがそれと同じである。空の指定を受け入れず、文献の全目的や他者の位置付けを制約しない。',
 'hzlc':'指定状況で、現在の論説hzikと先の回答hzjnの内容について、指定範囲・程度の一致が偶発的な過程の影響により成立するという条件。実際の成立をこの定義だけでは断言しない。',
 'hzld':'脚注の文脈から、偶然が二つの回答の思想の一致をどこまで生じさせうるかを問う質問。数値や一意な最大程度は与えず、範囲・程度の候補を求める。',
 'hzle':'著者waが現在の論説hzikを今ここに置くことを容認し、この箇所では同じ問いhzldを検討する試みという位置付けだけを与える。問いは記述として接続し、答えや現実の一致を肯定しない。',
}
LIMITS=[
 'magを、現在の回答をここに置くことを容認する控えめな態度として読む。可能性の推測や規範的許可などの全語義を解決したものではない。',
 'nurはこの箇所で著者が与える提示上の位置付けにかけ、文献の全目的や価値を一つに限定しない。文脈的な限定範囲の読解は全体の意味確認で再検討する。',
 'wiefernは可能な一致の範囲・程度を問う候補条件として構成する。尺度の順序、最大値、一意性、問いの語用論的な前提を補わない。思想の比較基準と偶発性の基礎説明は未完。',
 '同じ過程の偶発性・因果寄与・一致を組み合わせるが、偶然を未知の原因や統計的独立だけへ還元しない。可能な状況の選択も入力の意味契約である。',
 '問いを検討する試みとしての位置付けを述べる。実際の思想の一致、偶然による結果、実験の成功や答えの取得を主張しない。',
 '既存22文と全宣言・意味規約を保存する。脚注の全文章に部分草案が対応しても、周期・編集関係・暦・敬称・指示・反事実等の課題は残り、単位全体の意味確認には数えない。',
]


def additions():
    text=''.join('r '+n+sig+'.' for n,(sig,_,_) in PRIMITIVES.items())
    text+=('d rqrt[actual d possible h[d d] c target h[a d] c] g[a]['
        'j v[i[extent a][g candidate d[w[c[v possible][v actual v candidate]][c[v target][v extent v candidate]]]]]].')
    text+='d rqru[first a second a extent a context d chance h[a d] c causes h[a a a a d] c agrees h[a a a d] c occurs h[a d] c] c[g episode a['+conjunction([
        'c[v occurs][v episode v context]','c[v chance][v episode v context]',
        'c[v causes][v episode v first v second v extent v context]',
        'c[v agrees][v first v second v extent v context]',
    ])+']].'
    text+='d rqrv[person a document a role a context d assigns h[a a a d] c] c['+conjunction([
        'c[v assigns][v person v document v role v context]',
        'f other a[y[c[v assigns][v person v document v other v context]][e[v other][v role]]]',
    ])+'].'
    text+='d hzlc[extent a context d] c[k rqru[k hzik[] k hzjn[] v extent v context p hzkw p hzkx p hzkv p dg]].'
    text+='d hzld[] g[a][k rqrt[k hzjl[] p hzku p hzlc]].'
    text+='d hzle[] c['+conjunction([
        'k hzlb[k wa[] k hzik[] k hzjm[] k hzjl[]]',
        'k rqrv[k wa[] k hzik[] k hzla[] k hzjl[] p hzkz]',
        'k hzky[k hzla[] r[k hzld[]] k hzjl[]]',
    ])+'].'
    return text


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document)
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(cat.entries)
    old=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+additions()+'s[k hzle[]].');doc['statements']=old+doc['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqrt','rqru','rqrv'])
    primitives={}
    for d in doc['declarations'][size:]:
        if d['kind']=='primitive':
            _,args,meaning=PRIMITIVES[d['name']]
            primitives[d['name']]=dict(parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning)
    basis=dict(status='partial_provisional_presentation_and_modal_extent_question',document=FULL,library=LIBRARY,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/counterfactual-withholding-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Provisional presentation and modal extent question composed')


if __name__=='__main__':main()
