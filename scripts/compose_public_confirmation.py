"""Compose public confirming agents separately from confirming instruments."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_spiritual_guardians import quant

PARENT='data/covenant-question-basis-v1.json'
LIBRARY='examples/v016/public-confirmation.noema'
BASIS='data/public-confirmation-basis-v1.json'
PRIMITIVES={
 'h256p':('[a a d] c',['office','organization','point'],'同じ統治組織の公的な意思決定権限に関わる役職の全範囲。最高位を得るために競合する役職を落とさず、儀礼上の席次だけを比較範囲にしない。政治的な管轄はh256sで別に結ぶ。'),
 'h256q':('[a a a d] c',['higher','lower','organization','point'],'同じ組織・時点で、前の役職の統治上の意思決定権限が後の役職より上位にある。間接の上位を含む。人数・名声・儀礼の順位や、異なる組織の辺とは分ける。非反射性・推移性は合成側で確認する。'),
 'h256r':('[a a a d] c',['actor','office','organization','point'],'同じ主体が同じ組織の同じ役職を、この時点で制度上担う。単なる所属や自称、能力、儀礼への出席とは分ける。主体は個人でも合議的組織でもよく、正当性や特定の就任方式は含意しない。'),
 'h256s':('[a a d] c',['organization','community','point'],'この組織は同じ政治的共同体の共通の事柄について、公的に命令・禁止・裁定を行う統治の管轄を持つ。私的な会社・家族内の指揮や財産所有だけとは分ける。正当性、立法行政司法の特定の分割や近代的国家形態は含意しない。'),
 'h256t':('[a a d] c',['estate','empire','point'],'この身分団体・領邦の制度的な主体は、同じ帝国の国制において帝国共通の事項に参与する身分として位置付く。人個人の社会階級や現代の全国民を代表する政党とは分ける。全ての住民の参加や投票の平等を含意しない。'),
 'h256u':('[a a a d] c',['person','estate','body','point'],'この人は同じ身分の制度的な保持者として、自らの身分上の資格により、この会議体でその身分を代表して参与する位置にある。単なる同席、別の身分、別の会議への権限とは分ける。派遣代表への委任はh254fで別に扱う。'),
 'h256v':('[a a d] c',['body','empire','point'],'この会議体は同じ帝国の国制で帝国全体の共通の事項を共同審議・議決する機関として位置付く。地方だけの会議・私的会合とは分ける。身分による構成、成員の代表資格、実践内容は別に合成する。近代の国会名や単一の開催日へ固定しない。'),
 'h256w':('[a a d] c',['issue','empire','point'],'この論点は同じ帝国全体に共通する統治・秩序・対外関係などの公的な事柄に属する。個人の無関係な私事、別の政治体だけの問題とは分ける。宗教に関係する公的な事柄を一律に排除しない。'),
 'h256x':('[a a d] c',['actor','contract','point'],'同じ主体がこの契約を公的・制度的に承認し、その拘束力を認める確認を、この時点の状況で与えている。内容が真だとの認識、文書を受け取ったこと、単なる履行や他の契約の承認とは分ける。承認行為を行う制度上の位置は別に指定し、その承認による正当な効力は含意しない。'),
 'h256y':('[a a d] c',['instrument','contract','point'],'この同じ合意・法的文書の条項が、この契約を承認し拘束力を認める確認の根拠として制度的に用いられている。文書自身を意思ある承認者とせず、単なる契約への言及、文書の存在や別の契約の確認とは分ける。その確認による正当な効力は含意しない。'),
 'h256z':('[a d] c',['form','reference'],'同じ固定比較基準における、合意を結び公示する方式の全比較範囲。最上級を得るためにより厳粛な方式を除かず、実際に選んだ方式だけで範囲を作らない。'),
 'h257a':('[a a d] c',['first','second','reference'],'同じ比較基準で、前の方式が後の方式と少なくとも同程度に厳粛である。重要な約束の公的な引受けを強調し記憶させる言葉・儀礼・手続等の重さを比較し、拘束力の正当性や結果の真理を比較しない。両方向の成立は同程度、両方向の不成立は比較不能。反射性・推移性と最高位を合成側で確認する。'),
 'h257b':('[a a d] c',['instrument','form','point'],'この同じ合意の締結・公示は、この時点の状況で指定の方式を実際に備える。別の合意の方式や予定だけを混ぜない。方式の厳粛さや合意の正当性は別に扱う。'),
 'h257c':('[a d] c',['form','reference'],'同じ基準で、この方式は重要な約束の引受けを強調し記憶させる明示的な言葉・儀礼・手続を伴う厳粛な方式である。単なる華美な装飾・静けさや、比較範囲でたまたま最高であることだけとは分ける。特定宗教の宣誓を必須にしない。'),
}
MEANINGS={
 'r5am':'同じ組織の全役職範囲で厳密な上位関係rexを確認し、自己同一か上位という弱い比較の最高位rqyiを指定役職に求める。単に上位者が見当たらない極大を最高位にしない。',
 'r5an':'同じ政治的共同体を公的に管轄する組織のr5amの最高役職を、同じ主体が担う。個人と合議体を許し、一人の唯一の保持者や民主的な正当性を補わない。',
 'r5ao':'同じ会議・身分について、人がその身分上の資格で直接参与するか、同じ役職・身分の職務関係r46bを持つ派遣代表h254fである。派遣される場合と本人資格の場合を区別する。',
 'r5ap':'同じ帝国の共通機関において、身分の構成範囲が非空で全て同じ帝国の身分であり、各身分に適格な所属者がいる。逆に全所属者は人で、同じ構成身分の適格な代表である。現在の出席だけで構成範囲を縮めない。',
 'r5aq':'同じ所属者が担う生起した一つの活動が、同じ会議体の手続で、同じ帝国の公的論点を審議し、その論点が同じ機関の議決担当に属する内容。結論の到達や正当性は要求しない。',
 'r5ar':'同じ人・会議体に対するr5aqの活動・論点・帝国があるという内容。共同実践に引用でき、引用だけでは会合や審議を実行しない。',
 'r5as':'同じ帝国の身分会議r5apがr5arの公的審議を共同実践として持つという、この箇所のReichstagの採用読解。近代の政党議会・普通選挙や全帝国の唯一の歴史的会議を要求しない。',
 'r5at':'指定方式が同じ完全な比較範囲に属し、厳粛な方式であり、弱い比較rqyiにおいて全ての方式以上にある。同程度の複数の最上位を許し、比較不能や空範囲から最上級を作らない。',
 'r5au':'同じ合意・文書が同じ候補点で備える方式に、固定比較基準のr5atを満たすものがある。比較基準を候補点ごとに移動せず、合意の種類や正当性をこの述語だけで決定しない。',
 'r5av':'同じ政治的共同体について、同じ候補点での最高権力の保持者r5anが、同じ契約をh256xで承認している。',
 'r5aw':'同じ候補点での帝国身分会議r5asが、同じ契約をh256xで承認している。全ての歴史的な会議の承認や複数回の承認を要求しない。',
 'r5ax':'明示した合意の種類を同じ候補点で満たす文書について、同じ文書の最高度に厳粛な方式r5auと、同じ契約の条項を通じた確認h256yを結ぶ。種類は引数であり、和平合意の分類の完成を代用しない。',
 'r5ay':'同じ契約について、最高権力・帝国身分会議・指定種類の最も厳粛な合意のいずれかによる確認がある内容。各証人を同じ評価点へ結び、合意の方式比較だけは固定基準に保つ。承認の現実性や規範的有効性を単独で断言しない。',
}
LIMITS=[
 'oberste Gewaltは同じ政治的共同体を統治する権限体系で最高位を担う主体として読む。役職の完全範囲と管轄は明示した制度的入力であり、特定の王名・国名や国家の完全な定義を補わない。',
 'Reichstageは帝国の身分による共通事項の審議機関という歴史的な読み。身分の制度的保持者本人と派遣された職務代表をともに許す。帝国身分を現代の政党や全住民と同一視しない。複数形は種類として一般化し、全歴史的会議の同時承認を要求しない。',
 'feierlichstenは同じ固定基準で比較した厳粛な締結・公示方式の最高度として読む。方式の同程度は許すが、単なる極大や比較不能は最高位にしない。華美さ、法的な正しさ、条約の唯一性は導かない。',
 '確認は主体による公的承認と、文書の条項を通じた確認に分ける。どちらも正当な規範的効力を含意しない。r5ayはそれぞれの種類の承認を条件の内側で使うための選言であり、原文の列挙と譲歩の提示自体は別に接続する。',
 '和平締結の分類はr5ax/r5ayの引数に残る。以前の交戦主体・和平への合意・その同一の条項と締結を構成してから原文に適用する。名前だけの和平プリミティブをここに追加せず、この依存群を原文一文の完成と数えない。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def definitions():
    scope='i[role a][k h256p[v role v organization v point]]'
    order='i[first a last a][k h256q[v first v last v organization v point]]'
    weak='i[first a last a][x[e[v first][v last]][k h256q[v first v last v organization v point]]]'
    text='d r5am[office a organization a point d] c['+both('k rex['+scope+' '+order+']','k rqyi[v office '+scope+' '+weak+']')+'].\n'
    text+='d r5an[actor a community a point d] c['+quant(('office','organization'),both('k r5am[v office v organization v point]',
        'k h256r[v actor v office v organization v point]','k h256s[v organization v community v point]'),'g')+'].\n'
    delegated='g role a['+both('k h254f[v estate v person v role v body v point]','k r46b[v person v role v estate v point]')+']'
    text+='d r5ao[person a estate a body a point d] c['+both('k aa[v person]','x[k h256u[v person v estate v body v point]]['+delegated+']')+'].\n'
    represented='k h254g[v body v estate v point]';member='k h246c[v body v person v point]'
    qualified='k r5ao[v person v estate v body v point]'
    text+='d r5ap[body a empire a point d] c['+both('k h256v[v body v empire v point]','g estate a['+represented+']',
        'f estate a[y['+represented+']['+both('k h256t[v estate v empire v point]','g person a['+both(member,qualified)+']')+']]',
        'f person a[y['+member+'][g estate a['+both(represented,qualified)+']]]')+'].\n'
    fields='person a body a activity a issue a empire a'
    text+='d r5aq['+fields+'] e[b point['+both(member,'k dg[v activity v point]','k f3[v person v activity v point]',
        'k h254i[v activity v body v point]','k h254h[v activity v issue v point]','k h254j[v body v issue v point]',
        'k h256v[v body v empire v point]','k h256w[v issue v empire v point]')+']].\n'
    text+='d r5ar[person a body a] e[b point['+quant(('activity','issue','empire'),'t[k r5aq[v person v body v activity v issue v empire]][v point]','g')+']].\n'
    text+='d r5as[body a point d] c['+both('g empire a[k r5ap[v body v empire v point]]','k h246h[v body r[p r5ar] v point]')+'].\n'
    text+='d r5at[form a reference d] c['+both('k h257c[v form v reference]',
        'k rqyi[v form i[other a][k h256z[v other v reference]] i[first a last a][k h257a[v first v last v reference]]]')+'].\n'
    text+='d r5au[instrument a reference d point d] c[g form a['+both('k h257b[v instrument v form v point]','k r5at[v form v reference]')+']].\n'
    text+='d r5av[contract a community a point d] c[g actor a['+both('k r5an[v actor v community v point]','k h256x[v actor v contract v point]')+']].\n'
    text+='d r5aw[contract a point d] c[g body a['+both('k r5as[v body v point]','k h256x[v body v contract v point]')+']].\n'
    fields='contract a reference d kind h[a d] c point d'
    text+='d r5ax['+fields+'] c[g instrument a['+both('c[v kind][v instrument v point]','k r5au[v instrument v reference v point]','k h256y[v instrument v contract v point]')+']].\n'
    text+='d r5ay[contract a community a reference d kind h[a d] c] e[b point[x[k r5av[v contract v community v point]][x[k r5aw[v contract v point]][k r5ax[v contract v reference v kind v point]]]]].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['rex','rqyi','r46b','h254f','h254g','h246c','h246h','aa','dg','f3','h254i','h254h','h254j']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='public_confirming_agents_and_solemn_instruments_dependency',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
