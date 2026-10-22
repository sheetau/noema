"""Use complete populations at each event's dates and bind the same public ruler."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/government-release-basis-v1.json','data/qualified-prince-frame-basis-v1.json','data/named-epoch-sentence-basis-v1.json')
LIBRARY='examples/v016/humanity-release.noema';BASIS='data/humanity-release-basis-v1.json'
EPISODE='actor a activity a government a firstgroup a lastgroup a community a reference d candidate d first d acted d last d'
EARGS='v actor v activity v government v firstgroup v lastgroup v community v reference v candidate v first v acted v last'
SELECTED=EPISODE+' office a anchor d assessed h[a d] c'
SARGS=EARGS+' v office v anchor v assessed'
HISTORY='i[at d][k h257z[v reference v candidate v at]]'
BEFORE='i[left d right d][k ic[v left v right v candidate]]'
MEANINGS={
 'r5z3':'同じ固定基準・候補履歴の指定点に生存する全人間と、固定集団の成員がちょうど一致し、非空である。民族・国民・成功者だけ、現在生存する者だけを別時点の人口へ流用しない。',
 'r5z4':'同じ解放の前後の全人口をr5z3で別々に固定し、前の全員の評価と後の全員の政府側の自由を要求する。前後とも生存し前で不自由な全員には同じr5zsの変化があり、少なくとも一人の生存者が前の積極的拘束から同じ出来事で解放される。出生・死亡による入替だけを解放としない。',
 'r5z5':'同じ行為者・活動・政府・共同体・固定基準・候補履歴・結果点について、前後人口・前状態・行為点を共用するr5z4の解放がある。比較時に別時代の現在人口を固定しない。',
 'r5z6':'同じ人・役職・共同体・時点についてr5xhの君主であり、その同じ役職が同じ政府組織の最高位r5amで、本人がh256rでその職を担う。r5zjの同じ政府と共同体も結び、私的な個人と政府組織、別の役職・別国の資格を寄せ集めない。',
 'r5z7':'既存robの最初の達成の論理を、全設定を既に閉じた三引数の達成関係へ特殊化する。固定対象と目標記述の二引数だけをその関係内へ移し、履歴・厳密順序・全比較者・評価・先行達成排除・同時達成許容を変えない。',
 'r52a':'同じ基準と履歴について、人・活動・結果点ごとに、ある政府・共同体でr5z5の解放があるという比較関係。全時代で同じ全人口条件と自由内容を使い、具体的な成員と政府は各達成に対応させる。',
 'r52b':'r5z7にr52aを渡し、同じ全人間比較範囲・履歴・基準現在について、指定した人の同じ活動・結果点が最初の解放であるとする。過去の比較にまだ生まれていない現在の成員の解放を要求しない。',
 'r52c':'同じ具体的な前後人口・活動・政府・共同体・前後点のr5z4と、行為点での同じ役職のr5z6、およびr52bの最初を結ぶ。一般的な最初の証人を別の政府や解放行為へ替えない。',
 'r52d':'r52cの同じ解放について、前後両人口に属して前に自由でなかった同じ人を受益者とし、r5zvで同じ公的行為・政府側の自由・履歴・基準現在への恩恵を確認する。集団そのものをg3の人引数へ代入せず、未来の感謝又は現在の心情は導かない。',
}
LIMITS=[
 'menschliche Geschlechtは人類一般と読み、この出来事が作用する人々はその前後の各時点に生存する全人間で具体化する。原文の一国の臣民だけへの暗黙の縮小は行わず、政治的・規範的な主張内容として構成する。現実の歴史で世界の全員にその効果があったと実証したものではない。',
 '前後集団は同じ固定基準で全人口と照合する。出生者は後の全員自由へ含め、前の不自由や未出生時の拘束は要求しない。前にいたが後で死亡した人へ死後の状態や後の恩恵を要求せず、死亡を解放として数えない。',
 '前後を通じて生存し前に不自由だった全員に同じ出来事による自由への変化を要求する。さらに前の積極的な指図又は介入から解放された生存者を一人以上求め、拘束者の死亡と自由な出生者への入替だけで成功しない。',
 'これは人口が変わりうる集団についての出来事の読みであり、元から同じ人々を固定した比較r5zzや解放r5ztを変更しない。原文へ採用する比較はr52b/cを用い、各出来事ごとに同じ分類基準で人口を固定する。',
 '最初の一般定義はrobの対象・目標引数を達成関係に閉じるだけの特殊化である。新しい最初判定の基本関係は置かない。全比較者の評価と先行達成の否定を残し、同時達成を排除しない。',
 '君主と政府の結合は解放の行為点での同じ職・共同体を要求する。全期間の在任、政府組織が一人の人であること、個人の規範と組織の規範の自動的な同一性は加えない。前件の同じ君主・役職・共同体への本文束縛はなお必要である。',
 'r52dは具体的な受益者を同じ出来事へ結ぶ接続であり、全世界と後代の人々が実際にその事実を認め感謝するという全称の心情を追加しない。恩恵・功績の記述と両集団から値する評価への引用段階と全引数の束縛は次の統合に残る。',
 '比較評価の具体的な入力、本文の全設定、wenigstens等の提示、全称揚適合基準、独立した名称評価・著者帰属・sondern、一文全体と後続は未完。本文112主張・v196・17単位判断と確認済み文字数を保持する。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def specialize_first():
    old=deepcopy(parents()[0].entries['rob']['declaration']);ps=old['parameters'];achieves=ps[5]['name']
    def walk(x):
        if isinstance(x,list):return [walk(y) for y in x]
        if isinstance(x,dict):
            y={k:walk(v) for k,v in x.items()}
            if y.get('kind')=='apply' and y.get('function')==dict(kind='variable',name=achieves):
                assert len(y['arguments'])==5;y['arguments']=[y['arguments'][i] for i in (0,1,4)]
            return y
        return x
    old['body']=walk(old['body'])
    old['parameters']=[p for i,p in enumerate(ps) if i not in (3,4)]
    old['parameters'][3]['sort']['parameters']=['individual','individual','situation']
    old['name']='r5z7';return old
def definitions():
    member=lambda group:'k h246c[v '+group+' v person v reference]'
    living=both('k aa[v person]','k h256o[v person v candidate v point]')
    text='d r5z3[group a reference d candidate d point d] c['+both('k h257z[v reference v candidate v point]',
        'k r5ty[v group v reference]','f person a[z['+member('group')+']['+living+']]')+'].\n'
    shared=both(member('firstgroup'),member('lastgroup'))
    state='t[c[k r5zn[v government v community v reference]][v person]][v first]'
    transition='k r5zs[v actor v activity v government v person v community v reference v candidate v first v acted v last]'
    survivor=both(shared,'k r5zr[v government v person v community v reference v first]',transition)
    le=lambda a,b:'x[e[v '+a+'][v '+b+']][k ic[v '+a+' v '+b+' v candidate]]'
    text+='d r5z4['+EPISODE+'] c['+both('k r5z3[v firstgroup v reference v candidate v first]','k r5z3[v lastgroup v reference v candidate v last]',
        'k ta['+HISTORY+' '+BEFORE+']','k ic[v first v last v candidate]','k h257z[v reference v candidate v acted]',le('first','acted'),le('acted','last'),
        'k aa[v actor]','k h256o[v actor v candidate v acted]','k ag[v activity v first v last]','k dg[v activity v acted]',
        'k df[v actor v activity v acted]','k h26n2[v actor v activity v government v acted]','k r5zj[v government v community v first]',
        'f person a[y['+member('firstgroup')+'][k r5ze[v government v person v community v reference v first]]]',
        't[k r5zo[v government v lastgroup v community v reference]][v last]',
        'f person a[y['+both(shared,'u['+state+']')+']['+transition+']]','g person a['+survivor+']')+'].\n'
    short='actor a activity a government a community a reference d candidate d last d'
    args='v actor v activity v government v community v reference v candidate v last'
    text+='d r5z5['+short+'] c[g firstgroup a[g lastgroup a[g first d[g acted d[k r5z4['+EARGS+']]]]]].\n'
    text+='d r5z6[actor a office a government a community a point d] c['+both('k r5xh[v actor v office v community v point]',
        'k r5am[v office v government v point]','k h256r[v actor v office v government v point]','k r5zj[v government v community v point]')+'].\n'
    text+='d r52a[reference d candidate d] h[a a d] c[i[actor a activity a last d][g government a[g community a[k r5z5['+args+']]]]].\n'
    text+='d r52b[actor a activity a reference d candidate d anchor d last d assessed h[a d] c] c[k r5z7['+HISTORY+' '+BEFORE+' p aa k r52a[v reference v candidate] v assessed v anchor v actor v activity v last]].\n'
    text+='d r52c['+SELECTED+'] c['+both('k r5z4['+EARGS+']','k r5z6[v actor v office v government v community v acted]',
        'k r52b[v actor v activity v reference v candidate v anchor v last v assessed]')+'].\n'
    text+='d r52d['+SELECTED+' person a] c['+both('k r52c['+SARGS+']',shared,'u['+state+']',
        'k r5zv[v actor v activity v government v person v community v reference v candidate v anchor]')+'].\n'
    return text
def build():
    doc=deepcopy(parents()[0].document);doc.update(declarations=[],statements=[]);imported={}
    roots=(['r5ty','h246c','r5zn','r5zo','r5zr','r5zs','r5zv','r5ze','r5zj','ta','ag','dg','df','h26n2','h257z','ic','rob'],['r5xh'],['h256o','r5am','h256r'])
    for lib,selected in zip(parents(),roots):
        for d in closure(lib.document,selected):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not set(MEANINGS)&set().union(*(set(p.entries) for p in parents()))
    doc['declarations'].append(specialize_first());doc=parse(format_graph(doc,'compact')+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    paths=set().union(*(set(p.source_sha256) for p in parents()))
    basis=dict(status='dated_complete_human_populations_and_same_public_ruler_release',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
