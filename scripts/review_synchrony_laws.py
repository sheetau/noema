"""Collate the two numbered synchrony laws and record their whole-unit readings."""
from functools import lru_cache
import json
import re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_synchrony_laws import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/synchrony-laws-v1.md'
SOURCE='data/einstein-synchrony-laws-source-reading-v1.json';READING='data/synchrony-laws-reading-v1.json'
REPORT='reports/synchrony-laws-v1.json'
REVIEWS=('data/einstein-synchrony-symmetry-review-v1.json','data/einstein-synchrony-three-clock-review-v1.json')
PRIOR='data/einstein-consistent-synchrony-review-v1.json'
REASONS=(
 (
  '固定u0016全126文字・74非空白本文文字とM0031〜M0034を原刊894頁の番号1の全範囲へ照合した。場所記号は順にB・A・A・Bである。',
  'Bの時計がAの時計と同期するという前件から、Aの時計がBの時計と同期する結論への含意をeinaに保持する。各時計と場所の対応はeim7、同期条件は既存qoに接続する。',
  '二回のAをziqと時計eisib、二回のBをzirと時計eisikへ結ぶ。同じ系ra・単位rb・評価状況を共有し、前単位で予告した第一項eiskdを使う。',
  '著者による第一の一般法則qpの条件形での提示、番号1、前のコロンeiskcからの列挙と本文順序を保持する。前単位の仮定を物理的証明へ昇格させない。',
  'BからAへの向きをAからBへ取り違えず、前件が偽でも結論の同期を要求する無条件主張を足さない。文字の特定配置だけへ一般性を縮めず、新しい実測や絶対的時間の同一性を加えない。',
  '時計・地点の参照、一般法則の代表条件形での提示、番号付き列挙を意味規約に分離する。含意と場所対応、既存の全関連光往復による同期関係はNoemaの定義として合成する。',
  '原刊照合、前の仮定の固定判断、全真理値の条件検査、両方向の実際のqo本体への接続、著者・番号・参照の取り違え検査を記録する。有限例は全物理状況や意味同値の自動証明ではない。',
  '前のコロンから第一項を通読し、BがAと同期するならAがBと同期するという一般関係の印字順・内容・参照・提示を確認した。明示した読みの下でこの単位の未処理項目はないと判断する。',
 ),
 (
  '固定u0017全181文字・114非空白本文文字とM0035〜M0039を原刊894頁の番号2の全範囲へ照合した。場所記号は順にA・B・C・B・Cである。',
  '同じA時計がB時計ともC時計とも同期する二前件の連言から、B/Cの相互同期へ含意するeinbを構成する。両方向の結論は一般のqqでB/Cの代入順を交換した場合も含むことに対応し、法則を強めない。',
  '前件を共有するA時計eisibを同じ場所ziqへ、B時計eisikをzirへ、新たな代表C時計eiskgを場所eiskhへ結ぶ。結論も同じB/C・系・単位・状況を使い、予告済み第二項eiskeへ接続する。',
  'sowohl/als auchを連言、relativ zueinanderをB/C相互の関係として保つ。著者による一般法則qqの条件形での提示、同じ列挙の番号2、第一項からの順序を保持する。',
  '二つの前件を選言に弱めず、片方だけから結論を要求しない。前件のAを別時計へ分けず、結論の一方向だけを相互関係の全内容としない。原文にない個体不等式やC時計の設置済み、全時計の無条件同期を足さない。',
  'Cの時計・場所という役割参照と一般法則の提示を入力規約に分け、二前件・二方向の結論・含意・場所対応は合成する。相互同期という文全体を一つの真偽プリミティブへ置き換えない。',
  '原刊照合と通読を全16通りの条件検査、三対象の全512関係での一般条件と両方向の条件の比較、引数と提示の取り違え検査に分けて記録する。有限関係の確認を任意個数での物理的実現可能性の証明としない。',
  '前の仮定と第一項を受ける第二項を通読した。同じAを共有する両前件、B/C相互の結論、一般性、番号と本文順序に未処理項目はないと判断する。次の同時性・時間の定義のまとめは別単位として残す。',
 ),
)


def prose_count(text):return sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',text))


def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    for i,(letters,count) in enumerate((('BAAB',74),('ABCBC',114))):
        u=inv['units'][15+i];s=u['text'];assert s.startswith(str(i+1)+'. Wenn die Uhr in') and prose_count(s)==count
        ms=[]
        for mid,letter in zip(u['math_ids'],letters,strict=True):
            m=math[mid];assert '<mi>'+letter+'</mi>' in m['mathml']
            ms.append(dict(id=mid,sha256=m['sha256'],printed=letter,place={'A':'ziq','B':'zir','C':'eiskh'}[letter],clock={'A':'eisib','B':'eisik','C':'eiskg'}[letter]))
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(s)],text=s,nonblank_characters=count,math=ms))
    paths=[INVENTORY,'artifacts/einstein-synchrony-continuation-v1/page-894.jpg','artifacts/einstein-synchrony-continuation-v1/page-894.html','artifacts/einstein-synchrony-continuation-v1/retrieval.json','scripts/review_synchrony_laws.py']
    return dict(version='einstein-synchrony-laws-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['894'],images=[paths[1]],segments=segments,observations=['番号1のB・A・A・Bと番号2のA・B・C・B・Cを画像に照合した。同じAを共有するsowohl/als auch、relativ zueinander、句点までを含める。','二項目は直前の一般関係を予告するコロンに続く。次のWir haben soからの定義のまとめはここに混ぜない。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def build_reading():
    paths=[INVENTORY,DOC,SOURCE,PRIOR,'scripts/review_synchrony_laws.py']
    return dict(schema_version='noema-connected-reading-1',status='two_numbered_conditions_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=source_record()['segments'],source_nonblank_characters=188,selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX,INDEX+1]),requirements={f'einstein-1905:u00{16+i}':[dict(requirement=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,rs)] for i,rs in enumerate(REASONS)},interpretation_limits=LIMITS,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining=['二単位の全体判断の登録、u0018の定義のまとめ'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def review_record(i):
    catalog=load_catalog(ROOT,BASIS);u=json.loads(read(INVENTORY))['units'][15+i];segment=source_record()['segments'][i]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,SOURCE,READING,REPORT,PRIOR,'scripts/review_synchrony_laws.py','tests/test_synchrony_laws_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,READING,REPORT,PRIOR):
        r=json.loads(read(p));validate_hashes(ROOT,r['source_sha256']);merge_pins(pins,r['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[{k:m[k] for k in ('id','sha256')} for m in segment['math']]),selection=selection_binding(catalog,[INDEX+i]),source_order_statements=[INDEX+i],interpretation=LIMITS[:-1],limits=['明示した解釈に基づくアシスタントの通読判断。独立査読・唯一の歴史的解釈・同義性の自動証明・物理的実現の証明ではない。','u0018以降と二作品全体の記述は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for i,p in enumerate(REVIEWS):write_exact(ROOT/p,json.dumps(review_record(i),ensure_ascii=False,indent=2)+'\n')


def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);pins={}
    for i,p in enumerate(REVIEWS):
        r=review_record(i);assert json.loads(read(p))==r
        validate_review(ROOT,p,'einstein-1905',active,catalog,json.loads(read(INVENTORY)))
        assert prose_count(r['source']['text'])==(74,114)[i]
        merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='two_numbered_synchrony_laws_whole_units_reviewed',document=FULL,source_units={'einstein-1905:u0016':74,'einstein-1905:u0017':114},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
