"""Compose arbitrarily small nonzero additions and their possible outcomes."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_convention_comparison import ROOT,CUT
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,both,op,quant,ZERO
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-theory-comparison-caution.noema'
SOURCE='examples/v014/einstein-arbitrary-small-charge.noema'
LIBRARY='examples/v014/arbitrary-small-charge.noema'
CORE='examples/v014/arbitrary-small-charge-core.noema'
READING='data/arbitrary-small-charge-reading-v1.json'
FIELDS=[('pointlike','h[a d] c'),('charge','h[a a d] '+CUT),
    ('amount','h[a a a d d] '+CUT),('possible','h[a a d d] c'),
    ('added','h[a a a '+CUT+' d d] c')]
BASE=[('point','a'),('unit','a'),('context','d')]
SYMBOLS={n:'zrd'+n for n,_ in FIELDS}


def definitions():
    quantity,bound=v('quantity'),v('bound');zero=k('bb',ZERO);eps=k('bb',bound)
    text=definition('seqr',params([('quantity',CUT),('bound','b')]),both(
        k('aa',ZERO,bound),k('ba',quantity),op('u',k('sca',quantity,zero)),
        k('bg',k('bf',zero,eps),quantity),k('bg',quantity,eps)))
    point,unit,context,operation,alternative=map(v,('point','unit','context','operation','alternative'))
    charge=lambda scene:app(v('charge'),point,unit,scene)
    text+=definition('seqs',params(BASE+FIELDS[:2]),both(app(v('pointlike'),point,context),
        k('ba',charge(context)),op('u',k('sca',charge(context),zero))))
    amount=app(v('amount'),operation,point,unit,context,alternative)
    text+=definition('seqt',params(BASE+[('bound','b'),('operation','a'),('alternative','d')]+FIELDS),both(
        app(v('pointlike'),point,context),k('ba',charge(context)),
        app(v('possible'),operation,point,context,alternative),
        app(v('added'),operation,point,unit,amount,context,alternative),k('seqr',amount,bound),
        k('seqs',point,unit,alternative,*args(FIELDS[:2])),
        k('sca',charge(alternative),k('bd',charge(context),amount))))
    text+=definition('sequ',params(BASE+[('bound','b')]+FIELDS),quant('g','operation','a',
        quant('g','alternative','d',k('seqt',*args(BASE),bound,operation,alternative,*args(FIELDS)))))
    text+=definition('seqv',params(BASE+FIELDS),quant('f','bound','b',op('y',k('aa',ZERO,bound),
        k('sequ',*args(BASE),bound,*args(FIELDS)))))
    text+=definition('seqx','quantity b bound b',both(k('aa',ZERO,bound),op('u',op('e',quantity,ZERO)),
        k('aa',k('ac',bound),quantity),k('aa',quantity,bound)))
    return text


MEANINGS={
    'seqr':'指定した正の有理数上限より絶対値が小さく、零でない実切断。負の電荷も許し、上限との等号と零を除く。',
    'seqs':'同じ単位・文脈で零でない電荷を持つ点状の対象。この箇所の著者の電子という呼称に対応する候補であり、現代の特定粒子種を定義しない。',
    'seqt':'同じ対象・単位への追加量がseqrを満たし、その操作と対象に許容された結果状況で、元の電荷と追加量の和が結果の電荷となり、seqsを満たす。元の中性は仮定せず、零への相殺を成功としない。',
    'sequ':'指定上限に対してseqtを満たす操作と結果状況が存在する。現実の実行や、全ての実行結果での成功は主張しない。',
    'seqv':'どの正の有理数上限を与えてもsequを満たす。同じ対象・単位・元の状況を保ち、操作と結果は上限に依存してよい。一つの固定電荷や有限標本でこの全称条件を代用しない。',
    'seqw':'著者が対象とする全てのponderableな物質点について、同じ電荷単位でseqvの可能性を述べるu0260後半の部分内容。質量の式の適用拡張をこの内容だけから証明しない。',
    'seqx':'seqrの有理数版。数量の絶対値と正の上限の厳密な大小を表す。',
}
LIMITS=[
    '任意に小さいを、全ての正の有理数上限に対する存在として記述する。実数の正の上限にも有理数の正の下界があるという性質を使う表現であり、有限の小数標本への制限ではない。全実切断についてのその性質の機械的証明は未実装。',
    '点状・ponderableな物質点・電荷の帰属・電荷を加える操作と物理的に可能な結果の関係は明示した基礎入力である。操作の存在、電荷の連続的な可分性、測定・物理法則の真偽を言語処理系が保証するものではない。',
    'ここでいう電子は著者の点状の荷電対象という呼称に限定する。現代の電子という粒子種への変化や、無電荷からの粒子生成を補わない。',
    '選んだ可能な結果での成功を表し、全結果での成功を保証する能力・制御可能性は追加しない。元と結果の対象同一性は引数で保持する。',
    'u0260の後半の可能性に部分対応する。前半の質量結果への適用拡張とdennの理由接続、物理的な妥当性と原文全体の意味一致は未完である。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    values={SYMBOLS[n]:(sort,meaning) for (n,sort),meaning in zip(FIELDS,[
        '対象がこの文脈で点状の物体として扱われるという条件。座標点だけで物体と認定しない。',
        '同じ対象・電荷単位・状況に帰属する符号付き電荷の値。',
        '操作・対象・電荷単位・元の状況・結果状況ごとの追加電荷。',
        'その対象へのその操作について、元の状況から物理的に可能と指定する結果状況。現実に生じたとの主張とは分ける。',
        '同じ操作・対象・単位・追加量・元の状況・結果状況についての電荷追加。数値の差だけで操作が行われたと認定しない。'])}
    values.update(zrdnode=('a','u0260後半の可能性を述べる箇所。'),zrdscope=('a','同じ箇所の物質点と電荷追加に関する議論の範囲。'))
    text=definitions()+''.join('r '+n+'[] '+sort+'.' for n,(sort,_) in values.items())
    text+='r zrdmaterial[a d] c.'
    text+=definition('seqw','','b context['+quant('f','point','a',op('y',k('zrdmaterial',v('point'),v('context')),
        k('seqv',v('point'),k('zqk'),v('context'),*[k(SYMBOLS[n]) for n,_ in FIELDS])))+']','e')
    doc=parse(format_graph(doc,'compact')+text)
    new=parse(format_graph(doc,'compact')+'s[k uh[k zrdnode[] k rd[] r[k seqw[]] k zrdscope[] k ri[]]].')['statements']
    doc['statements']=old['statements']+new
    basis=json.loads((ROOT/'data/einstein-theory-comparison-caution-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-arbitrary-small-charge-basis-v1',document=SOURCE)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;lookup={d['name']:d for d in doc['declarations']}
    for name,(_,meaning) in values.items():
        d=lookup[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    d=lookup['zrdmaterial'];basis['primitives'].append(dict(symbol=d['name'],parameters=d['parameters'],result=d['result'],
        arguments=['point','context'],meaning_ja='著者がこの主張の範囲とするponderableな物質点。質量を持つ物体の基礎説明と点状近似の妥当性は未展開。'))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-arbitrary-small-charge-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,['seqr','seqs','seqt','sequ','seqv','seqx'],[]),(CORE,[],[len(old['statements'])])):
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
