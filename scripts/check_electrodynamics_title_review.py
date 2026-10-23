"""Preserve the explicit whole-title judgment and validate its evidence binding."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_electrodynamics_title import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_electrodynamics_title import DOC,SOURCE,INVENTORY,REPORT

REVIEW='data/electrodynamics-title-review-v1.json'
REASONS=(
 '固定u0001の表題全文と全範囲・ハッシュを用い、既存の原刊891頁との照合記録に結ぶ。数式対象はない。誌面内配列番号は単位外と記録し、末尾のセミコロンを新しい命題へ替えない。',
 '電気力学の研究主題eie5と、同じ研究対象を物体運動の場合へ限定するeisa7をeie6で合成した。Zurによる主題についての考察・寄与としての位置付けと表題の役割をeie7で結ぶ。',
 '電荷・電流・電気側と磁気側の場と作用は既存eibf/eibs/eicoの物理的規約、運動はeiagの物体・基準系・全物質点履歴を参照する。論説eirfと前付文脈eirg、著者表示eire、冒頭eir7は既存本文と同じ対象である。',
 '表題eisbcを同じ文書の主題を案内する箇所として提示し、主題を考察する論説というZurの位置付けを保つ。本文の物理的命題、著者表示、他文献の引用へ替えず、後続二箇所への順序を保持する。',
 '主題・運動への限定・位置付け・表題役割を保持する。特定物体の実在や運動、全物体の運動、剛性や等速、Maxwell理論だけへの限定、全体系の完成、成功・新規性・主張の真理を追加しない。静止との比較を禁止しない。',
 '分野名だけに依存せず、電荷輸送・場の生成変化・物質への作用という対象と法則的な研究主題を明示した。物理的同定を型で共有することと各型の関係式を全理論へ公理化することを区別し、主題限定・表題・寄与の基本関係の意味を再読した。',
 '局所検査の主題24場合・提示62場合と未知入力拒否、全引数・四つの引用型、旧主張と判断の不変、原刊照合を別々の根拠にする。有限検査や引用の型検査から物理的実証・全実数評価・原文との自動同義証明を導かない。',
 'Zur、Elektrodynamik、bewegter Körper、表題としての区切りを全体として再読し、明示した主題の読みで未処理項目はないと判断した。本文第一段落との対象・文書の共有も確認した。後続単位の仮定や論証はこの表題の判断へ含めない。',
)

@lru_cache(None)
def review_record():
    catalog=load_catalog(ROOT,BASIS);unit=json.loads(read(INVENTORY))['units'][0]
    formal=json.loads(read(REPORT));validate_hashes(ROOT,formal['source_sha256'])
    assert formal['topic']['cases']==24 and formal['presentation']['cases']==62
    assert formal['structure']['prior_reviews_preserved'] and formal['structure']['source_range']==[0,len(unit['text'])]
    evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC])
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,'scripts/check_electrodynamics_title_review.py','tests/test_electrodynamics_title_review.py',*(p for xs in evidence.values() for p in xs)}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for paths in evidence.values():
        for p in paths:
            if p.endswith('.json'):
                record=json.loads(read(p));validate_hashes(ROOT,record['source_sha256']);merge_pins(pins,record['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=unit['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])],math=[]),selection=selection_binding(catalog,[INDEX]),interpretation=LIMITS,
        limits=['明示した解釈に基づくアシスタントの意味判断。独立査読、意味同値の自動証明、物理法則の実証ではない。','この判断は表題全体を対象とする。後続u0004以降と二作品全体の記述は継続する。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=evidence,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(review_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    assert json.loads(read(REVIEW))==review_record()
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    verified=validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='electrodynamics_title_reviewed_under_explicit_reading',document=FULL,source_unit='einstein-1905:u0001',source_nonblank_characters=verified['source_nonblank_characters'],whole_unit_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=review_record()['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
