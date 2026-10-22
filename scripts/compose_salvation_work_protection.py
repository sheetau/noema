"""Compose full-capacity salvation work, violent hindrance and preventive duty."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_protected_remarks import bind

PARENTS=('data/personal-religious-remit-basis-v1.json','data/civic-oversight-basis-v1.json','data/monarchical-sentence-basis-v1.json')
LIBRARY='examples/v016/salvation-work-protection.noema'
BASIS='data/salvation-work-protection-basis-v1.json'
FAMILY='i b[h[j[a] d] e]'
PG='l[a][v person v goal]'
TWO='l[a][v actor v community]'
PRIMITIVES={
 'h26hq':('[a a d d] c',['person','goal','reference','point'],
   '本人が同じ目標について、それが何から成り何によって進められるかという自分の見解をこの点で定めている。固定基準は問われる目標内容の同一性を保つ。見解の確定であり、目標の実現、客観的な正解、他者への強制、教会又は君主による承認を含意しない。'),
 'h26hr':('[a a d a] c',['person','goal','reference','level'],
   '同じ本人が同じ目標への営みに投入できる力の程度として、同じ固定基準の能力条件の下で可能な全ての程度に属する。個々の能力の相互制約を含む総合的な投入程度で、原文にない数値単位を固定しない。実際に投入した程度、成功量、他人の最大能力を混ぜず、妨害を受けた結果に合わせて本人の基準能力を下げない。'),
 'h26hs':('[a a d a a] c',['person','goal','reference','left','right'],
   '同じ本人・目標・固定基準において、leftの投入程度はright以上であるという質的比較。能力や資源の種類を総合した当該営みの投入程度の評価基準に相対的であり、救済の真理・達成の比較ではない。反射性・推移性・比較可能性は合成側で検査する。'),
 'h26ht':('[a a a d d a] c',['person','work','goal','reference','point','level'],
   '同じ本人が同じ活動・目標・固定基準に関して、この点の営みに実際に投入する力の程度はlevelである。実際の活動生起・本人参加・目的は別に構成する。潜在能力、願望、別の活動の努力、達成の成功量ではない。程度の一意性と能力範囲への所属はr2clで別に確認する。'),
 'h26hu':('[a a '+FAMILY+' j[a] d] c',['person','work','target','bindings','reference'],
   'この固定基準で、同じ本人の同じ活動構成は、閉じた段階1内容族と同じ対象列・基準が指定する内容を目指して取り組む候補に属する。構造・対象・目的の対応であり、現在の実行・現に抱く意図・許可・達成可能性・妨害の有無を選別条件にしない。候補の全範囲を扱い、成功した又は既に必要だと判断した活動だけへ限定しない。'),
 'h26hv':('[a a d] c',['activity','victim','point'],
   '同じ活動がこの点で同じ対象者に対し、優越的な力を強制的に行使する。身体的な実力だけでなく、相手の選択を押し切る制度上・社会上の強制力も扱う。実際の負傷を必須にせず、単なる不賛同・論駁・助言・心理的な不快だけとは区別する。活動生起・行為者参加・妨害の因果性・力の行使の正当な権限は別に構成する。'),
 'h26hw':('[a a '+FAMILY+' j[a] d d] c',['activity','person','target','bindings','reference','point'],
   '同じ活動の働きがこの点で、同じ本人の閉じた段階1内容族・対象列・固定基準に指定された営みの機会・進行・実行の余地を因果的に損ない、又は妨げる。全面的な不能だけに限定せず、余分な障害を乗り越えて営みがなお成立する場合も扱う。単なる共起、妨害の意図だけ、無関係な目的への影響とは区別する。引用内容の不成立や現在の実行は要求しない。'),
 'h26hx':('[a a d d] c',['activity','person','reference','point'],
   '同じ活動でこの点の同じ対象者に強制力を行使することに、固定基準で採る権限・正当化の基準に照らした正当な根拠がある。現職者の自己申告、単に現行規則に書かれていること、宗教的な正しさの主張、物理的な強さとは区別する。正当な根拠の既知の不在と未知を分け、君主又は教会という名称だけでは真にしない。'),
}
MEANINGS={
 'r5n3':'本人・救済目的の正確な二対象列について、同じ本人自身の救済目的r5njとh246eの同じ実内容の成立を結ぶ。促進の目標に引用でき、引用だけから達成を導かない。',
 'r5n4':'同じ本人・救済目的の二対象列について、その目的が何から成り何によって進められるかという本人の見解h26hqが定まる内容。救済の達成や正しい神学的回答とは別の目標。',
 'r5n5':'同じ本人が同じ生起する営みに参加し、その同じ活動で同じ救済目的の決定r5n4と達成r5n3の両方を目指す。活動は複数の段階を含む取り組みでよく、両方の完成や一瞬での同時達成は要求しない。',
 'r5n6':'同じ本人・目的・固定能力基準の可能な投入程度が非空で、同じ程度比較がその範囲で反射的・推移的・全比較可能である。未評価や不正な比較を全力の証拠に使わない。',
 'r5n7':'r5n6の有効な能力範囲の中で、同じ活動への実際の投入程度がr2clにより一意であり、その程度が可能な全ての程度以上である。本人の能力に即した全力で、他人の最大能力や実際の成功を要求しない。',
 'r5oa':'同じ本人・活動・救済目的・基準・点で、決定と促進への営みr5n5と本人の能力に即した全力r5n7を結ぶ。取り組みは現実にあるが、救済の達成・見解の完成・正しさは必要ない。',
 'r5ob':'本人・活動・救済目的の正確な三対象列と固定基準を全力の営みr5oaへ渡す。暴力的妨害の対象を引用で保持し、阻まれた本人に現実の全力実行を要求しない。',
 'r5oc':'同じ本人自身の救済目的r5njについて、同じ活動が同じ決定r5n4と促進r5n3の両目標への取り組み候補h26huに属する。現在の実行や必要性の自己判断r5no、妨害の不在、救済の真理で候補を選ばない。',
 'r5od':'異なる二人のうち同じ加害側が参加する生起活動が、同じ被害側への優越的な強制力h26hv、その行使の正当な根拠h26hxの不在、同じ被害側の全力の営みr5obへの因果的妨害h26hwを伴う。力の行使だけ、正当な公的規律、妨害だけ、自己への作用、別人の別活動への妨害では満たさない。',
 'r5oe':'固定基準で同じ君主の同じ共同体に属する異なる二人の臣民と、被害側本人の同じ救済目的への同じ営み候補r5ocを結ぶ。加害や被害の現実の発生はまだ要求しない。',
 'r5of':'同じ固定基準のr5oeに属する全ての加害側・被害側・営み・救済目的について、同じ点にr5odの暴力的妨害活動がない。妨害されて実行不能な候補も残し、既に成功した営みだけを保護しない。',
 'r5og':'正確な君主・共同体の二対象列からr5ofの全対象への暴力的妨害の不在を返す。予防の目標であり、現実の脅威発生や臣民の救済成功は要求しない。',
 'r5oh':'同じ共同体の君主が参加する生起活動が、同じr5ogの目標を目指し、その成立又は維持に因果的に寄与し、実際に同じr5ogが成立する。脅威が既に発生したことや君主の単独執行は要求せず、単なる偶然の無妨害とは区別する。',
 'r5oi':'正確な君主・共同体の二対象列について、同じ点でr5ohの実効的な予防活動がある内容。所管と職責の要求に引用でき、義務から実際の履行を導かない。',
 'r5oj':'同じ君主が保持する同じ最高統治職に、同じr5oiの予防が公的所管h26hpとして属し、指定された規範源が同じ君主・職・内容・対象列・基準・点にその予防を正極性で要求する。職責の成立と実際の予防の成功を区別する。',
}
LIMITS=[
 'u0013第十一文後半wohl aber zu verhüten ... an der Bestimmung und Beförderung desselben nach allem seinen Vermögen zu arbeitenへの依存群。本人の救済目的を定め促進する全力の営み、他人による暴力的妨害、その予防と公的職責を構成する。前半との対照・限定・条件、規範源の固定、著者帰属と全文判断は未接続。',
 'Bestimmungは本人が自分の救済について何をどう進めるかを定めること、Beförderungは同じ救済の達成に向けた取り組みとして読む。arbeitenは同じ活動を両目標に向けて進めることで、完成した決定・客観的な正解・救済の成功を要求しない。複数段階から成る一つの取り組みを許し、二つの達成を同じ瞬間に要求しない。',
 'nach allem seinem Vermögenは本人の固定能力基準に相対的な最大の投入程度という明示読解。全能力種類の相互制約を含む総合的な質的程度を取り、使える力の全範囲、比較の整合性、実投入の一意性と最大性を分ける。医学的測定、エネルギーの特定単位、全員同じ最大能力、結果の成功を付け加えない。',
 '程度の尺度・比較と候補の完全な範囲は解釈入力である。比較不能や上限に到達する程度がない入力では全力という判定を補わず、有限モデルの最大値を現実の能力限界の証明にしない。暴力を受けたことで基準能力を下げ、妨害された営みを保護対象から消さない。',
 'gewaltthätigはAdelungの当該見出しに沿い、優越的な力の権限なき行使と読む。身体的な実力だけに狭めず、力の事実h26hvとその正当な根拠h26hxの不在を分ける。公的秩序のための正当な規律を自動的に防止対象とせず、君主や教会の自己申告だけで正当化もしない。hindernは因果的に機会・進行・実行余地を損なうこととし、完全阻止だけに限定しない。全力でなお取り組める被害者、既に全く実行を阻まれた被害者の双方を扱い、妨害判定で引用された営みを実行しない。',
 'einer den andernは同じ君主の臣民の異なる二人として読み、全ての該当する組と候補へ予防を向ける。人々の存在、実際の加害、既に必要と信じた営みだけへの限定を補わない。同じ救済は被害側本人のものとして固定する。',
 '予防は君主が参加する活動・同じ目標・その成立又は維持への寄与・実際の無妨害を結ぶ。まだ脅威が発生していなくても維持への寄与を認める。所管と要求にこの内容を引用する際には実行せず、職責から現実の無妨害や本人の救済達成を導かない。',
 '本文106主張、既存の意味判断、旧構成・固定証拠を変更しない。後続の全文統合では前半の宗教的所管外と、妨害防止に関する積極的所管を同じ君主に接続する必要がある。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    text=''
    for name,body in (('r5n3','t[s[k h246e[v goal v reference]]][v point]'),('r5n4','k h26hq[v person v goal v reference v point]')):
        text+='d '+name+'[bindings j[a] reference d] e[b point['+bind(('person','goal'),both('k r5nj[v person v goal v reference]',body))+']].\n'
    aims=lambda target:'k h26hf[v person v work r b[p '+target+'] '+PG+' v reference v point]'
    fields='person a work a goal a reference d point d';args='v person v work v goal v reference v point'
    text+='d r5n5['+fields+'] c['+both('k r5nj[v person v goal v reference]','k dg[v work v point]','k df[v person v work v point]',aims('r5n4'),aims('r5n3'))+'].\n'
    scope=lambda n:'k h26hr[v person v goal v reference v '+n+']'
    cmp=lambda l,r:'k h26hs[v person v goal v reference v '+l+' v '+r+']'
    regular=both('g level a['+scope('level')+']','f level a[y['+scope('level')+']['+cmp('level','level')+']]',
        'f left a[f right a[y['+both(scope('left'),scope('right'))+'][x['+cmp('left','right')+']['+cmp('right','left')+']]]]',
        'f left a[f middle a[f right a[y['+both(scope('left'),scope('middle'),scope('right'),cmp('left','middle'),cmp('middle','right'))+']['+cmp('left','right')+']]]]')
    text+='d r5n6[person a goal a reference d] c['+regular+'].\n'
    measured='i[at d level a][k h26ht[v person v work v goal v reference v at v level]]'
    unique='k r2cl['+measured+' i[level a]['+scope('level')+'] v point v level]'
    text+='d r5n7['+fields+'] c['+both('k r5n6[v person v goal v reference]',
        'g level a['+both(unique,'f other a[y['+scope('other')+']['+cmp('level','other')+']]')+']')+'].\n'
    text+='d r5oa['+fields+'] c['+both('k r5n5['+args+']','k r5n7['+args+']')+'].\n'
    text+='d r5ob[bindings j[a] reference d] e[b point['+bind(('person','work','goal'),'k r5oa['+args+']')+']].\n'
    candidates=['k h26hu[v person v work r b[p '+n+'] '+PG+' v reference]' for n in ('r5n4','r5n3')]
    text+='d r5oc[person a work a goal a reference d] c['+both('k r5nj[v person v goal v reference]',*candidates)+'].\n'
    harmfields='agent a victim a work a goal a intrusion a reference d point d'
    harmargs='v agent v victim v work v goal v intrusion v reference v point'
    harm=both('k aa[v agent]','k aa[v victim]','u[e[v agent][v victim]]','k dg[v intrusion v point]','k df[v agent v intrusion v point]',
        'k h26hv[v intrusion v victim v point]','u[k h26hx[v intrusion v victim v reference v point]]',
        'k h26hw[v intrusion v victim r b[p r5ob] l[a][v victim v work v goal] v reference v point]')
    text+='d r5od['+harmfields+'] c['+harm+'].\n'
    casefields='actor a community a agent a victim a work a goal a reference d'
    caseargs='v actor v community v agent v victim v work v goal v reference'
    text+='d r5oe['+casefields+'] c['+both('u[e[v agent][v victim]]','k r5ni[v actor v agent v community v reference]',
        'k r5ni[v actor v victim v community v reference]','k r5oc[v victim v work v goal v reference]')+'].\n'
    allcases='y[k r5oe['+caseargs+']][u[g intrusion a[k r5od['+harmargs+']]]]'
    for n in reversed(('agent','victim','work','goal')):allcases='f '+n+' a['+allcases+']'
    text+='d r5of[actor a community a reference d] e[b point['+allcases+']].\n'
    text+='d r5og[bindings j[a] reference d] e[b point['+bind(('actor','community'),'t[k r5of[v actor v community v reference]][v point]')+']].\n'
    prevention=both('k r2uj[v actor v community v point]','k dg[v activity v point]','k df[v actor v activity v point]',
        'k h26hf[v actor v activity r b[p r5og] '+TWO+' v reference v point]',
        'k h26hh[v activity r b[p r5og] '+TWO+' v reference v point]','t[k r5og['+TWO+' v reference]][v point]')
    text+='d r5oh[actor a community a activity a reference d point d] c['+prevention+'].\n'
    text+='d r5oi[bindings j[a] reference d] e[b point['+bind(('actor','community'),'g activity a[k r5oh[v actor v community v activity v reference v point]]')+']].\n'
    duty=both('k h234f[v office v community v point]','k r2ui[v actor v office v community v point]',
        'k h26hp[v office v community r b[p r5oi] '+TWO+' v reference v point]',
        'k h237z[v source v actor v office r b[p r5oi] '+TWO+' v reference '+TRUE+' v point]')
    text+='d r5oj[source a actor a community a reference d point d] c['+both('k r2uj[v actor v community v point]','g office a['+duty+']')+'].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5nj','r5ni','h246e','h26hp','h237z'],['h26hf','h26hh','dg','df'],['r2cl'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='full_capacity_salvation_work_violent_hindrance_and_preventive_duty',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
