"""Audit delivery evidence; keep semantic judgments distinct from test results."""
from functools import lru_cache
import json
from pathlib import Path
import re

from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews, merge_pins
from noema.semantic_reviews import digest, require, validate_hashes

ROOT=Path(__file__).resolve().parents[1]
INDEX='data/semantic-review-index-v456.json'
PROGRESS='reports/written-progress-v432.json'
ASSEMBLY='reports/reviewed-works-assembly-v1.json'
REGRESSION='reports/language-delivery-regression-v1.json'
CUSTOM='reports/local-reciprocity-custom-v1.json'
DOC='docs/two-work-completion-v1.md'
SPECS=['docs/spec-v08.md','docs/spec-v09.md','docs/spec-v010.md','docs/spec-v011.md',
       'docs/spec-v012.md','docs/spec-v013.md','docs/spec-v014.md',
       'docs/ranked-quotation-v1.md','docs/quotation-construction-v1.md']

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))

def prose_characters(unit):
    # [M0001] is an inventory reference, not seven characters of author prose.
    # Math contents are independently pinned and reviewed by validate_review.
    markers=re.findall(r'\[(M\d{4})\]',unit['text'])
    require(set(markers)==set(unit.get('math_ids',[])), 'Math marker inventory differs')
    prose=re.sub(r'\[M\d{4}\]','',unit['text'])
    return len(re.sub(r'\s','',prose))

@lru_cache(None)
def evidence_checks():
    index=read(INDEX)
    reviews=load_reviews(ROOT,INDEX)
    pins=dict(reviews['source_sha256'])
    reports={p:read(p) for p in (PROGRESS,ASSEMBLY,REGRESSION,CUSTOM)}
    for p,r in reports.items():
        validate_hashes(ROOT,r['source_sha256'])
        merge_pins(pins,r['source_sha256'])
        pins[p]=digest((ROOT/p).read_bytes())
    require(reports[REGRESSION]['passed']==115 and reports[REGRESSION]['failed']==0,
            'Missing language regression evidence')
    require(reports[CUSTOM]['cases']==33 and not reports[CUSTOM]['language_syntax_added'],
            'Missing reusable cultural-convention example')
    works={}
    for work,active in index['works'].items():
        inventory=read(active['source_inventory'])
        units=[u for u in inventory['units'] if u['kind']!='editorial']
        current=load_catalog(ROOT,active['meaning_basis'])
        merge_pins(pins,current.source_sha256)
        by_unit={r['unit']:r for r in reviews['works'][work]}
        require(len(by_unit)==len(units) and set(by_unit)=={u['id'] for u in units},
                'Author unit is missing or repeated')
        require({n for b in active['reviews'] for n in b['statements']}==set(range(len(current.document['statements']))),
                'Manuscript includes an unreviewed statement')
        for binding in active['reviews']:
            review=read(binding['review'])
            require(review['unresolved']==[] and review['interpretation'] and review['limits'],
                    'Missing explicit reading or unresolved source item')
            require(all(r['decision']=='satisfied' for r in review['requirements']),
                    'A semantic requirement is unfulfilled')
        text=(ROOT/active['document']).read_text(encoding='utf-8')
        require(re.fullmatch(r'[a-z2-7\s\[\]:.]+',text) is not None,
                'Unexpected literal or external payload in Noema text')
        audit=current.audit()
        require(audit['signature_and_documentation_coverage'], 'Undocumented declaration')
        summary=reports[ASSEMBLY]['works'][work]
        require(summary['units']==len(units) and summary['statements']==len(current.document['statements']) and
                summary['all_meanings_and_original_judgments_preserved'] and
                summary['compact_full_and_native_alphabet_roundtrips'], 'Assembly evidence differs')
        require(len(reports[PROGRESS]['semantic_reviews']['works'][work])==len(units),
                'Progress aggregation differs')
        works[work]=dict(document=active['document'],meaning_basis=active['meaning_basis'],
                        identifier_annotations=active['identifier_annotations'],
                        reviewed_units=len(units),author_units=len(units),
                        nonblank_text_characters=sum(prose_characters(u) for u in units),
                        math_elements=len({m for u in units for m in u.get('math_ids',[])}),
                        statements=len(current.document['statements']),
                        primitives=audit['primitive_count'],definitions=audit['definition_count'],
                        unreviewed_statements=0,unresolved_source_items=0,
                        natural_language_literal_substitution=False)
    require({w:r['reviewed_units'] for w,r in works.items()}=={'kant-1784':20,'einstein-1905':282},
            'Unexpected final source inventory')
    return works,pins

def build_report():
    works,pins=evidence_checks();pins=dict(pins)
    paths={DOC,'scripts/audit_two_work_completion.py','tests/test_two_work_completion.py',
           'docs/language-completion.md','docs/semantic-review-v1.md',
           'docs/reviewed-works-assembly-v1.md','data/reviewed-works-assembly-v1.json',
           'docs/local-reciprocity-custom-v1.md',*SPECS}
    for path in paths:pins[path]=digest((ROOT/path).read_bytes())
    reasons=[
        ('language_and_meanings','版0.8〜0.14の仕様と0.15/0.16の明示的な試作仕様、現行二作品の版管理された全宣言の意味規約を照合した。未説明の記号名を原語の代用にする方式ではなく、基本関係の規約と合成定義を区別する。'),
        ('model_free_processing','現行二作品の長短形式・固有文字の往復、解析・型・正規化と旧版互換・明示的版移行の115回帰検査を確認した。0.16の評価層の実行時制約と無限領域の非評価を明記し、一般的な停止性や無矛盾性を主張しない。'),
        ('two_complete_manuscripts','全原文単位に対する判断済み主張を二つの自己完結したNoema文書へ収録した。全宣言と推移的依存意味を保持し、不要な旧部分草案の主張は元の累積稿で保存する。自然言語本文の引用文字列や外部リンクで内容を代用していない。'),
        ('all_source_units','著者本文の302単位全てについて、原文の固定ハッシュ、現在の文番号、原判断への参照を保存した。数式・著者注・見出しを含む単位全体の判断であり、後世の編集要素は著者単位と分ける。原刊との相違と訂正は元証拠に固定する。'),
        ('semantic_judgments','元の302判断の全要求・根拠・明示した解釈・限界を保持し、現行の文、依存定義と意味規約、識別表記との一致を検証した。未解決の原文項目はないというアシスタント判断を引き継ぐ。テスト通過を新しい意味判断に転用せず、独立査読や自動同義証明とは区別する。'),
        ('reuse_beyond_the_works','別分野の条件付き呼びかけ・人物別の記述構成に加え、架空の共同体の局所的な返礼作法を既存構文で合成した。身体行為、共同体の義務、謝意の表示規約、実際の実行を33対照で区別し、32文字の固有文字へも往復できる。'),
    ]
    return dict(status='two_works_completed_under_explicit_readings',
                objective='二作品を、明示した解釈の下で欠落なく記述する',
                reviewer='assistant_review',review_index=INDEX,works=works,
                completion_criteria=[dict(id=k,decision='satisfied_under_stated_scope',reason=v) for k,v in reasons],
                unresolved_completion_items=[],
                limits=['原文とNoemaの意味判断はアシスタントによるもの。独立査読や同義性の自動証明ではない。',
                        '明示した解釈と基本関係の意味規約の下での完成。原著者の理論や歴史的主張の真理を証明しない。',
                        '二作品の完成はあらゆる人間の意味を網羅する証明ではない。未知の内容は今後も説明と定義によって拡張する。',
                        '0.15/0.16は明示的に選ぶ仕様。高階関数の一般的な効果・停止性の静的証明と無限領域の万能な実行器は提供しない。',
                        '文化固有の規約の例は架空の共同体についての局所定義であり、現実の文化の全語義を説明したと主張しない。',
                        '自動翻訳器、学習モデル比較、独立した人間による査読は本目標の対象外として保留する。'],
                semantic_equivalence_automatically_proved=False,
                source_sha256=dict(sorted(pins.items())))
