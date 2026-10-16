"""Compose qualitative modal degrees without adding probability primitives."""
import json
from pathlib import Path
from noema.constructed import parse,format_graph

ROOT=Path(__file__).resolve().parents[1]
LIBRARY='examples/v016/graded-modality.noema'
BASIS='data/graded-modality-basis-v1.json'
MEANINGS={
 'rqsq':'指定範囲の尺度値について、相異なる最小値と最大値を持つ厳密な全順序を要求する。数値、距離、等間隔、確率を仮定しない。',
 'rqsr':'非空の候補範囲で内容を評価し、不可能なら最低値、全候補で成立するなら最高値、その中間なら両端以外の尺度値を要求する。中間の値の選択は文脈的な評価であり、候補の件数から算出しない。',
 'rqss':'最高値の手前で近いと採る範囲を明示する。非空で、両端を含まず、その範囲内の値より上の中間値も含む。近さの実質的な基準を順序だけから発見したとはしない。',
 'rqst':'同じ候補範囲・尺度で二つの内容の程度を比較し、第一の内容を厳密に高く評価する。各値は可能・不可能・必然の両端と整合し、第一だけが成立する候補も要求する。第二を含意する第一を逆に高くするような包含逆転を認めない。',
 'rqsu':'基準の候補範囲を指定条件が真の候補に制限し、同じ目標を最高値の手前の近い範囲で評価する。条件を満たす候補は非空とし、現実の条件成立、目標の実現、条件の必要性は要求しない。',
 'rqsv':'第一の内容が比較対象より可能性の程度で上にあり、指定条件の下ではその同じ第一の内容がほぼ必然という、二つの判断を同じ尺度へ結ぶ。公衆・個人・自由などの内容は引数で与え、特定の原文語を基本記号へ埋め込まない。',
}
LIMITS=[
 'これは質的な比較尺度による読みの構成である。頻度や数値確率の推定器ではなく、原文に95%などの閾値を補わない。',
 '近いが端点ではないという厳密な読みを採る。almostの全用法、実質上の必然という緩い用法、任意の曖昧さを同じ規則で処理する主張ではない。',
 '候補範囲、内容の解釈、尺度、中間値、近さの範囲は意味を与える際の明示的な条件である。未知値を偽と置かず、根拠のない中間値を自動設定しない。',
 'カントu0011への適用には、公衆の自己啓蒙、比較される個人の離脱、自由を残す条件、比較背景、jaの強調、著者帰属の接続が必要。既存h6dは内部の一人への働きかけであり、公衆全体の変化として代入しない。',
 '原文の完成した対応や新しい著者主張としては登録しない。既存の本文、意味確認登録簿、原文対応率を変えない。',
]


def definitions():
    def v(n):return 'v '+n
    def op(n,*args):return n+''.join('['+a+']' for a in args)
    def call(n,*args):return 'k '+n+'['+' '.join(v(a) for a in args)+']'
    def use(n,*args):return 'c[v '+n+']['+' '.join(v(a) for a in args)+']'
    def both(*args):
        result=args[-1]
        for a in reversed(args[:-1]):result=op('w',a,result)
        return result
    def quant(n,var,sort,body):return n+' '+var+' '+sort+'['+body+']'
    def all_a(var,body):return quant('f',var,'a',body)
    def all_d(var,body):return quant('f',var,'d',body)
    def exists(var,sort,body):return quant('g',var,sort,body)
    def eq(a,b):return op('e',v(a),v(b))
    def no(body):return op('u',body)
    def implies(a,b):return op('y',a,b)
    def definition(name,args,body):return 'd '+name+'['+args+'] c['+body+'].'
    scale=lambda x:use('scale',x)
    less=lambda x,y:use('less',x,y)
    near=lambda x:use('near',x)
    text=definition('rqsq','scale h[a] c less h[a a] c low a high a',both(
        scale('low'),scale('high'),no(eq('low','high')),
        all_a('x',implies(scale('x'),both(no(less('x','x')),op('x',eq('x','low'),less('low','x')),op('x',eq('x','high'),less('x','high'))))),
        all_a('x',all_a('y',implies(both(scale('x'),scale('y')),both(implies(less('x','y'),no(less('y','x'))),op('x',eq('x','y'),op('x',less('x','y'),less('y','x'))))))),
        all_a('x',all_a('y',all_a('z',implies(both(scale('x'),scale('y'),scale('z'),less('x','y'),less('y','z')),less('x','z')))))))
    text+=definition('rqsr','cases h[d] c goal h[d] c scale h[a] c degree a low a high a',both(
        exists('world','d',use('cases','world')),scale('degree'),
        op('z',eq('degree','low'),no(exists('world','d',both(use('cases','world'),use('goal','world'))))),
        op('z',eq('degree','high'),all_d('world',implies(use('cases','world'),use('goal','world'))))))
    text+=definition('rqss','scale h[a] c less h[a a] c near h[a] c low a high a',both(
        exists('x','a',near('x')),
        all_a('x',implies(near('x'),both(scale('x'),no(eq('x','low')),no(eq('x','high'))))),
        all_a('x',all_a('y',implies(both(near('x'),scale('y'),less('x','y'),no(eq('y','high'))),near('y'))))))
    text+=definition('rqst','cases h[d] c first h[d] c second h[d] c scale h[a] c less h[a a] c low a high a firstdegree a seconddegree a',both(
        call('rqsq','scale','less','low','high'),call('rqsr','cases','first','scale','firstdegree','low','high'),
        call('rqsr','cases','second','scale','seconddegree','low','high'),less('seconddegree','firstdegree'),
        exists('world','d',both(use('cases','world'),use('first','world'),no(use('second','world'))))))
    restricted='i[world d]['+both(use('cases','world'),use('condition','world'))+']'
    text+=definition('rqsu','cases h[d] c condition h[d] c goal h[d] c scale h[a] c less h[a a] c near h[a] c low a high a degree a',both(
        call('rqsq','scale','less','low','high'),call('rqss','scale','less','near','low','high'),
        'k rqsr['+restricted+' v goal v scale v degree v low v high]',near('degree')))
    text+=definition('rqsv','cases h[d] c condition h[d] c first h[d] c second h[d] c scale h[a] c less h[a a] c near h[a] c low a high a firstdegree a seconddegree a conditioneddegree a',both(
        call('rqst','cases','first','second','scale','less','low','high','firstdegree','seconddegree'),
        call('rqsu','cases','condition','first','scale','less','near','low','high','conditioneddegree')))
    return text


def build():
    doc=parse('p:'+definitions())
    assert all(d['kind']=='definition' for d in doc['declarations'])
    basis=dict(status='qualitative_graded_modality_with_explicit_interpretation_parameters',document=LIBRARY,
        primitives={},definitions=MEANINGS,limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Qualitative comparison and condition-restricted near necessity composed')


if __name__=='__main__':main()
