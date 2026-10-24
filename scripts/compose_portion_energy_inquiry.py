"""Ask for the mean energy of the same enclosed portion in the moving frame."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_mean_light_energy import ROOT,read,TOTAL,BASE,VOLUMES,FRAME,OLD,GEOMETRY
from scripts.compose_moving_ball_transport import FRAME as TRANSPORT_FRAME
from scripts.compose_wave_transform_application import transformed
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-same-light-portion.noema';PARENT_BASIS='data/same-light-portion-basis-v1.json'
FULL='examples/v014/einstein-portion-energy-inquiry.noema';CORE='examples/v014/portion-energy-inquiry-core.noema'
BASIS='data/portion-energy-inquiry-basis-v1.json';ANNOTATIONS='data/portion-energy-inquiry-identifiers-v1.json';INDEX=389
SETTING=[(n,t) for n,t in TOTAL if n not in ('energy','newenergy')]
ANSWER=SETTING+[('value',R)]
code=lambda result:'i[h['+' '.join(t for n,t in SETTING)+'] '+result+']'
PRIMITIVES={
 'eists':([('node','a'),('author','a'),('anchor','a'),('prior','i[e]'),('condition',code('c')),('question',code('g['+R+']')),('scope','a'),('context','d')], 'authorがscopeのanchorから受けるpriorの議論を引き継ぎ、nodeでconditionの下にquestionを問うという論述上の提示。二つの閉じた規則は同じ型と順序の設定引数を取り、一つの割当を候補の外側で固定して共有する。条件が実際に真だとの断言、答えの存在・一意性・既知性・測定済み、引用の自動評価を含意しない。具体的な対象、物理条件、候補の意味は引用規則で合成する。この68役割の型を持つ実数質問族への一般提示関係であり、光やエネルギーを語義に含めない。'),
 'eistt':([], '固定原文einstein-1905:u0205[108,272)のWir fragenからd.h.を経る一文の箇所。質問とその言換えの具体的内容は別に合成する。'),
}
MEANINGS={
 'ekn6':'同じ68役割で、校正された波・二系の位相平均密度・同じ光の部分の領域と両同時体積・各時刻零での全点位相平均を保持する。ekmiの二つの総エネルギー積分だけを除いた設定であり、未知の新総量も旧総量も引数又は存在証人にしない。',
 'ekn7':'ekn6へ、K=ra、V=tc、波の範囲eisrx、部分zvaa、正の旧振幅と、同じK側の全時刻の初期部分輸送eknwを結ぶ質問族の条件。球面とその内部が前文の同じ部分であることを保つ。体積同値や総量比を前提にしない。',
 'ekoa':'同じ設定ekn7の新系kの時刻零断面について、半径R、pi、Lorentz因子D、位相平均密度A′²/(8pi)、新系体積を固定してekmgの重み付き空間積分を候補valueへ結ぶ。候補の外側にnewenergyという既知値を置かず、候補ごとに対象や単位を選び直さない。',
 'ekob':'同じ68設定を閉じ込めたekoaの実数値質問。新系でこの球面が囲む平均エネルギーを求める。質問の構成だけでは候補の全探索、解の存在・一意性・既知性を主張しない。',
 'ekoc':'同じ68設定の同じ質問ekobを、球面が囲む同じ光の部分の新系に相対的な平均エネルギーの問いとして参照する。ekn6の物理的な部分割当が同じ領域と密度を結ぶため、別の量又は第二の独立な答えを作らない。',
 'ekod':'前の持続する同じ部分の説明eknzを受け、同じ条件ekn7と球面内のエネルギー質問ekobの族を、著者が第八節で問う提示。許容設定を候補の内側で存在選択しない。',
 'ekoe':'同じ条件・同じ箇所・同じ著者の問いを、同じ光の部分に相対的なエネルギー質問ekocという言い方で記述した内容。別の実施済み質問行為を要求せず、d.h.が参照する説明内容として使う。',
 'ekof':'ekodの質問提示に、eismeによるekodからekoeへのすなわちの説明と、前の同じ球面・初期部分へのeisraの照応を結ぶ。質問の対象の言換えを答えの断言へ変えない。',
 'ekog':'同じ新系エネルギーの質問提示とその言換えekofを述べるメッセージ。',
 'ekoh':'u0205第二文を同じ著者・論説へ帰属し、前の持続的な囲い込みの文に続ける。',
}
LIMITS=[
 '原刊913頁のu0205[108,272)を通読する。Wir fragenの一人称複数は論述主体の著者rdとして読む。M0356とM0357はともに既出の動く系k=zbmであり、先行K又は球面自体の静止系ではない。',
 '同じ部分の連続体輸送と全時刻モデルは先行の明示した読みを保つ。求める総量は、先行A²/(8pi)と同じ位相平均密度を新系の同時断面で積分した平均エネルギーとして読む。有限球の瞬間的なエネルギーとの無説明な同一視はしない。',
 '時刻は後続本文のτ=0に合わせて選ぶ。Kのt=0とkのτ=0を同じ出来事集合にせず、同じ全領域履歴を逆Lorentz写像してからkの同時断面を取る。後続の楕円体・体積・総量比を著者が既に証明したとする提示は追加しない。',
 'ekn6は既存ekmiの総量を含まない物理設定を分離したもの。旧新総量の存在量化を条件に入れず、newenergyとの等値で答えを定義しない。二体積は記号的な設定値であり数値的に既知とは要求しない。候補を変えても対象・系・波・単位・体積・位相平均を固定する。',
 'd.h.は同じ対象の同じエネルギーを求める二つの言い方の説明である。後半の別名ekocは同じekobを呼ぶが、二つの閉じた記述の提示役割はeismeへ別に渡す。これは二つの無関係な質問、追加の答え、実験実施又は全場面の言語的同義性の主張ではない。',
 '既存eisseは二場を答える41設定、eiss4は振幅を答える61設定、zihは閉じた単一の数値質問に型付けされている。異型の無理な接続や物理役割の省略をせず、同じ一般的な条件付き質問提示を68設定の型eistsへ特殊化する。文の意味を一原始関係へ収納せず、条件・候補・同じ部分・言換え・帰属を別に合成する。',
 '質問提示と候補成立、答えの存在・一意性・既知性は別である。引用された全実数・全関数の物理条件を提示の検査で実行しない。有限の対照と保存済み下位証拠は物理的な全域存在や意味同義性の自動証明ではない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');V=v('light');speed=v('speed')
    newamps,_,_,phase=transformed(speed)
    oldphase=k('ekbf',V,v('rate'),v('ax'),v('ay'),v('az'))
    oldregion=k('ekau',v('space'),v('lower'),v('upper'));newregion=k('eken',speed,v('space'),v('lower'),v('upper'),V)
    pair={n:v(n) for n,t in SETTING}|dict(newframe=k('zbm'),scope=k('eistk'))
    conditions=[k('eklp',*args(BASE)),k('eklg',*args(BASE)),k('eklh',*args(BASE)),k('ekl4',*[pair[n] for n,t in VOLUMES])]
    rows=[(v('frame'),oldphase,[v(n) for n in ('ex','ey','ez','hx','hy','hz')],oldregion,k('eklw',*args(OLD)),v('amplitude')),(k('zbm'),phase,newamps,newregion,k('eklx',*args(GEOMETRY)),v('newamplitude'))]
    for frame,p,coefficients,region,portionregion,amp in rows:
        overrides=dict(frame=frame,phase=p,region=region,portionregion=portionregion,scope=k('eistk'),time=zero,density=k('ekle',v('pi'),amp),**dict(zip(('ex','ey','ez','hx','hy','hz'),coefficients)))
        conditions.append(k('ekme',*[overrides.get(n,v(n)) for n,t in FRAME]))
    text+=define('ekn6',SETTING,both(*conditions))
    fixed=[op('e',v(n),k(symbol)) for n,symbol in [('frame','ra'),('scope','eisrx'),('portion','zvaa')]]
    text+=define('ekn7',SETTING,both(*fixed,k('sca',V,k('tc')),k('ekn6',*args(SETTING)),k('ba',v('amplitude')),k('bg',zero,v('amplitude')),k('eknw',*[pair[n] for n,t in TRANSPORT_FRAME])))
    D=k('sdn2',V,speed,one,v('ax'));rho=k('ekle',v('pi'),v('newamplitude'))
    text+=define('ekoa',ANSWER,both(k('ekn7',*args(SETTING)),k('ekmg',v('radius'),v('pi'),D,rho,v('value'),v('newvolume'))))
    text+=define('ekob',SETTING,'j v[i[value '+R+']['+k('ekoa',*args(SETTING),v('value'))+']]', 'g['+R+']')
    text+=define('ekoc',SETTING,k('ekob',*args(SETTING)),'g['+R+']')
    p=v('point');author=k('rd');node=k('eistt');scope=k('eistk')
    for name,question in [('ekod','ekob'),('ekoe','ekoc')]:
        text+=content(name,k('eists',node,author,k('eistq'),quote('eknz'),'r[p ekn7]','r[p '+question+']',scope,p))
    text+=content('ekof',both(evaluate('ekod'),k('eisme',node,author,quote('ekod'),quote('ekoe'),k('eirf'),p),k('eisra',node,author,k('eirf'),k('eistq'),quote('eknz'),quote('ekod'),scope,p)))
    text+='d ekog[] f[j s[k ekof[]]].\n'
    text+=define('ekoh',[],both(k('eir3',node,author,k('eirf'),quote('ekog'),k('ri')),k('ue',k('eistr'),node,k('ri')),op('u',op('e',k('eistr'),node))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekoh',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_portion_moving_frame_mean_energy_question_and_gloss',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/same-light-portion-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
