"""Compose changing members, mediated religious oversight, and its common purpose."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_spiritual_guardians import quant

PARENTS=('data/guardian-irrationality-basis-v1.json','data/promissory-oath-basis-v1.json')
LIBRARY='examples/v016/mediated-guardianship.noema'
BASIS='data/mediated-guardianship-basis-v1.json'
CODE='i[h[j[a] d] e]'
TERMS='i[h[j[a]] e]'
PRIMITIVES={
    'h255i':('[a a d] c',['matter','subject','reference'],
        '同じ固定基準で、この具体的な判断・指示の事柄は、この教え・実践の主題に属する。主題一般と個々人に関わる事柄を区別し、同じ役割の別主題の監督を混ぜない。事柄がその人の宗教的生き方に関わるかはsgで別に結ぶ。'),
    'h255j':('[a a a a a d] c',['body','intermediary','role','ward','matter','point'],
        'この団体の指導は、この成員が同じ役割で持つ同じ相手・事柄への指導の立場を通して及ぶ。成員の指示を形成・維持する団体側の指導が下位の指導を左右するという制度的な媒介関係であり、たまたま同じ見解、独立した二つの監督、単なる時間的先行とは分ける。監督の立場の媒介を述べ、各時点で具体的な命令が発せられたり相手が服従したりすること、全体の正当性は要求しない。'),
    'h255k':('[a a '+CODE+' j[a] d d] c',['agreement','body','result','bindings','reference','candidate'],
        '同じ候補の経過で、この団体による同じ合意の制度的な実施・維持が、閉じたNoema結果関数に同じ個体列・固定基準を渡した結果を成立させ継続させる働きをする。単なる同時成立や願望、別の団体・合意の成果では代用しない。結果の真理は合成側で同じ記述を展開して別に要求する。唯一の十分原因、結果が以前は偽だったこと、個々人の不死を追加しない。'),
    'h255l':('[a a '+CODE+' j[a] d] c',['body','agreement','goal','bindings','reference'],
        'この団体は同じ合意を形成する際の共同の目的として、この閉じたNoema内容関数に指定の個体列・固定基準を渡す内容を採用する。団体の実践としての目的設定であり、全成員の私的な内心の目的の一致、外部の観察者による推測、目的の成功や可能性とは分ける。個々の引受け行為がこの共同の目的の実施に位置付くかは別に結ぶ。'),
    'h255m':('[a a a a d] c',['person','activity','body','agreement','point'],
        '本人のこの行為は、同じ団体が同じ合意の形成に採用した共同目的を実施する営みの一部として位置付けられている。私的に同じ望みを持つだけ、別の合意への参加、別行為での目的表明とは分ける。本人の内心の動機の一致、目的の達成や団体の正当性は要求しない。'),
}
MEANINGS={
    'r462':'同じ時点の団体の人である成員について、団体自身が役割を持ってその成員を監督し、同じ役割の範囲に同じ宗教上の事柄を含む。その事柄を固定した同じ主題へ結ぶ。団体を人へ型替えせず、自己監督・別主題の監督を排除する。',
    'r463':'同じ時点の団体成員が、政治的共同体の同じ人に対し、同じ役割・宗教的事柄で後見の立場を持ち、その立場を介して同じ団体の指導が及ぶh255j。役割保持・二者の監督・事柄の分類・媒介を同じ証人へ結ぶ。',
    'r464':'同じ継続的団体と宗教的主題について、その時点の全成員をr462の上位後見の対象とし、同じ政治的共同体の全成員へr463の媒介を要求する。両範囲を非空にし、どの人民にも一人以上の成員による媒介を認める。全成員が全人民を指導することや同じ人の残留は要求しない。',
    'r465':'団体・政治的共同体・主題・固定基準を保持して、各評価時点でr464の同じ上位後見と媒介を述べる内容。成員と人民の範囲は各時点のものを使う。',
    'r466':'同じ共同体の候補の全履歴で、固定基準以後の全時点にr464が続くrcaの内容。途中の空範囲や媒介の中断を飛ばさず、組織と共同体の識別を保持し人の交代を許す。',
    'r467':'r466と同じ範囲・状態について終点のない全将来rcbを要求する内容。各将来時点の後にも同じ履歴の時点があり、単なる終期不明や有限の長期維持とは区別する。数値尺度の無限大を補わない。',
    'r47a':'団体・政治的共同体・主題の正確な三個体列と固定基準からr467の終点なしの同じ後見を作る。永続化の因果に渡す閉じた結果記述であり、独立した別の結果値を使わない。',
    'r47b':'同じ団体・合意・共同体・主題・固定基準について、h255kの制度的実施による成立・維持と、同じr47aを同じ三個体と基準に適用したr467の結果を結ぶ。目的の内側での永続化の成功内容。引用しただけでは成功を断言しない。',
    'r47c':'団体・合意・政治的共同体・主題の正確な四個体列と固定基準について、途切れない上位後見・媒介r466と、同じ合意によるその終点なしの永続化r47bを共通の目的内容にする。sogarの談話上の強調は別に帰属する。',
    'r47d':'同じ団体の全当事者によるr46zと同じ信条への相互宣誓を、r47cの共同目的の採用h255lと結ぶ。各人の同じ引受け行為をその同じ団体・合意の共同目的の営みh255mへ位置付ける。目的を全員の私的な願望へ読み替えず、目的内容は実行しない。',
}
LIMITS=[
    'u0013冒頭の目的を、同じ団体による全成員への上位後見と、その成員を介して政治的共同体の全人民に及ぶ宗教上の後見として読む。単なる二辺の監督や指導関係の推移律でvermittelstを代用しない。',
    '後見の内容は既存dc/hzwn/h253rと正しい順序sg[事柄,人,時点]を組み合わせる。団体側も社会的な役割の担い手になり得るが人aaとはしない。将来の各成員・人民に同じ識別の団体・共同体を使い、基準時の人々の不死を要求しない。',
    'unaufhörlichは全将来の中断なし、verewigenはその状態を同じ合意の実施によって終点なしに成立・維持させる強い目的と読む。後続のauf immerという説明とも対応する採用解釈であり、数値的な時間の無限大は追加しない。rca/rcbは都合よく切り取った観測列を完全な未来へ昇格させない。',
    '終点なしの目的を有限モデルの中で実現したと称さない。有限履歴でr467が偽でも引用された目的は記述でき、原著者の規範的不可能性や現実の物理的不可能性をそれから導かない。',
    '合意の実施を通した団体の共同目的であり、全成員の内心の目的一致を追加しない。目的の採用h255lと同じ行為での制度的参加h255mは解釈入力で、単なる所属・儀礼の実行から推定しない。',
    'sogar、etwaと会議体の例示・自己呼称、sollte nicht berechtigt seinの権限の問い、直後の回答は未統合。本文96主張と確認済み分量を保持する。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    fields='body a member a role a matter a subject a reference d point d'
    text='d r462['+fields+'] c['+both('k h246c[v body v member v point]','k aa[v member]',
        'u[e[v body][v member]]','k hzwn[v body v role v point]','k dc[v body v member v point]',
        'k sg[v matter v member v point]','k h253r[v body v member v role v matter v point]',
        'k h255i[v matter v subject v reference]')+'].\n'
    fields='body a member a role a ward a matter a subject a community a reference d point d'
    text+='d r463['+fields+'] c['+both('k h246c[v body v member v point]','k aa[v member]','k aa[v ward]',
        'k h237c[v ward v community v point]','u[e[v member][v ward]]','k hzwn[v member v role v point]',
        'k dc[v member v ward v point]','k sg[v matter v ward v point]',
        'k h253r[v member v ward v role v matter v point]','k h255i[v matter v subject v reference]',
        'k h255j[v body v member v role v ward v matter v point]')+'].\n'
    fields='body a community a subject a reference d';args='v body v community v subject v reference'
    upper=quant(('role','matter'),'k r462[v body v member v role v matter v subject v reference v point]','g')
    lower=quant(('member','role','matter'),'k r463[v body v member v role v ward v matter v subject v community v reference v point]','g')
    text+='d r464['+fields+' point d] c['+both('k h246d[v body v point]','k h245z[v subject v reference]',
        'g member a[k h246c[v body v member v point]]','g ward a[k h237c[v ward v community v point]]',
        'f member a[y[k h246c[v body v member v point]]['+upper+']]',
        'f ward a[y[k h237c[v ward v community v point]]['+lower+']]')+'].\n'
    text+='d r465['+fields+'] e[b point[k r464['+args+' v point]]].\n'
    for name,temporal in (('r466','rca'),('r467','rcb')):
        text+=('d '+name+'['+fields+'] e[b candidate[k '+temporal+'['+
            'i[at d][k h253w[v community v candidate v at]] '+
            'i[first d last d][k ic[v first v last v candidate]] v reference '+
            'i[at d][k r464['+args+' v at]]]]].\n')
    text+='d r47a[bindings j[a] reference d] e[b candidate['+bind(('body','community','subject'),
        't[k r467['+args+']][v candidate]')+']].\n'
    causal='k h255k[v agreement v body r[p r47a] l[a][v body v community v subject] v reference v candidate]'
    text+='d r47b[body a agreement a community a subject a reference d] e[b candidate['+both(causal,
        't[k r467['+args+']][v candidate]')+']].\n'
    text+='d r47c[bindings j[a] reference d] e[b candidate['+bind(('body','agreement','community','subject'),both(
        't[k r466['+args+']][v candidate]','t[k r47b[v body v agreement v community v subject v reference]][v candidate]'))+']].\n'
    declares='i[person a activity a agreement a terms '+TERMS+' bindings j[a] point d]['+both(
        'k r46y[v body v reference v person v activity v agreement v terms v bindings v point]',
        'k h255m[v person v activity v body v agreement v point]')+']'
    text+='d r47d[body a agreement a creed a subject a community a reference d] c['+both(
        'e[k h254z[v agreement]][v reference]',
        'k h255l[v body v agreement r[p r47c] l[a][v body v agreement v community v subject] v reference]',
        'k hzcg[v agreement r[p r46u] v reference k r46a[v body v reference p h246c] '+
        'i[person a][l[a][v person v agreement v body v creed v subject]] '+
        'i[at d][k h255c[v agreement v reference v at]] p h255a '+declares+']')+'].\n'
    return text


def build():
    old,lib=parents();doc=deepcopy(lib.document);doc['statements']=[]
    imported={d['name']:lib.entries[d['name']] for d in doc['declarations']}
    for d in closure(old.document,['dc','sg','hzwn','h253r','h237c','h246d','rca','rcb']):
        n=d['name'];e=old.entries[n]
        if n in imported:assert imported[n]['declaration']==d and imported[n]['meaning_ja']==e['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(lib.entries))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    paths=set().union(*(set(c.source_sha256) for c in parents()))
    basis=dict(status='same_mediated_religious_guardianship_and_collective_perpetuation_purpose',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
