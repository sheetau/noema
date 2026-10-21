"""Compose posterity's entitlement to repudiate the same adopted resolutions."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind
from scripts.compose_cohort_covenant_purpose import NAMES,FIELDS,ARGS,REF

PARENT='data/cohort-covenant-denial-basis-v1.json'
LIBRARY='examples/v016/posterity-repudiation.noema'
BASIS='data/posterity-repudiation-basis-v1.json'
TRIPLE='l[a][v person v agreement v resolution]'
PRIMITIVES={
 'h26bk':('[a a d] c',['agreement','resolution','reference'],'同じ合意とその固定した形成基準について、合意により採択され、後の人々の認識・行為を拘束するために定められた決定事項の全範囲にこの項目が含まれる。単なる会議の議題、文書の任意の一節、別の合意の決議と区別する。拒否されたもの・有効とされたものだけへ範囲を狭めず、項目の存在から正当性・効力・履行を導かない。仮定の合意についても同じ項目の同定を保つ。'),
 'h26bl':('[a a a d d] c',['person','agreement','resolution','reference','point'],'本人が同じ合意の同じ決定事項を、自分の判断・行為を規範的に拘束する根拠として、この評価点で受け入れている。単に文書を読んだこと、たまたま同じ行動をすること、命題が真だと思うこと、外から強制されていることと区別する。受容だけで決議の客観的な正当性・効力を認めない。'),
 'h26bm':('[] a',[],'後代に生きる人として、先行時代の決議を自分への拘束の根拠として受け入れるかを判断する立場。教会や国家の特定の職務、血縁上の相続資格、合意の署名者の立場ではない。役割の指定だけで許可や実際の拒否を導かない。'),
 'h26bn':('[a a a a d] c',['response','person','agreement','resolution','reference'],'この反応行為が、同じ本人について、同じ合意の同じ決定事項を拘束の根拠として受け入れるかという対象への応答として位置付く。行為の実行、受容・拒否の向き、決議の効力は別に確認する。無関係な拒否、別の決議への応答、単なる同時発生は該当しない。'),
}
MEANINGS={
 'r5dp':'本人・合意・決議の正確な三個体列から、固定基準h26avの下でその決議を本人への拘束の根拠として受け入れるh26blの内容を返す。拒否における負極性の実践方針の対象として引用でき、引用だけでは受容や決議の効力を肯定しない。',
 'r5dq':'同じ合意の固定形成基準で採択された同じ決議について、本人がその決議への応答h26bnとして同じ行為zzqを実行し、同じ三個体列の受容内容r5dpに対してh244jの負極性の実践方針を取る。単なる不服従・未達成・受容の不存在から拒否を導かない。',
 'r5dr':'正確な本人・合意・決議の三個体列から、r5dqを満たす拒否行為があるという内容を返す。規範的資格の対象は拒否という選択であり、あらゆる具体的な手段への許可や全ての反応の実行は要求しない。',
 'r5ds':'同じ固定範囲と候補経過の有効な時代区分r5bwにおいて、本人が指定点で生存する人であり、その点は非空の先行時代の全点より後である。血縁ではなく後代の人という対象範囲を構成し、直後の一時代だけに狭めない。先行時代にも生存していたことは排除しない。',
 'r5dt':'同じ人・合意・決議・評価点について、人間の進展を評価する同じ規範h26axから後代の人の立場h26bmに、r5drの拒否選択を積極的に許可し、反対要求と衝突しないrduの資格を与える。拒否行為や受容内容は実行しない。',
 'r5du':'同じ六対象の候補r5dcと非空の採択決議の全範囲を保持し、同じ全履歴の各点でr5dsに当たる後代の全人に、各決議についてr5dtの拒否資格がある。直後の集団だけ、賛同者だけ、拒否済みの決議だけへ範囲を縮めず、全員の同時の拒否・同一行為を要求しない。',
 'r5dv':'正確な六個体列からr5duの後代の拒否資格を返す内容族。前文の同じ合意・時代・状態を保ち、次の文の仮定と理由付けに接続するために引用できる。',
}
LIMITS=[
 'Nachkommenはここでは血縁上の子孫ではなく、先行時代の後に生きる人々として読む。直後の時代を含み、同じ全履歴のさらに後の時代も含める。後に生まれた人だけへの制限、全員の同時生存、先行時代との成員の完全な断絶は追加しない。',
 'jene Beschlüsseは同じ先行合意により採択された拘束の決定事項の全範囲を指す。一般的な複数形として、項目の非空性と全項目を要求し、原文にない固定個数・正確に二つという制限は加えない。具体的な決定の条項内容は先行する合意の構成に従う。',
 'verwerfenは同じ決議を自分への拘束の根拠として受け入れないという実践的な態度を、応答行為として取ること。無言の不履行や不能、他人の批判の引用、内心の未賛同だけで代用しない。拒否後の行動の成功、制度的な廃止、文書の破棄、暴力行為は含意しない。',
 'berechtigtは既存rduの、反対要求と衝突しない積極的許可として先の読解を保つ。個々の反応方法全部を許可するのではなく、拒否行為を取るという選択の内容を対象にする。反応の実行や決議の実際の効力は資格判定時に評価しない。',
 'r5du/r5dvは同じ合意を受ける資格内容の構成段階。Das wäreの仮定、Verbrechenと人間本性・本来的使命、geradeとalso、vollkommenの全面性、unbefugter/frevelhafterの二評価、著者帰属と全文の通読は次に接続する。本文100主張と確認済み文字数は変えない。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def definitions():
    accept='k h26bl[v person v agreement v resolution '+REF+' v point]'
    text='d r5dp[bindings j[a]] e[b point['+bind(('person','agreement','resolution'),accept)+']].\n'
    text+='d r5dq[person a agreement a resolution a response a point d] c['+both(
        'k h26bk[v agreement v resolution k h254z[v agreement]]',
        'k h26bn[v response v person v agreement v resolution '+REF+']',
        't[k zzq[v person v response]][v point]',
        'k h244j[v person v response r[p r5dp] '+TRIPLE+' '+FALSE+' v point]')+'].\n'
    text+='d r5dr[bindings j[a]] e[b point['+bind(('person','agreement','resolution'),
        'g response a[k r5dq[v person v agreement v resolution v response v point]]')+']].\n'
    epoch='k h26ab[v earlier '+REF+' v candidate v old]'
    text+='d r5ds[person a earlier a candidate d point d] c['+both('k r5bw['+REF+' v candidate]',
        'k h26aa[v earlier '+REF+']','k aa[v person]','k h257z['+REF+' v candidate v point]','k h256o[v person v candidate v point]',
        'g old d['+epoch+']','f old d[y['+epoch+'][k ic[v old v point v candidate]]]')+'].\n'
    valid='i[items j[a]][e[v items]['+TRIPLE+']]'
    text+='d r5dt[person a agreement a resolution a point d] c[k rdu[k h26ax[] v person k h26bm[] r[p r5dr] '+TRIPLE+' '+TRUE+' v point '+valid+' p h7k p h7l]].\n'
    decisions='k h26bk[v agreement v resolution k h254z[v agreement]]'
    rights='f point d[f person a[y[k r5ds[v person v earlier v candidate v point]][f resolution a[y['+decisions+'][k r5dt[v person v agreement v resolution v point]]]]]]'
    text+='d r5du['+FIELDS+' candidate d] c['+both('k r5dc['+ARGS+' v candidate]','g resolution a['+decisions+']',rights)+'].\n'
    text+='d r5dv[bindings j[a]] e[b candidate['+bind(NAMES,'k r5du['+ARGS+' v candidate]')+']].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(old.document,['r5dc','r5bw','zzq','h244j','rdu','h7k','h7l','h26ax']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='posterity_same_resolutions_repudiation_and_entitlement',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
