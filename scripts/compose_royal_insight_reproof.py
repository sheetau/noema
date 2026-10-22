"""Compose self-assessed highest insight and exposure to justified reproof."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_protected_remarks import bind

PARENTS=('data/royal-writing-oversight-basis-v1.json','data/monarchical-religion-sentence-basis-v1.json')
LIBRARY='examples/v016/royal-insight-reproof.noema'
BASIS='data/royal-insight-reproof-basis-v1.json'
NAMES=('actor','community','person','project','work','field','regulation')
FAMILY='i[h[j[a] d] e]'
PRIMITIVES={
 'h26iu':('[a a a d d] c',['actor','standard','field','reference','point'],
   'この本人が同じ領域の認識の適切さを評価するため、この点でこの基準を自分の基準として採用している。他人だけの基準や基準名への言及と区別する。比較元を指定するh26doとは異なり、特定の比較元・最善の認識・正当な唯一の基準をあらかじめ含めない。'),
 'h26iv':('[a a d] c',['item','field','reference'],
   '同じ領域に関する認識上の評価で、固定した文脈において比較対象とする認識内容の全範囲に属する。成功した内容・本人が既に保持する内容・最善に見える内容だけへ後から絞らない。具体的な内容、領域への関係と代表化はh26ad/h26c5/h26agで、最高性と本人の判断は合成で別に与える。あらゆる可能な命題を無制限に比較するという前提は置かない。'),
 'h26iw':('[a a a a d d] c',['actor','office','specialist','field','reference','point'],
   '同じ領域の認識上の正否を判定する権威において、この人は同じ専門的学識者より上に立つ資格を、この統治職を保持することだけによって持つ。職による学問上の優越であり、政治的指揮系統、学識者の市民的服従義務、実力、本人の証拠に基づく専門知識の優越とは区別する。最高職の保持・相手の学識資格・この関係の否定は合成側で与える。'),
 'h26ix':('[a a d] c',['specialist','field','reference'],
   '同じ固定した領域の事柄を専門的に吟味する学識を備える者である。単なる肩書・当該領域の好み・全領域での無謬性とは区別する。政治的統治権や特定の発言の正しさは含めない。領域を文法・言語・文献解釈に指定することも、文脈上の別領域に指定することもできる。'),
 'h26iy':('[a d] c',['field','reference'],
   '同じ固定文脈で、この領域は文法・言葉の用法・学識に基づく文献の解釈を扱う領域である。古典的grammaticiの射程を現代の初等文法教師だけへ狭めず、政治的統治一般や宗教上の全判断へ無条件に広げない。'),
 'h26iz':('[a a d d d] c',['activity','actor','reference','point','candidate'],
   '同じ本人のこの活動が機会又は根拠を与え、この点から応答を受けうる場面として採る候補の全範囲にこの場面が属する。活動に無関係な空想・過去の別行為への反応と区別する。批判が実際にある場面だけを選別せず、応答の内容、批判性と正当化可能性は別に構成する。候補に応答があっても現実の発言・必然的な結果・活動の唯一原因性を含意しない。'),
 'h26i2':('[a a a '+FAMILY+' j[a] d d] c',['judgment','actor','activity','principle','bindings','reference','candidate'],
   'この候補場面のこの判断は、同じ本人の同じ行為を非難の対象とし、段階0の閉じた原則内容族に同じ対象列と固定基準を適用した内容を、その批判の規準として用いている。原則の中立的な紹介、他人の行為への批判、同じ真理値の別内容と区別する。判断の遂行者・正当化可能性は別に結び、原則の実行評価、現実の発言、批判への賛同又は処罰を自動的に加えない。'),
}
MEANINGS={
 'r5pn':'固定した同じ領域の全認識比較範囲h26ivが非空で、全項目がh26adと代表内容のh26c5により明示され、h26dnがその代表内容の全範囲で反射的・推移的・全比較可能な評価になっている。本人の保持や客観的な真理は別にする。',
 'r5po':'r5pnの整合した全比較範囲に属する同じ項目の代表内容が、その全項目以上と評価される最高性。同順位の最高を許し、単なる平均以上・一例への優越・唯一の最高へ替えない。',
 'r5pp':'項目・領域・評価基準の正確な三対象列と固定基準をr5poへ渡す内容族。本人による最高性の判断に引用でき、引用だけでは比較内容を実行しない。',
 'r5pq':'本人が同じ点で認識内容の判断と最高性の判断を自分のものとして保持し、自分の同じ基準を採用する。前者は同じ代表認識内容h26aeを肯定し、後者は同じ項目・領域・基準のr5ppを肯定する。客観的な真理や最高性の実行評価、現在新たな判断を形成することを要求しない。',
 'r5pr':'同じ行為についてr5pqの本人の見解があり、その内容判断を同じ活動の選択・遂行の理由h26drとして用いる。最高性についてのメタ判断まで別の動機であること、唯一の動機、実際の認識の正しさは要求しない。',
 'r5ps':'同じ君主・臣民・作品・活動についてr5peの統治的な内容介入があり、君主がその同じ監督活動を同じ領域についてr5prの自分の見識に基づいて行う。',
 'r5pt':'元の七対象列と固定基準をr5psへ渡し、最高の見識に基づく介入側を後の条件・比較へ引用できる内容族。',
 'r5pu':'同じ最高君主について、その共同体で本人が保持する全最高職と同じ領域の全学識者に対し、統治職の保持だけによる認識上の上位資格h26iwを否定する。本人の証拠に基づく学識の優越や学識者の市民的義務は否定しない。',
 'r5pv':'文法・言葉の用法・文献解釈の領域h26iyについて、全最高君主と共同体にr5puの限界があるというラテン語格言の一般内容。Caesarを特定の歴史的人物の出来事に限定しない。',
 'r5pw':'君主・共同体・領域の正確な三対象列へr5puを適用する内容族。本文では格言の権威限界を同じ宗教的認識領域へ文脈的に適用する。文法だけの一般命題からこの拡張が論理的に導出されたとはしない。',
 'r5px':'正確な空の対象列と固定基準へr5pvの一般格言内容を対応させる引用用内容族。文字列そのものの提示や著者帰属は全文統合で別に結ぶ。',
 'r5py':'同じ本人の生起した同じ行為が応答の機会又は根拠を与える候補場面に、r5pwの同じ君主・共同体・領域の原則を規準としてその行為を非難し、正当化できる判断がある可能性。現実に既に批判されたことや全候補で批判される必然性を要求しない。',
 'r5pz':'同じ七対象について、自分の最高とみなす見識に基づく統治的介入r5psと、その同じ監督活動に対する正当化可能な批判への曝露r5pyを結ぶ。',
 'r5p2':'同じ七対象列と固定基準をr5pzへ渡す内容族。二側の比較・条件・結果と全文の談話接続に備える部分構成である。',
}
LIMITS=[
 'aus eigener höchsten Einsichtは、君主が自分の見解を自分の採る評価基準で最上とみなし、その見解を同じ介入の理由として用いる読みを採る。höchstenには君主への敬称的な含みもありうるが、ここではその地位に対応する最上の見識という自認を明示する。唯一の歴史的読解とは主張せず、著者が君主の客観的な認識の正しさを保証する文にはしない。',
 '最高性は固定した同じ領域・比較範囲で全項目以上と構成する。同順位を許し、無限の全可能命題での絶対的な全知・唯一性や特定の比較元より少しよいことにしない。評価基準・比較範囲と具体的な認識内容は意味入力で明示する。',
 '内容判断と最高性判断は同じ本人が保持するが、別個であることも同一であることも許す。h26aeの内容とr5ppの最高性をそれぞれ引用し、真理や比較の成功を外側で実行しない。内容の把握が完全であること、現在の新たな判断行為、唯一の動機を補わない。h26drの履歴と評価点には同じ仮定場面を与え、その場面における行為の理由を表す。',
 'Caesar non est supra Grammaticosは、統治者という地位だけでは学識上の正否の決定において専門家の上に立てないという限界と読む。Caesarは最高統治者の役割例、Grammaticosは文法・言語の用法・文献解釈に通じた学識者。文法技術者だけへ狭めず、専門家に政治的統治権や無謬性を与えない。',
 '文字どおりの文法・文献領域の一般原則r5pvと、同じ限界を本文の宗教的認識領域へ適用するr5pwを分ける。後者は明示的な文脈的拡張であり、前者だけからの論理的帰結ではない。引用の実際の文字列、提示の仕方、著者による採用・帰属は全文統合時に別に結ぶ。',
 'Suetonius De grammaticis第4章のgrammatici/litteratiと第22章のMarcellusのTiberiusへの反論を、語の射程と政治的資格・言語上の正否を区別する古典的な並行例として確認した。Kantの格言と同一の文言ではなく、直接の出典又は伝承経路と断定しない。',
 'wo er sich dem Vorwurfe aussetztは、同じ介入が機会又は根拠を与える応答場面に、同じ原則を規準として同じ行為を批判でき、その判断が正当化可能であると読む。実際の発言の発生、特定の発言者、非難の必然性は主張しない。h26izは応答可能な範囲であり、批判性h26i2と正当化可能性h247iを分ける。',
 '今回の依存群だけでは第十二文の意味確認を増やさない。selbstの取り立て、würdigtの皮肉、原則の引用提示と著者帰属、聖職者の専制支援・残余臣民、二側の比較とnoch weit mehr、全仮定範囲・威厳への損傷との条件接続・全文通読は残る。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    canonical=lambda n:'k h26ag[v '+n+' v reference]'
    scope=lambda n:'k h26iv[v '+n+' v field v reference]'
    cmp=lambda l,r:'k h26dn[v standard v field '+canonical(l)+' '+canonical(r)+' v reference v assessment]'
    regular=both('g item a['+scope('item')+']',
        'f item a[y['+scope('item')+']['+both('k h26ad[v item v reference]','k h26c5['+canonical('item')+' v field v reference]',cmp('item','item'))+']]',
        'f left a[f right a[y['+both(scope('left'),scope('right'))+'][x['+cmp('left','right')+']['+cmp('right','left')+']]]]',
        'f left a[f middle a[f right a[y['+both(scope('left'),scope('middle'),scope('right'),cmp('left','middle'),cmp('middle','right'))+']['+cmp('left','right')+']]]]')
    text='d r5pn[field a standard a reference d assessment d] c['+regular+'].\n'
    text+='d r5po[item a field a standard a reference d assessment d] c['+both('k r5pn[v field v standard v reference v assessment]',scope('item'),
        'f other a[y['+scope('other')+']['+cmp('item','other')+']]')+'].\n'
    text+='d r5pp[bindings j[a] reference d] e[b assessment['+bind(('item','field','standard'),'k r5po[v item v field v standard v reference v assessment]')+']].\n'
    held=both('k h26ad[v item v reference]','k h26c5['+canonical('item')+' v field v reference]',
        'k h26ai[v actor v viewjudgment v reference v point]','k h26ai[v actor v rankjudgment v reference v point]',
        'k h26iu[v actor v standard v field v reference v point]',
        'k h245q[v viewjudgment '+canonical('item')+' r[p h26ae] v reference '+TRUE+' v point]',
        'k h26dq[v rankjudgment r[p r5pp] l[a][v item v field v standard] v reference '+TRUE+' v point]')
    text+='d r5pq[actor a viewjudgment a rankjudgment a item a field a standard a reference d point d] c['+held+'].\n'
    grounded=both('k r5pq[v actor v viewjudgment v rankjudgment v item v field v standard v reference v point]',
        'k h26dr[v actor v activity v viewjudgment v reference v point v point]')
    for n in reversed(('viewjudgment','rankjudgment','item','standard')):grounded='g '+n+' a['+grounded+']'
    text+='d r5pr[actor a activity a field a reference d point d] c['+grounded+'].\n'
    args=' '.join('v '+n for n in NAMES)+' v reference v point'
    params=' '.join(n+' a' for n in NAMES)+' reference d point d'
    text+='d r5ps['+params+'] c['+both('k r5pe['+args+']','k r5pr[v actor v regulation v field v reference v point]')+'].\n'
    text+='d r5pt[bindings j[a] reference d] e[b point['+bind(NAMES,'k r5ps['+args+']')+']].\n'
    authority='k h26iw[v actor v office v specialist v field v reference v point]'
    office=both('k h234f[v office v community v point]','k r2ui[v actor v office v community v point]')
    limit=both('k r2uj[v actor v community v point]',
        'f office a[y['+office+'][f specialist a[y[k h26ix[v specialist v field v reference]][u['+authority+']]]]]')
    text+='d r5pu[actor a community a field a reference d point d] c['+limit+'].\n'
    literal='f actor a[f community a[f field a[y['+both('k r2uj[v actor v community v point]','k h26iy[v field v reference]')+'][k r5pu[v actor v community v field v reference v point]]]]]'
    text+='d r5pv[reference d] e[b point['+literal+']].\n'
    text+='d r5pw[bindings j[a] reference d] e[b point['+bind(('actor','community','field'),'k r5pu[v actor v community v field v reference v point]')+']].\n'
    text+='d r5px[bindings j[a] reference d] e[b point['+bind((),'t[k r5pv[v reference]][v point]')+']].\n'
    reproach=both('k h26iz[v activity v actor v reference v point v candidate]',
        'k fa[v critic v judgment v candidate]',
        'k h26i2[v judgment v actor v activity r[p r5pw] l[a][v actor v community v field] v reference v candidate]',
        'k h247i[v judgment v reference v candidate]')
    text+='d r5py[actor a community a field a activity a reference d point d] c['+both('k dg[v activity v point]','k df[v actor v activity v point]',
        'g candidate d[g critic a[g judgment a['+reproach+']]]')+'].\n'
    text+='d r5pz['+params+'] c['+both('k r5ps['+args+']','k r5py[v actor v community v field v regulation v reference v point]')+'].\n'
    text+='d r5p2[bindings j[a] reference d] e[b point['+bind(NAMES,'k r5pz['+args+']')+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5pe'],['h26dn','h26dq','h26dr','h245q','h26ai','h26ae','h26ad','h26ag','h26c5','h247i','fa'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='self_assessed_highest_insight_and_possible_justified_reproof_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
