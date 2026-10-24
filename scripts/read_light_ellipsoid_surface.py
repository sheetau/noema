"""Collate and read the moving-frame ellipsoid introduction and displayed equation."""
from functools import lru_cache
import json,re
from xml.etree import ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes,REQUIREMENTS
from scripts.compose_light_ellipsoid_surface import ROOT,read,FULL,BASIS,INDEX,LIMITS,MEANINGS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/light-complex-facsimile-v1.json'
DOC='docs/light-ellipsoid-surface-v1.md';READING='data/einstein-light-ellipsoid-surface-reading-v1.json'
PRIOR='data/einstein-portion-energy-inquiry-u0205-review-v1.json'
REASONS=(
 '原刊913頁のu0206とu0207を一文として通読した。M0358=τ=0、M0359の三つの差の二乗和=R²、第一項のβξと各項のマイナスを照合した。',
 '同じ球面の逆Lorentz像を任意の新系時刻で可逆三角写像の球面像へ結ぶ。正のDとR、実数係数、両順序の位置復元により楕円体面を構成し、表示は新系時刻零の全三位置で同じ面に一致させる。',
 '前の問いの同じ68設定からK,V,波範囲,部分zvaa,状況を固定し、63役割を共有する。ξ,η,ζは同じkの三位置、τはk自身の時刻であり、t=0と同時に零へ置かない。',
 '著者の形状主張uh、コロンからの導入uf、式の表示eisoxと順序ue、前の質問への照応eisraを保つ。原文にない自明性、導出済み、光学的な見かけを追加しない。',
 '楕円体を可逆な線形像という一般的な幾何学の意味で読む。せん断を保持し、回転楕円体や特定主軸への限定を加えない。閉内部、物質殻、光速慣性系、同じ光の部分の物理的同一性を図形だけで置き換えない。',
 '一般関係の追加はなく、実数・写像・位置・全称と既存の物理部分及び表示関係を合成する。二つの新原始記号は本文と表示への参照であり、楕円体面という意味を未説明の述語へ格納しない。',
 '可逆写像・全時刻中心・面内外・新旧零時刻・63設定と四座標・表示の向きの対照、及び有理多項式補題を検査する。全実数の主軸定理、原文の物理理論又は意味同義性の自動証明ではない。',
 '前の同じ部分の問いから、楕円体面の考察・τ=0の式の提示まで再読した。明示した連続体と校正座標・アフィン球面像の読みの下で、二単位の内容と提示を欠落なく記述したと判断する。',
)

@lru_cache(None)
def build_reading():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};units=[]
    expected={'M0358':['τ','=','0'],'M0359':['(','β','ξ','−','a','β','v','V','ξ',')','2','+','(','η','−','b','β','v','V','ξ',')','2','+','(','ζ','−','c','β','v','V','ξ',')','2','=','R','2','.']}
    tokens={n:[el.text for el in ET.fromstring(math[n]['mathml']).iter() if el.tag.rsplit('}',1)[-1] in ('mi','mn','mo')] for n in expected}
    assert tokens==expected,(tokens,expected)
    facsimile=json.loads(read(SOURCE));image=facsimile['images'][0];assert digest((ROOT/image['path']).read_bytes())==image['sha256']
    assert facsimile['snapshot_math_sha256']['M0359']==math['M0359']['sha256']
    for index in (205,206):
        u=inv['units'][index];s=u['text'];units.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(s)],source=s,reviewed_prose_characters=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',s))),math=[dict(id=n,sha256=math[n]['sha256'],tokens=tokens[n]) for n in u['math_ids']],statements=[INDEX],definitions=list(MEANINGS)))
    catalog=load_catalog(ROOT,BASIS);paths=[INVENTORY,SOURCE,DOC,PRIOR,image['path'],'scripts/read_light_ellipsoid_surface.py']
    return dict(schema_version='noema-sentence-reading-1',status='same_surface_ellipsoid_and_display_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=units,reviewed_prose_characters=sum(u['reviewed_prose_characters'] for u in units),reviewed_math_elements=2,selection=selection_binding(catalog,[INDEX]),requirements=[dict(id=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],interpretation_limits=LIMITS,verified_full_units=0,semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
