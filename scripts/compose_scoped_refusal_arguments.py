"""Keep a duty/choice law separate from scoped discourse leading to label refusal."""
from copy import deepcopy
import json
from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both
from scripts.compose_situated_criticism import params,args
from scripts.compose_scoped_nonprescription import DUTY,SOURCE_DUTY
from scripts.compose_curve_discourse import conditional_basis

PARENT='examples/v014/kant-label-appraisals.noema'
SCOPED='h[a a i[e] a d] c'
ARGUMENT=[('author','a'),('context','d'),('scope','a'),('assumption','a'),('conclusion','a'),('premise','i[e]'),('result','i[e]')]
RELATIONS=[('adopts',SCOPED),('claims',SCOPED),('infers','h[a h[a] c a d] c'),('before','h[a a d] c')]
ROOTS=['rnx','rny']


def definitions():
    duty=op('t',app(k('rm7',*args(DUTY)),v('bindings')),v('context'))
    choice=op('t',app(k('rnk',*args(DUTY)),v('bindings')),v('context'))
    text=definition('rnx',params(DUTY),'i[bindings j[a]][b context['+op('y',duty,op('u',choice))+']]', 'h[j[a]] e')
    singleton='i[node a]['+op('e',v('node'),v('assumption'))+']'
    text+=definition('rny',params(ARGUMENT+RELATIONS),both(op('u',op('e',v('assumption'),v('conclusion'))),
        app(v('adopts'),v('assumption'),v('author'),v('premise'),v('scope'),v('context')),
        app(v('claims'),v('conclusion'),v('author'),v('result'),v('scope'),v('context')),
        app(v('infers'),v('author'),singleton,v('conclusion'),v('context')),
        app(v('before'),v('assumption'),v('conclusion'),v('context'))))
    return text

MEANINGS={
    'rnx':'同じ評価出所・本人の引数・立場・政策記述・文脈について、rm7の義務があればrnkの両方向の裁量はないという条件内容。本人の信念や名称の拒否を結論に含めない。',
    'rny':'同じ著者・文脈・仮定範囲で、前提記述を仮定として採用する箇所と、結論記述をその範囲の主張とする別箇所を結ぶ。本文順序と帰結としての提示を要求し、無条件の断言や推論の妥当性へ置き換えない。',
    'hzf5':'rnyを既存の条件付き談話のug・uhと、帰結提示ud・本文順序ueへ接続する。ここでug・uhは他の文書群にある共通の意味規約を導入する。',
    'hzf6':'rnxを既存h7k・h7lへ接続する。内側の自由政策と外側の義務・裁量を同じ記述で固定する。',
}
LIMITS=[
    'rnxは既存の義務と裁量の定義の関係を表す。同じ要求があるなら、不実行への裁量が必要とする反対要求の不在と両立しない。政策の実現、本人の認識、名称拒否はこの含意から導かない。',
    '前提を本人の義務判断、結論を同じ本人による名称拒否の表明として閉じた内容で渡す。前提と結論の人物をそろえるのは接続例の条件で、型だけで任意の二内容を同じ人物へ束縛しない。',
    'u0015の関係節内のalsoへの部分的な論証候補。君主の一般的な対象範囲や外側の啓蒙・称賛の主張は未構成であり、現在その君主が存在し実際に拒否したとの断言へ昇格させない。',
    '帰結として提示したことは論理的妥当性・十分な根拠・心理的因果の証明ではない。本文順序も出来事の時間順序ではない。仮定と結論は同じ範囲に結び、他の範囲での主張を混ぜない。',
    'ug・uhは既存の一般的な仮定採用・範囲内主張の意味規約であり、特定の語の翻訳規則ではない。今回の原文付き文書では二つの原始記号を追加するが、新しい著者主張は加えない。',
    '著者の具体的な論証の採用根拠、品位・寛容・傲慢の語用、自らという強調、啓蒙・称賛・解放と後続本文、全文の意味確認は未完。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    assert not {'ug','uh'} & {d['name'] for d in doc['declarations']}
    text='r ug[a a i[e] a d] c.r uh[a a i[e] a d] c.'+definitions()
    text+=definition('hzf5',params(ARGUMENT),k('rny',*args(ARGUMENT),'p ug','p uh','p ud','p ue'))
    text+=definition('hzf6',params(SOURCE_DUTY),k('rnx',*args(DUTY,required='p h7k',allowed='p h7l')),'h[j[a]] e')
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-label-appraisals-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-scoped-refusal-arguments-basis-v1',document='examples/v014/kant-scoped-refusal-arguments.noema')
    basis['primitives']+=deepcopy([r for r in conditional_basis()['primitives'] if r['symbol'] in ('ug','uh')])
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(previous,extra,stem):
    text,basis=source_composed();doc=parse(text)
    roots=[d['name'] for d in parse((ROOT/('examples/v014/'+previous+'.noema')).read_text(encoding='utf-8'))['declarations']]+ROOTS+extra
    selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected('policy-discretion',['rna','rnc','rnj'],'scoped-refusal-arguments')
def core_composed():return projected('policy-discretion-core',['rna','rnc','rnj','hzfr','hzft','hzfw','hzf5','hzf6'],'scoped-refusal-arguments-core')
BUILDERS=((generic_composed,'scoped-refusal-arguments'),(source_composed,'kant-scoped-refusal-arguments'),(core_composed,'scoped-refusal-arguments-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored scoped argument differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
