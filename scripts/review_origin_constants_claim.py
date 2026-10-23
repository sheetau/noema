"""Explicit whole-unit reading of Einstein u0085 under the stated interpretation."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_origin_constants_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_origin_constants_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/origin-constants-claim-v1.json'
REVIEW='data/einstein-origin-constants-u0085-review-v1.json'
CLAUSES=(
 ('und ',['ei7r','ue','zfk','zfp'],'直前のβの指定に続いて同じ四式のφを説明する。'),
 ('[M0137] eine vorläufig unbekannte Funktion von [M0138] ist. ',['sqd','sqc','smq','smb','spc','ei7p','ei7r'],'φがこの段階では未決定のvの関数であるという内容を、同じ正規化後の候補族と現在の関数へ結ぶ。'),
 ('Macht man über die Anfangslage des bewegten Systems und über den Nullpunkt von [M0139] keinerlei Voraussetzung, ',['sqa','zfn','zfo','zfm','ei7s'],'運動系の初期空間位置とτ零点の仮定を採らないことを前件とし、同じ物理条件を保つ設定について述べる。'),
 ('so ist auf den rechten Seiten dieser Gleichungen je eine additive Konstante zuzufügen.',['ei7s','ei7o','ei7n','ei7m','spu','ei7u'],'先の四式の各右辺へ一つずつ独立な実数定数を加える帰結。設定内の全記録対で同じ一組を共有する。'),
)
REASONS=(
 '固定u0085の全262文字、数式記号を除く本文204文字とM0137–M0139を原刊900頁へ照合した。四式・βからundの説明、原点仮定を外す条件文と後続の光速度の証明課題まで通読した。',
 '暫定的な未決定性、vに対する関数であること、同じφへの照応、初期空間位置とτ零点の仮定の非採用、条件と帰結、各右辺への加法と定数の共有範囲を保持する。sqdは値の異なる残存候補を要求し、ei7nの四存在量化はei7mの全記録対の外にある。',
 'φは直前の四式のspcであり、以前のa=zeqとはφ=aβで結ぶ。sqcの候補も同じβで正規化する。V,v、二系、三位置と時間の役割を先行定義から継承し、ei26/ei27/ei3aは同じ指定設定のeiyxへ接続する。',
 '冒頭のundをβからの説明の継続としてueで結ぶ。ei7pは未決定性の説明、ei7sはsqaからei7oへの条件付きの数学的帰結である。両者をeir3で同じ著者・論説へ帰属し、引用内容の成立や計算行為の実行は要求しない。',
 '未知は現在段階で候補が残るという明示した読みであり、あらゆる知識の不存在やφ=1を追加しない。仮定の非採用を零点の不一致に替えず、四定数を一値へ統一せず、記録ごとに取り替えない。零定数も許す。別設定へ元の零原点条件を再要求せず、数学的な必要性を人への命令にしない。',
 '実数の切断と加法、既存の正規化後の四式spu、同じ出来事の測定対応、候補関数の全域一致と相違の証人、既存の著者帰属と条件内容を合成する。zfn/zfoは既存の意味規約を持つ設定維持・仮定非採用の基本関係であり、新たな文専用原始語を加えていない。',
 '原刊画像と固定本文の照合、同じ設定・出来事の引数対照、二つの異なる入力での四定数共有、別記録・欠落・余分な対応、候補の一点一致と他点相違、引用の非実行を補助証拠とした。有限境界の関数指紋を関数一般の同一性判定にせず、全実数量化の評価拒否を保つ。旧原点の有理アフィン代数も保存する。',
 '二文全体を再読し、前半の同じφへの説明、後半の前件と四式への帰結、それぞれの参照と作用範囲を確認した。明示した候補による未決定性と設定変更の読みの下で、この全単位を欠落なく記述したと判断する。次の光速度の証明課題はこの単位へ混入させない。',
)

@lru_cache(None)
def record():
    source=source_record();catalog=load_catalog(ROOT,BASIS);s=source['segments'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_origin_constants_claim.py','tests/test_origin_constants_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and len(REASONS)==len(REQUIREMENTS)
    indices=[INDEX,INDEX+1]
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,clauses=clauses,interpretation=LIMITS,limits=['現在段階の候補関数による未決定性と原点仮定の非採用を明示した読みの下でのアシスタントの通読判断。独立査読、史実上の心理状態の復元、一般物理的導出・同義性の自動証明ではない。','u0086以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));r=record()
    assert json.loads(read(REVIEW))==r
    validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inv);pins=r['source_sha256'].copy();pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='unfixed_normalized_function_and_four_origin_constants_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=3,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
