"""Grounded belief updates and preserved content-based information comparisons."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort
from scripts.shared_modality import ROOT,v,app,call,op,renamed
from scripts.shared_reference import I,S,T,C,definition,lam,truth
from scripts.shared_time import q,allof
from scripts.shared_evidence import D,ALTERNATIVES,AWARE,CLAIMOF,AVAILABLE,MEMBERS,PAIR,GROUP
from scripts import shared_claim_choice as choice

LIBRARY='examples/v016/shared-revision-v1.noema';BASIS='data/shared-revision-basis-v1.json'
SOURCE='examples/v014/epistemic-revision.noema';SOURCE_BASIS='data/epistemic-revision-basis-v1.json'
NAMES={'rgq':'itemcontentall','ri2':'supportedtrueitem','ri3':'informationcontent','ri4':'informationpreserved',
    'ri5':'informationexpanded','ri6':'errorsreduced','ri7':'errorscleared'}
EVIDENCE='examples/v016/shared-evidence-v1.noema';EVIDENCE_BASIS='data/shared-evidence-basis-v1.json'
REUSED=('candidatenecessary','beliefselector','beliefaccepted','memberof','distinctmembers','proofstates','proofverified','proofsupports')
CORPUS=function_sort([I,I,S],T);CONTENTS=function_sort([I],C);WINDOW=function_sort([S],T)
ORDERS=function_sort([S],MEMBERS);PARENTS=function_sort([S],PAIR);LOCAL=function_sort([S],GROUP)
PRECEDENCE=function_sort([S,S],T);RECEIVED=function_sort([I,I,I,I,D,S,S],T);ADOPTS=function_sort([I,I,D,I,S,S],T)
RELATIONS=[('corpus',CORPUS),('supported',CORPUS),('contents',CONTENTS)]
ITEM=[('holder',I),('claim',I),('stage',S),('assessment',S)]+RELATIONS
PROFILE=[('holder',I),('stage',S),('assessment',S),('scope',GROUP)]+RELATIONS
CHANGE=[('holder',I),('before',S),('after',S),('assessment',S),('scope',GROUP)]+RELATIONS+[('comparisons',WINDOW)]
OLD_PARAMS={'itemcontentall':[('holder',I),('point',S),('stage',S),('corpus',CORPUS),('contents',CONTENTS)],
    'supportedtrueitem':ITEM,'informationcontent':PROFILE,**{n:CHANGE for n in ('informationpreserved','informationexpanded','errorsreduced','errorscleared')}}
CANDIDATES=[('agent',I),('before',S),('after',S),('alternatives',ALTERNATIVES)]
SUPPORT=[('claims',CLAIMOF),('recordclaims',CLAIMOF),('available',AVAILABLE),('orders',ORDERS),('parents',PARENTS),('local',LOCAL)]
RECEIPT=[('agent',I),('source',I),('event',I),('record',I),('description',D),('before',S),('after',S),
    ('recordclaims',CLAIMOF),('received',RECEIVED),('available',AVAILABLE),('precedence',PRECEDENCE)]
USE=RECEIPT+[('reason',I),('adopts',ADOPTS),('alternatives',ALTERNATIVES),('aware',AWARE),('orders',ORDERS),('parents',PARENTS),('local',LOCAL)]

def args(ps):return [v(n) for n,t in ps]
def eq(a,b):return op('equal',a,b)
def neq(a,b):return op('not',eq(a,b))
def disquote(x):return dict(kind='disquote',description=x)
def evaluate(x,point):return dict(kind='evaluate',content=disquote(x),situation=point)
def belief(point):return call('beliefaccepted',v('agent'),v('description'),point,v('alternatives'),v('aware'))

@lru_cache(maxsize=1)
def raw():
    ds=[renamed(d,NAMES) for d in parse((ROOT/SOURCE).read_text(encoding='utf-8'))['declarations']]
    ds += [deepcopy(d) for d in parse((ROOT/EVIDENCE).read_text(encoding='utf-8'))['declarations'] if d['name'] in REUSED]
    ds += deepcopy(choice.document()['declarations'])
    def add(name,ps,body,result=T):ds.append(definition(name,ps,result,body))
    before=app('alternatives',v('agent'),v('before'),v('world'));after=app('alternatives',v('agent'),v('after'),v('world'))
    add('candidatesincluded',CANDIDATES,q('forall','world',S,op('implies',after,before)))
    add('candidatesame',CANDIDATES,q('forall','world',S,op('iff',after,before)))
    add('candidatefiltered',CANDIDATES+[('description',D)],q('forall','world',S,op('iff',after,op('and',before,evaluate(v('description'),v('world'))))))
    corpus=lam([('holder',I),('claim',I),('stage',S)],call('beliefaccepted',v('holder'),app('claims',v('claim')),v('stage'),v('alternatives'),v('aware')))
    add('beliefcorpus',[('claims',CLAIMOF),('alternatives',ALTERNATIVES),('aware',AWARE)],corpus,CORPUS)
    add('claimcontents',[('claims',CLAIMOF)],lam([('claim',I)],disquote(app('claims',v('claim')))),CONTENTS)
    supported=allof(eq(app('recordclaims',v('record')),app('claims',v('claim'))),app('available',v('holder'),v('record'),v('stage')),
        call('proofsupports',app('orders',v('stage')),app('parents',v('stage')),app('local',v('stage')),v('record')))
    add('evidencebasis',SUPPORT,lam([('holder',I),('claim',I),('stage',S)],q('exists','record',I,supported)),CORPUS)
    reception=allof(neq(v('before'),v('after')),app('precedence',v('before'),v('after')),
        eq(app('recordclaims',v('record')),v('description')),
        app('received',*args(RECEIPT[:7])),app('available',v('agent'),v('record'),v('after')))
    add('evidencereceived',RECEIPT,reception)
    used=allof(call('evidencereceived',*args(RECEIPT)),app('adopts',v('agent'),v('record'),v('description'),v('reason'),v('before'),v('after')),
        call('proofsupports',app('orders',v('after')),app('parents',v('after')),app('local',v('after')),v('record')),belief(v('after')))
    add('evidenceused',USE,used)
    changed=op('or',op('not',call('candidatesame',*args(CANDIDATES))),neq(app('aware',v('agent'),v('description'),v('before')),
        app('aware',v('agent'),v('description'),v('after'))))
    add('beliefupdated',USE,op('and',call('evidenceused',*args(USE)),changed))
    add('beliefadopted',USE,op('and',call('evidenceused',*args(USE)),op('not',belief(v('before')))))
    add('evidencefiltered',USE,op('and',call('evidenceused',*args(USE)),call('candidatefiltered',*args(CANDIDATES),v('description'))))
    linked=[('priorholder',I),('nextholder',I),('priorafter',S),('nextbefore',S),('scope',GROUP),
        ('priorclaims',CLAIMOF),('nextclaims',CLAIMOF),('priorcorpus',CORPUS),('nextcorpus',CORPUS),('priorsupported',CORPUS),('nextsupported',CORPUS)]
    same=allof(eq(app('priorclaims',v('item')),app('nextclaims',v('item'))),
        op('iff',app('priorcorpus',v('priorholder'),v('item'),v('priorafter')),app('nextcorpus',v('nextholder'),v('item'),v('nextbefore'))),
        op('iff',app('priorsupported',v('priorholder'),v('item'),v('priorafter')),app('nextsupported',v('nextholder'),v('item'),v('nextbefore'))))
    add('informationlinked',linked,allof(eq(v('priorholder'),v('nextholder')),eq(v('priorafter'),v('nextbefore')),
        q('forall','item',I,op('implies',app('scope',v('item')),same))))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[])

@lru_cache(maxsize=1)
def composed():return normalize_document(raw())

MEANINGS={
 'candidatesincluded':'同じ主体の後段階の全候補が前段階の候補に含まれる。空の後候補も含めた集合関係で、受領や実際の真理を含めない。',
 'candidatesame':'同じ主体の前後の候補状況集合が一致する。記述認識や証拠の変化までは判定しない。',
 'candidatefiltered':'後候補が、前候補のうち同じ記述内容が真の状況と過不足なく一致する。空集合も許す構造条件で、受容の成立ではない。',
 'beliefcorpus':'同じ項目の記述・主体・段階についてbeliefacceptedを適用する受容関係を構成する。記録の受領や現実の真理から受容を補わない。',
 'claimcontents':'固定した項目から同じ閉じた記述を得て、その内容を返す関数。前後の比較中に項目の意味を変えない。',
 'evidencebasis':'同じ主体が同じ段階で利用でき、同じ記述を持つ記録が、その段階の妥当な有限証拠列で認定されるという支持関係を構成する。受容や真理は別。',
 'evidencereceived':'異なる前後段階の先行関係、同じ記録と記述、受け手・出所・受領出来事・前後段階の受領関係、後段階での利用可能性がある。記録の妥当性や信念変化を含めない。',
 'evidenceused':'evidencereceivedに加え、同じ主体・記録・記述・理由・前後段階の採用関係、後段階の証拠列による認定、同じ記述への後段階のbeliefacceptedがある。既に同じ内容を信じていた場合も含む。',
 'beliefupdated':'evidenceusedに加え、前後の候補集合または対象記述の認識状態が変わる。実際の真理や情報増加は別。',
 'beliefadopted':'evidenceusedに加え、前段階のbeliefacceptedは成立していなかった。根拠だけが増えた場合と、新たに受け入れた場合を分ける。',
 'evidencefiltered':'evidenceusedに加え、後候補がcandidatefilteredに一致する。後の受容条件から候補は非空となるが、実際の状況を含むことは補わない。',
 'informationlinked':'同じ主体・同じ境界段階について、指定範囲の項目記述・受容・支持が前記録の後状態と次記録の前状態で一致する。範囲外の情報や候補集合全体、証拠グラフ全体の同一性は主張しない。'}
ROLES={
 'agent':'更新・受領・信念を帰属する同じ主体。','holder':'比較する情報を受け入れる主体。','claim':'比較する命題項目。',
 'stage':'受容・支持を調べる段階。','point':'内容の真理を評価する状況。','assessment':'前後を通して固定する現実の真理の評価状況。',
 'before':'更新前の段階。','after':'更新後の段階。','scope':'前後で固定する命題項目の範囲。',
 'corpus':'主体・項目・段階について受け入れているという関係。単なる受領と区別する。',
 'supported':'主体・項目・段階について根拠による支持がある関係。真理は別に評価する。',
 'contents':'同じ項目の内容を返す固定した関数。','comparisons':'内容情報を比較する状況範囲。前後で同じ範囲を保つ。',
 'alternatives':'主体・段階・候補状況の関係。候補の網羅性や実際の状況の包含は明示的入力。',
 'description':'受領・採用・候補変更で同じ対象とする閉じた段階0の内容記述。',
 'claims':'命題項目から同じ閉じた内容記述を得る固定した関数。',
 'recordclaims':'証拠記録から同じ閉じた内容記述を得る関数。',
 'available':'主体が記録をその段階で利用できる関係。受容とは別。','aware':'主体・記述・段階の認識関係。',
 'orders':'段階ごとの有限な証拠認定順序を返す。','parents':'段階ごとの子記録・直接前提の関係を返す。','local':'段階ごとの証拠の局所認定条件を返す。',
 'source':'記録を受領した出所の識別子。起源の独立性をこの識別子だけで補わない。',
 'event':'同じ受領出来事の識別子。','record':'受領・採用する同じ証拠記録。',
 'received':'受け手・出所・出来事・記録・記述・前段階・後段階の受領関係。',
 'precedence':'指定段階の厳密な先行関係。完全な時間履歴の検査をこの二点の呼出しだけで代替しない。',
 'reason':'採用理由の識別子。','adopts':'主体・記録・記述・理由・前段階・後段階についてその記録を採用したという明示的関係。',
 'priorholder':'前の更新記録の主体。','nextholder':'次の更新記録の主体。','priorafter':'前の更新記録の後段階。','nextbefore':'次の更新記録の前段階。',
 'priorclaims':'前記録での項目記述。','nextclaims':'次記録での項目記述。','priorcorpus':'前記録での受容関係。','nextcorpus':'次記録での受容関係。',
 'priorsupported':'前記録での支持関係。','nextsupported':'次記録での支持関係。'}
LIMITS=[
 '受領・利用可能性・採用・候補変化・情報増加・誤り除去・現在の真理は別条件。受け取っただけで知ったことにせず、同じ内容の再伝聞や恒真な内容の追加を情報増加としない。',
 '候補の交差による更新は明示した一つの型。前候補が真の新情報と両立しない場合の候補拡大や全面改訂を禁止する一般規則ではない。',
 '前後の内容比較は主体・項目範囲・内容関数・評価状況・比較状況を固定する。比較範囲外の全可能状況の同値や、知識量一般の数値化を主張しない。',
 '証拠認定・受領・採用理由・認識・候補・先行関係は明示的解釈入力。内容記述を選ぶclaimchoice基本関数1語を共有し、これを意味の全面的還元と混同しない。',
 'evidenceusedは同じ記述の後の受容と支持を要求するが、内容が真であることは含めない。情報増加と誤り除去は固定した現実の真理も検査する旧定義へ接続する。',
 'informationlinkedは固定範囲の記述・受容・支持の一致。全候補集合・証拠台帳・範囲外の心理状態が同じであるという条件ではない。元の前後関係と証拠を別の関数値として保存し、古い状態を上書きしない。',
 '内容が未知でも受領記録は引用のまま保持できる。内容評価を要する受容・含意・情報比較は未知入力を拒否する。論理演算は短絡しない。']

def basis():
    original=json.loads((ROOT/SOURCE_BASIS).read_text(encoding='utf-8'))
    meanings={new:original['definitions'][old] for old,new in NAMES.items()};contracts={}
    for name,ps in OLD_PARAMS.items():
        d=next(d for d in raw()['declarations'] if d['name']==name)
        contracts[name]=dict(arguments=[dict(role=n,sort=t,interpretation=ROLES[n]) for n,t in ps],result=d['result'])
    old=json.loads((ROOT/EVIDENCE_BASIS).read_text(encoding='utf-8'))
    for name in REUSED:
        meanings[name]=deepcopy(old['definitions'][name]);contracts[name]=deepcopy(old['public_contracts'][name])
    meanings.update(MEANINGS)
    for d in raw()['declarations']:
        if d['name'] in MEANINGS:
            contracts[d['name']]=dict(arguments=[dict(role=p['name'],sort=p['sort'],interpretation=ROLES[p['name']]) for p in d['parameters']],result=d['result'])
    choicebasis=choice.basis();contracts.update(deepcopy(choicebasis['public_contracts']))
    return dict(status='shared_grounded_belief_revision',document=LIBRARY,primitives=deepcopy(choicebasis['primitives']),definitions=meanings,public_contracts=contracts,
        preserved_sources=[dict(document=SOURCE,basis=SOURCE_BASIS,renaming=NAMES),dict(document=EVIDENCE,basis=EVIDENCE_BASIS,names=list(REUSED)),
            dict(document=choice.LIBRARY,basis=choice.BASIS,names=['claimchoice'])],limitations=LIMITS+choice.LIMITS)

def prepare():
    choice.prepare()
    for path,text in [(LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')]:
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published revision source differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':prepare()
