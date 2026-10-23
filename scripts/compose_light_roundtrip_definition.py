"""Connect the hypothetical light roundtrip and its definitional synchrony equation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_equal_light_times import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-equal-light-times.noema';PARENT_BASIS='data/equal-light-times-basis-v1.json'
FULL='examples/v014/einstein-light-roundtrip-definition.noema';CORE='examples/v014/light-roundtrip-definition-core.noema'
BASIS='data/light-roundtrip-definition-basis-v1.json';ANNOTATIONS='data/light-roundtrip-definition-identifiers-v1.json';INDEX=238
TRIP=[(n,'a') for n in ('clocka','clockb','placea','placeb','depart','reflect','arrive','ray','frame','unit')]+[(n,R) for n in ('first','middle','last')]
EXTRA=[('document','a'),('context','d')]
SYNC=[(n,'a') for n in ('clocka','clockb','placea','placeb','frame','unit','document')]+[('context','d')]
RULE='i[h['+' '.join(t for _,t in SYNC)+'] c]'
PRIMITIVES={
 'eisjj':([], 'u0013第五文で仮想的に導入する同じ一往復の試行への参照。出発・反射・帰着と三読みは既存qc–qkと具体的設定へ結び、現実の発射済みを意味しない。'),
 'eisjk':([], '同じ仮想試行におけるAからの光の出発出来事。A時計のt_Aの読取りと結ぶ。'),
 'eisjl':([], '同じ仮想試行におけるBでの反射出来事。B時計のt_Bと、そこからAへ向かう同じ光の復路を結ぶ。'),
 'eisjm':([], '同じ仮想試行におけるAへの帰着出来事。出発とは別の出来事としてA時計のt′_Aを結ぶ。'),
 'eisjn':([], '同じ仮想試行でAからBへ進み、そこで反射されAへ戻る一つの光信号。往路と復路で別の光へ交換しない。'),
 'eisjo':([], '仮想試行のA時計による出発出来事の読みt_Aを表す実数切断の候補。特定の数値を補わず、型・読取りとの対応は設定で要求する。'),
 'eisjp':([], '同じ試行のB時計による反射出来事の読みt_Bを表す実数切断の候補。t_Aと同じ時計の別名とはしない。'),
 'eisjq':([], '同じ試行のA時計による帰着出来事の読みt′_Aを表す実数切断の候補。プライムを別の場所やB時計の読みへ替えず、同じA時計の後の出来事へ結ぶ。'),
 'eisjr':([], '固定u0013[1071,1291)の第五文の箇所。光の往復を定義説明の仮想設定として導入する。'),
 'eisjs':([], '固定u0013[1292,1347)の第六文と続くu0014の式M0030を一つの定義条件として提示する箇所。数式だけを独立した無条件の事実へ替えない。'),
 'eisjt':([('node','a'),('author','a'),('general','i[e]'),('particular','i[e]'),('document','a'),('context','d')],'authorがnodeでgeneralの説明を、同じ対象を持つparticularの設定によって具体化する言説関係。nämlichによる説明の接続に用い、無関係な例、単なる時間的後続、引用した設定が実際に生じたことの証明ではない。'),
 'eisju':([(n,'a') for n in ('node','author','clocka','clockb','placea','placeb','frame','unit','proposal','time','trial')]+[('condition','i[e]'),('rule',RULE),('document','a'),('context','d')],'同じproposalで導入するtimeの下で、指定された二時計が同期して走るという語を、ruleで与える同じ二地点・系・単位の条件によって定義する採用関係。trialの三読みを用いるconditionは、その仮想設定における具体的な条件式であり、ruleは必要範囲の全試行へ同じ条件を適用する。definitionsgemäßとwennをこの規約上の条件として保持し、conditionの実測済みや一回の偶然の一致だけを時計全体の同期としない。引用を実行せず、各試行の物理的条件・数式・範囲は合成で別に定める。'),
}
MEANINGS={
 'eimh':'前二文の異なるA/B時計と地点を保ち、daの同じ光・出発・反射・帰着・A/B/Aの読取りを、出来事の型・実数値・正確な時計構成一致へ結ぶ。数式の等時間条件はまだ加えない。',
 'eimi':'三つの有効な実数読みについて、反射時刻−出発時刻と帰着時刻−反射時刻の値が等しいという式。t_B−t_A=t′_A−t_Bを二つの差の数値的等値で保持する。',
 'eimj':'同じ具体的一往復の設定eimhと、その同じ三つの読みの等時間式eimiを結ぶ判定条件。',
 'eimk':'同じ異なる二時計・地点・系・単位について、既存qmとqnの完全な非空の全関連試行へeimjを適用する同期条件。各試行の場所を固定した両地点へ結び、一回の一致や空の試行集合で同期としない。',
 'eiml':'第五文の同じ仮想試行を既存qbとqc–qkへ結び、その同じ光・三出来事・三時刻でeimhを述べる設定。等時間式や実際の発射済みは主張しない。',
 'eimm':'著者が第五文でeimlをこの論説の仮想設定として採用する行為の内容。接続法による設定をugへの引用で保持する。',
 'eimn':'仮想設定の導入eimmを述べるメッセージ。光の往復そのものの実際の成立へ替えない。',
 'eimo':'第五文の著者帰属、nämlichによる前文の定義方法の具体化、二つの局所時間呼称への指示、前文からの順序を保持する。',
 'eimp':'同じ二時計と共通時間の案について、仮想試行の条件式eimsと全試行条件eimkによる同期の定義採用を述べる。',
 'eimq':'第六文と式M0030の定義採用eimpを主張するメッセージ。数式だけを実測済みの事実にしない。',
 'eimr':'第六文と式の同じ著者・論説への帰属、第五文からの順序と箇所の区別を保持する。',
 'eims':'仮想試行のt_A・t_B・t′_Aを、同じ順序でeimiへ渡す条件式の内容。式中で二度出るt_Bは同じ値である。',
}
LIMITS=[
 'Es gehe・werde・gelangeを、同じ光線の出発・反射・帰着を考える仮想設定の導入として読む。実験済み・観測済みの主張や読者への物理的発射命令にしない。nämlichは前文の定義方法の具体化である。',
 '前二文の同じA/B時計、異なるA/B地点と静止系、同じ単位を保つ。正確な時計構成一致はeildを再利用し、daの時計・光・場所・読取りとの対応を保つ。原文に数値は与えられていないので三読みを特定の数へ固定しない。',
 '光はAからBへ進み、その同じ光がBで反射されAへ戻る。A/B/Aの各時刻は出発・反射・帰着の同じ出来事へ結ぶ。帰着のプライムを新しい場所や別時計へ替えない。出発と帰着の区別を保つ。',
 'definitionsgemäß synchron, wennを、後続の式を同期の定義条件として採用する読みとする。仮想試行の具体的な式と、時計が同期して走るという全体の規約は分け、既存qnが指定する完全な非空の全関連試行に同じ条件を要求する。一回の偶然の一致を全期間の同期としない。',
 'M0030の等式は二つの差の実数値の等値であり、関数としての切断の個体同一性や近似比較ではない。第四文の等片道所要時間を具体的な反射一往復へ適用する。光速度Vの数値、真空条件、任意個数の同期の整合性・対称性・推移性はこの文へ加えない。',
 '試行範囲の完全性・候補記録・時計と光の関係・定義採用は意味規約付き入力である。有限例と有理値を埋め込んだ切断は引数・差・量化の検査であり、物理理論や実数全域の検証ではない。未知を不成立や零で補わない。',
 'u0013末尾の162非空白本文文字、M0019–M0029、u0014のM0030を対象とする。単位全体の判断は前四文の記録と合わせた別の通読記録で行う。',
]

def args(fs):return [v(n) for n,_ in fs]
def fixed_trip():return [k(n) for n in ('eisib','eisik','ziq','zir','eisjk','eisjl','eisjm','eisjn','ra','rb','eisjo','eisjp','eisjq')]


def definitions():
    text=''
    for n,(fs,_) in PRIMITIVES.items():
        result=R if n in ('eisjo','eisjp','eisjq') else 'a' if not fs else 'c'
        text+='r '+n+'['+' '.join(t for _,t in fs)+'] '+result+'.\n'
    setting=both(k('da',*args(TRIP)),*[k('zbd',v(n)) for n in ('depart','reflect','arrive')],*[k('ba',v(n)) for n in ('first','middle','last')],op('u',op('e',v('clocka'),v('clockb'))),op('u',op('e',v('placea'),v('placeb'))),op('u',op('e',v('depart'),v('arrive'))),k('eild',v('clockb'),v('clocka'),v('document'),v('context')))
    text+=define('eimh',TRIP+EXTRA,setting)
    text+=define('eimi',TRIP[-3:],both(*[k('ba',v(n)) for n in ('first','middle','last')],k('sca',k('bf',v('middle'),v('first')),k('bf',v('last'),v('middle')))))
    text+=define('eimj',TRIP+EXTRA,both(k('eimh',*args(TRIP+EXTRA)),k('eimi',*args(TRIP[-3:]))))
    fields=[(n+'trial',t) for n,t in TRIP]
    criterion='i['+' '.join(n+' '+t for n,t in fields)+']['+both(op('e',v('placeatrial'),v('placea')),op('e',v('placebtrial'),v('placeb')),k('eimj',*args(fields),*args(EXTRA)))+']'
    text+=define('eimk',SYNC,both(k('qm',v('clocka'),v('frame'),v('context')),k('qm',v('clockb'),v('frame'),v('context')),op('u',op('e',v('clocka'),v('clockb'))),op('u',op('e',v('placea'),v('placeb'))),k('qn',v('clocka'),v('clockb'),v('frame'),v('unit'),v('context'),criterion)))
    record=[op('e',k(field,k('eisjj')),k(ref)) for field,ref in zip(('qc','qd','qe','qf','qg','qh'),('ziq','zir','eisjk','eisjl','eisjm','eisjn'))]
    record += [k('sca',k(field,k('eisjj')),k(ref)) for field,ref in zip(('qi','qj','qk'),('eisjo','eisjp','eisjq'))]
    text+=content('eiml',both(k('qb',k('eisib'),k('eisik'),k('ra'),k('rb'),v('point'),k('eisjj')),*record,k('eimh',*fixed_trip(),k('eirf'),v('point'))))
    text+=content('eimm',k('ug',k('eisjr'),k('rd'),quote('eiml'),k('eirf'),v('point')))
    text+='d eimn[] f[j s[k eimm[]]].\n'
    text+=define('eimo',[],both(k('eir3',k('eisjr'),k('rd'),k('eirf'),quote('eimn'),k('ri')),k('eisjt',k('eisjr'),k('rd'),quote('eime'),quote('eiml'),k('eirf'),k('ri')),*[k('eisi4',k(d),k(t),k(p),k('eirf'),k('ri')) for d,t,p in (('eisi2','eisiw','ziq'),('eisi3','eisix','zir'))],k('ue',k('eisjh'),k('eisjr'),k('ri')),op('u',op('e',k('eisjh'),k('eisjr')))))
    text+=content('eims',k('eimi',*[k(n) for n in ('eisjo','eisjp','eisjq')]))
    text+=content('eimp',k('eisju',*[k(n) for n in ('eisjs','rd','eisib','eisik','ziq','zir','ra','rb','eisje','eisjd','eisjj')],quote('eims'),'r[p eimk]',k('eirf'),v('point')))
    text+='d eimq[] f[j s[k eimp[]]].\n'
    text+=define('eimr',[],both(k('eir3',k('eisjs'),k('rd'),k('eirf'),quote('eimq'),k('ri')),k('ue',k('eisjr'),k('eisjs'),k('ri')),op('u',op('e',k('eisjr'),k('eisjs')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eimo','eimr')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='hypothetical_light_roundtrip_and_definitional_synchrony_equation',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX,INDEX+1]).document
    ann=json.loads(read('data/equal-light-times-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
