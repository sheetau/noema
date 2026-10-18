"""Adopt opportunity-normalized exercise capacity in the Kant manuscript."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-courageous-undertaking.noema'
PARENT_BASIS='data/courageous-undertaking-basis-v1.json'
PARENT_ANNOTATIONS='data/courageous-undertaking-identifiers-v1.json'
FULL='examples/v016/kant-exercise-capacity.noema'
CORE='examples/v016/exercise-capacity-core.noema'
LIBRARY='examples/v016/exercise-capacity.noema'
BASIS='data/exercise-capacity-basis-v1.json'
ANNOTATIONS='data/exercise-capacity-identifiers-v1.json'
BORROWED=('data/standing-ability-basis-v1.json','data/method-scope-basis-v1.json','data/preparation-course-basis-v1.json')
FIELDS='person a goal e anchor d cases h[a d d] c preserved h[a d d] c opportunity h[a d] c preferred h[a d d d] c scope h[a a d d] c checked h[a a d d] c available h[a a d] c outcomes h[a a d d] c selected h[a a d d] c'
ARGS='v person v goal v anchor v cases v preserved v opportunity v preferred v scope v checked v available v outcomes v selected'
MEANINGS={
 'rqvk':'同じ本人・方法・基準・実行状況について、分類が評価済みであり、方法範囲内であり、利用可能でもある方法だけを返す。未分類の方法を肯定の証拠に使わない。',
 'rqvl':'指定状況で分類済み範囲内の達成方法があるか、利用可能な全方法の分類と範囲内の全方法の結果評価が整っていることを要求する。肯定の有効な証拠があれば他方法の未分類で取り消さない。',
 'rqvm':'同じ本人・基準の有効な非空の通常機会プロフィールで、全通常場面のrqvlが成立する。プロフィールの不正や未分類・未評価を不能と補わない。',
 'rqvn':'同じ本人・基準の有効な非空の通常機会プロフィールで、全通常場面に分類済み範囲内の達成方法がある。現在の外的障害だけでこの能力を失わせず、範囲外の習得方法による達成も流用しない。',
 'rqvo':'rqvmの評価条件が整い、rqvnの通常場面全体での行使能力がない。全通常場面で絶対に何もできないという強い条件ではなく、指定した通常行使の基準を満たさないことを表す。',
 'bc':'本人が人であり、自立的な理解力使用bbについて、現在の本人側の判断基盤を保持した通常機会プロフィールで、既有の基盤を行使する能力がないことをrqvoで評価する。外的な機会の欠如だけや将来の取得可能性とは分ける。原文で採る現在の通常行使能力の読みであり、未評価を不能とはしない。',
 'up':'同じ人の自立的理解力使用bbについて、bcと同じプロフィール・行使方法の範囲によるrqvnの能力を状況ごとの内容にする。取得後の別人側状態を基準へ移さない。',
 'fo':'同じ人の自立的理解力使用bbについて、bc・upと同じプロフィール・方法範囲でrqvmの評価条件が整っている内容。旧xeだけの現在地での評価から改訂する。',
 'be':'同じ本人の帰責された未成熟rqrjからupの自立的行使能力へ移る過程。終点も更新したupを用い、現在地のxdだけを終点へ残さない。本人・過程・前後状況とbpからupへの変化の記述は保持する。',
}
CONTEXT={
 'hzsc':(['本人','基準状況','候補状況'],'自立的な理解力使用を評価するため、その本人の基準状態に対して取る機会の候補。実際の履歴の断言ではなく、能力の文脈上の評価範囲である。'),
 'hzsd':(['本人','基準状況','候補状況'],'本人の理解・習慣・決意・勇気など、当該行使能力の基盤として採る状態が基準から保持されていること。結論となる能力そのものの同一性を仮定せず、将来の習得後の状態で基準を置換しない。'),
 'hzse':(['本人','候補状況'],'自立的使用を試みる外的な機会が与えられること。本人の技能・決意・成功・規範上の許可の成立とは別である。'),
 'hzsf':(['本人','基準状況','優先候補','劣後候補'],'同じ本人と基準において、行使能力を評価する通常性の厳密な優先関係。成功結果を見て通常性を選び直すことは正当化しない。'),
 'hzsg':(['本人','方法','基準状況','実行状況'],'自立的理解力使用の評価に採る、既有の判断基盤を行使する方法の範囲。別の基盤を先に習得することを要する準備計画を、その基準時点での行使能力の方法に数えない。考える行為そのものや努力を排除する条件ではない。範囲はNoemaの準備履歴構成などで具体化できる文脈条件であり、本文から特定の測定履歴を捏造しない。'),
 'hzsh':(['本人','方法','基準状況','実行状況'],'同じ方法についてhzsgの区分を判定できること。範囲外という既知の判定と、履歴や判断基準が未確定であることを区別する。'),
}
LIMITS=[
 '現在備わる判断基盤のもとで、機会のある通常場面における自立的な行使能力としてUnvermögenを読む。この採用判断は唯一の哲学的分析や能力一般の必要十分条件の証明ではない。',
 '不能は評価済みの通常行使能力の欠如であり、あらゆる正常場面で個別に不能という強い条件ではない。通常場面の一部で偶然できることを、基準全体を満たす能力とはしない。',
 '通常性、本人側の保持基盤、方法範囲、結果範囲は意味規約を持つ文脈入力。原文にない数値閾値、具体的な訓練履歴、認知機構を著者の主張として追加しない。評価不足はこの解釈内で能力の可否を確定できないことを示す。',
 '方法区分は準備区間の構成で具体化できるが、原文を一つの有限履歴・一つの測定手法へ限定しない。学習一般を排除せず、基準の判断基盤の行使と事前の基盤取得を区別する。',
 '共有するbc・up・fo・beを改訂するため、それらに依存する後続草案の意味も変わる。文の構文が不変でも意味まで不変とは扱わず、全文の採用読解は未確認とする。',
 '第一段落ではラテン語の語義、十分さの文脈基準と段落全体の意味確認が残る。今回の接続だけで全文単位を完了と数えない。',
]


@lru_cache(None)
def catalogs():return (load_catalog(ROOT,PARENT_BASIS),*(load_catalog(ROOT,p) for p in BORROWED))


def definitions():
    text='d rqvk[anchor d scope h[a a d d] c checked h[a a d d] c available h[a a d] c] h[a a d] c[k rqve[v anchor i[p a m a a d s d][w[c[v checked][v p v m v a v s]][c[v scope][v p v m v a v s]]] v available]].'
    availability='k rqvk[v anchor v scope v checked v available]'
    common='v person v goal v scene '+availability+' v outcomes v selected'
    text+='d rqvl[person a goal e anchor d scene d scope h[a a d d] c checked h[a a d d] c available h[a a d] c outcomes h[a a d d] c selected h[a a d d] c] c[x[k xd['+common+']][w[k rqvj[v person v anchor v scene v available v checked]][k xe[v person v scene '+availability+' v outcomes v selected]]]].'
    cases='k rqu6[v person v anchor v cases]';preferred='i[first d last d][c[v preferred][v person v anchor v first v last]]'
    text+='d rqvm['+FIELDS+'] c[w[k rqu7[v person v anchor v cases v preserved v opportunity]][k rqt4['+cases+' '+preferred+' i[scene d][k rqvl[v person v goal v anchor v scene v scope v checked v available v outcomes v selected]]]]].'
    profile='v person v goal v anchor v cases v preserved v opportunity v preferred '+availability+' v outcomes v selected'
    text+='d rqvn['+FIELDS+'] c[k rqva['+profile+']].'
    text+='d rqvo['+FIELDS+'] c[w[k rqvm['+ARGS+']][u[k rqvn['+ARGS+']]]].'
    return text


def ordered(declarations):
    by_name={d['name']:d for d in declarations};assert len(by_name)==len(declarations)
    result=[];seen=set();active=set()
    def visit(name):
        if name in seen:return
        assert name not in active,name;active.add(name)
        for dependency in sorted(_references(by_name[name].get('body'))):visit(dependency)
        result.append(by_name[name]);seen.add(name);active.remove(name)
    for d in declarations:visit(d['name'])
    return result


def build():
    old,*borrowed=catalogs();doc=deepcopy(old.document);statements=deepcopy(doc['statements']);doc['statements']=[]
    assert not (set(CONTEXT)|{'rqvk','rqvl','rqvm','rqvn','rqvo'})&set(old.entries)
    entries=dict(old.entries);have=set(entries)
    for cat in borrowed:
        for d in cat.document['declarations']:
            if d['name'] not in have:
                doc['declarations'].append(deepcopy(d));entries[d['name']]=cat.entries[d['name']];have.add(d['name'])
    doc=parse(format_graph(doc,'compact')+definitions()+
        'r hzsc[a d d] c.r hzsd[a d d] c.r hzse[a d] c.r hzsf[a d d d] c.r hzsg[a a d d] c.r hzsh[a a d d] c.')
    profile='v person k bb[v person] v scene p hzsc p hzsd p hzse p hzsf p hzsg p hzsh p ae p af p ap'
    replacements='d bc[person a scene d] c[w[k aa[v person]][k rqvo['+profile+']]].'
    replacements+='d up[person a] e[b scene[w[k aa[v person]][k rqvn['+profile+']]]].'
    replacements+='d fo[person a] e[b scene[w[k aa[v person]][k rqvm['+profile+']]]].'
    # Parse replacements with the old names removed, after dependency ordering.
    changed={'bc','up','fo'};prefix=deepcopy(doc);prefix['declarations']=closure(doc,['rqvo','rqvn','rqvm','aa','bb',*CONTEXT,'ae','af','ap'])
    parsed=parse(format_graph(prefix,'compact')+replacements)
    lookup={d['name']:d for d in parsed['declarations'] if d['name'] in changed}
    for i,d in enumerate(doc['declarations']):
        if d['name'] in changed:doc['declarations'][i]=lookup[d['name']]
    be=next(d for d in doc['declarations'] if d['name']=='be');hits=[]
    # Reuse the parser's AST for evaluation rather than assuming field names.
    pattern=parse(format_graph(prefix,'compact')+'d ztemp[p a s d] c[t[k bb[v p]][v s]].')['declarations'][-1]['body']
    def patch(value):
        if isinstance(value,dict):
            if value.get('kind')=='call' and value.get('symbol')=='xd':
                person,goal,scene,*rest=value['arguments'];assert goal==dict(kind='call',symbol='bb',arguments=[person]);hits.append(value)
                def subst(x):
                    if isinstance(x,dict):
                        if x.get('kind')=='variable':return deepcopy(person if x['name']=='va' else scene)
                        return {k:('up' if k=='symbol' and v=='bb' else subst(v)) for k,v in x.items()}
                    if isinstance(x,list):return [subst(v) for v in x]
                    return x
                return subst(pattern)
            return {k:patch(v) for k,v in value.items()}
        if isinstance(value,list):return [patch(v) for v in value]
        return value
    be['body']=patch(be['body']);assert len(hits)==1
    doc['declarations']=ordered(doc['declarations']);doc['statements']=statements;doc=parse(format_graph(doc,'compact'))
    core=deepcopy(doc);core['declarations']=closure(doc,['bi','bd','rqrk','rqrl','bc','up','fo','be','hzsb','wa','wh','wb','wc','wd','we','wf','wg']);core['statements']=[doc['statements'][1]]
    lib=deepcopy(doc);lib['declarations']=closure(doc,['rqvk','rqvl','rqvm','rqvn','rqvo']);lib['statements']=[]
    primitives=[];meanings={}
    for d in doc['declarations']:
        n=d['name']
        if d['kind']=='definition':meanings[n]=MEANINGS.get(n) or entries[n]['meaning_ja']
        else:
            labels,meaning=CONTEXT[n] if n in CONTEXT else (entries[n]['arguments'],entries[n]['meaning_ja'])
            primitives.append(dict(symbol=n,parameters=d['parameters'],result=d['result'],arguments=labels,meaning_ja=meaning))
    basis=dict(status='adopted_contextual_exercise_capacity_reading',document=FULL,revises_document=PARENT,
        revises_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=meanings,limitations=LIMITS,
        revision=dict(changed_bodies=['bc','up','be','fo'],new_context_relations=list(CONTEXT),statement_syntax_unchanged=True),
        predecessor_source_sha256={p:sha for cat in catalogs() for p,sha in cat.source_sha256.items()})
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/PARENT_ANNOTATIONS).read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    encoded=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:encoded(basis),ANNOTATIONS:encoded(annotations)}


def main():
    for name,text in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==text,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    print('Shared immaturity, exercise capacity, assessment and departure updated',flush=True)


if __name__=='__main__':main()
