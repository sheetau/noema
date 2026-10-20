"""Compose better arrangements, their proposed adoption, and public communication."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both

PARENT='data/clerical-obligation-basis-v1.json'
LIBRARY='examples/v016/reform-proposals.noema'
BASIS='data/reform-proposals-basis-v1.json'
TARGET='i[h[j[a] d] e]'
BIND_NAMES=('older','newer','field','standard')
NAMES=('person','activity','scholar','audience','proposal','church','field','subject','older','newer','standard')
FIELDS=' '.join(n+' a' for n in NAMES)+' reference d'
ARGS=' '.join('v '+n for n in NAMES)+' v reference'
PRIMITIVES={
    'h246v':('[a a a d] c',['field','church','subject','reference'],
        'この検討領域は、同じ宗教共同体に関わる宗教的な教え・実践のあり方と、それを共同で営む教会の制度・組織・運営を扱う。指定の宗教主題を含み、一回の儀式、建物の配置や組織集団だけへ限定しない。他の共同体にも共通する制度上の問題を排除しない。具体的な構成案やその優劣は別に結ぶ。'),
    'h246w':('[a a d] c',['configuration','field','reference'],
        '指定の構成は、同じ領域の営みを秩序立てる規則・手続・役割の配分や相互関係を定めるあり方である。既存の構成と構想上の候補をともに分類し、現に実施されること、唯一性や優劣は含意しない。名前だけの違いを制度的な違いと認定しない。'),
    'h246x':('[a a d] c',['configuration','field','point'],
        'この評価点では、指定領域の営みが同じ構成の規則・手続・役割関係に従って実際に組織されている。構想、提案、採用への賛同だけとは区別する。成功・正当性・改善や永久の維持を含意しない。'),
    'h246y':('[a a a a d d] c',['standard','field','left','right','reference','point'],
        '固定基準で明示した同じ評価基準に照らし、この評価点における同じ領域の構成の左は右に少なくとも劣らないと評価される。領域に関係する目的・事情・規範を基準として明示し、結果に合わせて基準を交換しない。相互成立は同程度、双方不成立は比較不能として扱い、未知とは分ける。基準の唯一の正当性や現実の実施を含意しない。'),
    'h246z':('[a a '+TARGET+' j[a] d d] c',['person','proposal','target','bindings','reference','point'],
        'この案は同じ本人の提案として、閉じた内容関数へ指定順の個体列と基準点を渡す内容の採用・実現を、他者の検討に付すものとして位置付けられている。単なる真偽の予測・比較評言・他人の案の中立的引用とは区別する。本人の見解を表す提案の内容指定であり、実際の伝達、命令権、採用の義務・実行・実現可能性は要求しない。'),
    'h247a':('[a a a '+TARGET+' j[a] d d] c',['activity','recipient','proposal','target','bindings','reference','point'],
        '同じ提示活動でこの受け手へ、指定案が、同じ内容関数・個体列・基準点で指定した内容の採用・実現を検討に付す提案として示される。単なる案名への言及、別内容の提案、成立済みの事実としての断言だけとは区別する。提案者・生起は別に結び、受領・理解・賛同・採用の義務や実際の改善は含意しない。'),
}
MEANINGS={
    'r36z':'同じ領域の比較元と候補を構成として分類し、同じ固定基準・評価点で両者の自己比較が成立し、候補は比較元以上、逆は不成立という厳密な改善内容を構成する。同程度・比較不能・自己比較の欠如は通さず、数値や全観点での無損失を補わない。',
    'r362':'比較元・候補・領域・評価基準の正確な四個体列へ、同じr36zの厳密な改善と候補構成の実際の実施h246xを結ぶ目標内容。提案対象として引用する場合、この改善や実施は評価しない。',
    'r363':'同じ教会の制度的共同体h246d、宗教上の主題h245z、共同の宗教実践hzxiへの位置付けh246hを、宗教と教会の営みの同じ検討領域h246vへ結ぶ。教義の真理や現在の礼拝の実行は要求しない。',
    'r364':'本人の同じ案について、r363の領域、同領域の比較元と候補の構成、基準点で実施される比較元を固定し、r362の改善と候補実施を同じ四個体列・基準点で提案内容へ渡す。案の現実の改善・採択・実施を資格条件にしない。',
    'r365':'同じ本人による同じ提示活動の生起を、固定した非空の公衆の全宛先への同じ案・r362の内容・四個体列・基準点の提案提示へ結ぶ。採用の義務や結果の成功を提示から導かない。',
    'r366':'同じ改善提案r364を、同じ本人の学識者としての公的活動r2ziと、その同じ活動の全読者世界cc/ceへ結ぶ活動候補。基準時に提案を伝え終わっていることは要求しない。',
    'r367':'同じ公的な改善提案候補r366と、同じ本人・活動・公衆・案・比較の束縛での実際の伝達r365を結ぶ内容。候補の基準点と伝達評価点を区別し、自由・使命の対象として引用できる。',
}
LIMITS=[
    'u0012[3186,3452)のVorschläge wegen besserer Einrichtung des Religions- und Kirchenwesensに向けた依存群。見解との全範囲の接続・自由・使命・談話・著者帰属は未統合で、確認文字数は加算しない。',
    'Einrichtungを宗教的な営みと教会組織の規則・手続・役割関係の構成として読む。対象を建物や一回の儀式に縮めない。原文が具体的な制度改正案や優劣の基準を列挙したとはしない。',
    'besserは固定された同じ基準による厳密な優越として読む。提案が目指す内容として保持し、現実の比較結果を提案資格の前提にしない。全ての観点が同時に改善するという強さや因果的な成功保証は加えない。',
    '比較の規則性は選択した二構成について確認する。未指定の全構成の全順序、尺度の測定法・唯一の正当性まで証明しない。比較元は基準点の現行構成とする明示した読みである。',
    '提案の採用・実現という内容と、案の伝達、強制的な命令、採用の義務、実施済みを分ける。個人の提案なので二人以上を求める既存rkoをそのまま適用しない。',
    '慎重な吟味と善意は前のGedankenを修飾する読みを保持する。提案全てへその資格を追加するかどうかは全文通読で範囲を明示し、原文にない資格を黙って追加しない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)


def definitions():
    def cmp(left,right):return 'k h246y[v standard v field v '+left+' v '+right+' v reference v point]'
    text='d r36z[older a newer a field a standard a reference d] e[b point['+both(
        'k h246w[v older v field v reference]','k h246w[v newer v field v reference]',
        cmp('older','older'),cmp('newer','newer'),cmp('newer','older'),'u['+cmp('older','newer')+']')+']].\n'
    goal=both('t[k r36z[v older v newer v field v standard v reference]][v point]','k h246x[v newer v field v point]')
    bound=both('e[v bindings][l[a]['+' '.join('v '+n for n in BIND_NAMES)+']]',goal)
    for n in reversed(BIND_NAMES):bound='g '+n+' a['+bound+']'
    text+='d r362[bindings j[a] reference d] e[b point['+bound+']].\n'
    text+='d r363[church a field a subject a reference d] c['+both('k h246d[v church v reference]',
        'k h245z[v subject v reference]','k h246h[v church r[p hzxi] v reference]',
        'k h246v[v field v church v subject v reference]')+'].\n'
    seq='l[a]['+' '.join('v '+n for n in BIND_NAMES)+']'
    candidate='person a proposal a church a field a subject a older a newer a standard a reference d'
    text+='d r364['+candidate+'] c['+both('k aa[v person]','k r363[v church v field v subject v reference]',
        'k h246w[v older v field v reference]','k h246w[v newer v field v reference]',
        'k h246x[v older v field v reference]',
        'k h246z[v person v proposal r[p r362] '+seq+' v reference v reference]')+'].\n'
    delivery='person a activity a audience a proposal a older a newer a field a standard a reference d'
    text+='d r365['+delivery+'] e[b point['+both('k dg[v activity v point]','k f3[v person v activity v point]',
        'g recipient a[k h6t[v audience v recipient v reference]]',
        'f recipient a[y[k h6t[v audience v recipient v reference]][k h247a[v activity v recipient v proposal r[p r362] '+seq+' v reference v point]]]')+']].\n'
    text+='d r366['+FIELDS+'] c['+both('k r364[v person v proposal v church v field v subject v older v newer v standard v reference]',
        'k r2zi[v person v activity v scholar v reference]','k cc[v activity v audience v reference]','k ce[v audience v reference]')+'].\n'
    text+='d r367['+FIELDS+'] e[b point['+both('k r366['+ARGS+']',
        't[k r365[v person v activity v audience v proposal v older v newer v field v standard v reference]][v point]')+']].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['aa','h246d','h245z','h246h','hzxi','r2zi','cc','ce','dg','f3','h6t']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='religious_ecclesiastical_arrangements_and_proposed_improvement',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
