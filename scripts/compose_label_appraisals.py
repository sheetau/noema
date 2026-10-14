"""Assess a label through scoped hypothetical uses without asserting a current use."""
from copy import deepcopy
import json
from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/kant-described-labels.noema'
SETTINGS=[('people','h[a a d] c'),('cases','h[a d d] c'),('uses','h[a a a d] c'),('deficient','h[a a a d] c')]
ASSESS=[('label','a'),('context','d')]+SETTINGS
ROOTS=['rnu','rnv','rnw']


def definitions():
    person=app(v('people'),v('label'),v('person'),v('context'))
    scene=app(v('cases'),v('label'),v('context'),v('point'))
    used=app(v('uses'),v('person'),v('activity'),v('label'),v('point'))
    deficient=app(v('deficient'),v('person'),v('activity'),v('label'),v('point'))
    nonempty=both(quant('g','person','a',person),quant('g','point','d',scene))
    alluses=quant('f','person','a',quant('f','point','d',quant('f','activity','a',op('y',both(person,scene,used),deficient))))
    witness=quant('g','person','a',quant('g','point','d',quant('g','activity','a',both(person,scene,used))))
    text=definition('rnu',params(ASSESS),both(nonempty,alluses))
    text+=definition('rnv',params(ASSESS),both(k('rnu',*args(ASSESS)),witness))
    text+=definition('rnw',params(SETTINGS),'i[label a][b context['+k('rnv',*args(ASSESS))+']]', 'h[a] e')
    return text

MEANINGS={
    'rnu':'同じ名称と評価文脈で固定した非空の人物範囲・仮定状況範囲について、その名称を使う全ての行為が、同じ人物・行為・名称・状況で指定の不足条件を満たす。現在の使用を要求しない。',
    'rnv':'rnuに加え、指定した範囲に少なくとも一つの名称使用の仮定例がある。前件のない空虚な条件成立を、名称の評価根拠にしない。',
    'rnw':'rnvを名称から評価内容への性質として構成する。同じ評価内容を引用し著者の主張への帰属候補として使えるが、構成だけでは著者帰属や内容の真理を断言しない。',
}
LIMITS=[
    '仮定状況での名称の自己適用と、同じ行為で裁量の資格を欠く評価を結ぶ接続例を使う。名称を拒む人物が現実にその立場を取ったことを前提にしない。',
    '人物範囲と仮定状況範囲は、名称と外側の評価文脈に固定する。使用と不足を別人・別行為・別状況から継ぎ合わせない。反例となる使用が一つあればrnuもrnvも不成立になる。',
    '範囲は明示した解釈条件であり、現実の全話者・全慣習・全可能世界を有限例で確認したとはしない。通常性・典型性・確率的傾向や反事実条件文の全理論ではない。',
    'rnvの仮定例の存在は現在の出来事の存在ではない。rnuの空虚な成立、仮定例のある評価、現在の名称使用を別々に保持する。',
    '著者帰属には閉じた評価内容を既存の候補選択rj6・hzd2へ渡す。モデル内で帰属の区別を検査するものであり、カントがこの形式的解釈を明示したという主張ではない。',
    '自己適用の関係を評価内容の引用へ埋め込む際、既知の対象記述への特殊化で個体の脱引用を除く。未知の帰属や意味規約は偽で補わない。',
    '傲慢という語の一般的な意味、語用慣習との照合、評価の論証、寛容に含まれる不賛同・抑制、称賛と解放、全文の意味確認は未完。原始記号と著者主張は追加しない。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-described-labels-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-label-appraisals-basis-v1',document='examples/v014/kant-label-appraisals.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(previous,extra,stem):
    text,basis=source_composed();doc=parse(text)
    roots=[d['name'] for d in parse((ROOT/('examples/v014/'+previous+'.noema')).read_text(encoding='utf-8'))['declarations']]+ROOTS+extra
    selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected('described-labels',['rj6'],'label-appraisals')
def core_composed():return projected('described-labels-core',['hzd2'],'label-appraisals-core')
BUILDERS=((generic_composed,'label-appraisals'),(source_composed,'kant-label-appraisals'),(core_composed,'label-appraisals-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored label appraisals differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
