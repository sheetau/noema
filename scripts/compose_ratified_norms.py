"""Separate institutional confirmation from norms attributed to a source."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant,lam
from scripts.compose_situated_criticism import params,args
from scripts.compose_policy_norms import DESCRIPTION,RULE,TRUE

PARENT='examples/v014/kant-scoped-liberty.noema'
TARGET=[('person','a'),('role','a'),('description',DESCRIPTION),('bindings','j[a]')]
LOCAL=[('source','a')]+TARGET+[('context','d'),('required',RULE),('allowed',RULE)]
GLOBAL=[('source','a'),('context','d'),('required',RULE),('allowed',RULE)]
INDEX=[('selected','h[a] c'),('people','h[a] a'),('roles','h[a] a'),('descriptions','h[a] '+DESCRIPTION),('arguments','h[a] j[a]')]
SCOPED=GLOBAL+INDEX
CONFIRM=[('source','a'),('context','d'),('authorities','h[a] c'),('confirms','h[a a d] c')]
CONCESSION=[('source','a'),('candidates','h[d] c'),('authorities','h[a] c'),('confirms','h[a a d] c'),('condition','h[a d] c')]
ROOTS=['rhp','rhq','rhr','rhs','rht','rhu','rhv','rhw']
SOURCE_ROOTS=['hzce','hzcf']


def definitions():
    fields=[v(n) for n,_ in LOCAL[:5]]
    rules=[app(v(relation),*fields,sign,v('context')) for relation in ('required','allowed') for sign in (TRUE,op('u',TRUE))]
    text=definition('rhp',params(LOCAL),both(*(op('u',rule) for rule in rules)))
    body=k('rhp',*args(LOCAL))
    for name,sort in reversed(TARGET):body=quant('f',name,sort,body)
    text+=definition('rhq',params(GLOBAL),body)
    allocation={name:app(v(fn),v('entry')) for name,fn in zip(('person','role','description','bindings'),('people','roles','descriptions','arguments'))}
    listed=quant('f','entry','a',op('y',app(v('selected'),v('entry')),k('rhp',*args(LOCAL,**allocation))))
    text+=definition('rhr',params(SCOPED),listed)
    matching=both(app(v('selected'),v('entry')),*(op('e',v(name),expr) for name,expr in allocation.items()))
    covered=op('y',op('u',k('rhp',*args(LOCAL))),quant('g','entry','a',matching))
    for name,sort in reversed(TARGET):covered=quant('f',name,sort,covered)
    text+=definition('rhs',params(SCOPED),covered)
    text+=definition('rht',params(SCOPED),both(k('rhr',*args(SCOPED)),k('rhs',*args(SCOPED))))
    text+=definition('rhu',params(CONFIRM),both(quant('g','authority','a',app(v('authorities'),v('authority'))),
        quant('f','authority','a',op('y',app(v('authorities'),v('authority')),app(v('confirms'),v('authority'),v('source'),v('context'))))))
    confirmed=k('rhu',v('source'),v('scene'),v('authorities'),v('confirms'))
    text+=definition('rhv',params(CONCESSION),quant('f','scene','d',op('y',app(v('candidates'),v('scene')),
        op('y',confirmed,app(v('condition'),v('source'),v('scene'))))))
    text+=definition('rhw',params(CONCESSION[:-1]),quant('g','scene','d',both(app(v('candidates'),v('scene')),confirmed)))
    return text


MEANINGS={
    'rhp':'同じ規範の出所・名宛人・立場・記述・引数列・評価文脈について、両極性の要求と両極性の積極的許可が全てない。要求がないだけで許可があると推定しない。',
    'rhq':'同じ出所と評価文脈について、全ての名宛人・立場・型に合う記述・有限引数列でrhpが成立する。指定した出所から要求も許可も生じないという限定された意味での規範的な無効性。',
    'rhr':'明示した対象一覧の各項目についてrhpが成立する。各項目は名宛人・立場・記述・順序付き引数列を保持する。空の一覧なら真だが、それだけでrhqとはしない。',
    'rhs':'同じ出所と文脈の全ての要求・許可について、名宛人・立場・記述・引数列が一致する一覧項目がある。別名の記述や並べ替えた列を同じ対象として補わない。',
    'rht':'一覧内に要求・許可がないrhrと、取りこぼしのないrhsを合わせる。未知の対象一覧を空として完全性を認定しない。',
    'rhu':'指定した承認主体の範囲が非空で、その各主体が同じ出所を同じ文脈で承認する。承認は要求や許可の成立、実行や正当性を含意しない。',
    'rhv':'指定した候補状況の各々で、rhuの承認があるなら、同じ出所について指定条件が成立する。現実の承認や承認可能な候補の存在を断定しない。',
    'rhw':'指定候補の中にrhuの承認が成立する状況がある。rhvの条件付きの主張とは別で、空候補では偽。',
}
LIMITS=[
    '要求・許可の解釈は同じ出所と評価文脈へ固定する。契約が物理的に作成・署名されたか、実際に強制されるか、内容が真かは別である。',
    'rhqは要求・積極的許可を生成しないという範囲の無効性であり、権能・免責・資格など全制度的効果や契約無効の法理を網羅した定義ではない。外部の出所による救済・返還・制裁等の要求まで否定しない。',
    '承認主体と確認行為の意味は入力で与える。承認の事実から、その主体に権限があることや規範的に正当であることを導かない。',
    '全記述と全有限列への量化を有限の既知一覧へ置き換えない。完全性は別の全域条件であり、有限の対照例の全通過をその証明とはしない。',
    'rhvは条件付き内容の一つの構成であり、譲歩に伴う通常予想・強調の全てを表すものではない。候補や承認主体の範囲を省略した原文の唯一の読解とはしない。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=definitions()+definition('hzce','contract a context d',k('rhq',v('contract'),v('context'),'p h7k','p h7l'))
    inputs=[('contract','a'),('candidates','h[d d] c'),('authorities','h[a] c'),('confirms','h[a a d] c')]
    candidates=lam('scene','d',app(v('candidates'),v('anchor'),v('scene')))
    body=both(k('hzce',v('contract'),v('anchor')),k('rhv',v('contract'),candidates,v('authorities'),v('confirms'),'p hzce'))
    text+=definition('hzcf',params(inputs),'b anchor['+body+']','e')
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-scoped-liberty-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-ratified-norms-basis-v1',document='examples/v014/kant-ratified-norms.noema')
    basis['definitions'].update(MEANINGS|{
        'hzce':'契約を規範の出所として扱い、既存のh7k・h7lの評価文脈において、rhqの要求・許可の不成立を述べる。特定の現行法上の結論や契約の不存在を意味しない。',
        'hzcf':'同じ契約について、基準文脈のhzceと、基準文脈で固定した候補における承認時にもhzceであるという条件を併記する。承認が実際に起きたことは付けない。原文の無効と仮定上の確認への部分的な読み。',
    });basis['unresolved']+=LIMITS+[
        'u0013のnull und nichtigと確認の仮定への解釈注記。評価文脈は著者の規範的な見地に対応させる必要があり、支配権力が現に採用する規範と自動同一化しない。',
        '契約の相互約束としての構造、永久に全ての啓蒙を妨げる目的、最高権力・帝国議会・講和の種類と最上級、著者の談話への接続は未完。新しい著者主張・原始概念・固有参照は追加しない。',
    ]
    audit_basis(doc,basis);return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS,'ratified-norms')
def core_composed():return projected(ROOTS+SOURCE_ROOTS,'ratified-norms-core')
BUILDERS=((generic_composed,'ratified-norms'),(source_composed,'kant-ratified-norms'),(core_composed,'ratified-norms-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored ratified norms differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
