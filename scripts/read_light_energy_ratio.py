"""Collate the full naming, energy ratio and zero-angle relative clause."""
from functools import lru_cache
import json,re
from xml.etree import ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,REQUIREMENTS
from scripts.compose_light_energy_ratio import ROOT,read,FULL,BASIS,INDEX,LIMITS,MEANINGS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/light-complex-facsimile-v1.json'
DOC='docs/light-energy-ratio-v1.md';READING='data/einstein-light-energy-ratio-reading-v1.json'
PRIOR='data/einstein-light-volume-ratio-u0209-review-v1.json'
REASONS=(
 '原刊913–914頁のu0210–u0213を一文として通読した。E/E′の系別命名、同じ面が囲む光、一般式の両等号とコンマ、次頁のwelche Formel、φ=0、より簡明な式と句点を照合した。',
 'ekplはE′/E、両平均密度と各体積の積の比、(1−(v/V)cosφ)/√(1−(v/V)²)を同じ値で結ぶ。ekpt/ekpvは同じ実数角零で√((1−v/V)/(1+v/V))を述べる。',
 '同じ70設定のうち65役割を共有する。二系の同時内部・波・部分・単位・平均・角・振幅・体積・二総量を結び、命名の残余証人と実際の比の共有設定を区別する。',
 '命名eislo、先行密度と体積・振幅からの帰結zc、主張uh、表示eisox、コロンuf、順序ue、照応eisra、同じ零角での移行eissbとより簡明という厳密比較eistbを保持する。',
 'gemessenは各系の校正単位での量評価、総量は同じ位相平均密度の空間積分として読む。同じ面と部分を保ち、表面積・瞬間密度・光速観測者・測定済みの二実験に替えない。',
 '新しい一般関係はなく、既存積分・量取得・全称条件・実数演算・提示と比較を合成した。六つの新原始記号は四本文表示箇所と二量記号への参照である。',
 '両等号、分子分母と根号、旧総量の非零条件、二積分の役割、全65設定と64証人、零角と特殊化、比較の方向と未知入力拒否を検査する。有限・有理の証拠を全実数域の証明に拡張しない。',
 '前の体積比から二総量の命名・一般表示・零角のより簡明な表示までを通読した。明示した同時断面・平均総量・量名と形式比較の読みの下で四単位の内容と提示を欠落なく記述したと判断する。',
)

@lru_cache(None)
def build_reading():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']}
    expected={'M0363':['E'],'M0364':['E','′'],'M0365':['E','′','E','=','A','′',None,'2','8','π','S','′','A','2','8','π','S','=','1','−','v','V','cos','\u2061','φ','1','−','(','v','V',')','2',','],'M0366':['φ','=','0'],'M0367':['E','′','E','=','1','−','v','V','1','+','v','V','.']}
    tokens={n:[el.text for el in ET.fromstring(math[n]['mathml']).iter() if el.tag.rsplit('}',1)[-1] in ('mi','mn','mo')] for n in expected};assert tokens==expected
    ns='{http://www.w3.org/1998/Math/MathML}';root=ET.fromstring(math['M0365']['mathml']);fractions=list(root.iter(ns+'mfrac'));general=fractions[4]
    assert not list(general[0].iter(ns+'msqrt')) and len(list(general[1].iter(ns+'msqrt')))==1
    special=ET.fromstring(math['M0367']['mathml']);radical=next(special.iter(ns+'msqrt'));assert len(list(radical.iter(ns+'mfrac')))==3
    facsimile=json.loads(read(SOURCE));images=facsimile['images'][:2]
    for image in images:assert digest((ROOT/image['path']).read_bytes())==image['sha256']
    for n in ('M0365','M0367'):assert facsimile['snapshot_math_sha256'][n]==math[n]['sha256']
    units=[]
    for index in range(209,213):
        u=inv['units'][index];s=u['text'];units.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(s)],source=s,reviewed_prose_characters=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',s))),math=[dict(id=n,sha256=math[n]['sha256'],tokens=tokens[n]) for n in u['math_ids']],statements=[INDEX],definitions=list(MEANINGS)))
    annotation=next(a for a in inv['annotations'] if a['id']=='A0028');assert annotation['kind']=='page' and annotation['source_id']=='914'
    catalog=load_catalog(ROOT,BASIS);paths=[INVENTORY,SOURCE,DOC,PRIOR,*[im['path'] for im in images],'scripts/read_light_energy_ratio.py']
    return dict(schema_version='noema-sentence-reading-1',status='same_enclosed_energy_names_ratio_and_zero_angle_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=units,reviewed_prose_characters=sum(u['reviewed_prose_characters'] for u in units),reviewed_math_elements=5,source_annotation=annotation,selection=selection_binding(catalog,[INDEX]),requirements=[dict(id=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],interpretation_limits=LIMITS,verified_full_units=0,semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
