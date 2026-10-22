"""Review all five sentences, shared rulers, examples and generalization."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes,REQUIREMENTS
from scripts.compose_self_departure_sentence import ROOT,FULL,BASIS,ANNOTATIONS
from scripts.check_fifth_paragraph import calls,named

INDEX='data/semantic-review-index-v200.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PARAGRAPH='data/eighth-paragraph-reading-v1.json';REVIEW='data/eighth-paragraph-review-v1.json'
REPORT='reports/eighth-paragraph-v1.json';DOC='docs/eighth-paragraph-v1.md'
STEMS=('prince-sentence','public-offers-sentence','spreading-spirit-sentence','manifest-example-sentence','self-departure-sentence')
SENTENCES=tuple('data/'+n+'-reading-v1.json' for n in STEMS)
PRIORS=tuple('reports/'+n+'-v1.json' for n in STEMS)
SOURCE='data/eighth-paragraph-source-reading-v2.json'
IMAGES=('artifacts/royal-writing-oversight-v1/page-491.jpg','artifacts/eighth-paragraph-source-v1/page-492.jpg')
ROOTS=('r53l','r55v','r57x','r6ao','r6bi')
NODES=('h26oq','h26pc','h26qi','h26ra','h26r3')
CONTEXTS=('h26og','h26pb','h26pq','h26q2','h26rz')
LIMITS=[
 '五文の採用解釈を保持し、全1354文字・1154非空白文字を段落として通読した。旧文別記録の後続未完という記述は記録時点の進捗であり、今回の未解決点ではない。旧第一〜第三文記録が述べた第四文のist/sei版差は誤読だったため、新しい判断には引き継がず訂正記録v2のseiを採用する。固定本文と旧証拠自体は変更しない。',
 '第一文は自己報告の品位判断と高慢な寛容という名称の自己適用拒否を持つ一般的君主についての主張。義務と自由の実行を自己報告の前提に加えず、同じ当人・職・共同体について啓蒙と称揚に値する功績を結ぶ。功績は政府側の拘束の解放であり、全員の能力の完成ではない。',
 '第二文は同じ君主条件の下での学識者としての公的提示の自由。敬意に値する聖職者の全職務要求の非免除と発表・履行の共充足を保ち、同じ限定群の外で職務制限を受けない他者へなおさらと拡張する。審査目的を実際の審査成功に、許可を実行に替えない。',
 '第三文は先行二文の宗教的自己選択と公的提示の自由を支持する態度が、同じ出発者から内外へ広がるという読み。国外には同じ自己誤解する政府由来の障害と対抗的努力を必要とする場合も含める。全政府・全人への到達、政府の悪意、克服完了を補わない。',
 '第四文のdieserは第三文の同じ外国政府であり、r57lの同じ八対象をr6ajで拡張する。元の同じ統治圏での自由と平穏・一致の共存を実例とし、その外国政府側で自由の下に根拠ある危害を見込む候補がないという内容への明瞭な支持を提示する。例からの演繹、政府の実際の賛同、全未来の安全保証とはしない。',
 '第五文は特定の君主・職務者だけから人々一般へ範囲を広げる。開始時の未陶冶について、全関連の将来経過で意図的な保持操作がなければ、同じ本人の自己からの漸進的離脱が後にあるという読み。候補は成功や妨害の不在で選別せず、人ごとの開始点と後件内の到達点を持つ。現在の全員の完成や任意の短い締切は追加しない。',
 '第一文の宗教的自由と政府側の解放、第二文の公的提示と職務義務、第三文の態度の伝播、第四文の実例による支持、第五文の人の形成過程を同じ概念に潰さない。最後の未陶冶は思考・判断習慣についての明示した読みであり、未成熟bfや全人格の悪と同一視しない。',
 '各文の提示文脈は区別し、同じ著者waと文章箇所の順序で結ぶ。先行四文の現在点はh26kn(h26km)を共有し、第三〜第五文の固定基準はh26ppを共有する。第五文は現在の一時点に縛られない一般的条件であり、既存の君主条件を無断で前件に加えない。',
 '著者の歴史的・哲学的主張の真理、候補範囲や規範・比較入力の現実の網羅性は有限試験で証明しない。原刊通読、語句対応、型・引用・引数接続・対照例の検査を分けたアシスタント判断であり、独立査読や意味同一性の自動証明ではない。',
]
REASONS=[
 '原刊491–492頁と固定転記u0015全五文を通読した。1354文字・1154非空白文字を五件の文範囲で重複なく覆い、文間は空白だけ。頁末のinは次頁のキャッチワードとして二重に数えず、第四文seiの訂正記録v2を適用した。数式はない。',
 '君主の自己報告と名称拒否、啓蒙と称揚に値する功績、職務を保った公的自由、内外への伝播と障害下の努力、同じ政府に示される実例、人々の条件付き自己形成を段落として確認した。量化・否定・条件・時間・目的・程度・引用を保つ。',
 'Unter ihmは同じ限定君主、Dieser Geistとerは同じ自由支持態度、dieserは同じ外国政府、ein Beispielは同じ元の統治圏の自由の型を受ける。第五文sieとdarinは同じ人々と未陶冶を指し、条件と結果は同じ本人の同じ候補経過を共有する。',
 '第一文のalso・selbst・sondern・wenigstens、第二文のnoch mehr aber、第三文のauchとselbst da、第四文のDennとdoch、第五文のwenn man nur nichtを本文内容と談話の役割に分けて保つ。全文は同じ著者への閉じた内容の帰属であり、引用の真理を帰属の前提にしない。',
 '特定の実在王、全政府・全人の成功、全信条との不一致、現実の審査・賛同、政府の悪意、自由だけによる即時達成を加えない。第五文で候補欠落を前件の偽に補わず、目的未達の操作や途中の後退を落とさない。',
 '宗教的自己選択・公的使用・義務・敬意・判断と洞察・態度の共有・因果的妨害・努力・平穏と一致・根拠ある危害・自己形成・質的漸進を公開された意味規約と合成で扱う。原語の綴りや一文全体の真偽を返す記号へ置換しない。',
 '各文の意味判断・局所検査・原刊画像・訂正記録を固定ハッシュで保存し、現行117主張への依存一致を確認する。旧17単位判断は再利用し、段落判断は通読による新しい記録として登録する。検査成功をそのまま同義判断にしない。',
 '一般的な君主の宗教的自由から、公的提示の自由、その精神の広がり、障害ある政府への実例、妨害しなければ進む人々の形成という展開を全体で再読した。前四文の同じ統治枠と、最後の一般化を区別し、明示した読みの下で未処理の語句・照応・提示作用はない。',
]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
def unit():return next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0015')
def rows():return [dict(record=p,source=read(p)['source'],selection=read(p)['selection']) for p in SENTENCES]
def indices():return list(range(112,117))
def merge_pins(paths):
    pins=dict(catalog().source_sha256)
    for p in paths:
        for name,sha in {p:digest((ROOT/p).read_bytes()),**read(p).get('source_sha256',{})}.items():
            assert name not in pins or pins[name]==sha,name
            pins[name]=sha
    return pins
def paragraph_reading():
    u=unit();paths={FULL,BASIS,ANNOTATIONS,INVENTORY,DOC,SOURCE,*SENTENCES,*IMAGES}
    return dict(status='eighth_paragraph_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text']),
        selection=selection_binding(catalog(),indices()),sentence_readings=rows(),interpretation=LIMITS,
        requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS,strict=True)],
        decision='equivalent_under_stated_reading',unresolved=[],source_nonblank_characters=1154,
        inherited_sentence_characters=1154,additional_punctuation_characters=0,
        semantic_equivalence_automatically_proved=False,no_independent_review=True,
        facsimile=dict(artifacts=list(IMAGES),pages=[491,492],visually_collated=True,
            differences='原刊のコロン、長いsと行末分綴、頁またぎを照合。第四文は原刊もseiであり旧ist観察を訂正済みv2で置き換える。'),
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
@lru_cache(None)
def coverage_checks():
    u=unit();covered=set();count=0
    for row in rows():
        record=read(row['record']);s=row['source'];a,b=s['range']
        assert s['unit']==u['id'] and s['unit_sha256']==u['text_sha256'] and s['text']==u['text'][a:b]
        assert record['whole_sentence_semantically_verified'] and not record.get('unresolved')
        assert not covered.intersection(range(a,b));covered.update(range(a,b));count+=sum(not c.isspace() for c in s['text'])
    assert count==1154 and len(u['text'])==1354
    assert all(i in covered for i,c in enumerate(u['text']) if not c.isspace())
    assert sum(not c.isspace() for c in u['text'])==count and digest(u['text'].encode('utf-8'))==u['text_sha256']
    assert read(SOURCE)['fourth_sentence']['original_reading'].endswith('sei')
    assert read(PARAGRAPH)==paragraph_reading()
    return dict(sentence_records=5,whole_paragraph_nonblank_characters=1154,all_nonblank_positions_covered=True,
        no_double_counting=True,old_ist_observation_not_inherited_as_a_variant=True)
@lru_cache(None)
def transition_checks():
    c=catalog();previous='h26m4';edges=[];deps=[]
    for i,(root,node,context) in enumerate(zip(ROOTS,NODES,CONTEXTS,strict=True),112):
        assert c.document['statements'][i]['body']==dict(kind='call',symbol=root,arguments=[])
        d=c.entries[root]['declaration'];edge=[named(previous),named(node),named(context)]
        assert any(x['arguments']==edge for x in calls(d,'ue')),(root,previous,node)
        for x in calls(d,'ue'):assert x['arguments'][-1]==named(context)
        claims=[x for relation in ('h26n7','h236i','hzon') for x in calls(d,relation)]
        assert claims and any(x['arguments'][0]==named(node) for x in claims)
        for x in claims:assert x['arguments'][1]==named('wa') and x['arguments'][-1]==named(context)
        deps.append(set(selection_binding(c,[i])['dependencies']));edges.append([previous,node]);previous=node
    assert all({'h26kn','h26km','r53b'}<=d for d in deps[:4])
    assert all('h26pp' in d for d in deps[2:])
    assert 'r53b' not in deps[4] and 'h26kn' not in deps[4] and 'h26ru' in deps[4]
    prior=c.entries['r6aj']['declaration'];assert len(calls(prior,'r57l'))==1
    extended=calls(prior,'r57l')[0]['arguments']
    assert len(extended)==9 and extended==[dict(kind='variable',name=p['name']) for p in prior['parameters']]
    for root in ('r57x','r6ao'):
        refs=calls(c.entries[root]['declaration'],'h26qe');assert len(refs)==2
        assert all(r['arguments'][-2]==named('h26pp') for r in refs)
    reason=calls(c.entries['r6ao']['declaration'],'h26q3')[0]
    assert calls(reason['arguments'][2],'r57r') and calls(reason['arguments'][3],'r6an')
    conditional=c.entries['r6be']['declaration'];before=calls(conditional,'r6bc')[0]['arguments'];after=calls(conditional,'r6bd')[0]['arguments']
    assert before==after and len(before)==6
    return dict(all_sentence_order_edges=edges,same_author_distinct_sentence_contexts=True,
        first_four_share_ruler_condition_and_present=True,last_sentence_generalizes_without_ruler_restriction=True,
        foreign_government_witness_extended=True,prior_freedom_type_and_reason_direction=True,same_person_and_course_in_final_conditional=True)
@lru_cache(None)
def preservation_checks():
    c=catalog();assert len(c.document['statements'])==117;selected=[]
    for row in rows():
        idx=[x['index'] for x in row['selection']['statements']];selected.extend(idx)
        assert row['selection']==selection_binding(c,idx),row['record']
    assert selected==indices()
    prior=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(prior)==17
    for row in prior:assert row['selection']==selection_binding(c,[x['index'] for x in row['selection']['statements']])
    pins=merge_pins([*SENTENCES,*PRIORS,SOURCE,PARAGRAPH]);validate_hashes(ROOT,pins)
    return dict(preserved_whole_unit_reviews=17,unchanged_sentence_bindings=5,unchanged_local_reports=5,
        no_manuscript_or_language_changes=True,hash_pinned_files=len(pins),paragraph_statements=indices())
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/PARAGRAPH,encoded(paragraph_reading()))
def build_report():
    results={}
    for n,f in (('coverage',coverage_checks),('transitions',transition_checks),('preservation',preservation_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(merge_pins([*SENTENCES,*PRIORS,SOURCE,PARAGRAPH]))|{DOC,INDEX,PARAGRAPH,INVENTORY,FULL,BASIS,ANNOTATIONS,*IMAGES,
        'scripts/check_eighth_paragraph.py','scripts/check_fifth_paragraph.py','tests/test_eighth_paragraph.py'}
    return dict(status='eighth_paragraph_explicit_reading_checked',document=FULL,**results,
        alignment=dict(**read(PARAGRAPH)['source'],definitions=list(ROOTS),statements=indices(),status='explicit_interpretive_annotation'),
        whole_paragraph_semantically_reviewed=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        whole_unit_registration='separate_explicit_review_required',semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
def review():
    record=read(PARAGRAPH);validate_hashes(ROOT,read(REPORT)['source_sha256'])
    evidence=dict(source_reading=[PARAGRAPH,SOURCE,*SENTENCES],formal_checks=[REPORT,*PRIORS],semantic_reading=[DOC])
    pins=merge_pins([PARAGRAPH,REPORT,SOURCE,*SENTENCES,*PRIORS])
    for p in (FULL,BASIS,ANNOTATIONS,INVENTORY,DOC):pins[p]=digest((ROOT/p).read_bytes())
    validate_hashes(ROOT,pins)
    return dict(schema_version='noema-semantic-review-1',work='kant-1784',unit='kant-1784:u0015',reviewer='assistant_review',
        decision=record['decision'],document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=unit()['text_sha256'],text=unit()['text'],range=[0,len(unit()['text'])],math=[]),
        selection=record['selection'],interpretation=record['interpretation'],
        limits=['各文の明示した解釈と限界を継承し、ist/seiの誤読は訂正v2を採るアシスタント判断。独立査読・自動同値証明ではない。',
            '著者の歴史的・哲学的主張の真理や、全解釈を同時に再現したという主張ではない。',
            '第九・第十段落とアインシュタイン論文は未完。'],unresolved=[],requirements=record['requirements'],evidence=evidence,source_sha256=pins)
