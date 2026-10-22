"""Bind comparison/standards and choose each prince's own release witnesses."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_release_merit import DETAILS,DARGS,NAMES,DATES,STANDARD
from scripts.compose_qualified_prince_frame import FIELDS as PRINCE,ARGS as PARGS

PARENTS=('data/release-merit-basis-v1.json','data/named-epoch-sentence-basis-v1.json')
LIBRARY='examples/v016/prince-merit-scope.noema';BASIS='data/prince-merit-scope-basis-v1.json'
ACHIEVEMENT='i b[h[a a d] c]';ASSESSMENT='i b[h[a d] c]'
COHORT='currentgroup a postgroup a currentepoch a postepoch a hearers a'
COARGS='v currentgroup v postgroup v currentepoch v postepoch v hearers'
FRAME='office a community a topic a reference d candidate d anchor d '+COHORT
FARGS='v office v community v topic v reference v candidate v anchor '+COARGS
PRIMITIVES={
 'h26n5':('[a '+ACHIEVEMENT+' d d] c',['person','achievement','reference','point'],
    '同じ固定評価基準において、指定された閉じた三引数の達成関係について、この人・結果点で、候補となる全活動の達成又は不達成を区別する評価が整っている。達成関係には人・活動・結果点を渡す。活動の候補を成功例又は既知例だけへ縮めず、未評価又は未知を不達成に置換しない。評価済みであることと達成の真偽を分け、証拠の正当性・本人の知識・著者が現実に歴史調査を完了したことは含意しない。段階1の記述をここで実行せず、達成そのものは合成側で評価する。'),
 'h26n6':('[a a a a a d] j['+STANDARD+']',['person','office','community','responders','epoch','reference'],
    '同じ人物・公的役職・共同体と、固定された応答者範囲・時代・評価基準において、功績を理由とする応答の適合を判定するために採用する条件の全有限列。各条件は同じ人物、段階1の応答記述、段階1の功績記述を受けてNoema内容を返す。理由と評価の釣合い、対象への正確な功績帰属、恩恵を認める応答の相応性を、その基準で要求される範囲で扱い、結果に合わせて不利な条件を除かない。単に応答を実行したか、命令されたか、好かれているかという判定と同一視しない。具体的条件はNoema関数として与え、未知又は名前だけの条件を成立済みにしない。非空性と全条件の同一引数への適用は合成側で検査する。この供給関係だけで基準の客観的な正しさや対象者の功績を断言しない。'),
}
MEANINGS={
 'r52q':'同じ固定基準・候補履歴の名前をr52aへ適用し、時点別の全人口について政府側の解放があるという共通の三引数の達成関係を段階1で閉じる。比較の対象を現在の人口又は指定君主の政府へ縮めない。',
 'r52r':'同じr52qの達成関係に対するh26n5の評価を、人・結果点の二引数関数にする。出来事ごとに比較内容を選び直さず、評価が済むことを成功そのものにしない。',
 'r52s':'r52rの同じ基準・履歴を閉じる段階1の比較評価関数記述。r52qの高い記述を構成する依存も保持し、段階0の引用へ押し込まない。',
 'r52t':'r52fと同じ具体的功績の引用構造を、段階1の比較評価関数記述へ接続する。功績自体は段階1に保ち、同じ評価関数を実評価と功績引用に共用する。',
 'r52u':'r52nと同じ具体的解放・生存受益者・恩恵・功績・両範囲の接続を、段階1の比較評価関数記述へ保つ。評価を脱引用する依存を含むが、応答そのものを実行しない。',
 'r52v':'各人物の同じ役職・共同体・現在世界・後代について、r52sの同じ比較評価とh26n6の双方の全基準をr52uへ供給する。評価関数や基準列を無関係な外部引数で差し替えず、両範囲の基準を混同しない。',
 'r52w':'同じ現在点の本人の能力と、その本人の政府・活動・前後人口・前後点・行為点・生存受益者を結論の内側で選ぶr52vの称揚適合を連言する。君主ごとに別の証人を選べるが、一人の証人を他人の功績へ流用しない。',
 'r52x':'同じ君主の限定条件r5xjを満たす全員に、その本人のr52wの能力と具体的功績への称揚適合を結ぶ一般条件。役職・共同体・固定基準を前後件で共有し、全君主に一つの活動を外から固定せず、存在を前提から導かない。',
}
LIMITS=[
 '原文第一文の一般的な君主について、その人物ごとの最初の解放の出来事と受益者を結論内で選ぶ。これは同一の活動・政府・受益者を全員へ一律に渡す旧r52pの接続例を本文へそのまま使わないための範囲設定である。旧定義と証拠は変更しない。',
 '選ぶのは同じ君主に結び付く政府・活動・前後人口・行為点・結果点・生存受益者であり、前後件の役職と共同体、全比較の履歴・基準現在、現在世界と後代の全範囲は共有する。出来事の唯一性、政府の世界唯一性、全時代で同じ人々という条件は補わない。',
 '比較評価h26n5は一般の閉じた達成関係の評価完備を表し、ここではr52aの同じ時点別人口の解放を渡す。原文の最初という比較を評価不足から真にしないための解釈モデル上の条件であり、歴史研究の実施報告や著者の全知を原文へ加えるものではない。比較の正否そのものはr5z7で別に計算する。',
 '適合基準h26n6は各関数のNoema内容を供給し、全基準を同じ人物・応答・功績へ適用する。特定の倫理学説、数値的な功績点、感謝や称揚の義務を原文へ追加しない。原文が述べる規範評価を文脈依存の全基準として扱う明示的な読みで、有限モデルの任意の真偽を史実や道徳的正しさの証明にしない。',
 '比較評価の記述は段階1を使う。r52tの功績引用も段階1、恩恵の状態は0、応答は1を保持する。r52uは比較評価の脱引用を含むので、それ自体を引用する場合には少なくとも段階2が必要になる。既存の段階0評価入力の型を黙って変更しない。',
 '原文の名称・名称使用者・自己報告の聴衆・義務の規範出所・時代と現在点・集団の本文設定、限定された同じ君主の談話帰属、wenigstens・sondern等の提示、名称の高慢評価の独立した著者帰属、一文全体と後続の判断は残る。本文112主張・v196・17単位判断を保持する。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def sortof(s):return parse('p:r z['+s+'] c.')['declarations'][0]['parameters'][0]
def upgrade(old,new,index,renames):
    d=deepcopy(parents()[0].entries[old]['declaration']);d['name']=new;d['parameters'][index]['sort']=sortof(ASSESSMENT)
    def walk(x):
        if isinstance(x,list):return [walk(y) for y in x]
        if isinstance(x,dict):
            y={k:(renames.get(v,v) if k=='symbol' else walk(v)) for k,v in x.items()}
            if y.get('kind')=='disquote':y.pop('rank',None)
            return y
        return x
    d['body']=walk(d['body']);return d
def initial():
    text='d r52q[reference i[d] candidate i[d]] '+ACHIEVEMENT+'[o a[r b[p r52a]][v reference v candidate]].\n'
    code='k r52q[k h223h[v reference] k h223h[v candidate]]'
    text+='d r52r[reference d candidate d] h[a d] c[i[person a point d][k h26n5[v person '+code+' v reference v point]]].\n'
    text+='d r52s[reference i[d] candidate i[d]] '+ASSESSMENT+'[o a[r b[p r52r]][v reference v candidate]].\n'
    return text
def latter():
    assessment='k r52s[k h223h[v reference] k h223h[v candidate]]'
    def standards(side):return 'k h26n6[v actor v office v community v '+side+'group v '+side+'epoch v reference]'
    text='d r52v['+DETAILS+' '+COHORT+' beneficiary a] h[a] e[i[actor a][b point[t[c[k r52u['+DARGS+' '+assessment+' '+COARGS+' v beneficiary '+standards('current')+' '+standards('post')+']][v actor]][v point]]]].\n'
    selected='t[c[k r52v['+DARGS+' '+COARGS+' v beneficiary]][v actor]][v point]'
    variables=(('activity','a'),('government','a'),('beforegroup','a'),('aftergroup','a'),('beneficiary','a'),('first','d'),('acted','d'),('last','d'))
    for n,s in reversed(variables):selected='g '+n+' '+s+'['+selected+']'
    text+='d r52w['+FRAME+'] h[a] e[i[actor a][b point['+both('e[v point][v anchor]',
        't[c[k r5xv[v topic v reference]][v actor]][v point]',selected)+']]].\n'
    text+='d r52x['+PRINCE+' candidate d anchor d '+COHORT+'] e[k r5xk['+PARGS+' k r52w['+FARGS+']]].\n'
    return text
def build():
    libs=parents();doc=deepcopy(libs[0].document);doc.update(declarations=[],statements=[]);imported={}
    for lib,roots in zip(libs,(['r52a','r52f','r52n','r5xv','r5xk','h223h'],[])):
        for d in closure(lib.document,roots) if roots else ():
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(l.entries) for l in libs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+initial())
    doc['declarations'] += [upgrade('r52f','r52t',12,{}),upgrade('r52n','r52u',12,{'r52f':'r52t'})]
    doc=parse(format_graph(doc,'compact')+latter());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(l.source_sha256) for l in libs))
    basis=dict(status='per_prince_release_witnesses_and_bound_comparison_standards',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
