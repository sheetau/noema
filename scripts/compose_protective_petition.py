"""Bind selected congregations and their arrangements to a shared policy petition."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_observed_protection import THREAT_OBSERVED_LINK,OBSERVED_LINK

PARENTS=('data/legislative-touchstone-basis-v1.json','data/personal-insight-grounds-basis-v1.json','data/congregational-choices-basis-v1.json','data/joint-petition-basis-v1.json')
LIBRARY='examples/v016/protective-petition.noema'
BASIS='data/protective-petition-basis-v1.json'
MODEL_NAMES=('policy','community','congregation','field','subject','configuration')
MODEL_FIELDS=' '.join(n+' a' for n in MODEL_NAMES)+' reference d candidate d anchor d'
MODEL_ARGS=' '.join('v '+n for n in MODEL_NAMES)+' v reference v candidate v anchor'
LABELS=[*MODEL_NAMES,'reference','candidate','anchor']
PREFIX='[a a a a a a d d d] '
STATE='h[a] c'
CONTEXT='reference d candidate d anchor d'
CONTEXT_ARGS='v reference v candidate v anchor'
PRIMITIVES={
 'h26ds':('[a a d d d] c',['policy','community','reference','candidate','point'],'この同じ公的措置が、同じ政治的共同体の指定候補経過のこの状況で実施・運用されている。宗教共同体の扱いを変える政策を指示できるが、この関係だけでは保護効果・非妨害・正当性・全対象への効果を含意しない。提案・検討・名称だけと区別し、同じ政策の同一性を比較間で保つ。'),
 'h26dt':(PREFIX+'j[a]',LABELS,'この同じ政策・政治的共同体・宗教共同体・領域・主題・制度配置と固定文脈に対する因果比較モデルの全変数列。政策要因・脅威要因・運用目標に関わる背景を明示したモデルの範囲であり、成功に都合のよい変数だけへ途中で絞らない。重複・要因包含・解の存在は合成側で検査する。'),
 'h26du':(PREFIX+'h[a h[a] c] c',LABELS,'同じ対象組と固定文脈のモデルにおいて、各変数の値を全状態割当てから定める構造方程式。政策や脅威の介入を行う間も同じ方程式・背景を保ち、政策有無の結果そのものを別のモデルから借りない。現実の機構への適合は明示解釈の責任であり、介入解と同じ状況の観測整合性は別に検査する。'),
 'h26dv':(PREFIX+'a',LABELS,'同じ対象組とモデルの中で、この政策が実施されることの真偽を表す要因変数。政治的共同体・宗教共同体・制度配置を取り替えず、介入を通じて同じ要因を使う。モデルへの包含、実際の政策内容との真偽一致は別に結ぶ。'),
 'h26dw':(PREFIX+'a',LABELS,'同じモデルで、選んだ同じ制度配置の運用を失わせるおそれのある事態の真偽を表す脅威要因。政策要因とは別に介入できるものを指定する。脅威の現実の生起を要求せず、要因の区別・包含、具体的な内容との対応は合成側で検査する。'),
 'h26dx':(PREFIX+'h[h[a] c] c',LABELS,'同じモデルの全状態割当てに対して、指定の宗教共同体・領域・主題・制度配置の運用という活動目標が成立する条件。無関係な活動や単なる政策実施へ置き換えない。実際のr5f2の同じ五対象列の内容との真偽一致は、比較状況と観測状況でそれぞれ検査する。'),
 'h26dy':(PREFIX+'h[h[a] c] d',LABELS,'同じ因果比較の状態割当てに対応する反事実的な評価状況。政策内容・脅威内容・同じ制度運用の内容をこの状況で評価し、モデル内の要因・目標との一致を検査する。現実の観測状況と同一とは限らず、別共同体の整合する状況へ写して代用しない。'),
 'h26dz':(PREFIX+'e',LABELS,'同じ対象組・モデル・固定文脈について、指定した脅威が成立することのNoema内容。政策や活動内容そのものとは区別し、自然言語ラベルで内容を代用しない。脅威の実際の生起を要求せず、モデルの脅威要因との一致は別に検査する。'),
 'h26d2':(PREFIX+'h[d] h[a] c',LABELS,'同じ対象組・固定文脈の各評価状況に対する、同じモデルの全変数の観測割当て。別共同体・配置・時点の整合する記録へ交換せず、未知を偽で埋めない。元の方程式の解であること、政策・運用・脅威の内容との一致を合成側で検査する。'),
}
MEANINGS={
 'r5gf':'同じ公的政策・政治的共同体・固定基準・候補経過について、その政策が評価点に実施されるh26dsの内容。保護・非妨害を定義する効果条件や実際の共同提案から切り離して引用できる。',
 'r5gg':'同じ政策と六対象・固定文脈の因果モデルをrk3へ渡し、政策実施、選んだ脅威への保護効果、同じ五対象列のr5f2の制度運用との対応、同点の観測整合性を要求する。現在の脅威発生を要求しない予防的な保護を含み、別の制度や共同体の効果で代用しない。',
 'r5gh':'r5ggと同じ対象組・政策・運用内容をrk4の非妨害比較へ渡す。政策なしで可能な同じ運用を政策ありで失わせず、両側の非空解・内容対応・同点の観測整合性を要求する。もともと運用できない場合には、非妨害から運用の成功を導かない。',
 'r5gi':'同じ基準点でr5geの本人の認識に基づく改革合意を満たす全共同体・新配置にr5gg、r5f7の維持意向を持つ全共同体・旧配置にr5ghを、同じ政策と評価点で要求する。全該当例を量化し、結果点で保護に成功した対象へ選び直さない。二対象群は独立し、改革側でないだけで維持側にしない。',
 'r5gj':'政策・政治的共同体の正確な二対象列と同じ固定基準・候補経過・選択点から、r5giの保護と非妨害を併せ持つ政策内容を返す。共同提案の対象として段階1で引用して渡せる。',
 'r5gk':'同じ市民の提案集団・政治的共同体・君主の宛先・政策・固定文脈について、r5gjの同じ二対象と保護・非妨害内容をr5fyの共同提出可能性へ渡す。提出する声・方法・宛先は既存構成を保ち、提案するだけで政策実施や保護・非妨害の成功を評価しない。',
}
LIMITS=[
 '第七文のum diejenigen Gemeinden in Schutz zu nehmenとohne doch diejenigen zu hindernへ、理由付き改革合意r5geと維持意向r5f7を同じ基準点で接続する。全当事者の認識判断と同意、旧配置を望む肯定的な意向はそのまま保持し、成功例だけを対象にしない。',
 '保護は既存rk3の強い因果比較の読みを採る。政策なし・脅威なしなら運用でき、政策なし・脅威ありなら運用できず、政策ありなら脅威の有無のどちらでも運用できることを非空な全解で要求する。現に脅威が発生したという条件は加えない。保護の全語義・全現実脅威の網羅を主張しない。',
 '非妨害は既存rk4の、同じ政策が可能な運用を失わせない強い比較である。政策の有無の双方に解を要求し、もともと運用できないことを政策のせいにしない。非妨害から実際の運用や望んだ全期間の成功を推論しない。',
 '効果比較の活動はr5f2の同じ制度配置の運用内容である。維持したい対象は同じ五対象列を使うr5f6の継続内容のまま保つが、反事実的なモデル状況を固定された現実履歴の後続点と同一視しない。ここで評価するのは指定状況における同じ運用の保護又は非妨害であり、全未来にわたる成功保証を追加しない。',
 'モデルの変数・方程式・要因・目標・状況対応・脅威内容・観測を、政策と全対象の同じ束縛・基準点で固定する。比較点での内容対応と実際の観測整合性をともに検査するが、モデルの現実適合や未知の危険まで有限試験で証明しない。',
 '改革側・維持側の対象が空の場合も、全称条件だけから現実の共同体を作り出さない。両側へ該当する対象には両条件を要求する。政策自体の実施内容は両群の非空性に依存しない。提案の引用はその実施を実行しない。',
 'r5gkは保護・非妨害を内容とする同じ共同提案への接続。公的洞察がこの提案可能性に足りるso weit、umの目的の文章上の帰属、同じ期間の到達内容、聖職者への取り立て、etwa・譲歩・換喩・可能性・全文帰属は残る。全文確認文字数は増やさない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    text='d r5gf[policy a community a reference d candidate d] e[b point[k h26ds[v policy v community v reference v candidate v point]]].\n'
    providers={n:'k '+sym+'['+MODEL_ARGS+']' for n,sym in (
        ('variables','h26dt'),('equations','h26du'),('factor','h26dv'),('threatfactor','h26dw'),
        ('goal','h26dx'),('worlds','h26dy'),('threat','h26dz'),('records','h26d2'))}
    providers['policy']='k r5gf[v policy v community v reference v candidate]'
    providers['activity']='k r5f2[l[a][v community v congregation v field v subject v configuration] '+CONTEXT_ARGS+']'
    for name,prior,fields in (('r5gg','rk3',THREAT_OBSERVED_LINK),('r5gh','rk4',OBSERVED_LINK)):
        text+='d '+name+'['+MODEL_FIELDS+'] e[k '+prior+'['+' '.join(providers[n] for n,_ in fields)+']].\n'
    obligations=[]
    choices='v agreement v community v congregation v field v subject v older v newer '+CONTEXT_ARGS
    retained='v community v congregation v field v subject v older '+CONTEXT_ARGS
    for selected,configuration,name,variables in (
        ('k r5ge['+choices+']','newer','r5gg',('congregation','field','subject','older','newer','agreement')),
        ('k r5f7['+retained+']','older','r5gh',('congregation','field','subject','older'))):
        consequence='t[k '+name+'[v policy v community v congregation v field v subject v '+configuration+' '+CONTEXT_ARGS+']][v point]'
        part='y['+selected+']['+consequence+']'
        for n in reversed(variables):part='f '+n+' a['+part+']'
        obligations.append(part)
    text+='d r5gi[policy a community a '+CONTEXT+'] e[b point['+both(
        't[k r5gf[v policy v community v reference v candidate]][v point]',*obligations)+']].\n'
    text+='d r5gj[bindings j[a] '+CONTEXT+'] e[b point['+bind(('policy','community'),
        't[k r5gi[v policy v community '+CONTEXT_ARGS+']][v point]')+']].\n'
    text+='d r5gk[group a community a recipient a policy a '+CONTEXT+'] c[k r5fy[v group v community v recipient r b[p r5gj] l[a][v policy v community] '+CONTEXT_ARGS+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['rk3','rk4'],['r5ge'],['r5f2','r5f7'],['r5fy'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='same_policy_protection_nonhindrance_and_joint_petition',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
