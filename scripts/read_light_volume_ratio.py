"""Read the naming and simple-calculation sentence against its saved source."""
from functools import lru_cache
import json,re
from xml.etree import ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,REQUIREMENTS
from scripts.compose_light_volume_ratio import ROOT,read,FULL,BASIS,INDEX,LIMITS,MEANINGS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/light-complex-facsimile-v1.json'
DOC='docs/light-volume-ratio-v1.md';READING='data/einstein-light-volume-ratio-reading-v1.json'
PRIOR='data/einstein-light-ellipsoid-surface-u0207-review-v1.json'
REASONS=(
 '原刊913頁のu0208–u0209を一文として通読した。SとS′、球とこの楕円体、so ist、簡単な計算が示すという挿入、コロンとM0362の分数・平方根・cosφを照合した。',
 '同じ二体積をekpa/ekpbで命名し、ekoyのS′/S=√(1−(v/V)²)/(1−(v/V)cosφ)へ接続する。正の平方根は分子、余弦と速度の積は分母の減項であり、二乗した比や逆比へ置き換えない。',
 '同じekn7の68設定のうち63役割を共有する。二体積、同じ光の部分、半径・方向・速度・π・単位と状況を保持し、既存角条件のcosφ=aを利用する。',
 '量記号の導入をeislo、帰結と簡単さの著者主張をuh、同じ始終点の低負担計算をs2y、式の導入と表示をuf/eisox、直前の楕円体への参照をeisraで表す。',
 '球と楕円体は各系自身の零時刻での同じ物理部分の閉内部を指す。面積、同一の出来事集合又は光の静止慣性系へ替えない。命名は記法上の慣習として読む。',
 '新しい一般関係はなく、量取得・全称条件・既存積分・実数演算・有限計算列を合成した。四つの新原始記号は本文、表示、二量記号への参照であり、体積比を文専用述語へ格納しない。',
 '比の向きと係数、全63役割と量名の残余証人、同じ計算列の接続と負担、引用された内容の非実行、未知入力拒否を対照する。積分の既存証拠と今回の有理補題の範囲を区別する。',
 '直前の楕円体面と零時刻式から二体積の命名・容易な計算による比の提示まで再読した。明示した連続体・同時断面・量名と計算評価の読みの下で二単位を欠落なく記述したと判断する。',
)

@lru_cache(None)
def build_reading():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']}
    expected={'M0360':['S'],'M0361':['S','′'],'M0362':['S','′','S','=','1','−','(','v','V',')','2','1','−','v','V','cos','\u2061','φ','.']}
    tokens={n:[el.text for el in ET.fromstring(math[n]['mathml']).iter() if el.tag.rsplit('}',1)[-1] in ('mi','mn','mo')] for n in expected};assert tokens==expected
    root=ET.fromstring(math['M0362']['mathml']);ns='{http://www.w3.org/1998/Math/MathML}';fractions=list(root.iter(ns+'mfrac'));rhs=fractions[1]
    assert len(list(rhs[0].iter(ns+'msqrt')))==1 and not list(rhs[1].iter(ns+'msqrt'))
    facsimile=json.loads(read(SOURCE));image=facsimile['images'][0];assert digest((ROOT/image['path']).read_bytes())==image['sha256']
    assert facsimile['snapshot_math_sha256']['M0362']==math['M0362']['sha256']
    units=[]
    for index in (207,208):
        u=inv['units'][index];s=u['text'];units.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(s)],source=s,reviewed_prose_characters=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',s))),math=[dict(id=n,sha256=math[n]['sha256'],tokens=tokens[n]) for n in u['math_ids']],statements=[INDEX],definitions=list(MEANINGS)))
    catalog=load_catalog(ROOT,BASIS);paths=[INVENTORY,SOURCE,DOC,PRIOR,image['path'],'scripts/read_light_volume_ratio.py']
    return dict(schema_version='noema-sentence-reading-1',status='same_volumes_named_and_ratio_presented_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=units,reviewed_prose_characters=sum(u['reviewed_prose_characters'] for u in units),reviewed_math_elements=3,selection=selection_binding(catalog,[INDEX]),requirements=[dict(id=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],interpretation_limits=LIMITS,verified_full_units=0,semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
