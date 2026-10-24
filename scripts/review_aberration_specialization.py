"""Review the named general law and the conditional right-angle display."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_aberration_specialization import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_aberration_specialization import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/aberration-specialization-v1.json'
REVIEWS=['data/einstein-aberration-specialization-u0195-review-v1.json','data/einstein-aberration-specialization-u0196-review-v1.json']

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'docs/aberration-presentation-v1.md','docs/aberration-line-v1.md','scripts/review_aberration_specialization.py','tests/test_aberration_specialization_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        text=s['text']
        meaning='直前の同じ式が、先行の許容する全速度・方向の光行差則を表すと同定する。同じ旧実数角φ=π/2の場合には、同じ式を簡明なcosφ′=−v/Vの形で示す。' if i==0 else '同じ旧角φ=π/2の条件と前段のφ′の命名を保持して、cosφ′=−v/Vを表示する。負号、速度vと光速Vの順、旧角と新角を保持する。'
        presentation='直前表示eisswの内容ekhcをeisoxで確認し、eischで法則名へ結び、uhでその全域の内容を著者の主張へ帰属する。eissbで同じ直角条件下の一般形から特殊形への提示、eisspで簡明さ、uf/ueでコロンと表示への説明・順序を保持する。' if i==0 else 'eisoxで表示を同じ条件内容ekhqへ結び、eir3で同じ著者・論説へ帰属し、ueでu0195のコロンに続く順序を保つ。無条件の数値式や真理の検査へ替えない。'
        if i==0:
            cut=text.index(' Ist ')
            clauses=[dict(range=[0,cut],text=text[:cut],statements=[377],definitions=['ekgy','ekhc','ekhr','eiss3','eisch','eisox','uh'],reason='この式という前方参照、光行差則の呼称、許容された全速度と方向という一般性を同じ61全称内容へ結ぶ。'),dict(range=[cut,len(text)],text=text[cut:],statements=[377],definitions=['ekhn','ekho','ekhp','ekhq','ekhs','ekhv','eissb','eissp','uf','ue'],reason='φ=π/2は同じ旧実数角の条件。一般形と特殊形に同じ設定を渡し、簡明さという著者評価、表示への書換えとコロンを保持する。')]
        else:clauses=[dict(range=s['range'],text=text,statements=[378],definitions=['ekhm','ekhn','ekho','ekhq','ekhw','ekhy','eisox','eir3','ue'],reason=meaning+' '+presentation)]
        assert all(n in catalog.entries for clause in clauses for n in clause['definitions'])
        reasons=[
         '固定在庫u0195全文とu0196の表示、M0341–M0342を原刊912頁へ照合した。Aberrationsgesetz、allgemeinsten、einfache、旧角φ=π/2、新角の余弦と負の速度比を保持し、原文・原刊・解釈記録をハッシュで固定した。',
         meaning,
         '同じ波・源・観測者・K/k・単位・位相・領域・速度・旧角・新角の65設定を共有する。一般性は先行の61全称の全許容域を使い、特殊形の二内容には同じ61変数と直角条件を渡す。名前と先行表示も同じekhcを参照し、角や法則の証人を選び直さない。',
         presentation,
         '最も一般的という程度は、先行の標準配置・近似が許容する全速度と方向の域に制限の追加がないこととして読む。小速度・特定方向へ縮めず、配置外の理論的万能性は補わない。簡明さは同じ記号で依存量が見渡せる形式評価とする。同時刻結線の字義的読解と印刷式の不整合を保持する。',
         '実数角は先行の内積・非負正弦・積分で定める測度を継承し、直角は同じpiの半分という等式で合成する。負比は既存の実数差・積・逆数から構成する。原語の法則名だけで意味を代用せず、全条件内容への命名、主張、提示、表示から合成し、新しい一般基本関係は加えない。',
         '負比と一般形右辺の代数的な一致、符号と尺度変更、角分岐、65設定の全位置、各61全称位置、引用・名前・提示・順序の各引数を検査した。全実数評価と未知入力を拒否する。pi=4の境界診断は正本の実数piと区別し、有限の成功から物理的真理や意味同義性を自動認定しない。',
         '直前表示からDiese Gleichung、法則名、一般性、Istによる直角条件、einfache Gestalt、コロン、後続の負比表示まで再読した。明示した全許容域と同時刻結線の読みの下で二単位の内容と提示を記述したと判断する。歴史的意図の一意な確定、実際の角が負比を満たすことの証明は含めない。',
        ]
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=text,range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,s['statements']),clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントによる意味判断であり、独立査読や意味同義性の自動証明ではない。','同時刻結線の字義的読解と印刷式の不整合を保持し、著者の歴史的意図や誤植を一意に断定しない。','u0178及びu0197以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC,'docs/aberration-presentation-v1.md','docs/aberration-line-v1.md']),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='named_general_aberration_law_and_right_angle_display_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=2,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
