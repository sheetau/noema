"""Bind religious matters and a fixed population-ratio attainment criterion."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_present_epoch_assessment import FRAME,ARGS
from scripts.compose_collective_attainment import STANDARD
from scripts.compose_topical_standing import ENABLING,EARGS

PARENTS=('data/judgment-performance-quality-basis-v1.json','data/present-epoch-assessment-basis-v1.json','data/royal-intervention-sentence-basis-v1.json')
LIBRARY='examples/v016/religious-collective-assessment.noema'
BASIS='data/religious-collective-assessment-basis-v1.json'
TOPIC='topic a anchor d standardcontext i[d]'
TARGS='v topic v anchor v standardcontext'
SOURCE=FRAME+' topic a standardcontext i[d]'
SARGS=ARGS+' v topic v standardcontext'
PRIMITIVES={
 'h26j7':('[a d] c',['topic','reference'],
   '同じ固定基準で、この領域は人間の生き方・義務・最終的な安寧や救済を、神聖なもの又は経験的生活を超える秩序との関係で理解する信念・教え・実践と、それらの吟味や共同の営みに関わる。教えへの賛否や不信もその対象についての検討に含める。特定の教会の組織運営だけ、教義の真理、本人の信仰、全人類に同一の教義があることを条件にしない。既存h245zの基礎教理より広く、h26g7の特定共同体への所属を必要としない領域指定。'),
 'h26ka':('[a a a d] c',['person','topic','matter','reference'],
   '同じ本人・主題・固定基準において、本人がその領域で理解し判断する能力を問われる事柄の全範囲に、この事柄が入る。身近な実践、教えの理解と吟味、共同の営み等の関連事項を含み、専門家の全知や全宗派の全命題の知識を課さない。結果を見る前に範囲を固定し、得意な事項・同意した教え・現に成功した判断だけへ縮めず、支援結果でも範囲を変えない。単に記号や原語の名前を付けた事項で内容を代用しない。'),
 'h26kb':('[a d] i[a]',['matter','reference'],
   '同じ固定基準の事柄を参照する閉じたNoema個体記述。主題や評価結果を変えて別の事項を指す記述へ置換しない。対象内容そのものの説明とは別の参照補助であり、呼出側hzviで実際の指示対象と照合する。'),
 'h26kc':('[a d] b',['group','reference'],
   '同じ固定集団と基準で、対象能力が人々全体を特徴付ける程度に行き渡ったと扱うため、能力分布を見る前に採る最小成員割合。有限な現在人口を等重みで扱う明示的な解釈の入力。有効域0より大かつ1以下は合成側で確認する。原文が具体値・過半数・全員一致を指定したとはせず、結果や判定時点に合わせて閾値を下げない。現実の調査値やカントが暗黙に使った唯一の数値の復元ではない。'),
}
MEANINGS={
 'r5s6':'人aaと宗教領域h26j7を保ち、h26kaの同じ本人・主題・固定基準の全事項を選ぶ。現在能力や信仰の有無による事後選別は行わない。',
 'r5s7':'同じ固定基準のh26kbから、事項別の閉じた参照を返す。能力の内容を実行せず、指示一致はhzviに委ねる。',
 'r5ta':'宗教的な事項範囲r5s6と同じ参照r5s7を、r5syの実際の適切さと安定性を含む能力評価へ接続する。条件h26j3/j4と通常比較h26j5/j6の明示的意味を保持する。',
 'r5tb':'r5taと同じ宗教的事項と基準にr5szの既有行使能力を接続する。宗教への同意や教会所属、全事柄の同時処理、無修飾能力を追加しない。',
 'r5tc':'r5taと同じ元の宗教的事項範囲を保ち、r5s2の全支援結果での能力評価を接続する。未評価を不能へ変換しない。',
 'r5td':'r5tcと同じ事項範囲・質・基準について、r5s3の一支援結果で同じ本人が能力状態へ置かれうることを返す。事柄ごとに別の支援結果を集めない。',
 'r5te':'指定集団の固定成員h246cと渡された対象者性質と列mpが、全個体についてちょうど一致し、全成員が人である。空と重複の拒否は割合検査pdと合わせて行う。',
 'r5tf':'同じ集団・基準の文脈閾値h26kcが0より大きく1以下の有理数である。全員一致の1も選択可能だが語義として固定しない。',
 'r5tg':'r5teの同じ完全人口とr5tfの固定閾値について、pdの非空・重複なし・正確な成員割合が閾値以上である。集団外の成功を除き、割合が増えたことで到達が失われない匿名な人数基準を構成する。',
 'r5th':'集団・固定基準を閉じ、r5tgを既存の集団到達の基準型へ渡す。呼び出しごとの評価点で人口や閾値を選び直さない。',
 'r5ti':'同じ現在人口・話者・時代について、宗教的な質付き活動r5taの全員の評価と、r5thの有効な割合基準をr5sdに接続する。',
 'r5tj':'r5tiと同じ現在・人口・宗教的事項・質・固定閾値について、r5tbの能力保有者が集団到達r5seを満たす。',
 'r5tk':'r5ti/jと同じ設定で、集団到達は偽だが同じ現在の具体的な進行内容は真であるというr5sgの対照を保持する。',
 'r5tl':'r5tiの有効な能力評価と集団基準の下でr5tjが偽であること。対象不在や評価不足を未到達として肯定しない。',
 'r5tm':'同じ現在点を固定したr5tjの到達内容を問う発話。原文の現在を外側の評価点に置換せず、実際の質問生起を補わない。',
 'r5tn':'r5tmと同じ設定でr5tkの未到達かつ進行内容を述べる発話。問いと回答を同じ宗教領域・質・人口・閾値へ結ぶ。',
}
LIMITS=[
 'u0014冒頭問答と第二文を、同じ現在人口・宗教的事項・質付き能力へ向けて接続する。後のin Religionsdingenを直前の時代評価の主題の明示と読む。AA VIII 41の宗教上の問題を主眼とする説明も補助にし、全ての知的分野を能力条件へ追加しない。',
 '宗教は特定教派の制度だけへ限定せず、信念・教え・実践とその吟味の領域とする。本人が信仰を持つことや特定の教義の真理は能力の要件ではない。必要な事項の内容は明示し、原語の綴りを内容として使わない。',
 'im Ganzen genommenの集団的判断を、有限な現在人口での等重みの普及割合と文脈的閾値で読む。一つの明示的形式化であり、社会的影響力による重み付けや制度の質そのものによる集団評価を唯一の誤りとはしない。原文に具体的な閾値はないので固定値を著者へ帰属しない。',
 '閾値は同じ集団・固定基準から与え、0より大かつ1以下とする。全員一致も特別な設定として表現できるが必須にしない。有限の小集団では閾値が1未満でも全員必要になる場合がある。匿名性・単調性は有効な正確割合と同じ閾値の下で成り立つ。',
 '空・重複・欠落・余分・別集団の列を拒否する。現在人口の完全性・話者の所属・時代の内点はr5scに保持する。評価対象の一部を分母から除いた標本割合へ変更しない。',
 'gut/sicherは前回の実際の条件充足・通常関連変化での安定性をそのまま採る。各課題の具体的な条件内容と比較範囲を与える責任は解釈に残る。条件例二つをあらゆる宗教的課題の全条件とはしない。',
 '進行内容は外から同じ現在点に結ぶが、次に機会開放・障害漸減等のNoema内容で閉じる。能力保有又は支援可能性だけを進行と同一視しない。',
 '条件付きの問い・denn/nun・Nein/aber wohl・著者帰属・第二文の甚だしい不足・第三文以降は未統合。本文108主張と全単位16区間を保ち、全体の意味確認文字数を加算しない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def definitions():
    text='d r5s6[person a topic a matter a reference d] c['+both('k aa[v person]','k h26j7[v topic v reference]','k h26ka[v person v topic v matter v reference]')+'].\n'
    text+='d r5s7[reference d] h[a] i[a][i[matter a][k h26kb[v matter v reference]]].\n'
    tail='v topic v anchor p r5s6 k r5s7[v anchor] v standardcontext'
    for n,target,support in (('r5ta','r5sy',False),('r5tb','r5sz',False),('r5tc','r5s2',True),('r5td','r5s3',True)):
        text+='d '+n+'['+TOPIC+(' '+ENABLING if support else '')+'] h[a] e[k '+target+'['+tail+(' '+EARGS if support else '')+']].\n'
    selected='c[v people][v person]'
    text+='d r5te[group a reference d people h[a] c] c[f person a['+both('z['+selected+'][k h246c[v group v person v reference]]','z['+selected+'][k hg[k mp[v group] v person]]','y['+selected+'][k aa[v person]]')+']].\n'
    threshold='k h26kc[v group v reference]'
    text+='d r5tf[group a reference d] c['+both('k hc[n p a b '+threshold+']','u[k hc[n p b b '+threshold+']]')+'].\n'
    fraction='k pd[k mp[v group] p aa i[person a]['+both(selected,'c[v reached][v person]')+'] i[ratio b][u[k hc[v ratio '+threshold+']]]]'
    text+='d r5tg[group a reference d people h[a] c reached h[a] c point d] c['+both('k r5te[v group v reference v people]','k r5tf[v group v reference]',fraction)+'].\n'
    text+='d r5th[group a reference d] '+STANDARD+'[i[people h[a] c reached h[a] c point d][k r5tg[v group v reference v people v reached v point]]].\n'
    checked='k r5ta[v topic v point v standardcontext]';capable='k r5tb[v topic v point v standardcontext]';standard='k r5th[v group v reference]'
    for n,target,tail in (('r5ti','r5sd',checked+' '+standard),('r5tj','r5se',checked+' '+standard+' '+capable),('r5tk','r5sg',checked+' '+standard+' '+capable+' v progress')):
        text+='d '+n+'['+SOURCE+(' progress e' if n=='r5tk' else '')+'] c[k '+target+'['+ARGS+' '+tail+']].\n'
    text+='d r5tl['+SOURCE+'] c['+both('k r5ti['+SARGS+']','u[k r5tj['+SARGS+']]')+'].\n'
    text+='d r5tm['+SOURCE+'] f[k rij[b outer[k r5tj['+SARGS+']] e[v speaker][v speaker]]].\n'
    text+='d r5tn['+SOURCE+' progress e] f[k rik[b outer[k r5tk['+SARGS+' v progress]] e[v speaker][v speaker]]].\n'
    return text
def build():
    libs=parents();all_entries={};merged=[]
    for lib in libs:
        for d in lib.document['declarations']:
            n=d['name']
            if n in all_entries:assert d==all_entries[n]['declaration'] and lib.entries[n]['meaning_ja']==all_entries[n]['meaning_ja'],n
            else:merged.append(d);all_entries[n]=lib.entries[n]
    doc=deepcopy(libs[0].document);doc.update(declarations=merged,statements=[])
    doc['declarations']=closure(doc,['r5sy','r5sz','r5s2','r5s3','r5sd','r5se','r5sg','mp','hg','pd','hc','rij','rik'])
    imported={d['name']:all_entries[d['name']] for d in doc['declarations']}
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(all_entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in libs))
    basis=dict(status='religious_scope_and_fixed_population_ratio_attainment_dependency',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
