"""Connect a council description to its own customary honorific designation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/guardian-irrationality-basis-v1.json','data/church-councils-basis-v1.json')
LIBRARY='examples/v016/classis-self-name.noema'
BASIS='data/classis-self-name-basis-v1.json'
PRIMITIVES={
    'h254s':('[a a a a d] c',['user','target','name','community','reference'],
        '同じ基準の同じ用法共同体で、使用主体はこの名称をこの対象に対して自らの呼び方として慣用的に採用している。対象と使用主体は人にも団体にもなり得る。単なる一回の引用、第三者からの呼称、名称を聞き知っていることとは別で、名称の描写の真理や全成員の同意・実際の発話時点の指定は含意しない。使用主体と対象を一致させた場合が自己呼称になる。'),
    'h254t':('[a a d] c',['name','community','reference'],
        'この名称は同じ用法共同体と基準で、対象を敬って扱う定型的な呼称形式を含む。敬称としての形と社会的な扱いを述べ、対象の実際の徳・能力・権威や話し手の内心の敬愛を述べない。皮肉な文脈でこの形式を言及する場合も、形式自体の性質と話し手の態度を混ぜない。'),
    'h254u':('[] a',[],
        'u0013[93,111)のehrwürdige Klassisという敬称付き自己呼称を指す名称個体。会議体そのものとは別。Klassisの制度的内容はr46l、敬称の形式はh254tへ別々に接続する。綴りは出典の範囲に保持し、原語の文字列を意味本体の代用にしない。'),
    'h254v':('[] a',[],
        'u0013のunter den Holländernで指定される、十八世紀のネーデルラントの人々の間の用法共同体への参照。採用読解では地方Hollandだけや全世界のドイツ語話者へ狭めたり広げたりしない。現代の国籍法・国境・民族血統の条件や、そこに属する全員の実際の呼称使用を補わない。'),
}
MEANINGS={
    'r46l':'会議体を受け、各基準でr46kの地域的中間会議の制度的構成を満たす内容を返す。Klassisという名称の保持する意味を、閉じたNoemaの性質記述として渡すための関数。名称の綴りや単なる識別子で分類を置き換えない。',
    'r46m':'指定名称が指定の閉じた性質記述を保持するhw2、同じ用法共同体での同じ使用主体による同じ対象への慣用的な名称採用h254s、同じ名称の敬称形式h254tを結ぶ。名称個体と対象を区別し、保持された性質の真理は脱引用しない。',
    'r46n':'r46mの使用主体と対象を同じ会議体へ束縛し、性質記述をr46lへ固定する。自分自身への敬称付きの呼称であり、第三者だけがそう呼ぶことでは代用しない。自己呼称だけで同じ会議体が制度上その分類を満たすとは認定しない。',
    'r46o':'同じ会議体・基準の制度的分類r46kと、原文の同じ敬称付き名称h254u・ネーデルラントでの用法h254vの自己呼称r46nを結ぶ。制度的内容と自己呼称を両方保持する名詞句の構成。著者の敬愛や会議体の道徳的権限を追加せず、全文の問いの外で団体の実在を断言しない。',
}
LIMITS=[
    'u0013のehrwürdige Klassis (wie sie sich unter den Holländern selbst nennt)を、敬称付き自己呼称への括弧内の説明として読む。名称の制度的内容r46lと敬称形式を分け、呼称の慣習と同じ会議体への自己適用を結ぶ。',
    'ehrwürdigはこの呼称の敬意を示す慣習的な形式として保持する。著者の心理的敬愛、対象の実際の尊敬に値する徳、皮肉の確定は追加しない。地方ドイツの改革派Classis史料はこの種の敬称形式の補助根拠であり、オランダの特定会議やカントの特定の参照先の証明に流用しない。',
    'Holländernはこの採用読解でネーデルラントの人々の間の用法を指す。名称が使われる文脈と、会議体が実在する場所や全員の国籍は別である。基本関係h254sは当該用法の社会的採用を入力として受け、有限検査から歴史的事実を生成しない。',
    'hw2は名称に明示した意味記述を結ぶ契約。記述の外延が同じという理由で別名や別記述へ自動置換せず、真理を脱引用しない。自己呼称の条件r46nと実際の分類r46kは別々に満たす必要がある。',
    '本文への全文統合は未完。etwaの例示と一般のGesellschaftへの位置付け、sollte nichtの権限の問い、誓約・同じ信条・上位後見・持続・次の否定回答を接続してから一文全体を判断する。今回の名詞句構成だけで確認済み文字数を加算しない。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    text='d r46l[body a] e[b reference[k r46k[v body v reference]]].\n'
    text+='d r46m[user a target a name a community a pattern i[h[a] e] reference d] c['+both(
        'u[e[v name][v target]]','k hw2[v name v pattern v reference]',
        'k h254s[v user v target v name v community v reference]','k h254t[v name v community v reference]')+'].\n'
    text+='d r46n[body a name a community a reference d] c[k r46m[v body v body v name v community r[p r46l] v reference]].\n'
    text+='d r46o[body a reference d] c['+both('k r46k[v body v reference]',
        'k r46n[v body k h254u[] k h254v[] v reference]')+'].\n'
    return text


def build():
    old,lib=parents();doc=deepcopy(lib.document);doc['statements']=[]
    imported={d['name']:lib.entries[d['name']] for d in doc['declarations']}
    for d in closure(old.document,['hw2']):
        n=d['name']
        if n in imported:assert d==imported[n]['declaration'] and old.entries[n]['meaning_ja']==imported[n]['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=old.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(lib.entries))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    primitives={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    primitives.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    paths=set().union(*(set(c.source_sha256) for c in parents()))
    basis=dict(status='same_regional_council_and_customary_honorific_self_name',document=LIBRARY,primitives=primitives,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
