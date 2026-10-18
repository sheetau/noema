"""Derive forecast opportunities from the same permission scenario period."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_described_dissemination import declaration
from scripts.compose_thinking_disseminators import call as k
from scripts.compose_existential_focus import BRANCH_FIELDS,FAMILY,PREDICATE
from scripts.compose_conditional_dissemination import FIELDS

PARENT='examples/v016/kant-attributed-focus.noema'
PARENT_BASIS='data/attributed-focus-basis-v1.json'
FULL='examples/v016/kant-shared-future-period.noema'
CORE='examples/v016/shared-future-period-core.noema'
LIBRARY='examples/v016/scenario-period-orders.noema'
BASIS='data/shared-future-period-basis-v1.json'
PROVIDERS=[(n,t) for n,t in BRANCH_FIELDS if n not in ('history','before')]
CONDITION=[('permission'+n,t) for n,t in FIELDS[:-1]]
MEANINGS={
 'rqtw':'期間枠と仮定候補から、その候補の期間内の時点をh7qで選ぶ関数を作る。別の期間候補や現実の文脈を代入しない。',
 'rqtx':'仮定候補を時間比較icの同じ文脈に固定し、二時点の順序関数を作る。候補を時点の一方へ置き換えない。',
 'rqty':'同じ期間枠から候補ごとの機会範囲rqtwと時間順序rqtxを作り、残る20供給関数とともにhzpsへ渡す。供給関数は同じ候補を受け、部分集団を見て範囲を変えない。存在する伝播内容と独立判断の定義を保持する。',
 'rqtz':'rqtpで使う許可の期間枠を、そのままrqtyの将来機会の範囲へ共有する。各候補の基準点は従来どおりoriginsから取得する。許可と予測の期間を別指定せず、期間内の基準点より後の機会だけを予測する枠を構成する。',
}
LIMITS=[
 '自由の許可期間と予測の機会範囲を共用する接続を追加する。一般のrqtp・hzpsを変更せず、異なる期間を明示する別の読みを文法から排除しない。',
 '同じ候補・期間枠を使う構造を固定するが、原文に具体的な始終日時が書かれているとはしない。期間の解釈と原文に適した長さは未指定のまま残る。',
 'rqtjとhzneが要求する非空の将来・整合した順序を保持する。期間を基準点一つへ縮めて空虚な予測を真にしない。',
 '公衆・伝達内容・評価場面・広がりなど残る20供給関数は原文の解釈を必要とする。全てを存在閉包した全文や、任意長の伝播の真理の証明ではない。',
 '既存34文と七単位の確認を保持する。新しい本文主張・原文対応範囲・意味確認済み単位は増やさない。',
]


def definitions():
    text=declaration('rqtw',[('frame','a'),('branch','d')],'h[d] c',
        'i[point d]['+k('h7q','v frame','v branch','v point')+']')
    text+=declaration('rqtx',[('branch','d')],'h[d d] c',
        'i[first d last d]['+k('ic','v first','v last','v branch')+']')
    supplied={n:'v '+n for n,t in PROVIDERS}
    supplied.update(history='i[branch d]['+k('rqtw','v period','v branch')+']',before='i[branch d]['+k('rqtx','v branch')+']')
    text+=declaration('rqty',[('period','a')]+PROVIDERS,FAMILY,k('hzps',*(supplied[n] for n,t in BRANCH_FIELDS)))
    text+=declaration('rqtz',CONDITION+PROVIDERS,'h['+PREDICATE+'] e',
        k('rqtp',*('v '+n for n,t in CONDITION),k('rqty','v permissionframe',*('v '+n for n,t in PROVIDERS))))
    return text


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['rqtz','hzpy','hzny','rqsx','rqtj'])
    library=deepcopy(doc);library['statements']=[];library['declarations']=closure(doc,['rqtw','rqtx','rqtj','hzne'])
    basis=dict(status='shared_permission_period_and_future_opportunities',document=FULL,parent=PARENT,
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
    print('Permission period shared with forecast opportunities',flush=True)


if __name__=='__main__':main()
