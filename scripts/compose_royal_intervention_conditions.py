"""Compose the full conditional nucleus of the royal-intervention sentence."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_royal_loss_comparison import NAMES

PARENTS=('data/royal-loss-comparison-basis-v1.json','data/royal-insight-reproof-basis-v1.json','data/royal-dignity-loss-basis-v1.json','data/monarchical-religion-sentence-basis-v1.json')
LIBRARY='examples/v016/royal-intervention-conditions.noema'
BASIS='data/royal-intervention-conditions-basis-v1.json'
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
PRIMITIVES={
 'h26jd':('[j[a] d d] c',['bindings','reference','case'],
   '同じ一般論述基準で、順序付き対象列についてここで検討する、相互に矛盾しない仮定場面の全範囲。対象列は君主候補・最高職・共同体・臣民候補・検討活動・作品・領域・第一活動・第二活動・集団の順とし、同じ役職の保持は別に確認する。介入の生起、認識の真理、損傷、批判の発生・正当性、支援成功や比較結果を先に選別条件にしない。内側の内容と対象分類の固定基準には同じ仮定場面を渡す。特定の実在者・国家・現在の出来事へ限定しない。'),
}
MEANINGS={
 'r5qs':'同じ十対象・一般論述基準の全仮定場面h26jdのうち、同じ本人が同じ共同体の君主r2ujで、指定した同じ最高職h234f/r2uiを保持する範囲。介入・損傷・批判・比較成功を先取りしない。',
 'r5qt':'同じ臣民の同じ作品を通じた検討r5pcに対する介入について、指定した同じ最高職での内容監督r5pdと、その同じ活動による検討への介入h26inを結ぶ。既存r5peの役職を明示した基本の介入条件。',
 'r5qu':'同じ仮定場面で第一活動がr5qtの著作への介入なら、その同じ活動が同じ君主・最高職・共同体の威厳へr5pkの因果的損傷を与える。特定の動機・批判済み・専制支援の成立を追加条件にしない。',
 'r5qv':'同じ仮定場面で第一活動がr5qmの自分の見識による介入なら、同じ最高職の威厳へのr5pkの損傷と、その同じ行為へのr5pyの正当化可能な批判への曝露がある。現実の批判発言・見識の客観的正しさを要求しない。',
 'r5qw':'同じ仮定場面で第二活動がr5qnの宗教的専制支援への権能使用を伴う介入なら、その同じ活動が同じ最高職の威厳へr5pkの損傷を与える。個々の対象者の服属成功や第一側の見識条件を追加しない。',
 'r5qx':'同じ仮定場面を内側基準・比較評価局面にし、同じ十対象の対応場面h26jcが非空なら、全対応対にr5qqの二側の適合・因果的損傷・共通基準・第二側の大きな追加低下を要求する。比較のない対象列から程度差の存在を主張せず、比較がある場合の不適合な対は隠さない。',
 'r5qy':'同じ十対象と仮定場面へ、基本の介入からの損傷r5qu、自身の見識側の損傷と批判r5qv、専制支援側の損傷r5qw、対応する全対の程度比較r5qxをそれぞれの条件範囲で結ぶ。比較機会がないことを他の条件付き帰結の免除にしない。',
 'r5qz':'同じ一般論述基準の全十対象・全仮定場面のr5qs範囲にr5qyを要求する、第十二文の条件内容全体。個々の仮定場面を内側の固定基準にし、前件の実際の成立や特定君主の実在の行為を別に断言しない。引用・焦点・皮肉等の談話提示は別に接続する。',
 'r5ra':'r5qzと同じ全範囲でr5quの基本の介入からの損傷だけを取り出す一般内容。',
 'r5rb':'r5qzと同じ全範囲でr5qvの自身の見識側の条件付き損傷と批判可能性を取り出す一般内容。',
 'r5rc':'r5qzと同じ全範囲でr5qwの専制支援側の条件付き損傷を取り出す一般内容。',
 'r5rd':'r5qzと同じ全範囲でr5qxの対応する二側の条件付き程度比較を取り出す一般内容。',
 'r5re':'正確な十対象列・一般論述基準・仮定場面をr5qsの共通範囲へ渡す内容族。',
 'r5rf':'同じ十対象列の第一活動について、内側基準と評価点を同じ仮定場面にし、r5qtの基本の著作介入を返す内容族。',
 'r5rg':'同じ十対象列の第一活動が同じ君主・最高職・共同体の威厳へ与えるr5pkの損傷内容。',
 'r5rh':'同じ十対象列の第一活動にr5qmの自分の見識による介入を結ぶ内容族。',
 'r5ri':'同じ十対象列の第一活動に、同じ最高職のr5pkの損傷と同じ行為のr5pyの批判可能性を結ぶ帰結内容族。',
 'r5rj':'同じ十対象列の第二活動にr5qnの専制支援への不相応な権能使用を伴う介入を結ぶ内容族。',
 'r5rk':'同じ十対象列の第二活動が同じ最高職の威厳へ与えるr5pkの損傷内容。',
 'r5rl':'同じ十対象列・仮定場面で、二活動と同じ公的威厳に対するh26jcの対応場面対が非空である内容。比較の結果や二側の成功から選ばない。',
 'r5rm':'同じ十対象列・仮定場面を内側基準と比較評価局面にし、r5qqの非空の全対応対の比較内容を返す。空の比較範囲では成立しない。',
 'r5rn':'同じ十対象列と仮定場面へr5qyの四条件全体を返す。談話提示に引用しても実際の介入・損傷・批判・比較を実行しない。',
}
LIMITS=[
 'u0013第十二文全体の条件内容を構成する。一般的な著作への介入による威厳の損傷、自身の見識に基づく場合の損傷と批判可能性、宗教的専制支援の場合の損傷、対応する二側の程度比較を同じ十対象に結ぶ。まだ全文の意味確認や本文への主張追加は行わない。',
 '一般論述基準と個別の仮定場面を区別し、場面ごとの内側の対象分類・保持見解・内容・威厳評価の基準には同じ仮定場面を渡す。最高職の保持を明示して別の職の監督・支援・威厳を混ぜず、現実の君主の行為の存在を条件文から導かない。',
 '基本条件は同じ作品への統治的な内容監督による介入であり、自己の見識又は専制支援のどちらかに当てはまらなければ無害だという二者択一にはしない。全文のsowohl/als auchで示す二側を保持しつつ、原文冒頭の一般的な条件を狭めない。',
 '自身の見識側では条件内容r5qmと帰結の損傷・批判可能性を分ける。君主が自分の基準で最上とみなす内容に基づくという既存の明示読解を保持し、その内容の真理や現実の批判発言は前提にしない。',
 '専制支援側は同じ最高職の権能を同じ支援の補助手段へ不相応に用いる介入である。正式な聖職者資格、権限移譲、物理的な権力低下、残余臣民全員の服属成功は追加しない。',
 '程度比較は、関連背景を保って対応させる場面対がある対象列について要求する。各対象列に必ず現実の比較例があるとはしないが、h26jcが意味規約上の全関連対を欠落なく供給することを前提とし、結果を見て空にしてはならない。非空ならr5qqの全対検査を要求し、空の比較範囲を大きな差の成功例として数えない。',
 '一つの仮定場面で四つの条件をそれぞれ保持する。見識条件が偽でも基本の介入があれば損傷を要求し、比較機会がなくても基本の介入・見識側・支援側の帰結は消さない。前件の一つだけを変えて別の帰結を撤回しない。',
 '談話用の内容族は正確な十対象列を共有し、範囲と前件と帰結の引数を交換しない。全体と各条件内容は引用に備えた合成内容であり、帰属・語用的な提示関係が付くまで著者の全文を記述済みとはしない。',
 '残る作業はsowohl/als auch/noch/weitの並列・追加・程度提示、so weitの程度提示、indemの手段説明、格言の文言と内容・文脈的適用の引用提示、selbstの取り立て、würdigtの皮肉、著者帰属と全文通読。原文の仮定範囲と語義の読みを全文で再点検する。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def conditions(case='v case'):
    prefix='v actor v office v community v person v project v work v field'
    base='k r5qt['+prefix+' v firstact '+case+' '+case+']'
    own='k r5qm['+prefix+' v firstact '+case+' '+case+']'
    support='k r5qn['+prefix+' v secondact v group '+case+' '+case+']'
    firstloss='k r5pk[v actor v office v community v firstact '+case+' '+case+']'
    secondloss='k r5pk[v actor v office v community v secondact '+case+' '+case+']'
    reproof='k r5py[v actor v community v field v firstact '+case+' '+case+']'
    pair='k h26jc[v firstact v secondact k h26io[v actor v office v community '+case+'] '+case+' '+case+' v firstpoint v secondpoint]'
    exists='g firstpoint d[g secondpoint d['+pair+']]'
    comparison='k r5qq['+ARGS+' '+case+' '+case+']'
    return dict(base=base,own=own,support=support,firstloss=firstloss,secondloss=secondloss,
        reproof=reproof,ownresult=both(firstloss,reproof),exists=exists,comparison=comparison)

def definitions():
    scope=both('k h26jd[l[a]['+ARGS+'] v reference v case]','k r2uj[v actor v community v case]',
        'k h234f[v office v community v case]','k r2ui[v actor v office v community v case]')
    text='d r5qs['+FIELDS+' reference d case d] c['+scope+'].\n'
    text+='d r5qt[actor a office a community a person a project a work a field a activity a reference d point d] c['+both(
        'k r5pc[v actor v community v person v project v work v field v reference v point]',
        'k r5pd[v actor v office v community v activity v work v reference v point]','k h26in[v activity v project v reference v point]')+'].\n'
    c=conditions()
    for n,left,right in (('r5qu','base','firstloss'),('r5qv','own','ownresult'),('r5qw','support','secondloss'),('r5qx','exists','comparison')):
        text+='d '+n+'['+FIELDS+' reference d case d] c[y['+c[left]+']['+c[right]+']].\n'
    text+='d r5qy['+FIELDS+' reference d case d] c['+both(*('k '+n+'['+ARGS+' v reference v case]' for n in ('r5qu','r5qv','r5qw','r5qx')))+'].\n'
    for n,target in (('r5qz','r5qy'),('r5ra','r5qu'),('r5rb','r5qv'),('r5rc','r5qw'),('r5rd','r5qx')):
        body='f case d[y[k r5qs['+ARGS+' v reference v case]][k '+target+'['+ARGS+' v reference v case]]]'
        for name in reversed(NAMES):body='f '+name+' a['+body+']'
        text+='d '+n+'[reference d] e[b point['+body+']].\n'
    c=conditions('v point')
    adapters={'r5re':'k r5qs['+ARGS+' v reference v point]',
        'r5rf':c['base'],'r5rg':c['firstloss'],'r5rh':c['own'],'r5ri':c['ownresult'],
        'r5rj':c['support'],'r5rk':c['secondloss'],'r5rl':c['exists'],'r5rm':c['comparison'],
        'r5rn':'k r5qy['+ARGS+' v reference v point]'}
    for n,body in adapters.items():text+='d '+n+'[bindings j[a] reference d] e[b point['+bind(NAMES,body)+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5qm','r5qn','r5qq'],['r5py'],['r5pk'],[])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='royal_intervention_full_conditional_nucleus_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
