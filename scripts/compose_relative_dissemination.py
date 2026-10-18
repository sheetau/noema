"""Separate origin-relative recipients from the independently intended audience."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_thinking_disseminators import FUTURE,THINKING,call,variable,conjunction,declaration

PARENT='examples/v016/kant-thinking-disseminators.noema'
PARENT_BASIS='data/thinking-disseminators-basis-v1.json'
FULL='examples/v016/kant-relative-dissemination.noema'
CORE='examples/v016/relative-dissemination-core.noema'
LIBRARY='examples/v016/relative-recipients.noema'
BASIS='data/relative-dissemination-basis-v1.json'
SCOPED=FUTURE[1:]+[('scope','h[a a d] c')]
MEANINGS={
 'rqth':'同じ中心人物・基準文脈で指定された関係を持つ、その中心とは異なる対象。関係の向きと文脈を保存し、逆向き・推移的なつながりや実際の伝達から所属を補わない。人であることは呼出側で別に確認する。',
 'hzok':'hzofの想定読者を、同じ発信者・参照文脈からrqthで取り出す範囲へ一般化する。その全員が人であることを要求し、同じ自己離脱・最初の発信・将来取得・持続を満たす範囲を内部で作る。未達の相手も母集団に残し、原点の本人を受け手に数えない。',
 'hzol':'同じ発信者の初期評価点での独立判断への応答傾向hzhhと、その人を中心とするhzokを結ぶ。発信者を交換しても範囲の中心を以前の人のままにせず、指定関係と基準文脈は保持する。',
 'hzom':'異なるかどうかを別に検査する二人について、同じ基準文脈で、一方が他方を情報源・援助の供給元として利用できるsaが少なくとも一方向で成立する。人であることを両側に要求する。実際の利用・受領・同意、物理的な近さや親密さは含まない。社会的に接点を持ちうる範囲を説明する一例であり、周囲一般との同義規約ではない。',
}
LIMITS=[
 '中心人物と伝達の最初の発信者は同じ引数である。中心・基準文脈・関係から範囲を作り、実際の受領者や性向を取得した人だけを外部から選んだ集合を使わない。',
 'scopeはNoemaで定義できる関数であり、周囲という未説明の新しい基本語ではない。文脈上の社会的・空間的な関係を別々に定義して渡せる。hzomは既存saから作る具体例で、原文の唯一の読みには固定しない。',
 '一方向の関係には向きがある。hzomが対称なのは二方向の選言を明示したためであり、一般のscopeへ対称性・推移性・相互理解を加えない。',
 '想定読者h6t・周囲の人・実際の受領者は異なる範囲である。以前のhzof/hzogとの整合性は、指定した相対範囲が同じ想定読者に一致し、中心本人を含まない場合だけ検査する。',
 '伝播先の範囲は参照文脈で固定する。途中の加入・離脱、接近や関係形成の過程、原文に適した範囲と広がりの基準、比喩・談話・様相・著者帰属は引き続き説明が必要。',
 '既存32文と全意味規約・七単位の確認を保存する。既存の伝播範囲の構造的な修正候補であり、新たな著者主張や意味確認済み単位を加算しない。',
]


def definitions(parent):
    # Generalize only the audience binding of the saved future-distribution
    # definition. Its achievement, temporal, route and acquisition bodies stay.
    original=next(d for d in parent['declarations'] if d['name']=='hzof')
    new=deepcopy(original);new['name']='hzok'
    audience,reference,origin=[p['name'] for p in new['parameters'][:3]]
    new['parameters']=new['parameters'][1:]+[dict(name='scope',sort={'kind':'function','parameters':['individual','individual','situation'],'result':'truth'})]
    relative=parse('p:d rqth[origin a target a reference d relation h[a a d] c] c['
        'w[u[e[v origin][v target]]][c[v relation][v origin v target v reference]]].')['declarations'][0]
    adapter=dict(kind='lambda',parameters=[dict(name=n,sort=t) for n,t in
        (('center','individual'),('person','individual'),('context','situation'))],
        body=dict(kind='call',symbol='rqth',arguments=[dict(kind='variable',name=n) for n in ('center','person','context','scope')]))
    def rewrite(node):
        if isinstance(node,list):return [rewrite(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='variable' and node['name']==audience:return dict(kind='variable',name=origin)
        if node.get('kind')=='function_ref' and node['symbol']=='h6t':return deepcopy(adapter)
        if node.get('kind')=='call' and node['symbol']=='h6t':
            return dict(kind='apply',function=deepcopy(adapter),arguments=rewrite(node['arguments']))
        return {k:rewrite(v) for k,v in node.items()}
    new['body']=rewrite(new['body'])
    extra=declaration('hzol',SCOPED+THINKING,conjunction(
        call('hzhh',variable('origin'),variable('initial'),*(variable(n) for n,t in THINKING)),
        call('hzok',*(variable(n) for n,t in SCOPED))))
    extra+='d hzom[origin a target a reference d] c[w[k aa[v origin]][w[k aa[v target]][x[k sa[v origin v target v reference]][k sa[v target v origin v reference]]]]].'
    context=deepcopy(parent);context['statements']=[];context['declarations']+=[relative,new]
    return [relative,new,*parse(format_graph(context,'compact')+extra)['declarations'][-2:]]


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    size=len(doc['declarations']);doc['declarations']+=definitions(doc)
    doc=parse(format_graph(doc,'compact'))
    core=deepcopy(doc);core['statements']=[]
    core['declarations']=closure(doc,['hzol','hzom','hzog','hzny','rqsx','rqsy'])
    library=deepcopy(core);library['declarations']=closure(doc,['rqth','hzom','rqsz','rqsw','rqsx','rqsy'])
    basis=dict(status='origin_relative_scope_separate_from_intended_audience',document=FULL,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        LIBRARY:format_graph(library,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Dissemination recipients bound to the same origin and reference context',flush=True)


if __name__=='__main__':main()
