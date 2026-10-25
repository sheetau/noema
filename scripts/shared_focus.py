"""Shared foreground/background packages, alternatives, topics and contrast."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort,sequence_sort
from scripts.shared_modality import ROOT,v,app,call,op,renamed
from scripts.shared_reference import I,S,T,C,U,definition,lam,truth,content
from scripts.shared_time import q,allof

LIBRARY='examples/v016/shared-focus-v1.noema';BASIS='data/shared-focus-basis-v1.json'
SCALAR_NAMES=dict(zip(('rst','rsu','rsv','rsw','rsx','rsy','rsz','rta','rtb','rtc','rtd','rte','rtf','rtg','rth','rti','rtj','rtk','rtl'),
    ('focuspackage','focusclaim','focusbackground','focusnegate','focusclaimtrue','focusbackgroundtrue','focusquestion',
     'focusorder','focusextreme','focusadditional','focusscalebackground','focusadditivescale','focusfrombackground',
     'focusscalar','focusscalaralso','focusaction','focusactions','focusquotedlist','focusactionalso')))
SOURCES=[dict(document='examples/v016/scalar-backgrounds.noema',basis='data/scalar-backgrounds-basis-v1.json',renaming=SCALAR_NAMES),
    dict(document='examples/v016/attributed-content-pairs.noema',basis='data/attributed-focus-basis-v1.json',renaming={'rtq':'focusattributed','rqtu':'focusthirdrank'}),
    dict(document='examples/v016/ordered-contrast.noema',basis='data/ordered-contrast-basis-v1.json',renaming={'rw3':'contrastordered'})]
PC=description_sort(C,1);CC=description_sort(C,2);TC=description_sort(C,3)
DI=description_sort(I);DS=description_sort(S);ALTS=sequence_sort(PC);WINDOW=function_sort([S],T)
SELECT=function_sort([CC,CC],CC);PAIR=function_sort([SELECT],CC)
RANKING=function_sort([I,PC,PC,S],T)
REPORT=function_sort([I,I,TC,I,S],T);BACKGROUND=function_sort([I,I,TC,TC,I,I,S],T)
TOPICFRAME=description_sort(function_sort([I],C),2);ABOUT=function_sort([I,I,DI,CC,S],T)
EXPECTS=function_sort([I,PC,PC,S,S],T)
ALTERNATIVE_PARAMS=[('focus',PC),('alternatives',ALTS),('comparisons',WINDOW)]
QUOTED_PARAMS=[(n,description_sort(t,1 if n in ('focus','alternatives') else 0)) for n,t in ALTERNATIVE_PARAMS]
ATTRIBUTION=[('node',I),('author',I),('package',PAIR),('foregroundscope',I),('backgroundscope',I),('context',S),
    ('reported',REPORT),('backgrounded',BACKGROUND)]
TOPIC=[('node',I),('author',I),('topic',I),('reference',DI),('frame',TOPICFRAME),('package',PAIR),
    ('foregroundscope',I),('backgroundscope',I),('context',S),('about',ABOUT),('reported',REPORT),('backgrounded',BACKGROUND)]
EXPECTATION=[('left',PC),('right',PC),('observer',I),('anchor',S),('expects',EXPECTS)]

def args(ps):return [v(n) for n,t in ps]
def eq(a,b):return op('equal',a,b)
def disquote(x):return dict(kind='disquote',description=x)
def evaluate(x,world):return dict(kind='evaluate',content=disquote(x),situation=world)
def quote(body,rank=0):return dict(kind='quote',body=body,**({'rank':rank} if rank else {}))
def ref(n):return dict(kind='function_ref',symbol=n)
def quoted(function,*arguments):return dict(kind='quoted_application',function=function,arguments=list(arguments))
def fold(sequence,variable,body,*,initial=True,operation='and'):
    return dict(kind='fold',sequence=sequence,initial=truth(initial),step=lam([('accumulator',T),(variable,PC)],op(operation,v('accumulator'),body)))
def liftfocus(x):return quoted(quote(ref('focuscontent'),2),x)

OLD_ROLES={
 'focuspackage':['foreground','background'],**{n:['package'] for n in ('focusclaim','focusbackground','focusnegate','focusquestion')},
 'focusclaimtrue':['package','point'],'focusbackgroundtrue':['package','point'],
 'focusorder':['alternatives','observer','anchor','ranking'],
 **{n:['focus','alternatives','observer','anchor','ranking'] for n in ('focusextreme','focusscalebackground','focusadditivescale')},
 'focusadditional':['alternatives','point'],
 'focusfrombackground':['backgroundfunction','focuscode','alternativescode','observercode','anchorcode','rankingcode'],
 **{n:['focuscode','alternativescode','observercode','anchorcode','rankingcode'] for n in ('focusscalar','focusscalaralso')},
 'focusaction':['actionframe','target'],'focusactions':['actionframe','targets'],'focusquotedlist':['contents'],
 'focusactionalso':['actionframe','target','targets','observercode','anchorcode','rankingcode'],
 'focusthirdrank':['description'],
 'focusattributed':['node','author','foreground','background','foregroundscope','backgroundscope','context','reported','backgrounded'],
 'contrastordered':['node','author','first','second','left','right','scope','context','records','contrasts','before']}

@lru_cache(maxsize=1)
def raw():
    ds=[]
    for source in SOURCES:
        ds.extend(renamed(d,source['renaming']) for d in parse((ROOT/source['document']).read_text(encoding='utf-8'))['declarations']
            if d['name'] in source['renaming'])
    def add(name,ps,result,body):ds.append(definition(name,ps,result,body))
    entail=[('focus',PC),('alternative',PC),('comparisons',WINDOW)]
    implication=op('implies',evaluate(v('focus'),v('world')),evaluate(v('alternative'),v('world')))
    add('focusentails',entail,T,q('forall','world',S,op('implies',app('comparisons',v('world')),implication)))
    add('focusequivalent',entail,T,op('and',call('focusentails',*args(entail)),call('focusentails',v('alternative'),v('focus'),v('comparisons'))))
    add('focuscontent',[('focus',PC)],C,disquote(v('focus')))
    not_entailed=op('not',call('focusentails',v('focus'),v('alternative'),v('comparisons')))
    excludes=fold(v('alternatives'),'alternative',op('implies',not_entailed,op('not',evaluate(v('alternative'),v('world')))))
    nonempty=op('not',eq(v('alternatives'),dict(kind='sequence',element=PC,items=[])))
    add('focusexclusion',ALTERNATIVE_PARAMS,C,content(allof(app('comparisons',v('world')),nonempty,excludes)))
    additional=fold(v('alternatives'),'alternative',op('and',not_entailed,evaluate(v('alternative'),v('world'))),initial=False,operation='or')
    add('focusaddition',ALTERNATIVE_PARAMS,C,content(op('and',app('comparisons',v('world')),additional)))
    for name,background in [('focusonly',False),('focusalso',True)]:
        other=quoted(quote(ref('focusaddition' if background else 'focusexclusion'),2),*args(QUOTED_PARAMS))
        main=liftfocus(v('focus'))
        add(name,QUOTED_PARAMS,PAIR,call('focuspackage',main if background else other,other if background else main))
    def combine(operation,left,right):
        body=content(op(operation,dict(kind='evaluate',content=v('first'),situation=v('world')),dict(kind='evaluate',content=v('second'),situation=v('world'))))
        return quoted(quote(lam([('first',C),('second',C)],body),2),left,right)
    ps=[('left',PAIR),('right',PAIR)]
    leftclaim=call('focusclaim',v('left'));rightclaim=call('focusclaim',v('right'))
    leftbackground=call('focusbackground',v('left'));rightbackground=call('focusbackground',v('right'))
    for name,operation,filtered in [('focusand','and',False),('focusif','implies',False),('focusfilteredif','implies',True)]:
        background=combine('and',leftbackground,combine('implies',leftclaim,rightbackground) if filtered else rightbackground)
        add(name,ps,PAIR,call('focuspackage',combine(operation,leftclaim,rightclaim),background))
    add('focusattributepackage',ATTRIBUTION,T,call('focusattributed',v('node'),v('author'),
        call('focusthirdrank',call('focusclaim',v('package'))),call('focusthirdrank',call('focusbackground',v('package'))),
        v('foregroundscope'),v('backgroundscope'),v('context'),v('reported'),v('backgrounded')))
    add('topiccontent',[('frame',TOPICFRAME),('reference',DI)],CC,quoted(v('frame'),v('reference')))
    topic=allof(eq(disquote(v('reference')),v('topic')),eq(call('focusclaim',v('package')),call('topiccontent',v('frame'),v('reference'))),
        app('about',v('node'),v('author'),v('reference'),call('focusclaim',v('package')),v('context')),call('focusattributepackage',*args(ATTRIBUTION)))
    add('topicmarked',TOPIC,T,topic)
    add('contrastconjunction',[('left',PC),('right',PC)],C,content(op('and',evaluate(v('left'),v('world')),evaluate(v('right'),v('world')))))
    candidate=app('expects',v('observer'),v('left'),v('right'),v('anchor'),v('candidate'))
    expected=op('and',q('exists','candidate',S,candidate),q('forall','candidate',S,op('implies',candidate,
        op('and',evaluate(v('left'),v('candidate')),op('not',evaluate(v('right'),v('candidate')))))))
    add('contrastexpectation',EXPECTATION,C,content(expected))
    quoted_expectation=[(n,description_sort(t,1 if n in ('left','right') else 0)) for n,t in EXPECTATION]
    add('contrastpackage',quoted_expectation,PAIR,call('focuspackage',quoted(quote(ref('contrastconjunction'),2),v('left'),v('right')),
        quoted(quote(ref('contrastexpectation'),2),*args(quoted_expectation))))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[])

@lru_cache(maxsize=1)
def composed():return normalize_document(raw())

MEANINGS={
 'focusentails':'固定した比較状況の全てで、焦点内容が真なら比較内容も真である。空の比較域では空虚に成立し、全可能状況での論理的含意とは区別する。',
 'focusequivalent':'同じ比較状況域で二内容が相互に含意する。記述の構文同一性や一般的な同義性を認定するものではない。',
 'focuscontent':'段階1の閉じた内容記述から内容を取り出す。真理の評価や段階の無制限な引上げではない。',
 'focusexclusion':'評価点が同じ比較域に含まれ、比較列が非空で、焦点から従わない各比較内容が評価点では偽である内容。従う弱い内容や同値な別記述は排除しない。焦点の真理は別。',
 'focusaddition':'評価点が比較域に含まれ、焦点から従わない比較内容の少なくとも一つがその点で成立するという背景内容。単なる別名、弱い帰結、重複を独立した添加として数えない。',
 'focusonly':'同じ閉じた焦点・比較列・比較域の記述から、排除条件を主張、焦点内容を背景とする組を作る。構成時に内容を実行しない。限定の前提と断言を分けた明示的な読み。',
 'focusalso':'同じ閉じた焦点・比較列・比較域の記述から、焦点内容を主張、独立した添加条件を背景とする組を作る。構成時に内容を実行しない。',
 'focusand':'二つの組の主張を論理積にし、二つの背景も論理積として保持する。背景を主張の一部に潰さない。',
 'focusif':'主張同士を含意にし、両背景は全体に保持するという明示的な投射。前件が偽でも後件の背景を消さない。',
 'focusfilteredif':'主張同士を含意にし、左背景と、左主張が成立するなら右背景も成立するという条件を背景にする。focusifと異なる投射として区別する。',
 'focusattributepackage':'同じ主張/背景の組を段階3へ接続し、同じ著者・箇所・文脈へ、主張範囲と背景範囲を分けて帰属する。二内容の真理は要求しない。',
 'topiccontent':'個体から内容を作る同じ閉じた段階2の枠へ、主題の閉じた個体参照を適用する。条件・否定・量化を枠の内部に保ち、内容を実行しない。',
 'topicmarked':'主題参照が同じ個体を指し、組の主張記述が同じ枠を同じ参照へ適用した記述と一致し、その主題について述べる明示的な関係と組の帰属がある。文法上の主語や内容真理だけから主題を推測しない。',
 'contrastconjunction':'二つの内容が共に成立するという主張内容。これだけでは対比・期待違反・原因を表したことにはしない。',
 'contrastexpectation':'同じ視点・二内容記述・基準文脈の予想候補が非空で、全候補で左内容が成立し右内容は成立しないという背景内容。評価点が変わっても比較の基準文脈を保持する。',
 'contrastpackage':'同じ閉じた二内容から、両内容の成立を主張、指定視点での予想条件を背景とする組を構成する。両方の成立と期待違反を区別し、構成時に引用内容を実行しない。'}
ROLES={
 'foreground':'組の主張側の閉じた内容記述。','background':'組の背景側の閉じた内容記述。',
 'package':'同じ主張記述と背景記述を区別して保持する組。','point':'内容真理を評価する状況。',
 'focus':'固定した焦点の内容記述。生成関数ではその記述の閉じた記述を渡す。','alternative':'含意を比較する内容記述。',
 'alternatives':'順序と重複を保つ比較内容記述の有限列。生成関数では列の閉じた記述を渡す。',
 'comparisons':'含意を判定する固定状況域。生成関数ではその関数の閉じた記述を渡す。',
 'observer':'尺度や期待を帰属する同じ視点。生成関数では閉じた個体参照を渡す。','anchor':'尺度や期待の固定基準文脈。生成関数では閉じた状況参照を渡す。',
 'ranking':'視点・二記述・基準文脈についての厳密な比較関係。','backgroundfunction':'背景内容を作る閉じた段階2の関数記述。',
 'focuscode':'同じ焦点記述を返す閉じた記述。','alternativescode':'同じ比較記述列を返す閉じた記述。',
 'observercode':'比較視点の閉じた個体参照。','anchorcode':'固定基準文脈の閉じた状況参照。','rankingcode':'同じ比較関係の閉じた関数参照。',
 'actionframe':'行為記述から内容を作る共通の閉じた枠。','target':'焦点となる閉じた行為記述。','targets':'比較する行為記述の有限列。',
 'contents':'閉じた内容記述の列。','description':'段階2の閉じた内容記述。','node':'同じ提示・帰属を記録する箇所。',
 'author':'同じ提示や主張を帰属する主体。','foregroundscope':'主張の範囲。','backgroundscope':'背景の範囲。','context':'同じ提示・帰属の文脈。',
 'reported':'箇所・主体・段階3の主張記述・範囲・文脈への帰属。','backgrounded':'同じ箇所・主体・二記述・二範囲・文脈への背景付き提示の帰属。',
 'first':'対比する第一の提示箇所。','second':'対比する第二の提示箇所。','left':'左の組または内容記述。型に従い、生成関数では閉じた記述を渡す。',
 'right':'右の組または内容記述。型に従い、生成関数では閉じた記述を渡す。','scope':'二つの帰属を共有する範囲。',
 'records':'箇所・主体・内容記述・範囲・文脈への帰属。','contrasts':'主体が同じ二記述を指定順で対比して提示する関係。',
 'before':'二つの本文箇所と文脈の順序。出来事の時系列とは別。','topic':'主題として指定する個体。',
 'reference':'同じ主題個体の閉じた参照。','frame':'個体から内容を作る閉じた段階2の枠。条件や否定を内部に保持する。',
 'about':'同じ箇所・主体・主題参照・主張記述・文脈について、その主題について述べる明示的な関係。',
 'expects':'視点・左記述・右記述・基準文脈・候補状況の通常予想関係。生成関数では閉じた関数参照を渡す。'}
LIMITS=[
 '主張、背景、帰属、主題・比較の選定、実際の真理を分ける。自然言語のonly/also/even/butの全用法や、談話主題の自動認定を提供しない。',
 '限定は排除を主張、焦点を背景とする一つの読み。添加は焦点から従わない別内容の成立を要求する読み。弱い帰結や同値別名を新しい情報とせず、一般の添加の唯一の定義とも主張しない。',
 '含意と同値は指定比較域に相対的。限定・添加は評価点の域内所属を要求する。比較域を勝手に狭めて一般的な同義・同一性と見なさない。',
 '旧尺度背景19定義、背景帰属・段階変換・順序付き対比の3定義を改名だけで保持。新定義は同じ型と組へ接続し、古い意味判断を更新しない。',
 '尺度の極端性、他の比較内容の成立、通常予想に反する成立、本文上の対比は別条件。予想候補の全てで右内容の不成立を要求する強い読みであり、確率的傾向一般ではない。',
 '主題は個体参照とその個体を引数に取る明示的な枠へ結合する。一般的な複数主題・談話全体の自動追跡・人間の意図の推測は含まない。',
 '条件文の全体背景と条件付き背景を別操作として示す。どの投射が文脈に適切かは自動選択しない。質問化は主張側の発話記述を作り、元の組は背景を保持する。',
 '引用の構成・帰属では未知の内容を保持できるが、真理・含意・期待の評価は未知入力を拒否する。論理式は短絡しない。第三者読解と円文字接続は別の検証。']

def basis():
    meanings={}
    for source in SOURCES:
        old=json.loads((ROOT/source['basis']).read_text(encoding='utf-8'))
        meanings.update({new:old['definitions'][oldname] for oldname,new in source['renaming'].items()})
    meanings.update(MEANINGS);contracts={}
    for d in raw()['declarations']:
        roles=OLD_ROLES.get(d['name'],[p['name'] for p in d['parameters']])
        assert len(roles)==len(d['parameters'])
        contracts[d['name']]=dict(arguments=[dict(role=n,sort=p['sort'],interpretation=ROLES[n]) for n,p in zip(roles,d['parameters'])],result=d['result'])
    return dict(status='shared_explicit_information_structure',document=LIBRARY,primitives={},definitions=meanings,public_contracts=contracts,
        preserved_sources=SOURCES,design_sources=['examples/v014/count-focus.noema','data/count-focus-basis-v1.json',
            'examples/v014/concession.noema','data/concession-basis-v1.json'],limitations=LIMITS)

def prepare():
    for path,text in [(LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')]:
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published focus source differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':prepare()
