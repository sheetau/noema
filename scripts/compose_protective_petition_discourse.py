"""Connect protective purpose, hypothetical recipients and throne metonymy."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_civic_participation_discourse import FAMILY,CONTEXT,CONTEXT_ARGS,PETITION

PARENTS=('data/legislative-touchstone-basis-v1.json','data/civic-participation-discourse-basis-v1.json','data/protective-petition-basis-v1.json')
LIBRARY='examples/v016/protective-petition-discourse.noema'
BASIS='data/protective-petition-discourse-basis-v1.json'
CASES=(*PETITION,'congregation','field','subject','older','newer','agreement')
PRIMITIVES={
 'h26ea':('[a a a d] c',['seat','holder','community','point'],
   'この物は、指定された同じ共同体の指定された統治者の公的な威厳・権威を表す座として制度・慣行上位置付けられた物理的な座席である。任意の私用の椅子や執務机だけとは区別する。素材・装飾・所在・その時の着座・提出者の身体的位置は指定せず、統治者の職務・権限・正当性は別に構成する。換喩の描写側に使っても、その物の現実の存在を追加しない。'),
 'h26eb':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d] c',
   ['node','author','whole','scope','referent','associated_description','context'],
   '著者が同じ全体内容の指定箇所で、指定範囲の同じ対象を、それと制度・慣行上結び付くものの記述によって換喩的に指す。三つの閉じた内容族へ同じ対象列・基準・候補・基準点を渡し、その同じ評価点の対象関係を保つ。対象と関連物の物理的同一性、関連物の現実の存在、関連物に対する文字どおりの行為を主張しない。'),
 'h26ec':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d] c',
   ['node','author','whole','scope','activity','purpose','context'],
   '著者が同じ全体内容・範囲の中で、指定した行為内容を、指定した目標内容の実現に向けて行うものとして提示する。三つの閉じた内容族へ同じ対象列・基準・候補・基準点を渡し、行為と目的の対象を取り替えない。現実の行為・達成・目的の正当性・唯一の動機を追加せず、外側の仮定や可能性の範囲を保つ。偶然目標と合う結果が出るだけの場合と区別する。'),
 'h26ed':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' '+FAMILY+' d] c',
   ['node','author','whole','scope','combined','principal','reservation','context'],
   '著者が同じ全体内容・範囲で、主たる目的を撤回せず、同じ政策が併せて守るべき留保を対照的に続けて提示する。四つの閉じた内容族へ同じ対象列・基準・候補・基準点を渡し、複合内容の中に主内容と留保を保持する。論理的矛盾、主目的の否定、留保の対象の実在や政策の実施・成功を提示だけから追加しない。'),
 'h26ee':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d] c',
   ['node','author','whole','scope','selection','consequence','context'],
   '著者が同じ全体内容・範囲で、指定の選択条件を満たすことになるかもしれない対象を仮定的に取り上げ、その場合の同じ帰結内容へ結ぶ。三つの閉じた内容族へ同じ対象列・基準・候補・基準点を渡す。選択条件は既知の現実の成立例だけへ縮めず、該当例の実在、数値確率、選択条件が全対象に成立することや帰結の現実の達成を追加しない。'),
}
MEANINGS={
 'r5he':'同じ提案集団・政治的共同体・宛先・政策の正確な四対象列から、同じr5gjの保護・非妨害を内容とするr5fxの共同提出を返す。基準点で固定した全当事者、同じ声・提案・公的な宛先と実行点を保持する。提案内容は引用したままで政策の実施を要求しない。',
 'r5hf':'同じ四対象列の政策と共同体に、同じ基準・候補・選択点のr5giの複合政策内容を対応させる。全該当改革共同体への保護と、維持意向を持つ全該当共同体への非妨害を併せ、同じ評価点に政策実施を要求する。',
 'r5hg':'同じ四対象列の政策実施と、同じ選択点でr5geを満たす全共同体・新配置へのr5ggの保護を要求する目的内容。対象を結果点の成功例へ選び直さず、該当共同体が空でも政策実施の内容は残る。非妨害は別の留保内容に分ける。',
 'r5hh':'同じ四対象列の政策実施と、同じ選択点でr5f7の維持意向を持つ全共同体・旧配置へのr5ghの非妨害を要求する留保内容。改革に合意しなかったという否定だけで対象を選ばず、肯定的な維持意向を保持する。',
 'r5hi':'同じ四対象列の宛先が、その同じ共同体・評価点のr2ujの君主的な公的統治者であるという指示対象の性質。提出行為における宛先と同じ変数を使い、特定の君主名や椅子の存在を追加しない。',
 'r5hj':'同じ四対象列の宛先にr2ujの統治者性があり、その同じ宛先・共同体・評価点に結び付くh26eaの物理的な座席があるという字義的な描写。換喩の描写側として引用し、共同提出や提案可能性の成立条件へは加えない。',
 'r5hk':'提案の四対象に宗教共同体・領域・主題・旧配置・新配置・合意を続けた正確な十対象列から、同じ基準点のr5geの本人の認識に従う改革合意を返す。対象存在の断言ではなく、提案内容の条件付き対象を指定する。',
 'r5hl':'同じ十対象列の共同体・宗教共同体・領域・主題・旧配置に、同じ基準点のr5f7の維持意向を対応させる。新配置・合意へ依存させず、改革側とは独立に対象を取る。',
 'r5hm':'同じ十対象列の政策・共同体・宗教共同体・領域・主題・新配置と固定された選択点に、評価点でのr5ggの保護を対応させる。別政策・旧配置・別時点の保護へ交換しない。',
 'r5hn':'同じ十対象列の政策・共同体・宗教共同体・領域・主題・旧配置と固定された選択点に、評価点でのr5ghの非妨害を対応させる。新配置の保護や無関係な共同体の無害さで代用しない。',
 'r5ho':'同じ十対象列の宗教共同体・政治的共同体・領域・主題がr5fzの枠組みに属し、同じ候補履歴に選択点が属する範囲。改革合意や維持意向、保護・非妨害の成功で候補を選別しない。',
 'r5hp':'同じ著者・全体内容・文脈へ、同じ宛先の王座による換喩、同じ共同提出の保護目的、仮定的な改革合意による対象選択、同じ政策での非妨害の留保を接続する。提示箇所の順序と区別を保持し、引用した政策・合意・椅子・実行の現実の成立を要求しない。',
}
LIMITS=[
 'u0013第七文後半のvor den Thron、um ... in Schutz zu nehmen、die sich etwa ... geeinigt hätten、ohne doch ...の提示を接続する依存群。原文の構文を、同じ共同提案の保護目的、その仮定的な対象、同じ政策への非妨害の留保として読む。全文の著者帰属はまだ加えない。',
 'Thronは同じ政治的共同体の公的な君主的統治者への提出先を指す換喩という既存読解を保つ。物理的な座席の描写も別に残すが、現実の椅子・着座・身体的な対面・椅子の前の場所を必須条件にしない。AdelungのStuhl項にある座と王の威厳・統治者側との転義は補助根拠であり、カントの唯一の語義の証明ではない。',
 '保護の目的は、同じ集団が同じ政策を公的な検討へ出すという行為の目標として提示する。既存r5fxの各人による同じ政策の採用を求める声を保持し、目的があることから提案の現実の実行や政策の成功を導かない。文章の目的関係を、因果比較モデルの成功だけで置き換えない。',
 '改革対象は同じ選択点で本人たちの認識に従って新配置へ合意するr5geで指定する。etwaと接続法を仮定上の該当対象という提示として読み、現実の共同体が既に改革したこと、特定教派、数値確率や全員の改革を追加しない。条件付き全称の対象が空であることは許す。',
 '保護と非妨害は同じ政策・評価点に結ぶ二つの要件である。旧配置を維持したいr5f7の肯定的意向を保ち、改革側の補集合にしない。両条件に該当する対象には両方を要求する。r5hgとr5hhの連言が既存r5giと同じ複合内容になることを検査する。',
 '十対象の選択・効果の内容族は、共同提案の四対象に同じ順序で六対象を続ける。基準・候補・選択点は状況型のまま保ち、効果だけを後の評価点で評価する。選択を結果点でやり直さず、政策や共同体の異なる事例を混ぜない。',
 '新しい提示関係は閉じた内容族を引数に取る汎用関係であり、原文一文の真偽を返す語ではない。内部の共同提出・選択・保護・非妨害は既存定義を使う。換喩の物理的な描写を含め、引用した内容を実行しない。',
 '全文の量化、Nun・wohl・gleichsamと期待描写、前文との照応、同じ全文内容と箇所への実適用、著者帰属と通読は残る。第七文の確認文字数は加算しない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    text=''
    def family(root,names,body):return 'd '+root+'[bindings j[a] '+CONTEXT+'] e[b point['+bind(names,body)+']].\n'
    text+=family('r5he',PETITION,'k r5fx[v group v community v recipient r b[p r5gj] l[a][v policy v community] '+CONTEXT_ARGS+' v point]')
    text+=family('r5hf',PETITION,'t[k r5gi[v policy v community '+CONTEXT_ARGS+']][v point]')
    reform='k r5ge[v agreement v community v congregation v field v subject v older v newer '+CONTEXT_ARGS+']'
    retention='k r5f7[v community v congregation v field v subject v older '+CONTEXT_ARGS+']'
    protect='t[k r5gg[v policy v community v congregation v field v subject v newer '+CONTEXT_ARGS+']][v point]'
    retain='t[k r5gh[v policy v community v congregation v field v subject v older '+CONTEXT_ARGS+']][v point]'
    for root,selected,effect,names in (
        ('r5hg',reform,protect,('congregation','field','subject','older','newer','agreement')),
        ('r5hh',retention,retain,('congregation','field','subject','older'))):
        body='y['+selected+']['+effect+']'
        for n in reversed(names):body='f '+n+' a['+body+']'
        text+=family(root,PETITION,both('t[k r5gf[v policy v community v reference v candidate]][v point]',body))
    monarch='k r2uj[v recipient v community v point]'
    text+=family('r5hi',PETITION,monarch)
    text+=family('r5hj',PETITION,both(monarch,'g seat a[k h26ea[v seat v recipient v community v point]]'))
    frame=both('k r5fz[v community v congregation v field v subject v reference]','k h257z[v reference v candidate v anchor]')
    for root,body in (('r5hk',reform),('r5hl',retention),('r5hm',protect),('r5hn',retain),('r5ho',frame)):
        text+=family(root,CASES,body)
    q=lambda n:'r b[p '+n+']'
    clauses=[
        'k h26eb[v thronenode v author v whole '+q('r5g6')+' '+q('r5hi')+' '+q('r5hj')+' v context]',
        'k h26ec[v purposenode v author v whole '+q('r5g6')+' '+q('r5he')+' '+q('r5hg')+' v context]',
        'k h26ed[v reservationnode v author v whole '+q('r5g6')+' '+q('r5hf')+' '+q('r5hg')+' '+q('r5hh')+' v context]',
        'k h26ee[v selectionnode v author v whole '+q('r5ho')+' '+q('r5hk')+' '+q('r5hm')+' v context]']
    nodes=('thronenode','purposenode','selectionnode','reservationnode')
    clauses+=['k ue[v '+a+' v '+b+' v context]' for a,b in zip(nodes,nodes[1:])]
    clauses+=['u[e[v '+a+'][v '+b+']]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    text+='d r5hp['+' '.join(n+' a' for n in nodes)+' author a whole i d[e] context d] c['+both(*clauses)+'].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['ue'],['r5g6'],['r5fx','r5gj','r5gi','r5ge','r5f7','r5gg','r5gh','r5fz','h257z','r2uj'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='protective_petition_purpose_selection_reservation_and_metonymy',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
