"""Review the zero-angle relative clause and the comparatively simpler display."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_amplitude_specialization import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_amplitude_specialization import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record
REPORT='reports/amplitude-specialization-v1.json'
REVIEWS=['data/einstein-amplitude-specialization-u0199-review-v1.json','data/einstein-amplitude-specialization-u0200-review-v1.json']

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'docs/observed-amplitude-v1.md','data/wave-amplitudes-facsimile-v1.json','scripts/review_amplitude_specialization.py','tests/test_amplitude_specialization_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        text=s['text']
        meaning='直前の同じ二乗振幅比の式は、同じ旧実数角φ=0の場合に、同じ対象・系・単位・選択側を保つ、先行形より簡明な形へ移ると述べる。' if i==0 else '同じφ=0の条件とA/A′の規約を継承し、A′²=A²(1−v/V)/(1+v/V)を表示する。旧新の振幅の二乗、分子の差と分母の和を保持する。'
        presentation='welche Gleichungをeisoxで直前eiss6のekikへ結び、eissbで同じ零角条件下の一般形ekixから特殊形ekiyへの提示を保持する。eistbで後者が前者より簡明という厳密比較、uf/ueでコロンと同じ表示への説明・順序を結ぶ。' if i==0 else 'eisoxで同じ零角条件の内容ekiyを表示項目へ結び、eir3で同じ著者・論説へ帰属し、ueでu0199のコロンに続ける。無条件の式や物理的真理の自動認定へ替えない。'
        if i==0:
            cut=text.index(' in die ')
            clauses=[dict(range=[0,cut],text=text[:cut],statements=[381],definitions=['ekib','ekiv','ekix','ekik','eiss6','eisox'],reason='welche Gleichungという直前表示への照応と、同じ旧実数角φ=0の条件を同じ設定へ結ぶ。'),dict(range=[cut,len(text)],text=text[cut:],statements=[381],definitions=['ekiu','ekiw','ekiy','ekiz','ekjb','eistb','eissb','uf','ue'],reason='同じ条件の式が先行形より簡明な形に移るという提示、厳密比較、コロンと表示への接続を保持する。')]
        else:clauses=[dict(range=s['range'],text=text,statements=[382],definitions=['ekiu','ekiv','ekiw','ekiy','ekjc','ekje','eisox','eir3','ue'],reason=meaning+' '+presentation)]
        assert all(n in catalog.entries for clause in clauses for n in clause['definitions'])
        reasons=[
         '固定在庫u0199全文とu0200の表示、M0346–M0347を原刊912頁へ照合した。関係節のwelche、φ=0、比較級einfachere、コロン、A′とAの二乗、分子の負号と分母の正号を保持し、原文と原刊画像をハッシュで固定した。',
         meaning,
         '同じ波・源・過程・観測者・二系・校正された単位・局所近似・電気側又は磁気側・旧新振幅の63設定を保持する。二内容の各59全称役割と同じ零角条件を共有し、比較相手を先行の同じ振幅式に固定する。',
         presentation,
         'φ=0は実数角の零条件であり、余弦1だけの指定に縮めない。einfachereは先行形に対する厳密な形式評価と読み、単に新しい形が簡明という絶対評価へ縮めない。原文にない実測記録、横波条件、振幅の両側等値、唯一の最簡形は補わない。',
         '振幅と物理的な校正・近似の役割は前段から継承する。特殊比は実数の二乗・差・和・積・逆数から構成し、比較は同じ引用記述と文脈を保つeistbへ結ぶ。この一般比較はeisspと同じ評価観点を二項へ拡張し、物理量や式の内容を原始語へ隠さない。',
         '一般形の余弦1での右辺と特殊比、分子分母と二乗、零振幅と光速近傍、単位尺度変更、同じ実数角、63設定の全位置、各59全称位置、比較相手・逆方向・同一形・引用と表示を検査した。全実数評価は拒否し、有限対照から物理法則の真理又は意味同義性を自動認定しない。',
         '直前の二乗比表示から関係節、同じφ=0、先行形より簡明な形への移行、コロン、後続の差と和の比まで再読した。先行の校正された局所波形と形式比較という明示読解の下で二単位の内容と提示を記述したと判断する。',
        ]
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=text,range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,s['statements']),clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントによる意味判断であり、独立査読や意味同義性の自動証明ではない。','形式の厳密比較と代数的な整理、著者への帰属、物理的な真理は区別する。','u0178及びu0201以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE,'data/wave-amplitudes-facsimile-v1.json'],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC,'docs/observed-amplitude-v1.md']),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='zero_angle_amplitude_ratio_and_comparative_form_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=2,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
