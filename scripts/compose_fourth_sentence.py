"""Adopt the fourth sentence with an explicit free-kind and nonliteral correspondence."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-limited-consequence.noema'
PARENT_BASIS = 'data/limited-consequence-basis-v1.json'
FULL = 'examples/v016/kant-fourth-sentence.noema'
CORE = 'examples/v016/fourth-sentence-core.noema'
LIBRARY = 'examples/v016/referenced-activity-kind.noema'
BASIS = 'data/fourth-sentence-basis-v1.json'
ANNOTATIONS = 'data/fourth-sentence-identifiers-v1.json'
MAPPINGS = [('h3a','r2gt','h3n'), ('h3a','r2ie','r2iu'), ('h3s','r2hf','r2ir'),
            ('h3s','r2hh','r2is'), ('h3s','r2if','r2iw'), ('h3s','r2ii','r2ix')]
MEANINGS = {
    'r2io': '活動と状況の参照対が非空で、全ての参照対が参照元の条件と同じ固定した種類条件を満たす。参照ごとに種類を取り替えず、未確認・不適格な参照を種類の根拠にしない。',
    'r2ip': 'r2ioで参照を検査した同じ種類条件を、指定した活動と状況が満たす。活動の同一性や参照元だけが持つ別の性質までは候補へ要求しない。',
    'r2iq': '同じ本人・提示文脈のh3uで選んだ参照元は非空で、全て同じ描写仮定内に生起する、固定した最小の溝への不確かな跳躍であり、足側の物理的阻害がない自己の身体移動h3zでもある。ここで共有する種類は具体的なh3zに固定する。',
    'r2ir': '同じ本人のr2iqの参照が有効で、その時点にh3zの自由な身体移動があるという、引用できる活動種類の内容。別の移動や時点も許し、溝の同一性・最小幅・跳躍だけであること・不確かさを種類の共通条件にしない。',
    'r2is': '種類の参照r2iqと同じ描写履歴が有効で、その履歴に属する現在にr2irへの経験由来の慣れが成立しない。参照の欠落や不正な履歴を不慣れと判定しない。経験・寄与・定着には同じ閉じたr2irの記述を渡す。',
    'r2it': '同じ本人・溝・活動・時点で、実行された自由な跳躍が不確かであることを焦点とし、その同じ自由な跳躍が不確かでないという代替をr2iaで排除する。別の跳躍や移動の安定性を否定しない。',
    'r2iu': '提示文脈で固定した同じ溝について、r2itの限定された不確かな自由な跳躍が少なくとも一つあるという内容。最小性をこの活動記述へ混ぜない。',
    'r2iv': '同じ本人・提示文脈の固定した溝が、同じ描写状況でh3cの最小幅条件を満たす。知的課題の困難度ではなく、従来の幅の比較を保持する。',
    'r2iw': '同じ描写状況で最小幅r2iv、不慣れr2is、限定された跳躍r2iuが成立し、同じ二記述r2isとr2iuを結ぶhzieの因果的寄与がある。従来h4cの原因説明への採用eaから寄与を推論せず、この読みに必要な原因を明示する。',
    'r2ix': '同じ本人・提示文脈の非空な描写仮定集合で、足枷の除去h3nならr2iwの理由付き帰結となり、除去を満たす仮定もあるという内容。現実の足枷・除去・跳躍を断言しない。',
    'r2iy': '同じ先行箇所・著者・人物範囲・両側の指示対応r2giを保持し、離脱、限定された活動、自由な活動の種類、不慣れ、最小性と理由付き帰結、条件前景の六組を既存qhで対応づける。各組は同じ本人を引数に取る閉じた記述であり、物理的同一性や両内容の論理的同値を要求しない。対応だけではどちらの内容も実行しない。',
}
LIMITS = [
    '第三段落第四文を、先行文と同じ人物範囲における、規定・定型表現への無吟味な依存からの離脱を仮定する文として読む。実際に全員が離脱したこと、離脱すれば能力を獲得することは補わない。',
    '身体描写を保持して対象側と対応づけ、幅を困難度へ、身体移動を判断へ物理的に同一化しない。意味対応はqhの規約に従う明示した読解であり、条件前景の論理的同値や現実世界の真理の自動証明ではない。',
    '種類照応は自由な自己の活動という共有面を採る。描写側では足側の物理的阻害がない自己の身体移動h3z、対象側では他者の指導なしに自分の理解力を使う判断r2heへ対応させる。溝や課題の同一性、不確かさを経験種類へ一般化せず、原文の唯一の語義解釈とはしない。',
    '身体側の原因もhzieによる寄与として明示し、旧h4cのeaによる説明採用を原因の実在の代用にしない。原文の理由を仮定内へ置く読みであり、現実の全時点への投射、唯一・十分・必要な原因は追加しない。',
    '最小課題への尺度期待と、離脱を認めた通常予想への譲歩は、対象側のr2ilにまとめて帰属する。描写の前景の対応から期待値を計算したり、身体側へ別の期待入力を捏造したりしない。既存の全比較・通常候補という操作化の限界は継承する。',
    '限定は同じ活動の確実性との対照であり、全判断の不能や全活動の不確かさへ広げない。対象側の離脱過程は複合過程を許し、描写側は各対象の除去過程を許す。原文が内部の作業手順や過程の個数を定めているとはしない。',
    '参照元・比較範囲・履歴・因果・対応の値は意味上の解釈入力。未知を偽で埋めず、有限検査を現実の全対象についての確認や独立査読とはしない。本文13番と53番の二つの旧帰属だけを更新し、他の52文と既存の全宣言・意味規約を保持する。',
    '第四文の通し判断はアシスタントによる明示した読みの下の判断である。第五文、段落全体、二作品全文の意味確認は引き続き必要。自然言語の自動翻訳器の実装や評価ではない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def additions():
    refs='i[activity a scene d][k h3u[v person k wh[] v activity v scene]]'
    valid='i[activity a scene d][w[k h2t[v person k wh[] v scene]][w[k h3c[v person k wh[] v scene k h3d[v person k wh[]]]][w[k dg[v activity v scene]][w[k h2u[v person k h3d[v person k wh[]] v activity v scene]][k h2v[v activity v scene]]]]]]'
    kind='i[activity a scene d][k h3z[v person v activity v scene]]'
    text='''
d r2io[references h[a d] c valid h[a d] c kind h[a d] c] c[
 w[g activity a[g scene d[c[v references][v activity v scene]]]][
 f activity a[f scene d[y[c[v references][v activity v scene]][w[c[v valid][v activity v scene]][c[v kind][v activity v scene]]]]]]].
d r2ip[activity a scene d references h[a d] c valid h[a d] c kind h[a d] c] c[w[k r2io[v references v valid v kind]][c[v kind][v activity v scene]]].
'''
    text+='d r2iq[person a] c[k r2io['+refs+' '+valid+' '+kind+']].\n'
    text+='d r2ir[person a] e[b point[g activity a[k r2ip[v activity v point '+refs+' '+valid+' '+kind+']]]].\n'
    text+='''
d r2is[person a] e[b point[w[k r2iq[v person]][k rci[v person r[p r2ir] v point
 i[past d][k h2r[v person v point v past]] i[first d last d][k ic[v first v last v point]] p h3e p h3g p h3f]]]].
d r2it[person a ditch a activity a point d] c[k r2ia[v activity v point
 i[act a scene d][w[k dg[v act v scene]][w[k h2u[v person v ditch v act v scene]][w[k h3z[v person v act v scene]][k h2v[v act v scene]]]]]
 l[h[a d] c][i[act a scene d][w[k dg[v act v scene]][w[k h2u[v person v ditch v act v scene]][w[k h3z[v person v act v scene]][u[k h2v[v act v scene]]]]]]]
 ]].
d r2iu[person a] e[b point[g activity a[k r2it[v person k h3d[v person k wh[]] v activity v point]]]].
d r2iv[person a point d] c[k h3c[v person k wh[] v point k h3d[v person k wh[]]]].
d r2iw[person a] e[b point[w[k r2iv[v person v point]][w[t[k r2is[v person]][v point]][w[t[k r2iu[v person]][v point]][k hzie[v person r[p r2is] v person r[p r2iu] v point]]]]]].
d r2ix[person a] e[b anchor[w[e[v anchor][k wh[]]][w[
 k rc[v person p h3n p r2iw i[scene d][k h2t[v person v anchor v scene]]]
 ][k re[v person p h3n i[scene d][k h2t[v person v anchor v scene]]]]]]].
'''
    clauses=['k r2gi[]']+['k qh[k '+node+'[] k wa[] r[p '+target+'] r[p '+depiction+'] k wh[]]' for node,target,depiction in MAPPINGS]
    body=clauses[-1]
    for clause in reversed(clauses[:-1]):body='w['+clause+']['+body+']'
    return text+'d r2iy[] c['+body+'].\n'


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[]
    assert not set(MEANINGS)&set(old.entries)
    doc=parse(format_graph(doc,'compact')+additions())
    assert len(statements)==54 and [statements[i]['body']['symbol'] for i in (13,53)]==['r2gk','r2gj']
    for index,name in ((13,'r2in'),(53,'r2iy')):statements[index]=dict(kind='assert',body=dict(kind='call',symbol=name,arguments=[]))
    doc['statements']=statements
    core=deepcopy(doc);core.update(declarations=closure(doc,['r2in','r2iy']),statements=[statements[i] for i in (13,53)])
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['r2io','r2ip','qh']),statements=[])
    added=doc['declarations'][len(old.document['declarations']):];assert len(added)==11
    basis=dict(status='fourth_sentence_adopted_with_explicit_nonliteral_correspondence',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,definitions=MEANINGS,primitives={},
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/limited-consequence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    encoded=lambda value:json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:encoded(basis),ANNOTATIONS:encoded(annotations)}


if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    print('Fourth sentence adopted with fixed activity kind and six nonliteral correspondences',flush=True)
