"""Separate non-expectation, counter-expectation and almost-all judgments."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/qualified-speech-sentence-basis-v1.json'
LIBRARY='examples/v016/counterexpected-affairs.noema';BASIS='data/counterexpected-affairs-basis-v1.json'
PC='i b[e]';ORDER='h[a '+PC+' '+PC+' d] c';CANDIDATES='h[a '+PC+' d d] c'
PRIMITIVES={
 'h26xm':('[a a d a d] c',['course','observer','reference','aspect','point'],
  '同じ人間的な事柄の推移を同じ観点の人が同じ固定基準・点で考察するとき、評価対象となる事例・関係・展開の全範囲に属する一つの側面。全体的な見方を指定する側で対象と区切りを先に固定し、逆説的かどうかや期待の成否によって除外しない。全宇宙の物体でも、成功例だけの標本でもない。人間的推移・全体的な考察の内容自体は後続で別に結ぶ。'),
 'h26xn':('[a a d] '+PC,['course','aspect','reference'],
  '同じ推移の同じ側面について、何がどのように成り立つかを具体的に記述した閉じた段階1内容。名前の綴りや「逆説的」というラベルを内容にせず、主体・事柄・条件関係を合成したNoema内容へ対応させる。観察者の好みで内容を替えない。現在の真理・期待や意外性は別に検査する。'),
 'h26xo':('[a d a '+PC+' d d] c',['course','reference','observer','claim','point','alternative'],
  '同じ推移・固定基準・人の観点で、同じ閉じた内容を考える際、この点で通常の予測として積極的に採用する標準的な成り行きの候補。単に否定しきれない可能性や稀な例外まで集めた集合ではない。内容の結果や望ましさを見て選別せず、通常の前提と利用できる情報に基づいて予測に採用する範囲を評価前に固定する。実際の未来・全論理的可能性・数値確率ではなく、空又は未評価の範囲から非期待を認定しない。'),
 'h26xp':('[a d a '+PC+' '+PC+' d] c',['course','reference','observer','first','second','point'],
  '同じ推移・固定基準・人の観点・点で、第一の内容が第二の内容と少なくとも同程度に見込まれるという通常の見込み比較。既存hzptと同じ弱い比較を文脈へ固定し、内容の真理、形式的含意や因果とは分ける。自己比較と推移性、同順位と比較不能はrqtsが検査する。未知入力を比較不能へ補わない。'),
 'h26xq':('[a a d d] j[a]',['course','observer','reference','point'],
  '同じ推移・人の観点・固定基準・点で、h26xmの全評価対象を一度ずつ挙げる有限の列。粒度と範囲を先に固定し、非逆説的な側面だけまとめたり、逆説的な側面だけ細分化したりしない。完全性・非空性・重複なしをrcmで確認する。無限の歴史全体を有限標本で推定した統計とはしない。'),
 'h26xr':('[a a d d] b',['course','observer','reference','point'],
  '同じ対象全体に対して、例外の比率を小さいとみなす文脈上の正の許容上限。結果を見る前に固定し、原文にない具体的な数値を著者の主張にしない。0より大きく1/2未満という最低限の整合性に加え、実際の小ささの適切さは公開する解釈入力の責任である。等重みの側面数による読みを採り、頻度・重要度で重み付けした測度とは区別する。'),
 'h26xs':('[a a d d] c',['observer','framework','reference','point'],
  'この人の観点で同じ基準・点において、出来事や関係を通常理解するために使い慣れている説明の枠組み。単に知っている語句、どこかに存在する理論や他人だけの知識と分ける。歴史上の著者個人の伝記的な心情を自動推定せず、記述で採る観点に帰属する。'),
 'h26xt':('[a '+PC+' d d] c',['framework','claim','reference','point'],
  '同じ基準・点で、この説明枠組みをその基本的な見方の修正なしに適用すれば、指定された同じ内容をその成り立ちが理解できる事柄として無理なく説明できる。単なる形式的無矛盾、内容への賛成、好悪、真理や将来の新理論による説明可能性とは分ける。説明の適合性は明示した解釈入力であり、未評価を不適合にしない。'),
}
MEANINGS={
 'r6go':'同じ内容・観点・評価点で積極的に採用する通常予測の標準候補が非空で、その全てで内容が成立するという期待。あらゆる例外可能性を排した確実性ではなく、通常の見通しに一貫して含まれることと読む。実際の真理や、可能性が一つあるだけの場合とは分ける。',
 'r6gp':'同じ通常予測の標準候補が非空であり、r6goの期待は成立しない。標準候補の少なくとも一つで内容が成立せず、一貫した肯定的な見通しとして採られていない読み。単に稀な例外が否定しきれない場合とは分け、否定を積極的に予想したことや数値的な低確率までは要求しない。',
 'r6gq':'閉じた段階1内容から、その同じ内容の否定を表す閉じた段階1記述を合成する。元内容の構成時の実行や、別の意味の反対語への置換をしない。',
 'r6gr':'同じ内容が評価点で成立し、同じ観点・点の整合する弱い見込み比較で、その否定より厳密に見込まれにくいことをrqtsで確認する。paradoxの反期待的な成立という読みの核であり、形式的矛盾・両側の真理・比較不能は要求しない。',
 'r6gs':'非空で重複のない指定範囲の正確な有限列について、指定性質を欠く対象が一つ以上あり、その数が文脈上の小さな許容比率と全数の積より少ない。許容比率は0より大きく1/2未満を要し、空・全件成立・過半数だけ・境界値を区別する。',
 'r6gt':'同じ人の観点・基準・点で、使い慣れた説明枠組みが少なくとも一つあり、そのいずれも同じ内容を基本的な見方の修正なしには無理なく説明できない。befremdlichを通常の理解の枠に収まりにくいと読む内容で、何も知らないことや説明の永遠の不可能性ではない。',
 'r6gu':'同じ人間の観点・推移・側面・固定基準・点について、その側面が評価範囲に属し、具体的内容が成立し、通常予測の標準候補に一貫して含まれる肯定的な見通しとしては採られず、使い慣れた理解の枠にも収まりにくいことを連言する。予期されなさと不可解さを同義として片方を落とさない。',
 'r6gv':'同じ人の観点・推移・基準・点で、評価対象となる全側面の具体的内容が成立することを要求し、その正確な有限列についてr6grの反期待性がr6gsとしてほとんど全てを占める。成り立たない内容を例外として混ぜず、範囲・粒度・比率を結果で変更しない。',
}
LIMITS=[
 'u0017第二文のbefremdlicher nicht erwarteterとfast alles paradoxに向けた依存群。nicht erwartetは通常の予測に一貫して含まれる肯定的な見通しとして採られていないこと、paradoxは成立する内容がその否定より見込まれにくいこと、befremdlichは馴染みの理解の枠に収まりにくいことと区別する。唯一の歴史的語義や心理学の必要十分条件は主張しない。',
 '通常予測として積極的に採用する標準候補を先に固定し、非期待ではその非空の範囲の一部で内容が成立しないことを確認する。稀な例外の可能性が一つ残るだけで非期待にはしない。全標準候補で否定される強い反対予想へも狭めず、空又は未知の想定を非期待へ読み替えない。確率の数値、未来に限定した予測や実際の驚きの感情は付け加えない。',
 '反期待性では既存rqtsの整合した弱い比較を用い、同順位や比較不能を厳密な反期待にしない。現に成立する内容を、その否定の記述と比較する。両方を同じ点で真にする論理矛盾とは異なる。',
 'fast allesは全てではないが例外がごく少ないという読みを採る。対象を有限の文脈上の全関連側面とし、等重みで数える。許容上限は固定した解釈入力で、単に過半数ならよいとせず、事後に分母・粒度・上限を変更しない。無限の歴史全体の測度や統計的な標本推論は構成していない。',
 '理解の枠組みへの適合は期待の成否から独立する。通常なら起こると予測できても説明しにくい場合、予測しなかったが馴染みの枠で説明できる場合を許す。枠組みが空の場合は不可解さを空虚に成立させない。',
 '同じ推移の各側面の閉じた内容はh26xnで供給するが、第一文r6gkとの対応、人間の事柄の推移の構成、im Großenの考察条件、manの量化、So/hier/so wie auch sonstの提示、全文帰属・通読は後続で結ぶ。この依存群だけで第二文の意味確認を増やさない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def definitions():
    fields='claim '+PC+' observer a anchor d candidates '+CANDIDATES
    selected='c[v candidates][v observer v claim v anchor v alternative]'
    nonempty='g alternative d['+selected+']'
    text='d r6go['+fields+'] c['+both(nonempty,'f alternative d[y['+selected+'][t[s[v claim]][v alternative]]]')+'].\n'
    text+='d r6gp['+fields+'] c['+both(nonempty,'u[k r6go[v claim v observer v anchor v candidates]]')+'].\n'
    text+='d r6gq[claim '+PC+'] '+PC+'[o a[r b[i[content e][b point[u[t[v content][v point]]]]]][v claim]].\n'
    text+='d r6gr[claim '+PC+' observer a anchor d ranking '+ORDER+'] c['+both('t[s[v claim]][v anchor]',
      't[k rqts[v claim l['+PC+'][k r6gq[v claim]] v observer v anchor v ranking]][v anchor]')+'].\n'
    deficit='k hf[v population i[item a][u[c[v property][v item]]]]'
    text+='d r6gs[population j[a] scope h[a] c property h[a] c tolerance b] c['+both('k rcm[v population v scope]',
      'k hc[n p a b v tolerance]','k hc[v tolerance n p b c]','k hc[n p a b '+deficit+']','k hc['+deficit+' k hb[v tolerance d[v population]]]')+'].\n'
    familiar='k h26xs[v observer v framework v reference v point]'
    text+='d r6gt[claim '+PC+' observer a reference d point d] c['+both('g framework a['+familiar+']',
      'f framework a[y['+familiar+'][u[k h26xt[v framework v claim v reference v point]]]]')+'].\n'
    fields='course a observer a reference d';args='v course v observer v reference';claim='k h26xn[v course v aspect v reference]'
    selected='k h26xm['+args+' v aspect v point]'
    candidates='i[observer a claim '+PC+' point d alternative d][k h26xo[v course v reference v observer v claim v point v alternative]]'
    ranking='i[observer a first '+PC+' second '+PC+' point d][k h26xp[v course v reference v observer v first v second v point]]'
    text+='d r6gu['+fields+' aspect a point d] c['+both('k aa[v observer]',selected,'t[s['+claim+']][v point]',
      'k r6gp['+claim+' v observer v point '+candidates+']','k r6gt['+claim+' v observer v reference v point]')+'].\n'
    text+='d r6gv['+fields+' point d] c['+both('k aa[v observer]','f aspect a[y['+selected+'][t[s['+claim+']][v point]]]',
      'k r6gs[k h26xq['+args+' v point] i[aspect a]['+selected+'] i[aspect a][k r6gr['+claim+' v observer v point '+ranking+']] k h26xr['+args+' v point]]')+'].\n'
    return text
def build():
    p=parent();doc=deepcopy(p.document);doc.update(declarations=closure(p.document,('rqts','rcm','hf','hb','hc','aa')),statements=[])
    imported={d['name']:p.entries[d['name']] for d in doc['declarations']}
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(p.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='nonexpectation_counterexpectation_and_almost_all_aspects_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(p.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
