"""Bind causal purposes and individual terms to the same cohort covenant oath."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENTS=('data/covenant-nullity-basis-v1.json','data/necessary-cohort-state-basis-v1.json','data/epoch-undertakings-basis-v1.json')
LIBRARY='examples/v016/cohort-covenant-purpose.noema'
BASIS='data/cohort-covenant-purpose-basis-v1.json'
CODE='i[h[j[a] d] e]'
TERMS='i[h[j[a]] e]'
NAMES=('firstgroup','nextgroup','earlier','later','agreement','condition')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
SIX='l[a]['+ARGS+']'
SEVEN='l[a][v person '+ARGS+']'
REF='k h26av[]'
PRIMITIVES={
 'h26as':('[a '+CODE+' j[a] d d] c',['agreement','result','bindings','reference','candidate'],'同じ合意の実施・維持が、閉じた結果関数と同じ対象列・固定基準で指定される結果を、この候補経過で成立させる因果的な働きをしている。結果の単なる併存・目的の採用・引用だけでは足りない。合意自身の正当性、唯一原因性、当事者全員の直接の実行、結果が以前は偽だったことは含意しない。結果内容の実際の成立は合成側で別に要求する。'),
 'h26at':('[a a a '+CODE+' j[a] d d] c',['person','activity','agreement','goal','bindings','reference','point'],'本人がこの同じ引受け行為・表明点において、同じ合意の共同目的として、指定の閉じた内容関数と順序付き対象列・固定基準の内容を相手方に表明して採用する。一般公衆への公開は要求しない。別の行為や合意における賛同、私的な欲求、全員の内心の一致で代用しない。目的の実現・実現可能性・履行・正当性は含意しない。'),
 'h26au':('[a a '+CODE+' j[a] d d] c',['person','agreement','goal','bindings','reference','candidate'],'この候補経過で本人が、同じ合意の実施に自分の行動をもって参加し、指定の閉じた目的関数・対象列・固定基準の内容の実現へ向けて役割を果たしている。形成時の発言だけ、無関係な活動、単に結果が成立したことでは足りない。個々人の具体的な役割分担や全員による同一行為は指定せず、本人の参加と共同目的の成功を区別する。'),
 'h26av':('[] d',[],'第六段落第四文の全時代・前後集団・合意と、認識・訂正・啓蒙の進展を解釈する固定基準。先の教会団体の種類だけへ対象を限定せず、各合意の形成基準h254z、真偽評価h26ar、著者の提示文脈と役割を区別する。'),
}
MEANINGS={
 'r5c4':'同じ六対象・固定基準・候補経過について、同じ合意の実施がr5c3の結果を生じさせるh26asと、その同じ対象への実際の結果r5c2を結ぶ。別の合意の原因性や結果の偶然の併存を成功へ替えない。',
 'r5c5':'正確な六個体列と固定基準からr5c4の因果的な達成内容を返す。同じ状態を引数として保持し、目的の採用時にはこの達成内容を実行しない。',
 'r5c6':'本人を先頭にした正確な七個体列（本人と六対象）から、固定基準h26avの下で同じ合意の同じr5c5目的に向けて本人が実施に参加するh26auの内容を返す。個人別の引受け条項として使用し、共同目的の成功を本人の現在の事実へしない。',
 'r5c7':'条項記述がr5c6、引数が本人と同じ六対象に等しいことを確認し、先行時代の同じ相互宣誓r5caへ、同じ行為・本人による同じ合意・r5c5・六対象・固定基準への共同目的採用h26atを結ぶ。誓約と目的を別行為で満たすことを許さない。',
 'r5da':'同じ六対象と固定基準について、r5bzの時代・当事者の枠組みと、rhzの同じ合意形成を結ぶ。条項r5c6と本人を先頭にした七個体列を固定し、全当事者の同じ相互宣誓をr5c7で共同目的へ結ぶ。二人以上の実際の当事者を要求するが、時代の全員の署名・後代の同意・目的達成・法的権限は要求しない。',
 'r5db':'正確な六個体列からr5daの目的付き相互宣誓形成の内容を返す。規範的な許否や著者の主張の対象として引用できるが、この引用によって形成・成功・正当性を事実としない。',
}
LIMITS=[
 'zu setzenは同じ合意の実施が後続集団を同じ状態へ置くという因果的な目的として読む。状態の達成はr5c2/r5c3、同じ合意による原因性はh26as、両者を含む目的内容はr5c4/r5c5に分ける。',
 'sich verbünden und darauf verschwörenは、全実際当事者が個人別条項を相互に引き受け、同じ引受け行為で同じ共同目的を採用し宣誓する構成として読む。条項は同じ目的へ向けた本人の実施参加であり、本人一人による必ず成功する保証や、実現不能でも既に履行済みという内容にはしない。',
 '合意形成の発言と、将来の本人の実施参加と、共同目的の成功は別。引用された条項・目的内容を形成時に実行しない。当事者間での目的の採用は、一般公衆への公開や私的な誠実さ・信念の一致を要求しない。',
 '当事者はh26acの全範囲を保持する。先行時代の全人類を一個の制度的団体としたり、全員の署名・同一の役割・法的な代表権を足したりしない。実施は機関や委任された人を介してもよく、署名者全員の直接因果を要求しない。',
 'h26avは第四文の固定基準であり、先の教会団体だけを対象にする参照へ縮めない。状態の具体的な構成・全比較候補・方法や結果の完全性の解釈入力に関する前版の限界は保持する。',
 '規範的なkann nichtの否認、共謀的な否定的提示、括弧内の重要性、überhauptの総括、著者帰属と一文全体の通読は残る。本文99主張と既存の確認済み文字数は変えない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def definitions():
    pair='v firstgroup v nextgroup v earlier v later v agreement'
    text='d r5c4['+FIELDS+' reference d candidate d] c['+both(
        'k h26as[v agreement r[p r5c3] '+SIX+' v reference v candidate]',
        'k r5c2['+ARGS+' v reference k h26ar[v reference] v candidate]')+'].\n'
    text+='d r5c5[bindings j[a] reference d] e[b candidate['+bind(NAMES,'k r5c4['+ARGS+' v reference v candidate]')+']].\n'
    text+='d r5c6[bindings j[a]] e[b candidate['+bind(('person',*NAMES),
        'k h26au[v person v agreement r[p r5c5] '+SIX+' '+REF+' v candidate]')+']].\n'
    text+='d r5c7['+FIELDS+' candidate d person a activity a terms '+TERMS+' bindings j[a] point d] c['+both(
        'e[v terms][r[p r5c6]]','e[v bindings]['+SEVEN+']',
        'k r5ca[v earlier '+REF+' v candidate v person v activity v agreement v terms v bindings v point]',
        'k h26at[v person v activity v agreement r[p r5c5] '+SIX+' '+REF+' v point]')+'].\n'
    declares='i[person a activity a pact a terms '+TERMS+' bindings j[a] point d]['+both('e[v pact][v agreement]',
        'k r5c7['+ARGS+' v candidate v person v activity v terms v bindings v point]')+']'
    formation='k rhz[v agreement r[p r5c6] k h254z[v agreement] i[person a anchor d][k h26ac[v agreement v person v anchor]] '+(
        'i[person a]['+SEVEN+'] p aa i[at d][k h257z['+REF+' v candidate v at]] i[first d last d][k ic[v first v last v candidate]] p h255a p dg p f3 '+declares+']')
    text+='d r5da['+FIELDS+' candidate d] c['+both('k r5bz['+pair+' '+REF+' v candidate]',formation)+'].\n'
    text+='d r5db[bindings j[a]] e[b candidate['+bind(NAMES,'k r5da['+ARGS+' v candidate]')+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,([],['r5c2','r5c3','h26ar'],['r5bz','r5ca','rhz','h255a','dg','f3'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='same_cohort_covenant_causal_purpose_terms_and_mutual_oath',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
