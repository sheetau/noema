"""Present the remaining light-speed proof task and its stated proof gap."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_origin_constants_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-origin-constants-claim.noema';PARENT_BASIS='data/origin-constants-claim-basis-v1.json'
FULL='examples/v014/einstein-light-proof-task.noema';CORE='examples/v014/light-proof-task-core.noema'
BASIS='data/light-proof-task-basis-v1.json';ANNOTATIONS='data/light-proof-task-identifiers-v1.json';INDEX=304
MEANINGS={
 'ei7v':'同じ設定でKの全光区間が現在の時計・測定規約によりVを持つなら、kの全光区間も同じVを持つという条件内容。両系のei43へ同じtcを渡す証明課題であり、課題の提示だけからその成立を導かない。',
 'ei7w':'この段階zfxまでの同じ論説eirfで、同じ著者が二原理eifj/eifyの両立性eif5の証明として提示した論証が存在しないという内容。単なる未発見、内容の偽、証明不可能、将来の未提示とは分ける。',
 'ei7x':'静止系の条件についての「仮定したように」を、先行wuで同じ著者が同じ真空光速度原理eifyを後続議論wvの仮定として採用したことへの振り返りとして記述する。本文順序を保ち、原理内容の真理や実証を加えない。',
 'ei7y':'現在段階の全光線の光速度保存の証明課題zga、既採用への挿入補足、両立性の証明未提示の説明と、それを課題の理由とするzgbを同じ著者・第三節へ結ぶ。',
 'ei7z':'証明課題とその理由ei7yを断定の伝達形式で述べる。課題を証明完了や読者への命令に替えない。',
 'ei72':'u0086全体を同じ著者・論説へ帰属し、直前の四加法定数の箇所zfqからの本文順序を保持する。',
}
LIMITS=[
 'u0086の一文全体とM0140を原刊900–901頁へ照合する。Wir haben nun zu beweisenは、この論述段階でこれから示す数学的・物理的課題の提示と読む。著者の一人称複数に読者全員の参加や人数を加えない。',
 'jeder Lichtstrahlは、先行の真空光伝播の全適用区間を意味する。現在のei43は完全・非空な全区間、各系の同期時計・局所表示・幾何学的光路長を保持し、特定の縦光線や球面波上の標本だけに狭めない。両系へ同じV=tcを渡し、距離と時間の個別の数値一致は要求しない。',
 'fallsの前件はKでの同じ速度法則、後件はkで測った同じ速度法則。条件内容を課題として引用し、両法則の現実の成立や四式からの導出済みとはしない。現在の測定規約によるei43を使い、旧sbc/smwの固定時計を流用しない。',
 'wie wir angenommen habenは、先行wuでの同じeifyの仮定採用への振り返りとして読む。eifyの系別のeifxを現在の時計条件と結ぶei43がこの箇所の前件であり、一般原理の採用を前件の実証と同一視しない。採用の範囲wvと、現在の課題を述べる第三節eismsを区別する。',
 'noch nicht geliefertはこの段階zfxまでの論説eirfでの証明未提示。既存zfr/sqiの提示関係を用い、現在の第三節内だけを探索して先行節の証明を見落とすことはしない。段階と対象内容を固定し、別の対象・著者・論説・後の段階の提示は該当しない。',
 '両立性は既存eif5により、同じ意味を保つ一つの許容設定で既出eifjとeifyが共に成り立つ余地と読む。原理ごとに別の設定を使うこと、現在点での両法則の真理、一般の証明認定とは区別する。',
 'dennは両立性の証明未提示を、現在の課題を行う理由として著者が挙げる関係zgbへ結ぶ。この理由の提示を論理的十分性の証明にはしない。未提示の内容と光速度保存の課題は異なる引用対象として保持する。',
 '次の球面波の放出設定と計算、両立性が示されたという結論は後続u0087–u0091の範囲。今回の課題提示からそれらの達成やφの決定を先取りしない。有限検査は結合と範囲の検査であり、一般物理的導出や意味同値の自動証明ではない。',
]

def definitions():
    point=v('point')
    text=content('ei7v',op('y',k('ei43',k('ra'),k('tc'),point),k('ei43',k('zbm'),k('tc'),point)))
    text+=content('ei7w',op('u',k('sqi',k('rd'),quote('eif5'),k('zfx'),k('eirf'),'p zfr')))
    text+=content('ei7x',both(k('ug',k('wu'),k('rd'),quote('eify'),k('wv'),point),k('ue',k('wu'),k('zfz'),point),op('u',op('e',k('wu'),k('zfz')))))
    text+=content('ei7y',both(k('zga',k('zfz'),k('rd'),quote('ei7v'),k('zfx'),k('eisms'),point),op('t',k('ei7x'),point),k('eisa5',k('zfz'),k('rd'),quote('ei7v'),quote('ei7x'),point),k('uh',k('zfy'),k('rd'),quote('ei7w'),k('eisms'),point),k('zgb',k('zfy'),k('rd'),quote('ei7w'),k('zfz'),k('eisms'),point),k('ue',k('zfz'),k('zfy'),point),op('u',op('e',k('zfz'),k('zfy')))))
    text+='d ei7z[] f[j s[k ei7y[]]].\n'
    text+=define('ei72',[],both(k('eir3',k('zfz'),k('rd'),k('eirf'),quote('ei7z'),k('ri')),k('ue',k('zfq'),k('zfz'),k('ri')),op('u',op('e',k('zfq'),k('zfz')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ei72',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_light_proof_task_and_compatibility_proof_gap',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/origin-constants-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
