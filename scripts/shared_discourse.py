"""Scoped discourse referents built from sequences and continuations."""
from functools import lru_cache
import json
from noema.constructed import format_graph
from noema.constructed_discourse import normalize_document,function_sort,sequence_sort,question_sort
from scripts.shared_modality import ROOT,v,app,call,op
from scripts.shared_reference import I,S,T,truth,lam,definition
from scripts.shared_time import q,allof

N='number'
STATE=sequence_sort(I)
PROPERTY=function_sort([I,S],T)
RELATION=function_sort([I,I,S],T)
TEST=function_sort([STATE,S],T)
UPDATE=function_sort([TEST,STATE,S],T)
IDENTITY=function_sort([I,I,I,I,S],T)
LIBRARY='examples/v016/shared-discourse-v1.noema'
BASIS='data/shared-discourse-basis-v1.json'


def empty():return dict(kind='sequence',element=I,items=[])
def finish():return lam([('endstate',STATE),('endworld',S)],truth(True))
def position(state,index,value):return dict(kind='position',sequence=state,index=index,value=value)
def append(state,value):return dict(kind='concat',left=state,right=dict(kind='sequence',element=I,items=[value]))
def continued(state=None):return app('continuation',v('state') if state is None else state,v('world'))
def update(body):return lam([('continuation',TEST),('state',STATE),('world',S)],body)
def at(target='referent'):return call('referentat',v('state'),v('index'),v(target))
def runs(name):return app(name,finish(),v('state'),v('world'))


@lru_cache(maxsize=1)
def raw():
    defs=[]
    def add(name,params,result,body):defs.append(definition(name,params,result,body))
    add('referentat',[('state',STATE),('index',N),('referent',I)],T,position(v('state'),v('index'),v('referent')))
    add('referentavailable',[('state',STATE),('index',N)],T,q('exists','referent',I,at()))
    body=q('exists','referent',I,op('and',at(),app('property',v('referent'),v('world'))))
    add('referenttest',[('index',N),('property',PROPERTY)],TEST,lam([('state',STATE),('world',S)],body))
    body=q('exists','subject',I,q('exists','object',I,allof(
        call('referentat',v('state'),v('subjectindex'),v('subject')),
        call('referentat',v('state'),v('objectindex'),v('object')),
        app('relation',v('subject'),v('object'),v('world')))))
    add('referentrelation',[('subjectindex',N),('objectindex',N),('relation',RELATION)],TEST,
        lam([('state',STATE),('world',S)],body))
    add('discoursetest',[('condition',TEST)],UPDATE,update(op('and',app('condition',v('state'),v('world')),continued())))
    body=q('exists','referent',I,op('and',app('property',v('referent'),v('world')),continued(append(v('state'),v('referent')))))
    add('introducereferent',[('property',PROPERTY)],UPDATE,update(body))
    distinct=dict(kind='fold',sequence=v('state'),initial=truth(True),step=lam([('distinct',T),('prior',I)],
        op('and',v('distinct'),op('not',op('equal',v('referent'),v('prior'))))))
    body=q('exists','referent',I,allof(app('property',v('referent'),v('world')),distinct,continued(append(v('state'),v('referent')))))
    add('distinctreferent',[('property',PROPERTY)],UPDATE,update(body))
    add('aliasreferent',[('index',N)],UPDATE,update(q('exists','referent',I,
        op('and',at(),continued(append(v('state'),v('referent')))))))
    nextstep=lam([('nextstate',STATE),('nextworld',S)],app('second',v('continuation'),v('nextstate'),v('nextworld')))
    add('sequencediscourse',[('first',UPDATE),('second',UPDATE)],UPDATE,
        update(app('first',nextstep,v('state'),v('world'))))
    add('closeddiscourse',[('discourse',UPDATE)],UPDATE,update(op('and',runs('discourse'),continued())))
    add('negateddiscourse',[('discourse',UPDATE)],UPDATE,update(op('and',op('not',runs('discourse')),continued())))
    add('alternativediscourse',[('first',UPDATE),('second',UPDATE)],UPDATE,
        update(op('and',op('or',runs('first'),runs('second')),continued())))
    fails=lam([('nextstate',STATE),('nextworld',S)],op('not',app('consequent',finish(),v('nextstate'),v('nextworld'))))
    no_counterexample=op('not',app('antecedent',fails,v('state'),v('world')))
    add('conditionaldiscourse',[('antecedent',UPDATE),('consequent',UPDATE)],UPDATE,update(op('and',no_counterexample,continued())))
    add('discourseholds',[('discourse',UPDATE),('initial',STATE),('world',S)],T,
        app('discourse',finish(),v('initial'),v('world')))
    selected=lam([('endstate',STATE),('endworld',S)],call('referentat',v('endstate'),v('index'),v('referent')))
    candidate=[('discourse',UPDATE),('initial',STATE),('index',N),('referent',I),('world',S)]
    add('discoursecandidate',candidate,T,app('discourse',selected,v('initial'),v('world')))
    def candidate_call(target):return call('discoursecandidate',v('discourse'),v('initial'),v('index'),v(target),v('world'))
    unique=q('forall','other',I,op('implies',candidate_call('other'),op('equal',v('referent'),v('other'))))
    add('discourseidentified',candidate,T,op('and',candidate_call('referent'),unique))
    add('discourseunique',[(n,t) for n,t in candidate if n!='referent'],T,
        q('exists','referent',I,call('discourseidentified',*(v(n) for n,t in candidate))))
    add('referentquestion',[(n,t) for n,t in candidate if n!='referent'],question_sort([I]),
        dict(kind='question',function=lam([('referent',I)],candidate_call('referent'))))
    params=[('index',N),('target',I),('source',I),('reason',I),('evidence',IDENTITY)]
    match=q('exists','referent',I,allof(at(),op('equal',v('referent'),v('target')),
        app('evidence',v('source'),v('reason'),v('referent'),v('target'),v('world'))))
    add('identifyreferent',params,UPDATE,update(op('and',match,continued())))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=defs,statements=[])


@lru_cache(maxsize=1)
def composed():return normalize_document(raw())


MEANINGS={
 'referentat':'参照列の指定位置がその個体を保持する。位置は0始まりの非負整数で、範囲外なら不成立。',
 'referentavailable':'指定位置に参照個体がある。',
 'referenttest':'指定位置に個体があり、その同じ個体が性質を満たすという状態検査を作る。',
 'referentrelation':'指定した二位置が存在し、その同じ主体・対象が関係を満たすという状態検査を作る。',
 'discoursetest':'現在の参照状態で条件を検査し、その状態を変えず後続を評価する更新。',
 'introducereferent':'性質を満たす個体を存在量化し、参照列の末尾に加えた状態で後続を評価する。一意性や既存個体との差異を補わない。',
 'distinctreferent':'性質を満たし、現在の参照列にある全個体と異なる個体を導入する。',
 'aliasreferent':'既存の参照位置にある同じ個体を列末尾にも保持する。個体の新設ではない。',
 'sequencediscourse':'前の更新が後続へ渡す同じ参照状態で次の更新を評価する。存在証人を別々に選び直さない。',
 'closeddiscourse':'内部の更新が成立することを検査し、外側の元の参照状態で後続を評価する。',
 'negateddiscourse':'内部の更新が成立しないことを検査し、内部の参照を外へ出さず後続を評価する。',
 'alternativediscourse':'いずれかの内部更新が成立することを検査する。どちらの枝の新規参照も外へ出さない。',
 'conditionaldiscourse':'前件の各成功状態で後件が成立することを要求する。前件内の参照は後件へ渡し、前件・後件の新規参照は条件全体の外へ出さない。',
 'discourseholds':'指定の初期参照状態と状況で更新全体が成立する。',
 'discoursecandidate':'更新の成功状態のいずれかで、指定位置がその個体を保持する。',
 'discourseidentified':'指定個体が候補であり、同じ位置の全候補がその個体と一致する。',
 'discourseunique':'同じ位置の候補が存在し、一つの個体に限られる。更新の存在成功だけとは区別する。',
 'referentquestion':'同じ更新と参照位置に対して、どの個体が候補であるかを尋ねる型付き質問を作る。答えの存在や一意性を主張しない。',
 'identifyreferent':'指定位置の個体と提示対象が同一であり、その同定が同じ出所・理由・両対象・状況の根拠を満たすという更新。'}
ROLES={
 'state':'現在の有効な束縛を持つ個体の有限列。同じ個体を複数位置に持てる。',
 'initial':'記述の開始前から参照できる個体の有限列。未導入個体を暗黙に追加しない。',
 'index':'この参照状態の位置。語義や辞書の番号ではなく、明示した局所束縛の位置。',
 'referent':'参照位置の候補として調べる個体。','property':'導入または同じ参照個体へ述べる性質。',
 'subjectindex':'関係の主体となる参照位置。','objectindex':'関係の対象となる参照位置。',
 'relation':'同じ主体・対象・評価状況の関係。','condition':'現在の参照列と状況に対する検査。',
 'first':'先に適用する更新または選択肢の左枝。','second':'後に適用する更新または選択肢の右枝。',
 'discourse':'参照状態と状況を後続の検査へ渡す更新。構成子の更新は後続について単調で状況を保存する。',
 'antecedent':'条件の前件。導入された参照は同じ条件の後件内で使える。',
 'consequent':'前件の成功した参照状態ごとに検査する後件。ここでの導入も条件の外へ出さない。',
 'world':'同じ記述を評価する状況。','target':'同定しようとする提示対象。既知の固有名、別の参照、観測対象などを明示する。',
 'source':'同定根拠の出所。','reason':'その同定に用いた理由・証拠の個体。',
 'evidence':'出所・理由・参照個体・提示対象・状況について同定を裏付ける関係。根拠の十分性は明示した入力規約。'}


def basis():
    return dict(status='shared_scoped_discourse_referents',document=LIBRARY,primitives={},definitions=MEANINGS,
        public_contracts={d['name']:dict(arguments=[dict(role=p['name'],sort=p['sort'],interpretation=ROLES[p['name']])
            for p in d['parameters']],result=d['result']) for d in raw()['declarations']},
        design_sources=['docs/spec-v014.md','docs/shared-reference-v1.md','docs/visible-word-formation-v1.md'],
        limitations=['参照状態は言語内の有限列であり、見えない指示対応表ではない。外部世界の個体を創造する処理でもない。',
            '作用範囲と位置は明示する。自然言語の代名詞の候補やアクセス可能性を自動推測しない。',
            '一般の高階関数を更新の型だけで単調・状況保存と認定しない。ここでの構成子から作る更新について解釈する。',
            '条件文は前件の全成功状態を後件で検査する読み。選択肢の導入を外へ持ち出す読みや反事実は別の構成を要する。',
            '同定の根拠を自動証明しない。未知入力は評価拒否し、候補不在や否定へ変換しない。',
            '円文字登録、局所参照を使う学習文書、第三者読解は未完。'])


def prepare():
    for path,text in ((LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')):
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published discourse module differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':prepare()
