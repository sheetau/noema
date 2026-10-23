"""Bind a holistic four-sentence judgment to the complete final paragraph."""
from functools import lru_cache
import json
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import load_reviews,merge_pins
from scripts.check_collective_return_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,INDEX,catalog,read,unit

DOC='docs/tenth-paragraph-v1.md';REVIEW='data/tenth-paragraph-review-v1.json'
STEMS=('qualified-speech-sentence','whole-view-sentence','civic-spirit-sentence','collective-return-sentence')
READINGS=tuple('data/'+n+'-reading-v1.json' for n in STEMS)
REPORTS=tuple('reports/'+n+'-v1.json' for n in STEMS)
SPANS=((0,303),(304,466),(467,715),(716,1174));INDICES=(119,120,121,122)
REASONS=(
 '固定u0017全1174文字・992非空白文字を四文と保存済み原刊493–494頁の照合で確認した。文間空白三文字を除く全位置を重複なく覆い、注標識二文字も第四文に含む。単位に数式はない。',
 '第一文の人物必要条件と引用された許可・服従要求、第二文の局所的な観察と全体考察への条件、第三文の同じ二制度の比較、第四文の全事例への条件・二終点・因果・関係節を保持する。各文の否定・全称・存在・程度・時間・様相の範囲を区別した。',
 '同じ話者と引用方針、同じ人間的推移、同じ民衆と二制度、同じ低い側の覆い、芽と二性向、原因側と影響先の人口、同じ政府と処遇対象を照合した。第四文のdieser/dieses/ihr selbst/seinerとnunを同じ内容・人物・後件時点へ結ぶ。',
 '四文それぞれの著者帰属を保持し、対照・提示される観察・全体との類比・見かけと現実・譲歩的対照・説明の継続・条件の比喩・括弧の補足・追加と強調を区別した。提示から引用内容の現実の真理は導かない。',
 '第一文の発言可能者の現実の存在、全体考察者の実在、見かけの利益の真理、第三文の発展の実現、第四文前件の実在を余計に足さない。集団能力増加を全員の単調増加にせず、政府の判断を実際の利益・規範採用・履行へ昇格させない。注本文も重複加算しない。',
 '人物・国家体制・軍隊・平穏・許可と服従、人間的推移と反期待、市民的自由と精神的課題機会、二性向・自然と芽・硬さと世話、心的傾向・能力・政府原則・尊厳・利益判断は意味規約と具体的な合成へ結ぶ。未説明の原語や残余関数を完成の代用にしない。',
 '四文別の通読判断と検査、全ての依存定義・意味規約、原刊照合と既存著者注の根拠を固定した。既存19全単位判断の依存一致も確認する。有限検査の範囲を公開し、通過を自然言語との同義性の自動証明に読み替えない。',
 '人物・軍隊と公的議論の政治的対比から、人間的推移の反期待的な様相、自由の大小と発展機会の逆説、同じ低い制度下で育つ二性向の後続作用へ進む四文全体を再読した。採用した解釈の下で未処理の条件・照応・提示・注参照はない。',
)

def review_record():
    c=catalog();u=unit();readings=[read(p) for p in READINGS];positions=set()
    for r,span,index in zip(readings,SPANS,INDICES):
        assert r['whole_sentence_semantically_verified'] and not r['unresolved']
        assert r['source']['unit_sha256']==u['text_sha256'] and r['source']['range']==list(span)
        assert r['source']['text']==u['text'][span[0]:span[1]]
        assert r['selection']==selection_binding(c,[index])
        assert not positions.intersection(range(*span));positions.update(range(*span))
    assert all(i in positions or ch.isspace() for i,ch in enumerate(u['text']))
    assert sum(not ch.isspace() for ch in u['text'])==sum(r['newly_reviewed_sentence_characters'] for r in readings)==992
    evidence=dict(source_reading=[SOURCE,*READINGS],formal_checks=list(REPORTS),semantic_reading=[DOC,*('docs/'+n+'-v1.md' for n in STEMS)])
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,INDEX,'scripts/check_tenth_paragraph.py',*(p for xs in evidence.values() for p in xs)}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,c.source_sha256)
    for paths in evidence.values():
        for p in paths:
            if p.endswith('.json'):
                record=read(p);validate_hashes(ROOT,record['source_sha256']);merge_pins(pins,record['source_sha256'])
    prior=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(prior)==19
    for row in prior:assert row['selection']==selection_binding(c,[s['index'] for s in row['selection']['statements']])
    return dict(schema_version='noema-semantic-review-1',work='kant-1784',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',
      document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
      source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[]),
      selection=selection_binding(c,list(INDICES)),
      interpretation=[item for r in readings for item in r['interpretation']]+['文別記録で後続文又は段落全体を未完とした記述は、その記録時の進捗であり、本段落の今回の未解決点ではない。四文は同じ論述の順序と照応を保って統合されている。'],
      limits=['各依存群の公開された範囲・尺度・因果モデル・価値基準を用いる明示解釈に基づくアシスタント判断。独立査読、自動同義証明、哲学や歴史の真理の実証ではない。','アインシュタイン論文の全文記述と意味確認は未完。二作品の完成を言語の万能性の証明とはしない。'],
      unresolved=[],requirements=[dict(id=name,decision='satisfied',reason=reason) for name,reason in zip(REQUIREMENTS,REASONS,strict=True)],evidence=evidence,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/REVIEW,encoded(review_record()))
@lru_cache(None)
def build_report():
    assert read(REVIEW)==review_record()
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    verified=validate_review(ROOT,REVIEW,'kant-1784',active,catalog(),read(INVENTORY))
    return dict(status='tenth_paragraph_holistically_reviewed_under_explicit_reading',document=FULL,
      source_unit=unit()['id'],sentence_ranges=SPANS,statements=list(INDICES),source_nonblank_characters=verified['source_nonblank_characters'],
      preserved_whole_unit_reviews=19,whole_unit_semantically_verified=True,verified_full_units={'kant-1784':1,'einstein-1905':0},
      semantic_equivalence_automatically_proved=False,
      source_sha256=read(REVIEW)['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
