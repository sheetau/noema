"""Keep normative constraints, practical control and personal aims distinct."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both
from scripts.compose_situated_criticism import params
from scripts.compose_qualified_utterance import closure
from scripts.compose_outcome_choice import MODEL,PROVIDERS,fold,TRUE,FALSE
from scripts.compose_policy_norms import DESCRIPTION,RULE
from scripts.compose_parameterized_goals import AIMS

PARENT='examples/v016/kant-outcome-choice.noema'
PARENT_BASIS='data/outcome-choice-basis-v1.json'
FULL='examples/v016/kant-norm-bound-choice.noema'
LIBRARY='examples/v016/norm-bound-choice.noema'
BASIS='data/norm-bound-choice-basis-v1.json'
READING='data/norm-bound-choice-reading-v1.json'
ASSESSED='h[a a a '+DESCRIPTION+' j[a] d] c'
NORM=[('source','a'),('person','a'),('target','a'),('role','a'),('point','d'),('code',DESCRIPTION),
    ('normchecked',ASSESSED),('required',RULE),('allowed',RULE)]
BASE=NORM+MODEL
ITEM=[('method','a'),('wanted','a')]+BASE
GOAL=[('aims',AIMS)]
CONTEXT=NORM+PROVIDERS+GOAL


def av(fields):return [v(n) for n,t in fields]


def bindings():return 'l[a][v person v target v wanted]'


def assessment():
    return app(v('normchecked'),v('source'),v('person'),v('role'),v('code'),bindings(),v('point'))


def definitions():
    text=definition('rqqi',params(BASE),both(k('rqqa',*av(MODEL)),fold(v('outcomes'),'wanted',assessment())))
    def norm(name,sign):return k(name,v('source'),v('person'),v('role'),v('code'),bindings(),sign,v('point'),
        'p h7g',v('required'),v('allowed'))
    ability=k('rqqb',v('method'),v('wanted'),*av(MODEL))
    text+=definition('rqqj',params(ITEM),both(ability,assessment(),norm('rds',FALSE)))
    text+=definition('rqqk',params(ITEM),both(ability,assessment(),norm('rdu',TRUE)))
    aim=app(v('aims'),v('person'),v('method'),v('code'),bindings(),v('point'))
    text+=definition('rqql',params(ITEM+GOAL),both(k('rqqj',*av(ITEM)),aim))
    def some(symbol,fields):return fold(v('outcomes'),'wanted',fold(v('methods'),'method',k(symbol,*av(fields)),False),False)
    text+=definition('rqqm',params(BASE+GOAL),some('rqql',ITEM+GOAL))
    text+=definition('rqqn',params(BASE),both(k('rqqi',*av(BASE)),op('u',some('rqqj',ITEM))))
    contextual=[app(v(n),v('person'),v('target'),v('point')) for n,t in MODEL]
    text+=definition('rqqo',params(CONTEXT),k('rqqm',*av(NORM),*contextual,*av(GOAL)))
    return text


MEANINGS={
    'rqqi':'可能結果モデルが有効であり、同じ出所・本人・立場・内容記述・基準状況について、本人・対象・各結果という三個体の順序付き引数に対する規範評価が全結果で済んでいる。',
    'rqqj':'指定した一つの方法が同じ目標結果を全応答で保証し、その結果の同じ内容記述と本人・対象・結果の束縛について、不成立が要求されている。禁止されていても実現可能な方法を区別する。',
    'rqqk':'rqqjと同じ方法・結果・規範対象について、実現能力があり、成立が積極的に許可され、不成立の要求はない。要求の欠落だけを積極的な許可としない。',
    'rqql':'rqqjの同じ本人が、その同じ方法で、その同じ結果記述と引数の内容を目指している。別の方法の目的や別人の願望を、その禁止結果を実現する目的と混ぜない。',
    'rqqm':'同じモデル・規範範囲・本人・対象について、rqqlを満たす方法と結果が少なくとも一組ある。禁止に反する目的と実現能力が結び付いているという存在条件。',
    'rqqn':'rqqiの全結果の規範評価を要求し、どの方法も禁止された結果を保証しない。未知の規範、無効な可能結果モデル、空範囲を実効的な制限の証拠としない。',
    'rqqo':'規範の名宛人・結果の対象・評価時点と同じ三者を用いて可能結果モデルの全設定を取得し、rqqmを評価する。別人・別対象・別時点のモデルへ暗黙に切り替えない。',
}
LIMITS=[
    'codeは本人・対象・結果の三個体を順に受け取る内容関数の閉じた記述。規範と目的で同じ記述・同じ引数を使う。意味が同じだけの別名の記述へ規範を移さない。三個体を受け取る長さは既存h7gで検査するが、結果識別子と内容の対応自体は同じ意味規約を要する。',
    'sourceは選んだ規範の出所、roleは名宛人の立場。公的な規範の出所として使うには、公的制度とその権限・適用範囲を別途記述する。この構造だけで任意の要求を公法と認定しない。',
    'aimsは本人がその方法・計画で同じ内容を目指す関係。私的な目的を公的意思と区別して記述できるが、利己性・悪意・感情や合理性を自動的に付け加えない。',
    'rqqjは不成立の要求があれば成立し、相反する成立要求の併存を除かない。rqqkは不成立要求がある場合に不成立になる。規範の衝突、例外、優先順位や法的な正当性の決定手続きは残る。',
    'rqqnが成立しても、禁止が能力の欠如を引き起こしたとは限らない。禁止が全くない場合も成立し得る。原因として規範が実効的に働くという主張には、規範の存在と因果の比較を別に要求する。',
    'これらは規範状態と目的と能力の条件であり、内容の真理、実行、結果の発生、現実の違反や責任を断言しない。記述を脱引用せず、引用構成や同一性の比較でも内容を実行しない。',
    'rqql/rqqmは個人的専制の必要十分条件ではない。公的意思の私的な扱い、立法と執行の関係、政治的な支配の継続や実行機構は未記述。この診断から前段の離脱を自動構成すると、禁止の撤回や目的の変更だけで政治的解放と誤認し得るため接続しない。',
    '1795年の比較資料を1784年の一意の語義に置き換えない。今回の規範・目的の分析を原文の新しい対応範囲や著者主張へ加算しない。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqqk','rqqn','rqqo'])
    basis=dict(status='normative_practical_and_purposive_diagnostics_not_despotism_definition',document=FULL,library=LIBRARY,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,reading_review=READING,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'] if d['name'] in MEANINGS},
        limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Normative, practical and purposive choice conditions composed',flush=True)


if __name__=='__main__':main()
