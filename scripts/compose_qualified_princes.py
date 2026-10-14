"""Compose relative-clause qualifications and a non-existential general claim."""
from copy import deepcopy
import json
from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/kant-scoped-refusal-arguments.noema'
QUALIFIERS=[('head','h[a] e'),('appraised','h[a] e'),('refused','h[a] e')]
GENERAL=[('qualifies','h[a] e'),('conclusion','h[a] e')]
ROOTS=['rnz','ro2','ro3','ro4']


def definitions():
    at=lambda expr:op('t',expr,v('context'))
    same=both(*(at(app(v(name),v('person'))) for name,_ in QUALIFIERS))
    text=definition('rnz',params(QUALIFIERS),'i[person a][b context['+same+']]','h[a] e')
    qualifies=at(app(v('qualifies'),v('person')))
    consequence=at(app(v('conclusion'),v('person')))
    text+=definition('ro2',params(GENERAL),'b context['+quant('f','person','a',op('y',qualifies,consequence))+']','e')
    text+=definition('ro3','qualifies h[a] e','b context['+quant('g','person','a',qualifies)+']','e')
    text+=definition('ro4',params(GENERAL),'b context['+quant('g','person','a',both(qualifies,op('u',consequence)))+']','e')
    return text

MEANINGS={
    'rnz':'三つの内容関数を同じ本人・文脈へ適用する制限条件。接続例では地位、発言についての本人の評価、本人による名称拒否を結ぶ。三条件を別人から集めない。',
    'ro2':'同じ文脈の全個体について、指定制限条件を満たすなら指定結論内容を満たすという一般条件。該当者の存在や特定個体への適用は断言しない。',
    'ro3':'指定制限条件を同じ文脈で満たす個体が少なくとも一つあるという存在内容。一般条件ro2から分離する。',
    'ro4':'同じ文脈で、制限条件を満たし結論を満たさない個体があるという反例内容。別人の不成立や別時点を反例に使わない。',
    'hzf7':'rnzの同じ人物に対する三条件から、既存h4lの評価済みで指導なしに自分の理解力を使えるという内容へro2を接続する。啓蒙された君主という評価への部分候補。',
    'hzga':'hzf7を主張発話として構成する。発話内容・著者帰属・内容の真偽を区別し、構成自体から実際の発話や該当者の存在を導かない。',
}
LIMITS=[
    '君主についての不定名詞句と関係節を一般的な条件文として読む接続候補。原文の唯一の解釈や厳密な必要十分条件とはしない。特定君主の実在や前提の実現を追加しない。',
    '地位の条件は既存hzfnの唯一の最高役職保持者という部分構造であり、国家・世襲・正当性の全意味は未完。接続例は明示した組織と役職の範囲に限り、世界の全君主を網羅したとしない。',
    '本人の品位判断は既存rngとhzfrによる明示基準への本人の判断を使う。発言の実行、本人の内側の義務判断の真偽、実際の義務、自由政策の実現を前件に追加しない。',
    '名称拒否は既存hzfwとhzftへの接続で、同じ本人についての名称適用をしないよう求める表明として扱う。傲慢の評価、自らの強調、非言語的拒否などの全語用は未完。',
    '結論のh4lは他者の指導なしに自分の理解力を使う能力の構成候補。自律・決意・学識・政治的な啓蒙などの全側面を網羅した定義ではない。',
    'ro2は明示された評価文脈ごとの条件であり、未来・過去・全可能世界を量化しない。条件を満たす個体がなければ空虚に真となり、ro3で存在を別途検査する。',
    '著者帰属は既存ucに閉じた内容記述を渡して行う。真の一般条件だけから著者帰属を推定せず、帰属があっても内容を真にしない。称賛に値すること、解放の功績、後続本文と全文の意味確認は残る。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=definitions()
    text+=definition('hzf7',params(QUALIFIERS),k('ro2',k('rnz',*args(QUALIFIERS)),'p h4l'),'e')
    text+=definition('hzga',params(QUALIFIERS),'j s['+k('hzf7',*args(QUALIFIERS))+']','f')
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-scoped-refusal-arguments-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-qualified-princes-basis-v1',document='examples/v014/kant-qualified-princes.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS,'qualified-princes')
def core_composed():
    previous=parse((ROOT/'examples/v014/action-standards-core.noema').read_text(encoding='utf-8'))
    roots=[d['name'] for d in previous['declarations']]+ROOTS+['hzf7','hzga','hzfw','uc']
    return projected(roots,'qualified-princes-core')
BUILDERS=((generic_composed,'qualified-princes'),(source_composed,'kant-qualified-princes'),(core_composed,'qualified-princes-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored qualified-prince artifact differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
