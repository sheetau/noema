"""Keep ecclesiastical examples, prospective formation and normative polarity distinct."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind
from scripts.compose_spiritual_guardians import quant

PARENTS=('data/guardian-irrationality-basis-v1.json','data/mediated-guardianship-basis-v1.json','data/classis-self-name-basis-v1.json')
LIBRARY='examples/v016/covenant-entitlement.noema'
BASIS='data/covenant-entitlement-basis-v1.json'
NAMES=('body','agreement','creed','subject','community')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
MEANINGS={
    'r47e':'ここでいう教会関係者の団体の範囲を、全成員が聖職者であるr456、または教会から職務付きで派遣される代表者の団体r46cとして構成する。聖職者だけの団体と長老を含み得る教会代表の団体を同一視しない。r46fの教会会議とr46oのClassisは後者を含むこの範囲で例示できる。',
    'r47f':'団体・合意・信条・宗教的主題・政治的共同体の正確な五個体列から、同じ合意の固定基準h254zにおける目的付き相互宣誓r47dの形成内容を作る。規範の名宛人である団体を先頭に置く。評価点を変えても別の合意・条項・形成基準へ取り替えない。実際の形成を外側で要求しない。',
    'r47g':'同じ評価規範・団体・立場について、r47fの同じ形成内容と正確な五個体列への正極性の積極的許可があり、同じ対象の負極性の要求と衝突しないrduを結ぶ。形成、履行、未来の成功、法制度上の効力を生む権能、神的な権威の実在は実行しない。',
    'r47h':'同じ固定基準で、団体がr47eの教会関係者の団体であり、同じ定式化と主題がr46pの宗教上の信条をなす候補範囲。許可・形成の成否・後見の成功によって候補を選別しない。合意と政治的共同体は別々の役割の引数として保持する。',
    'r47i':'指定の評価規範・立場・政治的共同体・固定基準の下で、r47hの団体・合意・信条・主題の候補に、r47gの同じ目的付き相互宣誓形成への衝突のない積極的許可がある例が一つでもあるという内容。どの候補も外側の実在・形成の事実として断言しない。',
    'r47j':'r47iの同じ許可事例の存在を否定する内容。全候補についてその権限を否認する読みであり、一つの不適格例だけで済ませず、形成や目的そのものの不成立へ否定を移さない。',
    'r47k':'同じr47iを負極性で問うrijの発話。否定疑問の形を保持するが、これだけで話し手が権限の存在を肯定したことや、否定回答を述べたことにはしない。sollte nichtの提示上の期待とAberの接続は外側で指定する。',
    'r47l':'同じr47iを負極性で述べるrikの回答発話。否定疑問の全体をさらに反転せず、元の権限事例の存在を否定する。ganzの全面的な拒否とIch sageの明示的な著者帰属は外側で接続する。',
}
LIMITS=[
    'berechtigt seinをここでは当該の拘束を目的とする合意を形成してよいという正当な規範上の資格として読み、衝突のない積極的許可rduで表す。評価側は本文統合で道理・人間の啓蒙に関する規範へ固定し、現行法や団体自身が許すことを正当性へ代用しない。',
    '形成行為の規範上の資格と、その行為が制度上の拘束力を生む権能は区別する。後続のnull und nichtigで述べる契約の無効性を、この語だけから先取りして連言に加えない。許可欠如・反対要求との衝突・物理的不可能性も区別する。',
    'r47eは原文の一般表現を例示に即して教会関係の職務者・代表者の団体と読むための範囲。全員牧師というr456をClassisに押し付けず、一般の同席者・宗教について話すだけの集まりへは広げない。この範囲が全時代のGesellschaft von Geistlichenの辞書的な必要十分条件だとはしない。',
    'r47hは同じ団体と信条の候補を指定し、合意の成立や目的の達成で選別しない。量化の領域には検討上の対象も含め、問いの提示から現実の該当団体や契約を存在断言しない。',
    '形成内容は合意ごとの基準h254zを保持し、規範を評価する点を変えても当事者や条項をその都度選び直さない。r47dと同じ固定基準・全当事者・目的への参加を使用し、完成の可否を調べるための実行は許可判定の条件にしない。',
    '問いと回答の同じ共通命題と極性を構成した依存群。第六段落専用の参照供給、etwa/または/自己呼称の提示、sogar、sollte nichtの期待、Aber、Ich sage/ganz、全文帰属と意味判断は未統合。本文96主張と確認済み分量を保持する。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    text='d r47e[body a reference d] c[x[k r456[v body v reference]][k r46c[v body v reference]]].\n'
    formation='k r47d[v body v agreement v creed v subject v community k h254z[v agreement]]'
    text+='d r47f[bindings j[a]] e[b point['+bind(NAMES,formation)+']].\n'
    bindings='l[a]['+ARGS+']'
    valid='i[items j[a]][e[v items]['+bindings+']]'
    fields='assessor a '+FIELDS+' role a point d'
    text+='d r47g['+fields+'] c[k rdu[v assessor v body v role r[p r47f] '+bindings+' '+TRUE+' v point '+valid+' p h7k p h7l]].\n'
    text+='d r47h['+FIELDS+' reference d] c['+both('k r47e[v body v reference]','k r46p[v creed v subject v reference]')+'].\n'
    fields='assessor a role a community a reference d';args='v assessor v role v community v reference'
    candidate=both('k r47h['+ARGS+' v reference]','k r47g[v assessor '+ARGS+' v role v point]')
    text+='d r47i['+fields+'] e[b point['+quant(('body','agreement','creed','subject'),candidate,'g')+']].\n'
    text+='d r47j['+fields+'] e[b point[u[t[k r47i['+args+']][v point]]]].\n'
    for name,target in (('r47k','rij'),('r47l','rik')):
        text+='d '+name+'['+fields+'] f[k '+target+'[k r47i['+args+'] '+FALSE+']].\n'
    return text


def build():
    old,purpose,church=parents();doc=deepcopy(purpose.document);doc['statements']=[]
    imported={d['name']:purpose.entries[d['name']] for d in doc['declarations']}
    for source,roots in ((old,['rdu','h7k','h7l','rij','rik']),(church,['r46o','r46f','r456','r46c'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not set(MEANINGS)&set().union(*(set(c.entries) for c in parents()))
    doc=parse(format_graph(doc,'compact')+definitions())
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    paths=set().union(*(set(c.source_sha256) for c in parents()))
    basis=dict(status='same_covenant_formation_entitlement_negative_question_and_answer',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
