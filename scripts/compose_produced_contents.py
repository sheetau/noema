"""Use the same closed content for causal attribution and achieved result."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/kant-continuing-institutions.noema'
PRODUCES='h[a i[e] d] c'
ACT=[('agents','h[a] c'),('act','a'),('result','i[e]'),('context','d'),
    ('occurs','h[a d] c'),('participates','h[a a d] c'),('produces',PRODUCES)]
CONTENT=[(n,t) for n,t in ACT if n not in ('act','context')]
SOURCE=[(n,t) for n,t in CONTENT if n not in ('occurs','participates')]
ROOTS=['rig','rih']


def definitions():
    agents=lambda n:app(v('agents'),v(n))
    body=both(quant('g','agent','a',agents('agent')),app(v('occurs'),v('act'),v('context')),
        quant('f','agent','a',op('y',agents('agent'),app(v('participates'),v('agent'),v('act'),v('context')))),
        app(v('produces'),v('act'),v('result'),v('context')),op('t','s[v result]',v('context')))
    text=definition('rig',params(ACT),body)
    text+=definition('rih',params(CONTENT),'b context['+quant('g','act','a',k('rig',*args(ACT)))+']','e')
    return text


MEANINGS={
    'rig':'非空の指定行為者群の全員が同じ生起する行為に参加し、その同じ行為が同じ閉じた内容記述を結果として生じさせ、記述された内容がその文脈で成立する。因果関係に渡した記述そのものを脱引用して評価し、独立した別の結果値へ交換しない。',
    'rih':'rigを満たす同じ行為が存在するという内容。目的、試み、因果関係の説明への採用とは区別し、全行為者が単独で十分な原因であることや、唯一の原因を要求しない。',
}
LIMITS=[
    'producesは、その行為が指定した閉じた内容を結果として生じさせるという因果関係を与える引数。単なる同時成立・先行・当事者の説明とは区別する。機構や因果推論をこの関係の指定だけで解決したとはしない。',
    '旧g3は人についての状態という意味規約なので、組織の状態へ暗黙に拡張しない。hzcqでは一般の閉じた内容へのproducesを明示した解釈として受け取る。',
    '同じ状況の行為と結果を結ぶ粒度を採用し、時間遅れ、過程内部、前に結果が偽だったこと、行為の意図、単独の十分原因性は追加しない。結果の内容自体には将来の持続を記述できる。',
    '結果記述の別名や別対象への因果を元の結果へ自動移送しない。rigとrihは動的な脱引用を含むため、そのまま引用できない。既知の閉じた結果を固定し、静的な特殊化を行った定義は通常のNoemaとして引用できる。',
    '特殊化は基準内容や因果関係を実行・生成せず、閉じた記述の脱引用を式へ展開する。値の一致は純粋で全域的な解釈について扱い、副作用や実行順を観察する実装を含まない。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    humans=quant('f','agent','a',op('y',app(v('agents'),v('agent')),k('aa',v('agent'))))
    actual=op('t',k('rih',*args(CONTENT,occurs='p dg',participates='p df')),v('context'))
    extra=definitions()+definition('hzcq',params(SOURCE),'b context['+both(humans,actual)+']','e')
    doc=parse(format_graph(doc,'compact')+extra);doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-continuing-institutions-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-produced-contents-basis-v1',document='examples/v014/kant-produced-contents.noema')
    basis['definitions'].update(MEANINGS|{'hzcq':'指定行為者全員を人aaとし、rihの行為の生起をdg、参加をdfへ接続する内容。結果記述は既存の持続hzcn・hzco・hzcpなどの閉じた適用式で指定できる。因果関係は意味を明示したproducesを受け取り、既存の人の状態に限定されたg3で代用しない。'})
    basis['unresolved']+=LIMITS+['u0013のverewigenへの、持続を結果として生じさせる目的内容の部分接続。どの時間的強さを採るか、監督の機構・宣誓・制度的な資格、so garの強調、著者の問いと判断への帰属は未完。実際に永続化が起きたとの主張は追加しない。']
    audit_basis(doc,basis);return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS,'produced-contents')
def core_composed():return projected(ROOTS+['hzcq','hzcn','hzco','hzcp','hzck','hzcl','hzcm'],'produced-contents-core')
BUILDERS=((generic_composed,'produced-contents'),(source_composed,'kant-produced-contents'),(core_composed,'produced-contents-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored produced content differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
