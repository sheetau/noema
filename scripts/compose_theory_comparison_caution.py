"""Describe a guarded comparison procedure separately from a requirement to use it."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_convention_comparison import ROOT,CUT
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,both,op,quant
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-convention-comparison.noema'
SOURCE='examples/v014/einstein-theory-comparison-caution.noema'
LIBRARY='examples/v014/theory-comparison-caution.noema'
CORE='examples/v014/theory-comparison-caution-core.noema'
PAIR='h[a a d] c';VALUE='h[a a a d] '+CUT
DESCRIPTION='i[h[a a] e]';REQUIRED='h[a a a a '+DESCRIPTION+' c d] c'
ASSESS=[(n,PAIR) for n in ('interpretations','meanings','units')]+[('corresponds','h[a a a d] c')]+[(n,VALUE) for n in ('leftvalue','rightvalue')]
POLICY=[('cases',PAIR),('concludes',PAIR)]+ASSESS
METADATA=[(n,'h[a] a') for n in ('actor','left','right','topic')]
NORMS=[('authority','a'),('role','a'),('subject','a'),('context','d'),('comparisons','h[a d] c')]+METADATA+[('description',DESCRIPTION),('required',REQUIRED)]
ROOTS=['seqk','seql','seqm','seqn','seqo','seqp']
READING='data/theory-comparison-caution-reading-v1.json'


def definitions():
    activity,case,context,interpretation=map(v,('activity','case','context','interpretation'))
    selected=app(v('interpretations'),activity,interpretation,context)
    left=app(v('leftvalue'),activity,interpretation,case,context);right=app(v('rightvalue'),activity,interpretation,case,context)
    acceptable=both(app(v('meanings'),activity,interpretation,context),app(v('units'),activity,interpretation,context),
        app(v('corresponds'),activity,interpretation,case,context),k('ba',left),k('ba',right),op('u',k('sca',left,right)))
    text=definition('seqk',params([('activity','a'),('case','a'),('context','d')]+ASSESS),both(
        quant('g','interpretation','a',selected),quant('f','interpretation','a',op('y',selected,acceptable))))
    guarded=both(app(v('cases'),activity,case,context),k('seqk',activity,case,context,*args(ASSESS)))
    text+=definition('seql',params([('activity','a'),('context','d')]+POLICY),
        quant('f','case','a',op('y',app(v('concludes'),activity,case,context),guarded)))
    fields=[('person','a'),('activity','a'),('subject','a'),('context','d')]+METADATA+POLICY
    text+=definition('seqm',params(fields),both(op('e',app(v('actor'),activity),v('person')),
        op('e',app(v('topic'),activity),v('subject')),op('u',op('e',app(v('left'),activity),app(v('right'),activity))),
        k('seql',activity,context,*args(POLICY))))
    condition=both(app(v('comparisons'),activity,context),op('e',app(v('topic'),activity),v('subject')),
        op('u',op('e',app(v('left'),activity),app(v('right'),activity))))
    true=op('e','n p a b','n p a b')
    requirement=app(v('required'),v('authority'),app(v('actor'),activity),v('role'),activity,v('description'),true,context)
    text+=definition('seqo',params(NORMS),quant('f','activity','a',op('y',condition,requirement)))
    return text


MEANINGS={
    'seqk':'同じ比較活動・事例・文脈について、採用する解釈候補が非空で、全候補が意味・単位・事例の対応条件を満たし、正規化された二値が異なる。解釈の一つで差が消える場合は、ここでの不一致判定を保留する。',
    'seql':'比較活動で不一致と結論する全事例について、その事例が評価範囲内でありseqkを満たすという手続き上の条件。結論を保留することを許し、必ず不一致を発見せよとは要求しない。',
    'seqm':'同じ比較活動の主体・対象領域・異なる二つの比較対象を固定し、seqlの手続き条件を満たす。数値だけを見た判定と、意味・単位・事例の対応を伴う判定を分ける。',
    'seqn':'電子の運動を対象とする比較活動について、主体と活動を引数にしてseqmの内容を作る。要求の対象となる手続きを指す記述であり、要求があるだけではその実行は成立しない。',
    'seqo':'指定領域の異なる対象を比較する全活動について、同じ出所・主体・立場・活動・手続き記述・極性・文脈への要求を述べる。記述された手続きの実際の真偽や規範の正当性は評価しない。',
    'seqp':'u0259後半の慎重な比較への要求を、seqnの手続き記述を対象とするseqoで部分的に具体化した内容。慎重さ一般やsehrの程度をこの条件だけで定義したものではない。',
}
LIMITS=[
    '慎重さの一部を、未整理の数値差だけから不一致と結論しない手続きとして具体化した解釈注記である。原文にこの検査項目が列挙されているという主張や、唯一の慎重さの定義ではない。',
    '意味対応・単位正規化・同じ物理事例への対応と、解釈候補の選定・完全性は明示した入力である。これらを実際に検証する一般手順、理論の全内容や電子の運動の概念構成は未完。',
    '数値差は比較条件の下での予測の不一致を示すにとどまる。理論全体の論理的矛盾・誤り・優劣を自動判定せず、近似・誤差幅のある比較は別の対応関係を必要とする。',
    '要求を記述するだけで現実の遵守や比較活動の存在を補わない。結論を出さない活動では手続き条件が成立し得るが、著者の要求が存在することとは別である。',
    'man ersieht darausは前半の記述から要求を導くという著者への推論帰属として接続する。数学的な事実だけから規範が論理的に導けると証明したわけではない。Natürlichの自明性、sehrの程度、後半全体の意味一致は未完。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    values={
        'zrcsubject':('a','この箇所で比較の対象領域となる電子の運動への参照。理論の内容や運動の基礎説明をこの名前だけで完成とはしない。'),
        'zrcrole':('a','この比較を行う者という方法上の立場。実際の職位や制度上の権限ではない。'),
        'zrcnode':('a','u0259後半で、前半から比較上の注意を導く箇所。'),
        'zrcscope':('a','力と加速度の規約による数値の差を踏まえて電子の運動の理論を比較する議論の範囲。')}
    relations={
        'zrccomparisons':(['activity','context'],'a d','比較方法上の要求を適用する活動の範囲。実行済みの一覧だけには限定しない。'),
        'zrcmust':(['authority','person','role','activity','description','polarity','context'],'a a a a '+DESCRIPTION+' c d','指定された同じ主体・活動・手続き記述の指定極性を満たすという比較方法上の要求。要求の存在と遵守を区別する。')}
    funcs={n:'zrc'+n for n,_ in METADATA+POLICY}
    for n,sort in METADATA+POLICY:
        meaning={
            'actor':'比較活動を担う主体。', 'left':'比較活動の一方の理論への参照。', 'right':'同じ比較活動の他方の理論への参照。', 'topic':'比較活動の対象領域への参照。',
            'cases':'比較活動で対象にする物理事例の範囲。', 'concludes':'その活動でその事例について不一致との判定を行う関係。',
            'interpretations':'その比較活動と文脈で採用すべき意味解釈の候補。判定結果の良否だけで選ぶものではなく、選定理由は未展開。',
            'meanings':'指定候補で、両理論の比較する量・規約の意味の対応が確認されている関係。',
            'units':'指定候補で、両理論の数値が共通単位へ正規化されている関係。',
            'corresponds':'同じ比較活動と解釈候補の両評価が、同じ物理事例・条件に対応している関係。',
            'leftvalue':'同じ比較活動・候補解釈・事例・文脈における、一方の理論の正規化した値。',
            'rightvalue':'同じ比較活動・候補解釈・事例・文脈における、他方の理論の正規化した値。'}[n]
        values[funcs[n]]=(sort,meaning)
    text=definitions()+''.join('r '+name+'[] '+sort+'.' for name,(sort,_) in values.items())
    text+=''.join('r '+name+'['+sort+'] c.' for name,(_,sort,_) in relations.items())
    fixed=[v('person'),v('activity'),k('zrcsubject'),v('context')]+[k(funcs[n]) for n,_ in METADATA+POLICY]
    text+=definition('seqn','person a activity a','b context['+k('seqm',*fixed)+']','e')
    norm=[k('rd'),k('zrcrole'),k('zrcsubject'),v('context'),'p zrccomparisons']+[k(funcs[n]) for n,_ in METADATA]+['r[p seqn]','p zrcmust']
    text+=definition('seqp','','b context['+k('seqo',*norm)+']','e')
    doc=parse(format_graph(doc,'compact')+text)
    new=parse(format_graph(doc,'compact')+'s[k zc[k zrcnode[] k rd[] r[k seqj[]] r[k seqp[]] k zrcscope[] k ri[]]].')['statements']
    doc['statements']=old['statements']+new
    basis=json.loads((ROOT/'data/einstein-convention-comparison-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-theory-comparison-caution-basis-v1',document=SOURCE)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;lookup={d['name']:d for d in doc['declarations']}
    for name,(_,meaning) in values.items():
        d=lookup[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    for name,(arguments,_,meaning) in relations.items():
        d=lookup[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=arguments,meaning_ja=meaning))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-theory-comparison-caution-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,['seqk','seql','seqm','seqo'],[]),(CORE,[],[len(old['statements'])])):
        selected=extract_document(doc,roots=roots,statement_indices=indices);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p:t if isinstance(t,str) else json.dumps(t,ensure_ascii=False,indent=2)+'\n' for p,t in files.items()}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body),flush=True)


if __name__=='__main__':main()
