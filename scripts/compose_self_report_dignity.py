"""Keep a duty self-report, its appraisal and actual performance separate."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,FALSE
from scripts.compose_religious_freedom_policy import DUTY_NAMES,DUTY,DARGS

PARENTS=('data/religious-freedom-policy-basis-v1.json','data/named-epoch-sentence-basis-v1.json')
LIBRARY='examples/v016/self-report-dignity.noema';BASIS='data/self-report-dignity-basis-v1.json'
MESSAGE='i e[h[a] f]';ACTION='i f[h[a a] e]';STANDARD='h[a '+ACTION+'] e'
FRAME_NAMES=('source','office','group','community','topic')
FRAME=' '.join(n+' a' for n in FRAME_NAMES)+' reference d'
FARGS=' '.join('v '+n for n in FRAME_NAMES)+' v reference'
SPEECH_NAMES=(*FRAME_NAMES,'audience')
SPEECH=' '.join(n+' a' for n in SPEECH_NAMES)+' reference d'
SARGS=' '.join('v '+n for n in SPEECH_NAMES)+' v reference'
APPRAISAL_NAMES=('actor',*SPEECH_NAMES)
APPRAISAL=' '.join(n+' a' for n in APPRAISAL_NAMES)+' reference d'
AARGS=' '.join('v '+n for n in APPRAISAL_NAMES)+' v reference'
PRIMITIVES={
 'h26ng':('[a a a '+MESSAGE+' d] c',['activity','recipient','subject','message','point'],
   '同じ提示活動がこの点で、同じ受け手に対し、同じ対象本人について、閉じた段階4の発話内容族を伝える。f2と同じ提示関係を高い記述段階へ広げる。活動の生起・提示主体・受け手範囲は別に構成する。受け手の理解・同意、発話内容の真理、対象本人と受け手の同一性を加えない。'),
 'h26nh':('[a a a d] j['+STANDARD+']',['person','office','community','reference'],
   '同じ本人・公的立場・共同体と固定基準において、その人の振舞いが本人にふさわしい尊重や道徳的な自己のあり方を損なわないと評価するための、採用する最低条件の全有限列。各条件は本人と段階5の行為記述からNoema内容を返す関数として与える。評価点や望む結果に合わせて条件を除かず、単なる嗜好、実行能力、命令の有無、発言内容が事実であること、賞賛に値する最大の卓越性を条件そのものとはしない。名だけの条件・未知を評価済みとせず、非空性と全条件の充足は合成側で確認する。本人が実際にこの評価を受け入れるかどうかは外側の判断で分ける。'),
 'h26ni':('[a i g[e] d] c',['person','content','point'],
   '本人がこの点で段階6の閉じた内容を成り立つものとして受け入れ判断している。h26nfと同じ誤りうる判断を、行為記述への評価を含む高い内容段階に保つ。内容の実行・真理、行為の生起、内側の義務判断や義務の真理、自己報告の誠実さを導かない。'),
}
MEANINGS={
 'r5wf':'同じ規範出所・公的立場・対象集団・共同体・宗教主題・固定基準について、引数の本人がr5weの義務判断を持つという内容を述べる主張発話の族。義務そのものの主張や、判断を述べた行為とは別である。',
 'r5wg':'同じ五個体と固定基準の閉じた名前をr5wfへ適用した段階4の発話族記述。本人引数は同じ発話対象として後で渡す。',
 'r5wh':'同じ本人の同じ提示活動が生起し、固定された非空の受け手集団の全成員に、その本人についての同じr5wg発話を伝える。名前の一致をr5wdで確認し、受け手ごとに違う活動や別人の判断を寄せ集めない。伝える内容は実行しない。',
 'r5wi':'同じ設定と受け手を固定し、本人・提示活動からr5whの自己報告の実行条件を返す。次の品位評価でこの内容を引用でき、引用しただけでは自己報告の生起を要求しない。',
 'r5wj':'同じ六個体と固定基準の閉じた名前をr5wiへ適用した段階5の行為記述。義務判断の報告を、その内容・人物・受け手・基準を保って評価対象にする。',
 'r5wk':'同じ本人と同じ段階5の行為記述について、与えた基準列の少なくとも一つが評価点で不成立である。rneの不足判定を高い行為記述に保ち、空列から不足を補わない。',
 'r5wl':'非空の基準列で同じ行為にr5wkの不足がない。rnfと同じ全最低条件の充足であり、最良・最大の卓越性を加えず、行為を実行しない。',
 'r5wm':'同じ本人・公的立場・共同体のh26nhの全品位基準を、同じ義務判断を同じ受け手に述べるr5wjの行為記述へ適用し、r5wlの非不足を返す。外側の判断内容であり、この評価が実際に真だとはまだ断定しない。',
 'r5wn':'同じ本人を含む七個体と固定基準の閉じた名前をr5wmへ適用した段階6の評価内容記述。否定はこの同じ品位不足の内側へ保持し、単に悪いと思っていないことに弱めない。',
 'r5wo':'同じr5wdの六個体と固定基準に加えて、受け手集団の閉じた名前が同じ集団を指すことを確認する。別の受け手に述べる別の行為を、同じ自己評価の対象にしない。',
 'r5wp':'r5woで全参照を確認したr5wnの非不足内容を、同じ本人がこの点で受け入れ判断する。外側の評価判断だけを要求し、実際の発言・内側の義務判断・義務・自由政策の真理を連言しない。',
 'r5wq':'同じ設定・受け手・基準を固定してr5wpを本人ごとの性質へ渡す。後で一般的な君主の制限条件へ結ぶ候補であり、該当人物の存在や全文の結論は主張しない。',
}
LIMITS=[
 'u0015第一文のseiner nicht unwürdig findet, zu sagen以下の依存群。前回の同じ宗教的自由の方針・義務判断を自己報告の内容へ入れ、その報告の品位への本人の評価までを構成する。君主の範囲、sondern/also、名称拒否、啓蒙・称賛・解放の功績と著者帰属は後続で統合する。本文112主張・17単位判断と確認文字数を変更しない。',
 'unwürdigは、この行為が本人にふさわしい尊重・道徳的な自己のあり方に反するという評価として読む。DWBの個人の品位や道徳的自己意識への不適合という用法と、seiner nicht unwürdigという用例を補助にする。直前のMajestätへの実際の因果的損傷と同一視しない。',
 'nicht unwürdigは非空の固定された最低基準の全充足として構成する。中立を含む最低水準でよく、最上の称賛や必ず実行することを加えない。単なる否定的信念の不在ではなく、この非不足内容を本人が受け入れることとする。基準の具体的な内容・適切さ・全範囲は解釈入力の責任として明記する。',
 '実際の基準充足、本人の品位評価、報告行為、報告の内側の義務判断、義務、自由政策の実現を別々に扱う。品位評価から実際の発言や誠実さを推論しない。発言の内容は義務判断の自己報告であり、自由方針そのものの直接の主張とはしない。',
 '同じ報告は同じ本人が行い、非空の全受け手へ同じ本人を対象とする発話族を伝える。公衆全体への到達、同意、口頭か書面か、一回だけの歴史的発言は加えない。原文への統合時に受け手の固定の仕方を示し、受け手ごとの別の行為を一つの報告へ寄せ集めない。',
 '発話族の引用は段階4、自己報告という行為記述は段階5、品位評価内容は段階6に保つ。外側の本人の判断はこの引用を実行しない。基準は行為記述を受け取るため、現実の報告の存在を前提にしない。',
 'ここでは評価の基準列を明示的な関数として受け取り、基準が本当に対象の品位を表すかは規約と読解で確認する。少数の有限モデルは原文の意味同値を自動証明せず、全一文の通読判断を先取りしない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def name_args(names):return ' '.join('k h223g[v '+n+']' for n in names)+' k h223h[v reference]'
def definitions():
    text='d r5wf['+FRAME+'] h[a] f[i[actor a][j s[b point[k r5we['+DARGS+' v point]]]]].\n'
    def code(name,target,names,result,rank):
        return 'd '+name+'['+' '.join(n+' i[a]' for n in names)+' reference i[d]] '+result+'[o a[r '+rank+'[p '+target+']][ '+' '.join('v '+n for n in (*names,'reference'))+']].\n'
    text+=code('r5wg','r5wf',FRAME_NAMES,MESSAGE,'e')
    audience='k h246c[v audience v recipient v reference]'
    conveys='k h26ng[v activity v recipient v actor k r5wg['+name_args(FRAME_NAMES)+'] v point]'
    actual=both('k r5wd['+DARGS+']','k dg[v activity v point]','k f3[v actor v activity v point]',
        'g recipient a['+audience+']','f recipient a[y['+audience+']['+conveys+']]')
    text+='d r5wh[actor a activity a '+SPEECH+' point d] c['+actual+'].\n'
    text+='d r5wi['+SPEECH+'] h[a a] e[i[actor a activity a][b point[k r5wh[v actor v activity '+SARGS+' v point]]]].\n'
    text+=code('r5wj','r5wi',SPEECH_NAMES,ACTION,'f')
    failed='q[v standards]['+FALSE+'][i[failed c standard '+STANDARD+'][x[v failed][u[t[c[v standard][v actor v action]][v point]]]]]'
    text+='d r5wk[actor a action '+ACTION+' standards j['+STANDARD+']] e[b point['+failed+']].\n'
    text+='d r5wl[actor a action '+ACTION+' standards j['+STANDARD+']] e[b point['+both('u[e[d[v standards]][n p a b]]','u[t[k r5wk[v actor v action v standards]][v point]]')+']].\n'
    action='k r5wj['+name_args(SPEECH_NAMES)+']';standards='k h26nh[v actor v office v community v reference]'
    text+='d r5wm['+APPRAISAL+'] e[k r5wl[v actor '+action+' '+standards+']].\n'
    text+='d r5wn['+' '.join(n+' i[a]' for n in APPRAISAL_NAMES)+' reference i[d]] i g[e][o a[r g[p r5wm]]['+' '.join('v '+n for n in (*APPRAISAL_NAMES,'reference'))+']].\n'
    valid=both('k r5wd['+DARGS+']','e[s[k h223g[v audience]]][v audience]')
    text+='d r5wo['+APPRAISAL+'] c['+valid+'].\n'
    text+='d r5wp['+APPRAISAL+' point d] c['+both('k r5wo['+AARGS+']','k h26ni[v actor k r5wn['+name_args(APPRAISAL_NAMES)+'] v point]')+'].\n'
    text+='d r5wq['+SPEECH+'] h[a] e[i[actor a][b point[k r5wp['+AARGS+' v point]]]].\n'
    return text
def build():
    libs=parents();doc=deepcopy(libs[0].document);doc.update(declarations=[],statements=[]);imported={}
    for lib,roots in zip(libs,(['r5we','r5wd','h246c','dg'],['f3'])):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(l.entries) for l in libs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(l.source_sha256) for l in libs))
    basis=dict(status='duty_self_report_and_nonfactive_personal_dignity_appraisal',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
