"""Bind shared confession, substantive non-amendment and reciprocal undertakings."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENTS=('data/guardian-irrationality-basis-v1.json','data/delegated-associations-basis-v1.json')
LIBRARY='examples/v016/irrevisable-confession.noema'
BASIS='data/irrevisable-confession-basis-v1.json'
TERMS='i[h[j[a]] e]'
PRIMITIVES={
    'h254w':('[a i[e] i[e] d] c',['formulation','baseline','candidate','reference'],
        '同じ定式化の同じ固定解釈のもとで、二つの閉じたNoema記述は教義上・規範上の実質的な内容を同じに保つ。単に同じ真理値になること、同じ名称、原語の綴りの一致とは分ける。表記・配列の変更でも内容を保つものは許せるが、教えの追加・削除・反転は同じにしない。意味の同一性を入力で明示する関係であり、任意の記述の同義性を判定するアルゴリズムや信条内容の真理を与えない。'),
    'h254x':('[a a a d] c',['body','formulation','alternative','reference'],
        'この団体の同じ信条を保持・改訂する際に検討する定式化の全候補範囲に、この代替が入る。現在のまま保持する候補も含み、実際に提出済みの案だけ、許可された案だけ、内容を保つ案だけへ狭めない。候補の内容は同じh246eが閉じたNoema記述で与える。候補の実在する物理文書、実施や真理は含意しない。'),
    'h254y':('[a a a a d d] c',['agreement','body','formulation','alternative','reference','point'],
        'この合意に定める制度上の規則では、同じ団体の同じ固定信条をこの代替へ改訂することが、この評価点で認められる。改訂が物理的に可能か、現実に行われたか、道徳的に正当かとは分ける。固定基準は元の信条と候補の解釈を保持するためのもので、評価点ごとに元の内容を選び直さない。未知の改訂権能を否定に補わない。'),
    'h254z':('[a] d',['agreement'],
        'この合意の条項を読む際に固定する基準状況。各当事者の宣言の時点や条項を評価する候補状況ごとに取り替えない。具体的な相互引受けでは外側の同じ基準との一致を要求する。この参照だけで合意の成立・有効性や特定の暦日時は主張しない。'),
    'h255a':('[a '+TERMS+' d] c',['agreement','terms','reference'],
        '同じ合意には、この固定基準でこの閉じたNoema条項関数が割り当てられている。各当事者が引き受ける記述と同一のものを要求し、別名・別の版・後日の改訂への引受けを勝手に移送しない。条項の実際の履行や規範的有効性は含意しない。'),
    'h255b':('[a a a '+TERMS+' j[a] d] c',['person','activity','agreement','terms','bindings','point'],
        '本人はこの同じ行為で、同じ合意の閉じた条項記述を同じ順序の引数に適用する内容を、自らを拘束する引受けとして表明する。単なる引用、他人への命令、文面の受領や履行済みとは分ける。引数列の先頭の本人との一致、行為の生起・担い手、他当事者に対する引受けは合成側で結ぶ。'),
    'h255c':('[a d d] c',['agreement','reference','point'],
        '同じ合意の形成を評価する固定基準について、指定状況が関係する経過の履歴に属する。各人の表明時点と基準を含めて履歴を供給する。履歴の順序と各表明が基準と同時か以前であることは別に検査する。存在しない表明を補ったり不都合な表明を時点範囲から落としたりしない。'),
    'h255d':('[a a a a '+TERMS+' j[a] d] c',['person','counterparty','activity','agreement','terms','bindings','point'],
        'この本人はこの同じ行為で、同じ合意の同じ条項記述と順序付き引数について、この相手当事者に対して責務を負うという引受けを表明している。互いに無関係な独白、別の合意への約束、第三者の報告とは分ける。相手の実際の理解・受領・承諾、履行、強制の不在や法的有効性は含意しない。'),
}
MEANINGS={
    'r46p':'同じ固定基準で宗教の基礎的な教えh245zを主題とする信条の定式化h246fを結ぶ。特定の教理を補わず、採用主体・内容の真理・本人の信念とは分ける。',
    'r46q':'同じ団体が同じ信条の評価点での閉じた内容を共同の立場として採用し、その内容が固定基準での同じ信条の内容を実質的に保つh254wことを要求する。内容を保つ別記述は許せるが、名称だけ同じで教理が変わった場合や採用をやめた場合は満たさない。内容自体は脱引用しない。',
    'r46r':'固定した候補範囲h254xに元の信条を含め、その全候補について、元の内容を保つか、同じ合意・団体・信条の規則による改訂が認められないことを要求する。内容を変える改訂の権能の不在であり、現実に改訂されなかったという結果とは別の条件。',
    'r46s':'同じ信条・主題・固定基準の宗教的定式化r46pに、同じ評価点での内容を保つ採用r46qと実質的改訂を認めない制度的条件r46rを結ぶ。採用を続けることと制度上の変更不能を同一視しない。',
    'r46t':'同じ合意・団体・信条・主題・固定基準について、候補の全履歴の基準以後でr46sの同じ内容の採用と変更不能が保たれる内容。既存rcaの厳密全順序・基準時包含・全将来を用い、都合の良い短期区間へ縮めない。履歴の終点不在、同じ身体・構成員の不死を要求しない。',
    'r46u':'本人・合意・団体・信条・主題の正確な五個体列を受け、合意の固定基準h254zに本人が人であり同じ団体に所属することと、r46tの共有する制度的結果を結ぶ条項内容。全当事者へ同じ合意・団体・信条・主題を渡し、先頭の本人だけを変える。本人の内心の信仰ではなく、同じ共同の制度上の規則を自分も拘束されるものとして引き受ける読み。',
    'r46v':'合意の固定基準を同じ外側基準へ一致させ、同じ団体の全所属者r46aをhzcgの当事者として固定する。全員が同じ条項r46uと同じ合意・団体・信条・主題を引き受け、各人の同じ表明行為・時点で他の全当事者に対する引受けh255dを結ぶ。宣誓の追加条件、目的、履行や正当性はまだ加えない。',
}
LIMITS=[
    'u0013のauf ein gewisses unveränderliches Symbolとsich unter einander verpflichtenの内容へ向けた依存群。unveränderlichを同じ内容の継続的採用と、合意に定める制度上の実質的改訂権能の不在として読む。物理的に文字を書き換えられないことや全可能世界で変更が起こり得ないこととはしない。',
    '旧rh3/rh4は記述の構文同一性と有限区間の保持を扱う。今回のr46q/r46tは内容を保つ改記を許し、全候補履歴の基準以後へ接続する。h254wの実質的内容の一致は明示解釈の責任で、同じ真理値・同じ名称・未検査の別名から自動認定しない。',
    '改訂候補の全範囲はh254xで基準時に固定する。元の信条を含むことを合成側で確認するが、有限検査だけで現実の全候補の完全さを証明しない。違法な案・未提出案・改訂に失敗する案も、結果だけで除外しない。',
    '引受ける共同の制度的結果を本人にも拘束する条項として表明する読み。各人の私的な信仰、実際の全教示、履行の成功、将来世代の同意や同じ個人の不死を補わない。基本関係h255b/dは引受けの表明を述べ、規範的な有効性は述べない。',
    '履歴・固定基準・候補・意味の同一性・改訂権能の入力が未知なら偽として穴埋めしない。条項を引用しただけなら信条内容・未来の採用・制度の実施を実行せず、実際の条項成立を尋ねた場合だけ必要な入力を要求する。',
    'eidlichの厳粛な表明・権威への呼びかけ、後見の目的、会議体の例示・自己呼称との接続、権限の問いと否定回答は未統合。本文96主張と意味確認分量は変更しない。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    text='d r46p[creed a subject a reference d] c['+both('k h245z[v subject v reference]','k h246f[v creed v subject v reference]')+'].\n'
    original='k h246e[v creed v reference]';current='k h246e[v creed v point]'
    text+='d r46q[body a creed a reference d point d] c['+both(
        'k h246g[v body v creed '+current+' v point]', 'k h254w[v creed '+original+' '+current+' v reference]')+'].\n'
    text+='d r46r[agreement a body a creed a reference d point d] c['+both(
        'k h254x[v body v creed v creed v reference]',
        'f alternative a[y[k h254x[v body v creed v alternative v reference]][x['+
        'k h254w[v creed '+original+' k h246e[v alternative v reference] v reference]]['+
        'u[k h254y[v agreement v body v creed v alternative v reference v point]]]]]')+'].\n'
    fields='agreement a body a creed a subject a reference d';args='v agreement v body v creed v subject v reference'
    text+='d r46s['+fields+'] e[b point['+both('k r46p[v creed v subject v reference]',
        'k r46q[v body v creed v reference v point]','k r46r[v agreement v body v creed v reference v point]')+']].\n'
    text+=('d r46t['+fields+'] e[b candidate[k rca['+
        'i[at d][k h253w[v body v candidate v at]] i[first d last d][k ic[v first v last v candidate]] '+
        'v reference i[at d][t[k r46s['+args+']][v at]]]]].\n')
    names=('person','agreement','body','creed','subject');ref='k h254z[v agreement]'
    text+='d r46u[bindings j[a]] e[b candidate['+bind(names,both('k aa[v person]',
        'k h246c[v body v person '+ref+']','t[k r46t[v agreement v body v creed v subject '+ref+']][v candidate]'))+']].\n'
    declares='i[person a activity a agreement a terms '+TERMS+' bindings j[a] point d]['+both(
        'k h255b[v person v activity v agreement v terms v bindings v point]',
        'f other a[y['+both('k h246c[v body v other v reference]','u[e[v person][v other]]')+']['+
        'k h255d[v person v other v activity v agreement v terms v bindings v point]]]')+']'
    text+='d r46v[body a agreement a creed a subject a reference d] c['+both('e[k h254z[v agreement]][v reference]',
        'k hzcg[v agreement r[p r46u] v reference k r46a[v body v reference p h246c] '+
        'i[person a][l[a][v person v agreement v body v creed v subject]] '+
        'i[at d][k h255c[v agreement v reference v at]] p h255a '+declares+']')+'].\n'
    return text


def build():
    old,lib=parents();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['hzcg','h246e','h246g','h245z','h246f','rca','h253w','ic','aa','h246c']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for d in closure(lib.document,['r46a']):
        n=d['name']
        if n in imported:assert d==imported[n]['declaration'] and lib.entries[n]['meaning_ja']==imported[n]['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(lib.entries))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    primitives={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    primitives.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    paths=set().union(*(set(c.source_sha256) for c in parents()))
    basis=dict(status='same_irrevisable_confession_in_reciprocal_undertakings',document=LIBRARY,primitives=primitives,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
