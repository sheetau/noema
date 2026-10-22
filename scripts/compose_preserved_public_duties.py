"""Preserve complete signed office requirements alongside one public freedom."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_confessional_divergence import NAMES

PARENTS=('data/confessional-divergence-basis-v1.json','data/prince-sentence-basis-v1.json')
LIBRARY='examples/v016/preserved-public-duties.noema';BASIS='data/preserved-public-duties-basis-v1.json'
CODE='i b[h[j[a] d] e]'
RULE='h[a a a '+CODE+' j[a] d c d] c'
PROVIDERS=[('items','h[a] c'),('issuers','h[a] a'),('targets','h[a] '+CODE),('bindings','h[a] j[a]'),('references','h[a] d'),('signs','h[a] c')]
BASE=[('person','a'),('office','a'),('anchor','d'),*PROVIDERS,('required',RULE)]
def fields(rows):return ' '.join(n+' '+s for n,s in rows)
def args(rows):return ' '.join('v '+n for n,_ in rows)
PRIMITIVES={}
MEANINGS={
 'r537':'選択した職務義務の各項目について、同じ本人・職務・出所・段階1の目標・束縛列・内容基準・極性の要求が基準点に成立する。空一覧も許すが、全要求の不存在や網羅性は別に確認する。',
 'r54a':'r537の同じ義務項目の出所・本人・職務・目標・束縛列・内容基準・極性を保ち、比較点でも同じ要求が存在する。対象内容を実行せず、免除や別の出所・役割・内容・極性への要求で代用しない。',
 'r54b':'同じ比較点でr54aの要求が残り、各項目の同じ段階1目標へ同じ束縛列と内容基準を渡した内容が、その項目の要求極性に一致する。肯定要求と否定要求をともに扱う。',
 'r54c':'同じ本人・職務・基準点の、全出所・全型適合段階1目標・全個体列・全内容基準・両極性の要求が、同じ組合せの選択項目として一覧に含まれる。有限の既知記述だけへ量化を縮めず、一覧外の義務を不存在と補わない。',
 'r54d':'選択項目が本当に要求であるr537と、同じ職務要求を取りこぼさないr54cを合わせる。空一覧が成立するのは、この型の職務要求が基準点に存在しない場合だけである。',
 'r54e':'同じ全職務要求r54dを固定し、非空の比較範囲内で指定発表内容が成立する全候補点に、同じ義務の非免除r54aを要求する。発表の実例の存在や履行との両立はこの条件だけでは補わない。',
 'r54f':'r54eの非免除に加え、同じ一つの比較候補点で指定発表内容と全義務の履行r54bが共に成立する。発表と履行の別候補の寄せ集め、解なし、義務の免除による空虚な履行を拒む。',
 'r54g':'同じ全職務要求r54dに対し発表の比較実例があり、その全実例で要求が残り履行される。義務が一つもないこととは区別した、義務が発表候補を排除しないという読み。許可はこの条件から推論しない。',
 'r54h':'同じ七対象・二項目列・比較関数から作る発表記述r536へ、同じ学識者の立場でr37cの自由を要求する。同じ本人の別の指定職務について、非空で網羅された義務と、その同じ発表を条件とするr54fの非免除・共充足を結ぶ。自由の出所と職務義務の出所は同一化しない。',
}
LIMITS=[
 'u0015第二文のdürfen/freiとunbeschadet ihrer Amtspflichtに向けた依存群。旧rp3–rpaの非免除・履行・共充足を、既存h237z/h245cが扱う段階1目標と束縛列・内容基準へ拡張する。旧定義の型や意味は変更しない。',
 'unbeschadetは職務義務を免除せず、発表と同じ職務義務の履行が両立するという読み。職務遂行への因果的な無害性、法的優先順位、現に履行したこと、発表能力は追加しない。自由は積極的許可と不実行要求の不在であり、両立だけから許可を導かない。',
 '全義務の一覧は、この固定した本人・職務・基準点について同じ段階1の規範形式で表す全要求を尽くす。任意の記述段階に渡る全規範を有限列挙したとはしない。全文では該当の職務義務がこの形式で表される具体的な供給と職務保持を結ぶ必要がある。',
 '一覧の出所・目標・束縛列・内容基準・極性は比較中に固定する。新しい要求の発生は禁止しないが、元の要求を別の要求へ置き換えることは非免除と数えない。矛盾する要求も存在し得るが、その場合の共充足は成立しない。',
 '比較範囲は同じ発表と職務を評価する全関連候補を固定する。成功した候補だけを選ばず、空範囲を両立の根拠にしない。現実の未来への到達、時間順序、確率的な通常性は別問題である。',
 '全域量化r54cは全ての型適合記述と個体列を含むため、有限評価器の既知の二記述・二列だけに置き換えて証明しない。限定診断と全域評価の拒否を記録し、型と接続の確認を現実の網羅性の証明とはしない。',
 'r54hでは発表実行・判断の保持・比較内容の評価は比較候補内に置く。許可時点に実際の発表や公衆の審査成功を要求しない。第一文の君主への照応、聖職者と敬意評価、無制約の他者、noch mehr、全候補量化と全文帰属は残る。',
 '本文113主張・17全単位判断と追加第一文490文字は変更しない。第二文の意味判断を検査通過だけで増やさない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    selected='c[v items][v item]'
    request=lambda point:'c[v required][c[v issuers][v item] v person v office c[v targets][v item] c[v bindings][v item] c[v references][v item] c[v signs][v item] v '+point+']'
    text='d r537['+fields(BASE)+'] c[f item a[y['+selected+']['+request('anchor')+']]].\n'
    text+='d r54a['+fields(BASE)+' point d] c['+both('k r537['+args(BASE)+']','f item a[y['+selected+']['+request('point')+']]')+'].\n'
    actual='t[c[s[c[v targets][v item]]][c[v bindings][v item] c[v references][v item]]][v point]'
    text+='d r54b['+fields(BASE)+' point d] c['+both('k r54a['+args(BASE)+' v point]','f item a[y['+selected+'][e['+actual+'][c[v signs][v item]]]]')+'].\n'
    variables=[('issuer','a'),('target',CODE),('binding','j[a]'),('reference','d'),('sign','c')]
    match=both(selected,*('e[c[v '+p+'][v item]][v '+v+']' for p,v in (('issuers','issuer'),('targets','target'),('bindings','binding'),('references','reference'),('signs','sign'))))
    covered='y[c[v required][v issuer v person v office v target v binding v reference v sign v anchor]][g item a['+match+']]'
    for n,s in reversed(variables):covered='f '+n+' '+s+'['+covered+']'
    text+='d r54c['+fields(BASE)+'] c['+covered+'].\n'
    text+='d r54d['+fields(BASE)+'] c['+both('k r537['+args(BASE)+']','k r54c['+args(BASE)+']')+'].\n'
    f=fields(BASE)+' trigger e cases h[d] c';a=args(BASE)+' v trigger v cases'
    instance=both('c[v cases][v point]','t[v trigger][v point]')
    preserved='f point d[y['+instance+'][k r54a['+args(BASE)+' v point]]]'
    text+='d r54e['+f+'] c['+both('k r54d['+args(BASE)+']','g point d[c[v cases][v point]]',preserved)+'].\n'
    text+='d r54f['+f+'] c['+both('k r54e['+a+']','g point d['+both(instance,'k r54b['+args(BASE)+' v point]')+']')+'].\n'
    text+='d r54g['+f+'] c['+both('k r54d['+args(BASE)+']','g point d['+instance+']',
        'f point d[y['+instance+'][k r54b['+args(BASE)+' v point]]]')+'].\n'
    target='k r536[v judgments v insights v comparisons]';binding='l[a]['+' '.join('v '+n for n in NAMES)+']'
    sourcefields=' '.join(n+' a' for n in NAMES)+' source a office a reference d anchor d judgments i[j[a]] insights i[j[a]] comparisons i[h[a d] c] '+fields(PROVIDERS)+' cases h[d] c'
    base='v person v office v anchor '+args(PROVIDERS)+' p h237z'
    text+='d r54h['+sourcefields+'] c['+both('g item a[c[v items][v item]]',
        'k r37c[v source v person v scholar '+target+' '+binding+' v reference v anchor]',
        'k r54f['+base+' c[s['+target+']]['+binding+' v reference] v cases]')+'].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for c,roots in zip(sources,(['r536'],['r37c','h237z'])):
        for d in closure(c.document,roots):
            n=d['name'];e=c.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not set(MEANINGS)&set().union(*(set(c.entries) for c in sources))
    doc=parse(format_graph(doc,'compact')+definitions())
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    paths=set().union(*(set(c.source_sha256) for c in sources))
    basis=dict(status='complete_signed_office_duties_and_public_freedom_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
