"""Construct bounded, independently recorded comparisons and possible tests."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_convention_comparison import ROOT,CUT
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,both,op,quant,ZERO
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-deflection-ratio.noema'
SOURCE='examples/v014/einstein-experimental-comparison.noema'
LIBRARY='examples/v014/experimental-comparison.noema'
CORE='examples/v014/experimental-comparison-core.noema'
READING='data/experimental-comparison-reading-v1.json'
NUMERIC='light electriclow electrichigh magneticlow magnetichigh predictionlow predictionhigh directlow directhigh'
BASE=[(n,'a') for n in ('subject','frame','comparison','theory','ratiomethod','directmethod')]+[('context','d')]
SPEC=lambda prefix:[(prefix+n,'a') for n in ('record','event','kind','unit')]+[(prefix+'scale','b')]+[(prefix+n,CUT) for n in ('low','high')]
RELATIONS=[('recorded','h[a a a a a a '+CUT+' '+CUT+' d] c'),('calibrated','h[a a b d] c'),
           ('methodof','h[a a d] c'),('independent','h[a a a d] c'),('matched','h[a a a a d] c')]
FIELDS=BASE+[('light',CUT)]+sum((SPEC(p) for p in ('electric','magnetic','direct')),[])+RELATIONS
DIRECT=BASE+SPEC('direct')+RELATIONS


def recorded(prefix):
    value=lambda n:v(prefix+n);context=v('context')
    return both(k('aa',ZERO,value('scale')),k('ba',value('low')),k('ba',value('high')),k('bc',value('low'),value('high')),
        app(v('recorded'),value('record'),v('subject'),value('kind'),v('frame'),value('event'),value('unit'),value('low'),value('high'),context),
        app(v('calibrated'),value('unit'),value('kind'),value('scale'),context),
        app(v('methodof'),value('record'),v('directmethod' if prefix=='direct' else 'ratiomethod'),context),
        app(v('matched'),v('subject'),v('frame'),v('comparison'),value('event'),context))


def provenance():
    return both(k('va',v('frame')),op('u',op('e',v('ratiomethod'),v('directmethod'))),
        app(v('independent'),v('directmethod'),v('ratiomethod'),v('theory'),v('context')))


def converted():
    get=lambda p,s:k('bj',v(p+'scale'),v(p+s))
    V=v('light');el,eh,ml,mh=[get(p,s) for p in ('electric','magnetic') for s in ('low','high')]
    pl=k('shv',V,k('shv',ml,k('sjd',eh)));ph=k('shv',V,k('shv',mh,k('sjd',el)))
    return [V,el,eh,ml,mh,pl,ph,get('direct','low'),get('direct','high')]


def definitions():
    text=''
    for real,interval,compatible in ((False,'setz','seub'),(True,'seua','seuc')):
        typ=CUT if real else 'b';fields=[(n,typ) for n in NUMERIC.split()]
        V,el,eh,ml,mh,pl,ph,dl,dh=args(fields);zero=k('bb',ZERO) if real else ZERO
        mul=lambda a,b:k('shv' if real else 'ad',a,b)
        lt=lambda a,b:k('bg' if real else 'aa',a,b)
        le=lambda a,b:k('bc',a,b) if real else op('u',lt(b,a))
        eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
        valid=lambda terms:[k('ba',x) for x in terms] if real else []
        text+=definition(interval,params(fields[:7]),both(*valid(args(fields[:7])),lt(zero,V),lt(zero,el),le(el,eh),le(zero,ml),le(ml,mh),
            eq(mul(eh,pl),mul(V,ml)),eq(mul(el,ph),mul(V,mh))))
        text+=definition(compatible,params(fields),both(k(interval,*args(fields[:7])),*valid([dl,dh]),le(dl,dh),
            le(pl,dh),le(dl,ph),lt(pl,V),lt(dl,V)))
    fields=[(n,CUT) for n in NUMERIC.split()]
    text+=definition('seud',params(fields),both(k('seua',*args(fields[:7])),k('ba',v('directlow')),k('ba',v('directhigh')),k('bc',v('directlow'),v('directhigh'))))
    text+=definition('seue',params(fields),both(k('seud',*args(fields)),op('u',k('seuc',*args(fields)))))
    distinct=[]
    for suffix in ('record','kind'):
        for left,right in (('electric','magnetic'),('electric','direct'),('magnetic','direct')):
            distinct.append(op('u',op('e',v(left+suffix),v(right+suffix))))
    text+=definition('seuf',params(FIELDS),both(provenance(),*distinct,*(recorded(p) for p in ('electric','magnetic','direct')),k('seud',*converted())))
    text+=definition('seug',params(FIELDS),both(k('seuf',*args(FIELDS)),k('seuc',*converted())))
    text+=definition('seuh',params(FIELDS),both(k('seuf',*args(FIELDS)),k('seue',*converted())))
    text+=definition('seui',params(DIRECT),both(provenance(),recorded('direct')))
    text+=definition('seuj','context d accessible h[d d] c experiment e',quant('g','alternative','d',both(
        app(v('accessible'),v('context'),v('alternative')),'t['+v('experiment')+']['+v('alternative')+']')))
    return text


MEANINGS={
    'setz':'正の光速度、分母の下限が正の電気側応答区間、非負の磁気側応答区間から、速度予測の下限V*magneticlow/electrichighと上限V*magnetichigh/electriclowを指定する有理数の関係。',
    'seua':'setzの実切断版。分母が零を含む応答区間を受け入れない。',
    'seub':'予測区間と直接測定区間が重なり、その共通部分に0以上・光速未満の値が存在する有理数の整合条件。直接測定の下限が負でも、勝手に値を補正せず共通部分を調べる。',
    'seuc':'seubの実切断版。区間の重なりは理論の証明や、中心値同士の一致を意味しない。',
    'seud':'予測区間と直接測定区間が比較可能な数値範囲である。重なりや理論との整合性は要求しない。',
    'seue':'有効な比較入力seudがあり、理論の許容速度を含む共通部分がない。無効な入力を実験的不一致として扱わない。',
    'seuf':'三つの区間記録を同じ対象・基準系・比較条件へ結び、量の種類、記録、方法、単位尺度、独立性と各出来事の対応を明示する。異なる時点の記録を許すが、同じ運動条件で比較できるというmatchedを要求する。理論との一致は前提にしない。',
    'seug':'seufの記録が数値上seucで両立する。結果が理論を証明したとはしない。',
    'seuh':'seufの記録が数値上seueで両立しない。誤差の上限や測定の解釈が適切という前提を離れて理論が偽と断定するものではない。',
    'seui':'同じ対象・基準系・比較条件で、直接測定の区間記録、単位校正、方法と独立性を保持する。偏向の記録が既に存在することは要求しない。',
    'seuj':'基準文脈から許容される少なくとも一つの状況でexperimentの内容が成立するという可能性。現実の測定実施や、可能な全結果の一致は要求しない。',
    'seuk':'同じ電子・K・比較対象の比の式に、仮定上の三つの区間測定をseufで結ぶ内容。前段の比の真理を測定値の前提に含めない。',
    'seul':'三つの測定と比較を同じ許容状況で行えるというu0268前半の部分解釈。結果が両立することは条件に含めない。',
    'seum':'同じ比較条件で直接速度を測る区間記録の内容。偏向記録の内容とは独立に述べる。',
    'seun':'seumを満たす許容状況があるという直接測定の可能性。これだけから三つの記録が同時に得られることは導かない。',
    'seuo':'同じ三つの記録が理論と両立するという検査用の内容。著者による実験結果としては帰属させない。',
    'seup':'同じ三つの記録が理論と両立しないという検査用の内容。著者による実験結果としては帰属させない。',
}
LIMITS=[
    '区間は与えられた保守的な数値の上限・下限であり、確率や信頼区間の指定ではない。原文はこの誤差区間モデルを明記しておらず、比較を説明するための解釈候補である。',
    '記録の区間の妥当性、直接法と偏向法の独立性、各出来事の同じ運動条件への対応は明示した入力関係である。方法名が違うことだけから独立性を認定しない。',
    'Vは共通基準の既知の値とし、三つの単位尺度は既存zofへ結ぶ。二つの応答の校正と幾何学的条件はcomparisonとmatchedの解釈に含め、装置と測定誤差の物理的構成は未完。',
    '直接測定が可能という理由から比較が可能という著者の理由づけを記録する。独立に可能な記録が共同で可能であることは別条件であり、理由の妥当性を自動認定しない。',
    '構成したのは独立な記録による比較の実行可能性である。誤差区間が広すぎて結果を区別できない場合を含むため、検証の識別力・必要精度・十分な反証可能性まで保証しない。',
    'u0268の高速に振動する電場・磁場による測定の例、u0266後半の全速度での決定可能性、実際の検証結果と原文全体の意味一致は未完。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    values={}
    for p in ('electric','magnetic','direct'):
        for n,sort in SPEC(p):
            values['zrm'+n]=(('h[d] '+CUT) if n.endswith(('low','high')) else sort,
                '同じ比較で使う'+p+'側の'+n[len(p):]+'。low/highは評価状況ごとに異なりうる区間記録の端点。')
    for n in ('comparison','ratiomethod','directmethod','claimnode','directnode','reasonnode','scope'):
        values['zrm'+n]=('a','u0268の比較・直接測定についての'+n+'への参照。')
    descriptions={'recorded':'記録・対象・量の種類・基準系・出来事・単位・下限・上限・状況を結ぶ区間記録。',
        'methodof':'記録を得る方法の同定。別名が付いているだけで独立な方法とはしない。',
        'independent':'直接法が偏向法の対象命題を結果の算出前提として使わないという独立性の条件。範囲の完全性と実現は別途検討する。',
        'matched':'同じ対象・基準系・比較条件に、指定出来事の測定を対応させる。関連する運動条件と応答の共通校正が保たれるという前提。'}
    for n,sort in RELATIONS:
        if n!='calibrated':values['zrm'+n]=(sort,descriptions[n])
    extra=definitions()+''.join('r '+n+'[] '+sort+'.' for n,(sort,_) in values.items())
    fixed={'subject':k('zramatter'),'frame':k('ra'),'theory':k('zrlrationode'),'context':v('context'),'light':k('tc'),'calibrated':'p zof'}
    def inputs(fields):
        return [fixed.get(n,app(k('zrm'+n),v('context')) if n.endswith(('low','high')) else k('zrm'+n)) for n,_ in fields]
    for name,target,fields in [('seuk','seuf',FIELDS),('seum','seui',DIRECT),('seuo','seug',FIELDS),('seup','seuh',FIELDS)]:
        extra+=definition(name,'','b context['+k(target,*inputs(fields))+']','e')
    for name,content in [('seul','seuk'),('seun','seum')]:
        extra+=definition(name,'','b context['+k('seuj',v('context'),k('zrjaccessible'),k(content))+']','e')
    doc=parse(format_graph(doc,'compact')+extra)
    statements=''.join('s['+k('uh',k(node),k('rd'),'r['+k(content)+']',k('zrmscope'),k('ri'))+'].' for node,content in [('zrmclaimnode','seul'),('zrmdirectnode','seun')])
    statements+='s['+k('zc',k('zrmreasonnode'),k('rd'),'r['+k('seun')+']','r['+k('seul')+']',k('zrmscope'),k('ri'))+'].'
    doc['statements']=old['statements']+parse(format_graph(doc,'compact')+statements)['statements']
    basis=json.loads((ROOT/'data/einstein-deflection-ratio-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-experimental-comparison-basis-v1',document=SOURCE);basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    lookup={d['name']:d for d in doc['declarations']}
    for name,(_,meaning) in values.items():
        d=lookup[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-experimental-comparison-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,list(MEANINGS)[:11],[]),(CORE,['setz','seub','seuo','seup'],list(range(len(old['statements']),len(doc['statements']))))):
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
