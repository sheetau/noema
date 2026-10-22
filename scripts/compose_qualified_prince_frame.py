"""Share the prince's argument across qualifications and scoped discourse."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_self_report_dignity import FRAME_NAMES,FARGS,SPEECH,SPEECH_NAMES,SARGS,name_args

PARENTS=('data/self-report-dignity-basis-v1.json','data/designation-rejection-basis-v1.json','data/named-epoch-sentence-basis-v1.json')
LIBRARY='examples/v016/qualified-prince-frame.noema';BASIS='data/qualified-prince-frame-basis-v1.json'
PROFILE='i h[h[a] e]'
FIELDS='label a users a '+SPEECH;ARGS='v label v users '+SARGS
NAMES=('label','users',*SPEECH_NAMES)
PRIMITIVES={
 'h26nn':('[a a a '+PROFILE+' '+PROFILE+' d] c',['node','author','scope','boundary','premise','context'],
   '著者がこの箇所で、同じ仮定範囲と段階7の閉じた人物範囲記述の下で、同じ人物引数への前提性質を採用して論じる。同じ人物・評価点を二つの性質記述へ渡す束縛であり、異なる人物の条件を混ぜない。ugと同種の仮定採用を高い記述へ保つ。該当人物の実在、前提の現実の真理、引用内容の実行を導かない。'),
 'h26no':('[a a a '+PROFILE+' '+PROFILE+' d] c',['node','author','scope','boundary','conclusion','context'],
   '著者がこの箇所で、同じ仮定範囲と段階7の閉じた人物範囲記述の下で、同じ人物引数に結論性質が当てはまるものとして提示する。uhと同種の範囲内の主張であり、無条件の現実の断言や、他の範囲・他の人物への適用に変えない。結論の真理・前提からの論理的必然・心理的因果は別問題である。'),
 'h26np':('[a a a a '+PROFILE+' '+PROFILE+' a d] c',['node','author','scope','clause','boundary','focus','item','context'],
   '同じ著者が同じ仮定範囲・節・人物範囲において、指定した対象にまで焦点内容が及ぶものとして取り立てる。その対象への適用は通常の期待ではそこまで及ぶと考えにくいという背景を伴う。h26jhと同じ取り立てを段階7の人物性質へ保つ。主語本人だけの強調、唯一性、数値確率、全代替対象の実際の拒否、焦点内容の現実の成立を補わない。'),
}
MEANINGS={
 'r5xh':'同じ本人・公的立場・共同体・評価点について、h234fの君主的統治職とhzfnの唯一の最高役職保持・任用・職務委託を結ぶ。存在量化で別の役職を選び直さず、後続の品位・義務・自由方針の役職を同じものに保つ。',
 'r5xi':'同じ役職と共同体を固定した、r5xhを満たす人物の性質。君主の範囲を世襲・特定国・世界でただ一人という条件へ狭めない。',
 'r5xj':'同じ人物・点に君主の範囲r5xi、自己報告を品位に反しないとする本人の判断r5wq、同じ名称の適用拒否r5w5をrnzで結ぶ。内側の義務判断・義務・自由政策の真理や自己報告の実行を前件へ追加しない。',
 'r5xk':'r5xjの同じ人物の条件を満たす全ての者に、引数で与える同じ人物の結論内容が当てはまる一般条件ro2。結論の具体的な啓蒙・称賛は後続で構成し、人物の存在をここから導かない。',
 'r5xl':'同じr5xjに該当する人物の存在ro3を、一般条件から分離して構成する。本文の独立した実在主張にはまだしない。',
 'r5xm':'同じr5xjに該当し、同じ結論を満たさない人物がいるという反例ro4。別人の結論や別時点の不成立を混ぜない。',
 'r5xn':'同じ役職と共同体の閉じた名前をr5xiへ適用した段階7の人物範囲記述。談話の前提と結論に共用し、人物の実在を引用から実行しない。',
 'r5xo':'同じ規範出所・役職・集団・共同体・主題・受け手・固定基準の名前を、品位判断の人物性質r5wqへ適用した段階7の記述。内側の義務判断だけへ前提を縮めない。',
 'r5xp':'同じ名称・使用者集団・規範出所・役職・対象集団・共同体・主題・基準の名前を、r5w5の名称拒否の人物性質へ適用した段階7の記述。r5xoと同じ人物引数を後で共用する。',
 'r5xq':'同じ名称と使用者、自己報告の受け手を含む全設定の名前を、r5xjの人物条件へ適用した段階7の閉じた記述。三条件を別人へ分散させない。',
 'r5xr':'談話の四つの性質記述へ渡す八個体と固定基準の全呼称を脱引用して、元の設定との一致を検査する。別名称・別受け手・別役職の引用を黙って採用しない。',
 'r5xs':'同じ著者・仮定範囲・君主の人物範囲の下で、先行箇所がr5xoの品位判断を前提として採り、別の後続箇所がr5xpの名称拒否を帰結として提示する。udによる帰結提示とueの本文順序を結び、論理的妥当性や現実の拒否を断言しない。',
 'r5xt':'同じ名称拒否の節・仮定範囲・君主の人物範囲で、その同じ名称への拒否までが期待を越えて取り立てられる提示。selbst den ... Namenを対象の取り立てとして保持し、von sichの同一本人への適用から区別する。',
 'r5xu':'r5xsの帰結提示とr5xtの取り立てを、同じ著者・仮定範囲・後続節・名称・意味設定で結ぶ。第一関係節と第二関係節の談話の接続であり、文全体の啓蒙・称賛の著者主張は別に統合する。',
}
LIMITS=[
 'u0015第一文のEin Fürstからvon sich ablehntまでの人物条件と談話に向けた依存群。三つの既存条件を同じ人物・役職・共同体・点へ接続する。本文112主張と17単位判断を変更せず、一文全体の意味確認を先取りしない。',
 'Ein Fürstを、明示した政治的共同体の君主的な最高職の保持者についての一般的な条件として読む。役職の全範囲と順序、唯一の保持、同じ制度への任用・委託を既存hzfn/r2uiで保つ。役職を別々に存在量化して品位や義務の役職と取り違えず、世襲・王という敬称・特定のフリードリヒへの実在主張を補わない。',
 '人物条件は、自己報告を品位に反しないと考える本人の判断と名称拒否である。本人の内側の義務判断、実際の義務や自由政策、実際の報告を追加しない。名称の高慢評価は著者の評価として別に帰属し、前件に隠して主文を空虚に成立させない。',
 'alsoは、先行の品位判断を含む人物描写から名称拒否へ進む帰結の提示として読む。その提示から、義務を信じる人は必ず名称を拒むという一般法則や心理的因果を導かない。両節を同じ仮定範囲に置き、先行の内側の義務内容だけを無条件の事実へ昇格させない。',
 'selbst den hochmüthigen Namenは、今回はその名称さえという目的語の取り立てとして読む。IDSのFokuspartikelの説明を文法上の補助とし、語順だけで唯一の解釈が証明されたとはしない。von sichは適用対象が拒否者本人であること、後続ist selbst aufgeklärtは本人の啓蒙への焦点として別に扱う。',
 '取り立ては同じ拒否内容・名称・節・範囲への期待背景として記述する。具体的に列挙されていない全代替の拒否、数値確率、最上位、実際の驚きや著者の測定済み心理は補わない。役職や人物の実在を提示関係から実行しない。',
 '高い段階の品位判断を保つため、談話では人物性質を段階7の閉じた記述へそろえる。共通の人物引数を各性質に適用し、参照先の全一致を検査する。段階を下げて引用の内外を混ぜない。',
 '一般条件・該当者の存在・反例は別の内容である。結論はこの依存群では引数として残し、既存の能力条件だけでist selbst aufgeklärtと称賛全体を完成扱いにしない。名前・使用者・受け手・規範源・固定基準と談話箇所の本文束縛、名称評価の著者帰属、sondern、一文後半と後続の意味確認は残る。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    text='d r5xh[actor a office a community a point d] c['+both('k h234f[v office v community v point]',
        'k hzfn[v actor v office v community v point p h234d p r2ui p h234e]')+'].\n'
    text+='d r5xi[office a community a] h[a] e[i[actor a][b point[k r5xh[v actor v office v community v point]]]].\n'
    qualified='k rnz[k r5xi[v office v community] k r5wq['+SARGS+'] k r5w5[v label v users '+FARGS+']]'
    text+='d r5xj['+FIELDS+'] h[a] e['+qualified+'].\n'
    for n,target in (('r5xk','ro2'),('r5xm','ro4')):
        text+='d '+n+'['+FIELDS+' conclusion h[a] e] e[k '+target+'[k r5xj['+ARGS+'] v conclusion]].\n'
    text+='d r5xl['+FIELDS+'] e[k ro3[k r5xj['+ARGS+']]].\n'
    def code(n,target,names,ref=True):
        fields=' '.join(x+' i[a]' for x in names)+(' reference i[d]' if ref else '')
        values=' '.join('v '+x for x in (*names,'reference') if ref or x!='reference')
        return 'd '+n+'['+fields+'] '+PROFILE+'[o a[r h[p '+target+']]['+values+']].\n'
    text+=code('r5xn','r5xi',('office','community'),False)+code('r5xo','r5wq',SPEECH_NAMES)
    text+=code('r5xp','r5w5',('label','users',*FRAME_NAMES))+code('r5xq','r5xj',NAMES)
    valid=both(*('e[s[k h223g[v '+n+']]][v '+n+']' for n in NAMES),'e[s[k h223h[v reference]]][v reference]')
    text+='d r5xr['+FIELDS+'] c['+valid+'].\n'
    boundary='k r5xn[k h223g[v office] k h223g[v community]]'
    premise='k r5xo['+name_args(SPEECH_NAMES)+']';result='k r5xp['+name_args(('label','users',*FRAME_NAMES))+']'
    shared='v author v scope '+boundary
    text+='d r5xs[first a second a author a scope a '+FIELDS+' context d] c['+both('k r5xr['+ARGS+']','u[e[v first][v second]]',
        'k h26nn[v first '+shared+' '+premise+' v context]','k h26no[v second '+shared+' '+result+' v context]',
        'k ud[v author i[node a][e[v node][v first]] v second v context]','k ue[v first v second v context]')+'].\n'
    text+='d r5xt[focus a second a author a scope a '+FIELDS+' context d] c['+both('k r5xr['+ARGS+']',
        'k h26np[v focus v author v scope v second '+boundary+' '+result+' v label v context]')+'].\n'
    text+='d r5xu[first a second a focus a author a scope a '+FIELDS+' context d] c['+both(
        'k r5xs[v first v second v author v scope '+ARGS+' v context]',
        'k r5xt[v focus v second v author v scope '+ARGS+' v context]')+'].\n'
    return text

def build():
    libs=parents();doc=deepcopy(libs[0].document);doc.update(declarations=[],statements=[]);imported={}
    for lib,roots in zip(libs,(['r5wq','h223g','h223h'],['r5w5'],['h234f','hzfn','h234d','h234e','r2ui','rnz','ro2','ro3','ro4','ud','ue'])):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(l.entries) for l in libs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(l.source_sha256) for l in libs))
    basis=dict(status='shared_prince_qualification_scoped_consequence_and_object_focus',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
