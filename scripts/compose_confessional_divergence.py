"""Compare offered views with the same issue in an adopted confession."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_protected_remarks import bind

PARENTS=('data/offered-judgments-basis-v1.json','data/prince-sentence-basis-v1.json')
LIBRARY='examples/v016/confessional-divergence.noema'
BASIS='data/confessional-divergence-basis-v1.json'
PROFILE='i[h[j[a]] e]';TARGET='i b[h[j[a] d] e]'
NAMES=('person','activity','scholar','audience','church','creed','subject')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
PRIMITIVES={
 'h26o3':('[a a d] c',['item','issue','reference'],
   'この固定基準の代表内容項目は、指定論点の比較単位として、その論点についての立場・区別・条件を表す。単に同じ話題に触れることとは区別し、比較と無関係な別論点の追加だけで差を作らない粒度に固定する。肯否・量化・条件・時間・様相・引用作用域を保持し、肯定連言の分割は許せるが否定や引用等の内外を無断に分割しない。異なる見解、未採用又は誤った内容も同じ論点に属し得る。命題内容はh26aeへ明示し、所属だけで相違・真理・支持を認定しない。'),
}
MEANINGS={
 'r53x':'同じ信条の定式化自身又は肯定的に含む部分について、同じ論点の代表内容項目をhzlhで帰属する。部分の閉じたNoema内容h246eと同じ代表項目のr5ccの記述が、同じ定式化の内容を保つh254wを要求する。別内容の部分や単なる言及を比較相手にしない。',
 'r53y':'同じ項目・論点・固定基準を受け、正確な一要素の論点列について、代表内容r5ccを返す比較用の内容関数。他の束縛列では偽とし、比較対象の論点をずらさない。',
 'r53z':'同じ項目・論点・固定基準の閉じた名前記述をr53yへ引用適用し、比較用の閉じた段階0の内容関数記述を構成する。名前の値の一致は呼出し側r532で確認する。',
 'r532':'同じ教会が採用した同じ信条r35rの同じ論点の内容r53xと、同じ論点の自分側の代表内容を、固定した非空の比較範囲でrpbにより比べる。少なくとも一候補で真偽が異なるという内容差を要求し、現在の真理、単なる綴りの差、教示規則への不適合や両立不能そのものへ置き換えない。',
 'r533':'二つの発表項目列の和の少なくとも一項目について、同じ信条の同じ論点・部分・対応項目を選んでr532の差がある。比較候補は同じ代表項目を引数とする固定関数から受け、別項目の差を発表対象へ流用しない。全項目の相違や、別項目での一致は要求しない。',
 'r534':'同じ本人・一つの発表活動・学識者・公衆と同じ二項目列の実際の発表r53uに、その同じ項目列の採用信条からの部分的な相違r533を結ぶ。本人の保持判断・洞察と審査目的を保持し、相違だけで発表や真理を推論しない。',
 'r535':'二項目列と比較関数を固定し、本人・活動・学識者・公衆・教会・信条・宗教主題の正確な七個体列からr534の実行内容を作る。規範対象の外で実際の発表や信条の真理を要求しない。',
 'r536':'同じ二項目列と比較関数の閉じた記述をr535へ引用適用した段階1の実行記述。別の項目列・信条・比較範囲へ置き換えず、後の自由と職務義務の保持が同じ発表を受けるための対象。',
}
LIMITS=[
 'u0015第二文のihre vom angenommenen Symbol hier oder da abweichenden Urtheile und Einsichtenを、発表する見解群の少なくとも一論点で、採用信条の同じ論点に属する内容と差があるという明示した読みで接続する。全文の意味判断はまだ行わない。',
 'hier oder daを、固定した割合や厳密な少数、別の全論点での一致、全信条の否認とはしない。単なる構文の相違でなく、同じ論点の内容を明示した全関連比較候補で比較し、一つ以上の違いを要求する。比較の全域性・粒度は意味解釈の責任で、有限標本から保証しない。',
 'Symbolはr35rの共同の宗教的信条として採用された定式化を受ける。教示の規則に沿わないことと、教義内容が異なることを分け、h246i/jの教示基準を内容の代用にしない。信条が客観的に真又は偽だという著者の主張は追加しない。',
 'h252fの肯定的な構成部分、hzlhの論点別内容帰属、h254wの同じ内容保持を再利用する。新しい基本関係h26o3は認識項目と比較論点の一般的な結合だけを表し、相違の真偽を返す一文専用記号ではない。実際の内容はh246eとh26aeのNoema記述で保持する。',
 '同じ話題に属する二命題を無差別に比較しない。各項目を同じ論点の比較単位に固定し、無関係な別論点の追加だけで差を作らない。任意の帰結、否定の内側、他人の引用を信条が肯定する部分へ昇格させない。',
 '自分側の内容の保持と根拠は同じr53uの実行内で確認する。本人の判断が誤り得ることを保持し、別時点での放棄した見解や他人の見解の差を借りない。信条と発表内容の双方が現在真でも、指定比較候補に差があれば相違は成立し得る。',
 '比較が二命題の両立不能を要求するわけではなく、既存rpbの内容差という読みである。一つの発表候補の有限列は全発表候補の列挙ではない。後の全称量化で未実行・不許可の候補も含む範囲を保持する。',
 '未接続なのは同じ限定君主の下という照応、聖職者と敬意評価、職務義務を保つ自由、無制約の他者、noch mehrの提示と全文帰属。正本113主張・登録簿v197・17全単位判断と追加第一文490文字は保持する。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def named(name):return 'k '+('h223h' if name=='reference' else 'h223g')+'[v '+name+']'
def valid(names):return ['e[s['+named(n)+']][v '+n+']' for n in names]
def item_code(name):return 'o a[r[p r5cc]]['+named(name)+' '+named('reference')+']'
def profile(name):return 'k r53z['+named(name)+' '+named('issue')+' '+named('reference')+']'

def definitions():
    canon='k h26ag[v standarditem v reference]'
    text='d r53x[creed a part a standarditem a issue a reference d] c['+both(*valid(('standarditem','reference')),
        'k h26ad[v standarditem v reference]','k h26o3['+canon+' v issue v reference]',
        'x[e[v part][v creed]][k h252f[v creed v part v reference]]',
        'k hzlh[v part v issue '+canon+' v reference]',
        'k h254w[v part k h246e[v part v reference] '+item_code('standarditem')+' v reference]')+'].\n'
    text+='d r53y[item a issue a reference d] h[j[a]] e[i[bindings j[a]][b point['+both(
        'e[v bindings][l[a][v issue]]','t[k r5cc[v item v reference]][v point]')+']]].\n'
    text+='d r53z[item i[a] issue i[a] reference i[d]] '+PROFILE+'[o a[r[p r53y]][v item v issue v reference]].\n'
    fields='church a creed a subject a item a issue a part a standarditem a reference d cases h[d] c'
    text+='d r532['+fields+'] c['+both(*valid(('item','issue','reference')),
        'k r35r[v church v creed v subject v reference]','k h26ad[v item v reference]',
        'k h26o3[k h26ag[v item v reference] v issue v reference]',
        'k r53x[v creed v part v standarditem v issue v reference]',
        'k rpb['+profile('item')+' '+profile('standarditem')+' l[a][v issue] v cases]')+'].\n'
    compare='k r532[v church v creed v subject v item v issue v part v standarditem v reference i[point d][c[v comparisons][k h26ag[v item v reference] v point]]]'
    for n in reversed(('issue','part','standarditem')):compare='g '+n+' a['+compare+']'
    text+='d r533[church a creed a subject a judgments j[a] insights j[a] reference d comparisons h[a d] c] c[q[m[v judgments][v insights]][u['+TRUE+']][i[found c item a][x[v found]['+compare+']]]].\n'
    fields=FIELDS+' judgments j[a] insights j[a] reference d comparisons h[a d] c point d'
    args=ARGS+' v judgments v insights v reference v comparisons v point'
    text+='d r534['+fields+'] c['+both('k r53u[v person v activity v scholar v audience v judgments v insights v reference v point]',
        'k r533[v church v creed v subject v judgments v insights v reference v comparisons]')+'].\n'
    text+='d r535[judgments j[a] insights j[a] comparisons h[a d] c bindings j[a] reference d] e[b point['+bind(NAMES,'k r534['+args+']')+']].\n'
    template='r b[i[judgments j[a] insights j[a] comparisons h[a d] c][i[bindings j[a] reference d][k r535[v judgments v insights v comparisons v bindings v reference]]]]'
    text+='d r536[judgments i[j[a]] insights i[j[a]] comparisons i[h[a d] c]] '+TARGET+'[o a['+template+'][v judgments v insights v comparisons]].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    roots=(['r53u','r5cc','h26ad','h26ag','h223g','h223h'],['r35r','h252f','hzlh','h254w','rpb'])
    for c,selected in zip(sources,roots):
        for d in closure(c.document,selected):
            n=d['name'];e=c.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&set().union(*(set(c.entries) for c in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(c.source_sha256) for c in sources))
    basis=dict(status='same_issue_adopted_confession_and_offered_divergence_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
