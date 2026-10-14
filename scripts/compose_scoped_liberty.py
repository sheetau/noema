"""Quantify described permissions without collapsing restriction and its duty."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_described_norms import DESCRIPTION, RULE, TRUE

PARENT = 'examples/v014/kant-speech-principals.noema'
SCOPE = 'h[a a a d] c'
TARGETS = 'h[a] ' + DESCRIPTION
FIELDS = [('source','a'),('person','a'),('role','a'),('context','d'),('scope',SCOPE),('targets',TARGETS),('required',RULE),('allowed',RULE)]
PAIR = [('officesource','a'),('publicsource','a'),('person','a'),('officerole','a'),('publicrole','a'),('context','d'),
        ('officescope',SCOPE),('publicscope',SCOPE),('officetargets',TARGETS),('publictargets',TARGETS),('required',RULE),('allowed',RULE)]
OUTER = [('assessor','a'),('regulator','a'),('office','a'),('regime','a'),('person','a'),('role','a'),('context','d')]
ROOTS = ['rhi','rhj','rhk','rhl','rhm','rhn','rho']
SOURCE_ROOTS = ['hzb6','hzb7','hzca','hzcb','hzcc','hzcd']


def definitions():
    scope = app(v('scope'), v('person'), v('activity'), v('role'), v('context'))
    target = app(v('targets'), v('activity'))
    normargs = [v('source'),v('person'),v('role'),v('activity'),target,TRUE,v('context'),v('required'),v('allowed')]
    nonempty = quant('g','activity','a',scope)
    text = definition('rhi',params(FIELDS),quant('f','activity','a',op('y',scope,k('rdm',*normargs))))
    text += definition('rhj',params(FIELDS),both(nonempty,k('rhi',*args(FIELDS))))
    for name, condition in (
        ('rhk',k('rdy',*normargs)),
        ('rhl',k('rdx',*normargs)),
        ('rhm',both(op('u',k('rdx',*normargs)),op('u',k('rdz',*normargs))))):
        text += definition(name,params(FIELDS),quant('g','activity','a',both(scope,condition)))
    opposite = list(normargs); opposite[5] = op('u',TRUE)
    text += definition('rhn',params(FIELDS),both(nonempty,quant('f','activity','a',op('y',scope,
        both(k('rdm',*normargs),k('rdm',*opposite))))))
    def side(prefix):
        return args(FIELDS,**{n:v(prefix+n) for n in ('source','role','scope','targets')})
    text += definition('rho',params(PAIR),both(k('rhk',*side('office')),k('rhj',*side('public'))))
    return text


MEANINGS = {
    'rhi':'指定した本人・役割・文脈の活動範囲の全対象について、それぞれに割り当てた実行記述への積極的な許可が同じ出所からあり、不実行要求と衝突しない。空範囲では全称として成立する。',
    'rhj':'rhiが成立し、同じ分類範囲に少なくとも一つ活動がある。活動の実行・達成可能性・許可の正当性は要求しない。',
    'rhk':'指定した範囲内の少なくとも一つの活動について、同じ記述への不実行要求があり、実行要求も実行許可もない。明示的で衝突のない禁止の存在であり、全活動の禁止ではない。',
    'rhl':'指定した範囲内に、同じ対象の両極性の要求、または許可と反対要求の衝突が少なくとも一つある。出所や記述の違う規範を混ぜない。',
    'rhm':'指定した範囲内に、規範は解釈済みで衝突もないが、実行への積極的な許可にも明示的な禁止にも分類できない活動がある。未解釈の入力とは別である。',
    'rhn':'範囲が非空で、全対象について実行・不実行の両方が積極的に許可され、それぞれ反対要求がない。実行してよいというrhiより強い選択条件であり、公的使用の自由に自動追加しない。',
    'rho':'同じ本人・文脈について、一方の役割・出所・活動範囲にはrhkの明示的な制限があり、もう一方にはrhjの全対象への許可がある。二つの出所・役割・対象記述の割当を別に保持し、現実の発言を要求しない。',
}
LIMITS = [
    'targetsは活動ごとの閉じた実行記述を渡す関数である。個々の記述・活動・本人・役割・出所を規範の対象として保持し、同義の別名への規範移送をしない。対応の正当性は引数の意味規約に依存する。',
    'scopeは実行済みの出来事だけを選ぶ条件ではない。実行されなかった活動も同じ分類を満たせば量化する。有限解釈の検査を、全ての現実の選択肢の網羅の証明とは扱わない。',
    '規範的な全称許可、存在する禁止、規範衝突、解釈済みの未分類状態を区別する。許可が全範囲にないことだけから禁止や衝突を推定しない。',
    'rhiは実行への許可であり、不実行を選べることも、あらゆる意味での自由も含めない。rhnはより強い別条件として保持する。自由意思、能力、権利の正当性、規範間の優先順位は未完。',
]


def source_composed():
    doc = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT/'data/kant-speech-principals-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements'] = doc['statements'],[]
    text = definitions()
    fixed = dict(targets='i[activity a][r[p zzq]]',required='p h7a',allowed='p h7b')
    for name,target,scope in (('hzb6','rhi','zzp'),('hzb7','rhk','zzp'),('hzca','rhj','zzo')):
        text += definition(name,params(FIELDS[:4]),k(target,*args(FIELDS,scope='p '+scope,**fixed)))
    text += definition('hzcb',params(PAIR[:6]),k('rho',*args(PAIR,officescope='p zzp',publicscope='p zzo',
        officetargets=fixed['targets'],publictargets=fixed['targets'],required='p h7a',allowed='p h7b')))
    body = both(k('h7g',v('bindings')),
        'a[v bindings][n p a b][v source]', 'a[v bindings][n p b b][v person]', 'a[v bindings][n p c b][v role]',
        k('hzb6',v('source'),v('person'),v('role'),v('context')))
    for name in reversed(('source','person','role')): body=quant('g',name,'a',body)
    text += definition('hzcc','bindings j[a]','b context['+body+']','e')
    text += definition('hzcd',params(OUTER),k('rds',v('assessor'),v('regulator'),v('office'),'r[p hzcc]',
        'l[a][v regime v person v role]',op('u',TRUE),v('context'),'p h7g','p h7k','p h7l'))
    doc = parse(format_graph(doc,'compact')+text); doc['statements']=statements
    basis.update(version='kant-scoped-liberty-basis-v1',document='examples/v014/kant-scoped-liberty.noema')
    basis['definitions'].update(MEANINGS | {
        'hzb6':'同じ本人・職務で私的使用zzpに分類される全活動について、既存の実行記述zzqへの積極的な許可があり不実行要求と衝突しない。空範囲は成立する。職務内の裁量の一つの操作的条件であり、自由の完全な定義ではない。',
        'hzb7':'同じ本人・職務で私的使用zzpに分類される活動のうち、実行記述zzqについて衝突のない明示的な禁止がある。許可の不在や未実行を制限の代用にしない。',
        'hzca':'同じ本人・立場で公的使用zzoに分類される活動が非空で、その全てに実行記述zzqへの積極的な許可があり不実行要求と衝突しない。実行しないことの選択や公衆全員への到達を要求しない。',
        'hzcb':'同じ本人・文脈の職務側のhzb7と、公的使用側のhzcaを併記する。職務上の発言全てを禁じず、公的活動を実際にしたかどうかを量化の選択基準にしない。',
        'hzcc':'個体列の順に内側の規範の出所・本人・役割を取り、hzb6の全称許可状態を内容として返す。ちょうど三引数を必要とし、過不足のある列を切り詰めない。',
        'hzcd':'外側の出所が規制者にその職務で、指定した内側の出所・本人・役割へのhzccの全称許可状態を成立させないよう要求する。対象政策は引用したままで評価せず、現実の制限が既にあることも、その要求の正当性も補わない。',
    })
    basis['unresolved'] += LIMITS + [
        'u0012のnicht freiとdarf es auch nicht seinを、実際の規範状態とそれを対象にする外側の規範に分ける。原文の自由の語義全体をhzb6の全称許可と同一と確定したわけではなく、採用する操作的な読みとして部分接続する。',
        'u0012のuneingeschränkte Freiheitについて公的な活動全体を量化するが、任意の記述・全規範源・全状況の権利保障を完成させたわけではない。既存のh7dより存在条件を強くしたhzcaを別定義として残し、旧主張は置き換えない。',
        '外側の禁止はhzccを満たすことへの否定的要求であり、個々の私的活動への禁止を意味しない。内側に許可がないだけでもhzccは偽になりうるため、外側の要求からhzb7を推論しない。',
        '役割・公衆の基本的意味、委任を理由にする説明、当事者の自律・裁量・権利、規範の出所の原文上の同定と正当性は未完。新しい原始概念・著者主張は追加しない。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS,'scoped-liberty')
def core_composed():return projected(ROOTS+SOURCE_ROOTS,'scoped-liberty-core')
BUILDERS=((generic_composed,'scoped-liberty'),(source_composed,'kant-scoped-liberty'),(core_composed,'scoped-liberty-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored scoped liberty differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
