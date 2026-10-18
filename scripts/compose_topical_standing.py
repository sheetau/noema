"""Use the same task-bound standing ability across topics and enabling results."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_falling_depiction import ROOT,closure
from scripts.compose_bodily_acquisition import PROFILES,GOAL
from scripts.compose_collective_attainment import FRAME,FARGS,STANDARD

PARENT='examples/v016/kant-collective-attainment.noema'
PARENT_BASIS='data/collective-attainment-basis-v1.json'
FULL='examples/v016/kant-topical-standing.noema'
CORE='examples/v016/topical-standing-core.noema'
LIBRARY='examples/v016/topical-standing.noema'
BASIS='data/topical-standing-basis-v1.json'
PROFILE=' '.join(n+' '+t for n,_,t in PROFILES)
METHODS='available h[a a d] c outcomes h[a a d d] c selected h[a a d d] c'
FIELDS='person a anchor d relevant h[a a] c tasks h[a] '+GOAL+' '+PROFILE+' '+METHODS
TAIL=' '.join('v '+n for n,_,_ in PROFILES)+' v available v outcomes v selected'
SUPPORT='person a context d assessed h[a] e eligible h[a a] c enabling h[a a a d] c effects h[a a a d d] c'
TOPIC='topic a anchor d topics h[a a a d] c names h[a] i[a]'
TARGS='v topic v anchor v topics v names'
ENABLING='agents h[a a d] c enabling h[a a a d] c effects h[a a a d d] c'
EARGS='v agents v enabling v effects'
MEANINGS={
 'rqwm':'非空の固定対象範囲の各事柄に、同じ閉じた活動記述から得た内容と活動別プロフィールを渡し、rqvvの既有能力評価が整うことを求める。記述と達成内容を別々に受けず、同じ記述を脱引用して本人へ適用する。',
 'rqwn':'rqwmが整い、対象範囲の各事柄についてrqvwの通常機会での行使能力がある。現在地の外的な機会の欠如だけを不能とせず、事柄ごとに異なる行使方法を許す。全事柄を同時に処理する一つの方法は要求しない。',
 'rqwo':'本人と現在に固定した実施者範囲について、各実施者のrlnが整い、全支援結果で同じ本人の能力評価が整う。範囲が既知の空集合なら全評価は成立するが、可能性を導かない。',
 'rqwp':'同じ本人と現在に対して指定された範囲の実施者に、利用可能な一つの支援方法と、本人の評価と能力がともに成立する一つの同じ結果がある。実施済みや成功保証、他実施者や同じ実施者の他方法の全評価は要求しない。',
 'hzvg':'事柄を固定して、本人のrlkの自立的で理由に支えられた判断内容を返す関数。sicher und gutの全語義をこの条件だけで確定しない。',
 'hzvh':'事柄の閉じた参照記述をhzvgへ構文的に適用し、本人を引数とする閉じた活動記述を作る。構築時には事柄の参照も判断内容も実行評価しない。',
 'hzvi':'同じ本人・主題・基準で選ぶ全事柄について、渡された閉じた個体参照がその同じ事柄を指すことを検査する。不一致の事柄を対象範囲から除いて成功としない。',
 'hzvj':'人aaについて、固定主題・本人・元の基準時点の事柄と参照が一致し、各事柄の活動記述によるrqwmの評価が整う。支援後の評価でも対象範囲を狭めない。',
 'hzvk':'hzvjと同じ固定事柄・活動記述・評価入力についてrqwnの既有行使能力を表す。本人側の能力基盤を保つ通常機会を使い、今すぐできることや準備による達成と分ける。',
 'hzvl':'同じ本人・元の基準に固定した実施者範囲にrqwoを適用し、各支援結果でhzvjが整うことを求める。現在地の古い方法評価rllを将来能力の評価として残さない。',
 'hzvm':'hzvlと同じ実施者・事柄・基準を保持し、同じ本人が一つの支援結果でhzvjとhzvkを満たす可能性をrqwpで表す。事柄別の成功を異なる結果から寄せ集めない。',
 'hzvn':'rqwiの集団到達をhzvj・hzvkの主題付き評価と能力へ接続する。集団外や異なる主題の能力、現在地での偶然の可否を集団の成功分布へ流用しない。',
 'hzvo':'hzvnと同じ時代・集団・基準・主題についてrqwjの未到達だが進行中という内容を作る。進行と能力取得可能性、到達を同一視しない。',
}
LIMITS=[
 'u0014の主題付き能力を、現在の本人側の基盤を保った通常機会での行使能力へ接続する比較候補。現在地の方法だけを調べる旧rll・rlmを黙って再定義せず、比較用として保持する。',
 '事柄の範囲は本人・主題・元の基準で固定する。活動別の六つの入力には同じ事柄の閉じた記述を渡し、他活動のプロフィールを流用しない。名前の同義性や現実の対象範囲の完全性は自動判定しない。',
 'rqwm・rqwnは渡された同じ活動記述から目標内容を取得する。hzvhは個体の閉じた参照を受ける。型が合うだけでは参照先が正しいとはせず、hzviで実際の対象と照合する。',
 '事柄ごとに別の行使方法を許す。支援可能性は一つの同じ結果で対象範囲全体の能力を求める。現在能力、支援可能性、全支援結果の評価、成功保証を分ける。',
 '既存のrlkは理由に支えられた自立的判断の候補であり、宗教の主題の全内容やsicher und gutの習熟・確実さ・適切さの全条件を確定したものではない。集団の基準、不足の程度、問答・進行・徴候・著者帰属は残る。',
 '実施者範囲や通常性の妥当性は意味規約を持つ文脈入力であり、有限モデルの成功から全人類・全活動・現実の支援を網羅したとしない。未評価は不能へ補わない。',
 '現行41文と十単位604文字の確認を保持し、原文の新しい範囲や全体確認を増やさない。比較候補の構成を本文全体の採用や独立査読と混同しない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def definitions():
    task='c[v tasks][v matter]'
    args='v person c[s['+task+']][v person] '+task+' v anchor '+TAIL
    relevant='c[v relevant][v person v matter]'
    for_all=lambda condition:'f matter a[y['+relevant+']['+condition+']]'
    text='d rqwm['+FIELDS+'] c[w[g matter a['+relevant+']]['+for_all('k rqvv['+args+']')+']].'
    allargs='v person v anchor v relevant v tasks '+TAIL
    text+='d rqwn['+FIELDS+'] c[w[k rqwm['+allargs+']]['+for_all('k rqvw['+args+']')+']].'
    offer='c[v enabling][v actor v person v method v context]'
    effect='c[v effects][v actor v person v method v context v future]'
    valid='k rln[v actor v person v context v enabling v effects]'
    assessed='t[c[v assessed][v person]][v future]'
    text+='d rqwo['+SUPPORT+'] c[f actor a[y[c[v eligible][v actor v person]][w['+valid+'][f method a[y['+offer+'][f future d[y['+effect+']['+assessed+']]]]]]]].'
    success='w['+assessed+'][t[c[v capable][v person]][v future]]'
    text+='d rqwp['+SUPPORT+' capable h[a] e] c[g actor a[w[c[v eligible][v actor v person]][g method a[w['+offer+'][g future d[w['+effect+']['+success+']]]]]]].'
    text+='d hzvg[matter a] h[a] e[i[person a][k rlk[v person v matter p ab p ac p fa p fb p fc p fd p ad]]].'
    text+='d hzvh[matter i[a]] '+GOAL+'[o a[r[p hzvg]][v matter]].'
    member='c[v topics][v person v topic v matter v anchor]'
    text+='d hzvi[person a '+TOPIC+'] c[f matter a[y['+member+'][e[s[c[v names][v matter]]][v matter]]]].'
    relevant='i[p a m a][c[v topics][v p v topic v m v anchor]]'
    tasks='i[m a][k hzvh[c[v names][v m]]]'
    params='v person v context '+relevant+' '+tasks+' '+' '.join('p '+s for _,s,_ in PROFILES)+' p ae p af p ap'
    for name,target in [('hzvj','rqwm'),('hzvk','rqwn')]:
        text+='d '+name+'['+TOPIC+'] h[a] e[i[person a][b context[w[k aa[v person]][w[k hzvi[v person '+TARGS+']][k '+target+'['+params+']]]]]].'
    eligible='i[actor a person a][c[v agents][v actor v person v anchor]]'
    args='v person v context k hzvj['+TARGS+'] '+eligible+' v enabling v effects'
    for name,target,extra in [('hzvl','rqwo',''),('hzvm','rqwp',' k hzvk['+TARGS+']')]:
        text+='d '+name+'['+TOPIC+' '+ENABLING+'] h[a] e[i[person a][b context[w[k aa[v person]][k '+target+'['+args+extra+']]]]].'
    fields=FRAME.replace(' context d','')+' standard '+STANDARD+' '+TOPIC
    args=FARGS+' k hzvj['+TARGS+'] v standard k hzvk['+TARGS+']'
    text+='d hzvn['+fields+'] e[b context[k rqwi['+args+']]].'
    text+='d hzvo['+fields+' progress e] e[b context[k rqwj['+args+' v progress]]].'
    return text


def build():
    old=parent();d=deepcopy(old.document);statements=d['statements'];d['statements']=[];size=len(d['declarations'])
    assert not set(MEANINGS)&set(old.entries)
    d=parse(format_graph(d,'compact')+definitions());d['statements']=statements
    lib=deepcopy(d);lib['declarations']=closure(d,['rqwm','rqwn','rqwo','rqwp']);lib['statements']=[]
    core=deepcopy(d);core['declarations']=closure(d,['hzvh','hzvj','hzvk','hzvl','hzvm','hzvn','hzvo','hzeq','hzer']);core['statements']=[]
    added=d['declarations'][size:]
    basis=dict(status='task_bound_topical_standing_and_enabling_comparison',document=FULL,library=LIBRARY,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={x['name']:{k:x[k] for k in ('parameters','result')} for x in added},limitations=LIMITS)
    return {FULL:format_graph(d,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,text in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==text,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
    print('Topical standing ability and shared enabling target composed',flush=True)


if __name__=='__main__':main()
