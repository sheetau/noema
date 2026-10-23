"""Connect intentional adoption, prospective naming and apparent incompatibility."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_light_postulate import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-vacuum-light-postulate.noema';PARENT_BASIS='data/vacuum-light-postulate-basis-v1.json'
FULL='examples/v014/einstein-two-postulates.noema';CORE='examples/v014/two-postulates-core.noema'
BASIS='data/two-postulates-basis-v1.json';ANNOTATIONS='data/two-postulates-identifiers-v1.json';INDEX=214
PRIMITIVES={
 'eiscf':([('agent','a'),('action','i[e]'),('scope','a'),('reference','d')],'指定主体がscopeの議論・活動において、actionで記述された行為をこれから行う方針・意思を明示する。単なる望ましさ、実行能力、命令、既に実行が終わった事実とは区別する。行為の対象と向きは同じ閉じたactionに保持し、この態度の成立から引用された行為やその対象命題の真理を導かない。著者の一人称複数を論述を進める主体の声として読むときにも使えるが、人数や読者全員の同意は規定しない。'),
 'eiscg':([], '相対性の原理をこの論説の以下で呼ぶための呼称個体。印字形Prinzip der Relativitätは識別表記へ記録し、何をこの名で呼ぶかはeischによる同じ内容への結合で与える。名前自体から物理法則や真理を認定しない。'),
 'eisch':([('designation','a'),('target','i[e]'),('scope','a'),('reference','d')],'指定された本文範囲scopeでdesignationという呼称を用いるとき、その呼称が閉じたtargetで指定した同じ内容を指すという命名規約が成立する。綴りの類似、対象がたまたま同じ真偽値を持つこと、当該内容の実証とは区別する。呼称は対象内容の略称として使われ、その内容に無関係な定義を追加しない。scopeの位置と原文上の時制は別に指定する。'),
 'eisci':([('scope','a'),('document','a'),('after','a'),('reference','d')],'scopeが同じdocumentの箇所afterより後に続く本文全体を指す。文書の順序による以後の範囲であり、現在の文だけ、過去の箇所、物理的な未来時刻、特定の後続箇所だけへの抜粋とは区別する。これからその名で呼ばれるという本文上の予告を評価するときに使い、後続の全ての文が必ずその語を使うとは要求しない。'),
 'eiscj':([('first','i[e]'),('second','i[e]'),('reference','d'),('setting','d')],'referenceの判断において、同じ閉じたfirst・secondを両立性の対象として保ったまま検討する、許容される一つの物理的設定setting。共通の物理量・系・時計・単位・法則の解釈を共有し、二内容のそれぞれに別々の世界や意味を割り当てない。対象領域に関係する制約に従う全設定を扱い、両方が真になるものだけを結果から選別しない。両内容の成立と許容設定の存在はsqhの合成で要求する。見かけの候補点での評価はそこでの許容性の見積りであり、現実の許容性を認定する証拠ではない。'),
 'eisck':([('claim','i[e]'),('reference','d'),('candidate','d')],'referenceで利用できる観察・推論・説明上の情報からclaimがどう見えるかを評価する、見かけの候補candidateの全範囲。閉じた同じclaimの対象と意味を保ち、候補点の情報・制約の見積りだけを変える。望んだ結論になる候補だけを選ばず、現実の真理、確信済みの信念、証明と同一視しない。範囲の非空性と全候補で同じ内容が成り立つことは合成で要求する。特定の観察者・数値確率・実際に全員が誤信したことは補わない。'),
 'eiscl':([], '固定原文einstein-1905:u0004[523,889)の第二文。先の推測の前提化を宣言し、今後の呼称を挿入し、見かけ上のみ不整合な真空光速度の仮定を追加する箇所。'),
}
MEANINGS={
 'eifz':'同じ先行推測eifjを、著者が第二文の箇所から同じ論説の議論の仮定として採用する行為の内容。既存ugを使い、内容の真理や証明を要求しない。',
 'eif2':'同じ真空光速度の内容eifyを、著者が同じ箇所・論説で追加の仮定として採用する行為の内容。',
 'eif3':'eifzとeif2という二つの採用行為を同じ点で結んだ、著者の意思の対象。意思を述べるときはこの行為内容を引用し、採用完了の事実に替えない。',
 'eif4':'この箇所より後の本文全体を指す範囲があり、その範囲で相対性原理の呼称が同じeifjの内容を指すという、今後の命名規約。後続全ての文で名称が出現するとは要求しない。',
 'eif5':'同じeifjとeifyを、同じ解釈・物理的制約の許容設定で共に満たす余地があるという両立性。既存sqhを使い、一つずつ別設定で成立するだけでは足りず、現在点で両法則が真であることや全設定での成立は求めない。',
 'eif6':'同じ二内容についてeif5の両立性が成り立たないという不整合の内容。',
 'eif7':'同じ不整合eif6に対する見かけの候補が非空で、全候補でその同じ不整合が成り立つという、見かけ上の不整合。候補点を現在点と同一視しない。',
 'eigd':'見かけ上の不整合eif7と実際の両立性eif5を同じ現在点で結ぶ。nur scheinbarのみによる留保を保ち、真の不整合や単なる未確認へ替えない。',
 'eiga':'二採用行為eif3への意思と、後続本文での同じ推測の命名eif4、および同じ二仮定の見かけ上のみの不整合eigdを結ぶ第二文全体の内容。',
 'eigb':'第二文の意思・命名・留保を述べるeigaを主張するメッセージ。光速度や先行推測自体の現実的な真理の主張へ替えない。',
 'eigc':'同じ著者・論説へのeigbの帰属、第二仮定の追加、先行推測への命名の挿入、光速度仮定への見かけの留保、第一文からの本文順序を接続する。',
}
LIMITS=[
 'Wir wollenは著者が議論を進める声による方針・意思の明示と読む。著者以外の人数や読者の同意、採用行為の完了を補わず、仮定の内容を実証済みとしない。',
 'diese Vermutungとderen Inhaltは同じeifj全体を指し、第一文の既証の限定eifqだけや光速度eifyへ替えない。Prinzip der Relativitätという呼称は以後の本文の範囲でこの内容へ結ぶ。',
 'mit ihmの先行詞はこの同じ相対性原理の内容eifj。nur scheinbar unverträglichは見かけの候補では不整合だが、現在の判断点では同じ二内容が両立するという読みを採る。物理的な両立性の証明をこの翻訳で完遂したとはしない。',
 '光速度eifyは前回の明示した読みを引き継ぐ。全力学適格系・全真空光伝播区間・全光源運動状態・共通単位・同期した局所時刻と同じVを保ち、数値を補わない。',
 '第二文全体を記述する。第三文の二前提の十分性、第四文の光エーテル不要と段落全体の通読判断は残る。',
]

def quote(n):return 'r[k '+n+'[]]'

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    for name,target in (('eifz','eifj'),('eif2','eify')):
        text+=content(name,k('ug',k('eiscl'),k('rd'),quote(target),k('eirf'),v('point')))
    text+=content('eif3',both(evaluate('eifz'),evaluate('eif2')))
    text+=content('eif4',q('g','scope','a',both(k('eisci',v('scope'),k('eirf'),k('eiscl'),v('point')),k('eisch',k('eiscg'),quote('eifj'),v('scope'),v('point')))))
    allowed='i[setting d]['+k('eiscj',quote('eifj'),quote('eify'),v('point'),v('setting'))+']'
    text+=content('eif5',k('sqh',allowed,k('eifj'),k('eify')))
    text+=content('eif6',op('u',evaluate('eif5')))
    candidate=lambda x:k('eisck',quote('eif6'),v('point'),x)
    text+=content('eif7',both(q('g','candidate','d',candidate(v('candidate'))),q('f','candidate','d',op('y',candidate(v('candidate')),'t[k eif6[]][v candidate]'))))
    text+=content('eigd',both(evaluate('eif7'),evaluate('eif5')))
    text+=content('eiga',both(k('eiscf',k('rd'),quote('eif3'),k('eirf'),v('point')),evaluate('eif4'),evaluate('eigd')))
    text+='d eigb[] f[j s[k eiga[]]].\n'
    text+=define('eigc',[],both(k('eir3',k('eiscl'),k('rd'),k('eirf'),quote('eigb'),k('ri')),
        k('eisb2',k('eiscl'),k('rd'),quote('eifz'),quote('eif2'),k('eirf'),k('ri')),
        k('eisa5',k('eiscl'),k('rd'),quote('eifj'),quote('eif4'),k('ri')),
        k('eisa5',k('eiscl'),k('rd'),quote('eify'),quote('eigd'),k('ri')),
        k('ue',k('eisb4'),k('eiscl'),k('ri')),op('u',op('e',k('eisb4'),k('eiscl')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eigc',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='two_postulates_intended_adoption_future_naming_apparent_incompatibility',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/vacuum-light-postulate-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eiscg',role='designation',forms=[dict(text='Prinzip der Relativität',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
