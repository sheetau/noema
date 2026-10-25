"""Description-sensitive belief, explicit evidence and finite provenance proofs."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort,sequence_sort
from scripts.shared_modality import ROOT,v,app,call,op
from scripts.shared_reference import I,S,T,C,definition,lam,truth
from scripts.shared_time import q,allof
from scripts.shared_plurality import MEMBERS,GROUP,PAIR,fold,seq,apply_expr

D=description_sort(C);CLAIMS=sequence_sort(D)
ALTERNATIVES=function_sort([I,S,S],T);AWARE=function_sort([I,D,S],T)
SELECTOR=function_sort([C,S,S],T);HOLDERS=function_sort([I],I);CLAIMOF=function_sort([I],D)
RECORDED=function_sort([I,I,D,S],T);OBSERVED=function_sort([I,I,D,S],T)
RELAYED=function_sort([I,I,I,I,D,S],T);AVAILABLE=function_sort([I,I,S],T)
INFERRED=function_sort([I,I,CLAIMS,D,I,S],T)
LIBRARY='examples/v016/shared-evidence-v1.noema';BASIS='data/shared-evidence-basis-v1.json'
SOURCES=[dict(document='examples/v016/shared-modality-v1.noema',basis='data/shared-modality-basis-v1.json',
    names=['candidatenecessary','candidateexists','candidateexcluded','candidatecontingent']),
    dict(document='examples/v016/shared-plurality-v1.noema',basis='data/shared-plurality-basis-v1.json',names=['memberof','distinctmembers'])]
BELIEF=[('agent',I),('description',D),('context',S),('alternatives',ALTERNATIVES),('aware',AWARE)]
RECORD=[('record',I),('context',S),('holders',HOLDERS),('claims',CLAIMOF),('recorded',RECORDED)]
PROOF=[('order',MEMBERS),('parents',PAIR),('local',GROUP)]
ROOTS=[('order',MEMBERS),('target',I),('parents',PAIR),('roots',PAIR)]
PAIRPROOF=[('left',I),('right',I)]+PROOF+[('roots',PAIR)]

def args(ps):return [v(n) for n,t in ps]
def eq(a,b):return op('equal',a,b)
def neq(a,b):return op('not',eq(a,b))
def evaluate(description,point):return dict(kind='evaluate',content=dict(kind='disquote',description=description),situation=point)
def every(sequence,name,sort,body):return fold(sequence,truth(True),[('sofar',T),(name,sort)],op('and',v('sofar'),body))
def recorded(record):return app('recorded',record,app('holders',record),app('claims',record),v('context'))
def supports(target):return call('proofsupports',*args(PROOF),target)
def roots(target):return call('proofroots',v('order'),target,v('parents'),v('roots'))

@lru_cache(maxsize=1)
def raw():
    ds=[]
    for source in SOURCES:
        ds.extend(deepcopy(d) for d in parse((ROOT/source['document']).read_text(encoding='utf-8'))['declarations'] if d['name'] in source['names'])
    def add(name,ps,body,result=T):ds.append(definition(name,ps,result,body))
    selector=lam([('content',C),('current',S),('world',S)],app('alternatives',v('agent'),v('current'),v('world')))
    add('beliefselector',[('agent',I),('alternatives',ALTERNATIVES)],selector,SELECTOR)
    selected=call('beliefselector',v('agent'),v('alternatives'))
    constant=dict(kind='content',variable='world',body=truth(True))
    add('beliefnonempty',[('agent',I),('context',S),('alternatives',ALTERNATIVES)],call('candidateexists',constant,v('context'),selected))
    content=dict(kind='disquote',description=v('description'))
    for name,modal in [('beliefaccepted','candidatenecessary'),('beliefdenied','candidateexcluded'),('beliefunsettled','candidatecontingent')]:
        add(name,BELIEF,op('and',app('aware',v('agent'),v('description'),v('context')),call(modal,content,v('context'),selected)))
    for name,actual in [('beliefaccurate',evaluate(v('description'),v('context'))),('beliefmistaken',op('not',evaluate(v('description'),v('context'))))]:
        add(name,BELIEF,op('and',call('beliefaccepted',*args(BELIEF)),actual))
    observed=RECORD+[('events',HOLDERS),('observed',OBSERVED)]
    add('evidenceobserved',observed,op('and',recorded(v('record')),app('observed',app('holders',v('record')),
        app('events',v('record')),app('claims',v('record')),v('context'))))
    reported=RECORD+[('prior',I),('relayed',RELAYED)]
    add('evidencereported',reported,allof(neq(v('record'),v('prior')),recorded(v('record')),recorded(v('prior')),
        eq(app('claims',v('record')),app('claims',v('prior'))),app('relayed',app('holders',v('record')),
            app('holders',v('prior')),v('record'),v('prior'),app('claims',v('record')),v('context'))))
    mapped=fold(v('premises'),dict(kind='sequence',element=D,items=[]),[('descriptions',CLAIMS),('premise',I)],
        dict(kind='concat',left=v('descriptions'),right=dict(kind='sequence',element=D,items=[app('claims',v('premise'))])))
    add('evidencepremises',[('premises',MEMBERS),('claims',CLAIMOF)],mapped,CLAIMS)
    inferred=RECORD+[('premises',MEMBERS),('rule',I),('available',AVAILABLE),('inferred',INFERRED)]
    access=every(v('premises'),'premise',I,op('and',recorded(v('premise')),app('available',app('holders',v('record')),v('premise'),v('context'))))
    add('evidenceinferred',inferred,allof(recorded(v('record')),call('distinctmembers',v('premises')),
        op('not',call('memberof',v('premises'),v('record'))),access,
        app('inferred',app('holders',v('record')),v('record'),call('evidencepremises',v('premises'),v('claims')),
            app('claims',v('record')),v('rule'),v('context'))))
    add('evidenceparents',[('record',I),('premises',MEMBERS),('parents',PAIR)],allof(
        call('distinctmembers',v('premises')),op('not',call('memberof',v('premises'),v('record'))),
        q('forall','premise',I,op('iff',app('parents',v('record'),v('premise')),call('memberof',v('premises'),v('premise'))))))
    add('evidencepremisestrue',[('descriptions',CLAIMS),('assessment',S)],every(v('descriptions'),'premise',D,evaluate(v('premise'),v('assessment'))))
    entails=q('forall','world',S,op('implies',app('comparisons',v('world')),op('implies',
        call('evidencepremisestrue',v('descriptions'),v('world')),evaluate(v('conclusion'),v('world')))))
    add('evidenceentails',[('descriptions',CLAIMS),('conclusion',D),('comparisons',function_sort([S],T))],
        op('and',q('exists','world',S,app('comparisons',v('world'))),entails))
    prior=q('forall','premise',I,op('implies',app('parents',v('item'),v('premise')),app('proven',v('premise'))))
    retain=lam([('accepted',T)],lam([('target',I)],op('or',app('proven',v('target')),
        op('and',eq(v('target'),v('item')),v('accepted')))))
    # Evaluate the node's condition once while extending the finite prefix,
    # instead of recalculating it for each later lookup in the predicate.
    proven=fold(v('order'),lam([('target',I)],truth(False)),[('proven',GROUP),('item',I)],
        apply_expr(retain,op('and',app('local',v('item')),prior)))
    add('proofstates',PROOF,proven,GROUP)
    allproven=lam([('proven',GROUP)],every(v('order'),'item',I,app('proven',v('item'))))
    add('proofverified',PROOF,op('and',call('distinctmembers',v('order')),apply_expr(allproven,call('proofstates',*args(PROOF)))))
    add('proofsupports',PROOF+[('target',I)],allof(call('proofverified',*args(PROOF)),call('memberof',v('order'),v('target')),
        apply_expr(call('proofstates',*args(PROOF)),v('target'))))
    ancestor=op('or',eq(v('ancestor'),v('item')),q('exists','premise',I,
        op('and',app('parents',v('item'),v('premise')),app('ancestry',v('premise'),v('ancestor')))))
    ancestry=fold(v('order'),lam([('target',I),('ancestor',I)],truth(False)),[('ancestry',PAIR),('item',I)],
        lam([('target',I),('ancestor',I)],op('or',app('ancestry',v('target'),v('ancestor')),op('and',eq(v('target'),v('item')),ancestor))))
    add('proofancestors',[('order',MEMBERS),('parents',PAIR)],ancestry,PAIR)
    selectedroots=lam([('ancestry',PAIR)],lam([('origin',I)],q('exists','ancestor',I,
        op('and',app('ancestry',v('target'),v('ancestor')),app('roots',v('ancestor'),v('origin'))))))
    add('proofroots',ROOTS,apply_expr(selectedroots,call('proofancestors',v('order'),v('parents'))),GROUP)
    add('prooforigin',PROOF+[('target',I),('origin',I),('roots',PAIR)],op('and',supports(v('target')),apply_expr(roots(v('target')),v('origin'))))
    overlap=q('exists','origin',I,op('and',app('leftroots',v('origin')),app('rightroots',v('origin'))))
    nonempty=lambda name:q('exists','origin',I,app(name,v('origin')))
    for name,condition in [('proofsharedorigin',overlap),('proofseparateorigins',allof(nonempty('leftroots'),nonempty('rightroots'),op('not',overlap)))]:
        add(name,PAIRPROOF,allof(supports(v('left')),supports(v('right')),
            apply_expr(lam([('leftroots',GROUP),('rightroots',GROUP)],condition),roots(v('left')),roots(v('right')))))
    add('proofcorroborates',PAIRPROOF+[('claims',CLAIMOF)],op('and',eq(app('claims',v('left')),app('claims',v('right'))),call('proofseparateorigins',*args(PAIRPROOF))))
    grounded=BELIEF+PROOF+[('target',I),('holders',HOLDERS),('claims',CLAIMOF)]
    add('beliefgrounded',grounded,allof(call('beliefaccepted',*args(BELIEF)),eq(app('holders',v('target')),v('agent')),
        eq(app('claims',v('target')),v('description')),supports(v('target'))))
    add('beliefgroundedtrue',grounded,op('and',call('beliefgrounded',*args(grounded)),evaluate(v('description'),v('context'))))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[])

@lru_cache(maxsize=1)
def composed():return normalize_document(raw())

MEANINGS={
 'beliefselector':'同じ主体の候補関係を、共通の様相関数へ渡せる選択関数にする。内容の真理から候補を補わない。',
 'beliefnonempty':'同じ主体・文脈の候補状況が少なくとも一つある。記述内容を評価しない。',
 'beliefaccepted':'同じ主体が同じ閉じた記述を認識し、その内容が非空の全候補で真であるという信念の読み。実際の真理は別条件。',
 'beliefdenied':'同じ記述を認識し、非空の全候補でその内容が偽である。未知や認識の欠如を否定としない。',
 'beliefunsettled':'同じ記述を認識し、その内容が真の候補と偽の候補の両方がある。',
 'beliefaccurate':'beliefacceptedに加え、同じ評価文脈でその内容が真である。',
 'beliefmistaken':'beliefacceptedに加え、同じ評価文脈でその内容が偽である。',
 'evidenceobserved':'同じ記録・保持者・内容記述・文脈の記録関係と、同じ保持者・出来事・記述・文脈の観察関係がある。観察内容の真理を自動で含めない。',
 'evidencereported':'異なる二記録が同じ記述を持ち、両保持者と前後の記録・同じ記述・文脈を結ぶ伝聞関係がある。前の記録の正当性や現在の内容真理は別に検査する。',
 'evidencepremises':'前提記録列から、順序と重複を保った内容記述列を構成する。記述内容は実行しない。',
 'evidenceinferred':'結論記録があり、重複しない前提記録列に結論自身を含まず、同じ主体が各前提を利用でき、同じ前提記述列・結論記述・規則・文脈の推論記録がある。論理的妥当性は別条件。',
 'evidenceparents':'指定記録の直接の前提が、重複せず自分自身を含まない指定列の要素と過不足なく一致する。観察の空列・伝聞元の一要素列・推論の前提列を証拠グラフへ結ぶ。',
 'evidencepremisestrue':'前提記述列の全内容が同じ評価状況で真である。空列なら真。',
 'evidenceentails':'非空の比較状況範囲で、全前提内容が真なら結論内容が真となる。前提の現実の真理、比較範囲外の妥当性、主体による理解を含めない。',
 'proofstates':'有限順序を左から調べ、局所条件が成立し全ての前提が既に認定された項目を追加する。結果は認定項目の述語。順序全体の妥当性はproofverifiedで別に確認する。',
 'proofverified':'重複しない有限列の全項目がproofstatesで認定される。前提の未記載・後方依存・循環を許さず、空列自体は妥当。局所条件や前提範囲の適切さは入力規約。',
 'proofsupports':'有限順序全体が妥当で、その中に指定対象があり認定されている。内容が真だという一般的証明ではない。',
 'proofancestors':'有限順序に沿って、各項目自身と先に構成された前提の祖先を関係として構成する。循環や順序違いの拒否はproofverifiedで別に行う。',
 'proofroots':'指定対象の祖先に結び付く起源識別子の集合を述語として構成する。重複経路でも同じ起源は同じ要素。入力の起源関係や順序自体を認定する条件ではない。',
 'prooforigin':'妥当な有限証拠列が対象を認定し、その祖先に指定の起源がある。',
 'proofsharedorigin':'両対象が同じ妥当な証拠列で認定され、その起源集合が交わる。異なる話者や記録でも同じ起源を共有し得る。',
 'proofseparateorigins':'両対象が同じ妥当な証拠列で認定され、それぞれ非空の起源集合を持ち、両集合は交わらない。統計的・因果的独立を意味しない。',
 'proofcorroborates':'同じ記述の二記録がproofseparateoriginsを満たすという出所上の別の裏付け。記述同義性や内容真理、確信度の加算は含めない。',
 'beliefgrounded':'同じ主体のbeliefacceptedと、同じ主体が保持する同じ記述の対象記録へのproofsupportsが共に成立する。根拠付きの誤信念も許す。',
 'beliefgroundedtrue':'beliefgroundedに加え、同じ文脈で内容が真である。知識一般の十分条件とはしない。'}
ROLES={
 'agent':'候補状況と記述の認識を帰属する主体。','description':'認識・真理・証拠を比較する閉じた段階0の命題内容記述。',
 'context':'同じ記録と認識を評価する文脈。実際の真理の評価状況としても使う。',
 'alternatives':'主体・文脈・候補状況の明示的な関係。現実を含むとは限らず、未知を空集合にしない。',
 'aware':'主体・記述・文脈についてその記述を認識しているという関係。同じ真理値の別記述へ自動で拡張しない。',
 'record':'観察・伝聞・推論の対象記録。','holders':'記録からその記録を保持する主体を得る関数。',
 'claims':'記録から同じ閉じた内容記述を得る関数。名前だけで真理を与えない。',
 'recorded':'記録・保持者・内容記述・文脈を結ぶ明示的関係。','events':'観察記録から対象の出来事を指定する関数。',
 'observed':'観察主体・出来事・内容記述・文脈についての観察報告の関係。内容が現実に真かは別。',
 'prior':'伝聞元の記録。評価文脈は現在の記録と共通で、実際の発生時刻の前後は別途与える。',
 'relayed':'受け手・伝え手・新記録・元記録・同じ記述・文脈を結ぶ伝達関係。',
 'premises':'推論で用いた有限の前提記録列。順序を保つ。','rule':'その推論記録で指定した規則の識別子。',
 'available':'推論主体が同じ文脈で指定前提記録を利用できる関係。','inferred':'主体・結論記録・前提記述列・結論記述・規則・文脈について推論したという記録。',
 'descriptions':'同じ順序の前提内容記述列。','assessment':'前提内容の真理を評価する状況。',
 'conclusion':'結論の閉じた内容記述。','comparisons':'含意を検査する非空の比較状況範囲。現実や全可能状況を自動で含めない。',
 'order':'認定する証拠記録を前提から結論へ並べた有限列。時刻の列ではない。',
 'parents':'子記録・直接の前提記録の関係。関連する前提を全て与えるという規約を要する。',
 'local':'その記録の観察・伝聞・推論などを認定する局所条件。原則として本文の共通定義を合成して与え、真理の万能判定器とはしない。',
 'target':'有限証拠列で認定または起源を調べる対象記録。','roots':'記録・起源識別子の関係。観察出来事等への対応と網羅性は明示的入力で、異なる識別子の独立を補わない。',
 'origin':'比較する同一起源の識別子。','left':'比較する第一の記録。','right':'比較する第二の記録。'}
LIMITS=[
 '候補状況と記述認識から構成する信念の読み。人間の信念の全用法・理解・記憶・合理性や論理的全知を説明する理論ではない。認識と実際の真理を分ける。',
 '観察・伝達・利用可能性・推論・記録・候補・認識・起源は明示的な解釈入力。基本宣言を追加しないことを、これらの社会的意味を全て還元したことと混同しない。',
 '有限の証拠依存列は、局所認定と指定された全前提に対する構造的条件。内容真理や証拠の信頼性を保証する論理証明ではない。局所推論にevidenceinferredと同じ前提記述のevidenceentailsを接続できる。',
 '前提の利用・記述列・論理的含意・現実の前提真理は異なる。空の前提からの推論も明示できるが、出所集合が空なら別起源の裏付けとは認定しない。',
 '同一起源の再伝聞は根集合の一要素として保持する。根集合が非空で交わらないことを確率的独立・共通原因の不在・真理や確信度の増加としない。起源の同定と網羅性は解釈規約。',
 '候補範囲・比較範囲を明示し、有限検査を全可能状況での同値や妥当性へ昇格させない。beliefgroundedtrueを知識一般の十分条件としない。',
 '未知の解釈は実行を拒否する。論理演算は短絡しないので、最終的に偽になる条件の内部でも必要な入力が未知なら拒否する。',
 '認定列は一つの文脈での有限な依存順序であり、記録発生時刻や因果順序を自動で含めない。後から入力関係を変えて過去の記録を上書きする履歴更新は別に構成する。']

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
    return dict(status='shared_description_belief_and_finite_evidence_provenance',document=LIBRARY,primitives={},definitions=meanings,
        public_contracts=contracts,preserved_sources=SOURCES,
        design_sources=['examples/v013/epistemic.noema','data/epistemic-basis-v1.json','examples/v014/epistemic-revision.noema','data/epistemic-revision-basis-v1.json'],
        limitations=LIMITS)

def prepare():
    for path,text in [(LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')]:
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published evidence source differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':prepare()
