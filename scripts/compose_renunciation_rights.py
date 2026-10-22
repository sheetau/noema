"""Compose personal/posterity renunciation and the same protected rights."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind

PARENTS=('data/limited-personal-deferral-basis-v1.json','data/personal-enlightenment-choice-basis-v1.json','data/fixed-compact-sentence-basis-v1.json')
LIBRARY='examples/v016/renunciation-rights.noema'
BASIS='data/renunciation-rights-basis-v1.json'
NAMES=('actor','response','earlier','posterity')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
FOUR='l[a]['+ARGS+']'
TWO='l[a][v actor v response]'
FIVE='l[a]['+ARGS+' v period]'
SOURCE='k h26ax[]';ROLE='k h26fz[]';REF='k h26f2[]'
ANCHOR='k h26fw[v response v reference]'
PRIMITIVES={
 'h26f3':('[i[h[j[a] d] e] j[a] d d] c',['conduct','bindings','reference','candidate'],'閉じた行為内容族へ同じ対象列・固定基準を適用する企てを検討する、相互に矛盾しない仮定経過の完全な範囲。行為の実行、方針採用、許可、侵害評価、成功を先に要求して候補を選別しない。履歴と対象者の構成は別に検査し、引用した企てをこの範囲指定だけで実行しない。'),
 'h26f4':('[a a a i[h[a d d] e] d] c',['source','rights','holder','development','reference'],'同じ規範出所・固定基準で、指定した担い手に帰属する、閉じた変化内容関数で示した展開を妨げられずに追求し得る条件と機会への正当な請求の全体が、この権利集合である。対象となる関連権利の全体を指し、侵害評価が成立する一部だけを後から選ばない。単なる利益・願望・実際の能力・任意行為への許可と区別する。特定法制度での制定・実現や、引用した展開の成功は要求しない。'),
 'h26f5':('[a a d] c',['rights','source','reference'],'同じ規範出所・固定基準で、この権利集合は任意の都合や取引で顧みなくしてよいものではなく、侵してはならない尊重の対象として位置付く。神聖という規範的な読みであり、神による授与、宗教儀礼、事実上侵害できないことを加えない。個別行為の侵害評価は別に結ぶ。'),
}
MEANINGS={
 'r5lb':'同じ人・応答の固定選択点が同じ先行時代内にあり、r5jzの完全かつ非空な後代集団を結ぶ。合意専用の形成点へ取り替えず、直後の一世代や血縁に限らない。',
 'r5lc':'r5lbの全後代成員について、同じ啓蒙規範h26axと個人の立場h26fzで、知るべき全事項と自己判断対象の対応r5knを要求する。未対応の成員を落とさない。',
 'r5ld':'正確な主体・応答・先行時代・後代集団の四対象列から、完全な後代集団の誰かが、その先行時代後の生存点で同じ義務事項への探究r5kqを行うという継続内容。これを負極性で選ぶと後代の継続全体を退ける方針になる。単に現在の主体が活動しないことにはしない。',
 'r5le':'同じ四対象と期間の正確な五対象列から、同じ選択点に始まる有界期間の終了以後に、同じ後代成員の探究継続がある内容。終了点を含み、後代である時点条件も保持する。',
 'r5lf':'r5lcを保ち、主体が同じ固定選択点で実行する同じ応答において、後代の継続r5ldを負極性の方針として採用する。逆向きの同時採用と、いずれかの期間後のr5leへの再開方針を拒む。後代の同意・実際の服従や、正当な代理権を要求も導出もしない。',
 'r5lg':'主体・応答の正確な二対象列と固定基準から、同じ主体自身のr5kvの放棄を返す。規範h26axと個人の立場h26fzを固定する。',
 'r5lh':'正確な四対象列と固定基準から同じr5lfの後代についての放棄を返す。現在の主体と将来の対象者を取り違えない。',
 'r5li':'本人の放棄r5lgを第九文の固定基準h26f2へ閉じた一引数の内容族。既存の侵害評価h26bt/h26bvが引用できるようにする。',
 'r5lj':'後代についての放棄r5lhを同じh26f2へ閉じた一引数の内容族。本人の放棄と同じ規範評価形式へ接続する。',
 'r5lk':'指定集団の前後点から、固定基準h26f2・固定真偽評価h26arの下で認識獲得・訂正・理由ある自己判断の少なくとも一つが進むr5csを返す。権利が関わる啓蒙進展を前段と同じ三つの選言で指定する。',
 'r5ll':'同じh26axから通時的人類h256mに帰属する、r5lkの展開を追求する条件と機会への全関連権利h26f4が、侵してはならない尊重の対象h26f5である。特定の現国家の権利や個人の好みへ替えない。',
 'r5lm':'同じ権利集合・本人・応答について、固定基準での本人の放棄r5liを重大な侵害h26btかつ意図的で不遜な軽視h26bvとして評価する。評価から行為実行や将来の成功を導かない。',
 'r5ln':'同じ権利集合・主体・応答・先行時代・後代集団について、同じr5ljの放棄を同じ二評価へ結ぶ。別の後代集団や別の行為の侵害を借りない。',
 'r5lo':'第九文の固定基準で、同じ全関連権利r5llについて、本人と後代の両方の全候補範囲で、それぞれの放棄が実行されるなら同じ二評価があるという内容。権利の存在は放棄の実例がない場合も保持し、本人の場合だけ又は後代の場合だけへ縮めない。',
}
LIMITS=[
 '第九文後半の本人と後世についての放棄を共通の権利評価へ接続する依存群。本人の放棄は既存r5kvを再利用し、後代については同じ実践的な方針採用を、後代全体の継続内容へ適用する。将来の全員が実際に方針へ従うことや、現在の主体に正当な代理権があることは加えない。',
 'Nachkommenschaftは、同じ選択点が属する先行時代の後に生存する人々の完全な非空の集団。先行時代からの生存者とさらに遠い後代を含む。先行時代内だけの活動や、単に選択点より後というだけの同時代の活動を後世の継続として数えない。時代区分は固定入力であり、終了時代を都合よく移さない。',
 '否定する継続内容は、後代の誰かがその後代の生存点に探究を行うという存在命題である。その負極性の方針採用として全体の放棄を読む。全員が成功しないこと、ある一人の不成功、一時的な中断へ弱めない。引用内容の真偽は方針採用の外側では評価しない。',
 '人類の権利は、この文脈で啓蒙の進展を追求する条件と機会への全関連請求と読む。進展は前段で構成した認識獲得・訂正・理由ある自己判断の選言。Rechteの複数を任意の一件だけへ縮めず、全関連権利の集合を固定する。この明示した読みを、現代の全人権一覧や唯一の歴史解釈の証明とはしない。',
 'heiligは侵してはならない尊重の対象という規範的な読み。verletzenは同じ放棄への重大な侵害評価、mit Füßen tretenの評価面は不遜な軽視として保持する。身体的な足による踏みつけの見立ての提示、mehr nochの増幅、zwar/aberの対照、全文の帰属は統合時に別に接続する。',
 'heißtは、この範囲の放棄に同じ侵害・軽視の評価を与える意味上の性格づけと読む。あらゆる権利侵害から放棄を逆推論する双条件や、現実に放棄が行われたという断言にはしない。全候補は行為実行・侵害評価で先に選別しない。',
 '有限検査は時代・成員・方針・評価の接続と反例を扱う。全人類と無限未来の網羅性、規範の客観的妥当性はそれだけでは証明しない。第九文の全文判断は未完で、本文104主張と意味確認済み文字数を保持する。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    member='k h246c[v posterity v person v reference]'
    frame=both('k aa[v actor]','k r5jz[v posterity v earlier v reference v candidate]',
        'k h26ab[v earlier v reference v candidate '+ANCHOR+']')
    text='d r5lb['+FIELDS+' reference d candidate d] c['+frame+'].\n'
    base='k r5lb['+ARGS+' v reference v candidate]'
    duties='f person a[y['+member+'][k r5kn['+SOURCE+' v person '+ROLE+' v reference]]]'
    text+='d r5lc['+FIELDS+' reference d candidate d] c['+both(base,duties)+'].\n'
    inquiry='g activity a[g topic a[k r5kq['+SOURCE+' v person '+ROLE+' v activity v topic v reference v candidate v point]]]'
    future=both(member,'k r5jy[v person v earlier v reference v candidate v point]',inquiry)
    text+='d r5ld[bindings j[a] reference d] e[b candidate['+bind(NAMES,both(base,'g person a[g point d['+future+']]'))+']].\n'
    after=both(future,'x[e[v end][v point]][k ic[v end v point v candidate]]')
    resumed='g end d['+both('k r5jd[v period v reference v candidate '+ANCHOR+' v end]',
        'g person a[g point d['+after+']]')+']'
    text+='d r5le[bindings j[a] reference d] e[b candidate['+bind((*NAMES,'period'),both(base,resumed))+']].\n'
    def policy(target,bindings,sign):return 'k h26ft[v actor v response r[p '+target+'] '+bindings+' v reference '+sign+' '+ANCHOR+']'
    chosen=both('k r5lc['+ARGS+' v reference v candidate]','t[k zzq[v actor v response]]['+ANCHOR+']',
        policy('r5ld',FOUR,FALSE),'u['+policy('r5ld',FOUR,TRUE)+']','f period a[u['+policy('r5le',FIVE,TRUE)+']]')
    text+='d r5lf['+FIELDS+' reference d candidate d] c['+chosen+'].\n'
    text+='d r5lg[bindings j[a] reference d] e[b candidate['+bind(NAMES[:2],'k r5kv['+SOURCE+' v actor '+ROLE+' v response v reference v candidate]')+']].\n'
    text+='d r5lh[bindings j[a] reference d] e[b candidate['+bind(NAMES,'k r5lf['+ARGS+' v reference v candidate]')+']].\n'
    for n,target in (('r5li','r5lg'),('r5lj','r5lh')):
        text+='d '+n+'[bindings j[a]] e[k '+target+'[v bindings '+REF+']].\n'
    text+='d r5lk[group a first d last d] e[b candidate[k r5cs[v group '+REF+' k h26ar['+REF+'] v candidate v first v last]]].\n'
    text+='d r5ll[rights a] c['+both('k h26f4['+SOURCE+' v rights k h256m[] r[p r5lk] '+REF+']','k h26f5[v rights '+SOURCE+' '+REF+']')+'].\n'
    for n,target,names,bindings in (('r5lm','r5li',NAMES[:2],TWO),('r5ln','r5lj',NAMES,FOUR)):
        appraisal=SOURCE+' v rights v actor '+ROLE+' r[p '+target+'] '+bindings+' '+REF+' v candidate'
        text+='d '+n+'[rights a '+' '.join(x+' a' for x in names)+' candidate d] c['+both('k h26bt['+appraisal+']','k h26bv['+appraisal+']')+'].\n'
    def allcases(target,names,bindings,scope,evaluation):
        candidate=both(scope,'k h26f3[r[p '+target+'] '+bindings+' '+REF+' v candidate]')
        body='y['+candidate+'][y[t[k '+target+'['+bindings+' '+REF+']][v candidate]]['+evaluation+']]'
        for n,sort in reversed((*((n,'a') for n in names),('candidate','d'))):body='f '+n+' '+sort+'['+body+']'
        return body
    selfscope=both('k aa[v actor]','k r5kn['+SOURCE+' v actor '+ROLE+' '+REF+']',
        'k ta[i[at d][k h257z['+REF+' v candidate v at]] i[first d last d][k ic[v first v last v candidate]]]',
        'k h257z['+REF+' v candidate k h26fw[v response '+REF+']]')
    selfcases=allcases('r5lg',NAMES[:2],TWO,selfscope,'k r5lm[v rights v actor v response v candidate]')
    latercases=allcases('r5lh',NAMES,FOUR,'k r5lc['+ARGS+' '+REF+' v candidate]','k r5ln[v rights '+ARGS+' v candidate]')
    text+='d r5lo[] e[b point[g rights a['+both('k r5ll[v rights]',selfcases,latercases)+']]].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    roots=(['h26fz','h26f2'],['r5kv','r5kq','r5kn','r5jd'],['r5jz','r5jy','r5cs','h26bt','h26bv','h256m','h26ax','h26ar'])
    for source,selected in zip(sources,roots):
        for d in closure(source.document,selected):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='personal_and_posterity_renunciation_as_infringement_of_same_rights',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
