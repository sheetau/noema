"""Compose ruler coordinates and local clock time within each frame."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both


def definitions():
    return '''
d sgf[places h[a] c channels h[a] c provided h[a a] c] c[
 w[g place a[c[v places][v place]]][w[g channel a[c[v channels][v channel]]][
 f place a[f channel a[y[w[c[v places][v place]][c[v channels][v channel]]][c[v provided][v place v channel]]]]]]
].
d sgg[places h[a] c clocks h[a] c located h[a a] c usable h[a] c synchronized h[a a] c reference a] c[
 w[c[v clocks][v reference]][f clock a[y[c[v clocks][v clock]][
 w[c[v usable][v clock]][w[g place a[w[c[v places][v place]][c[v located][v clock v place]]]][
 w[f place a[y[c[v located][v clock v place]][c[v places][v place]]]][c[v synchronized][v clock v reference]]]]
 ]]]
].
d sgh[place a clocks h[a] c located h[a a] c] c[
 g clock a[w[c[v clocks][v clock]][c[v located][v clock v place]]]
].
d sgi[places h[a] c clocks h[a] c located h[a a] c events h[a] c eventplace h[a a] c assigned h[a a] c] c[
 f place a[f event a[y[w[c[v places][v place]][w[k sgh[v place v clocks v located]][
 w[c[v events][v event]][c[v eventplace][v event v place]]]]][c[v assigned][v event v place]]]]
].
'''


MEANINGS={
    'sgf':'空でない場所範囲と成分範囲の全組合せに、値の付与条件を要求する。一地点または一成分の欠落を許さない。',
    'sgg':'同じ参照時計を配備範囲に含め、全配備時計が使用条件を満たし、指定空間内に設置され、その参照時計に同期する。時計の全設置場所を範囲内に要求するが、全地点への時計の配置は要求しない。',
    'sgh':'その場所に配備範囲の時計が少なくとも一つある。時計のない地点をこの条件へ含めない。',
    'sgi':'配備時計がある範囲内の場所で発生する全対象出来事に、その同じ場所での時刻付与条件を要求する。時計のない場所や出来事のない場所で時刻値を生成しない。',
}


def generic_composed():
    doc=parse('n:\n'+definitions())
    basis={'version':'frame-measurements-basis-v1','document':'examples/v014/frame-measurements.noema',
        'primitives':[],'definitions':MEANINGS.copy(),'unresolved':[
            '場所・成分・配備時計・出来事の範囲と測定関係は引数で与える。その範囲が原文の対象全体を尽くすことは有限例だけでは証明できない。',
            'sgi単独では出来事の存在を要求しない。時間の付与は対象出来事がある場合の条件であり、時計のない空間への補間を含まない。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-parallel-histories.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    text=format_graph(old,'compact')+definitions()+'''
r zcu[a a d] c.r zcv[a a a d] a.r zcw[a a a a d] c.
r zcx[a a a a a a h[b] c d] c.r zcy[a a a a d] h[b] c.
r zcz[a a d] c.r zc2[] a.r zc3[] a.
'''
    roles='x[e[v role][k yn[]]][x[e[v role][k yo[]]][e[v role][k yp[]]]]'
    value_args='place a frame a role a unit a value h[b] c context d valid h[h[b] c] c'
    call='v place v frame v role v unit v value v context v valid'
    projection='k zcv[v place v frame v role v context]'
    measure='k zcx[k zby[v frame v context] k zbn[v frame v context] '+projection+' v frame k zbo[v frame v role v context] v unit v value v context]'
    text+='d sgj['+value_args+'] c['+both(
        'c[v valid][v value]','k zcu[v place v frame v context]',roles,
        'k zcw[v place '+projection+' v frame k zbo[v frame v role v context] v context]',measure)+'].\n'
    selected='k zcy[v place v frame v role v unit v context]'
    text+='d sgk[place a frame a role a unit a context d valid h[h[b] c] c same h[h[b] c h[b] c] c] c['+both(
        'k sgj[v place v frame v role v unit '+selected+' v context v valid]',
        'f value h[b] c[y[k sgj['+call+']][c[v same][v value '+selected+']]]')+'].\n'
    requirements=['k sfb[v frame v context]','k ti[k ta[]]',
        'k xc[k zby[v frame v context]]','k zbx[v frame k zby[v frame v context] v context]',
        'k zbq[k zby[v frame v context] v context]','k x4[k zby[v frame v context] v frame v context]',
        'e[k zby[v frame v context]][k zby[v frame k zb4[]]]',
        'e[k zbn[v frame v context]][k zbn[v frame k zb4[]]]']
    requirements += ['e[k zbo[v frame k '+r+'[] v context]][k zbo[v frame k '+r+'[] k zb4[]]]' for r in ('yn','yo','yp')]
    requirements += ['k sgf[i[place a][k zcu[v place v frame v context]] i[role a]['+roles+'] '+
        'i[place a role a][k sgk[v place v frame v role k ta[] v context v valid v same]]]']
    text+='d sgl[frame a context d valid h[h[b] c] c same h[h[b] c h[b] c] c] c['+both(*requirements)+'].\n'
    text+='''
d sgm[frame a context d] c[k sgl[v frame v context p ba p sca]].
d sgn[] e[b context[w[k sgm[k ra[] k zb6[]]][k sgm[k zbm[] k zb6[]]]]].
d sgo[event a place a frame a unit a value h[b] c context d synchrony h[a a a a d] c valid h[h[b] c] c] c[
 w[c[v valid][v value]][w[k zbz[v frame k zbh[v frame v context] v context]][g clock a[
 w[k zbz[v frame v clock v context]][
 k saf[v event v clock v place k zbh[v frame v context] v frame v unit v value v context p ca p cb p cc p ci p ce v synchrony]]
 ]]]
].
d sgp[event a place a frame a unit a context d synchrony h[a a a a d] c valid h[h[b] c] c same h[h[b] c h[b] c] c] c[
 w[k sgo[v event v place v frame v unit k zbe[v event v frame v unit v context] v context v synchrony v valid]][
 f value h[b] c[y[k sgo[v event v place v frame v unit v value v context v synchrony v valid]][
 c[v same][v value k zbe[v event v frame v unit v context]]]]]
].
d sgq[frame a context d synchrony h[a a a a d] c valid h[h[b] c] c same h[h[b] c h[b] c] c] c[
 w[k va[v frame]][w[k ci[k rb[]]][
 w[f clock a[z[k zbz[v frame v clock v context]][k zbz[v frame v clock k zb4[]]]]][
 w[f clock a[z[k qa[v clock v frame v context]][k zbz[v frame v clock v context]]]][
 w[k sgg[i[place a][k zcu[v place v frame v context]] i[clock a][k zbz[v frame v clock v context]]
   i[clock a place a][k cb[v clock v place v frame]] i[clock a][w[k ca[v clock]][k cc[v clock v frame]]]
   i[clock a reference a][c[v synchrony][v clock v reference v frame k rb[] v context]] k zbh[v frame v context]]][
 k sgi[i[place a][k zcu[v place v frame v context]] i[clock a][k zbz[v frame v clock v context]]
   i[clock a place a][k cb[v clock v place v frame]] i[event a][k zcz[v event v frame v context]]
   i[event a place a][k cb[v event v place v frame]]
   i[event a place a][k sgp[v event v place v frame k rb[] v context v synchrony v valid v same]]]
 ]]]]]
].
d sgr[frame a context d] c[k sgq[v frame v context p qo p ba p sca]].
d sgs[] e[b context[w[k sgr[k ra[] k zb6[]]][k sgr[k zbm[] k zb6[]]]]].
'''
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[w[k ug[k zc2[] k rd[] r[k sgn[]] k rh[] k ri[]]][k zao[k zcp[] k zc2[] k rh[] k ri[]]]].
s[w[k ug[k zc3[] k rd[] r[k sgs[]] k rh[] k ri[]]][k zao[k zc2[] k zc3[] k rh[] k ri[]]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-parallel-histories-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-frame-measurements-basis-v1',document='examples/v014/einstein-frame-measurements.noema')
    basis['definitions'].update(MEANINGS)
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zcu',['place','frame','context'],'指定系で測る空間の地点範囲。標本点だけでなく記述の対象となる全空間を意味規約で指定する。異なる系の地点の同一視は補わない。'),
        ('zcv',['place','frame','role','context'],'地点を指定軸へ正射影した地点の候補。射影関係zcwで妥当性を別途要求する。'),
        ('zcw',['place','projection','frame','axis','context'],'指定系の地点から、その系の指定した有向軸への正射影関係。軸の方向と射影の幾何学的構成は未説明。'),
        ('zcx',['ruler','origin','projection','frame','axis','unit','value','context'],'同じ物差しを用い、指定系の有向軸に沿って原点から射影点まで測った符号付き距離。負値と零を許す。反復配置、校正と誤差の説明は未完。'),
        ('zcy',['place','frame','role','unit','context'],'地点の指定成分へ付与する座標候補。測定の存在と全候補の値一致はsgkが要求する。'),
        ('zcz',['event','frame','context'],'この空間と時間の記述で時刻付与の対象とする出来事の全範囲。個別の有限観測標本と同一視しない。'),
        ('zc2',[],'両系の物差しで空間を測り座標を定めるという思考設定の本文箇所。'),
        ('zc3',[],'各系の静止時計と光信号の方法で時計配置点の時刻を定めるという想定の本文箇所。')):
        d=decls[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'sgj':'同じ地点・系・軸・原点・物差し・単位・文脈で、正射影と符号付き測定を結ぶ有効な座標候補。',
        'sgk':'選んだ座標がsgjを満たし、全ての有効な測定候補と値が一致する。一つの成功した読みだけで不一致を隠さない。',
        'sgl':'初期と同じ原点・三軸・剛な物差しを用い、その系で静止する物差しで全地点の三成分を存在かつ一意に定める。',
        'sgm':'sglを実切断の妥当性baと値の一致scaへ結ぶ。',
        'sgn':'静止系と運動系のそれぞれにsgmを課す空間測定の想定内容。両系の座標値の等しさを要求しない。',
        'sgo':'配備した同じ系の参照時計へ同期する配備時計を、同じ場所の同じ出来事へ結び、有効な読みを時刻候補とする。',
        'sgp':'同じ出来事・地点・系の選択時刻がsgoを満たし、全ての有効な候補がその値に一致する。',
        'sgq':'初期と同じ全配備時計を同期の範囲に取り、同じ系で静止して空間内に配置されることを確認する。時計のある地点の対象出来事に一意な時刻を課す。',
        'sgr':'sgqの同期を§1の光往復全試行qoへ、時刻を実切断baと値一致scaへ接続する。',
        'sgs':'静止系と運動系のそれぞれにsgrを課す時間決定の想定内容。系をまたぐ時計の同期や指示の等しさを要求しない。'})
    basis['unresolved']+=generic_composed()[1]['unresolved']+[
        'u0045の部分的な操作的解釈。座標測定を正射影と符号付き距離に展開したが、その具体的操作は原文がこの段落で明記したものではない。',
        '有向軸の正方向、正射影、物差しの反復配置、測定精度、全空間と全出来事の範囲の実現は未完。',
        'cb・cc・ceは旧規約上の対象期間を共有する。別の実験設定で時計の配置・静止・読みを変える一般的な文脈添字への拡張は未完。',
        '時計のある地点での出来事時刻を既存の局所時計規約へ接続した。時計のない地点への連続的拡張は主張しない。',
        'M0077のx,y,zとM0078のξ,η,ζは同じ三成分の役割を各系へ束縛して表す。原字形自体の復元は意味条件ではない。',
        '両系での同じ出来事の四座標の対応と変換の導出、原刊照合、全文の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/frame-measurements-basis-v1.json'),(source_composed,'data/einstein-frame-measurements-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored frame measurement differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Frame-local space and time measurements composed')


if __name__=='__main__':main()
