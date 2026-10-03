"""Separate frame dependence, witnesses and a restricted simultaneity change."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both


def definitions():
    args='first a second a frame a other a context d events h[a] c frames h[a] c comparable h[a a a a d] c available h[a a d] c'
    passed='v first v second v frame v other v context v events v frames v comparable v available'
    text='d sdx['+args+'] c['+both(
        'u[e[v first][v second]]','u[e[v frame][v other]]',
        'c[v events][v first]','c[v events][v second]','c[v frames][v frame]','c[v frames][v other]',
        'c[v comparable][v first v second v frame v other v context]',
        *('c[v available][v '+event+' v '+frame+' v context]' for event in ('first','second') for frame in ('frame','other')))+'].\n'
    same='same h[a a a d] c'
    first='c[v same][v first v second v frame v context]'
    second='c[v same][v first v second v other v context]'
    text+='d sdy['+args+' '+same+'] c['+both('k sdx['+passed+']',first,'u['+second+']')+'].\n'
    text+='d sdz['+args+' '+same+'] c['+both('k sdx['+passed+']','u[z['+first+']['+second+']]')+'].\n'
    outer='context d events h[a] c frames h[a] c comparable h[a a a a d] c available h[a a d] c '+same
    def quantified(kind,body):
        for name in reversed(('first','second','frame','other')):body=kind+' '+name+' a['+body+']'
        return body
    text+='d sea['+outer+'] c['+quantified('f','y[k sdx['+passed+']][z['+first+']['+second+']]')+'].\n'
    for name,target in (('seb','sdy'),('sec','sdz')):
        text+='d '+name+'['+outer+'] c['+quantified('g','k '+target+'['+passed+' v same]')+'].\n'
    text+='d sed['+outer+'] c['+quantified('f','y[w[k sdx['+passed+']]['+first+']][u['+second+']]')+'].\n'
    square=lambda x:'k ad[v '+x+' v '+x+']'
    text+='d see[speed b light b scale b origin b time b position b result b] c['+both(
        'k aa[n p a b v light]','k aa['+square('speed')+' '+square('light')+']','u[e[v scale][n p a b]]',
        'e[k ad['+square('light')+' k ab[v result k ac[v origin]]]][k ad[v scale k ab[k ad['+square('light')+' v time] k ac[k ad[v speed v position]]]]]')+'].\n'
    text+='''
d sef[speed b light b scale b origin b first b firstx b firstout b second b secondx b secondout b] c[
 w[k see[v speed v light v scale v origin v first v firstx v firstout]][
 k see[v speed v light v scale v origin v second v secondx v secondout]]
].
'''
    return text


MEANINGS={
    'sdx':'異なる二出来事・異なる二基準系が指定範囲に属し、比較可能で、同じ文脈で四つ全ての時刻付与が利用可能。未付与を非同時と扱わないための定義域。',
    'sdy':'sdxの範囲で、第一の系では同時、第二の系では非同時であるという向きを持つ例。',
    'sdz':'sdxの範囲で同時性の真偽が二系で異なる例。どちら向きの違いでもよい。',
    'sea':'範囲内の全ての比較可能で時刻を付与済みの出来事対・基準系対について、同時性が保存される。空の比較範囲では空虚に成立する。',
    'seb':'sdyを満たす比較例が少なくとも一つある。全例が変化するとの主張ではない。',
    'sec':'sdzを満たす比較例が少なくとも一つある。seaの否定に対応する。',
    'sed':'指定範囲の全ての有効な比較で、第一系で同時なら第二系では非同時となるという、sebより強い全称条件。空の範囲での真を非絶対性の証拠とはしない。',
    'see':'有理数の時刻変換c²(出力-原点)=尺度(c²時刻-v位置)。c>0、v²<c²、尺度非零。後段の座標変換の時間成分を条件付きの補助検査として使う。',
    'sef':'二出来事に同じ速度・光速度・非零尺度・時刻原点を用いたsee。共通の変換を保ち、出来事ごとに原点や尺度を変えない。',
}


def generic_composed():
    doc=parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.\n'+definitions())
    inherited=json.loads((ROOT/'data/einstein-observer-judgments-basis-v1.json').read_text(encoding='utf-8'))
    basis={'version':'relative-simultaneity-basis-v1','document':'examples/v014/relative-simultaneity.noema',
        'primitives':[deepcopy(p) for p in inherited['primitives'] if p['symbol'] in ('aa','ab','ac','ad')],
        'definitions':MEANINGS.copy(),'unresolved':[
            '比較範囲・時刻の利用可能性・同時性は引数で与える。空の範囲や未付与から、非絶対性または非同時性を推定しない。',
            '有理数の時刻変換は後段の式を用いた補助検査であり、u0041までの原文の論証や全実切断の物理的導出の代用ではない。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-observer-judgments.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    text=format_graph(old,'compact')+definitions()+'''
r zbd[a] c.r zbe[a a a d] h[b] c.r zbh[a d] a.
r zbi[a a a a d] h[b] c.r zbj[] d.r zbk[] a.r zbl[a a a d] h[b] c.
d seg[event a frame a unit a value h[b] c context d synchrony h[a a a a d] c valid h[h[b] c] c] c[
 w[c[v valid][v value]][g clock a[g place a[
  k saf[v event v clock v place k zbh[v frame v context] v frame v unit v value v context p ca p cb p cc p ci p ce v synchrony]
 ]]]
].
d seh[event a frame a unit a context d synchrony h[a a a a d] c valid h[h[b] c] c same h[h[b] c h[b] c] c] c[
 w[k seg[v event v frame v unit k zbe[v event v frame v unit v context] v context v synchrony v valid]][
  f value h[b] c[y[k seg[v event v frame v unit v value v context v synchrony v valid]][
   c[v same][v value k zbe[v event v frame v unit v context]]
  ]]
 ]
].
d sei[event a frame a unit a context d synchrony h[a a a a d] c valid h[h[b] c] c] c[
 k seg[v event v frame v unit k zbe[v event v frame v unit v context] v context v synchrony v valid]
].
d sej[event a frame a context d] c[k seh[v event v frame k rb[] v context p qo p ba p sca]].
d sek[first a second a frame a context d] c[
 k sca[k zbe[v first v frame k rb[] v context] k zbe[v second v frame k rb[] v context]]
].
d sel[first a second a frame a other a context d] c[
 w[k sat[v frame v other v context]][w[k ba[k zbi[v frame v other k ta[] k rb[] v context]]][
 u[k sca[k zbi[v frame v other k ta[] k rb[] v context] k bb[n p a b]]]]]
].
d sem[first a second a frame a other a context d] c[
 w[k sel[v first v second v frame v other v context]][w[k ba[k zbl[v first v frame k ta[] v context]]][
 w[k ba[k zbl[v second v frame k ta[] v context]]][
 u[k sca[k zbl[v first v frame k ta[] v context] k zbl[v second v frame k ta[] v context]]]]]]
].
d sen[] e[b context[k sea[k zbj[] p zbd p va p sel p sej p sek]]].
d seo[] e[b context[k seb[k zbj[] p zbd p va p sel p sej p sek]]].
d sep[] e[b context[k sed[k zbj[] p zbd p va p sem p sej p sek]]].
d seq[] e[b context[w[u[t[k sen[]][v context]]][w[t[k seo[]][v context]][t[k sep[]][v context]]]]].
d ser[] e[b context[u[t[k sen[]][v context]]]].
d ses[] e[b context[w[t[k seo[]][v context]][t[k sep[]][v context]]]].
'''
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zc[k zbk[] k rd[] r[k sdt[]] r[k seq[]] k rh[] k ri[]]].
s[k zbc[k zbk[] k rd[] r[k ser[]] r[k ses[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-observer-judgments-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-relative-simultaneity-basis-v1',document='examples/v014/einstein-relative-simultaneity.noema')
    basis['definitions'].update(MEANINGS)
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zbd',['event'],'比較範囲の出来事。特定の二つの固有名を原文に補わない。'),
        ('zbe',['event','frame','time_unit','context'],'出来事に付与する時刻の候補値。単独では付与の存在・一意性を保証せず、sehで両方を検査する。'),
        ('zbh',['frame','context'],'基準系・文脈ごとに共通に使う参照時計。静止・時計型・同期はsafで別途要求する。'),
        ('zbi',['from_frame','to_frame','length_unit','time_unit','context'],'標準配置にある二系の符号付き相対速度。数値単位は指定した長さ単位と時間単位の商。系の順序を保持する。'),
        ('zbj',[],'相対的同時性の比較を論じる設定。先行する特定の棒の試行だけには限定しない。'),
        ('zbk',[],'同期判断の対比から同時性の非絶対性を述べる本文箇所。'),
        ('zbl',['event','frame','length_unit','context'],'標準配置の相対運動方向に沿った出来事の位置座標。座標全体の実現と一意性の一般説明は未完。')):
        d=decls[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'seg':'指定基準系・単位・文脈で、有効な値を読む静止局所時計と出来事の共通場所が存在し、その系の共通参照時計に同期している。',
        'seh':'選んだ候補時刻がsegを満たし、全てのsegを満たす値がその候補と一致する。場所や時計の違いによる複数表現は許すが、矛盾する時刻は許さない。',
        'sei':'選んだ候補がsegを満たすという接続部分。一意性を検査するsehとは区別する。',
        'sej':'sehを既存の光試行に基づく同期qo、有効な実切断ba、実数値の一致sca、時間単位rbに接続する。',
        'sek':'同じ系・単位・文脈の二時刻の値の一致。付与の存在と一意性は比較範囲sdx内のsejで要求する。',
        'sel':'既存の慣性系・標準配置・一定相対速度satに、有効で非零の符号付き速度を加えた比較範囲。',
        'sem':'selに加え、二出来事の相対運動方向の位置が有効な実数で異なるという制限。原文に明記のない条件なので解釈上の補足として区別する。',
        'sen':'比較設定のselの全範囲で同時性が保存されるという絶対性の候補。全文の概念的意味をこれだけに還元したとはしない。',
        'seo':'selの範囲で、第一系で同時な同じ二出来事が第二系で非同時となる例の存在。',
        'sep':'運動方向の位置差を持つsemの範囲で、同時性が保存されないという全称条件。横方向だけに離れた出来事等へは広げない。',
        'seq':'絶対性の否定、向きを持つ変化例の存在、制限した全称条件を合わせた結論の部分解釈。',
        'ser':'絶対性を否定する対比の第一項。',
        'ses':'変化例と制限した一般条件を提示する対比の第二項。'})
    basis['unresolved'].remove('u0041の相対的同時性への一般化、原刊画像の照合、本文全体の意味確認は未完。')
    basis['unresolved']+=generic_composed()[1]['unresolved']+[
        'u0041の全称的に読める表現を、非絶対性・変化例・運動方向の位置差に制限した一般則として部分解釈する。原文にない限定を補っているので、同義性の確認済み訳とはしない。',
        '「絶対的な意味を与えるべきでない」という認識上の要請と、「そう見る」という論述上の強さは未説明。対比と著者への推論帰属で部分保持する。',
        '局所時計の同期と全時刻の一意性、座標と相対速度の物理的実現、後段の時刻変換との実切断上の接続は未完。',
        '前段の棒と時計の例から一般の基準系・出来事への論証は著者への帰属として記述する。原刊画像の照合、全文の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/relative-simultaneity-basis-v1.json'),(source_composed,'data/einstein-relative-simultaneity-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored relative simultaneity differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Frame-relative simultaneity, available readings and restricted generalization composed')


if __name__=='__main__':main()
