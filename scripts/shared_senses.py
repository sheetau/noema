"""Explicit lexical entries, contextual alternatives and scoped replacement."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort,sequence_sort
from scripts.shared_modality import ROOT,v,app,call,op
from scripts.shared_reference import I,S,T,C,definition,lam,truth
from scripts.shared_time import q,allof
from scripts.shared_focus import PC,WINDOW,eq,disquote,quote,ref,quoted

LIBRARY='examples/v016/shared-senses-v1.noema';BASIS='data/shared-senses-basis-v1.json'
N='number';MEMBERS=sequence_sort(I);ARGUMENTS=description_sort(MEMBERS)
MEANING=description_sort(function_sort([MEMBERS],C));CASES=sequence_sort(ARGUMENTS)
FIELDS=[('word',I),('context',I),('sense',I),('meaning',MEANING),('arity',N),('roles',MEMBERS)]
CONSUMER=function_sort([t for n,t in FIELDS],T);ENTRY=function_sort([CONSUMER],T);ENTRIES=sequence_sort(ENTRY)
CHOSEN=function_sort([I,I,I,I,MEANING,N,MEMBERS,I],T)
SYNONYM=function_sort([I,I,I,I,I,I],T)
RELATED=function_sort([I,I,I,MEANING,I,MEANING,I],T)
FRAME=description_sort(function_sort([I,MEANING],C),1)
REPLACE=function_sort([I,I,I,I,I,I,FRAME,I],T)
SOURCES=[dict(document='examples/v016/shared-plurality-v1.noema',basis='data/shared-plurality-basis-v1.json',names=['memberof','distinctmembers']),
    dict(document='examples/v016/shared-focus-v1.noema',basis='data/shared-focus-basis-v1.json',names=['focusentails','focusequivalent'])]
SELECTION=[('entries',ENTRIES),('word',I),('context',I),('occurrence',I),('sense',I),('meaning',MEANING),
    ('arity',N),('roles',MEMBERS),('reason',I),('selected',CHOSEN)]
COMPARISON=[('left',MEANING),('right',MEANING),('arity',N),('cases',CASES),('worlds',WINDOW)]
PAIR=[('left',ENTRY),('right',ENTRY)]
SENSE_COMPARE=PAIR+[('cases',CASES),('worlds',WINDOW)]
SYNONYMS=SENSE_COMPARE+[('reason',I),('licensed',SYNONYM)]

def args(ps):return [v(n) for n,t in ps]
def length(xs):return dict(kind='length',sequence=xs)
def nonempty(xs,element):return op('not',eq(xs,dict(kind='sequence',element=element,items=[])))
def fold(xs,name,type_,body,*,some=False):
    return dict(kind='fold',sequence=xs,initial=truth(not some),step=lam([('accumulator',T),(name,type_)],op('or' if some else 'and',v('accumulator'),body)))
def fields(prefix):return [(prefix+n,t) for n,t in FIELDS]
def unpack(entry,prefix,body):return dict(kind='apply',function=entry,arguments=[lam(fields(prefix),body)])
def both(body):return unpack(v('left'),'left',unpack(v('right'),'right',body))
def same(names):return allof(*(eq(v('left'+n),v('right'+n)) for n in names))
def evaluate(content,world):return dict(kind='evaluate',content=content,situation=world)

@lru_cache(maxsize=1)
def raw():
    ds=[]
    for source in SOURCES:
        ds.extend(deepcopy(d) for d in parse((ROOT/source['document']).read_text(encoding='utf-8'))['declarations'] if d['name'] in source['names'])
    def add(name,ps,body,result=T):ds.append(definition(name,ps,result,body))
    add('senseentry',FIELDS,lam([('consume',CONSUMER)],app('consume',*args(FIELDS))),ENTRY)
    valid=lambda prefix:op('and',eq(length(v(prefix+'roles')),v(prefix+'arity')),call('distinctmembers',v(prefix+'roles')))
    add('entryvalid',[('entry',ENTRY)],unpack(v('entry'),'item',valid('item')))
    add('entrymatches',[('entry',ENTRY)]+FIELDS,unpack(v('entry'),'item',allof(*(eq(v('item'+n),v(n)) for n,t in FIELDS))))
    add('entrysame',PAIR,both(same([n for n,t in FIELDS])))
    add('entrycompatible',PAIR,both(op('implies',same(['word','context','sense']),same(['meaning','arity','roles']))))
    consistent=fold(v('entries'),'other',ENTRY,call('entrycompatible',v('entry'),v('other')))
    add('sensecatalog',[('entries',ENTRIES)],fold(v('entries'),'entry',ENTRY,op('and',call('entryvalid',v('entry')),consistent)))
    candidate=unpack(v('entry'),'item',op('and',eq(v('itemword'),v('word')),eq(v('itemcontext'),v('context'))))
    base=[('entries',ENTRIES),('word',I),('context',I)]
    add('sensecandidates',base,op('and',call('sensecatalog',v('entries')),fold(v('entries'),'entry',ENTRY,candidate)))
    matches=unpack(v('entry'),'item',eq(v('itemsense'),v('sense')))
    add('sensepossible',base+[('sense',I)],op('and',call('sensecandidates',*args(base)),fold(v('entries'),'entry',ENTRY,matches,some=True)))
    add('senseunique',base+[('sense',I)],allof(call('sensecandidates',*args(base)),nonempty(v('entries'),ENTRY),fold(v('entries'),'entry',ENTRY,matches)))
    add('senseresolved',base+[('sense',I),('complete',T)],op('and',v('complete'),call('senseunique',*args(base),v('sense'))))
    different=unpack(v('entry'),'left',unpack(v('other'),'right',op('not',eq(v('leftsense'),v('rightsense')))))
    add('sensemultiple',base,op('and',call('sensecandidates',*args(base)),
        fold(v('entries'),'entry',ENTRY,fold(v('entries'),'other',ENTRY,different,some=True),some=True)))
    present=fold(v('entries'),'entry',ENTRY,call('entrymatches',v('entry'),*args(FIELDS)),some=True)
    chosen=app('selected',v('occurrence'),v('word'),v('context'),v('sense'),v('meaning'),v('arity'),v('roles'),v('reason'))
    add('sensechosen',SELECTION,allof(call('sensecandidates',*args(base)),present,chosen))
    add('senseapplication',[('meaning',MEANING),('arguments',ARGUMENTS)],quoted(v('meaning'),v('arguments')),description_sort(C))
    instance=[('meaning',MEANING),('arguments',ARGUMENTS),('arity',N),('result',description_sort(C))]
    add('senseinstantiated',instance,op('and',eq(length(disquote(v('arguments'))),v('arity')),eq(v('result'),call('senseapplication',v('meaning'),v('arguments')))))
    add('senseinterpreted',SELECTION+[('arguments',ARGUMENTS),('result',description_sort(C))],op('and',call('sensechosen',*args(SELECTION)),call('senseinstantiated',*args(instance))))
    identity=quote(lam([('value',C)],v('value')),1)
    add('meaningfocus',[('meaning',MEANING),('arguments',ARGUMENTS)],quoted(identity,call('senseapplication',v('meaning'),v('arguments'))),PC)
    add('meaningcases',[('arity',N),('cases',CASES)],op('and',nonempty(v('cases'),ARGUMENTS),
        fold(v('cases'),'arguments',ARGUMENTS,eq(length(disquote(v('arguments'))),v('arity')))))
    for name,comparison in [('meaningentails','focusentails'),('meaningequivalent','focusequivalent')]:
        check=call(comparison,call('meaningfocus',v('left'),v('arguments')),call('meaningfocus',v('right'),v('arguments')),v('worlds'))
        add(name,COMPARISON,allof(call('meaningcases',v('arity'),v('cases')),q('exists','world',S,app('worlds',v('world'))),fold(v('cases'),'arguments',ARGUMENTS,check)))
    compare=call('meaningequivalent',v('leftmeaning'),v('rightmeaning'),v('leftarity'),v('cases'),v('worlds'))
    add('senseequivalent',SENSE_COMPARE,allof(call('entryvalid',v('left')),call('entryvalid',v('right')),both(op('and',same(['context','arity','roles']),compare))))
    licensed=app('licensed',v('leftcontext'),v('leftword'),v('leftsense'),v('rightword'),v('rightsense'),v('reason'))
    add('sensesynonymous',SYNONYMS,op('and',call('senseequivalent',*args(SENSE_COMPARE)),both(op('and',op('not',eq(v('leftword'),v('rightword'))),licensed))))
    relation_args=[v('leftword'),v('leftcontext'),v('leftsense'),v('leftmeaning'),v('rightsense'),v('rightmeaning'),v('reason')]
    common=allof(same(['word','context']),op('not',eq(v('leftsense'),v('rightsense'))),op('not',eq(v('leftmeaning'),v('rightmeaning'))))
    ps=PAIR+[('reason',I),('related',RELATED),('unrelated',RELATED)]
    for name,positive,negative in [('sensepolysemous','related','unrelated'),('sensehomonymous','unrelated','related')]:
        add(name,ps,allof(call('entryvalid',v('left')),call('entryvalid',v('right')),both(allof(common,app(positive,*relation_args),op('not',app(negative,*relation_args))))))
    add('senseframed',[('frame',FRAME),('word',I),('meaning',MEANING)],dict(kind='apply',function=disquote(v('frame')),arguments=[v('word'),v('meaning')]),C)
    ps=SYNONYMS+[('occurrence',I),('frame',FRAME),('permitted',REPLACE)]
    permission=app('permitted',v('occurrence'),v('leftcontext'),v('leftword'),v('leftsense'),v('rightword'),v('rightsense'),v('frame'),v('reason'))
    framed=lambda side:evaluate(call('senseframed',v('frame'),v(side+'word'),v(side+'meaning')),v('world'))
    agreement=q('forall','world',S,op('implies',app('worlds',v('world')),op('iff',framed('left'),framed('right'))))
    add('sensereplaceable',ps,op('and',call('sensesynonymous',*args(SYNONYMS)),both(op('and',permission,agreement))))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[])

@lru_cache(maxsize=1)
def composed():return normalize_document(raw())

MEANINGS={
 'senseentry':'語形参照・文脈・語義識別子・閉じた意味関数記述・項数・順序付き役割列を一つの項目として保持する。内容は実行しない。',
 'entryvalid':'senseentryで構成した項目について、項数が役割列の長さに等しく、役割の重複がない。意味関数の現実的な適切さや文脈の妥当性は別。',
 'entrymatches':'項目の六つの欄が、指定した六つの値と過不足なく一致する。意味記述は構文で比較する。',
 'entrysame':'二項目の六つの欄が一致する。高階関数全域を列挙して比較せず、格納した値を取り出す。',
 'entrycompatible':'同じ語形・文脈・語義識別子を持つ二項目は、意味記述・項数・役割列も一致する。別のキーには一致を強制しない。',
 'sensecatalog':'全項目がentryvalidを満たし、同じキーの項目の間に矛盾がない。完全に同じ項目の重複は許す。空の登録列も許す。',
 'sensecandidates':'整合した登録列の全項目が、指定した同じ語形と文脈の候補である。空列を許し、列挙の完了や唯一性を含まない。',
 'sensepossible':'同じ語形・文脈の整合した候補列に、指定の語義識別子がある。内容の真理は調べない。',
 'senseunique':'同じ語形・文脈の整合した非空候補列が全て指定の語義識別子を持つ。同一項目の重複を別候補と数えない。',
 'senseresolved':'senseuniqueに加え、候補列挙が完了している。唯一の観測候補から列挙の完了を推測しない。',
 'sensemultiple':'整合した同じ語形・文脈の候補列に異なる語義識別子がある。登録上の複数性であり、多義と同音異義の分類や現実の曖昧さを自動認定しない。',
 'sensechosen':'整合した同じ語形・文脈の候補列に六欄の一致する項目があり、同じ出現箇所・語形・文脈・語義・意味・項数・役割・理由の選択関係がある。選択後も候補列を保存する。',
 'senseapplication':'閉じた意味関数記述へ、順序付き個体列の閉じた記述を適用し、閉じた内容記述を構成する。項数・語義選択・内容の真理は別条件。',
 'senseinstantiated':'引数列の長さが指定項数に一致し、結果記述が同じ意味関数と同じ列の適用記述に一致する。内容を実行しない。',
 'senseinterpreted':'sensechosenとsenseinstantiatedを同じ項目・意味・項数・引数列・結果記述で結ぶ。内容の真理や他の候補の排除は含まない。',
 'meaningfocus':'意味関数の閉じた適用記述を、恒等適用で段階1の内容記述へ接続する。既存focusentails/focusequivalentへ渡すための変換。',
 'meaningcases':'比較用の閉じた引数列の例が非空で、全例の長さが同じ項数に一致する。全ての可能な引数を列挙した証明ではない。',
 'meaningentails':'非空の比較例と非空の比較状況域で、同じ引数列に適用した左の意味が右の意味を含意する。既存focusentailsを各例へ適用する。',
 'meaningequivalent':'同じ非空の比較例・比較状況域で、二つの意味の適用内容が相互に含意する。領域外の同値性や引用内の置換を保証しない。',
 'senseequivalent':'有効な二項目が同じ文脈・項数・順序付き役割を持ち、指定比較範囲でmeaningequivalentを満たす。語形と記述の一致は要求しない。',
 'sensesynonymous':'異なる二つの語形の項目がsenseequivalentを満たし、同じ文脈・両語形・両語義・理由について同義として扱う明示的な規約がある。範囲内の検査と規約を区別して保持する。',
 'sensepolysemous':'同じ語形・文脈に異なる語義識別子と意味記述があり、同じ二語義・意味・理由について関連を認める関係があり、無関連を認める関係はない。分類の解釈入力を真偽の一致から補わない。',
 'sensehomonymous':'同じ語形・文脈の異なる二語義について、無関連を認める関係があり、関連を認める関係はない。関連の不在だけから無関連を推測しない。',
 'senseframed':'閉じた枠を語形参照と意味記述へ適用し、その出現での内容を作る。枠は語形・記述そのものに言及でき、内容の真理だけで意味を代入しない。',
 'sensereplaceable':'同じ二項目の同義規約と範囲内の同値に加え、同じ出現箇所・文脈・両語形/語義・閉じた枠・理由の置換許可があり、その枠へ各語形と意味を渡した内容も比較域で一致する。引用・認識・待遇などの差を同義性だけで消さない。'}
ROLES={
 'word':'語形または語彙項目への参照。内容の代わりとなる文字列ではなく、意味は別欄に保持する。',
 'context':'登録・候補・選択・同義判断を共有する解釈文脈。','sense':'同じ文脈での語義識別子。',
 'meaning':'順序付きの個体列から内容を作る閉じた段階0の関数記述。',
 'arity':'個体引数の数。役割列の長さとの一致で非負整数に制限する。','roles':'各引数位置の意味役割を示す重複なしの個体参照列。',
 'entry':'六欄を保持する語義項目。','entries':'登録項目または候補項目の有限列。','left':'比較・分類・置換の左側の項目または意味記述。型に従う。',
 'right':'比較・分類・置換の右側の項目または意味記述。型に従う。','complete':'その語形と文脈で候補を尽くしたという明示的判断。',
 'occurrence':'語義を選択または置換する同じ出現箇所。','reason':'選択・分類・同義・置換を認める同じ理由の参照。',
 'selected':'出現箇所・語形・文脈・語義・意味記述・項数・役割列・理由の選択関係。',
 'arguments':'順序付き個体引数列の閉じた記述。','result':'同じ意味の適用から構成した閉じた内容記述。',
 'cases':'比較に用いる閉じた個体引数列記述の有限列。','worlds':'比較する状況域。','licensed':'同じ文脈・両語形・両語義・理由についての同義規約。',
 'related':'同じ語形・文脈・左語義/意味・右語義/意味・理由について関連を認める明示的関係。',
 'unrelated':'同じ七項について無関連を認める明示的関係。関連の単なる否定とは別。',
 'frame':'語形参照と意味記述を受けて内容を作る閉じた段階1の枠。内部の引用や態度を保持する。',
 'permitted':'出現箇所・文脈・左語形/語義・右語形/語義・閉じた枠・理由に対する明示的な置換許可。'}
LIMITS=[
 'ENTRYは既存の関数型による六欄の符号化であり、senseentryで構成した項目を入力契約とする。同じ関数型の任意の関数をレコードとして認証する型や検査ではない。関数を外部から受け取る場合は構成元も確認する。',
 '語形参照、登録語義、文脈ごとの候補、列挙完了、選択、内容評価を区別する。候補を内容の論理和へ潰さず、未確定を偽へ補わない。',
 '意味関数は有限個の個体引数列から内容を作る型で、0項の命題・1項の性質・多項関係を同じ構成で扱う。任意型の多相関数を新設したものではない。他の型には既存の型付き引用適用を使う。',
 '語形への参照と意味役割への参照は解釈入力であり、識別子を振るだけで語義を定義済みとはしない。例では意味本体と選択等の関係をNativeで構成する。',
 '項目の整合・項数の検査は意味関数の全域性を保証しない。論理演算は短絡せず、部分的な意味関数に不正な引数を渡すと評価を拒否し得る。先に項数を確認し、意味の適用と真理評価を分ける。',
 '非空の比較例と状況域における同値は、全引数・全可能状況・全言語使用の同値の証明ではない。同義規約・分類・置換許可の妥当性を有限検査から自動認定しない。',
 '多義/同音異義の分類は二つの肯定的な解釈関係を区別し、両方ある場合や両方ない場合はどちらも認定しない。語源や文化的な関連を自動推定しない。',
 '置換枠は語形と意味記述の双方を受ける。意味が比較域で一致しても、引用や認識・文体に関する枠の内容が変わる場合は置換を認めない。真理値の一致だけでは許可を補わない。',
 '入力の未知は保持・引用できる範囲と実行評価が必要な範囲を分け、必要な入力の未知は拒否する。候補数を確信度や意味の重みに変換しない。円文字接続と第三者読解は別の検証。']

def basis():
    meanings={};contracts={}
    for source in SOURCES:
        old=json.loads((ROOT/source['basis']).read_text(encoding='utf-8'))
        for name in source['names']:
            meanings[name]=deepcopy(old['definitions'][name]);contracts[name]=deepcopy(old['public_contracts'][name])
    meanings.update(MEANINGS)
    for d in raw()['declarations']:
        if d['name'] in MEANINGS:
            contracts[d['name']]=dict(arguments=[dict(role=p['name'],sort=p['sort'],interpretation=ROLES[p['name']]) for p in d['parameters']],result=d['result'])
    return dict(status='shared_contextual_lexical_senses',document=LIBRARY,primitives={},definitions=meanings,public_contracts=contracts,
        preserved_sources=SOURCES,design_sources=['examples/v016/shared-readings-v1.noema','data/shared-readings-basis-v1.json'],limitations=LIMITS)

def prepare():
    for path,text in [(LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')]:
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published senses source differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':prepare()
