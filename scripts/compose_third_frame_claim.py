"""Present the purposive third-frame introduction, coordinate naming and double application."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_third_frame_geometry import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-third-frame-geometry.noema';PARENT_BASIS='data/third-frame-geometry-basis-v1.json'
FULL='examples/v014/einstein-third-frame-claim.noema';CORE='examples/v014/third-frame-claim-core.noema'
BASIS='data/third-frame-claim-basis-v1.json';ANNOTATIONS='data/third-frame-claim-identifiers-v1.json';INDICES=(310,311)
NAMES=(('eisnr','K′'),('eisns','x′'),('eisnt','y′'),('eisnu','z′'),('eisnv','t′'))
RULES=(('eisns','ejbd','yn'),('eisnt','ejbe','yo'),('eisnu','ejbf','yp'))
PRIMITIVES={
 'eisnq':([('agent','a'),('action','i[e]'),('intention','a'),('scope','a'),('reference','d')],'agentがscopeで既にintentionの箇所に表明した同じ目標を目指すため、actionに記述された行為を手段として行うという目的関係。intentionは意図の表明箇所を指し、意図の対象・内容は別の関係で明示する。目的を意図する気持ちの新規発生に替えず、目標の達成、手段の十分性・成功や、客観的な因果関係の証明を要求しない。actionの実行と意図の同一性は合成側で保持する。'),
 'eisnw':([('node','a'),('author','a'),('designation','a'),('rule','i[h[a '+R+' d] c]'),('document','a'),('reference','d')],'authorがnodeで、同じdocumentの量を呼ぶdesignationを、対象・実数値・状況に対する閉じたruleの規約に従う記号として今採用する命名宣言。単なる既出表記の参照とは区別し、ruleの対象・測定単位・役割を保つ。記号の字面から物理的真理を導かず、規則をここで実行して測定を行うこと、他者の同意や歴史上の最初の命名を要求しない。'),
}
PRIMITIVES.update({n:([],printed+'という呼称個体。u0093–u0094の第三系K′'+('そのもの' if n=='eisnr' else 'での'+{'eisns':'第一位置座標','eisnt':'第二位置座標','eisnu':'第三位置座標','eisnv':'時刻'}[n])+'を指すための識別表記。対象・値の規則は別の関係で保持する。以前の補助変数x′や別系の座標へ語形だけで同一視しない。') for n,printed in NAMES})
MEANINGS={
 'ejbd':'第三系zgiの第一役割ynに固定した現在の位置測定eixuの規則。ここで名付けるx′はこの規則による測定値であり、先行する補助x−vtではない。',
 'ejbe':'同じ第三系zgiの第二役割yoに固定した現在の位置測定eixuの規則。',
 'ejbf':'同じ第三系zgiの第三役割ypに固定した現在の位置測定eixuの規則。',
 'ejbg':'第三系zgiでの同じ時点・単位rbの時刻値をeiylで与える規則。t′の参照をKのtやkのτに替えない。',
 'ejbh':'既出二系とは別の同じ第三系zgiを論説へ導入し、−vの全体並進・縦軸上の原点・三零点のejbbを仮定に採用し、K′の呼称を同じ系へ付す導入行為。現実での実在・測定済みの断言にはしない。',
 'ejbi':'ejbhの導入を行い、その同じ行為を前文zgnで表明した同じspc決定の意図のための手段とする。zgmで関数・段階・著者・節を固定し、意図zgnから導入zgoへの順序を保持する。目的の達成やφ=1は要求しない。',
 'ejbj':'同じ第三系の三位置座標x′,y′,z′を各測定規則ejbd/ejbe/ejbfに従って名付け、その解釈対応とt′の時刻規則ejbgを同じ論説へ保持する。t′について第三文の三位置座標と同じ新規命名宣言は加えない。',
 'ejbk':'同じ設定zb6でejbaの現在三記録の存在・値の一意性と、中間・最終の全四連鎖等式を満たす結果内容。',
 'ejbl':'第三系座標の命名と規則ejbjを行い、現在の四式・第三系設定・同じ中間記録による二回適用ejbcから全四連鎖等式ejbkを得ると著者が提示する。式を処理系自身が無条件に実証したという宣言に替えない。',
 'ejbm':'目的付きの第三系導入と仮定ejbiを述べるメッセージ。',
 'ejbn':'u0093の導入と仮定を同じ著者・論説へ帰属し、前文の未知関数の議論zgtからの進行を保持する。',
 'ejbo':'第三系座標の命名と二回変換の結果ejblを述べるメッセージ。',
 'ejbp':'u0093末文とu0094の四連鎖等式を同じ著者・論説へ帰属し、第三系設定zgoから結果zgpへの順序を保持する。',
}
LIMITS=[
 '固定u0093の三文全体とu0094の四連鎖等式を原刊901頁へ照合する。前文のφ決定意図、第三系導入と並進、三原点と零時刻、座標命名、同じ四式の二回適用とその結果を一つの意味群として読む。',
 'zu diesem Zweckeは前文で表明した同じ正規化後φ=spcの決定を目指す手段関係。行為内容ejbhの実行とzgmの同じ関数・段階への意図を保ち、意図が新たに生じることを目的にせず、決定の成功・唯一解・具体的方法の完了を要求しない。',
 'noch ein drittesは既出Kとkに加える相異なる第三系K′。並進は全固定配置・全比較時点のeioj、速度成分−v,0,0、原点の全時点横座標零とsfcの対応軸へ結ぶ。印字Ξはkの縦軸と読む。',
 'mögen ... zusammenfallenとes seiは議論上の仮定。基準出来事zgkでK/kの現在ei46とK′の原点・現在記録の全四成分零を結ぶ。光の放出出来事へ限定せず、異なる出来事の原点や零時刻を組み合わせない。',
 'Wir nennenの対象はK′で測る三位置座標。命名宣言と、同じ地点・長さ単位・状況の現在eixuへの対応を両方保持する。t′は第二文と表示式の同じ第三系時刻であり、三位置座標の命名に第四の命名を補わない。',
 '四つの連鎖等式は同じ出来事の三系の現在記録に対し、vと−vで同じ正規化後φの四式を二回適用する中間式と、各成分のφ(v)φ(−v)倍という最終式を両方保持する。全対象への記録の存在と各系の値の一意性を要求し、同値の別記録を許す。',
 'β(−v)は正の枝srdであり、φの正負引数の等値、φ=1、倍率1、K′とKの相対静止や恒等変換をここで主張しない。x′の現在の第三系座標と以前の補助x′=x−vtを区別する。',
 'wirは著者の論述上の声。導入・仮定・命名・結果提示を同じ著者と第三節へ帰属する。有限対照検査、保存済み代数証拠、原刊との通読判断を区別し、一般物理的導出や意味同値の自動証明と扱わない。',
]


def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    fields=[('place','a'),('value',R),('context','d')]
    for sign,rule,role in RULES:text+=define(rule,fields,k('eixu',v('place'),k('zgi'),k(role),v('value'),v('context')))
    text+=define('ejbg',[('moment','a'),('value',R),('context','d')],k('eiyl',v('moment'),k('zgi'),v('value'),v('context')))
    point=v('point');author=k('rd');paper=k('eirf');scope=k('eisms')
    text+=content('ejbh',both(k('eisd3',k('zgo'),k('zgi'),paper,point),k('ug',k('zgo'),author,quote('ejbb'),scope,point),k('eisd4',k('zgo'),author,k('eisnr'),k('zgi'),paper,point)))
    text+=content('ejbi',both(op('t',k('ejbh'),point),k('zgm',k('zgn'),author,quote('spc'),k('zgl'),scope,point),k('eisnq',author,quote('ejbh'),k('zgn'),scope,point),k('ue',k('zgn'),k('zgo'),point),op('u',op('e',k('zgn'),k('zgo')))))
    notation=[k('eislo',k(sign),'r[p '+rule+']',paper,point) for sign,rule in [(s,r) for s,r,_ in RULES]+[('eisnv','ejbg')]]
    naming=[k('eisnw',k('zgp'),author,k(sign),'r[p '+rule+']',paper,point) for sign,rule,_ in RULES]
    text+=content('ejbj',both(*notation,*naming))
    text+=content('ejbk',k('ejba',k('zb6')))
    text+=content('ejbl',both(op('t',k('ejbj'),point),k('zc',k('zgp'),author,quote('ejbc'),quote('ejbk'),scope,point)))
    for message,claim,body,node,previous in (('ejbm','ejbn','ejbi','zgo','zgt'),('ejbo','ejbp','ejbl','zgp','zgo')):
        text+='d '+message+'[] f[j s[k '+body+'[]]].\n'
        text+=define(claim,[],both(k('eir3',k(node),author,paper,quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ejbn','ejbp')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='purposive_third_frame_and_double_transform_claim',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/third-frame-geometry-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'] += [dict(symbol=n,role='designation',forms=[dict(text=printed,language='de',role='printed_identifying_form')]) for n,printed in NAMES]
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
