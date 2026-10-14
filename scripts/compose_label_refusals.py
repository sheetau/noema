"""Distinguish declining a designation from denying its descriptive content."""
from copy import deepcopy
import json
from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args

PARENT = 'examples/v014/kant-action-standards.noema'
NAMING = [('occurs', 'h[a d] c'), ('presents', 'h[a a d] c'), ('assigns', 'h[a a a d] c')]
USE = [('speaker','a'), ('activity','a'), ('label','a'), ('subject','a'), ('context','d')] + NAMING
SETTINGS = [('label','a'), ('users','h[a] c')] + NAMING
SOURCE_SETTINGS = [('label','a'), ('users','h[a] c'), ('assigns','h[a a a d] c')]
ROOTS = ['rnh','rni','rnj']


def definitions():
    text = definition('rnh', params(USE), both(app(v('occurs'), v('activity'), v('context')),
        app(v('presents'), v('speaker'), v('activity'), v('context')),
        app(v('assigns'), v('activity'), v('label'), v('subject'), v('context'))))
    unused = quant('f','speaker','a',op('y',app(v('users'),v('speaker')),
        op('u',quant('g','activity','a',k('rnh',*args(USE))))))
    content = both(quant('g','speaker','a',app(v('users'),v('speaker'))),unused)
    text += definition('rni',params(SETTINGS),'i[subject a][b context['+content+']]', 'h[a] e')
    text += definition('rnj',params(SETTINGS),'i[subject a][j m['+app(k('rni',*args(SETTINGS)),v('subject'))+']]', 'h[a] f')
    return text

MEANINGS = {
    'rnh':'同じ発話行為が生起し、同じ提示者がその行為で指定した名称を同じ対象へ適用する。名称は個体として識別し、名称の表す性質やその真偽とは別に保持する。',
    'rni':'明示した非空の名称使用者の範囲に、同じ対象を同じ名称で呼ぶrnhの行為がないという内容。対象から内容への関数であり、拒否する意思や表明そのものではない。',
    'rnj':'同じ対象についてrniの不使用を実現するよう促す発話。現在その名称が使われていないという主張や、対象が名称の表す性質を持たないという主張と区別する。',
    'hzfv':'rniの名称使用を既存の生起dgと提示者f3へ接続する。名称適用関係と対象となる使用者の範囲は引数で明示する。',
    'hzfw':'hzfvと同じ内容への呼びかけ。閉じた記述をhzftへ渡す接続例では、同じ本人について指定名称を使わないよう求める表明になる。',
}
LIMITS = [
    '名称を拒むことのうち、自分にその名称を使わないよう求める伝達的な形を構成する。内心で受け入れない態度、非言語的な拒絶、制度的な称号返上の全てを表したとはしない。',
    '名称個体と名称の適用行為を分離する。名称の綴り、音声、文字列、同名異義、社会的慣習と概念定義の対応は別途説明が必要であり、原語文字列をそのまま意味の代用にしない。',
    'assignsは行為・名称・対象・文脈を結ぶ明示的な入力関係で、単に名称に言及することではない。提示媒体や名付け慣習の構成的説明は未完である。',
    '不使用を求める相手の範囲と実際の受け手は別引数である。接続例では同じ範囲を渡すが、型だけで一致を強制しない。空の範囲で不使用達成を認定しない。',
    '内容は各評価状況における不使用であり、将来の永続や過去の全履歴を含めない。呼びかけの提示から相手の服従・理解・合意、名称の不適切さや性質の偽を導かない。',
    'u0015の名称拒否への部分注記。寛容の社会的意味、その名称が傲慢とされる評価とその帰属、alsoの論証関係、自らという強調、称賛と段落全体の意味確認は残る。原始記号と著者主張は追加しない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    for name,target,result in (('hzfv','rni','h[a] e'),('hzfw','rnj','h[a] f')):
        text += definition(name,params(SOURCE_SETTINGS),k(target,*args(SETTINGS,occurs='p dg',presents='p f3')),result)
    doc = parse(format_graph(doc,'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-action-standards-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-label-refusals-basis-v1',document='examples/v014/kant-label-refusals.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved'] += LIMITS
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed(): return projected(ROOTS+['rnc'],'label-refusals')
def core_composed(): return projected(ROOTS+['rnc','hzft','hzfv','hzfw'],'label-refusals-core')
BUILDERS=((generic_composed,'label-refusals'),(source_composed,'kant-label-refusals'),(core_composed,'label-refusals-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body: raise ValueError('Stored label refusal differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream: stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__': main()
