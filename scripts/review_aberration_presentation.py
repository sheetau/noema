"""Review the angle introduction and its displayed equation as whole units."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_aberration_presentation import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_aberration_presentation import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/aberration-presentation-v1.json'
REVIEWS=['data/einstein-aberration-presentation-u0193-review-v1.json','data/einstein-aberration-presentation-u0194-review-v1.json']

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'docs/aberration-line-v1.md','data/einstein-aberration-line-reading-v1.json','scripts/review_aberration_presentation.py','tests/test_aberration_presentation_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        text=s['text']
        meaning='同じ移動系の波面法線と源から観測者への同時刻結線の角をφ′と呼び、同じ法線を局所的な前方位相伝播の光線方向として説明する。先行a′の式を、同じ設定のcosφ′の表示へ明示すると述べる。' if i==0 else '同じφ′の命名と旧角φの規約を保って、cosφ′=(cosφ−v/V)/(1−(v/V)cosφ)を表示する。a′との明示的な区別、分子分母と二つの負号を保持する。'
        presentation='eisloでφ′を同じ波・候補角・状況の規則へ結び、uh/eisa5で光線方向との同定を同じ命名への挿入として帰属する。eissbで先行a′の同じ内容を表示形として明示するという提示、uf/ueでコロンと表示への接続、eir3で著者・論説への帰属を保つ。' if i==0 else 'eisoxで同じ条件内容ekhcを表示へ対応させ、eir3で著者・論説へ帰属し、u0193のコロンに続くueを保持する。式の真理を帰属の検査時に実行しない。'
        if i==0:
            cut=text.index(', so')
            clauses=[dict(range=[0,cut],text=text[:cut],statements=[375],definitions=['ekgn','ekgt','ekgu','ekgv','ekgw','ekgx','ekgy','ekgz','ekhd','ekhe','eislo','eisa5','eissx'],reason='φ′の命名、移動系、波面法線と括弧内の光線方向、源―観測者の結線を、同じ位相・領域・同時刻・対象の角へ接続する。'),dict(range=[cut,len(text)],text=text[cut:],statements=[375],definitions=['ekha','ekhb','ekhc','ekhf','ekhh','eissy','eissb','eisox','uf','ue'],reason='a′は先行の変換後法線の縦方向余弦の式であり、その同じ設定をcosφ′の表示へ明示するという著者の提示とコロンを保持する。実際の同値性を要求して原文を訂正しない。')]
        else:clauses=[dict(range=s['range'],text=text,statements=[376],definitions=['ekgo','ekhc','ekhi','ekhk','eisox','eir3','ue'],reason=meaning+' '+presentation)]
        assert all(n in catalog.entries for clause in clauses for n in clause['definitions'])
        reasons=[
         '固定在庫u0193全文とu0194の全表示、M0338–M0340を原刊912頁へ照合した。φ′、a′、Verbindungslinie „Lichtquelle-Beobachter“、括弧内のStrahlrichtung、二つの負号と分数の範囲を保持する。原文と原刊画像をハッシュで固定した。',
         meaning,
         '波・源・観測者・K/k・単位・旧位相・新引戻し位相・新領域・速度・旧角・新角を同じ65設定の中で共有する。旧静止源を新同時刻で表す曲線とその結線の遠距離極限を再使用し、φ′の59証人と三内容の61全称位置で値や対象を選び直さない。a′と結線との角の余弦は別の役割として保つ。',
         presentation,
         '結線は同じ移動系の同時刻、向きは源から観測者へと明示する。光線方向は局所の前方位相伝播として読み、実測エネルギー流・光子の軌跡・領域外の厳密平面波は追加しない。先行の近似条件と物理的な源の帰属を保ち、式を正しくするために結線を速度方向へ変更しない。',
         '角は二単位方向の内積と非負正弦、既存の実数積分に基づく測度へ合成する。法線と光線方向は同じ局所位相の全位置対と前方伝播へ結ぶ。名前のφ′は識別表記だけで意味を代用せず、閉じた対象・値・状況の規則ekgzへ結ぶ。新一般基本関係はない。',
         '新旧四座標、同時刻結線の尺度変更、二方向の違い、正確な有理数の前方位相伝播、両端の局所領域、全存在・全称位置、名前・挿入・先行式・表示の各引数を検査した。全実数評価は拒否する。前段の4/5対−3/5の対照を保持し、有限検査の成功から物理的な正しさ又は意味同義性を自動認定しない。',
         '先行の同じ波・方向式から、Nennt man、φ′、Wellennormale (Strahlrichtung)、移動系と結線、a′の式、soによる明示とコロン、M0340の表示を通して再読した。明示した同時刻結線と局所的な光線方向の読みの下で、今回二単位の内容と提示を記述したと判断する。歴史的意図の一意な確定や式の真理はこの判断に含めない。',
        ]
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=text,range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,s['statements']),clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントによる意味判断であり、独立査読や意味同義性の自動証明ではない。','同時刻結線の字義的読解と表示式の不整合を保持し、誤植や著者の歴史的意図を一意に確定しない。','u0178及びu0195以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE,'data/einstein-aberration-line-reading-v1.json'],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC,'docs/aberration-line-v1.md']),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='literal_line_angle_introduction_and_aberration_display_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=3,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
