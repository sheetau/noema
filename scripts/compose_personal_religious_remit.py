"""Leave personal religious choices unprescribed and outside monarchical remit."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind

PARENTS=('data/personal-salvation-judgment-basis-v1.json','data/monarchical-sentence-basis-v1.json')
LIBRARY='examples/v016/personal-religious-remit.noema'
BASIS='data/personal-religious-remit-basis-v1.json'
FAMILY='i b[h[j[a] d] e]'
NAMES=('actor','person','community','undertaking','goal')
FIELDS=' '.join(n+' a' for n in NAMES)+' reference d'
ARGS=' '.join('v '+n for n in NAMES)+' v reference'
PERSONAL='l[a][v person v undertaking v goal]'
ROLE='k h26hn[v person v community v reference]'
PRIMITIVES={
 'h26hn':('[a a d] a',['person','community','reference'],
   '同じ共同体・固定基準で、本人が自身の宗教上の判断と実践を選び、何を自分の救済のため必要とするかを決める側の立場。公的な法秩序に関わる市民の立場h244gとは評価の次元を分ける。特定宗派、国籍資格、現に判断・実行したこと、無限定の権利や実行能力をこの立場参照だけから導かない。'),
 'h26ho':('[a a '+FAMILY+' j[a] d d] c',['activity','person','role_content','bindings','reference','point'],
   '同じ活動がこの点で、同じ本人の閉じた段階1内容族・対象列・基準で指定される選択又は実行へ、その本人に代わる決定を押し付けるか、その本人の選択・実行を権威的・強制的に妨げる介入となる。行為の生起と介入主体の参加は別に結ぶ。内容族に明示された立場を保持し、宗教上の正否や必要性の決定への介入と、公的秩序を守り他者への暴力を防ぐ別の職務次元を混同しない。単なる助言・説得・意見の相違・関心や、他人の活動の偶然の共起は介入としない。'),
 'h26hp':('[a a '+FAMILY+' j[a] d d] c',['office','community','matter','bindings','reference','point'],
   '同じ共同体の同じ公的職について、段階1の閉じた内容族・同じ対象列・基準が指定する事項を公的に判断・処理することが、この点でその職の所管・職責の範囲にある。内容が宗教上の必要性なら、その正否を本人に代わって公的に決定する事項である。心理的な関心、知識、身体能力、実際の介入、現職者の好みや一方的な管轄主張とは別であり、内容の真理や実際の履行は含意しない。'),
}
MEANINGS={
 'r5nr':'本人・営み・救済目的の正確な三対象列と固定基準から、r5nlの目的に相対的な必要性内容を返す。所管対象に引用でき、呼び出し時に必要性を評価する場合と引用で保持する場合を区別する。',
 'r5ns':'同じ君主を規範の出所とし、同じ本人の宗教的自己選択の立場h26hnで、同じr5npの営み内容への実行要求も不実行要求もない。積極的な許可の発令を追加せず、他の規範源や市民的職務の規律まで消さない。',
 'r5nt':'本人・共同体・営み・救済目的・立場の正確な五対象列を、本人の宗教的自己選択の立場と同じr5np実行内容へ接続する。立場はh26hnの同一性で明示し、介入の対象を市民一般の全活動へ拡張しない。',
 'r5nu':'同じ点で実際に生起する活動に同じ君主本人が参加し、その同じ活動が同じ本人・宗教的選択立場・営み・救済目的へのh26hoの介入となる。活動が未実行、主体や介入対象が異なる場合は満たさない。',
 'r5nv':'同じ本人の宗教的な営みについて、r5nsの両方向の指図の不在と、同じ君主のr5nu介入活動が一つもないことを結ぶ。指図が未執行でも、規範なしの実力介入でも満たさない。本人の実行、救済の真理・成功、君主の心理的無関心は要求しない。',
 'r5nw':'同じ点で同じ共同体の君主であり、本人が保持する全ての同じ最高統治職について、本人の同じ救済目的への営みの必要性r5nrが公的な所管に属さない。職の空席を所管外の証拠にせず、別の役職・対象内容の所管で判定しない。',
 'r5nx':'同じ君主・共同体・固定基準について、その基準の臣民r5niと本人の内容r5nkに当たる全候補の呼称r5nnを確認し、本人の必要性判断r5nqにも当たる全候補に同じ評価点でr5nvの指図と介入の不在を要求する。呼称不備を非信念へ隠さず、許可済み・実行済みのものだけに絞らず、評価点で信念が変わっても元の範囲を消さない。',
 'r5ny':'r5nxと同じ固定基準の全ての臣民・営み・救済目的について、同じ君主のr5nwの所管外が同じ評価点で成り立つ。規範的な指図の不在から所管外を自動的に推論しない。',
 'r5nz':'正確な君主・共同体の二対象列と固定基準をr5nxの全対象への委任内容へ渡す。後続でkannの対象に引用でき、引用から実際の不干渉や臣民の行動を導かない。',
 'r5n2':'正確な君主・共同体の二対象列と固定基準をr5nyの全対象の所管外へ渡す。後続で本人への委任と職責上の対照を同じ君主に結べる。',
}
LIMITS=[
 '第十一文seine Unterthanen übrigens nur selbst machen lassen ... das geht ihn nichts anの依存群。本人の宗教的自己選択に対する君主の非指図・非介入と、その必要性を公的に決める所管の不在を構成する。kannの規範的な許容、Wennの監督条件、nur/übrigens/wohl aberの全文での限定・対照はまだ接続せず、意味確認文字数は増やさない。',
 'lassenはここでは、同じ本人の宗教的な正否・必要性に基づく判断と実践の選択を君主が指図・代行・強制的に妨害しないことと読む。積極的な許可の発令、本人の実行、目的の正しさ、君主の無関心を必要条件にはしない。規範的な禁止が未執行であるだけ、又は指図なしに実力介入する場合と区別する。',
 'übrigensが示す留保を保つため、内側の規範はh26hnの宗教的自己選択の立場に固定する。公的な外的行為の規律や他者への暴力防止を否定する構成ではない。単に秩序と呼べば宗教的支配が許される免除も設けない。対象次元の区別は引用するr5ntに明示し、全文化・全行為・全規範源への不干渉へ広げない。全文で実効的監督と暴力的妨害防止の積極的職責を併記する必要がある。',
 'das geht ihn nichts anは救済の正否・必要性を本人に代わって公的に決める職責・所管の否定として読む。何も要求していないこととは独立で、本人に善意があるか、宗教に関心があるか、実際に関与したかとも別である。君主としての役職と同じ対象内容を明示する。',
 '全称の対象は固定基準でのr5nq全体。後の信念の変化、営みの実行、規範の有無や救済の真理で範囲を選び直さない。空範囲の場合に全称だけが成立することは許すが、臣民が存在するという追加の事実や一人以上の成功例を原文外に補わない。全文の一般的事例範囲と同じ君主・共同体・基準へ接続する。',
 '規範の段階1対象はr5np、介入の段階1対象は立場を含むr5nt、所管の段階1対象は必要性r5nrであり、同じ真偽だけで交換しない。引用する側では営みも必要性も実行しない。r5nt内の立場照合は内容の帰属を保持する条件であり、本人が現に活動する条件を外側に付けない。',
 '君主が参加する同じ活動を介入の判定対象とする。命令・方針は実際の執行の有無によらずr5nsが扱い、本人が起こす指図・強制はr5nuが扱う。dfは参加であり、君主一人が全てを直接執行することには限定しない。他の独立主体の全介入がなくなることまでは主張せず、他人同士の暴力的妨害防止は後続に残す。',
 '全称の各候補ではr5niとr5nkが定める臣民・本人内容の範囲でr5nnの呼称妥当性を先に確認する。別の対象を指す呼称を、必要だとは信じていない事例や空の範囲へ変換しない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    text='d r5nr[bindings j[a] reference d] e[b point['+bind(('person','undertaking','goal'),
        't[k r5nl[v person v undertaking v goal v reference]][v point]')+']].\n'
    norm=lambda sign:'k h237z[v actor v person '+ROLE+' r b[p r5np] '+PERSONAL+' v reference '+sign+' v point]'
    text+='d r5ns['+FIELDS+' point d] c['+both('u['+norm(TRUE)+']','u['+norm(FALSE)+']')+'].\n'
    # Include the personal standing as an explicit fifth argument of the quoted
    # interference target, rather than relying on equal truth values of actions.
    personal=('person','community','undertaking','goal','role')
    text+='d r5nt[bindings j[a] reference d] e[b point['+bind(personal,both('e[v role]['+ROLE+']',
        't[k r5np['+PERSONAL+' v reference]][v point]'))+']].\n'
    intervention='k h26ho[v activity v person r b[p r5nt] l[a][v person v community v undertaking v goal '+ROLE+'] v reference v point]'
    text+='d r5nu['+FIELDS+' activity a point d] c['+both('k dg[v activity v point]','k df[v actor v activity v point]',intervention)+'].\n'
    text+='d r5nv['+FIELDS+' point d] c['+both('k r5nk[v person v undertaking v goal v reference]','k r5ns['+ARGS+' v point]',
        'u[g activity a[k r5nu['+ARGS+' v activity v point]]]')+'].\n'
    office=both('k h234f[v office v community v point]','k r2ui[v actor v office v community v point]')
    remit='k h26hp[v office v community r b[p r5nr] '+PERSONAL+' v reference v point]'
    text+='d r5nw['+FIELDS+' point d] c['+both('k r2uj[v actor v community v point]',
        'f office a[y['+office+'][u['+remit+']]]')+'].\n'
    for name,target in (('r5nx','r5nv'),('r5ny','r5nw')):
        frame=both('k r5ni[v actor v person v community v reference]','k r5nk[v person v undertaking v goal v reference]')
        body='y['+frame+']['+both('k r5nn[v person v undertaking v goal v reference]',
            'y[k r5nq['+ARGS+' v reference]][k '+target+'['+ARGS+' v point]]')+']'
        for n in reversed(('person','undertaking','goal')):body='f '+n+' a['+body+']'
        text+='d '+name+'[actor a community a reference d] e[b point['+body+']].\n'
    for name,target in (('r5nz','r5nx'),('r5n2','r5ny')):
        text+='d '+name+'[bindings j[a] reference d] e[b point['+bind(('actor','community'),
            't[k '+target+'[v actor v community v reference]][v point]')+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5nl','r5np','r5nq'],['h237z','dg','df'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='personal_religious_nonprescription_nonintervention_and_public_remit',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
