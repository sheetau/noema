"""Reuse rational quantities and connect measurements, partitions and containers."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort
from scripts.shared_modality import ROOT,v,app,call,op,renamed
from scripts.shared_reference import I,S,T,truth,lam,definition
from scripts.shared_time import allof
from scripts.shared_readings import num
from scripts.shared_plurality import MEMBERS,seq,fold,neq

N='number'; DIM=function_sort([I],N)
MAP=function_sort([I],I); READINGS=function_sort([I,S],N)
RELATION=function_sort([I,I,S],T)
REGISTER=function_sort([I,I,DIM,N,S],T)
MEASURE=function_sort([I,I,I,N,S],T)
COVERAGE=function_sort([MEMBERS,I,S],T)
SOURCE='examples/v011/quantities.noema'
SOURCE_BASIS='data/quantities-basis-v1.json'
PLURAL='examples/v016/shared-plurality-v1.noema'
PLURAL_BASIS='data/shared-plurality-basis-v1.json'
LIBRARY='examples/v016/shared-quantities-v1.noema'
BASIS='data/shared-quantities-basis-v1.json'
ARITHMETIC={'aa':'rationalbelow','ab':'rationaladd','ac':'rationalnegate','ad':'rationalmultiply'}
NAMES=dict(ARITHMETIC,da='dimensionless',db='dimensionproduct',dc='dimensioninverse',dd='dimensionquotient',
    de='dimensionpower',df='dimensionequal',dg='dimensionisscalar',dh='basisdimension',di='quantitycompatible',
    dj='quantityequal',ds='positivescales',dl='quantityproduct',dm='quantityquotient')
PLURAL_NAMES=('memberof','distinctmembers','membercount')
OLD_ROLES={
 'dimensionless':[], 'dimensionproduct':['leftdim','rightdim'], 'dimensioninverse':['dimension'],
 'dimensionquotient':['leftdim','rightdim'], 'dimensionpower':['dimension','power'],
 'dimensionequal':['leftdim','rightdim'], 'dimensionisscalar':['dimension'], 'basisdimension':['axis','dimension'],
 'quantitycompatible':['leftkind','rightkind','leftdim','rightdim','leftscale','rightscale'],
 'quantityequal':['leftkind','rightkind','leftdim','rightdim','leftscale','rightscale','left','right'],
 'positivescales':['firstscale','secondscale','thirdscale'],
 'quantityproduct':['leftdim','rightdim','resultdim','leftscale','rightscale','resultscale','left','right','result'],
 'quantityquotient':['leftdim','rightdim','resultdim','leftscale','rightscale','resultscale','left','right','result']}
UNIT=[('kind',I),('unit',I),('dimension',DIM),('scale',N)]
EVIDENCE=[('context',S),('registry',REGISTER),('measurement',MEASURE)]
AMOUNT=[('subject',I)]+UNIT+[('reading',N)]+EVIDENCE
PARTITION=[('parts',MEMBERS),('whole',I),('context',S),('partof',RELATION),('disjoint',RELATION),('complete',COVERAGE)]
SUM=[('parts',MEMBERS),('whole',I)]+UNIT+[('readings',READINGS)]+EVIDENCE+PARTITION[3:]
CONTENTS=[('containers',MEMBERS),('assignment',MAP),('context',S),('contains',RELATION)]


def args(ps):return [v(n) for n,t in ps]
def every(sequence,name,body,acc='accepted'):
    return fold(sequence,truth(True),[(acc,T),(name,I)],op('and',v(acc),body))
def read(subject):return app('readings',subject,v('context'))
def amount(subject):return call('amountat',subject,*args(UNIT),read(subject),*args(EVIDENCE))


@lru_cache(maxsize=1)
def raw():
    original=parse((ROOT/SOURCE).read_text(encoding='utf-8'))
    plural=parse((ROOT/PLURAL).read_text(encoding='utf-8'))
    defs=[renamed(d,NAMES) for d in original['declarations'] if d['name'] in NAMES]
    defs.extend(deepcopy(d) for d in plural['declarations'] if d['name'] in PLURAL_NAMES)
    def add(name,params,body,result=T):defs.append(definition(name,params,result,body))
    add('unitregistered',UNIT+[('context',S),('registry',REGISTER)],op('and',call('rationalbelow',num(0),v('scale')),
        app('registry',v('unit'),v('kind'),v('dimension'),v('scale'),v('context'))))
    add('amountat',AMOUNT,allof(call('unitregistered',*args(UNIT),v('context'),v('registry')),
        op('not',call('rationalbelow',v('reading'),num(0))),
        app('measurement',v('subject'),v('kind'),v('unit'),v('reading'),v('context'))))
    comparison=[('leftsubject',I),('rightsubject',I),('leftkind',I),('rightkind',I),('leftunit',I),('rightunit',I),
        ('leftdim',DIM),('rightdim',DIM),('leftscale',N),('rightscale',N),('left',N),('right',N)]+EVIDENCE
    measured=[call('amountat',v(side+'subject'),v(side+'kind'),v(side+'unit'),v(side+'dim'),v(side+'scale'),v(side),
        *args(EVIDENCE)) for side in ('left','right')]
    compat=[v(n) for n in OLD_ROLES['quantitycompatible']]
    add('sameamount',comparison,allof(*measured,call('quantityequal',*compat,v('left'),v('right'))))
    add('amountless',comparison,allof(*measured,call('quantitycompatible',*compat),call('rationalbelow',
        call('rationalmultiply',v('leftscale'),v('left')),call('rationalmultiply',v('rightscale'),v('right')))))
    different=op('implies',neq(v('part'),v('other')),app('disjoint',v('part'),v('other'),v('context')))
    disjoint=every(v('parts'),'part',every(v('parts'),'other',different,'allothers'))
    add('partitionof',PARTITION,allof(call('distinctmembers',v('parts')),
        every(v('parts'),'part',app('partof',v('part'),v('whole'),v('context'))),disjoint,
        app('complete',v('parts'),v('whole'),v('context'))))
    total=fold(v('parts'),num(0),[('total',N),('part',I)],call('rationaladd',v('total'),read(v('part'))))
    add('amountsum',SUM,allof(call('partitionof',*args(PARTITION)),amount(v('whole')),
        every(v('parts'),'part',amount(v('part'))),op('equal',total,read(v('whole')))))
    mapped=fold(v('members'),seq(),[('mapped',MEMBERS),('member',I)],dict(kind='concat',left=v('mapped'),
        right=seq(app('assignment',v('member')))))
    add('assignedmembers',[('members',MEMBERS),('assignment',MAP)],mapped,MEMBERS)
    add('containercontents',CONTENTS,every(v('containers'),'container',
        app('contains',app('assignment',v('container')),v('container'),v('context'))))
    counted=[('containers',MEMBERS),('count',N)]+CONTENTS[1:]
    add('countedcontainers',counted,op('and',call('membercount',v('containers'),v('count')),call('containercontents',*args(CONTENTS))))
    packed=[('containers',MEMBERS),('count',N),('assignment',MAP)]+SUM[1:]+[('contains',RELATION)]
    add('containeramount',packed,op('and',call('countedcontainers',*args(counted)),
        call('amountsum',call('assignedmembers',v('containers'),v('assignment')),*args(SUM[1:]))))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=defs,statements=[])


@lru_cache(maxsize=1)
def composed():return normalize_document(raw())


NEW_MEANINGS={
 'unitregistered':'同じ状況で、単位・量の種類・次元・正の有理数尺度が登録関係を満たす。単位名だけから尺度を推定しない。',
 'amountat':'同じ対象・量の種類・単位・状況について非負の読みが測定関係を満たし、次元と尺度が単位登録に一致する。',
 'sameamount':'二対象の同じ状況でのamountatが成立し、種類・次元が同じで尺度換算後の値が等しい。二対象の個体同一性は要求しない。',
 'amountless':'二対象の同じ状況でのamountatが成立し、種類・次元が同じで左の尺度換算後の値が右より小さい。',
 'partitionof':'部分列に重複がなく、各部分が同じ全体の部分で、異なる部分が互いに重ならず、同じ状況で列が全体を尽くす。空列の完全性も別途要求する。',
 'amountsum':'partitionofを満たし、同じ種類・単位・次元・尺度・状況で全体と各部分のamountatが成立し、部分の値の和が全体の値に等しい。',
 'assignedmembers':'有限列の各個体を割当先へ写した列。元の順序と重複をそのまま残す。',
 'containercontents':'列の各容器について、割当先の同じ部分がその容器の内容である関係を同じ状況で満たす。量や内容の相違は主張しない。',
 'countedcontainers':'内容の割当が成立する、重複のない容器列の個数が指定数と等しい。空列は0。中身の量を個数から推定しない。',
 'containeramount':'countedcontainersを満たす同じ内容割当の部分列についてamountsumが成立する。内容の重複や重なりを二重計上しない。'}
ROLES={
 'subject':'量を測定する対象。','kind':'体積・質量などの量の種類。物質の種類や次元そのものとは別に指定する。',
 'unit':'測定値を述べる単位の個体。','dimension':'基底軸から有理数指数への関数。採用する軸と意味を明示する。',
 'scale':'基準単位に対する正の有理数尺度。基準の値は読みと尺度の積。',
 'reading':'当該単位での非負の有理数値。このモジュールのamountは量の大きさを扱う。',
 'context':'単位登録・測定・部分・内容の関係を評価する同じ状況。測定条件や時点の選択を明示する。',
 'registry':'単位・種類・次元・尺度・状況の登録関係。規約の整合性や実現を自動証明しない。',
 'measurement':'対象・量の種類・単位・読み・状況の測定関係。未知の測定を0や否定に置き換えない。',
 'parts':'全体を構成する個体の有限列。','whole':'同じ状況で部分列が尽くす対象。',
 'partof':'部分・全体・状況の関係。','disjoint':'二部分が同じ状況で重ならないという関係。',
 'complete':'部分列・全体・状況について過不足のない範囲を指定する関係。列の型や長さだけでは分からない。',
 'readings':'対象と状況から、共通の指定単位での値を返す明示的な関数。測定関係と照合する。',
 'members':'割当を適用する個体の列。','assignment':'容器などの個体から、同じ内容物・部分を選ぶ明示的な関数。',
 'containers':'数える容器の有限列。容器と内容の個体を混同しない。','count':'容器列の個数。',
 'contains':'内容の部分・容器・状況の関係。引数は内容が先、容器が後。',
 'leftsubject':'比較の左側の測定対象。','rightsubject':'比較の右側の測定対象。',
 'leftkind':'左側の量の種類。','rightkind':'右側の量の種類。','leftunit':'左側の単位。','rightunit':'右側の単位。',
 'leftdim':'左側の次元。','rightdim':'右側の次元。','resultdim':'結果の次元。',
 'leftscale':'左側の正の単位尺度。','rightscale':'右側の正の単位尺度。','resultscale':'結果の正の単位尺度。',
 'left':'左側の有理数値。','right':'右側の有理数値。','result':'結果の有理数値。','value':'有理数値。',
 'power':'次元指数に掛ける有理数。値の冪乗の存在は別に調べる。','axis':'指定した基底次元の軸。',
 'firstscale':'一つ目の正の尺度。','secondscale':'二つ目の正の尺度。','thirdscale':'三つ目の正の尺度。'}


def basis():
    old=json.loads((ROOT/SOURCE_BASIS).read_text(encoding='utf-8'))
    plural=json.loads((ROOT/PLURAL_BASIS).read_text(encoding='utf-8'))
    meanings={NAMES[n]:m for n,m in old['definitions'].items() if n in NAMES}
    meanings.update({n:plural['definitions'][n] for n in PLURAL_NAMES});meanings.update(NEW_MEANINGS)
    primitives={ARITHMETIC[r['symbol']]:dict(r,symbol=ARITHMETIC[r['symbol']]) for r in old['primitives']}
    contracts={}
    for d in raw()['declarations']:
        name=d['name']
        if name in PLURAL_NAMES:contracts[name]=plural['public_contracts'][name];continue
        if d['kind']=='primitive':ps=list(zip(primitives[name]['arguments'],d['parameters']))
        else:
            names=OLD_ROLES.get(name,[p['name'] for p in d['parameters']])
            ps=list(zip(names,[p['sort'] for p in d['parameters']]))
        contracts[name]=dict(arguments=[dict(role=n,sort=t,interpretation=ROLES[n]) for n,t in ps],result=d['result'])
    return dict(status='shared_rational_quantities_and_contents',document=LIBRARY,primitives=primitives,
        definitions=meanings,public_contracts=contracts,
        preserved_definitions=[dict(document=SOURCE,names=NAMES),dict(document=PLURAL,names={n:n for n in PLURAL_NAMES})],
        limitations=['既存の有理数比較・加算・加法逆元・乗算の4基本宣言を再利用する。関数の型だけでは標準算術の解釈を強制できないため、意味規約を保持する。',
            '既存の次元・種類・尺度の13定義を保持する。新しい測定・内容の10定義を加える。複数モジュールの3定義は同じ本体で共有する。',
            'amountatは非負の有理数量の大きさ。誤差区間、任意実数値、無理数尺度、原点移動、対数単位の万能換算へ読み替えない。旧実数版と座標定義は保持する。',
            '登録・測定・部分・重なり・完全性の現実への根拠を自動認定しない。amountsumは加算の等式も要求し、任意の量が常に加法的とは推論しない。',
            '容器数や部分数から量を導かない。全体の範囲と測定状況を固定する。未知入力は評価拒否する。',
            '円文字共有辞書への登録、学習文書、第三者読解は未完。'])


def prepare():
    for path,text in ((LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')):
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published quantity module differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':prepare()
