"""Review the whole fifth paragraph, preserving corrected sentence bindings."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes,REQUIREMENTS
from scripts.compose_grounded_step import ROOT

FULL='examples/v016/kant-guardian-irrationality.noema'
BASIS='data/guardian-irrationality-basis-v1.json'
ANNOTATIONS='data/guardian-irrationality-identifiers-v1.json'
INDEX='data/semantic-review-index-v179.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PARAGRAPH='data/fifth-paragraph-reading-v1.json'
REVIEW='data/fifth-paragraph-review-v1.json'
REPORT='reports/fifth-paragraph-v1.json'
DOC='docs/fifth-paragraph-v1.md'
STEMS=('enlightenment-requirement','heard-prohibition','role-commands','single-ruler','everywhere-restriction',
    'question-discourse','answer-discourse','use-definitions','public-purpose-mechanism','office-obedience',
    'scholarly-compatibility','officer-example','protected-remarks','civic-example','public-civic-opinion',
    'clerical-obligation','clerical-public-freedom','clerical-conscience','clerical-explanation','clerical-report-forecast',
    'clerical-practical-benefit','clerical-resignation-condition','clerical-private-conclusion','unrestricted-scholarly-freedom','guardian-irrationality')
SENTENCES=tuple('data/'+n+'-reading-v1.json' for n in STEMS)
PRIORS=tuple('reports/'+n+'-v1.json' for n in STEMS)
IMAGES=('artifacts/public-reversal-reading-v1/page-484.jpg','artifacts/answer-discourse-v1/page-485.jpg',
    'artifacts/officer-example-v1/page-486.jpg','artifacts/representative-teaching-v1/page-487.jpg',
    'artifacts/spiritual-guardians-v1/page-488.jpg')
LIMITS=[
    '文別の25判断記録に含まれる29文の採用解釈を保持する。第一文だけはheard-prohibition-reading-v1のfirst_sentence_recheckにある訂正後の提示文脈と文選択を使い、旧選択を復活させない。各記録の「後続は未完」はその作成時の進捗であり、意味条件にはしない。',
    '啓蒙への供給要件、最小の害の自由、公的使用の全関連時機への自由要求、公的使用を欠く達成経路の不在、私的制限への許可と因果的留保を区別する。自由だけで即時・無条件に成功するという十分性、全ての私的行為の無害性は加えない。',
    '公的使用は学識者として全読者世界へ向ける本人の理性使用、私的使用は委ねられた市民的職務での使用という採用定義。私生活と公開空間の区別に置換せず、全活動を尽くす排他的二分類とも主張しない。',
    '前三役職の禁止と代替命令、唯一の統治者の自由選択と服従の発言は著者が提示する内容。後の将校・市民・聖職者の一般的職務例と同じ実在者には同定しない。発話、許可・要求、実際の履行、正当性を別に保持する。',
    '事務の機構と受動的遂行は職務の執行範囲に限定する。人工的協調を内心の同意に、同じ人の学識者としての公的活動との両立を職務上の制約の撤回に変えない。世界市民社会は国家を越える社会の構想として読む。',
    '将校への服従要求と公正な批評保護、市民への納付拒否禁止・限定した批判の処罰可能性と学識者としての不違反、聖職者の教示義務と公的自由・使命を、それぞれ同じ人の役割と内容に結ぶ。公正さや良心上の評価規範を現職の指図へ同一視しない。',
    '聖職者の教会・職務・信条・生徒・会衆と学識者としての宛先を保持する。職務上の代表的教示、予告された発言、本人の確信、規定群の実益、真理の可能性、内面的宗教との抵触、良心上の辞職条件を別の様相と作用域で構成する。教義の真理や実際の退職は引用から導かない。',
    '同じ規定群・内面的宗教基準を連続二文で共有する判断を保持する。先行実益文と辞職条件で別の存在証人を選び直さず、同じ原文範囲を集計で二度加えない。',
    '最後の一般的な公的自由には、それ以前の教義批評の慎重さ・善意・提案という範囲限定を追加しない。不合理の評価要件を具体的なNoema条件へ結び、同じ方針から同じ共同体の全関連する不合理な内容の持続へ至る帰結を保持する。終点なしや数値時間の非有界性は加えない。',
    '位置688のダッシュは、問いからIch antworteの自己回答への区切りである。既存hzcs/h236mと本文順序ueでその提示関係を表し、独立した主張や負号に変えない。原刊の長い横線と固定転写のen dashの字体差は原文を書き換えず記録する。',
    '語調・強調・譲歩・対照・理由・例示・定義提示・自己取り立ては同じ著者の第五段落文脈に帰属する。理由の提示と論理的証明・因果の成立、引用の真理と発話の存在を混同しない。',
    '有限検査、全記述域の有限評価拒否、型付き境界、原刊照合、通読による判断を区別する。これは公開した解釈の下でのアシスタントの判断であり、独立査読、意味同一性の自動証明、全歴史的含意や全語義の同時復元ではない。',
]
REASONS=[
    '固定原文u0012の全5,190文字・4,433非空白文字を原刊484–488頁と通読した。25文別判断の4,432文字と問い・回答間のダッシュ1文字で全非空白位置を過不足なく覆う。数式はない。',
    '自由の供給要件から周囲の禁止、四命令の制限評価、二問と回答、公私使用の定義、機構と職務制約、公的活動との両立、将校・市民・聖職者の例、最後の不合理と持続への理由までの全内容を確認した。量化・否定・様相・程度・時間・条件・因果を文別の作用域で保持する。',
    '本人・理性・役割・職務・組織・規範源・公衆・人民・会衆・信条・規定群・内面的宗教基準を前後の同じ範囲へ結ぶ。第一文のh232oへの訂正と、最終文のsgの事柄・人の引数順訂正を現行選択で確認した。',
    '主張、聞いた声と命令引用、問い、自己回答、用語定義、仮定、予告される報告、理由・対照・譲歩・自己取り立てを区別する。ダッシュの区切りと原刊の学識者の強調も対応する提示関係に含めた。',
    '職務上の制約と学識者の自由は同じ人の異なる立場であり、各対照は前内容の撤回ではない。許可から実行、主張から真理、良心上の不能から辞職の実施、因果的可能性から法的正当性への飛躍を加えない。全域量化を都合のよい既知例へ狭めない。',
    '公開した意味規約とNoema合成により、自由・義務・能力・判断・指導・制度・利益・因果・教示・信条・自己帰責・持続を区別する。原語文字列や未説明の一文専用述語で代用しない。文脈範囲や基準の外部供給は解釈の責任と明記する。',
    '原刊の五頁、文別読解、第一文の訂正記録、局所検査報告と現行依存関係の一致を別々に保存する。段落判断はこれらを照合して通読したアシスタントの判断であり、検査通過から自動生成する結論ではない。',
    '段落を通読し、最初の自由の要件を、全ての制度的制約の撤廃や自由だけによる成功保証に変えず、公的使用と職務内の使用の区別で展開することを確認した。聖職者の良心上の留保と後見人の不合理への最終理由までを含め、この明示した読みの下で未処理項目はない。',
]


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
def unit():return next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0012')


def rows():
    result=[]
    for path in SENTENCES:
        record=read(path)
        if path==SENTENCES[0]:
            corrected=read(SENTENCES[1])['first_sentence_recheck']
            selection=corrected['selection'];override=dict(record=SENTENCES[1],field='first_sentence_recheck',change=corrected['change'])
        else:selection=record['selection'];override=None
        result.append(dict(record=path,source=record['source'],selection=selection,correction=override))
    return result


def indices():return sorted({v['index'] for row in rows() for v in row['selection']['statements']})


def paragraph_reading():
    source=unit();paths={FULL,BASIS,ANNOTATIONS,INVENTORY,DOC,*SENTENCES,*IMAGES}
    return dict(status='fifth_paragraph_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=source['id'],unit_sha256=source['text_sha256'],range=[0,len(source['text'])],text=source['text']),
        selection=selection_binding(catalog(),indices()),sentence_readings=rows(),interpretation=LIMITS,
        punctuation=[dict(range=[688,689],text='–',reading='問いから著者自身の回答へ移る区切り。',
            definitions=['hzcs','h236m','ue','h236n','r2zh'],statements=[75],original_page=484)],
        requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS,strict=True)],
        decision='equivalent_under_stated_reading',unresolved=[],source_nonblank_characters=4433,
        inherited_sentence_characters=4432,additional_punctuation_characters=1,
        semantic_equivalence_automatically_proved=False,no_independent_review=True,
        facsimile=dict(artifacts=list(IMAGES),pages=[484,485,486,487,488],visually_collated=True,
            differences='長いs、行末分綴、改頁の送り語を照合。484頁のダッシュは問いと自己回答を区切る。原刊487頁のPrivatgebrauch後はセミコロンで、比較したAA転記のコロンへ置換しない。固定転写を変更しない。'),
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def merge_pins(paths):
    pins=dict(catalog().source_sha256)
    for p in paths:
        for name,sha in {p:digest((ROOT/p).read_bytes()),**read(p).get('source_sha256',{})}.items():
            assert name not in pins or pins[name]==sha,name
            pins[name]=sha
    return pins


@lru_cache(None)
def coverage_checks():
    source=unit();covered=set();count=0
    for row in rows():
        record=read(row['record']);s=row['source'];a,b=s['range']
        assert s['unit']==source['id'] and s['unit_sha256']==source['text_sha256']
        assert s['text']==source['text'][a:b] and record['whole_sentence_semantically_verified']
        assert not record.get('unresolved') and not covered.intersection(range(a,b))
        covered.update(range(a,b));count+=sum(not c.isspace() for c in s['text'])
    assert count==4432
    uncovered=[(i,c) for i,c in enumerate(source['text']) if not c.isspace() and i not in covered]
    assert uncovered==[(688,'–')],uncovered
    record=read(PARAGRAPH)
    for item in record['punctuation']:
        a,b=item['range'];assert item['text']==source['text'][a:b] and not covered.intersection(range(a,b));covered.update(range(a,b))
    assert all(i in covered for i,c in enumerate(source['text']) if not c.isspace())
    assert sum(not c.isspace() for c in source['text'])==4433 and len(source['text'])==5190
    assert digest(source['text'].encode('utf-8'))==source['text_sha256']
    assert record==paragraph_reading()
    return dict(sentence_records=25,source_sentences=29,inherited_nonblank_characters=4432,punctuation_characters=1,
        whole_paragraph_nonblank_characters=4433,all_nonblank_positions_covered=True,no_double_counting=True)


def calls(node,name):
    if isinstance(node,dict):return ([node] if node.get('kind')=='call' and node.get('symbol')==name else [])+sum((calls(v,name) for v in node.values()),[])
    if isinstance(node,list):return sum((calls(v,name) for v in node),[])
    return []
def named(n):return dict(kind='call',symbol=n,arguments=[])


@lru_cache(None)
def transition_checks():
    new=catalog();answer=new.entries['r2zh']['declaration']
    for question in ('h235n','h235o'):
        matching=[c for c in calls(answer,'h236m') if c['arguments'][2]==named(question)]
        assert len(matching)==1
        a=matching[0]['arguments'];assert a[:4]==[named('h236n'),named('wa'),named(question),named('h235p')]
        assert a[-1]==named('h232o')
        assert any(c['arguments']==[named('wa'),named(question),named('h235p'),named('h232o')] for c in calls(answer,'hzcs'))
        assert any(c['arguments']==[named(question),named('h236n'),named('h232o')] for c in calls(answer,'ue'))
    assert {'r2zh','h236n','h236m','hzcs','ue'}<=set(selection_binding(new,[75])['dependencies'])
    last=new.entries['r453']['declaration'];reason=calls(last,'ud');assert len(reason)==1
    assert reason[0]['arguments'][2:]==[named('h253m'),named('h232o')]
    assert calls(reason[0]['arguments'][1],'h254d')
    assert any(c['arguments']==[named('h253m'),named('h254d'),named('h232o')] for c in calls(last,'ue'))
    return dict(two_questions_same_self_answer=True,question_answer_boundary_preserved=True,
        final_reason_points_to_scholarly_freedom=True,no_new_language_relations=True)


@lru_cache(None)
def preservation_checks():
    new=catalog();assert len(new.document['statements'])==96
    corrected=read(SENTENCES[1])['first_sentence_recheck'];assert corrected['selection']!=corrected['replaced_selection']
    assert corrected['source']==read(SENTENCES[0])['source']
    for row in rows():
        idx=[x['index'] for x in row['selection']['statements']]
        assert row['selection']==selection_binding(new,idx),row['record']
    prior=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(prior)==14
    for row in prior:assert row['selection']==selection_binding(new,[x['index'] for x in row['selection']['statements']])
    assert indices()==[i for i in range(63,96) if i!=78],indices()
    pins=merge_pins([*SENTENCES,*PRIORS,PARAGRAPH]);validate_hashes(ROOT,pins)
    assert not {'r45e','r45h','r45i','r45k','r45p'}&set(new.entries)
    return dict(preserved_whole_unit_reviews=14,unchanged_sentence_bindings=25,corrected_first_sentence_binding=True,
        superseded_guardian_definitions_absent=True,unchanged_local_reports=len(PRIORS),
        no_manuscript_or_language_changes=True,hash_pinned_files=len(pins),paragraph_statements=indices())


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/PARAGRAPH,encoded(paragraph_reading()))


def build_report():
    results={}
    for n,fn in [('coverage',coverage_checks),('transitions',transition_checks),('preservation',preservation_checks)]:
        results[n]=fn();print(n+' checked',flush=True)
    paths=set(merge_pins([*SENTENCES,*PRIORS,PARAGRAPH]))|{DOC,INDEX,PARAGRAPH,INVENTORY,FULL,BASIS,ANNOTATIONS,*IMAGES,
        'scripts/check_fifth_paragraph.py','tests/test_fifth_paragraph.py'}
    return dict(status='fifth_paragraph_explicit_reading_checked',document=FULL,**results,
        alignment=dict(**read(PARAGRAPH)['source'],definitions=['r2zh','r453'],status='explicit_interpretive_annotation'),
        whole_paragraph_semantically_reviewed=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        whole_unit_registration='separate_explicit_review_required',semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def review():
    record=read(PARAGRAPH);validate_hashes(ROOT,read(REPORT)['source_sha256'])
    evidence=dict(source_reading=[PARAGRAPH,*SENTENCES],formal_checks=[REPORT,*PRIORS],semantic_reading=[DOC])
    pins=merge_pins([PARAGRAPH,REPORT,*SENTENCES,*PRIORS])
    for p in (FULL,BASIS,ANNOTATIONS,INVENTORY,DOC):pins[p]=digest((ROOT/p).read_bytes())
    validate_hashes(ROOT,pins)
    return dict(schema_version='noema-semantic-review-1',work='kant-1784',unit='kant-1784:u0012',reviewer='assistant_review',
        decision=record['decision'],document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=unit()['text_sha256'],text=unit()['text'],range=[0,len(unit()['text'])],math=[]),
        selection=record['selection'],interpretation=record['interpretation'],
        limits=['明示した読みの下でのアシスタント判断。独立査読・意味同一性の自動証明ではない。各文の解釈上の限界を継承する。',
            '全語義・全歴史的含意の同時復元ではない。原著者の主張の真理や制度的正当性を証明したものではない。',
            '後続段落とアインシュタイン論文は未完。'],unresolved=[],requirements=record['requirements'],evidence=evidence,source_sha256=pins)
