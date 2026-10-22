"""Connect the thinking dispositions to their apposition and unchanged lower regime."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_civic_spirit_sentence import REF,ANCHOR

PARENT='data/thinking-impulse-development-basis-v1.json'
MAIN='data/civic-spirit-sentence-basis-v1.json'
OLD='examples/v016/property-apposition.noema';OLD_BASIS='data/property-apposition-basis-v1.json'
LIBRARY='examples/v016/germ-regime-connection.noema';BASIS='data/germ-regime-connection-basis-v1.json'
HIGH='i b[h[a] e]'
FIELDS='community a lowerorder a higherorder a person a reference d view d'
ARGS='v community v lowerorder v higherorder v person v reference v view'
GROWTH=ARGS+' v process v start v end'
PRIMITIVES={
 'h27ar':('[a a '+HIGH+' a d] c',['node','author','referent','scope','context'],'同じ著者・論述範囲・提示文脈の名詞句が、渡した閉じた段階1の性質記述を名詞化して指すという解釈。性質を持つ人、植物個体、発達過程そのものとは区別する。同じ真偽を持つ別記述に替えず、指示から実際の性質の成立は導かない。'),
 'h27as':('[a a a a d] c',['first','second','author','scope','context'],'同じ著者・範囲・提示文脈で後の箇所が前の箇所の指示を説明する談話関係。同じ指示又は本文順序だけから自動では導かない。nämlichの説明的同格へ適用する。'),
 'h27at':('[] a',[],'固定原文kant-1784:u0017第四文[762,772)の芽の名詞句den Keim, の箇所。描写物や性質を持つ本人とは別の本文箇所。'),
 'h27au':('[] a',[],'固定原文kant-1784:u0017第四文[807,853)のnämlichで導かれる二性向の説明句の箇所。'),
 'h27av':('[] a',[],'固定原文kant-1784:u0017第四文[716,871)の条件前件を扱う論述範囲。前件が実際に成立しているとは含意しない。'),
 'h27aw':('[] d',[],'固定原文kant-1784:u0017第四文の論述提示文脈。発達の時点、比較の固定基準、第三文の提示文脈とは区別する。'),
}
MEANINGS={
 'r6i3':'同じ共同体・法秩序・固定基準で、指定時点に法秩序が運用され、全関連成員・市民的行為の許可集合が指定基準時点と一致する。許可の追加と喪失の双方を検出する。基準時点の法秩序運用や低い側という比較は呼出側で要求する。',
 'r6i4':'同じ本人の同じ心理的発達履歴で、開始と終点の間にある両端を含む時点。通常性の比較場面や発達区間外を制度保持の対象へ混ぜない。履歴の順序適合はr6iyで別に要求する。',
 'r6i5':'第三文と同じ指定比較範囲・共同体・二法秩序・固定基準について、指定観点の低い側が高い側より真に少ない市民的許可を持つ。r6iyの同じ本人・過程・両端による二性向の発達を要求し、その全発達区間で低い側の法秩序と同じ許可集合を保つ。制度の変更による発達へ取り替えない。',
 'r6i6':'同じ比較組・本人・基準・比較観点・開始点について、候補終点に至るr6i5の過程がある内容。比較の評価点と発達の終点を同一視しない。',
 'r6i7':'同じ比較組・本人・基準・比較観点を保ち、指定終点までにr6i6の開始点がある内容。全員同時の発達、終点後の永続、実際の思考実行は加えない。',
 'r6ja':'同じ共同体・固定基準で、人を引数とするr6iwの二性向の組を返す。発達の過程ではなく、その人に両性向が顕在化する時点ごとの性質。',
 'r6jb':'共同体と固定基準の閉じた呼称をr6jaへ適用して得る段階1の閉じた性質記述。r6isの活動対象と区別し、作成時に心理応答や思考の実行を評価しない。',
 'r6jc':'共同体・基準の呼称を照合し、芽の名詞句とnämlichの説明句を、同じr6jbの二性向の性質へ結ぶ。rytで別箇所、同じ著者・範囲・提示文脈、本文の正順と逆順の不在、説明関係を要求する。性質の実在や植物と人の物理的同一性を断言しない。',
 'r6jd':'第三文と同じ固定基準h26zj・本文現在の比較観点を明示して、同じ比較組と本人のr6i7を取り出す。後続条件文へ渡す対象側の発達内容であり、第四文全体ではない。',
 'r6je':'第三文と同じ固定基準で、同じ共同体の二性向についてr6jcの同格を結ぶ。r6jdが発達させる同じr6iwを性質の参照先とする。',
}
LIMITS=[
 'u0017第四文前件の対象側について、直前の低い自由の制度条件下での発達と、芽を二性向で説明する同格を接続する依存群。自然・植物の芽・硬い物体の物理的描写や世話まで完成したとはしない。',
 'このharten Hülleの先行範囲を第三文の低い市民的自由の側とする保存済み読解を採用する。現在の正本の同じ比較範囲・人間成員・全市民的行為・法秩序・固定基準へ結ぶ。低い側というラベルだけで大小を認定せずr6hgを評価する。',
 '発達中は同じ低い法秩序を運用し、市民的許可集合を比較時点と一致させるという明示した強い読み。原文が全ての制度変動を禁止すると証明したとはしない。精神的な態度の変化と市民的許可の保持を分け、心理的変化そのものを禁止しない。',
 '同じ本人の発達履歴を使い、両端とその間の全時点で制度を保つ。履歴の区間外や、性向を調べる仮想的通常場面は制度保持の範囲にしない。履歴を成功点だけへ切り詰めないという既存入力規約を保つ。',
 'nämlichは名詞化した同じ二性向の性質を後の句で説明する同格として読む。植物の芽の個体、人、発達過程、実際の自由な思考活動はそれぞれ別に扱う。引用された性質の成立を同格の成立条件へ加えない。',
 '群全体の条件文への人口・時点の量化は未統合。自然の作用と擬人化、植物の芽と対象側の対応、硬さと優しい世話、反作用・行為能力・政府・尊厳・著者注参照も残す。新しい意味確認文字数と全文判断は加算しない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def main_catalog():return load_catalog(ROOT,MAIN)
@lru_cache(None)
def legacy():
    doc=parse((ROOT/OLD).read_text(encoding='utf-8'))
    return closure(doc,('ryt',)),json.loads((ROOT/OLD_BASIS).read_text(encoding='utf-8'))['definitions']['ryt']

def definitions():
    def option(point):return 'k r6hf[v community v order v citizen v activity v reference v '+point+']'
    text='d r6i3[community a order a reference d baseline d point d] c['+both('k r6fr[v community v order v reference v point]',
      'f citizen a[f activity a[y[k r6he[v community v citizen v activity v reference]][e['+option('baseline')+']['+option('point')+']]]]')+'].\n'
    scope='v community v person v reference v start v end'
    text+='d r6i4[community a person a reference d start d end d point d] c['+both('k h27am['+scope+' v point]',
      'x[e[v point][v start]][k h27an['+scope+' v start v point]]',
      'x[e[v point][v end]][k h27an['+scope+' v point v end]]')+'].\n'
    low='k h26yy[v community v reference v view]';high='k h26yz[v community v reference v view]'
    text+='d r6i5['+FIELDS+' process a start d end d] c['+both('k h26zi[v community v lowerorder v higherorder v reference]',
      'k r6hg[v community v lowerorder v higherorder v reference '+low+' '+high+']',
      'k r6iy[v community v person v reference v process v start v end]',
      'f point d[y[k r6i4['+scope+' v point]][k r6i3[v community v lowerorder v reference '+low+' v point]]]')+'].\n'
    text+='d r6i6['+FIELDS+' start d] e[b end[g process a[k r6i5['+GROWTH+']]]].\n'
    text+='d r6i7['+FIELDS+'] e[b end[g start d[t[k r6i6['+ARGS+' v start]][v end]]]].\n'
    text+='d r6ja[community a reference d] h[a] e[i[person a][k r6iw[v community v person v reference]]].\n'
    text+='d r6jb[community i[a] reference i[d]] '+HIGH+'[o a[r b[p r6ja]][v community v reference]].\n'
    text+='d r6jc[community a reference d] c['+both('k r6it[v community v reference]',
      'k ryt[k h27at[] k h27au[] k wa[] k r6jb[k h223g[v community] k h223h[v reference]] k h27av[] k h27aw[] p h27ar p ue p h27as]')+'].\n'
    text+='d r6jd[community a lowerorder a higherorder a person a] e[k r6i7[v community v lowerorder v higherorder v person '+REF+' '+ANCHOR+']].\n'
    text+='d r6je[community a] c[k r6jc[v community '+REF+']].\n'
    return text

def build():
    p=parent();m=main_catalog();doc=deepcopy(p.document);doc['statements']=[];imported=dict(p.entries)
    for d in closure(m.document,('r6hg','r6he','h26yy','h26yz','h26zi','h26zj','h26kn','h26km','wa','ue')):
        n=d['name'];e=m.entries[n]
        if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=e
    ds,meaning=legacy();assert len(ds)==1 and ds[0]['name']=='ryt'
    if 'ryt' in imported:assert ds[0]==imported['ryt']['declaration'] and meaning==imported['ryt']['meaning_ja']
    else:doc['declarations']+=ds
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(m.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set(p.source_sha256)|set(m.source_sha256)|{OLD,OLD_BASIS}
    basis=dict(status='same_lower_regime_development_and_property_apposition_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|{'ryt':meaning}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()}|{'ryt':OLD_BASIS},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
