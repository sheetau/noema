"""Record the whole closing acknowledgment, dateline and receipt notice readings."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-closing-acknowledgment.noema';CORE='examples/v014/closing-acknowledgment-core.noema'
BASIS='data/closing-acknowledgment-basis-v1.json';ANNOTATIONS='data/closing-acknowledgment-identifiers-v1.json'
SOURCE='data/einstein-closing-acknowledgment-reading-v1.json';REPORT='reports/closing-acknowledgment-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/closing-acknowledgment-v1.md'
REVIEWS=['data/einstein-closing-acknowledgment-u'+str(n).zfill(4)+'-review-v1.json' for n in range(276,279)]
CLAUSES=(
 (
  ('Zum Schlusse bemerke ich, ',['eis5x','uh','ett','etu','etv'],'同じ論説を閉じる付言として、同じ著者が後続の二内容を述べる。物理的な結論や刊行側の注記にせず、三関係の総括に続ける。'),
  ('daß mir beim Arbeiten an dem hier behandelten Probleme ',['eis5v','eis5w','eis5y','sewq','sewx','etr'],'mirは同じ著者、作業は同じ研究、hierは同じ論説の考察対象へ結ぶ。過去の一続きの作業と全支援機会の範囲を保持し、別の研究の援助を流用しない。'),
  ('mein Freund und Kollege M. Besso ',['eis5t','eis5u','eira','eirb','etr','ett'],'同じBessoが著者の友人であり同僚であるという二関係を区別し、名称M. Bessoを既存の同じ人物へ適用する。社会関係だけから援助や共同著作を推論しない。'),
  ('treu zur Seite stand ',['eis5y','sewo','sewp','sewq','sewr','sewt','sewx','etr'],'同じ過去の作業の全ての関連支援機会で、同じ相手が同じ研究を前進させる目的に向けて行為するという継続的支援の読み。機会の成功選別・空範囲を認めず、目的の達成・物理的同席は要求しない。'),
  ('und daß ich demselben manche wertvolle Anregung verdanke.',['sewc','sewd','sewg','sewi','etm','etn','eto','etp','etq','ets','ett'],'undは支援と寄与の認識をともに述べ、demselbenは同じBessoへ戻す。少なくとも二つの異なる思考上の入力について、同じ研究での過去の寄与と使用、現在の肯定的評価を著者が認める。二記録の同一入力を複数に数えず、上限・真理・金銭債務や返礼義務を追加しない。'),
 ),
 (
  ('Bern, ',['eira','eirb','eis6c','ety'],'同じ日付行で名称Bernを同じ都市へ適用し、同じ文書の日付行の場所として表示する。名称と場所を区別し、実際の執筆場所とは断定しない。'),
  ('Juni 1905.',['eis5z','eis6a','eis6d','etw','ety','etz','et2'],'同じ民用暦の1905年と、その年の第6月を月の精度で表示する。謝辞の後の日付行として同じ文書へ結び、日や時刻・刊行日を補わない。'),
 ),
 (
  ('(Eingegangen ',['eis6e','eis6f','et3','et4'],'同じ論説が刊行側の受け手へ届いた受領を、独立した刊行側の注記として報告する。著者の主張・査読採択・印刷とは区別する。'),
  ('30. Juni 1905.)',['eis5z','eis6a','eis6b','eis6h','etx','et3','et4','et5','et6'],'同じ暦の1905年第6月第30日を指定し、受領時点がその日の内にあるとする。日付行と年・月を共有し、その後の同じ文書の注記へ結ぶ。特定時刻やUTCオフセットを追加しない。'),
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_closing_acknowledgment.py','tests/test_closing_acknowledgment_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        e=json.loads(read(path));validate_hashes(ROOT,e['source_sha256']);merge_pins(pins,e['source_sha256'])
    output=[]
    source_reasons=(
      '原刊921頁で三関係の総括と日付行の間にある結語を視認した。Zum Schlusse bemerke ich、過去の研究とhier、mein Freund und Kollege M. Besso、treu zur Seite stand、und、demselben、manche wertvolle Anregung verdankeまで同じ文として保持する。',
      '原刊921頁のBern, Juni 1905.を確認した。名称・月・年の表示であり、第30日を含む次の括弧注記とは別の行である。原文が指定しない日や執筆イベントは補わない。',
      '原刊921頁の括弧注記Eingegangen 30. Juni 1905.を確認した。受領の報告を、直前の日付行や著者の結語から分け、同じ論説の刊行側への受領と第30日の結び付きを保持する。',
    )
    for i,s in enumerate(source['units']):
        selection=[441+i];offset=0;clauses=[]
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text,offset
            assert all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=selection,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
          source_reasons[i],
          '謝辞は継続的支援、個人的交友、職業上の同僚関係、同じ問題の研究、複数の有益な過去の入力への現在の寄与の認識を分けて合成する。日付は年・月・日を役割ごとに結び、月精度の表示と、日内の受領の報告を分ける。',
          '著者rd、Bessoのzrqperson、研究zrqwork、論説eirfを共有し、同じ問題・同じ支援区間・同じ入力の各位置を保持する。M. BessoとBernの名称は対象から区別し、日付二行は同じ暦・年・月を共有するが、受領時点を表示文脈と同一視しない。',
          '結語の付言と著者の主張、文書の日付行、刊行側の受理注記を別の提示として保持する。三関係の総括、謝辞、日付行、受理注記という順序を結び、引用内容を実行して真理や著者の同意を補わない。',
          '忠実な支援を全ての関連機会への目的志向の実行という読み、mancheを二つ以上の異なる入力という読み、日付をグレゴリオ暦の民用日という読みとして明示する。達成・物理的同席・共同著作・返礼義務・入力の真理・特定時刻・執筆完了・採択や刊行日を追加しない。',
          '既存の支援・判断・四個体列・暦アドレス・受領・日内所属を再利用する。新しい社会関係、作業範囲帰属と論述役割は対象と引数を説明した一般的規約であり、特定の全文を一基本記号へ隠さない。過去の寄与と現在の評価はetmへ明示的に合成し、未知の入力を偽として補わない。',
          '局所検査で、支援の欠落・目的の取り違え・空範囲・別の研究、入力の重複・順序の交換・現在と過去・候補と現実の差を区別する。暦の役割と月精度、日内の異なる時点、別の受け手・文書・日を対照し、引用の非実行と旧441主張・意味規約・判断の保存を確認する。検査成功を全文意味判断に自動変換しない。',
          '対象単位を前後と合わせて再読し、関係・照応・時間・複数性・評価・提示の役割、名称と日付の精度が揃うと判断した。明示した解釈の下で各単位を欠落なく記述できたというアシスタントの意味判断であり、独立査読・歴史的真理・同義性の自動証明ではない。',
        )
        assert len(reasons)==len(REQUIREMENTS)
        output.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=basis['limitations'],limits=['明示した解釈の下でのアシスタントによる全文判断。独立査読、歴史的事実又は原文同義性の自動証明ではない。','u0239・u0265・u0275は別途判断する。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return output

def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,r in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(r,ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    rows=records();catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);pins=dict(rows[0]['source_sha256'])
    for path,r in zip(REVIEWS,rows):
        assert json.loads(read(path))==r;validate_review(ROOT,path,'einstein-1905',active,catalog,inventory);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='closing_acknowledgment_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in rows},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':3},semantic_equivalence_automatically_proved=False,source_sha256=pins)
