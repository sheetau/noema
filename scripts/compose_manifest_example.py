"""Compose a realized policy example and its manifest evidential bearing."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/civic-peace-concord-basis-v1.json'
LIBRARY='examples/v016/manifest-example.noema';BASIS='data/manifest-example-basis-v1.json'
FRAME=('government','office','community','group','topic')
CONTENT='i c[e]'
PRIMITIVES={
 'h26qw':('[a '+CONTENT+' d d] c',['example','instance_content','instance','reference'],
   'この例が指す具体的な配置・経過は、固定基準の下でこの時点に現実化した、指定の閉じた内容の事例である。例は配置を指す対象で、単独の人や発話行為と同一視しない。別の内容が同時点に偶然成立するだけではこの内容の実例とせず、記述内容の成立は合成側でも検査する。単なる想像上の事例や論述箇所の存在だけでは満たさず、何の推論的根拠になるかは別に結ぶ。'),
 'h26qx':('[a a d d] c',['example','organization','reference','assessment'],
   '同じ例の情報を、この組織が公的に判断する立場から、この評価点で参照できる。組織への公開情報・報告・共有された経験等を含み、特定の構成員の直接目撃、実際に注意を向けたこと、信念への採用は要求しない。世界のどこかに情報があるだけで組織に参照可能とせず、組織を個人の知覚主体にしない。'),
 'h26qy':('[a '+CONTENT+' d d] c',['example','content','reference','assessment'],
   '同じ固定基準・評価点において、この具体例が、指定された閉じた内容を支持する実質的な証拠上・推論上の根拠を与える。例と内容の単なる話題の一致や修辞的な例示だけと区別する。別事例への適用にはその相違を踏まえた根拠が必要で、一例だけからの無条件の演繹、内容の真理、証明の完全性、受け手の賛同をこの関係から導かない。'),
 'h26qz':('[a a '+CONTENT+' d d] c',['example','organization','content','reference','assessment'],
   '同じ例が同じ内容を支える関係は、この組織が公的に判断する立場で利用できる情報と通常の判断能力に照らして、隠れた推測や特別な発見を要さず明瞭に把握できる。組織の実際の理解・賛同、全構成員の一致、物理的な光や視覚的な明るさではない。例への参照可能性と実質的な根拠の有無は別に検査する。'),
}
MEANINGS={
 'r6ab':'同じ実在事例h26qwの同じ時点で、同じ政府設定の宗教的自己選択・公的提示の自由r56hと、同じ共同体の平穏r572・一致r575が成立する。単に自由の主張が引用されたことや、別国の自由と平穏の寄せ集めを実例としない。',
 'r6ac':'同じ例・組織・閉じた内容・固定基準・評価点について、参照可能性h26qx、実質的な支持根拠h26qy、その根拠の明瞭さh26qzを結ぶ。三関係は独立で、実際の認識や賛同を要求せず、支持対象の内容も実行しない。',
 'r6ad':'同じ政府・職・共同体・集団・宗教主題・固定基準のr6aaを評価点ごとの内容にする。自由の下で平穏か一致への根拠ある危害懸念が一つもないという対象で、他の政府の現在の平穏だけに替えない。',
 'r6ae':'同じ六引数の閉じた呼称をr6adの段階2引用へ適用して、特定政府設定の懸念の不在を閉じた内容として作る。実行してから引用するのではなく、引用構文への適用であり、呼称の対応確認は呼出側で行う。',
 'r6af':'同じ自由・平穏・一致の実例r6abを、対象政府の同じ適格設定についてr6aeで閉じた懸念の不在の内容へr6acで結ぶ。実例側と対象側の政府・共同体・集団を別引数に保ち、同じ職や同じ国を強制しない。対象側の自由政策の実現、実際の納得、危害の現実の不在を要求しない。',
 'r6ag':'同じ政府設定の自由r56hと同じ共同体の平穏r572・一致r575の同時成立を内容にする。事例が具体化する対象内容であり、対象政府への懸念の不在r6adとは区別する。',
 'r6ah':'同じ六引数の閉じた呼称をr6agへ適用した段階2の事例内容。事例の内容と実際に検査する自由・平穏・一致の設定を一致させる。',
}
LIMITS=[
 'u0015第四文のein Beispielとleuchtet dieser vorの依存群。例を先行する宗教的自己選択・公的提示の自由と公的平穏・一致の共存の実例として読み、その例が、対象政府の自由条件下での懸念の不在を支持する根拠として明瞭に示されると読む。',
 '実例の現実性・同じ自由内容の実現・同じ共同体の平穏と一致は合成する。例そのものは人や政府でも、単なる引用箇所でもない。原文は実例の日付・国名をここで指定しないため補わず、事例点と評価点の前後や厳密な相異も要求しない。',
 '支持根拠とその明瞭さは公開した一般関係である。別の政府への適用に必要な相違の考慮を意味規約に含み、一国の経験だけからあらゆる国の無害を形式的に証明したことにはしない。数値確率、未来の保証、誤解する政府が改心したことを加えない。',
 'r6acは組織に対する情報上の関係で、人の認識を要求する既存r2baとは異なる。政府をaaやdfの個人として扱わない。根拠が明瞭であることと、同じ政府が制度上誤った自己理解を持つことは両立する。',
 '自由と安全の具体例側は内容として実現を要求し、対象側の懸念の不在は段階2の閉じた支持対象として保持する。帰属される全文の内部での区別であり、この依存群自体は著者帰属や歴史的事実を主張しない。',
 '前文の同じ政府へのdieserの照応、先行する同じ君主の事例への固定、Denn/doch、全文帰属と通読はまだ接続しない。正本115主張と既存判断を保持し、新しい確認文字数は0。原刊istと固定本文・AAのsei差を保持する。',
]
def av(ns):return ' '.join('v '+n for n in ns)
def af(ns):return ' '.join(n+' a' for n in ns)
def named(n):return 'k '+('h223h' if n=='reference' else 'h223g')+'[v '+n+']'
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def definitions():
    frame=av(FRAME)+' v reference'
    ns=(*FRAME,'reference')
    quoted_fields=' '.join(n+' i['+('d' if n=='reference' else 'a')+']' for n in ns)
    text='d r6ag['+af(FRAME)+' reference d] e[b point['+both(
        't[k r56h['+frame+']][v point]',
        't[k r572[v community v reference]][v point]',
        't[k r575[v community v reference]][v point]')+']].\n'
    text+='d r6ah['+quoted_fields+'] '+CONTENT+'[o a[r c[p r6ag]]['+av(ns)+']].\n'
    text+='d r6ab[example a '+af(FRAME)+' reference d instance d] c['+both(
        *('e[s['+named(n)+']][v '+n+']' for n in ns),
        'k h26qw[v example k r6ah['+' '.join(named(n) for n in ns)+'] v instance v reference]',
        't[k r6ag['+frame+']][v instance]')+'].\n'
    text+='d r6ac[example a organization a content '+CONTENT+' reference d assessment d] c['+both(
        'k h26qx[v example v organization v reference v assessment]',
        'k h26qy[v example v content v reference v assessment]',
        'k h26qz[v example v organization v content v reference v assessment]')+'].\n'
    text+='d r6ad['+af(FRAME)+' reference d] e[b assessment[k r6aa['+frame+' v assessment]]].\n'
    text+='d r6ae['+quoted_fields+'] '+CONTENT+'[o a[r c[p r6ad]]['+av(ns)+']].\n'
    source=tuple('source'+n for n in FRAME)
    text+='d r6af[example a '+af(source)+' '+af(FRAME)+' reference d instance d assessment d] c['+both(
        'k r6ab[v example '+av(source)+' v reference v instance]',
        'k r56i['+frame+']',
        *('e[s['+named(n)+']][v '+n+']' for n in ns),
        'k r6ac[v example v government k r6ae['+' '.join(named(n) for n in ns)+'] v reference v assessment]')+'].\n'
    return text
def build():
    old=parent();doc=deepcopy(old.document)
    doc.update(declarations=closure(old.document,['r56h','r56i','r572','r575','r6aa','h223g','h223h']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='manifest_realized_liberty_example_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
