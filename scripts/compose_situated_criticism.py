"""Join a required remittance, its criticism and possible consequences by reference."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, call as k, app, both, op, quant, definition

PARENT = 'examples/v014/kant-possible-sanctions.noema'
PAYMENT_DESCRIPTION = 'i[h[a a] e]'
MESSAGE = 'i[h[a] f]'
PROPERTY = 'i[h[a] e]'
LINK = 'h[a a a a a '+PAYMENT_DESCRIPTION+' d] c'
SPEECH = [('person','a'), ('speech','a'), ('audience','h[a] c'), ('subject','a'), ('criticism',MESSAGE)]
DUTY = [('person','a'), ('action','a'), ('role','a'), ('issuer','a'), ('payment',PAYMENT_DESCRIPTION)]
BASE = DUTY + SPEECH[1:] + [('charge',LINK)]
PREMISE = BASE + [('quality','h[a] e')]
RESULT = [('person','a'), ('speech','a'), ('group','a'), ('resistance',PROPERTY), ('authority','a'), ('measure','a'),
    ('assessment',PROPERTY), ('adverse','h[a a d] c'), ('intends','h[a a a d] c'),
    ('responds','h[a a a a '+PROPERTY+' d] c'), ('causalprospects','h[a d d] c'), ('sanctionprospects','h[a d d] c')]
ALL = PREMISE + RESULT[2:]
CONTEXT = [('context','d')]


def params(fields):
    return ' '.join(name+' '+sort for name, sort in fields)


def args(fields, **replace):
    return [replace.get(name, v(name)) for name, _ in fields]


def definitions():
    fields = SPEECH+CONTEXT+ [('occurs','h[a d] c'),('presents','h[a a d] c'),('conveys','h[a a a '+MESSAGE+' d] c')]
    return definition('rfo', params(fields), both(
        app(v('occurs'), v('speech'), v('context')),
        app(v('presents'), v('person'), v('speech'), v('context')),
        quant('g','recipient','a',app(v('audience'),v('recipient'))),
        quant('f','recipient','a',op('y',app(v('audience'),v('recipient')),
            app(v('conveys'),v('speech'),v('recipient'),v('subject'),v('criticism'),v('context'))))))


MEANING = '指定した同じ発話行為が生起し、同じ人が提示者となり、非空の受け手範囲の各人へ、同じ対象に関する同じ発話記述を示す。受け手が理解・同意したこと、内容の真理、公的使用かどうかは含まない。'
LIMITS = [
    'rfoは発話行為を引数で固定する。受け手が複数でも、別の発話行為を各人の証拠として組み合わせない。必要なら一つの行為に部分行為がある読みを明示する。',
    '提示と実際の生起は関係の意味規約として渡す。内容への同意、話者の信念、伝達媒体や発話時刻の具体値は別条件である。',
]


def generic_composed():
    doc = parse('n:'+definitions())
    basis = dict(version='situated-criticism-basis-v1', document='examples/v014/situated-criticism.noema',
        primitives=[], definitions={'rfo':MEANING}, unresolved=LIMITS)
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT/'data/kant-possible-sanctions-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements'] = doc['statements'],[]
    text = definitions()
    text += definition('hzaw',params(SPEECH+CONTEXT),k('rfo',*args(SPEECH+CONTEXT),'p dg','p f3','p f2'))
    text += definition('hzax',params(BASE+CONTEXT),both(
        k('hzai',*args(DUTY+CONTEXT)), op('u',op('e',v('action'),v('speech'))),
        k('hzaw',*args(SPEECH+CONTEXT)),
        app(v('charge'),v('subject'),v('issuer'),v('person'),v('role'),v('action'),v('payment'),v('context'))))
    text += definition('hzay',params(PREMISE+CONTEXT),both(k('hzax',*args(BASE+CONTEXT)),
        op('t',app(v('quality'),v('speech')),v('context'))))
    text += definition('hzaz',params(RESULT+CONTEXT),both(
        k('hzar',v('speech'),v('group'),v('resistance'),v('context'),v('causalprospects')),
        k('hzau',v('authority'),v('measure'),v('person'),v('speech'),v('assessment'),
            v('adverse'),v('intends'),v('responds'),v('context'),v('sanctionprospects'))))
    premise = 'i[who a][b case['+k('hzay',*args(PREMISE+CONTEXT,person=v('who'),context=v('case')))+']]'
    conclusion = 'i[who a][b case['+k('hzaz',*args(RESULT+CONTEXT,person=v('who'),context=v('case')))+']]'
    text += definition('hza2',params(ALL+[('cases','h[d] c')]),k('rc',v('person'),premise,conclusion,v('cases')))
    text += definition('hza3',params(PREMISE+[('cases','h[d] c')]),k('re',v('person'),premise,v('cases')))
    doc = parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis.update(version='kant-situated-criticism-basis-v1',document='examples/v014/kant-situated-criticism.noema')
    basis['definitions'].update({
        'rfo':MEANING,
        'hzaw':'同じ人・発話行為・非空の受け手範囲・対象・発話記述を、既存の生起dg、提示者f3、伝達f2へ接続する。学識者としての公的使用という条件は追加しない。',
        'hzax':'同じ文脈で本人に指定納付内容への要求があり、別の行為で指定内容を述べ、その対象が同じ出所・本人・役割・行為・納付記述の賦課に対応する。対応関係chargeも明示し、無関係な賦課への批判を混ぜない。',
        'hzay':'hzaxの批判行為について、指定した評価性質qualityが同じ文脈で成立する。vorwitzigの評価を渡す場所を保持するが、その語義を未払い・許可の不在・批判の内容の偽へ置き換えない。',
        'hzaz':'同じ批判行為について、指定集団への抵抗の誘発可能性と、同じ本人のその批判への応答として措置が実行される可能性を結ぶ。二つの可能結果の存在を述べ、同じ未来で同時に生じるとは要求しない。',
        'hza2':'指定した非空の仮定状況範囲で、同じ本人のhzayが成立する場合にはhzazも成立する。when節を納付の要求がある状況への制限として読む部分草案。現在の批判・納付・抵抗・処罰や、前件の実例の存在を断言しない。',
        'hza3':'指定した範囲に、同じ本人のhzayが成立する状況が少なくとも一つある。条件文hza2の真理と、その前件に該当する場合の存在を区別する。',
    })
    basis['unresolved'] += LIMITS+[
        'chargeは賦課の対象と規範の引数を結ぶ関係であり、制度・徴税・金額・期限の定義そのものではない。文脈が一致することから具体的な支払期限や支払い済みを補わない。',
        'hza2は仮定状況ごとに納付要求、批判、誘発可能性、措置の可能性を接続した読み。原文のsogar、als ein Skandal、vorwitzigの具体的な評価基準、後続のdemohngeachtetと市民の義務への不違反の談話接続は未完。',
        '挿入説明の誘発可能性を条件文の帰結側へ置く読みを明示する。仮定の外でも独立に成立する付加説明としての読みに一意化した証明ではない。規範的な処罰許可へ読み替える場合はhzavを用い、hzazから許可を導かない。',
        '既存15件の著者主張は保持する。追加した条件文を、原文との意味一致が確認済みの著者主張とはしていない。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=['hza2','hza3','hzah','rfd'],statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='situated-criticism-core-basis-v1',document_path='examples/v014/situated-criticism-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


BUILDERS=((generic_composed,'situated-criticism'),(source_composed,'kant-situated-criticism'),(core_composed,'situated-criticism-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored situated criticism differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
