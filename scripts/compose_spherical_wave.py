"""Compose the spherical-wave check without promoting an attributed proof."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_affine_time_form import CUT


def definitions():
    return '''
d sqg[light b x b y b z b time b] b[k ab[k ab[k ad[v x v x] k ab[k ad[v y v y] k ad[v z v z]]] k ac[k ad[k ad[v light v light] k ad[v time v time]]]]].
d sqh[admissible h[d] c first e second e] c[g setting d[w[c[v admissible][v setting]][w[t[v first][v setting]][t[v second][v setting]]]]].
d sqi[agent a target i[e] stage d scope a supplied h[a a i[e] d a] c] c[g proof a[c[v supplied][v proof v agent v target v stage v scope]]].
'''


MEANINGS={
    'sqg':'有理数のx²+y²+z²-V²*t²。零であることだけでは時刻の正負、非退化、実際の光の伝播を意味しない。',
    'sqh':'同じ対象設定で二つの内容が共に成立する余地があるという両立性の読み。許容設定の存在を要求し、全設定での成立や現実での真理を要求しない。',
    'sqi':'指定主体が指定段階・論述範囲で対象内容の証明として提示したものが存在する。提示関係を引数で受け、検査器の証明認定と分ける。'}


def generic_composed():
    doc=parse((ROOT/'examples/v014/origin-constants.noema').read_text(encoding='utf-8')+definitions())
    basis=deepcopy(json.loads((ROOT/'data/origin-constants-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='spherical-wave-basis-v1',document='examples/v014/spherical-wave.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['両立性は指定した許容設定と同じ解釈に相対的である。証明の提示からその妥当性を導かない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-origin-constants.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()
    add=lambda x,y:'k bd['+x+' '+y+']';mul=lambda x,y:'k shv['+x+' '+y+']'
    x,y,z,t=('v '+name for name in ('x','y','z','time'))
    text+='d sqj[light '+CUT+' x '+CUT+' y '+CUT+' z '+CUT+' time '+CUT+'] '+CUT+'[k bf['+add(mul(x,x),add(mul(y,y),mul(z,z)))+' '+mul(mul('v light','v light'),mul(t,t))+']].\n'
    zero='k bb[n p a b]';coords=['k zc6[v record k '+role+'[]]' for role in ('yn','yo','yp','zc7')]
    residual='k sqj[v light '+' '.join(coords)+']'
    text+='d sqk[record a light '+CUT+'] c['+both('k sha[v record p ba]','k ba[v light]','k bg['+zero+' v light]',
        'k ba['+residual+']','k sca['+residual+' '+zero+']')+'].\n'
    text+='d sql[record a light '+CUT+'] c[w[k sqk[v record v light]][k bg['+zero+' '+coords[3]+']]].\n'
    text+='r zfr[a a i[e] d a] c.r zfs[d] c.r zft[a a d] c.r zfu[] a.r zfv[] a.r zfw[] a.r zfx[] d.\n'
    text+='r zfy[] a.r zfz[] a.r zga[a a i[e] d a d] c.r zgb[a a i[e] a a d] c.\n'
    text+='r zgc[] a.r zgd[] a.r zge[] a.r zgf[] a.r zgg[] a.r zgh[] a.\n'
    text+='d sqm[wave a emission a event a frame a setting d] c[g ray a['+both('k zft[v wave v ray v setting]','k cf[v ray]','k cg[v ray v emission v event v frame]')+']].\n'
    # A front is a locus, not a single point that happens to satisfy an equation.
    hit='k sqm[v wave v emission v event v frame v setting]'
    chart='k shd[v event v record v frame v setting]'
    future='k sql[v record k tc[]]'
    text+='d sqn[wave a emission a frame a setting d] c['+both(
        'g event a[g record a['+both('k zc4[v event]',chart,hit,future)+']]',
        'f event a[f record a[y[w[k zc4[v event]]['+chart+']][z['+hit+']['+future+']]]]')+'].\n'
    text+='d sqo[wave a emission a setting d] c['+both('k smk[v emission v setting]',
        'g ray a[k zft[v wave v ray v setting]]',
        'f ray a[y[k zft[v wave v ray v setting]][k cf[v ray]]]')+'].\n'
    wave='k zfu[]';emission='k zfv[]';event='k zfw[]';setting='k zb6[]'
    rest='k zdz['+event+' k ra[] '+setting+']';moving='k zdz['+event+' k zbm[] '+setting+']'
    text+='d sqp[] e[b context['+both('k sqo['+wave+' '+emission+' '+setting+']',
        'k sqn['+wave+' '+emission+' k ra[] '+setting+']')+']].\n'
    text+='d sqq[] e[b context['+both('k zc4['+event+']','k shd['+event+' '+rest+' k ra[] '+setting+']',
        'k sqm['+wave+' '+emission+' '+event+' k ra[] '+setting+']','k sqk['+rest+' k tc[]]')+']].\n'
    text+='d sqr[] e[b context['+both('k zc4['+event+']','k shd['+event+' '+moving+' k zbm[] '+setting+']','k sqk['+moving+' k tc[]]')+']].\n'
    text+='d sqs[] e[b context[w[t[k spk[]][v context]][t[k sqq[]][v context]]]].\n'
    text+='d sqt[] e[b context[f first a[f second a[y[w[k spg[v first v second]][k sqk[v first k tc[]]]][k sqk[v second k tc[]]]]]]].\n'
    text+='d squ[] e[b context[y[k sbc[k tc[] v context]][k smw[k zbm[] k tc[] v context]]]].\n'
    text+='d sqv[] e[b context[k sqn['+wave+' '+emission+' k zbm[] '+setting+']]].\n'
    text+='d sqw[] e[b context[k sqh[p zfs k saw[] k sbd[]]]].\n'
    text+='d sqx[] e[b context[u[k sqi[k rd[] r[k sqw[]] k zfx[] k rh[] p zfr]]]].\n'
    text+='d sqy[] e[b context['+both('t[k sqp[]][v context]',
        'k zc4['+event+']','k shd['+event+' '+rest+' k ra[] '+setting+']',
        'k sqm['+wave+' '+emission+' '+event+' k ra[] '+setting+']')+']].\n'
    # Additional sufficient conditions for the geometric future front, not source wording.
    text+='d sqz[] e[b context['+both('t[k sqp[]][v context]','t[k spk[]][v context]',
        't[k shi[]][v context]','k bg['+zero+' c[k spc[]][k zb7[]]]',
        'f event a[y[k zc4[v event]][z[k sqm['+wave+' '+emission+' v event k ra[] '+setting+']][k sqm['+wave+' '+emission+' v event k zbm[] '+setting+']]]]')+']].\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k uh[k zfy[] k rd[] r[k sqx[]] k rh[] k ri[]]].
s[k zga[k zfz[] k rd[] r[k squ[]] k zfx[] k rh[] k ri[]]].
s[k zgb[k zfy[] k rd[] r[k sqx[]] k zfz[] k rh[] k ri[]]].
s[k ug[k zgc[] k rd[] r[k sqp[]] k rh[] k ri[]]].
s[k zc[k zgd[] k rd[] r[k sqy[]] r[k sqq[]] k rh[] k ri[]]].
s[k zd3[k zge[] k rd[] r[k sqs[]] r[k sqq[]] r[k sqr[]] k rh[] k ri[]]].
s[k zc[k zgf[] k rd[] r[k sqr[]] r[k sqv[]] k rh[] k ri[]]].
s[k zfl[k zgh[] k rd[] r[k sqz[]] r[k sqv[]] k rh[] k ri[]]].
s[k zc[k zgg[] k rd[] r[k sqv[]] r[k sqw[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-origin-constants-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-spherical-wave-basis-v1',document='examples/v014/einstein-spherical-wave.noema')
    basis['definitions'].update(MEANINGS|{
        'sqj':'実切断でのx²+y²+z²-V²*t²。',
        'sqk':'有効な座標記録が、正のVについて球面波の二乗方程式を満たす。時刻の符号と実際の光の到来は別条件。',
        'sql':'sqkに時刻の正を加えた未来側の波面。放出点そのものはsqoで別に扱う。',
        'sqm':'指定波を構成する光線の少なくとも一つが、指定系で同じ放出出来事から指定出来事へ伝播する。',
        'sqn':'対象範囲の実測記録で、波の到来と未来側の球面方程式が過不足なく一致し、実際の到来点が少なくとも一つある。全空間を標本で代用しない。',
        'sqo':'波を構成する光線は非空で全て光であり、放出出来事は両系の共通空間原点かつt=τ=0である。',
        'sqp':'共通原点・共通零時刻の放出と、静止系でVにより拡大する球面波を仮定する内容。',
        'sqq':'指定した到来点の静止系記録がx²+y²+z²=V²*t²を満たすという内容。',
        'sqr':'同じ出来事の運動系記録がξ²+η²+ζ²=V²*τ²を満たすという内容。',
        'sqs':'既出の四式と、指定点の静止系球面式を座標置換の前提として合わせる。',
        'sqt':'四式を満たす全記録対について、静止系の二乗球面式から運動系の二乗球面式が従うという内容。',
        'squ':'静止系で仮定した光速度Vの法則が成り立つなら、運動系でも同じVの法則が成り立つという未証明課題の内容。',
        'sqv':'同じ波の到来と未来側の球面式が運動系でも過不足なく一致するという内容。',
        'sqw':'同じ許容物理設定で、相対性原理sawと光速度一定sbdが共に成立し得るという両立性の部分解釈。',
        'sqx':'この論述段階・範囲では両立性の証明がまだ提示されていない。内容が偽、証明が不可能、後段でも未証明という意味を加えない。',
        'sqy':'仮定した静止系の波面上に指定出来事の実測記録があるという、静止系球面式への前提内容。',
        'sqz':'未来側の波面への十分条件を補う解釈。先行四式、両系での記録の存在、正のφ、同じ光の到来を両系で追跡することを明示する。'})
    decls={d['name']:d for d in doc['declarations']}
    entries=[
        ('zfr',['proof','agent','content','stage','scope'],'指定主体がその段階までの論述範囲で対象内容の証明として当該論証を提示済みである。論証の妥当性や検査器の受理を含意しない。'),
        ('zfs',['setting'],'二原理の両立を検討する許容物理設定。同じ語・単位・測定規約の解釈を維持する。許容性の一般的構成は未完。'),
        ('zft',['wave','ray','setting'],'指定設定で同じ放出に由来する波の構成光線として扱う関係。光線の連続的な集合と波動場の構成は未完。'),
        ('zfu',[],'共通原点から放出する検討対象の波。球面性は名前でなくsqnの条件で与える。'),
        ('zfv',[],'同じ波の放出出来事。共通原点と零時刻をsqoで結ぶ。'),
        ('zfw',[],'同じ波が到来したものとして選ぶ対象出来事。座標と実際の到来は別に検査する。'),
        ('zfx',[],'両立性の証明をまだ提示していないと述べるu0086の段階。'),
        ('zfy',[],'両立性の証明が未提示であることを述べる箇所。'),
        ('zfz',[],'運動系の任意の光線にも同じ速度法則を示す課題を提示する箇所。'),
        ('zga',['node','author','target','stage','scope','context'],'著者が指定段階で対象内容を証明すべき課題として提示する。達成済みも解の存在も断言しない。'),
        ('zgb',['node','author','reason','task','scope','context'],'著者が引用した内容を、その課題を行う理由として挙げる。理由の真理や論理的十分性を含意しない。'),
        ('zgc',[],'共通零点からの球面波を設定する本文箇所。'),
        ('zgd',[],'静止系での球面方程式を得る本文箇所。'),
        ('zge',[],'既出の四式を使って球面方程式を変換する本文箇所。'),
        ('zgf',[],'変換した式から運動系でも球面波であると結論する本文箇所。'),
        ('zgg',[],'球面波の議論により二原理の両立が示されたとする本文箇所。'),
        ('zgh',[],'未来側の波面のための正のφ・記録・同じ到来の条件を補う解釈注記。')]
    for name,args,meaning in entries:
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['unresolved']+=[
        'u0086〜u0091への部分記述。原刊照合、波の到来と光線集合の一般的な意味、原文との全文意味一致は未完。',
        '球面式の保存だけではφ=0の退化やφ<0の時間方向反転を除けない。未来側の物理的な波面への追加十分条件はsqzで明示し、著者の逐語的前提とはしない。',
        '有限の記録範囲で球面式と到来が一致することは、連続空間の全点が対象に含まれることや全方向・全波源の光速度一定の証明ではない。',
        '二原理の両立は同じ許容設定での共充足として部分解釈した。実際の許容物理モデルの構成と一般の実切断上の証明は未完であり、著者の証明完了の結論への帰属で代用しない。',
        '原文の「簡単な計算」という評価・強調と、全方向の光の完全な場としての構成は未記述。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,name in ((generic_composed,'spherical-wave'),(source_composed,'einstein-spherical-wave')):
        text,basis=compose()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored spherical wave differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Spherical-wave equations and the still-open compatibility proof composed')


if __name__=='__main__':main()
