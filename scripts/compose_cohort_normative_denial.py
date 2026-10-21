"""Compose universal denial of entitlement to the prospective cohort covenant."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_protected_remarks import bind
from scripts.compose_cohort_covenant_purpose import NAMES,FIELDS,ARGS,SIX,REF

PARENTS=('data/covenant-nullity-basis-v1.json','data/cohort-covenant-purpose-basis-v1.json')
LIBRARY='examples/v016/cohort-normative-denial.noema'
BASIS='data/cohort-normative-denial-basis-v1.json'
PRIMITIVES={
 'h26aw':('[a d] c',['agreement','reference'],'固定した基準の下で検討する、複数者が条項を相互に引き受ける制度的合意案の全範囲に属する。実際に形成済みの合意、許可されたもの、目的を達成できるものだけへ限定しない。制度的に検討する対象の種類を指定し、当事者の表明・宣誓・条項の割当・成立・効力・目的採用はこの関係では断言しない。'),
 'h26ax':('[] a',[],'第四文の時代をまたぐ合意形成の正当な資格を、人間の啓蒙・進展という観点から評価する規範の出所。先行時代自身の取り決め、特定国の現行法、君主や合意当事者の事実上の承認に置換しない。どの内容を許可・要求するかは既存h7k/h7lで別に与える。後続文の人間本性からの理由付け自体をこの参照の名前だけで記述済みにはしない。'),
 'h26ay':('[] a',[],'同じ時代の人々が、後続時代に関わる相互拘束の合意を形成する側としての立場。聖職者個人の説教職、特定の教会団体や国家の職制ではない。この立場の指定から正当な権限・代表資格・全員の実際の参加は導かない。'),
}
MEANINGS={
 'r5dc':'同じ固定基準で、合意がh26awの検討対象であり、前後の時代・全生存集団がr5bxを満たし、合意基準が先行時代内にあり、同じ状態の条件項目h26alが非空である候補。実際の当事者・形成・目的採用・状態成立・進展不能・原因性は候補選別に用いない。',
 'r5dd':'同じ評価規範・先行集団・立場について、r5dbの目的付き相互宣誓形成と同じ正確な六個体列への正極性の積極的許可があり、負極性への要求と衝突しないrduを結ぶ。形成内容や目的の成功を評価しない。',
 'r5de':'全ての六対象について、r5dcの候補でr5ddの正当な資格がある例の存在を否定する内容。未形成の候補も対象とし、一つの不適格例だけで全体を否認しない。候補不存在の場合には一般的な否認は真だが、候補・契約の実在や禁止要求そのものを追加しない。',
 'r5df':'正確な六個体列からr5dcの候補範囲を返す内容族。全文の量化範囲や補足表現と同じ対象を参照するために用いる。',
 'r5dg':'同じ六個体列から、第四文の規範の出所h26ax・立場h26ayを固定したr5ddの資格内容を返す。本文の量化範囲の中での肯定対象であり、その成立自体を主張しない。',
 'r5dh':'第四文の規範の出所と立場を固定したr5deの普遍的な資格否認。kann nichtをここでは正当な資格の不在として読む。同じ合意を物理的に形成できないこと、同じ結果がどの経過にも起こらないこと、全対象への禁止要求とは区別する。',
}
LIMITS=[
 'Ein Zeitalterは任意の先行時代の人々という一般的な対象と読み、後続集団は同じ区分の直後の時代を指す。六対象を全て量化し、特定の一世代・一契約の例だけへ限定しない。評価状況の全履歴と固定した時代区分はr5bxの意味規約に従う。',
 'kann nichtは、同じ目的付き相互宣誓形成への衝突のない積極的許可がある例はない、という規範的な資格否認として読む。先のberechtigtへの回答、直前の契約無効性、直後のVerbrechenと子孫による拒否の説明に照らした明示的な読解であり、物理的な不可能性や全対象への禁止要求を語形だけから追加しない。',
 '候補範囲には、前後時代・集団の構成、同じ先行時代内の合意基準、検討する合意案と非空の状態項目を用いる。署名、当事者の資格、形成、目的採用・実現、状態の真偽を先に確認してから量化する構成ではない。全範囲の入力を結論に応じて狭めない。',
 '否認はrduの否定であり、許可がない場合にも、許可があっても反対要求と衝突する場合にも成立する。未知の許可・要求を否定へ補わない。空範囲で真になる一般命題から、該当例の実在や具体的な契約形成を導かない。',
 'h26axの出所はこの読解の固定した評価観点である。後続文の人間本性・使命・子孫の権利からの理由付けは別の内容として後に記述し、この参照一つで説明済みとはしない。',
 '共謀的な否定的提示、括弧内の重要性、überhauptの総括、著者帰属と一文全体の通読は残る。本文99主張と確認済み文字数は変えない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def definitions():
    scope=both('k h26aw[v agreement '+REF+']',
        'k r5bx[v firstgroup v nextgroup v earlier v later '+REF+' v point]',
        'k h26ab[v earlier '+REF+' v point k h254z[v agreement]]',
        'g aspect a[k h26al[v condition v aspect '+REF+']]')
    text='d r5dc['+FIELDS+' point d] c['+scope+'].\n'
    valid='i[items j[a]][e[v items]['+SIX+']]'
    text+='d r5dd[assessor a '+FIELDS+' role a point d] c[k rdu[v assessor v firstgroup v role r[p r5db] '+SIX+' '+TRUE+' v point '+valid+' p h7k p h7l]].\n'
    candidate=both('k r5dc['+ARGS+' v point]','k r5dd[v assessor '+ARGS+' v role v point]')
    for n in reversed(NAMES):candidate='g '+n+' a['+candidate+']'
    text+='d r5de[assessor a role a] e[b point[u['+candidate+']]].\n'
    for name,body in (('r5df','k r5dc['+ARGS+' v point]'),('r5dg','k r5dd[k h26ax[] '+ARGS+' k h26ay[] v point]')):
        text+='d '+name+'[bindings j[a]] e[b point['+bind(NAMES,body)+']].\n'
    text+='d r5dh[] e[k r5de[k h26ax[] k h26ay[]]].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['rdu','h7k','h7l'],['r5db','r5bx','h26al','h26av'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='universal_normative_denial_of_cohort_covenant_entitlement',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
