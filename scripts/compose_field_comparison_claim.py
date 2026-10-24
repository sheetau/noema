"""Present equivalence, equation form and the claimed common field factor."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_field_equations import FIELD,REGION
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-moving-field-definition.noema';PARENT_BASIS='data/moving-field-definition-basis-v1.json'
FULL='examples/v014/einstein-field-comparison-claim.noema';CORE='examples/v014/field-comparison-claim-core.noema'
BASIS='data/field-comparison-claim-basis-v1.json';ANNOTATIONS='data/field-comparison-claim-identifiers-v1.json';INDEX=155
FORM='h['+FIELD+' '+FIELD+' '+REGION+' '+R+'] c'
PRIMITIVES={
 'eispz':([('display','a'),('form','i['+FORM+']'),('electric',FIELD),('magnetic',FIELD),('region',REGION),('light',R),('context','d')], '同じcontextでdisplayの方程式群が、閉じたformの二場・領域・定数という各引数位置へelectric/magnetic/region/lightを代入した形を表すという構造上の対応。場は三空間成分から四座標の関数を返す型で、偏微分の独立変数、三軸の順序、定数、演算と差の符号を保持する。成分の表記又は同じ式の並べ方を変更しても役割の対応を保ち、追加の項・変更された軸・場を入れ替えた対応を許さない。表示と閉じた式の間で行う正の非零定数による分母払い等の正規化は別に明示・照合する。これは表示と実際の閉じた式・引数との対応であり、式の真理、二つの場の同値、数値結果の偶然の一致を認定する関係ではない。'),
 'eisp2':([], 'u0163第一文の二組の方程式が同じことを表すという理由付き・明白さ付きの主張箇所。'),
 'eisp3':([], 'u0163第二文の同形性を加え、対応する六関数が共通係数を除いて一致する必要性を述べる主張箇所。'),
 'eisp4':([], 'u0164のM0307にある六つの共通係数付き場変換式の表示箇所。直前zn2の結果導入に接続する。'),
}
MEANINGS={
 'ejub':'同じ現在のK/k、電磁過程、両場の物理的規約、両領域の真空、許容V/v、同じ逆座標写像による全領域一致を比較設定として保つ。式の成立、等価性、比例の成否を候補選定へ追加しない。',
 'ejuc':'同じ評価状況でKの方程式内容ejs6と変換後s6o、Kの方程式内容ejs6と移動系の物理的な場の内容ejtwが、それぞれ双方向に真偽を共有するという二つの条件。',
 'ejud':'比較設定ejubを満たす非空の全評価状況でejucが成立するという、二組ともKの式に等価だという著者の理由内容。一つの観測の一致へ縮めない。',
 'ejue':'同じ評価状況で変換後s6oと移動系の場のejtwが双方向に真偽を共有する。成分関数の等値や比例そのものは要求しない。',
 'ejuf':'同じ比較設定の非空全域でejueが成立するという、二組が同じことを表す必要性の内容。処理系が現実の等価性を証明したという宣言ではない。',
 'ejug':'二つの先行表示を同じ閉じた六式s5yの型へ結び、引数の二場だけを混合・逆像関数から移動系の二場へ対応させる。同じVと全領域一致を保持する構造の内容。',
 'ejuh':'現在の物理的な二場と同じ過程・領域の比較設定に、速度だけの同じψによるsak2の全六成分・全点の比例を接続する結果内容。非零性や値1は補わない。',
 'ejui':'同じ比較設定に、両組のKとの等価性ejucとベクトル表記以外の同形性ejugを加えた推論の前提。比例が成立すること自体で候補を選別しない。',
 'ejuj':'非空の全てのejuiの候補で、同じ全六成分の比例ejuhが成立するという、原著者のmüssenの必要性内容。命令や義務にしない。',
 'ejuk':'第一文で得る同じ意味の必要性ejufと、さらに二組の形が一致するejugを合わせた、第二文の推論の理由内容。',
 'ejul':'同じ著者が第一文で、二組ともKの式と等価だというejudから同じ意味を表す必要性ejufを提示し、それをOffenbarとして明白と位置付ける。',
 'ejum':'同じ著者が第二文で、先の比較とさらに同形である理由ejukから共通係数の必要性ejujを提示する。導出の帰属と処理系の論理的保証を分ける。',
 'ejun':'同じ著者が第三文で、共通係数の必要性から具体的な六式ejuhを結果として導入し、続く表示eisp4へ結ぶ。',
 'ejuo':'三文と表示式を同じ推論段落の順序へ結び、同じ二系・方程式への呼称と本文参照を保つ。',
 'ejup':'u0163–u0164の比較・共通係数・六式ejuoを述べるメッセージ。',
 'ejuq':'同じ著者・論説への段落の帰属と、直前の移動系六式eispxの後という順序を保持する。旧文155を置き換える。',
}
LIMITS=[
 'u0163の三文とu0164の六式を原刊908頁で連続して読む。理由付き等価性、明白さ、さらに同形であること、必要性、全六関数への共通係数、座標時刻への非依存、速度依存の許容、結果表示を保持する。',
 '等価性は同じ比較設定の非空全域で成立条件が一致するという読みであり、単独の真偽一致ではない。比較設定は物理的な両場・同じ過程・真空・座標域の対応を保ち、方程式や比例の成功例だけを選ばない。',
 '同形性は同じ六回転式の閉じた型と場引数の対応として構成する。正のVでの分母払い、二列配置と論理的な六条件の順の差を明示し、偏微分軸・符号・係数は変更しない。',
 'ψは速度だけを引数とするznzを同じ六成分と全点で共有する。原文の一組の全関数をこの六成分と読む。別の場の組全てについて同じ係数を選ぶという追加の普遍主張は補わない。速度依存を許すが実際の依存、非零性、正値、偶性、値1を要求しない。',
 '元の場からの混合と逆座標写像はs6k/s6l、全領域一致はsaj2、比例の全点・全成分はsai2/sak2を再利用する。現在の物理的な場の意味はejsy/ejtuへ接続する。',
 '六回転式だけでは変換後の式が導けない既存反例、同じ微分方程式を満たすだけでは比例が得られない定数場の反例を保持する。著者の理由と結論を記述し、原理の適用の片方向条件文を処理系が双方向同値へ格上げしない。',
 '固定M0307のM′右辺の小文字zは保存した原刊908頁の大文字Zへ局所訂正して読む。生資料・旧訂正記録は保持する。909頁のφ/ψの表記差と逆変換は後続。',
 '旧文155以外の357主張・旧意味規約・旧証拠を保持し、原文の全単位判断を有限検査や型検査から区別する。全実数・全関数域の有限列挙拒否を保持する。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    p=v('point');V=k('tc');speed=k('zb7');region=k('s6m',V,speed,k('znk'))
    text+=content('ejub',both(k('ejsy',p),k('ejtu',p),k('eispn',k('eispp'),k('ra'),k('znl'),k('znm'),k('znk'),p),*(k('ejsm',k(frame),k('ta'),k('rb'),p,k(domain)) for frame,domain in (('ra','znk'),('zbm','znt'))),k('s45',V,speed),k('saj2',region,k('znt'))))
    text+=content('ejuc',both(op('z',evaluate('ejs6'),evaluate('s6o')),op('z',evaluate('ejs6'),evaluate('ejtw'))))
    text+=content('ejud',k('ejrj',k('ejub'),k('ejuc'),p))
    text+=content('ejue',op('z',evaluate('s6o'),evaluate('ejtw')))
    text+=content('ejuf',k('ejrj',k('ejub'),k('ejue'),p))
    mixed=[k(n,V,speed,k('znl'),k('znm')) for n in ('s6k','s6l')]
    form='r[p s5y]'
    text+=content('ejug',both(k('s45',V,speed),k('saj2',region,k('znt')),k('eispz',k('eispq'),form,*mixed,region,V,p),k('eispz',k('eispx'),form,k('znr'),k('zns'),k('znt'),V,p)))
    text+=content('ejuh',both(evaluate('ejub'),evaluate('sak2')))
    text+=content('ejui',both(evaluate('ejub'),evaluate('ejuc'),evaluate('ejug')))
    text+=content('ejuj',k('ejrj',k('ejui'),k('ejuh'),p))
    text+=content('ejuk',both(evaluate('ejuf'),evaluate('ejug')))
    a=k('rd');scope=k('zno')
    text+=content('ejul',both(k('zc',k('eisp2'),a,quote('ejud'),quote('ejuf'),scope,p),k('zdg',k('eisp2'),a,quote('ejuf'),scope,p)))
    text+=content('ejum',k('zc',k('eisp3'),a,quote('ejuk'),quote('ejuj'),scope,p))
    text+=content('ejun',both(k('zc',k('zn2'),a,quote('ejuj'),quote('ejuh'),scope,p),k('eisox',k('eisp4'),quote('ejuh'),p),k('uf',a,k('zn2'),k('eisp4'),p)))
    nodes=('eisp2','eisp3','zn2','eisp4')
    text+=content('ejuo',both(evaluate('ejul'),evaluate('ejum'),evaluate('ejun'),k('eisch',k('eispf'),quote('ejs6'),scope,p),*(k('ue',k(x),k(y),p) for x,y in zip(nodes,nodes[1:])),*(op('u',op('e',k(x),k(y))) for i,x in enumerate(nodes) for y in nodes[i+1:])))
    text+='d ejup[] f[j s[k ejuo[]]].\n'
    text+=define('ejuq',[],both(k('eir3',k('eisp2'),a,k('eirf'),quote('ejup'),k('ri')),k('ue',k('eispx'),k('eisp2'),k('ri')),op('u',op('e',k('eispx'),k('eisp2')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==358
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=deepcopy(old['statements']);doc['statements'][INDEX]=dict(kind='assert',body=dict(kind='call',symbol='ejuq',arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='field_equivalence_same_form_and_common_factor_claim',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/moving-field-definition-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
