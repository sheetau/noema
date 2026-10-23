"""Record complete source-unit judgments for the two opening headings."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.check_einstein_principles_paragraph import calls
from scripts.compose_kinematics_headings import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/einstein-kinematics-headings-source-reading-v1.json'
DOC='docs/kinematics-headings-v1.md';REPORT='reports/kinematics-headings-v1.json'
REVIEWS=('data/einstein-kinematics-heading-review-v1.json','data/einstein-simultaneity-heading-review-v1.json')
REASONS=(
 (
  '固定u0006の全見出しI. Kinematischer Teil.を原刊892頁と照合した。ローマ数字I、句点と語句を保持し、数式・脚注はない。',
  '第一という部番号、論説の部という階層、運動学という主題を記述する。原文にない物理的な命題、実例、全理論の完成は追加しない。',
  '運動学の主題eihnを前段落と同じ剛体の型eigy及び研究領域eisdhへ結ぶ。区分eisdxと見出しeisdzを区別し、親は同じ論説eirfである。',
  '後続の第一部の内容を案内する見出しの役割を保持する。導入第三段落の後に置き、部見出しを本文中の物理命題の発話や文書全体の表題へ替えない。',
  '部番号と階層深さを分け、番号Iを物理量へ替えない。後続範囲を第一節だけに縮めず、第二部の直前までとする。書体・配置は照合に使うが意味上の追加条件としない。',
  '運動学を物体の位置・時刻・配置の変化を扱う研究として記述し、力の原因の理論とは区別する。番号付き区分、親子関係、主題の案内の意味規約を確認した。',
  '原刊照合、主題と見出しの局所検査、既存の剛性・時計の定義、現行本文と依存意味規約を固定する。主題の引用を物理的設定の実証に変えず、テスト通過だけで意味判断を代用しない。',
  '部番号、区分、運動学という主題と見出しの提示を一つの単位として通読した。明示した読みの下で欠落はないと判断する。第一部に含まれる本文各単位の完成はこの判断に含めない。',
 ),
 (
  '固定u0007の全見出し§ 1. Definition der Gleichzeitigkeit.を原刊892頁と照合した。節番号1、§と句点及び全語句を保持し、数式・脚注はない。',
  '第一という節番号、第一部に属する節という階層、同時性の意味と適用基準を定める仕事という主題を合成する。単なる同時な事例の主張へ替えない。',
  '節区分eisdyを同じ第一部eisdxへ結び、見出しeisd2と区別する。同時性の主題eihoは同じ系・単位・文脈で一意に付与された時刻の一致eihmを参照する。',
  'これから同時性を定義する第一節を案内する見出しとして記述する。第一部見出しの後の順序を保持し、定義が既に完成したという主張や具体的な同時性の断言にしない。',
  '同時性の候補値だけでなく両出来事への有効で一意な時刻付与を保持する。未付与を非同時にせず、全系での絶対的同時性、同所性、異なる二出来事という余計な条件を加えない。',
  '局所時計・共通参照時計・同期と校正、時刻付与の有効性と一意性、値の一致、概念の意味と適用基準を定める仕事を区別する。見出し全体の意味を原語の名札一つへ隠さない。',
  '原刊照合、時刻付与の接続と全実数評価の拒否、主題合成、番号・親区分・順序の検査及び現行本文を固定した。有限標本を全物理設定や全時刻の一意性の証明へ替えない。',
  '節番号、同時性の定義という複合主題、区分と見出しの提示を通読した。明示した読みの下で欠落はないと判断する。第二節直前までという案内範囲は、そこに含まれる本文の意味確認済みを意味しない。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));source=json.loads(read(SOURCE));validate_hashes(ROOT,source['source_sha256'])
    ds={d['name']:d for d in catalog.document['declarations']}
    evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC])
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,REPORT,DOC,'scripts/review_kinematics_headings.py','tests/test_kinematics_headings_review.py','scripts/check_einstein_principles_paragraph.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT):
        record=json.loads(read(p));validate_hashes(ROOT,record['source_sha256']);merge_pins(pins,record['source_sha256'])
    result=[]
    for which,(unit_index,statement,name,topic) in enumerate(((5,219,'eihr','eihn'),(6,220,'eihs','eihp'))):
        unit=inv['units'][unit_index];collation=source['source_units'][which]
        assert collation['unit']==unit['id'] and collation['unit_sha256']==unit['text_sha256'] and collation['text']==unit['text']
        assert unit['kind']=='heading' and not unit['math_ids']
        cs=list(calls(ds[name]['body']));assert not any(c['symbol']=='eir3' for c in cs)
        heading=next(c for c in cs if c['symbol']=='eihq')
        assert heading['arguments'][6]==dict(kind='quote',body=dict(kind='function_ref',symbol=topic))
        assert catalog.document['statements'][statement]['body']==dict(kind='call',symbol=name,arguments=[])
        result.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=unit['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
            source=dict(inventory=INVENTORY,unit_sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])],math=[]),selection=selection_binding(catalog,[statement]),source_order_statements=[statement],interpretation=LIMITS,
            limits=['原文の意味と提示の役割を照合したアシスタントの判断であり、独立査読や同義性の自動証明ではない。','この見出しが案内する本文各単位の意味確認、物理的な定義・法則の実証、二作品全体の完成は別である。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[which])],evidence=evidence,source_sha256=pins.copy()))
    return result

def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,record in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(record,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));verified=[]
    for path,record in zip(REVIEWS,records()):
        assert json.loads(read(path))==record
        v=validate_review(ROOT,path,'einstein-1905',active,catalog,inv)
        verified.append(dict(unit=record['unit'],nonblank_characters=v['source_nonblank_characters']))
    return dict(status='two_numbered_headings_reviewed_under_explicit_reading',document=FULL,units=verified,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=records()[0]['source_sha256']|{p:digest((ROOT/p).read_bytes()) for p in REVIEWS})
