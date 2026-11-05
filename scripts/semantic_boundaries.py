"""Compositional boundary rules; no new grammar or primitive meanings."""
from functools import lru_cache
from noema.constructed_discourse import function_sort as F, description_sort as D, sequence_sort as Q
from scripts.shared_modality import v, app, call, op
from scripts.shared_reference import definition, lam, truth
from scripts.shared_time import q, allof
from scripts.general_language import document

I='individual'; N='number'; S='situation'; T='truth'; C='content'
DC=D(C); DI=D(I); P=F([I],T); REL=F([I,I],T); FAMILY=D(F([I],C))


def eq(a,b):return op('equal',a,b)
def neg(a):return op('not',a)
def ev(c,s):return dict(kind='evaluate',content=c,situation=s)
def dq(d):return dict(kind='disquote',description=d)
def qa(f,*args):return dict(kind='quoted_application',function=f,arguments=list(args))
def fold(xs,element,body,*,some=False,name='item'):
    return dict(kind='fold',sequence=xs,initial=truth(not some),
                step=lam([('acc',T),(name,element)],op('or' if some else 'and',v('acc'),body)))
def args(ps):return [v(n) for n,t in ps]


def value_schema(sort,suffix):
    """Instantiate for ANY well-formed native sort; finite lists are adapters."""
    ds=[]; predicate=F([sort],T)
    def add(name,ps,body):ds.append(definition(name+suffix,ps,T,body))
    base=[('applicable',T),('complete',T)]
    unique=op('and',app('candidates',v('chosen')),q('forall','other',sort,
        op('implies',app('candidates',v('other')),eq(v('other'),v('chosen')))))
    add('uniquevalue',base+[('candidates',predicate),('chosen',sort)],allof(v('applicable'),v('complete'),unique))
    add('missingvalue',base+[('candidates',predicate)],allof(v('applicable'),v('complete'),
        q('forall','other',sort,neg(app('candidates',v('other'))))))
    empty=eq(v('candidates'),dict(kind='sequence',element=sort,items=[]))
    listed=base+[('candidates',Q(sort))]
    add('listeduniquevalue',listed+[('chosen',sort)],allof(v('applicable'),v('complete'),neg(empty),
        fold(v('candidates'),sort,eq(v('item'),v('chosen')))))
    add('listedmissingvalue',listed,allof(v('applicable'),v('complete'),empty))
    different=fold(v('candidates'),sort,neg(eq(v('left'),v('right'))),some=True,name='right')
    add('listedalternativevalues',[('candidates',Q(sort))],fold(v('candidates'),sort,different,some=True,name='left'))
    reports=F([I,I,sort,S],T)
    add('valueconflict',[('field',I),('world',S),('firstsource',I),('secondsource',I),('firstvalue',sort),('secondvalue',sort),
                        ('reports',reports),('singlevalued',F([I,S],T))],
        allof(app('singlevalued',v('field'),v('world')),neg(eq(v('firstvalue'),v('secondvalue'))),
            app('reports',v('firstsource'),v('field'),v('firstvalue'),v('world')),
            app('reports',v('secondsource'),v('field'),v('secondvalue'),v('world'))))
    return ds


def binding_schema(sorts,suffix):
    """Closed template plus typed VALUES, including unnamed bound witnesses."""
    template=D(F(sorts,C));fields=[('template',template)]+[('argument'+chr(97+i),t) for i,t in enumerate(sorts)]
    consumer=F([t for _,t in fields],T);package=F([consumer],T)
    ds=[definition('boundcontent'+suffix,fields,package,lam([('consume',consumer)],app('consume',*args(fields))))]
    unpack=lambda body:dict(kind='apply',function=v('package'),arguments=[lam(fields,body)])
    compare=allof(*(eq(v(n),v('expected'+n)) for n,t in fields))
    ds.append(definition('boundcontentmatches'+suffix,[('package',package)]+[('expected'+n,t) for n,t in fields],T,unpack(compare)))
    applied=dict(kind='apply',function=dq(v('template')),arguments=[v(n) for n,t in fields[1:]])
    ds.append(definition('boundcontentholds'+suffix,[('package',package),('world',S)],T,unpack(ev(applied,v('world')))))
    return ds


@lru_cache(maxsize=1)
def raw():
    ds=[]
    for sort,suffix in [(I,'individual'),(N,'number'),(DC,'description')]:ds.extend(value_schema(sort,suffix))
    for sorts,suffix in [([I],'individual'),([I,N],'individualnumber')]:ds.extend(binding_schema(sorts,suffix))
    def add(n,ps,body,result=T):ds.append(definition(n,ps,result,body))
    add('anchoredcontent',[('family',FAMILY),('anchor',DI)],qa(v('family'),v('anchor')),DC)
    target=[('description',FAMILY),('actual',F([I,S],T)),('world',S)]
    body=op('and',app('actual',v('object'),v('world')),
        ev(dict(kind='apply',function=dq(v('description')),arguments=[v('object')]),v('world')))
    add('actualtargetwitness',target+[('object',I)],body)
    add('actualtargetexists',target,q('exists','object',I,call('actualtargetwitness',*args(target),v('object'))))
    # A constructed reading must expose both families and both anchors. The
    # empirical/contentual justification remains a separate stated premise.
    ps=[('sourcefamily',FAMILY),('sourceanchor',DI),('literal',DC),
        ('targetfamily',FAMILY),('targetanchor',DI),('intended',DC)]
    add('readingconstruction',ps,op('and',eq(v('literal'),call('anchoredcontent',v('sourcefamily'),v('sourceanchor'))),
        eq(v('intended'),call('anchoredcontent',v('targetfamily'),v('targetanchor')))))
    support=F([I,DC,S],T)
    base=[('sources',Q(I)),('claim',DC),('world',S)]
    add('reportedsupport',base+[('supports',support)],fold(v('sources'),I,
        app('supports',v('item'),v('claim'),v('world')),some=True))
    ps=base+[('positive',support),('negative',support)]
    pos=call('reportedsupport',*args(base),v('positive')); no=call('reportedsupport',*args(base),v('negative'))
    for name,body in [('supportboth',op('and',pos,no)),('supportneither',op('and',neg(pos),neg(no))),
                      ('supportpositiveonly',op('and',pos,neg(no))),('supportnegativeonly',op('and',neg(pos),no))]:
        add(name,ps,body)
    trans=q('forall','a',I,q('forall','b',I,q('forall','c',I,
        op('implies',op('and',app('relation',v('a'),v('b')),app('relation',v('b'),v('c'))),app('relation',v('a'),v('c'))))))
    add('relationtransitive',[('relation',REL)],trans)
    includes=q('forall','a',I,q('forall','b',I,op('implies',app('edge',v('a'),v('b')),app('relation',v('a'),v('b')))))
    add('relationreachable',[('edge',REL),('source',I),('target',I)],q('forall','relation',REL,
        op('implies',op('and',includes,call('relationtransitive',v('relation'))),app('relation',v('source'),v('target')))))
    constraints=F([P],T);ps=[('constraints',constraints)]
    add('constraintsolvable',ps,q('exists','valuation',P,app('constraints',v('valuation'))))
    for name,negative in [('constrainttrue',False),('constraintfalse',True)]:
        value=app('valuation',v('node'));value=neg(value) if negative else value
        add(name,ps+[('node',I)],op('and',call('constraintsolvable',v('constraints')),
            q('forall','valuation',P,op('implies',app('constraints',v('valuation')),value))))
    graph=[('nodes',P),('positive',REL),('negative',REL),('grounded',P),('given',P)]
    # Edges are content equations, not inferred truth assertions. Dangling
    # edges are rejected, and each displayed node has at most one equation.
    endpoints=q('forall','a',I,q('forall','b',I,op('implies',op('or',app('positive',v('a'),v('b')),app('negative',v('a'),v('b'))),
        op('and',app('nodes',v('a')),app('nodes',v('b'))))))
    row=lambda name:op('or',app('positive',v('a'),v(name)),app('negative',v('a'),v(name)))
    single=q('forall','a',I,q('forall','b',I,q('forall','c',I,
        op('implies',op('and',row('b'),row('c')),eq(v('b'),v('c'))))))
    signs=q('forall','a',I,q('forall','b',I,neg(op('and',app('positive',v('a'),v('b')),app('negative',v('a'),v('b'))))))
    grounded=q('forall','a',I,op('implies',app('grounded',v('a')),app('nodes',v('a'))))
    add('truthgraphvalid',graph,allof(endpoints,single,signs,grounded))
    fixed=q('forall','a',I,op('implies',app('grounded',v('a')),eq(app('valuation',v('a')),app('given',v('a')))))
    equations=[]
    for relation,sign in [('positive',False),('negative',True)]:
        right=app('valuation',v('b'));right=neg(right) if sign else right
        equations.append(q('forall','a',I,q('forall','b',I,op('implies',app(relation,v('a'),v('b')),eq(app('valuation',v('a')),right)))))
    add('truthgraphassignment',graph+[('valuation',P)],allof(call('truthgraphvalid',*args(graph)),fixed,*equations))
    possible=q('exists','valuation',P,call('truthgraphassignment',*args(graph),v('valuation')))
    add('truthgraphsolvable',graph,possible)
    add('truthgraphtrue',graph+[('node',I)],allof(app('nodes',v('node')),call('truthgraphsolvable',*args(graph)),
        q('forall','valuation',P,op('implies',call('truthgraphassignment',*args(graph),v('valuation')),app('valuation',v('node'))))))
    add('truthgraphfalse',graph+[('node',I)],allof(app('nodes',v('node')),call('truthgraphsolvable',*args(graph)),
        q('forall','valuation',P,op('implies',call('truthgraphassignment',*args(graph),v('valuation')),neg(app('valuation',v('node')))))))
    return ds


def composed():return document(raw())


MEANINGS={
 'anchoredcontent':'閉じた内容関数の記述へ閉じた対象記述を適用し、その構文を保持する。二つの対象記述の指示先が同じでも記述自体を同一化しない。',
 'actualtargetwitness':'記述された性質を指定状況で満たし、同じ状況で実在すると明示された個体。意味領域の個体であることだけから実在を補わない。',
 'actualtargetexists':'指定された記述の性質を満たす実在の対象が指定状況に存在する。目標や信念にその記述が現れることだけでは導かない。',
 'readingconstruction':'字義と意図した内容の両方について、明示した関数記述と対象記述から構文を構成した結果に一致する。読みの妥当性・特徴対応・慣行の適切さは別の根拠として記述する。',
 'reportedsupport':'指定された出所列の少なくとも一つが、同じ内容記述・状況について指定方向の支持を記録している。内容を実行せず、支持からその真理を導かない。',
 'supportboth':'同じ内容記述について肯定・否定の双方の支持が指定出所にある。内容とその否定を同時に真とする主張ではない。',
 'supportneither':'指定出所では肯定・否定いずれの支持もない。指定外の出所や未確認の関係についての不在を補わない。',
 'supportpositiveonly':'指定出所に肯定の支持があり、否定の支持はない。内容の真理そのものとは別。',
 'supportnegativeonly':'指定出所に否定の支持があり、肯定の支持はない。内容の偽そのものとは別。',
 'relationtransitive':'同じ関係で第一から第二、第二から第三へ結ばれるなら、第一から第三へも結ばれる。',
 'relationreachable':'与えた有向辺を全て含むどの推移的関係でも、同じ始点から終点へ結ばれる。長さ1以上の有限経路による到達であり、零歩の自己到達を無条件には含めない。',
 'constraintsolvable':'個体ごとに真理値を割り当てる関数について、明示された制約式を満たす割当てが少なくとも一つある。制約は通常のNoema式で任意に合成できる。',
 'constrainttrue':'制約を満たす割当てが少なくとも一つあり、その全てで同じ節点が真。解なしから任意の真理を引き出さない。',
 'constraintfalse':'制約を満たす割当てが少なくとも一つあり、その全てで同じ節点が偽。',
 'truthgraphvalid':'肯定的/否定的な真理参照の対象が同じ節点域にあり、各節点の参照先は高々一つ、同じ参照に両極性はなく、真理を固定する節点も同じ域にある。参照の循環は許す。',
 'truthgraphassignment':'有効な参照グラフにおいて、固定された真理値と、肯定参照なら同値・否定参照なら反対という式を全て満たす割当て。記述された式を満たす割当てがあるかは別。',
 'truthgraphsolvable':'同じ参照グラフの全式を満たす二値の割当てが少なくとも一つある。',
 'truthgraphtrue':'少なくとも一つ解のある同じ参照グラフで、指定節点は全ての解で真。解がない場合の空虚な全称を真理として採用しない。',
 'truthgraphfalse':'少なくとも一つ解のある同じ参照グラフで、指定節点は全ての解で偽。解なしを内容の偽と同一視しない。'}
for suffix in ('individual','number','description'):
    for prefix,meaning in {
        'uniquevalue':'問いの適用条件と候補範囲の完全性が成立し、指定値が唯一の候補である。',
        'missingvalue':'問いの適用条件と候補範囲の完全性が成立するが、その範囲に値が存在しない。',
        'listeduniquevalue':'適用可能で列挙が完了した非空の候補列に、指定値だけがある。重複は別の候補を増やさない。',
        'listedmissingvalue':'適用可能で列挙が完了し、その候補列が空である。未完の空列と区別する。',
        'listedalternativevalues':'候補列に異なる値が少なくとも二つある。列挙の完了、候補の真理、情報源同士の矛盾は含意しない。',
        'valueconflict':'同じ項目・同じ状況で値が高々一つであるという条件の下で、指定された出所が異なる二値をそれぞれ断定している。複数値を許す性質や、単なる候補の列挙は矛盾としない。'}.items():
        MEANINGS[prefix+suffix]=meaning+' 型は'+suffix+'。'
for suffix in ('individual','individualnumber'):
    for prefix,meaning in {
        'boundcontent':'閉じた内容関数の記述と、順序付きの型付き引数値を同じ組へ保存する。引数値に名前や閉じた引用記述がなくてもよく、自由変数を引用内に捕獲しない。',
        'boundcontentmatches':'同じ組に保存した関数記述と各引数値が指定と一致する。引数の値を、その表し方の同一性と混同しない。',
        'boundcontentholds':'同じ組の関数記述へ保存した全引数値を適用し、指定状況で内容を評価する。組の作成・照合だけではこの評価をしない。'}.items():
        MEANINGS[prefix+suffix]=meaning+' 引数型列は'+suffix+'。'


def basis():
    return dict(document='examples/v016/semantic-boundaries-v1.noema',primitives={},definitions=MEANINGS,
        public_contracts={d['name']:dict(arguments=[dict(role=p['name'],sort=p['sort']) for p in d['parameters']],result=d['result']) for d in raw()},
        new_primitives=0,limits=['完全性・実在・出所の支持・基本関係は結果から逆算しない。未知入力を偽に補わない。',
        '値の五構成は任意の適格な型へ同じ規則で特殊化できる。無限型の量化が記述できることと有限実行器で計算できることは別。',
        '真理参照グラフは同値・否定と固定値の明示的な意味記述。Noemaの全構文の無制限な真理評価器ではない。',
        '候補・記述・語義・個体・実在・評価結果を区別する。関係の入力を与えるだけで、その根拠が正しいと証明したことにはしない。'])
