"""Compose equal opposite light-travel durations as an adoptable time definition."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_local_times_only import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-local-times-only.noema';PARENT_BASIS='data/local-times-only-basis-v1.json'
FULL='examples/v014/einstein-equal-light-times.noema';CORE='examples/v014/equal-light-times-core.noema'
BASIS='data/equal-light-times-basis-v1.json';ANNOTATIONS='data/equal-light-times-identifiers-v1.json';INDEX=237
LEG=[(n,'a') for n in ('time','ray','start','finish','origin','destination','frame','unit')]+[('context','d')]+[(n,R) for n in ('first','last','duration')]
RULE_FIELDS=[(n,'a') for n in ('time','leftplace','rightplace','frame','unit','document')]+[('context','d')]
RULE='i[h['+' '.join(t for _,t in RULE_FIELDS)+'] c]'
PLAN=[(n,'a') for n in ('proposal','task','time','lefttime','righttime','leftclock','rightclock','leftplace','rightplace','frame','unit','author','priorstage','stage','document')]+[('reference','d')]
ADOPT=[(n,'a') for n in ('proposal','time','leftplace','rightplace','frame','unit','author','stage','document')]+[('rule',RULE),('result','d')]
PRIMITIVES={
 'eisi5':([(n,'a') for n in ('time','event','place','frame','unit')]+[('reading',R),('context','d')],'timeという候補の時刻付与規約で、同じplaceのeventへframe・unitを明示してreadingを時刻値として割り当てる関係。既定義又は実測済みであることは要求せず、定義案の下での割当ても扱う。時刻原点は規約内で統一して解釈し、候補値の提示だけでは割当てを認めない。元の局所時計の付与規則との関係は定義案の対応で別に固定する。'),
 'eisi6':([('pair','a'),('slot','b'),('context','d')],'同じ比較組pairの候補記録から、slot=0,1,2で往路の光・出発出来事・到着出来事、slot=3,4,5で復路の光・出発出来事・到着出来事を取り出す。任意の未知欄や範囲外を既知値で埋めない。二方向の各伝播・場所・出来事の型は合成側で別に検査する。同じ光子、反射や往路到着と復路出発の同一性をこの一般記録では強制しない。'),
 'eisi7':([('pair','a'),('slot','b'),('time','a'),('frame','a'),('unit','a'),('context','d')],'同じpair・time・frame・unitの候補値を、slot=0,1,2で往路の出発時刻・到着時刻・所要時間、slot=3,4,5で復路の出発時刻・到着時刻・所要時間として取り出す。値が有効な実数であること、時刻割当て、終点から始点を引いた差との一致は合成側で要求する。未知又は不正な欄を零で埋めない。'),
 'eisja':([('pair','a')]+RULE_FIELDS,'同じtimeの規約で、同じ二地点・系・単位について等しい片道時間を定義する対象となる、両方向の対応した光伝播の比較組pairの全範囲。適切に対応する理想的試行も扱い、成功した組だけを選ばず、異なる条件や無関係な伝播を混ぜない。実際の光の発射済みや反射済みを要求しない。範囲の未知を空としない。'),
 'eisjb':(ADOPT,'proposalを用いて同じtimeを定義する際、authorがdocumentのstageで、同じ二地点・系・単位に引数を結んだruleを定義上の条件としてresultで採用する。ruleは時間の規約を定める手段であり、既に測定で確認した法則の報告や無関係な定義の併置ではない。引用した条件を現実の真理として実行せず、定義の登録と両地点への適用は別に要求する。'),
 'eisjc':(PLAN,'proposalは同じtaskで、priorstageまでのlefttime・righttimeの局所的な時計による時刻付与から、stageでtimeを両地点の共通時間として導入するための定義案である。二つの局所規則の時計・指針による値の付与方式を保持し、地点間の時刻原点の対応を追加規定で定め得る。元の時計の初期位相の一致や既に同期済みであることは前提にしない。全役割を同じ議論へ結ぶが、採用の実現や共通時間の成立はここから導かない。'),
 'eisjd':([], 'u0013第四文で導入を提案する、AとBに共通の時間規約の候補。第三文の後者「共通時間」という種類を引き継ぎ、第三文で既にその規約が定義済みだったことを補わない。'),
 'eisje':([], 'u0013第四文の、等片道光時間を条件として共通時間を定義する案への参照。内容はeisjc・eisjb・eimbへ接続する。'),
 'eisjf':([], '同じ二地点に共通する時間の規約をこの論説で導入する定義課題。前の局所規則を保った上で比較に用いる規約を追加する仕事であり、実測値を得る実験そのものではない。'),
 'eisjg':([], '第三文までの局所時間だけの段階eisiyに続き、第四文で新しい定義案を導入する論述段階。nunはこの議論の進行を指し、物理的な絶対的現在とはしない。'),
 'eisjh':([], '固定原文einstein-1905:u0013[822,1070)の第四文の箇所。共通時間の定義可能性と等片道時間を定める手段を述べる。'),
 'eisji':([(n,'a') for n in ('node','author','priornode')]+[('priorcontent','i[e]')]+[(n,'a') for n in ('time','leftplace','rightplace','document')]+[('context','d')],'nodeのDie letztere Zeitは、priornodeのpriorcontentで未定義と述べた同じ二地点の共通時間という種類を引き継ぎ、その候補timeを指す照応である。局所A時間だけ又は局所B時間だけへの照応、先行段階で既に存在した個体の再同定へ替えない。引用した先行内容の真理はこの言説関係から実行しない。'),
}
MEANINGS={
 'eil7':'同じ候補時間規約・系・単位における一方向の光伝播を、その始終の出来事・所在地・割当て時刻へ結ぶ。有効な非負実数の所要時間が終点時刻から始点時刻を引いた値と一致する。',
 'eima':'同じ比較組の往路を左から右、復路を右から左へ結び、双方の所要時間をeil7で確認して同じ値とする。二つの到着時刻そのものの等値や距離の等値ではない。',
 'eimb':'同じ二地点に対する等片道時間の定義条件として、対象の全比較組へeimaを適用する関係型。現実の試行存在を要求する規則ではなく、必要な組の存在を定義の引用から補わない。',
 'eimc':'同じ案と前後の論述段階、局所時間・時計・地点を結び、同じ規約にeimbを定義として採用した結果で、その規約が既定義となり両地点へ共通に適用される。定義上の採用と共有された規約への接続を分ける。',
 'eimd':'同じ案を同じ定義課題へ採用する可能な結果が存在し、その結果でeimcが成立する。実際の採用済み、全結果での成功保証、既に測定で等時間を得たことは主張しない。',
 'eime':'前文の局所A/B時間・二時計・二地点から、後続段階で共通時間を等片道光時間によって定義できるというeimdの内容。',
 'eimf':'第四文eimeを主張するメッセージ。定義可能性の内側の物理的条件を、現実の実測済みの法則へ替えない。',
 'eimg':'第四文の同じ著者・論説への帰属、前文の後者の共通時間への照応、本文順序と箇所の区別を保持する。',
}
LIMITS=[
 'Die letztere Zeitは直前の共通時間という種類への照応である。第三文で既に共通時間が定義済みだったとはしない。nunは局所定義だけの段階から新たな案を導入する論述上の進行として読む。',
 'kann definiert werdenは、同じ案を採用する可能な結果で定義と両地点への共通適用を満たせるという読み。受動文とmanはこの定義手続きの一般的な提示であり、特定の他人や全人類の能力・実際の採用行為を追加しない。著者は論説での規約採用者として固定する。',
 'indemとdurch Definitionは等しい片道所要時間を条件として採用する定義上の手段と読む。等しさを引用された規則として採用し、実験によって先に確認された物理法則や真空中の光速度一定をこの文の前提へ加えない。',
 '所要時間は同じ候補の時間規約の始終の割当て時刻の差であり、同じ単位で非負の実数値を持つ。二方向の伝播・始終点・A/Bを別に確認する。等しい到着時刻、距離、個体としての同じ切断関数で所要時間の数値的等値を代用しない。',
 '両方向で対応する光伝播の比較組を扱う。同じ光子の反射と往路終点から直ちに復路が始まる具体的な一往復は次文で導入されるので、ここでは余計な成立条件にしない。実際の光が既に存在したことや試行件数を定義条件へ追加しない。',
 '時刻付与・比較組の全範囲・定義案の役割対応・定義採用と可能な採用結果は意味規約付き入力である。未知を偽・零・空集合で補わない。有限モデルと有理値を埋め込んだ実数切断の検査は構成の検査であり、全物理モデルや実数全域の証明ではない。',
 '第四文181非空白本文文字とM0015–M0018のA・B・B・Aを対象とする。第五文の具体的な往復、第六文の同期式、および段落全体の判断は未完。',
]

def args(fs):return [v(n) for n,_ in fs]
def numeral(i):return 'n p '+number_word(i)+' b'
def fixed_plan():return [k(n) for n in ('eisje','eisjf','eisjd','eisiw','eisix','eisib','eisik','ziq','zir','ra','rb','rd','eisiy','eisjg','eirf')]+[v('point')]


def definitions():
    text=''
    for n,(fs,_) in PRIMITIVES.items():
        result='a' if not fs or n=='eisi6' else R if n=='eisi7' else 'c'
        text+='r '+n+'['+' '.join(t for _,t in fs)+'] '+result+'.\n'
    reading=lambda event,place,val:k('eisi5',v('time'),v(event),v(place),v('frame'),v('unit'),v(val),v('context'))
    leg=both(k('cf',v('ray')),k('zbd',v('start')),k('zbd',v('finish')),k('cg',v('ray'),v('start'),v('finish'),v('frame')),k('cb',v('start'),v('origin'),v('frame')),k('cb',v('finish'),v('destination'),v('frame')),op('u',op('e',v('origin'),v('destination'))),k('ci',v('unit')),k('va',v('frame')),reading('start','origin','first'),reading('finish','destination','last'),*[k('ba',v(n)) for n in ('first','last','duration')],k('bc',k('bb',numeral(0)),v('duration')),k('sca',v('duration'),k('bf',v('last'),v('first'))))
    text+=define('eil7',LEG,leg)
    field=lambda i:k('eisi6',v('pair'),numeral(i),v('context'))
    val=lambda i:k('eisi7',v('pair'),numeral(i),v('time'),v('frame'),v('unit'),v('context'))
    legs=[]
    for offset,origin,destination in ((0,'leftplace','rightplace'),(3,'rightplace','leftplace')):
        legs.append(k('eil7',v('time'),*[field(offset+i) for i in range(3)],v(origin),v(destination),v('frame'),v('unit'),v('context'),*[val(offset+i) for i in range(3)]))
    text+=define('eima',[('pair','a')]+RULE_FIELDS,both(*legs,k('sca',val(2),val(5))))
    text+=define('eimb',RULE_FIELDS,q('f','pair','a',op('y',k('eisja',v('pair'),*args(RULE_FIELDS)),k('eima',v('pair'),*args(RULE_FIELDS)))))
    adopt=[v(n) for n,_ in ADOPT[:-2]]+['r[p eimb]',v('result')]
    result=both(k('eisjc',*args(PLAN)),k('eisjb',*adopt),k('eisiq',v('time'),v('author'),v('stage'),v('document'),v('result')),k('eilr',v('time'),v('leftplace'),v('rightplace'),v('frame'),v('unit'),v('document'),v('result')))
    text+=define('eimc',PLAN+[('result','d')],result)
    text+=define('eimd',PLAN,q('g','result','d',both(k('eisf2',v('proposal'),v('task'),v('document'),v('reference'),v('result')),k('eimc',*args(PLAN),v('result')))))
    text+=content('eime',k('eimd',*fixed_plan()))
    text+='d eimf[] f[j s[k eime[]]].\n'
    text+=define('eimg',[],both(k('eir3',k('eisjh'),k('rd'),k('eirf'),quote('eimf'),k('ri')),k('eisji',k('eisjh'),k('rd'),k('eisiz'),quote('eil2'),k('eisjd'),k('ziq'),k('zir'),k('eirf'),k('ri')),k('ue',k('eisiz'),k('eisjh'),k('ri')),op('u',op('e',k('eisiz'),k('eisjh')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eimg',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='equal_opposite_light_durations_as_adoptable_common_time_definition',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/local-times-only-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
