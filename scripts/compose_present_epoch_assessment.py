"""Bind present population, collective assessment and one fixed epoch dialogue."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_collective_attainment import STANDARD
from scripts.compose_qualified_judgment import QUALIFIED,QARGS

PARENT='data/royal-intervention-sentence-basis-v1.json'
LIBRARY='examples/v016/present-epoch-assessment.noema'
BASIS='data/present-epoch-assessment-basis-v1.json'
FRAME='speaker a group a epoch a reference d candidate d point d'
ARGS='v speaker v group v epoch v reference v candidate v point'
CHECKED=FRAME+' assessed h[a] e standard '+STANDARD
ATTAINED=CHECKED+' capable h[a] e'
CONTRAST=ATTAINED+' progress e'
HISTORY='i[at d][k h257z[v reference v candidate v at]]'
BEFORE='i[first d last d][k ic[v first v last v candidate]]'
PERIODS='i[era a at d][k h26ab[v era v reference v candidate v at]]'
PEOPLE='i[person a][k h246c[v group v person v reference]]'
PRESENT='i[person a at d][k h256o[v person v candidate v at]]'
OLD_FRAME='v epoch v point '+HISTORY+' '+BEFORE+' '+PERIODS+' '+PEOPLE+' '+PRESENT
MEANINGS={
 'r5sb':'同じ固定区分・候補履歴で現在点が非空の時代区間に属し、固定基準での集団所属がその現在点に生存する全人間とちょうど一致し非空である。時代中の過去又は未来だけに生存する者を現在人口へ混ぜず、評価結果で人々を選ばない。',
 'r5sc':'r5sbと同じ現在の集団に発話の基準主体が人として属する。後のwirを同時代に生存する人々一般と読むための接続であり、全員が共同発話したこと、特定国・宗派への所属を追加しない。',
 'r5sd':'同じ現在人口と主体・時代・現在点でrqwhの全員の能力評価と集団基準の両端条件が整う。全員の評価と全員の能力保有を区別し、基準は同じ引数に固定する。',
 'r5se':'r5scの同じ現在人口にrqwiの集団到達を適用する。能力保有者を現在の集団内へ限定し、同じ現在点・同じ基準で判定する。全員一致を語義へ固定しない。',
 'r5sf':'r5scの同じ主体・集団・時代・現在点で、渡された進行内容が成立する。進行内容は具体的なNoema構成で与える必要があり、この接続だけで能力取得や到達の否定を補わない。',
 'r5sg':'同じ現在人口・時代・現在点で評価と基準が整い、集団到達は成立せず、指定された進行内容は成立する。未評価、空の人口、話者不在、別時点での進行を未到達だが進行中の成功例にしない。',
 'r5sh':'r5seの現在点を引数で固定して閉じた到達内容を返す。外側の評価点を動かしても問いの現在・人々・時代・基準を替えない。実際の到達や質問出来事は別である。',
 'r5si':'r5sgの同じ現在点と全設定を閉じ、未到達かつ進行中という回答内容を返す。外側の評価点と原文の現在を混同しない。',
 'r5sj':'r5shの到達内容を正極性で問う発話内容。発話種別はaskで、実際の質問生起や著者の帰属を追加しない。',
 'r5sk':'r5siの同じ設定の回答内容を正極性で述べる発話内容。質問と発話種別を区別し、構成だけで実際の回答生起や真理を断言しない。',
 'r5sl':'同じ現在点を固定した、r5sdの有効な評価とr5seの到達否定の内容。単なる入力不足又は対象不在による否定ではなく、Neinの候補内容として切り出す。',
 'r5sm':'同じ現在点を固定したr5sfの進行肯定内容。前の到達否定とは独立に保持し、aber wohlの肯定側の候補へ使える。',
 'r5sn':'質を含む同じ活動記述のhzvrの評価をr5sdへ結ぶ。主題範囲のanchorは現在点と同一で、質の基準文脈もhzvr内で同じanchorへ照合する。資料不足を不能へ替えない。',
 'r5so':'r5snと同じ宗教等の主題・全事項・参照・質の記述についてhzvsの行使能力をr5seへ結ぶ。無修飾のh4lの評価を流用せず、能力の質を外さない。',
 'r5sp':'r5sn/oと同じ主題・質・集団・現在について、未到達と進行をr5sgへ接続する。質の具体的な採用、進行内容の原文への採用は別に必要である。',
 'r5sq':'r5snと同じ現在・主題・質の設定の有効性と、r5soの到達否定を結ぶ。基準文脈の不一致や未評価だけで未到達を作らない。',
}
LIMITS=[
 'u0014冒頭の問答と続く能力判断へ向けた共通の接続。wirを同時代に生存する人々一般とする明示読解の候補として、現在人口の完全性と話者の所属を構成する。全文の著者帰属と意味判断はまだ加えない。',
 '時代は既存rjcの非空区間、現在はその内点とする。区分の固定基準・候補履歴・現在点・提示文脈は別の役割であり、ここでは提示文脈を導入しない。過去に完成していたこと又は未来の完成を現在の判定へ流用しない。',
 '集団基準は既存rqwgの両端条件を満たすものを同じ引数で受ける。全員一致・過半数・特定の比率を言語の意味へ固定しない。両端条件だけで単調性や基準の妥当性を証明したとはせず、原文への採用時には基準の意味を固定する必要がある。',
 '全員の評価が整うことは全員が能力を持つことではない。未知は拒否し、明示的な未評価も到達否定の根拠にはしない。集団外の成功を分布へ混ぜず、同じ集団・現在を基準の各呼出しへ渡す。',
 '進行と到達は独立の性質で、両方が真又は両方が偽でもよい。回答の候補が選ぶのは到達偽・進行真である。進行の原文接続では同じ集団への機会の開放・障害の漸減等の具体的な内容を別に構成し、任意の真フラグで代用して完成としない。',
 '質付き接続はhzvr/hzvsの同じ閉じた活動記述、元の対象範囲、本人側の能力基盤を保つ通常機会を継承する。無修飾のh4lや資料の有無による判断の正誤へ置き換えない。sicher und gutの具体的な読み、宗教的対象範囲、集団基準の採用は未完。',
 '閉じた問答では原文の現在点を固定する。Noema内容を別の外側評価点で扱っても、その時点を原文のjetztへすり替えない。構成したask/assertは仮定的な発話内容であり、Wenn gefragt wirdの条件付き提示・denn/nun・aber wohl・著者帰属は次の統合で残る。',
 '既存の全単位判断16区間と本文108主張を保持する。局所検査は接続と範囲の検査で、第一文又は第七段落の意味同一性を自動認定しない。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def definitions():
    member='k h246c[v group v person v reference]'
    living=both('k aa[v person]','k h256o[v person v candidate v point]')
    frame=both('k h26aa[v epoch v reference]','k rjc[v epoch '+HISTORY+' '+BEFORE+' '+PERIODS+']',
        'k h26ab[v epoch v reference v candidate v point]','g person a['+member+']',
        'f person a[z['+member+']['+living+']]')
    fields=FRAME.replace('speaker a ','');args=ARGS.replace('v speaker ','')
    text='d r5sb['+fields+'] c['+frame+'].\n'
    text+='d r5sc['+FRAME+'] c['+both('k r5sb['+args+']','k aa[v speaker]','k h246c[v group v speaker v reference]')+'].\n'
    for name,fields,target,tail in (
        ('r5sd',CHECKED,'rqwh','v assessed v standard'),
        ('r5se',ATTAINED,'rqwi','v assessed v standard v capable'),
        ('r5sf',FRAME+' progress e','rmk','v progress'),
        ('r5sg',CONTRAST,'rqwj','v assessed v standard v capable v progress')):
        text+='d '+name+'['+fields+'] c['+both('k r5sc['+ARGS+']','k '+target+'['+OLD_FRAME+' '+tail+']')+'].\n'
    attained=ARGS+' v assessed v standard v capable';contrast=attained+' v progress'
    text+='d r5sh['+ATTAINED+'] e[b outer[k r5se['+attained+']]].\n'
    text+='d r5si['+CONTRAST+'] e[b outer[k r5sg['+contrast+']]].\n'
    true='e[v speaker][v speaker]'
    text+='d r5sj['+ATTAINED+'] f[k rij[k r5sh['+attained+'] '+true+']].\n'
    text+='d r5sk['+CONTRAST+'] f[k rik[k r5si['+contrast+'] '+true+']].\n'
    text+='d r5sl['+ATTAINED+'] e[b outer['+both('k r5sd['+ARGS+' v assessed v standard]','u[k r5se['+attained+']]')+']].\n'
    text+='d r5sm['+FRAME+' progress e] e[b outer[k r5sf['+ARGS+' v progress]]].\n'
    source=FRAME+' standard '+STANDARD+' '+QUALIFIED
    tail='k hzvr['+QARGS+'] v standard k hzvs['+QARGS+']'
    checked=ARGS+' k hzvr['+QARGS+'] v standard'
    for name,fields,body in (
        ('r5sn',source,'k r5sd['+checked+']'),
        ('r5so',source,'k r5se['+ARGS+' '+tail+']'),
        ('r5sp',source+' progress e','k r5sg['+ARGS+' '+tail+' v progress]'),
        ('r5sq',source,both('k r5sd['+checked+']','u[k r5se['+ARGS+' '+tail+']]'))):
        text+='d '+name+'['+fields+'] c['+both('e[v anchor][v point]',body)+'].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['rqwh','rqwi','rqwj','rmk','rjc','h257z','ic','h26aa','h26ab','h256o','h246c','aa','hzvr','hzvs','rij','rik']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not set(MEANINGS)&set(old.entries)
    doc=parse(format_graph(doc,'compact')+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    basis=dict(status='present_population_and_qualified_collective_assessment_dependency',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
