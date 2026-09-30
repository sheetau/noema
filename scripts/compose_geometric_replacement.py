"""Describe a common geometric snapshot without identifying motion histories."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_event_time import ROOT


def definitions():
    return '''
d sci[places h[a] c first h[a] c second h[a] c] c[
 w[g point a[c[v first][v point]]][f point a[
 w[z[c[v first][v point]][c[v second][v point]]][y[c[v first][v point]][c[v places][v point]]]
 ]]
].
d scj[system a assumption i[e] scope a context d used h[a i[e] a d] c stated h[a i[e] a d] c] c[
 w[c[v used][v system v assumption v scope v context]][u[c[v stated][v system v assumption v scope v context]]]
].
d sck[first h[h[b] c] c second h[h[b] c] c valid h[h[b] c] c same h[h[b] c h[b] c] c] c[
 g left h[b] c[g right h[b] c[
 w[k sbx[v left v right v first v valid v same]][w[k sby[v left v first v same]][k sby[v right v second v same]]]
 ]]
].
'''


MEANINGS={
    'sci':'二つの非空の占有集合が全対象について一致し、占有点が全て位置型である。位置型として選んだ点だけを比較して範囲外の不一致を隠さない。',
    'scj':'同じ体系・仮定記述・範囲・文脈で、仮定を使うことと、明示的に述べていないことをともに要求する。仮定内容の真理は評価しない。',
    'sck':'二方法でそれぞれ一意な有効値が存在し、両値が一致する。空の結果集合や、異なる値を複数含む結果を同じ長さとは扱わない。',
}


def generic_composed():
    doc=parse((ROOT/'examples/v014/rod-comparison.noema').read_text(encoding='utf-8')+definitions())
    basis=deepcopy(json.loads((ROOT/'data/rod-comparison-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='geometric-replacement-basis-v1',document='examples/v014/geometric-replacement.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'sciは同じ幾何学的背景での占有点集合の一致という読み。物質点のラベル、速度、時計の進み、密度などの同一性は要求しない。',
        'scjの否定は明示的な意味条件であり、記録が見つからないだけで非明示と推論する規則ではない。体系・慣行における仮定使用と明示の基礎説明は未完。',
        'sckの実切断全域の存在・一意性を有限標本で証明しない。一つの長さの一致から全幾何の一致は導かれない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-rod-comparison.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    doc=parse(format_graph(old,'compact')+definitions()+'''
r zj[a] c.r zk[a a a h[b] c d] c.r zl[a d d] c.r zm[a] c.r zn[a d] c.
r zo[a a h[b] c d] c.r zp[] h[b] c.r zq[a d] c.
r zr[] a.r zs[a d] c.r zt[a i[e] a d] c.r zu[a i[e] a d] c.
r zv[] a.r zw[] a.r zx[a a a i[e] i[e] a d] c.
d scl[] e[b context[
 k sck[i[value h[b] c][k sbi[v value k ye[]]] i[value h[b] c][k sbk[v value k yf[]]] p sbg p sca]
]].
d scm[body a moving d resting d epoch h[b] c validtime h[h[b] c] c] c[
 w[c[v validtime][v epoch]][w[k zm[v body]][w[k va[k ra[]]][w[u[e[v moving][v resting]]][
 w[k zq[v body v moving]][w[k zq[v body v resting]][w[k xm[v body k ra[] v moving]][
 w[k x4[v body k ra[] v resting]][w[k zl[v body v moving v resting]][
 w[k zo[v body k ra[] v epoch v moving]][w[k zo[v body k ra[] v epoch v resting]][
 k sci[p zj i[point a][k zk[v point v body k ra[] v epoch v moving]]
 i[point a][k zk[v point v body k ra[] v epoch v resting]]]
 ]]]]]]]]]]]
].
d scn[body a moving d epoch h[b] c validtime h[h[b] c] c] c[
 g resting d[k scm[v body v moving v resting v epoch v validtime]]
].
d sco[validtime h[h[b] c] c] c[
 w[g body a[k zn[v body k yd[]]]][f body a[y[k zn[v body k yd[]]][k scn[v body k yd[] k zp[] v validtime]]]]
].
d scp[] e[b context[k sco[p ba]]].
d scq[] e[b context[w[k zs[k zr[] v context]][k scj[k zr[] r[k scl[]] k xy[] v context p zt p zu]]]].
d scr[] e[b context[w[k zs[k zr[] v context]][k scj[k zr[] r[k scp[]] k xy[] v context p zt p zu]]]].
''')
    doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k uh[k zv[] k rd[] r[k scq[]] k xy[] k ri[]]].
s[k uh[k zv[] k rd[] r[k scr[]] k xy[] k ri[]]].
s[k zx[k zw[] k rd[] k zr[] r[k scl[]] r[k scp[]] k xy[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-rod-comparison-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-geometric-replacement-basis-v1',document='examples/v014/einstein-geometric-replacement.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'].remove('u0034の旧運動学の暗黙の仮定と幾何学的置換、原刊照合、全文の意味確認は残る。')
    meanings=[
        ('zj',['place'],'同じ幾何学的背景に属する空間位置。座標系と空間の基礎説明は未完。'),
        ('zk',['place','body','frame','epoch','context'],'指定状態で同じ物体が同じ基準系の指定時刻にその位置を占める。全履歴の軌道ではなく一時刻の占有である。'),
        ('zl',['body','moving_context','resting_context'],'同じ物体について、動く状態に対する比較対象として許容した、特定配置で静止する状態。別物体のコピーとは区別する。可能な配置や加速過程の理論は未完。'),
        ('zm',['body'],'幾何学的形状を持つ物体。棒だけに制限しない。'),
        ('zn',['body','context'],'一般的な置換の主張で扱う物体の範囲。必要な全物体を含むという解釈を別途必要とし、有限例から認定しない。'),
        ('zo',['body','frame','epoch','context'],'占有関係zkがこの物体・基準系・時刻・状態の全占有位置を尽くすという前提。観測標本の一致だけから認定しない。'),
        ('zp',[],'幾何学的に比較する指定時刻t。初期時刻やゼロには固定しない。'),
        ('zq',['body','context'],'この状態で剛体として扱う物体。棒に限らない理想化であり、物質的機構からの構成説明は未完。'),
        ('zr',[],'本文が比較対象とする従来の運動学的体系。著者の二原理と同一視しない。'),
        ('zs',['system','context'],'指定体系がその文脈で広く使われている。頻度や採用集団の構成説明は未完。'),
        ('zt',['system','assumption','scope','context'],'体系がこの記述の内容を指定範囲で前提として使う。内容の真理は評価しない。'),
        ('zu',['system','assumption','scope','context'],'体系がこの記述の仮定をその範囲で明示的に述べている。非明示はこの関係の否定として別に記述する。'),
        ('zv',[],'旧運動学の暗黙の仮定を著者が帰属する本文箇所。'),
        ('zw',[],'同じ仮定を幾何学的な置換として言い換える本文箇所。'),
        ('zx',['node','author','system','first','second','scope','context'],'著者がこの体系に帰属した仮定の第一記述を第二記述で言い換える。論理的な同値の機械証明や、両内容への著者自身の同意を意味しない。'),
    ]
    declarations={d['name']:d for d in doc['declarations']}
    for name,args,meaning in meanings:
        d=declarations[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'scl':'先行する二操作がそれぞれ一意に与える正の長さが、互いに値として一致するという内容。初期長との比較で置き換えない。',
        'scm':'同じ剛体の運動状態と許容された静止配置を、同じ基準系・指定時刻の全占有点集合として比較する。速度や時計の進みは同一視しない。',
        'scn':'指定時刻にscmを満たす静止配置が少なくとも一つある。配置の一意性や運動の実行済み事実は要求しない。',
        'sco':'選択範囲が非空で、選択した全物体が同じ指定時刻にscnを満たす。条件を満たさない物体を黙って範囲から除かない。',
        'scp':'scoの時刻を有効な実切断へ接続した幾何学的置換の内容。',
        'scq':'広く使われる旧運動学が二方法の等値sclを使い、明示してはいないという内容。',
        'scr':'同じ旧運動学が幾何学的置換scpを使い、明示してはいないという内容。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'][-3:] + [
        'u0034の部分草案。全幾何を同じ背景の占有点集合として読む解釈であり、位置・形状・剛体・許容配置の基礎説明は未完。',
        'scnの状況量化は比較する静止配置の可能性を表す。実際に物体を停止させた事実や、停止時に形状が保存される法則は導かない。',
        '長さの一致と占有点の一致が一般に同値とは証明していない。原文の言い換えを著者への帰属として保存する。',
        '全対象範囲、暗黙の仮定と普及の根拠、原刊照合、全文の意味確認は残る。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/geometric-replacement-basis-v1.json'),(source_composed,'data/einstein-geometric-replacement-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored geometric replacement differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Geometric replacement, tacit assumptions and attributed reformulation composed')


if __name__=='__main__':main()
