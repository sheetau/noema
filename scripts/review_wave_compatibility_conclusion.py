"""Whole reading of the moving wave and the stated compatibility conclusion."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_wave_compatibility_conclusion import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_wave_compatibility_conclusion import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/wave-compatibility-conclusion-v1.json'
REVIEW='data/einstein-wave-compatibility-conclusion-u0091-review-v1.json'
CLAUSES=(
 ('Die betrachtete Welle ist ',['ejan','zfu','zfv'],'直前から検討している同じ波と放出を指す。'),
 ('also ',['ejao','ejaq','zc'],'先行の同じ設定と座標変換による式からの帰結提示を保持する。'),
 ('auch im bewegten System betrachtet eine Kugelwelle von der Ausbreitungsgeschwindigkeit [M0147]. ',['ejal','ejam','ejan','ei75','ei73','ei44'],'Kの既出波面と同じ波がkでも、全構成光線・全適用区間でVの伝播を持つ球面波であると述べる。'),
 ('Hiermit ist gezeigt, ',['ejap','ejar','zc','ui'],'この同じ球面波の議論を理由とし、同じ箇所の内容を著者が示されたと位置付ける。'),
 ('daß unsere beiden Grundprinzipien miteinander vereinbar sind.',['eif5','eifj','eify','eiscj','sqh','ejar'],'既出の二原理が、同じ物理的解釈の許容設定で共に成立し得るという両立性を結論内容とする。'),
)
REASONS=(
 '固定u0091全209文字・非空白本文177文字とM0147を原刊901頁へ照合した。直前のk二乗式、同じ波の結論、Hiermitから二原理の両立性まで二文全体を通読し、後続の未知φを決める課題との境界を確認した。',
 '検討中の同じ波、先行式からの帰結also、Kに加えてkでもというauch、同じVによる伝播と球面波面、議論を指すHiermit、示されたという位置付け、既出の二原理の相互の両立性を全て保持する。全構成光線と途中を含む全適用区間、全対象出来事の波面を一つの成功例へ縮めない。',
 '波は同じzfu、放出は同じzfv、kは既出zbm、Vは同じtc、物理設定はzb6に固定する。M0147のVを相対速度V−vへ置き換えない。unsere beiden Grundprinzipienは現在のeifjとeifyであり、旧草案の部分内容や一方だけを結論対象にしない。',
 '第一文は同じ設定と変換結果ejaoからejanへの帰結提示zc、第二文はその議論ejapからeif5への帰結とuiによる同じ箇所の証明済みの位置付けとした。二つの断定メッセージを同じ著者・論説・第三節へ帰属し、直前のzgeからzgf、zggへ進む順序を保持する。',
 '検討中の波の伝播をkの無関係な全光へ広げない。二乗式だけから正時刻・全到来一致・全区間速度を導かず、正のφやφ=1を著者の発話へ足して推論を修理しない。示されたという断定を未証明課題へ弱めず、処理系の証明認定にも変えない。以前の証明未提示の段階は保存する。',
 '伝播は既存の現在の時計・座標・幾何学的光路長ei44と同じ放出のei73、球面性は既存ei75の過不足ない未来側波面として合成する。両立性は同じ意味の許容設定eiscjと共充足sqh、証明済みの帰属は既存uiを使う。未説明の原文ラベルや文専用の新原始語に置き換えない。',
 '原刊・固定本文・意味規約の再読を根拠とし、全構成光線・全波区間の同じ放出と現在V、途中区間と他波、波面と伝播、両系の同じ波、同じ許容設定での二原理、帰結と証明済みの同じ箇所への帰属を有限対照した。元の物理的推論の妥当性や意味同値の自動証明を検査結果から認定しない。',
 '直前の式から二文と後続課題の境界まで再読した。現在の全対象範囲の幾何学的波面、検討中の波全体の現在伝播、同じ許容設定での両立性、著者による帰結と証明済みの提示という明示した読みの下で、関係・参照・範囲・提示を欠落なく記述したと判断する。',
)


@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'docs/semantic-review-v1.md','scripts/review_wave_compatibility_conclusion.py','tests/test_wave_compatibility_conclusion_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    s=source_record()['segments'][0];clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and len(REASONS)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX,INDEX+1]),source_order_statements=[INDEX,INDEX+1],clauses=clauses,interpretation=LIMITS,limits=['現在の測定規約と幾何学的な波面、同じ物理的意味の下での両立性、著者による帰結と証明済みの提示についてのアシスタントの通読判断。独立査読、一般物理的導出や意味同値の自動証明ではない。','原著者の推論の妥当性を翻訳の完成条件とせず、補足前提によって原文の断定を別の条件付き主張へ変更しない。','u0092以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));r=record()
    assert json.loads(read(REVIEW))==r
    validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inv);pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='same_wave_and_compatibility_conclusion_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
