"""Ask about the same hypothesized wave from the moving observer's frame."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_wave_observer_question import ROOT,read,QUESTION,INVESTIGATION,OBSERVER,LOCATION,TRACE,ANSWERS,CALIBRATION,FIELD,REGION
from scripts.compose_distant_wave_source import SETTING,SPACE
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,F,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-wave-observer-question.noema';PARENT_BASIS='data/wave-observer-question-basis-v1.json'
FULL='examples/v014/einstein-wave-inquiry.noema';CORE='examples/v014/wave-inquiry-core.noema'
BASIS='data/wave-inquiry-basis-v1.json';ANNOTATIONS='data/wave-inquiry-identifiers-v1.json';INDEX=366
EXTRA=[('observer','a'),('obslower',R),('obsupper',R)]+[(n,F) for n in ('obsx','obsy','obsz')]
FAMILY=SETTING+EXTRA
REGION_INPUT=[('space',SPACE),('lower',R),('upper',R),('light',R)]
PAIR='g['+FIELD+' '+FIELD+']'
code=lambda result:'i[h['+' '.join(t for n,t in FAMILY)+'] '+result+']'
PRIMITIVES={
 'eisse':([('node','a'),('author','a'),('anchor','a'),('prior','i[e]'),('condition',code('c')),('question',code(PAIR)),('scope','a'),('context','d')],'authorがscopeのanchorで導入したpriorの仮定を引き継ぎ、nodeで、conditionの下でquestionを問うという質問の提示行為。conditionとquestionは同じ順序・型の引数列を取る閉じた規則であり、一つの許容割当を両規則に共有してから答え候補を変える。先行内容の存在証人を別々の候補に対して選び直さず、condition内で引き継ぐ先行本体の引数と同じ対象を保つ。条件の追加の役割もその同じ割当内で固定する。これは二関数を答えとする条件付き質問族への型付きの一般提示関係であり、具体的な対象・条件・候補の性質は引用された規則で別に合成する。質問を単に紹介する関係、答えの主張、質問の存在だけ、意図だけではない。仮定が現実に成立すること、調査の実施済み、答えの存在・一意性・既知性、引用の自動評価を要求しない。'),
 'eissf':([], '固定原文einstein-1905:u0182のWir fragenからuntersucht werden.までの第一文の箇所。波の性質を移動系の静止観測者の条件で問う役割は別の構成へ接続する。'),
}
MEANINGS={
 'ekca':'同じ静止観測者ekbuについて、閉区間関係lgへ下端・上端・時刻の順に渡し、その全有効時刻で代表位置が指定領域に入るekbvを要求する。旧ekbwの呼出順の誤りを修正した構成であり、旧式は保存するがこの本文では依存しない。',
 'ekcb':'正しい全区間条件ekcaと、同じ波・過程・系・領域を調べるeissdを結ぶ。観測者と調査対象を別々の割当へ分離しない。',
 'ekcc':'正しい調査条件ekcbを保ち、同じ単位・換算で校正された二場ejsnと同じ過程の場の帰属eispnを答え候補へ要求する。',
 'ekcd':'同じ固定引数の下でekccを満たす二場の関数対を答えとする質問。旧ekbzの内部にある区間呼出の誤りを継承せず、対象の固定と未知入力の拒否を保持する。',
 'ekb2':'旧Kの局所空間集合と有限期間の積ekauを、同じVと既出の相対速度vによる最終Lorentz逆座標変換s6mの逆像として新kの領域へ移す。新旧の数値を同じ座標とせず、新系で同じ矩形時間区間へ置換しない。',
 'ekb3':'先行の波・源・二場・近似・振幅と法線の設定ekblの全35引数をそのまま保持し、K=ra、第七節、既出V、同じ長さ時間単位ta/rbを固定する。同じ二系の実物を含む定速運動eivzと光速未満条件、kに静止して同じ波を調べるekcbを、変換後領域と一つの追加観測者設定へ結ぶ。',
 'ekb4':'ekb3と同じ41引数の割当から、kでの同じ波・過程の電場と磁場を求めるekcdの質問を作る。二場の単位と電荷・力単位を先行から共有し、換算係数1及び1/Vを保つ。仮定の35役割は候補ごとの存在選択の内側へ移さない。',
 'ekb5':'著者が先行ekbnの仮定を保持して、同じ割当の条件ekb3に対応する質問ekb4を実際に提示する。Wirは論述主体の一人称複数として著者rdへ帰属し、共同著者や読者全員の行為を補わない。',
 'ekb6':'同じ仮定の下で波の性質を問う著者の提示ekb5を述べるメッセージ。内容が質問提示の帰属であることと、物理的な答えの主張であることを区別する。',
 'ekb7':'u0182第一文の質問提示を同じ著者・論説へ接続し、直前の振幅・法線の説明に続く別の箇所とする。',
}
LIMITS=[
 '旧ekbwはlg(time,lower,upper)としていたが、既存lgの契約はlg(lower,upper,time)である。旧の診断も同じ誤順をモデル化して見逃していた。ekca–ekcdで修正し、実際のlg本体の点ごとの診断を追加する。旧証拠・旧式は履歴として保持し、今回の文の依存から除外する。前回は原文判断を追加していないため既存の全文判断にはこの旧式への依存がない。',
 '固定u0182[0,144)の第一文118非空白本文文字とM0324=kを扱う。原刊910頁末から911頁冒頭へ続く一文であり、頁境界注記A0025を本文条件にしない。後半の二種類の変換適用と直ちに得る提示は別に残るため、u0182全単位を完成扱いしない。',
 'dieser Wellenとdieselbenは同じ先行の源・過程・波・近似設定を受ける。先行ekbnの31存在証人に対応する35設定役割をconditionとquestionに共有し、追加の一観測者・調査区間・位置関数も答え候補の外側で固定する。別の候補ごとに異なる波を選べる問いにはしない。',
 '動く系は既出k=zbm、旧系はK=ra、速度はzb7、光速度はtc。第三節で使う同じ長さ時間単位ta/rbにそろえて表す。これは計算と座標の単位選択であり、特定の数値速度や源の静止を追加しない。運動はeivzの実物と全履歴を受け、単に異なる二名称があることを移動としない。',
 '観測者はkの代表位置が正の調査区間にわたり静止し、その区間の全位置が同じ変換領域に入るという局所理想化を使う。身体内部の停止、全時間での領域内滞在、実際に測定を終えた記録を追加しない。',
 'Beschaffenheitは同じ波の物理的な電場と磁場の時空記述を求める問いとして読む。二場の校正と同じ過程への帰属を保持し、領域外の関数延長の違いは問う性質としない。先行の近似表現と実際の場を同一視せず、後続のsin表示を答えへ結ぶ際には誤差と十分性を維持する。',
 'eisseは既存の数値質問の提示と同じ発話上の区別を、条件と質問が同じ型の引数列を共有する質問族へ拡張した型付きの一般関係である。物理的な源・運動・静止・候補場を原始関係へ圧縮せず、ekb3/ekb4に分けて合成する。引用は閉じた二規則と先行内容だけであり、自由変数を含む質問を引用しない。',
 'この文の記述は著者による質問の提示であり、仮定の現実成立・解の存在・一意性・答えを既に知っていること・同じ波の場の変換則の証明を断言しない。数学的な逆像の構成を実際の全出来事の測定済みとしない。後半では両変換則の物理的適用を別に接続する。',
]

def replacements():
    one=k('bb','n p b b')
    return {'frame':k('zbm'),'lower':v('obslower'),'upper':v('obsupper'),'x':v('obsx'),'y':v('obsy'),'z':v('obsz'),'region':k('ekb2',*args(REGION_INPUT)),'electricconversion':one,'magneticconversion':k('sjd',v('light'))}

def query_args(fields=QUESTION):
    selected=replacements();return [selected.get(n,v(n)) for n,t in fields]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    inside=both(k('ba',v('time')),k('lg',v('lower'),v('upper'),v('time')))
    text+=define('ekca',LOCATION,both(k('ekbu',*args(OBSERVER)),q('f','time',R,op('y',inside,k('ekbv',*args(TRACE))))))
    text+=define('ekcb',INVESTIGATION,both(k('ekca',*args(LOCATION)),k('eissd',*[v(n) for n in ('observer','wave','process','frame','region','context')])))
    text+=define('ekcc',QUESTION+ANSWERS,both(k('ekcb',*args(INVESTIGATION)),k('ejsn',*args(CALIBRATION)),k('eispn',*[v(n) for n in ('process','frame','electricfield','magneticfield','region','context')])))
    text+=define('ekcd',QUESTION,'j v[i['+' '.join(n+' '+t for n,t in ANSWERS)+']['+k('ekcc',*args(QUESTION+ANSWERS))+']]',PAIR)
    text+=define('ekb2',REGION_INPUT,k('s6m',v('light'),k('zb7'),k('ekau',v('space'),v('lower'),v('upper'))),REGION)
    fixed=[op('e',v(n),k(ref)) for n,ref in [('frame','ra'),('lengthunit','ta'),('timeunit','rb'),('scope','eisrx')]]
    text+=define('ekb3',FAMILY,both(*fixed,k('sca',v('light'),k('tc')),k('ekbl',*args(SETTING)),k('eivz',v('context')),k('s45',v('light'),k('zb7')),k('ekcb',*query_args(INVESTIGATION))))
    text+=define('ekb4',FAMILY,k('ekcd',*query_args()),PAIR)
    text+=content('ekb5',k('eisse',k('eissf'),k('rd'),k('eissc'),quote('ekbn'),'r[p ekb3]','r[p ekb4]',k('eisrx'),v('point')))
    text+='d ekb6[] f[j s[k ekb5[]]].\n'
    text+=define('ekb7',[],both(k('eir3',k('eissf'),k('rd'),k('eirf'),quote('ekb6'),k('ri')),k('ue',k('eissc'),k('eissf'),k('ri')),op('u',op('e',k('eissc'),k('eissf')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekb7',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_hypothesized_wave_question_in_moving_frame',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/wave-observer-question-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
