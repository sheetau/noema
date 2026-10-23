"""Whole readings of the common-origin wave and its rest-frame equation."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_rest_spherical_wave import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_rest_spherical_wave import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/rest-spherical-wave-v1.json'
REVIEWS=tuple(f'data/einstein-rest-spherical-wave-u{n:04d}-review-v1.json' for n in (87,88))
CLAUSES=(
 (
  ('Zur Zeit [M0141] ',['ei76','ei46'],'同じ放出出来事におけるt=τ=0を保持する。'),
  ('werde von dem zu dieser Zeit gemeinsamen Koordinatenursprung beider Systeme aus eine Kugelwelle ausgesandt, ',['ei76','ei77','ei75','ejab','ug'],'両系の原点がその時に重なる出来事からの球面波の放出を仮定する。'),
  ('welche sich im System [M0142] mit der Geschwindigkeit [M0143] ausbreitet. ',['ei77','ei43','ei73','ei75'],'同じ波がKで同じVにより広がることを現在の測定・光区間・波面に結ぶ。'),
  ('Ist ([M0144]) ein eben von dieser Welle ergriffener Punkt, ',['ejaa','ei74','eiyx','zc6'],'その波がいま到来する任意の点の三座標と、同じ出来事の時刻を条件へ結ぶ。'),
  ('so ist also',['ejab','ejaa','zc'],'仮定した波と到来点の条件から後続の球面式を提示する帰結を保持する。'),
 ),
 (('[M0145].',['sqj','sqk','ejaa','ejab'],'同じ記録のx,y,z,tと同じVによるx²+y²+z²=V²t²を保持し、前の条件文を句点で閉じる。'),),
)
REASONS=(
 (
  '固定u0087全269文字・本文203文字とM0141–M0144を原刊901頁へ照合した。第一文の放出仮定と第二文の到来点の条件を、次のu0088の数式・句点まで続けて通読した。',
  '放出時刻の二つの零、放出時に限った両系の共通原点、同じ波の非空な全構成光線、KでのVの伝播、到来した任意の点、同じ座標と時刻、仮定からの式の帰結を保持する。波面は全対象範囲で到来と正時刻の球面式が過不足なく一致する条件とした。',
  'M0141は同じ放出出来事のK/k時刻、M0142は既存raのK、M0143は既存tcのV、M0144は同じ現在K記録の三位置を指す。zfu/zfvで同じ波と放出を共有し、各区間のwhも放出に一致させる。tを別の出来事から取らない。',
  'werde ... ausgesandtをugによる仮定の提示とし、実際の放出報告や読者への命令に替えない。Ist ... so ist alsoは全対象出来事とK記録に対する到来条件の下の式であり、zcにより波の仮定からの帰結として述べる。同じ著者・第三節・論説へ帰属する。',
  '共通原点と時刻一致を全時刻へ延長しない。波面外の到来や波面上の欠落を許さず、零時刻の放出を正時刻の到来から分ける。球面式だけで実際の光の伝播を済ませず、特定の一光線や一つの点へ対象を縮めない。後続の変換計算やφ=1を追加しない。',
  '既存の実切断の平方和sqj/sqk、正時刻sql、現在の同じ出来事の座標eiyxと共通原点ei46、現在の光区間ei44と全法則ei43を合成する。波を同じ放出の構成光線と到来の幾何学的波面として読むことを明記し、未説明の新しい原始語で一文を代用しない。',
  '原刊・固定本文・構成式の通読を根拠とし、同じ光線と測定区間の引数、全構成光線の共通放出、波面上の到来欠落・内部の余分な到来、同値な別記録、負時刻、任意の到来点の式を有限対照で確認した。全物理的モデルや連続空間の網羅を有限例から証明したとはしない。',
  '前の証明課題から放出仮定、到来点、表示式までを再読した。明示した現在の全対象範囲と幾何学的波面の読みの下で、二文の関係・参照・仮定と帰結を欠落なく保持したと判断する。',
 ),
 (
  '固定u0088のM0145と句点を原刊901頁へ照合した。五つの平方、左辺の二加法、右辺の積と等号、前の条件文を閉じる句点を確認した。',
  '同じ点の三位置の平方和が、同じVの平方と同じK時刻の平方の積に等しいことをsqj/sqkで表す。三成分を一成分へ縮めず、Vtの平方の符号から正時刻を勝手に導かない。',
  'x,y,z,tはejaaで量化された同じ出来事の現在K記録から取り、Vは同じtc。直前の波と放出をei74へ共有し、k側のξ,η,ζ,τの式へ先回りしない。',
  '前のIst ... so ist alsoの帰結として、仮定した波が到来する任意の点について述べる式である。ejab/ejadが同じ著者の仮定・条件付き帰結と本文順序を保持し、独立した無条件の実測値報告にしない。',
  '二乗式は零時刻と負時刻でも解を持ち得るため、未来側の到来条件sqlと放出条件ei76を分けた。表示式そのものに正時刻という余計な項を入れず、物理的到来と数値の一致を混同しない。後続の座標変換式はこの単位へ加えない。',
  '既存の実数加法・乗法・差と切断の同値で平方和を構成し、有効な四座標と正のVを保持する。未知の数式記号を自然言語ラベルで済ませず、既存の意味規約と現在の座標対応へ結んでいる。',
  '原刊表示とMathMLの五平方、数値対照の三位置・時刻・Vの変更、零時刻と負時刻、全到来記録への条件を確認した。一般実数体や物理的導出・原文との意味同値の自動証明ではない。',
  'u0087の放出仮定と到来点からu0088の式と句点まで再読した。同じ幾何学的波面と任意の到来点の読みの下で、表示式全体とその条件付きの役割を欠落なく記述したと判断する。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_rest_spherical_wave.py','tests/test_rest_spherical_wave_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and len(REASONS[i])==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['現在の全対象座標範囲と幾何学的な到来波面を明示した読みの下でのアシスタントの通読判断。独立査読、一般物理的導出、連続空間の実現や意味同値の自動証明ではない。','u0089以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r
        validate_review(ROOT,p,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='rest_spherical_wave_and_arrival_equation_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=5,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
