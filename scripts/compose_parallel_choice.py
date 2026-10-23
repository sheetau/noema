"""Integrate the complete frame-motion paragraph and its licensed assumption."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_axis_states import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_rod_methods import interval
from scripts.compose_material_axes import ROLES
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-axis-states.noema';PARENT_BASIS='data/axis-states-basis-v1.json'
FULL='examples/v014/einstein-parallel-choice.noema';CORE='examples/v014/parallel-choice-core.noema'
BASIS='data/parallel-choice-basis-v1.json';ANNOTATIONS='data/parallel-choice-identifiers-v1.json';INDICES=(268,269)
RULE='i[h[a '+R+' d] c]'
PRIMITIVES={
 'ud':([('author','a'),('premise_nodes','h[a] c'),('conclusion_node','a'),('context','d')], '著者が指定した文章箇所の集合を根拠側として、結論箇所を帰結として提示する。論理的含意、証明の妥当性、因果関係とは区別する。根拠の十分性を判定する関係ではない。'),
 'eism3':([('domain','h[a] c'),('forward','h[a] a'),('inverse','h[a] a'),('reference','a'),('axis','a'),('context','d')], '同じ物理的設定のreferenceと指定した運動方向axisを保つ空間的な対称操作が、候補domainの記述上でforwardとinverseとして作用する。恒等写像という名前や任意の候補番号の置換だけでは認めず、設定を区別しない非自明な空間操作に由来するという物理的な分類を保つ。対称な候補がその操作で不変でもよい。領域保存・可逆性・許容条件の保存はsfsで別に構成し、特定の結論を持つ候補の存在や推論の十分性は含めない。'),
 'eism4':([('agent','a'),('adoption','i[e]'),('scope','a'),('document','a'),('context','d')], 'agentが同じdocumentのscopeにおける論考を進めるため、adoptionとして記述した仮定採用を行ってよいという認識上の権原・正当な許容がある。単に禁止されていないこと、本人の希望、法的な権利、採用済み、採用内容の真理や証明とは異なる。閉じた採用行為の記述に同じ内容と範囲を固定する。'),
 'eism5':([], '第三節で引用符付きtとして言及される時刻記号の呼称個体。同じ静止系時刻の適用規則を合成側で結ぶ。実数値そのものや特定の時計の個体ではない。'),
 'eism6':([('use','a'),('designation','a'),('scope','a'),('document','a'),('context','d')], '同じdocumentのscopeでdesignationを意味のある記号として用いる出現の全範囲にuseが属する。本文・式・挿入説明を含む同じ記号の使用を扱い、都合のよい標本だけに限定しない。語形がたまたま同じ別の記号や別の議論は混ぜず、範囲の完全性を有限列挙から認定しない。'),
 'eism7':([('use','a'),('rule',RULE),('document','a'),('context','d')], '同じdocumentの記号使用useにおいて、対象・値・状況の役割を閉じたruleに従って解釈する。規則を一度引用するだけではなく当該使用への適用を保持し、引用から測定済みや値の実在を導かない。'),
 'eisna':([], 'この設定で第二の座標系を指す小文字kという記号の呼称個体。対象zbmとの結合は命名行為で保持する。'),
 'eisnb':([], 'この設定で既出の静止基準を指す大文字Kという記号の呼称個体。対象raとの結合は命名行為で保持する。'),
}
MEANINGS={
 'eiwk':'同じ静止基準raの原点・三軸を初期設定から引き継ぎ、現行eiv7の全軸幾何、全物質点の静止eipw、代表原点の完全な静止eit2を同じ運動比較期間へ結ぶ。移動側に静止を課さない。',
 'eiwl':'同じ設定の移動側の全原点・軸・計器の正X並進eivzと三軸幾何eiv7、静止側のeiwkを合わせる。初期長さ保存、時計同期や加速機構を追加しない。',
 'eiwm':'同じ候補履歴にeiwjの全時刻被覆と配置一意性、静止基準の同じ軸のeiwkを要求する。候補ごとに異なる設定を持てるが、初期対象と速度は共通である。',
 'eiwn':'一つの候補履歴eiwmに、同じ期間を通して対応三軸が平行であるeiwbを課す。時刻ごとに別の候補を選んで済ませない。',
 'eiwo':'全時刻で平行な許容候補eiwnが一つ存在するという可能性の内容。まだ特定の候補を現実化したり証明済みとしたりしない。',
 'eiwp':'第一文で設定したzb6を同じ選択候補zcjの文脈に固定し、全静止系時刻に軸配置が存在し一意であるeiwmを述べる内容。平行候補の存在とは区別する。',
 'eiwq':'同じ設定と運動方向を保つ空間的対称操作eism3と、候補領域での可逆性・許容条件eiwmの保存sfsを結ぶ理由内容。これだけでeiwoの存在を導かない。',
 'eiwr':'同じ著者が平行候補の存在eiwoを第三節の議論へ仮定として採用する行為内容。許容の対象として引用する。',
 'eiws':'eiwrを採用してよいという認識上の権原eism4と、その根拠としてeiwqの対称性を挙げるzctを合わせる。採用行為や引用内の物理条件を実行しない。',
 'eiwt':'指定した時点・値・状況について、同じ静止系ra・時間単位rbの有効で存在するylの値を指すという時刻記号の適用規則。移動側の時刻を代入しない。',
 'eiwu':'tの量の解釈をeiwtへ固定し、同じ論説で同じ記号を使う非空の全範囲eism6へ同じ規則を適用する。immerを一つの使用例や第三節内だけへの指定に弱めない。',
 'eiwv':'第一文で採用する、同じ運動後の設定zb6におけるeiwlの条件内容。',
 'eiww':'同じ二系をk/Kとして参照する記号の採用と、初期設定へ追加するeiwvの仮定採用を合わせた第一文の設定操作。',
 'eiwx':'Es werde ... erteiltとmitteilen mögeを、一つの設定操作eiwwへの指示として保持するメッセージ。実際の加速実施の報告ではない。',
 'eiwy':'第一文の設定指示eiwxを同じ著者・論説へ帰属し、u0043の初期設定の後という本文順序を保持する。',
 'eiwz':'同じ設定の帰結として配置一意性eiwpを述べ、平行候補の存在を仮定してよいというeiws、tの全使用の規定eiwuとその括弧による補足を合わせる第二文の内容。',
 'eiw2':'第二文の帰結・認識上の許容・対称性の根拠・時刻記号の挿入説明を述べるメッセージ。平行運動の実証へ替えない。',
 'eiw3':'第二文全体を同じ著者・論説へ帰属し、第一文の後に置く。',
}
LIMITS=[
 'u0044全687文字・526本文文字を対象とする。Es werde ... erteilt / mitteilen mögeは第一文の設定指示、Jeder Zeit ... entspricht dannはその設定内の帰結、befugt anzunehmenは認識上の正当な許容として読む。',
 '小文字kは同じ第二系zbm、大文字Kは既出の静止基準raを指す記号の導入と読む。速度vはzb7、増加するxは静止系の正X方向であり、前の棒のybと同一視しない。M0070/M0073/M0074のtは同じ静止系時刻の記号である。',
 '原点・三軸・物差し・全時計へ同じ正X速度を与える。軸と物差しは全物質点、時計は代表配置を追う。加速機構、加速中の剛性、運動前後の長さ不変、同期済みや内部時計停止を補わない。',
 '各静止系時刻の配置一意性はeiwjで全実時刻を覆い、全対応記述の同じ原点・全軸成員の座標一致を要求する。物質線の幾何と静止側の同じ原点・軸を完全履歴に結ぶ。',
 'so beschaffen sein kannは全期間で平行な一つの許容運動があるという候補存在として読む。befugtはその存在内容を仮定として採用してよいという権原であり、仮定の真理、採用完了又は特定候補の現実化を主張しない。',
 'Symmetriegründenは、同じ設定と運動方向を保つ空間的対称操作の下で許容条件が保存されるという理由として明示する。原文は具体的な変換・運動方程式・存在証明を与えないため、回転角や反射面を特定せず、空間操作への対応をeism3の物理的な意味入力として保持する。任意の候補番号の置換を対称性とみなさず、可逆性と条件保存はsfsで構成する。理由への帰属とその十分性は分ける。',
 '対応三軸は全時刻で平行とするが、逆向きも許す。二原点、正方向又はX支持直線の一致は追加しない。静止側の軸の保持を、移動側の静止へ取り違えない。',
 '括弧のimmerは、この議論の同じt記号の全使用が静止系時刻の規則eiwtに従うこと。規則の引用から時刻測定の実行や全系共通の時間を導かない。',
 'wirは著者が論考を進める声とし、読者全員の同意や物理学者集団の人数を補わない。帰結提示ud・括弧補足eisa5・理由帰属zctは内容の真理を自動で実行しない。有限検査と全段落の通読判断は分け、二作品全体は未完である。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    c=v('context');f=k('ra');origin=k('zbn',f,c);bounds=interval(f,c)
    traces=[k('eismh',origin,f,k('ta'),k('rb'),k(a),c) for a in ROLES]
    same=[op('e',origin,k('zbn',f,k('zb4')))]+[op('e',k('zbo',f,k(a),c),k('zbo',f,k(a),k('zb4'))) for a in ROLES]
    text+=define('eiwk',[('context','d')],both(k('eiv7',f,c),*same,*(k('eipw',k('zbo',f,k(a),c),f,c) for a in ROLES),k('eit2',origin,f,c,k('ta'),k('rb'),*bounds,*traces)))
    text+=define('eiwl',[('context','d')],both(k('eivz',c),k('eiv7',k('zbm'),c),k('eiwk',c)))
    hist=v('history');ctx=k('zci',hist)
    text+=define('eiwm',[('history','a')],both(k('eiwj',hist),k('eiwk',ctx)))
    text+=define('eiwn',[('history','a')],both(k('eiwm',hist),k('eiwb',f,k('zbm'),ctx)))
    text+=content('eiwo',q('g','history','a',k('eiwn',hist)))
    text+=content('eiwp',both(op('e',k('zci',k('zcj')),k('zb6')),k('eiwm',k('zcj'))))
    domain='i[history a]['+k('zch',hist,k('zb6'))+']'
    text+=content('eiwq',both(k('eism3',domain,'p zcr','p zcs',f,k('yn'),k('zb6')),k('sfs',domain,'p zcr','p zcs','p eiwm')))
    text+=content('eiwr',k('ug',k('zcp'),k('rd'),quote('eiwo'),k('eisms'),v('point')))
    text+=content('eiws',both(k('eism4',k('rd'),quote('eiwr'),k('eisms'),k('eirf'),v('point')),k('zct',k('zcq'),k('rd'),quote('eiwq'),k('zcp'),k('eisms'),v('point'))))
    val=v('value');moment=v('moment');time=k('yl',moment,f,k('rb'),c)
    text+=define('eiwt',[('moment','a'),('value',R),('context','d')],both(k('zcf',moment,f,k('rb'),c),k('ba',val),k('ba',time),k('sca',val,time)))
    use=k('eism6',v('use'),k('eism5'),k('eirf'),k('eirf'),v('point'))
    text+=content('eiwu',both(k('eislo',k('eism5'),'r[p eiwt]',k('eirf'),v('point')),q('g','use','a',use),q('f','use','a',op('y',use,k('eism7',v('use'),'r[p eiwt]',k('eirf'),v('point'))))))
    text+=content('eiwv',k('eiwl',k('zb6')))
    text+=content('eiww',both(k('ug',k('zcg'),k('rd'),quote('eiwv'),k('eisms'),v('point')),k('zao',k('zb5'),k('zcg'),k('eisms'),v('point')),*(k('eisd4',k('zcg'),k('rd'),k(sign),k(target),k('eirf'),v('point')) for sign,target in (('eisna','zbm'),('eisnb','ra')))))
    text+='d eiwx[] f[j m[k eiww[]]].\n'
    text+=define('eiwy',[],both(k('eir3',k('zcg'),k('rd'),k('eirf'),quote('eiwx'),k('ri')),k('ue',k('zb5'),k('zcg'),k('ri')),op('u',op('e',k('zb5'),k('zcg')))))
    premise='i[node a]['+op('e',v('node'),k('zcg'))+']'
    text+=content('eiwz',both(k('uh',k('zco'),k('rd'),quote('eiwp'),k('eisms'),v('point')),k('ud',k('rd'),premise,k('zco'),v('point')),k('ue',k('zcg'),k('zco'),v('point')),'t[k eiws[]][v point]','t[k eiwu[]][v point]',k('eisa5',k('zcp'),k('rd'),quote('eiwo'),quote('eiwu'),v('point'))))
    text+='d eiw2[] f[j s[k eiwz[]]].\n'
    text+=define('eiw3',[],both(k('eir3',k('zco'),k('rd'),k('eirf'),quote('eiw2'),k('ri')),k('ue',k('zcg'),k('zco'),k('ri')),op('u',op('e',k('zcg'),k('zco')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eiwy','eiw3')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='complete_frame_motion_and_symmetry_licensed_assumption',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/axis-states-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'] += [dict(symbol=n,role='designation',forms=[dict(text=printed,language='de',role='printed_identifying_form')]) for n,printed in (('eism5','t'),('eisna','k'),('eisnb','K'))]
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
