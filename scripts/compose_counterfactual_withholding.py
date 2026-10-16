"""Compose receipt by an anchor and a nonvacuous counterfactual withholding."""
from copy import deepcopy
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_calendar_dateline import conjunction

PARENT='examples/v016/kant-dated-reading.noema'
PARENT_BASIS='data/dated-reading-basis-v1.json'
FULL='examples/v016/kant-counterfactual-withholding.noema'
LIBRARY='examples/v016/counterfactual-withholding.noema'
BASIS='data/counterfactual-withholding-basis-v1.json'
ANNOTATIONS='data/counterfactual-withholding-identifiers-v1.json'
PRIMITIVES={
 'hzkm':('[d] a',['評価状況'],'その状況で基準時以前の事象を評価するために指定された時間的履歴枠。反事実の別経過には別の履歴解釈を許す。未指定の場合に実際の履歴を流用しない。'),
 'hzkn':('[d] d',['評価状況'],'その状況で過去の事象を評価する指定基準時点。異なる比較状況の時点を実際の基準時と自動的に同一視しない。'),
 'hzko':('[a i[h[d] c] d d] c',['視点となる人物','前提の状況条件記述','実際の評価状況','比較状況'],'この人物の視点で、この前提記述を仮に認める条件文を評価するために採用した比較状況。現実の時間的履歴や、単に前提が真となる全状況とは区別する。適切な比較の選択は意味契約で、最類似世界の一般理論をこの基本関係だけで与えない。'),
 'hzkp':('[a a a d] c',['差し控える対応','人物','提示を差し控える文献','評価状況'],'この対応において、この人物がこの文献を回答として提示することを差し控える。文献の破壊、他人への禁止、存在しない文献の物理的撤回を含意しない。執筆・送稿・公表のどの段階かは追加指定を要する。'),
 'hzkq':('[a a d] c',['影響を与える文献','結果となる対応','評価状況'],'この文献からの影響が、この対応が生じることに因果的に寄与する。単なる前後関係や同時成立だけでは満たさず、文献自体を意図ある人物として扱わない。影響の認知的機構や唯一原因性は含意しない。'),
}
MEANINGS={
 'rqrq':'taを満たす履歴に基準点が属し、その履歴の基準点以前（基準点を含む）のどこかで指定事象が成立する。無効な履歴では成立しないため、未成立条件rqrnを単に否定したものとは異なる。',
 'rqrr':'同じ受け手・文献・履歴枠・基準時・文脈で、基準時までに受領が成立することをrqrqで記述する。現在の所持や内容の理解は要求しない。',
 'rqrs':'実際の状況で前提が成立せず、採用する比較状況が少なくとも一つあり、その全てで前提と帰結が成立するという反事実の条件。空の選択や前提を満たさない比較を成功にしない。現実の帰結を主張せず、比較選択の妥当性は入力の意味契約に残る。',
 'hzkr':'指定状況の履歴枠・基準時の下で、脚注の同じ回答文献hzjnが著者waへ届いていること。実際の状況と反事実の状況で同じ受け手・文献を保持し、履歴の解釈は分ける。',
 'hzks':'指定状況に、著者waが現在の論説hzikの提示を差し控える対応が成立し、先の回答hzjnからの影響がその同じ対応に因果的に寄与する。単なる非提示や、別の文献を差し控えることでは満たさない。',
 'hzkt':'実際の脚注文脈の履歴・基準時を既存の未受領へ結び、先の回答と現在の論説を区別する。その回答が届いていれば、その影響で現在の回答を差し控えただろう、という選択された比較状況での読み。現実の差し控えを主張しない。',
}
LIMITS=[
 'sonstの前提を、直前の未受領に対する「先の回答が基準時までに届いていたなら」と読む。代名詞sieを先の回答、die gegenwärtigeを現在の論説hzikへ結ぶ。別解釈を排除した全体の意味確認ではない。',
 'zurükgehaltenを回答の提示を差し控えることへの影響として読む。執筆そのものを止めるか、送稿や公表を差し控えるかの具体的段階、因果機構は未確定。',
 '比較状況は前提記述・人物・実際の文脈へ結ぶ。選択範囲の妥当性、最類似世界や反可能条件の一般理論、実際の全過去の復元は未完。',
 '基準時までの受領と未受領の補集合関係は、有効な同一履歴・基準時・完全な事象解釈の下でのみ扱う。履歴が不正なら両方とも不成立になる。',
 '後続の試みとしての提示、偶然による思想の一致、控えめな可能表現は未記述。以前の周期・編集関係・暦・敬称等の制限も継承する。',
 '既存21文・全宣言・意味規約を保存し、反事実の一文を追加する。有限検査を原文単位全体の意味一致の証明にしない。',
]


def additions():
    text=''.join('r '+n+sig+'.' for n,(sig,_,_) in PRIMITIVES.items())
    text+='d rqrq[history h[d] c before h[d d] c anchor d occurred h[d] c] c['+conjunction([
        'k ta[v history v before]','c[v history][v anchor]',
        'g moment d['+conjunction(['c[v history][v moment]',
            'x[c[v before][v moment v anchor]][e[v moment][v anchor]]','c[v occurred][v moment]'])+']',
    ])+'].'
    text+=('d rqrr[person a item a frame a anchor d context d history h[a d d] c before h[d d d] c received h[a a d d] c] c['
        'k rqrq[i[moment d][c[v history][v frame v context v moment]] '
        'i[left d right d][c[v before][v left v right v context]] v anchor '
        'i[moment d][c[v received][v person v item v moment v context]]]].')
    text+='d rqrs[actual d antecedent h[d] c consequent h[d] c selects h[d d] c] c['+conjunction([
        'u[c[v antecedent][v actual]]','g candidate d[c[v selects][v actual v candidate]]',
        'f candidate d[y[c[v selects][v actual v candidate]][w[c[v antecedent][v candidate]][c[v consequent][v candidate]]]]',
    ])+'].'
    text+='d hzkr[context d] c[k rqrr[k wa[] k hzjn[] k hzkm[v context] k hzkn[v context] v context p h7q p ic p hzji]].'
    text+='d hzks[context d] c[g act a['+conjunction([
        'k dg[v act v context]','k hzkp[v act k wa[] k hzik[] v context]','k hzkq[k hzjn[] v act v context]',
    ])+']].'
    text+='d hzkt[] c['+conjunction([
        'u[e[k hzjn[]][k hzik[]]]',
        'k hzju[]',
        'e[k hzkm[k hzjl[]]][k hzjs[]]','e[k hzkn[k hzjl[]]][k hzjm[]]',
        'k rqrs[k hzjl[] p hzkr p hzks i[actual d candidate d][k hzko[k wa[] r[p hzkr] v actual v candidate]]]',
    ])+'].'
    return text


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document)
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(cat.entries)
    old=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+additions()+'s[k hzkt[]].');doc['statements']=old+doc['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqrn','rqrq','rqrr','rqrs'])
    primitives={}
    for d in doc['declarations'][size:]:
        if d['kind']=='primitive':
            _,args,meaning=PRIMITIVES[d['name']]
            primitives[d['name']]=dict(parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning)
    basis=dict(status='partial_nonvacuous_counterfactual_withholding',document=FULL,library=LIBRARY,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/dated-reading-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Positive receipt and counterfactual withholding composed')


if __name__=='__main__':main()
