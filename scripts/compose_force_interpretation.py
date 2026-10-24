"""Connect the interpretation introduction and the two prospective wordings."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-resting-charge-force.noema';PARENT_BASIS='data/resting-charge-force-basis-v1.json'
FULL='examples/v014/einstein-force-interpretation.noema';CORE='examples/v014/force-interpretation-core.noema'
BASIS='data/force-interpretation-basis-v1.json';ANNOTATIONS='data/force-interpretation-identifiers-v1.json'
INDICES=[358,359];WHOLE_INDICES=[358,163,164,165,166,359]
PRIMITIVES={
 'eisqm':([], 'u0173第一文で、直前の六つの場変換式の解釈のために、以下の注記を導入する箇所。'),
 'eisqn':([], 'u0173第六文で、先行する力と場の同定を受けて、直前六式の電気側三式を二つの言い表しへ導く箇所。続く番号付き二項を導入する。'),
 'eisqo':([('wording','a'),('target','i[e]'),('interpretation','i[e]'),('scope','a'),('context','d')], '指定された言葉による記述の仕方wordingを用いて、同じscopeのtargetの式又は内容を、interpretationの対象・量・条件・単位と役割対応の下で述べることができる。数式の記号を自然言語の物理的な役割へ展開するような記述可能性を含む。許される近似や留保は当該の記述に保ち、それを落とした厳密な同値の保証とはしない。語の見た目、両内容がたまたま真であること、実際の発話完了だけでは成立しない。ここでは本文で指示する記述の仕方を引数にし、内容を実行したり同義性を自動判定したりしない。言い方の個数・順序、著者がその可能性を主張することは別に合成する。'),
}
MEANINGS={
 'ejw7':'現在の物理的な両場と全領域の比較範囲ejubで、kの電気側znrの三成分が、旧両場を同じ逆座標変換で混合したs6kと領域znt全体で一致する。直前の係数1の六式の最初の電気側三式を指定し、磁気側の変換式を同定内容に加えない。',
 'ejxa':'同じ点状電気量のKでの単位値1とkでの単位値1、Kに静止する場合とkに当該瞬間静止する場合の現在の力・場の同定を合わせる解釈条件。二つの静止条件の両方を事実として要求せず、条件文を保持する。',
 'ejxb':'同じ電気側三式ejw7を、同じ単位電気量・力・場の解釈ejxaの下で、指定した二つの異なる言い表しzpq/zprによって述べられるという内容。これ以外の言い方の不可能性は主張しない。',
 'ejxc':'同じ電気側三式ejw7と、先の単位電気量・力の解釈ejxaを、二つの言い表しが可能だという著者のmithinの前提として合わせる。',
 'ejxd':'同じ著者が、直前の表示eisqaの最終六式ejvmについて、ここから続く単位電気量・力の注記と二表現の導入を説明として位置付ける。各注記の内容と著者の帰属は既存の四文と末尾文で保持する。',
 'ejxe':'同じ著者がejxcを受けて二つの言い表しの可能性ejxbを帰結として提示し、後続zpq/zprを順に第一・第二項へ結ぶ。二項を別の内容へ替えず、具体的内容の完成や推論の正しさを先取りしない。',
 'ejxf':'第一文の六式の解釈導入ejxdを述べるメッセージ。',
 'ejxg':'第一文を同じ著者・論説へ帰属し、直前の最終六式の表示の後へ置く。旧358主張の後ろへ保存し、本文の順序はueで保持する。',
 'ejxh':'第六文の二つの言い表しへの帰結付き導入ejxeを述べるメッセージ。',
 'ejxi':'第六文を同じ著者・論説へ帰属し、瞬間静止に関する第五文の後へ置く。後続二項との順序はejxeで保持する。',
}
LIMITS=[
 'u0173全六文を原刊909頁で連続して読む。第一文のdieser Gleichungenは直前M0314の六式、第六文のdie ersten dreiは電気側X′,Y′,Z′の三式を指す。二段組の最初の三行全体へ読み替えない。',
 '第一文のwirは同じ著者による論述の声と読む。以下の注記を六式の解釈として提示する説明関係を保持し、読者全員の同意や新しい実験を追加しない。',
 '第二文は点状の電気量1の仮定と距離1 cm・力1 Dynによる校正説明、第三文は相対性原理に基づく移動系での同じ電気量1の推論である。校正の第一対象が及ぼす力と、第四・第五文で同じ対象自身に働く力を区別する。',
 '第四・第五文はそれぞれKへの静止とkへの少なくとも当該瞬間の静止を前件とする。kの瞬間静止は座標時刻微分0で、加速度0や近傍全体の静止ではない。単位電気量、位置、場、力を同じ対象・評価出来事・系・単位へ接続する。',
 '校正出来事zooと力の評価出来事zpoの同一性又は非同一性を補わない。校正のcm/秒の座標を場のta/rbの数値へ代入せず、仮定の記録を実測や真空内の試験体の実在へ変えない。場の試験応答と機械的な力の意味は既存の明示規約を共有する。',
 'mithinは電気側三式と単位電気量・力の同定に基づく著者の帰結として読む。二つの言い表しを予告する能力・可能の内容を、著者の発話完了や処理系による同義性証明にしない。言葉を着せるという比喩は数式の物理的な役割を言語的に展開する働きとして保持する。',
 'folgende zweiは続く番号付き第一項zpqと第二項zprを指す。二つの相違と順序を構成し、可能な言い方がこの二つだけとは主張しない。後続u0174–u0175の近似の留保・旧来と新しい言い方の対比・内容全体はそれぞれの単位で別に確認する。',
 '原文の主張を真と証明することと記述することを区別する。相対性原理からの電荷不変性、定義による力の同定、二つの言い表しへの推論は著者に帰属し、有限検査の成功だけから意味同値又は物理的真理を認定しない。',
 '旧358主張・旧版・旧証拠を保ち、新しい第一文と第六文を末尾へ追加する。u0173の本文順序は358,163,164,165,166,359であり、旧文162のu0165の逆変換提示を置き換えない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    p=v('point');a=k('rd');scope=k('zno');paper=k('eirf')
    text+=content('ejw7',both(evaluate('ejub'),k('ejs3',k('znr'),k('s6k',k('tc'),k('zb7'),k('znl'),k('znm')),k('znt'))))
    text+=content('ejxa',both(*(evaluate(n) for n in ('ejwf','ejwm','ejww','ejwx'))))
    text+=content('ejxb',both(*(k('eisqo',k(n),quote('ejw7'),quote('ejxa'),scope,p) for n in ('zpq','zpr')),op('u',op('e',k('zpq'),k('zpr')))))
    text+=content('ejxc',both(evaluate('ejw7'),evaluate('ejxa')))
    notes=('zoy','zpg','zph','zpi','eisqn')
    text+=content('ejxd',both(k('eisox',k('eisqa'),quote('ejvm'),p),k('uf',a,k('eisqa'),k('eisqm'),p),*(k('uf',a,k('eisqm'),k(n),p) for n in notes),k('ue',k('eisqm'),k('zoy'),p),*(op('u',op('e',k('eisqm'),k(n))) for n in notes)))
    text+=content('ejxe',both(k('zc',k('eisqn'),a,quote('ejxc'),quote('ejxb'),scope,p),k('eislk',k('zpq'),k('eisqn'),'n p b b',paper,p),k('eislk',k('zpr'),k('eisqn'),'n p c b',paper,p),*(k('uf',a,k('eisqn'),k(n),p) for n in ('zpq','zpr')),k('ue',k('eisqn'),k('zpq'),p),k('ue',k('zpq'),k('zpr'),p),*(op('u',op('e',k(x),k(y))) for x,y in (('eisqn','zpq'),('eisqn','zpr'),('zpq','zpr')))))
    for val,msg,claim,node,prior in [('ejxd','ejxf','ejxg','eisqm','eisqa'),('ejxe','ejxh','ejxi','eisqn','zpi')]:
        text+='d '+msg+'[] f[j s[k '+val+'[]]].\n'
        text+=define(claim,[],both(k('eir3',k(node),a,paper,quote(msg),k('ri')),k('ue',k(prior),k(node),k('ri')),op('u',op('e',k(prior),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==358
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=deepcopy(old['statements'])+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ejxg','ejxi')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='force_interpretation_introduction_and_two_wordings',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=WHOLE_INDICES).document
    ann=json.loads(read('data/resting-charge-force-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
