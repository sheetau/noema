"""Compose grounded correction of a false commitment within the same cohort."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/covenant-nullity-basis-v1.json'
EPOCH='data/epoch-undertakings-basis-v1.json'
LIBRARY='examples/v016/cognitive-correction.noema'
BASIS='data/cognitive-correction-basis-v1.json'
PRIMITIVES={
 'h26ad':('[a d] c',['item','scope'],'固定した認識上の対象範囲に、この認識内容の項目が属する。肯定される見解とその改訂を扱う全項目を与え、誤っている項目や訂正が成功した項目だけに絞らない。文・文書の数や表記の種類を認識の数としない。'),
 'h26ae':('[a d] e',['item','scope'],'同じ項目が同じ固定基準で表す命題内容。Noemaの内容として解釈し、原文の文字列や語の名前だけでは代用しない。時刻・指示対象・条件を基準で束縛し、前後比較の途中で「今」の指示や真偽の評価対象を変えない。否定的な判断の対象にも同じ内容を用いる。'),
 'h26af':('[a a d d] c',['person','item','scope','point'],'この時点でこの人は、同じ固定基準のこの項目の内容を、自らの見解として真と受け入れている。現在の受容の状態であり、発話したこと、引用・検討中の仮説、忘却した過去の受容、所属集団の公式見解だけではない。内容の真理や根拠は含めない。'),
 'h26ag':('[a d] a',['item','scope'],'固定基準の同じ認識内容・同じ対象・同じ条件を表す項目群の代表項目。表記や項目名だけを替えた別名は同じ代表へ結ぶ。代表自身も同じ範囲に属し自分へ写る。各別名のh26aeは代表と同じ内容を与える。同じ有限標本で真偽が一致するだけの異なる認識対象を一つに潰さず、訂正の結果に合わせて同一視を変えない。'),
}
MEANINGS={
 'r5cc':'同じ項目と固定基準から代表項目h26agを取り、その代表のh26aeの命題内容を返す。前後で同じ参照対象を評価し、別名での再受容を別内容として扱わない。',
 'r5cd':'同じ範囲の項目のうち、指定項目と同じ代表を持つ項目を、この本人が同じ時点で一つでも真と受け入れている。項目名の置換や元の項目の削除だけで受容が消えたとはしない。',
 'r5ce':'本人が人であり、対象項目が同じ固定範囲に属し、その内容をr5cdで受容している一方、固定した評価状況でr5ccの内容が偽である。偽の命題を引用しただけの場合と、真なる見解への撤回を誤りの除去から区別する。',
 'r5cf':'同じ本人が同じ代表項目のh26aeを否定する判断を行い、その同じ判断で用いた理由が判断を支える。yaとh245qを結び、単なる理由の存在、他人の判断、別内容への支持や無根拠な撤回を区別する。他者から学ぶ場合を除く自立性は追加しない。',
 'r5cg':'同じ候補の順序付けられた前後点に本人が生存し、前にr5ceの誤った受容があり、後には同じ内容の別名も含めて受容がない。間の同じ履歴の点で本人のr5cfの理由ある否定判断が行われる。固定した内容・範囲・真偽評価を保ち、単なる忘却や死亡、世界の変化だけでの真偽変化を訂正としない。',
 'r5ch':'同じ本人・固定範囲・評価状況・候補・前後点について、対象履歴がtaの厳密な全順序を持ち、少なくとも一項目のr5cgの訂正がある。他の全知識の保持、新しい誤りの全面的不在、全誤りの除去を追加しない。',
 'r5ci':'同じ候補での対象集団に属する人の少なくとも一人にr5chの訂正がある。後代の全員が同じ認識を持ち同時に訂正することを要求せず、集団外の人の改善や人口の入替えだけで代用しない。',
 'r5cj':'同じ集団・範囲・真偽評価・候補・開始点からr5ciの訂正を生む結果を目標としてrjbの成功可能性の不在を述べる。利用可能な各方法の結果は非空とし、一部でも成功する結果があれば不能にしない。単に現に訂正がないことや、成功保証がないこととは異なる。',
}
LIMITS=[
 'von Irrthümern zu reinigenを、同じ認識内容の誤った受容を、理由のある否定判断を経て撤回する認識上の訂正として構成する。真偽の評価状況を前後で固定する。誤りの除去を単なる項目数の減少や忘却・死亡へ置換しない。',
 '一項目の訂正を許し、全ての正しい知識の無損失や新しい誤りの全面的不在を要求する旧ri6は使用しない。この条件は集団全体の正味の改善量ではなく、少なくとも一人の一つの訂正である。他の箇所で悪化があっても、この局所的な訂正の存在を取り消さない。',
 '別名は同じ固定された代表項目を用いる。代表の所属と冪等性、別名の同内容、認識の区別を保った範囲の網羅は入力の意味規約であり、有限の真理値一致から自動生成しない。原文の語を項目名として宣言するだけで内容を説明したことにはしない。',
 '訂正に用いた理由の支持は既存fdで明示し、使用fcから推定しない。全ての認識論を定義したものではない。知識一般の十分条件や、新しい内容・根拠・理解の獲得はこの誤り訂正とは別に構成する。',
 '集団の認識上の改訂を、その同じ集団に属する生存者の訂正として読む。全員の一致や集団の単一精神を仮定せず、個人の死や次の出生だけで改訂と数えない。各項目を公刊済み文書へ限定しない。',
 'r5cjへ渡す利用可能な方法は、その集団の構成員が個別に又は共同で取り得る学習・検討・改訂の全範囲とその結果を含む。集団の公式な共同決定だけへ狭めない。未知の方法・結果・受容・理由・真偽を空集合や偽へ補わない。',
 '現在の合意が後続集団をこの不能性へ置く目的、その状態の必然性、知識の拡大・啓蒙の進展の不能性、kann nichtの規範的否認、重要性・総括・共謀的提示・全文帰属はまだ接続しない。確認済み文字数を増やさない。',
]

@lru_cache(None)
def parents():return load_catalog(ROOT,PARENT),load_catalog(ROOT,EPOCH)

def definitions():
    text='d r5cc[item a scope d] e[k h26ae[k h26ag[v item v scope] v scope]].\n'
    same='e[k h26ag[v alias v scope]][k h26ag[v item v scope]]'
    text+='d r5cd[person a item a scope d point d] c[g alias a['+both('k h26ad[v alias v scope]',same,'k h26af[v person v alias v scope v point]')+']].\n'
    text+='d r5ce[person a item a scope d assessment d point d] c['+both('k aa[v person]','k h26ad[v item v scope]','k r5cd[v person v item v scope v point]','u[t[k r5cc[v item v scope]][v assessment]]')+'].\n'
    negative='i[judgment a matter a at d][k h245q[v judgment v matter r[p h26ae] v scope u[e[v person][v person]] v at]]'
    text+='d r5cf[person a item a scope d point d] c[t[k ya[v person k h26ag[v item v scope] p fa '+negative+' p fc p fd]][v point]].\n'
    fields='person a item a scope d assessment d candidate d first d last d'
    correction='g at d['+both('k h257z[v scope v candidate v at]','k ic[v first v at v candidate]',
        'x[e[v at][v last]][k ic[v at v last v candidate]]','k h256o[v person v candidate v at]','k r5cf[v person v item v scope v at]')+']'
    text+='d r5cg['+fields+'] c['+both('k h257z[v scope v candidate v first]','k h257z[v scope v candidate v last]',
        'k ic[v first v last v candidate]','k h256o[v person v candidate v first]','k h256o[v person v candidate v last]',
        'k r5ce[v person v item v scope v assessment v first]','u[k r5cd[v person v item v scope v last]]',correction)+'].\n'
    timeline='k ta[i[at d][k h257z[v scope v candidate v at]] i[before d after d][k ic[v before v after v candidate]]]'
    text+='d r5ch[person a scope d assessment d candidate d first d last d] c['+both(timeline,'g item a[k r5cg[v person v item v scope v assessment v candidate v first v last]]')+'].\n'
    group='group a scope d assessment d candidate d first d'
    text+='d r5ci['+group+' last d] c[g person a['+both('k h246c[v group v person v candidate]','k r5ch[v person v scope v assessment v candidate v first v last]')+']].\n'
    goal='b last[k r5ci[v group v scope v assessment v candidate v first v last]]'
    text+='d r5cj['+group+' available h[a a d] c outcomes h[a a d d] c] c[k rjb[v group '+goal+' v first v available v outcomes]].\n'
    return text

def build():
    old,epoch=parents();doc=deepcopy(old.document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in ((old,['ya','rjb','ta','h245q','aa','h256o','h246c','ic','fa','fc','fd']),(epoch,['h257z'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(epoch.entries))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    sources=set(old.source_sha256)|set(epoch.source_sha256)
    basis=dict(status='grounded_individual_correction_within_fixed_cohort',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
