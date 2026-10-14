"""Bind a past appointment to its terms without deriving a present obligation."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, both, quant
from scripts.compose_situated_criticism import params, args

PARENT = 'examples/v014/kant-adopted-standards.noema'
TARGET = 'i[h[a a] e]'
APPOINTS = 'h[a a a a d] c'
TERMS = 'h[a a '+TARGET+' c d] c'
REQUIRED = 'h[a a a a '+TARGET+' c d] c'
FIELDS = [('event','a'),('issuer','a'),('person','a'),('role','a'),('activity','a'),
    ('target',TARGET),('polarity','c'),('earlier','d'),('context','d')]
OPEN_FIELDS = [(name,sort) for name,sort in FIELDS if name not in ('event','earlier')]
RECORDS = [('appoints',APPOINTS),('terms',TERMS)]
RELATIONS = [('history','h[d] c'),('precedes','h[d d] c'),('occurs','h[a d] c'),
    ('entrusted','h[a a d] c')]+RECORDS


def definitions():
    temporal = both(k('ta',v('history'),v('precedes')),
        app(v('history'),v('earlier')),app(v('history'),v('context')),
        app(v('precedes'),v('earlier'),v('context')))
    record = both(app(v('occurs'),v('event'),v('earlier')),
        app(v('entrusted'),v('person'),v('role'),v('earlier')),
        app(v('appoints'),*map(v,('event','issuer','person','role','earlier'))),
        app(v('terms'),*map(v,('event','activity','target','polarity','earlier'))))
    text = definition('rfx',params(FIELDS+RELATIONS),both(temporal,record))
    witness = quant('g','event','a',quant('g','earlier','d',k('rfx',*args(FIELDS+RELATIONS))))
    text += definition('rfy',params(OPEN_FIELDS+RELATIONS),witness)
    norm = app(v('required'),*map(v,('issuer','person','role','activity','target','polarity','context')))
    text += definition('rfz',params(OPEN_FIELDS+RELATIONS+[('required',REQUIRED)]),
        both(k('rfy',*args(OPEN_FIELDS+RELATIONS)),norm))
    return text


MEANINGS = {
    'rfx':'指定した同じ履歴の現在より前に、生起した同じ任用行為が、同じ出所から同じ本人へ同じ職務を委ね、その行為の条件に同じ活動・目標記述・極性が含まれる。現在の要求や履行を推定せず、任用の内容と時点を一つの証人へ結ぶ。',
    'rfy':'rfxを満たす過去の任用行為と時点が存在する。行為と時点の同じ組を全条件で共有する。一意性・最初の任用・任期・本人の同意・現在までの継続を要求しない。',
    'rfz':'rfyの過去の任用があり、同じ出所・本人・職務・活動・目標記述・極性について現在の要求もある。過去の任用から現在の要求を導出する規則ではない。',
}
LIMITS = [
    'appointsは生起する任用行為・出所・本人・職務・時点の関係、termsはその同じ行為に付された活動・目標記述・極性・時点の関係として渡す。両入力の制度的成立や一般的な任用制度の構成説明は残る。',
    '条件とは任用に付された実行上の約束事を指す。目標を任用前に履行済みであること、本人の承諾、採用資格、試験合格、契約の法的有効性を同一視しない。',
    '目標記述を脱引用せず同じ値で保持する。虚偽や未評価の内容も条件として記述でき、要求の正当性・能力・実際の遂行・本人の信念は付けない。',
    '存在する行為と過去時点を一つの組として結ぶ。異なる任用の条件と職務を混ぜず、現在や将来の任用だけで過去の事実を満たさない。再任は排除しない。',
    '任用条件のうち指定した一活動への目標を扱う。全ての将来の教示への適用範囲、期間・例外・解除・辞職は別に記述する必要がある。',
]


def source_composed():
    doc = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT/'data/kant-adopted-standards-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements'] = doc['statements'],[]
    history = 'i[point d][k ia[v person v context v point]]'
    precedes = 'i[first d second d][k ic[v first v second v context]]'
    relations = [history,precedes,'p dg','p cf',v('appoints'),v('terms')]
    text = definitions()
    text += definition('hzbl',params(FIELDS+RECORDS),k('rfx',*args(FIELDS),*relations))
    text += definition('hzbm',params(OPEN_FIELDS+RECORDS),k('rfy',*args(OPEN_FIELDS),*relations))
    text += definition('hzbn',params(OPEN_FIELDS+RECORDS),k('rfz',*args(OPEN_FIELDS),*relations,'p h7a'))
    doc = parse(format_graph(doc,'compact')+text);doc['statements'] = statements
    basis.update(version='kant-appointment-terms-basis-v1',document='examples/v014/kant-appointment-terms.noema')
    basis['definitions'].update(MEANINGS | {
        'hzbl':'任用条件rfxを同じ本人の履歴ia・順序ic・行為の生起dg・職務の委任cfへ接続する。任用と付された条件の関係は引数で明示する。',
        'hzbm':'同じ人物の履歴で、hzblに相当する任用行為と時点が存在するという過去の事実。現在の任用状態・義務・講義の実行を要求しない。',
        'hzbn':'同じ目標記述を持つ過去の任用条件と現在のh7aの要求が併存する。教示の記述を渡せるが、受任を義務の正当化とするdennの説明関係は含めない。',
    })
    basis['unresolved'] += LIMITS + [
        'u0012のer ist auf diese Bedingung angenommen wordenへ部分接続する。先行する教示と同じ目標記述を条件にも要求にも渡す。過去の任用の具体的な日時・行為者名は補わない。',
        '条件付き任用という部分構造であり、教会・聖職者・教理の名詞全体、dennによる規範的な説明、良心・辞職・全文の意味一致は未完。',
        '新しい原始概念・局所参照・著者主張は追加しない。引数の任用・条件関係を未知なら未知のまま保持し、cfと現在の要求だけから過去の任用記録を作らない。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis = source_composed();doc = parse(text)
    selected = extract_document(doc,roots=roots,statement_indices=[])
    projected_basis = extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',projected_basis


def generic_composed():
    return projected(['rfx','rfy','rfz'],'appointment-terms')


def core_composed():
    return projected(['hzbl','hzbm','hzbn'],'appointment-terms-core')


BUILDERS = ((generic_composed,'appointment-terms'),(source_composed,'kant-appointment-terms'),(core_composed,'appointment-terms-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis = builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path = ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored appointment differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
