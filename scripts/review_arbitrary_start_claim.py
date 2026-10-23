"""Review the whole sentence connecting possible starts and all spatial values."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_arbitrary_start_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_arbitrary_start_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/arbitrary-start-claim-v1.json'
REVIEW='data/einstein-arbitrary-start-claim-review-v1.json'
CLAUSES=(
 ('Es ist zu bemerken, ',['ei3q','zei'],'同じ可能選択の内容に注意を促す著者の提示を保持する。'),
 ('daß wir statt des Koordinatenursprunges jeden anderen Punkt als Ausgangspunkt des Lichtstrahles hätten wählen können ',['ei3m','ei3n','ei3o','ei3p','skj'],'議論主体が原点以外の任意の地点を同じ光試行の出発点に選べたという可能性を保持する。地点ごとに異なる試行と可能設定を許し、同じ地点・座標・時刻と現在の完全な光往復へ結ぶ。'),
 ('und es gilt deshalb die eben erhaltene Gleichung ',['ei3t','zc','skv','skm','sjy'],'同じ選択可能性を理由に、直前の整理後の偏微分式が成り立つという帰結を保持する。原点の係数を定数として配らず、地点ごとの同じτの偏微分に同じ式を課す。'),
 ('für alle Werte von [M0105].',['skn','skv'],'全ての有効実数値x′,y,zを量化する。同じ時刻パラメータを保持し、有限の記録点だけへ制限しない。'),
)
REASONS=(
 '固定u0058全213文字・175本文文字とM0105を原刊899頁に照合した。注意喚起から末尾の全空間値まで四つの隙間のない範囲で記録し、前後の式との位置関係も確認した。',
 '原点に代わる任意の出発点の選択可能性と、そのため同じ式が全空間値で成り立つという関係を保持する。元設定と候補設定の同じ点・補助座標・K時刻、現在の全時計と完全光往復、移した正近傍と局所微分を合成する。',
 'wirは議論主体zeeとして保持する。候補τは全地点で同じzd4、Vとvも同じ値であり、eben erhaltene Gleichungはu0057のsjyへ参照する。各地点の二偏微分はskm内で取り直し、原点のzd6/zd7を全地点へ固定しない。',
 'Es ist zu bemerkenはzeiによる注意喚起、deshalbは同じ前提ei3pから全空間条件skvへの帰結zcとして著者へ帰属する。二つの主張は同じ第三節・論説と前の式からの順序を保持し、引用内容を実行して処理系の証明へ置き換えない。',
 '実際に全地点で光を発したことや全候補結果の成功を加えない。地点ごとに異なる試行を許す。既出の原点と他の任意の点を合わせた全空間を保持し、時刻は前段のパラメータのまま、横方向条件や具体的なτ解は先取りしない。',
 '空間三原点だけの移動ski、可能な結果の存在skj、移した近傍skl、地点別微分skmと全空間量化sknを変更せず再利用する。正側極限と十分な局所正則性を明示した前段の読みを引き継ぐ。新規原始語は追加しない。',
 '原刊と固定原文、前段の現在の全試行の証拠、空間移動と引数・可能選択・微分候補の対照を根拠とする。有限の値で一般の微分や全実数の量化を証明せず、全地点の試行の実現可能性や一般物理的導出を自動証明したとはしない。',
 '直前の二偏微分式からこの一文、後続のY/Z方向の類似議論まで通読した。明示した思考上の選択可能性と局所正則性の読みの下で、主体・出発点・参照・注意・理由・同じ式と全空間範囲を欠落なく記述したと判断する。',
)

@lru_cache(None)
def record():
    s=source_record()['segments'][0];catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_arbitrary_start_claim.py','tests/test_arbitrary_start_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and len(REASONS)==len(REQUIREMENTS)
    indices=[INDEX,INDEX+1]
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,clauses=clauses,interpretation=LIMITS,limits=['明示した選択可能性・正側極限・十分な局所正則性の読みの下でのアシスタントの通読判断。独立査読や全実数上の物理的導出、同義性の自動証明ではない。','u0059以降の横方向の条件、具体的なτ変換式、二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    r=record();assert json.loads(read(REVIEW))==r
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='possible_arbitrary_starts_and_all_spatial_values_whole_sentence_reviewed',document=FULL,source_units={'einstein-1905:u0058':175},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},all_spatial_trial_choices_exist_proved=False,general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
