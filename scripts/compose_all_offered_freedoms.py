"""Quantify all offered-view collections and every unrestricted public candidate."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_clerical_duty_scope import CODE,quantify
from scripts.compose_confessional_divergence import NAMES
from scripts.compose_prince_sentence import ANCHOR

PARENTS=('data/clerical-duty-scope-basis-v1.json','data/revered-clerical-scope-basis-v1.json','data/offered-judgments-basis-v1.json')
LIBRARY='examples/v016/all-offered-freedoms.noema';BASIS='data/all-offered-freedoms-basis-v1.json'
COMPARISONS='i[h[a d] c]'
CANDIDATES=[('activity','a'),('audience','a'),('judgments','j[a]'),('insights','j[a]')]
LOCAL='person a office a church a creed a subject a scholar a reference d anchor d comparisons '+COMPARISONS
LARGS='v person v office v church v creed v subject v scholar v reference v anchor v comparisons'
GENERAL='person a scholar a reference d anchor d'
GARGS='v person v scholar v reference v anchor'
PRIMITIVES={
 'h26o6':('[a a a a d d] c',['organization','formulation','topic','item','reference','candidate'],
   '同じ組織の同じ採用定式化・主題と、同じ代表認識項目について、固定基準で同一論点の内容差を調べる全関連比較候補。組織・採用・論点対応・内容の同一性は別に構成し、相違が見つかった場合だけを候補に残さない。現実の真偽、発表や許可の成立、職務義務の履行によって範囲を変更しない。有限試験の状況集合を現実の全範囲と同一視せず、全範囲の供給は明示した解釈契約とする。'),
}
MEANINGS={
 'r542':'個体列の末尾へ同じ一個体を追加する。引用適用のための構成部品であり、列の順序・重複を捨てない。',
 'r543':'任意の有限個体列を、空列の閉じた記述からr542と各個体のh223g名を順に引用適用して閉じた列記述へ組み立てる。列のための新しい基本名付け関係や既知列一覧は導入しない。',
 'r544':'r543で作った閉じた列記述を脱引用し、元の列と一致することを確認する。別個体への呼称、順序や重複の欠落を許さず、空列も正確に扱う。',
 'r545':'同じ教会・採用信条・主題・固定基準についてh26o6の全比較範囲を代表項目と比較点の二引数へ保つ。',
 'r546':'同じ教会・信条・主題・基準の閉じた名前をr545へ適用した比較関数の記述。構築時に相違や発表を実行しない。',
 'r547':'同じ本人・段階1目標・束縛列・内容基準・基準点について、h26o4の全関連候補の一つでその同じ実行内容が成立する。許可・職務要求の保持又は履行を候補資格に入れず、現実の実行・物理的能力・審査成功を要求しない。',
 'r55a':'同じ七対象と二項目列・比較関数について、列名が正確で非空の発表内容r536にr547の候補がある。本人の見解保持・把握・信条からの差・公的発表・審査目的はその候補内に置き、許可時点に実際の発表がある者へ縮めない。',
 'r55b':'r55aと同じ二項目列をr543で閉じ、同じ七対象・比較関数・職務にr54oの自由と非免除・共充足を接続する。本文で同じ内容を記述し直すことによる規範対象のずれを防ぐ。',
 'r55c':'同じ本人・職務・教会・信条・学識者・基準について、少なくとも一つの発表候補があり、全活動・全公衆・全判断列・全洞察列のうちr55aに該当する各候補にr55bを要求する。既知の二列や許可済みの標本に全称範囲を限定しない。',
 'r55d':'先行文と同じ限定君主の下の敬意に値する同じ聖職者r54zについて、比較関数の四呼称を確認し、同じ本文現在点のr55cの全候補への自由を帰結とする。該当人物の存在や自由の無条件の事実をこの条件から補わない。',
 'r55e':'同じ本人・活動・学識者・公衆と二項目列の、教会や信条からの差を追加しない公的提示r53wにr547の候補がある。非聖職者へ採用信条を強制せず、列名の一致と非空性を保つ。',
 'r55f':'r55eと同じr53w・四対象・基準について、全cf職務の要求がその全発表候補を排除しないr54pを要求する。特定一職務又は一つの安全な実例だけでは成立しない。',
 'r55g':'r55eと同じr53w・四対象・基準への自由r37cを、同じ本人の学識者の規範源h247bへ結ぶ。義務が制限しないことから自由を自動導出しない。',
 'r55h':'同じ本人・学識者・基準についてr55eの発表候補が存在し、その全活動・全公衆・全判断列・全洞察列にr55fの全職務による無制約を要求する。der durch keine Amtspflicht eingeschränkt istを公的提示全般の人物条件として読む準備で、一発表だけの無制約と分ける。',
 'r55i':'同じ本人・学識者・基準についてr55eの候補が存在し、その全候補にr55gの自由を要求する。r55hの無制約からの論理的推論とせず、本文の帰結として別に主張するための条件。',
}
LIMITS=[
 'u0015第二文の全発表候補への自由を、任意の有限の判断列・洞察列と全活動・全公衆へ量化して構成する。聖職者側は同じr54zからr55dへ接続し、他者側の無制約と自由はr55h/iとして分ける。全人物範囲・jeder andere・noch mehr・全文帰属は未統合。',
 '項目列は一つの複合発表を構成する有限列だが、全列を量化するので、既知の列だけや固定長の標本を本文範囲にしない。r543は各要素の名前からNoemaで列の記述を構築し、原語列や外部参照で内容を代用しない。',
 '候補資格r547は規範比較の同じ一候補で発表内容自体が成立しうること。許可や義務履行を先に確認しないため、禁止された発表や職務との衝突を残す。h26o4の範囲そのものを成功例へ絞らず、候補内の発表実行から現実の発表を導かない。',
 '本人の判断保持・洞察・内容差は実行内容の候補内で確認する。現在すでに発表した人、審査を通過した内容又は現在真の内容だけへ対象を限定しない。少なくとも一つの候補は要求し、空の全称だけを自由や無制約の証拠としない。',
 '聖職者の比較範囲は同じ採用信条・主題・代表項目に固定し、本文束縛r55dで四つの名前を照合する。比較で差が出た点だけを選ぶものではなく、全範囲の解釈契約は有限検査では証明されない。',
 '他者の公的提示はr53wの四対象であり、同じ教会・信条・信条との差を必須にしない。der durch keine Amtspflicht eingeschränkt istは、いずれの職務義務もその人の該当公的提示全般を制限しないという人物条件として採る。個々の発表について条件付きに許すだけの弱い読みに置き換えない。',
 'r55hとr55iはそれぞれ無制約と自由である。両者の含意は定理として導出せず、全文で他者の同じ人物範囲の前件と帰結へ置く。noch mehrの論述上の強調と、先行の聖職者以外という他者範囲は別に接続する。',
 '全列の量化は有限評価器で拒否する。診断では列の量化域だけを明示した標本へ置き換え、全活動・全公衆と条件文の接続を実評価する。深い発表・規範・人物分類の証拠と接続境界を分け、診断結果を全域同値や全文意味判断に変換しない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def names(ns):return ' '.join('v '+n for n in ns)
def named(n):return 'k '+('h223h' if n=='reference' else 'h223g')+'[v '+n+']'
def target(clerical=True):return 'k '+('r536' if clerical else 'r53w')+'[k r543[v judgments] k r543[v insights]'+(' v comparisons' if clerical else '')+']'
def binding(clerical=True):return 'l[a]['+names(NAMES if clerical else NAMES[:4])+']'
def public_fields(clerical=True):return ' '.join(n+' a' for n in (NAMES if clerical else NAMES[:4]))+' judgments j[a] insights j[a] reference d anchor d'+(' comparisons '+COMPARISONS if clerical else '')
def public_args(clerical=True):return names(NAMES if clerical else NAMES[:4])+' v judgments v insights v reference v anchor'+(' v comparisons' if clerical else '')

def definitions():
    text='d r542[items j[a] item a] j[a][m[v items][l[a][v item]]].\n'
    text+='d r543[items j[a]] i[j[a]][q[v items][r[l[a][]]][i[code i[j[a]] item a][o a[r[p r542]][v code k h223g[v item]]]]].\n'
    text+='d r544[items j[a]] c[e[s[k r543[v items]]][v items]].\n'
    text+='d r545[church a creed a subject a reference d] h[a d] c[i[item a point d][k h26o6[v church v creed v subject v item v reference v point]]].\n'
    text+='d r546[church i[a] creed i[a] subject i[a] reference i[d]] '+COMPARISONS+'[o a[r[p r545]][v church v creed v subject v reference]].\n'
    text+='d r547[person a target '+CODE+' bindings j[a] reference d anchor d] c[g point d['+both(
        'k h26o4[v person v target v bindings v reference v anchor v point]',
        't[c[s[v target]][v bindings v reference]][v point]')+']].\n'
    valid=both('k r544[v judgments]','k r544[v insights]','u[e[d[m[v judgments][v insights]]][n p a b]]')
    for name,clerical in (('r55a',True),('r55e',False)):
        text+='d '+name+'['+public_fields(clerical)+'] c['+both(valid,'k r547[v person '+target(clerical)+' '+binding(clerical)+' v reference v anchor]')+'].\n'
    text+='d r55b['+public_fields()+' office a] c[k r54o['+names(NAMES)+' v office v reference v anchor k r543[v judgments] k r543[v insights] v comparisons]].\n'
    eligible='k r55a['+public_args()+']';freedom='k r55b['+public_args()+' v office]'
    text+='d r55c['+LOCAL+'] c['+both(quantify(CANDIDATES,eligible,'g'),quantify(CANDIDATES,'y['+eligible+']['+freedom+']'))+'].\n'
    comparison='k r546['+' '.join(named(n) for n in ('church','creed','subject','reference'))+']'
    frame='ruler a rulingoffice a community a person a office a church a creed a subject a scholar a reference d'
    conditions='k r54z[v ruler v rulingoffice v community v person v office v church v creed v subject v scholar v reference]'
    validcomparison=both(*('e[s['+named(n)+']][v '+n+']' for n in ('church','creed','subject','reference')))
    text+='d r55d['+frame+'] c[y['+conditions+']['+both(validcomparison,
        'k r55c[v person v office v church v creed v subject v scholar v reference '+ANCHOR+' '+comparison+']')+']].\n'
    t=target(False);b=binding(False);cases='i[point d][k h26o4[v person '+t+' '+b+' v reference v anchor v point]]'
    text+='d r55f['+public_fields(False)+'] c[k r54p[v person v anchor p h237z c[s['+t+']]['+b+' v reference] '+cases+']].\n'
    text+='d r55g['+public_fields(False)+'] c[k r37c[k h247b[v person v scholar v reference] v person v scholar '+t+' '+b+' v reference v anchor]].\n'
    eligible='k r55e['+public_args(False)+']'
    for name,conclusion in (('r55h','r55f'),('r55i','r55g')):
        text+='d '+name+'['+GENERAL+'] c['+both(quantify(CANDIDATES,eligible,'g'),
            quantify(CANDIDATES,'y['+eligible+'][k '+conclusion+'['+public_args(False)+']]'))+'].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for c,roots in zip(sources,(['r54o','r54p'],['r54z','h223g','h223h'],['r53w'])):
        for d in closure(c.document,roots):
            n=d['name'];e=c.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(MEANINGS)|set(PRIMITIVES))&set().union(*(set(c.entries) for c in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    paths=set().union(*(set(c.source_sha256) for c in sources))
    basis=dict(status='all_offered_candidates_and_person_wide_nonrestriction_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
