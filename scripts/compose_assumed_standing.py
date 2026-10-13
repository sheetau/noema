"""Compose an explicitly qualified reading of presumptuous intervention."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT,v,call as k,app,op,both
from scripts.compose_origin_clock import definition
from scripts.compose_situated_criticism import PREMISE,ALL,CONTEXT,params,args

PARENT='examples/v014/kant-situated-criticism.noema'
EVALUATION=[('standing','a'),('criteria','j[h[a a] e]'),('assumes','h[a a a d] c')]
PERSONAL=[('person','a')]+EVALUATION
PREMISE_FIELDS=[field for field in PREMISE if field[0]!='quality']+EVALUATION
ALL_FIELDS=[field for field in ALL if field[0]!='quality']+EVALUATION


def definitions():
    failed='u[t[c[v criterion][v person v standing]][v context]]'
    content='b context[q[v criteria][u[e[n p a b][n p a b]]][i[found c criterion h[a a] e][x[v found]['+failed+']]]]'
    text=definition('rfp','person a standing a criteria j[h[a a] e]',content,'e')
    text+=definition('rfq',params([('activity','a')]+PERSONAL),
        'b context['+both(app(v('assumes'),v('person'),v('activity'),v('standing'),v('context')),
            op('t',k('rfp',v('person'),v('standing'),v('criteria')),v('context')))+']','e')
    text+=definition('rfr',params(PERSONAL),'i[activity a]['+k('rfq',v('activity'),*args(PERSONAL))+']','h[a] e')
    return text


MEANINGS={
    'rfp':'同じ人が同じ発言上の立場を取るために明示した条件列について、少なくとも一つの条件が当該文脈で不成立である。空列を条件不足とはしない。条件を確認していないことを不成立へ変換しない。',
    'rfq':'同じ人が同じ行為で同じ発言上の立場を自ら取り、rfpの条件不足が同じ文脈で成立する内容。役職への正式な就任、単なる発言、許可の欠如、発言内容の偽と同一化しない。',
    'rfr':'本人・発言上の立場・条件列・自ら立場を取る関係を固定し、行為からrfqの内容への関数を作る。批判の評価性質へ直接渡せる。',
}
LIMITS=[
    'これは出過ぎた振舞いという読解候補の操作的な構成である。vorwitzigの全語義、カントの当該使用の唯一の解釈、全ての無分別や性急さの必要十分条件を主張しない。',
    '立場は公式な役職に限らず、その場で何を判断・指図する側として振舞うかを含む。assumesはその振舞いへの関係であり、正当な権限があることや正式な委任とは別である。',
    '条件列の内容・採用根拠・網羅性は明示すべき前提であり、条件不充足だけから制裁や禁止を導かない。空列は評価基準の欠落を意味する場合があり、立場の正当性の証明にはしない。',
]


def generic_composed():
    doc=parse('n:'+definitions())
    basis=dict(version='assumed-standing-basis-v1',document='examples/v014/assumed-standing.noema',
        primitives=[],definitions=MEANINGS,unresolved=LIMITS)
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/kant-situated-criticism-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    quality=k('rfr',*args(PERSONAL))
    text=definitions()
    for name,parent,fields,original in (
        ('hza4','hzay',PREMISE_FIELDS+CONTEXT,PREMISE+CONTEXT),
        ('hza5','hza2',ALL_FIELDS+[('cases','h[d] c')],ALL+[('cases','h[d] c')]),
        ('hza6','hza3',PREMISE_FIELDS+[('cases','h[d] c')],PREMISE+[('cases','h[d] c')])):
        text+=definition(name,params(fields),k(parent,*args(original,quality=quality)))
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis.update(version='kant-assumed-standing-basis-v1',document='examples/v014/kant-assumed-standing.noema')
    basis['definitions'].update(MEANINGS|{
        'hza4':'先行hzayの未展開だったqualityへrfrの合成した評価性質を渡す。納付義務のある人が、同じ批判行為でその発言上の立場を取り、同じ人・立場について指定条件が不足するという読解候補。',
        'hza5':'hza2の全仮定状況での条件文へ、同じ人と批判行為に結び付いたrfrの評価を渡す。批判への処罰許可や内容の偽から評価を補わない。',
        'hza6':'同じ評価を組み込んだ前件が、指定仮定範囲内のどこかで成立する。条件文の真理と該当例の存在を引き続き分ける。',
    })
    basis['unresolved']+=LIMITS+[
        '外部資料の確認はdata/vorwitzig-reading-v1.jsonに記録する。Adelungの1811年版とDWBの歴史的用例からの設計上の推論であり、直接の語義対応を検証済みとしない。実行時に辞書参照や語ごとの翻訳規則を追加しない。',
        '前版の評価性質qualityを、この読解候補では合成した条件へ置換した。自ら立場を取る関係、評価条件の根拠、語用論的な非難の強さ、Skandal、sogar、demohngeachtet、制度の基礎説明は残る。',
        '新しい基本記号や著者主張は追加しない。解釈候補を作ったことを、原文との意味一致が確認済みの文章とは扱わない。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=['hza4','hza5','hza6','hzah','rfd'],statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='assumed-standing-core-basis-v1',document_path='examples/v014/assumed-standing-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


BUILDERS=((generic_composed,'assumed-standing'),(source_composed,'kant-assumed-standing'),(core_composed,'assumed-standing-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored assumed standing differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
