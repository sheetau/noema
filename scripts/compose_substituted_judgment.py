"""Compose substitutable tasks and a conditional first-person illustration."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_contextual_ability import generic_composed as ability
from scripts.compose_limits import ROOT


def definitions():
    return '''
d ra[person a provider a task i[h[a] e] context d access h[a a d] c supplies h[a a i[h[a] e] d] c] c[
 w[u[e[v person][v provider]]][w[c[v access][v person v provider v context]][c[v supplies][v provider v person v task v context]]]
].
d rb[person a task i[h[a] e] kind h[a d] c context d access h[a a d] c supplies h[a a i[h[a] e] d] c] c[
 g provider a[w[c[v kind][v provider v context]][k ra[v person v provider v task v context v access v supplies]]]
].
d rc[person a premise h[a] e result h[a] e cases h[d] c] c[
 w[g scene d[c[v cases][v scene]]][f scene d[y[c[v cases][v scene]][y[t[c[v premise][v person]][v scene]][t[c[v result][v person]][v scene]]]]]
].
d rd[person a goal e start d available h[a a d] c outcomes h[a a d d] c selected h[a a d d] c effort h[a a d d] c] c[
 g plan a[w[c[v available][v person v plan v start]][w[k xa[v person v plan v start v outcomes v selected]][
  f end d[y[c[v selected][v person v plan v start v end]][w[t[v goal][v end]][u[c[v effort][v person v plan v start v end]]]]]
 ]]]
].
d re[person a premise h[a] e cases h[d] c] c[
 g scene d[w[c[v cases][v scene]][t[c[v premise][v person]][v scene]]]
].
'''


def generic_composed():
    text, basis = ability()
    doc = parse(text)
    doc['schema_version'] = doc['lexicon_version'] = '0.14'
    doc = parse(format_graph(doc, 'compact') + definitions())
    basis = deepcopy(basis)
    basis.update(version='substituted-judgment-basis-v1', document='examples/v014/substituted-judgment.noema')
    basis['definitions'].update({
        'ra': '本人とは異なる供給元が本人に利用可能で、同じ本人・仕事の記述・文脈について供給関係がある。供給元が人であること、本人がその仕事を実行したことは要求しない。',
        'rb': '指定した種類に該当し、raを満たす供給元が存在する。種類判定・利用可能性・供給関係の対象を別々の個体から継ぎ合わせない。',
        'rc': '比較する仮定状況の集合が非空で、その全てで同じ人物について前件が成立すれば後件も成立する。現在の前件や後件の真理、実在する人物についての全称主張は含まない。',
        'rd': '本人が選択できる一つの同じ方法について、非空で整合した評価結果の全てで目的を満たし、その実行経路に本人の対象となる努力がない。単なる不実行や、成功不能による必要条件の空虚な成立とは区別する。',
        're': '選んだ仮定状況のどれかで、同じ人物について前件が成立する。rcの条件成立と前件の実例の存在を分けて検査するための条件。'})
    basis['unresolved'] += [
        '代替供給の具体的な意味、仕事、供給元の種類、努力・目的・仮定状況の範囲は引数で明示する。汎用の必要性・反事実条件文の全理論ではない。',
        'rcでは前件が全候補で偽でも条件は成立しうる。適用例の存在が必要な利用ではreを別に要求する。空の候補範囲はrcが拒否する。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-nature-depiction.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r sa[a a d] c.r sb[a a i[h[a] e] d] c.
r sc[a d] c.r sd[a d] c.
r se[a a d] c.r sf[a a d] c.r sg[a a d] c.r sh[a a d] c.
r si[a i[h[a] e] d] c.r sj[a d] c.r sk[a a d d] c.
r s2[a d d] c.r s3[] a.r s4[a a i[h[a] e] d] c.r s5[a a j[i[h[a] e]] d] c.
d sl[provider a scene d] c[w[k sc[v provider v scene]][k sd[v provider v scene]]].
d sm[person a] e[b scene[g judgment a[w[k fa[v person v judgment v scene]][k se[v judgment v person v scene]]]]].
d sn[person a] e[b scene[g judgment a[g matter a[w[k fa[v person v judgment v scene]][w[k fb[v judgment v matter v scene]][k sf[v matter v person v scene]]]]]]].
d so[person a] e[b scene[g judgment a[g matter a[w[k fa[v person v judgment v scene]][w[k fb[v judgment v matter v scene]][k sg[v matter v person v scene]]]]]]].
d sp[provider a scene d] c[w[k aa[v provider]][k si[v provider r[p so] v scene]]].
d sq[person a] e[b scene[g judgment a[g matter a[w[k fa[v person v judgment v scene]][w[k fb[v judgment v matter v scene]][k sh[v matter v person v scene]]]]]]].
d sr[provider a scene d] c[w[k aa[v provider]][k si[v provider r[p sq] v scene]]].
d ss[person a] e[b scene[k rb[v person r[p bm] p sl v scene p sa p sb]]].
d st[person a] e[b scene[k rb[v person r[p sm] p sp v scene p sa p sb]]].
d su[person a] e[b scene[k rb[v person r[p sn] p sr v scene p sa p sb]]].
d sv[person a] e[b scene[w[t[k ss[v person]][v scene]][w[t[k st[v person]][v scene]][t[k su[v person]][v scene]]]]].
d sw[person a] e[b scene[k sj[v person v scene]]].
d sx[person a] e[b scene[k rd[v person k sw[v person] v scene p ae p af p ap p sk]]].
d sy[person a] e[b context[k rc[v person p sv p sx i[scene d][k s2[v person v context v scene]]]]].
d sz[] j[i[h[a] e]][l[i[h[a] e]][r[p ss] r[p st] r[p su]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    text = format_graph(doc, 'compact') + '''
s[w[k s4[k s3[] k wa[] r[p sy] k wh[]]][w[k s5[k s3[] k wa[] k sz[] k wh[]]][k ue[k mw[] k s3[] k wh[]]]]].
'''
    doc = parse(text)
    basis = deepcopy(json.loads((ROOT / 'data/kant-nature-depiction-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-delegated-judgment-basis-v1', document='examples/v014/kant-delegated-judgment.noema')
    generic = generic_composed()[1]
    basis['definitions'].update({key: generic['definitions'][key] for key in ('ra', 'rb', 'rc', 'rd', 're')})
    decls = {d['name']: d for d in doc['declarations']}
    records = (
        ('sa', ['person', 'provider', 'scene'], 'その人がその供給元を利用できる関係。物についての所持・参照可能性や人からの援助の利用を文脈に応じて含み、他人を所有することとはしない。'),
        ('sb', ['provider', 'person', 'task_description', 'scene'], '本人が記述された仕事を自ら行う代わりに、その供給元の判断・指示・表現が本人の用に供される。物が実際に思考すること、本人自身が仕事を実行したこと、供給された判断の正しさは含意しない。'),
        ('sc', ['object', 'scene'], '複数の記された表現を、一つの作品としてまとめた情報的対象。記号一般・作品・記された表現の一般的な基礎説明は残る。'),
        ('sd', ['object', 'scene'], '記された内容を、記憶の内側だけでなく外部の持続する媒体から参照できる。作品とその媒体の一般的な関係の定義は残る。'),
        ('se', ['judgment', 'person', 'scene'], 'その判断が本人の行為を、本人を拘束する道徳的要求に照らして評価する。判断を実行した人は別のfaで結び、適切さや正しさは保証しない。'),
        ('sf', ['matter', 'person', 'scene'], 'その事柄は、その人の身体の調子を保つための食事・日々の生活の調整に関する。現代の減量目的だけには限定しない。原文での範囲の確定は未完。'),
        ('sg', ['matter', 'person', 'scene'], 'その事柄は、宗教的な実践と理解におけるその人の精神的な生き方・安寧に関する。特定の教義の真理を前提にしない。'),
        ('sh', ['matter', 'person', 'scene'], 'その事柄は、その人の身体的な健康の維持・回復に関する。健康一般の説明は残る。'),
        ('si', ['provider', 'recipient_task_description', 'scene'], 'その人が、受け手について記述された活動を援助する継続的な役割・実践を担う。単発の判断代行、免許の保有、能力や援助の成功とは別の条件。'),
        ('sj', ['person', 'scene'], 'その人について、この仮定例で問題となる実用上の目的が満たされる。本人の思考・努力を目的達成の定義に織り込まない。対象の目的は解釈の前提として明示する。'),
        ('sk', ['person', 'plan', 'start', 'end'], '本人がその方法を実行して開始から結果に至る際、文脈で問題とする本人の努力を要する経路である。結果状況で努力していないだけでは否定できない。'),
        ('s2', ['person', 'context', 'case'], 'この文脈で、その人物を仮定例の一人称の位置へ置いて比較する状況。現実の履歴や著者の自伝的事実とは区別する。'),
        ('s3', [], '三つの代替供給例を含む一人称条件文の談話箇所。直前の便宜さの文や後続の支払いの文を含めない。'),
        ('s4', ['node', 'author', 'person_property_description', 'context'], '著者がその箇所で、人物を引数とする内容の記述を、仮定的な一人称の例として提示する。人物引数は例の話者位置であり、著者と同一だと固定せず、実在者全員に成立するとも断言しない。'),
        ('s5', ['node', 'author', 'examples', 'context'], '著者がその箇所で順序付きの例を提示し、その列挙を尽くした一覧として閉じていない。列外の特定の例や供給元の存在を補わない。'))
    for name, labels, meaning in records:
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'], 'arguments': labels, 'meaning_ja': meaning})
    basis['definitions'].update({
        'sl': '一つにまとめた記された作品で、外部の持続する媒体から参照できる。書物についての構成的な部分説明であり、物理的な製本様式や歴史的な全語義は含めていない。',
        'sm': '本人が自分の行為を道徳的要求に照らして判断する内容。良心を判断の活動として読む候補であり、感情や能力としての全意味は未完。',
        'sn': '本人が、自身の身体の調子を保つ食事・生活の調整について判断する内容。',
        'so': '本人が、自身の宗教的な生き方・安寧に関する事柄について判断する内容。',
        'sp': '人であり、他者についてsoの活動を援助する継続的な役割を担う。宗教上の助言者の部分説明であり、特定の職名を未説明の概念IDへ置き換えていない。',
        'sq': '本人が、自身の身体的な健康の維持・回復について判断する内容。',
        'sr': '人であり、他者についてsqの活動を援助する継続的な役割を担う。医師の専門性・制度的な資格の全条件はまだ不足する。',
        'ss': '本人が、slを満たす供給元を利用でき、自分の理解力の使用bmの代わりとなる内容がそこから供される例。',
        'st': '本人が、spを満たす供給元を利用でき、本人の道徳的な判断smの代わりとなる判断がそこから供される例。',
        'su': '本人が、srを満たす供給元を利用でき、本人の食事・生活の調整についての判断snの代わりとなる判断がそこから供される例。',
        'sv': '三つの例ss・st・suが同じ本人について同じ状況で成立する。供給元は例ごとに存在量化し、宗教上の助言者と医師が必ず別人だとは補わない。',
        'sw': 'この仮定例で本人について問題とする実用上の目的sjの内容。本人の自立的思考と同一視しない。',
        'sx': '本人が選択できる同じ方法で、評価する全結果においてswを満たし、その経路に本人の対象となる努力がない。原文の努力の不要を目的相対的に読む候補。',
        'sy': '同じ仮定上の本人について、選択した非空の状況範囲で、三つの例svの成立を前件、本人の努力なしの達成sxを後件とする条件文。',
        'sz': '原文順の三つの例ss・st・suの記述。非網羅的な列挙として提示するs5へ渡す。'})
    basis['unresolved'] += generic['unresolved'][-2:] + [
        '三つの供給元・仕事の部分説明と仮定的な一人称を追加した。職業・良心・書物の語義全体、jaの談話効果や皮肉、方便としての条件文の全意味は確定していない。',
        'Es ist so bequemから始まる直前文、支払いについての後続文、残る段落は今回の部分草案へ含めていない。既存原文単位の全文完成には数えない。',
        'Korporaのアカデミー版電子転記AA VIII 35行13〜16でも三例と条件の順序を確認した。原刊画像の照合ではない。転記にはmichの重複など保存した底本との差があり、底本を黙って変更しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/substituted-judgment-basis-v1.json'),
                              (source_composed, 'data/kant-delegated-judgment-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored substituted judgment differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Three substituted tasks connected within a first-person hypothetical frame')


if __name__ == '__main__':
    main()
