"""Present the same point's motion task and the section-three substitution."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_point_motion_transform import ROOT,read,PATH
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-point-motion-transform.noema';PARENT_BASIS='data/point-motion-transform-basis-v1.json'
FULL='examples/v014/einstein-point-motion-claim.noema';CORE='examples/v014/point-motion-claim-core.noema'
BASIS='data/point-motion-claim-basis-v1.json';ANNOTATIONS='data/point-motion-claim-identifiers-v1.json';INDICES=(352,353)
PRIMITIVES={
 'eisou':([('node','a'),('author','a'),('question','i[g['+PATH+']]'),('scope','a'),('context','d')],'著者が指定箇所・範囲・提示文脈で、記述された質問の答えを見いだすことを課題として提示する。答えの候補は個体役割と実数量を受け実数量を返す関数で、その対象・尺度・適合条件は引用された質問に保持する。既存zdcと同じ課題提示の一般規約をこの回答型に適用する。解の存在・唯一性・発見済み・証明済み、実際の探索実行を含意しない。'),
 'eisov':([('node','a'),('author','a'),('division','a'),('established','i[e]'),('document','a'),('context','d')],'著者がnodeで同じdocumentの先行区分divisionにおいて展開し得たものとしてestablishedの内容を参照し、現在の論述に用いる。参照先の区分と引用内容を共に保持する。節番号だけの類似、新しい内容の導入、将来の導出の予告と区別する。この帰属から内容の真理・導出の妥当性・読者による実行を認定しない。'),
 'eisow':([], '固定原文einstein-1905:u0133第一文で、同じ点のKに対する運動を求める課題を提示する箇所。次の変換の箇所zkhと区別する。'),
}
MEANINGS={
 'ejnq':'第五節で同じ点のKでの全期間の運動を求めるejnnを、著者が解くべき課題として提示する。問いの引用から結果の公式や答えの存在を実行評価しない。',
 'ejnr':'u0133第一文の課題提示ejnqを述べるメッセージ。',
 'ejns':'同じ点の運動を求める課題を同じ著者・論説へ帰属し、直前の平面運動の仮定zkgに続ける。',
 'ejnt':'著者が同じ前提ejnoの下で、同じ点の仮定内容ejmyをKでの三式ejnpへ書き換えて得ると提示する。先行第三節で展開した現在の最終変換ejehへの参照と、導入するx/y/z/tの既出の量規則を同じ提示に結ぶ。',
 'ejnu':'u0133第二文からu0134の三式までの書換え提示ejntを述べるメッセージ。コロンの後の三式を別の発話へ分断しない。',
 'ejnv':'変換による三式の提示を同じ著者・論説へ帰属し、同じ点の運動を求める課題eisowの後に置く。',
}
LIMITS=[
 '原刊905頁でu0133の二文とu0134の三式を、先行する点の仮定と次の平行四辺形則の考察の間に読む。第一文は課題、第二文と表示式は§3の変換によって得る書換えの提示である。全169本文文字と三数式要素を対象とする。',
 'Gesucht istは同じ点zkbのKでの全期間の三位置を時刻の関数として求める課題と読む。ejnnは全実時刻の実際の履歴と一致する候補を指定するが、問いに答えの三式や解の存在・発見済みを先取りしない。',
 'Führt man ... ein, so erhält manを、著者が同じ変換条件の下で元の運動式をKの数量で書き換えて得るというzd3の提示として読む。読者が現実に計算した履歴や新たな物理的実験は追加しない。',
 'in §3 entwickeltenは、同じ論説の先行第三節eismsで展開した最終変換ejehを現在用いるという参照。既存の節見出しが深さ2・番号3と範囲を指定している。別の節や旧係数φ付きの途中式へ参照先を替えない。',
 'x/y/z/tは同じKの三空間座標と時刻の既出規則eixv/eixw/eixx/eiwtへ結ぶ。kのξ/η/ζ/τを単に改名するのではなく、同じ出来事の現在記録を結ぶssnを元の平面三式に適用する。',
 '結果のx=(wξ+v)/(1+vwξ/V²)t、y=√(1−(v/V)²)/(1+vwξ/V²)wηt、z=0は全K現在記録に適用する。正の根とβの逆数、同じ二速度定数、全期間と同じ対象を保持し、両系の時刻数値を等置しない。',
 '非零分母は商で運動をtの関数として表す際の明示した定義域であり、原文に印刷された追加条件とはしない。負の分母・負や零の成分を許し、点の光速上限を追加しない。零分母で元の変換に合う記録があり得ることも前段の証拠に保持する。',
 '新規関係は同じ課題提示の関数回答型と、先行区分で展開した内容を用いる一般参照の二つ。残る一基本記号は発話箇所の個体参照である。物理的な対象・測定・世界線・数式を一文専用の基本述語へ置き換えない。',
 '有限検査、同じ入力に依存する過去の証拠、原文全体の意味判断を分ける。書換え提示の帰属から実切断の一般定理・物理的真理・意味同値の自動証明を導かない。u0135以降の平行四辺形則・速度の大きさと角度は後続。',
]


def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    point=v('point');author=k('rd');scope=k('eisoq');node=k('zkh')
    text+=content('ejnq',k('eisou',k('eisow'),author,quote('ejnn'),scope,point))
    notation=[k('eislo',k(sign),'r[p '+rule+']',k('eirf'),point) for sign,rule in (('eisne','eixv'),('eisnf','eixw'),('eisng','eixx'),('eism5','eiwt'))]
    text+=content('ejnt',both(k('zd3',node,author,quote('ejno'),quote('ejmy'),quote('ejnp'),scope,point),k('eisov',node,author,k('eisms'),quote('ejeh'),k('eirf'),point),*notation))
    for body,message,claim,where,previous in (('ejnq','ejnr','ejns','eisow','zkg'),('ejnt','ejnu','ejnv','zkh','eisow')):
        text+='d '+message+'[] f[j s[k '+body+'[]]].\n'
        text+=define(claim,[],both(k('eir3',k(where),author,k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(where),k('ri')),op('u',op('e',k(previous),k(where)))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ejns','ejnv')];added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='point_motion_task_and_section_three_substitution_presented',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/point-motion-transform-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
