"""Compose non-substitutable standing and its practical observance in government dealings."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/government-principle-profile-basis-v1.json';MAIN='data/civic-spirit-sentence-basis-v1.json';PEOPLE='data/civic-human-agency-basis-v1.json'
LIBRARY='examples/v016/dignity-conforming-treatment.noema';BASIS='data/dignity-conforming-treatment-basis-v1.json'
CODE='i[h[j[a]] e]';FIELDS='government a community a reference d';ARGS='v government v community v reference'
PRIMITIVES={
 'h27dg':('[a d] c',['object','reference'],'指定対象が、同じ固定した規範的評価の基準において、肯定的な価値を持つ。価格の数値、現在の有用性、誰かの好み、実際の政府の評価とは区別する。価値の存在を与える一般入力で、代替可能性・人間性・行為の適合性は合成側で別に確認する。'),
 'h27dh':('[a a d] c',['object','replacement','reference'],'同じ価値基準で、第一対象に固有に向けられるべき配慮を放棄しても、第二対象を得ることで価値上の等価な置換となる。単に二人を等しく尊重すること、職員の交代、財産の売買、補助具の使用とは異なる。価値の担い手に向ける配慮そのものの代替関係であり、適当な候補だけの有限列へ比較を縮めない。'),
 'h27di':('[a a d] c',['activity','object','point'],'この活動が同じ点で、指定対象への実際の取扱い・処遇となる。単なる対象への言及、無関係な同時の活動、別対象への扱いからは成立しない。活動の生起と政府の公的行為であることはr5zkで別に確認する。'),
 'h27dj':('[a a d d] c',['activity','object','reference','point'],'同じ活動・対象・価値基準・点について、価値が行為の選択と実施にどう反映されたかを評価する情報が整っている。配慮の有無・等価置換による正当化の有無を未知から補わず、適合そのものは含めない。'),
 'h27dk':('[a a d d] c',['activity','object','reference','point'],'この活動の選択と実施において、指定対象の同じ基準での価値が、他の目的を達成する手段であることとは独立の拘束理由として現に扱われる。口先で価値に言及するだけ、好意だけ、偶然対象に利益が生じるだけでは成立しない。対象を手段にも用いることは排除しない。'),
 'h27dl':('[a a a d d] c',['activity','object','replacement','reference','point'],'この活動の選択又は実施が、第一対象に固有に向けるべき配慮の放棄を、第二対象の取得等によって価値上等価に埋め合わせられるものとして扱う。同じ本人・価値基準への実際の実践的な置換であり、別活動の考えや単なる仮定の検討ではない。職務交代や通常の財産取引そのものを禁止にしない。'),
}
MEANINGS={
 'r6lg':'同じ人間が固定した規範的評価で肯定的な価値を持ち、他のどの対象も、その本人に固有の配慮を価値上等価に置換できない。現在の能力・政府の利益・政府の実際の承認を成立条件にしない。',
 'r6lh':'同じ民衆の本人を対象とする、この政府の実際の公的活動。r5zkによって同じ生起活動の同じ人間の行為者と公的資格を結び、私人の行為を政府の処遇へ流用しない。',
 'r6li':'同じ活動・対象・基準・点で評価が整い、その対象の価値を独立の拘束理由として実際に扱い、別対象による価値上の等価置換をその活動で行わない。単に価値があると思うことと、実際の扱いを区別する。',
 'r6lj':'同じ政府・共同体の本人にr6lgの地位があり、同じ点の全ての公的処遇r6lhがr6liを満たす。能力の成功者だけを処遇対象に選ばず、別活動の適合で不適合な活動を隠さない。',
 'r6lk':'同じ民衆の全人間成員を非空で完全に列挙し、同じ政府・基準・点で全員にr6ljの扱いを適用する。尊厳を政府自身の有益さへ還元しない。',
 'r6ll':'同じ政府・共同体・基準を固定し、外側の引数列が空の場合に限り、評価点ごとのr6lkを返す具体的な一般方針。未記述の基準名や任意の残余関数へ委ねない。',
 'r6lm':'同じ政府・共同体・基準の閉じた名前をr6llへ適用した、段階0の閉じた方針記述。作成しただけでは処遇の実行も規範的採用も要求しない。',
 'r6ln':'方針記述に渡す政府・共同体・基準の閉じた名前が、それぞれ同じ対象を指すことを確認する。',
 'r6lo':'同じ政府・立場・候補規則について、h27dcの具体的内容が、名前を照合した同じr6lmの方針記述そのものであることを要求する。同じ真偽表の別名で規範の対象を置換しない。',
 'r6lp':'r6loで具体的な内容を固定した同じ規則を、r6k4で同じ政府が統治上の自己規律として採用する。採用と実際の履行は別である。',
 'r6lq':'同じ具体的方針の採用r6lpと、同じ評価点でのr6lkの履行を結ぶ。採用しただけ、好意や利益だけ、別人又は別活動への履行では成立しない。',
}
LIMITS=[
 'seiner Würde gemäß zu behandelnを、その人に肯定的かつ価値上代替できない地位があり、政府の公的処遇がその価値を独立の拘束理由として守り、別の利益等による等価な埋合せとして放棄しないことと読む。これはこの文への明示的な価値・行為の解釈であり、カント倫理学の全理論を証明するものではない。',
 '後年のGrundlegung AA IV 434–435の価格・内的価値・等価物による代替の区別を比較資料にする。1784年の唯一の語義へ自動的に遡及させず、後年の道徳性・普遍的立法・自律の体系全体をこの一文へ追加しない。',
 '肯定的価値と価値上の代替関係は公開した規範的評価の入力である。その妥当性を行動データや有限例から発見・証明したとはしない。代替否定は全ての別対象へ量化し、有限の価格候補の一覧や高い金銭価格へ縮めない。人々の等しい価値と、ある人への配慮を別人で置換することを区別する。',
 '同じ対象の価値を実際の行為選択・実施の拘束理由として扱うことを肯定的条件にする。相手を手段にも用いる行為を全て排除せず、単なる道具的な有用性に尽くされる扱いと区別する。本人の価値の承認を口で述べただけでは足りない。',
 '対象範囲は同じ民衆の全人間成員で、前回r6lcの能力がある者だけへ絞らない。尊厳の地位と能力を獲得する時期は別であり、政府の利益、職務上の実績、現在の判断の成功を価値の成立条件にしない。',
 '処遇の本体は同じ政府の人間の行為者が公的資格で担う実際の活動全てを扱う。その点に処遇の実例がない場合、一般方針の行為部分は条件的に充足し得る。実例の存在・常時の交際・一回だけの歴史的出来事を追加しない。規則の採用、実際の機会における履行、政府の利益判断を分ける。',
 '今回の具体的方針には固定された価値上の地位と、公的処遇全ての実践的な非代替性・独立の配慮を記述する。公的発言の許可だけを尊厳全体と同一視せず、原文が列挙しない個別の権利や特定の法令を創作しない。',
 '同じ規則候補への接続では具体的Noema記述を完全一致させる。政府原則の内容比較で用いる範囲相対的な同値と、特定記述への規範を別名へ移すことは異なる。',
 '政府自身の非事実的な有益さの判断、原則への因果作用、endlich/auch/sogar、同じ政治的終点のnun、Wenn/so・著者注・全文帰属と通読判断は残る。今回の局所構成を全文意味確認へ加算しない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in (PARENT,MAIN,PEOPLE))

def definitions():
    person='k r6hd[v person v community v reference]'
    text='d r6lg[person a reference d] c['+both('k aa[v person]','k h27dg[v person v reference]',
      'f replacement a[y[u[e[v replacement][v person]]][u[k h27dh[v person v replacement v reference]]]]')+'].\n'
    text+='d r6lh['+FIELDS+' activity a person a point d] c['+both(person,'k r5zk[v activity v government v point]','k h27di[v activity v person v point]')+'].\n'
    text+='d r6li[activity a person a reference d point d] c['+both('k h27dj[v activity v person v reference v point]','k h27dk[v activity v person v reference v point]',
      'f replacement a[y[u[e[v replacement][v person]]][u[k h27dl[v activity v person v replacement v reference v point]]]]')+'].\n'
    text+='d r6lj['+FIELDS+' person a point d] c['+both(person,'k r5zj['+ARGS+']','k r6lg[v person v reference]',
      'f activity a[y[k r6lh['+ARGS+' v activity v person v point]][k r6li[v activity v person v reference v point]]]')+'].\n'
    text+='d r6lk['+FIELDS+' point d] c['+both('k rcm[k h27b5[v community v reference] i[person a]['+person+']]',
      'f person a[y['+person+'][k r6lj['+ARGS+' v person v point]]]')+'].\n'
    text+='d r6ll['+FIELDS+'] h[j[a]] e[i[bindings j[a]][b point['+both('e[d[v bindings]][n p a b]','k r6lk['+ARGS+' v point]')+']]].\n'
    text+='d r6lm[government i[a] community i[a] reference i[d]] '+CODE+'[o a[r[p r6ll]]['+ARGS+']].\n'
    names='k h223g[v government] k h223g[v community] k h223h[v reference]'
    text+='d r6ln['+FIELDS+'] c['+both(*['e[s[k '+('h223h' if n=='reference' else 'h223g')+'[v '+n+']]][v '+n+']' for n in ('government','community','reference')])+'].\n'
    text+='d r6lo['+FIELDS+' rule a] c['+both('k r6k3['+ARGS+']','k r6ln['+ARGS+']','k h27db['+ARGS+' v rule]',
      'e[k h27dc['+ARGS+' v rule]][k r6lm['+names+']]')+'].\n'
    text+='d r6lp['+FIELDS+' rule a point d] c['+both('k r6lo['+ARGS+' v rule]','k r6k4['+ARGS+' v rule v point]')+'].\n'
    text+='d r6lq['+FIELDS+' rule a point d] c['+both('k r6lp['+ARGS+' v rule v point]','k r6lk['+ARGS+' v point]')+'].\n'
    return text

def build():
    p,m,a=parents();doc=deepcopy(p.document);doc.update(declarations=[],statements=[]);imports={};paths=set()
    for c,roots in ((p,('r6k3','r6k4','h27dc')),(m,('r5zk','r6hd','h223g','h223h')),(a,('h27b5',))):
        paths.update(c.source_sha256)
        for d in closure(c.document,roots):
            n=d['name'];e=c.entries[n]
            if n in imports:assert d==imports[n]['declaration'] and e['meaning_ja']==imports[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imports[n]=e
    # rcm is deliberately taken from the same canonical manuscript.
    for d in closure(m.document,('rcm',)):
        if d['name'] not in imports:doc['declarations'].append(d);imports[d['name']]=m.entries[d['name']]
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(c.entries for c in parents()))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imports.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='concrete_non_substitutable_standing_and_public_treatment_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imports.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imports.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
