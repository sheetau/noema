"""Separate an attributed institutional voice from endorsement and report truth."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,both
from scripts.compose_situated_criticism import params,args,MESSAGE,generic_composed as speech_document

PARENT='examples/v014/kant-appointment-terms.noema'
VOICE='h[a a a a a '+MESSAGE+' d] c'
SERVES='h[a a a d] c'
TEACHES='h[a a '+MESSAGE+' d] c'
CORE=[('person','a'),('activity','a'),('principal','a'),('role','a'),('audience','h[a] c'),
    ('subject','a'),('message',MESSAGE),('context','d')]
PRESENTATION=[('occurs','h[a d] c'),('presents','h[a a d] c'),('conveys','h[a a a '+MESSAGE+' d] c')]
RELATIONS=PRESENTATION+[('voices',VOICE),('positioned','h[a a a d] c'),('entrusted','h[a a d] c'),('serves',SERVES)]
SETTINGS=[field for field in CORE if field[0] not in ('person','activity','context')]+[('voices',VOICE),('serves',SERVES)]


def definitions():
    actual=k('rfo',*map(v,('person','activity','audience','subject','message','context')),*args(PRESENTATION))
    attribution=app(v('voices'),*map(v,('person','activity','principal','role','subject','message','context')))
    text=definition('rga',params(CORE+PRESENTATION+[('voices',VOICE)]),both(actual,attribution))
    delegated=both(k('rga',*args(CORE+PRESENTATION+[('voices',VOICE)])),
        app(v('positioned'),*map(v,('person','activity','role','context'))),
        app(v('entrusted'),*map(v,('person','role','context'))),
        app(v('serves'),*map(v,('person','principal','role','context'))))
    text+=definition('rgb',params(CORE+RELATIONS),delegated)
    fixed=SETTINGS+PRESENTATION+[('positioned','h[a a a d] c'),('entrusted','h[a a d] c')]
    text+=definition('rgc',params(fixed),'i[person a activity a][b context['+k('rgb',*args(CORE+RELATIONS))+']]', 'h[a a] e')
    body='i[subject a][j s[b context['+app(v('teaches'),*map(v,('principal','subject','message','context')))+']]]'
    text+=definition('rgd','principal a message '+MESSAGE+' teaches '+TEACHES,body,'h[a] f')
    return text


MEANINGS={
    'rga':'同じ本人・行為・対象・発話記述を非空の受け手群へ実際に提示し、その行為で同じ組織と役割の声として位置付ける。組織の実際の立場、本人の信念、権限、内容の真理を付けない。',
    'rgb':'rgaの同じ本人・行為・組織・役割に、活動の役割分類・委任・当該組織への奉仕を結ぶ。委任があることと、個々の発話が許可され正当であることは別である。',
    'rgc':'組織・役割・受け手・対象・発話記述と関係を固定し、本人と行為からrgbの内容への関数を作る。閉じた適用を引用して任用条件や義務の対象にでき、対象を実行せず保持する。',
    'rgd':'同じ組織が、同じ対象について、内側の発話記述を教示内容として提示するという関係を主張する外側の発話を作る。内側の記述を脱引用せず保持する。外側の発話が提示されたことだけでは、この組織関係や内側の真理は成立しない。',
}
LIMITS=[
    'voicesは提示者・提示行為・組織・役割・対象・発話記述・状況の帰属関係として渡す。その組織の声として提示することを指定し、組織が承認したとの認定を含めない。',
    '委任・役割分類・奉仕を加えても、個々の発話の許可、組織の実際の見解、話者の信念、受け手の同意・理解を推定しない。必要ならそれぞれ別の内容・規範を追加する。',
    'teachesは組織・対象・発話記述・状況の関係入力である。組織の教示を構成する制度・伝達経路・集団意思の一般的な説明は未完で、真理や個人の発話だけから埋めない。',
    '発話の記述は同じ型付き構文を共有する。質問や同じ真偽を返す別名、別の組織についての報告を、元の記述へ無断で置き換えない。',
]


def generic_composed():
    text,basis=speech_document();basis=deepcopy(basis)
    doc=parse(text+definitions())
    basis.update(version='institutional-voice-basis-v1',document='examples/v014/institutional-voice.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/kant-appointment-terms-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    text=definitions()
    text+=definition('hzbp',params(CORE+[('voices',VOICE)]),k('rga',*args(CORE),'p dg','p f3','p f2',v('voices')))
    text+=definition('hzbq',params(CORE+[('voices',VOICE),('serves',SERVES)]),
        k('rgb',*args(CORE),'p dg','p f3','p f2',v('voices'),'p cb','p cf',v('serves')))
    text+=definition('hzbr',params(SETTINGS),k('rgc',*args(SETTINGS),'p dg','p f3','p f2','p cb','p cf'),'h[a a] e')
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis.update(version='kant-institutional-voice-basis-v1',document='examples/v014/kant-institutional-voice.noema')
    basis['definitions'].update(MEANINGS|{
        'hzbp':'rgaを既存の行為の生起dg・提示者f3・受け手への伝達f2へ結ぶ。組織の声という帰属は明示的な入力であり、許可や内容の真理と分ける。',
        'hzbq':'hzbpの発話を同じ職務のcb・cfおよび組織への奉仕へ結ぶ。組織の名による職務上の提示の部分条件であり、自由な裁量の不在を付けない。',
        'hzbr':'hzbqの組織・役割・受け手・対象・発話・帰属関係を固定した、本人と行為から内容への構成。過去の任用条件と現在の要求の引用対象にできる。',
    })
    basis['unresolved']+=LIMITS+[
        'u0012のim Namen eines andern vorzutragenと、unsere Kirche lehrt dieses oder jenesの報告構造へ部分接続する。後者では外側の主張、組織の教示関係、内側の内容を区別する。',
        '原文の任用されたという記述は、実際に講義済みであるとの断言ではない。hzbrの記述を前版の任用条件や義務へ渡し、実行とは分ける。今回も新しい著者主張は追加しない。',
        'われわれのという集団の指示、教会・教理の一般的な意味、dieses oder jenesの例示・不特定性、wird sagenの予想、Beweisgründe、自由な裁量の不在、良心と辞職は未完。',
        '採用基準への適合や任用条件と同じ対象へ結ぶことは可能だが、組織の名による提示だけを、それら全ての成立や正当性の代用にしない。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=['hzbp','hzbq','hzbr','rgd','hzbm','hzbn'],statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='institutional-voice-core-basis-v1',document_path='examples/v014/institutional-voice-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


BUILDERS=((generic_composed,'institutional-voice'),(source_composed,'kant-institutional-voice'),(core_composed,'institutional-voice-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored institutional voice differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
