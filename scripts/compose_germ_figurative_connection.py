"""Connect the actual lower-regime development and the composed germ depiction."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/nurtured-germ-basis-v1.json';MAIN='data/civic-spirit-sentence-basis-v1.json'
OLD='examples/v016/thinking-disposition.noema';OLD_BASIS='data/thinking-disposition-basis-v1.json'
LIBRARY='examples/v016/germ-figurative-connection.noema';BASIS='data/germ-figurative-connection-basis-v1.json'
HIGH='i b[h[a] e]';REF='k h26zj[]';CTX='k h27aw[]';AUTHOR='k wa[]'
FIELDS='community a lowerorder a higherorder a';ARGS='v community v lowerorder v higherorder'
SELECTED='k h26zi['+ARGS+' '+REF+']'
MEMBER='k r6hd[v person v community '+REF+']'
PRIMITIVES={
 'h27bv':('[a a a d] a',['community','lowerorder','higherorder','context'],'同じ比較組・提示文脈において、展開と世話の描写の働き手として指す自然のまとまり。意味内容はr6jfの内的変化力の全体とr6jmの働きで構成し、この参照だけから現実の意志・感情・作動を断言しない。発達の成否や描写時点から選び直さない。'),
 'h27bw':('[a a a a d] a',['community','lowerorder','higherorder','person','context'],'同じ比較組・本人・提示文脈で、二性向の展開を描く芽として指す対象。後の発達時点や成長成功から別の芽を選ばない。人本人との物理的同一性を要求せず、異なる本人の描写対象が必ず別個体であるとも定めない。'),
 'h27bx':('[a a a d] a',['community','lowerorder','higherorder','context'],'同じ比較組・提示文脈において、この硬い覆いとして指す描写対象。本人ごと又は描写時点ごとに選び直さず、同じ低い制度条件の下での各人の発達に一つの指示を保つ。被覆や硬さの成立はr6jmで別に構成する。'),
 'h27by':('[a a a d] d',['community','lowerorder','higherorder','context'],'同じ比較組・提示文脈で固定する描写側の形成史・植物機能・自然の変化力・抵抗性・世話の解釈基準。対象側の第三文の制度基準や、形成・負荷候補の時点と役割を分ける。結果に応じて基準を変更しない。'),
 'h27bz':('[a a '+HIGH+' '+HIGH+' d] c',['node','author','target','depiction','context'],'著者がこの箇所・提示文脈で、同じ人引数を持つ閉じた段階1の対象側の性質を、別の性質記述による非字義的な描写として提示する。人物引数が同じ対象者の役割を共有し、各記述内部で明示した制度・芽・覆いの参照を保つ。内容の実行、真偽一致、物理的同一性を要求しない。既存rw7へ渡す提示関係。'),
 'h27b2':('[a a a a a a a d d] c',['node','author','antecedent','cover','community','lowerorder','higherorder','reference','context'],'同じ著者・提示文脈のこの指示箇所で、描写上の覆いが、指定された先行箇所の同じ共同体・比較組・基準の低い法秩序に対応するという照応解釈。高い側へ無言で替えず、物理的な同一性・防護効果・現実の制度の真理は導かない。先行内容への帰属と本文順序は呼出側で要求する。'),
 'h27b3':('[] a',[],'固定原文kant-1784:u0017第四文[736,762)のunter dieser harten Hülleという覆いへの指示箇所。第三文の低い側の説明箇所h26zsとは別に指す。'),
 'h27b4':('[a a a a '+HIGH+' a d] c',['node','author','person','germ','property','scope','context'],'同じ著者・論述範囲・提示文脈で、この芽が、閉じた性質記述を指定本人へ適用して表す性向の組に対応するという比喩上の指示。性質を持つ人と性質そのもの、植物個体を区別し、指示だけから現在の顕在性や実際の発達を導かない。'),
}
MEANINGS={
 'r6jp':'同じ共同体・低い法秩序・高い法秩序を固定し、人引数だけを残したr6jdの対象側。第三文と同じ基準・比較観点を保った心理的発達を記述する。',
 'r6jq':'r6jpと同じ比較組・同じ人引数・内容評価点を持つ描写側。第三文の同じ比較範囲と成員を保ち、提示文脈で固定した自然・本人の芽・同じ覆い・描写基準をr6joへ渡す。形成過程や始点を心理的過程と同一化しない。',
 'r6jr':'比較組の三つの閉じた呼称をr6jpへ適用した段階1の閉じた対象性質記述。作成時に心理的発達を実行しない。',
 'r6js':'同じ三つの閉じた呼称をr6jqへ適用した段階1の閉じた描写性質記述。自然・植物・被覆・世話を現実の事実として実行しない。',
 'r6jt':'共同体・両法秩序・基準の呼称が元の対象を指すことを検査し、r6jrとr6jsの異なる二記述をrw7で同じ前件箇所・著者・提示文脈の比喩へ結ぶ。',
 'r6ju':'第三文の低い側h26zsの全内容r6ikへの既存の著者帰属を保ち、後の覆い箇所との別箇所・正順・逆順の不在を要求する。同じ比較組について選んだ一つの覆いを、その組の低い法秩序へ対応づける。先行内容の引用を実行しない。',
 'r6jv':'第三文の同じ共同体の全人間成員について、描写に渡す同じ本人の芽が、同じ本人へ適用するr6jbの二性向の組に対応することを要求する。全員の実際の顕在化や同時の発達を主張せず、性質の組と植物・人を区別する。',
 'r6jw':'第三文の非空の固定した全比較組について、対象側と描写側の提示r6jt、低い制度への覆いの照応r6ju、本人と二性向への芽の対応r6jv、既存のnämlich同格r6jeをまとめる。第四文前件の比喩接続であり、条件文全体や後件の成立を追加しない。',
}
LIMITS=[
 'u0017第四文前件の描写と対象側を接続する。対象側r6jdと描写側r6joは既に合成した内容を使い、自然言語の文字列・未知の一文述語・裸の名称で置き換えない。既存rw7の段階1の性質提示を再利用する。',
 '同じ比較組の人を共通の引数位置として二側へ渡す。植物は提示文脈で同じ本人について指定する描写対象であり、人本人や二性向との物理的同一性は要求しない。複数の本人について一つの象徴的な芽を指してもよく、全員に別の植物を実在させない。',
 '同じ内容評価点を二側で対応する終点の役割として使う。両側の過程や始点を同一化せず、同じ時計で測った実在の歴史だとも主張しない。描写側の解釈基準は提示文脈で別に固定する。',
 'この覆いは第三文の低い市民的自由の側を受けるという採用済みの読み。先行する低い側の全内容の帰属と、各比較組の指定された低い法秩序への対応を両方保つ。覆いは同じ比較組の全員に共通とし、本人や成長結果から選び直さない。',
 '芽を二性向の性質として説明する同格と、その同じ性質を同じ本人について植物として描く対応を分ける。これらの指示関係から、その人が実際に性質を持つことは導かない。成員全体への対応も、全員の同時発達を意味しない。',
 '比喩の提示・指示解釈は公開した談話上の入力であり、表面の語順から自動推論する処理ではない。未知の参照・帰属を任意の対象や真として補わず、閉じた内容を実行して現実の真理を要求しない。',
 'Wenn/soの条件全体と人口・時点への量化、民衆への漸次の反作用、行為能力、政府原則・自己利益・機械以上の人間・尊厳、著者注参照は未統合。今回も全文判断と意味確認文字数を増やさない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def main_catalog():return load_catalog(ROOT,MAIN)
@lru_cache(None)
def legacy():
    ds=closure(parse((ROOT/OLD).read_text(encoding='utf-8')),('rw7',))
    return ds,json.loads((ROOT/OLD_BASIS).read_text(encoding='utf-8'))['definitions']['rw7']

def definitions():
    text='d r6jp['+FIELDS+'] h[a] e[i[person a][k r6jd['+ARGS+' v person]]].\n'
    selected=lambda symbol:'k '+symbol+'['+ARGS+' '+CTX+']'
    germ='k h27bw['+ARGS+' v person '+CTX+']'
    text+='d r6jq['+FIELDS+'] h[a] e[i[person a][b point['+both(SELECTED,MEMBER,
      't[k r6jo['+selected('h27by')+' '+selected('h27bv')+' '+germ+' '+selected('h27bx')+']][v point]')+']]].\n'
    for name,target in (('r6jr','r6jp'),('r6js','r6jq')):
        text+='d '+name+'[community i[a] lowerorder i[a] higherorder i[a]] '+HIGH+'[o a[r b[p '+target+']][v community v lowerorder v higherorder]].\n'
    names=' '.join('k h223g[v '+n+']' for n in ('community','lowerorder','higherorder'))
    text+='d r6jt['+FIELDS+'] c['+both('k r6it[v community '+REF+']',
      *['e[s[k h223g[v '+n+']]][v '+n+']' for n in ('lowerorder','higherorder')],
      'k rw7[k h27av[] '+AUTHOR+' k r6jr['+names+'] k r6js['+names+'] '+CTX+' p h27bz]')+'].\n'
    text+='d r6ju['+FIELDS+'] c['+both('u[e[k h27b3[]][k h26zs[]]]',
      'k h26ub[k h26zs[] '+AUTHOR+' r f[k r6ik[]] k h26zk[]]',
      'k ue[k h26zs[] k h27b3[] '+CTX+']','u[k ue[k h27b3[] k h26zs[] '+CTX+']]',
      'k h27b2[k h27b3[] '+AUTHOR+' k h26zs[] '+selected('h27bx')+' '+ARGS+' '+REF+' '+CTX+']')+'].\n'
    bundle='k r6jb[k h223g[v community] k h223h['+REF+']]'
    text+='d r6jv['+FIELDS+'] c['+both('k r6it[v community '+REF+']',
      'f person a[y['+MEMBER+'][k h27b4[k h27at[] '+AUTHOR+' v person '+germ+' '+bundle+' k h27av[] '+CTX+']]]')+'].\n'
    conditions=both(*['k '+n+'['+ARGS+']' for n in ('r6jt','r6ju','r6jv')],'k r6je[v community]')
    text+='d r6jw[] c['+both('g community a[g lowerorder a[g higherorder a['+SELECTED+']]]',
      'f community a[f lowerorder a[f higherorder a[y['+SELECTED+']['+conditions+']]]]')+'].\n'
    return text

def build():
    p=parent();m=main_catalog();doc=deepcopy(p.document);doc['statements']=[];imported=dict(p.entries)
    for d in closure(m.document,('r6ik','h26zs','h26zk','h26ub')):
        n=d['name'];e=m.entries[n]
        if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=e
    ds,meaning=legacy();assert len(ds)==1 and ds[0]['name']=='rw7'
    if 'rw7' in imported:assert ds[0]==imported['rw7']['declaration'] and meaning==imported['rw7']['meaning_ja']
    else:doc['declarations']+=ds
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(m.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set(p.source_sha256)|set(m.source_sha256)|{OLD,OLD_BASIS}
    basis=dict(status='germ_cover_nature_figurative_connection_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|{'rw7':meaning}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()}|{'rw7':OLD_BASIS},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
