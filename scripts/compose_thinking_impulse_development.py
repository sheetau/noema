"""Ground two nonfactive thinking dispositions and their latent development."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/civic-spirit-sentence-basis-v1.json'
OLD='examples/v016/covered-unfolding.noema';OLD_BASIS='data/covered-unfolding-basis-v1.json'
LIBRARY='examples/v016/thinking-impulse-development.noema';BASIS='data/thinking-impulse-development-basis-v1.json'
CODE='i[h[a] e]';TRUE='e[n p a b][n p a b]';FALSE='u['+TRUE+']'
FIELDS='community a person a reference d';ARGS='v community v person v reference'
CONTEXT='v community v reference v person'
PRIMITIVES={
 'h27ad':('[a d a '+CODE+' d c d] c',['community','reference','person','target','anchor','impulse','candidate'],'同じ共同体・固定基準・本人が、同じ閉じた活動性質を意識する比較場面の全範囲。impulseが偽なら肯定的な傾き、真なら内的な促しを調べる。基準点の本人の応答傾向を評価し、成功・好意・促しの有無で候補を選ばない。実際に起きた観測列とは区別する。'),
 'h27ae':('[a d a '+CODE+' d c d] c',['community','reference','person','target','anchor','impulse','candidate'],'指定比較場面では、基準点における本人の関連した心理的構成・理解・習慣などの基盤を保っている。応答の真偽自体を保持条件にせず、新たな訓練や別人の性向への交換を認めない。発達の前後の基盤まで同一とする条件ではない。'),
 'h27af':('[a d a '+CODE+' d] c',['community','reference','person','target','candidate'],'この比較場面で、本人に同じ活動の内容が意識上の選択肢として提示又は想起され、そこへの態度が現れ得る局面にある。実際の活動実行、達成能力、外的許可や目的達成は要求しない。'),
 'h27ag':('[a d a '+CODE+' d c d d] c',['community','reference','person','target','anchor','impulse','preferred','other'],'同じ比較の背景・妨害・刺激の受容などからpreferredをotherより通常とする厳密な優先関係。応答したかを優先根拠にせず、rqt4で非反射性・推移性・極小候補への到達を検査する。時間順序や心理的な強度の大小とは異なる。'),
 'h27ah':('[a d a '+CODE+' d] c',['community','reference','person','target','candidate'],'本人が同じ活動を自分にとって引き受けたい又は続けたいあり方として肯定的に受け入れる、その場面での対象指向的な応答。対象が成立しているという信念、客観的な善、実行、習熟又は単に快い気分とは区別する。ここから反復性や傾向を単独では導かない。'),
 'h27ai':('[a d a '+CODE+' d] c',['community','reference','person','target','candidate'],'本人の内側から同じ活動を始め又は続ける方へ行動を促す動機的な圧力が現れる、その場面での応答。単に好ましいと眺める態度とは分け、抵抗不能、決意、実行、成功、外からの命令や正当な義務は含意しない。'),
 'h27aj':('[a d a '+CODE+' d c d] c',['community','reference','person','target','anchor','impulse','candidate'],'指定した同じ比較場面で、この種類の応答について入力が判明し評価できる。未観測又は未評価の応答を偽で補わない。各基準点で全比較場面に要求し、発達の前の無傾向を不正又は空の比較から作らない。'),
 'h27ak':('[d] a',['reference'],'固定基準で、自由な思考に向かう肯定的な傾きという性質を識別する対象。性質自体はr6ivのimpulse偽で合成し、この識別対象の存在だけで傾きを成立させない。'),
 'h27al':('[d] a',['reference'],'固定基準で、自由な思考を始め又は続ける内的な促しという性質を識別する対象。性質自体はr6ivのimpulse真で合成し、肯定的な傾きと異なる性質であることを発達側で検査する。'),
 'h27am':('[a a d d d d] c',['community','person','reference','start','end','point'],'同じ本人のこの開始点から候補終点への心理的な発達を評価する全履歴。実際の発達の時系列と、各端点の性向を診断する仮想的な通常比較場面を区別する。候補終点を変えた別履歴や身体的な描写側の履歴と混同しない。'),
 'h27an':('[a a d d d d d] c',['community','person','reference','start','end','left','right'],'この同じ発達履歴でleftがrightに時間的に先行する関係。ta/tgで厳密な全順序と両端の所属を検査し、通常性の優先関係h27agを時間へ流用しない。'),
 'h27ao':('[a a d a d d] c',['community','person','reference','process','start','end'],'この同じ本人・共同体・基準の心理的な変化過程が、指定された開始と終点を結ぶ。日付の前後や別人の変化だけで代用しない。本人が意図的に変えた行為や人格ある自然の実在は含意しない。'),
 'h27ap':('[a d a a d d] c',['community','reference','process','object','start','end'],'指定された同じ心理的な過程が、同じ二端点間でこの本人の性質の変化に関わる。対象と過程を同定し、二時点で真偽が違うだけでは成立させない。生理的又は社会的な原因機構の全体をこの関係だけから導かない。'),
 'h27aq':('[a d a a d] c',['community','reference','person','feature','point'],'この本人の内部に、指定された同じ性質が発現し得る構成・素質がある。単なる論理的可能性、外的な活動機会、他人の性質や既にその性質が顕在化したこととは異なる。潜在性と顕在性は両立し得る。起源や自然の世話は別途結ぶ。'),
}
MEANINGS={
 'r6iq':'同じ人間の成員について、固定した精神的課題のいずれかを本人の悟性と理由により遂行するr6hhが実際に成立するという自由な思考の対象内容。単なる許可又は実行機会ではなく、態度の対象を表す内容であり、引用時には実行しない。',
 'r6ir':'同じ共同体と固定基準を保ち、人引数だけを開けたr6iqの自由な思考の性質を返す。別人の成功や別課題領域への志向に替えない。',
 'r6is':'同じ共同体・基準の閉じた呼称をr6irへ適用した、段階0の閉じた活動性質記述。作成時には人の実在・思考内容・その成功を実行しない。',
 'r6it':'共同体と固定基準の呼称が元の対象を指すことを照合する。誤った呼称を単に傾向のない場合に紛れ込ませない。',
 'r6iu':'同じ人間成員と非空の課題範囲・同じ対象記述について、全比較場面で心理的基盤の保持・活動内容を意識する局面・応答の評価済みを要求する。通常性の順序が整合し非空の極小場面を持つことも確認する、各種類の傾向評価の有効性。',
 'r6iv':'r6iuが有効で、同じ非空の通常極小場面の全てに、impulse偽なら肯定的な傾きの応答、真なら内的な促しの応答があること。劣後する例外は許すが、同程度に通常な場面の欠落は無視しない。現在の応答・実行・能力・義務は導かない。',
 'r6iw':'同じ本人・共同体・基準・評価点で、自由な思考への肯定的な傾向と内的な促しの両方がある内容。一方だけ、別人又は別点の第二性質で補わない。',
 'r6ix':'固定基準で異なる二つの性質識別対象を、それぞれ同じ本人のr6ivの肯定的傾向と内的な促しへ対応させる顕在性。どちらの識別対象でもない性質に成功を移さない。',
 'r6iy':'同じ本人・共同体・基準・心理的過程・開始と終点にrw4を適用する。両端で二種類の傾向評価が有効で、開始時に両性質の素質があり、少なくとも一方はまだ顕在化せず、終点で両方が顕在化する。初期に片側が既に顕在化していてもよい。',
 'r6iz':'同じ本人・共同体・基準・開始点を固定し、候補終点に至るr6iyの心理的過程がある発達内容。制度上の発展機会だけでこの変化の実在を満たさない。',
 'r6i2':'指定評価点を終点として、同じ本人・共同体・固定基準の二つの思考性向がr6izの過程で発達したという内容。後続条件文の前件へ使う候補であり、本文現在で無条件に発達済みと断言しない。',
}
LIMITS=[
 'u0017第四文のHang und Beruf zum freien Denkenとausgewikkelt hatに向けた対象側の依存群。Berufは保存済み語義資料の内的な促しの候補を採用し、Hangの肯定的な傾きと区別する。職業、外的命令、神又は自然による正当な義務の付与を補わない。原文の唯一の解釈や語義候補の網羅は主張しない。',
 '保存済みAdelung転記は1811年版で原文より後、原刊画像未照合である。候補を区別する参考に使い、この文脈の採用を辞書が証明したとはしない。旧二候補の草案と証拠を変更せず、選択理由と限界を新記録へ残す。',
 '自由な思考は、第三文と同じ民衆の本人が固定した精神的課題のいずれかについて自分の悟性により理由ある判断をするという読み。判断を目指す活動への態度として引用し、実際の実行・能力を傾向の成立条件にしない。想像や全心理機能の一般的な定義とはしない。',
 '旧rw6の有限観測重みだけの候補を自動継承せず、既存rqt4による通常比較の応答傾向を用いる。基準点の心理的基盤を保つ全候補とその評価可能性を要求し、結果から範囲・優先を選ばない。非空の極小候補全てという強い条件であり、通常場面内部の確率的な例外や強度の数値尺度は補わない。',
 '肯定的な受容と内的な動機的圧力は区別した基本的な心理応答の入力である。両者の通常性・同じ対象への指向・顕在化は合成するが、心理機構を神経生理へ還元する一般理論は要求しない。閉じた記述が同じ真偽でも、別の思考内容への態度へ流用しない。',
 '心理的な発達は、同じ過程・順序付き履歴で潜在性から両性向の顕在性へ至ることとする。初めから全性質が未発現であること、途中の単調増加、自己の意図的な訓練、全成員の同時の発達、実際の思考実行や終了後の永続を要求しない。前後の不正・空・未知の比較を発達として数えない。',
 '自然の一般的な意味と擬人化、芽と傾向・促しの同格、最も優しい世話、硬い覆いと同じ低い側の制度の同定、全体の条件と人口への適用、後続の反作用・行為能力・政府・尊厳は未統合。第四文全文の意味判断と新しい確認文字数は追加しない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def legacy():
    ds=closure(parse((ROOT/OLD).read_text(encoding='utf-8')),('rw4',));ms=json.loads((ROOT/OLD_BASIS).read_text(encoding='utf-8'))['definitions']
    return ds,{'rw4':ms['rw4']}

def definitions():
    text='d r6iq['+FIELDS+'] e[b point['+both('k r6hd[v person v community v reference]',
      'g task a['+both('k h26ys[v community v person v task v reference]','t[k r6hh[v person v task v reference]][v point]')+']')+']].\n'
    text+='d r6ir[community a reference d] h[a] e[i[person a][k r6iq['+ARGS+']]].\n'
    text+='d r6is[community i[a] reference i[d]] '+CODE+'[o a[r[p r6ir]][v community v reference]].\n'
    text+='d r6it[community a reference d] c['+both('e[s[k h223g[v community]]][v community]','e[s[k h223h[v reference]]][v reference]')+'].\n'
    code='k r6is[k h223g[v community] k h223h[v reference]]'
    fixed=CONTEXT+' '+code+' v anchor v impulse'
    cases='i[scene d][k h27ad['+fixed+' v scene]]'
    preferred='i[first d last d][k h27ag['+fixed+' v first v last]]'
    preserved='k h27ae['+fixed+' v scene]';elicited='k h27af['+CONTEXT+' '+code+' v scene]';classified='k h27aj['+fixed+' v scene]'
    text+='d r6iu['+FIELDS+' anchor d impulse c] c['+both('k r6hd[v person v community v reference]',
      'g task a['+both('k h26ys[v community v person v task v reference]','g matter a[k h26yt[v task v matter v reference]]')+']',
      'k r6it[v community v reference]',
      'f scene d[y[k h27ad['+fixed+' v scene]]['+both(preserved,elicited,classified)+']]',
      'k rqt4['+cases+' '+preferred+' i[scene d]['+TRUE+']]')+'].\n'
    response='x['+both('u[v impulse]','k h27ah['+CONTEXT+' '+code+' v scene]')+']['+both('v impulse','k h27ai['+CONTEXT+' '+code+' v scene]')+']'
    text+='d r6iv['+FIELDS+' anchor d impulse c] c['+both('k r6iu['+ARGS+' v anchor v impulse]',
      'k rqt4['+cases+' '+preferred+' i[scene d]['+response+']]')+'].\n'
    text+='d r6iw['+FIELDS+'] e[b anchor['+both(*['k r6iv['+ARGS+' v anchor '+flag+']' for flag in (FALSE,TRUE)])+']].\n'
    text+='d r6ix['+FIELDS+' feature a point d] c[x['+both('e[v feature][k h27ak[v reference]]','k r6iv['+ARGS+' v point '+FALSE+']')+']['+both('e[v feature][k h27al[v reference]]','k r6iv['+ARGS+' v point '+TRUE+']')+']].\n'
    valid=[ 'k r6iu['+ARGS+' v '+point+' '+flag+']' for point in ('start','end') for flag in (FALSE,TRUE)]
    hist='i[point d][k h27am['+ARGS+' v start v end v point]]'
    order='i[left d right d][k h27an['+ARGS+' v start v end v left v right]]'
    transitions='i[process a first d last d][k h27ao['+ARGS+' v process v first v last]]'
    affected='i[process a object a first d last d][k h27ap[v community v reference v process v object v first v last]]'
    features='i[feature a][x[e[v feature][k h27ak[v reference]]][e[v feature][k h27al[v reference]]]]'
    latent='i[object a feature a point d][k h27aq[v community v reference v object v feature v point]]'
    manifest='i[object a feature a point d][k r6ix[v community v object v reference v feature v point]]'
    text+='d r6iy['+FIELDS+' process a start d end d] c['+both('u[e[k h27ak[v reference]][k h27al[v reference]]]',*valid,
      'k rw4[v person v process v start v end '+hist+' '+order+' '+transitions+' '+affected+' '+features+' '+latent+' '+manifest+']')+'].\n'
    text+='d r6iz['+FIELDS+' start d] e[b end[g process a[k r6iy['+ARGS+' v process v start v end]]]].\n'
    text+='d r6i2['+FIELDS+'] e[b end[g start d[t[k r6iz['+ARGS+' v start]][v end]]]].\n'
    return text

def build():
    p=parent();doc=deepcopy(p.document);doc.update(declarations=closure(p.document,('r6hd','r6hh','h26ys','h223g','h223h','rqt4','tg')),statements=[])
    imported={d['name']:p.entries[d['name']] for d in doc['declarations']};ds,means=legacy()
    for d in ds:
        n=d['name']
        if n in imported:assert d==imported[n]['declaration'],n
        else:
            doc['declarations'].append(d)
            if n not in means:assert d==p.entries[n]['declaration'];imported[n]=p.entries[n]
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(p.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set(p.source_sha256)|{OLD,OLD_BASIS}
    basis=dict(status='two_thinking_dispositions_and_latent_development_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|means|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()}|{n:OLD_BASIS for n in means},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
