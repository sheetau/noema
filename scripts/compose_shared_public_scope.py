"""Bind permission and future thinker membership to one referenced public."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_described_dissemination import declaration
from scripts.compose_thinking_disseminators import call as k
from scripts.compose_shared_future_period import CONDITION
from scripts.compose_existential_route_fields import SOURCE_PROVIDERS
from scripts.compose_focused_dissemination import PREDICATE

PARENT='examples/v016/kant-existential-route-fields.noema'
PARENT_BASIS='data/existential-route-fields-basis-v1.json'
FULL='examples/v016/kant-shared-public-scope.noema'
CORE='examples/v016/shared-public-scope-core.noema'
LIBRARY='examples/v016/shared-public-scope.noema'
BASIS='data/shared-public-scope-basis-v1.json'
PROVIDERS=[(n,t) for n,t in SOURCE_PROVIDERS if n!='members']
MEANINGS={
 'rqu3':'同じ公衆と参照文脈の想定読者h6tから、人物・評価機会を受ける構成員述語を作る。評価機会が変わっても参照文脈は固定する。人であること、許可、成功をこの範囲の選別条件にせず、既存の呼出側で別に検査する。',
 'rqu4':'自由の許可条件と将来の予測に同じ公衆・参照文脈を使う。rqu3から構成員の供給関数を内部で作り、残る12供給関数とともにrqu2へ渡す。後見役の対象集団、発信者中心の受け手範囲、規範の出所、候補内の個人の変化は同一化しない。',
}
LIMITS=[
 '公衆を同じ参照文脈の想定読者範囲として扱う、既存hznaの読みを引き継ぐ。どの集団にも同じ構成員固定を要求する一般文法規則ではなく、この条件付き予測の接続である。',
 '予測の各機会で該当する人は交替できる。固定するのは公衆の参照範囲であり、独立判断・自己離脱・伝播の真偽や該当者ではない。加入・離脱を含む動的な公衆の読みは別途必要である。',
 'h6tの範囲は許可された人、実際の受領者、変化した人から逆算しない。人でない個体が範囲に含まれる場合も黙って除外せず、既存の適格性検査へ渡す。',
 '公衆個体と公的発信の宛先である読者世界、後見役が担当する大衆、発信者の周囲は区別する。同じ対象であるという別の根拠なしに同一化しない。',
 '残る12供給関数と公衆・参照文脈自体の適切な解釈、原文の段落全体の意味確認は未完。既存34文・七つの意味確認と原文対応範囲を保持する。',
]


def definitions():
    text=declaration('rqu3',[('audience','a'),('reference','d')],'h[a d] c',
        'i[person a point d]['+k('h6t','v audience','v person','v reference')+']')
    supplied={n:'v '+n for n,t in PROVIDERS}
    supplied['members']='i[branch d]['+k('rqu3','v permissionaudience','v permissionreference')+']'
    text+=declaration('rqu4',CONDITION+PROVIDERS,'h['+PREDICATE+'] e',
        k('rqu2',*('v '+n for n,t in CONDITION),*(supplied[n] for n,t in SOURCE_PROVIDERS)))
    return text


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['rqu4','hzpy','hzr2','rqsx'])
    library=deepcopy(doc);library['statements']=[]
    library['declarations']=closure(doc,['rqu3','hzp7','rqti','rqtj','rqtw','rqtx'])
    basis=dict(status='permission_and_prediction_share_referenced_public',document=FULL,parent=PARENT,
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
    print('Shared referenced public connected to conditional prediction',flush=True)


if __name__=='__main__':main()
