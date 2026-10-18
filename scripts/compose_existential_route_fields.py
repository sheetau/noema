"""Quantify route-field witnesses per recipient, preserving native validation."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_existential_dissemination import ROUTE,SHARED,EXISTENTIAL
from scripts.compose_qualitative_thinkers import QUALITATIVE,FIELDS,PROVIDERS
from scripts.compose_shared_future_period import CONDITION

PARENT='examples/v016/kant-qualitative-receipt.noema'
PARENT_BASIS='data/qualitative-receipt-basis-v1.json'
FULL='examples/v016/kant-existential-route-fields.noema'
CORE='examples/v016/existential-route-fields-core.noema'
LIBRARY='examples/v016/existential-route-fields.noema'
BASIS='data/existential-route-fields-basis-v1.json'
METADATA=('sender','recipient','activity','point')
SPECS={'hzpb':ROUTE,'hzpc':SHARED,'hzpd':EXISTENTIAL,'hzq4':EXISTENTIAL+QUALITATIVE,
    'hzq5':FIELDS+[('subgroup','h[a d] c')],'rqt5':[('period','a')]+PROVIDERS,'rqt6':CONDITION+PROVIDERS}
SUCCESSORS=dict(zip(SPECS,('hzr3','hzr4','hzr5','hzr6','hzr7','rqt7','rqu2')))
SOURCE_PROVIDERS=[(n,t) for n,t in PROVIDERS if n not in METADATA]
MEANINGS={
 'hzr3':'同じ発信者・受け手・内容・期間・自己離脱について、段階の送信者・受け手・行為・時点を与える四関数と、経路・取得過程・前後点が存在する。各段階の提示・受領・時間順序・中継来歴と取得・持続は既存の本体で検査する。関数の存在だけでは伝達は成立しない。',
 'hzr4':'同じ発信者を中心とする人の範囲について、hzr3を満たす受け手の正確な範囲へ既存の広がり条件を適用する。四つの対応関数は各受け手の経路の内側で存在量化され、全受け手に一つの任意な対応表を指定する必要はない。',
 'hzr5':'一つの自己離脱と前後点を存在で指定し、全受け手へ共有してhzr4を要求する。経路の対応関数を受け手ごとに選ぶことによって、自己離脱まで別々に選び直すことはできない。',
 'hzr6':'同じ本人・初期機会の数値なしの独立判断への性向hzq3を、hzr5の自己離脱と伝播へ接続する。',
 'hzr7':'将来の各機会に、母集団の複数の人とその中の指定部分集団の人がhzr6を満たす内容。経路の対応関数は将来機会や人ごとに外部供給せず、実際の伝達を満たす存在として保持する。',
 'rqt7':'許可に使う同じ候補・期間から機会範囲と時間順序を作り、残る13供給関数を同じ候補へ適用してhzr7の内容族を構成する。',
 'rqu2':'許可の条件とrqt7の内容族を既存rqtpで結ぶ。後見役の比較・期待背景・著者帰属の枠へ渡せる。受け手の性向記述は既存hzr2を使用できる。',
}
LIMITS=[
 '四関数は経路段階に必要な役割と時点の具体例であり、自然言語の単語を引く辞書ではない。提示・受領・行為の生起・時系列・来歴の関係と一致する値だけが条件を満たす。',
 '関数は全域関数として量化するが、経路に使う段階について既存本体が検査する。各受け手の具体例の関数が一致することや、経路段階ラベルが文書全体で唯一の通信記録であることは追加しない。',
 '関数と任意長の有限列を全探索する手続は提供しない。閉じた関数項と経路の具体例を既存の証人検証へ渡せる。成功は指定解釈内の存在を示すが、失敗は不存在の証明ではない。',
 '自己離脱の共有、正確な受け手範囲、存在する経路、取得・因果・持続を保持する。見つかった受け手だけで集団全体の広がりを近似して真とはしない。',
 '原文に適した公衆・発話・性向基準・期間・周囲・広がりの解釈は残る。本文34文・確認済み七単位を保持し、原文対応範囲は増やさない。',
]


def definitions(parent):
    lookup={d['name']:d for d in parent['declarations']}
    remove={name:{i for i,(n,t) in enumerate(fields) if n in METADATA} for name,fields in SPECS.items()}
    def rewrite(node):
        if isinstance(node,list):return [rewrite(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node['symbol'] in SUCCESSORS:
            old=node['symbol'];return dict(kind='call',symbol=SUCCESSORS[old],
                arguments=[rewrite(x) for i,x in enumerate(node['arguments']) if i not in remove[old]])
        return {k:rewrite(v) for k,v in node.items()}
    result=[]
    for old,new in SUCCESSORS.items():
        declaration=deepcopy(lookup[old]);assert len(declaration['parameters'])==len(SPECS[old])
        bound=[p for i,p in enumerate(declaration['parameters']) if i in remove[old]]
        assert len(bound)==4
        declaration['parameters']=[p for i,p in enumerate(declaration['parameters']) if i not in remove[old]]
        declaration['name']=new;declaration['body']=rewrite(declaration['body'])
        if old=='hzpb':
            for p in reversed(bound):declaration['body']=dict(kind='exists',variable=p['name'],sort=p['sort'],body=declaration['body'])
        assert not _references(declaration)&set(SUCCESSORS)
        result.append(declaration)
    return result


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    size=len(doc['declarations']);doc['declarations']+=definitions(doc)
    doc=parse(format_graph(doc,'compact'))
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['rqu2','hzpy','hzr2','rqsx'])
    library=deepcopy(doc);library['statements']=[];library['declarations']=closure(doc,['hzr3','hzr2'])
    basis=dict(status='recipient_local_existential_route_fields',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Route roles and times quantified as local witnesses',flush=True)


if __name__=='__main__':main()
