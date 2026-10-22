"""Compose loss of the same ruler's public dignity under fixed comparisons."""
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
LIBRARY='examples/v016/royal-dignity-loss.noema'
BASIS='data/royal-dignity-loss-basis-v1.json'
NAMES=('actor','community','person','project','work','field','regulation')
PRIMITIVES={
 'h26io':('[a a a d] a',['actor','office','community','reference'],
   '同じ本人が同じ共同体の同じ最高統治職において帯びる、公的な威厳・高い地位にふさわしい尊重のあり方という評価側面。固定した評価基準での同じ側面を指し、単なる私的人気、儀礼的呼称、物理的強制力、財産、法的役職の存続、立法の正当性h26gsとは区別する。この側面が実際に高いことや最高職の保持は名称から導かず、別に構成する。'),
 'h26ip':('[a d a] c',['aspect','reference','level'],
   '同じ固定基準で同じ評価側面について採る質的程度の全範囲。各程度の区別と比較基準を明示し、損傷があるという結論に合わせて尺度又は基準を変更しない。数値の単位、等間隔、必ず最高値があること、全対象に一つの普遍尺度は要求しない。'),
 'h26iq':('[a d a a] c',['aspect','reference','left','right'],
   '同じ評価側面と固定基準で、leftはright以上の程度である。ここでは公的な威厳が保たれる程度が高い向きに揃え、損傷の大きさの向きと混同しない。反射性・推移性・比較可能性は合成側で検査し、同程度の別値を直ちに同一個体とはしない。'),
 'h26ir':('[a d d a] c',['aspect','reference','point','level'],
   '同じ固定基準で同じ側面を指定場面において評価した程度はlevelである。基準側と介入側で評価側面・主体・役職・共同体を変えない。評価の一意性と尺度内所属はr2clで別に確認する。単なる測定値の欠落、誰か一人の好悪、法的地位の消滅を値の低下へ補わない。'),
 'h26is':('[a a d d d] c',['activity','aspect','reference','point','comparison'],
   'この活動が同じ側面へ及ぼす作用を評価するため、当該場面の関連背景を保ち、その活動の働きがなかった場合として採る比較場面の全範囲。反事実的な比較であり、単なる過去の時点又は無関係な理想状態へ替えない。因果的に関連する比較基準を固定し、結果の低下を見て比較場面を選ばない。少なくとも一場面の存在、結果の評価と因果的寄与は別に構成する。'),
 'h26it':('[a a d d d] c',['activity','aspect','reference','point','comparison'],
   'この同じ活動の働きが、固定した同じ側面について、指定の関連背景を保った比較場面から当該場面への評価差に因果的に寄与している。単なる共起・順序・相関や、他の活動の作用と区別する。活動の生起、比較の妥当性、差の向きと実際の程度は別に確認する。唯一原因性、行為者の損害意図、別要因の不在、永久的な作用は要求しない。'),
}
MEANINGS={
 'r5pg':'同じ評価側面・固定基準の程度範囲h26ipが非空で、以上比較h26iqがその全範囲で反射的・推移的・全比較可能である。同順位を許し、未評価・循環的な比較から損傷を認定しない。',
 'r5ph':'r5pgの整合した同じ尺度上で、同じ場面のh26irの評価値がr2clにより一意に確定する。尺度外の値・評価欠落・異なる二つの測定値を拒む。',
 'r5pi':'同じ側面・基準の当該場面と比較場面に一意なr5phの値があり、比較側が当該側以上で逆は成立しない。厳密な低下を、同順位・比較不能・違う側面の値から区別する。',
 'r5pj':'同じ活動が当該場面で生起し、同じ側面・基準に対するh26isの比較場面が非空で、その全比較についてr5piの厳密な低下とh26itの同じ活動の因果的寄与がある。比較例の一部だけを拾って損傷を補わず、前後に低くなったという共起から因果を作らない。',
 'r5pk':'同じ君主が同じ共同体の最高職h234f/r2uiを保持し、その同じ本人・職・共同体の公的威厳h26ioへ同じ活動がr5pjの因果的な損傷を与える。別人の損失・私的な不人気・法的失職と混同しない。',
 'r5pl':'同じ臣民の同じ作品を通じた試みr5pcへ、同じ君主の同じ監督活動がh26inとして介入し、その同じ最高職でr5pdの内容審査とr5pkの本人の威厳への損傷がともにある。監督職と損傷側の職を別々に存在量化して寄せ集めない。',
 'r5pm':'君主・共同体・臣民・検討活動・作品・領域・監督活動の正確な七対象列と固定基準をr5plへ渡す。後の条件文と二種類の介入比較の結果内容に引用でき、引用だけで介入や損傷を実行しない。',
}
LIMITS=[
 'u0013第十二文冒頭Es thut selbst seiner Majestät Abbruchと、直後の著作への統治上の介入を接続する依存群。公的な威厳の損傷と因果を構成する。selbstの取り立て、würdigtの皮肉、自己の最高の見識・批判的引用、聖職者の専制支援、二側の比較と全文の条件・帰属は未完。',
 'Majestätはここでは同じ君主の最高統治職に結び付く公的な威厳・高い地位にふさわしい尊重のあり方と読む。Adelung Majestätの最高の権力・地位、外に示される威厳、人物の敬称を区別し、この文を君主の身体損傷・法的廃位又は単なる敬称への侮辱とはしない。実力や現実の支持率が下がることも必須ではない。',
 'Abbruchは同じ威厳の減損とする。Adelung Abbruchの名望・権利・威厳等の減少の語義を補助資料とする。全喪失、永久性、他の全要因の不在は要求しない。gesetzgebendes Ansehenの正当な立法上の権威h26gsとこの評価側面を自動同一化しない。',
 '同じ基準の質的尺度を用い、非空の範囲、全前順序、各場面での一意な評価、逆向きが成り立たない厳密な低下を分ける。数値差・割合・単位・最高値は原文へ補わない。比較不能や未知は損傷の不存在へ書き換えず、判定の前提不足として扱う。',
 '因果評価では同じ背景に即した無介入の比較場面の全範囲を固定する。当該場面がその全比較より低く、同じ介入がその差に寄与するという明示読解。低い比較だけを選別せず、比較ごとに結論が割れる入力ではこの確定した損傷を認めない。無介入場面を現実の過去に限定しないため、他の要因で以前より高くなっていても無介入の場合より損なわれる状況を扱える。',
 '比較場面の因果的妥当性、評価側面の具体化、現実の威厳評価は意味入力の責任であり、有限モデルが現実の因果を発見したとはしない。関係h26itは活動と同じ側面の差への一般的な寄与であり、原文一文を未分析で返す真理値ではない。',
 '介入r5pdと損傷r5pkを同じ最高職の同じ束縛で結ぶ。本人と他人、最高職と別の職、作品と別作品、同じ場面と別の評価点を混ぜない。既存r5pc/pdとその語義判断は保存する。全文統合では同じ七対象列を全仮定範囲に置き、一般文から現実の君主の介入事実を断言しない。',
 'noch weit mehrの程度比較はこの厳密な低下だけからは導かない。二種類の介入を同じ比較基準で対応させ、損傷がより大きいことと隔たりの強調を後で別に結ぶ。全文の意味確認文字数を増やさない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    scope=lambda n:'k h26ip[v aspect v reference v '+n+']'
    cmp=lambda a,b:'k h26iq[v aspect v reference v '+a+' v '+b+']'
    regular=both('g level a['+scope('level')+']','f level a[y['+scope('level')+']['+cmp('level','level')+']]',
        'f left a[f right a[y['+both(scope('left'),scope('right'))+'][x['+cmp('left','right')+']['+cmp('right','left')+']]]]',
        'f left a[f middle a[f right a[y['+both(scope('left'),scope('middle'),scope('right'),cmp('left','middle'),cmp('middle','right'))+']['+cmp('left','right')+']]]]')
    text='d r5pg[aspect a reference d] c['+regular+'].\n'
    unique='k r2cl[i[at d level a][k h26ir[v aspect v reference v at v level]] i[level a]['+scope('level')+'] v point v degree]'
    text+='d r5ph[aspect a reference d point d degree a] c['+both('k r5pg[v aspect v reference]',unique)+'].\n'
    decrease='g actual a[g baseline a['+both('k r5ph[v aspect v reference v point v actual]',
        'k r5ph[v aspect v reference v comparison v baseline]',cmp('baseline','actual'),'u['+cmp('actual','baseline')+']')+']]'
    text+='d r5pi[aspect a reference d point d comparison d] c['+decrease+'].\n'
    frames='k h26is[v activity v aspect v reference v point v comparison]'
    pair=both('k r5pi[v aspect v reference v point v comparison]','k h26it[v activity v aspect v reference v point v comparison]')
    text+='d r5pj[activity a aspect a reference d point d] c['+both('k dg[v activity v point]','g comparison d['+frames+']','f comparison d[y['+frames+']['+pair+']]')+'].\n'
    aspect='k h26io[v actor v office v community v reference]'
    text+='d r5pk[actor a office a community a activity a reference d point d] c['+both('k h234f[v office v community v point]',
        'k r2ui[v actor v office v community v point]','k r5pj[v activity '+aspect+' v reference v point]')+'].\n'
    joined=both('k r5pd[v actor v office v community v regulation v work v reference v point]',
        'k r5pk[v actor v office v community v regulation v reference v point]')
    text+='d r5pl['+' '.join(n+' a' for n in NAMES)+' reference d point d] c['+both(
        'k r5pc[v actor v community v person v project v work v field v reference v point]',
        'g office a['+joined+']','k h26in[v regulation v project v reference v point]')+'].\n'
    text+='d r5pm[bindings j[a] reference d] e[b point['+bind(NAMES,'k r5pl['+' '.join('v '+n for n in NAMES)+' v reference v point]')+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5pc','r5pd','h26in'],['r2cl'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='same_ruler_public_dignity_causal_loss_partial',document=LIBRARY,
        primitives=prims,definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
