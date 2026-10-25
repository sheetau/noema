"""Reusable normative targets, justified rules and counterfactual comparisons."""
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort
from scripts.shared_modality import ROOT,v,app,call,op,renamed
from scripts.shared_reference import I,S,T,C,definition,lam,truth
from scripts.shared_time import q,allof

LIBRARY='examples/v016/shared-norms-v1.noema'
BASIS='data/shared-norms-basis-v1.json'
NORM_SOURCE='examples/v014/described-norms.noema'
COUNTER_SOURCE='examples/v016/counterfactual-withholding.noema'
NAMES=dict(zip(('rdm','rdn','rdo','rdp','rdq'),
    ('permissionclear','demandconflict','permissionconflict','notforbidden','normviolated')))
COUNTER_NAMES={'rqrs':'contraryconditional'}
ACTION=function_sort([I,I],C)
D=dict(kind='description',result=ACTION)
PRED=function_sort([S],T)
DP=dict(kind='description',result=PRED)
TARGET=[('source',I),('person',I),('role',I),('activity',I),('description',D),('polarity',T),('context',S)]
RULE=function_sort([t for n,t in TARGET],T)
NORM_PARAMS=TARGET+[('required',RULE),('allowed',RULE)]
RECOGNIZED=function_sort([I,I,S],T)
APPLICABLE=function_sort([I,I,I,S],T)
SUPPORTS=function_sort([I,I]+[t for n,t in TARGET],T)
SELECT=function_sort([S,S],T)
CLOSER=function_sort([S,S,S],T)
JUSTIFIES=function_sort([I,DP,I,S,S],T)
CONDITIONAL=[('actual',S),('antecedent',PRED),('consequent',PRED),('selects',SELECT)]


def args(parameters):return [v(n) for n,t in parameters]
def apply_expr(fn,*values):return dict(kind='apply',function=fn,arguments=list(values))
def disquote(value):return dict(kind='disquote',description=value)
def target(sign=None):return [v(n) if n!='polarity' or sign is None else sign for n,t in TARGET]
def at(name,point):return app(name,v(point))
def selected(point):return app('selects',v('actual'),v(point))


@lru_cache(maxsize=1)
def raw():
    old=parse((ROOT/NORM_SOURCE).read_text(encoding='utf-8'))
    defs=[renamed(d,NAMES) for d in old['declarations'] if d['name'] in NAMES]
    def add(name,params,result,body):defs.append(definition(name,params,result,body))
    required=app('required',*target());allowed=app('allowed',*target())
    opposite=app('required',*target(op('not',v('polarity'))))
    executed=dict(kind='evaluate',content=apply_expr(disquote(v('description')),v('person'),v('activity')),situation=v('context'))
    for name,body in (
        ('normrequired',required),('normpermitted',allowed),('normforbidden',opposite),
        ('normfulfilled',op('and',required,op('equal',executed,v('polarity')))),
        ('normoptional',op('and',call('permissionclear',*args(NORM_PARAMS)),
             call('permissionclear',*(target(op('not',v('polarity')))+[v('required'),v('allowed')]))))):
        add(name,NORM_PARAMS,T,body)
    evidence=[('recognized',RECOGNIZED),('applicable',APPLICABLE),('supports',SUPPORTS)]
    witnesses=[('norm',I),('reason',I)]+TARGET+evidence
    body=allof(app('recognized',v('norm'),v('source'),v('context')),
               app('applicable',v('norm'),v('person'),v('role'),v('context')),
               app('supports',v('norm'),v('reason'),*target()))
    add('normwitness',witnesses,T,body)
    body=q('exists','norm',I,q('exists','reason',I,call('normwitness',*args(witnesses))))
    add('groundedrule',evidence,RULE,lam(TARGET,body))

    old=parse((ROOT/COUNTER_SOURCE).read_text(encoding='utf-8'))
    defs.extend(renamed(d,COUNTER_NAMES) for d in old['declarations'] if d['name'] in COUNTER_NAMES)
    valid=op('and',q('exists','candidate',S,selected('candidate')),
        q('forall','candidate',S,op('implies',selected('candidate'),at('antecedent','candidate'))))
    add('conditionalvalid',CONDITIONAL,T,valid)
    for name,body in (
        ('conditionalall',q('forall','candidate',S,op('implies',selected('candidate'),at('consequent','candidate')))),
        ('conditionalmight',q('exists','candidate',S,op('and',selected('candidate'),at('consequent','candidate'))))):
        add(name,CONDITIONAL,T,op('and',call('conditionalvalid',*args(CONDITIONAL)),body))
    comparison=[('antecedent',PRED),('eligible',SELECT),('closer',CLOSER)]
    def admitted(n):return op('and',app('eligible',v('actual'),v(n)),at('antecedent',n))
    better=q('exists','other',S,op('and',admitted('other'),app('closer',v('actual'),v('other'),v('candidate'))))
    add('comparisonbest',comparison,SELECT,lam([('actual',S),('candidate',S)],op('and',admitted('candidate'),op('not',better))))
    irreflexive=q('forall','left',S,op('implies',admitted('left'),op('not',app('closer',v('actual'),v('left'),v('left')))))
    transitive=q('forall','left',S,q('forall','middle',S,q('forall','right',S,
        op('implies',allof(admitted('left'),admitted('middle'),admitted('right'),
            app('closer',v('actual'),v('left'),v('middle')),app('closer',v('actual'),v('middle'),v('right'))),
            app('closer',v('actual'),v('left'),v('right'))))))
    add('comparisonordered',[('actual',S)]+comparison,T,op('and',irreflexive,transitive))
    best=call('comparisonbest',*args(comparison))
    for name,condition in (('orderedconditional','conditionalall'),('orderedmight','conditionalmight')):
        add(name,[('actual',S),('antecedent',PRED),('consequent',PRED),('eligible',SELECT),('closer',CLOSER)],T,
            op('and',call('comparisonordered',v('actual'),*args(comparison)),
                call(condition,v('actual'),v('antecedent'),v('consequent'),best)))
    support=[('viewpoint',I),('premise',DP),('reason',I),('actual',S),('consequent',PRED),('selects',SELECT),('justifies',JUSTIFIES)]
    accounted=q('forall','candidate',S,op('implies',selected('candidate'),
        app('justifies',v('viewpoint'),v('premise'),v('reason'),v('actual'),v('candidate'))))
    add('counterfactualsupported',support,T,op('and',
        call('contraryconditional',v('actual'),disquote(v('premise')),v('consequent'),v('selects')),accounted))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=defs,statements=[])


@lru_cache(maxsize=1)
def composed():return normalize_document(raw())


MEANINGS={
 'permissionclear':'指定極性の積極的な許可があり、同じ対象の反対極性への要求がない。',
 'demandconflict':'同じ対象の成立と不成立がともに要求される。',
 'permissionconflict':'指定極性の積極的な許可と、反対極性への要求が併存する。',
 'notforbidden':'反対極性への要求がない。積極的な許可の存在ではない。',
 'normviolated':'指定極性への要求があり、同じ記述・本人・活動の実際の状態がその極性と一致しない。',
 'normrequired':'指定された出所・本人・役割・活動・記述・極性・文脈について要求がある。',
 'normpermitted':'指定された対象と極性への積極的な許可がある。反対要求の有無は別に調べる。',
 'normforbidden':'指定された対象の反対極性が要求される。許可の欠如とは異なる。',
 'normfulfilled':'指定極性への要求があり、同じ記述・本人・活動の実際の状態がその極性に一致する。',
 'normoptional':'同じ対象の成立と不成立の両方が積極的に許可され、どちらへの要求もない。',
 'normwitness':'同じ規範が同じ出所・文脈で認められ、本人・役割へ適用され、その規範と理由が同じ対象・極性を支える。',
 'groundedrule':'各対象についてnormwitnessを満たす同じ規範と理由の組が存在する、という要求または許可の関係を作る。',
 'contraryconditional':'現実で前提が偽で、比較候補が非空であり、全候補で前提と帰結が成立する。旧rqrsの本体を保存。',
 'conditionalvalid':'比較候補が非空であり、全候補が同じ前提を満たす。現実の前提や帰結は条件にしない。',
 'conditionalall':'妥当な非空の比較候補すべてで帰結が成立する。',
 'conditionalmight':'妥当な非空の比較候補の少なくとも一つで帰結が成立する。',
 'comparisonbest':'同じ現実状況の候補範囲で前提を満たし、それより優先される前提適合候補がない状況をすべて選ぶ関係。',
 'comparisonordered':'前提適合候補上の優先関係が非反射的かつ推移的である。最良候補の存在は別条件。',
 'orderedconditional':'前提適合候補の優先関係が厳密な半順序をなし、最良候補が非空で、その全てで帰結が成立する。',
 'orderedmight':'前提適合候補の優先関係が厳密な半順序をなし、最良候補の少なくとも一つで帰結が成立する。',
 'counterfactualsupported':'閉じた前提記述を実行してcontraryconditionalを満たし、各比較候補の選択が同じ視点・前提記述・理由・現実状況の根拠関係を満たす。'}
ROLES={
 'source':'要求または許可の出所。同じ規範体系や制度内で固定する。',
 'person':'対象となる本人。','role':'本人のどの立場に対する規範か。','activity':'実行・不実行を問題にする同じ活動。',
 'description':'本人と活動から内容を作る閉じたNoema関数の記述。原語の文や、その場の真偽で代用しない。',
 'polarity':'真は記述の成立、偽は不成立への規範。','context':'規範と履行を評価する状況。',
 'required':'同じ七項目への要求。要求を認定する規範と解釈を別途明示する。',
 'allowed':'同じ七項目への積極的な許可。要求・禁止の不在や物理的可能性から補わない。',
 'norm':'採用または適用される規範の個体。','reason':'規範の適用または比較候補の選択に用いる明示的な根拠の個体。',
 'recognized':'規範・出所・文脈の採用関係。普遍的な正当性の証明とはしない。',
 'applicable':'規範・本人・役割・文脈に対する適用関係。例外・優先順位を反映する場合は採用規約を明示する。',
 'supports':'同じ規範・理由・七対象項目の根拠関係。要求用と許可用を分け、何を根拠として認めたかを説明する。',
 'actual':'条件文の基準となる現実状況。','antecedent':'各状況における仮定の真偽。','consequent':'同じ状況における帰結の真偽。',
 'selects':'現実状況と比較候補の対応。前提・帰結で別の候補を使わない。',
 'eligible':'現実状況ごとの比較対象範囲。背景を何として固定したかと範囲の根拠を明示する。',
 'closer':'同じ現実状況で左候補を右候補より優先する厳密な関係。距離の数値や全順序は要求しない。',
 'viewpoint':'比較候補と根拠を採用する視点の人物。','premise':'前提述語の閉じたNoema記述。これ自体を脱引用して前提として使う。',
 'justifies':'視点・前提記述・理由・現実状況・比較候補の選択根拠。根拠の十分性を自動証明しない。'}


def basis():
    contracts={}
    for d in raw()['declarations']:
        ps=NORM_PARAMS if d['name'] in NAMES.values() else CONDITIONAL if d['name']=='contraryconditional' else [(p['name'],p['sort']) for p in d['parameters']]
        contracts[d['name']]=dict(arguments=[dict(role=n,sort=t,interpretation=ROLES[n]) for n,t in ps],result=d['result'])
    return dict(status='shared_normative_and_counterfactual_conventions',document=LIBRARY,primitives={},
        definitions=MEANINGS,public_contracts=contracts,
        preserved_definitions=[dict(document=NORM_SOURCE,names=NAMES),dict(document=COUNTER_SOURCE,names=COUNTER_NAMES)],
        limitations=['要求・許可・規範の採用・適用・根拠を入力する規約を明示する。定義本体だけでは社会的正当性や例外の優先順位を決定しない。',
            '比較候補の範囲と優先関係は明示した読みの入力。最良候補が存在しない場合や前提不能を空虚な成功にしない。',
            '未知の関係は評価を拒否する。空の候補、規範の不在、否定へ変換しない。',
            '履行を評価する場合だけ行為記述を実行する。許可と能力、規範と事実、反事実と因果を自動的に同一視しない。',
            '有限モデルと二題材の対照は全自然言語の意味や無限領域の証明ではない。円文字登録と第三者読解は別途必要。'])


def prepare():
    for path,text in ((LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')):
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published module differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':prepare()
