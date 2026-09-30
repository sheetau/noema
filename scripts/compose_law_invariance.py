"""Compose law preservation across representations of the same candidate history."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_event_time import ROOT


def definitions():
    return '''
d sap[history a first a second a law a represented h[a a a] c conforms h[a a] c] c[
 w[g left a[c[v represented][v history v first v left]]][w[g right a[c[v represented][v history v second v right]]][
 f left a[f right a[y[w[c[v represented][v history v first v left]][c[v represented][v history v second v right]]][
 z[c[v conforms][v law v left]][c[v conforms][v law v right]]
 ]]]]]
].
d saq[first a second a law a selected h[a] c represented h[a a a] c conforms h[a a] c] c[
 w[g history a[c[v selected][v history]]][f history a[y[c[v selected][v history]][
 k sap[v history v first v second v law v represented v conforms]
 ]]]
].
d sar[first a second a laws h[a] c histories h[a] c represented h[a a a] c conforms h[a a] c] c[
 w[g law a[c[v laws][v law]]][f law a[y[c[v laws][v law]][k saq[v first v second v law v histories v represented v conforms]]]]
].
'''


MEANINGS={
    'sap':'同じ候補履歴の二つの表現系での記述を比較する。両方に記述が存在し、全ての対応する記述対で、同じ法則への適合の真偽が一致する。記述や数値自体の同一性は要求しない。',
    'saq':'非空の選択した候補履歴全てで、同じ法則についてsapが成立する。現実に成立した履歴や法則に適合する履歴だけへ選択範囲を狭めない。',
    'sar':'非空の選択した法則全てについてsaqが成立する。法則ごと・履歴ごとの表現保存を同時に要求する。'}


def generic_composed():
    doc=parse('n:\n'+definitions())
    basis={'version':'law-invariance-basis-v1','document':'examples/v014/law-invariance.noema',
        'primitives':[],'definitions':dict(MEANINGS),'unresolved':[
            '表現される履歴と記述、法則への適合は引数で与える。異なる記述が同じ履歴を表すという関係の根拠は別に必要。',
            '適合しない候補も対象とする条件だが、選択範囲が全候補を尽くすことは定義だけでは保証しない。',
            '有限の候補で一致しても一般法則の同一性は証明されない。意味規約で適合関係と対象領域を明示する必要がある。',
            '同じ法則の許容条件が対応する表現で一致するという外延的な条件である。法則の説明力・原因機構や式の字面の同一性は表さない。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    previous=parse((ROOT/'examples/v014/einstein-roundtrip-speed.noema').read_text(encoding='utf-8'))
    statements,previous['statements']=previous['statements'],[]
    doc=parse(format_graph(previous,'compact')+definitions()+'''
r va[a] c.r vb[a a d] c.r vc[a a d] c.
r vd[a d] c.r ve[a d] c.r vf[a a d] c.r vg[a] c.
r vh[a a a d] c.r vi[a a d] c.r vj[a a d] c.
r vk[] a.r vl[a a i[e] a d] c.
d sat[first a second a context d] c[
 w[k va[v first]][w[k va[v second]][w[u[e[v first][v second]]][w[k vb[v first v second v context]][k vc[v first v second v context]]]]]
].
d sau[history a context d] c[g system a[w[k vg[v system]][k vf[v history v system v context]]]].
d sav[first a second a context d] c[
 w[k vj[v first v second v context]][w[f history a[y[k ve[v history v context]][k sau[v history v context]]]][
 k sar[v first v second i[law a][k vd[v law v context]] i[history a][k ve[v history v context]]
 i[history a frame a representation a][k vh[v history v frame v representation v context]]
 i[law a representation a][k vi[v law v representation v context]]]
 ]]
].
d saw[] e[b context[
 w[g first a[g second a[k sat[v first v second v context]]]][
 f first a[f second a[y[k sat[v first v second v context]][k sav[v first v second v context]]]]]
]].
''')
    doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'\ns[k vl[k vk[] k rd[] r[k saw[]] k rh[] k ri[]]].\n')
    basis=deepcopy(json.loads((ROOT/'data/einstein-roundtrip-speed-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-law-invariance-basis-v1',document='examples/v014/einstein-law-invariance.noema')
    basis['definitions'].update(MEANINGS)
    meanings=[
        ('va',['frame'],'物理的な状態変化を参照する座標系。座標の構成と測定は未説明。'),
        ('vb',['first_frame','second_frame','context'],'二座標系の軸の相対的な向きが指定文脈で変化しない。原点の運動と分け、軸が一致することまでは要求しない。'),
        ('vc',['first_frame','second_frame','context'],'二座標系の原点間の相対位置が時間に対して一定速度ベクトルで変化する。加速度を持つ運動とは区別する。ゼロ速度も退化例として許す解釈。軌道・時間・速度からの構成説明は未完。'),
        ('vd',['law','context'],'状態変化を支配する法則の評価範囲に含まれる法則。各法則が真であることや、各候補が適合することは含意しない。'),
        ('ve',['history','context'],'法則の許容・不許容を比較する候補の状態変化履歴。現実に成立した履歴だけや、法則に適合する履歴だけを対象にしない。'),
        ('vf',['history','system','context'],'候補履歴が指定した物理系の状態変化を記述するという対応。実際にその変化が起きたことは含意しない。'),
        ('vg',['system'],'物理的な系として扱う対象。状態変数・物体との構成説明は未完。'),
        ('vh',['history','frame','representation','context'],'同じ候補履歴に、指定座標系に関する状態変化の記述を対応させる。異なる座標系で異なる数値や記述を許す。全記述の対応範囲はvjに明示する。'),
        ('vi',['law','representation','context'],'その状態変化の記述が指定法則の許容条件を満たす。座標系ごとに別の法則を選ぶ関係ではなく、同じ法則を対応する記述に適用する。許容条件の内容は各法則に別途必要。'),
        ('vj',['first_frame','second_frame','context'],'この比較でvdの法則範囲、veの候補範囲、vhの対応する記述が必要な範囲を尽くすという前提。有限の標本から認定しない。'),
        ('vk',[],'相対性原理の内容を提示する本文箇所。'),
        ('vl',['node','author','principle','scope','context'],'著者がその箇所で指定内容を原理の定義として提示する。内容の真理や、その後の推論が成立することは含意しない。')]
    declarations={d['name']:d for d in doc['declarations']}
    for name,args,meaning in meanings:
        d=declarations[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'sat':'異なる二座標系で、軸の相対回転がなく、原点の相対速度が一定という比較対象の条件。座標値の同一性や共通原点を要求しない。',
        'sau':'候補履歴が物理系の状態変化の履歴として結び付いている。',
        'sav':'対象範囲が完全と指定され、全ての選択候補が物理系に対応した上で、二座標系の間でsarの法則適合条件が保存される。無効な選択候補だけを除外して成立させない。',
        'saw':'比較対象の座標系対が存在し、その全対でsavが成立するという原理の内容。有限の観測履歴の一致だけを述べるものとは区別する。'})
    basis['unresolved']+=generic_composed()[1]['unresolved']+[
        'u0025を許容される状態変化の保存として記述する解釈草案。法則の一般性や同一性の全意味を確定したものではない。',
        '等速並進の二つの条件、物理系・状態変化・座標記述の基礎定義、各法則の内容は未完。',
        'u0024の二原理を後続議論の根拠として採用する談話、第二原理の光源運動からの独立性、u0022の時間の命名は別途必要。',
        '個別のガリレイ変換やローレンツ変換を原理の定義に固定しない。原刊画像との照合と全文の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/law-invariance-basis-v1.json'),(source_composed,'data/einstein-law-invariance-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored law invariance differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Law invariance and source principle definition composed')


if __name__=='__main__':main()
