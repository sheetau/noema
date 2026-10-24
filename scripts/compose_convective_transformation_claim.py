"""Present the ninth-section transformation and both accompanying displays."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,v,call as k,op,both
from scripts.compose_material_relative_frame import define
from scripts.compose_convective_transformed_quantities import SETTING,GLOBAL,args
from scripts.compose_doppler_infinity import quantified
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-convective-transformed-quantities.noema';PARENT_BASIS='data/convective-transformed-quantities-basis-v1.json'
FULL='examples/v014/einstein-convective-transformation-claim.noema';CORE='examples/v014/convective-transformation-claim-core.noema'
BASIS='data/convective-transformation-claim-basis-v1.json';ANNOTATIONS='data/convective-transformation-claim-identifiers-v1.json';INDEX=410
CASES=[(n,t) for n,t in SETTING if n!='context']
PRIMITIVES={
 'eiswn':([], '固定原文u0233のTransformiert manからdie Gleichungen:までの、原系での成立仮定・二節の変換式の使用・新系の式の導入を行う文章箇所。'),
 'eiswo':([], '固定原文u0235のwobeiという、M0389の六式に続く同じ速度・密度の関係を導く箇所。冒頭の別のwobeiとは区別する。'),
}
MEANINGS={
 'ekz3':'同じ物理的contextでekzxの二系変換設定に従う全引数について、元の同じGLOBALの方程式ekyqを要求する内容。先行のekzcを現在の変換設定へ限定して使う。変換後の式を成立条件へ加えない。',
 'ekz4':'ekz3と同じ全設定・同じcontextについて、構成した新二場・領域・密度・三速度の六回転式ekzzを表示する内容。磁気側は原刊に印刷されたsemfで、ρ′の発散式は次の表示へ分ける。',
 'ekz5':'同じ全設定について、構成した新三速度と同じρ′の五等式ekz2を表示する内容。ρ′を新電場の発散にも同じ元の密度の変換にも結び、別の密度値を二つ置かない。',
 'ekz6':'同じ33引数のekzzとekz2を合わせる変換結果。二つの表示が二場・領域・光速度・系速度・元の分布と量・文脈を共有する。片側だけ別の設定を存在証人に取らない。',
 'ekz7':'同じ二系変換設定の全引数について、六回転式と五等式の全結果ekz6を要求する内容。元の方程式と変換則を用いてこれを得るという著者の導出の結論であり、有限検査から真理を認定しない。',
 'ek2a':'著者が先行ekzcを同じKの方程式として仮定し、diese Gleichungenを先行導入eiswfの同じ内容へ照応させる。現在の変換設定での旧法則ekz3から結果ekz7を得るとzcで提示し、同じ論説の第三節の最終座標変換ejehと第六節の最終場変換ejvmをeisovで参照して用いる。双方向の同値性や導出の健全性を追加しない。',
 'ek2b':'変換後六式の表示zqaをekz4へ、wobeiに続く表示zqbを五等式ekz5へ結ぶ。著者が同じ五等式を補足として述べるuhと、導入から六式・wobei・五等式へ続く説明ufを保持する。',
 'ek2c':'u0233–u0236の仮定・照応・二節参照・導出提示・六式・wobei・五等式を一続きに結ぶ。四箇所は相異なり、同じ論説の本文順序で進む。後続u0237の物理的速度同定や相対性への結論はここへ混ぜない。',
 'ek2d':'同じ四単位の全内容ek2cを述べるメッセージ。引用した方程式や導出の一般的な真理をメッセージの提示と混同しない。',
 'ek2e':'著者rd・論説eirfへ同じメッセージek2dを帰属し、直前の条件付きLorentz基礎eiswkに続く一文として接続する。旧410主張を保存して新しい一主張を追加する。',
}
LIMITS=[
 '固定u0233–u0236を原刊916頁下半分と全MathMLへ照合し、一文の変換導入・六式・wobei・五等式として読む。改行・二列配置・式末尾の句点を別の物理命題へ変えない。',
 'welche im System K gelten mögenは、先行する同じ原系方程式ekzcがKで成立すると仮定して議論する役割ugとして保持する。現実の実験確認やKでのみ成立する主張にはしない。先行の担体解釈の条件付き基礎を、変換の計算へ新しい剛体付着の前提として加えない。',
 'mit Hilfe der Transformationsgleichungen von §3 und §6は、二節の最終式を現在の同じK/k・V・速度・単位へ適用する手段として読む。eisovが同じ節と引用内容を保持し、ekzxが正逆s46とs6k/s6lを現在の対象へ実際に用いる。過去の特定の場の数値を現在の場へ代入せず、φ又は未決定の共通係数付きの途中式を最終則に取り替えない。',
 'so erhält manは、元の方程式と同じ変換設定から新しい式を得るという著者の提示zcである。本文が述べていない逆向きの推論、証明の正しさ、読者の実行、式の実証を追加しない。引用内容が偽でも同じ著者帰属を記述できる。',
 '物理的contextを各閉じた内容の評価点に固定し、残る32引数を全称量化する。ekzxの同じ変換設定が前提・二表示・結論に共通であり、元の法則は同じGLOBAL32、結果の二式は同じSETTING33を使う。これは全実数・全関数域の法則の内容であり、有限標本の主張へ縮めない。',
 '新しい三速度とρ′は、元の実際の規格化密度・流速から、同じ新座標の逆像で構成するekzu/ekzvを使う。ρ′の五等式と六式で別の量を選ばず、同じ新電場の実際の偏微分に接続する。新系で測った電荷の速度との同定は次文u0237で扱い、今回の前提には入れない。総電荷の系間不変も前提にしない。',
 '分数を定義するV>0、|v|<V、正のβ、D=V²−v ux≠0を明示する。D>0、流速の絶対値<V、正の電荷密度を付加しない。分母が零の点を領域から隠して除くことはせず、考察領域全体で式が定義されるという適用規約を保持する。',
 '原刊M0389の磁気側三式に1/Vがないことをsemfへ保存する。M0383と同じ形に修正せず、原著者の導出の妥当性や誤植の歴史的確定を完成条件にはしない。電気側の三式の1/Vと対流項、磁気側回転の符号、三対角微分、五等号を保持する。',
 '新しい原始関係はない。二つの定数は本文箇所の参照のみで、仮定・照応・推論・節参照・内容表示・説明・順序・著者帰属は既存の一般関係から構成する。旧原文・旧版・旧410主張・全判断と証拠を保存する。',
]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in PRIMITIVES)
    text+=define('ekz6',SETTING,both(k('ekzz',*args(SETTING)),k('ekz2',*args(SETTING))))
    for root,law,fields in [('ekz3','ekyq',GLOBAL),('ekz4','ekzz',SETTING),('ekz5','ekz2',SETTING),('ekz7','ekz6',SETTING)]:
        text+=content(root,quantified('f',CASES,op('y',k('ekzx',*args(SETTING,context=v('point'))),k(law,*args(fields,context=v('point'))))))
    p=v('point');a=k('rd');paper=k('eirf');scope=k('eisv6');node=k('eiswn')
    refs=[k('eisov',node,a,k(section),quote(rule),paper,p) for section,rule in [('eisms','ejeh'),('zno','ejvm')]]
    text+=content('ek2a',both(k('ug',node,a,quote('ekzc'),scope,p),k('eiswm',node,a,k('eiswf'),quote('ekzc'),paper,p),k('zc',node,a,quote('ekz3'),quote('ekz7'),scope,p),*refs))
    nodes=('eiswn','zqa','eiswo','zqb')
    text+=content('ek2b',both(k('eisox',k('zqa'),quote('ekz4'),p),k('eisox',k('zqb'),quote('ekz5'),p),k('uh',k('zqb'),a,quote('ekz5'),scope,p),*(k('uf',a,k(x),k(y),p) for x,y in zip(nodes,nodes[1:]))))
    text+=content('ek2c',both(evaluate('ek2a'),evaluate('ek2b'),*(k('ue',k(x),k(y),p) for x,y in zip(nodes,nodes[1:])),*(op('u',op('e',k(x),k(y))) for i,x in enumerate(nodes) for y in nodes[i+1:])))
    text+='d ek2d[] f[j s[k ek2c[]]].\n'
    text+=define('ek2e',[],both(k('eir3',node,a,paper,quote('ek2d'),k('ri')),k('ue',k('eiswk'),node,k('ri')),op('u',op('e',k('eiswk'),node))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ek2e',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='ninth_section_transformation_premise_references_and_displays',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/convective-transformed-quantities-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
