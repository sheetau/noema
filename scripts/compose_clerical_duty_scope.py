"""Bind clerical public freedom to all requirements without a reified ledger."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_preserved_public_duties import CODE,RULE,NAMES,fields,args

PARENTS=('data/preserved-public-duties-basis-v1.json','data/prince-sentence-basis-v1.json')
LIBRARY='examples/v016/clerical-duty-scope.noema';BASIS='data/clerical-duty-scope-basis-v1.json'
BOUND=[('issuer','a'),('target',CODE),('binding','j[a]'),('reference','d'),('sign','c')]
BASE=[('person','a'),('office','a'),('anchor','d'),('required',RULE)]
PRIMITIVES={
 'h26o4':('[a '+CODE+' j[a] d d d] c',['person','target','bindings','reference','anchor','candidate'],
   '同じ本人・閉じた段階1目標・束縛列・内容基準について、基準点の制度的な事情の下で、その内容の実行と本人の職務要求を共に比較する全関連候補。対象の内容や要求が満たされた候補だけを選ばず、不実行・不履行・要求の変化がある場合も範囲に残す。要求の保持・履行・実行例の存在は合成側で検査する。対象は固定した制度的事情の下の規範的両立であり、身体的能力・因果的無害性・現実の将来到達・全論理的可能世界の範囲ではない。成功例や許可の有無を見て範囲を変更せず、完全な範囲の指定は明示した解釈入力である。'),
}
MEANINGS={
 'r54i':'同じ本人・職務について、基準点で存在する全出所・全段階1目標・全個体列・全内容基準・両極性の要求を、同じ組合せのまま比較点にも要求する。要求関係を直接量化し、一覧項目の供給や既知記述の列挙に依存しない。',
 'r54j':'r54iの非免除と、基準点の全要求の対象内容が同じ比較点で各要求極性に一致することを結ぶ。肯定・否定要求の双方、異なる束縛列・内容基準の要求を取りこぼさない。',
 'r54k':'非空の比較範囲で、指定内容を実行する全候補にr54iの非免除があり、同じ一候補で実行とr54jの全義務履行が共に成立する。網羅された一覧を使うr54fと同じ条件を、全要求の直接量化で表す。',
 'r54l':'指定した全職務範囲について、実行候補が少なくとも一つあり、全実行候補の同じ点で全職務それぞれのr54jが成立する。単一職務の無制約を全職務へ拡張し、職務要求が一つもない場合も許す。職務範囲を完全に供給することと自由の成立は別である。',
 'r54m':'同じ七対象・二項目列・比較関数で作る発表目標r536への自由r37cを、同じ本人の同じ職務の全要求を直接扱うr54kへ結ぶ。基準点の職務要求が少なくとも一つあることも要求し、自由の出所と義務の出所を同一化しない。',
 'r54n':'同じ本人・職務・教会を固定する聖職者r35m、その同じ教会の採用信条r35r、評価点での同じ職務への委任cfと教会への奉仕h246k、同じ本人の学識者の立場h247dを結ぶ。教示済み・生徒の存在・信条への内心の同意は追加しない。',
 'r54o':'r54nの同じ聖職者・職務・教会・信条・主題を、同じ公的発表r536へのr54mへ接続する。公的自由の規範源はh247b、比較範囲は同じ本人・目標・七対象・内容基準・評価点を渡すh26o4とする。実際の発表を許可の外側で要求しない。',
 'r54p':'r54lの職務範囲を、同じ本人が基準点で委ねられている全職務cfへ直接結ぶ。選択した一職務だけ、既知の職名一覧、成功候補だけの職務範囲を用いない。全職務の無制約条件であり、公的自由そのものは別に要求する。',
}
LIMITS=[
 'u0015第二文の同じ聖職者・職務・教会・採用信条に、既に構成した発表の自由と職務義務の非免除・共充足を接続する依存群。本文への帰属・全候補量化・敬意評価・君主照応・他者への拡張は未統合で、新たな意味確認文字数は加えない。',
 '全要求は既存h237zが扱う段階1目標、個体束縛列、内容基準、極性で直接量化する。義務を表す個体や参照関数をさらに基本記号として増やす必要はない。旧一覧方式r537/r54a–hと証拠は保存し、完全で実在する一覧の下での同値を式の展開で確認する。',
 '全義務とはこの明示した規範形式における全職務要求である。任意の引用段階に及ぶ全規範を横断する量化とはしない。原文が特定しない個別の教義・義務を捏造せず、教示方針r36e等も同じ型の対象として含められる。',
 '比較範囲h26o4は要求を満たす候補だけを先に選ばない。本文のunbeschadetを非免除と規範的な共充足として読み、因果的無害性や物理的な発表能力へ強めない。完全な候補範囲という解釈契約を有限検査で証明したとはしない。',
 'r54lは全職務用の一般部品であり、r54pが職務範囲を同じ本人の全cf役割へ結ぶ。公的な学識者の立場や任意の規範対象を職務と同一視せず、指定した一職務だけでjeder andereの無制約を認定しない。他者の本文対象とその発表への接続は後続で行う。',
 'r54nは教会への奉仕と同じ職務の保持を評価点で確認し、人物分類・信条採用・学識者の参照を固定基準に置く。r35tの生徒・会衆・教示基準の全構造を、この文が明示しない追加条件として課さない。',
 'r54oは特定された発表候補一組の条件であり、全聖職者・全発表候補への自由を既に述べたとはしない。実際の判断保持・発表・審査成功を許可時点へ移さない。',
 '全コード・全列の量化は有限評価器で拒否する。有限診断では二つのコードと二つの列にだけ置き換えた範囲を明示し、他の量化・同一性・脱引用は元の構成を実行する。旧一覧との有限一致と全域の論理的同値を区別する。',
]

def quantify(rows,body,op='f'):
    for n,s in reversed(rows):body=op+' '+n+' '+s+'['+body+']'
    return body

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    request=lambda point:'c[v required][v issuer v person v office v target v binding v reference v sign v '+point+']'
    text='d r54i['+fields(BASE)+' point d] c['+quantify(BOUND,'y['+request('anchor')+']['+request('point')+']')+'].\n'
    fulfillment='e[t[c[s[v target]][v binding v reference]][v point]][v sign]'
    text+='d r54j['+fields(BASE)+' point d] c['+both('k r54i['+args(BASE)+' v point]',quantify(BOUND,'y['+request('anchor')+']['+fulfillment+']'))+'].\n'
    instance=both('c[v cases][v point]','t[v trigger][v point]')
    text+='d r54k['+fields(BASE)+' trigger e cases h[d] c] c['+both(
        'g point d[c[v cases][v point]]',
        'f point d[y['+instance+'][k r54i['+args(BASE)+' v point]]]',
        'g point d['+both(instance,'k r54j['+args(BASE)+' v point]')+']')+'].\n'
    text+='d r54l[person a anchor d offices h[a] c required '+RULE+' trigger e cases h[d] c] c['+both(
        'g point d['+instance+']',
        'f point d[y['+instance+'][f office a[y[c[v offices][v office]][k r54j['+args(BASE)+' v point]]]]]')+'].\n'
    target='k r536[v judgments v insights v comparisons]';binding='l[a]['+' '.join('v '+n for n in NAMES)+']'
    fixed=' '.join(n+' a' for n in NAMES)+' source a office a reference d anchor d judgments i[j[a]] insights i[j[a]] comparisons i[h[a d] c] cases h[d] c'
    has_requirement=quantify([('issuer','a'),('duty',CODE),('binding','j[a]'),('dutyref','d'),('sign','c')],
        'k h237z[v issuer v person v office v duty v binding v dutyref v sign v anchor]','g')
    text+='d r54m['+fixed+'] c['+both(has_requirement,
        'k r37c[v source v person v scholar '+target+' '+binding+' v reference v anchor]',
        'k r54k[v person v office v anchor p h237z c[s['+target+']]['+binding+' v reference] v cases]')+'].\n'
    context='person a office a church a creed a subject a scholar a reference d anchor d'
    text+='d r54n['+context+'] c['+both('k r35m[v person v office v church v reference]',
        'k r35r[v church v creed v subject v reference]','k cf[v person v office v anchor]',
        'k h246k[v person v church v office v anchor]',
        'e[v scholar][k h247d[v person v reference]]')+'].\n'
    fixed=' '.join(n+' a' for n in NAMES)+' office a reference d anchor d judgments i[j[a]] insights i[j[a]] comparisons i[h[a d] c]'
    cases='i[point d][k h26o4[v person '+target+' '+binding+' v reference v anchor v point]]'
    text+='d r54o['+fixed+'] c['+both('k r54n[v person v office v church v creed v subject v scholar v reference v anchor]',
        'k r54m['+' '.join('v '+n for n in NAMES)+' k h247b[v person v scholar v reference] v office v reference v anchor v judgments v insights v comparisons '+cases+']')+'].\n'
    text+='d r54p[person a anchor d required '+RULE+' trigger e cases h[d] c] c[k r54l[v person v anchor i[office a][k cf[v person v office v anchor]] v required v trigger v cases]].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for c,roots in zip(sources,(['r536','r37c','h237z'],['r35m','r35r','h246k','cf','h247b','h247d'])):
        for d in closure(c.document,roots):
            n=d['name'];e=c.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(MEANINGS)|set(PRIMITIVES))&set().union(*(set(c.entries) for c in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    paths=set().union(*(set(c.source_sha256) for c in sources))
    basis=dict(status='direct_all_requirements_and_same_clerical_office_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
