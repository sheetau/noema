"""Read the second section heading and its paired-principle introduction."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_second_section_opening import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/second-section-opening-v1.md'
SOURCE='data/einstein-second-section-opening-source-reading-v1.json';REPORT='reports/second-section-opening-v1.json'
REVIEWS=('data/einstein-second-section-heading-review-v1.json','data/einstein-two-principle-introduction-review-v1.json')
PRIORS=('data/einstein-simultaneity-heading-review-v1.json','data/einstein-principles-paragraph-review-v1.json','data/einstein-rest-system-time-review-v1.json')
REASONS=(
 (
  '固定u0023の全48文字・40本文文字を原刊895頁の§ 2. Über die Relativität von Längen und Zeiten.と照合した。数式と脚注はない。',
  '第二という節番号、第一部の下位の節という階層、長さと時間の両方の相対性という主題を合成する。長さだけ・時間だけの見出しへ縮めない。',
  '長さを二地点間距離thへ、時間を出来事への時刻付与zbeと有効で一意な付与に基づく同時性eihmへ結ぶ。区分eiskzと見出しeisk2を分け、同じ第一部eisdxを親とする。',
  '見出しの非断言的な主題案内を既存eihq/eisdwで保持する。前節の時間命名箇所の後に第二節を開き、個別の物理的結論を述べる発話へ替えない。',
  '相対性を基準系と測定規約への量の依存という主題として読む。全系対・全方向での不一致、収縮や遅れの公式、特定の測定の成功は補わない。支配範囲は第三節直前までとする。',
  '空間的長さの対象、時刻・間隔・同時性の対象、系への依存を調べる研究主題、階層・表示番号・区分を分けて構成する。題名一つを未説明の原始命題へ置き換えない。',
  '原刊照合と、三つの主題関係・全引数位置・階層・番号・順序・引用非実行の検査を区別する。既存時刻規約を引用し、全実数や全物理状況を有限標本で証明しない。',
  '節番号、両主題、その相対性、節を案内する見出しの役割を全体として通読した。明示した読みの下で未処理項目はない。後続本文の完成はこの判断に含めない。',
 ),
 (
  '固定u0024の全182文字・161本文文字を原刊895頁のDie folgenden Überlegungenからdefinierenまで照合した。行末の分綴を別の語へ替えず、数式と脚注はない。',
  '同じ後続論述の範囲で相対性原理と光速度一定の原理をともに前提として用いること、その両原理を以下で定義する予告を結ぶ。両方の採用と両方の定義先を要求する。',
  '二呼称を既出の同じ内容eifj/eifyへ結び、welche beiden Prinzipienも同じ二内容を指す。後続範囲wvは現在のwuの後の本文、定義先は順にvkとwtである。',
  'stützen sichはこの議論における仮定採用、wir definieren folgendermaßenは直後の定式化への予告として保持する。単なる語の一覧や既に定義・実証を終えた事実へ替えない。',
  '一方だけの前提、二原理以外の定義・数学の排除、二原理の必要最小性、全結論の導出済み、原理の現実の真理を追加しない。旧部分草案saw/sbdの同値をこの文から認定しない。',
  '仮定採用ug、呼称内容対応eisch、後続本文範囲eisciを再利用し、一般的な定義予告eisk5を同じ内容と各参照先に適用する。導入一文全体を新たな原始関係へ隠さない。',
  '固定原文・二原理の先行判断・現在の意味規約と、採用・呼称・定義予告の全位置の取り違え検査を保存する。引用した物理法則をこの導入で実行せず、未知入力を偽で補わない。',
  '後続考察への両原理の採用、同じ二内容の照応、第一・第二の定式化への予告を一文として通読した。明示した読みの下で欠落はない。定義本文u0025以降の読解・構成・比較は残る。',
 ),
)


def source_record():
    inv=json.loads(read(INVENTORY));units=inv['units'][22:24]
    assert [len(u['text']) for u in units]==[48,182]
    assert [sum(not c.isspace() for c in u['text']) for u in units]==[40,161]
    assert all(not u['math_ids'] for u in units)
    assert inv['units'][41]['kind']=='heading' and inv['units'][41]['text'].startswith('§ 3.')
    paths=[INVENTORY,DOC,'scripts/review_second_section_opening.py','artifacts/einstein-rest-time-v1/page-895.jpg','artifacts/einstein-rest-time-v1/page-895.html','artifacts/einstein-rest-time-v1/retrieval.json']
    return dict(version='einstein-second-section-opening-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['895'],images=[paths[3]],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=sum(not c.isspace() for c in u['text']),math=[]) for u in units],division=dict(level=2,ordinal=2,parent='einstein-1905:u0006',first='einstein-1905:u0023',last='einstein-1905:u0041',next_boundary='einstein-1905:u0042'),observations=['895頁の前節の命名文直後に第二節見出しがあり、その直下に二原理への依拠と定義予告の一文がある。','番号1と2の定義が順に続く。主題・根拠・定義予告は別の論述上の役割として読む。','分綴Relativitäts-prinzipとLichtgeschwindig-keitは固定転記の一語として照合する。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));source=json.loads(read(SOURCE));assert source==source_record()
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,REPORT,DOC,*PRIORS,'scripts/review_second_section_opening.py','tests/test_second_section_opening_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT):
        rec=json.loads(read(p));validate_hashes(ROOT,rec['source_sha256']);merge_pins(pins,rec['source_sha256'])
    result=[]
    for which,index in enumerate(INDICES):
        u=inv['units'][22+which]
        result.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[]),selection=selection_binding(catalog,[index]),source_order_statements=[index],interpretation=LIMITS,limits=['明示した読みの下でのアシスタントの通読判断。独立査読や同義性の自動証明ではない。','後続u0025以降の全単位記述・判断と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[which])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),source_sha256=pins.copy()))
    return result


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,record in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(record,ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));verified=[]
    for path,record in zip(REVIEWS,records()):
        assert json.loads(read(path))==record
        result=validate_review(ROOT,path,'einstein-1905',active,catalog,inv)
        verified.append(dict(unit=record['unit'],nonblank_characters=result['source_nonblank_characters']))
    return dict(status='second_section_heading_and_principle_introduction_reviewed',document=FULL,units=verified,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=records()[0]['source_sha256']|{p:digest((ROOT/p).read_bytes()) for p in REVIEWS})
