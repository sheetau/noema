"""Keep one parallel history across all times and attribute its symmetry rationale."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both


def definitions():
    return '''
d sfo[history a moments h[a] c states h[a a a] c same h[a a] c] c[
 w[g moment a[c[v moments][v moment]]][f moment a[y[c[v moments][v moment]][
 w[g state a[c[v states][v history v moment v state]]][
 f first a[f second a[y[w[c[v states][v history v moment v first]][c[v states][v history v moment v second]]][c[v same][v first v second]]]]]
 ]]]
].
d sfp[history a moments h[a] c states h[a a a] c same h[a a] c property h[a a] c] c[
 w[k sfo[v history v moments v states v same]][f moment a[f state a[
 y[w[c[v moments][v moment]][c[v states][v history v moment v state]]][c[v property][v moment v state]]
 ]]]
].
d sfq[moments h[a] c histories h[a] c states h[a a a] c same h[a a] c property h[a a] c] c[
 g history a[w[c[v histories][v history]][k sfp[v history v moments v states v same v property]]]
].
d sfr[moments h[a] c histories h[a] c states h[a a a] c same h[a a] c property h[a a] c] c[
 w[g moment a[c[v moments][v moment]]][f moment a[y[c[v moments][v moment]][
 g history a[w[c[v histories][v history]][w[k sfo[v history v moments v states v same]][
 g state a[w[c[v states][v history v moment v state]][c[v property][v moment v state]]]
 ]]]]]]
].
d sfs[domain h[a] c forward h[a] a inverse h[a] a condition h[a] c] c[
 w[g item a[c[v domain][v item]]][f item a[y[c[v domain][v item]][
 w[c[v domain][c[v forward][v item]]][w[c[v domain][c[v inverse][v item]]][
 w[e[c[v inverse][c[v forward][v item]]][v item]][w[e[c[v forward][c[v inverse][v item]]][v item]][
 z[c[v condition][v item]][c[v condition][c[v forward][v item]]]]]]]
 ]]]
].
'''


MEANINGS={
    'sfo':'非空の時点範囲の全時点で、同じ履歴に状態が存在し、全ての対応状態が指定同値関係で一致する。表現の個体識別子が違っていてもよい。',
    'sfp':'同じ履歴についてsfoが成立し、全時点の全対応状態で性質が成立する。一つの表現だけを選んで不一致を隠さない。',
    'sfq':'許容する履歴のうち一つが、全時点を通してsfpを満たす。存在量化が時点の全称量化の外側にある。',
    'sfr':'各時点について、その時点の性質を満たす履歴を別々に選んでもよいという弱い条件。各候補自体の状態付与は全時点で一意であることを要求する。',
    'sfs':'非空の領域上の変換と逆変換が領域を保ち、両方向に互いの逆で、指定条件の真偽を保存する。これだけでは望む性質を持つ対象の存在を保証しない。',
}


def generic_composed():
    doc=parse('n:\n'+definitions())
    basis={'version':'parallel-histories-basis-v1','document':'examples/v014/parallel-histories.noema',
        'primitives':[],'definitions':MEANINGS.copy(),'unresolved':[
            '履歴・状態の対応、状態の同値性、許容条件、時点範囲は引数で与える。有限の候補を物理的な全運動と同一視しない。',
            '可逆な対称性の存在だけから、特定の性質を持つ履歴やその選択の正当性を導かない。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-frame-translation.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    text=format_graph(old,'compact')+definitions()+'''
r zch[a d] c.r zci[a] d.r zcj[] a.r zck[a a a a a h[b] c d] c.
r zcl[a] d.r zcm[a a a a d] c.r zcn[a] c.
r zco[] a.r zcp[] a.r zcq[] a.r zcr[a] a.r zcs[a] a.r zct[a a i[e] a a d] c.
d sft[history a] c[
 w[k zch[v history k zb6[]]][w[k sfm[k zci[v history]]][
 f moment a[z[k ys[v moment k zci[v history]]][k ys[v moment k zb6[]]]]]]
].
d sfu[history a moment a pose a valid h[h[b] c] c same h[h[b] c h[b] c] c] c[
 w[k zcn[v pose]][w[k zcf[v moment k ra[] k rb[] k zb6[]]][w[k zcf[v moment k ra[] k rb[] k zci[v history]]][
 w[c[v valid][k yl[v moment k ra[] k rb[] k zb6[]]]][w[c[v valid][k yl[v moment k ra[] k rb[] k zci[v history]]]][
 w[c[v same][k yl[v moment k ra[] k rb[] k zb6[]] k yl[v moment k ra[] k rb[] k zci[v history]]]][
 k zck[v history v moment v pose k ra[] k rb[] k yl[v moment k ra[] k rb[] k zb6[]] k zci[v history]]
 ]]]]]]
].
'''
    scene='k zcl[v pose]'
    selected='e[v point][k zbn[k zbm[] k zb4[]]]'
    axes=['e[v axis][k zbo[k zbm[] k '+role+'[] k zb4[]]]' for role in ('yn','yo','yp')]
    selected='x['+selected+'][g axis a[w[x['+axes[0]+'][x['+axes[1]+']['+axes[2]+']]][k zcc[v point v axis k zci[v history]]]]]'
    coordinate_checks=['k zce[v point v moment k ra[] k ta[] k zci[v history]]',
        'k zce[v point v moment k ra[] k ta[] '+scene+']']
    for role in ('yn','yo','yp'):
        a='k ym[v point v moment k ra[] k ta[] k '+role+'[] k zci[v history]]'
        b='k ym[v point v moment k ra[] k ta[] k '+role+'[] '+scene+']'
        coordinate_checks+=['c[v valid]['+a+']','c[v valid]['+b+']','c[v same]['+a+' '+b+']']
    text+='d sfv[history a moment a pose a valid h[h[b] c] c same h[h[b] c h[b] c] c] c['+both(
        'k zcn[v pose]','f point a[y['+selected+']['+both(*coordinate_checks)+']]')+'].\n'
    clauses=['k zcn[v pose]','k sfb[k ra[] '+scene+']','k sfb[k zbm[] '+scene+']']
    for frame in ('ra','zbm'):
        clauses.append('e[k zbn[k '+frame+'[] '+scene+']][k zbn[k '+frame+'[] k zb4[]]]')
        for role in ('yn','yo','yp'):
            clauses.append('e[k zbo[k '+frame+'[] k '+role+'[] '+scene+']][k zbo[k '+frame+'[] k '+role+'[] k zb4[]]]')
    for role in ('yn','yo','yp'):
        clauses.append('k zbt[k zbo[k ra[] k '+role+'[] '+scene+'] k zbo[k zbm[] k '+role+'[] '+scene+'] '+scene+']')
    text+='d sfw[pose a] c['+both(*clauses)+'].\n'
    text+='''
d sfx[history a admissible h[a] c assigned h[a a a] c same h[a a] c aligned h[a] c] c[
 w[c[v admissible][v history]][k sfp[v history i[moment a][k ys[v moment k zb6[]]] v assigned v same i[moment a pose a][c[v aligned][v pose]]]]
].
d sfy[admissible h[a] c assigned h[a a a] c same h[a a] c aligned h[a] c] c[
 k sfq[i[moment a][k ys[v moment k zb6[]]] v admissible v assigned v same i[moment a pose a][c[v aligned][v pose]]]
].
d sfz[first a second a] c[k zcm[v first v second k ra[] k ta[] k zb6[]]].
d sga[history a moment a pose a] c[w[k sfu[v history v moment v pose p ba p sca]][k sfv[v history v moment v pose p ba p sca]]].
d sgb[] e[b context[
 w[e[k zci[k zcj[]]][k zb6[]]][w[k sft[k zcj[]]][k sfo[k zcj[] i[moment a][k ys[v moment k zb6[]]] p sga p sfz]]]
]].
d sgc[] e[b context[k sfy[p sft p sga p sfz p sfw]]].
d sgd[] e[b context[w[e[k zci[k zcj[]]][k zb6[]]][k sfx[k zcj[] p sft p sga p sfz p sfw]]]].
d sge[] e[b context[k sfs[i[history a][k zch[v history k zb6[]]] p zcr p zcs p sft]]].
'''
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k uh[k zco[] k rd[] r[k sgb[]] k rh[] k ri[]]].
s[w[k ug[k zcp[] k rd[] r[k sgd[]] k rh[] k ri[]]][w[k uh[k zcp[] k rd[] r[k sgc[]] k rh[] k ri[]]][k zao[k zcg[] k zcp[] k rh[] k ri[]]]]].
s[k zct[k zcq[] k rd[] r[k sge[]] k zcp[] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-frame-translation-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-parallel-histories-basis-v1',document='examples/v014/einstein-parallel-histories.noema')
    basis['definitions'].update(MEANINGS)
    decls={d['name']:d for d in doc['declarations']}
    entries=[
        ('zch',['history','scope_context'],'同じ運動問題の候補履歴。許容されない候補も含み得る。許容性はsftで別に判定する。'),
        ('zci',['history'],'候補履歴に対応する運動設定。同じ初期の系・軸・計器をsfmで引き継ぐ。'),
        ('zcj',[],'仮定のもとで選ぶ一つの運動履歴。時刻ごとに別の履歴へ切り替えない。'),
        ('zck',['history','moment','pose','reference_frame','time_unit','time','context'],'指定履歴の軸の配置が、静止系の指定時刻にその状態であるという対応。候補時刻の存在・一致と配置の一意性は別に要求する。'),
        ('zcl',['pose'],'軸配置を記述する断面の設定。履歴の全期間を一枚の断面と同一視しない。'),
        ('zcm',['first_pose','second_pose','reference_frame','length_unit','scope_context'],'二配置の位置・軸の役割・方向が指定系と単位で同じである。状態識別子の同一性や、方向だけの一致ではない。実空間の全点からの構成説明は未完。'),
        ('zcn',['pose'],'軸の幾何学的な配置を表す状態。'),
        ('zco',[],'各静止系時刻に軸の一定の配置が対応すると述べる本文箇所。'),
        ('zcp',[],'全時点で対応軸が平行になる一つの運動を選ぶ仮定の本文箇所。'),
        ('zcq',[],'対称性をこの仮定の正当化として挙げる本文箇所。'),
        ('zcr',['history'],'候補運動を別の候補運動へ変換する操作。原文は具体的な操作を指定していないため、意味規約の入力として未確定のまま残す。'),
        ('zcs',['history'],'zcrの逆として指定する操作。実際に逆であることをsfsで要求する。'),
        ('zct',['node','author','reason_description','assumption_node','scope','context'],'著者が記述された理由を、その仮定を採用してよい根拠として提示する。理由の真理、十分性、物理的な証明の完成を含意しない。')]
    for name,args,meaning in entries:
        d=decls[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'sft':'同じ候補範囲の履歴が、前段の原点・軸・計器の並進sfmを満たし、共通の時点範囲を持つ。',
        'sfu':'候補履歴と比較の設定で、同じ静止系・時間単位の時刻が存在し有効で同じ値であることを確認し、軸配置へ結ぶ。',
        'sfv':'同じ原点と全ての動く軸の配置点について、履歴の当該時点の三座標と配置断面の三座標が存在し、有効で一致する。時計内部の点や軸配置以外の計器はこの断面比較の範囲に補わない。',
        'sfw':'配置断面で二系の三軸が構成され、原点と各役割の軸が初期の同じ対象であり、対応する三軸が全て平行である。原点や支持直線の一致は追加しない。',
        'sfx':'指定した一つの許容履歴が全時点で一意な配置を持ち、全対応配置で軸が平行である。',
        'sfy':'sfxと同じ全時点条件を満たす許容履歴が存在するという候補判定。',
        'sfz':'配置の同値性を共通の静止系・長さ単位・比較範囲へ固定する。',
        'sga':'静止系時刻の対応sfuと、履歴から配置断面への軸座標の対応sfvを、ともに実切断の妥当性baと値一致scaへ接続する。',
        'sgb':'選択した履歴が既存の運動設定zb6と対応し、全時点で配置が存在して一意であるという内容。',
        'sgc':'全時点で平行な許容運動を一つ選べるという存在内容。',
        'sgd':'選択した一つの履歴を既存の運動設定へ結び、全時点で平行な配置を持つとする仮定内容。',
        'sge':'候補領域の可逆変換が運動の許容条件を保存するという、対称性理由の部分モデル。平行配置の存在をそれだけで証明しない。'})
    basis['unresolved'].remove('u0044後半の各時刻での軸配置、対称性による選択の正当化と平行配置の仮定、u0045の両系での測定、原刊照合、全文の意味確認は未完。')
    basis['unresolved']+=generic_composed()[1]['unresolved']+[
        'u0044後半の部分解釈。Symmetriegründenを許容性を保つ可逆変換という一般形へ接続したが、原文の具体的な対称変換は特定されていない。これを同義性の確認済み訳とはしない。',
        '対称性だけでは全時点で平行な運動の存在を導けない。著者への正当化の帰属と、運動の存在・選択の仮定を分離して保持する。',
        '全時点の配置の一意性と座標の観測、配置の実数全域での同値性、軸の正方向の整合、原刊画像との照合は未完。',
        'u0045の両系での空間・時刻の測定、後続の変換の課題と導出、全文の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/parallel-histories-basis-v1.json'),(source_composed,'data/einstein-parallel-histories-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored parallel history differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Definite configurations, one parallel history and attributed symmetry rationale composed')


if __name__=='__main__':main()
