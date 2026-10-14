"""Bind parties' declarations to one agreement and one version of its terms."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args
from scripts.compose_policy_norms import DESCRIPTION,RULE

PARENT='examples/v014/kant-ratified-norms.noema'
DECLARES='h[a a a '+DESCRIPTION+' j[a] d] c'
ASSIGNED='h[a '+DESCRIPTION+' d] c'
ACT=[('person','a'),('act','a'),('agreement','a'),('terms',DESCRIPTION),('bindings','j[a]'),('scene','d'),
    ('occurs','h[a d] c'),('performs','h[a a d] c'),('declares',DECLARES)]
PAST=ACT+[('context','d'),('history','h[d] c'),('before','h[d d] c')]
FORM=[('agreement','a'),('terms',DESCRIPTION),('context','d'),('parties','h[a d] c'),('arguments','h[a] j[a]'),
    ('eligible','h[a] c'),('history','h[d] c'),('before','h[d d] c'),('assigned',ASSIGNED),
    ('occurs','h[a d] c'),('performs','h[a a d] c'),('declares',DECLARES)]
SOURCE=[(n,t) for n,t in FORM if n not in ('eligible','before','occurs','performs')]
CONTENT=[(n,t) for n,t in SOURCE if n!='context']+[('candidates','h[d d] c'),('authorities','h[a] c'),('confirms','h[a a d] c')]
ROOTS=['rhx','rhy','rhz','rh2']
SOURCE_ROOTS=['hzcg','hzch','hzci']


def definitions():
    body=both('a[v bindings][n p a b][v person]',app(v('occurs'),v('act'),v('scene')),
        app(v('performs'),v('person'),v('act'),v('scene')),
        app(v('declares'),*(v(n) for n in ('person','act','agreement','terms','bindings','scene'))))
    text=definition('rhx',params(ACT),body)
    temporal=both(k('ta',v('history'),v('before')),app(v('history'),v('context')),app(v('history'),v('scene')),
        op('x',op('e',v('scene'),v('context')),app(v('before'),v('scene'),v('context'))))
    text+=definition('rhy',params(PAST),both(temporal,k('rhx',*args(ACT))))
    member=lambda n:app(v('parties'),v(n),v('context'))
    two=quant('g','left','a',quant('g','right','a',both(member('left'),member('right'),op('u',op('e',v('left'),v('right'))))))
    witness=k('rhy',*args(PAST,bindings=app(v('arguments'),v('person'))))
    witness=quant('g','act','a',quant('g','scene','d',witness))
    text+=definition('rhz',params(FORM),both(two,app(v('assigned'),v('agreement'),v('terms'),v('context')),
        quant('f','person','a',op('y',member('person'),both(app(v('eligible'),v('person')),witness)))))
    text+=definition('rh2',params(FORM+[('required',RULE),('allowed',RULE)]),both(k('rhz',*args(FORM)),
        k('rhq',v('agreement'),v('context'),v('required'),v('allowed'))))
    return text


MEANINGS={
    'rhx':'同じ本人・生起する行為・合意対象・条項記述・順序付き引数列・状況を結ぶ引受けの表明。引数列の先頭は同じ本人でなければならない。条項の内容自体は実行評価しない。',
    'rhy':'rhxの行為が、同じ厳密な全順序の履歴に属し、基準文脈と同時かそれ以前に生じた。行為と時点を別々の記録から継ぎ合わせない。',
    'rhz':'基準文脈で固定した二者以上の適格な当事者全員について、同じ合意対象に割り当てた同じ条項記述へのrhyの引受けがある。各人に異なる引数列・行為・時点を許す。',
    'rh2':'rhzの引受けの構成と、同じ合意対象を出所とする全要求・許可の不成立rhqを併記する。合意の形成と規範的な効力を同一視しない。',
}
LIMITS=[
    'declaresは、その行為で本人が、同じ合意対象の条項記述を自分への引受けとして表明する関係である。単なる文面の受領、他人の発言の報告、賛否の推測、実際の履行とは区別する。表明を認定する慣習・認知・媒体の構成説明は残る。',
    'assignedは合意対象に同じ版の条項記述を結ぶ関係。後から別の記述へ変更した場合、旧記述への引受けを新記述へ自動移送しない。同義な別名も別の記述として保持する。',
    'partiesは基準文脈の当事者範囲を固定する。過去の表明を探すときに当事者を選び直さない。範囲が現実の全当事者を尽くすことは解釈上の前提であり、有限例で証明しない。',
    '個人ごとに異なる引数列を同じ条項関数へ渡せる。先頭の本人以外の位置は条項記述の引数規約による。契約種類ごとの全要件、対価、自由な同意、強制・欺罔の不在、能力、証人、署名や宣誓、他の当事者の受領・理解、解除・失効は要求していない。',
    'rhzは相互の引受けを構成する部分条件であり、全ての意味での契約やその現在の有効性の必要十分条件ではない。規範的な効力はrhq等で別に記述する。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    before='i[first d second d]['+k('ic',v('first'),v('second'),v('context'))+']'
    text=definitions()+definition('hzcg',params(SOURCE),k('rhz',*args(FORM,eligible='p aa',before=before,occurs='p dg',performs='p f3')))
    text+=definition('hzch',params(SOURCE),both(k('hzcg',*args(SOURCE)),k('hzce',v('agreement'),v('context'))))
    consequence=op('t',k('hzcf',v('agreement'),v('candidates'),v('authorities'),v('confirms')),v('context'))
    text+=definition('hzci',params(CONTENT),'b context['+op('y',k('hzcg',*args(SOURCE)),consequence)+']','e')
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-ratified-norms-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-mutual-undertakings-basis-v1',document='examples/v014/kant-mutual-undertakings.noema')
    basis['definitions'].update(MEANINGS|{
        'hzcg':'当事者全員を人aaとし、既存の行為の生起dg・表明する側f3・同じ評価文脈の時間順序icへrhzを接続する。履歴・当事者・条項の割当・引受けの表明は明示した入力である。',
        'hzch':'同じ合意対象の相互引受けhzcgと、要求・許可を生成しないhzceを同時に述べる。表明が生起した事実をその契約の規範的効力の証明にしない。',
        'hzci':'指定された同じ合意対象について、hzcgの形成がある場合に、前版hzcfの無効性と仮定上の承認への判断が成立するという内容。形成が実際にあったことは断言せず、全合意の無効性を一般主張として追加しない。',
    });basis['unresolved']+=LIMITS+[
        'u0013の相互の引受けと同じ契約への参照を部分接続する。誓い、一定で変更しない信条、共同体・教会・構成員の制度的役割、永続的な後見という目的は未記述。',
        'hzciは引数で指定された契約についての条件内容を作る。原文が問題にする目的を持つ契約の選択と著者への帰属は未接続であり、全文単位の意味確認済みには数えない。',
    ]
    audit_basis(doc,basis);return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS,'mutual-undertakings')
def core_composed():return projected(ROOTS+SOURCE_ROOTS,'mutual-undertakings-core')
BUILDERS=((generic_composed,'mutual-undertakings'),(source_composed,'kant-mutual-undertakings'),(core_composed,'mutual-undertakings-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored mutual undertakings differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
