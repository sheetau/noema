"""Connect thought items to typed, unevaluated Noema message descriptions."""
from copy import deepcopy
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_calendar_dateline import conjunction

PARENT='examples/v016/kant-thought-correspondence.noema'
PARENT_BASIS='data/thought-correspondence-basis-v1.json'
FULL='examples/v016/kant-described-thoughts.noema'
LIBRARY='examples/v016/described-thoughts.noema'
BASIS='data/described-thoughts-basis-v1.json'
ANNOTATIONS='data/described-thoughts-identifiers-v1.json'
DESCRIBES='h[a a d] i[f]'
CRITERION='h[i[f] i[f] a d] c'
MEANINGS={
 'rqrz':'同じ型の二つの発話記述が構文として同一であるという保守的な対応基準。束縛変数名は正規化される。発話の内容を実行せず、別名展開や任意の意味同値を推定しない。論点と状況は共通の基準インターフェースのために受け取る。',
 'rqsa':'同じ論点・状況で二内容項目の発話記述を取り出し、その同じ論点・状況の記述比較基準に渡す。項目そのものの同一性を要求しない。',
 'rqsb':'比較領域の各論点で、どちらかの文献が述べる項目同士について、従来の項目対応関係とrqsaによる記述比較の真偽が一致することを要求する。比較領域外・非帰属項目には同値を課さない。',
 'rqsc':'rqsaによる記述比較を項目間の対応関係としてrqryへ渡し、論点ごとの一致の正確な範囲を定める。渡す基準がrqrzの場合だけ構文同一性を用い、一般には明示した基準に従う。',
 'hzlj':'現在の論説と先の回答について、同じ状況のhzlf・hzlh・hzliと、与えた記述対応基準の整合条件rqsbを述べる。これは条件であり、全状況で成立すると自動には主張しない。',
 'hzlk':'現在の論説と先の回答の一致範囲を、同じ状況の論点・所属・帰属と明示した発話記述・対応基準から構成する。従来hzkvとの同値には、同じ状況でhzljが成立することが必要。',
 'hzll':'発話記述とその比較基準を明示して、偶発的な過程が二文献の思想をどこまで一致させうるかを問う。比較・因果寄与・偶発性を同じ状況で結ぶ。候補の実際の成立や成功を断言しない。',
}


def additions():
    text='d rqrz[left i[f] right i[f] aspect a scene d] c[e[v left][v right]].'
    common='describes '+DESCRIBES+' criterion '+CRITERION
    text+='d rqsa[left a right a aspect a scene d '+common+'] c[c[v criterion][c[v describes][v left v aspect v scene] c[v describes][v right v aspect v scene] v aspect v scene]].'
    params='first a second a scene d domain h[a d] c attributed h[a a a d] c matches h[a a a d] c '+common
    def relevant(item):return 'x[c[v attributed][v first v aspect v '+item+' v scene]][c[v attributed][v second v aspect v '+item+' v scene]]'
    text+='d rqsb['+params+'] c[f aspect a[y[c[v domain][v aspect v scene]][f left a[y['+relevant('left')+'][f right a[y['+relevant('right')+'][z[c[v matches][v left v right v aspect v scene]][k rqsa[v left v right v aspect v scene v describes v criterion]]]]]]]]].'
    text+='d rqsc[first a second a extent a scene d domain h[a d] c includes h[a a d] c attributed h[a a a d] c '+common+'] c[k rqry[v first v second v extent v scene v domain v includes v attributed i[left a right a aspect a at d][k rqsa[v left v right v aspect v at v describes v criterion]]]].'
    text+='d hzlj[scene d '+common+'] c[k rqsb[k hzik[] k hzjn[] v scene p hzlf p hzlh p hzli v describes v criterion]].'
    text+='d hzlk[extent a scene d '+common+'] c[k rqsc[k hzik[] k hzjn[] v extent v scene p hzlf p hzlg p hzlh v describes v criterion]].'
    text+='d hzll['+common+'] g[a][k rqrt[k hzjl[] p hzku i[extent a scene d][k rqru[k hzik[] k hzjn[] v extent v scene p hzkw p hzkx i[first a second a scope a at d][k rqsc[v first v second v scope v at p hzlf p hzlg p hzlh v describes v criterion]] p dg]]]].'
    return text


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document);assert not set(MEANINGS)&set(cat.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+additions());doc['statements']=statements
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqrz','rqsa','rqsb','rqsc'])
    basis=dict(status='typed_message_description_comparison_interface',document=FULL,library=LIBRARY,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},
        interfaces=dict(describes='内容項目・論点・状況から、閉じた型付きNoema発話の記述を返す。項目の真理を返さず、未登録項目へ既定の記述を補わない。実際の文献への忠実な帰属は別途説明を要する。',
            criterion='二つの発話記述・論点・状況を受ける対応条件。rqrzは内容を実行しない構文同一性の基準。任意の外部基準について未評価性や意味の正しさを自動保証しない。'),
        limitations=[
            '発話型fは主張・真偽を問う質問・指示を保持できる。答えの対象型を持つg[a]等の問いをfへ変換して収める規則はなく、それらの内容項目には別の型付き接続が必要。',
            '構文同一性は意味同値の完全な基準ではない。同じ意味の別名や別構文もrqrzでは不一致となりうる。比較の失敗から思想の積極的な対立は導かない。',
            '引用内の否定・量化・条件・対象・発話の種類は構造として保持し、同じ状況での真偽が等しいだけでは同一化しない。',
            'hzljは与えた対応基準と従来の対応関係の整合条件。条件を定義しただけではカント二文献について条件が成立したとは扱わない。',
            'hzllは基準を明示した質問の接続先であり、既存hzld・提示文hzleを無条件に置換しない。実文献の内容項目の記述、比較基準、原文との意味一致は未完。',
            '既存23文と全宣言・意味規約を保存する。新しい基本関係は追加せず、七つの合成定義を加える。原文対応範囲と意味確認済み単位は増やさない。',
        ])
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/thought-correspondence-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Typed thought descriptions connected without executing their contents')


if __name__=='__main__':main()
