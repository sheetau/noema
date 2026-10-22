"""Compose royal support of spiritual despotism against the remaining subjects."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENTS=('data/royal-writing-oversight-basis-v1.json','data/monarchical-religion-sentence-basis-v1.json')
LIBRARY='examples/v016/royal-despotic-support.noema'
BASIS='data/royal-despotic-support-basis-v1.json'
NAMES=('actor','community','person','project','work','field','regulation','group')
PRIMITIVES={
 'h26i3':('[a a a d d] c',['order','field','community','reference','point'],
   'この同じ指配の仕組みが、この共同体内で同じ固定した領域の理解・判断・実践を規律する働きを持つ。単なるその領域への言及、同時にある別制度、共同体の外だけにある仕組みと区別する。支配者、裁量への抑制の有無、対象者、正当性は別に構成する。'),
 'h26i4':('[a a d d] c',['activity','order','reference','point'],
   '同じ活動が、この指配の仕組みの維持又は運用を助ける実務上の支えを供している。権限・執行・資源・後押し等の寄与を含むが、単なる共存、私的な賛意、無関係な援助や未着手の意図だけとは区別する。具体的な支援手段の一種類、唯一原因性、対象全員の服属成功、仕組みの拡大を必須にしない。活動の生起・担い手・仕組みの性質は合成側で結ぶ。'),
 'h26i5':('[a a d d] c',['activity','office','reference','point'],
   'この活動が、この同じ公的職に結び付く統治上の権能又は執行上の資源を実際に動員している。保持者の私的行為・個人的好意・公職の名称への言及と区別する。職の保持者と最高位、活動の参加者と生起、使用の正当性や成功は別に構成する。'),
 'h26i6':('[a a d d] c',['order','target','reference','point'],
   '同じ指配の仕組みの働きが、この人の独立した判断・実践上の選択を抑えて従属させる方向に、この人へ向けられている。対象者の自発的な選択を援助すること、中立的に話題にすること、別人だけへの支配と区別する。対象者の服属・害・圧迫の成功又は特定の物理的暴力が既に実現したことは要求しない。対象の独立性に対立する向きを与え、支配の性質と実際の支援は別に結ぶ。'),
 'h26i7':('[a a a d d] c',['activity','office','order','reference','point'],
   'この同じ活動で、この公的職の権能を、指定した別の指配の仕組みを助けるための手段として用いている。実際の動員、支援の寄与、職の保持は別に要求する。無関係な機能の併存や偶然の副作用ではなく、同じ権能の使用を同じ仕組みのための補助手段へ結び付ける。職の法的な下位化、譲渡、強制力の減少、唯一の目的は含意しない。'),
 'h26ja':('[a a a d d] c',['office','order','community','reference','point'],
   '同じ固定した評価基準で、この共同体のこの公的職にふさわしい地位・公的役割のあり方と、その権能をこの指配の仕組みのための補助手段にする用い方が両立しない。品位に反する使用という評価であり、単なる誰かの不人気、現行法上の禁止、実力の低下、実際の失職へ置き換えない。何が不相応かの基準は意味入力で明示し、当該使用の生起や仕組みの専制性は別に構成する。'),
}
MEANINGS={
 'r5p3':'同じ固定集団の全構成員列mpが人だけを含み、互いに異なる少なくとも二人がいる。einiger Tyrannenの不定の複数を保ち、特定の人数・上限・少数派比率・全専制者の列挙を要求しない。重複した一人を二人と数えない。',
 'r5p4':'r5p3の同じ複数者全員が同じ君主・共同体・固定基準の臣民r5niであり、その集団外にも同じ臣民がいる。彼の国家の中にいるという範囲と残りの臣民を保持する。正式な聖職者spの資格は要求しない。',
 'r5p5':'同じ君主・共同体・固定基準の臣民r5niで、同じ指定集団mpには属さない人。übrigenをこの集合差として構成し、君主の全臣民、別国の住民、都合のよい対象だけへ替えない。',
 'r5p6':'同じ人・同じ指配の仕組みについて既存r2qaの決定統制と抑制されない個人裁量を保ち、その同じ仕組みが同じ国家の宗教的な領域h26g7を規律するh26i3。宗教という名、肩書、宗教的な助言だけを専制としない。',
 'r5p7':'同じ指定集団の一人がr5p6の宗教的専制の担い手であり、同じ活動が同じ仕組みをh26i4として支え、その仕組みが少なくとも一人の同じ残余臣民r5p5に対抗して向けられる。別の仕組みの専制性・支援・対象を寄せ集めない。',
 'r5qa':'r5p4の同じ複数者全員についてr5p7の支援される仕組みがあり、同じ残余臣民の全員がそのいずれかの仕組みの対抗対象となる。各専制者と各対象者に異なる仕組みを許し、全専制者が全対象を同じ一つの仕組みで支配するとは強めない。',
 'r5qb':'同じ君主が同じ共同体の同じ最高職h234f/r2uiを保持し、同じ生起活動に参加し、その活動でその職の統治権能h26i5を実際に動員する。君主の私的支援や別役職の権能を最高権力の使用へ取り違えない。',
 'r5qc':'同じ残余臣民の同じ作品による理解明確化r5pcへの監督・介入に、同じ最高職でr5pdの内容審査とr5qbの権能使用があり、その同じ活動が同じ集団の宗教的専制r5qaを支援する。品位に反する手段化の評価はまだ付けない中間構成。',
 'r5qd':'同じ公的職・活動・指配の仕組みについて、職の権能を同じ仕組みの補助手段として用いるh26i7ことと、その用い方が同じ共同体・基準で職にふさわしいあり方に反するh26jaことを結ぶ。単なる権能使用・通常の適切な支援・実力低下と区別する。',
 'r5qe':'r5p7の同じ専制者・同じ支援対象の仕組みに、同じ最高職と活動のr5qdを結ぶ。支援する仕組みとは別の仕組みへの不相応な手段化を借りない。',
 'r5qf':'r5p4の同じ複数者全員と残余臣民全員について、r5qeの同じ支援と不相応な権能使用を結ぶ。各対象の全称範囲を維持し、支援例と品位を損なう例を別の活動・役職・仕組みから集めない。',
 'r5qg':'同じ残余臣民の同じ作品への監督・介入について、同じ最高職の内容審査r5pd・権能使用r5qb・全対象の専制支援と不相応な手段化r5qfを結ぶ。最高権力をその支援へ低める側の条件内容であり、現実の特定君主の行為をここだけで断言しない。',
 'r5qh':'君主・共同体・臣民・検討活動・作品・領域・監督活動・支援される複数者集団の正確な八対象列と固定基準をr5qgへ渡す。全文の二側比較と条件に引用でき、引用だけでは介入・支援・対象者の服属を実行しない。',
}
LIMITS=[
 'u0013第十二文後半の最高権力を宗教的専制の支援にまで低める側を構成する。geistlichenはDespotismを修飾するため、支配する人全員に既存spの任用された聖職者資格を追加しない。宗教的な理解・判断・実践を恣意的に支配する担い手と読み、正当な宗教的助言一般への非難に拡張しない。',
 'einiger Tyrannenは特定されない複数の担い手と読み、固定した集団の全員に同じ意味条件を要求する。少なくとも異なる二人を保つが、具体的な人数・割合・国家内の全専制者を尽くすことは要求しない。複数者それぞれの支配の仕組みは同じでも異なってもよい。',
 'in seinem Staateとseine übrigen Unterthanenは、同じ君主の同じ共同体での臣民集合から、支援される複数者を除いた残余と読む。原文はここを特定集団の現代的市民資格や外国の被支配者へ広げない。残余全体が対抗対象となる読みを明示し、対象ごとに別の支配者・仕組みを許す。全員の服属成功や現在の被害までは述べない。',
 'unterstützenは同じ仕組みの維持・運用への実務上の支えとする。Adelungの援助又は作用・意図を促進する語義を補助にし、賛意だけ・まだ実行していない意図だけに弱めない。軍事力・金銭・法令など一つの手段や、支配拡大・全対象の制圧成功を必須にしない。',
 'erniedrigtは、最高職の権能をその職にふさわしくない補助手段として同じ専制支援へ用いる読みを採る。Adelungの品位に反する行為という比喩用法と整合させ、物理的な力の減少、法的な権限移譲、正式な上下関係の逆転、失職にしない。実際の使用と不相応という評価を分ける。Majestätへの因果的な損傷は既存r5pl/pmにあり、ここから自動的に同一視しない。',
 'so weit ... zu unterstützenは、その低め方の具体化がまさに同じ支援であることを、同じ活動・最高職・仕組みの束縛で保持する。数値の程度・限界や時間的な最終結果は追加しない。全文での程度の提示、sowohl/als auchとnoch weit mehrによる損傷比較は別に接続する。',
 '同じ作品への介入の対象者も残余臣民に含める。内容審査r5pd、最高職の権能使用r5qb、支援r5qfの最高職は同じ存在量化した職であり、別職の支援を混ぜない。各支援の専制者と仕組み、宗教的領域、共同体、対抗対象、基準と場面を保つ。',
 'これは一般条件内に置く部分構成である。全文の条件・全仮定範囲・威厳損傷と二側の程度比較、格言の引用提示と著者帰属、selbstの取り立て・würdigtの皮肉・so weitの提示、全文通読は未完。意味確認済み文字数を増やさない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    member=lambda n:'k hg[k mp[v group] v '+n+']'
    plural=both('f member a[y['+member('member')+'][k aa[v member]]]',
        'g first a[g second a['+both(member('first'),member('second'),'u[e[v first][v second]]')+']]')
    text='d r5p3[group a] c['+plural+'].\n'
    rest='k r5p5[v actor v community v group v target v reference]'
    text+='d r5p5[actor a community a group a target a reference d] c['+both('k r5ni[v actor v target v community v reference]','u['+member('target')+']')+'].\n'
    text+='d r5p4[actor a community a group a reference d] c['+both('k r5p3[v group]',
        'f tyrant a[y['+member('tyrant')+'][k r5ni[v actor v tyrant v community v reference]]]','g target a['+rest+']')+'].\n'
    text+='d r5p6[order a tyrant a field a community a reference d point d] c['+both('t[k r2qa[v order v tyrant]][v point]',
        'k h26g7[v field v community v reference]','k h26i3[v order v field v community v reference v point]')+'].\n'
    params='actor a community a group a field a activity a';args='v actor v community v group v field v activity'
    witness=args+' v tyrant v order v reference v point'
    target='k h26i6[v order v target v reference v point]'
    text+='d r5p7['+params+' tyrant a order a reference d point d] c['+both(member('tyrant'),
        'k r5p6[v order v tyrant v field v community v reference v point]','k h26i4[v activity v order v reference v point]',
        'g target a['+both(rest,target)+']')+'].\n'
    def collective(witness):
        return both('k r5p4[v actor v community v group v reference]',
            'f tyrant a[y['+member('tyrant')+'][g order a['+witness+']]]',
            'f target a[y['+rest+'][g tyrant a[g order a['+both(witness,target)+']]]]' )
    text+='d r5qa['+params+' reference d point d] c['+collective('k r5p7['+witness+']')+'].\n'
    text+='d r5qb[actor a office a community a activity a reference d point d] c['+both('k r2uj[v actor v community v point]',
        'k h234f[v office v community v point]','k r2ui[v actor v office v community v point]',
        'k dg[v activity v point]','k df[v actor v activity v point]','k h26i5[v activity v office v reference v point]')+'].\n'
    def intervention(extra):
        return both('k r5pc[v actor v community v person v project v work v field v reference v point]',
            'k r5p5[v actor v community v group v person v reference]',
            'g office a['+both('k r5pd[v actor v office v community v regulation v work v reference v point]',
                'k r5qb[v actor v office v community v regulation v reference v point]',extra)+']',
            'k h26in[v regulation v project v reference v point]')
    allparams=' '.join(n+' a' for n in NAMES)+' reference d point d'
    text+='d r5qc['+allparams+'] c['+intervention('k r5qa[v actor v community v group v field v regulation v reference v point]')+'].\n'
    text+='d r5qd[office a order a activity a community a reference d point d] c['+both(
        'k h26i7[v activity v office v order v reference v point]','k h26ja[v office v order v community v reference v point]')+'].\n'
    text+='d r5qe[office a '+params+' tyrant a order a reference d point d] c['+both('k r5p7['+witness+']',
        'k r5qd[v office v order v activity v community v reference v point]')+'].\n'
    text+='d r5qf[office a '+params+' reference d point d] c['+collective('k r5qe[v office '+witness+']')+'].\n'
    text+='d r5qg['+allparams+'] c['+intervention('k r5qf[v office v actor v community v group v field v regulation v reference v point]')+'].\n'
    text+='d r5qh[bindings j[a] reference d] e[b point['+bind(NAMES,'k r5qg['+' '.join('v '+n for n in NAMES)+' v reference v point]')+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5pc','r5pd','h26in'],['mp','hg','aa','r2qa'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='royal_power_used_for_spiritual_despotism_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
