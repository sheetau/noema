"""One quoted policy for human or represented principals and political ability."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/legislative-freedom-sentence-basis-v1.json','data/military-peace-guarantee-basis-v1.json')
ROOTS=(('r2ug','r2uh','h234g','h234h','aa','dg','f3','h223h','xd','r572','h237c'),('r6fp',))
LIBRARY='examples/v016/political-quoted-speech.noema';BASIS='data/political-quoted-speech-basis-v1.json'
MESSAGE='i b[h[a] f]'
PRIMITIVES={
 'h26v3':('[a a a d d] c',['performer','principal','call','reference','point'],
  'この人は、同じ固定基準において、指定された同じ主体を代表し、この同じ発話行為の内容をその主体自身の公的な方針表明として述べる制度上の資格をこの点で持つ。自称・単なる伝言や朗読・別の行為の委任と分け、必要な同じ主体の承認・委任手続を満たす。内容が政治的に賢明又は規範的に許されること、正当な許可が実際に成立したことは含意しない。'),
 'h26v4':('[a a d d] c',['call','principal','reference','point'],
  '同じ基準で、この発話行為はこの点で、指定主体自身がその内容を公的な方針として打ち出す行為に制度上帰属する。代表者の私的な見解や、主体について述べた外部の報告とは分ける。代表資格、生起、実行者、具体的な引用内容は別に検査する。内容の真理、許可の成立、聞き手の服従や発話の規範的正当性を自動的に導かない。'),
 'h26v5':('[a a d a d] c',['principal','community','reference','method','start'],
  '同じ主体・政治的共同体・引用内容の固定基準について、この開始点の実際の公的立場・資源・制度手続の下で、その主体が公式の方針を打ち出すために実行できる方法。発声や文章の朗読だけ、他の主体の権限の借用、先に別の統治体を作る必要のある方法とは分ける。成功や平穏を先取りせず、特定の候補が好ましいこと又は規範的に許されることだけで利用可能としない。'),
 'h26v6':('[a a d a d d] c',['principal','community','reference','method','start','end'],
  '同じ主体・共同体・引用基準・方法・開始点で、公式の方針表明を行う通常の実践的な想定結果の範囲。発話・許可・平穏を同じ結果で評価し、成功した結果だけを想定可能としない。範囲の現実的な妥当性は解釈入力の責任で、現在の実行を要求しない。'),
 'h26v7':('[a a d a d d] c',['principal','community','reference','method','start','end'],
  '同じ設定で発言可能性を判断する評価対象の結果。通常の運用上の背景と選択規則を結果から独立に固定し、許可や平穏に失敗する結果を見て除かない。非空・想定結果への包含・全選択結果での目標達成は既存xa/xdで確認し、全異常事態や全未来への絶対保証へ拡げない。'),
}
MEANINGS={
 'r6fv':'同じ発話・実行者・宛先・内容の出所について、第一の閉じた発話族と第二の発話族をともに提示し、第二を第一への対照的留保として提示する。同じ第一内容へこの発話で付す全留保の閉じた発話族を量化し、第二以外を置かない。nurをこの呼びかけ内での唯一の留保と読む。',
 'r6fw':'同じ人が同じ生起する発話を実行し、内容の出所principalの同じ基準の複数の全宛先へ、既存r2ugの話題・量の許可とr2uhの命令に従う履行を、r6fvの順序付きの唯一の留保として提示する。実行者と規範内容の出所を区別し、双方の内容・宛先は同じ出所・基準へ固定する。',
 'r6fx':'同じ人が同じ主体の発話を実行する立場として、その主体本人であるか、同じ主体・発話・基準・点への代表資格と制度的な行為帰属をともに持つ。個人の発言と代表者を介する公的主体の発言を同じ内容へ結び、無権限の代弁を通さない。',
 'r6fy':'同じ主体・発話・閉じた基準呼称について、同じ点にr6fwの発話内容とr6fxの本人又は代表者の位置を満たす人がある内容。発話内容の真理・許可の成立・服従の成功は発話したことから要求しない。',
 'r6fz':'同じ主体・基準について、r6fyを満たす発話がある内容。別々の発話で許可と留保を提示しただけの場合とは分け、特定の発話行為の唯一性は要求しない。',
 'r6f2':'同じ主体・共同体・基準で、r6fzの方針表明があり、その同じ全宛先が同じ共同体の成員で、同じ主体によるr2ueの許可方針と同じ共同体r572の平穏がその同じ点で成立する内容。政治的にこの方針を打ち出せるという可能性の目標であり、実際の服従は加えない。',
 'r6f3':'同じ主体・共同体・基準呼称・開始点について、公式の方針表明の利用可能な方法があり、その非空の全選択結果でr6f2の同じ発話・許可・平穏が成立するという既存xdの能力。引用内の命令が発せられることとその履行を区別し、単なる発声能力や良い結果一例では政治的に言えるとしない。',
 'r6f4':'固定基準の閉じた呼称がその基準を指すことを確認し、同じ共同体のこの点でr6f3として方針を打ち出せる全ての人に、同じ本人・点のr6fpの判断能力・恐れの不在・軍隊と平穏保証の人物条件を要求する内容。nur derjenigeの必要条件であり、逆向きの十分性や人物の実在を加えない。',
}
LIMITS=[
 'u0017第一文のräsonnirt ... nur gehorcht!とnur derjenige ... kann das sagenへの依存群。第五段落で確認したr2ug/r2uhの自由選択への許可と、同じ要求を指示として扱い履行する服従をそのまま用いる。引用内の出所・全宛先・基準を共通にし、前の段落の特定人物や刊行点を固定しない。',
 'nur gehorchtは、この自由な議論の呼びかけに付す留保として服従だけを挙げる読み。許可方針の真理条件に服従の現実の履行を加えず、全世界の他の義務や法規を廃止しない。同じ発話で同じ第一内容に付す留保を全記述域で量化する。記述はこの提示で用いる閉じた発話族として同定し、別構文を自動同義化しない。',
 '集団的な公的主体が言う場合は、同じ人の実行・同じ内容とともに、同じ発話への代表資格と制度的帰属を確認する。国民全員の合唱や最高役職保持者本人による発声を必須にせず、資格を持つ代表者を許す。代表資格から当の方針の政治的な妥当性や許容を導かない。',
 'kann das sagenは、この文脈では公式にこの方針を打ち出し、その許可と公的平穏を両立できるという政治的・実践的な能力として読む。文字列を声にできるだけの能力へ縮めない。基準点の能力の内側に同じ結果での許可と平穏を置き、現実に既に発言したことや国民全員が服従したことを外側の前提にしない。',
 'この能力の方法・結果範囲は通常の実践的な文脈で固定する。全結果への質的な保証という既存xdの読みを採り、成功確率や効用の数値を補わない。r6fpの軍隊条件を能力の定義に入れて必要条件を自明にすることはせず、能力と必要人物条件を別に構成する。',
 '全ての人を量化する必要条件は、能力があれば人物条件を要する向きだけである。能力のある者の存在、人物条件を満たせば必ず言えるという十分条件、国家が人間個人であることは追加しない。自由国のr6fuは後続の集団主体側の対比へ渡す。',
 '留保の網羅性と既存服従の要求網羅性には全記述域量化が残る。引用は実行せず、有限診断では実際の束縛本体を少数の記述へ適用したコピーだけを評価する。有限例を全域の検証とはしない。',
 '自由国のnicht wagen darf、危険の認識と試みの非許可基準、影の比喩・selbst・Aber/auch/zugleich aber、同じ引用への照応と全文帰属・通読は未統合。本文119主張・登録簿v203・19全単位判断と確認文字数を保持する。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    common='call a performer a recipient a principal a';args='v call v performer v recipient v principal'
    text='d r6fv['+common+' first '+MESSAGE+' second '+MESSAGE+' point d] c['+both(
      'k h234g[v call v recipient v principal v first v point]','k h234g[v call v recipient v principal v second v point]',
      'k h234h['+args+' v first v second v point]',
      'f alternative '+MESSAGE+'[y[k h234h['+args+' v first v alternative v point]][e[v alternative][v second]]]')+'].\n'
    first='o a[r b[p r2ug]][v reference]';second='o a[r b[p r2uh]][v reference]'
    selected='k h233p[v principal s[v reference] v recipient]'
    plural='g first a[g second a['+both('u[e[v first][v second]]','k h233p[v principal s[v reference] v first]','k h233p[v principal s[v reference] v second]')+']]'
    text+='d r6fw[performer a principal a call a reference i[d] point d] c['+both('k aa[v performer]','k dg[v call v point]','k f3[v performer v call v point]',plural,
      'f recipient a[y['+selected+']['+both('k aa[v recipient]','k r6fv[v call v performer v recipient v principal '+first+' '+second+' v point]')+']]')+'].\n'
    delegated=both('k h26v3[v performer v principal v call v reference v point]','k h26v4[v call v principal v reference v point]')
    text+='d r6fx[performer a principal a call a reference d point d] c['+both('k aa[v performer]','x[e[v performer][v principal]]['+delegated+']')+'].\n'
    text+='d r6fy[principal a call a reference i[d]] e[b point[g performer a['+both('k r6fw[v performer v principal v call v reference v point]',
      'k r6fx[v performer v principal v call s[v reference] v point]')+']]].\n'
    text+='d r6fz[principal a reference i[d]] e[b point[g call a[t[k r6fy[v principal v call v reference]][v point]]]].\n'
    text+='d r6f2[principal a community a reference i[d]] e[b point['+both('t[k r6fz[v principal v reference]][v point]',
      'f recipient a[y['+selected+'][k h237c[v recipient v community s[v reference]]]]',
      't[k r2ue[v principal s[v reference]]][v point]','t[k r572[v community s[v reference]]][v point]')+']].\n'
    providers=' '.join('i[actor a method a start d'+(' end d' if n!='h26v5' else '')+'][k '+n+'[v actor v community s[v reference] v method v start'+(' v end' if n!='h26v5' else '')+']]' for n in ('h26v5','h26v6','h26v7'))
    text+='d r6f3[principal a community a reference i[d] start d] c[k xd[v principal k r6f2[v principal v community v reference] v start '+providers+']].\n'
    name='k h223h[v reference]'
    implication='y[k aa[v person]][y[k r6f3[v person v community '+name+' v point]][t[c[k r6fp[v topic v community v reference]][v person]][v point]]]'
    text+='d r6f4[topic a community a reference d] e[b point['+both('e[s['+name+']][v reference]','f person a['+implication+']')+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,rs in zip(sources,ROOTS):
        for d in closure(source.document,rs):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(imported)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(s.source_sha256 for s in sources))
    basis=dict(status='same_official_quoted_policy_political_ability_and_necessary_person_conditions_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
