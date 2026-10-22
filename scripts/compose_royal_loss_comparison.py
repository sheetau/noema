"""Compare causal dignity losses under shared baselines and matched cases."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENTS=('data/royal-dignity-loss-basis-v1.json','data/royal-insight-reproof-basis-v1.json','data/royal-despotic-support-basis-v1.json','data/monarchical-religion-sentence-basis-v1.json')
LIBRARY='examples/v016/royal-loss-comparison.noema'
BASIS='data/royal-loss-comparison-basis-v1.json'
NAMES=('actor','office','community','person','project','work','field','firstact','secondact','group')
PRIMITIVES={
 'h26jb':('[a d a a] c',['aspect','reference','higher','lower'],
   '同じ評価側面の同じ固定した質的尺度で、higherとlowerの間隔が文脈上大きいと評価される。尺度・基準を変更せず、二つの値の大小順、一意な測定、因果作用は別に確認する。数値単位、等間隔、倍率又は一定の数値閾値を必須にしない。単に少し違うこと、順序上隣り合う項目の個数、強い語調だけへ還元しない。'),
 'h26jc':('[a a a d d d d] c',['firstact','secondact','aspect','reference','assessment','firstpoint','secondpoint'],
   '同じ評価側面と固定基準で二活動の作用を比較するこの評価局面において、関連する背景を保ち、比較対象の働き方を対応させて考察する場面対の全範囲に、この向き付きの対が属する。現実の異なる時期の評判を任意に並べず、結果の差を見て好都合な対だけを選ばない。具体的な活動種類、主体、対象と役職、無介入の比較場面、実際の損傷や隔たりは別に検査する。現実に双方が発生したこと、全状況の無差別な交差比較、二種類の行為条件の排他性は含意しない。'),
}
MEANINGS={
 'r5qi':'同じ評価側面・固定基準で、二活動それぞれの指定場面に対する無介入比較範囲h26isが非空で、全場面について両側の所属が一致する。同じ高さの別の無関係な背景を共通基準とせず、一つの好都合な比較場面だけを共有する場合を拒む。',
 'r5qj':'同じ評価側面・基準で両場面のr5phの一意な評価値があり、第一側の値が第二側以上で逆は成り立たず、その同じ値の間隔がh26jbで大きい。単なる違い、同順位、逆順、大きいとの入力だけ、曖昧な測定からは成立しない。',
 'r5qk':'同じ二活動・評価側面・基準・評価局面の対応場面h26jcで、両活動がそれぞれr5pjの因果的損傷を与え、r5qiの全無介入基準を共有し、第二側の評価がr5qjとして大幅に低い。損傷なしの高低や、別基準の低い終点を大きな損傷へ替えない。',
 'r5ql':'同じ君主が両場面で同じ共同体の同じ最高職を保持し、その同じ本人・職・共同体の公的威厳h26ioについてr5qkの比較が成り立つ。別人・別職の損傷や、私的な人気・法的地位の違いへ置き換えない。',
 'r5qm':'自分の最上とみなす見解を理由とするr5prの介入について、同じ臣民・検討活動・作品・領域のr5pcと、引数で指定した同じ最高職での内容監督r5pdと介入h26inを結ぶ。既存r5psの最高職を外へ明示し、比較と同じ職を共有する。批判への曝露は全文の別の帰結として接続する。',
 'r5qn':'宗教的専制の支援側について、同じ残余臣民の同じ作品への監督・介入、同じ最高職の権能使用r5qb、全対象の支援と不相応な手段化r5qfを結ぶ。既存r5qgの最高職を外へ明示し、比較と同じ職を共有する。',
 'r5qo':'同じ君主・最高職・共同体・臣民・検討活動・作品・領域を保った二側のr5qm/r5qnが、同じ公的威厳についてh26jcの対応場面対として登録される。結果の大小や批判の有無をこの範囲条件にして比較を選別しない。',
 'r5qp':'同じ十対象と二場面がr5qoの二側として対応し、その同じ最高職の公的威厳についてr5qlの両側の損傷・共通基準・第二側の大きな追加低下が成り立つ。',
 'r5qq':'同じ十対象・基準・評価局面の全対応場面h26jcを非空とし、その全対にr5qpを要求する。登録された対の一部の損傷欠落・逆転・種類不適合を量化から隠さず、比較の空範囲で大きな損傷を認定しない。現実の特定君主の行為の存在は述べない。',
 'r5qr':'君主・最高職・共同体・臣民・検討活動・作品・領域・第一活動・第二活動・支援される集団の正確な十対象列と固定基準をr5qqへ渡す内容族。評価点は比較を行う局面であり、両活動の仮定場面とは分ける。全文の程度比較を引用しても活動や比較を実行しない。',
}
LIMITS=[
 'u0013第十二文のsowohl ... als auch und noch weit mehrを、自身の見識による介入側にも威厳の損傷があり、宗教的専制を支援する側では対応する条件の下でそれがさらに大きいという比較と読む。両側の存在を現実の歴史的事件として断言せず、全条件文・談話帰属は後で接続する。',
 '比較は同じ本人・最高職・共同体・臣民・作品・検討活動・領域と評価尺度に固定する。二つの働き方を考察する場面は異なってよく、活動個体も同じ又は異なるものを許す。既存の二種類の条件を排他的だとはしないが、同一の場面を左右へ複製して厳密な追加低下を得たことにはしない。',
 '関連背景を保って対応させた場面対の全範囲をh26jcで固定し、二側の適合と比較結果を別に検査する。無関係な全事例の任意の組合せでも一方が必ず悪いという主張に広げない。妥当な対の範囲は意味入力で明示し、結果を見て例外を外すことを禁じる。',
 '両側にr5pjの厳密な低下と同じ活動の因果的寄与を要求し、それぞれの無介入比較範囲h26isを全域で一致させる。この共通基準の下で第二側の終点評価が大幅に低いことを、より大きな損傷と読む。単に第二側の終点が低くても、出発する比較背景が違えば足りない。',
 'weitは同じ尺度の同じ二値の隔たりが大きいこととして別に構成する。単なる厳密な大小、順序の項目数、数値の差・割合・倍率と同一視しない。h26jbだけで比較の順序を保証せず、一意な測定と厳密な低下が必要である。',
 '最高職を明示するr5qm/r5qnは、既存のr5ps/r5qgの内部と同じ対象・関係を再構成する。既存定義を改変せず、両側の内容審査、専制支援の権能使用と威厳の帰属を同じ職に結ぶ。自身の見識側の批判可能性r5pyは、比較の対象範囲を結果で絞らないためここでは前提にせず、全文で独立に帰結として接続する。',
 '全対応対について比較を要求するが、全現実の時点や全国家に無条件にこの対応関係があるとはしない。対応が空・未知又は不適合なら、この確定した程度比較を認定しない。有限検査が現実の威厳や社会的因果を測定したとはしない。',
 '本群は程度比較の意味依存を構成する。sowohl/als auch/nochの談話上の並列と追加、weitの強調提示、so weitの程度提示、格言引用と著者帰属、selbstの取り立てとwürdigtの皮肉、全文の全仮定範囲と条件・帰結・通読は残る。意味確認文字数は増やさない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    first='k h26is[v firstact v aspect v reference v firstpoint v baseline]'
    second='k h26is[v secondact v aspect v reference v secondpoint v baseline]'
    text='d r5qi[firstact a secondact a aspect a reference d firstpoint d secondpoint d] c['+both('g baseline d['+first+']',
        'f baseline d[e['+first+']['+second+']]')+'].\n'
    cmp=lambda l,r:'k h26iq[v aspect v reference v '+l+' v '+r+']'
    lower=both('k r5ph[v aspect v reference v firstpoint v higher]','k r5ph[v aspect v reference v secondpoint v lower]',
        cmp('higher','lower'),'u['+cmp('lower','higher')+']','k h26jb[v aspect v reference v higher v lower]')
    text+='d r5qj[aspect a reference d firstpoint d secondpoint d] c[g higher a[g lower a['+lower+']]].\n'
    pair='k h26jc[v firstact v secondact v aspect v reference v assessment v firstpoint v secondpoint]'
    loss=both(pair,'k r5pj[v firstact v aspect v reference v firstpoint]','k r5pj[v secondact v aspect v reference v secondpoint]',
        'k r5qi[v firstact v secondact v aspect v reference v firstpoint v secondpoint]',
        'k r5qj[v aspect v reference v firstpoint v secondpoint]')
    text+='d r5qk[firstact a secondact a aspect a reference d assessment d firstpoint d secondpoint d] c['+loss+'].\n'
    aspect='k h26io[v actor v office v community v reference]'
    offices=[s for p in ('firstpoint','secondpoint') for s in ('k h234f[v office v community v '+p+']','k r2ui[v actor v office v community v '+p+']')]
    text+='d r5ql[actor a office a community a firstact a secondact a reference d assessment d firstpoint d secondpoint d] c['+both(*offices,
        'k r5qk[v firstact v secondact '+aspect+' v reference v assessment v firstpoint v secondpoint]')+'].\n'
    params='actor a office a community a person a project a work a field a activity a'
    common=('k r5pc[v actor v community v person v project v work v field v reference v point]',
        'k r5pd[v actor v office v community v activity v work v reference v point]','k h26in[v activity v project v reference v point]')
    text+='d r5qm['+params+' reference d point d] c['+both(*common,'k r5pr[v actor v activity v field v reference v point]')+'].\n'
    text+='d r5qn['+params+' group a reference d point d] c['+both(*common,'k r5p5[v actor v community v group v person v reference]',
        'k r5qb[v actor v office v community v activity v reference v point]',
        'k r5qf[v office v actor v community v group v field v activity v reference v point]')+'].\n'
    allparams=' '.join(n+' a' for n in NAMES)
    args=' '.join('v '+n for n in NAMES)
    prefix='v actor v office v community v person v project v work v field'
    pair='k h26jc[v firstact v secondact '+aspect+' v reference v assessment v firstpoint v secondpoint]'
    branches=both(pair,'k r5qm['+prefix+' v firstact v reference v firstpoint]',
        'k r5qn['+prefix+' v secondact v group v reference v secondpoint]')
    tail=' reference d assessment d firstpoint d secondpoint d';tailargs=' v reference v assessment v firstpoint v secondpoint'
    text+='d r5qo['+allparams+tail+'] c['+branches+'].\n'
    text+='d r5qp['+allparams+tail+'] c['+both('k r5qo['+args+tailargs+']',
        'k r5ql[v actor v office v community v firstact v secondact'+tailargs+']')+'].\n'
    text+='d r5qq['+allparams+' reference d assessment d] c['+both('g firstpoint d[g secondpoint d['+pair+']]',
        'f firstpoint d[f secondpoint d[y['+pair+'][k r5qp['+args+tailargs+']]]]')+'].\n'
    text+='d r5qr[bindings j[a] reference d] e[b assessment['+bind(NAMES,'k r5qq['+args+' v reference v assessment]')+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5ph','r5pj','h26io'],['r5pc','r5pd','h26in','r5pr'],['r5p5','r5qb','r5qf'],[])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='matched_royal_interventions_and_greater_dignity_loss_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
