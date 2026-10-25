"""Bind an alternative acceleration definition to the same comoving history."""
from scripts.compose_electron_directional_masses import *

PARENT='examples/v014/einstein-electron-directional-masses.noema'
PARENT_BASIS='data/electron-directional-masses-basis-v1.json'
FULL='examples/v014/einstein-electron-alternative-conventions.noema'
CORE='examples/v014/electron-alternative-conventions-core.noema'
BASIS='data/electron-alternative-conventions-basis-v1.json'
ANNOTATIONS='data/electron-alternative-conventions-identifiers-v1.json'
ALT=CONVENTION+[('alternative','d')]
MASS_PAIR=[('mass',R)]+COEFFICIENTS
SIX=[(n,R) for n in ('ax','ay','az','fx','fy','fz')]
CHANGE=[(n,R) for n in ('oldlongitudinal','oldtransverse','forceparallel','forcetransverse','accelerationparallel','accelerationtransverse','longitudinal','transverse')]
OLD=[('oldlongitudinal',R),('oldtransverse',R)]
COMPARISON=ALT+OLD+COEFFICIENTS
MEANINGS={
 'end':'同じμと二候補係数について、全ての有効な実数の三加速度・三力で、等方的なμa=fの三式と候補の縦横係数による三式が同値であるという係数同定。現在の零加速度の一例から係数を決めない。',
 'ene':'有効なμ、縦候補、横候補について両候補が同じμに等しいという明示形。物理的質量の正値性は適用設定に置く。',
 'enf':'二方向群の力・加速度の数値の定義を、それぞれ正の一定倍率で変えたときの係数対応。新縦×加速度縦倍率=旧縦×力縦倍率、新横×加速度横倍率=旧横×力横倍率。純粋な数値関係であり、倍率を単位尺度又は実際の物理的定義と自動同一視しない。',
 'eng':'元の物理設定とkの力/Kの加速度のemcを保持し、指定したalternativeで同じ対象・出来事・力単位・加速度単位についてkの力/kの加速度という規約を選ぶ。変更されるのは加速度を定義する系で、元の実軌道や力を別物へ変えない。',
 'enh':'同じengの変更規約で、実際のkの三加速度newax/neway/newazと同じkのforceに候補係数を適用する。さらに等方的な応答に関する全六実数の同定endを保持する。',
 'eni':'enhと同じ物理設定・実k加速度・力に、候補の二係数がμ,μであるeneを結ぶ明示形。単なる任意の二数値への代入ではない。',
 'enj':'同じengの条件の下で、全成分関係による候補enhと、μ,μの明示形eniが同値であるという内容。全実数の同値性を有限検査が証明したとはしない。',
 'enk':'同じ元の測定規約emc、両履歴の実加速度変換ek75と同じkの初期運動式ek7cを合わせる。既存の小tとτの初期変化を保持し、変換や力学式を単位の定義に埋め込まない。',
 'enl':'同じenkの物理法則・変換とengの変更規約の下で、変更後の実三成分がμ,μのeniを満たすという条件文。変更規約や運動法則の成立を無条件に主張しない。',
 'enm':'元の同じ設定でのemfの二係数と、変更規約でのeniの二係数を一つの比較へ束縛し、力の倍率1,1、加速度の倍率β³,β²というenfを結ぶ。係数、系、実加速度を別々の証人に分けない。',
 'enn':'二組の有効な係数について、縦又は横の少なくとも一方の値が異なること。全方向の差や、単なる名称の差を要求しない。',
 'eno':'同じ物理的な変更規約の比較enmと、係数の数値差ennを結ぶ。v=0の退化例では成立しない。u0259の全ての別定義に対する主張ではなく、同じ電子を用いて定義依存を構成するための具体的な接続である。',
}
LIMITS=[
 'u0259を完成させるため、別の定義を同じ実際の物理設定へ結ぶ依存群を追加する。旧426主張・261全単位判断を維持し、新しい著者主張と全文判断は追加しない。原文がこの具体的な別規約を指定したとはしない。',
 '変更例は、力を同じ瞬間共動系kのεE′に保ち、加速度をKのd²x/dt²等から同じkのd²ξ/dτ²等へ替える規約である。原刊の量の定義を補うための明示例で、現在の主張を現代の別質量へ訂正するものではない。',
 '量の単位と尺度、同じ物体・出来事・低速質量・電荷・同じ力の記録は元のemcから共有する。新しい加速度は先行PAIRの独立した実履歴の微分であり、所望の質量を得るために定義した数値ではない。',
 'alternativeは規約を採る仮定的な比較文脈である。新しい物理的な軌道をその文脈に丸ごと複製せず、比較する同じ元の物理値へ別の数値定義を適用する。実際の規約変更や測定の実施を要求しない。',
 '正のμと0<v<Vでは元のμβ³,μβ²と変更後のμ,μが異なる。v=0では一致する。二つの数値評価を同じ比率で変えると係数が保たれる場合もあるので、あらゆる別定義が必ず異なる質量を与えるとは強めない。enfの任意倍率は数値診断であり、各倍率を物理的に実現した別定義として認定しない。',
 '係数は全成分関係によって同定し、零加速度の一例に依存しない。全六実数の同値性の数学的読解と、登録した有理関数履歴・完全平方の有理値・二値束縛診断を区別する。未知の入力と全実数域の有限認定は拒否する。',
 '全文統合では、関連する別定義の仮定的な比較範囲を結果に依存せず明示し、現在の電子と縦横質量へ接続する必要がある。この変更例だけを原文の一般的な条件文へ置き換えない。Natürlich、電子運動の理論の範囲、非常に慎重に比較すべき要求と推論帰属は未統合である。旧seqg/seqh、seqk–seqoの比較・要求を再利用し、入力の意味と作用範囲を解決してからu0259を判断する。',
]

def definitions():
    base=k('seph',v('mass'),v('mass'),*args(SIX));candidate=k('seph',*args(COEFFICIENTS),*args(SIX))
    text=define('end',MASS_PAIR,both(*(k('ba',x) for x in args(MASS_PAIR)),quantified('f',SIX,op('y',both(*(k('ba',x) for x in args(SIX))),op('z',base,candidate)))))
    text+=define('ene',MASS_PAIR,both(*(k('ba',x) for x in args(MASS_PAIR)),*(k('sca',v(n),v('mass')) for n,t in COEFFICIENTS)))
    text+=define('enf',CHANGE,both(*(k('ba',x) for x in args(CHANGE)),*(k('bg',ZERO,v(n)) for n in ('forceparallel','forcetransverse','accelerationparallel','accelerationtransverse')),k('sca',k('shv',v('longitudinal'),v('accelerationparallel')),k('shv',v('oldlongitudinal'),v('forceparallel'))),k('sca',k('shv',v('transverse'),v('accelerationtransverse')),k('shv',v('oldtransverse'),v('forcetransverse')))))
    text+=define('eng',ALT,both(k('emc',*args(CONVENTION)),k('zraconvention',v('matter'),k('eisxy'),k('eisxy'),v('event'),v('forceunit'),v('accelerationunit'),v('alternative'))))
    actual=k('seph',*args(COEFFICIENTS),*[v('new'+n) for n,t in ACCEL],*[app(v('force'),k(axis)) for axis in ROLES[:3]])
    for name,identity in [('enh','end'),('eni','ene')]:text+=define(name,ALT+COEFFICIENTS,both(k('eng',*args(ALT)),actual,k(identity,*args(MASS_PAIR))))
    text+=define('enj',ALT+COEFFICIENTS,op('y',k('eng',*args(ALT)),op('z',k('enh',*args(ALT+COEFFICIENTS)),k('eni',*args(ALT+COEFFICIENTS)))))
    text+=define('enk',CONVENTION,both(k('emc',*args(CONVENTION)),k('ek75',*args(PAIR)),k('ek7c',*args(PAIR))))
    text+=define('enl',ALT,op('y',both(k('enk',*args(CONVENTION)),k('eng',*args(ALT))),k('eni',*args(ALT),v('mass'),v('mass'))))
    beta=k('soy',k('tc'),k('eisxt'));square=k('shv',beta,beta);cube=k('shv',square,beta)
    text+=define('enm',COMPARISON,both(k('eng',*args(ALT)),k('emf',*args(CONVENTION),*args(OLD)),k('eni',*args(ALT+COEFFICIENTS)),k('enf',*args(OLD),ONE,ONE,cube,square,*args(COEFFICIENTS))))
    text+=define('enn',OLD+COEFFICIENTS,both(*(k('ba',x) for x in args(OLD+COEFFICIENTS)),op('x',op('u',k('sca',v('oldlongitudinal'),v('longitudinal'))),op('u',k('sca',v('oldtransverse'),v('transverse'))))))
    text+=define('eno',COMPARISON,both(k('enm',*args(COMPARISON)),k('enn',*args(OLD+COEFFICIENTS))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==426
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='same_electron_alternative_acceleration_convention',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/electron-directional-masses-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
