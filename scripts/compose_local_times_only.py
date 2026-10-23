"""Compose local-time definitions, lack of common time and restricted comparison."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_second_local_clock import ROOT,read
from scripts.compose_local_clock_valuation import BASE
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-second-local-clock.noema';PARENT_BASIS='data/second-local-clock-basis-v1.json'
FULL='examples/v014/einstein-local-times-only.noema';CORE='examples/v014/local-times-only-core.noema'
BASIS='data/local-times-only-basis-v1.json';ANNOTATIONS='data/local-times-only-identifiers-v1.json';INDEX=236
RULE='i[h['+' '.join(t for _,t in BASE+[('event','a')])+'] c]'
LOCAL=[(n,'a') for n in ('time','task','observer','clock','hand','place','frame','unit','document')]+[('context','d')]
SCOPE=[(n,'a') for n in ('lefttime','righttime','leftclock','rightclock','leftplace','rightplace','frame','unit','author','stage','document')]+[('context','d')]
STAGE=[(n,'a') for n in ('author','stage','document')]+[('context','d')]
METHOD=[(n,'a') for n in ('method','task','author','stage','document')]+[('context','d')]
PRIMITIVES={
 'eisip':(LOCAL[:-1]+[('rule',RULE),('context','d')], 'timeが同じtaskの対象について、observer・clock・hand・place・frame・unitを固定し、ruleの局所的な指針表示と出来事の対応で時間値を付与する規約である。timeは物質や絶対的時間そのものではなく、この局所的な時刻付与規則の対象。規則を引用して参照し、全対象の実際の読取り済みや遠隔同期を要求しない。'),
 'eisiq':([('time','a')]+STAGE, '同じauthorがdocumentのstageまでの当該二地点の時間規定の議論で、timeを時刻付与の規約として既に定義した範囲に含める。bisherの範囲を論述段階へ固定し、後で導入する規約・単なる候補・他の論説を含めない。全既定義範囲を与え、未知の登録を未定義として補わない。'),
 'eisir':([(n,'a') for n in ('time','place','frame','unit','document')]+[('context','d')], 'timeという一つの時間規約が、同じframe・unitでplaceの出来事の値を、その規約内で共有された値の解釈と比較関係へ結んで適用される。単に同じ名前を各地で用いることや、位相の関係を定めていない局所尺度の寄せ集めではない。同じtimeが複数地点へ適用される場合は、その一つの規約内で場所をまたぐ比較が意味を持つ。実際の全読取りの存在や特定の光同期方式は先取りしない。'),
 'eisis':([(n,'a') for n in ('task','first','second')]+SCOPE, '同じstageで、lefttime・righttimeによりそれぞれ局所的に評価されるfirst・secondの時間的関係を、同じ二時計・二地点・系・単位の下で定める課題がtaskである。先後・同時性などの時間比較を扱い、単に時計盤の数字を並べることや別の二出来事の比較へ替えない。各出来事の型と所在地は合成で別に確認し、課題の達成をこの指定から導かない。'),
 'eisit':([(n,'a') for n in ('method','task','stage','document')]+[('context','d')], '同じtaskに対してstageの議論で検討する実行可能な比較手続きの全範囲にmethodが属する。新たな時間規約を使う候補もここには含み得るため、その使用を別に調べる。成功した手続きだけを選ぶ範囲ではなく、成功と必要な規定は別に要求する。'),
 'eisiu':([(n,'a') for n in ('method','task','convention','stage','document')]+[('context','d')], '同じmethodをtaskへ適用するために必要な時間的な規定の全範囲の一つがconventionである。局所値の意味・原点合わせや地点間の対応を定める規約を含み、手続きの中へ隠れた追加規定を入れない。通常の論理や算術の操作そのものを追加の時間規定と数えない。必要な規定の採用済みかどうかは別に判定する。'),
 'eisiv':([(n,'a') for n in ('method','task','requirement','stage','document')]+[('context','d')], 'methodが同じstageのtaskの個別の必要条件requirementを満たす。局所規則による対象値の意味を保ち、比較する同じ二出来事の先後・同時性等が規約上定まることを各条件に沿って検査する。全条件の達成・追加規定の不要性を一入力で認めず、未知を不成立へ変換しない。'),
 'eisiw':([], 'u0013のここまでで定めた局所A時間の規約への参照。第一文のeik4による同じA側の時刻付与へ結ぶ。'),
 'eisix':([], 'u0013のここまでで定めた局所B時間の規約への参照。第二文が再利用するeik4による同じB側の時刻付与へ結ぶ。'),
 'eisiy':([], 'u0013第一・第二文の設定を終え、第三文で追加の共通時間の規定を導入する前の論述段階。原文[0,561)までのこの二地点の定義をbisherの範囲とし、物理的な絶対時刻や全文の最終状態としない。'),
 'eisiz':([], '固定原文einstein-1905:u0013[561,821)の第三文の箇所。比較不能の限定と、これまでの局所時間だけの定義を述べる。'),
 'eisi2':([], 'この文で局所A時間を指す呼称個体。印字形A-Zeitを識別表記へ保持し、場所と規約の対応は別に結ぶ。'),
 'eisi3':([], 'この文で局所B時間を指す呼称個体。印字形B-Zeitを識別表記へ保持し、同じ文字ZeitだけからA時間と同一にしない。'),
 'eisi4':([(n,'a') for n in ('designation','time','place','document')]+[('context','d')], '同じdocumentのこの記述でdesignationがplaceの局所時間規約timeを指す呼称として使われる。場所文字を伴う引用表現の指示を保持し、文字の形の一致を対象の同一性や物理的な共通時刻へ替えない。'),
}
MEANINGS={
 'eilp':'局所時間規約を、既存eik4の同じ時計・指針・場所・観測者・対象課題と結ぶ参照対応。規則の引用を実行済みとしない。',
 'eilq':'指定された異なる二つの局所時間がこの論述段階で既に定義され、当該範囲の全既定義時間はその二つのいずれかである。後段階の規定は排除しない。',
 'eilr':'異なる二地点に、同じ系・単位で一つの共有された時間規約が適用される。別々の局所時刻表を同じ名前で呼ぶだけでは満たさない。',
 'eils':'当該段階までに既に定義した規約の中には、指定された両地点に共通のeilrを満たす時間規約がない。共通時間一般の永遠の不存在ではない。',
 'eilt':'同じ二つの局所時間・時計・場所・段階で、A側の出来事とB側の出来事を時間的に比較する課題を結ぶ。実際の出来事の所在地と型を確認する。',
 'eilu':'同じ比較手続きに必要な全時間規定が当該段階で既に定義済みである。隠れた追加規定を許さない。',
 'eilv':'同じ手続きが比較課題の非空の全必要条件を満たす。個別条件一つの成功だけや空の条件集合で達成を認めない。',
 'eilw':'同じ課題に適用でき、追加規定を使わず、全必要条件を満たす手続きが存在しない。追加規定を要する手続きの将来の成功は否定しない。',
 'eilx':'当該二地点の各時間比較課題eiltについて、追加規定なしの成功手続きがないことを述べる。出来事の最低件数を追加しない一般的な否定。',
 'eily':'A・Bの同じ局所時間と時計・場所・段階についてeilxを述べる主節内容。',
 'eilz':'局所A時間とB時間を前二文の同じ局所規則へ結び、その二つだけがこの段階で定義済みであるという内容。',
 'eil2':'同じ段階までにはAとBに共通の時間を定義していないという否定内容。',
 'eil3':'二つの局所時間だけを定義したことと共通時間の未定義を結ぶ、セミコロン後の説明内容。',
 'eil4':'追加規定なしの比較不能とその説明を同じ点で主張し、後者から前者への説明理由を結ぶ第三文の全内容。',
 'eil5':'第三文eil4を主張するメッセージ。限定された不能を単なる問いや全ての時間の存在否定へ替えない。',
 'eil6':'同じ著者・論説への帰属、前文の局所的可能性との対比、局所だけと共通未定義の対比、二呼称の同じ場所・時間規約への指示、本文順序を保つ。',
}
LIMITS=[
 'ohne weitere Festsetzungを、今まで定めた時間規約だけで比較課題を達成する手続きの不存在として読む。追加規定を用いる手続き、将来の共通時間、物理的出来事の存在そのものまで否定しない。未知の手続きや未知の条件を偽へ変換しない。',
 'ein Ereignis in A mit einem Ereignis in Bは二地点の出来事を時間的に比較する一般的な課題の読み。各課題で二つの対象・所在地・時計・局所規則を保持し、表示数値を並べるだけでは時間比較を完了としない。',
 'bisherとnurはこの二地点の議論の第三文直前までの全既定義規約へ限定する。局所A時間とB時間を前二文のeik4へ接続し、同じ名前を付けることと規約の共有を区別する。',
 'keine gemeinsame Zeitは、この段階までに著者が両地点に共通の時間規約を定義していないという否定。実在する共通時間の否認、処理系に記述できないという意味、後続規約の未定義への固定ではない。',
 'セミコロン後を比較不能の説明理由として読み、冒頭aberは前文のB側でも可能な局所評価との対比、後半aberは局所二時間だけと共通時間未定義との対比とする。著者のwirと二呼称の引用を保持する。',
 '全手続き・全必要規定・全必要条件・全既定義範囲は意味規約付き入力であり、有限検査から物理的比較可能性の完全判定を主張しない。既存eisgkの全条件と個別充足を使い、第三文の真偽を一つの未説明の基本関係へ隠さない。',
 '第三文181非空白本文文字とM0009–M0014の六つの場所記号を対象とする。第四文以降の等片道時間・往復光・同期式と段落全体の判断は未完。',
]

def args(fs):return [v(n) for n,_ in fs]
def fixed_scope():return [k(n) for n in ('eisiw','eisix','eisib','eisik','ziq','zir','ra','rb','rd','eisiy','eirf')]+[v('point')]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('eilp',LOCAL,k('eisip',*args(LOCAL[:-1]),'r[p eik4]',v('context')))
    defined=lambda time:k('eisiq',time,*args(STAGE))
    text+=define('eilq',[('lefttime','a'),('righttime','a')]+STAGE,both(op('u',op('e',v('lefttime'),v('righttime'))),defined(v('lefttime')),defined(v('righttime')),q('f','time','a',op('y',defined(v('time')),op('x',op('e',v('time'),v('lefttime')),op('e',v('time'),v('righttime')))))))
    common=[(n,'a') for n in ('time','leftplace','rightplace','frame','unit','document')]+[('context','d')]
    shared=lambda place:k('eisir',v('time'),v(place),v('frame'),v('unit'),v('document'),v('context'))
    text+=define('eilr',common,both(op('u',op('e',v('leftplace'),v('rightplace'))),shared('leftplace'),shared('rightplace')))
    already_common=both(defined(v('time')),k('eilr',*args(common)))
    text+=define('eils',[(n,'a') for n in ('leftplace','rightplace','frame','unit')]+STAGE,op('u',q('g','time','a',already_common)))
    events=both(k('eisis',v('task'),v('first'),v('second'),*args(SCOPE)),k('zbd',v('first')),k('zbd',v('second')),k('cb',v('first'),v('leftplace'),v('frame')),k('cb',v('second'),v('rightplace'),v('frame')),op('u',op('e',v('leftplace'),v('rightplace'))))
    text+=define('eilt',[('task','a')]+SCOPE,q('g','first','a',q('g','second','a',events)))
    needed=k('eisiu',v('method'),v('task'),v('convention'),v('stage'),v('document'),v('context'))
    text+=define('eilu',METHOD,q('f','convention','a',op('y',needed,defined(v('convention')))))
    req=k('eisgk',v('task'),v('requirement'),v('document'),v('context'))
    met=k('eisiv',v('method'),v('task'),v('requirement'),v('stage'),v('document'),v('context'))
    all_met=both(q('g','requirement','a',req),q('f','requirement','a',op('y',req,met)))
    text+=define('eilv',METHOD,all_met)
    existing_success=both(k('eisit',v('method'),v('task'),v('stage'),v('document'),v('context')),k('eilu',*args(METHOD)),k('eilv',*args(METHOD)))
    text+=define('eilw',[('task','a')]+STAGE,op('u',q('g','method','a',existing_success)))
    text+=define('eilx',SCOPE,q('f','task','a',op('y',k('eilt',v('task'),*args(SCOPE)),k('eilw',v('task'),*args(STAGE)))))
    text+=content('eily',k('eilx',*fixed_scope()))
    bindings=[]
    for names in (('eisiw','eisie','eisic','eisib','eisid','ziq'),('eisix','eisin','eisil','eisik','eisim','zir')):
        bindings.append(k('eilp',*[k(n) for n in names+('ra','rb','eirf')],v('point')))
    text+=content('eilz',both(*bindings,k('eilq',k('eisiw'),k('eisix'),*[k(n) for n in ('rd','eisiy','eirf')],v('point'))))
    text+=content('eil2',k('eils',*[k(n) for n in ('ziq','zir','ra','rb','rd','eisiy','eirf')],v('point')))
    ev=lambda n:'t[k '+n+'[]][v point]'
    text+=content('eil3',both(ev('eilz'),ev('eil2')))
    text+=content('eil4',both(ev('eily'),ev('eil3'),k('eisdk',k('eirf'),quote('eil3'),quote('eily'),v('point'))))
    text+='d eil5[] f[j s[k eil4[]]].\n'
    text+=define('eil6',[],both(k('eir3',k('eisiz'),k('rd'),k('eirf'),quote('eil5'),k('ri')),k('zbc',k('eisiz'),k('rd'),quote('eilm'),quote('eily'),k('eirf'),k('ri')),k('zbc',k('eisiz'),k('rd'),quote('eilz'),quote('eil2'),k('eirf'),k('ri')),*[k('eisi4',k(d),k(t),k(p),k('eirf'),k('ri')) for d,t,p in (('eisi2','eisiw','ziq'),('eisi3','eisix','zir'))],k('ue',k('eisio'),k('eisiz'),k('ri')),op('u',op('e',k('eisio'),k('eisiz')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eil6',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='local_times_only_and_comparison_without_further_stipulation',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/second-local-clock-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'] += [dict(symbol=n,role='designation',forms=[dict(text=t,language='de',role='printed_identifying_form')]) for n,t in (('eisi2','A-Zeit'),('eisi3','B-Zeit'))]
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
