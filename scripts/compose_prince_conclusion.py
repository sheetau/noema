"""Connect individual attainment and deserved response in one prince profile."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_qualified_prince_frame import PROFILE,FIELDS,ARGS,NAMES
from scripts.compose_self_report_dignity import name_args
from scripts.compose_deserved_responses import RESPONSE,BASIS as GROUND,STANDARD

PARENTS=('data/qualified-prince-frame-basis-v1.json','data/religious-collective-assessment-basis-v1.json','data/deserved-responses-basis-v1.json')
LIBRARY='examples/v016/prince-conclusion.noema';BASIS='data/prince-conclusion-basis-v1.json'
MERIT='response '+RESPONSE+' ground '+GROUND+' standards j['+STANDARD+']'
MARGS='v response v ground v standards'
PRIMITIVES={
 'h26nq':('[a a a a '+PROFILE+' '+PROFILE+' d] c',['node','author','scope','clause','boundary','property','context'],
   '同じ著者・仮定範囲・節で、段階7の人物範囲記述が束縛する当人自身を、指定性質が当てはまる対象として強調する提示。周囲の人やその人が働きかける対象に関する話だけでなく当人に述定するという対照を表す。二つの記述へ同じ人物・点を渡す。意外な最低確率、当人だけの排他性、別人が性質を持つこと又は持たないこと、無条件の存在や性質の真理を補わない。'),
}
MEANINGS={
 'r5xv':'同じ宗教領域と固定基準にr5tbの自立的で適切かつ安定した判断の既有行使能力を接続する人物性質。h223hの閉じた基準名はr5tb内部で元の基準との一致を検査する。質・全関連事項・本人側の基盤を保持し、集団普及割合、実際の判断、能力の取得過程を要件にしない。',
 'r5xw':'同じ宗教領域と固定基準の閉じた名前をr5xvへ適用する段階7の人物性質記述。主文の本人の到達状態を引用し、引用を作るだけでは能力を実行しない。',
 'r5xx':'同じ人物と評価点について、r5xvの宗教的判断の行使能力と、指定した応答・功績根拠・非空の全基準によるro5の値する評価を連言する。別人の啓蒙と功績、別点の評価を寄せ集めず、応答の実行を追加しない。',
 'r5xy':'r5xjで限定した同じ君主にr5xxの二つの結論を適用する一般条件。応答と根拠の具体的な意味は後続で渡す引数であり、未定義の称賛を定義済みに数えない。条件に合う君主の実在、万人の実際の称賛又は義務を補わない。',
 'r5xz':'同じ人物条件の全設定の呼称をr5xrで照合し、r5xqの完全な条件範囲の下でr5xwの能力性質を結論として提示する。前件を単なる君主の身分へ弱めず、自由政策の実現を前件へ強めない。',
 'r5x2':'同じ主文の節・著者・仮定範囲・全人物条件で、r5xwの性質の対象をその君主当人自身として強調する。名称にまで及ぶ先行selbstの尺度的取り立てとは分ける。',
 'r5x3':'r5xzの条件内の結論提示とr5x2の当人の強調を同じ節・範囲・設定へ接続する。談話の成立から能力、義務判断、実際の自由政策を実行しない。',
}
LIMITS=[
 'u0015第一文のist selbst aufgeklärtとund verdientの結合に向けた依存群。aufgeklärtを、直前u0014で具体化した宗教事項の自立的で適切かつ安定した判断ができる個人の到達状態として読む。u0016の宗教事項を主眼とする説明も同じ読解の文脈に使う。唯一の語義や、政治的啓蒙全体の一般定義を主張しない。',
 '君主の政治的立場・義務についての自己報告の品位判断・名称拒否は前件r5xjに保持する。形容詞に別の実際の政策や義務判断を加えず、全知、全分野の技能、道徳的無謬性、特定の信仰、学識者の職業資格を課さない。君主の思想全般を一つの能力だけに還元する一般理論ではない。',
 '本人の既有基盤を保った通常機会での行使能力であり、現時点の外的機会、既に行った判断、過去の学習過程、未来の必ず成功する予測とは分ける。固定範囲と質の全条件を成功例だけで選ばない。',
 'ist selbstのselbstはその君主当人自身の対照的な強調として読む。前のselbst den ... Namenの意外な対象まで及ぶ読みと区別し、当人だけが啓蒙されている、他の人が既に啓蒙されている、君主であるから意外だという主張を追加しない。',
 'undの主語・評価点の共有と、verdientの真の根拠内容・非空の明示基準という既存ro5を接続する。基準には同じ応答と功績の閉じた記述を渡す。実際の称賛・義務・将来の全員一致を導かない。',
 '応答・根拠・基準はここでは明示された未充足の引数である。肯定的な事実報告と称賛の区別、恩恵認識だけではない感謝、世界と後世双方の範囲、最初の政府側の解放と良心の自由、功績に対する適合基準を次の一群として閉じる。旧ro7/roo/rovだけでこれらを完成扱いにしない。',
 '全設定と談話節の本文束縛、名称の高慢評価の独立した著者帰属、sondern、主文全体と後続の意味確認は残る。本文112主張・登録簿v196・17単位判断と確認文字数を変更しない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    text='d r5xv[topic a reference d] h[a] e[k r5tb[v topic v reference k h223h[v reference]]].\n'
    text+='d r5xw[topic i[a] reference i[d]] '+PROFILE+'[o a[r h[p r5xv]][v topic v reference]].\n'
    text+='d r5xx[topic a reference d '+MERIT+'] h[a] e[i[actor a][b point['+both(
        't[c[k r5xv[v topic v reference]][v actor]][v point]',
        't[k ro5[v actor '+MARGS+']][v point]')+']]].\n'
    text+='d r5xy['+FIELDS+' '+MERIT+'] e[k r5xk['+ARGS+' k r5xx[v topic v reference '+MARGS+']]].\n'
    boundary='k r5xq['+name_args(NAMES)+']'
    conclusion='k r5xw[k h223g[v topic] k h223h[v reference]]'
    text+='d r5xz[clause a author a scope a '+FIELDS+' context d] c['+both('k r5xr['+ARGS+']',
        'k h26no[v clause v author v scope '+boundary+' '+conclusion+' v context]')+'].\n'
    text+='d r5x2[focus a clause a author a scope a '+FIELDS+' context d] c['+both('k r5xr['+ARGS+']',
        'k h26nq[v focus v author v scope v clause '+boundary+' '+conclusion+' v context]')+'].\n'
    text+='d r5x3[focus a clause a author a scope a '+FIELDS+' context d] c['+both(
        'k r5xz[v clause v author v scope '+ARGS+' v context]',
        'k r5x2[v focus v clause v author v scope '+ARGS+' v context]')+'].\n'
    return text

def build():
    libs=parents();doc=deepcopy(libs[0].document);doc.update(declarations=[],statements=[]);imported={}
    for lib,roots in zip(libs,(['r5xk','r5xq','r5xr','h26no','h223g','h223h'],['r5tb'],['ro5'])):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(l.entries) for l in libs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(l.source_sha256) for l in libs))
    basis=dict(status='individual_attainment_and_open_deserved_response_conclusion',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
