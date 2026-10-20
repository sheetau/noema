"""Compose unrestricted qualified communication and a separate public calling."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_creed_opinions import NAMES as THOUGHT
from scripts.compose_reform_proposals import NAMES as PROPOSAL
from scripts.compose_protected_remarks import bind

PARENTS=('data/clerical-obligation-basis-v1.json','data/creed-opinions-basis-v1.json','data/reform-proposals-basis-v1.json')
LIBRARY='examples/v016/scholarly-mission.noema'
BASIS='data/scholarly-mission-basis-v1.json'
NAMES=('person','scholar','church','creed','subject')
POLICY=(*NAMES,'frame')
THOUGHT_ITEM=('person','scholar','creed','thought','judgment','beneficiary')
PROPOSAL_ITEM=('person','scholar','church','subject','proposal','field','older','newer','standard')
THOUGHT_VARS=('thought','judgment','beneficiary')
PROPOSAL_VARS=('proposal','field','older','newer','standard')
CODE='i b[h[j[a] d] e]'
PRIMITIVES={
    'h247b':('[a a d] a',['person','scholar','reference'],
        'この本人が学識者として公に理性を用いる立場について、自由と公的に伝える課題を評価する規範の出所。同じ基準で固定し、雇用する教会の命令権や職業資格、現に許した者と同一視しない。具体的な許可・禁止・要求は別に記述し、この参照だけから導かない。'),
    'h247c':('[a a d] a',['person','scholar','reference'],
        '同じ本人の学識者としての公的な伝達の課題を適用する全時機を扱う期間枠。原文外の日時・期限・回数を固定せず、明示した解釈で指定する。成功した時機だけへ事後に絞らない。候補経過ごとの履歴と非空の連続した期間はh7q/h7rとtbで別に確認する。'),
}
MEANINGS={
    'r37a':'見解の伝達r36yへ、本人・活動・学識者・公衆・見解・信条・判断・受益者の正確な八個体列と基準点を渡す目標アダプター。',
    'r37b':'改善提案の伝達r367へ、本人・活動・学識者・公衆・案・教会・領域・主題・比較元・候補・評価基準の正確な十一個体列と基準点を渡す目標アダプター。',
    'r37c':'同じ出所・本人・立場・段階1の目標・束縛列・内容基準・評価点について、正極性の積極的許可h245cと負極性要求h237zの不在を結ぶ自由。許可の不在だけ、実行、能力、不実行の許可とは区別する。',
    'r37d':'同じ資格ある見解について公的伝達候補r36xがあり、同じ学識者の立場での全活動・全公衆候補に、同じr37aの伝達への自由r37cがある。現に許された候補だけを対象にせず、候補欠如を空虚な自由としない。',
    'r37e':'同じ改善提案について公的伝達候補r366があり、同じ学識者の立場の全活動・全公衆候補に、同じr37bの伝達への自由r37cがある。提案の採用や実施への許可へ取り違えない。',
    'r37f':'同じ見解・判断・受益者・信条について、整合した非空の課題期間のいずれかの時機に、同じ学識者の立場で公的伝達r36yが実行される内容。全伝達方法や全時点の実行は要求しない。',
    'r37g':'同じ改善提案と比較の束縛について、整合した非空の課題期間のいずれかの時機に同じ学識者としてr367を実行する内容。案を採用・実施する義務や改善成功を追加しない。',
    'r37h':'同じ本人・学識者・教会・信条・宗教主題・基準で、全ての資格ある見解r36vにr37f、全ての改善提案r364にr37gを課す伝達方針。各項目で伝達方法・時機を選べ、相反する案も伝えることと採用することを分ける。',
    'r37i':'本人・学識者・教会・信条・宗教主題・期間枠の正確な六個体列と基準点からr37hを構成する目標アダプター。',
    'r37j':'同じ本人の同じ信条についての全資格見解と、同じ教会・宗教主題の全改善提案に、r37d/eの全候補への自由が及ぶ。alleとvolleを固定した対象範囲の全称として扱い、内容の真理や伝達済みの項目へ縮めない。',
    'r37k':'同じ学識者の規範源h247bが、本人にその立場で、h247cの期間内の全項目の伝達方針r37iを正極性で要求する。Berufを公的伝達への課題として読む。規範の成立から伝達の実行や案の採用を導かない。',
    'r37l':'同じ本人・学識者・教会・信条・主題・基準・評価点で、全対象の伝達の自由r37jと、公的伝達の課題r37kを別々に要求する。使命から自由を導出せず、自由だけで使命を補わない。',
}
LIMITS=[
    'u0012[3186,3452)のvolle FreiheitとBeruf、alleの範囲を接続する依存群。ja sogar・Aber、同じ聖職者事例への照応と全文著者帰属は未統合で確認文字数を加算しない。',
    '自由は既存の規範的な読みで、肯定許可と反対要求の不在。物理的に妨害がないこと、伝達能力、内容の真理や不実行への許可は加えない。規範源を教会の雇用上の命令と同一化しない。',
    '使命は、固定範囲の資格ある各見解と各提案を公に伝える課題という明示した読み。各候補活動すべてを実行すること、全時点の発言、提案の全採用や実施ではない。伝達時機は明示解釈の期間に置き、原文にない締切を補わない。',
    'r36v/r364が対象の完全な分類を与え、各該当項目を全称で扱う。全称領域を許可・成功・実行で事後に縮めない。資格ある対象がない場合は項目別方針は空虚に満たし、存在や発言の強制を原文外に補わない。対象がある場合の自由は公的活動候補の存在を別に要求する。',
    '慎重な吟味と善意はGedanken側のr36vの資格を保持し、Vorschläge側へ追加しない。提案の相互不整合があっても、全部を採用する義務を述べていないので矛盾する実施を課さない。',
    '基準時の資格と評価時の規範、候補期間内の伝達実行を分ける。各案の比較や改善内容、教義の真理を外側の自由や課題の事実条件へ移さない。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def fields(names):return ' '.join(n+' a' for n in names)+' reference d'
def args(names):return ' '.join('v '+n for n in names)+' v reference'
def seq(names):return 'l[a]['+' '.join('v '+n for n in names)+']'
def quant(names,body,op='f'):
    for n in reversed(names):body=op+' '+n+' a['+body+']'
    return body


def definitions():
    text=''
    for name,target,names in [('r37a','r36y',THOUGHT),('r37b','r367',PROPOSAL),('r37i','r37h',POLICY)]:
        if name=='r37i':continue
        text+='d '+name+'[bindings j[a] reference d] e[b point['+bind(names,'t[k '+target+'['+args(names)+']][v point]')+']].\n'
    norm='v source v person v role v target v bindings v reference '
    text+='d r37c[source a person a role a target '+CODE+' bindings j[a] reference d point d] c['+both(
        'k h245c['+norm+TRUE+' v point]','u[k h237z['+norm+FALSE+' v point]]')+'].\n'
    source='k h247b[v person v scholar v reference]'
    for name,candidate,target,items,names in [('r37d','r36x','r37a',THOUGHT_ITEM,THOUGHT),('r37e','r366','r37b',PROPOSAL_ITEM,PROPOSAL)]:
        scope='k '+candidate+'['+args(names)+']'
        freedom='k r37c['+source+' v person v scholar r b[p '+target+'] '+seq(names)+' v reference v point]'
        text+='d '+name+'['+fields(items)+'] e[b point['+both(quant(('activity','audience'),scope,'g'),
            quant(('activity','audience'),'y['+scope+']['+freedom+']'))+']].\n'
    interval='k tb[i[at d][k h7q[v frame v candidate v at]] i[at d][k h7r[v frame v candidate v at]] i[first d last d][k ic[v first v last v candidate]]]'
    for name,target,items,names in [('r37f','r36y',THOUGHT_ITEM,THOUGHT),('r37g','r367',PROPOSAL_ITEM,PROPOSAL)]:
        actual=quant(('activity','audience'),'t[k '+target+'['+args(names)+']][v at]','g')
        text+='d '+name+'['+fields((*items,'frame'))+'] e[b candidate['+both(interval,
            'g at d['+both('k h7r[v frame v candidate v at]',actual)+']')+']].\n'
    scope_thought='k r36v[v person v thought v judgment v beneficiary v creed v reference]'
    scope_proposal='k r364[v person v proposal v church v field v subject v older v newer v standard v reference]'
    for name,which,extra in [('r37h',('r37f','r37g'),('frame',)),('r37j',('r37d','r37e'),())]:
        conditions=[]
        for scope,variables,target,items in [(scope_thought,THOUGHT_VARS,which[0],THOUGHT_ITEM),
            (scope_proposal,PROPOSAL_VARS,which[1],PROPOSAL_ITEM)]:
            conditions.append(quant(variables,'y['+scope+'][t[k '+target+'['+args((*items,*extra))+']][v point]]'))
        text+='d '+name+'['+fields((*NAMES,*extra))+'] e[b point['+both(*conditions)+']].\n'
    text+='d r37i[bindings j[a] reference d] e[b point['+bind(POLICY,'t[k r37h['+args(POLICY)+']][v point]')+']].\n'
    bindings='l[a]['+' '.join('v '+n for n in NAMES)+' k h247c[v person v scholar v reference]]'
    text+='d r37k['+fields(NAMES)+'] e[b point[k h237z['+source+' v person v scholar r b[p r37i] '+bindings+' v reference '+TRUE+' v point]]].\n'
    text+='d r37l['+fields(NAMES)+'] e[b point['+both('t[k r37j['+args(NAMES)+']][v point]',
        't[k r37k['+args(NAMES)+']][v point]')+']].\n'
    return text


def build():
    old,thought,proposal=parents();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['h245c','h237z','tb','h7q','h7r','ic']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for lib,roots in [(thought,['r36v','r36x','r36y']),(proposal,['r364','r366','r367'])]:
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(p.entries) for p in parents()))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='full_qualified_public_communication_freedom_and_calling',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(set().union(*(set(p.source_sha256) for p in parents())))},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
