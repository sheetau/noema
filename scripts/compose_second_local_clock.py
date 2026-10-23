"""Compose the second local clock and the exact-constitution qualification."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_local_clock_valuation import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-local-clock-valuation.noema';PARENT_BASIS='data/local-clock-valuation-basis-v1.json'
FULL='examples/v014/einstein-second-local-clock.noema';CORE='examples/v014/second-local-clock-core.noema'
BASIS='data/second-local-clock-basis-v1.json';ANNOTATIONS='data/second-local-clock-identifiers-v1.json';INDEX=235
PAIR=[(n,'a') for n in ('left','right','document')]+[('context','d')]
FEATURE=[(n,'a') for n in ('left','right','feature','standard','document')]+[('context','d')]
PRIMITIVES={
 'eisif':([(n,'a') for n in ('left','right','standard','document')]+[('context','d')], 'standardが、同じdocumentの同じ二時計のBeschaffenheitを比較するため、その構成を記述する全特徴と共通の記述規約を定める。時計の材質・部品の組合せと結合・周期生成と指針表示の構成、および同じ条件での固有の応答を対象とする。比較に適合した完全な規約であり、一致した項目だけを選んだ検査表ではない。設置場所、個体番号、読みの初期位相・原点設定は構成上の同一性に含めず、時計の同一個体性や同期を認定しない。個々の特徴の一致は別に合成する。'),
 'eisig':([(n,'a') for n in ('standard','feature','document')]+[('context','d')], '同じstandardで時計の構成を漏れなく比較する全特徴範囲にfeatureが属する。一致した特徴だけや測定済みの項目へ範囲を狭めない。材質や構造を具体的にどの方式へ限定するかは原文に追加せず、方式の違いも比較できる共通の記述規約を用いる。'),
 'eisih':([(n,'a') for n in ('clock','feature','standard','value','document')]+[('context','d')], '同じclockの構成について、standardのfeatureに属する質的な内容がvalueで記述される。valueは共通規約で同定された構成記述であり、単なる外見の似た名前・検査結果の真偽・時計の現在の指示値ではない。部品の配置や結合、材質、固有応答などの該当内容を全て含め、他の時計で余分な構成があれば同じ記述集合とはしない。未知の特徴を空集合や共通値で埋めない。数値を含む構成記述も同じ物理単位と規約で同定する。'),
 'eisii':([('node','a'),('author','a'),('host','i[e]'),('qualification','i[e]'),('intention','i[e]'),('document','a'),('context','d')], 'authorがnodeでhostを述べる途中に、qualificationを条件に付け加えるintentionを、ダッシュと引用に相当する挿入として提示する。追加対象を同じ条件内容に固定し、無関係な時計の話や挿入を消した断言へ替えない。挿入の提示から時計の構成一致の現実の真理を導かない。'),
 'eisij':([('node','a'),('author','a'),('prior','i[e]'),('additional','i[e]'),('document','a'),('context','d')], 'authorがnodeで、同じdocumentのpriorに対してadditionalも同様に扱うものとして追加するauchの談話関係。二つの対応する内容と向きを保持し、因果・同義性・排他的な選択・双方の無条件の現実成立を含意しない。'),
 'eisik':([], 'u0013第二文の点Bに置く別の時計への参照。第一文のA側時計eisibと区別し、構成の一致を指示値の一致や同じ個体へ替えない。'),
 'eisil':([], 'u0013第二文の点Bにいると設定する観測者への参照。著者本人やA側の観測者と同一とは要求しない。'),
 'eisim':([], 'u0013第二文のB側時計の一般の指針表示部分への参照。'),
 'eisin':([], 'u0013第二文の点Bの直近の出来事を時間的に評価する課題への参照。A側の課題と同様の方法を使うが、対象の場所と出来事の範囲を取り替えない。'),
 'eisio':([], '固定原文einstein-1905:u0013[252,560)の第二文の箇所。原刊893頁末から894頁冒頭へ続く。'),
}
MEANINGS={
 'eilc':'同じ特徴について両時計が共通の非空の構成記述集合を持つ。共通する一項目だけでなく、各値の帰属が両方向に一致することを要求する。',
 'eild':'二つとも時計であり、完全な構成比較の同じ規約と非空の全特徴範囲があり、その全特徴でeilcの正確な一致が成立する。程度の近さ・同じ読み・時計個体の同一性で代用しない。',
 'eile':'先行するA側の同じ時計eisibが点ziqにあるという条件内容。',
 'eilf':'B側の同じ時計eisikが点zirにあるという条件内容。',
 'eilg':'B側時計と先行A側時計がeildの意味で全く同じ構成を持つという追加条件内容。同期や初期の読みの一致を追加しない。',
 'eilh':'第一文の同じA側の局所評価の可能性eik6を取り出した内容。auchの比較元として用いる。',
 'eili':'同じ一般定義eik6をB側の観測者・時計・指針・場所・対象課題へ適用した局所評価の可能性。',
 'eilj':'A側の設定にB側の時計と正確な構成一致を加えた条件の下で、B側でもeiliが可能であるという主節。二地点・二時計を区別する。',
 'eilk':'著者が同じ第二文の仮定範囲へ構成一致eilgを付け加えて採用する操作の内容。',
 'eill':'同じeilkをこれから付け加えるという著者の意思。意思の対象を別条件へ交換せず、内容の実証や行為の実行を自動導出しない。',
 'eilm':'条件付き可能性eiljと挿入の意思eillを同じ評価点で結ぶ第二文の全内容。',
 'eiln':'第二文の条件・可能性・意思eilmを主張するメッセージ。',
 'eilo':'同じ著者・論説への帰属、時計の追加と可能性の追加という二つのauch、構成一致を付け加える意思の挿入、第一文からの順序を保つ。',
}
LIMITS=[
 'Befindet sich auch ... so ist auch ... möglichを、A側の設定を引き継ぎ、B側にも同じ構成の別時計を置くなら同様の局所評価が可能という条件として読む。両時計の現実的存在や実行済みを無条件に主張しない。',
 'genau derselben Beschaffenheitを、時計の構成を記述する完全な共通規約の下で全特徴の内容が一致することと読む。単なる近似、外見、同じ型番、校正値一つの一致へ弱めない。個体の同一性、設置場所、現在の指示値やその初期位相は構成の比較対象にしない。',
 '構成記述の共通規約と全特徴範囲は明示した意味規約付きの入力であり、有限の検査項目だけで実機の完全一致を実証しない。全特徴ごとに非空で両方向に一致する記述集合を要求し、片側だけの余分な構成や未知の値を無視しない。',
 'wir wollen hinzufügenは同じ構成条件をこの文の設定へ付け加える意思として保持する。引用符内は原語の綴り自体でなく追加する条件内容を指し、ダッシュによる挿入と二つのauchを別に保持する。',
 'Bの局所評価には第一文のeik6以下を再利用する。近傍、同時の指針表示、全対象と一つの候補状況という解釈を保ち、AとBの時計の同期・同じ時計原点・遠隔出来事の比較を追加しない。M0005・M0007・M0008はzir、M0006はziq。',
 '第二文234非空白本文文字と四つの場所記号を対象とする。第三文以降の共通時間と同期の導入、およびu0013全体の判断は未完。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    attr=lambda clock:k('eisih',v(clock),v('feature'),v('standard'),v('value'),v('document'),v('context'))
    text+=define('eilc',FEATURE,both(q('g','value','a',attr('left')),q('f','value','a',both(op('y',attr('left'),attr('right')),op('y',attr('right'),attr('left'))))))
    member=k('eisig',v('standard'),v('feature'),v('document'),v('context'))
    common=q('g','standard','a',both(k('eisif',v('left'),v('right'),v('standard'),v('document'),v('context')),q('g','feature','a',member),q('f','feature','a',op('y',member,k('eilc',*[v(n) for n,_ in FEATURE])))))
    text+=define('eild',PAIR,both(k('ca',v('left')),k('ca',v('right')),common))
    for name,clock,place in (('eile','eisib','ziq'),('eilf','eisik','zir')):
        text+=content(name,k('eiky',k(clock),k(place),k('ra'),v('point')))
    text+=content('eilg',k('eild',k('eisik'),k('eisib'),k('eirf'),v('point')))
    for name,names in (('eilh',('eisie','eisic','eisib','eisid','ziq')),('eili',('eisin','eisil','eisik','eisim','zir'))):
        text+=content(name,k('eik6',*[k(n) for n in names+('ra','rb','eirf')],v('point')))
    evaluate=lambda n:'t[k '+n+'[]][v point]'
    premise=both(*[evaluate(n) for n in ('eile','eilf','eilg')],op('u',op('e',k('ziq'),k('zir'))),op('u',op('e',k('eisib'),k('eisik'))))
    text+=content('eilj',op('y',premise,evaluate('eili')))
    text+=content('eilk',k('ug',k('eisio'),k('rd'),quote('eilg'),k('eisio'),v('point')))
    text+=content('eill',k('eiscf',k('rd'),quote('eilk'),k('eirf'),v('point')))
    text+=content('eilm',both(evaluate('eilj'),evaluate('eill')))
    text+='d eiln[] f[j s[k eilm[]]].\n'
    text+=define('eilo',[],both(k('eir3',k('eisio'),k('rd'),k('eirf'),quote('eiln'),k('ri')),*[k('eisij',k('eisio'),k('rd'),quote(a),quote(b),k('eirf'),k('ri')) for a,b in (('eile','eilf'),('eilh','eili'))],k('eisii',k('eisio'),k('rd'),quote('eilj'),quote('eilg'),quote('eill'),k('eirf'),k('ri')),k('ue',k('eish2'),k('eisio'),k('ri')),op('u',op('e',k('eish2'),k('eisio')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eilo',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='second_local_clock_with_exact_constitution_and_additional_qualification',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/local-clock-valuation-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
