"""Keep x-vt as an auxiliary label and ask for synchronized moving-frame time."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_homogeneous_coordinates import CUT, OP, VALID, SAME, TRUE

TAU='h['+' '.join([CUT]*4)+'] '+CUT
SHIFT='h['+' '.join([CUT]*3)+'] '+CUT


def definitions():
    text='''
d sif[speed b position b time b] b[k ab[v position k ac[k ad[v speed v time]]]].
'''+('d sig[speed '+CUT+' position '+CUT+' time '+CUT+' subtract '+OP+' multiply '+OP+'] '+CUT+
        '[c[v subtract][v position c[v multiply][v speed v time]]].\n')
    width='g first a[g last a['+both('c[v moments][v first]','c[v moments][v last]','c[v before][v first v last]')+']]'
    available='f point a[f moment a[y[w[c[v points][v point]][c[v moments][v moment]]][c[v available][v point v moment]]]]'
    pair=both('c[v points][v point]','c[v moments][v first]','c[v moments][v last]')
    equal='q[v axes]['+TRUE+'][i[ok c axis a][w[v ok][c[v same][c[v coordinate][v point v first v axis] c[v coordinate][v point v last v axis]]]]]'
    constant='f point a[f first a[f last a[y['+pair+']['+equal+']]]]'
    text+='d sih[points h[a] c moments h[a] c axes j[a] available h[a a] c before h[a a] c coordinate h[a a a] h[b] c same h[h[b] c h[b] c] c] c['+both(
        'k shm[v axes]','g point a[c[v points][v point]]',width,available,constant)+'].\n'
    return text


MEANINGS={
    'sif':'有理数の補助座標x′=x-vt。速度と時刻の符号と原点をそのまま保つ。',
    'sig':'sifの演算構造を、指定した数値の差と積に適用する。入力の有効性と単位は呼出側で確認する。',
    'sih':'非空の点範囲と時間幅を持つ時点範囲について、全点・全時点で座標が利用可能であり、同じ点の全時点対で指定した全成分の値が一致する。点同士の座標一致は要求しない。',
}


def generic_composed():
    inherited=json.loads((ROOT/'data/homogeneous-coordinates-basis-v1.json').read_text(encoding='utf-8'))
    parent=parse((ROOT/'examples/v014/homogeneous-coordinates.noema').read_text(encoding='utf-8'))
    parent['declarations']=[d for d in parent['declarations'] if d['name'] in ('aa','ab','ac','ad','shm')]
    doc=parse(format_graph(parent,'compact')+definitions())
    basis={'version':'comoving-labels-basis-v1','document':'examples/v014/comoving-labels.noema',
        'primitives':deepcopy(inherited['primitives']),'definitions':{'shm':inherited['definitions']['shm'],**MEANINGS},
        'unresolved':[
            '時間幅と座標の利用可能性、点・時点の範囲を引数で与える。有限の端点だけで連続時間全体の不変性を証明しない。',
            'x′が一定であることから、それが別の系の物差しで測ったξと等しいとは結論しない。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-homogeneous-coordinates.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    text=format_graph(old,'compact')+definitions()+'''
r zdi[a d] c.r zdj[] a.r zdk[] a.r zdl[] a.r zdp[] a.
'''
    text+='r zdm[a a i['+SHIFT+'] a d] c.r zdn[a a a i[g['+TAU+']] a d] c.r zdo[a a i[h['+TAU+'] c] a a d] c.\n'
    time='k yl[v moment k ra[] k rb[] v context]'
    x='k ym[v point v moment k ra[] k ta[] k yn[] v context]'
    coord='k ym[v point v moment k ra[] k ta[] v role v context]'
    text+='d sij[point a moment a role a context d subtract '+OP+' multiply '+OP+'] '+CUT+'[i[q b][x['+both(
        'e[v role][k yn[]]','c[k sig[k zb7[] '+x+' '+time+' v subtract v multiply]][v q]')+']['+both(
        'u[e[v role][k yn[]]]','c['+coord+'][v q]')+']]].\n'
    selected='i[point a][w[k zdi[v point v context]][k x4[v point k zbm[] v context]]]'
    available=['k zce[v point v moment k ra[] k ta[] v context]','k zcf[v moment k ra[] k rb[] v context]',
        'c[v valid]['+time+']']
    for role in ('yn','yo','yp'):
        available+=['c[v valid][k ym[v point v moment k ra[] k ta[] k '+role+'[] v context]]',
            'c[v valid][k sij[v point v moment k '+role+'[] v context v subtract v multiply]]']
    args='context d valid '+VALID+' same '+SAME+' before '+SAME+' subtract '+OP+' multiply '+OP
    requirements=['u[e[k ra[]][k zbm[]]]','k va[k ra[]]','k va[k zbm[]]','k ci[k rb[]]','k ti[k ta[]]',
        'k tj[k ta[] k rb[] k tb[]]','c[v valid][k zb7[]]','c[v before][k bb[n p a b] k zb7[]]',
        'c[v valid][k zbi[k ra[] k zbm[] k ta[] k rb[] v context]]',
        'c[v same][k zb7[] k zbi[k ra[] k zbm[] k ta[] k rb[] v context]]',
        'k sih['+selected+' i[moment a][k ys[v moment v context]] l[a][k yn[] k yo[] k yp[]] '+
        'i[point a moment a]['+both(*available)+'] '+
        'i[first a last a][c[v before][k yl[v first k ra[] k rb[] v context] k yl[v last k ra[] k rb[] v context]]] '+
        'i[point a moment a role a][k sij[v point v moment v role v context v subtract v multiply]] v same]']
    text+='d sik['+args+'] c['+both(*requirements)+'].\n'
    text+='''
d sil[context d] c[k sik[v context p ba p sca p bg p bf p shv]].
d sim[] e[b context[k sil[k zb6[]]]].
'''
    text+='d sin[speed '+CUT+' position '+CUT+' time '+CUT+'] '+CUT+'[k sig[v speed v position v time p bf p shv]].\n'
    fargs=['k sin[k zb7[] k zc6[v first k yn[]] k zc6[v first k zc7[]]]',
        'k zc6[v first k yo[]]','k zc6[v first k yp[]]','k zc6[v first k zc7[]]']
    proposed='c[v function]['+' '.join(fargs)+']'
    content=both('k sgw[p shf p shg p she p shh]','k ba[k zb7[]]',
        'k sca[k zb7[] k zbi[k ra[] k zbm[] k ta[] k rb[] k zb6[]]]',
        'f first a[f second a[y['+both('k shf[v first]','k shg[v second]','k she[v first v second]')+']['+both(
            'k ba['+proposed+']','k sca['+proposed+' k zc6[v second k zc7[]]]')+']]]')
    text+='d sio[function '+TAU+'] c['+content+'].\n'
    text+='d sip[] g['+TAU+'][j v[i[function '+TAU+'][k sio[v function]]]].\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zdm[k zdj[] k rd[] r[p sin] k rh[] k ri[]]].
s[w[k uh[k zdk[] k rd[] r[k sim[]] k rh[] k ri[]]][k zdg[k zdk[] k rd[] r[k sim[]] k rh[] k ri[]]]].
s[k zdn[k zdl[] k rd[] k zdb[] r[k sip[]] k rh[] k ri[]]].
s[k zdo[k zdp[] k rd[] r[p sio] k zdl[] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-homogeneous-coordinates-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-comoving-labels-basis-v1',document='examples/v014/einstein-comoving-labels.noema')
    basis['definitions'].update(MEANINGS);decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zdi',['point','context'],'この設定で位置の履歴を考察する点の全範囲。物質点に限定せず、座標系に静止する配置点も扱う。'),
        ('zdj',[],'x′=x-vtと置くという補助座標の導入箇所。'),
        ('zdk',[],'運動系で静止する点のx′・y・zが時間に依存しないと述べる箇所。'),
        ('zdl',[],'まずτをx′・y・z・tの関数として求める課題の箇所。'),
        ('zdp',[],'そのため同期時計の読みを方程式で表す必要を述べる箇所。'),
        ('zdm',['node','author','rule','scope','context'],'著者が引用した三引数の数値関数を補助量の定義として導入する。新しい基準系の物理的測定と同一とは主張しない。'),
        ('zdn',['node','author','parent_task','question','scope','context'],'著者が先行課題の中で、この質問の答えをまず求める下位課題として選ぶ。答えの発見済み・存在・唯一性を含意しない。'),
        ('zdo',['node','author','required_rule','subtask','scope','context'],'著者がこの下位課題を解くため、記述された候補条件を方程式で表す必要を述べる。式の導出や目的の達成は含意しない。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'sij':'同じ点・静止系時刻・文脈から、x-vt・y・zを成分ごとに取り出す。運動系のξ・η・ζや時計のτへ置き換えない。',
        'sik':'運動系で静止する範囲内の全点について、共通速度・静止系の時刻・単位・全時点の利用可能性を保持し、補助三座標が全時点で一定であることを要求する。',
        'sil':'sikを実切断の妥当性ba、値一致sca、時間順序bg、差bf、符号付き積shvへ接続する。',
        'sim':'同じ等速並進設定で静止点の補助三座標が不変であるという内容。',
        'sin':'実切断についてx-vtを定義する。x′の導入規則として引用する。',
        'sio':'同じ出来事の座標対応の全範囲で、候補関数がx′・y・z・静止系時刻tから有効な運動系時刻τを返す条件。τはshd・sgpを通じた配備静止時計の同期した読みへ結ばれている。',
        'sip':'sioを満たす四引数関数を答えとする質問。関数の具体形や係数を先に補わない。'})
    basis['unresolved']+=generic_composed()[1]['unresolved']+[
        'u0048の部分記述。運動系の静止をx4で指定し、x′・y・zの全時点不変性を著者の主張として保持する。物理的な静止と等速並進の一般的同値性の機械的証明は未完。',
        '方程式で表すという目的を、同期時計の読みへの候補関数の照合条件へ接続した。後続の光往復の具体的な式やτの導出は未完。',
        'x′は静止系の数値から作る補助量であり、運動系の長さ単位で測定したξと自動的に同一視しない。',
        '点の履歴ym・ylと出来事の座標記録zc6の一般的な接続、全点・全時点の範囲の実現、原刊照合、全文の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/comoving-labels-basis-v1.json'),(source_composed,'data/einstein-comoving-labels-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored comoving labels differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Auxiliary comoving labels and the moving-time subtask composed')


if __name__=='__main__':main()
