"""Integrate the normalization choice and the same-event comoving conclusion."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,op,both
from scripts.compose_material_relative_frame import define
from scripts.compose_point_particle_dynamics import SETTING,CASES,args,coord,ROLES,ZERO,ONE
from scripts.compose_material_velocity import POINT,DOMAIN,CURVE
from scripts.compose_doppler_infinity import quantified
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-electron-representative-scope.noema';PARENT_BASIS='data/electron-representative-scope-basis-v1.json'
FULL='examples/v014/einstein-electron-coordinate-claim.noema';CORE='examples/v014/electron-coordinate-claim-core.noema'
BASIS='data/electron-coordinate-claim-basis-v1.json';ANNOTATIONS='data/electron-coordinate-claim-identifiers-v1.json';INDICES=(417,418)
# These are referential witnesses, not predicates hiding the sentence's meaning.
REFERENCES={
 'eisxv':('a','u0244で指定しu0245で考察する、同じ電子の同じ出来事への参照。Kの時刻零と位置原点を合成側で指定する。別の観測実験や出来事の発生を補わない。'),
 'eisxw':('a','u0245第一文の一般性を保つ仮定の許容・採用と考察への取上げの箇所。'),
 'eisxx':('a','u0245第二文の共動系での瞬間静止を明白として述べる箇所。'),
 'eisxy':('a','u0245で一つ選ぶ共動座標系への持続する参照。以前の具体的な移動系zbmとは同一視せず、同じ電子のvでの一定並進と物理的な座標対応をek5wで指定する。'),
 'eisxz':(POINT,'同じ選んだ共動系の四原点ずれへの参照。四成分は未指定であり、零ではない値も許す。ek5wの座標対応に結び、後続u0248の零原点選択をまだ加えない。'),
 'eisx2':(DOMAIN,'同じ選んだ共動系における同じ電子の局所履歴の座標時間領域への参照。非空性と内点、旧域との完全な双方向対応はek5wで構成する。'),
 'eisx3':(CURVE,'同じ選んだ共動系と時間領域における同じ電子の四座標曲線への参照。数値を任意に付けただけの軌道ではなく、ek5wとek5xで実際の履歴と三微分へ結ぶ。'),
 'eisx4':('a','u0245以降で同じ共動系を指す小文字kの表記。指示対象はeisxyであり、前の節の具体的なkを無条件に流用しない。'),
 'eisx5':('a','u0245でKの第一空間軸を指す大文字Xの表記。既存の軸役割ynへ結び、x座標値や独立の物体へ替えない。'),
}
MEANINGS={
 'ek6f':'同じ電子・速度・全物理設定の正規化ek56に、K=raと同じ指定出来事eisxvを結ぶ。四原点と瞬間速度(v,0,0)を共有し、光速上限や共動系をまだ要求しない。',
 'ek6g':'同じ評価状況・K・指定出来事においてek6fの一つの設定があるという仮定内容。原点での考察と正X方向の瞬間速度を共同証人に結ぶ。',
 'ek6h':'同じ設定の四座標の時刻成分を返す。静止系tの表記を同じ瞬間へ結ぶための射影。',
 'ek6i':'XとKの指示、vの同じ値eisxtへの射影、tの同じ設定の時刻への射影を表記の採用として保持する。',
 'ek6j':'同じ著者が正規化内容ek6gを同じ第十節の議論で実際に仮定として採用する行為内容。引用内の物理的存在を現実化しない。',
 'ek6k':'一般性保存ek6eの主張、同じ採用行為ek6jの正当な許容と採用、同じ電子の指定瞬間での考察eisnx、その根拠としての一般性、直前の探究への照応と表記を結ぶ。',
 'ek6l':'第一文の許容と採用を述べる断定的メッセージ。粒子を実験で移動させる命令へ替えない。',
 'ek6m':'第一文を同じ著者・論説へ帰属し、直前の初期運動法則の探究に続ける主張417。',
 'ek6n':'同じ正規化設定ek6fを、選んだ一つのk・四原点ずれ・局所新履歴とek5wで結ぶ。光速度は既存tc、並進速度は既存eisxt。新系の静止は前提にしない。',
 'ek6o':'ek6nと同じ引数と選んだk・ずれ・新履歴に対して、同じ出来事での実際の三微分零ek5xを述べる帰結。',
 'ek6p':'同じ指定出来事に対してek6nの設定が一つあるという内容。選んだkの帰結を空の前提から済ませず、静止自体を存在の前提にしない。',
 'ek6q':'同じ共有設定のek6nからek6oへの全称条件付き内容。前提と帰結で設定・出来事・k・光速度・原点ずれ・新履歴を変えない。',
 'ek6r':'選んだ共動設定の存在ek6pと、その同じ設定での瞬間静止ek6qを合わせた第二文の物理的内容。',
 'ek6s':'著者が同じek6rを述べて明白として提示し、第一文の採用を受け、括弧t=0とkの表記を結ぶ。物理的な真理や導出の機械的証明を主張しない。',
 'ek6t':'同じ設定のKの時刻成分が有効な零であるという等式。空間原点やkの時刻零とは別の射影。',
 'ek6u':'同じ共動設定ek6nで、第一文と同じ指定出来事のK時刻が零という括弧補足の閉じた内容。',
 'ek6v':'瞬間静止の帰結と明白さ・照応・括弧・表記の提示を伝える断定的メッセージ。',
 'ek6w':'第二文を同じ著者・論説へ帰属し、第一文に続ける主張418。',
}
LIMITS=[
 'u0245全二文とM0399–M0405を対象とする。原刊917頁末Koordinaten-と918頁冒頭sprungを保持し、後続の原点指定を参照して座標原点と読む。固定原文を修正しない。',
 'können und wollen wir annehmenは、一般性を保つため正当に採れる仮定を今採用するという論述上の決定と読む。許容eism4と採用ugを分け、単なる願望、実験の実施、引用内の物理的存在の現実化にはしない。ins Auge fassenは同じ電子を指定瞬間について考察することであり、視覚的観測の実施を補わない。',
 '一般性は全物理設定の代表配置と同じ物理的法則の答え候補の保存ek6eとして明示する。正X方向への回転とKの時空原点の選び直しであり、法則の成分式の字面の一致ではない。既存のKを代表配置の記述として用いる。全回転の存在や物理的真理を機械的に証明したとはしない。',
 '同じ電子eisxh、指定出来事eisxv、瞬間速さeisxtを両文で保持する。第一文の正規化には光速上限を要求しない。第二文の共動系は既存の正の光速度tcと0≤v<tcでの局所的な適用として読む。零速度の退化例を許す。',
 'kとその四原点ずれ・新時間域・新曲線は一つの選択への参照として後続にも保つ。ek6pで実際の完全な両履歴への対応を要求し、ek6qはその同じ配置での実際の三微分零を帰結にする。新履歴や静止を前提の中に隠さない。任意の関数を対応する履歴と認定しない。',
 't=0はKでの同じ指定瞬間。kの時間原点・空間原点を零へ固定せず、その指定はu0248で追加する。電子の前後の静止、加速度零、全区間の等速、無放射、有限時間の運動の解を補わない。一定速度は座標系の並進へ掛かる。',
 'Xの二出現は同じKの第一空間軸、vの二出現はu0244の同じ瞬間速さ、Kはra、kは今回選ぶeisxyへ結ぶ。以前の別のkや系間速度を同名によって代用しない。',
 'einleuchtendは同じ帰結内容への著者の明白さの提示zdgであり、真理判定や自動証明ではない。二文の本文順序・引用・照応・理由・括弧補足を合成する。新規原始記号は参照と表記のみで、仮定・考察・一般性・物理的帰結を一つの原始述語へ押し込めない。',
]

BOUND=[(('location' if n=='point' else n),t) for n,t in CASES if n!='event']
def shared():return args(SETTING,frame=k('ra'),context=v('point'),electricconversion=ONE,point=v('location'),event=k('eisxv'))
def moving():return [*args(SETTING),k('eisxy'),k('tc'),k('eisxz'),k('eisx2'),k('eisx3')]

def definitions():
    text=''.join('r '+n+'[] '+t+'.\n' for n,(t,_) in REFERENCES.items())
    text+=define('ek6f',SETTING,both(k('ek56',*args(SETTING)),op('e',v('frame'),k('ra')),op('e',v('event'),k('eisxv'))))
    text+=content('ek6g',quantified('g',BOUND,k('ek6f',*shared())))
    text+=define('ek6h',SETTING,coord(v('point'),ROLES[3]),R)
    p=v('point');who=k('rd');paper=k('eirf');scope=k('eisxg');first=k('eisxw');second=k('eisxx')
    text+=content('ek6i',both(*(k('eisd4',first,who,k(sign),k(target),paper,p) for sign,target in [('eisx5','yn'),('eisnb','ra')]),k('eiswy',k('eisxu'),'r[p ek6f]','r[p ek4r]',paper,scope,p),k('eiswy',k('eism5'),'r[p ek6f]','r[p ek6h]',paper,scope,p)))
    text+=content('ek6j',k('ug',first,who,quote('ek6g'),scope,p))
    text+=content('ek6k',both(k('uh',first,who,quote('ek6e'),scope,p),k('eism4',who,quote('ek6j'),scope,paper,p),op('t',k('ek6j'),p),k('eisnx',first,who,k('eisxh'),quote('ek6g'),scope,p),k('zct',first,who,quote('ek6e'),first,scope,p),k('eisra',first,who,paper,k('eisxs'),quote('ek4y'),quote('ek6g'),scope,p),op('t',k('ek6i'),p)))
    text+='d ek6l[] f[j s[k ek6k[]]].\n'
    text+=define('ek6m',[],both(k('eir3',first,who,paper,quote('ek6l'),k('ri')),k('ue',k('eisxs'),first,k('ri')),op('u',op('e',k('eisxs'),first))))
    text+=define('ek6n',SETTING,both(k('ek6f',*args(SETTING)),k('ek5w',*moving())))
    text+=define('ek6o',SETTING,k('ek5x',*moving()))
    text+=content('ek6p',quantified('g',BOUND,k('ek6n',*shared())))
    text+=content('ek6q',quantified('f',BOUND,op('y',k('ek6n',*shared()),k('ek6o',*shared()))))
    text+=content('ek6r',both(op('t',k('ek6p'),p),op('t',k('ek6q'),p)))
    text+=define('ek6t',SETTING,k('sca',k('ek6h',*args(SETTING)),ZERO))
    text+=content('ek6u',quantified('f',BOUND,op('y',k('ek6n',*shared()),k('ek6t',*shared()))))
    text+=content('ek6s',both(k('uh',second,who,quote('ek6r'),scope,p),k('zdg',second,who,quote('ek6r'),scope,p),k('eisra',second,who,paper,first,quote('ek6k'),quote('ek6r'),scope,p),k('eisa5',second,who,quote('ek6r'),quote('ek6u'),p),k('eisd4',second,who,k('eisx4'),k('eisxy'),paper,p)))
    text+='d ek6v[] f[j s[k ek6s[]]].\n'
    text+=define('ek6w',[],both(k('eir3',second,who,paper,quote('ek6v'),k('ri')),k('ue',first,second,k('ri')),op('u',op('e',first,second))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==417
    assert not(set(MEANINGS)|set(REFERENCES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ek6m','ek6w')]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=REFERENCES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='electron_normalization_choice_and_same_event_comoving_claim',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/electron-representative-scope-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    ann['entries'] += [dict(symbol=n,role='designation',forms=[dict(text=s,language='de',role='printed_identifying_form')]) for n,s in [('eisx4','k'),('eisx5','X')]]
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
