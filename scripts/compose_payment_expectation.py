"""Separate payment capacity, avoidable thinking and prospective takeover."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT
from scripts.compose_substituted_judgment import generic_composed as substitution


def definitions():
    return '''
d rf[payer a receiver a transfer a medium a purpose i[h[a] e] scene d moves h[a a a a d] c accepted h[a d] c consideration h[a a i[h[a] e] d] c] c[
 w[u[e[v payer][v receiver]]][w[c[v moves][v transfer v payer v receiver v medium v scene]][
  w[c[v accepted][v medium v scene]][c[v consideration][v transfer v receiver v purpose v scene]]
 ]]
].
d rh[person a task i[h[a] e] scene d human h[a] c undertakes h[a a i[h[a] e] d] c] c[
 g other a[w[c[v human][v other]][w[u[e[v other][v person]]][c[v undertakes][v other v person v task v scene]]]]
].
d ri[content e context d candidates h[d] c later h[d d] c] c[
 w[g scene d[c[v candidates][v scene]]][f scene d[y[c[v candidates][v scene]][w[u[e[v context][v scene]]][w[c[v later][v context v scene]][t[v content][v scene]]]]]]
].
'''


def generic_composed():
    text, basis = substitution()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='payment-expectation-basis-v1', document='examples/v014/payment-expectation.noema')
    basis['definitions'].update({
        'rf': '別の受け手への同じ移転について、支払う人・価値媒体・状況を固定し、その媒体が支払いに受け入れられ、同じ移転が記述された活動への対価として扱われる。無関係な移転や贈与を対価と混ぜない。',
        'rh': '本人とは異なる人が、本人のために記述された仕事を引き受ける。全員が引き受けること、特定の一人を固定すること、仕事を完了することは含めない。',
        'ri': '予想候補が非空で、その全てが指定文脈より先の状況として位置付けられ、そこで内容が成立する。現在の内容の真理や現実にその未来が実現することは含まない。'})
    basis['unresolved'] += [
        '支払媒体・価値移転・対価としての扱い・引受けの意味・予想候補とその時間的位置付けは引数で与える。貨幣や契約の制度全体、確率的な予測の理論は含まない。',
        'riは全ての選んだ予想候補での成立を表す。選定範囲外の可能性を排除したり、ある確率以上だと数値的に主張したりするものではない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-delegated-judgment.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r ti[a a a a d] c.r tj[a d] c.r tk[a a i[h[a] e] d] c.r tl[a a d d] c.
r ts[a a i[h[a] e] d] c.r tu[a i[h[a] e] d] c.r tw[a i[h[a] e] d d] c.r tx[d d] c.r t4[] a.
d to[person a] e[b scene[g receiver a[g transfer a[g medium a[
 k rf[v person v receiver v transfer v medium r[p bm] v scene p ti p tj p tk]
]]]]].
d tp[person a] e[b scene[k xd[v person k to[v person] v scene p ae p af p ap]]].
d tq[person a] e[b scene[k rd[v person k sw[v person] v scene p ae p af p ap p tl]]].
d tr[person a] e[b context[k rc[v person p tp p tq i[scene d][k s2[v person v context v scene]]]]].
d tz[person a] e[b scene[k rh[v person r[p bm] v scene p aa p ts]]].
d t2[person a] e[b context[w[k tu[v person r[p bm] v context]][
 k ri[k tz[v person] v context i[scene d][k tw[v person r[p tz] v context v scene]] p tx]
]]].
d t3[person a] e[b context[w[t[k tr[v person]][v context]][t[k t2[v person]][v context]]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    text = format_graph(doc, 'compact') + '''
s[w[k s4[k t4[] k wa[] r[p t3] k wh[]]][k ue[k s3[] k t4[] k wh[]]]].
'''
    doc = parse(text)
    basis = deepcopy(json.loads((ROOT / 'data/kant-delegated-judgment-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-payment-expectation-basis-v1', document='examples/v014/kant-payment-expectation.noema')
    generic = generic_composed()[1]
    basis['definitions'].update({name: generic['definitions'][name] for name in ('rf', 'rh', 'ri')})
    decls = {d['name']: d for d in doc['declarations']}
    for name, labels, meaning in (
        ('ti', ['transfer', 'payer', 'receiver', 'medium', 'scene'], '指定した移転で、支払う側から受け手へその価値媒体の管理・利用に関する地位が移る。現金の物理的移動だけに限定せず、単なる残高の存在とも区別する。価値・権利・移転一般の基礎説明は未完。'),
        ('tj', ['medium', 'scene'], 'その文脈で、その媒体が支払いに用いる価値媒体として受け入れられている。特定の通貨、額、物理的形態を原文へ補わない。'),
        ('tk', ['transfer', 'receiver', 'purpose_description', 'scene'], 'その受け手に関する同じ移転が、記述された仕事への対価として位置付けられる。贈与や別件の支払いとの区別を持ち、仕事の完了や履行の保証は含まない。'),
        ('tl', ['person', 'plan', 'start', 'end'], 'その人の方法の実行経路に、ここで問題とする本人の思考・理解力の使用が含まれる。現在時点だけの不実行とは区別する。思考全般の語義を確定したものではない。'),
        ('ts', ['other', 'person', 'task_description', 'scene'], '他者が本人のために記述された仕事を自分の担当として引き受ける。引受けと実行・完了を分け、原文にない契約の詳細や期日を固定しない。'),
        ('tu', ['person', 'task_description', 'context'], '仮定上の話者の視点で、その記述された仕事が煩わしく不快なものとして評価される。著者本人の評価や仕事の客観的な性質と同一視しない。'),
        ('tw', ['person', 'prospect_description', 'context', 'candidate'], '仮定上の話者が、その人物についての予想の記述を確からしいものとして提示する際に採用する候補状況。原文のwerden ... schonの確信を伴う見込みの一つの読みであり、数値確率や全可能世界の集合ではない。'),
        ('tx', ['context', 'candidate'], '予想候補が、その文脈より先の状況として位置付けられる。実現済みの同じ履歴内の時間順序とは区別し、具体的な期日は指定しない。'),
        ('t4', [], '支払う能力と自分で考える必要のなさ、他者による引受けの見込みを述べる一文の談話箇所。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'], 'arguments': labels, 'meaning_ja': meaning})
    basis['definitions'].update({
        'to': '本人が、理解力を用いる仕事bmへの対価として、別の受け手へ受容された価値媒体を移転する内容。額・受け手・移転個体は存在量化し、原文にない固有の値は補わない。',
        'tp': '本人が選択できる方法があり、非空で整合した全評価結果でtoの支払いが成立する。支払い済みという主張と区別する。',
        'tq': '本人の実用上の目的swを満たす同じ選択可能な方法があり、全評価結果への経路に本人の対象となる思考tlがない。思考不能や、本人が何もしないという事実とは異なる。',
        'tr': '同じ本人について、選んだ仮定状況で支払う能力tpがあればtqが成立するという条件。逆方向の含意や同値、支払い済みという前件へ置き換えない。',
        'tz': '本人と異なる人が、本人の理解力を用いる仕事bmをその人のために引き受ける内容。引受ける人は状況ごとに異なってよく、全員が引き受けることや完了を要求しない。',
        't2': '仮定上の話者が仕事bmを煩わしいと評価し、自分についての他者の引受けtzを将来の予想候補全てで見込む。引受けの現実の成立は断言しない。',
        't3': '同じ仮定上の人物・文脈について、支払い能力を前件とするtrと他者の引受けの見込みt2を結ぶ。一人称の提示s4によって著者へ帰属し、前の三例の文の後に置く。'})
    basis['unresolved'] += generic['unresolved'][-2:] + [
        '支払いは対価としての価値移転、denkenは文脈で問題となる本人の理解力の使用、werden ... schonは確信を伴う将来の見込みとして読む部分草案である。各語の全意味や唯一の読みの証明ではない。',
        'nurはここでは十分条件を提示する読みを保ち、支払えなければ必ず自分で考えるという逆向きの条件を追加しない。焦点・強調・皮肉の談話効果は未完。',
        '前件の支払う能力と後半の見込みを一文内で保持するが、支払いが引受けを必ず引き起こすという因果機構や、支払いと履行の同じ契約上の当事者の同定までは追加していない。',
        '後半の予想は仮定上の話者の文脈で提示し、支払う能力の条件文と同じ人物へ結ぶ。文全体の皮肉や語用論上の作用範囲、直前の便宜さの文と残りの段落、原刊照合と全文完成は残る。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/payment-expectation-basis-v1.json'),
                              (source_composed, 'data/kant-payment-expectation-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored payment expectation differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Payment capacity and prospective undertaking connected without asserting payment or completion')


if __name__ == '__main__':
    main()
