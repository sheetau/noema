"""Bind risk-aware official speech to explicit prudential prohibition."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/political-quoted-speech-basis-v1.json','data/republic-polity-basis-v1.json','data/legislative-freedom-sentence-basis-v1.json')
ROOTS=(('r6fy','h223h'),('r6fu',),('h223g',))
OLD='examples/v016/risk-undertaking.noema';OLD_BASIS='data/risk-undertaking-basis-v1.json'
LIBRARY='examples/v016/republic-speech-prohibition.noema';BASIS='data/republic-speech-prohibition-basis-v1.json'
ACTION='i c[h[a a] e]'
PRIMITIVES={
 'h26wa':('[a a d a '+ACTION+' d d] c',['actor','community','reference','activity','description','view','outcome'],
  '同じ主体・政治的共同体・固定基準で、同じ活動を指定された閉じた目標記述のために行う場合、この判断点から可能と見込む結果。成功例だけでなく失敗・途中の不利益も含み、認識する主体の判断候補ごとに評価する。現実の実行又は危険の現実性を含意しない。'),
 'h26wb':('[a a d d] c',['actor','community','reference','outcome'],
  '同じ主体の公的統治上の立場と同じ共同体・固定基準から見て、この結果が主体にとって不利益を伴う。共同体の平穏・統治の維持への損失を含む政治的な評価であり、代表者個人の私益や単なる反対意見の存在だけとは分ける。どの結果を不利益とするかは明示した評価入力で、全ての不利益が禁止を導くとはしない。'),
 'h26wc':('[a a d a '+ACTION+' d] c',['actor','community','reference','activity','description','point'],
  'この主体は同じ共同体・基準・点で、同じ活動が目指す閉じた記述の内容を自らの実践判断の対象として認識する。集団的主体の場合は、その公的な意思決定手続に帰属する認識であり、代表者の私的な推測や全市民の一致とは区別する。内容の成立や成功は要求しない。'),
 'h26wd':('[a a d a '+ACTION+' d d] c',['actor','community','reference','activity','description','point','view'],
  '同じ主体が同じ活動・目標について、同じ共同体・基準・評価点の実践判断で採っている判断候補。集団の場合は公的意思決定に帰属する判断の候補を用い、都合のよい代表者の見解だけに狭めない。非空性と各候補での危険は合成側で検査する。実際の世界を必ず含むとはしない。'),
 'h26we':('[a a d a d] c',['actor','community','reference','activity','point'],
  '同じ主体が同じ共同体・固定基準の下で、この点で同じ活動を開始する。集団主体の場合、公式にその主体の活動として開始された試みであり、代表資格のない私人の着手を国家自身の着手としない。目標の達成や既に発話したことは含意しない。'),
 'h26wf':('[a a d a '+ACTION+' d] c',['actor','community','reference','activity','description','point'],
  '同じ主体に帰属する同じ活動が、この共同体・基準・点で指定された閉じた目標記述の実現を目指す。単なる結果の一致、別主体の私的目的、目標の現実の成功と分ける。'),
 'h26wg':('[a a d a d] c',['actor','community','reference','activity','point'],
  '同じ主体・共同体・固定基準・点について、この公式発言を試みることを規範的に検討する活動候補の全範囲。実行済み・成功済み・許可済みのものに限らず、禁止又は危険な候補を除外しない。範囲は規範の評価前に固定する。活動対象は可能な試みを個体として指すことを許し、候補であることから実行を導かない。'),
 'h26wh':('[a d a a a a '+ACTION+' c d] c',['community','reference','standard','actor','role','activity','description','polarity','point'],
  '同じ共同体・引用の固定基準に関して、指定した政治的・実践的判断基準が、この点で同じ主体に同じ公的統治上の役割における同じ活動について、閉じた内容記述の指定極性での実行を要求する。負極性はその記述を実行しないよう求める明示的禁止。基準は共同体の公的平穏と統治を維持する実践的責任に照らすもので、現行法令・多数決・許可の欠落・物理的不可能と同一視しない。要求の成立を危険の存在だけから推論しない。'),
}
MEANINGS={
 'r6f5':'同じ固定基準に対し、その基準名の指示を照合した上で、主体と活動を取る公式発言の内容族を返す。目標は現行r6fyの同じ許可・服従・唯一の留保と代表帰属を持つ発言であり、その成功した実行と危険を認めた試みを区別する。',
 'r6f6':'同じ基準の閉じた呼称をr6f5へ適用した段階2の閉じた活動目標記述。主体と活動の二引数を残し、構成時に発言又は許可を実行しない。',
 'r6f7':'同じ共同体・基準を固定し、主体と活動の二引数について、同じ点でr6f6の公式発言を目指して開始し、その目標を認識した非空の全判断候補に不利益な可能結果があるという既存rwiを適用する内容族。成功や現在の害・実際の発話を要しない。',
 'r6ga':'同じ共同体と基準の閉じた呼称をr6f7へ適用した段階2の試みの記述。規範が対象とするのはこの試みの内容であり、元の発話だけ又は現実に成功した発話へ置換しない。',
 'r6gb':'同じ主体・共同体・政治的判断基準・統治上の役割・引用基準・点で、共同体と基準の呼称一致、非空の全検討活動候補に対するr6gaの負極性要求を確認する。積極的許可の欠落だけでは成立せず、試み・発話・危険の現実の成立は外側に要求しない。',
 'r6gc':'同じ固定基準と点でr6fuの共和国に当たる全主体について、その共同体自身を発言主体とし、同じ政治的判断基準と統治上の役割におけるr6gbの禁止を要求する内容。ein Freistaatはこの明示モデル内の一般的な種類への主張と読み、共和国の実在や全政治主体への禁止は補わない。',
}
LIMITS=[
 'u0017第一文was ein Freistaat nicht wagen darfを、同じ引用方針を公式に述べる試みを、政治的な実践判断上してはならないとする読み。現行法による禁止、身体的な発声不能、許可が知られていない状態へ置換しない。歴史的語義の唯一解や禁止の真理の証明ではなく、この文脈で採る解釈を明示した記述である。',
 'wagenは失敗・不利益の可能性を認識しながら目標を目指して開始するrwiとして読む。勇敢な人格、恐怖の心理、実際の害、成功までは補わない。集団の認識と開始は公的な意思決定に帰属する入力であり、市民全員の心理や代表者個人の私見とは区別する。',
 '目標には同じ許可・服従と唯一の留保を持つr6fyを用いる。許可と平穏の成功を要求するr6f2は政治的能力側の目標であり、こちらで試みが成立するための実際の成功条件にはしない。言おうとする内容は両側で同じr2ug/r2uhである。',
 '旧rwg/rwh/rwiをそのまま保存して再利用する。旧rwkは積極的許可の不在でも真になるため、ここでは使わない。明示的な負の要求を採り、積極的許可との無矛盾性は追加しない。禁止と許可が衝突する規範入力でも禁止そのものは失われない。',
 '検討活動候補は非空かつ全範囲として固定する。規範対象を実行済みの試みだけに絞らず、未知の規範入力を禁止又は許可欠如に変換しない。記述を構成する時には、その記述された試みを実行しない。',
 'Freistaatはr6fuの明示した最高職の共同保持モデルをそのまま用いる。一般的な種類への全称として読み、共和政の実在を付加しない。主体ごとの禁止では空の候補で成功させない。基準と役割は後続の文全体で明示する引数で、同名の法令や役職の実在を必須にしない。',
 '引用の全記述域、共和国の実際の制度条件は既存定義のまま保持する。今回の検査は接続を対象とし、それぞれの本体の証拠を既存の固定報告で参照する。全文の照応・接続・強調・帰属と通読は残り、本文119主張・19全単位判断と確認文字数は増やさない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
@lru_cache(None)
def legacy():
    ds=closure(parse((ROOT/OLD).read_text(encoding='utf-8')),('rwi',))
    m=json.loads((ROOT/OLD_BASIS).read_text(encoding='utf-8'))['definitions']
    return ds,{d['name']:m[d['name']] for d in ds}

def definitions():
    named='e[s[k h223h[v reference]]][v reference]'
    text='d r6f5[reference d] h[a a] e[i[actor a activity a][b point['+both(named,'t[k r6fy[v actor v activity k h223h[v reference]]][v point]')+']]].\n'
    text+='d r6f6[reference i[d]] '+ACTION+'[o a[r c[p r6f5]][v reference]].\n'
    goal='k r6f6[k h223h[v reference]]'
    providers=[]
    for n,params,vs in (
      ('h26wa','actor a activity a description '+ACTION+' point d outcome d','v actor v community v reference v activity v description v point v outcome'),
      ('h26wb','actor a outcome d','v actor v community v reference v outcome'),
      ('h26wc','actor a activity a description '+ACTION+' point d','v actor v community v reference v activity v description v point'),
      ('h26wd','actor a activity a description '+ACTION+' point d view d','v actor v community v reference v activity v description v point v view'),
      ('h26we','actor a activity a point d','v actor v community v reference v activity v point'),
      ('h26wf','actor a activity a description '+ACTION+' point d','v actor v community v reference v activity v description v point')):
        providers.append('i['+params+'][k '+n+'['+vs+']]')
    text+='d r6f7[community a reference d] h[a a] e[i[actor a activity a][b point['+both(named,'k rwi[v actor v activity '+goal+' v point '+' '.join(providers)+']')+']]].\n'
    text+='d r6ga[community i[a] reference i[d]] '+ACTION+'[o a[r c[p r6f7]][v community v reference]].\n'
    candidate='k h26wg[v actor v community s[v reference] v activity v point]'
    target='k r6ga[k h223g[v community] v reference]'
    negative='u[e[v actor][v actor]]'
    required='k h26wh[v community s[v reference] v standard v actor v role v activity '+target+' '+negative+' v point]'
    text+='d r6gb[actor a community a standard a role a reference i[d] point d] c['+both(
      'e[s[k h223g[v community]]][v community]','e[s[k h223h[s[v reference]]]][s[v reference]]',
      'g activity a['+candidate+']','f activity a[y['+candidate+']['+required+']]')+'].\n'
    text+='d r6gc[standard a role a reference d] e[b point['+both(named,
      'f polity a[y[t[k r6fu[v polity v reference]][v point]][k r6gb[v polity v polity v standard v role k h223h[v reference] v point]]]')+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,rs in zip(sources,ROOTS):
        for d in closure(source.document,rs):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    ds,means=legacy()
    for d in ds:
        assert d['name'] not in imported
        doc['declarations'].append(d)
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(s.source_sha256 for s in sources))|{OLD,OLD_BASIS}
    basis=dict(status='risk_aware_official_speech_explicit_prudential_prohibition_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|means|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()}|{n:OLD_BASIS for n in means},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
