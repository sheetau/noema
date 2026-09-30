"""Compose a rod's initial setting, uniform translation and method-tagged question."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_event_time import ROOT


def definitions():
    numeric = '''
d sbl[speed b first b last b firstx b lastx b firsty b lasty b firstz b lastz b] c[
 w[k aa[n p a b v speed]][w[u[k aa[v last v first]]][
 w[e[k ab[v lastx k ac[v firstx]]][k ad[v speed k ab[v last k ac[v first]]]]][
 w[e[v firsty][v lasty]][e[v firstz][v lastz]]]]]
].
'''
    names = 'speed first last firstx lastx firsty lasty firstz lastz'.split()
    real = '''w[k bg[k bb[n p a b] v speed]][w[k bc[v first v last]][
 w[k sag[k bf[v lastx v firstx] k sah[v speed k bf[v last v first]] p bc]][
 w[k sag[v firsty v lasty p bc]][k sag[v firstz v lastz p bc]]]]]'''
    for name in reversed(names):
        real = f'w[k ba[v {name}]][{real}]'
    numeric += 'd sbm['+' '.join(n+' h[b] c' for n in names)+'] c['+real+'].\n'
    return numeric + '''
d sbn[points h[a] c moments h[a] c before h[a a] c pair h[a a a] c] c[
 w[g point a[c[v points][v point]]][
 w[g first a[g last a[w[c[v moments][v first]][w[c[v moments][v last]][c[v before][v first v last]]]]]][
 f point a[f first a[f last a[y[
 w[c[v points][v point]][w[c[v moments][v first]][w[c[v moments][v last]][u[c[v before][v last v first]]]]]
 ][c[v pair][v point v first v last]]]]]]]
].
d sbo[first a second a firstmethod h[h[b] c] c secondmethod h[h[b] c] c] g[a h[b] c][
 j v[i[method a value h[b] c][w[u[e[v first][v second]]][
 x[w[e[v method][v first]][c[v firstmethod][v value]]][w[e[v method][v second]][c[v secondmethod][v value]]]
 ]]]
].
'''


MEANINGS = {
    'sbl':'有理数の座標で、正の一定速度によるx方向の変位、y・zの不変、非負の経過時間を要求する。初期座標や時刻原点をゼロに固定しない。',
    'sbm':'sblと同じ条件を有効な実数の下側切断で記述する。座標の一致は切断の両方向包含で判定し、関数の実装上の同一性とは分ける。',
    'sbn':'非空の点集合と時間幅を持つ時点集合で、逆向きでない全時点対と全点に同じ対条件を課す。同時刻の別の記録も対象となる。beforeは厳密な時間順序として別途接続する。',
    'sbo':'異なる二方法の識別子と値の組を答えとする質問。各方法の候補判定を独立に保ち、同じ値でも異なる値でも許す。答えの存在や唯一性を断定しない。',
}


def generic_composed():
    text = (ROOT/'examples/v014/rod-measurements.noema').read_text(encoding='utf-8') + definitions()
    doc = parse(text)
    basis = deepcopy(json.loads((ROOT/'data/rod-measurements-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='rod-setup-basis-v1', document='examples/v014/rod-setup.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'sbnの選択集合が全物質点・全時点を尽くすことは別の意味規約に必要。有限標本の一致から連続時間全体の等速性を認定しない。',
        '全点の同じ変位は指定区間の並進条件であり、加速過程、物質の剛性、静止時と運動時の長さの一致を説明しない。',
        'sboは方法付き候補の集合を表す。現実の測定結果を生成する手続きではない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def source_composed():
    old = parse((ROOT/'examples/v014/einstein-rod-measurements.noema').read_text(encoding='utf-8'))
    statements, old['statements'] = old['statements'], []
    doc = parse(format_graph(old, 'compact')+definitions()+'''
r ya[] h[b] c.r yb[] h[b] c.
r yc[] d.r yd[] d.r ye[] d.r yf[] d.
r yl[a a a d] h[b] c.r ym[a a a a a d] h[b] c.
r yn[] a.r yo[] a.r yp[] a.r yq[a a d] c.r yr[a a d] c.r ys[a d] c.
r yt[a d] c.r yu[a a a d] c.r yv[a d d] c.r yx[d d] c.
r y2[] a.r y3[] a.r yz[a a i[g[a h[b] c]] a d] c.
d sbp[context d positive h[h[b] c] c] c[
 w[c[v positive][k ya[]]][w[k xa[k xi[]]][w[k xc[k xj[]]][w[k yt[k xi[] v context]][
 w[k ti[k ta[]]][w[k x4[k xi[] k ra[] v context]][w[k x4[k xj[] k ra[] v context]][
 w[k xd[k xj[] k xi[] k ra[] v context]][g observer a[
 w[k xb[v observer]][k xe[v observer k xj[] k xi[] k ra[] k ta[] k ya[] v context]]
 ]]]]]]]]]
].
d sbq[context d] c[k sbp[v context p sbg]].
d sbr[context d before h[h[b] c h[b] c] c pair h[h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c] c] c[
 w[u[e[k yn[]][k yo[]]]][w[u[e[k yn[]][k yp[]]]][w[u[e[k yo[]][k yp[]]]][
 w[k ci[k rb[]]][w[k ti[k ta[]]][w[k yq[k xi[] k ra[] v context]][
 w[k yr[k xn[] k xi[] v context]][w[k yr[k xo[] k xi[] v context]][
 k sbn[i[point a][k yr[v point k xi[] v context]] i[moment a][k ys[v moment v context]]
 i[first a last a][c[v before][k yl[v first k ra[] k rb[] v context] k yl[v last k ra[] k rb[] v context]]]
 i[point a first a last a][c[v pair][k yb[] k yl[v first k ra[] k rb[] v context] k yl[v last k ra[] k rb[] v context]
 k ym[v point v first k ra[] k ta[] k yn[] v context] k ym[v point v last k ra[] k ta[] k yn[] v context]
 k ym[v point v first k ra[] k ta[] k yo[] v context] k ym[v point v last k ra[] k ta[] k yo[] v context]
 k ym[v point v first k ra[] k ta[] k yp[] v context] k ym[v point v last k ra[] k ta[] k yp[] v context]]]
 ]]]]]]]]]
].
d sbs[context d] c[k sbr[v context p bg p sbm]].
d sbw[initial h[d] c motion h[d] c] e[b context[
 w[u[e[k yc[]][k yd[]]]][w[u[e[k ye[]][k yf[]]]][
 w[c[v initial][k yc[]]][w[k yu[k xi[] k ra[] k yn[] k yc[]]][
 w[k yv[k xi[] k yc[] k yd[]]][w[c[v motion][k yd[]]][
 w[k yx[k yd[] k ye[]]][k yx[k yd[] k yf[]]]]]]]]]
]].
d sbt[] e[k sbw[p sbq p sbs]].
d sbu[first h[h[b] c d] c second h[h[b] c d] c] g[a h[b] c][
 k sbo[k xw[] k xx[] i[value h[b] c][c[v first][v value k ye[]]] i[value h[b] c][c[v second][v value k yf[]]]]
].
d sbv[] g[a h[b] c][k sbu[p sbi p sbk]].
''')
    doc['statements'] = statements
    doc = parse(format_graph(doc, 'compact')+'''
s[k ug[k y2[] k rd[] r[k sbt[]] k xy[] k ri[]]].
s[k yz[k y3[] k rd[] r[k sbv[]] k xy[] k ri[]]].
''')
    basis = deepcopy(json.loads((ROOT/'data/einstein-rod-measurements-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-rod-setup-basis-v1', document='examples/v014/einstein-rod-setup.noema')
    prior_gap = 'u0030・u0031の二方法の部分草案。u0029の棒の初期長・剛性・軸・運動の付与・問いはまだ接続していない。'
    basis['unresolved'].remove(prior_gap)
    basis['definitions'].update(MEANINGS)
    meanings = [
        ('ya', [], '静止状態で同じ物差しにより測った棒の初期長l。任意の数値は補わない。'),
        ('yb', [], '静止系で正のx方向へ与える一定速度v。長さ単位taと時間単位rbの商による数値として指定する。'),
        ('yc', [], '棒と物差しが静止して初期長を測る設定。'),
        ('yd', [], '棒に運動を与えた後の等速並進区間の設定。加速過程をこの区間へ混ぜない。'),
        ('ye', [], 'その運動する棒を方法aで測る設定。'), ('yf', [], 'その運動する棒を方法bで測る設定。'),
        ('yl', ['moment','frame','time_unit','context'], '指定時点の指定基準系・時間単位での時刻値。'),
        ('ym', ['point','moment','frame','length_unit','axis','context'], '同じ物質点・時点・基準系・長さ単位・軸・文脈の座標値。'),
        ('yn', [], '選択した静止系のx軸。'), ('yo', [], '同じ座標系のy軸。'), ('yp', [], '同じ座標系のz軸。'),
        ('yq', ['rod','frame','context'], 'yrがこの棒の全物質点、ysが選択した運動区間の全時点を尽くすという前提。有限標本から成立を認定しない。'),
        ('yr', ['point','rod','context'], 'その棒を構成する物質点。表面点や端点だけに制限しない。'),
        ('ys', ['moment','context'], '選択した等速運動区間の時点。実際の区間は全時点を対象とする。'),
        ('yt', ['rod','context'], '棒を剛体として扱う理想化。物質の機構、加速時の応答、幾何学的剛性の構成説明は未完。'),
        ('yu', ['rod','frame','axis','context'], '初期配置で棒の長軸を指定座標系の指定軸上に置く。単なる平行だけではない。形状からの構成説明は未完。'),
        ('yv', ['rod','initial_context','moving_context'], '同じ棒を初期設定から後の運動設定へ移す思考上の操作。時間の順と対象の同一性を保持するが、加速法則は指定しない。'),
        ('yx', ['motion_context','measurement_context'], '指定運動状態を、測定方法の設定において評価対象として引き継ぐ対応。二方法を同じ測定設定と同一視しない。'),
        ('y2', [], '静止棒から等速移動棒を設定する本文箇所。'), ('y3', [], '二方法による棒の長さを尋ねる本文箇所。'),
        ('yz', ['node','author','question','scope','context'], '著者が指定考察範囲でこの記述の質問を提示する。質問の答えが存在する、唯一である、現に測定されたとは断定しない。'),
    ]
    declarations = {d['name']:d for d in doc['declarations']}
    for name, args, meaning in meanings:
        declaration = declarations[name]
        basis['primitives'].append(dict(symbol=name,parameters=declaration['parameters'],result=declaration['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'sbp':'同じ棒と物差しの初期静止、剛体の理想化、正の初期長、物差しの配置と測定を結合する。初期観測者は存在だけを要求し、後の観測者と同一と決めない。',
        'sbq':'sbpの正の長さを実切断の条件sbgへ接続する。',
        'sbr':'同じ棒の全物質点を、同じ速度・基準系・単位・文脈の全時点対へ結び付ける。x変位だけを時間に比例させ、y・zの変化を許さない。',
        'sbs':'sbrの時間順序と点対条件を実切断のbg・sbmへ接続する。',
        'sbw':'初期状態と運動状態の判定を受け取り、軸への配置・時間順の操作・二方法への設定の継承と結合する。',
        'sbt':'初期静止長、x軸への配置、運動を与える順序、等速並進、二つの別の測定設定への接続を一つの想定内容としてまとめる。現実の実行済み事実とは断定しない。',
        'sbu':'方法a/bの識別子とそれぞれの測定設定を、方法付き長さ候補の質問へ接続する。',
        'sbv':'sbuの候補判定を既存の直接測定sbi・同時端点測定sbkへ接続した質問。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'][-3:] + [
        'u0029の部分草案。剛性、棒の長軸を座標軸上へ置くこと、運動を与える操作、設定間の物理的な継承は基本関係の意味規約に留まる。',
        '単位の商による速度数値と直交座標の規約を採用する。単位体系・座標系・物理的観測の全基礎をこの文書だけで再定義したものではない。',
        '全点・全時点の等速性は記述したが、有限実行器で実数全域の物理モデルを検証したとは扱わない。',
        '本草案で初期設定と問いを部分的に接続したが、u0032以降の同値・相違・論証と原刊照合、全文の意味確認は残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def main():
    for compose, filename in ((generic_composed,'data/rod-setup-basis-v1.json'),(source_composed,'data/einstein-rod-setup-basis-v1.json')):
        text, basis = compose()
        for name, body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path = ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored rod setup differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:
                    stream.write(body)
    print('Initial rod setting, uniform translation and method-tagged length question composed')


if __name__ == '__main__':
    main()
