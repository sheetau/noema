"""Finite public adoption records, exact changes and grounded uptake."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort,sequence_sort
from scripts.shared_modality import ROOT,v,app,call,op
from scripts.shared_reference import I,S,T,U,definition,lam,truth
from scripts.shared_time import q,allof
from scripts.shared_readings import every,fold
from scripts.shared_speech import TO,CONVEYS,BEFORE

N='number';D=description_sort(U);DI=description_sort(I)
MESSAGE=description_sort(function_sort([I],U))
OWNERS=sequence_sort(I);CLAIMS=sequence_sort(D);SCAN=function_sort([N],T)
WITHDRAW=function_sort([I,I,D,I,S],T)
CORRECT=function_sort([I,I,D,D,I,S],T)
LIBRARY='examples/v016/shared-conversation-v1.noema';BASIS='data/shared-conversation-basis-v1.json'
SOURCES=[dict(document='examples/v016/shared-quantities-v1.noema',basis='data/shared-quantities-basis-v1.json',names=['rationaladd']),
    dict(document='examples/v016/shared-speech-v1.noema',basis='data/shared-speech-basis-v1.json',
         names=['speechpresented','speechto','speechreceived','speechunderstood','speechaccepted'])]
STATE=[('owners',OWNERS),('claims',CLAIMS)]
CHANGE=[('beforeowners',OWNERS),('beforeclaims',CLAIMS),('afterowners',OWNERS),('afterclaims',CLAIMS)]


def args(ps):return [v(n) for n,t in ps]
def num(n):return dict(kind='number',numerator=n,denominator=1)
def length(x):return dict(kind='length',sequence=x)
def eq(a,b):return op('equal',a,b)
def append(sequence,sort,value):return dict(kind='concat',left=sequence,right=dict(kind='sequence',element=sort,items=[value]))
def has(prefix,owner,claim):return call('commitmenthas',v(prefix+'owners'),v(prefix+'claims'),owner,claim)
def valid(prefix):return call('commitmentvalid',v(prefix+'owners'),v(prefix+'claims'))


@lru_cache(maxsize=1)
def raw():
    ds=[]
    for source in SOURCES:
        ds.extend(deepcopy(d) for d in parse((ROOT/source['document']).read_text(encoding='utf-8'))['declarations'] if d['name'] in source['names'])
    def add(name,ps,body,result=T):ds.append(definition(name,ps,result,body))
    add('commitmentvalid',STATE,eq(length(v('owners')),length(v('claims'))))
    found=allof(eq(v('item'),v('claim')),dict(kind='position',sequence=v('owners'),index=v('index'),value=v('owner')))
    previous=app('previous',call('rationaladd',v('index'),num(-1)))
    scan=fold(v('claims'),lam([('index',N)],truth(False)),[('previous',SCAN),('item',D)],
        lam([('index',N)],op('or',found,previous)))
    last=call('rationaladd',length(v('claims')),num(-1))
    add('commitmenthas',STATE+[('owner',I),('claim',D)],allof(valid(''),dict(kind='apply',function=scan,arguments=[last])))
    subset=q('forall','person',I,every(v('beforeclaims'),'item',op('implies',has('before',v('person'),v('item')),
        has('after',v('person'),v('item')))))
    add('commitmentsubset',CHANGE,allof(valid('before'),valid('after'),subset))
    reverse=[v('afterowners'),v('afterclaims'),v('beforeowners'),v('beforeclaims')]
    add('commitmentsame',CHANGE,op('and',call('commitmentsubset',*args(CHANGE)),call('commitmentsubset',*reverse)))
    target=op('and',eq(v('person'),v('owner')),eq(v('item'),v('claim')))
    exceptone=q('forall','person',I,every(v('beforeclaims'),'item',op('implies',
        op('and',has('before',v('person'),v('item')),op('not',target)),has('after',v('person'),v('item')))))
    add('commitmentexceptsubset',CHANGE+[('owner',I),('claim',D)],allof(valid('before'),valid('after'),exceptone))
    included=call('commitmentsame',v('afterowners'),v('afterclaims'),
        append(v('beforeowners'),I,v('owner')),append(v('beforeclaims'),D,v('claim')))
    cp=CHANGE+[('owner',I),('claim',D)]
    add('commitmentincluded',cp,op('and',valid('before'),included))
    add('commitmentadded',cp,op('and',op('not',has('before',v('owner'),v('claim'))),call('commitmentincluded',*args(cp))))
    removed=allof(has('before',v('owner'),v('claim')),op('not',has('after',v('owner'),v('claim'))),
        call('commitmentsubset',*reverse),call('commitmentexceptsubset',*args(cp)))
    add('commitmentremoved',cp,removed)
    rp=CHANGE+[('owner',I),('oldclaim',D),('newclaim',D)]
    replaced=allof(op('not',eq(v('oldclaim'),v('newclaim'))),has('before',v('owner'),v('oldclaim')),
        op('not',has('after',v('owner'),v('oldclaim'))),has('after',v('owner'),v('newclaim')),
        call('commitmentexceptsubset',*args(CHANGE),v('owner'),v('oldclaim')),
        call('commitmentexceptsubset',*reverse,v('owner'),v('newclaim')))
    add('commitmentreplaced',rp,replaced)
    add('utteranceinstance',[('message',MESSAGE),('subjectdescription',DI)],
        dict(kind='quoted_application',function=v('message'),arguments=[v('subjectdescription')]),D)
    uptake=TO+[('receives',CONVEYS),('understands',CONVEYS),('accepts',CONVEYS)]
    accepted=allof(call('speechaccepted',*args(uptake)),
        eq(v('subject'),dict(kind='disquote',description=v('subjectdescription'))),
        call('commitmentincluded',*args(CHANGE),v('recipient'),call('utteranceinstance',v('message'),v('subjectdescription'))))
    add('commitmentaccepted',CHANGE+uptake+[('subjectdescription',DI)],accepted)
    grounds=[('event',I),('reason',I),('context',S)]
    add('commitmentwithdrawn',cp+grounds+[('withdraws',WITHDRAW)],op('and',call('commitmentremoved',*args(cp)),
        app('withdraws',v('owner'),v('event'),v('claim'),v('reason'),v('context'))))
    add('commitmentcorrected',rp+grounds+[('corrects',CORRECT)],op('and',call('commitmentreplaced',*args(rp)),
        app('corrects',v('owner'),v('event'),v('oldclaim'),v('newclaim'),v('reason'),v('context'))))
    lp=[('priorconversation',I),('nextconversation',I),('priorowners',OWNERS),('priorclaims',CLAIMS),
        ('nextowners',OWNERS),('nextclaims',CLAIMS),('priorpoint',S),('nextpoint',S),('before',BEFORE)]
    add('conversationlinked',lp,allof(eq(v('priorconversation'),v('nextconversation')),
        call('commitmentsame',v('priorowners'),v('priorclaims'),v('nextowners'),v('nextclaims')),
        app('before',v('priorpoint'),v('nextpoint'))))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[])


@lru_cache(maxsize=1)
def composed():return normalize_document(raw())


MEANINGS={
 'commitmentvalid':'採用記録の人物列と発話記述列の長さが等しく、各位置が人物と記述の組になる。記述内容の真理は要求しない。',
 'commitmenthas':'妥当な二列の同じ位置に、指定人物と同じ構文の発話記述の組がある。記述を実行しない。',
 'commitmentsubset':'両状態が妥当で、変更前の全ての人物・記述の組が変更後にもある。順序と重複件数を区別しない。',
 'commitmentsame':'両状態が妥当で、人物と記述の組の集合が等しい。並べ替える場合も人物と記述を対応させる。',
 'commitmentexceptsubset':'両状態が妥当で、指定した人物・記述の一組を除く変更前の全組が変更後にもある。',
 'commitmentincluded':'指定の人物・記述の組を変更前に加えた集合が、変更後の全記録と等しい。既存の同じ組の再受諾も許す。',
 'commitmentadded':'指定の人物・記述の組が以前はなく、それを新規に加えたことだけが状態差である。',
 'commitmentremoved':'以前にあった指定の人物・記述の組だけが変更後からなくなる。他人物と他記述は保持する。',
 'commitmentreplaced':'同じ人物の以前の記述を除き、構文上異なる新記述を加えたことだけが状態差である。新記述が以前からあってもよい。',
 'utteranceinstance':'一個体引数の閉じた発話関数記述へ、閉じた対象記述を適用し、一つの発話記述を構成する。内容を実行しない。',
 'commitmentaccepted':'提示・受領・理解・受諾の既存条件を満たし、対象記述が同じ対象を指し、同じ発話の適用記述を受け手の採用記録へ含めた状態になる。他の記録は保持する。',
 'commitmentwithdrawn':'指定記録だけの除去が成立し、同じ人物・行為・記述・理由・状況について撤回したという明示的な関係が成立する。記述内容の否定は主張しない。',
 'commitmentcorrected':'指定人物の旧記述から新記述への置換が成立し、同じ行為・新旧記述・理由・状況について訂正したという明示的関係が成立する。新記述の真理は要求しない。',
 'conversationlinked':'二更新の会話識別子が同じで、前更新の後状態と次更新の前状態が同じ採用記録を持ち、指定した二時点に前後関係がある。個別の更新の妥当性は別に検査する。'}
ROLES={
 'owners':'記述列と位置で対応する人物の有限列。','claims':'人物列と位置で対応する閉じた段階0の発話記述列。',
 'beforeowners':'変更前の人物列。','beforeclaims':'変更前の発話記述列。',
 'afterowners':'変更後の人物列。','afterclaims':'変更後の発話記述列。',
 'owner':'状態変更の対象人物。提示者や別の受け手へ置き換えない。','claim':'対象とする閉じた発話記述。',
 'oldclaim':'取り除く旧発話記述。','newclaim':'追加する新発話記述。旧記述と構文が異なる。',
 'message':'一個体を対象とする閉じた発話関数の記述。','subjectdescription':'同じ対象を指す閉じた個体記述。受諾時に対象との同一性だけを評価する。',
 'event':'撤回または訂正の行為。','reason':'撤回・訂正を記録する理由や証拠の識別子。','context':'撤回または訂正を記録する状況。',
 'withdraws':'人物・行為・記述・理由・状況に対する撤回の解釈関係。単なる記録の欠落から推測しない。',
 'corrects':'人物・行為・旧記述・新記述・理由・状況に対する訂正の解釈関係。記述の真理から推測しない。',
 'priorconversation':'前更新の会話識別子。','nextconversation':'次更新の会話識別子。',
 'priorowners':'前更新が残した人物列。','priorclaims':'前更新が残した記述列。',
 'nextowners':'次更新が受け取る人物列。','nextclaims':'次更新が受け取る記述列。',
 'priorpoint':'前更新の記録時点。','nextpoint':'次更新の記録時点。','before':'第一時点が第二時点より前だという関係。'}
LIMITS=[
 '状態は会話上採用した人物・発話記述の有限な組の集合である。心理的信念・内容の真理・法的な義務を自動認定しない。否定的内容や相互に矛盾する内容の記録も保持する。',
 '二列の長さが違えば不正状態となる。単独で片方を並べ替えると人物と記述の結合が変わる。同一組の重複と組の並び順は状態の差としない。出来事の回数・時間順は別の履歴で表す。',
 '受諾は同じ記述の既存記録を許す。新規追加は以前の不在を別に要求する。撤回は以前にあった記録を除く読み、訂正は構文上異なる記述への変更という読みである。',
 '撤回・訂正の認定関係は新しい明示的な解釈入力であり、基本宣言を増やさないことを意味の入力が増えないことと混同しない。単なる状態差から出来事や理由を推測しない。',
 '採用記述は段階0の発話。関数適用による記述の構成は引用のまま行い、受諾時は対象記述だけを評価する。対象を同定できない場合は拒否する。任意段階の引用や型への自動拡張ではない。',
 '更新は前後状態の関係を検査する定義であり、外部アプリの状態を自動で書き換える命令ではない。履歴例は旧状態・各行為・根拠・時点を別々に残し、連結だけで個別更新の正当性を補わない。',
 '記述一致は構文の一致。別構文の同義性や語用論的な受諾を推測しない。未知入力は否定に変えず評価拒否。有限モデルは全ての現実の会話や無限領域の証明ではない。']


def basis():
    meanings={};primitives={};contracts={}
    for source in SOURCES:
        old=json.loads((ROOT/source['basis']).read_text(encoding='utf-8'))
        for n in source['names']:
            if n in old['definitions']:meanings[n]=deepcopy(old['definitions'][n])
            else:primitives[n]=deepcopy(old['primitives'][n])
            contracts[n]=deepcopy(old['public_contracts'][n])
    meanings.update(MEANINGS)
    speech=json.loads((ROOT/SOURCES[1]['basis']).read_text(encoding='utf-8'))['public_contracts']['speechaccepted']
    uptake_roles={p['role']:p['interpretation'] for p in speech['arguments']}
    for d in raw()['declarations']:
        if d['name'] in MEANINGS:
            contracts[d['name']]=dict(arguments=[dict(role=p['name'],sort=p['sort'],interpretation=
                (uptake_roles[p['name']] if d['name']=='commitmentaccepted' and p['name'] in uptake_roles else ROLES[p['name']]))
                for p in d['parameters']],result=d['result'])
    return dict(status='shared_public_adoption_state_changes',document=LIBRARY,primitives=primitives,definitions=meanings,
        public_contracts=contracts,preserved_sources=SOURCES,limitations=LIMITS)


def prepare():
    for path,text in ((LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')):
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published conversation differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':prepare()
