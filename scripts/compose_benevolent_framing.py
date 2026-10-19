"""Separate an evaluated favor from critical presentation of that evaluation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT='examples/v016/kant-supervisory-rank.noema'
PARENT_BASIS='data/supervisory-rank-basis-v1.json'
FULL='examples/v016/kant-benevolent-framing.noema'
CORE='examples/v016/benevolent-framing-core.noema'
LIBRARY='examples/v016/critical-evaluation.noema'
BASIS='data/benevolent-framing-basis-v1.json'
ANNOTATIONS='data/benevolent-framing-identifiers-v1.json'
PRIMITIVES={
 'hzxp':(['beneficiary','scene'],'この状況が、指定対象の利益・善を実現する内容として評価される。単に害がないこととは分け、評価基準は解釈で固定する。状況が現実に起きたこと、特定の行為者の意図や受益者の実感は含意しない。'),
 'hzxq':(['actor','goal_description','bindings','scene'],'同じ主体が、指定した閉じた内容関数と順序付き引数で表される目標をそれ自体好ましいものとして求め、実現へ進んで取り組む意向と準備を持つ。単に別の利益を得るための手段として狙うこととは分ける。目標は実行評価せず、実行・実現可能性・成功や他の動機の不在は含意しない。'),
 'hzxr':(['property_description','bindings','scene'],'指定した閉じた内容関数と同じ順序付き引数について、その性質の程度をこの評価文脈で高いものとして扱う。数値尺度、他の全対象を上回る最大性、現実の成立は補わない。基礎の性質の成立は呼出側で別に結ぶ。'),
 'hzxs':(['node','presenter','claim_description','event_description','evaluation_description','context'],'提示者がこの箇所の同じ主張記述の内で記述された出来事を、指定の好意的な評価記述によって描写して提示する。二記述の三個体と一状況の引数は同じ出来事の主体・対象・行為・時点を指す対応を持つ。実際の出来事や評価の真理、誠実な是認は含意せず、過去に誰かが同じ言葉を発したとも補わない。'),
 'hzxt':(['node','presenter','claim_description','event_description','evaluation_description','context'],'同じ箇所・主張記述・出来事・評価の描写において、提示者がその好意的な評価をそのまま是認する立場から批判的に距離を置くことを表現している。単なる引用や態度の不明とは分ける。評価の論理的否定、事実としての悪意、正反対の意味、受け手の理解や笑いを自動的に導かない。'),
}
MEANINGS={
 'rqyl':'既存diの引受け行為の条件を分離したもの。同じ主体・対象・行為・先行状況についてde・dv・hzxoがあり、その状況でも最高位rqyjが成立する。本体の展開は前版diの同じ量化位置と一致する。',
 'rqym':'一対象だけの引数列について、その対象の利益・善が実現する状況hzxpという目標内容。列が空・過剰の場合は満たさず、害がないだけの内容には置き換えない。',
 'rqyn':'同じ主体が自分とは異なる対象の利益を目指し、その目標をそれ自体求めて進んで取り組む意向・準備を持ち、同じ実際の行為へ参加してその行為の目標にもしている。目標や成功を実行評価せず、他の動機の併存は排除しない。',
 'rqyo':'行為・主体・受益対象の三位置を過不足なく持つ列へ、同じrqynの内容を適用する。位置の交換や別対象の善意を混ぜない。',
 'rqyp':'rqylの同じ引受け行為にrqynの他者の利益への姿勢と目的があり、その性質を同じ行為・主体・対象・時点で高い程度として評価する内容。字義通り評価する場合の条件であり、引用されただけで真とはしない。',
 'rqyq':'同じ箇所・提示者・文脈における基礎内容の主張帰属に、同じ出来事記述と評価記述の好意的な描写と、その評価への表明された批判的な距離を結ぶ。両記述は評価せず、評価が真・偽・未知のいずれでも提示の記述と区別する。皮肉の全類型の定義とはしない。',
 'rqyr':'同じ後見人の箇所dqと著者wa・提示文脈whに、既存dpの主張、引受け行為rqyl、その同じ行為の好意的な強い評価rqyp、評価からの批判的距離を結ぶ。gütigstをこの読みで提示する追加の語用的記述であり、現実の親切さやその否定を追加しない。',
}


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def substitute(node,mapping):
    if isinstance(node,list):return [substitute(x,mapping) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='variable' and node['name'] in mapping:return deepcopy(mapping[node['name']])
    return {k:substitute(v,mapping) for k,v in node.items()}


def refactor(doc,old):
    original=old.entries['di']['declaration'];found=[]
    def walk(node):
        if isinstance(node,list):return [walk(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='and' and node['arguments'][0].get('kind')=='call' and node['arguments'][0].get('symbol')=='de' and 'hzxo' in _references(node):
            actor,act,prior=node['arguments'][0]['arguments']
            target=node['arguments'][1]['arguments'][0]['arguments'][2]
            found.append(deepcopy(node))
            return dict(kind='call',symbol='rqyl',arguments=[actor,target,act,prior])
        return {k:walk(v) for k,v in node.items()}
    revised=deepcopy(original);revised['body']=walk(revised['body']);assert len(found)==1
    params=original['parameters'];actor,target=[p['name'] for p in params]
    act=found[0]['arguments'][0]['arguments'][1]['name'];prior=found[0]['arguments'][0]['arguments'][2]['name']
    extracted=dict(kind='definition',name='rqyl',parameters=[dict(name=n,sort=s) for n,s in ((actor,'individual'),(target,'individual'),(act,'individual'),(prior,'situation'))],result='truth',body=found[0])
    at=next(i for i,d in enumerate(doc['declarations']) if d['name']=='di')
    doc['declarations'][at:at+1]=[extracted,revised]
    return doc


def build():
    old=parent();doc=deepcopy(old.document);assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    statements=deepcopy(doc['statements']);doc['statements']=[];doc=refactor(doc,old)
    text='''
r hzxp[a d] c.r hzxq[a i[h[j[a]] e] j[a] d] c.r hzxr[i[h[j[a]] e] j[a] d] c.
r hzxs[a a i[e] i[h[a a a d] c] i[h[a a a d] c] d] c.
r hzxt[a a i[e] i[h[a a a d] c] i[h[a a a d] c] d] c.
d rqym[bindings j[a]] e[b scene[g beneficiary a[w[e[v bindings][l[a][v beneficiary]]][k hzxp[v beneficiary v scene]]]]].
d rqyn[act a actor a beneficiary a scene d] c[w[u[e[v actor][v beneficiary]]][w[k dg[v act v scene]][w[k df[v actor v act v scene]][w[
 k hzxq[v actor r[p rqym] l[a][v beneficiary] v scene]
 ][k hztl[v actor v act r[p rqym] l[a][v beneficiary] v scene]]]]]].
d rqyo[bindings j[a]] e[b scene[g act a[g actor a[g beneficiary a[w[e[v bindings][l[a][v act v actor v beneficiary]]][k rqyn[v act v actor v beneficiary v scene]]]]]]].
d rqyp[actor a target a act a prior d] c[w[k rqyl[v actor v target v act v prior]][w[
 k rqyn[v act v actor v target v prior]
 ][k hzxr[r[p rqyo] l[a][v act v actor v target] v prior]]]].
d rqyq[node a presenter a claim i[e] event i[h[a a a d] c] evaluation i[h[a a a d] c] context d presents h[a a i[e] i[h[a a a d] c] i[h[a a a d] c] d] c distances h[a a i[e] i[h[a a a d] c] i[h[a a a d] c] d] c claims h[a a i[e] d] c] c[
 w[c[v claims][v node v presenter v claim v context]][w[c[v presents][v node v presenter v claim v event v evaluation v context]][c[v distances][v node v presenter v claim v event v evaluation v context]]]
].
d rqyr[] c[k rqyq[k dq[] k wa[] r[k dp[]] r[p rqyl] r[p rqyp] k wh[] p hzxs p hzxt p uc]].
'''
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k rqyr[]].')
    basis=dict(status='benevolent_evaluation_and_critical_presentation_separated',document=FULL,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,primitives={},definitions={},
        predecessor_source_sha256=old.source_sha256,
        limitations=['gütigstを高い程度の好意的な描写と、それへの批判的な距離として読む。皮肉の唯一の理論や著者の内心の検証ではない。',
            '他者の利益、目標への積極的姿勢、程度の基準、提示態度の解釈は基本関係に残る。親切さの全語義・全文化での基準を証明しない。',
            '同じ引受けの四位置を二記述へ対応させる意味規約を持つ。別行為の親切さや、一般的な性格評価へ置き換えない。',
            '最高程度の数値的最大性、評価の正反対、悪意、実際の受益、聞き手の理解は補わない。',
            '集団目的の読み、schon・auch、一文全体・第二段落全体の意味確認は未完。'],
        unresolved=[dict(basis=r['basis'],historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n=d['name']
        if d['kind']=='primitive':
            args,meaning=PRIMITIVES[n] if n in PRIMITIVES else (old.entries[n]['arguments'],old.entries[n]['meaning_ja'])
            basis['primitives'][n]=dict(parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning)
        else:basis['definitions'][n]=MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    core=deepcopy(doc);core['statements']=[doc['statements'][7],doc['statements'][44]];core['declarations']=closure(doc,_references(core['statements']))
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['rqyq','rqym','rqyn','rqyo']),statements=[])
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/supervisory-rank-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for p,s in build().items():write_exact(ROOT/p,s)
    print('Benevolent evaluation and critical presentation composed',flush=True)


if __name__=='__main__':main()
