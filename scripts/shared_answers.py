"""Explicit positive/negative answer information and typed projections."""
from functools import lru_cache
import json
from noema.constructed import format_graph
from noema.constructed_discourse import normalize_document,function_sort,question_sort
from scripts.shared_modality import ROOT,v,app,call,op
from scripts.shared_reference import I,T,definition,lam
from scripts.shared_time import q,allof

LIBRARY='examples/v016/shared-answers-v1.noema'
BASIS='data/shared-answers-basis-v1.json'
PROPERTY=function_sort([I],T)
RELATION=function_sort([I,I],T)
QUESTION=question_sort([I])
PAIRQUESTION=question_sort([I,I])


def matches(question,*arguments):return dict(kind='answer_matches',question=question,arguments=list(arguments))
def quantified(kind,parameters,body):
    for n,t in reversed(parameters):body=q(kind,n,t,body)
    return body


@lru_cache(maxsize=1)
def raw():
    ds=[]
    def add(name,ps,body,result=T):ds.append(definition(name,ps,result,body))
    for prefix,ps in [('answer',[('candidate',I)]),('pairanswer',[('first',I),('second',I)])]:
        qs=question_sort([t for n,t in ps]);pred=function_sort([t for n,t in ps],T)
        pn=[('positive',pred),('negative',pred)];qp=[('question',qs)]+pn
        xs=[v(n) for n,t in ps];p=app('positive',*xs);n=app('negative',*xs);a=matches(v('question'),*xs)
        forall=lambda body:quantified('forall',ps,body)
        exists=lambda body:quantified('exists',ps,body)
        add(prefix+'consistent',pn,forall(op('not',op('and',p,n))))
        add(prefix+'sound',qp,forall(op('and',op('implies',p,a),op('implies',n,op('not',a)))))
        add(prefix+'informative',pn,exists(op('or',p,n)))
        add(prefix+'covers',[('question',qs),('positive',pred)],forall(op('implies',a,p)))
        complete=allof(call(prefix+'sound',*(v(n) for n,t in qp)),v('closed'),
            call(prefix+'covers',v('question'),v('positive')))
        add(prefix+'complete',qp+[('closed',T)],complete)
        add(prefix+'partial',qp+[('closed',T)],allof(call(prefix+'sound',*(v(n) for n,t in qp)),
            call(prefix+'informative',v('positive'),v('negative')),op('not',v('closed'))))
        add(prefix+'unsettled',pn+ps,op('and',op('not',p),op('not',n)))
        add(prefix+'none',[('question',qs)],forall(op('not',a)))
    pair=matches(v('question'),v('first'),v('second'))
    for name,retained,hidden in [('answerfirstquestion','first','second'),('answersecondquestion','second','first')]:
        add(name,[('question',PAIRQUESTION)],dict(kind='question',function=lam([(retained,I)],q('exists',hidden,I,pair))),QUESTION)
    for name,fixed,remaining in [('answerafterfirst','first','second'),('answerbeforesecond','second','first')]:
        add(name,[('question',PAIRQUESTION),(fixed,I)],dict(kind='question',function=lam([(remaining,I)],pair)),QUESTION)
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[])


@lru_cache(maxsize=1)
def composed():return normalize_document(raw())


BASE_MEANINGS={
 'consistent':'肯定候補と否定候補が重ならない。問いに対して正しいかは別に検査する。',
 'sound':'肯定候補は全て問いの成立条件を満たし、否定候補は全て満たさない。何も述べない空情報も許す。',
 'informative':'肯定または否定した候補が少なくとも一つある。正しさ・新規性・有用性は含意しない。',
 'covers':'問いを満たす全候補が肯定候補に含まれる。余分な肯定候補や、網羅を明言したかは別条件。',
 'complete':'肯定・否定の情報が正しく、全ての答えを肯定候補に含め、これで全てだという明示がある。空の全回答も許す。',
 'partial':'正しく、少なくとも一候補を肯定または否定し、これで全てだとは明示しない回答。偶然全ての答えを含む場合もある。',
 'unsettled':'指定候補は明示した肯定域にも否定域にも属さない。問いの答えでないことや処理系の未知入力とは異なる。',
 'none':'問いを満たす候補がない。質問を提示したことや、まだ候補を述べていないことからは導かない。'}
PROJECTION_MEANINGS={
 'answerfirstquestion':'二個体の問いから、少なくとも一つの第二対象と組になって答えとなる第一対象を尋ねる問いを構成する。答えの存在は主張しない。',
 'answersecondquestion':'二個体の問いから、少なくとも一つの第一対象と組になって答えとなる第二対象を尋ねる問いを構成する。各集合の直積が元の答えとは限らない。',
 'answerafterfirst':'第一対象を固定し、その対象との順序付き組が元の問いを満たす第二対象を尋ねる。',
 'answerbeforesecond':'第二対象を固定し、その対象との順序付き組が元の問いを満たす第一対象を尋ねる。'}
ROLES={
 'question':'今回の評価で条件と文脈を固定した型付きの問い。質問者の意図や提示行為は別に記述する。',
 'positive':'答えだと肯定した候補の範囲。二個体の場合は順序付きの組であり、二つの周辺集合で代用しない。',
 'negative':'答えではないと明示した候補の範囲。肯定域の補集合を自動設定しない。',
 'closed':'肯定した候補が全回答だという明示。実際に網羅しているかとは別の真偽入力。',
 'candidate':'一個体の問いについて照合する候補。',
 'first':'答えの第一対象。第二対象との順序を保持する。',
 'second':'答えの第二対象。第一対象との順序を保持する。'}
LIMITS=[
 '公開する型は一個体と二個体の問い。既存のquestion/answer_matchesは任意の有限個数・型を扱うが、この二型の検査を全ての型の証明へ拡張しない。別型への同じ構成は明示的な型付き定義として行う。',
 '問いと肯定/否定域は明示した文脈で固定する。自然言語から回答範囲・網羅の意図を推測しない。正しさと、実際に提示・受諾されたことを区別する。',
 'partialは網羅を明言しない正しい非空情報であり、実際に不足しているという意味ではない。completeは明示された全回答の検証で、coversだけでは全回答という発話にならない。',
 'unsettledは明示情報の外にある既知候補。未知の解釈は評価拒否であり、否定や未回答の偽へ変換しない。informativeは新情報量や有用性を測らない。',
 '二対象の射影は相手を存在量化する。第一・第二の候補集合だけから対応関係を復元しない。固定対象への問いは元の組の対応を保持する。',
 '有限モデルは無限領域の評価器ではない。数値等の無限領域での全回答を有限標本で代用しない。引用した回答内容の真理と、回答としての提示・受諾・訂正・撤回は別条件。会話状態更新は後続課題。']


def basis():
    meanings={prefix+suffix:('一個体の問い：' if prefix=='answer' else '順序付き二個体の問い：')+body
        for prefix in ('answer','pairanswer') for suffix,body in BASE_MEANINGS.items()}
    meanings.update(PROJECTION_MEANINGS)
    contracts={d['name']:dict(arguments=[dict(role=p['name'],sort=p['sort'],interpretation=ROLES[p['name']])
        for p in d['parameters']],result=d['result']) for d in raw()['declarations']}
    return dict(status='shared_explicit_partial_and_exhaustive_answers',document=LIBRARY,primitives={},
        definitions=meanings,public_contracts=contracts,limitations=LIMITS)


def prepare():
    for path,text in ((LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')):
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published answers differ: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':prepare()
