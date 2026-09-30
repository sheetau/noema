"""Compose a measured roundtrip rate and adoption of a common vacuum-light value."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.language import convert
from noema.meaning_basis import audit_basis
from scripts.compose_event_time import ROOT, definitions as event_definitions


def definitions():
    return '''
d sah[left h[b] c right h[b] c] h[b] c[i[value b][
 x[k aa[v value n p a b]][g first b[g second b[
 w[k aa[n p a b v first]][w[k aa[n p a b v second]][w[c[v left][v first]][w[c[v right][v second]][k aa[v value k ad[v first v second]]]]]]]]
]]].
d sai[distance h[b] c start h[b] c end h[b] c speed h[b] c] c[
 w[k ba[v distance]][w[k ba[v start]][w[k ba[v end]][w[k ba[v speed]][
 w[k bg[k bb[n p a b] v distance]][w[k bg[v start v end]][w[k bg[k bb[n p a b] v speed]][
 k sag[k sah[v speed k bf[v end v start]] k bd[v distance v distance] p bc]
 ]]]]]]]
].
d saj[distance b start b end b speed b lengthscale b timescale b speedscale b] c[
 w[k aa[n p a b v lengthscale]][w[k aa[n p a b v timescale]][w[k aa[n p a b v speedscale]][
 w[k aa[n p a b v distance]][w[k aa[v start v end]][w[k aa[n p a b v speed]][
 e[k ad[k ad[v speedscale v speed] k ad[v timescale k ab[v end k ac[v start]]]]][k ad[n p c b k ad[v lengthscale v distance]]]
 ]]]]]]
].
d sak[value h[b] c selected h[a] c measured h[a h[b] c] c] c[
 w[g trial a[c[v selected][v trial]]][f trial a[y[c[v selected][v trial]][c[v measured][v trial v value]]]]
].
'''


MEANINGS = {
    'sah':'非負の実数の下側切断の積。既存のreal-productsのccと同じ式を、時計関係の記号と衝突しない名前で再利用する。',
    'sai':'正の一方向距離、正の往復経過時間、正の速度について、速度×経過時間＝距離＋距離を切断の両方向の包含で課す。同じ互換単位での読みを渡す。',
    'saj':'有理数の距離・出発時刻・帰着時刻・速度と正の各単位尺度について、基準単位に換算して往復の速度式を満たす。出発と帰着は共通の時間尺度を使う。',
    'sak':'非空の指定試行の全てで、一つの共通値が測定条件を満たす。試行ごとに異なる値を選ぶ条件とは区別する。'}


def generic_composed():
    base = convert(parse((ROOT/'examples/v011/real-cuts.noema').read_text(encoding='utf-8')), '0.14')
    doc = parse(format_graph(base,'compact') + event_definitions() + definitions())
    basis = deepcopy(json.loads((ROOT/'data/real-cuts-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='roundtrip-speed-basis-v1', document='examples/v014/roundtrip-speed.noema')
    basis['definitions'].update(json.loads((ROOT/'data/event-time-basis-v1.json').read_text(encoding='utf-8'))['definitions'])
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'saiは実数の式、sajは有理数の尺度換算の検査用定義。後者を実数全域の証明とは扱わない。',
        'sahは非負入力にだけ使う。saiでは速度と経過時間の正値性を確認する。',
        '距離、時間、速度の単位が対応すること、光が同じ二地点を往復すること、空間が真空であることは別の接続条件である。',
        '試行範囲の完全性をsakだけでは保証しない。観測した有限試行の一致から普遍法則の成立を推論しない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    previous = parse((ROOT/'examples/v014/einstein-event-time.noema').read_text(encoding='utf-8'))
    statements, previous['statements'] = previous['statements'], []
    text = format_graph(previous,'compact') + definitions() + '''
r ta[] a.r tb[] a.r tc[] h[b] c.
r td[a a a a d] c.r te[a] a.r tf[a] a.r tg[a] h[b] c.
r th[a a a a h[b] c] c.r ti[a] c.r tj[a a a] c.r tk[a a a a] c.
r tl[a a a d] c.r tm[] a.r tn[] a.r to[a a a a d] c.
d sal[trial a frame a timeunit a lengthunit a speedunit a value h[b] c context d criterion h[h[b] c h[b] c h[b] c h[b] c] c] c[
 w[k da[k te[v trial] k tf[v trial] k qc[v trial] k qd[v trial] k qe[v trial] k qf[v trial] k qg[v trial] k qh[v trial] v frame v timeunit k qi[v trial] k qj[v trial] k qk[v trial]]][
 w[k ti[v lengthunit]][w[k tj[v lengthunit v timeunit v speedunit]][
 w[k th[k qc[v trial] k qd[v trial] v frame v lengthunit k tg[v trial]]][
 w[k tk[k qh[v trial] k qe[v trial] k qf[v trial] v frame]][w[k tk[k qh[v trial] k qf[v trial] k qg[v trial] v frame]][
 c[v criterion][k tg[v trial] k qi[v trial] k qk[v trial] v value]
 ]]]]]]
].
d sam[value h[b] c context d criterion h[h[b] c h[b] c h[b] c h[b] c] c] c[
 w[k tl[k ra[] k rb[] k ta[] v context]][
 k sak[v value i[trial a][k td[v trial k ra[] k rb[] k ta[] v context]]
 i[trial a speed h[b] c][k sal[v trial k ra[] k rb[] k ta[] k tb[] v speed v context v criterion]]]
 ]
].
d san[value h[b] c context d] c[k sam[v value v context p sai]].
d sao[] e[b context[k san[k tc[] v context]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    doc = parse(format_graph(doc,'compact')+'''
s[w[k ug[k tm[] k rd[] r[k sao[]] k rh[] k ri[]]][k to[k tm[] k rd[] k tn[] k rh[] k ri[]]]].
''')
    basis = deepcopy(json.loads((ROOT/'data/einstein-event-time-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-roundtrip-speed-basis-v1',document='examples/v014/einstein-roundtrip-speed.noema')
    basis['definitions'].update(MEANINGS)
    meanings = [
        ('ta',[],'この速度評価に共通の長さ単位。'),('tb',[],'長さ単位taを時間単位rbで割った速度単位。'),
        ('tc',[],'全ての関連する光往復に共通と仮定する速度の読み。数値は指定しない。'),
        ('td',['trial','frame','time_unit','length_unit','context'],'指定基準系・単位・文脈で評価対象となる光往復試行。単なる既観測の一覧ではなく法則の適用範囲として指定する。'),
        ('te',['trial'],'その試行で出発と帰着の読みを与える局所時計。'),('tf',['trial'],'その試行の反射地点の局所時計。'),
        ('tg',['trial'],'その試行で測る二地点間の一方向距離の読み。'),
        ('th',['first_place','second_place','frame','length_unit','distance'],'指定基準系で二地点の空間的距離が指定長さ単位の値である関係。経路長や往復距離との同一化は含まない。'),
        ('ti',['unit'],'長さを測る単位である。物理的実現・校正は未説明。'),
        ('tj',['length_unit','time_unit','speed_unit'],'速度単位が指定長さ単位を指定時間単位で割った単位であり、これらの読みの商に追加換算係数が不要という関係。'),
        ('tk',['ray','from_event','to_event','frame'],'同じ光信号の指定された伝播区間が指定基準系の真空中にある。往路と復路を別々に要求する。'),
        ('tl',['frame','time_unit','length_unit','context'],'tdの試行範囲がこの法則で対象とする光往復を尽くしているという前提。有限観測から認定しない。'),
        ('tm',[],'経験に従って光速度の定数性を採用する本文箇所。'),('tn',[],'この採用に関係する経験的根拠。具体的な実験結果は原文に列挙されていない。'),
        ('to',['node','author','experience','scope','context'],'著者がその箇所・範囲での採用を、指定した経験的根拠に従うものとして位置付ける。根拠の正しさや採用内容の真理を含意しない。')]
    declarations = {d['name']:d for d in doc['declarations']}
    for name, args, meaning in meanings:
        d = declarations[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'sal':'同じ試行の二時計・二地点・出発反射帰着・光・読みを既存の物理プロトコルdaに結び、距離・真空の両区間・単位を要求する。速度条件へ距離と出発地点の出発帰着の読みを渡す。反射時計との同期条件dbは追加しない。',
        'sam':'関連試行の完全性・非空性・共通値を保持し、同じ単位と文脈で全試行のsalへ判定関数を渡す。',
        'san':'完全と指定した試行範囲の全てで同じ速度値がsalと実切断の速度式saiを満たす。基準系・単位・文脈は全試行で共通。',
        'sao':'共通速度値tcについてsanが成立するという状況ごとの内容。著者の採用へ記述として渡す。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'][-4:] + [
        '原文u0019〜u0021の式と経験に従う採用の部分草案。普遍性の全範囲、距離と真空の基礎概念、測定の一意性、原刊画像との照合は未完。',
        '往復の2倍距離の法則を記述する。任意の曲がった経路の長さが端点間距離の2倍であるとは推論しない。',
        '原文のVを共通の値tcとするが現代の光速の数値を補わない。他の慣性系との不変性や光源の運動からの独立性は後続節の課題。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose, filename in ((generic_composed,'data/roundtrip-speed-basis-v1.json'),(source_composed,'data/einstein-roundtrip-speed-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body: raise ValueError('Stored roundtrip speed differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream: stream.write(body)
    print('Roundtrip speed and empirical adoption composed')


if __name__=='__main__': main()
