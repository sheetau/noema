"""Bind separately authored readings of the fifth sentence and fourth paragraph."""
from functools import lru_cache
import json
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes, REQUIREMENTS
from scripts.check_revolution_presentation import ROOT, FULL, BASIS, ANNOTATIONS, catalog, INDEX, INVENTORY
from scripts.check_political_withdrawal import REVIEWS as SENTENCES

AUDIT = 'data/public-fifth-sentence-reading-v1.json'
PARAGRAPH = 'data/fourth-paragraph-reading-v1.json'
REVIEW = 'data/fourth-paragraph-review-v1.json'
REPORT = 'reports/fourth-paragraph-v1.json'
DOC = 'docs/fourth-paragraph-v1.md'
IMAGES = ['artifacts/future-dissemination-reading-v1/page-483.jpg',
          'artifacts/public-reversal-reading-v1/page-484.jpg']
SELECTION = [55, 56, 58, 59, 60, 61, 62]
PRIOR = ['reports/' + n + '-v1.json' for n in (
    'public-first-sentence', 'public-second-sentence', 'public-third-sentence', 'public-slow-attainment',
    'political-withdrawal', 'revolution-routes', 'thinking-reform', 'public-revolution',
    'prejudice-guidance', 'prejudice-forecast', 'leading-band', 'revolution-presentation')]
LIMITS = [
    '公衆は公的議論の宛先となる読者集団、大衆は同じ段落の文脈上の集団、政治的共同体は革命の対象となる秩序の共同体として区別する。各文の同じ範囲・全成員を保ち、後見人の各部分集団を全員同じ人々とはしない。',
    '集団の啓蒙・政治的離脱・思考様式の改革・偏見の広がりは、固定した対象列と結果別の文脈基準による。全員、固定した過半数、特定の国家の歴史的事件を補わない。',
    '自由は公的理性使用についての規範的な許可として読み、自己啓蒙のほぼ必然はその維持を条件とする。全候補での無条件の成功保証や唯一原因性は主張しない。',
    '革命は旧政治秩序の根幹を変えようとする集団的対抗とし、成功・流血を必須にしない。政治的離脱は同じ当事者が専制と欲深い圧迫への服属を終えること、改革は自分の理解力と理由を使う判断傾向への実際の変化とする。',
    '第五文の前半は政治的離脱の可能性を留保付きで認め、公衆の改革を生む革命経路を固定候補の全域で否定する。個人の改善や革命以外の改革経路は否定しない。後半は同じ革命候補における偏見の将来の働きを別の肯定内容として示す。',
    '新旧の偏見は同じ機能を持つという読みで、影響の人数・強度の数値的な同一性ではない。新しい意見群には内容差と以前の非普及を要求し、初発明、全員にとって初耳、旧意見の完全消滅は要求しない。',
    '理由・帰結・強調・語調・譲歩・訂正・比喩は提示者に帰属し、引用内容の現実的な真理と区別する。頚木・植え付け・報復・Leitbandの描写は対応する対象・役割・時点へ結び、実際の物理的出来事や密かな操作者の存在へ変えない。',
    '原文の全語義やあらゆる歴史的含意を同時に復元する判断ではない。各文の解釈上の限界を継承し、公開した意味規約の下でのアシスタントの通読判断として記録する。独立査読、意味同一性の自動証明、二作品全文の完成ではない。',
]
REASONS = [
    '固定原文u0011の全1216文字・1040非空白文字を、原刊483頁のDaß aberから484頁のdienenまで読み直した。五文の句読点を含む範囲を照合し、全非空白位置を文別記録へ対応させた。数式はない。',
    '自己啓蒙の比較的可能性と自由を条件とするほぼ必然、任用後見人を含む自立達成と周囲への普及、公衆による後見人の拘束の反転と扇動条件、偏見の有害さと反作用、到達経路の低速度、革命の二結果と新旧偏見の働きを確認した。様相・量化・因果・否定・時間・程度を句ごとに保持する。',
    '公衆の範囲h222eと全成員、大衆h223i、共通候補・期間・起点を各文で共有する。前後の公衆、任用された自己思考者、先行の後見人、扇動者は役割に応じて束縛し、無差別に同一集団へ潰さない。第五文の新旧意見と受け手も同じ基準と候補へ結ぶ。',
    'aber・ja・nur・Denn・Besonders・selbst・so・weil・Daher・vielleicht wohl・sondernの提示上の役割を確認した。主張、条件、理由、強調、語調、非字義的描写を分け、留保を改革の否定や後半予測へ拡張しない。著者の推論を論理的な導出証明と扱わない。',
    '五文を通読し、単なる能力から実際の達成への飛躍、圧迫者と受け手の取り違え、意見の改名による新しさ、一つの当たった予測による全称の代用、唯一原因・永久性・全員同時の変化の付加がないことを確認した。比較の共通機能を人数の完全一致へ強めない。',
    '能力・判断・理由・自己活動・共同体・参加・政治秩序・動機・圧迫・服属と終結・普及・通常比較・身体作用・提示の公開意味規約を使う。原語の語形や一文専用の未説明述語で内容を代用しない。文脈上の対象範囲と比率基準は意味規約の明示的な入力であり、検査器が現実から自動認定するものではない。',
    '原刊の視覚照合、文別の通読判断、意味の固定された依存関係、局所的な反例検査、統合帰属の検査を分けて記録した。新たな全単位判断はこの通読によるもので、有限テストの通過を意味同一性へ変換していない。アシスタントによる判断であり独立査読はない。',
    '個人の離脱の難しさとの比較から、公衆内の自己思考者の普及、偏見がその普及を妨げる反転、緩慢な到達と政治的革命の限界までを一段落として再読した。自由の条件付きの見通しと、革命だけで判断様式が改革されることの否定は別の経路・結果である。この明示した読みの下で段落内に未処理項目はない。',
]
CLAUSES = [
    ('Durch eine Revolution ', ['r2qx', 'r2qg', 'r2qr', 'r2ml'], '政治秩序の根幹を変えようとする同じ集団的対抗が、同じ候補内で結果を生む。成功や流血は必須にしない。'),
    ('wird ', ['r2qs', 'r2qt', 'r2qu'], '結果を同じ期間枠の起点より後に置く。現在既に起きた出来事の報告とはしない。'),
    ('vielleicht wohl ', ['r2sf', 'r2sg', 'h227t', 'h227u'], '政治的離脱の結果を未確定とし、その可能性を認めて次の対比へ進む。'),
    ('ein Abfall ', ['r2qe', 'r2qd', 'rcf'], '同じ当事者が実際に服属関係を終える過程。単なる交代や動機の変化では足りない。'),
    ('von persönlichem Despotism ', ['r2qa', 'h226t', 'h227a'], '同じ共同体に実施された、個人の裁量への独立した抑制がない支配から離れる。'),
    ('und ', ['r2qe'], '同じ当事者・過程・前後点で専制と圧迫の両方への服属を終える。'),
    ('gewinnsüchtiger oder herrschsüchtiger ', ['r2px', 'r2py', 'r2pz', 'r2qc'], '同じ圧迫行為の目的となる過度な利得欲または支配欲。両方の併存を許す。'),
    ('Bedrükkung, ', ['r2qb', 'r2qc', 'hzie'], '同じ受け手の選択等を優越的圧力で制約し、不利益を実際に生む行為・仕組み。'),
    ('aber ', ['r2sg', 'h222q'], '同じ革命の帰結について、政治的離脱の可能性と改革経路の不在を対比する。'),
    ('niemals ', ['r2sa', 'r2sc'], '全対象革命・候補において公衆の改革と呼ぶ広がりが生じる経路を否定する。離脱成功例だけに制限しない。'),
    ('wahre Reform der Denkungsart ', ['r2qp', 'r2qn', 'r2qm', 'r2ql', 'r2gy'], '単に意見が変わることとは分け、自分の理解力と理由を使う判断の仕方への実際の変化と読む。'),
    ('zu Stande kommen; ', ['r2qr', 'r2qz', 'r2ra'], '二結果に共通の成立・因果の述語として読む。前半の全内容を同じ著者へ帰属する。'),
    ('sondern ', ['r2sh', 'h227v'], '改革を否定した上で、後半の肯定的な予測を代わりに示す。政治的離脱の可能性を撤回しない。'),
    ('neue ', ['r2rj', 'h227j', 'r2rh', 'h227m'], '基準時には広く採用されず、旧意見と実質的に内容が違う候補内の意見群。'),
    ('Vorurtheile ', ['r2rb', 'r2ri', 'h224w', 'h224x'], '十分な根拠の吟味なしに確立した原則として採用する複数の意見。各項の実際の働きを要求する。'),
    ('werden, ', ['r2rl', 'r2rm', 'r2rn', 'r2ro'], '同じ公衆と全革命候補について、起点より後の働きを予測し著者へ帰属する。'),
    ('eben sowohl als die alten, ', ['r2rj', 'r2rk', 'h227l'], '固定した旧意見群と同じく、未吟味の判断の理由として働く。人数・強度の数値的一致ではない。'),
    ('zum Leitbande ', ['r2rx', 'r2ru', 'r2rv', 'r2rw', 'r2rs'], '同じ意見・本人・行為・時点を、帯・子ども・歩行の身体的描写へ非字義的に対応させる。'),
    ('des gedankenlosen ', ['r2rc', 'h227i'], '意見を同じ判断の理由に用いることの吟味がない。意識や思考能力の欠如へ強めない。'),
    ('großen Haufens ', ['r2m7', 'h223i', 'r2rp', 'h223l'], '同じ大衆の人数と未吟味の働きを保ち、その集団を低く扱う呼称も別に帰属する。'),
    ('dienen.', ['r2rc', 'r2rd', 'r2rf', 'r2si'], '同じ大衆で、単なる保有を越え、後続判断の理由として実際に用いられる働き。意見の意図や特定操作者を付加しない。'),
]


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def unit():
    return next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')


def fifth_reading():
    source = unit()
    position, clauses = 907, []
    for text, definitions, reading in CLAUSES:
        assert source['text'].startswith(text, position), (position, text)
        clauses.append(dict(range=[position, position + len(text)], text=text,
                            definitions=definitions, reading=reading))
        position += len(text)
    assert position == 1216
    paths = {FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, INDEX, *IMAGES, *PRIOR}
    return dict(status='public_fifth_sentence_reviewed_under_explicit_reading', reviewer='assistant_review',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=source['id'], unit_sha256=source['text_sha256'],
                            range=[907, 1216], text=source['text'][907:]),
                clauses=clauses, selection=selection_binding(catalog(), [61, 62]),
                interpretation=LIMITS, interpretation_document=DOC,
                judgment='原刊484頁と固定本文を通読し、各句の内容・因果・量化・否定・時点・照応・留保・譲歩・対比・語調・比喩を確認した。記録した読みの下で第五文に未処理項目はない。',
                unresolved_items_under_adopted_reading=[],
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                newly_reviewed_sentence_characters=269, preserved_first_four_sentence_characters=771,
                combined_five_sentence_characters=1040,
                facsimile=dict(artifacts=[IMAGES[1]], pages=[484], visually_collated=True,
                               differences='長いsと行末分綴。Despo-/tism、Be-/drükkung、Denk-/ungsart、Vor-/urtheileを行継ぎで照合。固定本文を変更しない。'),
                primary_context='https://korpora.org/Kant/aa08/036.html',
                semantic_equivalence_automatically_proved=False, no_independent_review=True,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def paragraph_reading():
    source = unit()
    paths = {AUDIT, DOC, INVENTORY, FULL, BASIS, ANNOTATIONS, *IMAGES, *(p for p, _ in SENTENCES)}
    return dict(status='fourth_paragraph_reviewed_under_explicit_reading', reviewer='assistant_review',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=source['id'], unit_sha256=source['text_sha256'],
                            range=[0, 1216], text=source['text']),
                selection=selection_binding(catalog(), SELECTION),
                sentence_readings=[p for p, _ in SENTENCES] + [AUDIT], interpretation=LIMITS,
                requirements=[dict(id=k, decision='satisfied', reason=v)
                              for k, v in zip(REQUIREMENTS, REASONS, strict=True)],
                decision='equivalent_under_stated_reading', unresolved=[],
                source_nonblank_characters=1040, newly_reviewed_sentence_characters=269,
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def source_checks():
    record = read(AUDIT)
    assert record == fifth_reading()
    source = record['source']
    assert len(source['text']) == 309 and len(''.join(source['text'].split())) == 269
    assert ''.join(c['text'] for c in record['clauses']) == source['text']
    for clause in record['clauses']:
        assert set(clause['definitions']) <= set(record['selection']['dependencies']), clause
    assert digest(unit()['text'].encode('utf-8')) == source['unit_sha256']
    validate_hashes(ROOT, record['source_sha256'])
    return dict(consecutive_clauses=len(CLAUSES), reviewed_nonblank_characters=269,
                all_named_definitions_reachable=True, original_image_pinned=True,
                semantic_judgment_not_inferred_from_tests=True)


@lru_cache(None)
def paragraph_checks():
    assert read(PARAGRAPH) == paragraph_reading()
    source = unit()
    covered = set()
    count = 0
    for path in [p for p, _ in SENTENCES] + [AUDIT]:
        record = read(path)
        start, end = record['source']['range']
        assert record['source']['text'] == source['text'][start:end]
        assert record['source']['unit_sha256'] == source['text_sha256']
        assert record['whole_sentence_semantically_verified']
        assert not covered & set(range(start, end))
        covered.update(range(start, end))
        count += sum(not c.isspace() for c in record['source']['text'])
    assert all(i in covered for i, c in enumerate(source['text']) if not c.isspace())
    assert count == sum(not c.isspace() for c in source['text']) == 1040
    assert len(source['text']) == 1216
    validate_hashes(ROOT, read(PARAGRAPH)['source_sha256'])
    return dict(sentences=5, all_nonblank_positions_covered=True, no_double_counting=True,
                paragraph_nonblank_characters=1040, new_sentence_characters=269,
                complete_requirement_judgments=len(REQUIREMENTS))


@lru_cache(None)
def preservation_checks():
    new = catalog()
    assert len(new.document['statements']) == 63
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in SENTENCES:
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    assert read(PRIOR[-1])['attribution']['native_integrated_root'] == 'r2si'
    assert read(PRIOR[-1])['attribution']['replaced_definitions'] == []
    return dict(preserved_whole_unit_reviews=len(reviews), preserved_sentence_characters=771,
                unchanged_local_reports=len(PRIOR), no_language_changes_for_review=True,
                complete_integrated_attribution_evidence=PRIOR[-1])


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(fifth_reading()))
    write_exact(ROOT / PARAGRAPH, encoded(paragraph_reading()))


def build_report():
    results = {}
    for name, fn in [('source', source_checks), ('paragraph', paragraph_checks),
                     ('preservation', preservation_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(catalog().source_sha256) | set(read(AUDIT)['source_sha256']) | {
        AUDIT, PARAGRAPH, DOC, INVENTORY, INDEX, *IMAGES, *PRIOR, *[p for p, _ in SENTENCES],
        'scripts/check_fourth_paragraph.py', 'tests/test_fourth_paragraph.py',
        'scripts/check_revolution_presentation.py', 'scripts/check_political_withdrawal.py'}
    return dict(status='fourth_paragraph_explicit_reading_checked', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=['r2si'],
                               status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, newly_reviewed_sentence_characters=269,
                paragraph_reviewed_sentence_characters=1040,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                whole_unit_registration='separate_explicit_review_required',
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def review():
    record = read(PARAGRAPH)
    validate_hashes(ROOT, read(REPORT)['source_sha256'])
    evidence = dict(source_reading=[PARAGRAPH, AUDIT] + [p for p, _ in SENTENCES],
                    formal_checks=[REPORT] + PRIOR, semantic_reading=[DOC])
    pins = dict(catalog().source_sha256)
    for path in {FULL, BASIS, ANNOTATIONS, INVENTORY} | {p for paths in evidence.values() for p in paths}:
        pins[path] = digest((ROOT / path).read_bytes())
        if path.endswith('.json'):
            for child, sha in read(path).get('source_sha256', {}).items():
                assert child not in pins or pins[child] == sha
                pins[child] = sha
    validate_hashes(ROOT, pins)
    return dict(schema_version='noema-semantic-review-1', work='kant-1784', unit='kant-1784:u0011',
                reviewer='assistant_review', decision=record['decision'],
                document=FULL, meaning_basis=BASIS, identifier_annotations=ANNOTATIONS,
                source=dict(inventory=INVENTORY, unit_sha256=unit()['text_sha256'], text=unit()['text'],
                            range=[0, len(unit()['text'])], math=[]),
                selection=record['selection'], interpretation=record['interpretation'],
                limits=['明示した読みの下でのアシスタントの判断。独立査読や同義性の自動証明ではない。',
                        '原文の全語義・韻律・全歴史的含意の同時復元ではない。各文の限界を継承する。',
                        '後続段落とアインシュタイン論文は未完。現実の歴史や哲学的主張の真理の証明ではない。'],
                unresolved=[], requirements=record['requirements'], evidence=evidence, source_sha256=pins)
