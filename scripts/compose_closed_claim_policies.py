"""Compile a literal catalogue of claims into an ordinary rank-zero policy."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_specialization import specialize_definition
from scripts.compose_claim_conformance import ROOT,SOURCE as PARENT,DESCRIPTION,RULE,TRUE,IDENTITY,params,av
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure

LIBRARY='examples/v016/closed-claim-policies.noema'
SOURCE='examples/v016/kant-closed-claim-policies.noema'
CORE='examples/v016/closed-claim-policies-core.noema'
EXAMPLE='examples/v016/closed-claim-policies-example.noema'
BASIS='data/closed-claim-policies-basis-v1.json'
ITEM=IDENTITY+[('target',DESCRIPTION),('context','d'),('required',RULE)]
CATALOGUE=IDENTITY+[('targets','j['+DESCRIPTION+']'),('context','d'),('required',RULE)]
POLICY=IDENTITY[:3]+[('people','j[a]'),('scope','h[a] c'),('targets','j['+DESCRIPTION+']'),('cases','h[d] c'),('required',RULE)]


def norm(context):
    return app(v('required'),v('source'),v('actor'),v('office'),v('target'),'l[a][v actor v person]',TRUE,v(context))


def definitions():
    actual=op('t',app('s[v target]','l[a][v actor v person]'),v('context'))
    text=definition('ryg',params(ITEM),both(norm('context'),actual))
    fold='q[v targets]['+TRUE+'][i[ok c target '+DESCRIPTION+']['+both(v('ok'),k('ryg',*av(ITEM)))+']]'
    nonempty=op('u',op('e','d[v targets]','n p a b'))
    text+=definition('ryh',params(CATALOGUE),both(nonempty,fold))
    stable='q[v targets]['+TRUE+'][i[ok c target '+DESCRIPTION+']['+both(v('ok'),norm('candidate'))+']]'
    person=both(quant('f','candidate','d',op('y',app(v('cases'),v('candidate')),stable)),k('ryh',*av(CATALOGUE)))
    content=both(op('e','d[v bindings]','n p a b'),k('rcm',v('people'),v('scope')),
        quant('g','candidate','d',app(v('cases'),v('candidate'))),
        quant('f','person','a',op('y',app(v('scope'),v('person')),person)))
    text+=definition('ryi',params(POLICY),'i[bindings j[a]][b context['+content+']]','h[j[a]] e')
    return text


def example_base(text):
    extra='''
r jvsource[] a.r jvactor[] a.r jvoffice[] a.r jvperson[] a.r jvnow[] d.
r jvscope[a] c.r jvcases[d] c.r jvcontent[a a a d] c.r jvfirst[] a.r jvsecond[] a.
'''
    extra+='r jvrequired['+RULE[2:-3]+'] c.'
    for name,claim in (('jvone','jvfirst'),('jvtwo','jvsecond')):
        extra+='d '+name+'[bindings j[a]] e[b context[w[e[d[v bindings]][n p c b]][g actor a[g person a[w[a[v bindings][n p a b][v actor]][w[a[v bindings][n p b b][v person]][k jvcontent[k '+claim+'[] v actor v person v context]]]]]]]].'
    extra+='d jvalias[bindings j[a]] e[k jvone[v bindings]].'
    return parse(text+extra)


def catalogue(names,element):
    return dict(kind='sequence',element=deepcopy(element),
        items=[dict(kind='quote',body=dict(kind='function_ref',symbol=name),rank=0) for name in names])


def example(text,names=('jvone','jvtwo')):
    doc=example_base(text)
    # Obtain the canonical sequence type from the checked parameter itself.
    target_type=next(d for d in doc['declarations'] if d['name']=='ryi')['parameters'][5]['sort']
    targets=catalogue(names,target_type['element'])
    result=specialize_definition(doc,'ryi','jvclosed',{5:targets})
    args='k jvsource[] k jvactor[] k jvoffice[] l[a][k jvperson[]] p jvscope '
    before=args+'l['+DESCRIPTION+']['+' '.join('r[p '+name+']' for name in names)+'] p jvcases p jvrequired'
    after=args+'p jvcases p jvrequired'
    extra='d jvpolicy[bindings j[a]] e[c[k jvclosed['+after+']][v bindings]].'
    extra+='q[t[c[k ryi['+before+']][l[a][]]][k jvnow[]]].'
    extra+='q[t[k jvpolicy[l[a][]]][k jvnow[]]].q[e[r[p jvpolicy]][r[p jvpolicy]]].'
    return parse(format_graph(result.document,'compact')+extra),result


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['rcm'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['ryg','ryh','ryi'])
    demo,_=example(format_graph(lib,'compact'))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core),(EXAMPLE,demo))}


def basis():
    return dict(status='literal_claim_catalogue_compiled_to_rank_zero_policy',parent=PARENT,document=SOURCE,
        definitions={
            'ryg':'同じ出所・行為主体・職務・本人に関する一つの基準内容への要求と、同じ内容の実際の履行を結ぶ。二個体列の順序を保つ。',
            'ryh':'明示した非空の基準記述列の全要素についてrygが成立する。記述の同一性を保持し、同義の別名へ要求を移さない。',
            'ryi':'非空で完全列挙した対象者と非空の比較状況について、同じ基準列への要求の維持と現在の要求・履行を内容とする。外側の引数列は空であることを要求する。',
            'jvclosed/jvpolicy':'作例で明示した二つのNoema記述をryiへ束縛し、既知の引用の脱引用と有限の畳み込みを展開した通常の階数0の定義。元の一般形も保存する。'},
        limitations=[
            'この構成は基準内容の具体化ではなく、既知のNoema定義を政策へ接続するための言語機能である。作例の基準内容を尊厳の定義や原文の具体的要求へ置き換えない。',
            '基準列は記述の順序と重複を保持する。重複だけで意味が増えるとはせず、一覧外の基準を尽くすことも自動証明しない。対象者の一覧はrcmにより別に完全性を検査する。',
            '現行版の特殊化は、静的に既知の階数0引用とリテラルの有限列に限定する。未知の記述を推測せず、高階数の脱引用を下位へ移さず、通常の型検査と引用検査を最後にも行う。',
            '展開は原始関係を実行しない。意味の比較は全域的・純粋でNoemaの値に従う解釈について行い、評価順序・実行時間・副作用・未知値での停止順序の一致までは主張しない。展開量と深さに上限がある。',
            '原始語の定義、具体的な尊厳の基準、政府の資格、人間と機械の対比、原文全体との意味一致は未完である。新しい原文範囲・著者主張・意味確認済み区間を加算しない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
