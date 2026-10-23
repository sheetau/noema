"""Review the moving light trial, both displayed equations and author note."""
from functools import lru_cache
import json,re
from xml.etree import ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_moving_trip_reading import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS

DOC='docs/moving-trip-reading-v1.md';SOURCE='data/einstein-moving-trip-reading-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';REPORT='reports/moving-trip-reading-v1.json'
PRIOR='data/einstein-carried-clock-synchrony-review-v1.json'
DEPENDENCIES=('reports/moving-trip-geometry-v1.json','reports/carried-clock-synchrony-v1.json','reports/rod-methods-v1.json','reports/second-principle-v1.json')
NUMBERS=(36,37,38,39,280);COUNTS=(343,0,3,0,130)
REVIEWS=tuple(f'data/einstein-moving-trip-reading-u{n:04}-review-v1.json' for n in NUMBERS)
REASONS=(
 '原刊896/897頁と固定u0036〜u0039・注u0280を照合した。二式の分母V−v/V+v、帰着時刻のprime、頁をまたぐund、896頁のZur Zeitへの注1)を保持する。',
 '各時計のそばの共動観測者と第一節の判定適用、同じ光の出発・反射・帰着を結ぶ。現在の静止系測定の長さと三記録を二式へ接続し、時刻は局所静止系時刻かつ同所の動く時計の表示とする。',
 '同じ棒xi・端xn/xo・時計zaj/zak・光zax・三記録zas/zat/zau、静止系ra、単位ta/rb/tb、原理eiot、第一節eisdyと判定biを保持する。r_ABはzav、t_A/t_B/t_A′は各記録のzag/zahである。',
 '追加の想定ug/zaoと現在の結果提示eismjを分け、全直線軌道と式を初めから想定へ含めない。注は現在の時間使用への説明・補足として本文の局所位置へ結ぶ。undとzugleichをそれぞれ連言と同一値の二つの読みとして保持する。',
 '判定の適用から同期成功を導かず、動く時計へ静止条件qoを課さない。初期長との等値、往復係数、別系の時刻、原理だけの十分性・自動証明・実測結果を追加しない。u0040の観測者別の判断は別に残す。',
 '代表位置の共動と全世界線、現在の測定方法eip6、同じ出来事の局所時刻eiq2、実切断の二式sdbを合成する。時間の語の説明eitqは同じ二時計の任意の適格記録を扱い、三つの記録だけへ縮めない。',
 '原刊画像・固定原文と数式構造、既存の意味判断と検査を保存する。検査は接続・数値式・引用の非実行を調べるもので、全実数履歴や物理法則の真理、意味同値の自動証明ではない。',
 '直前の時計設定、二式に続くr_ABの説明、原刊脚注と照らして五単位を通読した。想定・結果提示・局所的な時間の説明という明示した読みの下で、各単位の内容と文書上の役割を保持していると判断する。',
)

def prose(s):return sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',s))

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));units=[next(u for u in inv['units'] if u['id']==f'einstein-1905:u{n:04}') for n in NUMBERS]
    assert [prose(u['text']) for u in units]==list(COUNTS)
    maths={m['id']:m for m in inv['math']};forms={n:''.join(ET.fromstring(maths[n]['mathml']).itertext()) for u in units for n in u['math_ids']}
    for n,denom in (('M0060','V−v'),('M0061','V+v')):
        frac=ET.fromstring(maths[n]['mathml']).find('.//{*}mfrac');assert frac is not None
        assert ''.join(frac[1].itertext()).replace(' ','')==denom
    assert forms['M0055']==forms['M0059']=='A' and forms['M0057']=='B'
    bindings={'M0054':'zag(zas) = zah(zas): t_A','M0055':'xn: A','M0056':'zag(zat) = zah(zat): t_B','M0057':'xo: B','M0058':'zag(zau) = zah(zau): t_A prime','M0059':'xn: A','M0060':'sdb: (tc-yb)*(zag(zat)-zag(zas)) = zav; zav via eip6','M0061':'sdb: (tc+yb)*(zag(zau)-zag(zat)) = zav; zav via eip6'}
    paths={INVENTORY,DOC,'scripts/review_moving_trip_reading.py'}
    for receipt in ('artifacts/einstein-rod-methods-v1/retrieval.json','artifacts/einstein-moving-trip-v1/retrieval.json'):
        paths.add(receipt)
        for row in json.loads(read(receipt))['sources']:
            assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-moving-trip-reading-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['896','897'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=prose(u['text']),math=[dict(id=n,sha256=maths[n]['sha256'],printed=forms[n],binding=bindings[n]) for n in u['math_ids']]) for u in units],observations=['Wir denken uns fernerと接続法の光往復は追加の想定。finden wirは現在の結果の提示。','896頁末尾の往路式に897頁冒頭のundと復路式が続く。','注1)はZur Zeitの直後に付き、静止系時刻とその場所の動く時計の表示の両方を説明する。インベントリのpage_at_end=921は実際の掲載頁として使わない。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def record(i):
    catalog=load_catalog(ROOT,BASIS);segment=source_record()['segments'][i]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,SOURCE,REPORT,PRIOR,*DEPENDENCIES,'scripts/review_moving_trip_reading.py','tests/test_moving_trip_reading_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    indices=list(INDICES) if i==0 else [263] if i==4 else [262]
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=segment['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=segment['unit_sha256'],text=segment['text'],range=segment['range'],math=[{k:m[k] for k in ('id','sha256')} for m in segment['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,interpretation=LIMITS,limits=['明示した解釈の下のアシスタントによる通読判断。独立査読や同義性の自動証明ではない。','共有された想定・二式・脚注の文脈を用いて各全単位を確認する。u0040以降と二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for i,path in enumerate(REVIEWS):write_exact(ROOT/path,json.dumps(record(i),ensure_ascii=False,indent=2)+'\n')

def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for i,path in enumerate(REVIEWS):
        rec=record(i);assert json.loads(read(path))==rec
        validate_review(ROOT,path,'einstein-1905',active,catalog,inv);assert prose(rec['source']['text'])==COUNTS[i]
        merge_pins(pins,rec['source_sha256']);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='moving_trial_two_results_and_time_note_whole_units_reviewed',document=FULL,source_units={f'einstein-1905:u{n:04}':c for n,c in zip(NUMBERS,COUNTS)},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':5},semantic_equivalence_automatically_proved=False,source_sha256=pins)
