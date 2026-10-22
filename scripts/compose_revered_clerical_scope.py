"""Compose worthy regard and the same qualified ruler's jurisdiction."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_prince_sentence import ANCHOR

PARENTS=('data/clerical-duty-scope-basis-v1.json','data/prince-sentence-basis-v1.json')
LIBRARY='examples/v016/revered-clerical-scope.noema';BASIS='data/revered-clerical-scope-basis-v1.json'
GROUND='i b[h[a] e]';RESPONSE='i b[h[a a] e]';STANDARD='h[a '+RESPONSE+' '+GROUND+'] e'
PRIMITIVES={
 'h26o5':('[a '+RESPONSE+' '+GROUND+' d] j['+STANDARD+']',['subject','response','ground','reference'],
   '同じ対象者・二人間の応答状態記述・根拠性質記述・固定基準について、その対象者がその応答に値するかを評価する全適用基準のNoema関数列。各関数は対象者と同じ二記述を受け状況ごとの適合内容を返す。原文に特定の倫理学説を補わず明示した評価枠に固定し、結果を見て不適合基準を落とさない。全範囲と採用根拠は解釈入力の契約であり、有限例や常時真の検査値から正当性を認定しない。空・未知の列を適合として補わず、根拠の成立・非空性・全基準充足は合成側で確認する。'),
}
MEANINGS={
 'r54q':'同じ職務・教会・固定基準における聖職者r35mの人物性質。応答評価の根拠として本人を引数に取り、固定した分類を外側の評価点で変更しない。',
 'r54r':'同じ職務・教会・基準の閉じた名前をr54qへ適用する、段階1の人物性質記述。敬意の対象を同じ聖職者として捉えるために用い、実在や適合評価を構築時に実行しない。',
 'r54s':'同じ根拠性質の下で、第一の人が第二の人を肯定的に受け止め価値を認め、軽んじず敬意を保つh26nuの態度を持つ内容。実際の発話・服従・返礼・親密さは加えない。',
 'r54t':'r54sへ同じ根拠記述そのものの引用を適用する、二人間の敬意の状態記述。行為を捏造して三引数の称揚行為へ変換せず、構築時には態度を実行しない。',
 'r54u':'同じ対象者について根拠性質が成立し、非空の全適用基準が同じ対象・応答状態記述・根拠記述に適合する。ro5/r52kと同じ値する評価の構造を、行為でない二人間の応答状態へ保つ。実際の態度・発話・義務は導かない。',
 'r54v':'職務・教会・基準の呼称を元の設定へ照合し、r54rの同じ聖職者としての根拠とr54tの敬意状態をr54uへ渡す。全適合基準は同じ二記述・対象者・基準のh26o5から取得する。',
 'r54w':'同じ本人が、同じ君主r5xhが保持する同じ統治職・共同体・評価点の管轄に服するh26hiの制度上の立場にある。別の君主・共同体への服属、単なる滞在、命令への実際の服従で補わない。',
 'r54x':'先行第一文のr53bに同じ君主・統治職・共同体を渡し、その同じ本文の現在点で、同じ人がr54wによりその君主の下にあることを結ぶ。特定の実在王や別の限定条件を導入しない。',
 'r54y':'同じ聖職者・職務・教会・信条・宗教主題・学識者のr54nに、r54vの同じ聖職者としての敬意に値する評価を合わせる。採用した限定的読みに対応し、実際に敬われている者だけへ限定しない。',
 'r54z':'r54xの先行文と同じ限定君主の下にある本人と、r54yの同じ職務・教会における敬意評価を、先行文と同じ現在点で共有する。後続の一般許可の対象条件として用い、条件だけから許可・義務履行・発表を導かない。',
}
LIMITS=[
 'u0015第二文のUnter ihmとverehrungswürdige Geistlicheに向けた範囲接続。全発表候補への自由、無制約の他者、noch mehr、文全体の帰属は未統合で、意味確認文字数は増やさない。',
 'Unter ihmは先行文の条件を満たす同じ一般的君主の統治下という読み。r53bの人物・統治職・共同体と同じ現在点を共有し、別の君主・特定のフリードリヒの実在・独立した同じ王の選択を追加しない。',
 'verehrungswürdigは、この文では聖職者として敬意に値するという評価による限定として読む。単なる慣習的敬称、実際の人気、敬意の態度の現実の存在だけでは代用しない。評価されない他の人への許可を否定せず、唯一の歴史語用解釈と主張しない。',
 '敬意に値することは、同じ聖職者の性質が実際に成立し、その性質の下での肯定的承認・敬意という状態に非空の全評価基準が適合することとして構成する。原文に個別の功績・教説の真理・内心の信仰を捏造せず、適合基準の正しさそのものを有限検査で証明しない。',
 '敬意の保持は二人間の態度であり、既存の称揚行為に架空の活動引数を足して合わせない。h26nuを再利用し、値する評価は真の根拠・非空の全基準という既存構造を同じ二人間の状態記述へ移す。',
 '根拠性質の名前の一致、根拠の真理、評価基準の適合、敬意の実際の保持を別々に扱う。偽の根拠や空基準を値する評価とせず、応答記述を評価の途中で実行しない。',
 '限定君主の条件は先行文の同じr53bを再利用する。先行文は他の高い内容と合わせ段階7で談話提示しているが、この対象条件自体は最小段階2で引用でき、段階7への持上げも可能である。本文の現在点と深い先行条件の実評価証拠は保持し、今回の接続検査は同じ三対象の境界を明示する。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    text='d r54q[office a church a reference d] h[a] e[i[person a][b point[k r35m[v person v office v church v reference]]]].\n'
    text+='d r54r[office i[a] church i[a] reference i[d]] '+GROUND+'[o a[r b[p r54q]][v office v church v reference]].\n'
    text+='d r54s[ground '+GROUND+'] h[a a] e[i[holder a person a][b point['+both('k aa[v holder]','k aa[v person]','k h26nu[v holder v person v ground v point]')+']]].\n'
    text+='d r54t[ground i b['+GROUND+']] '+RESPONSE+'[o a[r b[p r54s]][v ground]].\n'
    criterion='t[c[v standard][v person v response v ground]][v point]'
    allfit='q[v standards]['+TRUE+'][i[prior c standard '+STANDARD+']['+both('v prior',criterion)+']]'
    text+='d r54u[person a response '+RESPONSE+' ground '+GROUND+' standards j['+STANDARD+'] point d] c['+both(
        't[c[s[v ground]][v person]][v point]','u[e[d[v standards]][n p a b]]',allfit)+'].\n'
    ground='k r54r[k h223g[v office] k h223g[v church] k h223h[v reference]]';response='k r54t[o r['+ground+']]'
    valid=both('e[s[k h223g[v office]]][v office]','e[s[k h223g[v church]]][v church]','e[s[k h223h[v reference]]][v reference]')
    text+='d r54v[person a office a church a reference d point d] c['+both(valid,
        'k r54u[v person '+response+' '+ground+' k h26o5[v person '+response+' '+ground+' v reference] v point]')+'].\n'
    text+='d r54w[ruler a rulingoffice a community a person a point d] c['+both('k aa[v person]',
        'k r5xh[v ruler v rulingoffice v community v point]','k h26hi[v person v rulingoffice v community v point]')+'].\n'
    text+='d r54x[ruler a rulingoffice a community a person a] c['+both(
        't[c[k r53b[]][v ruler v rulingoffice v community]]['+ANCHOR+']',
        'k r54w[v ruler v rulingoffice v community v person '+ANCHOR+']')+'].\n'
    context='person a office a church a creed a subject a scholar a reference d point d'
    text+='d r54y['+context+'] c['+both('k r54n[v person v office v church v creed v subject v scholar v reference v point]',
        'k r54v[v person v office v church v reference v point]')+'].\n'
    text+='d r54z[ruler a rulingoffice a community a person a office a church a creed a subject a scholar a reference d] c['+both(
        'k r54x[v ruler v rulingoffice v community v person]',
        'k r54y[v person v office v church v creed v subject v scholar v reference '+ANCHOR+']')+'].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for c,roots in zip(sources,(['r54n'],['h26nu','h223g','h223h','r5xh','h26hi','r53b','h26kn','h26km'])):
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
    basis=dict(status='same_qualified_ruler_and_worthy_clerical_regard_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
