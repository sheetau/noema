"""Compose grasped, grounded cognitive holdings and their individual/cohort gain."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/cognitive-correction-basis-v1.json'
LIBRARY='examples/v016/cognitive-acquisition.noema'
BASIS='data/cognitive-acquisition-basis-v1.json'
PRIMITIVES={
 'h26ah':('[a a d d] c',['person','item','scope','point'],'同じ人が、この固定基準の代表項目の内容を、その指示対象・区別・関係を捉えて扱える状態にある。文字列の反復や記号の記憶だけとは区別する。全ての論理的帰結を知ることや、内容が真であること、根拠・独立性を含意しない。別名を替えて把握状態を増やさず、より細かい関係を新たに捉える場合はその関係を別の内容として明示する。'),
 'h26ai':('[a a d d] c',['person','judgment','scope','point'],'この人が同じ固定基準のこの判断を、現在保持する自らの見解としている。現在まさに判断行為を遂行していることは要求せず、過去に判断したが現在は放棄・忘却した場合や、他人の判断を保管するだけの場合を除く。内容と極性はh245q、現在の受容はh26afで別に結ぶ。'),
 'h26aj':('[a a d d] c',['reason','judgment','scope','point'],'固定した認識上の基準で、この同じ理由が、この判断の現在の受容を成立・維持させる十分な認識根拠として働いている。理由と見解の単なる共存、事後の理屈づけ、偶然に結論だけが当たる結び付き、根拠の敗北があるのに保持しただけの場合を除く。理由の使用fc・支持fd、本人の内容把握、結論の真理は別に確認する。演繹的証明だけへ限定せず、経験・信頼できる証言等も基準に応じて扱う。'),
}
MEANINGS={
 'r5ck':'同じ本人が保持する同じ肯定判断が、固定した代表項目のh26aeを内容とし、その判断で現在用いる一つの理由がfdで支持し、h26ajの十分な認識根拠として受容に働く。異なる判断や内容から条件を寄せ集めない。',
 'r5cl':'本人が人であり、固定範囲の同じ項目を別名も含めて受容し、その代表内容を把握し、固定した真偽評価で内容が真であり、同じ肯定判断へのr5ckの根拠がある。Erkenntnisseの拡大を比較するための、把握された根拠ある認識の保有条件。',
 'r5cm':'同じ候補の履歴にある前後の点で本人が生存し、同じ項目のr5clを以前は持たず、後には持つ。内容・基準・真偽評価を固定する。項目の新規受容に限らず、既に受容していた内容の把握や根拠を新たに得た場合も含む。',
 'r5cn':'同じ人・固定範囲・評価・候補・前後点について、履歴がtaの厳密な全順序を持ち、一項目以上のr5cmの獲得がある。他の全認識を失わないことや、全対象の理解完成を要求しない。',
 'r5co':'同じ集団に前後とも生存者がおり、有効な同じ履歴の前後について、その成員の個人的なr5cmの獲得、又は後の成員が以前のどの生存成員にもなかった項目のr5clを持つことがある。出生や世代交代を許し、同じ水準の保有者の入替えだけは集団の新規拡大にしない。',
 'r5cp':'同じ集団・範囲・真偽評価・候補・開始点からr5coの新たな認識を生む結果が、利用可能な方法のどの結果にもないことをrjbで表す。方法ごとの結果は非空で、成功保証の欠如や現在の未獲得だけへ弱めない。',
}
LIMITS=[
 'Erkenntnisse zu erweiternは、把握し根拠に基づいて保持する認識内容の新たな獲得として読む。認識の蓄積には誤った受容もあり得るが、新たな誤解そのものをこの拡大の成功には数えない。誤りの訂正は既存r5cg–r5cjで別に扱う。',
 '同じ項目の別名はh26agで固定し、内容はh26aeのNoema命題として与える。全比較状況で真となる内容でも、本人が初めて把握し根拠を得たなら獲得になり得る。論理的に真であることから本人の理解を導く論理的全知は仮定しない。',
 '既知の結論への新しい証明・説明を理解する場合は、その証明や説明が結論を支えるという関係を別の認識内容として記述する。結論の名前を付け替えただけでは新規項目としない。固定範囲は必要な対象・条件・根拠関係の区別を網羅し、成功例だけへ縮めない。',
 '把握h26ah、保持h26ai、十分な根拠の実際の働きh26ajは一般的な認識関係の解釈入力であり、一文全体や拡大の真偽を返す関係ではない。有限検査は現実の認識過程や根拠の適切さを証明しない。全哲学的な知識理論の必要十分条件を確立したとは主張しない。',
 '一人の一項目の獲得と、集団に以前なかった内容の保有を拡大として数える。出生した人が既存内容を保持するだけの世代交代は維持であり、本人の既存生涯内の新たな獲得は別に数える。全員の同意・全知識の無損失・集団の単一精神は仮定しない。',
 'r5cpの方法は個々の成員が取り得る学習・研究と共同の活動をともに含む全範囲。結果で新たに生存する成員も評価する。未知の把握・保持・根拠・真偽・方法を偽又は空集合へ補わない。',
 '啓蒙進展の不能性と三つの不能性の同じ状態への接続、先行する合意の目的と状態の必然性、規範的否認、重要性・総括・共謀的提示・全文帰属はまだ残る。全文の意味判断や確認済み文字数を増やさない。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def living(person,point):return both('k aa[v '+person+']','k h256o[v '+person+' v candidate v '+point+']')
def timeline():return 'k ta[i[at d][k h257z[v scope v candidate v at]] i[before d after d][k ic[v before v after v candidate]]]'
def ordered():return both('k h257z[v scope v candidate v first]','k h257z[v scope v candidate v last]','k ic[v first v last v candidate]')
def definitions():
    canonical='k h26ag[v item v scope]'
    positive='k h245q[v judgment '+canonical+' r[p h26ae] v scope e[v person][v person] v point]'
    ground='g judgment a[g reason a['+both('k h26ai[v person v judgment v scope v point]',positive,
        'k fc[v judgment v reason v point]','k fd[v reason v judgment v point]','k h26aj[v reason v judgment v scope v point]')+']]'
    text='d r5ck[person a item a scope d point d] c['+ground+'].\n'
    text+='d r5cl[person a item a scope d assessment d point d] c['+both('k aa[v person]','k h26ad[v item v scope]',
        'k r5cd[v person v item v scope v point]','k h26ah[v person '+canonical+' v scope v point]',
        't[k r5cc[v item v scope]][v assessment]','k r5ck[v person v item v scope v point]')+'].\n'
    fields='person a item a scope d assessment d candidate d first d last d'
    text+='d r5cm['+fields+'] c['+both(ordered(),living('person','first'),living('person','last'),
        'u[k r5cl[v person v item v scope v assessment v first]]','k r5cl[v person v item v scope v assessment v last]')+'].\n'
    text+='d r5cn[person a scope d assessment d candidate d first d last d] c['+both(timeline(),
        'g item a[k r5cm[v person v item v scope v assessment v candidate v first v last]]')+'].\n'
    member=lambda person:'k h246c[v group v '+person+' v candidate]'
    earlier='g other a['+both(member('other'),living('other','first'),'k r5cl[v other v item v scope v assessment v first]')+']'
    newcontent=both(living('person','last'),'k r5cl[v person v item v scope v assessment v last]','u['+earlier+']')
    newperson='k r5cm[v person v item v scope v assessment v candidate v first v last]'
    gain='g person a[g item a['+both(member('person'),'x['+newperson+']['+newcontent+']')+']]'
    population=lambda at:'g person a['+both(member('person'),living('person',at))+']'
    group='group a scope d assessment d candidate d first d'
    text+='d r5co['+group+' last d] c['+both(timeline(),ordered(),population('first'),population('last'),gain)+'].\n'
    goal='b last[k r5co[v group v scope v assessment v candidate v first v last]]'
    text+='d r5cp['+group+' available h[a a d] c outcomes h[a a d d] c] c[k rjb[v group '+goal+' v first v available v outcomes]].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['r5cc','r5cd','rjb','ta','h245q','aa','h256o','h246c','ic','fc','fd','h257z','h26ad']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='grasped_grounded_cognitive_acquisition_and_cohort_gain',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
