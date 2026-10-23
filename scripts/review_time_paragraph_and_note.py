"""Pin the complete time-description paragraph and its separate author note."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.check_einstein_principles_paragraph import calls
from scripts.compose_local_simultaneity_note import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS as NOTE_LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json'
SOURCES=('data/einstein-motion-time-source-reading-v1.json','data/einstein-time-continuation-source-reading-v1.json')
STEMS=('motion-time-description','temporal-judgments','train-clock-example','local-simultaneity-note')
REPORTS=tuple('reports/'+n+'-v1.json' for n in STEMS)
DOCS=tuple('docs/'+n+'-v1.md' for n in STEMS)
READINGS=tuple('data/'+n+'-reading-v1.json' for n in STEMS[:3])
REVIEWS={'einstein-1905:u0010':'data/einstein-time-paragraph-review-v1.json','einstein-1905:u0279':'data/einstein-local-simultaneity-note-review-v1.json'}
SPANS=((0,126),(127,337),(338,481),(482,666))
PARAGRAPH_LIMITS=[
 '第一文のWirは著者の一般的な記述方法の声として読む。運動を記述する意図から三座標の時間関数を与える方法へ結び、特定の点の現実の運動や実際の発言歴を追加しない。定数・非等速・往復も含め、微分可能性や動力学法則を加えない。',
 '同じ点・系・長さと時間の尺度・全対象期間に三関数を割り当て、seを正しい全履歴対応の基準として引用する。数学的な表示、物理的な意味、実際に正しい軌道、実測を区別する。',
 'erst dann … wennは物理的意味のための先行理解という必要条件であり、十分性を補わない。manは同じ記述の時間の意味を把握する使用者とし、vorherを厳密な先行として保持する。第二文の注意喚起を別に結ぶ。',
 '時間が関わる判断一般の時間的内容を、同時性についての判断によって説明できるという読みを採る。対象・否定・量化・条件を保持し、全ての判断の対象が実際に同時であるという断言や単一の肯定文への還元に替えない。alleとimmer、考慮すべき方法上の要請を保持する。',
 '列車と時計の例では、同じ話者・列車・ここに当たる場所・時計・短針・時の単位・到着を共有する。7は十二時表示の7時とし、日付・午前午後・任意の経過時間七単位を補わない。表示出来事と列車到着の同時性を同じ系・尺度へ結ぶ。',
 'Wenn ich sageは発言の仮定、z. B.は先行論点の具体例、etwaはおおよその説明として保持する。二つの引用内容や時計の指示・列車到着を帰属の時点で実行せず、厳密な論理的同値を要求しない。',
 '同じ場所への割当は局所的な理想化である。文末の著者脚注1)を別単位u0279の記述へ接続し、近接した場所の同時性概念に残る不精密さ・抽象化の必要・ここでは論じないという留保と両立させる。脚注の185文字は段落の560文字へ合算せず、別単位として数える。',
 '意味保持・物理的な割当・校正・近接尺度は規約を明示した入力である。有限の対照例を全実数・全関数の証明、物理的な実験、任意の自然言語の自動変換、同義性の自動証明へ昇格させない。',
]
PARAGRAPH_REASONS=(
 '固定u0010全666文字・560非空白文字を四範囲[0,126)、[127,337)、[338,481)、[482,666)で覆う。前二文は原刊892頁末尾、後二文は893頁上端へ照合し、行末分割を接続した転記と対応する。数式はなく、文末の著者脚注1)は別単位u0279へ結ぶ。',
 '運動を時間関数で記述する方法、物理的意味には時間の先行理解が必要という条件と注意、時間が関わる全判断を同時性について説明する性質と考慮の要請、列車到着と時計の短針の例を保持する。条件・量化・先行・約言を省かない。',
 '先行する同じra、同じ物質点と三座標関数、同じ数学的記述とその使用者・時間規約を結ぶ。第四文のjener Zug・hier・meiner Uhrを同じ例の対象へ固定し、両引用で同じ到着と時計・尺度を使う。脚注番号は同じ論説の同じ注を指す。',
 '四文を同じ著者・論説へ主張として帰属し、方法的条件、注意喚起、考慮すべき要請、引用された発言の仮定と約言、具体例という提示役割を分ける。本文224–227の順序と、本文に属する注番号から脚注228への参照を保持する。',
 '数学的表示から物理的真理や実測を導かず、時間理解の必要性を十分性へ替えない。判断についての説明から全出来事の同時性を主張せず、列車の例を実際の到着や厳密な同義証明へ替えない。局所の同所性を理想化として明示し、脚注でその限界を保持する。',
 '物質点、全期間の関数と正しい履歴対応、記述・提示、物理的意味と明確な理解、時間の関与と判断説明、同時性、列車到着、短針・時の目盛・時計読取り、発言・約言・例示・注参照の規約を再読した。原語や一文全体の未説明の真偽入力へ置き換えていない。',
 '三つの文別読解記録と四つの局所報告、原刊画像の照合、全依存定義と意味規約を固定する。実数・関数の全域は有限評価で拒否し、局所的な関数・時刻の対照例と引用・引数の接続を区別する。脚注の内容も別の局所検査と通読判断を持つ。',
 '位置の時間関数表示から時間の物理的解釈へ進み、時間判断の一般的な説明を列車と時計の例で具体化する四文を続けて通読した。明示した読みの下で内容・条件・参照・提示・注参照の未処理項目はない。後続の時計位置による時間定義の限界は次の単位で扱う。',
)
NOTE_REASONS=(
 '固定u0279全212文字・185非空白文字を原刊893頁下部の著者脚注1)へ照合した。括弧annähernd、gleichfalls、muß、soll hier nichtを含む全一文を覆い、本文u0010第四文末尾の注番号へ結ぶ。インベントリのpage_at_end=921を実際の掲載頁とはしない。',
 '近接又は同じ場所の二出来事の同時性概念にある不精密さ、それも抽象化で橋渡しする必要があること、ここでは論じないという方針を保持する。不精密さの存在だけ又は不議論の宣言だけに縮めない。',
 '同じ問題eisfvを、同じ同時性概念eihm・局所適用範囲eijd・抽象化の操作型eisfrへ固定する。必要性・添加・不議論を別々の問題へ分散せず、同じ著者・論説・注箇所へ結ぶ。',
 '著者脚注として全内容を主張するeijfを帰属し、引用例の末尾の注番号1)から同じ注を指す。注一覧で末尾に配置されたことを本論の時系列や因果とせず、現在の論述範囲での不議論の方針を保持する。',
 '同所だけに限定せず近接も許し、遠隔の任意の場所や数値閾値を加えない。抽象化の必要を実施済み・十分性・不精密さの消滅へ替えず、不議論を議論不能・永久禁止・問題不存在へ替えない。gleichfallsの比較対象の固有名や件数も補わない。',
 '不精密さは理想的な同時性概念と有限の広がりを持つ物理的記述の対応上の問題、抽象化はどの差を捨象して局所一致を使うかを定める操作として明示した。問題名や原語だけで内容を代用せず、同時性の既存定義と局所範囲を引用する。',
 '原刊照合、厳密な同所・近接・遠隔の対照、同じ論点と操作型の接続、必要性と非実施、添加と不議論、帰属と注番号の検査を固定した。局所規約の充足を物理的な理想化の妥当性や同義性の自動証明としない。',
 '関係節を含む全脚注を通読し、不精密さの所在から必要な抽象化と現在の不議論までを同じ問題について保持していると判断する。本文の局所例の理想化への留保として参照が接続され、明示した読みの未処理項目はない。',
)

@lru_cache(None)
def review_record(unit_id):
    assert unit_id in REVIEWS
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));unit=next(u for u in inv['units'] if u['id']==unit_id)
    ds={d['name']:d for d in catalog.document['declarations']};paragraph=unit_id.endswith('u0010')
    if paragraph:
        assert len(unit['text'])==666 and sum(not c.isspace() for c in unit['text'])==560 and not unit['math_ids']
        spans=[]
        for path,expected in zip(READINGS,([224,225],[226],[227])):
            rec=json.loads(read(path));validate_hashes(ROOT,rec['source_sha256']);assert rec['source_text_sha256']==unit['text_sha256'] and rec['source']==unit['text'][slice(*rec['range'])] and rec['selection']==selection_binding(catalog,expected)
            spans.extend(rec.get('sentence_ranges',[rec['range']]))
        assert spans==[list(s) for s in SPANS]
        assert sum(sum(not c.isspace() for c in unit['text'][a:b]) for a,b in SPANS)==560
        assert all(ds[n]['body']['force']=='assert' for n in ('eiin','eiis','eiiz','eijb'))
        indices=[224,225,226,227];reasons=PARAGRAPH_REASONS;interpretation=PARAGRAPH_LIMITS
    else:
        assert len(unit['text'])==212 and sum(not c.isspace() for c in unit['text'])==185 and not unit['math_ids']
        assert ds['eijf']['body']['force']=='assert'
        indices=[228];reasons=NOTE_REASONS;interpretation=NOTE_LIMITS
    source=json.loads(read(SOURCES[1]));assert source['note_anchor']==dict(unit='einstein-1905:u0010',range=[482,666],printed_marker='1)',target='einstein-1905:u0279')
    note=next(u for u in inv['units'] if u['id']=='einstein-1905:u0279');assert source['segments'][2]['text']==note['text'] and source['segments'][2]['unit_sha256']==note['text_sha256']
    def get(parent,callee):
        found=[c for c in calls(ds[parent]['body']) if c['symbol']==callee];assert len(found)==1;return found[0]
    assert get('eijc','eisfo')['arguments']==get('eijg','eisfo')['arguments']
    assert get('eijg','eir3')['arguments'][0]==dict(kind='call',symbol='eisfn',arguments=[])
    assert get('eijc','eir5')['arguments'][2]==dict(kind='call',symbol='eise3',arguments=[])
    assert get('eija','eisfd')['arguments'][1]==get('eija','eisfe')['arguments'][1]
    note_calls={c['symbol'] for c in calls(ds['eije']['body'])};assert {'eisfq','eisfs','eisfu','eisft'}<=note_calls
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    evidence=dict(source_reading=list(SOURCES),formal_checks=list(REPORTS),semantic_reading=list(DOCS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,*SOURCES,*REPORTS,*DOCS,*READINGS,'scripts/review_time_paragraph_and_note.py','tests/test_time_paragraph_and_note_review.py','scripts/check_einstein_principles_paragraph.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (*SOURCES,*REPORTS,*READINGS):
        rec=json.loads(read(path));validate_hashes(ROOT,rec['source_sha256']);merge_pins(pins,rec['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=unit_id,reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])],math=[]),selection=selection_binding(catalog,indices),source_order_statements=indices,interpretation=interpretation,
        limits=['明示した読みの下で内容・範囲・参照・提示を照合したアシスタントの判断。独立査読、全ての歴史的解釈、同義性の自動証明、物理的な実測や理想化の一般的妥当性を主張しない。','後続の原文単位と二作品全体の記述は未完で、目標は継続する。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=evidence,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for unit,path in REVIEWS.items():write_exact(ROOT/path,json.dumps(review_record(unit),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));verified={};pins={}
    for unit,path in REVIEWS.items():
        record=review_record(unit);assert json.loads(read(path))==record
        result=validate_review(ROOT,path,'einstein-1905',active,catalog,inv);verified[unit]=result['source_nonblank_characters'];merge_pins(pins,record['source_sha256']);pins[path]=digest((ROOT/path).read_bytes())
    assert verified=={'einstein-1905:u0010':560,'einstein-1905:u0279':185}
    return dict(status='time_description_paragraph_and_author_note_holistically_reviewed',document=FULL,source_units=verified,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
