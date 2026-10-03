"""Share one translation across a frame origin and all its placed instruments."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both


def definitions():
    return '''
d sff[objects h[a] c placed h[a a] c] c[
 w[g object a[c[v objects][v object]]][f object a[y[c[v objects][v object]][g point a[c[v placed][v point v object]]]]]
].
d sfg[point a origin a objects h[a] c placed h[a a] c] c[
 x[e[v point][v origin]][g object a[w[c[v objects][v object]][c[v placed][v point v object]]]]
].
d sfh[origin a objects h[a] c placed h[a a] c moments h[a] c before h[a a] c pair h[a a a] c available h[a a] c] c[
 w[k sff[v objects v placed]][w[
 f point a[f moment a[y[w[k sfg[v point v origin v objects v placed]][c[v moments][v moment]]][c[v available][v point v moment]]]]
 ][k sbn[i[point a][k sfg[v point v origin v objects v placed]] v moments v before v pair]]]
].
'''


MEANINGS={
    'sff':'非空の対象範囲で、各対象に少なくとも一つの配置を表す点がある。点を欠く対象を運動条件から脱落させない。',
    'sfg':'指定原点そのもの、または範囲内の対象の配置点のいずれかである。範囲外の物体や内部機構の点を自動で追加しない。',
    'sfh':'全対象の配置点と原点について、全選択時点の座標が利用可能であり、時間幅を持つ区間の逆向きでない全時点対で同じ運動条件が成立する。',
}


def generic_composed():
    doc=parse((ROOT/'examples/v014/rod-setup.noema').read_text(encoding='utf-8')+definitions())
    basis=deepcopy(json.loads((ROOT/'data/rod-setup-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='frame-translation-basis-v1',document='examples/v014/frame-translation.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        '配置点の範囲は対象の位置・姿勢を表すために選ぶ。時計内部の歯車や針まで剛に静止することは要求しない。',
        '選択範囲の完全性、利用可能な座標の存在と一意性、時間順序の正当性は意味規約として別に必要。有限例を連続時間全体の検証とはしない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-coordinate-frames.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    text=format_graph(old,'compact')+definitions()+'''
r zb6[] d.r zb7[] h[b] c.
r zca[a d d] c.r zcb[a d d] c.r zcc[a a d] c.r zcd[a a d] c.
r zce[a a a a d] c.r zcf[a a a d] c.r zcg[] a.
'''
    members=['e[v object][k zbo[k zbm[] k '+role+'[] k zb4[]]]' for role in ('yn','yo','yp')]
    members+=['e[v object][k zby[k zbm[] k zb4[]]]','k zbz[k zbm[] v object k zb4[]]']
    joined=members[-1]
    for clause in reversed(members[:-1]):joined='x['+clause+']['+joined+']'
    text+='d sfi[object a] c['+joined+'].\n'
    origin='k zbn[k zbm[] k zb4[]]'
    clauses=['u[e[v context][k zb4[]]]','k zca[k zbm[] k zb4[] v context]',
        'e['+origin+'][k zbn[k zbm[] v context]]','k zbv[k zbm[] '+origin+' v context]',
        'k zcb['+origin+' k zb4[] v context]',
        'e[k zby[k zbm[] k zb4[]]][k zby[k zbm[] v context]]',
        'k zbx[k zbm[] k zby[k zbm[] k zb4[]] v context]',
        'g clock a[k zbz[k zbm[] v clock k zb4[]]]',
        'f clock a[z[k zbz[k zbm[] v clock k zb4[]]][k zbz[k zbm[] v clock v context]]]',
        'f object a[y[k sfi[v object]][k zcb[v object k zb4[] v context]]]']
    for role in ('yn','yo','yp'):
        axis='k zbo[k zbm[] k '+role+'[] k zb4[]]'
        clauses+=['e['+axis+'][k zbo[k zbm[] k '+role+'[] v context]]',
            'k zbw[k zbm[] '+axis+' k '+role+'[] v context]']
    text+='d sfj[context d] c['+both(*clauses)+'].\n'
    numeric='pair h[h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c] c'
    terms=['k zb7[]','k yl[v first k ra[] k rb[] v context]','k yl[v last k ra[] k rb[] v context]']
    for role in ('yn','yo','yp'):
        for moment in ('first','last'):
            terms.append('k ym[v point v '+moment+' k ra[] k ta[] k '+role+'[] v context]')
    text+='d sfk[point a first a last a context d '+numeric+'] c[c[v pair]['+' '.join(terms)+']].\n'
    args='context d before h[h[b] c h[b] c] c '+numeric+' same h[h[b] c h[b] c] c valid h[h[b] c] c'
    clauses=['k sfj[v context]','k ci[k rb[]]','k ti[k ta[]]','k tj[k ta[] k rb[] k tb[]]',
        'u[e[k yn[]][k yo[]]]','u[e[k yn[]][k yp[]]]','u[e[k yo[]][k yp[]]]',
        'k zcd[k zbm[] k ra[] v context]','c[v valid][k zb7[]]',
        'c[v valid][k zbi[k ra[] k zbm[] k ta[] k rb[] v context]]',
        'c[v same][k zb7[] k zbi[k ra[] k zbm[] k ta[] k rb[] v context]]',
        'k sfh['+origin+' p sfi i[point a object a][k zcc[v point v object v context]] i[moment a][k ys[v moment v context]] '+
        'i[first a last a][c[v before][k yl[v first k ra[] k rb[] v context] k yl[v last k ra[] k rb[] v context]]] '+
        'i[point a first a last a][k sfk[v point v first v last v context v pair]] '+
        'i[point a moment a][w[k zce[v point v moment k ra[] k ta[] v context]][k zcf[v moment k ra[] k rb[] v context]]]]']
    text+='d sfl['+args+'] c['+both(*clauses)+'].\n'
    text+='''
d sfm[context d] c[k sfl[v context p bg p sbm p sca p ba]].
d sfn[] e[b context[k sfm[k zb6[]]]].
'''
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[w[k ug[k zcg[] k rd[] r[k sfn[]] k rh[] k ri[]]][k zao[k zb5[] k zcg[] k rh[] k ri[]]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-coordinate-frames-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-frame-translation-basis-v1',document='examples/v014/einstein-frame-translation.noema')
    basis['definitions'].update(MEANINGS)
    decls={d['name']:d for d in doc['declarations']}
    entries=[
        ('zb6',[],'§3で一方の系に運動を与えた後の等速並進区間。初期静止設定zb4と区別する。'),
        ('zb7',[],'§3で系kに与える正のx方向の一定速度v。数値単位はta/rbで、棒の別設定の速度ybと同一視しない。'),
        ('zca',['frame','initial_context','motion_context'],'同じ座標系を初期設定から後の並進設定へ移す思考上の操作。加速過程の物理的な機構や全履歴を含まない。'),
        ('zcb',['object','initial_context','motion_context'],'原点・軸・計器として同じ対象を後の設定へ引き継ぐ。時計の指示や運動前後の測定値を同一とする関係ではない。'),
        ('zcc',['point','object','context'],'対象の配置を表す点。物質軸や物差しの配置を決める点、および時計を据え付けた位置を表す点を含む。時計の動く内部機構を固定する意味ではない。'),
        ('zcd',['moving_frame','reference_frame','context'],'選ばれた配置点がこの系の原点・全軸・物差し・全時計の配置を尽くし、ysが等速区間の全時点を尽くすという前提。有限標本から認定しない。'),
        ('zce',['point','moment','frame','length_unit','context'],'指定点・時点に三位置座標ymが存在し一意である。関数から候補値を取り出せるだけではこの条件を認めない。'),
        ('zcf',['moment','frame','time_unit','context'],'指定時点にその系での時刻ylが存在し一意である。動く系の時計の指示を静止系の時刻へ混ぜない。'),
        ('zcg',[],'§3で原点に与えた一定速度を軸・物差し・時計にも共有させる想定の本文箇所。')]
    for name,args,meaning in entries:
        d=decls[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'sfi':'初期の同じ系に備えた三軸・物差し・全時計の集合。後の設定で別の計器へ置き換えた集合から始めない。',
        'sfj':'初期設定とは異なる後の設定に同じ系を移し、原点・役割ごとの軸・物差しの同一性と配備を保持する。時計の範囲は両方向の包含で保持し、追加・脱落も区別する。',
        'sfk':'全配置点の二時点を、共通の速度・静止系の時間・三位置座標・単位・文脈を持つ同じ運動条件へ渡す。',
        'sfl':'sfjの対象同一性、範囲の完全性、座標・時刻の利用可能性、単位の商、相対速度の値との一致を保持し、原点と全計器の配置点にsfhを適用する。',
        'sfm':'sflを実切断の時間順序bg、正方向等速並進sbm、値の一致sca、有効性baへ接続する。',
        'sfn':'§3の並進区間zb6にsfmを課す想定内容。前段の初期設定の想定へ追加する。'})
    basis['unresolved'].remove('u0044の原点・軸・計器への運動の共有と対称性に基づく仮定、u0045の両系での空間と時刻の測定、原刊照合、全文の意味確認は未完。')
    basis['unresolved']+=generic_composed()[1]['unresolved'][-2:]+[
        'u0044第一文の部分草案。原点の速度を全配置点へ共通に課すが、時計の歯車や針が止まること、時計が同期済みであること、同じ速さで進むことは含意しない。',
        'zce・zcfの存在と一意性、zcdの完全性は意味規約であり、物理的な観測と全域の座標付与からの構成説明は残る。',
        '初期静止から並進へ移す操作の機構、加速履歴、前後の長さの関係は未説明。等速区間の全点同一変位だけから加速中も剛体であるとしない。',
        'u0044後半の各時刻での軸配置、対称性による選択の正当化と平行配置の仮定、u0045の両系での測定、原刊照合、全文の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/frame-translation-basis-v1.json'),(source_composed,'data/einstein-frame-translation-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored frame translation differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Common translation of the origin, axes, ruler and clock placements composed')


if __name__=='__main__':main()
