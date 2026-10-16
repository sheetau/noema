"""Connect a question seeking a property description to an attributed definition."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params
from scripts.compose_qualified_utterance import closure

PARENT='examples/v016/kant-norm-bound-choice.noema'
PARENT_BASIS='data/norm-bound-choice-basis-v1.json'
FULL='examples/v016/kant-definition-question.noema'
LIBRARY='examples/v016/definition-question.noema'
BASIS='data/definition-question-basis-v1.json'
CODE='i[h[a] e]'
QUESTION='g['+CODE+']'
QCODE='i b['+QUESTION+']'
PAIR=[('questionnode','a'),('answernode','a'),('author','a'),('context','d'),('reference',CODE),('answer',CODE),
    ('presents','h[a a '+QCODE+' d] c'),('defines','h[a a '+CODE+' d] c'),
    ('before','h[a a d] c'),('responds','h[a a a d] c')]


def av(fields):return [v(n) for n,t in fields]


def definitions():
    value=lambda name:op('t',app('s['+v(name)+']',v('person')),v('scene'))
    equivalent=quant('f','person','a',quant('f','scene','d',op('z',value('reference'),value('candidate'))))
    text=definition('rqqp','reference '+CODE+' candidate '+CODE,equivalent)
    text+=definition('rqqq','reference '+CODE,'j v[i[candidate '+CODE+']['+k('rqqp',v('reference'),v('candidate'))+']]',QUESTION)
    text+=definition('rqqr','reference '+CODE,'o a[r b[p rqqq]][o r[v reference]]',QCODE)
    text+=definition('rqqs',params(PAIR),both(op('u',op('e',v('questionnode'),v('answernode'))),
        app(v('presents'),v('questionnode'),v('author'),k('rqqr',v('reference')),v('context')),
        app(v('defines'),v('answernode'),v('author'),v('answer'),v('context')),
        app(v('before'),v('questionnode'),v('answernode'),v('context')),
        app(v('responds'),v('author'),v('questionnode'),v('answernode'),v('context'))))
    return text


MEANINGS={
    'rqqp':'二つの性質記述を同じ個体と同じ状況へ適用し、全個体・全状況で真偽が一致するという外延的な候補条件。構文の同一性や説明としての十分さとは別に評価する。',
    'rqqq':'参照する性質記述についてrqqpを満たす候補記述を求める、性質記述型を答えとする質問。答えの存在や唯一性を追加主張しない。',
    'rqqr':'同じ閉じた参照記述からrqqqへの適用の層1の記述を構成する。構成中は候補検査や参照内容を実行しない。',
    'rqqs':'別々の問いと回答の箇所を同じ著者・文脈へ結び、同じ参照から作った質問記述の提示、指定候補を概念説明として提示したこと、本文順序、回答としての提示を要求する。候補の正しさは要求しない。',
    'hzic':'表題の定義質問を既存biの啓蒙の性質記述に結び、冒頭第一文の同じbiの説明提示を回答として接続する。冒頭の既存cpが用いる著者・文脈・定義箇所と同じ参照を使う。',
}
PRIMITIVES={
    'hzia':dict(arguments=[],meaning_ja='カントの表題内で「何が啓蒙か」を問うu0006の本文箇所。文や概念の意味をこの識別子で代用せず、質問内容はrqqqと既存biから構成する。'),
    'hzib':dict(arguments=['node','author','question_description','context'],meaning_ja='著者が指定箇所に、層1の記述で指定された性質記述型の質問を提示する。表題内の問いも扱い、著者が現実の聞き手に回答を要求した出来事や、答えの正しさは含めない。'),
}
LIMITS=[
    'rqqpは同じ外延を持つ性質の記述を求める形式的な核であり、自然言語の「何であるか」に含まれる理解・本質・説明の十分さの全てを定義し終えた条件ではない。同じ外延の別名や冗長な記述も候補として通り得る。',
    '外延的な候補一致と、引用された記述の構文的な同一性を分ける。候補として一致する別名を、著者が提示した質問や回答の記録へ自動代入しない。',
    '型付き質問を構成・引用・具体候補に適用できる。記述型の全候補領域は有限列挙しない。候補評価には記述の脱引用があるため、質問の記述は層1として扱う。',
    'rqqsは著者による提示の条件であり、誤答や不十分な回答も回答として提示されたことを記述できる。実際の候補条件の成立はrqqpまたは質問への具体候補適用で別に検査する。',
    '参照先biは既存の離脱過程の性質であり、未成熟・能力・原因・決意と勇気・離脱の未解決の語義を引き継ぐ。表題の質問を新しい未説明の語彙記号で置き換えないが、参照を結んだだけでその語義の完成とはしない。',
    'u0005の回答の枠付けとu0006の質問を部分的に記述する。最初の定義文が回答の入口であるという接続であり、本文全体の唯一の回答箇所としたり、後続の説明を不要としたりしない。',
    '元の15主張をそのまま後続させ、表題と冒頭の提示関係を一つ加える。第一段落全体や表題二単位の意味確認済み判定はまだ行わない。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    text=definitions()+'r hzia[] a.r hzib[a a '+QCODE+' d] c.'
    refs=[k('hzia'),k('wb'),k('wa'),k('wh'),'r[p bi]','r[p bi]','p hzib','p ua','p ue','p hzcs']
    text+=definition('hzic','',k('rqqs',*refs))+'s[k hzic[]].'
    doc=parse(format_graph(doc,'compact')+text);doc['statements']+=old['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqqs'])
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='partial_title_definition_question_and_opening_response',document=FULL,library=LIBRARY,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],**PRIMITIVES[d['name']]) for d in added if d['kind']=='primitive'},
        limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('The title question is linked to the opening definition response',flush=True)


if __name__=='__main__':main()
