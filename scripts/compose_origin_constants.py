"""Separate origin conventions, constant translations and an undetermined scale."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_affine_time_form import CUT, PHI, FAMILY


def rational_definitions():
    return '''
d sps[cx b cy b cz b ct b offset b dx b dy b dz b dt b output b x b y b z b time b] b[k ab[k sld[v cx v cy v cz v ct v offset k ab[v x v dx] k ab[v y v dy] k ab[v z v dz] k ab[v time v dt]] v output]].
'''


MEANINGS={'sps':'同じアフィン行の四入力の原点を定数だけ移し、出力にも定数を加えた値。移動量は入力点に依存しない。'}


def generic_composed():
    doc=parse((ROOT/'examples/v014/four-coordinates.noema').read_text(encoding='utf-8')+rational_definitions())
    basis=deepcopy(json.loads((ROOT/'data/four-coordinates-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='origin-constants-basis-v1',document='examples/v014/origin-constants.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['原点変更のアフィン代数と、物理的な記録がその変換を満たすことを区別する。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


OFFSETS=('ot','ox','oy','oz')


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-four-coordinates.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+rational_definitions()
    offset_args=' '.join(name+' '+CUT for name in OFFSETS)
    offset_values=' '.join('v '+name for name in OFFSETS)
    V='k tc[]';v='k zb7[]';phi='c[k spc[]]['+v+']'
    x,y,z,t=['k zc6[v first k '+role+'[]]' for role in ('yn','yo','yp','zc7')]
    expressions=['k spd['+V+' '+v+' '+phi+' '+x+' '+t+']',
        'k spe['+V+' '+v+' '+phi+' '+x+' '+t+']','k spf['+phi+' '+y+']','k spf['+phi+' '+z+']']
    clauses=['k sha[v first p ba]','k sha[v second p ba]',
        'k spa['+V+' '+v+' k soy['+V+' '+v+']]','k ba['+phi+']']
    for role,offset,expr in zip(('zc7','yn','yo','yp'),OFFSETS,expressions):
        rhs='k bd['+expr+' v '+offset+']'
        clauses+=['k ba[v '+offset+']','k ba['+expr+']','k ba['+rhs+']','k sca[k zc6[v second k '+role+'[]] '+rhs+']']
    text+='d spu[first a second a '+offset_args+'] c['+both(*clauses)+'].\n'
    text+='d spv[first a second a setting d] c[g event a['+both('k zc4[v event]',
        'k shd[v event v first k ra[] v setting]','k shd[v event v second k zbm[] v setting]')+']].\n'
    for symbol,frame in (('spw','ra'),('spx','zbm')):
        text+='d '+symbol+'[record a setting d] c[g event a[w[k zc4[v event]][k shd[v event v record k '+frame+'[] v setting]]]].\n'
    left='i[record a][k spw[v record v setting]]';right='i[record a][k spx[v record v setting]]'
    relation='i[first a second a][k spv[v first v second v setting]]'
    text+='d spy['+offset_args+' setting d] c['+both(*('k ba[v '+name+']' for name in OFFSETS),
        'k sgw['+left+' '+right+' '+relation+' p shh]',
        'f first a[f second a[y[w[k spw[v first v setting]][k spx[v second v setting]]][z[k spu[v first v second '+offset_values+']][k spv[v first v second v setting]]]]]')+'].\n'
    body='k spy['+offset_values+' v setting]'
    for name in reversed(OFFSETS):body='g '+name+' '+CUT+'['+body+']'
    text+='d spz[setting d] c['+body+'].\n'
    text+='r zfm[] d.r zfn[d] c.r zfo[d d] c.r zfp[] a.r zfq[] a.\n'
    text+='d sqa[] e[b context[w[k zfn[v context]][k zfo[k zfm[] v context]]]].\n'
    text+='d sqb[] e[b context[k spz[v context]]].\n'
    text+='d sqc[] '+FAMILY+'[i[alternative d][k spb[k tc[] c[k zer[]][v alternative]]]].\n'
    zero='k bb[n p a b]'
    domain='i[speed '+CUT+']['+both('k ba[v speed]','k bc['+zero+' v speed]','k bg[v speed k tc[]]')+']'
    validfamily='f alternative d[y[k zet[k zee[] k zfm[] v alternative]][f speed '+CUT+'[y[c['+domain+'][v speed]][k ba[c[c[k sqc[]][v alternative]][v speed]]]]]]'
    text+='d sqd[] e[b context['+both('k zet[k zee[] k zfm[] k zfm[]]',validfamily,
        'k smq[k spc[] k sqc[] k zfm[] '+domain+']',
        'k smb[k zee[] k zfm[] '+domain+' p zet k sqc[] p sca]')+']].\n'
    text+='d sqe[first d second d speed '+CUT+'] c[k sma[k zee[] k zfm[] '+domain+' p zet k sqc[] p sca v first v second v speed]].\n'
    text+='d sqf[speed '+CUT+'] c[k sms[k spc[] k sqc[] k zfm[] v speed]].\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k uh[k zfp[] k rd[] r[k sqd[]] k rh[] k ri[]]].
s[k zc[k zfq[] k rd[] r[k sqa[]] r[k sqb[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-four-coordinates-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-origin-constants-basis-v1',document='examples/v014/einstein-origin-constants.noema')
    basis['definitions'].update(MEANINGS|{
        'spu':'同じV,v,正規化後のφを使う四座標式に、時間・縦・横二成分の独立した四定数を加える。零も許し、一つの定数を四式へ強制しない。',
        'spv':'指定した状況で、同じ対象出来事の静止系記録と運動系記録が対応すること。零原点の先行状況zb6には固定しない。',
        'spw':'指定した状況で対象出来事に割り当てられた静止系座標記録の範囲。',
        'spx':'指定した状況で対象出来事に割り当てられた運動系座標記録の範囲。',
        'spy':'指定状況の非空で関数的な座標対応を、一組の四定数で全記録対にわたり過不足なく表す。定数を記録ごとに取り替えない。',
        'spz':'指定状況について、全記録対に共通する四つの実数定数が存在する。四存在量化をspyの全記録量化の外に置く。',
        'sqa':'同じ物理的・単位の条件を保つ対象設定で、現在の論述段階では初期空間原点とτ零点についての仮定を採用しない、という条件内容。原点の不一致の断言ではない。',
        'sqb':'その設定で、一組の四加法定数を含む座標式が対応を表すという内容。著者の条件付き結論として引用する。',
        'sqc':'先行係数aの候補関数族zerを、各候補状況で同じβにより正規化したφの候補族。',
        'sqd':'u0085の段階で現在のφを含む有効な候補関数が残り、ある対象速度で異なる値を持つ候補も残ること。後続のφ=1を先取りしない。',
        'sqe':'現在の段階に残る二候補の正規化後のφが、指定した同一速度で異なるという一点の証人。',
        'sqf':'現在の正規化後のφと、現在の候補状況における正規化後の族の値を、指定した速度で結ぶ。'})
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zfm',[],'四式を得たが新しいφをまだ決定していないu0085の論述段階。u0064のzesとは別の参照。'),
        ('zfn',['setting'],'原点と時計の零点以外は先行する物理条件、基準系、単位、V,vおよび尺度φを維持する、原点変更の検討対象設定。物理条件の維持は外部解釈の前提。'),
        ('zfo',['stage','setting'],'指定の論述段階と設定で、運動系の初期空間原点とτの零点についての仮定を採用しない。物理的な不一致を意味しない。'),
        ('zfp',[],'正規化後のφが当面は未知であるというu0085の主張箇所。'),
        ('zfq',[],'初期原点の仮定を外すと各右辺に加法定数が要るというu0085の条件付き記述箇所。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['unresolved']+=[
        'u0085への部分的な接続を追加した。親文書の未完事項は履歴として残し、この追補を併読する。原刊照合と全文の意味一致は未完。',
        '一般の実切断の体の法則、全記録への共通定数の存在、物理的な原点変更がその条件を満たすことは証明していない。有限の記録例と有理数の代数を区別する。',
        'φの未決定性は残存する候補関数として部分解釈した。主体の知識一般や、あらゆる根拠からの認識不可能性は定義していない。候補集合の史実に即した再構成は未完。',
        '仮定の非採用zfoと原点以外の条件維持zfnは意味規約を持つ基本関係であり、否定・不一致だけから導かない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,name in ((generic_composed,'origin-constants'),(source_composed,'einstein-origin-constants')):
        text,basis=compose()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored origin constants differ: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Four independent origin constants and the undetermined normalized function composed')


if __name__=='__main__':main()
