"""Separate unsettled endorsement from possible truth within a doctrine."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args,MESSAGE
from scripts.compose_institutional_voice import CORE,VOICE,SERVES

PARENT='examples/v014/kant-institutional-grounds.noema'
SELECTION='h[a a d d] c'
ACCEPTS='h[a a d] c'
CONTAINS='h[a a d] c'
CONTENTS='h[a] e'
ABOUT='h[a a '+MESSAGE+' d] c'
BASE=[('person','a'),('document','a'),('anchor','d')]
JUDGMENT=BASE+[('accepts',ACCEPTS),('judged',SELECTION)]
POSSIBILITY=BASE+[('alternatives',SELECTION),('contains',CONTAINS),('contents',CONTENTS)]
COMBINED=JUDGMENT+POSSIBILITY[3:]
TRUTH=[('document','a'),('anchor','d'),('point','d'),('contains',CONTAINS),('contents',CONTENTS)]
SPEECH=CORE+[('voices',VOICE),('serves',SERVES),('document','a')]+COMBINED[3:]+[('about',ABOUT)]
ROOTS=['rgi','rgj','rgk','rgl','rgm','rgn','rgo','rgp']


def definitions():
    accepted=app(v('accepts'),v('who'),v('document'),v('point'))
    cases='i[who a anchor d point d]['+app(v('judged'),v('who'),v('document'),v('anchor'),v('point'))+']'
    positive='i[who a][b point['+accepted+']]'
    negative='i[who a][b point['+op('u',accepted)+']]'
    text=definition('rgi',params(JUDGMENT),k('rn',v('person'),positive,v('anchor'),cases))
    selected=app(v('judged'),*map(v,('person','document','anchor','point')))
    actual=app(v('accepts'),*map(v,('person','document','point')))
    text+=definition('rgj',params(JUDGMENT),quant('g','point','d',both(selected,op('u',actual))))
    text+=definition('rgk',params(JUDGMENT),k('rn',v('person'),negative,v('anchor'),cases))
    text+=definition('rgl',params(JUDGMENT),both(k('rgj',*args(JUDGMENT)),quant('g','point','d',both(selected,actual))))
    text+=definition('rgm',params(TRUTH),quant('g','claim','a',both(
        app(v('contains'),v('document'),v('claim'),v('anchor')),
        op('t',app(v('contents'),v('claim')),v('point')))))
    possible=app(v('alternatives'),*map(v,('person','document','anchor','point')))
    text+=definition('rgn',params(POSSIBILITY),quant('g','point','d',both(possible,k('rgm',*args(TRUTH)))))
    text+=definition('rgo',params(COMBINED),both(k('rgj',*args(JUDGMENT)),k('rgn',*args(POSSIBILITY))))
    text+=definition('rgp',params(POSSIBILITY),both(quant('g','point','d',possible),op('u',k('rgn',*args(POSSIBILITY)))))
    return text


MEANINGS={
    'rgi':'同じ本人・対象・基準文脈で選んだ判断候補が非空で、その全てで対象への賛同が成立する。既存rnによる質的な確定の条件であり、実際の文脈の賛同や真理を推定しない。',
    'rgj':'同じ判断候補の中に、対象への賛同が成立しない状況がある。候補が空なら偽で、空範囲を確信不足の証拠にしない。全候補での否定や、心理的な確信度の数値とは別である。',
    'rgk':'判断候補が非空で、全候補で賛同が成立しない。rgjの確定した賛同の不足と、肯定・否定が混在するrglを区別する。',
    'rgl':'同じ判断候補の中に、賛同が成立する状況と成立しない状況がそれぞれある。空範囲・全て賛同・全て不賛同を区別する。',
    'rgm':'基準文脈で同じ対象に含まれると指定された命題的部分のうち、評価状況で真であるものが少なくとも一つある。全体や全ての部分の真理を要求しない。',
    'rgn':'同じ本人・対象・基準文脈で選んだ可能状況のどれかでrgmが成立する。部分の所属は基準文脈に固定し、候補状況ごとに都合のよい別の主張へ入れ替えない。',
    'rgo':'rgjの確定した賛同の不足と、rgnの含まれる真理の可能性が併存する。判断候補と可能状況は別の範囲で、同じ状況での実現を要求しない。',
    'rgp':'可能状況の範囲が非空で、その全てについて含まれる真なる命題がない。候補の欠落を不可能性とみなさず、全可能世界にわたる不可能性も自動的には主張しない。',
}
LIMITS=[
    '賛同を判断候補上で全称・存在的に評価する質的なモデルである。心理的な確信の程度、確率、信頼度の数値や、原文のvoller Ueberzeugungの完全な必要十分条件を定義したものではない。',
    'acceptsは本人・対象・状況の賛同関係、judgedとalternativesは同じ本人・対象・基準文脈に対する二つの選択関係として明示する。認識状態、選択の正当性や可能性の一般理論は別に必要である。',
    'containsは基準文脈において対象に含まれる命題的部分、contentsは各部分の内容を指定する。規範や命令そのものを真偽命題へ置換せず、真理を論じる部分を別に明示する。',
    '一部の真理の可能性は対象全体への賛同ではなく、現在の真理でもない。含まれる部分の抽出・同定や、真理の隠れ方の説明は未完。',
    '空の判断候補や可能状況を、確信・確信の不足・否定の確定・不可能性の証拠にしない。未知の選択関係や真理を、空範囲・偽で埋めない。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/kant-institutional-grounds-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    text=definitions()+definition('hzbw',params(SPEECH),both(k('hzbq',*args(CORE),v('voices'),v('serves')),
        app(v('about'),v('document'),v('subject'),v('message'),v('context')),
        k('rgo',*args(COMBINED,anchor=v('context')))))
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis.update(version='kant-unsettled-teaching-basis-v1',document='examples/v014/kant-unsettled-teaching.noema')
    basis['definitions'].update(MEANINGS|{'hzbw':'同じ組織の名による職務上の提示hzbqを、指定した同じ規定群の対象・発話へ結ぶ。その規定群への賛同が判断候補で確定せず、規定群に含まれる命題的部分の真理が可能状況で排除されない。別の規定群の確信や真理を混ぜない。'})
    basis['unresolved']+=LIMITS+[
        'u0012の規定群に対する十分な確信の不足と、そこに真理が含まれる可能性を、二つの明示された候補範囲の質的なモデルで部分記述する。仮定的なwürde、doch、ganzの程度、verborgenの含意は未完。',
        'hzbwは実際の提示に追加する条件であり、確信の不足と可能性だけから提示の義務・許可・能力を導かない。可能性を理由とするweilの正当化、実際の受任、良心との両立は別に必要である。',
        '教会・規定群・命題的部分の一般的な構成、内的宗教との無矛盾、実益、辞職の条件、原文全文の意味一致は未完。新しい原始概念・局所参照・著者主張を追加しない。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=roots,statement_indices=[])
    projected_basis=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',projected_basis


def generic_composed():return projected(ROOTS,'unsettled-teaching')


def core_composed():return projected(ROOTS+['hzbw'],'unsettled-teaching-core')


BUILDERS=((generic_composed,'unsettled-teaching'),(source_composed,'kant-unsettled-teaching'),(core_composed,'unsettled-teaching-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored unsettled teaching differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
