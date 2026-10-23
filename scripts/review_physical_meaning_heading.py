"""Record the whole reading of Einstein's fourth section heading."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_physical_meaning_heading import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_physical_meaning_heading import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/physical-meaning-heading-v1.json';REVIEW='data/einstein-physical-meaning-heading-review-v1.json'
CLAUSES=(
 ('§ 4. ',['ejew','eihq','eisn5'],'第一部に属する深さ2・表示番号4の第四節の見出し。'),
 ('Physikalische Bedeutung der erhaltenen Gleichungen, ',['ejeu','ejev','ssn','eiyz','eiy2'],'先に得た同じ現在四式を、物理的な記録との参照を保って意味の考察の対象とする。'),
 ('bewegte starre Körper ',['ejes','eigy','eiag'],'同伴側で全物質点の剛性を保ち、比較側で動く同じ物体についての主題。'),
 ('und bewegte Uhren ',['ejet','ejer','ca'],'時計の代表配置が動く場合も、剛体と並ぶ第二の対象に含む。'),
 ('betreffend.',['ejev','ejew','zhr'],'この二種類の対象に関する方程式の物理的意味を、同じ第四節の主題として案内する。'),
)
REASONS=(
 '固定u0109の全108文字・非空白95文字を原刊903頁の見出し二行へ照合した。§4、物理的意味、得られた方程式、動く剛体と時計、betreffendと句点を通読した。',
 'ejeuが現在のK/k適格記録範囲と先行の最終四式ssnを結び、ejevがその物理的意味を二種類の対象ejes/ejetについて考察する主題を示す。ejewが主題と節番号・階層・親区分を結ぶ。',
 'erhaltenen Gleichungenは第三節末の同じ四座標変換である。K/k、単位、対象期間、物体同一性は前段の規約を保つ。第四節は第一部に直接属し、u0109–u0128の区分と見出し位置zhtを区別する。',
 '見出しは区分の論述主題を案内するものとしてeihq/eisdwで保持する。式の真理、球の収縮率、時計遅れを著者がこの見出しで断言したというメッセージに変えない。',
 '剛体の全物質点間距離と運動の完全履歴を保持し、時計は代表配置の運動として内部の針の運動から分ける。二対象の片方を落とさず、特定軸・速度・収縮率・同期や校正の条件は見出しに追加しない。',
 '既存の物体・全物質点・校正計量・世界線・時計型・方程式・研究の提示の規約を合成する。追加の原始記号は第四節の区分個体だけであり、見出しの内容を未説明の一記号や原語の綴りにしない。',
 '全履歴への引数接続、三方向それぞれの運動と元へ戻る配置、前後時刻・区間外の拒否、時計と物体の違い、二対象の引用と節階層を有限対照で検査した。全実数の存在量化は有限評価の拒否を保持する。原刊通読と有限検査を区別する。',
 '先行する四式とβから見出し、後続の球の設定まで再読した。同じ四式の物理的意味を動く剛体と時計について扱う主題という読みで、参照・二対象・節構造・提示の役割を欠落なく保持したと判断する。球の本文と著者脚注の完成はこの判断から導かない。',
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_physical_meaning_heading.py','tests/test_physical_meaning_heading_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    s=source_record()['segments'][0];clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and len(REASONS)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['同じ二系での剛体と時計の運動を対象に、既出四式の物理的意味を考察する見出しという読みの下でのアシスタントの通読判断。独立査読や意味同値の自動証明ではない。','u0110以降及び著者脚注u0281と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    pins=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())}
    return dict(status='fourth_physical_meaning_heading_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
