"""Bind complete epoch cohorts and earlier parties to the same mutual oath."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/covenant-nullity-basis-v1.json'
LIBRARY='examples/v016/epoch-undertakings.noema'
BASIS='data/epoch-undertakings-basis-v1.json'
TERMS='i[h[j[a]] e]'
PRIMITIVES={
 'h257z':('[d d d] c',['reference','candidate','point'],'同じ固定した議論の範囲と同じ候補において、前後の時代を読む経過の履歴にこの時点が属する。比較対象の時代を含む経過全体を与え、間の不都合な点だけを落とさない。候補は一つの経過を指定し、別候補の時点を混ぜない。順序は同じ候補のicで与える。'),
 'h26aa':('[a d] c',['epoch','reference'],'この固定基準で採る時代区分の全対象に、この時代が属する。直後関係を得るために中間の時代を除かず、目的や能力の判定結果で区分を選び直さない。特定の暦年幅・生物学的な一世代・親子関係を意味しない。'),
 'h26ab':('[a d d d] c',['epoch','reference','candidate','point'],'同じ固定区分・候補の中で、この点がこの時代の時間範囲に属する。各時代の範囲を全て与え、生存者や合意の成立に合わせて境界を動かさない。非空の区間、時代間の順序、全履歴の被覆は合成側で確認する。'),
 'h26ac':('[a a d] c',['agreement','person','reference'],'この人は同じ合意の同じ固定基準で、その条項を自ら引き受ける当事者の全範囲に属する。未表明者・未宣誓者を除かず、同時代の全生存者、後続集団、単なる受け手や同席者とも同一視しない。合意に正当な権限があるか、条項が実際に効力を持つかは含意しない。'),
}
MEANINGS={
 'r5bw':'同じ固定区分・候補の全時代について既存rjeの非空で順序付けられた区間を要求し、さらに同じ履歴内の全点がいずれかの選択時代に属することを確認する。時代間の未割当の時間を残したまま直後と判定しない。',
 'r5bx':'r5bwの全履歴を覆う区分の下で、同じ候補の生存関係h256oと全人類aa、候補点での全所属h246cをrjhへ接続する。各集団は各時代のいずれかの点で生存する全ての人と一致し、二集団は異なるが成員の重なりを許す。次の時代は同じ区分の直後とする。',
 'r5by':'合意の固定基準の全当事者が人であり、同じ候補における先行時代の集団に属する。先行集団の全員が当事者であるとは要求せず、後の時代だけに生存する者を混ぜない。',
 'r5bz':'同じ前後集団と二時代のr5bx、同じ合意の固定条項基準h254zが先行時代にあること、同じ基準の全当事者についてのr5byを結ぶ。固定した時代区分の基準と、個々の合意の条項基準を混同しない。',
 'r5ca':'同じ表明点が同じ先行時代に属し、本人の同じ合意・条項・引数への引受けh255bがあり、固定基準の他の全当事者に対するh255dの引受けと、その同じ行為・条項への宗教的宣誓r46xがある。行為の生起・担い手・基準以前の配置は外側のrhzで確認する。',
 'r5cb':'r5bzの同じ前後集団・時代・当事者に、二人以上の全当事者が同じ合意に割り当てた同じ条項を引き受けるrhzを結ぶ。r5caによりその同じ引受け行為を先行時代の相互宣誓とする。条項と引数関数は明示した引数に残し、後続集団への妨害目的を型だけで代用しない。',
}
LIMITS=[
 'Zeitalterをその時代に生きる人々という集団として読む。時代区分の基準を固定し、両時代に生きる同じ人を許す。集団の区別を成員の完全な入替えや血縁へ置き換えない。r5bxの対象は特定国や宗派に限定しない人類である。',
 '既存rjf/rjhの区分相対の直後関係に、対象履歴の全点を区分で覆うr5bwを加えた。旧定義・旧証拠は変更しない。現実の全時点や時代の境界の正しさは入力の責任であり、有限モデルで証明しない。',
 '合意当事者は先行時代の人々のうち、その合意を引き受ける者として全範囲を固定する。同時代の全人類の署名や、次の時代の者の同意を要求しない。当事者が先行集団全体を合法的に代表する資格もこの所属からは導かない。',
 '宣誓は直前の相互宣誓と同じ宗教的な呼びかけの読みを引き継ぎ、同じ行為・同じ条項に結ぶ。呼びかけ先の実在、誠実さ、履行、合意の正当性は断言しない。verschwörenの共謀的・否定的な提示は目的と規範的否認を統合する段階で残る。',
 'r5cbは条項と引数関数を明示した合意形成の構成。後続集団の知識の拡大・誤りの除去・啓蒙進展の不能性と、その状態を生じさせる目的・必然性・kann nichtの規範的否認、括弧の重要性、全文帰属はまだ結ばない。全文判断や確認済み文字数は増やさない。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

HISTORY='i[at d][k h257z[v reference v candidate v at]]'
BEFORE='i[first d last d][k ic[v first v last v candidate]]'
EPOCHS='i[epoch a][k h26aa[v epoch v reference]]'
PERIODS='i[epoch a at d][k h26ab[v epoch v reference v candidate v at]]'
FRAME=HISTORY+' '+BEFORE+' '+PERIODS
PAIR_FIELDS='firstgroup a nextgroup a earlier a later a agreement a reference d candidate d'
PAIR_ARGS='v firstgroup v nextgroup v earlier v later v agreement v reference v candidate'

def definitions():
    covered='f at d[y[k h257z[v reference v candidate v at]][g epoch a['+both('k h26aa[v epoch v reference]','k h26ab[v epoch v reference v candidate v at]')+']]]'
    text='d r5bw[reference d candidate d] c['+both('k rje['+EPOCHS+' '+FRAME+']',covered)+'].\n'
    succession='k rjh[v firstgroup v nextgroup v earlier v later '+EPOCHS+' '+FRAME+' v candidate p aa p aa i[person a at d][k h256o[v person v candidate v at]] p h246c]'
    text+='d r5bx[firstgroup a nextgroup a earlier a later a reference d candidate d] c['+both('k r5bw[v reference v candidate]',succession)+'].\n'
    text+='d r5by[firstgroup a agreement a anchor d candidate d] c[f person a[y[k h26ac[v agreement v person v anchor]]['+both('k aa[v person]','k h246c[v firstgroup v person v candidate]')+']]].\n'
    text+='d r5bz['+PAIR_FIELDS+'] c['+both('k r5bx[v firstgroup v nextgroup v earlier v later v reference v candidate]',
        'k h26ab[v earlier v reference v candidate k h254z[v agreement]]','k r5by[v firstgroup v agreement k h254z[v agreement] v candidate]')+'].\n'
    fields='earlier a reference d candidate d person a activity a agreement a terms '+TERMS+' bindings j[a] point d'
    others='f other a[y['+both('k h26ac[v agreement v other k h254z[v agreement]]','u[e[v person][v other]]')+'][k h255d[v person v other v activity v agreement v terms v bindings v point]]]'
    text+='d r5ca['+fields+'] c['+both('k h26ab[v earlier v reference v candidate v point]',
        'k h255b[v person v activity v agreement v terms v bindings v point]',others,'k r46x[v person v activity v terms v bindings v point]')+'].\n'
    declares='i[person a activity a agreement a terms '+TERMS+' bindings j[a] point d][k r5ca[v earlier v reference v candidate v person v activity v agreement v terms v bindings v point]]'
    formation='k rhz[v agreement v terms k h254z[v agreement] i[person a anchor d][k h26ac[v agreement v person v anchor]] v arguments p aa '+HISTORY+' '+BEFORE+' p h255a p dg p f3 '+declares+']'
    text+='d r5cb['+PAIR_FIELDS+' terms '+TERMS+' arguments h[a] j[a]] c['+both('k r5bz['+PAIR_ARGS+']',formation)+'].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['rje','rjh','rhz','r46x','h256o','h246c','h254z','h255a','h255b','h255d','aa','dg','f3','ic']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='complete_epoch_cohorts_and_earlier_mutual_oath_dependency',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
