"""Compose a nonfactive comparison of civic permission and mental opportunity."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_collective_office import ROOT,SOURCE as PARENT
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,op,both,quant,v
from scripts.compose_restricted_utterance import primitive
from scripts.compose_qualified_utterance import closure
from scripts.compose_described_norms import DESCRIPTION,RULE
from scripts.compose_policy_recognition import ALTERNATIVES

LIBRARY='examples/v016/option-inclusion.noema'
SOURCE='examples/v016/kant-apparent-liberty.noema'
CORE='examples/v016/apparent-liberty-core.noema'
BASIS='data/apparent-liberty-basis-v1.json'
FIELDS=[('people','h[a] c'),('activities','h[a a] c'),('first','h[a a d] c'),('second','h[a a d] c'),('context','d')]
FIELDS_TEXT=' '.join(n+' '+t for n,t in FIELDS)
TRUE='e[n p a b][n p a b]'


def definitions():
    scope=both(app(v('people'),v('person')),app(v('activities'),v('person'),v('activity')))
    first=app(v('first'),v('person'),v('activity'),v('context'))
    second=app(v('second'),v('person'),v('activity'),v('context'))
    text=definition('rwu',FIELDS_TEXT,quant('f','person','a',quant('f','activity','a',op('y',both(scope,first),second))))
    text+=definition('rwv',FIELDS_TEXT,both(k('rwu',*[v(n) for n,t in FIELDS]),
        quant('g','person','a',quant('g','activity','a',both(scope,second,op('u',first))))))
    return text


PROVIDERS=[('people','h[a] c'),('civilactivities','h[a a] c'),('mentalactivities','h[a a] c'),
    ('higher','h[d] d'),('lower','h[d] d'),('source','h[d] a'),('role','h[a a] a'),('target','h[a] '+DESCRIPTION),
    ('required',RULE),('allowed',RULE),('goal','h[a a] e'),('available','h[a a d] c'),
    ('prospects','h[a a d d] c'),('evaluated','h[a a d d] c'),('assessor','h[] a'),
    ('alternatives',ALTERNATIVES),('node','h[] a'),('scope','h[] a')]


def additions():
    text=''.join(primitive('iac'+n,t) for n,t in PROVIDERS)
    text+='r iacreport[a a i d[e] a d] c.'
    for side in ('higher','lower'):
        point=k('iac'+side,v('view'))
        text+=definition('iac'+side+'civil','person a activity a view d',k('rdm',k('iacsource',point),v('person'),
            k('iacrole',v('person'),v('activity')),v('activity'),k('iactarget',v('activity')),TRUE,point,'p iacrequired','p iacallowed'))
        text+=definition('iac'+side+'mental','person a activity a view d',k('xd',v('person'),k('iacgoal',v('person'),v('activity')),
            point,'p iacavailable','p iacprospects','p iacevaluated'))
    for label in ('civil','mental'):
        text+=definition('iac'+label+'gain','view d',k('rwv','p iacpeople','p iac'+label+'activities',
            'p iaclower'+label,'p iachigher'+label,v('view')))
    text+=definition('iacadvantage','','b view['+both(k('iaccivilgain',v('view')),k('iacmentalgain',v('view')))+']','e')
    text+=definition('iacappearance','','b anchor['+both(k('iaccivilgain',v('anchor')),
        k('rro',k('iacassessor'),'r c[k iacadvantage[]]',v('anchor'),'p iacalternatives'))+']','e')
    text+=definition('iacattribution','',k('iacreport',k('iacnode'),k('wa'),'r d[k iacappearance[]]',k('iacscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=parse('p:'+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iacattribution[]].')
    doc['statements']=parent['statements']+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='partial_nonfactive_inclusion_reading_not_freedom_equivalence',parent=PARENT,document=SOURCE,
        definitions={
            'rwu':'固定した人と活動の範囲で、第一側で可能な選択が全て第二側でも可能である。範囲外の選択は比較しない。空範囲は真。',
            'rwv':'rwuに加え、同じ範囲内で第二側だけの選択が存在する。単なる件数増加、選択肢の交換、同じ範囲の自己比較は十分でない。',
            'iachighercivil/iaclowercivil':'同じ本人・活動・役割・行為記述に対する積極的許可と反対要求の不在rdmを、比較する二状況の規範源へ照合する。',
            'iachighermental/iaclowermental':'同じ本人・目標の内容について、比較する二状況で実際のxdを用いて達成方法を調べる。達成済みとはしない。',
            'iaccivilgain/iacmentalgain':'同じ人と各活動範囲を固定し、市民的許可または精神的活動の達成可能性が低い側から高い側へ真に包含拡大する。',
            'iacadvantage':'同じ比較視点で市民的許可と精神的活動の両方の包含拡大が成立するという内容。',
            'iacappearance':'基準視点で市民的許可の拡大があり、非空の見かけの候補視点全てで同じiacadvantageが成立する。現在の精神的優位は要求しない。',
            'iacattribution':'同じ著者・原文箇所・範囲・文脈に候補内容を帰属し、内容自体は実行しない。'},
        input_contracts={
            'people/activities':'比較する人と活動を一度選び両側・全候補視点で保持する。活動を実行したか、許可されたかを選別条件にしない。',
            'higher/lower':'比較視点ごとに同じ二制度条件を表す状況を返す。候補によって別の制度へすり替えない。',
            'goal':'同じ本人・精神的活動の目標内容。候補視点ごとに成功しやすい別目標へ変更しない。',
            'alternatives':'指定した評価側・同じ内容記述・基準視点において、有利に見える根拠となる候補視点。信念一般や事実とは同一視しない。評価側は原文に明示されないため名前を補わない。'},
        limitations=[
            '自由の程度を許可選択肢の真包含、精神の利益を達成可能な活動の真包含と読む操作的候補。数値尺度・重み・質的な利益・市民的自由や精神の自由の全意味を定義したものではない。',
            '一部を失って別の重要な選択が増える場合は比較不能になり得る。原文が必ず包含順序を意味するとは主張しない。',
            'xdが偽であることを、評価が完備した不可能xgと同一視しない。これは達成方法の存在集合の比較であり、全ての未達成が不可能だという判定ではない。',
            '有利に見えることを非空の候補での一致として表す。知覚過程、確信度、根拠の正当性、心理的判断の全意味は未完。',
            '二側の共変動であり、市民的自由が精神の自由を因果的に増大させる証明ではない。実際の障壁、より少ない自由との逆の比較、後続の展開は未接続。',
            '母集団・活動分類・制度・目標の原文との適合、意味の全体確認は未完。既存の定義を再利用するが名前の付与だけで語義を説明済みと数えない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
