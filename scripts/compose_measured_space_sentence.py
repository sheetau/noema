"""Present the imagined measured space and six frame-specific coordinates."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_spatial_coverage import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_rod_methods import history
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-spatial-coverage.noema';PARENT_BASIS='data/spatial-coverage-basis-v1.json'
FULL='examples/v014/einstein-measured-space-sentence.noema';CORE='examples/v014/measured-space-sentence-core.noema'
BASIS='data/measured-space-sentence-basis-v1.json';ANNOTATIONS='data/measured-space-sentence-identifiers-v1.json';INDEX=270
COORDINATES=(('eisne','x','eixv','ra','yn'),('eisnf','y','eixw','ra','yo'),('eisng','z','eixx','ra','yp'),('eisnh','ξ','eixy','zbm','yn'),('eisni','η','eixz','zbm','yo'),('eisnj','ζ','eix2','zbm','yp'))
PRIMITIVES={n:([],printed+'という座標記号の呼称個体。u0045で'+('静止系K' if frame=='ra' else '運動系k')+'の'+{'yn':'第一','yo':'第二','yp':'第三'}[role]+'成分を指す。実数値そのものではなく、同じ地点・尺度・状況への適用規則は合成側で固定する。') for n,printed,rule,frame,role in COORDINATES}
MEANINGS={
 'eixt':'初期の両系・三軸配置・同仕様の全計器を保持し、現在の選択履歴zcjを同じcontextへ固定して全期間平行なeiwnと両系の全空間測定eixsを課す。静止側の同じ物差しはraに静止し、移動側の同じ物差しはraに対する既出並進とzbm自身での静止を満たす。これらは想定する内容の条件である。',
 'eixu':'同じ地点・系・軸役割・状況の実測による一意座標eixqを保ち、指定実数valueが同じ長さ単位taの選択座標zcyと有効かつ値で一致するという記号解釈の共通規則。',
 'eixv':'静止系raの第一役割ynに固定したeixuの規則。xを移動系の第一座標に替えない。',
 'eixw':'静止系raの第二役割yoに固定したeixuの規則。',
 'eixx':'静止系raの第三役割ypに固定したeixuの規則。',
 'eixy':'移動系zbmの第一役割ynに固定したeixuの規則。ξの値をxに等置しない。',
 'eixz':'移動系zbmの第二役割yoに固定したeixuの規則。ηの値をyに等置しない。',
 'eix2':'移動系zbmの第三役割ypに固定したeixuの規則。ζの値をzに等置しない。',
 'eix3':'同じ既出の運動後設定zb6でeixtが成り立つという、測定済みと考える閉じた内容。測定する能力や将来の計画だけへ弱めず、内容の外へ物理的な実測事実を主張しない。',
 'eix4':'同じ本文箇所でK/kを既出のra/zbmへ保持し、六つの座標記号をそれぞれの閉じた地点・値・状況の規則へeisloで結ぶ。bez.の対応を静止側三成分と移動側三成分の対応として明示する。',
 'eix5':'著者がeix3を同じ第三節の思考上の構成として想定し仮定へ採用するeislz/ug、先行する運動設定への追加zao、記号規定eix4を合わせる。先の権原だけから採用や実現を推論せず、この文の想定行為として述べる。',
 'eix6':'Wir denken unsの想定行為と記号対応を述べるメッセージ。命令や現実の測定完了報告へ替えない。',
 'eix7':'u0045第一文の全メッセージを同じ著者・論説へ帰属し、u0044第二文の後という本文順序を保持する。',
}
LIMITS=[
 'u0045第一文[0,240)の全176本文文字を対象とする。Wir denken uns nun ... ausgemessen und so ... ermitteltを、空間が測定され座標が得られている配置を今想定するという行為として読む。測定可能性、予定、現実の実験報告へ替えない。',
 '同じ二系の原点・軸・物差し・時計群を初期設定から保持する。移動側は既出の正X定速度と全期間平行な選択候補を思考内容の中で採用する。u0044の認識上の許容や対称性の理由だけから、その実現や物理的真理を導かない。',
 '静止側の物差しはraに静止し、移動側は同じzbmと共に動き、その系では静止する。測定の各配置では同じ物差しを置き直せるが、対象・原点・軸・尺度は保存する。初期と運動後の長さ値、両系の座標値や正方向の一致を要求しない。',
 '測定済みという内容はeixsの全地点・三役割の被覆、配置間の幾何保存、校正した同じ道具・方法の実行、射影と非負距離、値の存在と全有効候補の一意性へ結ぶ。有限観測点だけ又は数値候補だけへ弱めない。',
 'K/kは同じ既出の二系、x/y/zとξ/η/ζはそれぞれの第一・第二・第三座標である。新しい六原始記号は呼称個体のみで、測定関係や一文全体を新しい原始述語へ包まない。',
 'soは同じ空間測定によってその座標が得られる対応として読み、測定関係と値をeixq/eixuで共有する。別の測定結果、空間の先行測定からの独立の論理証明や時間変換の導出を補わない。',
 'wirは著者の論考上の声として読む。第三節の同じ思考設定への追加と本文順序を保持する。引用された内容の成立を著者帰属から実行しない。',
 'この一文の通読判断とu0045全体の判断は分ける。第二文の時計配置点の時刻、§1の同期方法、追加指示とt/τの記号はまだ統合しない。二作品全体は未完。',
]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in PRIMITIVES)
    c=v('context');rest=k('ra');moving=k('zbm');initial=k('zb4')
    ruler=lambda frame:k('zby',frame,c)
    initialconditions=[k('eivf',frame,initial) for frame in (rest,moving)]+[k('eivg',rest,moving,initial),k('eivl',rest,moving,initial)]
    physical=both(*initialconditions,op('e',k('zci',k('zcj')),c),k('eiwn',k('zcj')),k('eixs',c),k('eipw',ruler(rest),rest,c),k('eigy',*history(ruler(rest),rest,c)),k('eivv',ruler(moving),c),k('eipw',ruler(moving),moving,c))
    text+=define('eixt',[('context','d')],physical)
    fields=[('place','a'),('frame','a'),('role','a'),('value',R),('context','d')]
    coord=k('zcy',v('place'),v('frame'),v('role'),k('ta'),c)
    text+=define('eixu',fields,both(k('eixq',v('place'),v('frame'),v('role'),c),k('ba',v('value')),k('ba',coord),k('sca',v('value'),coord)))
    for designation,printed,rule,frame,role in COORDINATES:
        text+=define(rule,[('place','a'),('value',R),('context','d')],k('eixu',v('place'),k(frame),k(role),v('value'),c))
    text+=content('eix3',k('eixt',k('zb6')))
    notation=[k('eislo',k(sign),'r[p '+rule+']',k('eirf'),v('point')) for sign,printed,rule,frame,role in COORDINATES]
    notation += [k('eisd4',k('zc2'),k('rd'),k(sign),k(target),k('eirf'),v('point')) for sign,target in (('eisnb','ra'),('eisna','zbm'))]
    text+=content('eix4',both(*notation))
    text+=content('eix5',both(k('eislz',k('zc2'),k('rd'),quote('eix3'),k('eisms'),v('point')),k('ug',k('zc2'),k('rd'),quote('eix3'),k('eisms'),v('point')),k('zao',k('zcg'),k('zc2'),k('eisms'),v('point')),'t[k eix4[]][v point]'))
    text+='d eix6[] f[j s[k eix5[]]].\n'
    text+=define('eix7',[],both(k('eir3',k('zc2'),k('rd'),k('eirf'),quote('eix6'),k('ri')),k('ue',k('zco'),k('zc2'),k('ri')),op('u',op('e',k('zco'),k('zc2')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eix7',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='imagined_measured_space_sentence',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/spatial-coverage-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'] += [dict(symbol=n,role='designation',forms=[dict(text=printed,language='de',role='printed_identifying_form')]) for n,printed,rule,frame,role in COORDINATES]
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
