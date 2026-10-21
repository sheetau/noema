"""Bind political parties' peace terms through authorized human declarations."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENTS=('data/covenant-question-basis-v1.json','data/public-confirmation-basis-v1.json')
LIBRARY='examples/v016/peace-conclusion.noema'
BASIS='data/peace-conclusion-basis-v1.json'
TERMS='i[h[j[a]] e]'
PRIMITIVES={
 'h257d':('[a d] c',['party','reference'],'この主体は同じ基準で、政治的共同体を統治し、他の政治的主体との対外的な合意を自らの公的行為として担う勢力である。国家・統治組織・その公的な地位での君主等を許し、私的な個人や単なる商事団体とは分ける。現代の主権国家の全属性や、戦争・条約を行うことの道徳的な正当性を要求しない。'),
 'h257e':('[a a d] c',['agreement','party','reference'],'この政治的主体は、同じ合意の同じ固定基準における当事者である。当事者の全範囲を与え、未表明者を除かない。署名する人個人・同席者・現在生存する住民の一覧とは分ける。交戦当事者のほか、共同締結する同盟者・保障者を含み得る。'),
 'h257f':('[a a a d] c',['agreement','first','second','reference'],'同じ合意が終結の対象とする、固定基準で指定した交戦相手の組である。一組の向きはr5azで対称化する。合意に関係する全組を与え、履行失敗や合意に反対する者を理由に組を落とさない。同じ側の同盟者や交戦していない保障者同士を対戦組へ補わない。実際の先行する戦争は別に確認する。'),
 'h257g':('[a a d] c',['first','second','point'],'同じ時点で、二つの政治的主体の間に、組織的な武力対立としての戦争の関係が継続している。個人的な口論、単なる外交上の不和とは分ける。戦闘が休止していても戦争を終結していない関係を含み、正式な宣戦文書だけを必要条件にしない。向きは合成側で対称化する。'),
 'h257h':('[a a d] c',['party','opponent','point'],'同じ時点で、この政治的主体は同じ相手に対して、その統治上の指揮に帰属する組織的な武力攻撃・敵対行動を行っている。住民一人の無関係な私闘と区別する。制度上の交戦関係、攻撃の正当性、他の相手への行動とは分ける。'),
 'h257i':('[a a a a d] c',['person','party','activity','agreement','point'],'この人がこの同じ政治的主体を代表し、この合意について、この表明行為で主体を制度上拘束する引受けを行う資格を持つ。自称、単なる同席や無関係な役職と分ける。君主本人の公的地位での表明も含む。必要な制度上の委任・承認手続を充たす位置を与え、私的な発言、無権限の仮署名、未承認の提案だけでは満たさない。道徳的な権限や合意内容の正当性は含意しない。'),
 'h257j':('[a a a a a '+TERMS+' j[a] d] c',['person','party','counterparty','activity','agreement','terms','bindings','point'],
    'この人はこの同じ行為で、この政治的主体を代表し、同じ相手当事者に対して、同じ合意の閉じた条項関数を同じ順序の引数へ適用する内容を、主体自身に課す引受けとして確定的に表明する。共同合意への参加としての引受けであり、単なる交渉案・伝言・受領・他人の約束の報告とは分ける。内容を実現し維持する責務への引受けを述べ、履行済み・将来の履行の成功・正当な効力は含意しない。代表資格と生起・実行者は同じ行為について合成側で確認する。'),
 'h257k':('[a d d] c',['agreement','candidate','point'],'同じ合意の形成と先行する交戦を同じ候補状況から評価する、その候補に属する経過の履歴にこの点が含まれる。固定の条項基準、各表明点、先行する交戦点と候補点を取り落とさずに供給する。順序・各点の包含・前後は別に検査する。別候補の履歴を混ぜない。'),
}
MEANINGS={
 'r5az':'同じ合意・固定基準の終結対象の組h257fを対称化する。向きの表記だけで片方の当事者の責務を落とさない。',
 'r5ba':'同じ二主体間の戦争関係h257gを対称化する。片方向に記録された戦争を不在にせず、武力行動の有無とは分ける。',
 'r5bb':'同じ固定基準でその合意の当事者である主体について、対象となる相手ごとに交戦関係がなく、本人からの組織的武力敵対行動もない内容。相手方の引受けは同じ内容を相手へ適用して別に結ぶ。無関係な第三国との戦争や全世界の永遠平和を要求しない。',
 'r5bc':'当事者・合意の正確な二個体列から、同じ合意の固定条項基準h254zでr5bbの和平状態の内容を作る。合意形成のときはこの記述を引用し、実際の履行を要求しない。',
 'r5bd':'人aaが同じ表明行為の実行者f3であり、その行為・合意について同じ政治的主体を拘束する代表資格h257iを持つ。行為の生起は相互引受けの外側でdgを確認する。',
 'r5be':'同じ人・行為の実行と代表資格を保ち、固定基準の他の全当事者へ、同じ条項・引数の主体自身の引受けh257jを表明する。相手ごとに別の実行者や行為の表明を継ぎ合わせない。',
 'r5bf':'同じ合意の固定基準と同じ候補の履歴にrhzを適用し、二者以上の全政治的当事者が同じr5bcの条項を正確な当事者・合意の列で引き受ける。人の行為を政治的主体へr5bd/eで結び、当事者を人だけに狭めない。',
 'r5bg':'同じ合意の終結対象の組は非空で、全組は相異なる当事者同士である。各組について、同じ候補の履歴内で固定基準より前の交戦r5baがある。全当事者間の総当たりの戦争や保障者の交戦を要求しない。',
 'r5bh':'同じ候補の厳密全順序の履歴に固定基準と候補点が含まれ、固定基準は候補点以前である。r5bgの先行交戦とr5bfの同じ和平条項への相互の公的引受けを結ぶ、ここでの和平締結の分類。締結後の履行失敗から、かつての和平締結がなかったとはしない。',
 'r5bi':'最も厳粛な合意文書による同じ契約の確認r5axの種類引数に、構成した和平締結r5bhを同じ候補点で供給する。方式の比較基準と合意の候補点を保持する。',
 'r5bj':'最高権力・帝国身分会議・最も厳粛な和平締結の三種類の確認r5ayに、同じr5bhを供給した内容。和平合意を承認主体へ置き換えず、確認から正当な規範的効力を推論しない。',
}
LIMITS=[
 'Friedensschlußは従前の交戦関係を終える政治的諸主体の合意と、その条項を担う合意文書という読み。物理的な紙そのものに人格や意図を付けず、同じ合意の文書として扱う。特定の歴史的条約名や現代条約法の全要件を補わない。',
 '和平の中核を、指定した相手との戦争関係を終え組織的な武力敵対行動を行わない状態への相互の引受けとして記述する。休戦は戦争関係がなお残り得るのでこの中核と区別する。交易・賠償・領土・宗教条項など特定条約の追加条項を、和平一般の必要条件にしない。',
 '全当事者と全終結対象の組は固定基準で与える。一つ以上の対戦組があり、対象の全組で先行交戦を要求するが、同盟者同士や保障者まで相互に戦っていたとはしない。各当事者が政治的主体であることと、その代表者が人であることを区別する。',
 '条項は合意の中核の内容を割り当てるh255aにより引用する。条項を引き受けたことと実際にそれを守ることを区別し、締結時の交戦継続や後の違反だけで締結の形成を否定しない。平和の実現が永遠に保証されることも要求しない。',
 '代表権と確定した相互引受けの制度的な認定は明示した入力であり、自動判定ではない。必要な制度上の手続を経ない交渉案や無権限の署名は除くが、強制の不在・公平性・道徳的正当性や全追加条項の履行をこの分類だけから導かない。',
 '同種契約の仮定形成・無効性と、確認を挙げる譲歩・全面性・著者帰属は本文統合で残る。この依存群の検査だけで原文234文字の意味判断を増やさない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def history():return 'i[at d][k h257k[v agreement v candidate v at]]'
def before():return 'i[first d last d][k ic[v first v last v candidate]]'

def definitions():
    text='d r5az[agreement a first a last a reference d] c[x[k h257f[v agreement v first v last v reference]][k h257f[v agreement v last v first v reference]]].\n'
    text+='d r5ba[first a last a point d] c[x[k h257g[v first v last v point]][k h257g[v last v first v point]]].\n'
    text+='d r5bb[party a agreement a reference d] e[b point['+both('k h257e[v agreement v party v reference]',
        'f other a[y[k r5az[v agreement v party v other v reference]]['+both('u[k r5ba[v party v other v point]]','u[k h257h[v party v other v point]]')+']]')+']].\n'
    text+='d r5bc[bindings j[a]] e[b point['+bind(('party','agreement'),'t[k r5bb[v party v agreement k h254z[v agreement]]][v point]')+']].\n'
    representation=both('k aa[v person]','k f3[v person v activity v point]','k h257i[v person v party v activity v agreement v point]')
    text+='d r5bd[party a activity a agreement a point d] c[g person a['+representation+']].\n'
    fields='agreement a reference d party a activity a terms '+TERMS+' bindings j[a] point d'
    allothers='f other a[y['+both('k h257e[v agreement v other v reference]','u[e[v party][v other]]')+'][k h257j[v person v party v other v activity v agreement v terms v bindings v point]]]'
    text+='d r5be['+fields+'] c[g person a['+both(representation,allothers)+']].\n'
    parties='i[party a at d][k h257e[v agreement v party v at]]'
    declares='i[party a activity a agreement a terms '+TERMS+' bindings j[a] point d][k r5be[v agreement v reference v party v activity v terms v bindings v point]]'
    text+='d r5bf[agreement a reference d candidate d] c['+both('e[v reference][k h254z[v agreement]]',
        'k rhz[v agreement r[p r5bc] v reference '+parties+' i[party a][l[a][v party v agreement]] i[party a][k h257d[v party v reference]] '+history()+' '+before()+
        ' p h255a p dg i[party a activity a point d][k r5bd[v party v activity v agreement v point]] '+declares+']')+'].\n'
    pair='k r5az[v agreement v first v last v reference]'
    prior='g at d['+both('k h257k[v agreement v candidate v at]','k ic[v at v reference v candidate]','k r5ba[v first v last v at]')+']'
    text+='d r5bg[agreement a reference d candidate d] c['+both('g first a[g last a['+pair+']]',
        'f first a[f last a[y['+pair+']['+both('u[e[v first][v last]]','k h257e[v agreement v first v reference]','k h257e[v agreement v last v reference]',prior)+']]]')+'].\n'
    anchor='k h254z[v agreement]'
    text+='d r5bh[agreement a candidate d] c['+both('k ta['+history()+' '+before()+']','k h257k[v agreement v candidate '+anchor+']','k h257k[v agreement v candidate v candidate]',
        'x[e['+anchor+'][v candidate]][k ic['+anchor+' v candidate v candidate]]','k r5bg[v agreement '+anchor+' v candidate]','k r5bf[v agreement '+anchor+' v candidate]')+'].\n'
    text+='d r5bi[contract a reference d point d] c[k r5ax[v contract v reference p r5bh v point]].\n'
    text+='d r5bj[contract a community a reference d] e[k r5ay[v contract v community v reference p r5bh]].\n'
    return text

def build():
    old,confirmation=parents();doc=deepcopy(old.document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in ((old,['rhz','h254z','h255a','aa','dg','f3','ic']),(confirmation,['r5ax','r5ay'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:
                assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(confirmation.entries))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    sources=set(old.source_sha256)|set(confirmation.source_sha256)
    basis=dict(status='political_peace_conclusion_and_typed_confirmation_dependency',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
