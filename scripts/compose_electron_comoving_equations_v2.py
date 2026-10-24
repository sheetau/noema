"""Correct the small-t reading while preserving the previous evidence version."""
from scripts import compose_electron_comoving_equations as previous
from scripts.compose_electron_comoving_equations import *

FULL='examples/v014/einstein-electron-comoving-equations-v2.noema'
CORE='examples/v014/electron-comoving-equations-v2-core.noema'
BASIS='data/electron-comoving-equations-basis-v2.json'
ANNOTATIONS='data/electron-comoving-equations-identifiers-v2.json'
REFERENCES=previous.REFERENCES|{
 'eisx6':'u0248–u0249の同じ共動系kの座標時刻τの表記。原刊のM0409の記号一覧にτがあり、電子テキストはこれを落としている。u0246の括弧M0406は原刊もtであり、このτ表記をその箇所へ同一視しない。',
}
MEANINGS=previous.MEANINGS|{
 'ek74':'同じKの時間域・三速度関数・指定点の座標時刻tに、右側初期微分ek32と初期一次式の剰余o(Δt)を要求する。原刊の小さいtという限定を旧系の実際の履歴へ結ぶ。共動系の時刻τで置き換えず、有限区間の厳密な等加速を追加しない。',
 'ek7c':'同じkの実二階微分と実電場に三式μa=εEを課し、同じkの三速度の右微分ek32と初期一次式の剰余o(Δτ)を合わせる。さらに同じKの初期変化ek74を保つ。原文の小さいtとkの微分変数τを分け、両履歴の同じ出来事対応をek63から共有する。',
}
LIMITS=list(previous.LIMITS)
LIMITS[0]='u0246–u0249を原刊918頁の一続きとして再読した。M0406は原刊も電子テキストもtである。v1の「原刊τ」という照合判断を撤回し、旧版は履歴として保存する。M0409は原刊にξ,η,ζ,τ,X′,Y′,Z′があり、電子テキストのτ脱落という照合判断は維持する。'
LIMITS[1]='直後・小さいtは、指定した同じ出来事からKの正の時間差で近づく初期運動として読む。同じKの速度の剰余o(Δt)と右微分を明示し、同じkでは座標時刻τによる初期剰余o(Δτ)と運動三式を要求する。ek63の両履歴の全域対応と正の時刻変化率を共有し、tとτを同じ座標変数とはしない。有限区間の厳密式、最小時間粒、全区間の静止又は一定加速度へ拡張しない。'
LIMITS[4]='u0248で同じkの四原点ずれを零にする。Kのt=0はu0245ですでに固定され、u0246の小tはそのKの時刻を指す。共動系τの原点指定は後続の明示選択と一群で解釈する。旧u0245の自由な原点ずれは変更しない。'
LIMITS.append('v1の読解・規約・本文・検査・判断を改変せず、u0245までの親から訂正版を作る。u0246–u0249は新しい依存内容と訂正された規約で再判断する。旧版のテスト成功は原刊の文字の正しさを証明しなかった。')

def definitions():
    text=previous.definitions()
    tau=coord(new_values()['point'],ROLES[3]);nv=new_values()
    old=define('ek7c',PAIR,both(k('ek3t',*new_args(VECTOR)),k('ek32',*new_args(FUTURE)),*(k('ek7b',nv['domain'],nv[n],tau,nv[a]) for (n,t),(a,s) in zip(PROFILES,ACCEL))))
    moment=coord(v('point'),ROLES[3])
    initial=define('ek74',SETTING,both(k('ek32',*args(FUTURE)),*(k('ek7b',v('domain'),v(n),moment,v(a)) for (n,t),(a,s) in zip(PROFILES,ACCEL))))
    corrected=define('ek7c',PAIR,both(k('ek3t',*new_args(VECTOR)),k('ek32',*new_args(FUTURE)),*(k('ek7b',nv['domain'],nv[n],tau,nv[a]) for (n,t),(a,s) in zip(PROFILES,ACCEL)),k('ek74',*args(SETTING))))
    assert text.count(old)==1
    return text.replace(old,initial+corrected)

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==419
    assert not(set(MEANINGS)|set(REFERENCES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ek7q','ek7x')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='corrected_original_small_t_and_comoving_initial_equations',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    annotations=json.loads(read(previous.ANNOTATIONS));annotations.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
