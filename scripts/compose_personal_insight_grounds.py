"""Bind a held comparative epistemic view to the very same act of assent."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_protected_remarks import bind
from scripts.compose_congregational_choices import FRAME,FRAME_ARGS,CONTEXT,CONTEXT_ARGS

PARENTS=('data/legislative-touchstone-basis-v1.json','data/congregational-choices-basis-v1.json','data/public-insight-basis-v1.json')
LIBRARY='examples/v016/personal-insight-grounds.noema'
BASIS='data/personal-insight-grounds-basis-v1.json'
FAMILY='i[h[j[a] d] e]'
NAMES=('newer','field','standard','baseline','preferred')
APPRAISAL='newer a field a standard a baseline a preferred a reference d point d'
APPRAISAL_ARGS='v newer v field v standard v baseline v preferred v reference v point'
ASSENT='person a activity a judgment a agreement a '+FRAME+' newer a standard a baseline a preferred a '+CONTEXT+' point d'
ASSENT_ARGS='v person v activity v judgment v agreement '+FRAME_ARGS+' v newer v standard v baseline v preferred '+CONTEXT_ARGS+' v point'
PRIMITIVES={
 'h26dn':('[a a a a d d] c',['standard','field','left','right','reference','assessment'],'同じ固定基準の同じ領域に関する二つの代表認識内容を、その事柄の区別・関係・根拠をより適切に捉えるという同じ認識上の評価基準で比べ、左が右に少なくとも劣らないと評価される。人気・利益・制度の権威だけの序列とは区別する。内容はh26aeで別にNoemaとして与え、別名を変えて比較を変えない。把握や説明・根拠の質を項目数や論理的情報量だけへ還元せず、厳密な優越・本人の採用・評価の真理は別に結ぶ。'),
 'h26do':('[a a a a d d] c',['person','standard','baseline','field','reference','point'],'同じ人がこの点で、この領域のより適切な認識を判断するために、指定の評価基準と代表比較元の内容を、自分が用いる基準として採用している。比較元は同じ議論・対象の文脈に固定し、優越が出るよう後から都合のよい劣った見解へ選び直さない。他人だけの基準、基準名への言及、基準を作った本人であることとは区別する。全員共通・唯一の正当な基準・客観的な優越は要求しない。'),
 'h26dp':('[a a a d d] c',['configuration','item','field','reference','assessment'],'同じ領域のこの制度配置が、この代表認識内容に示された事柄の理解に照らした実践上の帰結に適合する。単に同時に話題にすることや、無関係な見解への賛同ではない。認識内容はh26aeで明示し、実際の配置の運用・この理解の真理・全員の支持・他の理解への不適合を含意しない。'),
 'h26dq':('[a '+FAMILY+' j[a] d c d] c',['judgment','content','bindings','reference','polarity','point'],'この判断が、段階0の閉じた内容族に同じ順序付き対象列と固定基準を適用した内容を、この点で指定極性により認めている。h242dの判断の肯否を固定基準付きの内容族へ拡張する。保持する本人は別に結び、内容の真理・実施・客観的な根拠を実行評価しない。同じ真理値を持つ別内容への肯定を移送しない。'),
 'h26dr':('[a a a d d d] c',['person','activity','judgment','reference','candidate','point'],'この人が同じ候補履歴のこの点で、同じ判断を、この行為の選択・遂行を導く自分の理由として用いている。判断と行為の共存、他人の理由、事後だけの説明、別の行為への理由とは区別する。唯一の動機・十分原因・理由の客観的な妥当性・判断内容の真理を要求しない。'),
}
MEANINGS={
 'r5ga':'同じ固定認識範囲の比較元と候補をh26agで代表内容へそろえ、双方が同じ制度領域の事柄を扱うh26c5ことを要求する。同じ認識上の基準h26dnについて両自己比較と候補以上の比較、逆比較の不成立を結ぶ厳密な優越内容。項目数・名前だけや比較不能を改善にしない。',
 'r5gb':'新配置・領域・基準・比較元認識・候補認識の正確な五対象列に、新配置が制度配置であること、候補認識のr5gaの厳密な優越、その同じ代表認識に新配置が適合するh26dpことを結ぶ内容族。旧配置が比較元認識に対応したことや新配置の実施は補わない。',
 'r5gc':'同じ人が同じ点で同じ判断を自分の見解として保持し、その本人が同じ領域・基準・代表比較元を採用し、その判断がr5gbの同じ五対象と固定基準の内容を肯定する。事前に形成した判断の保持を許し、現在の判断行為や客観的な認識優越は要求しない。',
 'r5gd':'同じ本人・合意・新配置へのr5f4の同意表明について、その同じ活動・時点にr5gcの保持判断があり、それを本人がその同意の理由h26drとして用いる。別の同意、後の理由づけ、他人の判断や基準を借りず、客観的な認識の真理や制度の実施へ強めない。',
 'r5ge':'同じ共同体の制度変更への合意r5f5を保ち、同じ固定当事者全員について、同意表明を既に行った同じ活動・点でr5gdの本人の認識判断が理由になっている。人ごとに異なる基準・比較元・候補認識・保持判断を許し、全員に同じ私的な認識や客観的な正しさを強制しない。',
}
LIMITS=[
 'u0013第七文のnach ihren Begriffen der besseren Einsichtを、共同体の当事者が自分の基準による、より適切な認識についての判断に従って制度変更へ同意したことと読む。比較基準・比較元・候補内容は本人に属し、同じ制度領域に固定する。唯一の文法解釈や哲学理論と主張しない。',
 '認識の候補内容が比較元より適切であり、新配置がその理解に適合する、という本人の判断内容を構成する。これを客観的な新制度の優越や実施済みに置き換えず、旧制度がある特定の旧理解から生じたという来歴も追加しない。比較元を成功に合わせて選ぶことは採用関係の意味規約で禁じる。',
 'h26dnは説明・根拠・区別・関係を捉える認識の適切さの比較であり、旧rlhの情報集合の増加とは異なる。具体的な比較基準と認識内容は入力で明示し、内容はh26aeのNoemaとして与える。根拠や説明の質の全哲学的理論をこの語彙関係だけで証明したとはしない。',
 'r5gc/r5gdでは本人の肯定内容を引用して保持する。公的洞察の実際のr5cl/r5ftとは区別し、本人の比較が誤っていても自分の判断に従うことは記述できる。保持h26aiを使い、同意と同時に新しい判断を行うfa条件を追加しない。',
 '同じ同意活動への理由使用を要求するが、唯一の動機・形式的証明・客観的な支持fd・十分な知識根拠h26ajを要求しない。これらを加えると、本人の考えに従ったという記述を正しい認識に基づく行為へ強めてしまう。',
 'r5geを改革側の肯定選択条件にし、維持側r5f7は独立に保つ。保護・非妨害の同じ内容への接続、洞察が共同提案に足りる条件、期間・談話・著者帰属と全文確認は残る。確認文字数は増やさない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    canonical=lambda n:'k h26ag[v '+n+' v reference]'
    def cmp(left,right):return 'k h26dn[v standard v field '+canonical(left)+' '+canonical(right)+' v reference v assessment]'
    scope=[s for n in ('baseline','preferred') for s in ('k h26ad[v '+n+' v reference]','k h26c5['+canonical(n)+' v field v reference]')]
    text='d r5ga[baseline a preferred a field a standard a reference d] e[b assessment['+both(*scope,
        cmp('baseline','baseline'),cmp('preferred','preferred'),cmp('preferred','baseline'),'u['+cmp('baseline','preferred')+']')+']].\n'
    target=both('k h246w[v newer v field v reference]',
        't[k r5ga[v baseline v preferred v field v standard v reference]][v assessment]',
        'k h26dp[v newer '+canonical('preferred')+' v field v reference v assessment]')
    text+='d r5gb[bindings j[a] reference d] e[b assessment['+bind(NAMES,target)+']].\n'
    bindings='l[a]['+' '.join('v '+n for n in NAMES)+']'
    text+='d r5gc[person a judgment a '+APPRAISAL+'] c['+both('k h26ai[v person v judgment v reference v point]',
        'k h26do[v person v standard '+canonical('baseline')+' v field v reference v point]',
        'k h26dq[v judgment r[p r5gb] '+bindings+' v reference '+TRUE+' v point]')+'].\n'
    text+='d r5gd['+ASSENT+'] c['+both('k r5f4[v person v activity v agreement '+FRAME_ARGS+' v newer '+CONTEXT_ARGS+' v point]',
        'k r5gc[v person v judgment '+APPRAISAL_ARGS+']',
        'k h26dr[v person v activity v judgment v reference v candidate v point]')+'].\n'
    grounded='k r5gd['+ASSENT_ARGS+']'
    for n,sort in reversed((('activity','a'),('point','d'),('judgment','a'),('standard','a'),('baseline','a'),('preferred','a'))):grounded='g '+n+' '+sort+'['+grounded+']'
    text+='d r5ge[agreement a '+FRAME+' older a newer a '+CONTEXT+'] c['+both(
        'k r5f5[v agreement '+FRAME_ARGS+' v older v newer '+CONTEXT_ARGS+']',
        'f person a[y[k h26dj[v agreement v person '+CONTEXT_ARGS+']]['+grounded+']]')+'].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['h26ai','h26ag','h26ad','h26ae','h246w'],['r5f4','r5f5','h26dj'],['h26c5'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='personal_epistemic_appraisal_grounding_same_assent',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
