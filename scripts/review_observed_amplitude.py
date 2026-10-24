"""Review the remaining amplitude inquiry, frame-bound names and displayed ratio."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_observed_amplitude import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_observed_amplitude import DOC,SOURCE,INVENTORY,COLLATION,DEPENDENCIES,source_record
REPORT='reports/observed-amplitude-v1.json'
REVIEWS=['data/einstein-observed-amplitude-u0197-review-v1.json','data/einstein-observed-amplitude-u0198-review-v1.json']

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,COLLATION,DOC,*DEPENDENCIES,'docs/wave-amplitudes-v1.md','scripts/review_observed_amplitude.py','tests/test_observed_amplitude_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        text=s['text']
        meaning='同じ波が移動系で示す振幅を、この段階でなお求める課題として提示する。AとA′を、静止系と移動系の同じ電気側又は磁気側について校正された力の単位で評価する非負振幅と命名し、先行の成分変換から二乗比を得ると述べる。' if i==0 else '同じ波・系・単位・選んだ側・旧角の条件を継承し、A′²=A²(1−(v/V)cosφ)²/(1−(v/V)²)を表示する。原刊912頁の分母に平方根がないことを明示し、固定電子在庫との差を保存する。'
        presentation='eiss4で同じ先行仮定の条件と実数値質問の族を、この段階でなお取り扱う課題として帰属する。eisloでA/A′の二つの役割を命名し、eissbで先行成分式を同じ設定で明示し、zcで二乗比への帰結提示、uf/ueでコロンと表示への説明・順序を保つ。' if i==0 else 'eisoxで表示を同じ59全称の条件内容ekikへ結び、eir3で同じ著者・論説へ帰属し、ueでu0197のコロンに続ける。等式の物理的真理を帰属時に実行しない。'
        if i==0:
            first=text.index(' Nennt man ');second=text.index(', so erhält man:')
            clauses=[dict(range=[0,first],text=text[:first],statements=[379],definitions=['ekic','ekid','ekie','ekin','eiss4'],reason='Wir、nun noch、同じ波と移動系での振幅、求める課題を、候補の外側で61設定を共有する質問族へ結ぶ。'),dict(range=[first,second],text=text[first:second],statements=[379],definitions=['ekhz','ekia','ekib','ekif','ekig','ekih','eket','eislo','eiss7','eista'],reason='A/A′の命名とそれぞれの系、電気側又は磁気側、gemessenを同じ校正された物理場の局所近似の振幅として保持する。実測記録の存在や両側の振幅等値を追加しない。'),dict(range=[second,len(text)],text=text[second:],statements=[379],definitions=['ekii','ekij','ekik','ekim','ekio','ekiq','eissb','zc','uf','ue'],reason='同じ先行成分変換から結果を得るという提示とコロンを、同じ対象・単位・側の二乗比と後続表示へ接続する。')]
        else:clauses=[dict(range=s['range'],text=text,statements=[380],definitions=['ekii','ekij','ekik','ekir','ekit','eisox','eir3','ue'],reason=meaning+' '+presentation)]
        assert all(n in catalog.entries for clause in clauses for n in clause['definitions'])
        reasons=[
         '固定在庫u0197全文とu0198の表示、M0343–M0345を原刊912頁へ照合した。既存のdata/wave-amplitudes-facsimile-v1.jsonに従い、M0345の外側分母の根号だけが原刊にはないことを別記録で保持する。元と照合後のMathML、元単位と数式のハッシュ、原刊画像を固定した。',
         meaning,
         '同じ60物理設定を、側・旧振幅・新振幅を加えた63役割へ共有する。質問は61入力を候補の外側に固定し、二つの表記規則は各56証人で波と候補値を同じ設定へ結ぶ。比は59全称役割の同じ割当について述べ、電気側か磁気側かを旧新で取り違えない。',
         presentation,
         'gemessenは各系の校正された力の単位で評価する量という理想化した読解と明示する。先行の局所近似・誤差と十分性を保持し、正弦の係数を誤差零の実測記録へ置き換えない。原文にない測定装置・実施済みの記録・横波条件・電気振幅と磁気振幅の等値を新たな明示的前提にしない。',
         '三係数の非負の大きさはseal、同じ六成分の変換はsdz2とtransformed、物理的な力と単位はeketに含まれる既存の校正規約へ結ぶ。二乗比は実数の積・差・逆数から構成する。新一般関係は数値質問族の課題提示だけで、振幅・測定・系・波を原語の綴りや一文専用の原始関係へ圧縮しない。',
         '非負性、両側の選択、横波の正負零の尺度と速度、成分変換、非横波の反例、原刊と電子在庫の分母の違い、設定・質問・存在と全称の各位置、課題と命名と帰結提示を検査する。原文にない条件を使って式を常に真にせず、全実数評価を拒否する。局所検査は意味同義性又は物理理論の全域的証明ではない。',
         '先行の同じ波の検討から、Wir haben nun noch、移動系に現れる振幅、Nennt man、二つの名とそれぞれの系、電気側又は磁気側、gemessen、so erhält manとコロン、原刊の二乗比を通して再読した。校正された局所波形の理想化という明示読解の下で二単位の内容と提示を記述したと判断する。',
        ]
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=text,range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,s['statements']),clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントによる意味判断であり、独立査読や意味同義性の自動証明ではない。','局所近似の校正された振幅の読みであり、実際の測定記録や真空方程式からの全域的導出の証明ではない。','u0178及びu0199以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE,COLLATION],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC,'docs/wave-amplitudes-v1.md']),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='same_wave_amplitude_inquiry_names_and_ratio_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=3,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
