"""Distinguish a possible causal result from an excluded result of that activity kind."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant as q
from scripts.compose_situated_criticism import params

PARENT='examples/v014/kant-independent-profiles.noema'
FULL='examples/v014/kant-causal-outcome-contrast.noema'
CORE='examples/v014/causal-outcome-contrast-core.noema'
LIBRARY='examples/v014/causal-outcome-contrast.noema'
DESCRIPTION='i[h[a] e]'
PROSPECTS='h[a d d] c'
BASE=[('target','a'),('kind','h[a] c'),('effect',DESCRIPTION),('anchor','d'),('prospects',PROSPECTS),
    ('occurs','h[a d] c'),('produces','h[a a '+DESCRIPTION+' d] c')]
PAIR=BASE[:2]+[('first',DESCRIPTION),('second',DESCRIPTION)]+BASE[3:]
SOURCE=PAIR[:-2]


def av(fields):return [v(n) for n,_ in fields]


def definitions():
    possible=k('rfk',v('activity'),v('target'),*av(BASE[2:]))
    text=definition('rqc',params(BASE),q('g','activity','a',both(app(v('kind'),v('activity')),possible)))
    text+=definition('rqd',params(BASE),op('u',k('rqc',*av(BASE))))
    def side(name,effect):return k(name,v('target'),v('kind'),v(effect),*av(BASE[3:]))
    text+=definition('rqe',params(PAIR),both(side('rqc','first'),side('rqd','second')))
    text+=definition('hzhk',params(SOURCE),k('rqe',*av(SOURCE),'p dg','p g3'))
    return text


MEANINGS={
    'rqc':'指定種類の活動のうち、同じ対象・基準文脈について、選定された候補で活動が生起し、その活動が指定の結果記述を対象へ生じさせ、結果内容も成立するものが少なくとも一つある。rfkの同一活動・同一候補の結合を保つ。',
    'rqd':'同じ種類の活動の中にrqcの因果的結果を生む候補がない。結果そのものの全世界での不成立、他種類の活動による結果生成、規範的な禁止とは別である。',
    'rqe':'同じ対象・活動種類・基準文脈・候補関係について、第一の結果は生む可能性があり、第二の結果は生む可能性がない。第一を生む活動だけを選んで第二の否定範囲を狭めない。',
    'hzhk':'カント本文のdgの活動生起とg3の記述された結果生成へrqeを接続する。活動種類、離脱側と考え方の改革側の結果記述、対象、候補関係を引数で明示する部分構成。',
}
LIMITS=[
    'u0011のvielleicht wohlとaber niemalsの対比へ向けた、種類全体に対する因果的可能性の部分構成。vielleichtの認識的な留保、wohlの語用、未来の時間範囲、aberの提示行為を尽くさない。',
    '革命の種類、個人的専制からの離脱、利欲または支配欲による圧迫、真の考え方の改革はまだ具体的な定義へ充足していない。引数名や原語の引用を概念の説明済みの証拠にはしない。',
    '第二の結果の可能性を否定する範囲は指定種類の全活動と全候補である。同じ候補で別の原因により第二の結果が真であっても、それだけでこの否定には反しない。',
    '候補関係は同じ基準文脈から与える。可能性が現実の出来事や結果を含意するとはしない。候補の完全性、現実の因果の基礎、原文のneverの全範囲は別に確認する必要がある。',
    '活動種類が空ならrqdだけは真になり得るが、rqeは第一の可能性を要求するため成立しない。種類や候補を不利な事例に合わせて狭めない。',
    '記述とその真理を区別し、真偽が一致する別の結果記述へ因果関係を移さない。rfkは結果記述を脱引用して実行するため、閉じた著者帰属へそのまま引用できない。',
    '著者の主張は追加せず、同じ原文範囲への部分定義の対応を記録する。後続の新旧の偏見・導きの比喩、全文の意味一致は未完。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    basis=json.loads((ROOT/'data/kant-independent-profiles-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='kant-causal-outcome-contrast-basis-v1',document=FULL);basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    audit_basis(doc,basis)
    files={FULL:format_graph(doc,'compact')+'\n','data/kant-causal-outcome-contrast-basis-v1.json':basis}
    for path,roots in ((CORE,['hzhk']),(LIBRARY,['rqc','rqd','rqe'])):
        selected=extract_document(doc,roots=roots,statement_indices=[]);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p:x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n' for p,x in files.items()}


def main():
    for p,body in build().items():
        path=ROOT/p
        if path.exists():assert path.read_text(encoding='utf-8')==body,p
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Possible and excluded causal results composed over the same activity kind',flush=True)


if __name__=='__main__':main()
