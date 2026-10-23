"""Whole readings of K-time relative speed, the time value and its substitution."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_longitudinal_elimination import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_longitudinal_elimination import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/longitudinal-elimination-v1.json'
REVIEWS=tuple(f'data/einstein-longitudinal-elimination-u{n:04d}-review-v1.json' for n in (69,70,71,72))
CLAUSES=(
 (
  ('Nun bewegt sich aber der Lichtstrahl ',['ei52','eisnp','ei6b'],'同じ光について、kでの光速VからKで測る原点との相対速度へ観点を移す対照として読む。'),
  ('relativ zum Anfangspunkt von [M0124] ',['ei5y','eivx','eizm','ei5w','ei5x'],'同じk原点に対する光の運動を、同じ二時刻の両位置の差の変化として保持する。'),
  ('im ruhenden System gemessen mit der Geschwindigkeit [M0125], ',['ei5y','sna','eitf','se'],'両軌道を同じKの長さ・時間尺度へ結び、全区間での相対速度V−vを保持する。'),
  ('so daß gilt:',['ei52','zc','snt'],'その同じ相対運動から後続のtの式が得られるという著者の帰結を保持する。'),
 ),
 (('[M0126]',['snt','sni','sne','sna','ei54'],'同じ光線のK時刻と原点からの相対位置に対するx′/(V−v)=tを保持する。句点は数式内で固定されている。'),),
 (
  ('Setzen wir diesen Wert von [M0127] in die Gleichung für [M0128] ein, ',['ei55','sni','snh','ei56','zd3'],'同じtの値を先行する同じξのτ代入式へ入れる計算上の書換えを示す。'),
  ('so erhalten wir:',['ei56','snu','ei6a'],'その代入によって次のξの式を得るという著者の提示を保つ。'),
 ),
 (('[M0129]',['snu','snj','snb','ei56','ei6a'],'同じ光線上でξ=a*V²*x′/(V²−v²)を保持する。aは同じ未定φ(v)である。'),),
)
REASONS=(
 (
  '固定u0069全体とM0124/M0125を、原刊899頁末のAnfangs-から900頁冒頭のpunktへ続く文として照合した。次の時刻式まで読んだ。',
  'Nun ... aberの観点の対照、同じ光、k原点に対する運動、Kで測る条件、V−vという速度、so daßの帰結と後続式へのコロンを保持する。',
  '光は同じzez/zeyのwf、原点は同じkのzbnとzbv、速度は同じVとvである。光と原点の全軌道をKの同じ時刻・長さ単位へ結び、終点の補助x′を同時刻の位置差へ結ぶ。',
  'ei52で同じ光の測定上の対照を提示し、相対運動をuhによる著者主張、時刻式をzcによる帰結として述べる。ei54は同じ論説・第三節と先のξ表示からの順序を保持する。',
  'V−vをkで測る光速や光速原理への反例としない。原点は放出時に光と同所だが、光の到達出来事で同所にいるとは要求しない。同時刻の原点位置と全区間の運動を保つ。',
  '相対運動はei5w/ei5xの位置差と経過時間から構成し、実際の同じ原点の全履歴eizmと光軌道ei47へ結ぶ。対照は既存の共通観点付き規約の閉引用版を再使用し、文ごとの未説明語で代用しない。',
  '原刊二頁と固定原文、全時間量化を保つ定義、内部で曲がる同端点曲線、原点位置・時刻・対象の対照検査を根拠にする。一般の連続軌道や物理法則の自動証明ではない。',
  '前のkでのVとξの式から原刊の改頁をまたいで読み、tの式まで確認した。明示した測定観点の対照と同じ原点光線の読みの下で、文全体の参照・範囲・役割の欠落はないと判断する。',
 ),
 (
  '固定u0070のM0126全体を原刊900頁へ照合した。分母はV−v、分子はx′、右辺はtであり、句点は固定MathMLの内部に含まれる。',
  'x′/(V−v)=tの等号、商、速度の差と補助座標を保持する。sniは同じ領域でx′=(V−v)tも合わせる等価な読みである。',
  'tは同じ光の到達出来事のK時刻、x′はそのKのxから同じv*tを引いた値。V,v、原点、放出の零点を先行相対運動から保持する。',
  'ei52/ei54により先行相対運動から得る著者の帰結として記述する。無関係な三数の恒等式や、時刻の新しい定義に置き換えない。',
  '先行する正のvとv<V、t>0の範囲を保持し、零分母を許さない。tとτを同一にせず、原点からのK測定の相対位置をkのξへ替えない。',
  '既存sni/sna/sneの実切断による差・積・商と現在の原点軌道を使う。式を画像の引用や未説明の記号名として格納しただけにはしない。',
  '原刊と固定MathML、同じK位置・時刻を変える対照、既存の有理多項式補題を根拠にする。有限代入の成功を全実数の体の法則の証明とはしない。',
  '直前のV−vの説明から表示式と次の代入指示を通読した。同じ原点光線と測定尺度の読みの下で式全体と帰結の役割を保持したと判断する。',
 ),
 (
  '固定u0071全体とM0127/M0128を原刊900頁へ照合した。直前のtの表示と先行ξの式、直後の結果式を合わせて読んだ。',
  'この値という先行参照、代入先のξの方程式、値を入れる操作、そうすれば結果を得るという構造を保持する。',
  '代入する値は同じ光線のsni/sntのt、代入先は同じ出来事のsnh/snsである。ei55は同じV,v,φ(v),x′と原点の条件を保持し、別の式や時刻へ交換しない。',
  'Setzen wir ... einは著者が提示する計算上の代入として読み、ei56のzd3で前の式と結果を条件付き書換えへ結ぶ。ei6aは同じ著者・論説・第三節へ帰属する。',
  '実際の計算行為、実行日時、読者の参加、原文にない途中式の履歴を加えない。代入の前提を落として無条件の座標変換を得ることにもしない。',
  '型付きの閉引用と既存zd3による計算提示、実切断で定義した同じ二式とtの値を使う。自然言語の操作名だけで数式への接続を済ませない。',
  '原刊と固定原文、t・τ・x′・ξを別々に変える対照、未定係数を保った数値代入と既存の有理代数補題を根拠にする。一般的な計算の健全性の証明とは区別する。',
  '前のtの値、代入の一文、次の結果式まで再読した。著者による同じ値の計算提示という読みの下で、参照・操作・条件・帰結を欠落なく保持したと判断する。',
 ),
 (
  '固定u0072のM0129全体を原刊900頁へ照合した。分子V²、分母V²−v²、外側のaとx′、数式内部の句点を確認した。',
  'ξ=a*V²*x′/(V²−v²)の等号・係数・二乗・差・商・積を保持する。先行するtの代入から得る式である。',
  'ξとx′は同じ光の到達出来事の別の値であり、aは同じφの同じvでの値。Vとvを前の式と共有し、新しい係数や別の基準系にしない。',
  'ei56/ei6aは先行するξの式を同じtの値で書き換えた結果として同じ著者へ帰属する。単独の新しい定義や測定結果の報告にはしない。',
  'aを1に固定せず、光線上の式をここだけで光線外の全空間へ拡張しない。横二方向の光線と類推は次のu0073以降の範囲に残す。',
  'snj/snbの実切断による積と商、先行するsnhとsniを用いる。0≤v<Vの数値領域と今回の正の並進設定を区別し、零分母を受理しない。',
  '原刊と固定MathML、係数を変えた代入、K時刻とk時刻の区別、既存の有理多項式補題を用いた。有限の場合での一致から一般の変換を証明したとはしない。',
  '同じtの式と代入の文から結果まで通読した。明示した同じ原点光線の読みの下で、全式と代入結果という位置付けに欠落はないと判断する。',
 ),
)

@lru_cache(None)
def records():
    source=source_record();catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_longitudinal_elimination.py','tests/test_longitudinal_elimination_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and len(REASONS[i])==len(REQUIREMENTS)
        indices=[INDEX] if i<2 else [INDEX,INDEX+1]
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,clauses=clauses,interpretation=LIMITS,limits=['明示した測定観点の対照・原点光線・計算上の代入という読みの下でのアシスタントの通読判断。独立査読、一般の実数体・物理的導出や同義性の自動証明ではない。','u0073以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,r in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for path,r in zip(REVIEWS,records()):
        assert json.loads(read(path))==r
        validate_review(ROOT,path,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='relative_speed_and_time_elimination_whole_units_reviewed',document=FULL,source_units={s['unit']:s['source_nonblank_characters'] for s in source_record()['segments']},reviewed_math_elements=6,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
