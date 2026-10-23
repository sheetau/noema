"""Whole reading of the physical-meaning question and transverse endpoint displays."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_transverse_endpoint_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS
from scripts.check_transverse_endpoint_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/transverse-endpoint-claim-v1.json'
REVIEWS=tuple(f'data/einstein-transverse-endpoint-u{n:04d}-review-v1.json' for n in (97,98,99,100))
CLAUSES=(
 (
  ('Wir fragen nun nach der Bedeutung von [M0170]. ',['ejco','zhg','spc','ejcs'],'同じ著者が直前の相反積に続く今の議論で、同じφの物理的意味を問う。'),
  ('Wir fassen das Stück der [M0171]-Achse des Systems [M0172] ins Auge, ',['ejcp','ejck','eisnx'],'kの第二軸の指定区間を同じ対象として考察へ取り上げる。'),
  ('das zwischen [M0173] und [M0174] gelegen ist. ',['ejb7','ejca','ejcb','ejcc','ejck'],'二端(0,0,0)と(0,l,0)の間の全閉区間を占めるという対象の特徴。'),
  ('Dieses Stück der [M0175]-Achse ist ein relativ zum System [M0176] mit der Geschwindigkeit [M0177] senkrecht zu seiner Achse bewegter Stab, ',['ejcf','ejcd','ejcl','eipf','eiu6'],'その同じ軸区間を同じ棒とし、Kに対する全点の速度vの並進と自軸への直交を述べる。'),
  ('dessen Enden in [M0178] die Koordinaten besitzen:',['ejcg','ejci','ejcj','ejcq','ejcw'],'その棒の両端の現在K座標をコロン以下の二項へ結ぶ。対象全時刻での存在と全記録への式を保持する。'),
 ),
 (('[M0179]',['ejcm','ejcj','srw','sry','srx','ejcq'],'第一端はη=l側。x₁=vt、y₁=l/φ(v)、z₁=0を同じ時刻・端のK座標として提示する。'),),
 (('und',['ejcq','eiskj','ejcm','ejcn'],'同じコロンに続く第一端と第二端の両表示を連言として結び、その順序を保持する。'),),
 (('[M0180]',['ejcn','ejcj','srw','sry','ejcq'],'第二端はη=0側。x₂=vt、y₂=0、z₂=0と末尾句点を同じ棒の列挙の終わりとして読む。'),),
)
REASONS=(
 (
  '固定u0097の全350文字・非空白本文235文字とM0170–M0178を保存した原刊902頁へ照合した。Wir fragen nunから第三文のコロンまで三文を読み、続く両端表示との接続を確認した。',
  '意味への問い、対象へ考察を向けること、指定全区間、同じ区間の棒としての説明、Kに対する速度v、自軸との直交、同じ棒の両端座標の導入を分けて構成した。問いを解答や値の計算へ替えず、両端だけの配置で区間全体を代用しない。',
  'φは同じ正規化後spc、vはzb7、kはzbm、Kはra、棒はzgu、lはzgz。Dieses Stückとdessenを同じ棒へ結び、印字Hをkの第二軸ηの役割として読む。前段の縦棒や第三系K′へ参照を移さない。',
  'nunは前の相反積に続く談話上の移行、wirは同じ著者の論述上の声。zhgの問い、eisnxの考察対象の選定とugの設定採用、uhによる棒とその座標の主張を別々に保持し、三つとも同じ著者・論説・第三節へ帰属する。',
  '閉区間全体を理想化した線状棒として読むことを明示する。物質を切断したという操作、t=τ、φの正値又はφ=1、後続の測定長・反転対称性を加えない。棒の全点・全時刻の履歴を保持し、現在記録の存在を一組だけの標本へ狭めない。',
  '軸区間はejb7/ejcaの包含と全高さの被覆、全履歴と静止はeipe、全点並進はeipf、直交はeiu6、現在測定はejce/eiyx/sbへ合成する。新しいeisnxは対象・特徴の記述・範囲を取る汎用の考察関係で、物理内容や原文一文を原始語へ埋め込まない。',
  '原刊画像・固定本文・意味規約の通読に、全区間と物理履歴の先行証拠、三つの記録量化の二値域での各位置検査、時刻範囲の例化、純粋数式の本体、引用・列挙・著者帰属の対照を合わせる。全実数時刻の有限評価を拒否し、未知値を補わない。',
  '第一文の問いから、同じ軸区間の選定、同じ棒の運動とコロンまでを再読した。閉区間の理想化、談話上の現在、対象区間の任意時刻における現在記録という明示した読みの下で、三文の内容・参照・提示と次の二項への接続を欠落なく保持したと判断する。',
 ),
 (
  '固定u0098のM0179を原刊902頁の第一表示へ照合した。x₁=vt、y₁=l/φ(v)、z₁=0の三式であり、保存MathMLのmfracを確認し、平坦化文字列のlφ(v)を積と読まない。',
  '三空間成分を同じK記録の同じ時刻へ結ぶ。第一成分は速度と時刻の積、第二成分は同じ正の固有長と非零の同じφ(v)の商、第三成分は零。各K時刻に現在記録対が存在し、全該当記録が三式と同じ四変換を満たす。',
  '添字1は高いη=l側のzgwであり、η=0側zgvではない。l=zgz、v=zb7、φ=spcを前後と同一に保ち、K時刻tとk時刻τを混同しない。同じ出来事の二記録はejcgで物理履歴と測定へ結ぶ。',
  'u0097末のコロンに続く第一項eisnyとして、著者がejcmを主張する。eiskjの番号1は同じ列挙に属し、二つの別な実験や処理系の実測報告として扱わない。',
  '商を積や絶対値へ替えず、φの正値性・対称性・φ=1を先取りしない。表示は対象区間の任意時刻についての式と読み、一時点の値や両端の同一化へ狭めない。棒の測定長そのものの説明は後続へ残す。',
  'srwの四変換とkの端位置、sryの三空間式、srxの(lφ)/φ²による商を既存の意味規約のまま使う。ejcjが現在の同じ端点記録へ適用し、何を測ったかを未知の式名だけで代用しない。',
  '分数と添字の原刊通読に、正負の非零φ、各端・各時刻、全四座標の個別変更という有限対照を併記する。これは任意の実数体や物理世界の証明でも、テストから自動生成された意味判断でもない。',
  'コロンの後の第一表示を、その同じ棒と第二表示を参照しながら再読した。同じ現在記録と高いη側の端1、同じφ(v)の商という読みで、三式と列挙内の役割を欠落なく保持したと判断する。',
 ),
 (
  '固定u0099の全3文字undを原刊902頁の二つの端点表示の間で照合した。',
  '第一項と第二項を共に述べる連言であり、ejcqが二つの主張を同時に保持する。さらにeiskjとueで同じコロンの第一項から第二項への列挙順を保持する。',
  '接続先は同じ横棒zguのη=l側ejcmとη=0側ejcnである。無関係な二式、前の相反積又は後の測定長への接続にしない。',
  '二つの座標表示を同じ著者の同じ列挙として結ぶ語であり、新しい仮定、代替案、因果又は時間発展を示す語として扱わない。',
  '第一項だけ又は第二項だけではejcqを満たさない。両端を同じ端とせず、undから二つの出来事の物理的な時間順を導かない。',
  '連言の既存論理演算、各主張uh、同じ列挙の順位eiskj、本文順序ueを用いる。und一語専用の意味不明な原始語は作らない。',
  '原刊の二表示間の位置を読み、どちらかの主張の欠落・内容の交換・順位や導入箇所の交換を対照する。形式上の連言と本文順序の検査を、物理的な同時性の自動証明とはしない。',
  '第一表示、und、第二表示を続けて再読した。同じ棒の両端を共に列挙するという役割を、二つの内容と同じ提示範囲へ欠落なく結んだと判断する。',
 ),
 (
  '固定u0100のM0180を原刊902頁の第二表示へ照合した。x₂=vt、y₂=0、z₂=0と末尾句点を確認した。',
  '同じK記録の第一成分はvとその時刻tの積、第二・第三成分は零。各対象時刻の同じ端の二系記録の存在と、全該当記録への式を保持する。',
  '添字2は低いη=0側zgvであり、第一表示のη=l側とは区別する。同じ棒・K・k・速度・φを保持し、proper=0をejcnからejcjへ渡す。',
  '同じコロンの第二項eisnzとして、undに続き著者がejcnを主張する。句点はこの両端座標の提示を閉じ、次の測定長への結論とは分ける。',
  '零を未測定座標への補完値にせず、実際の現在記録を世界線・場所・同じ時刻の履歴へ結ぶ。x₂=0やt=τを追加せず、第一端のlをこの端へ代入しない。',
  '同じ既存srw/sryへproper=0を渡す合成を用いる。第二端だけの専用数式原始語を作らず、実切断の零・積・値同値と現在端点記録の意味規約を保つ。',
  '原刊の三式と句点の通読、proper=0の数値核の各座標変更、全時刻での記録存在と同じ出来事の二系対応の検査を併記する。有限評価器の限界と未知入力の拒否を保つ。',
  'undに続く第二表示と句点まで再読した。同じ棒の低いη側の端2を同じ任意K時刻の現在記録で述べるという読みの下で、三式と列挙の終わりを欠落なく保持したと判断する。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_transverse_endpoint_claim.py','tests/test_transverse_endpoint_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and len(REASONS[i])==len(REQUIREMENTS)
        selection=list(INDICES if i==0 else [INDICES[-1]])
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=LIMITS,limits=['全閉区間を理想化した線状棒とし、対象区間の任意K時刻の現在記録に両端式を述べるという明示した読みの下でのアシスタントの通読判断。独立査読、一般物理的導出、意味同値の自動証明ではない。','u0101以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r
        validate_review(ROOT,p,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='transverse_rod_question_and_endpoint_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=11,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},semantic_equivalence_automatically_proved=False,source_sha256=pins)
