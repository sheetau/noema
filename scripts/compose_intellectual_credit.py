"""Compose received intellectual input and nonfactive credit for its value."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.extraction import extract_document, extract_basis
from noema.meaning_basis import audit_basis
from noema.linking import relocate
from noema.specialization import specialize_definition
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, both, op, quant
from scripts.compose_situated_criticism import params, args
from scripts.compose_personal_criteria import APPRAISAL, JUDGING, DESCRIPTION

PARENT = 'examples/v014/einstein-law-characterization.noema'
JUDGMENT = 'examples/v014/personal-criteria.noema'
SOURCE = 'examples/v014/einstein-intellectual-credit.noema'
LIBRARY = 'examples/v014/intellectual-credit.noema'
CORE = 'examples/v014/intellectual-credit-core.noema'
READING = 'data/intellectual-credit-reading-v1.json'
SLOTS = [('recipient','a'), ('giver','a'), ('input','a'), ('work','a')]
RELATIONS = [('occurs','h[a d] c'), ('performs','h[a a d] c'),
    ('produces','h[a a d] c'), ('uses','h[a a a d] c'),
    ('standard','h[a a a d] c'), ('meets','h[a a d] c')]
FIELDS = SLOTS + [('context','d')] + RELATIONS
CREDIT = SLOTS + [('criterion',DESCRIPTION), ('context','d')] + JUDGING
SEVERAL = [(n,t) for n,t in CREDIT if n != 'input']


def reused_judgment():
    source = parse((ROOT/JUDGMENT).read_text(encoding='utf-8'))
    return relocate(next(d for d in source['declarations'] if d['name']=='rlg'), {'rlg':'sewb'})


def definitions():
    context=v('context')
    contribution=quant('g','event','a',both(
        app(v('occurs'),v('event'),context),
        app(v('performs'),v('giver'),v('event'),context),
        app(v('produces'),v('event'),v('input'),context),
        app(v('uses'),v('recipient'),v('input'),v('work'),context)))
    text=definition('sewc',params(FIELDS),contribution)
    text+=definition('sewd',params(FIELDS),quant('g','measure','a',both(
        app(v('standard'),v('recipient'),v('work'),v('measure'),context),
        app(v('meets'),v('input'),v('measure'),context))))
    text+=definition('sewe',params(FIELDS),both(k('sewc',*args(FIELDS)),k('sewd',*args(FIELDS))))
    text+=definition('sewf',params(RELATIONS),'i['+params(SLOTS)+'][b context['+k('sewe',*args(FIELDS))+']]', 'h[a a a a] e')
    initial='i['+params(SLOTS)+']['+app(v('relation'),*args(SLOTS))+']'
    shifted='i['+params(SLOTS)+']['+app(v('state'),v('item'),v('recipient'),v('giver'),v('input'))+']'
    folded='q[v bindings]['+initial+'][i[state h[a a a a] e item a]['+shifted+']]'
    text+=definition('sewg','relation h[a a a a] e','i[bindings j[a]][b context['+both(
        op('e','d[v bindings]','n p e b'),quant('g','seed','a',op('t',app(folded,*[v('seed')]*4),context)))+']]', 'h[j[a]] e')
    judgment=k('sewb',*args(APPRAISAL,person=v('recipient'),subject=v('giver'),
        bindings='l[a]['+' '.join(args(SLOTS))+']'))
    text+=definition('sewh',params(CREDIT),quant('g','judgment','a',judgment))
    text+=definition('sewi',params(SEVERAL),quant('g','first','a',quant('g','second','a',both(
        op('u',op('e',v('first'),v('second'))),
        k('sewh',*args(CREDIT,input=v('first'))),k('sewh',*args(CREDIT,input=v('second')))))))
    return text


MEANINGS={
    'sewb':'既存rlgを衝突しない名へ移した判断構成。同じ本人・対象・基準記述・順序付き引数を結び、非空の候補状況全てで内容が成立する。現実の真偽とは分ける。',
    'sewc':'ある行為が起こり、寄与者がそれを行い、そこから生じた同じ入力を受け手が同じ仕事の思考に用いる。入力の真実性、命令や採用提案であること、唯一の起源であることは要求しない。',
    'sewd':'同じ受け手が同じ仕事について採用する肯定的な評価基準の少なくとも一つを、同じ入力が満たす。基準の普遍的妥当性や全基準の充足を意味しない。',
    'sewe':'同じ入力について、同じ相手からの寄与sewcと仕事に相対的な肯定的評価sewdが成立する。',
    'sewf':'寄与と評価の関係を固定し、受け手・寄与者・入力・仕事の四引数から内容を作る。',
    'sewg':'四引数の内容を同じ順序の個体列へ接続する。長さ四を要求し、順序と重複を保持する。',
    'sewh':'受け手が寄与者について同じ基準記述と四引数列を判断内容として採用する。任意の基準を受け取り、それだけでは寄与の認識に限定しない。',
    'sewi':'互いに異なる少なくとも二つの入力について、同じ受け手・相手・仕事・基準記述の判断がある。判断記録二件だけで同じ入力を二つに数えない。正確に二つという上限は付けない。',
    'sewj':'本文の寄与・思考上の使用・評価基準を固定した四引数の基準。判断の内容として静的に引用する。',
    'sewk':'著者が同じ仕事に関する少なくとも二つの有益な入力をM. Bessoの寄与として認める、というu0276後半の候補内容。実際の寄与の独立した証明ではない。',
    'sewl':'sewkの既知の基準引用を静的に展開した、著者帰属として引用できる内容。実行時の未知の記述を展開しない。',
}
LIMITS=[
    'Anregungを仕事の思考に使われる入力として具体化する候補である。刺激、問い、方向づけを含み、真なる命題や採用を求める提案だけへ限定しない。ただし思考上の使用の機構自体は原始関係に残る。',
    '肯定的評価は本人の仕事に相対的な基準充足として扱う。基準の内容・採用や価値の基礎説明は未完であり、一語に原始記号を割り当てて説明を完了したとは扱わない。',
    'verdankenの寄与の認識を記述する。金銭債務・返礼義務・好意の感情・感謝の発話行為を自動的に付加しない。虚偽の帰属も記述でき、現実での寄与seweは別に検査する。',
    'mancheの複数性を少なくとも二つと読む候補である。多さの程度、過去時制、談話上の結びと謝辞の語用は未完。友人・同僚・忠実な支援を述べる前半は今回の対応範囲に含めない。',
    '固有名M. Bessoは同じ個体への原文ラベルとして記録する。文字列だけから人物の同一性や性質を推定しない。独立した命名行為の分析と全文の意味確認は未完。',
    '候補状況による判断の既存の限界を引き継ぐ。有限試験は認識一般や歴史上の寄与を証明しない。原始的な行為・産出・思考上の使用の構成説明と時間関係は残る。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    doc['declarations'].append(reused_judgment())
    values={
        'zrqperson':('a','原文M. Bessoが指す同じ人物。'),
        'zrqwork':('a','u0276でここに扱った問題への仕事として指される同じ研究。'),
        'zrqnode':('a','u0276後半で寄与を認める主張箇所。'),
        'zrqscope':('a','u0276の謝辞の議論の範囲。'),
    }
    explanations={
        'occurs':'行為が文脈で起こる。','performs':'人物が同じ行為を行う。',
        'produces':'同じ行為から同じ入力が生じる。唯一の起源や著作権を意味しない。',
        'uses':'受け手が同じ入力を同じ仕事の思考に取り入れる。単なる物理的受信と分ける。',
        'standard':'受け手が同じ仕事に関して肯定的評価に用いる基準。',
        'meets':'同じ入力が同じ評価基準を満たす。',
        'judgments':'本人の判断の帰属。','matters':'判断が対象とする相手。',
        'linked':'判断の同じ基準記述と順序付き引数列。',
        'candidates':'判断がその文脈で採用する候補状況。現実と一致するとは限らない。',
    }
    values.update({'zrq'+n:(sort,explanations[n]) for n,sort in RELATIONS+JUDGING})
    extra=definitions()+''.join('r '+n+'[] '+sort+'.' for n,(sort,_) in values.items())
    extra+=definition('sewj','',k('sewg',k('sewf',*[k('zrq'+n) for n,_ in RELATIONS])),'h[j[a]] e')
    extra+=definition('sewk','','b context['+k('sewi',k('rd'),k('zrqperson'),k('zrqwork'),
        'r[k sewj[]]',v('context'),*[k('zrq'+n) for n,_ in JUDGING])+']','e')
    doc=parse(format_graph(doc,'compact')+extra)
    doc=specialize_definition(doc,'sewk','sewl',{}).document
    statement='s[k uh[k zrqnode[] k rd[] r[k sewl[]] k zrqscope[] k ri[]]].'
    doc['statements']=old['statements']+parse(format_graph(doc,'compact')+statement)['statements']
    basis=json.loads((ROOT/'data/einstein-law-characterization-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-intellectual-credit-basis-v1',document=SOURCE)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    lookup={d['name']:d for d in doc['declarations']}
    for n,(_,meaning) in values.items():
        d=lookup[n];basis['primitives'].append(dict(symbol=n,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-intellectual-credit-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,list(MEANINGS)[:9],[]),(CORE,['sewe','sewk'],[len(old['statements'])])):
        selection=extract_document(doc,roots=roots,statement_indices=indices);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selection.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selection,version=stem+'-basis-v1',document_path=path)
    return {p:x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n' for p,x in files.items()}


def main():
    for p,body in build().items():
        path=ROOT/p
        if path.exists():assert path.read_text(encoding='utf-8')==body,p
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
        print(p,len(body),flush=True)


if __name__=='__main__':main()
