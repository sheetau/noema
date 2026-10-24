"""Review the five units of the coordinate application and its beta supplement."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_field_transformation_application import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_field_transformation_application import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/field-transformation-application-v1.json'
REVIEWS=tuple(f'data/einstein-field-transformation-application-u{n:04d}-review-v1.json' for n in range(156,161))
CLAUSES=(
 (('Wenden wir auf diese Gleichungen die in § 3 entwickelte Transformation an, ',['ejtk','ejtl','ejs6','ejeh','eisov','zd3'],'直前の同じ仮定の式へ、第三節で展開した最終四座標変換を適用する著者の書換え提示。'),
  ('indem wir die elektromagnetischen Vorgänge auf das dort eingeführte, mit der Geschwindigkeit [M0290] bewegte Koordinatensystem beziehen, ',['ejte','ejtf','ejtg','ejth','ejti','ejtj','eig3','eivz','eiy6'],'同じ電磁過程の全出来事を、第三節で導入した同じ速度vのkとKの座標へ結び、場の引数も同じ逆写像で変更するという操作を保持する。'),
  ('so erhalten wir die Gleichungen:',['ejtl','ejtn','s6o','eispq'],'この適用によって後続の六式を得ると提示する。一般的な導出の妥当性を処理系が認定したことへ替えない。')),
 (('[M0291]',['s6i','s6j','s6k','s6l','s6m','s6n','s6o','ejti','ejtn'],'原刊907頁にある変換後の第一–第四式。新座標の関数として読んだ同じXと混合成分の偏微分・差の符号を保ち、次頁の二式へ続ける。'),),
 (('[M0292]',['s6i','s6j','s6k','s6l','s6m','s6n','s6o','ejtn'],'原刊908頁冒頭にある第五・第六式。前頁の四式と同じV・v・β・場・新座標領域を使う一つの六式群として保持する。'),),
 (('wobei',['ejtm','ejtn','uh','uf','eispr'],'直前の変換式に使うβの意味を続く式で補う接続。無関係な新法則や別の条件節にせず、同じ一文の補足にする。'),),
 (('[M0293]',['spq','soy','stw','sjd','ejtm','ejtn'],'同じV,vに対する正のβ=1/√(1−(v/V)²)を指定する。直前の六式で用いた係数を第三節と同じ規約に固定する。'),),
)
SEMANTICS=(
 'ejteは現在の二場と領域の同じ電磁過程を物理語彙へ結び、ejtf/ejtgは所属出来事の同じ両記録を結ぶ。ejth/ejtjは全出来事の両側の記録と全記録対を保ち、ejtiで最終四式と同じ逆座標写像を場の引数・領域に用いる。ejtlは同じ前提・元の式・結果・第三節参照を著者の提示へ合成する。',
 '電気側の三時間微分と磁気側の第一時間微分について、同じV、βとv/V、二場の混合、逆座標写像での関数合成、偏微分の軸と差を保持する。s6nは同じ変換された領域で六条件を一緒に要求し、四式だけの法則へ縮めない。',
 '磁気側の第二・第三時間微分の式を、先行四式と同じs6nの条件群に保持する。二つの左辺のβ(M+vZ/V)、β(N−vY/V)、右辺の対応する偏微分の軸と符号を保つ。',
 'ejtnでβ補足ejtmを同じ表示群の説明ufへ結び、表示後の本文順序ueを保つ。接続詞だけの真偽判定へ替えず、同じ六式で使う係数の指定という役割を一文の中で構成する。',
 '既存spqが保持する同じ正のVと対象速度vについて、βを正の逆平方根と同値なV/√(V²−v²)に結ぶ。別のv/Vをβと呼ぶ慣習、負の根、途中のφ付き係数へ交換しない。',
)
WHOLE=(
 '導入文全体を前の仮定から次頁の六式末尾とβまで連続して再読した。第三節の変換、その節で導入した速度vの系、同じ電磁過程の二座標での記述、式を得る提示を欠落なく保持したと判断する。',
 '原刊907頁の四式全てを各左辺・右辺・偏微分軸と差の符号まで再読した。改頁後の二式と合わせた同じ六式の第一部分を、明示した新変数による表示の読みの下で保持したと判断する。',
 '908頁冒頭の二式を前頁の四式と続けて再読した。同じ六式の残り二式であり、別の物理的な場の定義を追加しないことを確認した。全ての式を欠落なく保持したと判断する。',
 'wobeiを直前の六式と直後のβの式に接続して再読した。係数の補足指定という提示の役割を、同じ文の中で欠落なく保持したと判断する。',
 'β表示を原刊908頁の正の平方根と分母全体まで再読した。同じV・v・βの規約を保持して一文を閉じる補足として、欠落なく記述したと判断する。',
)


@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_field_transformation_application.py','tests/test_field_transformation_application_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
            f"固定{s['unit']}の全範囲と全数式要素{[m['id'] for m in s['math']]}を原刊907–908頁へ照合した。第三節の変換の適用、改頁をまたぐ六式、wobeiとβを一続きの文として読み、ハッシュを固定した。",
            SEMANTICS[i],
            'K/kはra/zbm、同じ比較設定はzb6、V/vはtc/zb7、二場と領域はznl/znm/znkへ固定する。元の仮定ejs6を同じ設定に適用し、第三節eismsで展開した最終ejehとそこで導入した表記規約eiy6を参照する。全所属出来事と両記録を共有する。',
            'zd3は著者が変換により式を得ると述べる提示である。式の表示はeisox、wobeiとβはuhとufの補足、同じ著者・論説への帰属はeir3で保持する。引用の真理や導出の健全性を自動認定しない。',
            '過程の範囲を成功標本だけへ限定せず、全所属出来事の両側の記録と全同一出来事対を保つ。同じ写像の逆像で領域を変え、旧新の数値を同じ地点へ代入しない。混合成分を後続u0161の移動系の測定場と先取りして同一視せず、発散条件も追加しない。',
            '電磁過程は既存の電荷輸送・電気側・磁気側作用の閉じた規約eig3へ接続する。新しい基本関係は過程の二場による物理的記述の帰属と全所属出来事の指定であり、座標測定・局所時計・系の運動・四式・場の混合と逆写像は合成で保持する。新しい他の記号は過程群と二箇所の参照だけである。',
            '同じ過程・出来事・両記録の全引数、全所属範囲の両記録の存在、全記録対への逆変換、四座標の各位置、元の仮定と最終変換の文脈、第三節参照・六式・βの提示を対照した。既存の場の混合・逆像・全関数域拒否と、六回転式だけでは前提不足となる反例をハッシュで保持する。局所例は全実数や原文意味の自動証明ではない。',
            WHOLE[i],
        )
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['明示した読みの下でのアシスタントによる全単位の通読判断。独立査読や意味同値の自動証明ではない。','著者の書換え・導出の提示を記述した判断であり、六回転式だけからの一般的な帰結を証明したものではない。反例と必要条件の区別を保持する。','u0161以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r;validate_review(ROOT,p,'einstein-1905',active,catalog,inv)
        merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='field_transformation_application_five_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=4,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':5},semantic_equivalence_automatically_proved=False,source_sha256=pins)
