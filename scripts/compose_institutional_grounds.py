"""Describe an institution's cited grounds separately from their support."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args,MESSAGE

PARENT='examples/v014/kant-institutional-voice.noema'
INSTITUTIONAL='h[a a d] c'
EXAMINED='h[a a '+MESSAGE+' d] c'
CORE=[('principal','a'),('judgment','a'),('subject','a'),('message',MESSAGE),('reasons','h[a] c'),('context','d')]
RELATIONS=[('institutional',INSTITUTIONAL),('about','h[a a d] c'),('examined',EXAMINED),('used','h[a a d] c')]
SUPPORT=[('support','h[a a d] c')]
SETTINGS=[field for field in CORE if field[0] not in ('subject','context')]


def definitions():
    member=app(v('reasons'),v('reason'))
    used=app(v('used'),v('judgment'),v('reason'),v('context'))
    identified=both(app(v('institutional'),v('principal'),v('judgment'),v('context')),
        app(v('about'),v('judgment'),v('subject'),v('context')),
        app(v('examined'),v('judgment'),v('subject'),v('message'),v('context')))
    text=definition('rge',params(CORE+RELATIONS),both(identified,quant('g','reason','a',member),
        quant('f','reason','a',op('y',member,used))))
    text+=definition('rgf',params(CORE+RELATIONS+SUPPORT),both(k('rge',*args(CORE+RELATIONS)),
        quant('f','reason','a',op('y',member,app(v('support'),v('reason'),v('judgment'),v('context'))))))
    text+=definition('rgg',params(CORE+RELATIONS),both(k('rge',*args(CORE+RELATIONS)),
        quant('f','reason','a',op('y',used,member))))
    text+=definition('rgh',params(SETTINGS+RELATIONS),
        'i[subject a][j s[b context['+k('rgg',*args(CORE+RELATIONS))+']]]','h[a] f')
    return text


MEANINGS={
    'rge':'同じ組織に帰属する同じ判断を、同じ対象・発話記述へ結ぶ。指定した理由範囲は非空で、その各理由がこの判断・状況で用いられる。範囲外の理由を排除せず、理由の支持や主張の真理を要求しない。',
    'rgf':'rgeの指定理由が、それぞれ同じ判断を支持する。支持関係は別に与える。理由を用いたという事実から支持を推定せず、各理由単独での十分な証明や、理由の組合せの論理的妥当性も主張しない。',
    'rgg':'rgeの同じ判断・状況で実際に用いられる理由が、指定範囲で尽くされる。組織の全判断・全状況・全ての可能な根拠を尽くすという意味ではない。',
    'rgh':'組織・判断・内側の発話記述・理由範囲と関係を固定し、同じ対象についてrggが成立するという外側の主張を作る。引用して提示するだけでは、一覧の完全性・実際の使用・支持・内側の真理を認定しない。',
}
LIMITS=[
    'institutionalは判断の組織への帰属を明示する関係引数であり、人が判断するfaへ組織を直接代入しない。組織意思の形成・承認・判断の個体化は別の説明を要する。',
    '用いる理由と、判断を支持する理由を区別する。supportは支持の評価関係であり、論理的な証明検査器や、真なる前提からの演繹を自動構成する処理ではない。',
    'reasonsは個体から真偽への範囲を表す。順序や重複を強制せず、有限リストに限定しない。有限モデルによる検査を全理由領域についての証明とはしない。',
    'rggの完全性は同じ判断・状況における使用理由の範囲についてである。既知の例だけを閉じた世界とみなさず、使用関係が未知なら不使用で補わない。',
]


def generic_composed():
    doc=parse('n:'+definitions())
    basis=dict(version='institutional-grounds-basis-v1',document='examples/v014/institutional-grounds.noema',
        primitives=[],definitions=MEANINGS,unresolved=LIMITS)
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/kant-institutional-voice-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    text=definitions()
    for name,base in (('hzbs','rge'),('hzbt','rgf'),('hzbu','rgg')):
        extra=['p fd'] if base=='rgf' else []
        text+=definition(name,params(CORE+[('institutional',INSTITUTIONAL)]),
            k(base,*args(CORE),v('institutional'),'p fb','p hzv','p fc',*extra))
    text+=definition('hzbv',params(SETTINGS+[('institutional',INSTITUTIONAL)]),
        k('rgh',*args(SETTINGS),v('institutional'),'p fb','p hzv','p fc'),'h[a] f')
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis.update(version='kant-institutional-grounds-basis-v1',document='examples/v014/kant-institutional-grounds.noema')
    basis['definitions'].update(MEANINGS|{
        'hzbs':'rgeを既存の判断対象fb・発話内容への判断hzv・理由の使用fcへ結ぶ。組織への帰属と指示された理由範囲を明示し、別の判断の理由を混ぜない。',
        'hzbt':'hzbsに既存fdの支持評価を加える。原文の組織の報告を、その支持が実際に成立するという断言に読み替えない。',
        'hzbu':'hzbsの同じ判断・状況で用いられる理由が、指示された理由範囲で尽くされるというrggへ接続する。',
        'hzbv':'hzbuの組織・判断・発話記述・理由範囲を固定し、対象を受けて、これらが用いられる理由であると主張する発話を作る。前版の組織の教示の報告と同じ内側の発話記述を共有できる。',
    })
    basis['unresolved']+=LIMITS+[
        'u0012のdas sind die Beweisgründe, deren sie sich bedientへ部分接続する。dieを、文脈で固定した同じ判断に使う理由を尽くす一覧として読む候補を明示する。全場面にわたる唯一の読解としない。',
        'Beweisgründeの証明としての地位、具体的な理由の内容と推論規則、集団の指示と判断形成、原文のdieses oder jenesの不特定性やwird sagenの予想は未完。',
        '前版の教示報告と今回の理由報告は別の発話記述として結べる。片方の実際の真偽から他方を導かず、本人の信念・賛同・内側の真理・実際の発言も補わない。',
        '新たな原始概念・局所参照・著者主張は追加しない。自由な裁量・良心・辞職の条件と全文の意味一致は残る。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=['hzbs','hzbt','hzbu','hzbv','rgd','hzbp'],statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='institutional-grounds-core-basis-v1',document_path='examples/v014/institutional-grounds-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


BUILDERS=((generic_composed,'institutional-grounds'),(source_composed,'kant-institutional-grounds'),(core_composed,'institutional-grounds-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored institutional grounds differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
