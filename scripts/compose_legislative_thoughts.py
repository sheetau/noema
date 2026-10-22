"""Compose a legislative improvement issue and one's own public thoughts on it."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_protected_remarks import bind

PARENT='data/religious-emphasis-sentence-basis-v1.json';DEPENDENCY='data/legislative-formulations-basis-v1.json'
LIBRARY='examples/v016/legislative-thoughts.noema';BASIS='data/legislative-thoughts-basis-v1.json'
FRAME=('ruler','people','community','baseline','oldform','standard')
FIELDS=' '.join(n+' a' for n in FRAME)+' reference d';ARGS=' '.join('v '+n for n in FRAME)+' v reference'
PUBLIC=('person','activity','scholar','audience');NAMES=(*PUBLIC,*FRAME)
ISSUE='i[h[a a] e]';TARGET='i b[h[j[a] d] e]'
PRIMITIVES={
 'h26tg':('[a a d] c',['standard','community','reference'],
   '同じ政治的共同体・固定基準で、公的な共同行為を規律する法をどう定めるのがより適切かを比較する評価観点の束である。規範内容の整合・目的への適合・表現の明晰さなどを具体的な観点として指定でき、一つの現代的な立法理論や数値尺度へ固定しない。単なる本人の好み、出現頻度、実際の採択だけで適切さを代用せず、指定した観点の実質的妥当性は解釈入力に責任がある。'),
 'h26th':('[a a a a a a d d] c',['standard','leftlaw','leftform','rightlaw','rightform','community','reference','point'],
   '同じ評価観点・共同体・固定基準・評価点で、左の全法内容を左の定式で定めることの適切さが、右の全法内容を右の定式で定めることの適切さ以下である。表現と規範内容の対応は別に確認する。本人の賛成、現在の効力、語数や改訂日付の順序とは区別し、比較の向き・同順位を保つ。実際の優越を判断の外側で先に肯定しない。'),
 'h26ti':('[a i[h[a d] e] d '+ISSUE+'] c',['item','provider','reference','issue'],
   '同じ項目・内容供給関数・固定基準が表す命題内容は、指定の閉じた二引数の検討課題についての見解である。課題は改訂法内容とその定式を引数に取り、何が同じ比較元より適切な定め方となるかを指定する。見解は特定案の肯定だけでなく、改善の条件・限界・方法についての肯定又は否定を内容に含めてよい。単なる語の共起や別法の話題にせず、項目の全内容自体は供給関数にNoemaで明示する。課題を実行して成功案があることや見解の真理を要求しない。'),
}
MEANINGS={
 'r6cq':'同じ統治者・人民・共同体・比較元の法と定式・評価観点・固定基準について、改訂法と新定式の二引数を取る改善の課題内容。r6cpの両全法内容と改訂方向を保ち、両側の反射的比較と元以下新・新以下元の否定により厳密な優越を作る。同順位を改善にせず、語数・採択の新しさへ置換しない。',
 'r6cr':'六個体と基準の閉じた呼称をr6cqへ適用し、改訂法と定式の二引数を残す閉じた検討課題の記述を作る。特定の成功案を選んでから見解の範囲を定めない。',
 'r6cs':'同じ六対象と基準のh223g/h223hの呼称をr6crへ渡す。r6ctで呼称の一致を検査し、同じ改善課題を保持判断と提示に共有する。',
 'r6ct':'同じ六対象と基準について、呼称が元の対象を指し、比較元の全法内容・定式がr6cmの同じ立法範囲にあり、観点h26tgが同じ共同体の法の適切さを扱うことを確認する。成功する改訂案やその真理を入力妥当性へ混ぜない。',
 'r6cu':'同じ本人が、同じ改善課題についての代表内容をr53nの自分の保持判断として持つ。同じh26aeの内容供給と代表h26agへ結び、他人の見解の引用や別の課題を本人の思想にしない。特定案への賛成や改善の客観的成功、根拠ある洞察まで要求しない。',
 'r6cv':'r6cuの同じ本人・項目・改善課題を、同じ活動・学識者の立場・全読者公衆への本人名義の公的提示r53qへ結ぶ。その同じ活動で自分の理解力を使うab/acを要求するが、本文にない審査目的や全世界の受領を追加しない。',
 'r6cw':'非空の任意有限項目列の全項目に、同じ本人・一つの活動・立場・公衆・立法課題・基準・点でr6cvを要求する。複数の見解を一つの発表候補に束ね、一つ以上ならよく、異なる活動や他人の保持判断を寄せ集めない。',
 'r6cx':'同じ項目列と、本人・活動・学識者・公衆・統治者・人民・共同体・比較元法・旧定式・観点の正確な十対象列と基準からr6cwの実行内容を返す。臣民の範囲と許可は後で同じ内容へ結ぶ。',
 'r6cy':'項目列の閉じた記述をr6cxへ固定し、十対象列と基準を受ける段階1の公的思想提示内容を引用として作る。許可の対象にしても、保持判断や発表の実行を許可時点の外側の前提へ移さない。',
}
LIMITS=[
 'u0016第二文ihre Gedanken über eine bessere Abfassung derselben ... der Welt öffentlich vorzulegenへ向けた依存群。前回の全法内容・定式・改訂方向に、評価観点、改善課題、自分の保持見解、公的理性使用と本人名義の提示を結ぶ。率直な批判・全臣民への許可・安全性・洞察・全文提示はまだ接続しない。',
 'bessereを、同じ公的規律を定める上での適切さの厳密な改善と読む。二側が同順位なら優越は成立しない。表現の明晰さだけにも規範内容の変更だけにも狭めず、数値尺度や唯一の最良案を追加しない。観点は発表候補ごとに指定でき、君主や現行制度が実際に賛成する観点だけには限らない。',
 'Gedanken überは、改善の課題について本人が持つ見解として読む。全ての発言が完成した特定案を最良と肯定するとはしない。改善条件、限界、方法を述べる内容や、特定の改善案を退ける内容もh26aeで記述できる。検討課題に引数を残すことで、実際に改善が可能又は採択されたことを、見解を述べる前提にしない。',
 '自分の見解は同じ本人・代表項目・固定基準の受容と保持判断である。内容は供給されたNoema命題であり、原語の名前や肯定の真偽だけで代用しない。これは主張として提示する思想の読みで、あらゆる内的イメージや純粋な問いを思想一般の定義から排除したという主張ではない。',
 '公的理性使用は既存の学識者の立場と全読者公衆への宛先を保持し、実行には同じ活動で本人の理解力を使い、非空の人間の受け手へ本人名義で同じ内容を提示することを要求する。全読者の受領・理解・賛同や、同じ内容の客観的真理は要求しない。',
 '前段落のzur Prüfungと違い、この文には審査目的を明示する語がないためr53sではなくr53qを使い、hzuの追加目的を課さない。公的自由の一般概念を私的な無制約の行動にせず、実際の発表内容は後で引用して許可対象にする。',
 '有限の非空項目列は一つの発表候補であり、全見解や全人を一つの固定列に閉じない。候補ごとの全列・人物・立法課題・改訂観点の網羅は次の許可範囲で扱う。r6cyの引用から現在の発表や臣民の現在の信念を断定しない。',
 '正本118主張・18全単位判断・第一文336文字は保持する。局所試験は比較方向・引用と現実の分離・同じ判断と発表・引数結合を確認し、主張の真理や第二文全文の意味一致を自動的に証明しない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)
def definitions():
    compare=lambda l,f,r,g:'k h26th[v standard v '+l+' v '+f+' v '+r+' v '+g+' v community v reference v point]'
    improvement=both('k r6cp[v ruler v people v community v baseline v revision v oldform v newform v reference]',
        'k h26tg[v standard v community v reference]',compare('baseline','oldform','baseline','oldform'),compare('revision','newform','revision','newform'),
        compare('baseline','oldform','revision','newform'),'u['+compare('revision','newform','baseline','oldform')+']')
    text='d r6cq['+FIELDS+'] h[a a] e[i[revision a newform a][b point['+improvement+']]].\n'
    text+='d r6cr['+' '.join(n+' i[a]' for n in FRAME)+' reference i[d]] '+ISSUE+'[o a[r[p r6cq]]['+ARGS+']].\n'
    codes=' '.join('k h223g[v '+n+']' for n in FRAME)+' k h223h[v reference]'
    text+='d r6cs['+FIELDS+'] '+ISSUE+'[k r6cr['+codes+']].\n'
    valid=['e[s[k h223g[v '+n+']]][v '+n+']' for n in FRAME]+['e[s[k h223h[v reference]]][v reference]']
    text+='d r6ct['+FIELDS+'] c['+both(*valid,'k r6cm[v ruler v people v community v baseline v oldform v reference]',
        'k h26tg[v standard v community v reference]')+'].\n'
    text+='d r6cu[person a item a '+FIELDS+' point d] c['+both('k r6ct['+ARGS+']',
        'k h26ti[k h26ag[v item v reference] r[p h26ae] v reference k r6cs['+ARGS+']]',
        'g judgment a[k r53n[v person v judgment v item v reference v point]]')+'].\n'
    pfields=' '.join(n+' a' for n in PUBLIC);pargs=' '.join('v '+n for n in PUBLIC)
    own='g faculty a['+both('k ab[v faculty v person v point]','k ac[v person v faculty v activity v point]')+']'
    text+='d r6cv['+pfields+' item a '+FIELDS+' point d] c['+both('k r6cu[v person v item '+ARGS+' v point]',
        'k r53q['+pargs+' v item v reference v point]',own)+'].\n'
    fold='q[v items]['+TRUE+'][i[ok c item a]['+both('v ok','k r6cv['+pargs+' v item '+ARGS+' v point]')+']]'
    text+='d r6cw['+pfields+' items j[a] '+FIELDS+' point d] c['+both('u[e[d[v items]][n p a b]]',fold)+'].\n'
    text+='d r6cx[items j[a] bindings j[a] reference d] e[b point['+bind(NAMES,'k r6cw['+pargs+' v items '+ARGS+' v point]')+']].\n'
    template='r b[i[items j[a]][i[bindings j[a] reference d][k r6cx[v items v bindings v reference]]]]'
    return text+'d r6cy[items i[j[a]]] '+TARGET+'[o a['+template+'][v items]].\n'
def build():
    old=parent();dep=dependency();roots=('r53n','r53q','r53m','h26ad','h26ag','h26ae','ab','ac','h223g','h223h')
    doc=deepcopy(old.document);doc.update(declarations=closure(doc,roots),statements=[]);imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for d in closure(dep.document,('r6cp','r6cm')):
        n=d['name'];e=dep.entries[n]
        if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
        else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(imported)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set(old.source_sha256)|set(dep.source_sha256)
    basis=dict(status='own_public_thoughts_on_a_legislative_improvement_issue_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
