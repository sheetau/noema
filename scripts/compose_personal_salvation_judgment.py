"""Compose political subjects and fallible judgments of means to personal salvation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENT='data/monarchical-sentence-basis-v1.json'
LIBRARY='examples/v016/personal-salvation-judgment.noema'
BASIS='data/personal-salvation-judgment-basis-v1.json'
FIELDS='person a undertaking a goal a reference d'
ARGS='v person v undertaking v goal v reference'
PRIMITIVES={
 'h26hi':('[a a a d] c',['person','role','community','point'],
   '本人がこの点で、同じ共同体の同じ最高統治職の公的管轄・統治権に服する制度上の立場にある。現に命令に従う行動、同意、権威の正当性、私的所有・農奴身分、単なる居住・滞在、近代的な国籍・参政権とは区別する。最高職とその同じ君主による保持は別に構成する。'),
 'h26hj':('[a a d] c',['goal','person','reference'],
   '同じ固定基準の目的内容が、同じ本人自身の宗教的・精神的な究極の安寧ないし救済に関する。内容自体はh246eで閉じたNoema記述を得る。世俗的な富・健康や別人だけの救済と区別するが、魂の実在・不死、神の存在、一宗派の教説、実際の救済、本人の信念をこの分類から断定しない。'),
 'h26hk':('[a a d] c',['undertaking','person','reference'],
   '同じ固定基準の営み内容が、同じ本人自身の行為・実践を記述する。h246eの閉じたNoema内容で行為の具体的条件を指定し、別人だけの行為を本人の行為へ替えない。学習・判断・祈りその他の宗教実践を排除せず、公的発言だけに限らない。実行、許可、必要性、目的達成は含意しない。'),
 'h26hl':('[a a a d d d] c',['person','undertaking','goal','reference','assessment','outcome'],
   '同じ本人・営み・目的・固定基準・評価点について、必要な手段を判定するための、背景条件を固定した関連する実践的可能経過の全範囲にoutcomeが属する。目的達成や営みの実行、本人の信念を先に条件として候補を選ばない。outcomeは経過全体を評価できる状況で、行為と救済を同じ物理的瞬間に起こる事象へ狭めない。絶対的な神学的可能性の決定ではなく、明示された前提下での目的相対的な可能経過の範囲。'),
 'h26hm':('[a i b[e] d] c',['person','content','point'],
   '本人がこの点で、段階1の閉じた内容を成り立つものとして受け入れ、判断している。既存h233cの誤りうる信念を段階1へ広げる。引用された内容の実行、真であること、知識・確信、発言、実際の行動を要求しない。段階0内容を内部で評価する命題についても、外側の信念はその命題の真偽を先に決めない。'),
}
MEANINGS={
 'r5ni':'同じ点の人について、同じ共同体の君主r2ujと、その本人が保持する同じ最高統治職r2ui・h234fへの制度的服属h26hiを結ぶ。別の君主・役職・共同体・点の服属で補わず、現実の服従行動を追加しない。',
 'r5nj':'同じ人自身の宗教的な救済・究極の安寧を内容とする目的の分類。目的内容が成り立つとはまだ断定しない。',
 'r5nk':'同じ人自身の営みと、自身の救済に関する目的を、同じ固定基準で結ぶ。まだ、その営みの必要性や実行を要求しない。',
 'r5nl':'同じ本人・営み・目的・基準で、評価点から関連する可能経過を取り、少なくとも一つで目的内容が成立し、目的が成立する全経過で営み内容も成立する。達成不能な目的からの空虚な必要性を除き、十分条件や実際の行動・救済と区別する。',
 'r5nm':'本人・営み・目的・固定基準の閉じた名前をr5nlへ適用した、段階1の閉じた必要性内容。名前は次の妥当性検査を通して元の対象に結ぶ。',
 'r5nn':'h223gで選んだ本人・営み・目的の各呼称とh223hの固定基準の呼称が、同じ元の対象・状況を指すことを全て確認する。異なる名前を必要性の判断へ流し込まない。',
 'r5no':'同じ本人が、同じ本人自身の営みを自身の救済目的のため必要とするr5nl内容を、同じ点で受け入れている。r5nkの内容帰属とr5nnの呼称妥当性を要求するが、引用された必要性や営み・救済の実際の成立は要求しない。',
 'r5np':'正確な本人・営み・救済目的の三対象列と基準について、同じ本人の営み内容がこの点で実際に成立する。将来の信念の持続や目的達成を行為そのものの条件へ混ぜない。',
 'r5nq':'同じ君主の同じ共同体における臣民r5niと、その同じ人の自身の救済に必要だという営み判断r5noを同じ点で結ぶ。後続の委ねる範囲に使う対象条件であり、行為の実行や君主の許可・不干渉を先取りしない。',
}
LIMITS=[
 '第十一文seine Unterthanen ... was sie um ihres Seelenheils willen zu thun nöthig findenの対象範囲と必要性の自己判断を構成する。本人に委ねるlassen、nur/übrigens、主節のkann、監督条件との接続はまだ含めず、文全体の意味確認文字数は増やさない。',
 'Unterthanenは同じ君主の共同体の最高統治権に服する制度上の人々と読む。Adelungの国家・領邦の最高権力に対する第二義を採り、私的領主への農奴的服属、現に命令を守る人だけ、現代の参政資格には限定しない。',
 'Seelenheilは本人自身の宗教的・精神的な究極の安寧ないし救済という目的内容として読む。特定の教義を唯一の真理として追加しない。具体的な目的も営みもh246eの閉じたNoema内容を必要とし、出典名だけで内容を代用しない。',
 'nöthig findenは誤りうる本人の実践的な必要性判断。関連する背景条件下で目的が達する全可能経過にその営みが含まれることを必要性の内容とする。少なくとも一つの目的達成経過を要求し、不能な目的ゆえ何でも必要になる読みは採らない。この条件も信念の内部にあり、実際の目的達成可能性を臣民の選別条件にしない。',
 '必要性の内容r5nlは段階0の実内容を評価するため、引用には段階1を使う。本人が必要と考えるr5noはこの引用内容を実行しない。誤った必要性判断、未実行、実際には達成不能な目的も本人の判断があれば対象になりうる。',
 '本人・営み・目的・固定基準の呼称を別々に照合する。r5npは実行内容だけの接続先で、本人の判断が後に変わったことを、それ以前から区別してきた行為の消滅へ替えない。',
 'ここでは存在や対象条件を構成するのみ。全文での臣民全員への量化、君主の職責、強制的妨害とその防止、全能力で救済を決定・促進する後続と照応は未接続。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def definitions():
    role='g role a['+both('k h234f[v role v community v point]','k r2ui[v actor v role v community v point]',
        'k h26hi[v person v role v community v point]')+']'
    text='d r5ni[actor a person a community a point d] c['+both('k aa[v person]','k r2uj[v actor v community v point]',role)+'].\n'
    text+='d r5nj[person a goal a reference d] c['+both('k aa[v person]','k h26hj[v goal v person v reference]')+'].\n'
    text+='d r5nk['+FIELDS+'] c['+both('k r5nj[v person v goal v reference]','k h26hk[v undertaking v person v reference]')+'].\n'
    candidate='k h26hl['+ARGS+' v point v outcome]'
    achieved='t[s[k h246e[v goal v reference]]][v outcome]'
    undertaken='t[s[k h246e[v undertaking v reference]]][v outcome]'
    text+='d r5nl['+FIELDS+'] e[b point['+both('k r5nk['+ARGS+']','g outcome d['+both(candidate,achieved)+']',
        'f outcome d[y['+both(candidate,achieved)+']['+undertaken+']]')+']].\n'
    names=('person','undertaking','goal','reference')
    text+='d r5nm[person i[a] undertaking i[a] goal i[a] reference i[d]] i b[e][o a[r b[p r5nl]]['+' '.join('v '+n for n in names)+']].\n'
    valid=['e[s[k h223g[v '+n+']]][v '+n+']' for n in names[:-1]]+['e[s[k h223h[v reference]]][v reference]']
    text+='d r5nn['+FIELDS+'] c['+both(*valid)+'].\n'
    code='k r5nm['+' '.join('k h223g[v '+n+']' for n in names[:-1])+' k h223h[v reference]]'
    text+='d r5no['+FIELDS+' point d] c['+both('k r5nk['+ARGS+']','k r5nn['+ARGS+']','k h26hm[v person '+code+' v point]')+'].\n'
    text+='d r5np[bindings j[a] reference d] e[b point['+bind(names[:-1],both('k r5nk['+ARGS+']','t[s[k h246e[v undertaking v reference]]][v point]'))+']].\n'
    text+='d r5nq[actor a person a community a undertaking a goal a reference d point d] c['+both(
        'k r5ni[v actor v person v community v point]','k r5no['+ARGS+' v point]')+'].\n'
    return text

def build():
    source=parent();doc=deepcopy(source.document);doc.update(declarations=closure(source.document,['aa','r2uj','r2ui','h234f','h223g','h223h','h246e']),statements=[])
    imported={d['name']:source.entries[d['name']] for d in doc['declarations']}
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(source.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='same_political_subject_and_fallible_necessary_means_to_own_salvation',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(source.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
