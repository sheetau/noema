"""Record the complete reading of the charged electron's initial rest law."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-electron-rest-law-claim.noema';CORE='examples/v014/electron-rest-law-claim-core.noema'
BASIS='data/electron-rest-law-claim-basis-v1.json';ANNOTATIONS='data/electron-rest-law-claim-identifiers-v1.json'
SOURCE='data/einstein-electron-rest-law-reading-v1.json';REPORT='reports/electron-rest-law-claim-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/electron-rest-law-claim-v1.md'
REVIEWS=tuple(f'data/einstein-electron-rest-law-u{n:04d}-review-v1.json' for n in range(240,244))
CLAUSES=(
 (
  ('In einem elektromagnetischen Felde ',['ek34','ejsn','ek3p','ek3q'],'同じ校正された電磁場の領域に同じ点粒子の局所履歴を置く。電場と磁場を区別し、真空又は無磁場に限定しない。'),
  ('bewege sich ein punktförmiges, mit einer elektrischen Ladung [M0394] versehenes Teilchen ',['ek36','ek4m','ek3u','eisqc','sbw2','ek4d','ek4i','ek4j','ek4c','ek37'],'点状の同じ担体に符号付き非零電荷εを帰属させ、位置変化する場合を仮定する設定指示。現実の存在や実験の命令に替えず、瞬間静止を許す。'),
  ('(im folgenden „Elektron“ genannt), ',['ek4e','eisd4','eisxi','eisxh'],'括弧内で導入した同じ粒子に以後の呼称Elektronを採る。固定負電荷や現代の粒子種の含意は補わない。'),
  ('über dessen Bewegungsgesetz wir nur folgendes annehmen:',['ek4f','eiswx','ek35','ek4g','ek4h','ek4k','ek4l'],'この同じ粒子の運動法則について、同じ著者がこの段階で独立に採る前提を後続の条件付き三式だけに限定する。背景・意味規約・設定・導いた帰結は追加の独立な運動前提に数えない。コロンから同じ後続の式へ接続する。'),
 ),
 (
  ('Ruht das Elektron in einer bestimmten Epoche, ',['ek3r','ek33','ek34','ek35','eisxh'],'先の同じ電子の、任意の設定で指定した同じ出来事の三座標速度が零であることを条件とする。全時刻にわたる静止ではない。'),
  ('so erfolgt in dem nächsten Zeitteilchen die Bewegung des Elektrons ',['ek3y','ek3z','ek32','ek33','sjs','senz'],'当該座標時刻の直後への初期速度変化として、基点を含む同じ時間領域の右側で三速度の微分を同じ加速度へ結ぶ。通常実数での右微分という読みを明示し、有限な時間粒や有限区間の一定加速を補わない。'),
  ('nach den Gleichungen',['ek3t','ek33','ek35','ek4g','eisxd','eisxe'],'同じ静止条件の下で、後続の三行のμa=εEによってこの初期運動を指定する。前提採用と表示への接続を保持し、検証器の物理法則の証明にしない。'),
 ),
 (
  ('[M0395]',['ek3s','ek3t','ek3q','sepp','ek32','ek33','ek35','ek4g','eisox'],'μ d²x/dt²=εX、μ d²y/dt²=εY、μ d²z/dt²=εZの三行を順序と対応を保って表す。同じ局所履歴の座標時刻の二階微分と同じ出来事の電場、符号付き電荷、低速慣性質量を使う。直前の静止条件・直後の初期変化と後続の意味説明を同じ表示へ結ぶ。'),
 ),
 (
  ('wobei ',['ek4g','eisxf','eisxe','uf'],'同じ三式に付随する意味説明として後方へ結び、独立の無関係な定義列へ替えない。'),
  ('[M0396] die Koordinaten des Elektrons, ',['ek4c','ek4a','eiswz','eisxk','ek34','yn','yo','yp'],'x,y,zを、同じ電子・系・出来事の位置から取り出す三空間座標へ順に対応させる。場、速度、固有時、別の粒子の座標へ交換しない。'),
  ('[M0397] die Masse des Elektrons bedeutet, ',['ek4c','ek4b','eiswy','eisxl','ek3o'],'μを同じ粒子・出来事・単位での慣性質量の値へ対応させる。電荷又は任意の正定数には替えない。'),
  ('sofern dasselbe langsam bewegt ist.',['eisww','ek3o','ek4b','ek34','ek4l'],'低速で運動する場合の質量というμの意味の限定を保つ。現在の全設定を低速に限定せず、後で扱う任意速度の力学へ使う基準の慣性係数として読む。'),
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_electron_rest_law_claim.py','tests/test_electron_rest_law_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for index,(s,parts) in enumerate(zip(source['segments'],CLAUSES)):
        assert s['unit']==f'einstein-1905:u{240+index:04d}'
        statements=[413,414] if index==0 else [414];clauses=[];offset=0
        for text,symbols,reason in parts:
            assert s['text'][offset:offset+len(text)]==text,(s['unit'],offset,text)
            assert all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=statements,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        rereading=(
          '原刊917頁で一文を再読した。電磁場内の点状荷電粒子を動かす設定指示、εの帰属、括弧内の以後の命名、同じ粒子の運動法則に関する仮定の限定、コロンによる後続の予告をすべて保持したと判断する。現実の存在や現代の電子種という補足を入れない。',
          '原刊917頁で直前の仮定採用と直後の三式を含めて再読した。指定された一時点での同じ電子の静止を条件に、直後の初期運動が三式に従うという条件と前方参照を保持したと判断する。通常実数の右側の微分という明示した読みの下での判断であり、有限時間の挙動は述べない。',
          '原刊917頁の三行を見直し、各行のμ、二階座標時刻微分、εと対応するX/Y/Z、等号、三空間軸の順を照合した。直前の条件を受けて表示された三式と、後続の記号説明の全内容を同じ設定に接続したと判断する。式の物理的妥当性の独立な証明ではない。',
          '原刊917頁のwobeiから文末までを直前の三式とともに再読した。x,y,zが電子の座標、μが同じ電子の低速時の質量を意味することを保持したと判断する。低速の句をμの意味の限定として読むことを明示し、現在の全運動へ一律に制限を課さない。',
        )[index]
        reasons=(
          f'固定した{s["unit"]}の全文を原刊917頁と照合した。u0240–u0243の連続した導入・条件・三式・意味説明を文脈とし、M0394のε、M0395の三行、M0396のx,y,z、M0397のμを個々のハッシュで固定する。第十節見出しu0239は今回の全文判断の外である。',
          '物理的設定ek34は同じ点粒子・出来事・局所履歴・電磁場・単位・符号付き電荷・低速慣性質量を保つ。ek36の位置変化を持つ仮定的導入と、ek35の任意設定での静止条件付き法則を区別する。ek33は三式と同じ加速度による右側初期変化を結び、ek4cは同じ設定からの射影で記号の意味を接続する。各句に示す定義と理由がこの単位の実際の構成である。',
          '導入参照eisxhをek34で同じ対象へ固定し、eisd4によって以後の呼称を採用する。各量は同じ設定から取り出すので別の電子・出来事・系の値へ交換しない。著者rd、論説eirf、K=ra、第十節eisxgを共用する。仮定予告・静止条件・表示・意味説明は別箇所とし、順序ueと説明ufで同じ内容へ接続する。',
          'bewege sichの仮定的設定は指示形式ek4i、その後の命名・前提採用・表示・意味説明は断定形式ek4kへ置き、二つの伝達を同じ著者の論説へeir3で帰属させる。nur folgendesは同じ運動法則についてこの段階の独立な前提だけを限定する。表示は条件付きek35を受け、無条件の真理、検証済み定理、実験の実行へ取り替えない。',
          '通常実数の右側の差商極限という直後の読み、正の低速慣性質量、完全な二階微分可能な局所履歴、整合単位を明示的なモデル規約として採る。瞬間静止は位置変化と両立する。有限な最小時間、有限時間の一定加速、解の存在一意性、全時刻の低速、真空、無磁場、無放射、電荷の固定負値は補わない。第十節見出しの緩い加速を今回解決したとはしない。',
          '右側領域ek3yは元の時間領域を当該時刻以上へ制限し、基点を保って既存sjsの微分を使う。三式は既存の実数積・等値・実際の座標微分から構成し、文ごとの物理原始関係へ収納しない。新しい一般関係は独立な運動前提の採用と、同じ設定からの数量・座標表記の射影による意味指定に限る。前提の同値な表示は指定した同じ内容へ正規化して参照する。',
          '固定した下位の物理的依存検査に加え、右側領域と解析的な速度多項式、同じ時点の三軸、条件の向き、導入の位置変化、三射影、余分な独立前提、著者・対象・範囲・表示の取り違えを局所検査する。二値の小領域で全30束縛位置を区別して確認し、全引用内容と全実数のネイティブ量化は有限検査で認定しない。検査成功から原文同義性を導かず、この全文判断を別に記録する。',
          rereading,
        )
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,statements),source_order_statements=statements,clauses=clauses,interpretation=basis['limitations'],limits=['明示した読みの下でのアシスタントによる全単位判断。独立査読、全連続体の証明、原文同義性の自動証明ではない。','直後を右側の初期微分、低速をμの意味の限定、ただ次だけをこの段階の独立な運動法則の前提の限定と読む。','第十節見出しと二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    assert len(out)==4
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,record in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(record,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    pins={};rs=records()
    for path,r in zip(REVIEWS,rs):
        assert json.loads(read(path))==r;validate_review(ROOT,path,'einstein-1905',active,catalog,inventory)
        merge_pins(pins,r['source_sha256']);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='electron_rest_law_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in rs},reviewed_math_elements=4,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},semantic_equivalence_automatically_proved=False,source_sha256=pins)
