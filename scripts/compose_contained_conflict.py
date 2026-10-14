"""Compose contained opposition, scoped consistency and non-factive judgments."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args
from scripts.compose_unsettled_teaching import CONTAINS,CONTENTS,SPEECH

PARENT='examples/v014/kant-unsettled-teaching.noema'
SCOPE='h[d d] c'
CLASHES='h[a a d] c'
CANDIDATES='h[a a a d d] c'
LOGIC=[('anchor','d'),('scope',SCOPE),('contains',CONTAINS),('contents',CONTENTS)]
SATISFIES=[('document','a'),('point','d'),('anchor','d'),('contains',CONTAINS),('contents',CONTENTS)]
COHERENT=[('document','a')]+LOGIC
JOINT=[('document','a'),('standard','a')]+LOGIC
PART=[('claim','a'),('standard','a')]+LOGIC
CONFLICT=[('document','a'),('standard','a'),('anchor','d'),('point','d'),('contains',CONTAINS),('clashes',CLASHES)]
BELIEF=[('person','a'),('document','a'),('standard','a'),('anchor','d'),('contains',CONTAINS),('clashes',CLASHES),('candidates',CANDIDATES)]
SPEECH_FIELDS=SPEECH+[('standard','a'),('clashes',CLASHES)]
ROOTS=['rgq','rgr','rgs','rgt','rgu','rgv','rgw','rgx','rgy','rgz','rg2']


def definitions():
    member=app(v('contains'),v('document'),v('claim'),v('anchor'))
    truth=op('t',app(v('contents'),v('claim')),v('point'))
    selected=app(v('scope'),v('anchor'),v('point'))
    satisfied=k('rgq',*args(SATISFIES))
    standard=k('rgq',*args(SATISFIES,document=v('standard')))
    text=definition('rgq',params(SATISFIES),quant('f','claim','a',op('y',member,truth)))
    text+=definition('rgr',params(COHERENT),quant('g','point','d',both(selected,satisfied)))
    text+=definition('rgs',params(JOINT),quant('g','point','d',both(selected,satisfied,standard)))
    text+=definition('rgt',params(JOINT),both(k('rgr',*args(COHERENT)),
        k('rgr',*args(COHERENT,document=v('standard'))),op('u',k('rgs',*args(JOINT)))))
    text+=definition('rgz',params(PART),both(quant('g','point','d',both(selected,truth)),
        k('rgr',*args(COHERENT,document=v('standard'))),
        op('u',quant('g','point','d',both(selected,truth,standard)))))
    text+=definition('rg2',params(LOGIC[1:]),'i[claim a standard a anchor d]['+k('rgz',*args(PART))+']',CLASHES)
    clash=app(v('clashes'),v('claim'),v('standard'),v('point'))
    text+=definition('rgu',params(CONFLICT),quant('g','claim','a',both(member,clash)))
    text+=definition('rgv',params(CONFLICT),op('u',k('rgu',*args(CONFLICT))))
    # Membership is fixed at the anchor; candidate situations evaluate clashes.
    cases='i[who a here d there d]['+app(v('candidates'),v('who'),v('document'),v('standard'),v('here'),v('there'))+']'
    some='i[who a][b point['+k('rgu',*args(CONFLICT))+']]'
    none='i[who a][b point['+k('rgv',*args(CONFLICT))+']]'
    one='i[who a][b point['+clash+']]'
    text+=definition('rgw',params(BELIEF),k('rn',v('person'),some,v('anchor'),cases))
    text+=definition('rgx',params(BELIEF),quant('g','claim','a',both(member,k('rn',v('person'),one,v('anchor'),cases))))
    text+=definition('rgy',params(BELIEF),k('rn',v('person'),none,v('anchor'),cases))
    return text


MEANINGS={
    'rgq':'基準文脈で対象に含まれる命題的部分が、評価状況で全て真である。既知の空集合なら真。含まれる規範・命令を自動的に真偽命題へ変換しない。',
    'rgr':'同じ基準文脈の指定範囲内に、対象の全命題的部分が真になる状況がある。指定範囲での充足可能性であり、現在の真理や全可能状況についての整合性ではない。',
    'rgs':'指定範囲内の同じ一状況で、対象と基準の全命題的部分が共に真となる。各部分ごとに異なる証人を選ぶ条件と区別する。',
    'rgt':'対象と基準が指定範囲内でそれぞれ充足可能だが、共通の充足状況はない。自己矛盾する対象や空の範囲を、二対象間の対立の証拠にしない。',
    'rgz':'一つの命題的部分と基準が指定範囲でそれぞれ充足可能で、共通の充足状況がない。その範囲で両立しないという限定付きの論理的解釈。',
    'rg2':'rgzを、部分・基準・評価文脈の対立関係として渡す関数を作る。範囲の選択、命題的所属、内容は明示した引数を保つ。宗教や良心における対立の意味全体と同一視しない。',
    'rgu':'基準文脈で対象に含まれる部分のうち、評価状況において指定基準と対立するものが存在する。対立関係の解釈を明示的に受け取る。',
    'rgv':'基準文脈で対象に含まれるどの部分も、評価状況で指定基準と対立しない。既知の空集合なら真だが、未知の所属や対立関係を空集合・偽で補わない。全体の共同充足可能性は含意しない。',
    'rgw':'本人・対象・基準・基準文脈について選んだ判断候補が非空で、どの候補でも対立する部分がある。候補ごとに対立の証人となる部分が異なってよい。現実の対立は含意しない。',
    'rgx':'基準文脈で対象に含まれる同じ一部分が、非空の全判断候補で基準と対立する。rgwの各候補で何かが対立する条件より強い。',
    'rgy':'非空の全判断候補で、対象に対立する部分が含まれない。rgwを否定しただけの、対立を確信していない状態とは別である。',
}
LIMITS=[
    '内的宗教の概念、何をその内容とするか、規範的な対立、良心との適合の実質的な定義は未完。clashesを引数とし、任意の評価結果を普遍的な対立の意味と宣言しない。',
    'rgqからrg2までの充足条件は、明示した範囲における命題的解釈である。範囲の完全性は別に必要で、有限検査を全可能世界の論理的矛盾の証明とは扱わない。',
    '各部分の対立がないことと、全体が基準と同時に充足可能であることを区別する。自己矛盾や空範囲では、対立の不成立から両立を結論しない。',
    'rgw・rgx・rgyは質的な判断候補モデルである。見つける行為、実際の調査、記述の認識、確信度、矛盾した信念の一般理論は未記述。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/kant-unsettled-teaching-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    text=definitions()+definition('hzbx',params(SPEECH_FIELDS),both(k('hzbw',*args(SPEECH)),
        k('rgv',*args(CONFLICT,anchor=v('context'),point=v('context')))))
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis.update(version='kant-contained-conflict-basis-v1',document='examples/v014/kant-contained-conflict.noema')
    basis['definitions'].update(MEANINGS|{'hzbx':'前版の職務上の提示と賛同の不足・真理の可能性に、同じ規定群には指定基準と対立する部分がない条件を接続する。基準は内的宗教として解釈する引数で、良心に適う職務遂行や辞職の義務をここから導かない。'})
    basis['unresolved']+=LIMITS+[
        'u0012のnichts ... widersprechendesを部分ごとの対立の不在として記述する。auf alle Fälle、wenigstens、dochの範囲・焦点や内的宗教の同定、原文全文の意味一致は未完。',
        'glaubte er das letztere darin zu findenの判断内容を、同じ対象・基準に対する対立する部分の存在として部分記述する。仮定節、良心に適う職務遂行不能、辞職の要求への接続は未完。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=roots,statement_indices=[])
    projected_basis=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',projected_basis


def generic_composed():return projected(ROOTS,'contained-conflict')
def core_composed():return projected(ROOTS+['hzbx'],'contained-conflict-core')
BUILDERS=((generic_composed,'contained-conflict'),(source_composed,'kant-contained-conflict'),(core_composed,'contained-conflict-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored contained conflict differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
