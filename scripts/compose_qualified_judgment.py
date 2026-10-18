"""Keep performance criteria on one judgment and inside its ability task."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_falling_depiction import ROOT,closure
from scripts.compose_bodily_acquisition import PROFILES,GOAL
from scripts.compose_collective_attainment import FRAME,FARGS,STANDARD
from scripts.compose_topical_standing import TOPIC,TARGS,ENABLING

PARENT='examples/v016/kant-topical-standing.noema'
PARENT_BASIS='data/topical-standing-basis-v1.json'
FULL='examples/v016/kant-qualified-judgment.noema'
CORE='examples/v016/qualified-judgment-core.noema'
LIBRARY='examples/v016/qualified-judgment.noema'
BASIS='data/qualified-judgment-basis-v1.json'
QUALITY='h[a a a d d] c'
QCODE='i['+QUALITY+']'
JUDGING='owned h[a a d] c use h[a a a d] c judgments h[a a d] c matters h[a a d] c reasons h[a a d] c support h[a a d] c guidance h[a a a d] c'
QUALIFIED=TOPIC+' standardcontext i[d] secure '+QCODE+' adequate '+QCODE
QARGS=TARGS+' v standardcontext v secure v adequate'
MEANINGS={
 'rqwq':'本人の同じ事柄・判断・実行時点に、rcrの自立的で理由に支えられた遂行と二つの質の基準を要求する。両基準の評価文脈も同じ明示的な基準に固定し、別々の判断から条件を寄せ集めない。',
 'rqwr':'同じ判断で実際に用いた理由が非空で、その全てがその同じ判断を同じ実行時点で支持すること。理由が一つもない場合の空虚な全称を防ぐ。全理由が真、無矛盾、十分、結論が真という別条件までは導かない。',
 'hzvp':'事柄・基準文脈・二つの質の条件を固定し、本人のrqwqの判断内容を返す。単に何らかの理由のある判断ができることと、指定した質でできることを分ける。',
 'hzvq':'事柄・基準文脈・二つの質の閉じた記述をhzvpへ構文的に適用し、本人を引数とする閉じた活動記述を作る。構築時に基準の真偽や参照を実行しない。',
 'hzvr':'本人・主題・元の対象範囲と参照が一致し、基準文脈の記述が元の基準時点を指し、質を含む同じ活動記述でrqwmの評価が整う。無修飾の活動のプロフィールを流用しない。',
 'hzvs':'hzvrと同じ対象・基準文脈・質の活動記述にrqwnを適用した行使能力。目標内容とプロフィールの活動記述には同じhzvqを使う。',
 'hzvt':'同じ実施者範囲の全支援結果でhzvrの評価が整うこと。質の基準も元の記述と文脈に保持し、支援後に緩めた基準へ置換しない。',
 'hzvu':'指定実施者に、同じ本人が一つの結果でhzvrとhzvsを満たす支援の可能性がある。現在の能力欠如や実際の取得済みを前提とせず、他方法の評価欠落だけで成功証人を取り消さない。',
 'hzvv':'同じ時代・集団・基準について、質を含むhzvr・hzvsをrqwiの到達判断へ渡す。無修飾の判断能力から質を満たす集団到達へ飛躍しない。',
 'hzvw':'hzvvと同じ質・主題・集団の未到達と、指定された進行内容をrqwjで結ぶ。評価不足を未到達に補わない。',
}
LIMITS=[
 'sicher und gutを伴う能力の対象に質の基準を残す比較候補である。二つの基準は明示した閉じたNoemaの式で指定し、原文の単語を未知の真偽フラグへ置換して完成としない。どの基準が原文に適切かという採用判断は別に残る。',
 'rqwrは、用いた全理由が支持するという合成できる基準の例であり、確実さや適切さの必要十分条件ではない。理由の一部が弱くても結論を確かに判断できる場合や、全理由が支持しても誤る場合まで排除・解決したとはしない。',
 '同じ実行の判断に複数の基準を結ぶ。基準間の独立性は仮定せず、一方から他方が従うという推論も追加しない。基準は結果を見て選び直さず、文脈を明示する。',
 '質の記述を変えると活動記述も変わるため、同じ真理値を持つ別の基準や無修飾の活動の評価プロフィールを自動移植しない。記述の同義性を機械的に決める規則ではない。',
 '現在能力の欠如、能力の新規取得、支援可能性は異なる。hzvuは能力のある状態へ置く可能性であり、前状態での欠如は含まない。無操作や現在能力の自動的な将来保持も追加しない。',
 '宗教的な対象範囲、原文での質の読み、不足の程度、集団基準、問答・進行・徴候・著者帰属の統合は残る。有限例から全文の意味同一性や現実の判断の正しさを認定しない。',
 '現行41文と十単位604文字の意味判断を保持し、新しい原文範囲や全体確認を増やさない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def both(*clauses):
    body=clauses[-1]
    for clause in reversed(clauses[:-1]):body='w['+clause+']['+body+']'
    return body


def definitions():
    judgment='k rcr[v person v judgment v point '+' '.join('v '+n for n in ('owned','use','judgments','matters','reasons','support','guidance'))+']'
    clauses=[judgment,'c[v matters][v judgment v matter v point]']
    clauses+=['c[v '+n+'][v person v matter v judgment v context v point]' for n in ('secure','adequate')]
    fields='person a matter a context d point d '+JUDGING+' secure '+QUALITY+' adequate '+QUALITY
    text='d rqwq['+fields+'] c[g judgment a['+both(*clauses)+']].'
    used='c[v reasons][v judgment v reason v point]'
    text+='d rqwr[judgment a point d reasons h[a a d] c support h[a a d] c] c['+both('g reason a['+used+']','f reason a[y['+used+'][c[v support][v reason v judgment v point]]]')+'].'
    refs='p ab p ac p fa p fb p fc p fd p ad'
    text+='d hzvp[matter a context d secure '+QUALITY+' adequate '+QUALITY+'] h[a] e[i[person a][b point[k rqwq[v person v matter v context v point '+refs+' v secure v adequate]]]].'
    codes='matter i[a] context i[d] secure '+QCODE+' adequate '+QCODE
    text+='d hzvq['+codes+'] '+GOAL+'[o a[r[p hzvp]][v matter v context v secure v adequate]].'
    tasks='i[m a][k hzvq[c[v names][v m] v standardcontext v secure v adequate]]'
    relevant='i[p a m a][c[v topics][v p v topic v m v anchor]]'
    args='v person v context '+relevant+' '+tasks+' '+' '.join('p '+s for _,s,_ in PROFILES)+' p ae p af p ap'
    checks=['k aa[v person]','k hzvi[v person '+TARGS+']','e[s[v standardcontext]][v anchor]']
    for name,target in [('hzvr','rqwm'),('hzvs','rqwn')]:
        text+='d '+name+'['+QUALIFIED+'] h[a] e[i[person a][b context['+both(*checks,'k '+target+'['+args+']')+']]].'
    eligible='i[actor a person a][c[v agents][v actor v person v anchor]]'
    args='v person v context k hzvr['+QARGS+'] '+eligible+' v enabling v effects'
    for name,target,extra in [('hzvt','rqwo',''),('hzvu','rqwp',' k hzvs['+QARGS+']')]:
        text+='d '+name+'['+QUALIFIED+' '+ENABLING+'] h[a] e[i[person a][b context['+both('k aa[v person]','k '+target+'['+args+extra+']')+']]].'
    fields=FRAME.replace(' context d','')+' standard '+STANDARD+' '+QUALIFIED
    args=FARGS+' k hzvr['+QARGS+'] v standard k hzvs['+QARGS+']'
    text+='d hzvv['+fields+'] e[b context[k rqwi['+args+']]].'
    text+='d hzvw['+fields+' progress e] e[b context[k rqwj['+args+' v progress]]].'
    return text


def build():
    old=parent();d=deepcopy(old.document);statements=d['statements'];d['statements']=[];size=len(d['declarations'])
    assert not set(MEANINGS)&set(old.entries)
    d=parse(format_graph(d,'compact')+definitions());d['statements']=statements
    lib=deepcopy(d);lib['declarations']=closure(d,['rqwq','rqwr']);lib['statements']=[]
    core=deepcopy(d);core['declarations']=closure(d,['hzvq','hzvr','hzvs','hzvt','hzvu','hzvv','hzvw','rqwr','hzvg']);core['statements']=[]
    basis=dict(status='qualified_judgment_and_same_task_criteria_comparison',document=FULL,library=LIBRARY,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={x['name']:{k:x[k] for k in ('parameters','result')} for x in d['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(d,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,text in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==text,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
    print('Judgment criteria bound inside the same ability task',flush=True)


if __name__=='__main__':main()
