"""Keep a release relative to selected normative sources from becoming total release."""
from copy import deepcopy
import json
from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args
from scripts.compose_scoped_nonprescription import SOURCE_FIELD

PARENT='examples/v014/kant-first-achievers.noema'
RANGES=[('minimum','h[a] c'),('broader','h[a] c')]
CONDITION=RANGES+[('condition','h[a a] e')]
SETTINGS=[('members','h[a a] c')]+[(n,t) for n,t in SOURCE_FIELD if n not in ('source','people','context')]
ROOTS=['roh','roi']


def definitions():
    subset=quant('f','source','a',op('y',app(v('minimum'),v('source')),app(v('broader'),v('source'))))
    text=definition('roh',params(RANGES),both(quant('g','source','a',app(v('minimum'),v('source'))),subset))
    selected=quant('f','source','a',op('y',app(v('minimum'),v('source')),op('t',app(v('condition'),v('source'),v('subject')),v('context'))))
    text+=definition('roi',params(CONDITION),'i[subject a][b context['+both(k('roh',*args(RANGES)),selected)+']]','h[a] e')
    return text

MEANINGS={
    'roh':'明示した最小範囲が非空で、広い比較範囲の部分集合である。比較範囲に含まれない出所を、限定の対象へ無断で追加しない。',
    'roi':'rohの範囲で、同じ対象者と文脈について、選んだ最小範囲の各出所に対応する内容が成立する。他の出所の成立も不成立も要求しない。',
    'hzgg':'同じ対象集団の成員・役割・主題・基準時・活動・実行記述を固定し、出所ごとにhzfoの両方向の積極的許可を評価する。出所を替える際に対象者や活動範囲を替えない。',
    'hzgh':'指定政府側の出所一つをroiの最小範囲にし、広い比較範囲内にあることを要求してhzggへ接続する。政府以外の全出所の許可や、実際の知的自立を補わない。',
}
LIMITS=[
    'wenigstens von Seiten der Regierungへの範囲限定の候補である。「少なくとも」を政府側の肯定とし、「政府側だけ」の排他的な否定にしない。他側面の未知を真偽いずれかへ補わない。',
    'この接続では規範の出所を比較する。政府という制度の全意味、強制・実力による干渉、学習や能力の不足、内面的な依存を許可の有無へ還元しない。',
    '対象集団の成員・主題・基準時・対象活動・記述を、出所間の比較で保持する。原文の人類全体の網羅性や、全ての出所の網羅性は入力の規約に依存する。',
    '最小範囲は非空で比較範囲に含まれる。複数出所を選んだ場合は全ての成立を要求する。広い範囲に拡張すると成立条件は強まり、逆方向の推論は認めない。',
    '型付きの一般式は任意の範囲述語を受け取る。有限解釈器は条件式の両辺を評価するため、指定されない出所の関数値も要求する場合がある。意味上の無断言と、実装が部分的な入力だけで評価できることは別である。',
    '限定された内容の変化・生成・最初の達成は既存hzge・rodへ接続する。これを全出所からの解放やh4lの能力獲得に昇格させない。限定なしの原文訳、感謝・世界・後世・良心・人類の未成熟と全文の意味確認は残る。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    fields=args(SOURCE_FIELD,people='i[person a]['+app(v('members'),v('subject'),v('person'))+']')
    text=definitions()+definition('hzgg',params(SETTINGS),'i[source a subject a][b context['+k('hzfo',*fields)+']]','h[a a] e')
    selected='i[source a]['+op('e',v('source'),v('government'))+']'
    text+=definition('hzgh',params([('government','a'),('broader','h[a] c')]+SETTINGS),k('roi',selected,v('broader'),k('hzgg',*args(SETTINGS))),'h[a] e')
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-first-achievers-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-limited-release-basis-v1',document='examples/v014/kant-limited-release.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS,'limited-release')
def core_composed():
    roots=[d['name'] for d in parse((ROOT/'examples/v014/first-achievers-core.noema').read_text(encoding='utf-8'))['declarations']]
    return projected(roots+ROOTS+['hzgg','hzgh'],'limited-release-core')
BUILDERS=((generic_composed,'limited-release'),(source_composed,'kant-limited-release'),(core_composed,'limited-release-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored limited release differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
