"""Integrate the officer's protected scholarly remarks under an equitable norm."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,FALSE

PARENT='examples/v016/kant-officer-example.noema'
PARENT_BASIS='data/officer-example-basis-v1.json'
DEPENDENCY='data/military-remarks-basis-v1.json'
FULL='examples/v016/kant-protected-remarks.noema'
CORE='examples/v016/protected-remarks-core.noema'
BASIS='data/protected-remarks-basis-v1.json'
ANNOTATIONS='data/protected-remarks-identifiers-v1.json'
NAMES=('office','institution','person','making','presenting','scholar','notes','audience','field')
FIELDS=' '.join(n+' a' for n in NAMES)+' reference d'
ARGS=' '.join('v '+n for n in NAMES)+' v reference'
PUBLIC=('person','making','presenting','scholar','notes','audience','field')
PRIMITIVES={
    'h244d':('[d] a',['reference'],
        'この議論で行為を制限することの当否を、公正・道理に照らして評価するときに採る規範の出所。同じ事情に同じ扱いを求め、役割・他者への影響など関連する事情と、恣意的な好悪・特権を区別する評価の枠組みである。現に命令を出す者や法令の存在とは別の規範源として参照する。具体的な禁止拒否は別に記述し、この参照だけから導かない。'),
    'h244e':('[a d] c',['regulator','reference'],
        'この固定基準で当該公的活動に許否の方針を課す立場となり得る者の範囲。現在許可した者・実際に禁じた者・正当な権限が認められた者だけへ絞らず、議論で関係する全ての規制主体を対象とする。具体的な役職はh235rで別に指定する。'),
    'h244f':('[] a',[],
        '固定原文kant-1784:u0012[2332,2512)、Es kann ihm aberからzur Beurtheilung vorzulegen.までの将校の学識者としての活動を保護する一文全体の箇所。'),
}
MEANINGS={
    'r33g':'本人・作成活動・注記の正確な三個体列からr33dの作成実行内容を構成する。順序と長さを保ち、作品の作成と外部記録を含む対象を閉じた記述として扱う。',
    'r33h':'本人・提出活動・注記・公衆の正確な四個体列からr33eの提出実行内容を構成する。提出の目的である読者の判断を実行条件へ追加しない。',
    'r33i':'本人・作成活動・提出活動・注記・公衆の正確な五個体列からr33fの両実行内容を構成する。作成と提出の単独内容r33g/hとは別に追跡する。',
    'r33j':'規制者・本人・学識者の立場・作成活動・注記の正確な五個体列について、同じ規制者が同じ本人にその立場でr33gの作成を負極性で要求する禁止内容。実際の禁止と不実行、許可の不在を区別する。',
    'r33k':'規制者・本人・学識者の立場・提出活動・注記・公衆の正確な六個体列について、同じ規制者がr33hの提出を負極性で要求する禁止内容。別の作品や公衆の禁止へ移さない。',
    'r33l':'規制者・本人・学識者の立場・作成活動・提出活動・注記・公衆の正確な七個体列について、同じ規制者がr33iの両実行を負極性で要求する禁止内容。単独の作成・提出の禁止とは別の規範対象として保持する。',
    'r33m':'同じ公正な評価規範h244dが、同じ規制者へその方針を定める立場h235rで、r33j/k/lの作成・提出・両実行の禁止内容をいずれも不成立にするよう要求する。内側の不実行要求と外側の禁止拒否を分け、実際の無禁止・積極的許可・物理的不能・本人の実行を導かない。',
    'r33n':'同じ本人・職務・組織が先行文r323の命令事例のいずれかに属する。上官・指揮役職・命令提示・対象行為・極性・事務は同じ事例の中で存在量化し、議論の意向や服従の実行を条件にしない。',
    'r33o':'先行する同じ将校の命令事例r33nと、同じ本人・職務・組織の軍務への注記作成と提出の候補r33cを結ぶ範囲。職務内の議論を学識者としての活動に取り違えず、候補の禁止・実行・評価内容の真理で対象を選び直さない。',
    'r33p':'同じ本人・作成活動・提出活動・学識者の立場・注記・公衆・軍務領域・固定基準について、関係する全規制主体h244eにr33mの禁止拒否要求が及ぶ内容。活動の実行や現実の規制者の行為は要求しない。',
    'r33q':'第五段落の固定基準h232vで、r33oに属する同じ九個体の各組について、同じ評価点でr33pの規範的保護が成立する内容。前件の実例や現在の無禁止を別に断言しない。',
    'r33r':'一文全体r33qを著者waと第五段落の提示h232oへ帰属する。前文r324の職務内の制約と、同じ本人の別の立場での公的使用をr2zgの次元で対照し、先行する服従要求を撤回せず本文順序を保持する。',
}
LIMITS=[
    'Es kann ihm ... nicht verwehrt werdenは、同じ将校の学識者としての活動を規範的に拒否してはならないという読みを採る。物理的に妨害できないこと、実際に禁止がないこと、許可が現に存在すること、作品や提出が実在することとは分ける。',
    'billigermaßenは公正・道理に基づく評価の規範源h244dへの指定として保持する。原文が特定しない法典や統治者を捏造せず、公正さを現職の上官の命令と同一視しない。この規範源から当該禁止の拒否を要求することが文の規範内容であり、評価基準の唯一性や完全な倫理理論の証明は主張しない。',
    '許否を課し得る全ての関係主体h244eに禁止拒否を向ける。主体範囲と方針を定める立場は同じ基準で固定し、今許す主体だけへ縮めない。範囲の供給が現実に網羅的かという問題は解釈の責任であり、有限検査では証明しない。',
    '作成、提出、両方を行うことの各禁止を別に拒否する。連言への禁止だけを拒否して単独の活動を禁じる余地を残さず、禁止拒否から活動内容やその真理を実行しない。単独の保護も、この文で構成する同じ公的な注記の活動の組に属する候補についてである。',
    'ihmは先行する同じ将校の命令事例r323の本人を受ける。職務と軍事組織を保持するが、注記の話題は一つの命令の有用性に限定せず、その組織に関わる軍務の活動・仕組みへ広げる。命令への服従要求は先行文に保持する。',
    'als Gelehrterは同じ本人が学識者の立場で理性を用いて公衆へ見解を向ける活動構成とする。肩書きや免許だけではなく、作成と提出の双方を同じ本人・注記・公衆へ結ぶ。基準時に制作済みの作品を要求しない。',
    'Fehlerは備えるべき条件の不充足という論点、Anmerkungenはそれを分析・説明・指摘する所見の非空のまとまりと読む。原文外の具体的欠陥や固定個数を補わず、注記が扱う欠点の現実の真理を主張しない。',
    'dieseとseinem Publikumは同じ注記とその本人が向ける同じ公衆を受ける。zur Beurtheilungは読者がその注記を判断することを目的とする。全読者の実際の判断・理解・賛同や、判断の正しさを提出の条件へ追加しない。',
    'aberは同じ本人の職務内の制約と学識者としての公的活動の保護との対照であり、先行内容の否定や撤回ではない。書面の記録は実行内容の中へ置き、前件の候補分類には入れない。',
    '全体の意味判断は明示した読みでの通読による。個別の実評価、列アダプターと量化接続の型付き境界検査を区別し、原文との同義性や全現実主体の網羅の自動証明とはしない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)


def bind(names,body):
    body=both('e[v bindings][l[a]['+' '.join('v '+n for n in names)+']]',body)
    for n in reversed(names):body='g '+n+' a['+body+']'
    return body


def definitions():
    text=''
    specs=[('r33g',('person','activity','notes'),'r33d'),
           ('r33h',('person','activity','notes','audience'),'r33e'),
           ('r33i',('person','making','presenting','notes','audience'),'r33f')]
    for name,names,target in specs:
        text+='d '+name+'[bindings j[a]] e[b point['+bind(names,
            't[k '+target+'['+' '.join('v '+n for n in names)+']][v point]')+']].\n'
    bans=[('r33j',('regulator','person','scholar','activity','notes'),'r33g',('person','activity','notes')),
          ('r33k',('regulator','person','scholar','activity','notes','audience'),'r33h',('person','activity','notes','audience')),
          ('r33l',('regulator','person','scholar','making','presenting','notes','audience'),'r33i',('person','making','presenting','notes','audience'))]
    for name,names,target,args in bans:
        body='k h7k[v regulator v person v scholar r[p '+target+'] l[a]['+' '.join('v '+n for n in args)+'] '+FALSE+' v point]'
        text+='d '+name+'[bindings j[a] reference d] e[b point['+bind(names,body)+']].\n'
    claims=[]
    for target,names in [('r33j',('regulator','person','scholar','making','notes')),
                         ('r33k',('regulator','person','scholar','presenting','notes','audience')),
                         ('r33l',('regulator','person','scholar','making','presenting','notes','audience'))]:
        claims.append('k h237z[k h244d[v reference] v regulator k h235r[v regulator v reference] r b[p '+target+'] l[a]['+
            ' '.join('v '+n for n in names)+'] v reference '+FALSE+' v point]')
    text+='d r33m[regulator a person a scholar a making a presenting a notes a audience a reference d] e[b point['+both(*claims)+']].\n'
    # r323's declared order is person, office, institution, issuer, higher,
    # notice, action, work, polarity, reference.
    antecedent='k r323[v person v office v institution v issuer v higher v notice v action v work v polarity v reference]'
    for n,sort in reversed([('issuer','a'),('higher','a'),('notice','a'),('action','a'),('work','a'),('polarity','c')]):
        antecedent='g '+n+' '+sort+'['+antecedent+']'
    text+='d r33n[person a office a institution a reference d] c['+antecedent+'].\n'
    text+='d r33o['+FIELDS+'] c['+both('k r33n[v person v office v institution v reference]',
        'k r33c[v office v institution '+' '.join('v '+n for n in PUBLIC)+' v reference]')+'].\n'
    text+=('d r33p['+' '.join(n+' a' for n in PUBLIC)+' reference d] e[b point[f regulator a[y[k h244e[v regulator v reference]]['+
        't[k r33m[v regulator v person v scholar v making v presenting v notes v audience v reference]][v point]]]]].\n')
    ref='k h232v[]'
    content='y[k r33o['+' '.join('v '+n for n in NAMES)+' '+ref+']][t[k r33p['+' '.join('v '+n for n in PUBLIC)+' '+ref+']][v point]]'
    for n in reversed(NAMES):content='f '+n+' a['+content+']'
    text+='d r33q[] e[b point['+content+']].\n'
    node,author,ctx,quote='k h244f[]','k wa[]','k h232o[]','r d[k r33q[]]'
    text+='d r33r[] c['+both('k h236i['+node+' '+author+' '+quote+' '+ctx+']',
        'k h236k['+node+' '+author+' k h243t[] r d[k r324[]] '+node+' '+quote+' r[p r2zg] '+ctx+']',
        'k ue[k h243t[] '+node+' '+ctx+']','u[e[k h243t[]]['+node+']]')+'].\n'
    return text


def build():
    old,lib=parent(),dependency();doc=deepcopy(old.document)
    statements,doc['statements']=doc['statements'],[];imported={}
    for d in lib.document['declarations']:
        n=d['name']
        if n in old.entries:
            assert d==old.entries[n]['declaration'] and lib.entries[n]['meaning_ja']==old.entries[n]['meaning_ja']
        else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS)) & (set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r33r',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new])
    ds={d['name']:d for d in added}
    meanings={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS
    primitives={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
                for n,e in imported.items() if e['kind']=='primitive'}
    primitives.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='equitable_protection_of_officer_scholarly_remarks',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,definitions=meanings,primitives=primitives,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(lib.source_sha256)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    annotations=json.loads((ROOT/'data/officer-example-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
